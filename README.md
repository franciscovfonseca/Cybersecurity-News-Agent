<div align="center">

<img src="docs/banner.png" alt="Cybersecurity News Agent" width="100%"/>

# Cybersecurity News Intelligence Agent

[![Claude AI](https://img.shields.io/badge/Claude%20AI-Powered-7B2D8B?style=for-the-badge&logo=anthropic&logoColor=white)](https://claude.ai)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Notion](https://img.shields.io/badge/Notion-Integration-000000?style=for-the-badge&logo=notion&logoColor=white)](https://notion.so)
[![RSS](https://img.shields.io/badge/RSS-5%20Sources-FFA500?style=for-the-badge&logo=rss&logoColor=white)]()

**An agentic AI tool that aggregates, analyzes and rates cybersecurity news - delivering actionable intelligence directly to a Notion workspace.**

</div>

---

## Project Overview

I built an AI-powered cybersecurity news aggregator that automatically collects articles from trusted security sources, analyzes each one for relevance and actionability and delivers rated summaries directly to a Notion database.

The agent runs on-demand - when I want to catch up on security news, I execute a single command and receive a curated, prioritized feed of the most important cybersecurity developments.

> **The problem it solves:** Security professionals are overwhelmed with information. This agent cuts through the noise by using AI to rate content based on actionability, threat relevance and business impact - so you focus on what actually matters.

<br>

<p align="center">
  <img src="https://github.com/user-attachments/assets/71bc9333-aa4c-4bd5-bec9-57604052ef44" alt="Cybersecurity News Notion Database" width="100%"/>
</p>

<p align="center"><em>The agent fetches news - AI rates by threat severity - Results appear in Notion, ready to action</em></p>

<br>

---

## Why I Built This

As someone working in cybersecurity, I found myself drowning in news from dozens of sources. I needed a way to:

- **Filter signal from noise** - not every vulnerability matters to every organization
- **Prioritize my reading** - focus on what's actively being exploited
- **Build a knowledge base** - track trends and threats over time

<br>

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Source Aggregation** | Pulls from 5 curated cybersecurity RSS feeds |
| **AI-Powered Analysis** | Claude AI rates each article from S-Tier to D-Tier |
| **Smart Labeling** | Automatic categorization with 25+ security-specific labels |
| **Quality Scoring** | 1-100 actionability score based on threat relevance |
| **Notion Integration** | Results stored in a structured, searchable database |
| **On-Demand Execution** | Run when you want to catch up - no always-on infrastructure |
| **Deduplication** | Skips articles already processed to avoid duplicates |

<br>

---

## Architecture

The agent follows a simple pipeline: **Collect - Analyze - Store**.

```mermaid
flowchart LR
    subgraph Sources["RSS Sources"]
        S1[CIS Advisories]
        S2[CISA Alerts]
        S3[Krebs on Security]
        S4[BleepingComputer]
        S5[The Hacker News]
    end

    subgraph Agent["Claude AI Agent"]
        F[RSS Fetcher]
        D[Deduplicator]
        A[AI Analyzer]
    end

    subgraph Output["Notion Database"]
        N[(Structured\nDatabase)]
    end

    S1 & S2 & S3 & S4 & S5 --> F
    F --> D
    D --> A
    A -->|Rated & Labeled| N

    style Agent fill:#7B2D8B,color:#fff
    style N fill:#000000,color:#fff
```

### Data Flow

1. **RSS Fetcher** - Collects latest articles from all configured sources
2. **Deduplicator** - Checks Notion to skip already-processed articles
3. **AI Analyzer** - Claude analyzes each article for threat relevance and actionability and assigns ratings
4. **Notion Client** - Stores results with full metadata

### Component Diagram

```mermaid
flowchart TD
    subgraph "src/"
        A[agent.py\nMain orchestrator]
        B[rss_fetcher.py\nFeed collection]
        C[ai_analyzer.py\nClaude AI analysis]
        D[notion_client.py\nDatabase operations]
    end

    subgraph "config/"
        E[sources.json\nRSS feed URLs]
        F[prompts.json\nAI prompt templates]
    end

    A --> B
    A --> C
    A --> D
    B --> E
    C --> F

    style A fill:#3776AB,color:#fff
    style C fill:#7B2D8B,color:#fff
    style D fill:#000000,color:#fff
```

<br>

---

## Rating System

The AI rates each article using a tier system based on actionability and threat relevance:

| Tier | Criteria | Action |
|------|----------|--------|
| **S Tier** | Active exploitation, critical CVE, major breach | Immediate attention |
| **A Tier** | Important vulnerability, actionable guidance | Read this week |
| **B Tier** | Educational, moderate relevance | Queue for later |
| **C Tier** | Niche topic, limited actionability | Skim or skip |
| **D Tier** | Marketing, outdated or noise | Ignore |

### Rating Criteria

| Factor | Weight | Description |
|--------|--------|-------------|
| **Active Exploitation** | High | Is this being exploited in the wild? |
| **Severity** | High | CVSS score, potential impact |
| **Breadth of Impact** | Medium | How many organizations affected? |
| **Actionability** | High | Can I do something with this today? |
| **Timeliness** | Medium | Is this breaking or old news? |
| **Source Authority** | Low | Official advisory vs. blog post |

<br>

---

## Data Sources

| Source | Type | Content Focus |
|--------|------|---------------|
| **CIS (MS-ISAC)** | Advisories | Security advisories, best practices |
| **CISA** | Government | Official US alerts, KEV catalog |
| **Krebs on Security** | Journalism | Investigative cybercrime reporting |
| **BleepingComputer** | News | Broad security news coverage |
| **The Hacker News** | News | Vulnerabilities, breaches and tools |

---

<details>
<summary><strong>Content Labels</strong> (click to expand)</summary>

<br>

Articles are automatically tagged with relevant categories:

```
Vulnerabilities    Threat Intel      Malware           Ransomware
Phishing           Data Breach       Cloud Security    Identity & Access
Network Security   Endpoint Security Compliance        Privacy
Incident Response  Patch Management  Zero-Day          APT
Supply Chain       Critical Infrastructure             Government
Financial Services Healthcare        Best Practices    Tools & Techniques
Career             Industry News
```

</details>

<br>

---

## Setup

### Prerequisites

- Python 3.11+
- Anthropic API key
- Notion integration token and database ID

### Installation

```bash
git clone https://github.com/franciscovfonseca/Cybersecurity-News-Agent.git
cd Cybersecurity-News-Agent
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

### Usage

```bash
# Run with default settings
python src/agent.py

# Limit to specific sources
python src/agent.py --sources cisa krebs

# Dry run (no database writes)
python src/agent.py --dry-run

# Set lookback period
python src/agent.py --days 3
```

<br>

---

## Repository Structure

```
Cybersecurity-News-Agent/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── docs/
│   └── banner.png
├── src/
│   ├── agent.py
│   ├── rss_fetcher.py
│   ├── ai_analyzer.py
│   └── notion_client.py
└── config/
    ├── sources.json
    └── prompts.json
```

<br>

---

## What I Built and Learned

- **Agentic AI Development** - Building autonomous tools with Claude AI
- **Python Automation** - RSS parsing, API integration and async data processing
- **AI Prompt Engineering** - Structured analysis prompts for consistent, reliable output
- **API Integration** - Notion API for persistent storage and retrieval
- **Cybersecurity Domain Knowledge** - Curating authoritative, relevant sources

<br>

---

<div align="center">

**franciscovfonseca** · [GitHub](https://github.com/franciscovfonseca) · [LinkedIn](https://www.linkedin.com/in/franciscovfonseca/)

</div>
