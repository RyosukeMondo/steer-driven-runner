# Steer-Driven Runner

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Autonomous AI development runner driven by steering documents. Transform high-level product specifications into working code through AI-powered autonomous development iterations.

## Overview

Steer-Driven Runner orchestrates AI agents (like Codex) to autonomously develop software based on steering documents (product.md, design.md, tech.md). It provides:

- **Autonomous Iterations**: AI reads steering docs, implements features, tests, and commits
- **Real-Time Monitoring**: Live dashboard showing progress, code metrics, and current tasks
- **Async Feedback**: Non-blocking human feedback injection during development
- **Circuit Breakers**: Automatic safeguards against infinite loops and failures
- **Checkpoints**: Periodic human review points for quality control

## Features

- 🤖 **AI-Driven Development**: Fully autonomous coding based on specifications
- 📊 **Live Monitoring**: Rich CLI dashboard with iteration progress and metrics
- 💬 **Async Feedback**: Post feedback anytime without blocking AI progress
- 🔄 **Circuit Breakers**: Automatic detection of no-progress situations
- ⚙️ **Configurable**: Customize iterations, checkpoints, models via CLI or env vars
- 🎯 **Steering-Driven**: Works from high-level documents or detailed task lists
- 📝 **Comprehensive Logging**: JSON structured logs + rich console output

## Installation

### ⚡ Global installation with uv (recommended)

```bash
# Ultra-fast: Install CLI tools globally
uv tool install git+https://github.com/RyosukeMondo/steer-driven-runner.git
```

This makes `steer-run`, `steer-monitor`, and `steer-feedback` available system-wide instantly!

### Using uv for development

```bash
# Clone the repository
git clone https://github.com/RyosukeMondo/steer-driven-runner.git
cd steer-driven-runner

# Install with uv
uv pip install -e .

# Or install with dev dependencies
uv pip install -e ".[dev]"
```

### Using pip

```bash
# Install from GitHub
pip install git+https://github.com/RyosukeMondo/steer-driven-runner.git

# Or from source
git clone https://github.com/RyosukeMondo/steer-driven-runner.git
cd steer-driven-runner
pip install -e .
```

## Quick Start

### 1. Initialize a Project

```bash
# In your project directory
steer-run init
```

This creates:
```
.spec-workflow/
├── steering/
│   ├── product.md   # Product specifications
│   ├── design.md    # Design specifications
│   └── tech.md      # Technical specifications
├── feedback/        # Async feedback system
└── monitor/         # Runtime state
```

### 2. Edit Steering Documents

Edit `.spec-workflow/steering/product.md` with your product vision:

```markdown
# Product Specification

## Vision
A todo app for visual thinkers with infinite canvas

## Features
- Visual task cards on 2D canvas
- Color-coded priorities
- Relationship lines between tasks
```

### 3. Run Autonomous Development

```bash
# Terminal 1: Run autonomous iterations
steer-run -i 50 -c 10

# Terminal 2: Monitor progress (optional)
steer-monitor
```

### 4. Post Feedback

```bash
# Post feedback while AI is running
steer-feedback "Add user authentication" --priority HIGH --type FEATURE

# Or just
steer-feedback "The canvas needs zoom controls"
```

## Usage

### CLI Commands

#### `steer-run` - Run Autonomous Development

```bash
steer-run [OPTIONS]

Options:
  -i, --iterations INTEGER   Maximum iterations (default: 50)
  -c, --checkpoint INTEGER   Checkpoint interval (default: 10)
  -s, --spec TEXT           Specification name (for task-driven mode)
  -m, --model TEXT          Codex model (default: gpt-5.1-codex)
  -p, --project-root PATH   Project root directory
  --help                    Show help message

Examples:
  steer-run                           # Run with defaults
  steer-run -i 100 -c 5              # 100 iterations, checkpoint every 5
  steer-run -m gpt-5.1-codex-max     # Use max model
  steer-run -s mvp-foundation        # Run specific spec
```

#### `steer-monitor` - Monitor Progress

```bash
steer-monitor [OPTIONS]

Options:
  -p, --project-root PATH   Project root directory
  -r, --refresh-rate FLOAT  Refresh rate in seconds (default: 2.0)
  --help                    Show help message

Examples:
  steer-monitor                 # Monitor current directory
  steer-monitor -r 1.0          # Refresh every second
```

#### `steer-feedback` - Post Feedback

```bash
steer-feedback MESSAGE [OPTIONS]

Options:
  -p, --priority [LOW|MEDIUM|HIGH|CRITICAL]     Priority (default: MEDIUM)
  -t, --type [FEEDBACK|BUG|FEATURE|IMPROVEMENT|VISUAL]  Type (default: FEEDBACK)
  --project-root PATH                           Project root directory
  --help                                        Show help message

Examples:
  steer-feedback "Web UI doesn't show database todos" --priority CRITICAL --type BUG
  steer-feedback "Add canvas zoom controls" --type FEATURE
```

#### `steer-run init` - Initialize Project

```bash
steer-run init [OPTIONS]

Options:
  -p, --project-root PATH   Project root directory
  --help                    Show help message
```

### Environment Variables

Configure via environment variables (prefix with `STEER_`):

```bash
# In .env file or export
STEER_MAX_ITERATIONS=100
STEER_CHECKPOINT_INTERVAL=10
STEER_CODEX_MODEL=gpt-5.1-codex-max
STEER_MAX_TOKENS=4000
STEER_TEMPERATURE=0.7
```

### Configuration

Create a `.env` file in your project root:

```env
# Runner settings
STEER_MAX_ITERATIONS=50
STEER_CHECKPOINT_INTERVAL=10

# AI settings
STEER_CODEX_MODEL=gpt-5.1-codex
STEER_MAX_TOKENS=4000
STEER_TEMPERATURE=0.7

# Circuit breakers
STEER_MAX_NO_PROGRESS=3
STEER_MAX_CONSECUTIVE_FAILURES=3
```

## How It Works

### Autonomous Loop

```
1. Read steering documents (product.md, design.md, tech.md)
2. Determine next task to implement
3. Write code
4. Run tests
5. Commit changes
6. Write state for monitoring
7. Check for feedback
8. Repeat until complete or max iterations
```

### Monitoring Dashboard

The monitor shows real-time:

```
┌─────────────────────────────────────────────────────┐
│    Steer-Driven Runner Monitor                     │
│    Status: RUNNING                                  │
└─────────────────────────────────────────────────────┘
┌──────────────────┬──────────────────────────────────┐
│ Iteration: 5/50  │                                  │
│ [████████░░░░░░] │                                  │
│ Progress: 10.0%  │        Recent Output             │
│                  │                                  │
│ Code Metrics     │  Running tests...                │
│ Lines: 12,345    │  All tests passed!               │
│ Files: 87        │  Committing changes...           │
│                  │                                  │
│ Current Task     │                                  │
│ Status:          │                                  │
│ in_progress      │                                  │
│                  │                                  │
│ Implementing     │                                  │
│ authentication   │                                  │
└──────────────────┴──────────────────────────────────┘
```

### Async Feedback System

The feedback system works like a mailbox:

1. **Human posts feedback**: `steer-feedback "message"`
2. **AI checks on next iteration**: Reads pending.md
3. **AI considers feedback**: Incorporates into planning
4. **Feedback archived**: Moved to archive/ after processing

**Benefits**:
- Non-blocking: AI doesn't wait
- Async: Post anytime, AI picks up next iteration
- Contextual: AI has full context when processing

## Architecture

```
steer-driven-runner/
├── src/steer_driven_runner/
│   ├── __init__.py         # Package initialization
│   ├── __main__.py         # python -m support
│   ├── cli.py              # Click CLI commands
│   ├── config.py           # Configuration (Pydantic)
│   ├── state.py            # State management
│   ├── runner.py           # Main autonomous loop
│   ├── monitor.py          # Real-time dashboard
│   └── feedback.py         # Feedback system
├── pyproject.toml          # Project metadata & deps
├── README.md               # This file
└── LICENSE                 # MIT License
```

## Development

### Setup Development Environment

```bash
# Clone and install with dev dependencies
git clone https://github.com/RyosukeMondo/steer-driven-runner.git
cd steer-driven-runner
uv pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=steer_driven_runner --cov-report=term-missing
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/
```

## Stopping the Runner

### Graceful Stop

Create a `stop.txt` file in your project root:

```bash
touch stop.txt
```

The runner will:
1. Complete the current iteration
2. Save state
3. Remove stop.txt
4. Exit gracefully

### Force Stop

Press `Ctrl+C` in the runner terminal.

## Circuit Breakers

The runner includes automatic safeguards:

### No Progress Circuit Breaker

Triggers if no git commits for 3 consecutive iterations:
- Prevents infinite loops
- Requires human intervention
- Logs last prompt for debugging

### Failure Circuit Breaker

Triggers after 3 consecutive failures:
- Escalates to human review
- Saves error state
- Provides troubleshooting info

## Troubleshooting

### "Codex command not found"

Install Codex CLI:
```bash
# Follow Codex installation instructions
```

### Monitor shows "Waiting for autonomous runner"

The runner hasn't started yet. Start it with:
```bash
steer-run
```

### "Steering documents not found"

Initialize your project:
```bash
steer-run init
```

### Feedback not being processed

Check if:
1. Feedback file exists: `.spec-workflow/feedback/pending.md`
2. Runner is actively running iterations
3. AI made commits (feedback archived only after commits)

## Examples

### Simple Project

```bash
# Initialize
mkdir my-app
cd my-app
steer-run init

# Edit .spec-workflow/steering/product.md
# (Add your product vision)

# Run
steer-run -i 30
```

### With Monitoring

```bash
# Terminal 1
steer-run -i 100 -c 10

# Terminal 2
steer-monitor
```

### With Feedback

```bash
# While runner is running, in another terminal:
steer-feedback "Add user login page" --priority HIGH --type FEATURE
steer-feedback "Tests are failing for API module" --priority CRITICAL --type BUG
```

## Roadmap

- [ ] Support for multiple AI backends (OpenAI, Anthropic, local models)
- [ ] Web UI for monitoring and feedback
- [ ] Spec templates library
- [ ] Collaborative multi-agent development
- [ ] Cost tracking and optimization
- [ ] Git branch strategies
- [ ] Docker support

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code quality (black, ruff, mypy)
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by autonomous AI development experiments
- Built with [Rich](https://github.com/Textualize/rich) for beautiful CLI
- Powered by [Click](https://click.palletsprojects.com/) for CLI framework
- Configuration via [Pydantic](https://pydantic.dev/)

## Links

- **Repository**: https://github.com/RyosukeMondo/steer-driven-runner
- **Issues**: https://github.com/RyosukeMondo/steer-driven-runner/issues
- **Author**: Ryosuke Mondo

---

Made with ❤️ by [Ryosuke Mondo](https://github.com/RyosukeMondo)
