"""
Centralized exception handling for DRF views.
Standardizes all errors to: { "success": false, "message": "..." }
Sanitizes internal provider names from user-facing error messages.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework import status
import re
from core.utils import sanitize_text

def sanitize_error_message(message):
    if not isinstance(message, str):
        message = str(message)

    if re.search(r"bedrock|deepseek|tavily|langchain|newsapi|textract", message, re.IGNORECASE):
        if re.search(r"tavily|search", message, re.IGNORECASE):
            return "Research Service Temporarily Unavailable"
        elif re.search(r"bedrock|deepseek|model", message, re.IGNORECASE):
            return "TruthScan AI Analysis is temporarily unavailable. Please try again shortly."
        else:
            return sanitize_text(message)

    return sanitize_text(message)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that guarantees { "success": false, "message": "..." }
    """
    response = exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code
        data = response.data

        # Extract message from DRF detail or dict
        if isinstance(data, dict):
            if "detail" in data:
                message = str(data["detail"])
            elif "message" in data:
                message = str(data["message"])
            else:
                # Combine first error message
                first_key = list(data.keys())[0]
                first_val = data[first_key]
                if isinstance(first_val, list):
                    message = f"{first_key}: {first_val[0]}"
                else:
                    message = f"{first_key}: {first_val}"
        elif isinstance(data, list) and len(data) > 0:
            message = str(data[0])
        else:
            message = str(data)

        clean_message = sanitize_error_message(message)

        # Check if requiresUpgrade was passed in custom APIException
        extra = {}
        if hasattr(exc, "extra_data") and isinstance(exc.extra_data, dict):
            extra = exc.extra_data

        response.data = {
            "success": False,
            "message": clean_message,
            **extra,
        }
        return response

    # Unhandled exception
    clean_message = sanitize_error_message(str(exc) or "Internal Server Error")
    return Response(
        {
            "success": False,
            "message": clean_message,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
