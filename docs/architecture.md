# Architecture

## Pipeline Overview

```
RSS Sources → Fetcher → Deduplicator → AI Analyzer → Notion Storage
```

## Components

| Component | File | Purpose |
|---|---|---|
| Agent | `agent.py` | Main orchestrator |
| RSS Fetcher | `rss_fetcher.py` | Collects articles from feeds |
| AI Analyzer | `ai_analyzer.py` | Claude-powered analysis |
| Notion Client | `notion_client.py` | Database operations |

## Data Flow

1. **Fetch** — Collect articles from 5 RSS sources
2. **Deduplicate** — Skip already-processed URLs
3. **Analyze** — Claude AI rates and categorizes each article
4. **Store** — Save results to Notion database
