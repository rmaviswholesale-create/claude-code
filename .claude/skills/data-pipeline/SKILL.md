---
name: data-pipeline
description: |
  Build and run agentic data pipelines with Ruflo — ingest, transform, vectorize, and store data using coordinated agents. Use when processing CSVs, syncing APIs, building RAG pipelines, or automating any data workflow that needs AI reasoning at each step.
---

# Data Pipeline

## What This Skill Does

Coordinates multiple agents to move data from source → transform → store, with AI reasoning at each step. Agents can clean data, extract insights, vectorize content for search, and write results to databases — all in parallel.

## Quick Start

```bash
# Process a CSV file with agents
ruflo swarm init --topology hierarchical --objective "process data file"
npx ruflo sparc run analyzer "read data/input.csv, clean it, extract insights, save to data/output.json"

# Build a RAG pipeline (vectorize docs for search)
ruflo swarm init --topology mesh --max-agents 4
npx ruflo sparc run researcher "read all .md files in docs/, vectorize them, store in AgentDB"
```

## Pipeline Patterns

### Pattern 1: Ingest → Transform → Store

```javascript
// Step 1: Ingest
mcp__claude-flow__swarm_init { topology: "hierarchical", maxAgents: 6 }

mcp__claude-flow__agent_spawn {
  type: "researcher",
  task: "fetch data from API or read files"
}

// Step 2: Transform (parallel)
mcp__claude-flow__agent_spawn {
  type: "analyzer",
  task: "clean, normalize, and enrich the ingested data"
}

// Step 3: Store
mcp__claude-flow__memory_usage {
  action: "store",
  namespace: "pipeline-output",
  key: "processed-data-v1",
  value: "<transformed data>"
}
```

### Pattern 2: RAG Pipeline (Docs → Vector DB)

```bash
# Vectorize all docs so agents can search them semantically
ruflo swarm init --topology hierarchical

# Chunk and embed documents
npx ruflo sparc run researcher \
  "read every file in docs/, chunk into 500-token pieces, store each in AgentDB with metadata"

# Verify search works
ruflo memory search --query "how does authentication work" --namespace docs
```

### Pattern 3: API Sync Pipeline

```bash
# Pull data from an API, transform, push to another

ruflo workflow create --name "api-sync" --steps '[
  {"agent": "researcher", "task": "fetch from source API"},
  {"agent": "analyzer",   "task": "transform to target schema"},
  {"agent": "coder",      "task": "push to destination API or DB"}
]'

# Run it
ruflo workflow execute --name "api-sync"

# Schedule it (runs every hour)
ruflo hooks worker dispatch --trigger api-sync --schedule "0 * * * *"
```

### Pattern 4: CSV/Excel Processing

```bash
# Agent reads, cleans, and summarizes a spreadsheet
npx ruflo sparc run analyzer \
  "read data/sales.csv, identify anomalies, group by category, output summary to data/summary.json"

# If file is large, use batch executor
npx ruflo sparc run batch-executor \
  "process data/large-file.csv in chunks of 1000 rows, store results in AgentDB namespace=sales"
```

## Vector Search Setup

```bash
# Initialize the vector search index
ruflo memory init --backend hybrid --hnsw true

# Store a document with embedding
ruflo memory store \
  --key "doc-001" \
  --value "$(cat docs/api-guide.md)" \
  --namespace docs \
  --embed true

# Semantic search across all stored docs
ruflo memory search \
  --query "how to authenticate users" \
  --namespace docs \
  --top-k 5
```

## Working with AgentDB Directly

```javascript
// Store a batch of records with embeddings
mcp__claude-flow__memory_usage {
  action: "batch_store",
  namespace: "products",
  records: [
    { key: "prod-001", value: "Blue Widget - SKU 1234", embed: true },
    { key: "prod-002", value: "Red Gadget - SKU 5678", embed: true }
  ]
}

// Hybrid search (keyword + semantic)
mcp__claude-flow__memory_usage {
  action: "hybrid_search",
  namespace: "products",
  query: "blue widget",
  top_k: 10,
  rerank: true
}
```

## Scheduling & Automation

```bash
# Run pipeline on a schedule using loop workers
ruflo loop-workers add \
  --name "daily-sync" \
  --schedule "0 6 * * *" \
  --task "npx ruflo sparc run researcher 'sync latest data from API'"

# View all scheduled workers
ruflo loop-workers list

# Check last run output
ruflo loop-workers logs --name "daily-sync"
```

## Error Handling

```bash
# Enable retry on failure
ruflo swarm init --topology hierarchical \
  --retry-max 3 \
  --retry-backoff exponential

# Set up alerting on pipeline failure
ruflo hooks post-task \
  --on-failure "ruflo memory store --key 'pipeline-error' --value 'FAILED' --namespace alerts"
```

## Best Practices

1. **Always namespace your data** — use `--namespace` to keep pipelines isolated
2. **Embed at ingest time** — store with `--embed true` so search works immediately
3. **Use batch-executor for large files** — don't load 100k rows into one agent context
4. **Store intermediate results** — agents can resume from memory if a step fails
5. **Schedule with loop-workers** — don't run pipelines manually, automate them
