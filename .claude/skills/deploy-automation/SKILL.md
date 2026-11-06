---
name: deploy-automation
description: |
  Automate deployments end-to-end with Ruflo agents — build, test, validate, and deploy with a swarm watching every step. Use when setting up CI/CD, deploying to production, rolling back a bad release, or running pre-deployment validation.
---

# Deploy Automation

## What This Skill Does

Coordinates a deployment swarm that builds your app, runs tests, validates production-readiness, deploys, and monitors post-deploy — all with agent-managed rollback if something goes wrong.

## Quick Start

```bash
# Run a full pre-deployment check
npx ruflo sparc run production-validator \
  "validate this app is ready to deploy — check tests, build, env vars, and dependencies"

# Full deploy pipeline
ruflo workflow execute --name "deploy-pipeline" \
  --params '{"env": "production", "strategy": "blue-green"}'
```

## Pre-Deploy Validation

Always run this before any deployment:

```bash
# Spawn a validation swarm
ruflo swarm init --topology hierarchical --max-agents 5

ruflo agent spawn --type production-validator --name "build-check"
ruflo agent spawn --type tester --name "test-check"
ruflo agent spawn --type security-manager --name "security-check"

# Run validation
npx ruflo sparc run production-validator \
  "check: 1) npm run build succeeds, 2) all tests pass, 3) no .env secrets committed, 4) dependencies are up to date"
```

Validation checklist agents will verify:
- Build compiles without errors
- Test suite passes at 90%+ coverage
- No secrets or credentials in committed files
- All environment variables are set
- Dependencies have no critical CVEs

## Deploy Pipeline Workflows

### Simple Deploy

```bash
ruflo workflow create --name "simple-deploy" --steps '[
  {"agent": "tester",              "task": "run full test suite"},
  {"agent": "production-validator","task": "validate build and env"},
  {"agent": "devops",              "task": "run npm run build && deploy to staging"},
  {"agent": "tester",              "task": "run smoke tests on staging"},
  {"agent": "devops",              "task": "promote staging to production"}
]'

ruflo workflow execute --name "simple-deploy"
```

### Blue-Green Deploy

```javascript
mcp__claude-flow__workflow_create {
  name: "blue-green-deploy",
  steps: [
    { agent: "devops", task: "build new image and push to registry" },
    { agent: "devops", task: "deploy to green environment (idle slot)" },
    { agent: "tester", task: "run full smoke test suite against green" },
    { agent: "production-validator", task: "validate green is healthy" },
    { agent: "devops", task: "switch traffic from blue to green" },
    { agent: "devops", task: "monitor for 5 minutes, rollback if errors spike" }
  ]
}
```

### Rollback

```bash
# Auto-rollback if deploy fails
ruflo workflow create --name "safe-deploy" \
  --on-failure "ruflo agent spawn --type devops --task 'rollback to previous version'"

# Manual rollback
npx ruflo sparc run devops \
  "rollback the last deployment — restore previous Docker image or git revert last deploy commit"
```

## Environment Management

```bash
# Validate all required env vars are set before deploy
npx ruflo sparc run production-validator \
  "read .env.example, check every key exists in the current environment, report any missing"

# Store env config in secure memory (not in git)
ruflo memory store \
  --key "prod-env-config" \
  --value "$(cat .env.production)" \
  --namespace secrets \
  --encrypt true
```

## Post-Deploy Monitoring

```bash
# Spawn a monitor agent after deploy
ruflo agent spawn --type production-validator \
  --task "watch app logs for 10 minutes after deploy, alert if error rate > 1%"

# Set up observability
npx ruflo sparc run devops \
  "configure structured logging and health check endpoint, verify /health returns 200"
```

## CI/CD Integration

### GitHub Actions Hook

Add this to `.github/workflows/deploy.yml`:

```yaml
- name: Ruflo pre-deploy validation
  run: |
    npx ruflo@latest sparc run production-validator \
      "validate this commit is safe to deploy"
    npx ruflo@latest sparc run security-review \
      "scan for vulnerabilities in changed files"
```

### Hook-Based Auto-Deploy

```bash
# Auto-run deploy validation after every commit to main
ruflo hooks setup --trigger post-commit \
  --branch main \
  --command "npx ruflo sparc run production-validator 'validate latest commit'"
```

## MCP Tool Pattern

```javascript
// Full deploy sequence via MCP
mcp__claude-flow__swarm_init {
  topology: "hierarchical",
  objective: "deploy to production safely"
}

// Parallel pre-checks
mcp__claude-flow__agent_spawn { type: "tester",              task: "run tests" }
mcp__claude-flow__agent_spawn { type: "security-manager",   task: "security scan" }
mcp__claude-flow__agent_spawn { type: "production-validator", task: "build check" }

// Wait for all green, then deploy
mcp__claude-flow__agent_spawn {
  type: "devops",
  task: "deploy only if all pre-checks passed",
  depends_on: ["tester", "security-manager", "production-validator"]
}
```

## Troubleshooting

**Deploy fails silently**
→ Check agent logs: `ruflo agent logs --name "devops"`
→ Check swarm output: `cat .claude-flow/logs/swarm.log`

**Tests pass locally but fail in CI**
→ Use the `production-validator` agent — it checks for env var mismatches

**Rollback didn't trigger**
→ Ensure `--on-failure` flag is set on the workflow, not just the agent

## Best Practices

1. **Never deploy without running the validation swarm first**
2. **Always have a rollback plan defined before deploying**
3. **Store deploy history in memory** — `ruflo memory store --namespace deploys`
4. **Use blue-green for zero-downtime** — never cut over until green is verified
5. **Monitor for at least 5 minutes post-deploy** before considering it done
