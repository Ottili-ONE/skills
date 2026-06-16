---
name: cursor-cli
version: "2.1.0"
description: Use when automating or invoking Cursor CLI (agent/cursor-agent) for non-interactive tasks, CI pipelines, or multi-agent delegation.
category: dev-tools
author: Pushpinder Pal Singh
license: MIT
compatibility:
  - Claude Code
  - Codex
  - Cursor
  - OpenClaw
  - Ottili AI
---

# Cursor CLI Agent Skill

Guide for Cursor CLI (`agent` / `cursor-agent`) including installation, authentication, non-interactive mode, and automation patterns.

## Installation

### Standard (macOS, Linux, Windows WSL)

```bash
curl https://cursor.com/install -fsS | bash
```

### Homebrew (macOS)

```bash
brew install --cask cursor-cli
```

### After installation

Add to PATH if needed:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Verify:

```bash
agent --version
# or
cursor-agent --version
```

## Authentication

Browser login:

```bash
agent login
```

Or API key:

```bash
export CURSOR_API_KEY=your_api_key_here
```

## Update

```bash
agent update
# or
agent upgrade
```

## Commands

### Interactive

```bash
agent
agent "Add error handling to this API"
```

Backward compatible: `cursor-agent` works the same way.

### Model selection

```bash
agent models
agent --model gpt-5
```

During session: `/models`

### Sessions

- List: `agent ls`
- Resume last: `agent resume`
- Specific: `agent --resume="[chat-id]"`

### Context (files/folders)

```
@filename.ts
@src/components/
```

### Slash commands (interactive)

- `/models` – switch model
- `/compress` – summarize conversation
- `/rules` – create or edit rules
- `/commands` – custom commands
- `/mcp enable [server-name]` / `/mcp disable [server-name]`

### Non-interactive / CI mode

For scripts and automation, prefer print mode:

```bash
agent -p 'Run tests and report coverage'
agent -p 'Refactor this file to use async/await'
```

Output formats:

```bash
agent -p 'Analyze code' --output-format text
agent -p 'Find bugs' --output-format json
agent -p 'Run tests' --output-format stream-json --stream-partial-output
```

Force edits without confirmation:

```bash
agent -p 'Fix all linting errors' --force
```

Media input:

```bash
agent -p 'Analyze this screenshot: screenshot.png'
```

## Automation from other agents

When calling Cursor CLI from another agent or script, use **print mode** (`-p` / `--print`) with `--output-format text` or `json`. Print mode does not require an interactive TTY.

Example for delegation:

```bash
cursor-agent --model auto -p "Review auth middleware for security issues" --output-format text
```

For interactive TUI workflows in headless environments, use tmux to provide a PTY:

```bash
tmux new-session -d -s cursor
tmux send-keys -t cursor "cd /path/to/project" Enter
tmux send-keys -t cursor "agent 'Your task here'" Enter
sleep 60
tmux capture-pane -t cursor -p -S -100
```

## Rules and configuration

The agent loads automatically:

- `.cursor/rules`
- `AGENTS.md`
- `CLAUDE.md`

Use `/rules` to manage rules inside the CLI.

## MCP integration

MCP servers come from `mcp.json`. Enable or disable during a session:

```
/mcp enable server-name
/mcp disable server-name
```

## Common workflows

### Code review

```bash
agent -p 'Review the changes in the current branch against main. Focus on security and performance.'
```

### Refactoring

```bash
agent -p 'Refactor src/utils.ts to reduce complexity and improve type safety.'
```

### Git commit message

```bash
agent -p 'Generate a commit message for the staged changes adhering to conventional commits.'
```

### CI/CD

```bash
export CURSOR_API_KEY=$CURSOR_API_KEY
agent -p 'Audit this codebase for security vulnerabilities' --output-format json --force
```

## Multi-agent delegation

When used with `work-untill-i-die`, Cursor is typically the `grunt` role for fast, cheap iteration:

```bash
cursor-agent -p "<self-contained brief>" --model auto --output-format json
```

Add `--force` only when the delegate must modify files. Default to read-only delegation when possible.
