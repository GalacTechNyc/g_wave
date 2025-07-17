# G-Wave: Multi-Agent AI Assistant with Self-Healing Capabilities

G-Wave is a sophisticated multi-agent AI assistant that combines multiple Large Language Models (LLMs) to create a robust, self-improving system capable of complex code analysis, generation, and task execution.

## 🚀 Key Features

### Multi-Agent Architecture
- **Planner Agent (Grok)**: Strategic task planning and decision-making
- **Coder Agent (Gemini/Claude)**: Code generation and implementation with fallback support
- **Actor Agent (Kimi)**: Tool execution and action coordination
- **Intelligent Fallbacks**: Automatic model switching when primary agents fail

### Self-Healing & Self-Improvement
- **Automatic Error Detection**: Identifies and analyzes failures in real-time
- **Staging Environment**: Safe testing of fixes before production deployment
- **Dynamic Self-Modification**: Rewrites its own code to fix bugs and improve performance
- **Rollback Protection**: Automatic reversion if fixes don't work

### Advanced Capabilities
- **External File Access**: Can read and write files outside the workspace using absolute paths
- **Configurable Loop Limits**: Adjustable execution limits (default: 20, up to custom values)
- **Comprehensive Error Handling**: Robust parameter validation and error recovery
- **Stateful Execution**: Maintains context across multiple operations
- **Intelligent Summarization**: Provides detailed summaries for incomplete tasks

## 📋 Supported AI Providers

- **Google Gemini** (gemini-2.5-pro) - Primary coder
- **Anthropic Claude** (claude-3-5-sonnet) - Fallback coder
- **xAI Grok** (grok-2-1212) - Strategic planner
- **Moonshot Kimi** (moonshot-v1-8k) - Action executor

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/GalacTechNyc/g_wave.git
   cd g_wave
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Install G-Wave**
   ```bash
   pip install -e .
   ```

## 🔧 Configuration

Create a `.env` file with your API keys:

```env
# Required: At least one AI provider
GEMINI_API_KEY="your_google_gemini_api_key"
CLAUDE_API_KEY="your_anthropic_claude_api_key"
XAI_API_KEY="your_xai_grok_api_key"
MOONSHOT_API_KEY="your_moonshot_kimi_api_key"
```

## 🎯 Usage

### Command Line Interface

**Basic usage:**
```bash
g_wave "analyze the codebase and create documentation"
```

**With custom loop limits:**
```bash
g_wave "perform detailed code review" --max-loops 30
```

**Interactive mode:**
```bash
g_wave
> analyze main.py for potential improvements
> create unit tests for the core functions
> exit
```

### Python Module

```python
from g_wave.main import run_agent_loop

# Execute a task
run_agent_loop("create a Python web scraper", max_loops=25)
```

## 🔍 Available Tools

G-Wave has access to these core tools:

- **`list_files`**: Directory listing and file discovery
- **`read_file`**: File content reading and analysis
- **`save_file`**: File creation and modification (workspace + external)
- **`replace_in_file`**: Targeted code replacement and refactoring
- **`run_command`**: Shell command execution
- **`finish`**: Task completion signaling

## 🎨 Example Use Cases

### Code Analysis & Documentation
```bash
g_wave "analyze this React project and create comprehensive documentation"
```

### Bug Fixing & Optimization
```bash
g_wave "find and fix performance issues in the database queries" -l 40
```

### Test Generation
```bash
g_wave "create unit tests for all functions in the utils module"
```

### External Project Integration
```bash
g_wave "analyze /path/to/external/project and suggest improvements"
```

## 🏗️ Architecture

### Multi-Agent Workflow
1. **Planning Phase**: Grok analyzes the task and determines the next action
2. **Implementation Phase**: Gemini/Claude generates code if needed
3. **Execution Phase**: Kimi executes the planned action using available tools
4. **Validation Phase**: Results are validated and state is updated
5. **Iteration**: Process repeats until task completion or loop limit

### Self-Healing Mechanism
```
Error Detected → Create Staging Copy → Self-Analyze → Generate Fix → Test Fix → Deploy or Rollback
```

### File Access Security
- **Workspace Default**: Relative paths default to `g_wave_workspace/`
- **External Access**: Absolute paths allow system-wide file operations
- **Path Validation**: Comprehensive path sanitization and validation

## 📊 Performance & Limits

- **Default Loop Limit**: 20 iterations
- **Maximum Recommended**: 50 iterations for complex tasks
- **Timeout Protection**: 2-minute timeout per operation
- **Memory Efficient**: Stateful execution with minimal memory footprint
- **Error Recovery**: Automatic retry with exponential backoff

## 🚨 Troubleshooting

### Common Issues

**API Key Errors:**
```bash
# Verify your .env file
cat .env
# Check API key validity
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GEMINI_API_KEY'))"
```

**Loop Limit Exceeded:**
```bash
# Increase loop limit for complex tasks
g_wave "complex task" --max-loops 50
```

**Permission Errors:**
```bash
# Check file permissions
ls -la g_wave_workspace/
# Ensure Python has write access
```

### Self-Healing Activation
If G-Wave encounters errors, it will:
1. Create a staging copy of itself
2. Analyze the error and generate a fix
3. Test the fix in staging
4. Deploy to production if successful
5. Rollback if the fix fails

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/GalacTechNyc/g_wave.git
cd g_wave
pip install -e ".[dev]"
```

### Running Tests
```bash
pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/) for LLM integration
- Uses [Typer](https://typer.tiangolo.com/) for CLI functionality
- Inspired by multi-agent AI research and self-improving systems

## 📚 Documentation

For detailed documentation, see [CLAUDE.md](CLAUDE.md) - comprehensive guide for Claude Code integration and advanced usage.

## 🌟 Features Roadmap

- [ ] Web interface for visual task management
- [ ] Plugin system for custom tools
- [ ] Distributed execution across multiple machines
- [ ] Advanced analytics and performance monitoring
- [ ] Integration with popular IDEs and editors

---

**Created with ❤️ by the G-Wave Team**

*G-Wave: Where AI agents collaborate to solve complex problems*