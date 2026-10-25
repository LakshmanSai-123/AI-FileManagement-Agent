from pathlib import Path

project_code = r'''
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
    "Archives": [".zip", ".rar", ".7z"]
}

SOURCE_FOLDER.mkdir(parents=True, exist_ok=True)

for category in CATEGORIES:
    (SOURCE_FOLDER / category).mkdir(exist_ok=True)


def get_api_key():
    """Read the API key from Colab Secrets or an environment variable."""

    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        try:
            from google.colab import userdata
            api_key = userdata.get("Gen_AI")
        except (ImportError, Exception):
            api_key = None

    if not api_key:
        raise RuntimeError(
            "Groq API key not found. Configure GROQ_API_KEY "
            "or add Gen_AI to Google Colab Secrets."
        )

    return api_key


client = Groq(api_key=get_api_key())
MODEL = "openai/gpt-oss-20b"

print("AI File Management Agent is ready!")
print("Workspace:", SOURCE_FOLDER)


# ============================================================
# 2. TOOL 1: LIST FILES
# ============================================================

def list_files():
    """Display files and folders in the workspace."""

    print("\\nFILES AND FOLDERS")

    for item in sorted(SOURCE_FOLDER.iterdir()):
        if item.is_file():
            print(f"📄 {item.name}")
        else:
            print(f"📁 {item.name}/")

            for child in sorted(item.iterdir()):
                if child.is_file():
                    print(child.name)


# ============================================================
# 3. TOOL 2: COUNT FILES
# ============================================================

def get_actual_counts():
    """Count files in each category."""

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

    print("\\nFILE COUNT REPORT")

    total = 0

    for category, count in counts.items():
        print(f"{category}: {count}")
        total += count

    print(f"Total categorised files: {total}")

    return counts


# ============================================================
# 4. TOOL 3: ORGANIZE FILES
# ============================================================

def organize_files():
    """
    Organize supported files from the workspace root.
    Existing files are not overwritten.
    Unsupported files are left untouched.
    """

    moved = []
    skipped = []

    for item in list(SOURCE_FOLDER.iterdir()):

        if not item.is_file():
            continue

        extension = item.suffix.lower()
        destination_category = None

        for category, extensions in CATEGORIES.items():
            if extension in extensions:
                destination_category = category
                break

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

    print("\\nORGANIZATION REPORT")

    if moved:
        for item in moved:
            print("", item)
    else:
        print("No supported files needed moving.")

    if skipped:
        print("\\nSkipped files:")

        for item in skipped:
            print("", item)

    return moved, skipped


# Keep the original British spelling available for compatibility.
organise_files = organize_files


# ============================================================
# 5. TOOL VERIFICATION
# ============================================================

def verify_organization():
    """Check whether supported files remain in the root."""

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
            "Some supported files remain in the root: "
            + ", ".join(remaining)
        )

    return True, "All supported root files have been organized."


verify_organisation = verify_organization


# ============================================================
# 6. DEFINE TOOLS FOR THE AI MODEL
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
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "count_files",
            "description": "Count files in each category folder.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "organize_files",
            "description": (
                "Move supported files from the workspace root "
                "into category folders. Never overwrite files."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


available_functions = {
    "list_files": list_files,
    "count_files": count_files,
    "organize_files": organize_files
}


# ============================================================
# 7. LOCAL FALLBACK
# ============================================================

def local_agent(instruction):
    """Rule-based fallback that does not call the Groq API."""

    instruction = instruction.lower()

    print("\\n🛠️ Local fallback activated.")

    if any(word in instruction for word in [
        "count", "how many", "number of"
    ]):
        count_files()

    elif any(word in instruction for word in [
        "list", "show", "display"
    ]):
        list_files()

    elif any(word in instruction for word in [
        "organise", "organize", "sort files"
    ]):
        organize_files()

        success, details = verify_organization()
        print("\\nVerification:", details)

    else:
        print(
            "I couldn't match that instruction to a local rule. "
            "Try asking me to list, count, or organize files."
        )


# ============================================================
# 8. FINAL AI AGENT
# ============================================================

def smart_agent(instruction):

    print("\\n" + "=" * 50)
    print("USER INSTRUCTION:", instruction)
    print("=" * 50)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """
You are an AI file management agent.

Select the appropriate available tool.

Rules:
- Use list_files when the user wants to see files.
- Use count_files when the user asks about file counts.
- Use organize_files when the user asks to organize or sort files.
- Do not claim an action succeeded before it is executed.
- If no tool is appropriate, answer briefly.
- Never invent file counts or claim to access files outside
  the provided workspace.
"""
                },
                {
                    "role": "user",
                    "content": instruction
                }
            ],
            tools=tools,
            tool_choice="auto",
            max_completion_tokens=300
        )

    except Exception as error:
        print("\\n Groq API unavailable.")
        print("Reason:", str(error)[:250])
        local_agent(instruction)
        return

    message = response.choices[0].message

    if not message.tool_calls:
        print(
            "\\n AI:",
            message.content or
            "Please give me a file-management instruction."
        )
        return

    for tool_call in message.tool_calls:

        function_name = tool_call.function.name

        if function_name not in available_functions:
            print("Unknown tool requested:", function_name)
            continue

        print("\\n🔧 AI selected tool:", function_name)

        try:
            output = StringIO()

            with redirect_stdout(output):
                available_functions[function_name]()

            captured_output = output.getvalue()

            if captured_output:
                print(captured_output)

            if function_name == "count_files":
                print("🔍 Local verification:", get_actual_counts())

            elif function_name == "list_files":
                print("🔍 Workspace checked:", SOURCE_FOLDER.exists())

            elif function_name == "organize_files":
                success, details = verify_organization()
                print("🔍 Verification:", details)

                if not success:
                    print(
                        " Some supported files may need "
                        "another organization attempt."
                    )

        except Exception as error:
            print("Tool execution failed:", str(error))


# ============================================================
# 9. INTERACTIVE COMMAND LOOP
# ============================================================

def main():

    print("\\nExamples:")
    print("- List my files")
    print("- How many files are in each category?")
    print("- Organize my files")
    print("- exit to stop the agent")

    while True:

        try:
            user_instruction = input("\\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\\nAgent stopped. Goodbye!")
            break

        if user_instruction.lower() in ["exit", "quit", "stop"]:
            print("Agent stopped. Goodbye!")
            break

        if not user_instruction:
            print("Please enter an instruction.")
            continue

        smart_agent(user_instruction)


if __name__ == "__main__":
    main()
'''

Path("main.py").write_text(project_code.strip() + "\n", encoding="utf-8")

print("Created main.py")
print("File size:", Path("main.py").stat().st_size, "bytes")
