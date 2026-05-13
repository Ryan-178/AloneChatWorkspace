import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from agent_framework.core.base_llm import Message, LLMConfig, UsageInfo
from agent_framework.llm.litellm_provider import LiteLLMProvider, _estimate_cost


class TestEstimateCost:
    def test_known_model(self):
        cost = _estimate_cost("gpt-4o", 1000, 500)
        assert cost > 0

    def test_unknown_model_fallback(self):
        cost = _estimate_cost("unknown-model", 1000, 500)
        assert cost > 0

    def test_gpt4o_mini(self):
        cost = _estimate_cost("gpt-4o-mini", 1000, 500)
        assert cost > 0
        assert cost < _estimate_cost("gpt-4o", 1000, 500)


class TestLiteLLMProviderMock:
    def test_chat_mock(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.content = "Hello"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch("litellm.completion", return_value=mock_response):
            provider = LiteLLMProvider(LLMConfig(model="gpt-4o"))
            result = provider.chat([Message(role="user", content="hi")])
            assert result.role == "assistant"
            assert result.content == "Hello"
            usage = provider.get_total_usage()
            assert usage.total_tokens == 15

    def test_chat_mock_with_tool_calls(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.content = ""
        mock_response.choices[0].message.tool_calls = [{"id": "1"}]
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 10

        with patch("litellm.completion", return_value=mock_response):
            provider = LiteLLMProvider()
            result = provider.chat([Message(role="user", content="hi")])
            assert result.tool_calls == [{"id": "1"}]

    def test_chat_with_custom_config(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.content = "Hi"
        mock_response.usage.prompt_tokens = 1
        mock_response.usage.completion_tokens = 1
        mock_response.usage.total_tokens = 2

        custom_cfg = LLMConfig(model="gpt-3.5-turbo", temperature=0.5)
        with patch("litellm.completion", return_value=mock_response):
            provider = LiteLLMProvider()
            result = provider.chat([Message(role="user", content="x")], config=custom_cfg)
            assert result.content == "Hi"

    def test_usage_history(self):
        provider = LiteLLMProvider()
        provider.record_usage(UsageInfo(prompt_tokens=5, completion_tokens=3, total_tokens=8, estimated_cost=0.001))
        total = provider.get_total_usage()
        assert total.total_tokens == 8
        assert total.estimated_cost == 0.001
        provider.clear_usage_history()
        assert provider.get_total_usage().total_tokens == 0

    def test_multiple_usage_records(self):
        provider = LiteLLMProvider()
        provider.record_usage(UsageInfo(prompt_tokens=10, completion_tokens=5, total_tokens=15, estimated_cost=0.001))
        provider.record_usage(UsageInfo(prompt_tokens=20, completion_tokens=10, total_tokens=30, estimated_cost=0.002))
        total = provider.get_total_usage()
        assert total.prompt_tokens == 30
        assert total.completion_tokens == 15
        assert total.total_tokens == 45
        assert total.estimated_cost == 0.003

    def test_messages_to_litellm_with_name(self):
        msg = Message(role="tool", content="result", name="calc", tool_call_id="call_1")
        from agent_framework.llm.litellm_provider import _messages_to_litellm
        result = _messages_to_litellm([msg])
        assert result[0]["name"] == "calc"
        assert result[0]["tool_call_id"] == "call_1"

    @pytest.mark.asyncio
    async def test_chat_stream_mock(self):
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Hello"
        chunk1.choices[0].finish_reason = None
        chunk1.usage = None

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = " world"
        chunk2.choices[0].finish_reason = "stop"
        chunk2.usage = MagicMock()
        chunk2.usage.prompt_tokens = 5
        chunk2.usage.completion_tokens = 2

        async def async_generator():
            yield chunk1
            yield chunk2

        with patch("litellm.acompletion", return_value=async_generator()):
            provider = LiteLLMProvider()
            chunks = []
            async for c in provider.chat_stream([Message(role="user", content="hi")]):
                chunks.append(c)
            assert len(chunks) == 2
            assert chunks[0].content == "Hello"
            assert chunks[1].finish_reason == "stop"


class TestBaseLLM:
    def test_base_llm_init_defaults(self):
        from agent_framework.core.base_llm import BaseLLM
        class DummyLLM(BaseLLM):
            def chat(self, messages, config=None):
                return Message(role="assistant", content="")
            async def chat_stream(self, messages, config=None):
                yield Chunk(content="")
        llm = DummyLLM()
        assert llm.config.model == "gpt-4o"

    def test_base_llm_init_with_config(self):
        from agent_framework.core.base_llm import BaseLLM
        class DummyLLM(BaseLLM):
            def chat(self, messages, config=None):
                return Message(role="assistant", content="")
            async def chat_stream(self, messages, config=None):
                yield Chunk(content="")
        cfg = LLMConfig(model="custom")
        llm = DummyLLM(config=cfg)
        assert llm.config.model == "custom"
