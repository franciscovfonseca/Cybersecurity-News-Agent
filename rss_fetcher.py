#!/usr/bin/env python3
"""
AI Analyzer Module

Uses Claude AI to analyze cybersecurity articles, assign ratings,
generate summaries, and apply relevant labels.
"""

import json
import os
import re
from typing import Optional

import anthropic


class AIAnalyzer:
    """
    Claude-powered article analyzer for cybersecurity content.
    
    Evaluates articles based on:
    - Threat severity and active exploitation
    - Actionability for security professionals
    - Breadth of impact
    - Timeliness and relevance
    """
    
    # Valid ratings
    VALID_RATINGS = ["S Tier", "A Tier", "B Tier", "C Tier", "D Tier"]
    
    # Valid labels
    VALID_LABELS = [
        "Vulnerabilities", "Threat Intel", "Malware", "Ransomware",
        "Phishing", "Data Breach", "Cloud Security", "Identity & Access",
        "Network Security", "Endpoint Security", "Compliance", "Privacy",
        "Incident Response", "Patch Management", "Zero-Day", "APT",
        "Supply Chain", "Critical Infrastructure", "Government",
        "Financial Services", "Healthcare", "Best Practices",
        "Tools & Techniques", "Career", "Industry News"
    ]
    
    def __init__(self, prompts: dict):
        """
        Initialize the analyzer with prompt templates.
        
        Args:
            prompts: Dictionary with 'system' and 'analysis' prompt templates
        """
        self.prompts = prompts
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    
    async def analyze(self, article: dict) -> dict:
        """
        Analyze an article and return structured assessment.
        
        Args:
            article: Article dictionary with title, content, source, etc.
            
        Returns:
            Dictionary with rating, quality_score, summary, labels, explanation
        """
        # Build the analysis prompt
        prompt = self.prompts["analysis"].format(
            title=article["title"],
            source=article["source"],
            published=article.get("published_date", "Unknown"),
            content=article.get("content", "No content available")[:1500]
        )
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=self.prompts["system"],
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract and parse response
            response_text = response.content[0].text
            analysis = self._parse_response(response_text)
            
            return analysis
            
        except anthropic.APIError as e:
            raise Exception(f"Claude API error: {e}")
        except Exception as e:
            raise Exception(f"Analysis failed: {e}")
    
    def _parse_response(self, response_text: str) -> dict:
        """
        Parse Claude's JSON response into structured data.
        
        Includes validation and fallback handling for malformed responses.
        
        Args:
            response_text: Raw response text from Claude
            
        Returns:
            Validated analysis dictionary
        """
        # Try to extract JSON from response
        try:
            # Handle potential markdown code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text
            
            data = json.loads(json_str)
            
        except json.JSONDecodeError:
            # Fallback for malformed JSON
            return self._fallback_analysis(response_text)
        
        # Validate and sanitize response
        return self._validate_analysis(data)
    
    def _validate_analysis(self, data: dict) -> dict:
        """
        Validate and sanitize analysis data.
        
        Args:
            data: Parsed JSON data
            
        Returns:
            Validated analysis dictionary
        """
        # Validate rating
        rating = data.get("rating", "D Tier")
        if rating not in self.VALID_RATINGS:
            rating = "D Tier"
        
        # Validate quality score
        quality_score = data.get("quality_score", 1)
        try:
            quality_score = int(quality_score)
            quality_score = max(1, min(100, quality_score))
        except (ValueError, TypeError):
            quality_score = 1
        
        # Validate summary
        summary = data.get("summary", "No summary available")
        if not isinstance(summary, str) or len(summary) < 10:
            summary = "No summary available"
        # Truncate if too long
        if len(summary) > 500:
            summary = summary[:497] + "..."
        
        # Validate explanation
        explanation = data.get("rating_explanation", "No explanation provided")
        if not isinstance(explanation, str):
            explanation = "No explanation provided"
        if len(explanation) > 1000:
            explanation = explanation[:997] + "..."
        
        # Validate labels
        labels = data.get("labels", [])
        if not isinstance(labels, list):
            labels = []
        # Filter to valid labels only
        labels = [l for l in labels if l in self.VALID_LABELS]
        # Ensure at least one label
        if not labels:
            labels = ["Industry News"]
        
        return {
            "rating": rating,
            "quality_score": quality_score,
            "summary": summary,
            "rating_explanation": explanation,
            "labels": labels
        }
    
    def _fallback_analysis(self, response_text: str) -> dict:
        """
        Generate fallback analysis when JSON parsing fails.
        
        Args:
            response_text: Raw response text
            
        Returns:
            Default analysis dictionary
        """
        # Try to extract rating from text
        rating = "C Tier"
        for tier in self.VALID_RATINGS:
            if tier.lower() in response_text.lower():
                rating = tier
                break
        
        return {
            "rating": rating,
            "quality_score": 50,
            "summary": "Analysis parsing failed - manual review recommended",
            "rating_explanation": f"Automated parsing failed. Raw response excerpt: {response_text[:200]}...",
            "labels": ["Industry News"]
        }


class MockAIAnalyzer:
    """
    Mock analyzer for testing without API calls.
    """
    
    def __init__(self, prompts: dict):
        self.prompts = prompts
    
    async def analyze(self, article: dict) -> dict:
        """Return mock analysis for testing."""
        import random
        
        ratings = ["S Tier", "A Tier", "B Tier", "C Tier", "D Tier"]
        labels_pool = [
            "Vulnerabilities", "Threat Intel", "Malware", "Ransomware",
            "Data Breach", "Cloud Security", "Best Practices"
        ]
        
        return {
            "rating": random.choice(ratings),
            "quality_score": random.randint(30, 95),
            "summary": f"Mock summary for: {article['title'][:50]}",
            "rating_explanation": "This is a mock analysis for testing purposes.",
            "labels": random.sample(labels_pool, k=random.randint(1, 3))
        }


# For standalone testing
if __name__ == "__main__":
    import asyncio
    
    # Test with mock analyzer
    prompts = {
        "system": "You are a cybersecurity analyst.",
        "analysis": "Analyze: {title}"
    }
    
    analyzer = MockAIAnalyzer(prompts)
    
    test_article = {
        "title": "Critical Zero-Day in Popular Software",
        "source": "BleepingComputer",
        "published_date": "2024-01-15",
        "content": "A critical vulnerability has been discovered..."
    }
    
    async def test():
        result = await analyzer.analyze(test_article)
        print("Analysis result:")
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
