PROVIDERS = {
    "AutoDL": {
        "base_url": "https://www.autodl.art/api/v1",
        "models": {
            "gpt-5.4": "gpt-5.4",
            "gpt-5.4-nano": "gpt-5.4-nano",
            "qwen3.6-plus": "qwen3.6-plus",
            "DeepSeek-V3.2": "DeepSeek-V3.2"
        },
        "auth_type": "header",
        "auth_name": "Authorization",
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com",
        "models": {
            "DeepSeek-V3.2": "deepseek-chat",
        },
        "auth_type": "query",
        "auth_name": "api_key",
    },
    "Aliyun": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": {
            "qwen3.6-plus": "qwen3.6-plus",
            "qwen3.6-flash": "qwen3.6-flash",
            "qwen3.6-max": "qwen3.6-max"
        },
        "auth_type": "header",
        "auth_name": "api_key",
    }
}

MODULES = ["gpt-5.4", "gpt-5.4-nano", "DeepSeek-V3.2", "qwen3.6-plus"]


def get_providers_for_model(model_name):
    """Return providers that support a given display model name."""
    result = []
    for name, conf in PROVIDERS.items():
        models_map = conf.get("models") or {}
        if model_name in models_map.keys():
            result.append(name)
    return result


def get_all_display_models():
    """Collect all display model names defined across providers (de-duplicated)."""
    s = []
    for conf in PROVIDERS.values():
        for display in (conf.get("models") or {}).keys():
            if display not in s:
                s.append(display)
    return s


def get_provider_model_name(provider_name, display_model):
    """Return the provider-specific model id for a given display model name."""
    conf = PROVIDERS.get(provider_name)
    if not conf:
        return None
    return (conf.get("models") or {}).get(display_model)


def build_call_info(model_name, provider_name):
    """Build display text that describes which provider/model/auth will be used."""
    if not provider_name:
        return "未选择 provider"
    conf = PROVIDERS.get(provider_name)
    if not conf:
        return f"未知 provider: {provider_name}"
    auth = conf.get("auth_type", "header")
    auth_desc = f"{auth.upper()} ({conf.get('auth_name')})"
    provider_model = get_provider_model_name(provider_name, model_name)
    model_line = f"Model (UI): {model_name}"
    if provider_model and provider_model != model_name:
        model_line += f"  -> Provider model id: {provider_model}"
    return f"{model_line}  -> Provider: {provider_name}\nBase URL: {conf.get('base_url')}\nAuth: {auth_desc}"
