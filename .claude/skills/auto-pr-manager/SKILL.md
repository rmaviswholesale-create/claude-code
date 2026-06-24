---
name: auto-pr-manager
description: |
  Automate the full pull request lifecycle with Ruflo agents — auto-review code, respond to comments, fix CI failures, and merge when green. Use when you want agents to babysit a PR, auto-fix review feedback, or run a swarm code review before pushing.
---

# Auto PR Manager

## What This Skill Does

Deploys a swarm of agents to handle PR work: reviewing diffs, fixing CI failures, responding to reviewer comments, and merging when everything is green. Built on Ruflo's `github-code-review` plugin and MCP GitHub tools.

## Quick Start

```bash
# Run a full swarm code review before pushing
ruflo swarm init --topology hierarchical --objective "review my changes"
npx ruflo sparc run reviewer "review all changed files in git diff"

# Watch a PR and auto-fix issues
/github:pr-manager
# Then paste your PR URL when prompted
```

## Swarm Code Review (Before You Push)

Run this before every PR to catch issues early:

```bash
# 1. Initialize review swarm
ruflo swarm init --topology hierarchical --max-agents 6

# 2. Spawn review agents in parallel
ruflo agent spawn --type reviewer --name "security-check"
ruflo agent spawn --type reviewer --name "perf-check"
ruflo agent spawn --type tester --name "test-coverage"

# 3. Run review across all changed files
npx ruflo sparc run reviewer "$(git diff main --name-only | tr '\n' ' ')"

# 4. Store findings in memory
ruflo memory store --key "pr-review-$(git rev-parse --short HEAD)" \
  --value "review complete" --namespace reviews
```

## Auto-Fix CI Failures

```javascript
// MCP pattern — runs when CI fails
mcp__claude-flow__swarm_init {
  topology: "hierarchical",
  objective: "fix CI failure"
}

mcp__claude-flow__agent_spawn {
  type: "debugger",
  task: "read CI logs, identify root cause, fix it"
}

mcp__claude-flow__agent_spawn {
  type: "tester",
  task: "verify fix passes locally before pushing"
}
```

```bash
# CLI equivalent
ruflo swarm init --topology hierarchical
ruflo agent spawn --type debugger
ruflo agent spawn --type tester
npx ruflo sparc run debugger "fix failing CI — check .claude-flow/logs/ for details"
```

## Respond to Review Comments

```bash
# Let an agent draft responses to all open review comments
npx ruflo sparc run reviewer \
  "read PR review comments and either apply the fix or write a reasoned response"

# After agent applies fixes, commit and push
git add -A && git commit -m "address review feedback" && git push
```

## PR Lifecycle Commands

```bash
# Full PR health check
/github:pr-manager

# Swarm review of a specific PR
/github:code-review-swarm

# Issue triage
/github:issue-triage

# Release management
/github:release-manager
```

## MCP Tool Pattern — Full PR Automation

```javascript
// 1. Analyze the PR diff
mcp__claude-flow__github_repo_analyze {
  repo: "owner/repo",
  analysis_type: "pr_diff",
  pr_number: 42
}

// 2. Run security scan
mcp__claude-flow__aidefence_scan {
  target: "pr_diff",
  checks: ["injection", "secrets", "pii"]
}

// 3. Check test coverage delta
mcp__claude-flow__sparc_mode {
  mode: "tester",
  task_description: "verify new code has test coverage"
}

// 4. Post review summary as comment
mcp__claude-flow__github_pr_manage {
  repo: "owner/repo",
  pr_number: 42,
  action: "comment",
  body: "Swarm review complete — see findings above"
}
```

## Auto-Merge When Ready

```bash
# Watch PR until green, then merge
ruflo workflow execute --name "watch-and-merge" \
  --params '{"pr": 42, "repo": "owner/repo", "strategy": "squash"}'
```

## Best Practices

1. **Always swarm-review before pushing** — catches issues before reviewers see them
2. **Store review results in memory** — agents can learn from past PR patterns
3. **Use security scan on every PR** — `ruflo-aidefence` catches secrets and injection
4. **Let agents respond to nit comments** — saves time on minor style feedback
5. **Set a merge strategy upfront** — squash for features, merge for releases
