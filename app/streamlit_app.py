"""
TaskMaster-Agent Streamlit Web 界面
聊天式交互 + 实时步骤展示 + 模式切换
启动: streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path
import streamlit as st
import json

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT / "src"))

from taskmaster.agent import TaskMasterAgent
from taskmaster.config import LLM_PROVIDER, OPENAI_API_KEY, GROK_API_KEY

st.set_page_config(page_title="TaskMaster Agent", page_icon="🤖", layout="wide")
st.title("🤖 TaskMaster Agent")
st.caption("本地多功能 AI 智能代理 · 支持文件整理、搜索总结、提醒、数据分析、报告生成")

# 侧边栏模式说明
with st.sidebar:
    st.header("⚙️ 运行模式")
    mode = st.selectbox("选择后端", ["demo", "ollama", "openai", "grok"], 
                        index=["demo","ollama","openai","grok"].index(LLM_PROVIDER) if LLM_PROVIDER in ["demo","ollama","openai","grok"] else 0)
    st.info(f"当前配置模式: **{mode}**\n\n"
            "• demo: 零依赖，规则引擎（推荐新手）\n"
            "• ollama: 本地免费（需先装 Ollama + 模型）\n"
            "• openai / grok: 云端高智能（需 API Key）")

    st.markdown("---")
    st.markdown("**快速指令示例**")
    examples = [
        "帮我整理 data/sandbox 里的文件",
        "搜索一下 Polymarket 最新新闻并总结",
        "提醒我后天给妈妈打电话",
        "分析一下销售数据",
        "生成一份本周工作总结报告"
    ]
    for ex in examples:
        if st.button(ex, key=ex):
            st.session_state.pending_instruction = ex
            st.rerun()

    st.caption("💡 切换模式后需重启 Streamlit 生效（修改 config 或环境变量）")

# 初始化 agent（会根据当前 mode）
@st.cache_resource
def get_cached_agent(mode: str):
    return TaskMasterAgent(provider=mode)

agent = get_cached_agent(mode)

# 聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好！我是 TaskMaster Agent。我可以帮你整理文件、搜索总结、设置提醒、分析数据、生成报告。\n\n请直接输入自然语言指令，例如：「整理一下 sandbox 里的文件」"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入
if "pending_instruction" in st.session_state:
    user_input = st.session_state.pop("pending_instruction")
else:
    user_input = st.chat_input("输入指令，例如：提醒我明天开会，或整理文件...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Agent 正在思考并执行..."):
            result = agent.run(user_input)

        # 漂亮展示
        if "llm_summary" in result:
            st.markdown(result["llm_summary"])
        else:
            st.markdown(f"**已执行工具**: `{result.get('final_output',{}).get('tool', 'N/A')}`")

        with st.expander("查看完整执行轨迹（调试用）"):
            st.json(result)

        # 特殊渲染
        final = result.get("final_output", {})
        if final.get("tool") == "file_organizer":
            st.success(f"✅ 整理完成！移动了 {final.get('moved_count',0)} 个文件（沙箱模式）。")
        elif final.get("tool") == "reminder":
            st.success("✅ 提醒已保存到本地文件 tasks/reminders.txt")
        elif final.get("tool") == "report":
            st.success(f"✅ 报告已生成: {final.get('path')}")

    st.session_state.messages.append({"role": "assistant", "content": "执行完成，详细结果见上方。"})

st.divider()
st.caption("TaskMaster-Agent v1.0 | 所有操作默认安全沙箱 | 配置 LLM_PROVIDER 环境变量切换后端")
