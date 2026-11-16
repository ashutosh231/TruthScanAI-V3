"""
Research & Tavily Service Unit Tests.
Matches tools.test.js from original Express implementation.
"""

from django.test import TestCase
from research.tavily_service import (
    extract_publisher,
    extract_claim_entities,
    assess_evidence_relevance,
    generate_search_query,
    generate_refined_search_query,
    ResearchCollector,
)

class TavilyResearchUnitTests(TestCase):
    def test_extract_publisher_from_url(self):
        self.assertEqual(extract_publisher("https://www.nasa.gov/mission_pages/jwst/main"), "nasa.gov")
        self.assertEqual(extract_publisher("https://reuters.com/world/india"), "reuters.com")
        self.assertEqual(extract_publisher("https://api.tavily.com/source"), "Web Source")

    def test_extract_claim_entities(self):
        claim = "Narendra Modi died in hospital today"
        entities = extract_claim_entities(claim)
        self.assertIn("narendra", entities)
        self.assertIn("modi", entities)
        self.assertIn("hospital", entities)
        # Stop words should not be present
        self.assertNotIn("in", entities)

    def test_assess_relevance_rejects_commercial_spam(self):
        claim = "President signs climate change treaty into law"
        commercial_item = {
            "title": "Best Espresso Machine and Coffee Maker Reviews 2026",
            "snippet": "Use coupon code SAVE50 to get discount on kitchen appliances and air fryers.",
        }
        is_rel, score, reason = assess_evidence_relevance(claim, commercial_item)
        self.assertFalse(is_rel)
        self.assertIn("commercial or affiliate", reason)

    def test_assess_relevance_accepts_genuine_corroboration(self):
        claim = "NASA James Webb telescope confirms water on exoplanet"
        news_item = {
            "title": "NASA James Webb Space Telescope Detects Atmospheric Water Vapor",
            "snippet": "Astronomers confirm atmospheric signatures consistent with water vapor on exoplanet.",
        }
        is_rel, score, reason = assess_evidence_relevance(claim, news_item)
        self.assertTrue(is_rel)
        self.assertGreater(score, 0)

    def test_research_collector_deduplicates_sources(self):
        collector = ResearchCollector()
        sources = [
            {"id": "src-1", "url": "https://nasa.gov/1", "title": "Record 1"},
            {"id": "src-2", "url": "https://nasa.gov/1", "title": "Duplicate Record 1"},
            {"id": "src-3", "url": "https://reuters.com/2", "title": "Record 2"},
        ]
        collector.add_sources(sources)
        self.assertEqual(len(collector.sources), 2)
        self.assertTrue(collector.hasRelevantEvidence)
        meta = collector.get_metadata()
        self.assertEqual(meta["resultsCount"], 2)
        self.assertIsNone(meta["searchError"])
