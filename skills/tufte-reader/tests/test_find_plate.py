"""python3 -m unittest discover -s skills/tufte-reader/tests —— find_plate.py 的离线测试，不访问网络。"""
import contextlib
import io
import json
import sys
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import find_plate  # noqa: E402


def page(title, width, license, mime="image/jpeg"):
    return {"title": title, "imageinfo": [{"width": width, "height": width, "mime": mime,
                                            "descriptionurl": "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"),
                                            "thumburl": "https://thumb.example/" + title[5:].replace(" ", "_"),
                                            "extmetadata": {"LicenseShortName": {"value": license}}}]}


RESP = {"query": {"pages": {"1": page("File:A.jpg", 2000, "Public domain"),
                            "2": page("File:B.jpg", 3000, "CC BY-SA 4.0"),
                            "3": page("File:C.jpg", 600, "CC0"),
                            "4": page("File:D.pdf", 4000, "Public domain", "application/pdf"),
                            "5": page("File:E.tif", 1200, "CC BY 4.0", "image/tiff"),
                            "6": page("File:F.jpg", 1500, "No restrictions")}}}


def run(argv, resp=RESP):
    out, calls = io.StringIO(), []

    def fake_urlopen(req, timeout=0):
        calls.append(req.full_url)
        if "thumb.example" in req.full_url:
            return io.BytesIO(b"\x89PNG fake")
        return io.BytesIO(json.dumps(resp).encode())

    with mock.patch("urllib.request.urlopen", fake_urlopen), contextlib.redirect_stdout(out):
        rc = find_plate.main(argv)
    return rc, out.getvalue(), calls


class FindPlateTest(unittest.TestCase):
    def test_query_has_terms_and_category(self):
        rc, out, calls = run(["dragon", "fire", "--cat", "Category:Musaeum_Hermeticum"])
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 1)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(calls[0]).query)
        self.assertEqual(q["gsrsearch"], ['dragon fire incategory:"Musaeum Hermeticum"'])
        self.assertEqual(q["gsrnamespace"], ["6"])
        self.assertEqual(q["gsrlimit"], ["20"])
        self.assertIn("tufte-reader-plate", find_plate.plate.UA)
        _, _, calls = run(["dragon", "--cat", "Theodor de Bry", "--deep", "--limit", "99"])
        q = urllib.parse.parse_qs(urllib.parse.urlparse(calls[0]).query)
        self.assertEqual(q["gsrsearch"], ['dragon deepcat:"Theodor de Bry"'])
        self.assertEqual(q["gsrlimit"], ["50"])

    def test_filters_license_width_and_mime(self):
        rc, out, _ = run(["x"])
        self.assertEqual(rc, 0)
        self.assertIn("结果  6 个，可用 3 个", out)
        self.assertIn("| 2000×2000 | Public domain | File:A.jpg | https://commons.wikimedia.org/wiki/File:A.jpg |", out)
        self.assertIn("| 1500×1500 | No restrictions | File:F.jpg |", out)
        self.assertIn("| 1200×1200 | CC BY 4.0 | File:E.tif |", out)
        for absent in ("File:B.jpg", "File:C.jpg", "File:D.pdf"):
            self.assertNotIn(absent, out)
        self.assertLess(out.index("File:A.jpg"), out.index("File:E.tif"))  # 宽的排前面

    def test_all_lists_rejects_with_reasons(self):
        rc, out, _ = run(["x", "--all", "--min-width", "800"])
        self.assertEqual(rc, 0)
        self.assertIn("可用 3 个（许可可用且宽度不小于 800px）", out)
        self.assertIn("File:B.jpg ✗ 许可 CC BY-SA 4.0 |", out)
        self.assertIn("File:C.jpg ✗ 只有 600px |", out)
        self.assertIn("File:D.pdf ✗ 不是图片（application/pdf） |", out)

    def test_no_results_hint(self):
        rc, out, _ = run(["x", "--min-width", "9000"])
        self.assertEqual(rc, 0)
        self.assertIn("可用 0 个", out)
        self.assertIn("加 --all", out)
        self.assertNotIn("| 宽×高", out)

    def test_help_and_category_only(self):
        rc, out, calls = run(["--help"])
        self.assertEqual((rc, calls), (0, []))
        self.assertIn("find_plate.py 关键词", out)
        rc, out, calls = run(["--cat", "Agostino Ramelli"])
        self.assertEqual(rc, 0)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(calls[0]).query)
        self.assertEqual(q["gsrsearch"], ['incategory:"Agostino Ramelli"'])
        self.assertEqual(q["iiurlwidth"], ["320"])

    def test_duplicates_keep_widest(self):
        resp = {"query": {"pages": {"1": page("File:Plate 7.jpg", 1200, "Public domain"),
                                    "2": page("File:Plate 7.tif", 3000, "Public domain", "image/tiff"),
                                    "3": page("File:Other.jpg", 1500, "CC0")}}}
        rc, out, _ = run(["x"], resp)
        self.assertIn("结果  2 个，可用 2 个", out)
        self.assertIn("| 3000×3000 | Public domain | File:Plate 7.tif |", out)
        self.assertNotIn("File:Plate 7.jpg", out)

    def test_thumb_downloads_shown_rows(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d, mock.patch.object(find_plate.shutil, "which", return_value=None):
            rc, out, calls = run(["x", "--thumb", d])  # 假缩略图不是真图片，不拼总览
            self.assertEqual(rc, 0)
            got = sorted(p.name for p in Path(d).glob("*.jpg"))
            self.assertEqual(got, ["01-a.jpg", "02-f.jpg", "03-e.jpg"])  # 只下载合格的三幅，按表格顺序编号
            self.assertEqual(sum("thumb.example" in c for c in calls), 3)
            self.assertIn("缩略图  3 张", out)

    def test_usage_errors_do_not_touch_network(self):
        for argv in ([], ["--deep"], ["x", "--min-width", "big"], ["x", "--limit", ""]):
            rc, out, calls = run(argv)
            self.assertEqual(rc, 2, argv)
            self.assertEqual(calls, [], argv)
            self.assertIn("find_plate.py", out)


if __name__ == "__main__":
    unittest.main()
