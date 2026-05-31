"""
安全模块测试 - Security Module Tests

验证路径安全验证、动态扫描等安全功能
Validates path security validation, dynamic scanning, and other security features
"""
import os
import sys
import tempfile
import json
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPathValidator:
    """路径安全验证器测试 / Path Validator Tests"""

    def setup_method(self):
        from agent_framework.security.path_validator import PathValidator
        self.validator = PathValidator()

    def test_path_traversal_blocked(self):
        """测试路径遍历被阻止 / Test path traversal is blocked"""
        allowed_base = str(Path.cwd())
        from agent_framework.security.path_validator import PathValidator
        result = PathValidator.resolve_safe_path(
            "../../../../etc/passwd", allowed_base
        )
        assert result is None, "Path traversal should be blocked"

    def test_safe_path_allowed(self):
        """测试安全路径被允许 / Test safe path is allowed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_file = Path(tmpdir) / "test.txt"
            safe_file.write_text("hello", encoding="utf-8")

            from agent_framework.security.path_validator import PathValidator
            result = PathValidator.resolve_safe_path(str(safe_file), tmpdir)
            assert result is not None, "Safe path should be allowed"
            assert result.exists(), "Resolved path should exist"

    def test_symlink_outside_base_blocked(self):
        """测试符号链接到基目录外被阻止 / Test symlink outside base is blocked"""
        from agent_framework.security.path_validator import PathValidator

        with tempfile.TemporaryDirectory() as base_dir:
            with tempfile.TemporaryDirectory() as outside_dir:
                outside_file = Path(outside_dir) / "secret.txt"
                outside_file.write_text("secret", encoding="utf-8")

                if os.name == 'nt':
                    return

                link_path = Path(base_dir) / "link_to_outside"
                try:
                    os.symlink(str(outside_file), str(link_path))
                    result = PathValidator.resolve_safe_path(str(link_path), base_dir)
                    assert result is None, "Symlink outside base should be blocked"
                except (OSError, NotImplementedError):
                    pass

    def test_blocked_system_paths(self):
        """测试系统路径被阻止 / Test system paths are blocked"""
        dangerous_paths = ["/etc/passwd", "/sys/kernel"]
        if os.name == 'nt':
            dangerous_paths = ["C:\\Windows\\System32\\config", "C:\\Windows\\notepad.exe"]

        for path in dangerous_paths:
            is_safe = self.validator.is_safe_path(path)
            if os.path.exists(path):
                assert not is_safe, f"System path should be blocked: {path}"

    def test_sanitize_session_id(self):
        """测试会话ID净化 / Test session ID sanitization"""
        dangerous_ids = [
            ("../../../etc/passwd", "etcpasswd"),
            ("valid-id-123", "valid-id-123"),
            ("../malicious/..", "malicious"),
            ("<script>alert(1)</script>", "scriptalert1script"),
        ]

        for raw, expected_prefix in dangerous_ids:
            sanitized = self.validator.sanitize_session_id(raw)
            assert "/" not in sanitized, f"Session ID should not contain path separators: {raw}"
            assert ".." not in sanitized, f"Session ID should not contain '..': {raw}"

    def test_sanitize_skill_name(self):
        """测试Skill名称净化 / Test skill name sanitization"""
        dangerous_names = [
            ("../../malicious", "malicious"),
            ("normal-skill", "normal-skill"),
            ("../etc-passwd/..", "etc-passwd"),
        ]

        for raw, expected_prefix in dangerous_names:
            sanitized = self.validator.sanitize_skill_name(raw)
            assert "/" not in sanitized, f"Skill name should not contain path separators: {raw}"
            assert ".." not in sanitized, f"Skill name should not contain '..': {raw}"

    def test_sanitize_filename(self):
        """测试文件名净化 / Test filename sanitization"""
        dangerous_filenames = [
            ("../../etc/passwd", "etcpasswd"),
            ("file<>.txt", "file.txt"),
            ("normal.py", "normal.py"),
            ("a|b:c*d", "abcd"),
        ]

        for raw, expected_prefix in dangerous_filenames:
            sanitized = self.validator.sanitize_filename(raw)
            assert "/" not in sanitized, f"Filename should not contain path separators: {raw}"
            assert "\\" not in sanitized, f"Filename should not contain backslashes: {raw}"


class TestSecurityScanner:
    """动态安全扫描器测试 / Security Scanner Tests"""

    def setup_method(self):
        from agent_framework.security.scanner import SecurityScanner
        self.scanner = SecurityScanner()

    def test_scan_python_file_with_shell_true(self):
        """测试扫描 shell=True 漏洞 / Test scanning shell=True vulnerability"""
        from agent_framework.security.scanner import SecurityScanner

        with tempfile.TemporaryDirectory() as tmpdir:
            vuln_file = Path(tmpdir) / "vuln.py"
            vuln_file.write_text("""
import subprocess

def run_cmd(cmd):
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
    )
    return result
""")

            scanner = SecurityScanner()
            report = scanner.scan_directory(tmpdir)

            shell_findings = [f for f in report.findings if f.category == "shell_injection"]
            assert len(shell_findings) > 0, "Should detect shell=True"
            assert any("Shell=True" in f.description for f in shell_findings)

    def test_scan_python_file_with_eval(self):
        """测试扫描 eval() 漏洞 / Test scanning eval() vulnerability"""
        from agent_framework.security.scanner import SecurityScanner

        with tempfile.TemporaryDirectory() as tmpdir:
            vuln_file = Path(tmpdir) / "eval_vuln.py"
            vuln_file.write_text("""
def calculate(expr):
    result = eval(expr)
    return result
""")

            scanner = SecurityScanner()
            report = scanner.scan_directory(tmpdir)

            eval_findings = [f for f in report.findings if f.category == "eval_exec"]
            assert len(eval_findings) > 0, "Should detect eval()"

    def test_scan_clean_file(self):
        """测试扫描干净文件 / Test scanning clean file"""
        from agent_framework.security.scanner import SecurityScanner

        with tempfile.TemporaryDirectory() as tmpdir:
            clean_file = Path(tmpdir) / "clean.py"
            clean_file.write_text("""
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
""")

            scanner = SecurityScanner()
            report = scanner.scan_directory(tmpdir)

            assert len(report.findings) == 0, f"Clean file should have no findings, got {len(report.findings)}"

    def test_scan_hardcoded_secret(self):
        """测试扫描硬编码密钥 / Test scanning hardcoded secrets"""
        from agent_framework.security.scanner import SecurityScanner

        with tempfile.TemporaryDirectory() as tmpdir:
            vuln_file = Path(tmpdir) / "config.py"
            vuln_file.write_text("""
API_KEY = "sk-1234567890abcdef"
SECRET_KEY = "my-super-secret-key"
password = "admin123"
""")

            scanner = SecurityScanner()
            report = scanner.scan_directory(tmpdir)

            secret_findings = [f for f in report.findings if f.category == "hardcoded_secret"]
            assert len(secret_findings) > 0, "Should detect hardcoded secrets"

    def test_scan_insecure_cors(self):
        """测试扫描不安全CORS / Test scanning insecure CORS"""
        from agent_framework.security.scanner import SecurityScanner

        with tempfile.TemporaryDirectory() as tmpdir:
            vuln_file = Path(tmpdir) / "api.py"
            vuln_file.write_text("""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
)
""")

            scanner = SecurityScanner()
            report = scanner.scan_directory(tmpdir)

            cors_findings = [f for f in report.findings if f.category == "insecure_cors"]
            assert len(cors_findings) > 0, "Should detect insecure CORS"

    def test_report_formatting(self):
        """测试报告格式化 / Test report formatting"""
        from agent_framework.security.scanner import SecurityScanner, SecurityFinding, ScanReport

        report = ScanReport(
            scan_time="2024-01-01T00:00:00",
            total_files=10,
            total_findings=2,
            findings_by_severity={"CRITICAL": 1, "HIGH": 1, "MEDIUM": 0, "LOW": 0},
            findings=[
                SecurityFinding(
                    severity="CRITICAL",
                    category="shell_injection",
                    file_path="/test/vuln.py",
                    line_number=5,
                    description="shell=True detected",
                    code_snippet="result = subprocess.run(cmd, shell=True)",
                    recommendation="Use shell=False",
                    cwe="CWE-78",
                ),
            ],
            scan_summary="1 CRITICAL | 1 HIGH | 2 total findings",
        )

        formatted = SecurityScanner.print_report(report)
        assert "CRITICAL" in formatted
        assert "CWE-78" in formatted
        assert "/test/vuln.py" in formatted

    def test_to_json_export(self):
        """测试JSON导出 / Test JSON export"""
        from agent_framework.security.scanner import SecurityScanner, SecurityFinding, ScanReport

        report = ScanReport(
            scan_time="2024-01-01T00:00:00",
            total_files=5,
            total_findings=1,
            findings_by_severity={"CRITICAL": 0, "HIGH": 1, "MEDIUM": 0, "LOW": 0},
            findings=[
                SecurityFinding(
                    severity="HIGH",
                    category="hardcoded_secret",
                    file_path="/test/conf.py",
                    line_number=3,
                    description="Hardcoded API key",
                    code_snippet="API_KEY = 'sk-test'",
                    recommendation="Use env vars",
                    cwe="CWE-798",
                ),
            ],
            scan_summary="1 HIGH | 1 total findings",
        )

        scanner = SecurityScanner()
        json_str = scanner.to_json(report)
        json_data = json.loads(json_str)
        assert json_data["total_findings"] == 1
        assert json_data["findings"][0]["cwe"] == "CWE-798"


class TestIntegration:
    """集成测试 / Integration Tests"""

    def test_scanner_on_project_code(self):
        """测试扫描器在实际项目代码上运行 / Test scanner on actual project code"""
        from agent_framework.security.scanner import SecurityScanner

        project_dir = Path(__file__).parent.parent / "agent_framework"
        if not project_dir.exists():
            return

        scanner = SecurityScanner()
        report = scanner.scan_directory(str(project_dir))

        assert report.total_files > 0, "Should scan at least some files"
        assert report.scan_summary is not None

    def test_path_validator_with_file_tools(self):
        """测试路径验证器与文件工具集成 / Test path validator integration with file tools"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["WORKSPACE_DIR"] = tmpdir

            try:
                from agent_framework.tools.builtin.file.read import FileReadTool
                read_tool = FileReadTool()

                safe_file = Path(tmpdir) / "allowed.txt"
                safe_file.write_text("safe content", encoding="utf-8")

                result = read_tool.execute(str(safe_file))
                assert result["success"], f"Safe file should be readable: {result}"

                malicious_result = read_tool.execute(str(Path(tmpdir) / "../../../etc/passwd"))
                assert not malicious_result.get("success", False), "Path traversal should be blocked"
            finally:
                if "WORKSPACE_DIR" in os.environ:
                    del os.environ["WORKSPACE_DIR"]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
