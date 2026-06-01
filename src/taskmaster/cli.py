#!/usr/bin/env python3
"""
TaskMaster-Agent 命令行入口
用法：
  python -m taskmaster.cli "帮我整理 sandbox 里的文件"
  python -m taskmaster.cli "搜索一下今天AI最新新闻并总结"
"""

import sys
import json
from pathlib import Path

try:
    from .agent import get_agent
    from .config import LLM_PROVIDER
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.taskmaster.agent import get_agent
    from src.taskmaster.config import LLM_PROVIDER


def print_help(exit_code=0):
    """打印零基础友好的命令行帮助。"""
    print("TaskMaster-Agent - 本地多功能 AI 智能代理")
    print(f"当前模式: {LLM_PROVIDER}")
    print("")
    print("用法:")
    print('  python -m taskmaster.cli "你的自然语言指令"')
    print("  python run_cli.py \"你的自然语言指令\"")
    print("")
    print("示例:")
    print('  python -m taskmaster.cli "整理一下 data/sandbox 里的文件"')
    print('  python -m taskmaster.cli "提醒我明天开会"')
    print('  python -m taskmaster.cli "分析一下销售数据"')
    print('  python -m taskmaster.cli "生成一份本周总结报告"')
    sys.exit(exit_code)


def main():
    if len(sys.argv) < 2:
        print_help(1)

    if sys.argv[1] in {"-h", "--help", "help"}:
        print_help(0)

    instruction = " ".join(sys.argv[1:])
    agent = get_agent()
    print(f"[TaskMaster] 正在处理: {instruction}")
    print(f"[模式] {LLM_PROVIDER}\n")

    result = agent.run(instruction)

    print("✅ 执行完成\n")
    if "llm_summary" in result:
        print("🤖 AI 总结:\n" + result["llm_summary"] + "\n")
    else:
        print("📋 执行结果:")
        print(json.dumps(result.get("final_output", {}), ensure_ascii=False, indent=2))

    print(f"\n⏱️ 耗时: {result.get('duration_sec', 0)}s")
    print("提示: 使用 streamlit run app/streamlit_app.py 体验图形聊天界面")


if __name__ == "__main__":
    main()
