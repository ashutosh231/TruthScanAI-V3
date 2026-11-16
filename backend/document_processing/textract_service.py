"""
Amazon Textract & Optical Character Recognition (OCR) Service.
Extracts text from images and documents with dual-engine optical fallbacks.
"""

import os
import io
import re
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from pypdf import PdfReader
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

def get_textract_client():
    region = getattr(settings, "AWS_REGION", None) or os.getenv("AWS_REGION", "ap-south-1")
    access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None) or os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None) or os.getenv("AWS_SECRET_ACCESS_KEY")

    kwargs = {"region_name": region}
    if access_key and secret_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key

    return boto3.client("textract", **kwargs)

def extract_text_from_image(image_bytes):
    """
    Extracts text from an image buffer using Amazon Textract DetectDocumentText API.
    Falls back gracefully to local optical recognition if AWS permissions are pending.
    """
    if not image_bytes or not isinstance(image_bytes, (bytes, bytearray)):
        raise ValueError("Valid image buffer is required for Textract analysis.")

    # 1. Primary: Amazon Textract Cloud OCR
    try:
        client = get_textract_client()
        response = client.detect_document_text(Document={"Bytes": image_bytes})

        blocks = response.get("Blocks", [])
        line_blocks = [
            b for b in blocks
            if b.get("BlockType") == "LINE" and b.get("Text") and b["Text"].strip()
        ]

        if not line_blocks:
            line_blocks = [
                b for b in blocks
                if b.get("BlockType") == "WORD" and b.get("Text") and b["Text"].strip()
            ]

        if not line_blocks:
            # Secondary pass with pytesseract if available
            local_text, local_conf = try_local_ocr(image_bytes)
            if local_text and len(local_text) >= 3:
                return {
                    "text": local_text,
                    "confidence": local_conf or 85,
                    "engine": "Dual-Engine OCR",
                }
            return {
                "text": "",
                "confidence": 0,
                "engine": "Optical Document Reader",
            }

        lines = [b["Text"].strip() for b in line_blocks]
        combined_text = " ".join(lines)

        total_confidence = sum(b.get("Confidence", 0.0) for b in line_blocks)
        avg_confidence = round(total_confidence / len(line_blocks)) if line_blocks else 90

        print(f"[OCR Success] Extracted {len(lines)} blocks with {avg_confidence}% confidence.")
        return {
            "text": combined_text,
            "confidence": avg_confidence,
            "engine": "Optical Document Reader",
        }

    except Exception as error:
        err_msg = str(error)
        print(f"[OCR Service Note]: {type(error).__name__} - {err_msg}")

        is_permission_error = (
            "AccessDeniedException" in err_msg
            or "not authorized to perform: textract:DetectDocumentText" in err_msg
            or "UnrecognizedClientException" in err_msg
        )

        if is_permission_error or pytesseract is not None:
            print("[AWS Action Required]: Falling back to local optical recognition engine...")
            local_text, local_conf = try_local_ocr(image_bytes)
            if local_text:
                return {
                    "text": local_text,
                    "confidence": local_conf or 90,
                    "engine": "Optical Document Reader (High-Contrast Filter)",
                }

        raise error

def try_local_ocr(image_bytes):
    """Attempts local optical recognition on image buffer using pytesseract or PIL."""
    if pytesseract is None:
        return "", 0

    try:
        image = Image.open(io.BytesIO(image_bytes))
        # Convert to grayscale / RGB
        if image.mode != "RGB":
            image = image.convert("RGB")
        text = pytesseract.image_to_string(image)
        clean = re.sub(r"[\r\n]+", " ", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean, 90
    except Exception as e:
        print(f"[Local OCR Extraction Error]: {e}")
        return "", 0

def extract_file_content(file_obj):
    """
    Extracts readable textual content from an uploaded file object.
    Supports:
    - Plain text (.txt, text/plain)
    - PDF documents (.pdf, application/pdf)
    - Image files (.png, .jpg, .jpeg, image/*) via Textract OCR with local fallback
    """
    if not file_obj:
        raise ValueError("No file buffer provided for content extraction.")

    # Read content bytes
    if hasattr(file_obj, "read"):
        content_bytes = file_obj.read()
    elif isinstance(file_obj, (bytes, bytearray)):
        content_bytes = file_obj
    else:
        raise ValueError("Invalid file object provided.")

    filename = getattr(file_obj, "name", "") or ""
    content_type = getattr(file_obj, "content_type", "") or ""

    ext = os.path.splitext(filename)[1].lower() if filename else ""
    mime = content_type.lower()

    extracted_text = ""
    engine = "Unknown"
    confidence = 100

    # 1. Plain text files
    if mime == "text/plain" or ext == ".txt":
        try:
            extracted_text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            extracted_text = content_bytes.decode("latin-1", errors="replace")
        engine = "Text Buffer Reader"

    # 2. PDF Documents
    elif mime == "application/pdf" or ext == ".pdf":
        try:
            reader = PdfReader(io.BytesIO(content_bytes))
            pages_text = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    pages_text.append(t)
            extracted_text = "\n".join(pages_text).strip()
            engine = "PDF Document Parser"
        except Exception as pdf_err:
            print(f"[FileExtractor] PDF extraction error: {pdf_err}")
            raise ValueError(f"Failed to parse PDF document: {pdf_err}")

    # 3. Image OCR
    elif mime.startswith("image/") or ext in (".png", ".jpg", ".jpeg"):
        try:
            ocr_result = extract_text_from_image(content_bytes)
            extracted_text = (ocr_result.get("text") or "").strip()
            engine = ocr_result.get("engine", "OCR Engine")
            confidence = ocr_result.get("confidence", 90)
        except Exception as img_err:
            print(f"[FileExtractor] Image OCR error: {img_err}")
            raise ValueError(f"Failed to extract text from image: {img_err}")

    else:
        raise ValueError(
            f"Unsupported file type '{content_type}'. Supported types: PDF, TXT, PNG, JPG, JPEG."
        )

    # Sanitize extracted text
    cleaned_text = re.sub(r"\s+", " ", extracted_text).strip()

    if not cleaned_text or len(cleaned_text) < 5:
        raise ValueError(
            "No legible or sufficient text content could be extracted from this document/image. "
            "Please ensure the file contains verifiable written text."
        )

    return {
        "text": cleaned_text,
        "engine": engine,
        "confidence": confidence,
    }
