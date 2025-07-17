from dotenv import load_dotenv
load_dotenv()

import os
import subprocess
import typer
import re
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Import langchain modules for use throughout the module
import langchain.prompts
import langchain.schema

app = typer.Typer(help="G-Wave: A simplified, more robust AI agent.")

# --- Workspace Configuration ---
WORKSPACE_DIR = "g_wave_workspace"

# --- Agent Initialization ---
gemini = ChatGoogleGenerativeAI(model="gemini-2.5-pro", api_key=os.getenv("GEMINI_API_KEY"))
claude = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=os.getenv("CLAUDE_API_KEY"))
try:
    grok = ChatOpenAI(model="grok-2-1212", base_url="https://api.x.ai/v1", api_key=os.getenv("XAI_API_KEY"))
except Exception as e:
    print(f"⚠️ Grok initialization failed: {e}. Using Claude as fallback for planning")
    grok = claude
kimi = ChatOpenAI(model="moonshot-v1-8k", base_url="https://api.moonshot.ai/v1", api_key=os.getenv("MOONSHOT_API_KEY"))

# --- Agentic Tools ---
def list_files(path: str = '.', directory: str = None) -> str:
    """Lists files in the specified directory."""
    safe_path = path or directory or '.'
    # If the path doesn't exist, default to current directory
    if not os.path.exists(safe_path):
        safe_path = '.'
    try:
        files = os.listdir(safe_path)
        return "\n".join(files) if files else "No files in directory."
    except Exception as e:
        return f"Error listing files: {e}"

def read_file(filename: str) -> str:
    """Reads the content of a file."""
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def save_file(filename: str = None, file_name: str = None, path: str = None, file_path: str = None, code: str = None, content: str = None) -> str:
    """Saves or overwrites a file. Can access files outside workspace if absolute path is provided."""
    filepath = filename or file_name or path or file_path
    file_content = code or content
    if not filepath:
        return "Error: No filename provided."
    if not file_content or file_content.isspace():
        return "Error: Attempted to save empty content. Aborting."
    try:
        # Allow absolute paths for files outside workspace
        if os.path.isabs(filepath):
            safe_path = Path(filepath)
        elif not filepath.startswith(WORKSPACE_DIR):
            # Default to workspace for relative paths
            safe_path = Path(WORKSPACE_DIR) / filepath
        else:
            safe_path = Path(filepath)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        with open(safe_path, "w") as f:
            f.write(file_content)
        return f"Successfully saved code to {safe_path}"
    except Exception as e:
        return f"Error saving file: {e}"

def replace_in_file(filename: str, old_code: str, new_code: str) -> str:
    """Replaces a specific block of code in a file. Can access files outside workspace if absolute path is provided."""
    try:
        # Allow absolute paths for files outside workspace
        if os.path.isabs(filename):
            safe_path = Path(filename)
        elif not filename.startswith(WORKSPACE_DIR):
            # Default to workspace for relative paths
            safe_path = Path(WORKSPACE_DIR) / filename
        else:
            safe_path = Path(filename)
            
        with open(safe_path, "r") as f:
            content = f.read()
        if old_code not in content:
            return f"Error: The specified 'old_code' was not found in {safe_path}."
        
        new_content = content.replace(old_code, new_code)
        
        with open(safe_path, "w") as f:
            f.write(new_content)
        return f"Successfully replaced code in {safe_path}."
    except Exception as e:
        return f"Error replacing code in file: {e}"

def finish(reason: str) -> str:
    """Signals that the task is complete."""
    return f"Task finished: {reason}"

def run_command(command: str) -> str:
    """Executes a shell command."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return f"Error executing command: {e}"

TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "save_file": save_file,
    "replace_in_file": replace_in_file,
    "run_command": run_command,
    "finish": finish,
}

# --- New, Simplified Orchestrator ---
def run_agent_loop(task: str, max_loops: int = 20, is_self_improvement=False, original_task=""):
    """Runs the stateful agent loop with a self-improvement mechanism."""
    
    state = {"task": task, "history": [], "files_content": {}}

    for i in range(max_loops):
        print(f"\n\n==================== LOOP {i+1}/{max_loops} ====================")
        
        # --- Display Current State ---
        print(">> Reviewing current state...")
        history_log = "\n".join(f"  - {h}" for h in state['history']) if state['history'] else "  - No actions taken yet."
        print(f"History:\n{history_log}")
        if state['files_content']:
            print("\nKnown File Contents:")
            for filename, content in state['files_content'].items():
                print(f"  --- {filename} ---")
                print(f"  {content[:200]}..." if len(content) > 200 else content)
                print(f"  --------------------")
        print("======================================================")
        
        action_str = ""
        try:
            print("\n>> Planning next action...")
            # Step 1: Plan - Grok decides the next step
            plan_prompt_template = """
You are a master planner. Your primary directive is to fulfill the user's task by breaking it down into small, incremental steps.
**Focus only on the single next best action to take.** Do not plan multiple steps ahead.
Your available tools are: {tool_names}.
Based on the current state, what is the single next best action to take?

Task: {task}
History: {history}
File Contents: {files_content}

Decision:
"""
            plan_prompt = langchain.prompts.PromptTemplate.from_template(plan_prompt_template)
            planner_chain = plan_prompt | grok | langchain.schema.StrOutputParser()
            next_step = planner_chain.invoke({
                "task": state["task"],
                "history": "\n".join(state["history"]) or "No history yet.",
                "files_content": state["files_content"] or "No files read yet.",
                "tool_names": ", ".join(TOOLS.keys())
            })
            print(f"Grok's Plan: {next_step}")

            # Step 2: Implement (if coding is the next step)
            implementation = ""
            if "replace_in_file" in next_step.lower() or "save_file" in next_step.lower():
                impl_prompt_template = """
You are a world-class programmer. Your task is to generate the code for a file based on a plan.
If the plan is to modify an existing file, you must output the entire, final version of the file.
Output ONLY the raw code, with no commentary or markdown.

Plan: {plan}
Existing File Contents (for context): {files_content}

Generate the complete code for the file now.
"""
                impl_prompt = langchain.prompts.PromptTemplate.from_template(impl_prompt_template)
                
                # --- Coder chain with fallback ---
                try:
                    print(">> Gemini attempting to generate code...")
                    coder_chain = impl_prompt | gemini | langchain.schema.StrOutputParser()
                    implementation = coder_chain.invoke({
                        "plan": next_step,
                        "files_content": state["files_content"] or "N/A"
                    })
                except Exception as e:
                    print(f"Gemini failed: {e}. Falling back to Claude.")
                    coder_chain = impl_prompt | claude | langchain.schema.StrOutputParser()
                    implementation = coder_chain.invoke({
                        "plan": next_step,
                        "files_content": state["files_content"] or "N/A"
                    })

                implementation = re.sub(r"```python\n(.*?)\n```", r"\1", implementation, flags=re.DOTALL).strip()
                print(f"Generated Code:\n{implementation}")

            # Step 3: Act - Kimi chooses and formats the tool call
            action_prompt_template = """
You are an action agent. Your job is to convert the plan into a single, specific tool call.
Your available tools are: {tool_list}.
Output ONLY the action in the format: TOOL_NAME|key1=value1|key2=value2.
If using 'replace_in_file', the 'new_code' value is provided separately. You must specify the 'filename' and 'old_code'.

Plan: {plan}

Action:
"""
            action_prompt = langchain.prompts.PromptTemplate.from_template(action_prompt_template)
            action_chain = action_prompt | kimi | langchain.schema.StrOutputParser()
            action_str = action_chain.invoke({
                "plan": next_step,
                "tool_list": str(list(TOOLS.keys()))
            })
            print(f"Kimi's Action: {action_str}")

            # --- Tool Execution ---
            if not action_str or '|' not in action_str:
                raise ValueError("Kimi failed to provide a valid action.")

            parts = action_str.strip().split('|')
            tool_name = parts[0]
            
            if tool_name == "finish":
                reason = "No reason given."
                if len(parts) > 1 and '=' in parts[1]:
                    reason = parts[1].split('=', 1)[1]
                print(f"\n=== Task Finished: {reason} ===")
                break

            if tool_name in TOOLS:
                args = {}
                for part in parts[1:]:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        args[key] = value
                    else:
                        # Handle positional arguments for specific tools
                        if tool_name == 'list_files':
                            args['path'] = part
                        elif tool_name == 'read_file':
                            args['filename'] = part
                        elif tool_name == 'run_command':
                            args['command'] = part

                # Parameter validation and correction
                if tool_name == "run_command":
                    # Remove invalid parameters
                    args = {k: v for k, v in args.items() if k in ['command']}
                    if 'command' not in args:
                        raise ValueError(f"run_command requires 'command' parameter")
                
                elif tool_name == "read_file":
                    # Ensure correct parameter name - handle multiple possible parameter names
                    if 'path' in args and 'filename' not in args:
                        args['filename'] = args.pop('path')
                    if 'file_path' in args and 'filename' not in args:
                        args['filename'] = args.pop('file_path')
                    if 'file' in args and 'filename' not in args:
                        args['filename'] = args.pop('file')
                    args = {k: v for k, v in args.items() if k in ['filename']}
                    if 'filename' not in args:
                        raise ValueError(f"read_file requires 'filename' parameter")
                    
                    # Handle cases where filename has a non-existent directory prefix
                    if 'filename' in args and not os.path.exists(args['filename']):
                        # Try removing directory prefixes like "project_directory/"
                        filename = args['filename']
                        if '/' in filename:
                            basename = os.path.basename(filename)
                            if os.path.exists(basename):
                                args['filename'] = basename
                
                elif tool_name == "save_file":
                    args['code'] = implementation
                    # Validate save_file parameters
                    valid_params = ['filename', 'file_name', 'path', 'file_path', 'code', 'content']
                    args = {k: v for k, v in args.items() if k in valid_params}
                
                elif tool_name == "replace_in_file":
                    args['new_code'] = implementation
                    # Validate replace_in_file parameters
                    valid_params = ['filename', 'old_code', 'new_code']
                    args = {k: v for k, v in args.items() if k in valid_params}
                    if 'filename' not in args or 'old_code' not in args:
                        raise ValueError(f"replace_in_file requires 'filename' and 'old_code' parameters")
                
                elif tool_name == "list_files":
                    # Validate list_files parameters
                    valid_params = ['path', 'directory']
                    args = {k: v for k, v in args.items() if k in valid_params}
                    
                    # Handle cases where path has a non-existent directory like "project_directory"
                    if 'path' in args and not os.path.exists(args['path']):
                        args['path'] = '.'
                    if 'directory' in args and not os.path.exists(args['directory']):
                        args['directory'] = '.'
                
                result = TOOLS[tool_name](**args)
                
                if tool_name == "read_file":
                    filename_key = next((k for k in ['filename', 'file', 'path', 'file_path'] if k in args), None)
                    if filename_key:
                        state["files_content"][args[filename_key]] = result

                state["history"].append(f"Action: {action_str}, Result: {result}")
                print(f"Action Result: {result}")
            else:
                raise ValueError(f"Tool '{tool_name}' not found.")

        except Exception as e:
            print(f"\n--- AGENT ERROR ---")
            print(f"An error occurred: {e}")
            state["history"].append(f"Action failed with error: {e}")

            if is_self_improvement:
                print("Self-improvement loop failed. Aborting to prevent recursion.")
                break

            print(">> Initiating self-improvement loop...")
            self_improvement_task = (
                f"The agent failed to complete the original task: '{original_task}'.\n"
                f"The last attempted action was: '{action_str}'.\n"
                f"The error was: '{e}'.\n"
                f"Error context: This error occurred during tool execution.\n"
                f"Available tools and their required parameters:\n"
                f"- read_file(filename: str)\n"
                f"- save_file(filename: str, code: str)\n"
                f"- replace_in_file(filename: str, old_code: str, new_code: str)\n"
                f"- list_files(path: str = '.')\n"
                f"- run_command(command: str)\n"
                f"- finish(reason: str)\n\n"
                f"Analyze the history and the source code of 'g_wave/main.py' to identify the root cause. "
                f"Focus on parameter naming and tool execution logic. "
                f"You must use the 'replace_in_file' tool to fix the bug."
            )
            
            # --- Staging and Production Self-Healing ---
            # Find the current script file dynamically
            current_script = os.path.abspath(__file__)
            script_dir = os.path.dirname(current_script)
            prod_file = current_script
            staging_file = os.path.join(script_dir, "main_staging.py")
            
            # 1. Create a staging copy
            try:
                shutil.copy(prod_file, staging_file)
                print(f"✓ Created staging copy: {staging_file}")
            except Exception as copy_error:
                print(f"❌ Failed to create staging copy: {copy_error}")
                break
            
            # 2. Run the self-improvement loop on the staging file
            run_agent_loop(self_improvement_task, max_loops=3, is_self_improvement=True, original_task=original_task)
            
            # 3. Test the staging file
            print("\n>> Testing the staging file...")
            cmd = [sys.executable, staging_file, original_task]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    print("✔️ Staging test passed. Promoting to production.")
                    shutil.move(staging_file, prod_file)
                    print("✅ Self-improvement successful! Fixed code promoted to production.")
                else:
                    print(f"❌ Staging test failed. Discarding changes.\n--- Staging Output ---\n{result.stdout}\n--- Staging Error ---\n{result.stderr}")
                    if os.path.exists(staging_file):
                        os.remove(staging_file)
            except subprocess.TimeoutExpired:
                print("⏱️ Staging test timed out. Discarding changes to prevent infinite loops.")
                if os.path.exists(staging_file):
                    os.remove(staging_file)

            print(">> Self-improvement loop finished. Please retry the original task.")
            break
    else:
        print(f"\n--- Max loops reached ({max_loops}). Attempting to provide summary based on current progress. ---")
        
        # Try to provide a summary of what was accomplished
        if state['history']:
            print("\n>> Providing summary of analysis completed so far...")
            summary_prompt = f"""
Based on the actions taken so far, provide a comprehensive summary of what has been discovered about this project:

Task: {state['task']}
Actions completed: {len(state['history'])}
Files analyzed: {list(state['files_content'].keys())}

History of actions:
{chr(10).join(state['history'][-10:])}  # Last 10 actions

Please provide a detailed summary of findings and recommendations for next steps.
"""
            
            try:
                # Use the planner to create a summary (imports are at top of file)
                summary_template = langchain.prompts.PromptTemplate.from_template(summary_prompt)
                summary_chain = summary_template | grok | langchain.schema.StrOutputParser()
                summary = summary_chain.invoke({})
                print(f"\n📋 SUMMARY:\n{summary}")
            except Exception as e:
                print(f"\n📋 SUMMARY: Completed {len(state['history'])} actions. Analyzed {len(state['files_content'])} files. Task may need more time to complete fully.")
                print(f"Files analyzed: {', '.join(state['files_content'].keys())}")
        else:
            print("\n📋 No actions were completed. Task may need to be reformulated or simplified.")

@app.command()
def chat(
    task: str = typer.Argument(None, help="The task for the agent to perform."),
    max_loops: int = typer.Option(20, "--max-loops", "-l", help="Maximum number of loops (default: 20, increase for complex tasks)")
):
    """Interactive chat mode or single-task execution with the G-Wave agent."""
    if task:
        run_agent_loop(task, max_loops=max_loops, original_task=task)
    else:
        print("Welcome to G-Wave! I can read, write, and execute code across multiple steps.")
        print(f"Using max loops: {max_loops} (use --max-loops to adjust for complex tasks)")
        while True:
            task_input = input("> ")
            if task_input.lower() in ["exit", "quit"]:
                break
            if not task_input:
                continue
            
            run_agent_loop(task_input, max_loops=max_loops, original_task=task_input)

if __name__ == "__main__":
    app()
