#!/usr/bin/env python3
"""
RSS Feed Fetcher

Collects articles from configured cybersecurity RSS feeds.
Handles different feed formats and normalizes data structure.
"""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse

import aiohttp
import feedparser
from dateutil import parser as date_parser


class RSSFetcher:
    """
    Asynchronous RSS feed fetcher for cybersecurity news sources.
    
    Supports multiple feed formats and normalizes article data
    into a consistent structure for downstream processing.
    """
    
    def __init__(self, sources: list):
        """
        Initialize the fetcher with configured sources.
        
        Args:
            sources: List of source configurations with name, url, and type
        """
        self.sources = sources
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.headers = {
            "User-Agent": "CybersecurityNewsAgent/1.0 (RSS Aggregator)"
        }
    
    async def fetch_all(
        self,
        source_filter: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> list:
        """
        Fetch articles from all configured sources.
        
        Args:
            source_filter: Only fetch from this source (by name)
            since: Only return articles published after this datetime
            
        Returns:
            List of normalized article dictionaries
        """
        sources = self.sources
        
        # Apply source filter if specified
        if source_filter:
            sources = [
                s for s in sources 
                if source_filter.lower() in s["name"].lower()
            ]
            if not sources:
                print(f"   ⚠️ No source matching '{source_filter}'")
                return []
        
        # Fetch all sources concurrently
        tasks = [self._fetch_source(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and filter results
        articles = []
        for i, result in enumerate(results):
            source = sources[i]
            
            if isinstance(result, Exception):
                print(f"   ⚠️ Error fetching {source['name']}: {result}")
                continue
            
            # Filter by date if specified
            if since:
                result = [
                    a for a in result 
                    if a.get("published_date") and a["published_date"] >= since
                ]
            
            print(f"   • {source['name']}: {len(result)} articles")
            articles.extend(result)
        
        # Sort by date (newest first)
        articles.sort(
            key=lambda x: x.get("published_date") or datetime.min,
            reverse=True
        )
        
        return articles
    
    async def _fetch_source(self, source: dict) -> list:
        """
        Fetch and parse a single RSS source.
        
        Args:
            source: Source configuration dictionary
            
        Returns:
            List of article dictionaries from this source
        """
        async with aiohttp.ClientSession(
            timeout=self.timeout,
            headers=self.headers
        ) as session:
            try:
                async with session.get(source["url"]) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    content = await response.text()
                    return self._parse_feed(content, source)
                    
            except asyncio.TimeoutError:
                raise Exception("Request timed out")
            except aiohttp.ClientError as e:
                raise Exception(f"Connection error: {e}")
    
    def _parse_feed(self, content: str, source: dict) -> list:
        """
        Parse RSS/Atom feed content into normalized articles.
        
        Args:
            content: Raw feed XML content
            source: Source configuration for metadata
            
        Returns:
            List of normalized article dictionaries
        """
        feed = feedparser.parse(content)
        articles = []
        
        for entry in feed.entries:
            try:
                article = self._normalize_entry(entry, source)
                if article:
                    articles.append(article)
            except Exception as e:
                # Skip malformed entries
                continue
        
        return articles
    
    def _normalize_entry(self, entry: dict, source: dict) -> Optional[dict]:
        """
        Normalize a feed entry into a consistent article structure.
        
        Args:
            entry: Raw feedparser entry
            source: Source configuration
            
        Returns:
            Normalized article dictionary or None if invalid
        """
        # Extract URL
        url = entry.get("link") or entry.get("id")
        if not url:
            return None
        
        # Extract title
        title = entry.get("title", "").strip()
        if not title:
            return None
        
        # Extract content (try multiple fields)
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].get("value", "")
        elif hasattr(entry, "summary"):
            content = entry.summary
        elif hasattr(entry, "description"):
            content = entry.description
        
        # Clean HTML from content
        content = self._strip_html(content)
        
        # Truncate content if too long (for API efficiency)
        if len(content) > 2000:
            content = content[:2000] + "..."
        
        # Parse publication date
        published_date = None
        date_fields = ["published_parsed", "updated_parsed", "created_parsed"]
        
        for field in date_fields:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    time_struct = getattr(entry, field)
                    published_date = datetime(*time_struct[:6])
                    break
                except:
                    continue
        
        # Try parsing from string if structured date failed
        if not published_date:
            for field in ["published", "updated", "created"]:
                if hasattr(entry, field) and getattr(entry, field):
                    try:
                        published_date = date_parser.parse(getattr(entry, field))
                        break
                    except:
                        continue
        
        # Generate unique ID
        article_id = hashlib.md5(url.encode()).hexdigest()[:12]
        
        return {
            "id": article_id,
            "title": title,
            "url": url,
            "content": content,
            "source": source["name"],
            "source_type": source.get("type", "news"),
            "published_date": published_date,
            "fetched_date": datetime.now(),
            # Fields to be populated by AI analyzer
            "rating": None,
            "quality_score": None,
            "summary": None,
            "rating_explanation": None,
            "labels": []
        }
    
    def _strip_html(self, text: str) -> str:
        """
        Remove HTML tags from text content.
        
        Args:
            text: HTML string
            
        Returns:
            Plain text string
        """
        import re
        
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', ' ', text)
        
        # Decode HTML entities
        clean = clean.replace('&nbsp;', ' ')
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&quot;', '"')
        clean = clean.replace('&#39;', "'")
        
        # Normalize whitespace
        clean = re.sub(r'\s+', ' ', clean)
        
        return clean.strip()


# For standalone testing
if __name__ == "__main__":
    import json
    
    # Test sources
    test_sources = [
        {
            "name": "BleepingComputer",
            "url": "https://www.bleepingcomputer.com/feed/",
            "type": "news"
        }
    ]
    
    async def test():
        fetcher = RSSFetcher(test_sources)
        articles = await fetcher.fetch_all()
        
        print(f"\nFetched {len(articles)} articles:\n")
        for article in articles[:3]:
            print(f"Title: {article['title']}")
            print(f"URL: {article['url']}")
            print(f"Date: {article['published_date']}")
            print(f"Content: {article['content'][:200]}...")
            print("-" * 50)
    
    asyncio.run(test())
