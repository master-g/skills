"""从项目目录运行两个技能的公开入口。"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILLS = Path(__file__).resolve().parents[1]


class TextPlan(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.project = Path(temp.name).resolve()
        self.pi = self.project / "pi"
        self.brief = self.project / ".farm/edit-brief.md"
        self.brief.parent.mkdir()
        self.brief.write_text("# 修改标题\n\n## 目标\n更新标题\n\n## 背景与相关文件\nREADME.md\n\n## 边界\n只改标题\n\n## 验收命令\nhead -1 README.md\n\n## 报告\n写入 .farm/edit-report.md\n\n## 停止条件\n超出范围时停止\n")

    def run_entry(self, script, *args):
        return subprocess.run([sys.executable, SKILLS / script, *args], cwd=self.project,
                              env={**os.environ, "PATH": str(self.project),
                                   "CODEX_HOME": str(self.project / "codex-dir"),
                                   "GROK_HOME": str(self.project / "grok-dir")},
                              text=True, capture_output=True)

    def catalog(self):
        return self.run_entry("setup-farm/discover.py", "--harness", "pi")

    def plan(self):
        return self.run_entry("farm/text_plan.py", self.brief, "demo/text", "可完成标题修改")

    def install_pi(self, command):
        self.pi.write_text('#!/bin/sh\n[ "$*" = "--list-models" ] || exit 64\n' + command)
        self.pi.chmod(0o755)

    def test_refresh_replaces_previous_candidates_with_diagnostic(self):
        for command, message in [(None, "未找到 pi"), ("exit 17", "17"),
                                 ("echo 'provider model context max-out thinking images'", "没有可用模型")]:
            with self.subTest(command=command):
                self.install_pi("echo 'provider model context max-out thinking images'\necho 'demo text 1M 32K no no'")
                previous = json.loads(self.catalog().stdout)
                self.assertIs(previous["models"][0]["thinking_supported"], False)
                self.pi.unlink()
                if command:
                    self.install_pi(command)
                result = self.catalog()
                self.assertNotEqual(result.returncode, 0)
                catalog = json.loads(result.stdout)
                self.assertEqual(json.loads((self.project / ".farm/pi-catalog.json").read_text())["models"], [])
                self.assertIn(message, catalog["error"])
                self.assertEqual(bool(catalog["binary"]), bool(command))
                self.assertIn(message, self.plan().stderr)

    def test_cached_directories_generate_separate_pane_plans(self):
        fixtures = {
            "codex": [{"slug": "visible", "visibility": "list", "input_modalities": ["image"],
                       "supported_reasoning_levels": [{"effort": "high"}]},
                      {"slug": "hidden", "visibility": "hide"}],
            "grok": {"visible": {"info": {"hidden": False, "reasoning_efforts": [{"id": "high"}]},
                                 "api_key": "fixture-secret"},
                     "hidden": {"info": {"hidden": True}}},
        }
        for name, models in fixtures.items():
            binary = self.project / name
            binary.write_text("#!/bin/sh\nexit 99\n")
            binary.chmod(0o755)
            directory = self.project / (name + "-dir")
            directory.mkdir()
            (directory / "models_cache.json").write_text(json.dumps({"models": models, "fetched_at": "sample"}))
        result = self.run_entry("setup-farm/discover.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("fixture-secret", result.stdout)
        pi, codex, grok = json.loads(result.stdout)
        self.assertIn("error", pi)
        for catalog in (codex, grok):
            self.assertEqual([m["id"] for m in catalog["models"]], ["visible"])
            model = catalog["models"][0]
            self.assertEqual(model["thinking_levels"], ["high"])
            self.assertIs(model["images"], True if catalog == codex else None)
            result = self.run_entry("farm/text_plan.py", "--harness", catalog["harness"],
                                    self.brief, "visible", "文本任务")
            self.assertEqual(result.returncode, 0, result.stderr)
            plan = json.loads(result.stdout)
            self.assertEqual((plan["entry"], plan["harness"]), ("herdr-pane", catalog["harness"]))

    def test_plan_from_catalog(self):
        self.install_pi("echo 'provider model context max-out thinking images'\necho 'demo text 1M 32K yes no'")
        catalog = self.catalog()
        self.assertEqual(catalog.returncode, 0, catalog.stderr)
        model = json.loads(catalog.stdout)["models"][0]
        self.assertEqual(model["id"], "demo/text")
        self.assertIsNone(model["thinking_levels"])
        result = self.plan()
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan["task"], "修改标题")
        self.assertEqual(plan["location"], str(self.project))
        self.assertEqual(plan["entry"], "headless")
        self.assertEqual(plan["harness"], "pi")
        self.assertEqual(plan["model"], "demo/text")
        self.assertEqual(plan["thinking"], "Pi 默认")
        self.assertEqual(plan["reason"], "可完成标题修改")


if __name__ == "__main__":
    unittest.main()
