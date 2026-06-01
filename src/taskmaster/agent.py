"""
TaskMaster-Agent 核心智能代理
支持 demo（规则+模拟）、ollama、本地、云端 LLM
提供统一 .run(instruction) 接口，返回执行报告
所有文件操作默认 dry_run + 沙箱，安全第一
"""

import os
import re
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
try:
    from duckduckgo_search import DDGS
    HAS_DDG = True
except ImportError:
    HAS_DDG = False
    DDGS = None

from .config import (
    LLM_PROVIDER, OPENAI_API_KEY, GROK_API_KEY,
    OLLAMA_BASE_URL, OLLAMA_MODEL, TASKS_DIR, REPORTS_DIR, DATA_DIR
)

# 安全沙箱根目录（永远不会操作用户真实系统目录）
SANDBOX_ROOT = DATA_DIR / "sandbox"
SANDBOX_ROOT.mkdir(exist_ok=True)

REMINDERS_FILE = TASKS_DIR / "reminders.txt"


class TaskMasterAgent:
    """多功能本地 AI Agent 主类"""

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or LLM_PROVIDER
        self.llm = None
        self._init_llm()

    def _init_llm(self):
        """按优先级初始化 LLM（失败自动降级）"""
        if self.provider == "demo":
            print("[Agent] Demo 模式启动 - 无需 LLM，规则引擎将模拟智能决策")
            return

        try:
            if self.provider == "ollama":
                from langchain_ollama import ChatOllama
                self.llm = ChatOllama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL, temperature=0.2)
                print(f"[Agent] 已连接 Ollama: {OLLAMA_MODEL}")
            elif self.provider in ("openai", "grok"):
                from langchain_openai import ChatOpenAI
                key = OPENAI_API_KEY if self.provider == "openai" else GROK_API_KEY
                base = "https://api.openai.com/v1" if self.provider == "openai" else "https://api.x.ai/v1"
                model = "gpt-4o-mini" if self.provider == "openai" else "grok-2-1212"
                self.llm = ChatOpenAI(api_key=key, base_url=base, model=model, temperature=0.3)
                print(f"[Agent] 已连接 {self.provider} LLM")
            else:
                self.provider = "demo"
        except Exception as e:
            print(f"[Agent] LLM 初始化失败 ({e})，自动降级到 demo 模式")
            self.provider = "demo"
            self.llm = None

    # ==================== 工具实现（全部安全） ====================

    def tool_file_organizer(self, target_dir: str = "sandbox", dry_run: bool = True) -> Dict[str, Any]:
        """文件整理工具 - 按扩展名 + 日期归档"""
        src = SANDBOX_ROOT if "sandbox" in target_dir else Path(target_dir).expanduser()
        if not src.exists():
            return {"error": f"目录不存在: {src}", "action": "none"}

        moved = []
        for f in src.iterdir():
            if not f.is_file() or f.name.startswith("."):
                continue
            ext = f.suffix.lower().lstrip(".") or "other"
            date_folder = datetime.now().strftime("%Y-%m")
            dest_dir = src / f"_organized_{ext}" / date_folder
            if not dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(f), str(dest_dir / f.name))
            moved.append(f"{f.name} → {dest_dir.name}/")

        return {
            "tool": "file_organizer",
            "scanned": str(src),
            "moved_count": len(moved),
            "details": moved[:8],
            "dry_run": dry_run,
            "note": "实际执行请设置 dry_run=False（谨慎操作）"
        }

    def tool_web_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """网页搜索 + 简单总结（duckduckgo，无 key）"""
        if not HAS_DDG:
            return {
                "tool": "web_search",
                "query": query,
                "error": "duckduckgo-search 未安装",
                "fallback": "已降级：请 pip install duckduckgo-search 或直接使用浏览器搜索",
                "demo_result": f"（演示）关于「{query}」的搜索结果：最新AI工具层出不穷，建议关注 LangChain、Ollama 等本地部署方案。"
            }
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            summary = "\n".join([f"- {r.get('title','')}: {r.get('body','')[:120]}..." for r in results[:3]])
            return {
                "tool": "web_search",
                "query": query,
                "results_count": len(results),
                "summary": summary or "未找到有效结果",
                "sources": [r.get("href", "") for r in results[:3]]
            }
        except Exception as e:
            return {"tool": "web_search", "error": str(e), "fallback": "网络错误，请稍后重试"}

    def tool_data_analysis(self, csv_name: str = "sample_sales.csv") -> Dict[str, Any]:
        """简单数据分析（内置样例或用户 data/ 下的 csv）"""
        path = DATA_DIR / csv_name
        if not path.exists():
            # 生成迷你样例
            df = pd.DataFrame({
                "date": pd.date_range("2025-01-01", periods=8, freq="W"),
                "sales": [1200, 1350, 980, 1500, 1420, 1680, 1100, 1750],
                "category": ["A"]*4 + ["B"]*4
            })
            df.to_csv(path, index=False)
        df = pd.read_csv(path)
        return {
            "tool": "data_analysis",
            "file": str(path),
            "rows": len(df),
            "columns": list(df.columns),
            "summary": {
                "sales_mean": float(df["sales"].mean()) if "sales" in df.columns else None,
                "latest": df.tail(2).to_dict("records")
            }
        }

    def tool_reminder(self, task: str, when: str = "明天") -> Dict[str, Any]:
        """添加提醒（写入本地文件）"""
        REMINDERS_FILE.parent.mkdir(exist_ok=True)
        entry = f"[{datetime.now().isoformat()}] {when} - {task}\n"
        with open(REMINDERS_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        return {
            "tool": "reminder",
            "saved": entry.strip(),
            "file": str(REMINDERS_FILE),
            "all_reminders": REMINDERS_FILE.read_text(encoding="utf-8").splitlines()[-5:] if REMINDERS_FILE.exists() else []
        }

    def tool_generate_report(self, topic: str = "本周任务总结") -> Dict[str, Any]:
        """生成 Markdown 报告"""
        report = f"""# {topic}
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 已完成
- 使用 TaskMaster-Agent 完成了文件整理
- 执行了网页搜索与数据分析

## 待办（来自提醒）
{REMINDERS_FILE.read_text(encoding="utf-8")[-500:] if REMINDERS_FILE.exists() else '（暂无）'}

---
*由 TaskMaster-Agent 自动生成*
"""
        out = REPORTS_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        out.write_text(report, encoding="utf-8")
        return {"tool": "report", "path": str(out), "preview": report[:300] + "..."}

    # ==================== 指令路由与执行 ====================

    def _parse_intent(self, instruction: str) -> Dict[str, Any]:
        """简单意图解析（demo 模式核心 + LLM 辅助）"""
        text = instruction.lower()
        if any(k in text for k in ["整理", "文件", "下载", "归档", "organize", "move"]):
            return {"action": "file_organizer", "params": {"target_dir": "sandbox", "dry_run": True}}
        if any(k in text for k in ["搜索", "查", "总结", "web", "search", "news"]):
            q = instruction
            return {"action": "web_search", "params": {"query": q}}
        if any(k in text for k in ["分析", "数据", "csv", "sales", "report"]):
            return {"action": "data_analysis", "params": {"csv_name": "sample_sales.csv"}}
        if any(k in text for k in ["提醒", "提醒我", "todo", "remind"]):
            return {"action": "reminder", "params": {"task": instruction, "when": "今天"}}
        if any(k in text for k in ["报告", "总结", "generate"]):
            return {"action": "report", "params": {"topic": instruction}}
        return {"action": "web_search", "params": {"query": instruction}}  # 默认搜索

    def run(self, instruction: str) -> Dict[str, Any]:
        """主入口：执行自然语言指令"""
        start = datetime.now()
        result = {
            "instruction": instruction,
            "provider": self.provider,
            "started_at": start.isoformat(),
            "steps": []
        }

        intent = self._parse_intent(instruction)
        result["steps"].append({"step": "intent", "result": intent})

        action = intent["action"]
        params = intent.get("params", {})

        # 执行对应工具
        if action == "file_organizer":
            out = self.tool_file_organizer(**params)
        elif action == "web_search":
            out = self.tool_web_search(**params)
        elif action == "data_analysis":
            out = self.tool_data_analysis(**params)
        elif action == "reminder":
            out = self.tool_reminder(**params)
        elif action == "report":
            out = self.tool_generate_report(**params)
        else:
            out = {"error": "未知动作"}

        result["steps"].append({"step": "execute", "tool": action, "result": out})
        result["final_output"] = out
        result["duration_sec"] = round((datetime.now() - start).total_seconds(), 2)

        # 可选：用 LLM 美化最终回复
        if self.llm and self.provider != "demo":
            try:
                from langchain_core.messages import HumanMessage
                prompt = f"用户指令：{instruction}\n工具返回：{json.dumps(out, ensure_ascii=False)[:800]}\n请用中文给用户一个简洁、友好的执行总结（不超过120字）。"
                resp = self.llm.invoke([HumanMessage(content=prompt)])
                result["llm_summary"] = resp.content
            except Exception:
                pass

        return result


def get_agent() -> TaskMasterAgent:
    """工厂函数"""
    return TaskMasterAgent()
