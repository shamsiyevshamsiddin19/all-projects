"""Pinterest rasm, video va giflarni yuklab olish moduli testlari."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from subtitr import media
from subtitr.pinterest import (
    download_pinterest_media,
    extract_pinterest_media,
    is_pinterest_url,
    resolve_pinterest_url,
    sanitize_filename,
)


class PinterestDownloaderTests(unittest.TestCase):
    def test_is_pinterest_url_detection(self):
        self.assertTrue(is_pinterest_url("https://www.pinterest.com/pin/123456789/"))
        self.assertTrue(is_pinterest_url("https://pinterest.com/pin/123456789/"))
        self.assertTrue(is_pinterest_url("https://pin.it/abc123X"))
        self.assertTrue(is_pinterest_url("http://uk.pinterest.com/pin/998877/"))
        self.assertFalse(is_pinterest_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertFalse(is_pinterest_url("https://instagram.com/p/Cxyz123"))
        self.assertFalse(is_pinterest_url("https://tiktok.com/@user/video/123"))
        self.assertFalse(is_pinterest_url(""))
        self.assertFalse(is_pinterest_url(None))  # type: ignore

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("Normal Title"), "Normal Title")
        self.assertEqual(sanitize_filename("File/With:Bad*Chars?"), "File_With_Bad_Chars_")
        self.assertEqual(sanitize_filename("   "), "pinterest_media")

    def test_extract_video_media(self):
        mock_html = """
        <html>
        <head>
            <title>Origami Video | Pinterest</title>
            <meta property="og:title" content="Origami Video" />
        </head>
        <body>
            <script id="__PWS_DATA__">
                {"videos": {"video_list": {"V_720P": {"url": "https://v1.pinimg.com/videos/mc/720p/abc.mp4"}}}}
            </script>
        </body>
        </html>
        """
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = mock_html.encode("utf-8")
            mock_resp.geturl.return_value = "https://www.pinterest.com/pin/12345/"
            mock_resp.__enter__.return_value = mock_resp
            mock_urlopen.return_value = mock_resp

            result = extract_pinterest_media("https://www.pinterest.com/pin/12345/")

            self.assertEqual(result["type"], "video")
            self.assertEqual(result["ext"], ".mp4")
            self.assertIn("720p/abc.mp4", result["url"])
            self.assertEqual(result["title"], "Origami Video")

    def test_extract_gif_media(self):
        mock_html = """
        <html>
        <head><title>Aesthetic Animation - Pinterest</title></head>
        <body>
            <img src="https://i.pinimg.com/736x/ab/cd/ef/abcdef.gif" />
        </body>
        </html>
        """
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = mock_html.encode("utf-8")
            mock_resp.geturl.return_value = "https://www.pinterest.com/pin/54321/"
            mock_resp.__enter__.return_value = mock_resp
            mock_urlopen.return_value = mock_resp

            result = extract_pinterest_media("https://www.pinterest.com/pin/54321/")

            self.assertEqual(result["type"], "gif")
            self.assertEqual(result["ext"], ".gif")
            self.assertIn("/originals/ab/cd/ef/abcdef.gif", result["url"])

    def test_extract_image_media_with_originals_upscale(self):
        mock_html = """
        <html>
        <head>
            <meta property="og:title" content="Beautiful Landscape" />
        </head>
        <body>
            <img src="https://i.pinimg.com/736x/11/22/33/112233.jpg" />
        </body>
        </html>
        """
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = mock_html.encode("utf-8")
            mock_resp.geturl.return_value = "https://www.pinterest.com/pin/999/"
            mock_resp.__enter__.return_value = mock_resp
            mock_urlopen.return_value = mock_resp

            result = extract_pinterest_media("https://www.pinterest.com/pin/999/")

            self.assertEqual(result["type"], "image")
            self.assertEqual(result["ext"], ".jpg")
            self.assertEqual(result["url"], "https://i.pinimg.com/originals/11/22/33/112233.jpg")
            self.assertEqual(result["title"], "Beautiful Landscape")

    def test_download_pinterest_media_file_writing_and_cache(self):
        with tempfile.TemporaryDirectory() as td:
            dest_dir = Path(td)
            fake_bytes = b"FAKE_MEDIA_CONTENT_BYTES" * 100

            mock_info = {
                "type": "image",
                "url": "https://i.pinimg.com/originals/test.png",
                "title": "Test Art",
                "ext": ".png",
                "pin_id": "777",
            }

            with (
                patch("subtitr.pinterest.extract_pinterest_media", return_value=mock_info),
                patch("urllib.request.urlopen") as mock_urlopen,
                patch("subtitr.pinterest.emit") as mock_emit,
            ):
                mock_resp = MagicMock()
                mock_resp.headers = {"Content-Length": str(len(fake_bytes))}
                mock_resp.read.side_effect = [fake_bytes, b""]
                mock_resp.__enter__.return_value = mock_resp
                mock_urlopen.return_value = mock_resp

                # 1. Yuklab olish
                res_path = download_pinterest_media(
                    "https://www.pinterest.com/pin/777/",
                    dest_dir=dest_dir,
                    use_cache=True,
                )

                self.assertTrue(res_path.exists())
                self.assertEqual(res_path.suffix, ".png")
                self.assertEqual(res_path.read_bytes(), fake_bytes)
                self.assertTrue(any("Test Art" in str(c) for c in mock_emit.call_args_list))

                # 2. Keshdan olish (qayta so'rovsiz)
                cached_path = download_pinterest_media(
                    "https://www.pinterest.com/pin/777/",
                    dest_dir=dest_dir,
                    use_cache=True,
                )
                self.assertEqual(cached_path, res_path)
                self.assertTrue(any("keshdan olindi" in str(c) for c in mock_emit.call_args_list))

    def test_media_download_video_routes_pinterest_url(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td)
            expected_out = dest / "sample.mp4"
            expected_out.write_bytes(b"sample video bytes")

            with patch("subtitr.media.download_pinterest_media", return_value=expected_out) as mock_dl:
                res = media.download_video("https://pin.it/xyz999", dest_dir=dest)
                mock_dl.assert_called_once_with(
                    "https://pin.it/xyz999",
                    dest_dir=dest,
                    use_cache=True,
                    progress_lo=0.01,
                    progress_hi=0.05,
                    quality=None,
                )
                self.assertEqual(res, expected_out)


if __name__ == "__main__":
    unittest.main()
