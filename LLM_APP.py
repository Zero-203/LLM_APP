import os
import gradio as gr
from openai import OpenAI  # 如果你使用的包名是 openai，请改为 import openai 并调整 client 初始化
import traceback
import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())


def openai_stream_chat(user_message, history, model="gpt-5.4-nano", api_key=None):
    """
    Gradio ChatInterface 的流式回调：
    - 从 history 重建 messages（user/assistant）
    - 发起 stream=True 的 chat completion 请求
    - 遍历返回的增量事件，把累积文本通过 yield 发回 Gradio
    """
    messages = []
    # history 可能是 (user, assistant) 的列表，或是消息 dict 列表（含 role / content）
    def _extract_text(content):
        # 将不同类型的 content 统一抽取为字符串
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(str(item.get("text") or item.get("content") or ""))
                else:
                    parts.append(str(item))
            return "".join(parts)
        if isinstance(content, dict):
            return str(content.get("text") or content.get("content") or "")
        return str(content)

    print(history)
    if history:
        first = history[0]
        if isinstance(first, dict) and 'role' in first:
            # history 是消息 dict 列表，按 role/content 重建 messages
            for msg in history:
                role = msg.get('role')
                content = _extract_text(msg.get('content'))
                if role and content is not None:
                    messages.append({"role": role, "content": content})
        else:
            # 兼容旧的 (user, assistant) 列表格式（chatbot 返回的格式通常是 (user, assistant) 列表）
            for user, assistant in history:
                messages.append({"role": "user", "content": _extract_text(user)})
                if assistant:
                    messages.append({"role": "assistant", "content": _extract_text(assistant)})
    # 将当前输入追加为最后一个 user 消消息
    messages.append({"role": "user", "content": user_message})

    # 根据传入的 api_key 创建客户端（优先使用传入的 api_key，否则使用环境变量）
    used_key = api_key if api_key else os.getenv("OPENAI_API_KEY")
    try:
        client = OpenAI(base_url="https://www.autodl.art/api/v1", api_key=used_key)
    except Exception:
        # 如果创建客户端失败，仍尝试在请求时捕获异常
        client = None

    try:
        # 发起流式请求；根据你的 SDK 版本，API 名称可能略有不同
        stream = client.chat.completions.create(
            model=model,  # 使用页面中选择的模型
            messages=messages,
            stream=True,
        )
    except Exception as e:
        # 发生错误时直接返回错误信息
        yield "生成失败: " + str(e)
        return

    # 使用列表累加，避免频繁字符串拼接；最后用 join 生成完整文本
    partial_parts = []
    try:
        for event in stream:
            # 每个 event 可能包含多个选择（choices）；取第一个即可
            for choice in getattr(event, "choices", []):
                # 新版本 SDK 在增量中通常使用 delta 字段；检查 content 是否存在
                delta = getattr(choice, "delta", None)
                if not delta:
                    # 有些 SDK 返回结构可能直接在 choice 中提供 text / content
                    content = getattr(choice, "text", None) or getattr(choice, "content", None)
                    if content:
                        partial_parts.append(content)
                        yield "".join(partial_parts)
                    continue

                # delta 可能是 dict-like，尝试取 "content"
                content = None
                try:
                    # 若 delta 是 Mapping
                    content = delta.get("content") if hasattr(delta, "get") else getattr(delta, "content", None)
                except Exception:
                    content = getattr(delta, "content", None)

                if content:
                    partial_parts.append(content)
                    yield "".join(partial_parts)
    except Exception:
        # 流处理异常时返回完整错误堆栈方便调试
        yield "流式接收中断:\n" + traceback.format_exc()


def respond(model, api_key, chat_history, user_message):
    """
    响应函数：处理用户消息并流式返回助手回复
    chat_history 格式：messages dict 列表 [{"role": "user", "content": "..."}, ...]
    输出：[chatbot_display, msg_input, updated_history]
    """
    if user_message is None or str(user_message).strip() == "":
        return

    chat_history = chat_history or []

    # 确保 chat_history 是 messages dict 列表格式
    if chat_history and isinstance(chat_history[0], dict) and 'role' in chat_history[0]:
        messages = chat_history.copy()
    else:
        # 兼容旧的 (user, assistant) 元组格式
        messages = []
        for item in chat_history:
            try:
                user, assistant = item
            except Exception:
                continue
            messages.append({"role": "user", "content": str(user)})
            if assistant is not None:
                messages.append({"role": "assistant", "content": str(assistant)})

    # 添加新的用户消息和空的助手回复占位
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": ""})

    # 首次 yield：显示用户消息，清空输入框，更新 history state
    yield messages, "", messages

    # 调用 OpenAI API，获取流式回复（传入的 history 不包含空的 assistant 条目）
    assistant_text = ""
    try:
        for chunk in openai_stream_chat(user_message, messages[:-2], model=model, api_key=api_key):
            assistant_text = chunk
            # 更新最后一个 assistant 消息
            messages[-1]["content"] = assistant_text
            # 流式输出：更新显示、清空输入框、保存 history
            yield messages, "", messages
    except Exception as e:
        messages[-1]["content"] = "生成失败: " + str(e)
        yield messages, "", messages


def on_history_select(selected_title, history_store):
    """当用户选择历史对话时自动加载"""
    if selected_title and selected_title in history_store:
        history_data = history_store[selected_title]
        return history_data, history_data, selected_title
    return [], [], ""


def delete_history(selected_title, history_store):
    """删除对话并清空聊天框"""
    if selected_title and selected_title in history_store:
        del history_store[selected_title]
    # 清空所有内容
    return [], [], history_store, gr.update(choices=list(history_store.keys()), value=None), ""


def create_new_conversation(chat_history, current_title, history_store):
    """保存当前对话并开始新对话"""
    if chat_history:
        if current_title and current_title in history_store:
            # 更新现有对话
            history_store[current_title] = chat_history
        else:
            # 创建新对话
            title = f"对话 {len(history_store) + 1}"
            history_store[title] = chat_history
    # 清空对话、标题和下拉菜单选择
    return [], [], history_store, gr.update(choices=list(history_store.keys()), value=None), ""


with gr.Blocks() as demo:
    gr.Markdown("# OpenAI + Gradio 流式聊天")

    history_store = gr.State({})  # 存储所有历史对话
    selected_history = gr.State([])  # 当前编辑的对话内容
    current_history_title = gr.State("")  # 当前编辑的历史对话标题

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 历史对话")
            history_dropdown = gr.Dropdown(label="选择历史对话", interactive=True)
            with gr.Row():
                delete_btn = gr.Button("删除对话")
            create_btn = gr.Button("新建对话")

        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="聊天记录",
                buttons=[["copy","share"]]
            )
            with gr.Row():
                model_dropdown = gr.Dropdown(
                    choices=["gpt-5.4","gpt-5.4-nano", "DeepSeek-V3.2", "qwen3.6-plus"], 
                    value="gpt-5.4", 
                    label="Model"
                )
                api_key_text = gr.Textbox(
                    label="API Key", 
                    placeholder="Enter API key (overrides OPENAI_API_KEY)", 
                    type="password"
                )
            with gr.Row():
                msg = gr.Textbox(
                    show_label=False, 
                    placeholder="Type a message and press Enter",
                    lines=3
                )
                send_btn = gr.Button("Send", scale=0)

    # 事件绑定
    # 选择历史对话时自动加载到聊天框中
    history_dropdown.change(
        on_history_select,
        inputs=[history_dropdown, history_store],
        outputs=[selected_history, chatbot, current_history_title]
    )

    # 删除历史对话并清空聊天框
    delete_btn.click(
        delete_history,
        inputs=[history_dropdown, history_store],
        outputs=[chatbot, selected_history, history_store, history_dropdown, current_history_title]
    )

    # 创建新对话：保存当前对话，清空聊天框和状态
    create_btn.click(
        create_new_conversation,
        inputs=[chatbot, current_history_title, history_store],
        outputs=[chatbot, selected_history, history_store, history_dropdown, current_history_title]
    )

    # 发送消息：读取 selected_history，输出到 chatbot、msg、selected_history
    send_btn.click(
        respond,
        inputs=[model_dropdown, api_key_text, selected_history, msg],
        outputs=[chatbot, msg, selected_history]
    )

    # 回车提交
    msg.submit(
        respond,
        inputs=[model_dropdown, api_key_text, selected_history, msg],
        outputs=[chatbot, msg, selected_history]
    )

demo.launch()
