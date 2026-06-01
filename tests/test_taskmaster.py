"""
TaskMaster-Agent 基础自检
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from taskmaster.agent import TaskMasterAgent


def test_demo_agent_runs():
    agent = TaskMasterAgent(provider="demo")
    res = agent.run("整理一下 sandbox 里的文件")
    assert "final_output" in res
    assert res["final_output"]["tool"] == "file_organizer"


def test_web_search_tool():
    agent = TaskMasterAgent(provider="demo")
    import taskmaster.agent as agent_module

    agent_module.HAS_DDG = False
    res = agent.run("搜索一下 Python 最新动态")
    assert "web_search" in str(res.get("final_output", {}))


def test_reminder_and_report():
    agent = TaskMasterAgent(provider="demo")
    r1 = agent.run("提醒我测试任务")
    assert r1["final_output"]["tool"] == "reminder"
    r2 = agent.run("生成报告")
    assert r2["final_output"]["tool"] == "report"


if __name__ == "__main__":
    print("Running TaskMaster self-check...")
    test_demo_agent_runs()
    test_web_search_tool()
    test_reminder_and_report()
    print("✅ TaskMaster-Agent 核心自检通过！")
