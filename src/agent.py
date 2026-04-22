#!/usr/bin/env python3
"""
Cybersecurity News Intelligence Agent

Main orchestrator that coordinates RSS fetching, AI analysis, and Notion storage.
Run this script to process the latest cybersecurity news from configured sources.

Usage:
    python agent.py                    # Process all sources
    python agent.py --source cisa      # Process single source
    python agent.py --days 3           # Look back 3 days instead of 1
    python agent.py --dry-run          # Analyze without saving to Notion
"""

import argparse
import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from rss_fetcher import RSSFetcher
from ai_analyzer import AIAnalyzer
from notion_client import NotionClient

# Load environment variables
load_dotenv()


class CybersecurityNewsAgent:
    """
    Main agent class that orchestrates the news intelligence pipeline.
    
    Pipeline:
    1. Fetch articles from RSS feeds
    2. Filter out already-processed articles
    3. Analyze each article with Claude AI
    4. Store results in Notion database
    """
    
    def __init__(
        self,
        config_path: str = "config/sources.json",
        prompts_path: str = "config/prompts.json",
        dry_run: bool = False
    ):
        self.config_path = Path(config_path)
        self.prompts_path = Path(prompts_path)
        self.dry_run = dry_run
        
        # Initialize components
        self.fetcher = RSSFetcher(self._load_sources())
        self.analyzer = AIAnalyzer(self._load_prompts())
        
        if not dry_run:
            self.notion = NotionClient(
                token=os.getenv("NOTION_TOKEN"),
                database_id=os.getenv("NOTION_DATABASE_ID")
            )
        else:
            self.notion = None
            
        # Statistics
        self.stats = {
            "fetched": 0,
            "new": 0,
            "analyzed": 0,
            "stored": 0,
            "skipped": 0,
            "errors": 0,
            "by_rating": {"S Tier": 0, "A Tier": 0, "B Tier": 0, "C Tier": 0, "D Tier": 0}
        }
    
    def _load_sources(self) -> list:
        """Load RSS source configuration."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                config = json.load(f)
                return config.get("sources", [])
        else:
            # Default sources if config doesn't exist
            return [
                {
                    "name": "CIS Advisories",
                    "url": "https://www.cisecurity.org/feed/advisories",
                    "type": "advisory"
                },
                {
                    "name": "CISA Advisories",
                    "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
                    "type": "advisory"
                },
                {
                    "name": "Krebs on Security",
                    "url": "https://krebsonsecurity.com/feed/",
                    "type": "blog"
                },
                {
                    "name": "BleepingComputer",
                    "url": "https://www.bleepingcomputer.com/feed/",
                    "type": "news"
                },
                {
                    "name": "The Hacker News",
                    "url": "https://feeds.feedburner.com/TheHackersNews",
                    "type": "news"
                }
            ]
    
    def _load_prompts(self) -> dict:
        """Load AI prompt templates."""
        if self.prompts_path.exists():
            with open(self.prompts_path) as f:
                return json.load(f)
        else:
            # Default prompts if config doesn't exist
            return {
                "system": """You are a cybersecurity intelligence analyst. Your job is to evaluate security news articles and rate them based on their relevance and actionability for security professionals.

You must respond with valid JSON only, no additional text.""",
                
                "analysis": """Analyze this cybersecurity article and provide a structured assessment.

ARTICLE:
Title: {title}
Source: {source}
Published: {published}
Content: {content}

Evaluate based on:
1. Active exploitation - Is this being exploited in the wild?
2. Severity - What's the potential impact?
3. Breadth - How many organizations could be affected?
4. Actionability - Can security teams act on this today?
5. Timeliness - Is this breaking news or old information?

Respond with this exact JSON structure:
{{
    "rating": "S Tier|A Tier|B Tier|C Tier|D Tier",
    "quality_score": <1-100>,
    "summary": "<one sentence summary>",
    "rating_explanation": "<why you assigned this rating>",
    "labels": ["<label1>", "<label2>", ...]
}}

RATING GUIDE:
- S Tier: Active exploitation, critical CVE (CVSS 9+), major breach affecting millions
- A Tier: Important vulnerability, actionable guidance, significant threat
- B Tier: Educational content, moderate relevance, useful context
- C Tier: Niche topic, limited actionability, vendor-specific
- D Tier: Marketing content, outdated news, minimal value

VALID LABELS:
Vulnerabilities, Threat Intel, Malware, Ransomware, Phishing, Data Breach,
Cloud Security, Identity & Access, Network Security, Endpoint Security,
Compliance, Privacy, Incident Response, Patch Management, Zero-Day, APT,
Supply Chain, Critical Infrastructure, Government, Financial Services,
Healthcare, Best Practices, Tools & Techniques, Career, Industry News"""
            }
    
    async def run(
        self,
        source_filter: Optional[str] = None,
        days_back: int = 1,
        max_articles: Optional[int] = None
    ) -> dict:
        """
        Execute the full news intelligence pipeline.
        
        Args:
            source_filter: Only process this source (by name)
            days_back: How many days back to look for articles
            max_articles: Maximum number of articles to process
            
        Returns:
            Statistics dictionary with processing results
        """
        print("\n" + "="*60)
        print("🛡️  CYBERSECURITY NEWS INTELLIGENCE AGENT")
        print("="*60)
        print(f"📅 Looking back: {days_back} day(s)")
        print(f"🔧 Dry run: {self.dry_run}")
        if source_filter:
            print(f"🎯 Source filter: {source_filter}")
        print("="*60 + "\n")
        
        # Step 1: Fetch articles
        print("📡 Step 1: Fetching articles from RSS feeds...")
        cutoff_date = datetime.now() - timedelta(days=days_back)
        articles = await self.fetcher.fetch_all(
            source_filter=source_filter,
            since=cutoff_date
        )
        self.stats["fetched"] = len(articles)
        print(f"   ✓ Fetched {len(articles)} articles\n")
        
        if not articles:
            print("ℹ️  No new articles found. Exiting.")
            return self.stats
        
        # Step 2: Filter duplicates (check Notion)
        print("🔍 Step 2: Checking for duplicates...")
        if self.notion and not self.dry_run:
            existing_urls = await self.notion.get_existing_urls()
            new_articles = [a for a in articles if a["url"] not in existing_urls]
            self.stats["skipped"] = len(articles) - len(new_articles)
        else:
            new_articles = articles
            
        self.stats["new"] = len(new_articles)
        print(f"   ✓ {len(new_articles)} new articles to process")
        print(f"   ✓ {self.stats['skipped']} duplicates skipped\n")
        
        if not new_articles:
            print("ℹ️  All articles already processed. Exiting.")
            return self.stats
        
        # Apply max_articles limit
        if max_articles and len(new_articles) > max_articles:
            print(f"⚠️  Limiting to {max_articles} articles\n")
            new_articles = new_articles[:max_articles]
        
        # Step 3: Analyze with AI
        print("🤖 Step 3: Analyzing articles with Claude AI...")
        analyzed_articles = []
        
        for i, article in enumerate(new_articles, 1):
            print(f"   [{i}/{len(new_articles)}] {article['title'][:50]}...")
            
            try:
                analysis = await self.analyzer.analyze(article)
                article.update(analysis)
                analyzed_articles.append(article)
                self.stats["analyzed"] += 1
                self.stats["by_rating"][analysis["rating"]] += 1
                print(f"       → {analysis['rating']} (Score: {analysis['quality_score']})")
            except Exception as e:
                print(f"       ❌ Error: {e}")
                self.stats["errors"] += 1
        
        print(f"\n   ✓ Analyzed {self.stats['analyzed']} articles\n")
        
        # Step 4: Store in Notion
        if not self.dry_run and self.notion:
            print("📝 Step 4: Storing results in Notion...")
            
            for i, article in enumerate(analyzed_articles, 1):
                try:
                    await self.notion.create_page(article)
                    self.stats["stored"] += 1
                    print(f"   [{i}/{len(analyzed_articles)}] ✓ Stored: {article['title'][:40]}...")
                except Exception as e:
                    print(f"   [{i}/{len(analyzed_articles)}] ❌ Error: {e}")
                    self.stats["errors"] += 1
            
            print(f"\n   ✓ Stored {self.stats['stored']} articles in Notion\n")
        else:
            print("📝 Step 4: Skipped (dry run mode)\n")
        
        # Print summary
        self._print_summary()
        
        return self.stats
    
    def _print_summary(self):
        """Print execution summary."""
        print("="*60)
        print("📊 EXECUTION SUMMARY")
        print("="*60)
        print(f"   Fetched:   {self.stats['fetched']}")
        print(f"   New:       {self.stats['new']}")
        print(f"   Analyzed:  {self.stats['analyzed']}")
        print(f"   Stored:    {self.stats['stored']}")
        print(f"   Skipped:   {self.stats['skipped']}")
        print(f"   Errors:    {self.stats['errors']}")
        print()
        print("📈 RATING DISTRIBUTION")
        print("-"*30)
        for rating, count in self.stats["by_rating"].items():
            bar = "█" * count
            print(f"   {rating}: {count} {bar}")
        print("="*60 + "\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cybersecurity News Intelligence Agent"
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Only process this source (by name)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="How many days back to look (default: 1)"
    )
    parser.add_argument(
        "--max",
        type=int,
        help="Maximum number of articles to process"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze without saving to Notion"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/sources.json",
        help="Path to sources config file"
    )
    
    args = parser.parse_args()
    
    # Validate environment
    if not args.dry_run:
        if not os.getenv("NOTION_TOKEN"):
            print("❌ Error: NOTION_TOKEN not set in environment")
            print("   Run: export NOTION_TOKEN='your-token'")
            print("   Or create a .env file with NOTION_TOKEN=your-token")
            return 1
        if not os.getenv("NOTION_DATABASE_ID"):
            print("❌ Error: NOTION_DATABASE_ID not set in environment")
            return 1
    
    # Run agent
    agent = CybersecurityNewsAgent(
        config_path=args.config,
        dry_run=args.dry_run
    )
    
    asyncio.run(agent.run(
        source_filter=args.source,
        days_back=args.days,
        max_articles=args.max
    ))
    
    return 0


if __name__ == "__main__":
    exit(main())
