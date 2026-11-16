"""
AI Engine Unit Tests.
Matches agent.test.js from original Express implementation.
"""

import json
from django.test import TestCase
from ai_engine.bedrock_service import (
    normalize_message_content,
    parse_raw_json,
    extract_and_validate_report,
)
from research.tavily_service import ResearchCollector

class AiEngineUnitTests(TestCase):
    def test_normalize_message_content_strips_think_tags(self):
        raw_output = "<think>Evaluating internal weights and checking truthfulness</think>{\n  \"verdict\": \"TRUE\"\n}"
        normalized = normalize_message_content(raw_output)
        self.assertNotIn("<think>", normalized)
        self.assertNotIn("Evaluating internal weights", normalized)
        self.assertIn('"verdict": "TRUE"', normalized)

    def test_parse_raw_json_extracts_from_markdown_codeblock(self):
        markdown_text = "Here is the factual dossier:\n```json\n{\n  \"verdict\": \"FALSE\",\n  \"confidence\": 98\n}\n```\nEnd of dossier."
        parsed = parse_raw_json(markdown_text)
        self.assertEqual(parsed["verdict"], "FALSE")
        self.assertEqual(parsed["confidence"], 98)

    def test_extract_and_validate_report_with_live_sources(self):
        collector = ResearchCollector()
        collector.searchSucceeded = True
        collector.webSearchSucceeded = True
        collector.sources = [
            {
                "id": "tavily-1",
                "title": "Official NASA Mission Release",
                "url": "https://www.nasa.gov/mission/water-found",
                "publisher": "nasa.gov",
                "publishedAt": "2026-03-12",
                "retrievedAt": "2026-11-16T12:00:00Z",
                "sourceType": "web",
                "snippet": "Astronomers confirm atmospheric signatures consistent with water vapor.",
                "relevance": "Official record",
            }
        ]

        model_json = json.dumps({
            "verdict": "TRUE",
            "confidence": 92,
            "explanation": "Empirical telemetry corroborates the claim directly from official primary records retrieved via Tavily.",
            "timelineAndContext": "Official data published on March 12, 2026.",
            "debunkingEvidence": [],
            "keySignals": ["Official cryptographic record", "Direct institutional release"],
            "tactics": [],
            "sourcesChecked": ["nasa.gov"],
            "advisory": "Factual information verified by state authority.",
            "sources": collector.sources,
        })

        report = extract_and_validate_report(model_json, "NASA confirmed water vapor", collector)
        self.assertEqual(report["verdict"], "TRUE")
        self.assertEqual(report["confidence"], 92)
        self.assertEqual(len(report["sources"]), 1)
        # Verify internal provider name was sanitized
        self.assertNotIn("Tavily", report["explanation"])

    def test_extract_and_validate_enforces_uncertain_when_zero_evidence(self):
        collector = ResearchCollector()
        collector.sources = []
        collector.searchSucceeded = True

        model_json = json.dumps({
            "verdict": "TRUE",
            "confidence": 90,
            "explanation": "Claim appears true.",
        })

        report = extract_and_validate_report(model_json, "Uncorroborated claim", collector)
        self.assertEqual(report["verdict"], "UNCERTAIN")
        self.assertEqual(report["confidence"], 0)
