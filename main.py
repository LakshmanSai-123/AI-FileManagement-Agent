# ============================================================
# AI FILE MANAGEMENT AGENT
# Python + Groq API
# ============================================================

import os
import shutil
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

from groq import Groq


# ============================================================
# 1. CONFIGURATION
# ============================================================

SOURCE_FOLDER = Path(
    os.environ.get("FILE_AGENT_WORKSPACE", "MyFiles")
).resolve()

CATEGORIES = {
    "Documents": [".txt", ".pdf", ".doc", ".docx"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "Code": [".py", ".java", ".c", ".cpp", ".js", ".html", ".css"],
    "Spreadsheets": [".xlsx", ".xls", ".csv"],
    "Archives": [".zip", ".rar", ".7z"],
}

MODEL = "openai/gpt-oss-20b"
client = None


def ensure_workspace():
    """Create the workspace and its category folders."""
    SOURCE_FOLDER.mkdir(parents=True, exist_ok=True)

    for category in CATEGORIES:
        (SOURCE_FOLDER / category).mkdir(exist_ok=True)


def get_client():
    """Initialize Groq only when an AI request is needed."""
    global client

    if client is None:
        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured. "
                "Set it as an environment variable."
            )

        client = Groq(api_key=api_key)

    return client


# ============================================================
# 2. TOOL: LIST FILES
# ============================================================

def list_files():
    """Display files and folders in the workspace."""
    ensure_workspace()

    print("\nFILES AND FOLDERS")

    for item in sorted(SOURCE_FOLDER.iterdir()):
        if item.is_file():
            print(f"📄 {item.name}")
        else:
            print(f"📁 {item.name}/")

            for child in sorted(item.iterdir()):
                if child.is_file():
                    print(f"   {child.name}")


# ============================================================
# 3. TOOL: COUNT FILES
# ============================================================

def get_actual_counts():
    """Count files in each category folder."""
    ensure_workspace()
    counts = {}

    for category in CATEGORIES:
        folder = SOURCE_FOLDER / category

        counts[category] = sum(
            1 for item in folder.iterdir()
            if item.is_file()
        )

    return counts


def count_files():
    """Print category-wise file counts."""
    counts = get_actual_counts()

    print("\nFILE COUNT REPORT")

    for category, count in counts.items():
        print(f"{category}: {count}")

    print(f"Total categorized files: {sum(counts.values())}")

    return counts


# ============================================================
# 4. TOOL: ORGANIZE FILES
# ============================================================

def organize_files():
    """
    Move supported files from the workspace root into categories.
    Do not overwrite existing destination files.
    Leave unsupported files untouched.
    """
    ensure_workspace()

    moved = []
    skipped = []

    for item in list(SOURCE_FOLDER.iterdir()):
        if not item.is_file():
            continue

        destination_category = next(
            (
                category
                for category, extensions in CATEGORIES.items()
                if item.suffix.lower() in extensions
            ),
            None,
        )

        if destination_category is None:
            skipped.append(item.name)
            continue

        destination_folder = SOURCE_FOLDER / destination_category
        destination = destination_folder / item.name

        if destination.exists():
            skipped.append(
                f"{item.name} (destination already exists)"
            )
            continue

        shutil.move(str(item), str(destination))
        moved.append(f"{item.name} -> {destination_category}/")

    print("\nORGANIZATION REPORT")

    if moved:
        for filename in moved:
            print("done", filename)
    else:
        print("No supported files needed moving.")

    if skipped:
        print("\nSkipped files:")
        for filename in skipped:
            print("warning", filename)

    return moved, skipped


# British spelling alias
organise_files = organize_files


# ============================================================
# 5. VERIFY ORGANIZATION
# ============================================================

def verify_organization():
    """Check whether supported files remain in the workspace root."""
    ensure_workspace()

    supported_extensions = {
        extension
        for extensions in CATEGORIES.values()
        for extension in extensions
    }

    remaining = [
        item.name
        for item in SOURCE_FOLDER.iterdir()
        if item.is_file()
        and item.suffix.lower() in supported_extensions
    ]

    if remaining:
        return False, (
            "Supported files remain in the root: "
            + ", ".join(remaining)
        )

    return True, "All supported root files have been organized."


verify_organisation = verify_organization


# ============================================================
# 6. AI TOOL DEFINITIONS
# ============================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and folders in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_files",
            "description": "Count files in each category folder.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "organize_files",
            "description": (
                "Organize supported files from the workspace root "
                "without overwriting existing destination files."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

available_functions = {
    "list_files": list_files,
    "count_files": count_files,
    "organize_files": organize_files,
}


# ============================================================
# 7. LOCAL FALLBACK
# ============================================================

def local_agent(instruction):
    """Handle basic commands without the AI API."""
    instruction = instruction.lower()

    print("\n🛠️ Local fallback activated.")

    if any(word in instruction for word in (
        "count", "how many", "number of",
    )):
        count_files()

    elif any(word in instruction for word in (
        "list", "show", "display",
    )):
        list_files()

    elif any(word in instruction for word in (
        "organize", "organise", "sort files",
    )):
        organize_files()
        _, details = verify_organization()
        print("\nVerification:", details)

    else:
        print(
            "I couldn't match that instruction. "
            "Try asking me to list, count, or organize files."
        )


# ============================================================
# 8. AI AGENT
# ============================================================

def smart_agent(instruction):
    """Ask Groq to select an approved file-management tool."""
    print("\n" + "=" * 50)
    print("USER INSTRUCTION:", instruction)
    print("=" * 50)

    try:
        response = get_client().chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI file management agent. "
                        "Use list_files to list files, count_files "
                        "to count files, and organize_files to "
                        "organize supported files. Do not claim an "
                        "action succeeded before its execution. "
                        "Use only the approved tools."
                    ),
                },
                {"role": "user", "content": instruction},
            ],
            tools=tools,
            tool_choice="auto",
            max_completion_tokens=300,
        )

    except Exception as error:
        print("\n⚠️ Groq API unavailable.")
        print("Reason:", str(error)[:250])
        local_agent(instruction)
        return

    message = response.choices[0].message

    if not message.tool_calls:
        print(
            "\n🤖 AI:",
            message.content or "Please enter a file-management instruction.",
        )
        return

    for tool_call in message.tool_calls:
        function_name = tool_call.function.name

        if function_name not in available_functions:
            print("warning Unknown tool requested:", function_name)
            continue

        print("\n🔧 AI selected tool:", function_name)

        try:
            output = StringIO()

            with redirect_stdout(output):
                available_functions[function_name]()

            captured_output = output.getvalue()

            if captured_output:
                print(captured_output, end="")

            if function_name == "count_files":
                print("🔍 Local verification:", get_actual_counts())

            elif function_name == "list_files":
                print("🔍 Workspace checked:", SOURCE_FOLDER.exists())

            elif function_name == "organize_files":
                _, details = verify_organization()
                print("🔍 Verification:", details)

        except Exception as error:
            print(" Tool execution failed:", str(error))


# ============================================================
# 9. INTERACTIVE COMMAND LOOP
# ============================================================

def main():
    """Start the interactive agent."""
    ensure_workspace()

    print("AI File Management Agent is ready!")
    print("Workspace:", SOURCE_FOLDER)
    print("\nExamples:")
    print("- List my files")
    print("- How many files are in each category?")
    print("- Organize my files")
    print("- Type exit to stop the agent")

    while True:
        try:
            instruction = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAgent stopped. Goodbye!")
            break

        if instruction.lower() in ("exit", "quit", "stop"):
            print("Agent stopped. Goodbye!")
            break

        if not instruction:
            print("Please enter an instruction.")
            continue

        smart_agent(instruction)


if __name__ == "__main__":
    main()
