#!/usr/bin/env python3
"""
Notion Client Module

Handles all interactions with the Notion API for storing
and querying cybersecurity news articles.
"""

import os
from datetime import datetime
from typing import Optional, Set

from notion_client import Client


class NotionClient:
    """
    Notion API client for the Cybersecurity News database.
    
    Handles:
    - Creating new article pages
    - Checking for existing articles (deduplication)
    - Querying the database
    """
    
    def __init__(self, token: str, database_id: str):
        """
        Initialize the Notion client.
        
        Args:
            token: Notion integration token
            database_id: ID of the target database
        """
        self.client = Client(auth=token)
        self.database_id = database_id
        
        # Cache for existing URLs (for deduplication)
        self._url_cache: Optional[Set[str]] = None
    
    async def get_existing_urls(self) -> Set[str]:
        """
        Get all URLs already in the database.
        
        Used for deduplication to avoid processing the same article twice.
        
        Returns:
            Set of URL strings
        """
        if self._url_cache is not None:
            return self._url_cache
        
        urls = set()
        has_more = True
        start_cursor = None
        
        while has_more:
            response = self.client.databases.query(
                database_id=self.database_id,
                start_cursor=start_cursor,
                page_size=100,
                filter={
                    "property": "URL",
                    "url": {
                        "is_not_empty": True
                    }
                }
            )
            
            for page in response.get("results", []):
                url_prop = page.get("properties", {}).get("URL", {})
                url = url_prop.get("url")
                if url:
                    urls.add(url)
            
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
        
        self._url_cache = urls
        return urls
    
    async def create_page(self, article: dict) -> dict:
        """
        Create a new page in the database for an article.
        
        Args:
            article: Article dictionary with all required fields
            
        Returns:
            Created page response from Notion API
        """
        properties = self._build_properties(article)
        
        response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties
        )
        
        # Update cache
        if self._url_cache is not None:
            self._url_cache.add(article["url"])
        
        return response
    
    def _build_properties(self, article: dict) -> dict:
        """
        Build Notion properties object from article data.
        
        Args:
            article: Article dictionary
            
        Returns:
            Notion-formatted properties dictionary
        """
        properties = {
            # Title (required)
            "Title": {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": article["title"][:2000]}
                    }
                ]
            },
            
            # URL
            "URL": {
                "url": article["url"]
            },
            
            # Source (select)
            "Source": {
                "select": {"name": article["source"]}
            },
            
            # Rating (select)
            "Rating": {
                "select": {"name": article.get("rating", "C Tier")}
            },
            
            # Quality Score (number)
            "Quality Score": {
                "number": article.get("quality_score", 50)
            },
            
            # Labels (multi-select)
            "Labels": {
                "multi_select": [
                    {"name": label} for label in article.get("labels", [])
                ]
            },
            
            # Summary (rich text)
            "Summary": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": article.get("summary", "")[:2000]}
                    }
                ]
            },
            
            # Rating Explanation (rich text)
            "Rating Explanation": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": article.get("rating_explanation", "")[:2000]}
                    }
                ]
            },
            
            # Processed Date (date)
            "Processed Date": {
                "date": {
                    "start": datetime.now().isoformat()
                }
            }
        }
        
        # Published Date (date) - optional
        if article.get("published_date"):
            pub_date = article["published_date"]
            if isinstance(pub_date, datetime):
                properties["Published Date"] = {
                    "date": {
                        "start": pub_date.date().isoformat()
                    }
                }
        
        return properties
    
    async def query_by_rating(self, rating: str, limit: int = 10) -> list:
        """
        Query articles by rating tier.
        
        Args:
            rating: Rating tier (e.g., "S Tier")
            limit: Maximum number of results
            
        Returns:
            List of matching pages
        """
        response = self.client.databases.query(
            database_id=self.database_id,
            page_size=limit,
            filter={
                "property": "Rating",
                "select": {
                    "equals": rating
                }
            },
            sorts=[
                {
                    "property": "Processed Date",
                    "direction": "descending"
                }
            ]
        )
        
        return response.get("results", [])
    
    async def get_recent(self, limit: int = 20) -> list:
        """
        Get the most recently processed articles.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of recent pages
        """
        response = self.client.databases.query(
            database_id=self.database_id,
            page_size=limit,
            sorts=[
                {
                    "property": "Processed Date",
                    "direction": "descending"
                }
            ]
        )
        
        return response.get("results", [])


class MockNotionClient:
    """
    Mock Notion client for testing without API calls.
    """
    
    def __init__(self, token: str = None, database_id: str = None):
        self.pages = []
        self.existing_urls = set()
    
    async def get_existing_urls(self) -> Set[str]:
        return self.existing_urls
    
    async def create_page(self, article: dict) -> dict:
        self.pages.append(article)
        self.existing_urls.add(article["url"])
        return {"id": f"mock-{len(self.pages)}", "url": article["url"]}
    
    async def query_by_rating(self, rating: str, limit: int = 10) -> list:
        return [p for p in self.pages if p.get("rating") == rating][:limit]
    
    async def get_recent(self, limit: int = 20) -> list:
        return self.pages[-limit:]


# For standalone testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test with mock client
        client = MockNotionClient()
        
        # Test article
        article = {
            "title": "Test Article",
            "url": "https://example.com/test",
            "source": "Test Source",
            "rating": "A Tier",
            "quality_score": 85,
            "labels": ["Vulnerabilities", "Threat Intel"],
            "summary": "This is a test article summary.",
            "rating_explanation": "High quality threat intel.",
            "published_date": datetime.now()
        }
        
        # Test create
        result = await client.create_page(article)
        print(f"Created page: {result}")
        
        # Test deduplication
        urls = await client.get_existing_urls()
        print(f"Existing URLs: {urls}")
        
        # Test query
        recent = await client.get_recent()
        print(f"Recent articles: {len(recent)}")
    
    asyncio.run(test())
