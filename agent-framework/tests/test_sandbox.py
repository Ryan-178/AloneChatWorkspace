import pytest
import sys

from agent_framework.sandbox.subprocess_sandbox import SubprocessSandbox
from agent_framework.security.rate_limiter import RateLimiter, RateLimitConfig, RateLimitError


class TestSubprocessSandbox:
    def test_echo_command(self):
        sandbox = SubprocessSandbox()
        result = sandbox.run([sys.executable, "-c", "print('hello')"])
        assert result.success is True
        assert "hello" in result.data["stdout"]

    def test_timeout(self):
        sandbox = SubprocessSandbox(timeout_seconds=1)
        result = sandbox.run([sys.executable, "-c", "import time; time.sleep(5)"])
        assert result.success is False
        assert "timed out" in result.error

    def test_allowed_commands(self):
        sandbox = SubprocessSandbox(allowed_commands=[sys.executable])
        result = sandbox.run([sys.executable, "-c", "print('hi')"])
        assert result.success is True
        result2 = sandbox.run(["python", "-c", "print(1)"])
        assert result2.success is False
        assert "not in the allowed commands list" in result2.error

    def test_stderr_capture(self):
        sandbox = SubprocessSandbox()
        result = sandbox.run([sys.executable, "-c", "import sys; sys.stderr.write('error msg')"])
        assert result.success is True
        assert "error msg" in result.data["stderr"]

    def test_exit_code_nonzero(self):
        sandbox = SubprocessSandbox()
        result = sandbox.run([sys.executable, "-c", "import sys; sys.exit(1)"])
        assert result.success is False
        assert "Exit code 1" in result.error

    def test_network_disabled(self):
        sandbox = SubprocessSandbox(network_access=False)
        result = sandbox.run([sys.executable, "-c", "print(1)"])
        assert result.success is True

    def test_execution_time(self):
        sandbox = SubprocessSandbox()
        result = sandbox.run([sys.executable, "-c", "print(1)"])
        assert result.execution_time_ms > 0


class TestRateLimiter:
    def test_under_limit(self):
        rl = RateLimiter(RateLimitConfig(rpm=10, tpm=1000))
        rl.check_request(tokens=50)
        rl.record_request(tokens=50)

    def test_rpm_exceeded(self):
        rl = RateLimiter(RateLimitConfig(rpm=2, tpm=10000))
        rl.record_request()
        rl.record_request()
        with pytest.raises(RateLimitError) as exc_info:
            rl.check_request()
        assert "requests per minute" in str(exc_info.value)
        assert exc_info.value.retry_after_seconds > 0

    def test_tpm_exceeded(self):
        rl = RateLimiter(RateLimitConfig(rpm=100, tpm=10))
        with pytest.raises(RateLimitError) as exc_info:
            rl.check_request(tokens=20)
        assert "tokens per minute" in str(exc_info.value)
        assert exc_info.value.retry_after_seconds > 0

    def test_record_request_no_tokens(self):
        rl = RateLimiter(RateLimitConfig(rpm=10, tpm=10000))
        rl.record_request()
        assert len(rl._request_times) == 1
        assert len(rl._token_counts) == 0

    def test_record_request_with_tokens(self):
        rl = RateLimiter(RateLimitConfig(rpm=10, tpm=10000))
        rl.record_request(tokens=100)
        assert len(rl._request_times) == 1
        assert len(rl._token_counts) == 1

    def test_window_cleanup(self):
        rl = RateLimiter(RateLimitConfig(rpm=100, tpm=100000))
        rl.record_request(tokens=50)
        assert len(rl._token_counts) == 1
        rl.check_request()

    def test_rate_limit_error_attributes(self):
        err = RateLimitError("test", retry_after_seconds=5.5)
        assert err.retry_after_seconds == 5.5
        assert "test" in str(err)
