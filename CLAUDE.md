# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This repository has two distinct purposes:

1. **Leaked Claude Code source** (`src/`) — the full TypeScript/React source code of Anthropic's Claude Code CLI, accidentally exposed via an npm sourcemap. This is archived here for educational and research purposes only. It is NOT an official Anthropic product and cannot be built without the internal Anthropic toolchain.

2. **Valley of the Sun Moving LLC website** (`index.html`, `nginx.conf`, `deploy.sh`, `setup.sh`) — a standalone static HTML business website deployed to a Hostinger VPS.

---

## Valley of the Sun Moving Website

### Deployment

**GitHub Actions (automatic):** Push to `main` triggers `.github/workflows/deploy.yml`, which deploys `index.html` and `nginx.conf` to the configured Hostinger VPS.

**Manual one-command install (run on VPS):**
```bash
curl -fsSL https://raw.githubusercontent.com/rmaviswholesale-create/claude-code/main/setup.sh | bash
```

**Manual deploy (if already on VPS):**
```bash
bash deploy.sh
```

The site files are:
- `index.html` — single-page static site for the moving company
- `nginx.conf` — nginx server config (serves from `/var/www/valleyofthesunmoving`)
- `scripts/` — Python helpers for the Hostinger API (register/attach/cleanup SSH keys)

---

## Claude Code Source Architecture (`src/`)

> Note: This source cannot be built or run here — it requires Bun with internal Anthropic build tooling. The notes below are for reading and understanding the code.

### Entry Point & Core Loop

- **`src/main.tsx`** — CLI entry point. Uses Commander.js to parse CLI flags and React/Ink to render the terminal UI. Fires parallel startup prefetches (keychain, MDM settings, GrowthBook) before imports settle.
- **`src/QueryEngine.ts`** — Owns the multi-turn LLM conversation loop. Calls `src/query.ts` for each API request, dispatches tool calls, handles retries, compact (context compression), and streaming.
- **`src/query.ts`** — Single-turn API call layer. Invokes `@anthropic-ai/sdk`, handles token budget, auto-compact, and tool result routing.

### Tool System

- **`src/Tool.ts`** — Base types: `Tool`, `Tools`, `ToolUseContext`, `CanUseToolFn`, permission result types.
- **`src/tools.ts`** — Tool registry. Assembles the active tool list; conditionally includes ant-only tools (`REPLTool`, `SuggestBackgroundPRTool`) and feature-flagged tools (KAIROS, AGENT_TRIGGERS, MONITOR_TOOL, etc.) using `feature()` and `process.env.USER_TYPE`.
- **`src/tools/*/`** — One directory per tool. Each tool directory contains the tool implementation (`.tsx`), a `prompt.ts` for the tool's schema/description, and UI components. Key tools:
  - `BashTool` — shell execution with sandboxing, read-only validation, sed/destructive-command checks
  - `AgentTool` — spawns sub-agents; supports built-in, custom, and in-process teammates
  - `FileReadTool`, `FileEditTool`, `FileWriteTool`, `GlobTool`, `GrepTool` — file operations
  - `WebFetchTool`, `WebSearchTool` — web access
  - `SkillTool` — invokes registered skills (slash-command extensions)
  - `MCPTool` — bridges to MCP server tools
  - `TaskCreateTool`, `TaskGetTool`, `TaskListTool`, etc. — background task management
  - `SendMessageTool` — leader↔teammate messaging in swarm mode

### Feature Flags

Feature flags use `feature('FLAG_NAME')` from `bun:bundle`. At build time, Bun constant-folds these and dead-code-eliminates the gated branches. Active flags include:
- `COORDINATOR_MODE` — multi-agent coordinator/worker topology
- `KAIROS` — proactive "always-on" assistant mode
- `KAIROS_DREAM` / `KAIROS_PUSH_NOTIFICATION` / `KAIROS_GITHUB_WEBHOOKS`
- `AGENT_TRIGGERS` / `AGENT_TRIGGERS_REMOTE` — cron and remote trigger tools
- `MONITOR_TOOL`, `REACTIVE_COMPACT`, `CONTEXT_COLLAPSE`, `PROACTIVE`, `TEAMMEM`

### Global State

**`src/bootstrap/state.ts`** — Singleton module holding session-wide mutable state (cwd, cost totals, telemetry providers, session ID, KAIROS flag, etc.). The comment "DO NOT ADD MORE STATE HERE" reflects intentional discipline. State is accessed via named exports (`getOriginalCwd`, `getSessionId`, `getKairosActive`, etc.).

### Memory System

**`src/memdir/`** — File-based persistent memory. `MEMORY.md` is the entry-point file (max 200 lines / 25 KB). The `memdir.ts` module builds the memory prompt injected into the system prompt each turn. Auto-memory paths are configurable via `CLAUDE_AUTO_MEM_PATH`.

### Multi-Agent / Swarm

- **`src/utils/swarm/`** — In-process teammate spawning, permission bridging between leader and workers, layout management for multi-pane display, and reconnection logic.
- **`src/coordinator/coordinatorMode.ts`** — Coordinator mode: a leader Claude instance delegates subtasks to worker instances. Enabled via `CLAUDE_CODE_COORDINATOR_MODE=1` (requires `COORDINATOR_MODE` feature flag).
- **`src/tasks/InProcessTeammateTask/`** — Tracks in-process teammate state.
- **`src/tasks/RemoteAgentTask/`** — Tracks async remote agent tasks.

### Services

- **`src/services/mcp/client.ts`** — MCP client supporting stdio, SSE, and StreamableHTTP transports via `@modelcontextprotocol/sdk`.
- **`src/services/analytics/`** — GrowthBook (feature flags/experiments) + Statsig gates + Datadog + first-party event logging. `growthbook.ts` manages the GrowthBook client; `_CACHED_MAY_BE_STALE` suffix on helpers signals they may return stale values.
- **`src/services/compact/`** — Auto-compact: compresses conversation history when near token limits. Includes reactive and micro-compact variants.
- **`src/services/autoDream/`** — Background memory consolidation service. Runs after enough sessions accumulate since the last consolidation; fires a forked sub-agent to read/consolidate/prune `MEMORY.md`.
- **`src/services/oauth/`** — OAuth flows for claude.ai authentication.
- **`src/services/lsp/`** — LSP (Language Server Protocol) integration.
- **`src/services/plugins/`** — Plugin marketplace install/update lifecycle.

### Bridge (IDE Integration)

**`src/bridge/`** — Connects Claude Code to IDE extensions (VS Code, JetBrains). The bridge runs as a long-lived polling connection to a remote API (`bridgeApi.ts`), relays messages between the IDE and the REPL (`replBridge.ts`), and handles session creation and JWT auth (`jwtUtils.ts`).

### Skills

**`src/skills/bundled/`** — Slash-command extensions shipped with the CLI. Each skill is registered at startup via `initBundledSkills()`. Bundled skills include: `updateConfig`, `keybindings`, `verify`, `debug`, `simplify`, `remember`, `batch`, `stuck`, and conditionally `dream` (KAIROS/KAIROS_DREAM gate). To add a bundled skill: create `src/skills/bundled/myskill.ts`, export a `registerMySkill()` function calling `registerBundledSkill()`, then import and call it from `src/skills/bundled/index.ts`.

### Slash Commands

**`src/commands/`** — 100+ slash commands, each in its own subdirectory. `src/commands.ts` assembles the command list and filters for remote mode. Commands are invoked via `SkillTool` or directly from `processSlashCommand`.

### Undercover Mode

**`src/utils/undercover.ts`** — Ant-only (Anthropic-employee) feature. Prevents leaking internal model codenames, project names, or unreleased version numbers into public commits/PRs. Automatically activates unless the git remote is on an internal allowlist. Dead-code-eliminated from external builds via `process.env.USER_TYPE === 'ant'`.

### Companion ("Buddy") System

**`src/buddy/`** — A Tamagotchi-style terminal companion. Species and stats are deterministically derived from `userId` via a Mulberry32 PRNG (`mulberry32` seeded with `hashString(userId)`). 18 species across 5 rarities (Common → Legendary). Stats include `DEBUGGING`, `CHAOS`, `SNARK`, etc.

### UI Rendering

Claude Code uses **React + [Ink](https://github.com/vadimdemedes/ink)** to render a rich terminal UI. `src/ink/` contains the Ink component layer, layout engine (yoga-layout), terminal I/O, and event hooks. `src/components/` holds higher-level UI components (PromptInput, StructuredDiff, Settings dialogs, etc.).
