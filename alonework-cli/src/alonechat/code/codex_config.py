"""
CodexConfigBuilder - 生成 Codex CLI config.toml 配置文件
Generates Codex CLI config.toml configuration files.
"""

from typing import Any, Dict, List, Optional


class CodexConfigBuilder:
    """构建 Codex config.toml 配置"""

    def __init__(self):
        self._model: str = "deepseek-chat"
        self._model_provider: str = "deepseek"
        self._providers: Dict[str, Dict[str, Any]] = {}
        self._sandbox_mode: str = "workspace-write"
        self._approval_policy: str = "on-request"
        self._language: str = "zh"
        self._extra_sections: Dict[str, Any] = {}
        self._features: Dict[str, bool] = {}

    def set_model(self, model: str, provider: Optional[str] = None) -> "CodexConfigBuilder":
        self._model = model
        if provider:
            self._model_provider = provider
        return self

    def set_provider(
        self,
        name: str,
        base_url: str,
        api_key_env: str = "",
        wire_api: str = "responses",
        provider_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        requires_openai_auth: bool = False,
        supports_websockets: bool = False,
    ) -> "CodexConfigBuilder":
        pid = provider_id or name.lower().replace(" ", "-")
        self._providers[pid] = {
            "name": name,
            "base_url": base_url,
            "wire_api": wire_api,
            "requires_openai_auth": requires_openai_auth,
            "supports_websockets": supports_websockets,
        }
        if api_key_env:
            self._providers[pid]["env_key"] = api_key_env
        if extra_headers:
            self._providers[pid]["http_headers"] = extra_headers
        return self

    def set_model_provider(self, provider_id: str) -> "CodexConfigBuilder":
        self._model_provider = provider_id
        return self

    def set_sandbox(self, mode: str) -> "CodexConfigBuilder":
        self._sandbox_mode = mode
        return self

    def set_approval_policy(self, policy: str) -> "CodexConfigBuilder":
        self._approval_policy = policy
        return self

    def set_language(self, lang: str) -> "CodexConfigBuilder":
        self._language = lang
        return self

    def set_feature(self, key: str, enabled: bool) -> "CodexConfigBuilder":
        self._features[key] = enabled
        return self

    def add_section(self, section_name: str, values: Dict[str, Any]) -> "CodexConfigBuilder":
        self._extra_sections[section_name] = values
        return self

    def build(self) -> str:
        lines = []
        lines.append(f'model = "{self._model}"')
        lines.append(f'model_provider = "{self._model_provider}"')
        lines.append("")
        for pid, provider in self._providers.items():
            lines.append(f'[model_providers.{pid}]')
            for key, value in provider.items():
                if isinstance(value, bool):
                    lines.append(f"{key} = {str(value).lower()}")
                elif isinstance(value, dict):
                    lines.append(f"[model_providers.{pid}.{key}]")
                    for hk, hv in value.items():
                        lines.append(f'{hk} = "{hv}"')
                elif isinstance(value, str):
                    lines.append(f'{key} = "{value}"')
                else:
                    lines.append(f"{key} = {value}")
            lines.append("")
        if self._sandbox_mode or self._approval_policy:
            lines.append("[sandbox]")
            if self._sandbox_mode:
                lines.append(f'mode = "{self._sandbox_mode}"')
            lines.append("")
        if self._approval_policy:
            lines.append(f'approval_policy = "{self._approval_policy}"')
            lines.append("")
        if self._features:
            lines.append("[features]")
            for key, enabled in self._features.items():
                lines.append(f"{key} = {str(enabled).lower()}")
            lines.append("")
        for section_name, values in self._extra_sections.items():
            lines.append(f"[{section_name}]")
            for key, value in values.items():
                if isinstance(value, bool):
                    lines.append(f"{key} = {str(value).lower()}")
                elif isinstance(value, str):
                    lines.append(f'{key} = "{value}"')
                elif isinstance(value, list):
                    formatted = ", ".join(f'"{v}"' for v in value)
                    lines.append(f"{key} = [{formatted}]")
                else:
                    lines.append(f"{key} = {value}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def deepseek_config(
        api_key: str = "",
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
    ) -> "CodexConfigBuilder":
        builder = CodexConfigBuilder()
        builder.set_model(model, "deepseek")
        builder.set_provider(
            name="DeepSeek",
            base_url=base_url,
            api_key_env="DEEPSEEK_API_KEY",
            wire_api="chat",
        )
        builder.set_sandbox("workspace-write")
        builder.set_approval_policy("on-request")
        return builder

    @staticmethod
    def openai_config(
        api_key: str = "",
        model: str = "o4-mini",
    ) -> "CodexConfigBuilder":
        builder = CodexConfigBuilder()
        builder.set_model(model, "openai")
        builder.set_provider(
            name="OpenAI",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            wire_api="responses",
            requires_openai_auth=True,
        )
        builder.set_sandbox("workspace-write")
        builder.set_approval_policy("on-request")
        return builder

    @staticmethod
    def ollama_config(
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434/v1",
    ) -> "CodexConfigBuilder":
        builder = CodexConfigBuilder()
        builder.set_model(model, "ollama")
        builder.set_provider(
            name="Ollama",
            base_url=base_url,
            wire_api="responses",
        )
        builder.set_sandbox("workspace-write")
        builder.set_approval_policy("never")
        return builder
