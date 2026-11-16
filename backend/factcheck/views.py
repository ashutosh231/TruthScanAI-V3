"""
Fact Check & Image Scanner Views.
Implements POST /api/fact-check, POST /api/fact-check/file,
GET /api/fact-check/history, GET /api/fact-check/:id, and POST /api/scan.
"""

import math
from datetime import datetime, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.mongodb import (
    get_factchecks_collection,
    to_object_id,
    serialize_doc,
)
from core.permissions import IsAuthenticatedMongoUser
from core.ratelimit import fact_check_rate_limit
from core.utils import validate_safe_url, sanitize_public_report
from factcheck.serializers import CreateFactCheckSerializer
from factcheck.services import check_user_trial_limit
from ai_engine.bedrock_service import fact_check_with_ai
from document_processing.textract_service import (
    extract_file_content,
    extract_text_from_image,
)

VALID_VERDICTS = [
    "TRUE",
    "FALSE",
    "MISLEADING",
    "UNCERTAIN",
    "MIXED",
    "UNVERIFIED",
    "VERIFICATION_UNAVAILABLE",
]

class CreateFactCheckView(APIView):
    """
    POST /api/fact-check
    Perform AI fact-checking on submitted claim text or URL.
    """
    permission_classes = [IsAuthenticatedMongoUser]

    @fact_check_rate_limit
    def post(self, request):
        serializer = CreateFactCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Text content is required for fact-check verification."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        text = serializer.validated_data["text"]
        input_type = serializer.validated_data["type"]
        metadata = serializer.validated_data.get("metadata", {})

        # SSRF validation for URL type
        if input_type == "url":
            is_valid, err_msg = validate_safe_url(text)
            if not is_valid:
                return Response(
                    {"success": False, "message": f"Invalid or prohibited URL: {err_msg}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Trial limit enforcement for non-premium
        allowed, error_payload = check_user_trial_limit(request.user)
        if not allowed:
            return Response(error_payload, status=status.HTTP_402_PAYMENT_REQUIRED)

        # Call AI Fact-Checking Pipeline
        ai_result = fact_check_with_ai(text)

        detailed_metadata = {
            **metadata,
            "timelineAndContext": ai_result.get("timelineAndContext", ""),
            "debunkingEvidence": ai_result.get("debunkingEvidence", []),
            "keySignals": ai_result.get("keySignals", []),
            "tactics": ai_result.get("tactics", []),
            "sourcesChecked": ai_result.get("sourcesChecked", []),
            "advisory": ai_result.get("advisory", ""),
            "sources": ai_result.get("sources", []),
            "researchMetadata": ai_result.get("researchMetadata", {}),
        }

        factchecks_col = get_factchecks_collection()
        now = datetime.now(timezone.utc)

        doc_to_insert = {
            "user": request.user._id,
            "input": text,
            "type": input_type,
            "verdict": ai_result.get("verdict", "UNCERTAIN"),
            "confidence": ai_result.get("confidence", 0),
            "explanation": ai_result.get("explanation", ""),
            "sources": ai_result.get("sources", []),
            "researchMetadata": ai_result.get("researchMetadata", {}),
            "metadata": detailed_metadata,
            "createdAt": now,
            "updatedAt": now,
        }

        insert_res = factchecks_col.insert_one(doc_to_insert)
        fact_check_id = insert_res.inserted_id

        total_usage = factchecks_col.count_documents({"user": request.user._id})

        public_result = sanitize_public_report({
            "id": str(fact_check_id),
            "_id": str(fact_check_id),
            "input": text,
            "type": input_type,
            "verdict": doc_to_insert["verdict"],
            "confidence": doc_to_insert["confidence"],
            "explanation": doc_to_insert["explanation"],
            "timelineAndContext": ai_result.get("timelineAndContext", ""),
            "debunkingEvidence": ai_result.get("debunkingEvidence", []),
            "keySignals": ai_result.get("keySignals", []),
            "tactics": ai_result.get("tactics", []),
            "sourcesChecked": ai_result.get("sourcesChecked", []),
            "advisory": ai_result.get("advisory", ""),
            "sources": ai_result.get("sources", []),
            "researchMetadata": ai_result.get("researchMetadata", {}),
            "trialsUsed": total_usage,
            "trialsRemaining": None if request.user.isPremium else max(0, 2 - total_usage),
            "isPremium": request.user.isPremium,
            "createdAt": now.isoformat(),
        })

        return Response(
            {
                "success": True,
                "result": public_result,
            },
            status=status.HTTP_201_CREATED,
        )


class CheckFileView(APIView):
    """
    POST /api/fact-check/file
    Fact-check an uploaded document or image file.
    """
    permission_classes = [IsAuthenticatedMongoUser]

    @fact_check_rate_limit
    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {
                    "success": False,
                    "message": "No file uploaded. Please upload a PDF, TXT, PNG, or JPG file.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Trial limit enforcement
        allowed, error_payload = check_user_trial_limit(request.user)
        if not allowed:
            return Response(error_payload, status=status.HTTP_402_PAYMENT_REQUIRED)

        # Extract real content
        try:
            extracted = extract_file_content(uploaded_file)
        except Exception as extract_err:
            return Response(
                {"success": False, "message": f"File content extraction failed: {str(extract_err)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        extracted_text = extracted["text"]
        engine = extracted["engine"]
        extraction_confidence = extracted.get("confidence", 90)

        # Run AI Fact Check
        ai_result = fact_check_with_ai(extracted_text)

        detailed_metadata = {
            "originalName": getattr(uploaded_file, "name", ""),
            "mimetype": getattr(uploaded_file, "content_type", ""),
            "size": getattr(uploaded_file, "size", 0),
            "extractionEngine": engine,
            "extractionConfidence": extraction_confidence,
            "timelineAndContext": ai_result.get("timelineAndContext", ""),
            "debunkingEvidence": ai_result.get("debunkingEvidence", []),
            "keySignals": ai_result.get("keySignals", []),
            "tactics": ai_result.get("tactics", []),
            "sourcesChecked": ai_result.get("sourcesChecked", []),
            "advisory": ai_result.get("advisory", ""),
            "sources": ai_result.get("sources", []),
            "researchMetadata": ai_result.get("researchMetadata", {}),
        }

        factchecks_col = get_factchecks_collection()
        now = datetime.now(timezone.utc)

        doc_to_insert = {
            "user": request.user._id,
            "input": extracted_text,
            "type": "file",
            "verdict": ai_result.get("verdict", "UNCERTAIN"),
            "confidence": ai_result.get("confidence", 0),
            "explanation": ai_result.get("explanation", ""),
            "sources": ai_result.get("sources", []),
            "researchMetadata": ai_result.get("researchMetadata", {}),
            "metadata": detailed_metadata,
            "createdAt": now,
            "updatedAt": now,
        }

        insert_res = factchecks_col.insert_one(doc_to_insert)
        fact_check_id = insert_res.inserted_id

        total_usage = factchecks_col.count_documents({"user": request.user._id})

        public_result = sanitize_public_report({
            "id": str(fact_check_id),
            "_id": str(fact_check_id),
            "input": extracted_text,
            "type": "file",
            "verdict": doc_to_insert["verdict"],
            "confidence": doc_to_insert["confidence"],
            "explanation": doc_to_insert["explanation"],
            "timelineAndContext": ai_result.get("timelineAndContext", ""),
            "debunkingEvidence": ai_result.get("debunkingEvidence", []),
            "keySignals": ai_result.get("keySignals", []),
            "tactics": ai_result.get("tactics", []),
            "sourcesChecked": ai_result.get("sourcesChecked", []),
            "advisory": ai_result.get("advisory", ""),
            "sources": ai_result.get("sources", []),
            "researchMetadata": ai_result.get("researchMetadata", {}),
            "trialsUsed": total_usage,
            "trialsRemaining": None if request.user.isPremium else max(0, 2 - total_usage),
            "isPremium": request.user.isPremium,
            "createdAt": now.isoformat(),
        })

        return Response(
            {
                "success": True,
                "result": public_result,
            },
            status=status.HTTP_201_CREATED,
        )


class FactCheckHistoryView(APIView):
    """
    GET /api/fact-check/history?page=1&limit=10
    Get authenticated user's fact check history.
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def get(self, request):
        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (ValueError, TypeError):
            page = 1

        try:
            limit = min(50, max(1, int(request.query_params.get("limit", 10))))
        except (ValueError, TypeError):
            limit = 10

        skip = (page - 1) * limit
        query = {"user": request.user._id}

        factchecks_col = get_factchecks_collection()
        total = factchecks_col.count_documents(query)

        cursor = (
            factchecks_col.find(query)
            .sort("createdAt", -1)
            .skip(skip)
            .limit(limit)
        )
        docs = list(cursor)

        sanitized_items = [
            sanitize_public_report(serialize_doc(doc))
            for doc in docs
        ]

        total_pages = math.ceil(total / limit) if total > 0 else 1

        return Response(
            {
                "success": True,
                "count": len(sanitized_items),
                "total": total,
                "page": page,
                "totalPages": total_pages,
                "data": sanitized_items,
            },
            status=status.HTTP_200_OK,
        )


class FactCheckDetailView(APIView):
    """
    GET /api/fact-check/:id
    Get a single fact-check record by ID.
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def get(self, request, pk):
        obj_id = to_object_id(pk)
        if not obj_id:
            return Response(
                {"success": False, "message": "Fact check record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        factchecks_col = get_factchecks_collection()
        fact_check = factchecks_col.find_one({"_id": obj_id})

        # Return 404 if record doesn't exist OR belongs to another user
        if not fact_check or str(fact_check.get("user")) != str(request.user._id):
            return Response(
                {"success": False, "message": "Fact check record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        public_doc = sanitize_public_report(serialize_doc(fact_check))

        return Response(
            {
                "success": True,
                "data": public_doc,
            },
            status=status.HTTP_200_OK,
        )


class ScanNewsView(APIView):
    """
    POST /api/scan
    Upload image, extract text via Amazon Textract, and fact check via AWS Bedrock.
    """
    permission_classes = [IsAuthenticatedMongoUser]

    @fact_check_rate_limit
    def post(self, request):
        image_file = request.FILES.get("image")
        if not image_file:
            return Response(
                {"success": False, "message": "No image provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate MIME type
        content_type = getattr(image_file, "content_type", "")
        valid_mimes = ["image/jpeg", "image/png", "image/jpg"]
        if content_type not in valid_mimes:
            return Response(
                {"success": False, "message": "Only JPG and PNG images are supported."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file size (5MB)
        max_size = 5 * 1024 * 1024
        if getattr(image_file, "size", 0) > max_size:
            return Response(
                {"success": False, "message": "Image size must be less than 5MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Trial limit enforcement: 2 free trials for free tier users
        allowed, error_payload = check_user_trial_limit(request.user)
        if not allowed:
            return Response(error_payload, status=status.HTTP_402_PAYMENT_REQUIRED)

        # Textract OCR extraction
        image_bytes = image_file.read()
        try:
            ocr_result = extract_text_from_image(image_bytes)
        except Exception as textract_err:
            print(f"[Textract Error]: {textract_err}")
            return Response(
                {"success": False, "message": "Unable to extract text from the image."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        extracted_text = (ocr_result.get("text") or "").strip()
        ocr_confidence = ocr_result.get("confidence", 95)

        # Handle no readable text detected
        if not extracted_text:
            return Response(
                {"success": False, "message": "No readable text was detected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Bedrock fact check
        try:
            ai_result = fact_check_with_ai(extracted_text)
        except Exception as bedrock_err:
            print(f"[Bedrock Error]: {bedrock_err}")
            return Response(
                {"success": False, "message": "Unable to analyze the extracted text."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Validate AI result
        verdict = ai_result.get("verdict")
        confidence = ai_result.get("confidence")
        explanation = ai_result.get("explanation")

        if (
            not ai_result
            or verdict not in VALID_VERDICTS
            or not isinstance(confidence, (int, float))
            or confidence < 0
            or confidence > 100
            or not isinstance(explanation, str)
            or not explanation.strip()
        ):
            print("[Validation Error] Malformed AI output:", ai_result)
            return Response(
                {"success": False, "message": "Unable to analyze the extracted text."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Persist to MongoDB
        factchecks_col = get_factchecks_collection()
        now = datetime.now(timezone.utc)
        record_id = None
        try:
            doc_to_insert = {
                "user": request.user._id,
                "input": extracted_text,
                "type": "scan",
                "verdict": verdict,
                "confidence": round(confidence),
                "explanation": explanation.strip(),
                "sources": ai_result.get("sources", []),
                "researchMetadata": ai_result.get("researchMetadata", {}),
                "metadata": {
                    "ocrConfidence": ocr_confidence,
                    "timelineAndContext": ai_result.get("timelineAndContext", ""),
                    "debunkingEvidence": ai_result.get("debunkingEvidence", []),
                    "keySignals": ai_result.get("keySignals", []),
                    "tactics": ai_result.get("tactics", []),
                    "sourcesChecked": ai_result.get("sourcesChecked", []),
                    "advisory": ai_result.get("advisory", ""),
                    "source": "Camera Optical Scan (High-Precision OCR Lens)",
                    "sources": ai_result.get("sources", []),
                    "researchMetadata": ai_result.get("researchMetadata", {}),
                },
                "createdAt": now,
                "updatedAt": now,
            }
            insert_res = factchecks_col.insert_one(doc_to_insert)
            record_id = str(insert_res.inserted_id)
        except Exception as db_err:
            print(f"[ScanView DB Save Notice]: {db_err}")

        public_data = sanitize_public_report({
            "extractedText": extracted_text,
            "claimAnalyzed": extracted_text,
            "source": "Camera Optical Scan (High-Precision OCR Lens)",
            "inputType": "CAMERA",
            "ocrConfidence": ocr_confidence,
            "verdict": verdict,
            "confidence": round(confidence),
            "explanation": explanation.strip(),
            "timelineAndContext": ai_result.get("timelineAndContext", ""),
            "debunkingEvidence": ai_result.get("debunkingEvidence", []),
            "keySignals": ai_result.get("keySignals", []),
            "tactics": ai_result.get("tactics", []),
            "sourcesChecked": ai_result.get("sourcesChecked", []),
            "advisory": ai_result.get("advisory", ""),
            "sources": ai_result.get("sources", []),
            "researchMetadata": ai_result.get("researchMetadata", {}),
            "recordId": record_id,
        })

        return Response(
            {
                "success": True,
                **public_data,
                "data": public_data,
            },
            status=status.HTTP_200_OK,
        )
