# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

G-Wave is a multi-agent AI assistant built with Python that employs a sophisticated self-healing architecture. The system uses multiple Large Language Models (LLMs) with specialized roles for planning, coding, and action execution, with the unique ability to autonomously fix its own bugs.

## Installation and Setup

Install the project:
```bash
pip install -e .
```

Or install with dependencies:
```bash
pip install -r requirements.txt
```

## Core Commands

### Running the Agent
```bash
# Interactive mode
python -m g_wave.main

# Single task execution
python -m g_wave.main "your task here"

# Complex tasks with more loops
python -m g_wave.main "complex analysis task" --max-loops 30

# Alternative entry point
g_wave "your task here"

# With custom loop limit
g_wave "your task here" -l 25
```

### Development Commands
```bash
# Install in development mode
pip install -e .

# Run from source
python g_wave/main.py "task description"
```

## Architecture Overview

### Multi-Agent System
G-Wave operates using a stateful loop with three distinct LLM roles:

1. **Planner (Grok/Claude)**: Analyzes current state and determines the next high-level action
2. **Coder (Gemini/Claude)**: Generates code when `save_file` or `replace_in_file` operations are needed
3. **Actor (Kimi)**: Converts plans into precise tool calls

### Core State Management
- **State Dictionary**: Tracks `task`, `history`, and `files_content`
- **Workspace Restriction**: All file operations are restricted to `g_wave_workspace/` directory
- **Stateful Loop**: Maximum 20 iterations per task execution (increased for complex analysis tasks)

### Self-Healing Mechanism
The system includes an automated self-healing workflow:

1. **Error Detection**: Unhandled exceptions trigger self-healing mode
2. **Staging Environment**: Production code is copied to `g_wave/main_staging.py`
3. **Autonomous Fix**: Agent analyzes error and attempts repair in staging
4. **Testing**: Modified staging code is tested with the original failed task
5. **Promotion/Rollback**: Successful fixes are promoted to production, failures are discarded

## Available Tools

The agent has access to these tools:
- `list_files(path)`: Lists directory contents anywhere on the system
- `read_file(filename)`: Reads file content into agent state (supports absolute paths)
- `save_file(filename, code)`: Creates/overwrites files (use absolute paths for files outside workspace)
- `replace_in_file(filename, old_code, new_code)`: Replaces code blocks in files (supports absolute paths)
- `run_command(command)`: Executes shell commands
- `finish(reason)`: Terminates the operation

## File Structure

```
g_wave/
├── main.py              # Production agent code
├── main_staging.py      # Staging environment (created during self-healing)
├── main_production.py   # Alternative production version
├── prompts.py           # Prompt templates for different agent roles
└── __init__.py

g_wave_workspace/        # Restricted workspace for agent operations
├── requirements.txt     # Workspace-specific dependencies
└── [generated files]    # Agent-created files

pyproject.toml          # Project configuration and dependencies
requirements.txt        # Main project dependencies
```

## Key Configuration

### Environment Variables Required
- `GEMINI_API_KEY`: Google Gemini API key for coding tasks
- `CLAUDE_API_KEY`: Anthropic Claude API key (fallback for planning)
- `XAI_API_KEY`: X.AI Grok API key for planning tasks
- `MOONSHOT_API_KEY`: Moonshot Kimi API key for action execution

### Model Configuration
- **Planner**: Grok-beta (with Claude fallback)
- **Coder**: Gemini-2.5-pro (with Claude fallback)
- **Actor**: Moonshot-v1-8k

## Development Notes

### Known Issues
1. **Coder Prompt Bug**: The coder prompt always generates full file content, which can cause issues with `replace_in_file` operations
2. **Stale State**: File modifications don't update the internal `files_content` state
3. **Brittle String Matching**: `replace_in_file` relies on exact string matches

### Security Features
- **File Access**: Can access files outside workspace using absolute paths (e.g., `/Users/user/project/file.py`)
- **Default Workspace**: Relative paths default to `g_wave_workspace/` for safety
- Self-healing includes timeout protection to prevent infinite loops
- Staging environment ensures safe testing before production deployment

### Testing the System
The agent includes comprehensive error handling and fallback mechanisms. Test the self-healing by intentionally introducing errors and observing the automated recovery process.

## Deployment Considerations

The system is designed for local development and testing. The self-healing mechanism makes it particularly suitable for experimental and iterative development workflows where the agent can learn from its mistakes and improve over time.