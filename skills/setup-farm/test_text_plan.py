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
        self.env = {"HOME": str(self.project), "FARM_PAIRS": ""}
        self.pi = self.project / "pi"
        self.brief = self.project / ".farm/edit-brief.md"
        self.brief.parent.mkdir()
        self.brief.write_text("# 修改标题\n\n## 目标\n更新标题\n\n## 背景与相关文件\nREADME.md\n\n## 边界\n只改标题\n\n## 验收命令\nhead -1 README.md\n\n## 报告\n写入 .farm/edit-report.md\n\n## 停止条件\n超出范围时停止\n")

    def run_entry(self, script, *args):
        return subprocess.run([sys.executable, SKILLS / script, *args], cwd=self.project,
                              env={**os.environ, **self.env, "PATH": str(self.project),
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
            "codex": [{"slug": "visible", "visibility": "list", "input_modalities": ["text", "image"],
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

        session = self.project / "session.json"
        entries = [{"entry": "herdr-pane", "harness": harness, "launch": "herdr agent start",
                    "completion": "herdr agent prompt --wait", "variant_input": "fixture effort option"}
                   for harness in ("codex", "grok")]
        session.write_text(json.dumps({"scope": str(self.project), "entries": entries}))
        result = self.run_entry("farm/entry_plan.py", self.brief, "--session", session, "--pane",
                                "--model", "visible", "--variant", "high", "--select",
                                "herdr-pane", "codex", "--reason", "复用已核对的 Codex pane")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual({c["harness"] for c in data["candidates"]}, {"codex", "grok"})
        self.assertEqual(data["plan"]["variant_input"], "fixture effort option")
        self.assertEqual(data["plan"]["variant"], "high")

    def test_session_selection_uses_current_entry_evidence(self):
        self.install_pi("echo 'provider model context max-out thinking images'\necho 'demo text 1M 32K yes no'")
        self.assertEqual(self.catalog().returncode, 0)
        session = self.project / "session.json"
        native = {"entry": "native", "harness": "opencode", "launch": "subagent",
                  "completion": "completion notification", "variant_input": "subagent.model=id#variant",
                  "models": [{"id": "demo/text", "thinking_levels": ["high"]}]}
        headless = {"entry": "headless", "harness": "pi", "launch": "headless.sh run",
                    "completion": "headless.sh wait"}
        session.write_text(json.dumps({"scope": str(self.project), "entries": [headless, native]}))

        def plans(*args):
            return self.run_entry("farm/entry_plan.py", self.brief, "--session", session,
                                  "--model", "demo/text", *args)

        result = plans()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({r["entry"] for r in json.loads(result.stdout)["candidates"]},
                         {"headless", "native"})
        result = plans("--variant", "high", "--select", "native", "opencode",
                       "--reason", "当前原生入口支持指定档位")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)["plan"]
        self.assertEqual((plan["model"], plan["variant"], plan["reason"]),
                         ("demo/text", "high", "当前原生入口支持指定档位"))
        self.assertNotEqual(plans("--pane").returncode, 0)
        unavailable = plans("--variant", "HIGH")
        self.assertNotEqual(unavailable.returncode, 0)
        self.assertIn("未公布档位 HIGH", json.loads(unavailable.stdout)["excluded"][1]["error"])
        del native["variant_input"]
        session.write_text(json.dumps({"scope": str(self.project), "entries": [native]}))
        rejected = plans("--variant", "high")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("指定档位", json.loads(rejected.stdout)["excluded"][0]["error"])

    def test_pane_plan_refreshes_models_and_reports_each_unavailable_entry(self):
        session = self.project / "session.json"
        pane = {"entry": "herdr-pane", "harness": "pi", "launch": "herdr agent start",
                "completion": "herdr agent prompt --wait"}
        entries = [pane, {**pane, "harness": "grok", "error": "缓存读取失败"},
                   {**pane, "harness": "codex", "completion": ""},
                   {**pane, "harness": "claude", "launch": ""},
                   {**pane, "entry": "headless"}]
        session.write_text(json.dumps({"scope": str(self.project), "entries": entries}))
        for model in ("before", "after"):
            self.install_pi("echo 'provider model'\necho 'demo " + model + "'")
            self.assertEqual(self.catalog().returncode, 0)
            result = self.run_entry("farm/entry_plan.py", self.brief, "--session", session, "--pane")
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual([(c["entry"], c["model"]) for c in data["candidates"]],
                             [("herdr-pane", "demo/" + model)])
            self.assertEqual({r["error"] for r in data["excluded"]},
                             {"缓存读取失败", "缺少完成信号", "缺少启动", "需要可见 Herdr pane"})
        result = self.run_entry("farm/entry_plan.py", self.brief, "--session", session,
                                "--model", "demo/before", "--pane")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("demo/before", json.loads(result.stdout)["excluded"][0]["error"])

    def test_named_pi_from_claude_in_herdr_with_missing_pairs(self):
        self.env.update(FARM_PAIRS=str(self.project / "missing"), HERDR_ENV="1")
        self.install_pi("echo 'provider model thinking images'\necho 'demo vision no yes'")
        (self.project / "python3").symlink_to(sys.executable)
        herdr = self.project / "herdr"
        herdr.write_text('#!/bin/sh\n[ "$*" = "integration status" ]\n')
        herdr.chmod(0o755)
        env = {**self.env, "PATH": os.pathsep.join((str(self.project), os.defpath))}
        command = ["/bin/bash", SKILLS / "farm/preflight.sh"]
        preflight = subprocess.run([*command, "--named"], cwd=self.project, env=env,
                                   text=True, capture_output=True)
        self.assertEqual(preflight.returncode, 0, preflight.stderr)
        self.assertEqual(json.loads(preflight.stdout)["mux"], "herdr")
        self.assertIn("pi", json.loads(preflight.stdout)["clis"])
        fixed = subprocess.run(command, cwd=self.project, env=env, text=True, capture_output=True)
        self.assertNotEqual(fixed.returncode, 0)
        self.assertIn(self.env["FARM_PAIRS"], fixed.stderr)
        self.assertEqual(self.catalog().returncode, 0)
        self.brief.write_text("# 核对截图\n输入类型：local-image\n")
        session = self.project / "session.json"
        session.write_text(json.dumps({"scope": str(self.project), "entries": [{
            "entry": "headless", "harness": "pi", "launch": "headless.sh run",
            "completion": "headless.sh wait",
            "local_image": {"method": "read", "source": "fixture"}
        }]}))
        selected = self.run_entry("farm/entry_plan.py", self.brief, "--session", session,
                                  "--orchestrator", "claude:opus", "--named", "headless", "pi",
                                  "--select", "headless", "pi", "--model", "demo/vision",
                                  "--reason", "读取本地截图")
        self.assertEqual(selected.returncode, 0, selected.stderr + selected.stdout)
        plan = json.loads(selected.stdout)["plan"]
        self.assertEqual((plan["entry"], plan["harness"], plan["completion"], plan["source"]["kind"]),
                         ("headless", "pi", "headless.sh wait", "named"))

        # 按确认计划走无头启动、等待和单 worker 返工，用替身记录 Pi 实际收到的参数。
        self.pi.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
        headless = ["/bin/sh", SKILLS / "farm/headless.sh"]
        for continuation in ([], ["-c"]):
            for suffix in ("pid", "exit", "pgid"):
                (self.brief.parent / f"edit.{suffix}").unlink(missing_ok=True)
            subprocess.run([*headless, "run", "edit", plan["model"], *continuation],
                           cwd=self.project, env=env, check=True)
            waited = subprocess.run([*headless, "wait", "edit"], cwd=self.project, env=env,
                                    text=True, capture_output=True, check=True)
            self.assertEqual(waited.stdout.strip(), "done 0")
            argv = (self.brief.parent / "edit.log").read_text().splitlines()
            self.assertEqual(argv, ["-p", *continuation, "--model", "demo/vision",
                                    f"读 {self.brief} 并执行,报告按其中要求落盘"])

    def test_pairs_in_brief_plans_survive_refresh(self):
        self.install_pi("echo 'provider model'\necho 'demo short'")
        session = self.project / "session.json"
        native = {"entry": "native", "harness": "opencode", "launch": "subagent",
                  "completion": "result", "variant_input": "model#variant",
                  "models": [{"id": "demo/text", "thinking_levels": ["high"]}]}
        session.write_text(json.dumps({"scope": str(self.project), "entries": [
            native, {"entry": "headless", "harness": "pi", "launch": "run", "completion": "wait"}]}))
        default = self.project / ".config/farm/pairs"
        default.parent.mkdir(parents=True)
        default.write_text("* = pi:short")
        override = self.project / 'my "pairs"'
        mappings = "* = pi:short\npi:* = opencode:demo/text\npi:main = opencode:demo/text#high"
        override.write_text(mappings)

        def run(host, *args):
            return self.run_entry("farm/entry_plan.py", self.brief, "--session", session,
                                  "--orchestrator", host, *args)

        for setting in ("", str(override)):
            self.env["FARM_PAIRS"] = setting
            self.assertEqual(self.catalog().returncode, 0)
            self.assertEqual(default.read_text(), "* = pi:short")
            self.assertEqual(override.read_text(), mappings)
        for path, host, key, entry, harness, model, variant in [
                (default, "pi:main", "*", "headless", "pi", "demo/short", None),
                (override, "pi:main", "pi:main", "native", "opencode", "demo/text", "high"),
                (override, "pi:other", "pi:*", "native", "opencode", "demo/text", None),
                (override, "codex:other", "*", "headless", "pi", "demo/short", None)]:
            self.env["FARM_PAIRS"] = "" if path == default else str(path)
            result = run(host, "--select", entry, harness, "--model", model, "--reason", "固定映射")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            plan = json.loads(result.stdout)["plan"]
            self.assertEqual((plan["source"]["file"], plan["source"]["key"]), (str(path), key))
            self.assertEqual(plan["variant"], variant)

        named = run("pi:main", "--named", "headless", "pi", "--model", "demo/short",
                    "--select", "headless", "pi", "--reason", "本次点名")
        self.assertEqual(json.loads(named.stdout)["plan"]["source"]["kind"], "named")
        for args, reason in [(("--pane",), "可见"), (("--named", "native", "opencode",
                              "--model", "demo/gone"), "demo/gone")]:
            result = run("pi:main", *args)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(reason, result.stdout)
            self.assertNotIn("plan", json.loads(result.stdout))
        override.write_text("* = pi:demo/retired")
        stale = run("pi:main")
        self.assertNotEqual(stale.returncode, 0)
        self.assertIn("目录中没有固定模型：demo/retired", stale.stdout)
        override.unlink()
        missing = run("pi:main")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn(str(override), missing.stderr)
        model_only = run("pi:main", "--named", "--model", "demo/short")
        self.assertEqual(json.loads(model_only.stdout)["source"]["kind"], "named")
        override.write_text("other:* = pi:short")
        for setting in (str(override), ""):
            self.env["FARM_PAIRS"] = setting
            if not setting:
                default.unlink()
            result = json.loads(run("pi:main").stdout)
            self.assertEqual(result["source"]["kind"], "task")
            self.assertEqual(len(result["candidates"]), 2)

        session.write_text(json.dumps({"scope": str(self.project), "entries": []}))
        empty = run("pi:main", "--named", "native", "opencode", "--model", "demo/text")
        self.assertNotEqual(empty.returncode, 0)
        self.assertIn("会话清单没有入口", json.loads(empty.stdout)["error"])

    def test_screenshot_requires_model_and_local_image_delivery(self):
        self.install_pi("echo 'provider model images'\necho 'demo text no'\necho 'demo mystery ?'\necho 'demo vision yes'")
        catalog = json.loads(self.catalog().stdout)
        screenshot = self.brief.with_name("screen-brief.md")
        screenshot.write_text("# 核对截图\n\n输入类型：local-image\n\n## 目标\n读取 screen.png 的标题。\n")
        session = self.project / "session.json"
        row = {"entry": "headless", "harness": "pi", "launch": "run", "completion": "wait"}

        def plans(brief, *args):
            session.write_text(json.dumps({"scope": str(self.project), "entries": [row]}))
            result = self.run_entry("farm/entry_plan.py", brief, "--session", session, *args)
            return result.returncode, json.loads(result.stdout)

        status, blocked = plans(screenshot)
        self.assertNotEqual(status, 0)
        errors = {r["model"]: r["error"] for r in blocked["excluded"]}
        self.assertIn("未知", errors["demo/mystery"])
        self.assertIn("不支持", errors["demo/text"])
        self.assertIn("取得", errors["demo/vision"])
        row["local_image"] = {"method": "read 工具读取 brief 中的路径", "source": "夹具工具清单"}
        status, valid = plans(screenshot)
        self.assertEqual(status, 0)
        self.assertEqual([c["model"] for c in valid["candidates"]], ["demo/vision"])
        self.assertEqual(valid["candidates"][0]["input"]["delivery"], row["local_image"])
        self.assertEqual(valid["candidates"][0]["input"]["capability"]["source"], catalog["source"])
        self.assertEqual(valid["candidates"][0]["input"]["capability"]["basis"], "catalog")

        self.brief.write_text(self.brief.read_text() + "\n示例：\n```\n输入类型：CSV\n```\n")
        files = []
        for brief, model, reason in [(self.brief, "demo/text", "修改标题"), (screenshot, "demo/vision", "读取截图")]:
            status, selected = plans(brief, "--select", "headless", "pi", "--model", model, "--reason", reason)
            self.assertEqual(status, 0)
            path = brief.with_suffix(".json")
            path.write_text(json.dumps(selected))
            files.append(path)
        result = self.run_entry("farm/pool_plan.py", "-j", "1", *files)
        self.assertEqual(result.returncode, 0, result.stderr)
        queue = json.loads(result.stdout)
        self.assertEqual(queue["max_active"], 1)
        self.assertEqual([(p["model"], p["reason"]) for p in queue["queue"]],
                         [("demo/text", "修改标题"), ("demo/vision", "读取截图")])

        for state, expected in [([], ["demo/text"]), (["--active", self.brief], []),
                                (["--passed", self.brief], ["demo/vision"])]:
            result = self.run_entry("farm/pool_plan.py", "-j", "1", *state, *files)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual([p["model"] for p in json.loads(result.stdout)["ready"]], expected)

        row["verified_inputs"] = {"demo/vision": {"local-image": {
            "status": "unsupported", "method": "另一工具", "source": "夹具读图报告"}}}
        self.assertEqual(plans(screenshot)[0], 0)
        row["verified_inputs"]["demo/vision"]["local-image"]["method"] = row["local_image"]["method"]
        status, blocked = plans(screenshot)
        self.assertNotEqual(status, 0)
        self.assertIn("夹具读图报告", blocked["excluded"][-1]["error"])

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
