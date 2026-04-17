import gradio as gr
from providers import PROVIDERS, get_provider_model_name, get_providers_for_model, build_call_info
from streaming import openai_stream_chat


def respond(model, provider_name, api_key, chat_history, user_message):
    """
    Respond generator that yields incremental chatbot updates.
    Signature preserved for UI binding.
    """
    if user_message is None or str(user_message).strip() == "":
        return

    chat_history = chat_history or []
    if chat_history and isinstance(chat_history[0], dict) and 'role' in chat_history[0]:
        messages = chat_history.copy()
    else:
        messages = []
        for item in chat_history:
            try:
                user, assistant = item
            except Exception:
                continue
            messages.append({"role": "user", "content": str(user)})
            if assistant is not None:
                messages.append({"role": "assistant", "content": str(assistant)})

    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": ""})

    yield messages, "", messages

    base_url = None
    if provider_name in PROVIDERS:
        base_url = PROVIDERS[provider_name]["base_url"]

    assistant_text = ""
    try:
        provider_model = None
        if provider_name:
            provider_model = get_provider_model_name(provider_name, model)
        used_model = provider_model or model

        for chunk in openai_stream_chat(user_message, messages[:-2], model=used_model, api_key=api_key, base_url=base_url):
            assistant_text = chunk
            messages[-1]["content"] = assistant_text
            yield messages, "", messages
    except Exception as e:
        messages[-1]["content"] = "生成失败: " + str(e)
        yield messages, "", messages


def on_history_select(selected_title, history_store, current_chat, current_title, model_name, provider_name, api_key):
    """
    Handle selecting a history item. Returns UI-updates in same shape as before.
    """
    if current_chat:
        if current_title and current_title in history_store:
            history_store[current_title]["chat"] = current_chat
            history_store[current_title]["model"] = model_name
            history_store[current_title]["provider"] = provider_name
            history_store[current_title]["api_key"] = api_key
        else:
            title = f"对话 {len(history_store) + 1}"
            history_store[title] = {"chat": current_chat, "model": model_name, "provider": provider_name, "api_key": api_key}

    if selected_title and selected_title in history_store:
        entry = history_store[selected_title]
        history_data = entry.get("chat", [])
        model = entry.get("model")
        provider = entry.get("provider")
        api_key_val = entry.get("api_key") or ""

        model_update = gr.update(value=model) if model is not None else gr.update(value=None)
        provider_choices = get_providers_for_model(model) if model else []
        provider_update = gr.update(choices=provider_choices, value=provider) if provider is not None else gr.update(choices=provider_choices, value=None)

        if model and provider:
            info = build_call_info(model, provider)
        elif model:
            info = build_call_info(model, None)
        else:
            info = ""

        return history_data, history_data, selected_title, history_store, gr.update(choices=list(history_store.keys()), value=selected_title), model_update, provider_update, api_key_val, info

    return [], [], "", history_store, gr.update(choices=list(history_store.keys()), value=None), gr.update(value=None), gr.update(choices=[], value=None), "", ""


def delete_history(selected_title, history_store):
    if selected_title and selected_title in history_store:
        del history_store[selected_title]
    return [], [], history_store, gr.update(choices=list(history_store.keys()), value=None), ""


def create_new_conversation(chat_history, current_title, history_store, model_name=None, provider_name=None, api_key=None):
    if chat_history:
        if current_title and current_title in history_store:
            history_store[current_title] = {"chat": chat_history, "model": model_name, "provider": provider_name, "api_key": api_key}
        else:
            title = f"对话 {len(history_store) + 1}"
            history_store[title] = {"chat": chat_history, "model": model_name, "provider": provider_name, "api_key": api_key}

    return [], [], history_store, gr.update(choices=list(history_store.keys()), value=None), ""


def on_model_change(model_name):
    providers = get_providers_for_model(model_name)
    if not providers:
        return gr.update(choices=[], value=None), "未找到支持该模型的 provider"
    if len(providers) == 1:
        info = f"已选择提供商: {providers[0]}"
        return gr.update(choices=providers, value=providers[0]), info
    info = "该模型在多家 provider 可用，请从下列 provider 中选择：\n" + ", ".join(providers)
    return gr.update(choices=providers), info
