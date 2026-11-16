"""
LangChain Service compatibility layer.
Exports the Bedrock research pipeline functions.
"""

from ai_engine.bedrock_service import (
    execute_fact_check_agent,
    fact_check_with_ai,
    extract_and_validate_report,
    normalize_message_content,
    parse_raw_json,
)

__all__ = [
    "execute_fact_check_agent",
    "fact_check_with_ai",
    "extract_and_validate_report",
    "normalize_message_content",
    "parse_raw_json",
]
