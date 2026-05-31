"""
CodexBridge - 基于 codex-sdk-python 的代码执行桥接层
CodexBridge - Code execution bridge based on codex-sdk-python

使用 OpenAI 官方 codex SDK 进行编程任务
Uses OpenAI official codex SDK for programming tasks
"""
import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class CodexProvider(str, Enum):
    """
    Codex提供商枚举 - Codex Provider Enum
    支持的LLM后端 / Supported LLM backends
    """
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class SandboxMode(str, Enum):
    """
    沙箱模式枚举 - Sandbox Mode Enum
    定义代码执行的安全级别
    Defines security level for code execution
    """
    DANGER_FULL_ACCESS = "danger-full-access"
    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"


class ApprovalPolicy(str, Enum):
    """
    审批策略枚举 - Approval Policy Enum
    定义工具执行的审批方式
    Defines approval method for tool execution
    """
    NEVER = "never"
    ON_REQUEST = "on-request"
    UNLESS_TRUSTED = "unless-trusted"
    ALWAYS = "always"


@dataclass
class CodexProviderConfig:
    """
    Codex提供商配置 - Codex Provider Configuration
    配置LLM后端连接参数
    Configure LLM backend connection parameters
    """
    name: str
    base_url: str
    api_key_env: str = ""
    wire_api: str = "responses"
    extra_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class CodexBridgeConfig:
    """
    CodexBridge配置 - CodexBridge Configuration
    配置Codex SDK的行为和参数
    Configure Codex SDK behavior and parameters
    """
    provider: CodexProvider = CodexProvider.OPENAI
    model: str = "o4-mini"
    api_key: str = ""
    base_url: str = ""
    sandbox_mode: SandboxMode = SandboxMode.WORKSPACE_WRITE
    approval_policy: ApprovalPolicy = ApprovalPolicy.ON_REQUEST
    working_directory: str = "."
    language: str = "zh"
    extra_providers: Dict[str, CodexProviderConfig] = field(default_factory=dict)
    extra_args: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    stream_timeout: float = 120.0
    llm: Any = None


class CodexExecResult(BaseModel):
    """
    Codex执行结果 - Codex Execution Result
    封装执行后的返回数据
    Encapsulates return data after execution
    """
    success: bool = Field(default=False)
    output: str = Field(default="")
    error: str = Field(default="")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    file_changes: List[Dict[str, Any]] = Field(default_factory=list)
    token_usage: Dict[str, int] = Field(default_factory=dict)
    duration_ms: float = Field(default=0.0)
    session_id: Optional[str] = Field(default=None)


class CodexEvent(BaseModel):
    """
    Codex事件 - Codex Event
    流式执行过程中的事件
    Events during streaming execution
    """
    type: str = Field(default="")
    content: str = Field(default="")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class CodexBridge:
    """
    CodexBridge - 基于 codex-sdk-python 的代码执行桥接层
    CodexBridge - Code execution bridge based on codex-sdk-python
    
    使用OpenAI官方Codex Python SDK进行编程任务
    Uses OpenAI official Codex Python SDK for programming tasks
    
    功能特性 / Features:
    - 通过SDK直接调用Codex CLI能力 / Directly call Codex CLI capabilities via SDK
    - 支持流式输出 / Supports streaming output
    - 沙箱安全执行 / Secure sandboxed execution
    - 多LLM后端支持 / Multi-LLM backend support
    """

    def __init__(self, config: Optional[CodexBridgeConfig] = None):
        """
        初始化CodexBridge - Initialize CodexBridge
        
        Args:
            config: CodexBridge配置 / CodexBridge configuration
        """
        self.config = config or CodexBridgeConfig()
        self._session_id: Optional[str] = None
        self._event_handlers: List[Callable[[CodexEvent], None]] = []
        self._client: Optional[Any] = None
        self._llm = self.config.llm

    @property
    def is_available(self) -> bool:
        """检查Codex SDK是否可用 - Check if Codex SDK is available"""
        try:
            import codex_sdk
            return True
        except ImportError:
            return False

    def on_event(self, handler: Callable[[CodexEvent], None]) -> None:
        """注册事件处理器 - Register event handler"""
        self._event_handlers.append(handler)

    def _emit_event(self, event: CodexEvent) -> None:
        """发送事件到所有处理器 - Send event to all handlers"""
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception:
                pass

    def _get_client(self) -> Any:
        """
        获取或创建Codex SDK客户端 - Get or create Codex SDK client
        
        Returns:
            Codex SDK客户端实例 / Codex SDK client instance
        """
        if self._client is not None:
            return self._client

        try:
            from codex_sdk import CodexClient
            
            client_config = {
                "model": self.config.model,
                "working_directory": self.config.working_directory,
                "sandbox_mode": self.config.sandbox_mode.value,
                "approval_policy": self.config.approval_policy.value,
            }
            
            if self.config.api_key:
                client_config["api_key"] = self.config.api_key
            
            if self.config.base_url:
                client_config["base_url"] = self.config.base_url
            
            self._client = CodexClient(**client_config)
            return self._client
            
        except ImportError:
            raise RuntimeError(
                "codex-sdk-python未安装，请运行: pip install codex-sdk-python\n"
                "codex-sdk-python not installed, please run: pip install codex-sdk-python"
            )

    async def exec(
        self,
        prompt: str,
        cwd: Optional[str] = None,
        images: Optional[List[str]] = None,
        model: Optional[str] = None,
        sandbox_mode: Optional[SandboxMode] = None,
        approval_policy: Optional[ApprovalPolicy] = None,
        json_output: bool = True,
        timeout: Optional[float] = None,
    ) -> CodexExecResult:
        """
        执行编码任务 - Execute coding task
        使用Codex SDK处理用户请求
        Uses Codex SDK to process user requests
        
        Args:
            prompt: 用户提示词 / User prompt
            cwd: 工作目录 / Working directory
            images: 图片列表 / Image list
            model: 模型名称 / Model name
            sandbox_mode: 沙箱模式 / Sandbox mode
            approval_policy: 审批策略 / Approval policy
            json_output: 是否JSON格式输出 / Whether to output in JSON format
            timeout: 超时时间(秒) / Timeout in seconds
            
        Returns:
            执行结果 / Execution result
        """
        result = CodexExecResult()
        start_time = time.time()
        
        try:
            client = self._get_client()
            
            exec_kwargs = {
                "prompt": prompt,
                "cwd": cwd or self.config.working_directory,
            }
            
            if model:
                exec_kwargs["model"] = model
            if sandbox_mode:
                exec_kwargs["sandbox_mode"] = sandbox_mode.value
            if approval_policy:
                exec_kwargs["approval_policy"] = approval_policy.value
            if timeout:
                exec_kwargs["timeout"] = timeout
            
            response = await client.execute(**exec_kwargs)
            
            result.success = True
            result.output = response.get("output", "")
            result.error = response.get("error", "")
            result.tool_calls = response.get("tool_calls", [])
            result.file_changes = response.get("file_changes", [])
            result.token_usage = response.get("token_usage", {})
            result.session_id = response.get("session_id")
            
        except Exception as e:
            result.error = str(e)
            result.success = False
            
            if self._llm is not None:
                result.output = await self._fallback_to_llm(prompt)

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    async def _fallback_to_llm(self, prompt: str) -> str:
        """
        回退到LLM执行 - Fallback to LLM execution
        当Codex SDK不可用时使用LLM
        Use LLM when Codex SDK is unavailable
        
        Args:
            prompt: 用户提示词 / User prompt
            
        Returns:
            LLM响应 / LLM response
        """
        from agent_framework.core.base_llm import Message
        
        system_prompt = """你是一个专业的编程助手。
请帮助用户完成编程任务，包括但不限于：
- 编写代码
- 调试问题
- 重构优化
- 代码审查

请用中文回答。"""
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=prompt),
        ]
        
        response = self._llm.chat(messages)
        return f"[LLM回退模式 / LLM fallback mode]\n{response.content}"

    async def exec_stream(
        self,
        prompt: str,
        cwd: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> AsyncGenerator[CodexEvent, None]:
        """
        流式执行编码任务 - Execute coding task with streaming
        实时返回执行过程的事件
        Real-time returns events during execution
        
        Args:
            prompt: 用户提示词 / User prompt
            cwd: 工作目录 / Working directory
            model: 模型名称 / Model name
            timeout: 超时时间(秒) / Timeout in seconds
            
        Yields:
            执行事件流 / Execution event stream
        """
        try:
            client = self._get_client()
            
            stream_kwargs = {
                "prompt": prompt,
                "cwd": cwd or self.config.working_directory,
            }
            
            if model:
                stream_kwargs["model"] = model
            if timeout:
                stream_kwargs["timeout"] = timeout
            
            async for event in client.execute_stream(**stream_kwargs):
                codex_event = CodexEvent(
                    type=event.get("type", "message"),
                    content=event.get("content", ""),
                    metadata=event.get("metadata", {}),
                )
                self._emit_event(codex_event)
                yield codex_event
                
        except Exception as e:
            error_event = CodexEvent(
                type="error",
                content=str(e),
            )
            self._emit_event(error_event)
            yield error_event
            
            if self._llm is not None:
                output = await self._fallback_to_llm(prompt)
                yield CodexEvent(type="message", content=output)
        
        yield CodexEvent(
            type="completed",
            content="",
            metadata={"duration_ms": (time.time() - start_time) * 1000} if 'start_time' in dir() else {}
        )

    async def review(
        self,
        cwd: Optional[str] = None,
        target: Optional[str] = None,
        model: Optional[str] = None,
    ) -> CodexExecResult:
        """
        代码审查 - Code review
        使用Codex SDK进行代码质量检查
        Uses Codex SDK for code quality check
        
        Args:
            cwd: 工作目录 / Working directory
            target: 审查目标 / Review target
            model: 模型名称 / Model name
            
        Returns:
            审查结果 / Review result
        """
        work_dir = cwd or self.config.working_directory
        review_prompt = f"请审查以下代码变更。\n工作目录: {work_dir}"
        if target:
            review_prompt += f"\n目标文件/目录: {target}"
        
        return await self.exec(
            prompt=review_prompt,
            cwd=work_dir,
            model=model,
        )

    async def apply(
        self,
        cwd: Optional[str] = None,
    ) -> CodexExecResult:
        """
        应用代码变更 - Apply code changes
        确认并应用之前生成的变更
        Confirm and apply previously generated changes
        
        Args:
            cwd: 工作目录 / Working directory
            
        Returns:
            应用结果 / Apply result
        """
        try:
            client = self._get_client()
            result = await client.apply(cwd=cwd or self.config.working_directory)
            
            return CodexExecResult(
                success=True,
                output=result.get("output", "Apply operation completed"),
                file_changes=result.get("file_changes", []),
            )
        except Exception as e:
            return CodexExecResult(
                success=False,
                error=str(e),
            )

    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        对话模式 - Chat mode
        与Codex进行交互式对话
        Interactive conversation with Codex
        
        Args:
            message: 用户消息 / User message
            context: 对话上下文 / Conversation context
            
        Returns:
            响应内容 / Response content
        """
        client = self._get_client()
        
        kwargs = {"message": message}
        if context:
            kwargs["context"] = context
        
        response = await client.chat(**kwargs)
        return response.get("content", "")

    async def terminate(self) -> None:
        """终止当前会话 - Terminate current session"""
        if self._client:
            try:
                await self._client.terminate()
            except Exception:
                pass

    def cleanup(self) -> None:
        """清理资源 - Cleanup resources"""
        if self._client:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.terminate())
                else:
                    loop.run_until_complete(self.terminate())
            except Exception:
                pass
        self._client = None

    def __enter__(self):
        """上下文管理器入口 - Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口 - Context manager exit"""
        self.cleanup()
        return False
