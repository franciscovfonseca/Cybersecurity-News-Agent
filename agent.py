# Setup Guide

## Prerequisites

- Python 3.11+
- Notion account with API access
- Anthropic API key

## Installation

```bash
git clone https://github.com/franciscovfonseca/Cybersecurity-News-Agent.git
cd Cybersecurity-News-Agent
pip install -r requirements.txt
cp .env.example .env
```

## Configuration

Edit `.env` with your credentials:

```
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_database_id
ANTHROPIC_API_KEY=your_anthropic_key
```

## Usage

```bash
python src/agent.py              # Process all sources
python src/agent.py --days 3     # Look back 3 days
python src/agent.py --dry-run    # Test without saving
```
