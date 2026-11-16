"""
AWS Bedrock Integration & Fact-Checking Engine.
Uses boto3 for AWS Bedrock integration with model ID (e.g. deepseek.v3.2).
Grounded on live research from Tavily.
"""

import os
import re
import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings

from research.tavily_service import (
    ResearchCollector,
    search_tavily,
)
from ai_engine.prompts import build_synthesis_prompt
from core.utils import sanitize_public_report

def get_bedrock_client():
    region = getattr(settings, "AWS_REGION", None) or os.getenv("AWS_REGION", "ap-south-1")
    access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None) or os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None) or os.getenv("AWS_SECRET_ACCESS_KEY")

    kwargs = {"region_name": region}
    if access_key and secret_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key

    return boto3.client("bedrock-runtime", **kwargs)

def get_bedrock_model_id():
    return getattr(settings, "BEDROCK_MODEL_ID", None) or os.getenv("BEDROCK_MODEL_ID", "deepseek.v3.2")

def normalize_message_content(raw):
    if raw is None:
        return ""
    if isinstance(raw, dict):
        if "content" in raw:
            return normalize_message_content(raw["content"])
        if "text" in raw:
            return normalize_message_content(raw["text"])
    if isinstance(raw, list):
        parts = []
        for block in raw:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        text = "\n".join(parts)
    else:
        text = str(raw)

    return re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.I).strip()

def parse_raw_json(raw_text):
    clean_text = raw_text.strip()
    clean_text = re.sub(r"<think>[\s\S]*?</think>", "", clean_text, flags=re.I).strip()

    if "```" in clean_text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_text, re.I)
        if match and match.group(1):
            clean_text = match.group(1).strip()
        else:
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.I)
            clean_text = re.sub(r"```\s*$", "", clean_text)
            clean_text = clean_text.strip()

    start_idx = clean_text.find("{")
    end_idx = clean_text.rfind("}")

    if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
        raise ValueError("Agent response did not contain a valid JSON object structure.")

    json_sub = clean_text[start_idx:end_idx + 1]
    return json.loads(json_sub)

def extract_and_validate_report(raw_input, original_claim, collector):
    normalized_text = normalize_message_content(raw_input)
    if not normalized_text:
        raise ValueError("Agent response did not contain a valid JSON object structure.")

    try:
        parsed = parse_raw_json(normalized_text)
    except Exception as parse_err:
        err_msg = str(parse_err)
        if "did not contain a valid JSON object" in err_msg:
            raise parse_err
        raise ValueError(f"Agent produced malformed JSON: {err_msg}")

    raw_verdict = str(parsed.get("verdict") or "").upper().strip()
    if raw_verdict == "TRUE":
        verdict = "TRUE"
    elif raw_verdict == "FALSE":
        verdict = "FALSE"
    elif raw_verdict in ("MISLEADING", "MIXED"):
        verdict = "MISLEADING"
    elif raw_verdict == "VERIFICATION_UNAVAILABLE":
        verdict = "VERIFICATION_UNAVAILABLE"
    else:
        verdict = "UNCERTAIN"

    # Reconcile sources
    retrieved_by_url = {src.get("url"): src for src in collector.sources if src.get("url")}
    final_sources = []

    model_sources = parsed.get("sources")
    if isinstance(model_sources, list):
        for s in model_sources:
            if isinstance(s, dict) and s.get("url") and s["url"] in retrieved_by_url:
                real = retrieved_by_url[s["url"]]
                final_sources.append({
                    "id": real.get("id") or s.get("id"),
                    "title": s.get("title") or real.get("title"),
                    "url": real.get("url"),
                    "publisher": s.get("publisher") or real.get("publisher"),
                    "publishedAt": real.get("publishedAt"),
                    "retrievedAt": real.get("retrievedAt"),
                    "sourceType": "web",
                    "snippet": real.get("snippet") or "",
                    "relevance": s.get("relevance") or real.get("relevance") or "Retrieved live web evidence",
                })

    if not final_sources and collector.sources:
        final_sources = [
            {
                "id": s.get("id"),
                "title": s.get("title") or "Empirical Reference",
                "url": s.get("url"),
                "publisher": s.get("publisher") or "Web Source",
                "publishedAt": s.get("publishedAt"),
                "retrievedAt": s.get("retrievedAt"),
                "sourceType": "web",
                "snippet": s.get("snippet") or "",
                "relevance": s.get("relevance") or "Retrieved live web evidence",
            }
            for s in collector.sources
        ]

    # Deduplicate by url
    seen_urls = set()
    unique_sources = []
    for s in final_sources:
        u = s.get("url")
        if u and u not in seen_urls:
            seen_urls.add(u)
            unique_sources.append(s)
    final_sources = unique_sources

    total_evidence = len(collector.sources)
    if total_evidence == 0:
        if verdict != "VERIFICATION_UNAVAILABLE":
            verdict = "UNCERTAIN"

    # Confidence score calculation
    raw_conf = parsed.get("confidence")
    if verdict in ("UNCERTAIN", "VERIFICATION_UNAVAILABLE") or total_evidence == 0:
        confidence = 0
    else:
        try:
            val = float(raw_conf)
            if 0 <= val <= 100:
                confidence = round(val)
            else:
                confidence = 85 if len(final_sources) > 1 else 70
        except (TypeError, ValueError):
            confidence = 85 if len(final_sources) > 1 else 70

    def clean_arr(val):
        if isinstance(val, list):
            return [str(it).strip() for it in val if isinstance(it, str) and str(it).strip()]
        return []

    debunking = clean_arr(parsed.get("debunkingEvidence"))
    signals = clean_arr(parsed.get("keySignals"))
    tactics = clean_arr(parsed.get("tactics"))
    sources_checked = clean_arr(parsed.get("sourcesChecked"))

    explanation = str(parsed.get("explanation") or "").strip()
    if not explanation:
        if verdict == "UNCERTAIN":
            explanation = "Live web research did not find sufficient empirical records or verified news reports to corroborate or refute this claim."
        else:
            explanation = "The submitted claim underwent live web verification against empirical records."

    timeline = str(parsed.get("timelineAndContext") or "").strip()
    advisory = str(parsed.get("advisory") or "").strip()
    if not advisory:
        advisory = "Verify sensitive claims against accredited primary records before sharing."

    if not sources_checked and final_sources:
        publishers = []
        for s in final_sources:
            p = s.get("publisher") or s.get("title")
            if p and p not in publishers:
                publishers.append(p)
        sources_checked = publishers[:5]

    report = {
        "verdict": verdict,
        "confidence": confidence,
        "explanation": explanation,
        "timelineAndContext": timeline,
        "debunkingEvidence": debunking,
        "keySignals": signals,
        "tactics": tactics,
        "sourcesChecked": sources_checked,
        "advisory": advisory,
        "sources": final_sources,
        "researchMetadata": collector.get_metadata(),
    }

    return sanitize_public_report(report)

def invoke_bedrock_model(prompt_text, options=None):
    """
    Invokes AWS Bedrock model using boto3 converse or invoke_model API.
    """
    client = get_bedrock_client()
    model_id = (options and options.get("modelId")) or get_bedrock_model_id()

    # Try Converse API first
    try:
        response = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt_text}],
                }
            ],
            inferenceConfig={
                "temperature": 0.1,
                "maxTokens": 2048,
            },
        )
        output_msg = response.get("output", {}).get("message", {})
        return normalize_message_content(output_msg.get("content"))
    except Exception as converse_err:
        # Fall back to invoke_model with standard payload format
        try:
            body = json.dumps({
                "prompt": prompt_text,
                "temperature": 0.1,
                "max_tokens": 2048,
            })
            resp = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=body,
            )
            resp_body = json.loads(resp["body"].read().decode("utf-8"))
            if "completion" in resp_body:
                return resp_body["completion"]
            if "generation" in resp_body:
                return resp_body["generation"]
            if "outputs" in resp_body:
                return resp_body["outputs"][0].get("text", "")
            return json.dumps(resp_body)
        except Exception as invoke_err:
            raise RuntimeError(f"Bedrock invocation failed: converse={converse_err}, invoke={invoke_err}")

def execute_fact_check_agent(claim, options=None):
    """
    Controlled research-assisted fact checking pipeline:
    1. Executes live web research via Tavily
    2. Enforces explicit VERIFICATION_UNAVAILABLE if search completely failed
    3. Builds synthesis prompt
    4. Invokes AWS Bedrock with 1-time retry for malformed JSON
    5. Validates and sanitizes final report
    """
    if not claim or not isinstance(claim, str) or not claim.strip():
        raise ValueError("Claim text is required for fact-check verification.")

    sanitized_claim = claim.strip()
    collector = ResearchCollector()
    options = options or {}

    # Phase 1: Live Web Research
    try:
        search_output = search_tavily(sanitized_claim, options)
        if search_output.get("success"):
            collector.searchSucceeded = True
            collector.webSearchSucceeded = True
            collector.searchQuery = search_output.get("query", sanitized_claim)
            collector.hasRelevantEvidence = search_output.get("hasRelevantEvidence", False)
            if search_output.get("results"):
                collector.add_sources(search_output["results"])
            collector.rawResults = search_output.get("rawResults", [])
        else:
            collector.searchSucceeded = False
            collector.webSearchSucceeded = False
            collector.searchQuery = search_output.get("query", sanitized_claim)
            collector.hasRelevantEvidence = False
            collector.searchError = search_output.get("error", "Research service unavailable")
    except Exception as tool_err:
        print(f"[FactCheckAgent] Research execution notice: {tool_err}")
        collector.searchSucceeded = False
        collector.webSearchSucceeded = False
        collector.hasRelevantEvidence = False
        collector.searchError = "Research service temporarily unavailable"

    # Phase 2: If live web research completely failed, return VERIFICATION_UNAVAILABLE
    if not collector.searchSucceeded and not collector.sources:
        unavailable_report = {
            "verdict": "VERIFICATION_UNAVAILABLE",
            "confidence": 0,
            "explanation": "Automated live research is temporarily unavailable. Evidence collection service could not be reached at this time.",
            "timelineAndContext": f'Verification attempted for claim: "{sanitized_claim[:100]}".',
            "debunkingEvidence": [],
            "keySignals": ["Live web research service unavailable", "No external telemetry retrieved"],
            "tactics": [],
            "sourcesChecked": [],
            "advisory": "Verification could not be completed due to external research service unavailability. Please try again shortly.",
            "sources": [],
            "researchMetadata": collector.get_metadata(),
        }
        return sanitize_public_report(unavailable_report)

    # Phase 3: Synthesis prompt
    synthesis_prompt = build_synthesis_prompt(sanitized_claim, collector)

    # Phase 4: Model invocation with 1 retry
    try:
        # Check if caller provided mock model
        mock_model = options.get("model")
        if mock_model and hasattr(mock_model, "invoke"):
            response = mock_model.invoke(synthesis_prompt)
            content = normalize_message_content(response)
        elif mock_model and callable(mock_model):
            response = mock_model(synthesis_prompt)
            content = normalize_message_content(response)
        else:
            content = invoke_bedrock_model(synthesis_prompt, options)

        try:
            return extract_and_validate_report(content, sanitized_claim, collector)
        except Exception as first_err:
            print(f"[FactCheckAgent] First model attempt JSON validation note: {first_err}. Retrying once...")
            retry_prompt = (
                f"{synthesis_prompt}\n\nATTENTION RECOVERY: Your previous response was rejected because: "
                f'"{first_err}". You MUST output ONLY a single, strictly valid raw JSON object matching the schema. '
                "No markdown fences, no conversational preface, no trailing text."
            )
            if mock_model and hasattr(mock_model, "invoke"):
                retry_response = mock_model.invoke(retry_prompt)
                retry_content = normalize_message_content(retry_response)
            elif mock_model and callable(mock_model):
                retry_response = mock_model(retry_prompt)
                retry_content = normalize_message_content(retry_response)
            else:
                retry_content = invoke_bedrock_model(retry_prompt, options)

            try:
                return extract_and_validate_report(retry_content, sanitized_claim, collector)
            except Exception as second_err:
                print(f"[FactCheckAgent] Model retry failed JSON validation: {second_err}")
                parse_failure_report = {
                    "verdict": "VERIFICATION_UNAVAILABLE",
                    "confidence": 0,
                    "explanation": "Automated fact-checking analysis could not be validated. The system rejected malformed AI output to prevent unsubstantiated conclusions.",
                    "timelineAndContext": f'Analyzed claim: "{sanitized_claim[:100]}".',
                    "debunkingEvidence": [],
                    "keySignals": ["Response formatting limitation", "Failed schema validation"],
                    "tactics": [],
                    "sourcesChecked": [s.get("publisher") or s.get("title") for s in collector.sources[:3]],
                    "advisory": "The analysis engine was unable to validate the dossier format. Please re-submit the claim.",
                    "sources": collector.sources,
                    "researchMetadata": collector.get_metadata(),
                }
                return sanitize_public_report(parse_failure_report)

    except Exception as model_error:
        print(f"[FactCheckAgent] Analysis engine invocation failure: {model_error}")
        fallback_report = {
            "verdict": "VERIFICATION_UNAVAILABLE",
            "confidence": 0,
            "explanation": "Automated fact-checking pipeline encountered an analysis service limitation. Research analysis could not be completed at this time.",
            "timelineAndContext": f'Verification attempted for claim: "{sanitized_claim[:100]}".',
            "debunkingEvidence": [],
            "keySignals": [
                "Investigation service temporarily unavailable",
                "Analysis pipeline terminated safely without fabricating conclusions",
            ],
            "tactics": [],
            "sourcesChecked": [s.get("publisher") or s.get("title") for s in collector.sources[:3]],
            "advisory": "The automated verification service encountered a temporary service limitation. Consult accredited records or retry shortly.",
            "sources": collector.sources,
            "researchMetadata": collector.get_metadata(),
        }
        return sanitize_public_report(fallback_report)

def fact_check_with_ai(text, options=None):
    """Entry point matching bedrockService.js factCheckWithAI."""
    return execute_fact_check_agent(text, options)
