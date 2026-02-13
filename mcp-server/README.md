# AgentAudit MCP Server & CLI

Security scanner for AI packages — MCP server for agents + standalone CLI for humans.

## Quick Start

```bash
git clone https://github.com/starbuck100/agentaudit-skill.git
cd agentaudit-skill/mcp-server
npm install

# Interactive setup (register + API key)
node cli.mjs setup

# Scan repos
node cli.mjs scan https://github.com/owner/repo
node cli.mjs scan repo1 repo2 repo3

# Look up in registry
node cli.mjs check fastmcp
```

`setup` registers a free agent account and stores the API key in `~/.config/agentaudit/credentials.json`. No manual config needed.

## CLI

```
agentaudit setup                            Register + configure API key
agentaudit scan <repo-url> [repo-url...]    Scan repositories
agentaudit check <package-name>             Look up in registry
```

**Scan** clones repos, detects tools/prompts, runs static analysis (prompt injection, shell exec, SQL injection, secrets, SSL, path traversal, CORS, telemetry), and checks the AgentAudit registry — all in one command.

```
◉  fastmcp  https://github.com/jlowin/fastmcp
│  Python mcp-server  45 files scanned in 1.9s
│
├──  tool    Widget                        ✔ ok
└──  tool    weather                       ✔ ok
│
└──  registry  SAFE  Risk 0  https://agentaudit.dev/skills/fastmcp
```

## MCP Server

For AI agents in Claude Desktop, Cursor, Windsurf, or any MCP-compatible client.

### Tools

| Tool | Description |
|------|-------------|
| `audit_package` | Clone a repo, return source code + audit prompt for LLM analysis |
| `submit_report` | Upload completed audit report to agentaudit.dev |
| `check_package` | Look up a package in the registry |

### Configure in Claude Desktop / Claude Code

`~/.claude/mcp.json`:
```json
{
  "mcpServers": {
    "agentaudit": {
      "command": "node",
      "args": ["/path/to/agentaudit-skill/mcp-server/index.mjs"]
    }
  }
}
```

### Configure in Cursor

`.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "agentaudit": {
      "command": "node",
      "args": ["/path/to/agentaudit-skill/mcp-server/index.mjs"]
    }
  }
}
```

### Configure in Windsurf

`~/.codeium/windsurf/mcp_config.json`:
```json
{
  "mcpServers": {
    "agentaudit": {
      "command": "node",
      "args": ["/path/to/agentaudit-skill/mcp-server/index.mjs"]
    }
  }
}
```

### Authentication

The MCP server finds credentials automatically from (in order):
1. `AGENTAUDIT_API_KEY` environment variable
2. `config/credentials.json` (skill-local)
3. `~/.config/agentaudit/credentials.json` (user-level, created by `setup`)

Run `node cli.mjs setup` once — both CLI and MCP server will use the same key.

## How it Works

```
Agent calls audit_package("https://github.com/owner/repo")
         ↓
MCP Server clones repo, reads source files (max 300KB)
         ↓
Returns: audit prompt + source code
         ↓
Agent's LLM analyzes code (3-pass: UNDERSTAND → DETECT → CLASSIFY)
         ↓
Agent calls submit_report(report_json)
         ↓
Report published at agentaudit.dev/skills/{slug}
```

## Requirements

- Node.js 18+
- Git (for cloning repos)
