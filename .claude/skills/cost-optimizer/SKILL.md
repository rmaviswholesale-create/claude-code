---
name: cost-optimizer
description: |
  Reduce Claude API costs by 50-75% using Ruflo's smart model routing. Routes simple tasks to cheap/free models and complex tasks to Opus/Sonnet. Use when you want to control spending, set token budgets, or get a cost report across all agents.
---

# Cost Optimizer

## What This Skill Does

Routes tasks to the cheapest model that can handle them, tracks spend across all agents, and alerts you when budgets are hit. Works through Ruflo's built-in cost-tracker plugin and model router.

## Quick Start

```bash
# See current spend
ruflo cost report

# Set a daily budget (alerts when hit)
ruflo cost budget --daily 5.00 --currency usd

# Turn on smart routing (routes cheap tasks to Haiku, expensive to Sonnet/Opus)
ruflo cost routing --enable --strategy smart
```

## How Smart Routing Works

```
Task comes in → Router scores complexity (1-10)
  Score 1-3  → Claude Haiku 4.5     (~10x cheaper)
  Score 4-6  → Claude Sonnet 4.6    (default)
  Score 7-10 → Claude Opus 4.8      (max power)
  Local tasks → Ollama (free)
```

### Configure Routing Thresholds

```yaml
# .claude-flow/config.yaml — add this block
routing:
  enabled: true
  thresholds:
    haiku: 3        # score ≤ 3 → Haiku
    sonnet: 6       # score ≤ 6 → Sonnet
    opus: 10        # score > 6 → Opus
  local_first: true # try Ollama before API calls
  budget_guard: true # hard stop at budget limit
```

### Force a Model for a Task

```bash
# Force cheap model for a simple task
ruflo swarm init --model haiku --topology hierarchical

# Force Opus for a complex architecture task
ruflo agent spawn --type architect --model opus
```

## Budget Management

```bash
# Set monthly budget with alert at 80%
ruflo cost budget --monthly 50.00 --alert-at 80

# View spend by agent type
ruflo cost breakdown --by agent-type

# View spend by task
ruflo cost breakdown --by task --last 7d

# Export spend report as CSV
ruflo cost report --format csv --output spend-report.csv
```

## Token Efficiency Tips

### 1. Use Memory to Avoid Repeat Work
```bash
# Store results so agents don't re-compute
ruflo memory store --key "research-results-v1" \
  --value "$(cat research.md)" --namespace cache

# Next time, retrieve instead of re-running
ruflo memory search --query "research results" --namespace cache
```

### 2. Batch Tasks in One Swarm
```bash
# One swarm for 5 tasks = shared context = fewer tokens
ruflo swarm init --topology hierarchical --objective "do all 5 tasks"
# vs 5 separate calls with cold-start overhead each time
```

### 3. Use Background Workers for Audits
```bash
# Run the cost-audit worker nightly instead of ad-hoc
ruflo hooks worker dispatch --trigger audit --schedule "0 2 * * *"
```

## MCP Tool Usage

```javascript
// Check current spend before spawning expensive agents
mcp__claude-flow__token_usage {
  operation: "check-budget",
  timeframe: "today"
}

// Get cost estimate before running a task
mcp__claude-flow__cost_estimate {
  task: "refactor entire auth module",
  topology: "hierarchical",
  max_agents: 8
}
```

## Typical Savings by Pattern

| Pattern | Before | After Smart Routing | Saving |
|---|---|---|---|
| Code review | Sonnet × 10 agents | Haiku × 8, Sonnet × 2 | ~65% |
| Doc generation | Opus × 1 | Haiku × 1 | ~90% |
| Architecture | Sonnet × 1 | Opus × 1 (needed) | 0% |
| Test writing | Sonnet × 5 | Haiku × 5 | ~80% |
| Bug fixing | Sonnet × 3 | Sonnet × 1, Haiku × 2 | ~40% |

## Troubleshooting

**Budget alert keeps firing but I haven't spent much**
→ Check if daemon background workers are running constantly: `ruflo daemon status`
→ Stop unnecessary workers: `ruflo daemon stop --worker testgaps`

**Smart routing sends complex tasks to Haiku**
→ Lower the complexity threshold: set `haiku: 2` in config

**Cost report shows $0 but I've been using it**
→ Cost tracking requires the MCP server running: `ruflo mcp start`
