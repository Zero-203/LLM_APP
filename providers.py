import json
import os


def load_providers():
    config_path = os.path.join(os.path.dirname(__file__), "providers.json")
    with open(config_path, "r") as f:
        return json.load(f)


PROVIDERS = load_providers()

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
