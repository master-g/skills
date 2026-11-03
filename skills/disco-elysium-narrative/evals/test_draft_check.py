#!/usr/bin/env python3
"""draft_check.py 界面层字段的夹具测试。用法：python3 test_draft_check.py"""
import tempfile
from pathlib import Path

from draft_check import check

SCENE = """**逻辑思维**【成功】 — 他在拖时间。

> **你** — 我先去把锁等待查清楚。

新任务:查清锁等待

值班同事 — “查吧。”他没抬头。
"""
BRACKET = SCENE + "\n[雨刷还在摆]\n[你没有下车]\n"
CRISIS_OK = "你说这周一直站在阳台上想这件事，我听到了。你现在安全吗？\n"
CRISIS_UI = CRISIS_OK + "\n新任务:给信任的人打电话\n"


def run(text):
    with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False) as f:
        f.write(text)
    try:
        return check(f.name)
    finally:
        Path(f.name).unlink()


def main():
    r = run(SCENE)
    assert r['task_lines'] == 1 and not r['bracket_ending'] and not r['crisis_ui_leak'], r
    r = run(BRACKET)
    assert r['bracket_ending'], r
    r = run(CRISIS_OK)
    assert r['task_lines'] == 0 and not r['crisis_ui_leak'] and not r['crisis_leak'], r
    r = run(CRISIS_UI)
    assert r['crisis_ui_leak'] and r['task_lines'] == 1, r
    assert run('> 任务完成：查清锁等待\n')['task_lines'] == 1
    print('test_draft_check: ok')


if __name__ == '__main__':
    main()
