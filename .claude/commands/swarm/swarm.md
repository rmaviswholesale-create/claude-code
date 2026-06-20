# /swarm

Main swarm orchestration command for Claude Flow V3.

## 🚨 Background Execution Pattern

Spawn ALL agents in ONE message with `run_in_background: true`. Then **STOP AND WAIT** — agents are async; the runtime delivers results automatically. Don't poll, don't ask for status, don't call `swarm status` until all agents complete.

## ✅ Correct Spawn Pattern

```javascript
// All calls in ONE message — run_in_background: true on every Task()
Agent({ prompt: "Research...",   subagent_type: "researcher",  run_in_background: true })
Agent({ prompt: "Design...",     subagent_type: "architect",   run_in_background: true })
Agent({ prompt: "Implement...",  subagent_type: "coder",       run_in_background: true })
Agent({ prompt: "Test...",       subagent_type: "tester",      run_in_background: true })
Agent({ prompt: "Review...",     subagent_type: "reviewer",    run_in_background: true })
```

## 📊 Required Status Display

```
╔══════════════════════════════════════════════════════════════╗
║  🐝 SWARM LAUNCHED                                           ║
╠══════════════════════════════════════════════════════════════╣
║  📋 Task: [user's task description]                          ║
║  🔄 Topology: hierarchical  │  👥 Agents: 5/15               ║
╠══════════════════════════════════════════════════════════════╣
║  AGENT           │  STATUS     │  TASK                       ║
╠══════════════════════════════════════════════════════════════╣
║  🔍 Researcher   │  🟢 ACTIVE  │  Analyzing requirements     ║
║  🏗️ Architect    │  🟢 ACTIVE  │  Designing approach         ║
║  💻 Coder        │  🟢 ACTIVE  │  Implementing solution      ║
║  🧪 Tester       │  🟢 ACTIVE  │  Writing tests              ║
║  👀 Reviewer     │  🟢 ACTIVE  │  Code review & security     ║
╠══════════════════════════════════════════════════════════════╣
║  ⏳ Working in parallel... Results will arrive automatically ║
╚══════════════════════════════════════════════════════════════╝
```

## 📋 Agent Types by Task

See canonical routing table in `CLAUDE.md` → "Agent Routing". Quick reference:

| Task type | Agents |
|---|---|
| New Feature | researcher, architect, coder, tester, reviewer |
| Bug Fix | researcher, coder, tester |
| Refactor | architect, coder, reviewer |
| Security | security-architect, auditor, reviewer |
| Performance | researcher, perf-engineer, coder |
| Documentation | researcher, documenter |

## 🔧 Usage

```bash
cf=npx\ @claude-flow/cli@latest
$cf swarm init --topology hierarchical
$cf swarm status  # only after all agents complete
```

## ⚙️ Options

See full flag reference in [swarm-init.md](swarm-init.md). Common flags:

| Flag | Values | Default |
|---|---|---|
| `--strategy` | research, development, analysis | auto |
| `--topology` | hierarchical, mesh, ring, star | hierarchical |
| `--max-agents` | number | 15 |
