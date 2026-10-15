"""python3 -m unittest discover -s skills/tufte-reader/tests —— plate.py 的离线测试，不访问网络。"""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import plate  # noqa: E402


def rec(license="Public domain", attribution=False, artist="Michael Maier"):
    return {"title": "File:X.jpeg", "page": "https://commons.wikimedia.org/wiki/File:X.jpeg", "license": license,
            "attribution_required": attribution, "artist": artist, "credit": "", "date": "1617", "fetched": "2026-10-14"}


class PlateTest(unittest.TestCase):
    def test_help_exits_zero_without_network(self):
        out = io.StringIO()
        with mock.patch("urllib.request.urlopen") as net, contextlib.redirect_stdout(out):
            self.assertEqual(plate.main(["--help"]), 0)
            self.assertEqual(plate.main(["File:X.jpeg", "--region", "bad"]), 2)
        net.assert_not_called()
        self.assertIn("plate.py 来源", out.getvalue())

    def test_crop_geometry(self):
        self.assertEqual(plate.crop_geometry(2000, 1000, "pct:10,20,50,25"), "1000x250+200+200")
        self.assertEqual(plate.crop_geometry(3000, 4000, "pct:2.9,18.1,75.5,52.8"), "2265x2112+87+724")

    def test_region_asks_commons_for_enough_pixels(self):
        seen = {}

        def fake_query(title, width):
            seen["width"] = width
            raise LookupError("stop here")  # 只验证请求宽度，不往下走

        out = io.StringIO()
        with mock.patch.object(plate, "query", fake_query), contextlib.redirect_stdout(out):
            self.assertEqual(plate.main(["File:X.jpeg", "--region", "pct:10,10,40,50"]), 1)
        self.assertEqual(seen["width"], 2500)  # 1000 / 40%

    @unittest.skipUnless(plate.shutil.which("magick"), "需要 ImageMagick")
    def test_shrink_flattens_alpha_and_rejects_blank(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            # 透明底的灰度 PNG：黑线画在透明上
            subprocess.run(["magick", "-size", "400x300", "xc:none", "-fill", "black", "-draw", "line 0,0 400,300",
                            "-draw", "circle 200,150 250,150", "-colorspace", "gray", str(d / "ga.png")], check=True)
            out = plate.shrink(d / "ga.png", d / "a", 300)
            self.assertEqual(out, d / "a.png")
            info = subprocess.run(["magick", str(out), "-format", "%[channels] %[fx:standard_deviation]", "info:"],
                                  capture_output=True, text=True, check=True).stdout.split()
            self.assertFalse(info[0].startswith("graya"), info)
            self.assertGreater(float(info[1]), 0.1)
            # 空白页：报 ERROR、不留成品
            subprocess.run(["magick", "-size", "400x300", "xc:white", str(d / "blank.png")], check=True)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertIsNone(plate.shrink(d / "blank.png", d / "b", 300))
            self.assertIn("ERROR 成品几乎是一片纯色", buf.getvalue())
            self.assertFalse((d / "b.png").exists())
            # 裁切：取左上四分之一（里面画了一条对角线，裁出来不是纯色）
            subprocess.run(["magick", "-size", "400x300", "xc:white", "-fill", "black", "-draw", "line 0,0 199,149",
                            str(d / "src.png")], check=True)
            out = plate.shrink(d / "src.png", d / "q", 1000, "pct:0,0,50,50")
            size = subprocess.run(["magick", str(out), "-format", "%w %h", "info:"], capture_output=True, text=True,
                                  check=True).stdout.split()
            self.assertEqual(size, ["200", "150"])  # 只缩不放，裁出的 200×150 原样保留

    def test_license_allowlist(self):
        self.assertEqual(plate.license_label("Public domain"), "公有领域")
        self.assertEqual(plate.license_label("PDM-owner"), "公有领域")
        self.assertEqual(plate.license_label("No restrictions"), "无已知版权限制")
        self.assertEqual(plate.license_label("CC0"), "CC0")
        self.assertEqual(plate.license_label("CC BY 4.0"), "CC BY 4.0")
        for bad in ("CC BY-SA 3.0", "CC BY-NC 4.0", "CC BY-ND 2.0", "GFDL", "", None):
            self.assertIsNone(plate.license_label(bad), bad)

    def test_plain_strips_markup(self):
        self.assertEqual(plate.plain('<span lang="en">Michael&nbsp;Maier</span>\n'), "Michael Maier")
        self.assertEqual(plate.plain("<b>Atalanta</b>  &amp; <i>Fugiens</i>"), "Atalanta & Fugiens")

    def test_snippet_public_domain(self):
        out = plate.snippet(rec(), "figures/plates/x.png")
        self.assertIn('<figure class="plate" data-source="https://commons.wikimedia.org/wiki/File:X.jpeg"', out)
        self.assertIn('data-license="Public domain"', out)
        self.assertIn("公有领域。", out)
        self.assertIn('src="figures/plates/x.png"', out)
        self.assertIn("TODO-题图", out)
        self.assertNotIn("署名", out)

    def test_snippet_cc_by_attribution(self):
        clean = plate.snippet(rec("CC BY 4.0", True, "Wellcome Collection"), "x.png")
        self.assertIn("CC BY 4.0，署名：Wellcome Collection。", clean)
        messy = plate.snippet(rec("CC BY 4.0", True, "https://wellcomeimages.org/… Gallery: …"), "x.png")
        self.assertIn("署名：TODO-题图：署名", messy)

    def test_rejected_license_downloads_nothing(self):
        info = {"descriptionurl": "https://commons.wikimedia.org/wiki/File:Y.svg", "url": "https://upload.example/y.svg",
                "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 3.0"}}}
        d = Path(tempfile.mkdtemp())
        out = io.StringIO()
        with mock.patch.object(plate, "query", return_value=("File:Y.svg", info)), \
                mock.patch.object(plate.urllib.request, "urlopen") as net, contextlib.redirect_stdout(out):
            rc = plate.main(["File:Y.svg", "-o", str(d / "plates")])
        self.assertEqual(rc, plate.EXIT_LICENSE)
        self.assertIn("CC BY-SA 3.0", out.getvalue())
        net.assert_not_called()
        self.assertFalse((d / "plates").exists())


    def test_ia_source_in_allowlist(self):
        rec, url = plate.ia_source("ia:atalantafugiensh00maie$185", "pct:3.9,19.1,73.5,50.8", 1000)
        self.assertEqual(url, "https://iiif.archive.org/iiif/atalantafugiensh00maie$185/pct:3.9,19.1,73.5,50.8/1000,/0/default.jpg")
        # 阅读器页面的叶号从 0 数，比 IIIF 少 1
        self.assertEqual(rec["page"], "https://archive.org/details/atalantafugiensh00maie/page/n184/mode/1up")
        self.assertEqual(plate.license_label(rec["license"]), "公有领域")
        out = plate.snippet(rec, "x.png")
        self.assertIn(">Internet Archive（Getty Research Institute 扫描）</a>，公有领域。", out)
        self.assertNotIn("署名", out)

    def test_ia_rejects_unlisted_item_and_bad_args(self):
        out = io.StringIO()
        with mock.patch.object(plate.urllib.request, "urlopen") as net, contextlib.redirect_stdout(out):
            self.assertEqual(plate.main(["ia:someotherbook$12", "--region", "pct:1,2,3,4"]), plate.EXIT_LICENSE)
            self.assertEqual(plate.main(["ia:atalantafugiensh00maie$185"]), 2)  # 缺 --region
            self.assertEqual(plate.main(["ia:atalantafugiensh00maie$185", "--region", "full"]), 2)
            self.assertEqual(plate.main(["ia:atalantafugiensh00maie", "--region", "pct:1,2,3,4"]), 2)  # 缺叶号
        net.assert_not_called()
        self.assertIn("不在 IA_ITEMS 白名单里", out.getvalue())

if __name__ == "__main__":
    unittest.main()
