# AI File Management Agent

An AI-powered file management agent built using Python and the Groq API.

## Features

- Lists files and folders in the workspace.
- Counts files in different categories.
- Organizes supported files into category folders.
- Preserves unsupported files.
- Avoids overwriting existing files.
- Uses the Groq API to interpret user instructions.
- Includes a local fallback when the API is unavailable.

## Technologies Used

- Python
- Groq API
- pathlib
- os
- shutil

## Project Structure

```text
ai-file-management-agent/
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
└── tests/
    └── test_file_manager.py
```

## Installation

Install the required dependency:

```bash
pip install -r requirements.txt
```

## API Key Setup

Set the `GROQ_API_KEY` environment variable before running the agent.

Never publish your API key on GitHub.

## Run the Project

```bash
python main.py
```

Example instructions:

- List my files
- How many files are in each category?
- Organize my files
- Type `exit` to stop the agent

## Testing

Run the automated tests with:

```bash
python -m pytest -v
```

## Safety

Test the agent with sample files before using it on important data. The agent moves files into category folders.

## License

This project is available for educational and portfolio purposes.
