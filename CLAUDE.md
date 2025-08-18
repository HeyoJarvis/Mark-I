# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HeyJarvis is an AI agent orchestration system for automated task creation. The system allows users to create AI agents through natural language conversations and deploys them in secure Docker containers.

**Core Location**: All main code is in the `JarvisAlive/` directory.

## Development Commands

### Installation & Setup
```bash
# Install dependencies
cd JarvisAlive
pip install -r requirements.txt

# Alternative with virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Main interactive mode
python main.py

# Demo mode (shows all features)
python main.py --demo
```

### Testing
```bash
# Run tests with coverage
python tests/run_tests.py

# Run specific tests
pytest tests/test_jarvis_integration.py
pytest -v tests/

# Run single test file
pytest tests/test_lead_scanner.py -v
```

### Code Quality (from pyproject.toml)
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8

# Type checking
mypy .
```

### Infrastructure
```bash
# Start Redis (required dependency)
docker run -d --name redis -p 6379:6379 redis:latest

# Using Docker Compose
docker-compose up -d
```

## Architecture

### Core Components

**Orchestration Layer** (`orchestration/`):
- `jarvis.py` - Meta-orchestrator providing business-level coordination
- `orchestrator.py` - LangGraph-based orchestration engine using StateGraph
- `state.py` - Shared state management between orchestrators

**Agent Building** (`agent_builder/`):
- `code_generator.py` - LLM-powered code generation for agents
- `agent_spec.py` - Agent specification and creation functions
- `sandbox.py` - Secure Docker container execution environment

**AI Engines** (`ai_engines/`):
- `anthropic_engine.py` - Claude API integration
- `base_engine.py` - Abstract base for AI providers
- `mock_engine.py` - Testing implementation

**Conversation Management** (`conversation/`):
- `websocket_handler.py` - Real-time communication handling
- `jarvis_conversation_manager.py` - Session and context management

**Department Structure** (`departments/`):
- Business-specific agent collections (e.g., `sales/`)
- Pre-built agent templates and workflows

### Key Design Patterns

- **Dual Orchestration**: Jarvis (business layer) wraps HeyJarvisOrchestrator (technical layer)
- **LangGraph Integration**: State-driven agent workflows using LangGraph StateGraph
- **Docker Sandboxing**: All agent execution in isolated containers
- **Redis Sessions**: Persistent conversation and state storage
- **Template System**: Jinja2-based agent code templates (`templates/`)

### Dependencies

- **Core**: LangGraph 0.2.16, LangChain 0.2.16, Anthropic Claude API
- **Infrastructure**: Redis, Docker, FastAPI
- **Data**: Pydantic for validation, Rich for CLI interface
- **Logo Generation**: OpenAI DALL-E integration for branding features

## Development Notes

- **Python Version**: Requires 3.11+ (specified in QUICKSTART.md)
- **Environment**: Uses `.env` files for configuration
- **Testing**: pytest with asyncio support for async components
- **Logging**: Structured logging with configurable levels
- **Entry Point**: Always work from `JarvisAlive/` directory
- **API Keys**: Anthropic API key required in environment