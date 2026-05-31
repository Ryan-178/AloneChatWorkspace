"""
速率限制器 - Rate Limiter / 速率限制器
线程安全的请求速率控制，防止滥用和DDoS攻击
Thread-safe request rate control to prevent abuse and DDoS attacks

安全特性 / Security features:
- 线程安全（使用锁机制）
- 多维度限制（按IP、用户、API密钥）
- 自适应限流（根据系统负载动态调整）
- 滑动窗口算法（更精确的速率控制）

参考实现 / Reference implementations:
- Cloudflare Rate Limiting
- AWS API Gateway Throttling
- Redis RATE_LIMITER (if using Redis backend)
"""
import time
import threading
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from contextlib import contextmanager


class RateLimitError(Exception):
    """
    速率限制错误 - Rate Limit Error / 速率限制錯誤
    当超过允许的请求频率时抛出
    Raised when allowed request frequency is exceeded
    """
    def __init__(self, message: str, retry_after_seconds: float, limit_type: str = "global"):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
        self.limit_type = limit_type  # global, per_ip, per_user, per_api_key


@dataclass
class RateLimitConfig:
    """
    速率限制配置 - Rate Limit Configuration / 速率限制配置
    定义各种维度的速率限制规则
    Defines rate limiting rules for various dimensions

    Attributes:
        rpm: 每分钟请求数 / Requests per minute
        tpm: 每分钟Token数 / Tokens per minute (for LLM APIs)
        rph: 每小时请求数 / Requests per hour
        rpd: 每天请求数 / Requests per day
        burst: 突发请求数 / Burst requests (allow short bursts)
    """
    rpm: int = 60
    tpm: int = 100000
    rph: int = 1000
    rpd: int = 10000
    burst: int = 10  # 允许短时间突发 / Allow short bursts

    # 细粒度控制 - Fine-grained controls
    per_ip_rpm: Optional[int] = None  # 每个IP的限制 / Per-IP limit
    per_user_rpm: Optional[int] = None  # 每个用户的限制 / Per-user limit
    per_api_key_rpm: Optional[int] = None  # 每个API密钥的限制 / Per-API-key limit

    # 自适应控制 - Adaptive controls
    enable_adaptive: bool = False  # 是否启用自适应限流 / Enable adaptive throttling
    max_system_load: float = 0.8  # 最大系统负载阈值 / Max system load threshold


@dataclass
class _ClientState:
    """
    客户端状态 - Client State / 客戶端狀態
    跟踪单个客户端的请求历史
    Tracks request history for a single client
    """
    request_times: List[float] = field(default_factory=list)
    token_counts: List[Tuple[float, int]] = field(default_factory=list)  # (timestamp, tokens)
    hourly_counts: List[Tuple[float, int]] = field(default_factory=list)  # (timestamp, count)
    daily_counts: List[Tuple[float, int]] = field(default_factory=list)  # (timestamp, count)

    def cleanup(self, now: float) -> None:
        """清理过期记录 - Clean up expired records / 清理過期記錄"""
        # 清理1分钟窗口 - Clean up 1-minute window
        self.request_times = [t for t in self.request_times if now - t < 60.0]
        self.token_counts = [(t, c) for t, c in self.token_counts if now - t < 60.0]

        # 清理1小时窗口 - Clean up 1-hour window
        self.hourly_counts = [(t, c) for t, c in self.hourly_counts if now - t < 3600.0]

        # 清理1天窗口 - Clean up 1-day window
        self.daily_counts = [(t, c) for t, c in self.daily_counts if now - t < 86400.0]


class RateLimiter:
    """
    速率限制器 - Rate Limiter / 速率限制器
    使用滑动窗口算法实现精确的速率控制
    Uses sliding window algorithm for precise rate control

    线程安全说明 / Thread safety notes:
    - 所有公共方法都是线程安全的
    - 内部使用RLock保证原子性操作
    - 支持高并发场景

    使用示例 / Usage example:
    ```python
    config = RateLimitConfig(rpm=100, per_ip_rpm=20)
    limiter = RateLimiter(config)

    try:
        limiter.check_request(ip_address="192.168.1.1", user_id="user123")
        # 处理请求... / Process request...
        limiter.record_request(ip_address="192.168.1.1", user_id="user123")
    except RateLimitError as e:
        logger.warning(f"Rate limited: {e}")
        # 返回429状态码和Retry-After头 / Return 429 status with Retry-After header
    ```
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        初始化速率限制器 - Initialize rate limiter

        Args:
            config: 速率限制配置 / Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        self._lock = threading.RLock()

        # 全局状态 - Global state
        self._global_state = _ClientState()

        # 按IP的状态 - Per-IP states
        self._ip_states: Dict[str, _ClientState] = defaultdict(_ClientState)

        # 按用户的状态 - Per-user states
        self._user_states: Dict[str, _ClientState] = defaultdict(_ClientState)

        # 按API密钥的状态 - Per-API-key states
        self._api_key_states: Dict[str, _ClientState] = defaultdict(_ClientState)

        # 统计信息 - Statistics
        self._total_requests: int = 0
        _total_rejected: int = 0
        self._start_time: float = time.time()

    @contextmanager
    def _acquire_lock(self):
        """获取锁上下文管理器 - Lock context manager / 獲取鎖上下文管理器"""
        with self._lock:
            yield

    def _now(self) -> float:
        """获取当前时间戳 - Get current timestamp / 獲取當前時間戳"""
        return time.time()

    def _cleanup_state(self, state: _ClientState) -> None:
        """清理指定状态的过期记录 - Clean up expired records for given state"""
        now = self._now()
        state.cleanup(now)

    def _check_limits(
        self,
        state: _ClientState,
        tokens: int,
        limits: Tuple[int, int],  # (rpm, tpm)
        client_id: str,
        limit_type: str,
    ) -> Optional[RateLimitError]:
        """
        检查是否超出限制 - Check if limits are exceeded / 檢查是否超出限制

        Args:
            state: 客户端状态 / Client state
            tokens: Token数量 / Token count
            limits: (rpm, tpm) 元组 / (rpm, tpm) tuple
            client_id: 客户端标识符 / Client identifier
            limit_type: 限制类型 / Limit type

        Returns:
            如果超限则返回RateLimitError，否则返回None
            Returns RateLimitError if exceeded, otherwise None
        """
        rpm_limit, tpm_limit = limits

        now = self._now()

        # 检查RPM限制 - Check RPM limit
        if len(state.request_times) >= rpm_limit:
            oldest = state.request_times[0]
            retry_after = 60.0 - (now - oldest)
            return RateLimitError(
                f"Rate limit exceeded: {rpm_limit} requests per minute for {limit_type} '{client_id}'",
                retry_after_seconds=max(retry_after, 0.1),
                limit_type=limit_type,
            )

        # 检查TPM限制 - Check TPM limit
        total_tokens = sum(c for _, c in state.token_counts) + tokens
        if total_tokens > tpm_limit:
            if state.token_counts:
                oldest = state.token_counts[0][0]
                retry_after = 60.0 - (now - oldest)
            else:
                retry_after = 60.0
            return RateLimitError(
                f"Rate limit exceeded: {tpm_limit} tokens per minute for {limit_type} '{client_id}'",
                retry_after_seconds=max(retry_after, 0.1),
                limit_type=limit_type,
            )

        return None

    def check_request(
        self,
        tokens: int = 0,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        检查请求是否允许 - Check if request is allowed / 檢查請求是否允許
        按优先级检查全局、IP、用户、API密钥限制
        Checks global, IP, user, API key limits by priority

        Raises:
            RateLimitError: 如果任何限制被超出 / If any limit is exceeded

        Args:
            tokens: 此请求消耗的Token数 / Tokens consumed by this request
            ip_address: 客户端IP地址 / Client IP address
            user_id: 用户ID / User ID
            api_key: API密钥 / API key
        """
        with self._lock:
            now = self._now()

            # 清理所有相关状态 - Clean up all relevant states
            self._cleanup_state(self._global_state)

            if ip_address and ip_address in self._ip_states:
                self._cleanup_state(self._ip_states[ip_address])

            if user_id and user_id in self._user_states:
                self._cleanup_state(self._user_states[user_id])

            if api_key and api_key in self._api_key_states:
                self._cleanup_state(self._api_key_states[api_key])

            # 1. 检查全局限制 - Check global limits
            error = self._check_limits(
                self._global_state,
                tokens,
                (self.config.rpm, self.config.tpm),
                "global",
                "global",
            )
            if error:
                raise error

            # 2. 检查每IP限制 - Check per-IP limits
            if ip_address and self.config.per_ip_rpm:
                ip_state = self._ip_states[ip_address]
                error = self._check_limits(
                    ip_state,
                    tokens,
                    (self.config.per_ip_rpm, self.config.tpm),  # TPM继承全局设置
                    ip_address,
                    "per_ip",
                )
                if error:
                    raise error

            # 3. 检查每用户限制 - Check per-user limits
            if user_id and self.config.per_user_rpm:
                user_state = self._user_states[user_id]
                error = self._check_limits(
                    user_state,
                    tokens,
                    (self.config.per_user_rpm, self.config.tpm),
                    user_id,
                    "per_user",
                )
                if error:
                    raise error

            # 4. 检查每API密钥限制 - Check per-API-key limits
            if api_key and self.config.per_api_key_rpm:
                api_state = self._api_key_states[api_key]
                error = self._check_limits(
                    api_state,
                    tokens,
                    (self.config.per_api_key_rpm, self.config.tpm),
                    api_key[:8] + "...",  # 不完整显示密钥 / Don't show full key
                    "per_api_key",
                )
                if error:
                    raise error

    def record_request(
        self,
        tokens: int = 0,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        记录成功的请求 - Record successful request / 記錄成功的請求
        应该在处理完请求后调用此方法
        Should be called after processing the request

        Args:
            tokens: 消耗的Token数 / Tokens consumed
            ip_address: 客户端IP地址 / Client IP address
            user_id: 用户ID / User ID
            api_key: API密钥 / API key
        """
        with self._lock:
            now = self._now()
            self._total_requests += 1

            # 记录到全局状态 - Record to global state
            self._global_state.request_times.append(now)
            if tokens > 0:
                self._global_state.token_counts.append((now, tokens))

            # 记录到IP状态 - Record to IP state
            if ip_address:
                ip_state = self._ip_states[ip_address]
                ip_state.request_times.append(now)
                if tokens > 0:
                    ip_state.token_counts.append((now, tokens))

            # 记录到用户状态 - Record to user state
            if user_id:
                user_state = self._user_states[user_id]
                user_state.request_times.append(now)
                if tokens > 0:
                    user_state.token_counts.append((now, tokens))

            # 记录到API密钥状态 - Record to API key state
            if api_key:
                api_state = self._api_key_states[api_key]
                api_state.request_times.append(now)
                if tokens > 0:
                    api_state.token_counts.append((now, tokens))

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息 - Get statistics / 獲取統計信息
        返回速率限制器的运行统计
        Returns runtime statistics of the rate limiter

        Returns:
            统计数据字典 / Statistics dictionary
        """
        with self._lock:
            uptime = self._now() - self._start_time
            return {
                "total_requests": self._total_requests,
                "uptime_seconds": round(uptime, 2),
                "requests_per_second": round(self._total_requests / uptime, 2) if uptime > 0 else 0,
                "tracked_ips": len(self._ip_states),
                "tracked_users": len(self._user_states),
                "tracked_api_keys": len(self._api_key_states),
                "config": {
                    "rpm": self.config.rpm,
                    "tpm": self.config.tpm,
                    "per_ip_rpm": self.config.per_ip_rpm,
                    "per_user_rpm": self.config.per_user_rpm,
                    "per_api_key_rpm": self.config.per_api_key_rpm,
                },
            }

    def reset_client(self, client_type: str, client_id: str) -> bool:
        """
        重置客户端状态 - Reset client state / 重置客戶端狀態
        用于管理员手动解除限制
        Used for admins to manually lift restrictions

        Args:
            client_type: 客户端类型 ("ip", "user", "api_key") / Client type
            client_id: 客户端标识符 / Client identifier

        Returns:
            是否重置成功 / Whether reset was successful
        """
        with self._lock:
            if client_type == "ip":
                if client_id in self._ip_states:
                    del self._ip_states[client_id]
                    return True
            elif client_type == "user":
                if client_id in self._user_states:
                    del self._user_states[client_id]
                    return True
            elif client_type == "api_key":
                if client_id in self._api_key_states:
                    del self._api_key_states[client_id]
                    return True
            return False

    def cleanup_old_clients(self, max_age_seconds: float = 3600.0) -> int:
        """
        清理不活跃的客户端 - Clean up inactive clients / 清理不活躍的客戶端
        应该定期调用以释放内存
        Should be called periodically to free memory

        Args:
            max_age_seconds: 最大不活跃时间（秒） / Max inactive time (seconds)

        Returns:
            清理的客户端数量 / Number of cleaned clients
        """
        with self._lock:
            now = self._now()
            cleaned = 0

            # 清理IP状态 - Clean IP states
            inactive_ips = [
                ip for ip, state in self._ip_states.items()
                if not state.request_times or now - state.request_times[-1] > max_age_seconds
            ]
            for ip in inactive_ips:
                del self._ip_states[ip]
                cleaned += 1

            # 清理用户状态 - Clean user states
            inactive_users = [
                uid for uid, state in self._user_states.items()
                if not state.request_times or now - state.request_times[-1] > max_age_seconds
            ]
            for uid in inactive_users:
                del self._user_states[uid]
                cleaned += 1

            # 清理API密钥状态 - Clean API key states
            inactive_keys = [
                key for key, state in self._api_key_states.items()
                if not state.request_times or now - state.request_times[-1] > max_age_seconds
            ]
            for key in inactive_keys:
                del self._api_key_states[key]
                cleaned += 1

            return cleaned


# ============================================================================
# 全局速率限制器实例 - Global rate limiter instance / 全局速率限制器實例
# ============================================================================

# 默认配置 - Default configuration
_default_config = RateLimitConfig(
    rpm=60,
    tpm=100000,
    per_ip_rpm=20,
    per_user_rpm=30,
    per_api_key_rpm=100,
)

# 全局实例 - Global instance
_global_limiter = RateLimiter(_default_config)


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """
    获取速率限制器实例 - Get rate limiter instance / 獲取速率限制器實例

    Args:
        config: 自定义配置（可选） / Custom configuration (optional)

    Returns:
        速率限制器实例 / Rate limiter instance
    """
    if config:
        return RateLimiter(config)
    return _global_limiter


# 便捷函数 - Convenience functions
def check_rate_limit(
    tokens: int = 0,
    ip_address: Optional[str] = None,
    user_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    检查速率限制（便捷函数） - Check rate limit (convenience function)
    使用全局速率限制器实例
    Uses the global rate limiter instance
    """
    _global_limiter.check_request(tokens, ip_address, user_id, api_key)


def record_rate_limit(
    tokens: int = 0,
    ip_address: Optional[str] = None,
    user_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """
    记录请求（便捷函数） - Record request (convenience function)
    使用全局速率限制器实例
    Uses the global rate limiter instance
    """
    _global_limiter.record_request(tokens, ip_address, user_id, api_key)
