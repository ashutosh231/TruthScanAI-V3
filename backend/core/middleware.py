"""
Global middleware for TruthScan AI Django backend.
- Attaches raw_body for HMAC webhook signature verification.
- Centralized exception and 404 response formatter.
"""

from django.http import JsonResponse
from core.exceptions import sanitize_error_message

class CentralizedErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Capture raw request body before reading so Razorpay webhook can verify signature
        try:
            request.raw_body = request.body.decode("utf-8", errors="replace")
        except Exception:
            request.raw_body = ""

        response = self.get_response(request)

        # Standardize 404 JSON response for API endpoints
        if response.status_code == 404 and (
            request.path.startswith("/api/")
            or request.path.startswith("/auth/")
            or request.path.startswith("/fact-check/")
            or request.path.startswith("/news/")
            or request.path.startswith("/payments/")
            or request.path.startswith("/users/")
            or request.path.startswith("/scan/")
        ):
            # If the response hasn't already sent a JSON body
            content_type = response.get("Content-Type", "")
            if "application/json" not in content_type:
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"API endpoint not found: {request.method} {request.path}",
                    },
                    status=404,
                )

        return response

    def process_exception(self, request, exception):
        clean_msg = sanitize_error_message(str(exception) or "Internal Server Error")
        return JsonResponse(
            {
                "success": False,
                "message": clean_msg,
            },
            status=500,
        )
