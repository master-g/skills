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


if __name__ == "__main__":
    unittest.main()
