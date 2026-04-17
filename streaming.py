import traceback
from openai import OpenAI


def _extract_text(content):
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


def openai_stream_chat(user_message, history, model="gpt-5.4-nano", api_key=None, base_url=None):
    """
    Streamed chat completions using OpenAI-compatible client.
    """
    messages = []

    if history:
        first = history[0]
        if isinstance(first, dict) and 'role' in first:
            for msg in history:
                role = msg.get('role')
                content = _extract_text(msg.get('content'))
                if role and content is not None:
                    messages.append({"role": role, "content": content})
        else:
            for user, assistant in history:
                messages.append({"role": "user", "content": _extract_text(user)})
                if assistant:
                    messages.append({"role": "assistant", "content": _extract_text(assistant)})
    messages.append({"role": "user", "content": user_message})

    used_key = None
    if api_key:
        used_key = api_key
    try:
        client = OpenAI(base_url=base_url, api_key=used_key)
    except Exception:
        client = None

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
    except Exception as e:
        yield "生成失败: " + str(e)
        return

    partial_parts = []
    try:
        for event in stream:
            for choice in getattr(event, "choices", []):
                delta = getattr(choice, "delta", None)
                if not delta:
                    content = getattr(choice, "text", None) or getattr(choice, "content", None)
                    if content:
                        partial_parts.append(content)
                        yield "".join(partial_parts)
                    continue

                content = None
                try:
                    content = delta.get("content") if hasattr(delta, "get") else getattr(delta, "content", None)
                except Exception:
                    content = getattr(delta, "content", None)

                if content:
                    partial_parts.append(content)
                    yield "".join(partial_parts)
    except Exception:
        yield "流式接收中断:\n" + traceback.format_exc()
