"""
Document Processing & File Extraction Unit Tests.
Matches fileExtraction.test.js from original Express implementation.
"""

from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from document_processing.textract_service import extract_file_content

def build_minimal_text_pdf(text="Verified Document Telemetry Text"):
    text_bytes = f"BT\n/F1 24 Tf\n100 700 Td\n({text}) Tj\nET\n".encode()
    objs = [
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n",
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n",
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R>> endobj\n",
        b"4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n",
        f"5 0 obj <</Length {len(text_bytes)}>> stream\n".encode() + text_bytes + b"endstream\nendobj\n",
    ]
    header = b"%PDF-1.4\n"
    body = b"".join(objs)
    offsets = [0]
    cur = len(header)
    for obj in objs:
        offsets.append(cur)
        cur += len(obj)

    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode()

    trailer = f"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n{len(header) + len(body)}\n%%EOF\n".encode()
    return header + body + xref + trailer

class FileExtractionUnitTests(TestCase):
    def test_extract_plain_text_file(self):
        text_content = b"Official announcement: Central scientific authority releases verified telemetry on polar ice caps."
        file_obj = SimpleUploadedFile(
            name="press_release.txt",
            content=text_content,
            content_type="text/plain",
        )
        res = extract_file_content(file_obj)
        self.assertEqual(res["engine"], "Text Buffer Reader")
        self.assertIn("Central scientific authority", res["text"])

    def test_extract_pdf_document(self):
        pdf_data = build_minimal_text_pdf("Verified Document Telemetry Text")
        file_obj = SimpleUploadedFile(
            name="test_doc.pdf",
            content=pdf_data,
            content_type="application/pdf",
        )
        res = extract_file_content(file_obj)
        self.assertEqual(res["engine"], "PDF Document Parser")
        self.assertIn("Verified Document Telemetry Text", res["text"])

    def test_unsupported_file_type_raises_error(self):
        file_obj = SimpleUploadedFile(
            name="video.mp4",
            content=b"dummy video data",
            content_type="video/mp4",
        )
        with self.assertRaises(ValueError) as ctx:
            extract_file_content(file_obj)
        self.assertIn("Unsupported file type", str(ctx.exception))
