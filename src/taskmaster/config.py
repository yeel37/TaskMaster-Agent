"""
TaskMaster-Agent 配置
支持三种运行模式：demo（无LLM）、ollama（本地免费）、openai/grok（云端）
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 健壮项目根目录发现（从 src/taskmaster/config.py 向上找）
_p = Path(__file__).resolve()
PROJECT_ROOT = _p
for _ in range(7):
    if (PROJECT_ROOT / "data" / "sandbox").exists():
        break
    PROJECT_ROOT = PROJECT_ROOT.parent
else:
    # 最后回退：使用当前文件位置推断
    PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
TASKS_DIR = PROJECT_ROOT / "tasks"
TASKS_DIR.mkdir(exist_ok=True)
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# LLM 后端选择
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "demo").lower()  # demo | ollama | openai | grok

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROK_API_KEY = os.getenv("GROK_API_KEY", "") or os.getenv("XAI_API_KEY", "")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")  # 或 llama3.1:8b，中文友好

ENABLED_TOOLS = ["file_organizer", "web_search", "data_analysis", "reminder", "report"]

print(f"[TaskMaster] 模式: {LLM_PROVIDER} | 已启用工具: {', '.join(ENABLED_TOOLS)}")
