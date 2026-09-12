import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

try:
    import cv2
    import pytesseract
    from PIL import Image
    VISION = True
except ImportError:
    VISION = False

from facelessyt.visual_research import analyse, check_image, fetch_thumbnail, MAX_BYTES


@unittest.skipUnless(VISION, "optional vision dependencies unavailable")
class VisionTests(unittest.TestCase):
    def image_bytes(self, size=(640, 360), color=(255, 0, 0)):
        buffer = io.BytesIO()
        Image.new("RGB", size, color).save(buffer, format="PNG")
        return buffer.getvalue()

    def response(self, status, raw=b"", headers=None):
        response = Mock(status_code=status, headers=headers or {})
        response.iter_content.return_value = [raw]
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        return response

    def test_uniform_red_contrast_zero_saturation_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "red.png"
            path.write_bytes(self.image_bytes())
            with patch.object(pytesseract, "get_tesseract_version", side_effect=pytesseract.TesseractNotFoundError()):
                result = analyse(path)
            self.assertEqual(result["contrast_std_0_1"], 0)
            self.assertEqual(result["mean_saturation_0_1"], 1)
            self.assertIsNone(result["ocr_word_count"])
            self.assertIsNone(result["ctr"])

    def test_successful_empty_ocr_is_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "image.png"
            path.write_bytes(self.image_bytes())
            with patch.object(pytesseract, "get_tesseract_version", return_value="test"), patch.object(
                pytesseract, "image_to_data", return_value={"text": [], "conf": []}):
                result = analyse(path)
            self.assertEqual(result["ocr_status"], "ok")
            self.assertEqual(result["ocr_word_count"], 0)

    def test_fallback_and_cache_avoid_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = Mock()
            session.get.side_effect = [self.response(404), self.response(200, self.image_bytes())]
            row = {"url": "https://youtube.com/watch?v=CpMCYO2oWBI"}
            path, capture = fetch_thumbnail(row, Path(tmp), session=session)
            self.assertTrue(capture["source_url"].endswith("hqdefault.jpg"))
            fetch_thumbnail(row, Path(tmp), session=session)
            self.assertEqual(session.get.call_count, 2)
            path.write_bytes(b"corrupted")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                fetch_thumbnail(row, Path(tmp), session=session)

    def test_redirect_rejected_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = Mock()
            session.get.side_effect = [self.response(302), self.response(302)]
            with self.assertRaisesRegex(ValueError, "redirects disallowed"):
                fetch_thumbnail({"url": "https://youtu.be/CpMCYO2oWBI"}, Path(tmp), session=session)
            self.assertFalse(session.get.call_args.kwargs["allow_redirects"])

    def test_byte_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = Mock()
            session.get.side_effect = [self.response(200, headers={"Content-Length": str(MAX_BYTES + 1)})] * 2
            with self.assertRaisesRegex(ValueError, "byte limit"):
                fetch_thumbnail({"url": "https://youtu.be/CpMCYO2oWBI"}, Path(tmp), session=session)

    def test_placeholder_and_bad_image(self):
        for raw in [self.image_bytes((120, 90)), b"not an image"]:
            with self.assertRaises((ValueError, OSError)):
                check_image(raw)


if __name__ == "__main__":
    unittest.main()
