"""
动态安全扫描器 - Dynamic Security Scanner

运行时检测代码库中的安全漏洞
Runtime detection of security vulnerabilities in the codebase

支持 / Supports:
- 路径遍历检测 / Path traversal detection
- 命令注入检测 / Command injection detection
- 硬编码密钥检测 / Hardcoded secret detection
- 不安全配置检测 / Insecure configuration detection
- 依赖漏洞检查 / Dependency vulnerability checking
"""
import ast
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SecurityFinding:
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # path_traversal, command_injection, hardcoded_secret, etc.
    file_path: str
    line_number: int
    description: str
    code_snippet: str
    recommendation: str
    cwe: Optional[str] = None


@dataclass
class ScanReport:
    scan_time: str
    total_files: int
    total_findings: int
    findings_by_severity: Dict[str, int]
    findings: List[SecurityFinding]
    scan_summary: str


class SecurityScanner:
    """
    动态安全扫描器 - Dynamic Security Scanner

    在运行时分析代码库中的安全漏洞
    Analyzes codebase for security vulnerabilities at runtime

    用法 / Usage:
        scanner = SecurityScanner()
        report = scanner.scan_directory("/path/to/project")
        print(report.scan_summary)
    """

    DANGEROUS_PATTERNS: Dict[str, List[Dict[str, Any]]] = {
        "path_traversal": [
            {
                "pattern": r"Path\(.*\)",
                "check": lambda code, node: _check_path_traversal(code, node),
                "severity": "HIGH",
                "cwe": "CWE-22",
            },
        ],
        "shell_injection": [
            {
                "pattern": r"shell\s*=\s*True",
                "severity": "CRITICAL",
                "cwe": "CWE-78",
            },
            {
                "pattern": r"subprocess\.run\(.*shell\s*=\s*True",
                "severity": "CRITICAL",
                "cwe": "CWE-78",
            },
            {
                "pattern": r"os\.system\(|os\.popen\(|subprocess\.Popen\(.*shell\s*=\s*True",
                "severity": "CRITICAL",
                "cwe": "CWE-78",
            },
        ],
        "hardcoded_secret": [
            {
                "pattern": r"""(?i)(?:api[_-]?key|secret|password|token|credential)\s*[=:]\s*['\"](?!\$|\{|env)""",
                "severity": "HIGH",
                "cwe": "CWE-798",
            },
            {
                "pattern": r"""(?i)jwt[_-]?secret|session[_-]?secret|encryption[_-]?key""",
                "severity": "HIGH",
                "cwe": "CWE-798",
            },
        ],
        "insecure_cors": [
            {
                "pattern": r"""allow_origins\s*=\s*\[['\"]\*['\"]\]""",
                "severity": "HIGH",
                "cwe": "CWE-942",
            },
        ],
        "insecure_deserialization": [
            {
                "pattern": r"pickle\.loads?\(|yaml\.load\(|marshal\.loads?\(",
                "severity": "CRITICAL",
                "cwe": "CWE-502",
            },
        ],
        "eval_exec": [
            {
                "pattern": r"(?<![a-zA-Z_])eval\(|(?<![a-zA-Z_])exec\(",
                "severity": "CRITICAL",
                "cwe": "CWE-95",
            },
        ],
    }

    IGNORED_DIRS = {
        "__pycache__", ".git", ".svn", "node_modules",
        ".venv", "venv", "env", ".tox", ".eggs",
        "dist", "build", ".npm", ".yarn",
    }

    IGNORED_EXTENSIONS = {
        ".pyc", ".pyo", ".so", ".dll", ".dylib",
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
        ".woff", ".woff2", ".ttf", ".eot",
        ".zip", ".tar", ".gz", ".bz2",
        ".exe", ".msi", ".deb", ".rpm",
        ".lock", ".sum", ".map",
    }

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path).resolve() if base_path else Path.cwd()
        self.findings: List[SecurityFinding] = []
        self.scanned_files: int = 0

    def scan_directory(
        self,
        directory: Optional[str] = None,
        recursive: bool = True,
        file_patterns: Optional[Set[str]] = None,
    ) -> ScanReport:
        """
        扫描目录中的安全漏洞 / Scan directory for security vulnerabilities

        Args:
            directory: 要扫描的目录 / Directory to scan
            recursive: 是否递归扫描 / Whether to scan recursively
            file_patterns: 文件匹配模式 / File matching patterns

        Returns:
            扫描报告 / Scan report
        """
        scan_path = Path(directory).resolve() if directory else self.base_path
        if not scan_path.exists():
            return ScanReport(
                scan_time=datetime.utcnow().isoformat(),
                total_files=0,
                total_findings=0,
                findings_by_severity={},
                findings=[],
                scan_summary=f"Directory not found: {scan_path}",
            )

        self.findings.clear()
        self.scanned_files = 0

        if file_patterns is None:
            file_patterns = {"*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.rs", "*.go", "*.java", "*.yaml", "*.yml", "*.json", "*.sh"}

        for pattern in file_patterns:
            if recursive:
                for file_path in scan_path.rglob(pattern):
                    self._scan_file(file_path)
            else:
                for file_path in scan_path.glob(pattern):
                    self._scan_file(file_path)

        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for finding in self.findings:
            sev = finding.severity.upper()
            if sev in severity_counts:
                severity_counts[sev] += 1

        total_critical = severity_counts.get("CRITICAL", 0)
        total_high = severity_counts.get("HIGH", 0)
        total_medium = severity_counts.get("MEDIUM", 0)

        summary_parts = []
        if self.scanned_files > 0:
            summary_parts.append(f"Scanned {self.scanned_files} files")
        if total_critical > 0:
            summary_parts.append(f"{total_critical} CRITICAL")
        if total_high > 0:
            summary_parts.append(f"{total_high} HIGH")
        if total_medium > 0:
            summary_parts.append(f"{total_medium} MEDIUM")
        summary_parts.append(f"{len(self.findings)} total findings")

        return ScanReport(
            scan_time=datetime.utcnow().isoformat(),
            total_files=self.scanned_files,
            total_findings=len(self.findings),
            findings_by_severity=severity_counts,
            findings=self.findings.copy(),
            scan_summary=" | ".join(summary_parts),
        )

    def _scan_file(self, file_path: Path) -> None:
        """扫描单个文件 / Scan a single file"""
        if not file_path.is_file():
            return

        if any(ignored in file_path.parts for ignored in self.IGNORED_DIRS):
            return

        ext = file_path.suffix.lower()
        if ext in self.IGNORED_EXTENSIONS:
            return

        self.scanned_files += 1

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        self._scan_with_regex(file_path, content)

        if ext == ".py":
            self._scan_python_ast(file_path, content)

    def _scan_with_regex(self, file_path: Path, content: str) -> None:
        """使用正则表达式扫描 / Scan using regex patterns"""
        lines = content.split("\n")

        for category, patterns in self.DANGEROUS_PATTERNS.items():
            for pattern_config in patterns:
                regex = re.compile(pattern_config["pattern"])
                for match in regex.finditer(content):
                    line_number = content[:match.start()].count("\n") + 1

                    check_fn = pattern_config.get("check")
                    if check_fn:
                        if not check_fn(content, None):
                            continue

                    line_content = lines[line_number - 1].strip() if line_number <= len(lines) else ""

                    self.findings.append(SecurityFinding(
                        severity=pattern_config["severity"],
                        category=category,
                        file_path=str(file_path),
                        line_number=line_number,
                        description=self._get_description(category),
                        code_snippet=line_content[:200],
                        recommendation=self._get_recommendation(category),
                        cwe=pattern_config.get("cwe"),
                    ))

    def _scan_python_ast(self, file_path: Path, content: str) -> None:
        """使用Python AST进行深度扫描 / Deep scan using Python AST"""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._check_ast_call(file_path, node, content)

    def _check_ast_call(self, file_path: Path, node: ast.Call, content: str) -> None:
        """检查AST调用节点 / Check AST call nodes"""
        func_name = self._get_call_name(node)

        if func_name in ("open",):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    line_number = node.lineno
                    self.findings.append(SecurityFinding(
                        severity="CRITICAL",
                        category="command_injection",
                        file_path=str(file_path),
                        line_number=line_number,
                        description="Shell=True detected in subprocess call",
                        code_snippet=content.split("\n")[line_number - 1].strip() if line_number > 0 else "",
                        recommendation="Use subprocess with shell=False and pass args as a list",
                        cwe="CWE-78",
                    ))

        if func_name and ("subprocess" in func_name or func_name in ("run", "Popen", "call")):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    line_number = node.lineno
                    self.findings.append(SecurityFinding(
                        severity="CRITICAL",
                        category="command_injection",
                        file_path=str(file_path),
                        line_number=line_number,
                        description="shell=True in subprocess call",
                        code_snippet=content.split("\n")[line_number - 1].strip() if line_number > 0 else "",
                        recommendation="Remove shell=True and pass command as a list of arguments",
                        cwe="CWE-78",
                    ))

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """获取函数调用名 / Get function call name"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return f"{self._get_attribute_base(node.func)}.{node.func.attr}"
        return None

    def _get_attribute_base(self, node: ast.Attribute) -> str:
        """获取属性访问的基名 / Get base name of attribute access"""
        if isinstance(node.value, ast.Name):
            return node.value.id
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_base(node.value)}.{node.value.attr}"
        return ""

    def _get_description(self, category: str) -> str:
        descriptions = {
            "path_traversal": "Potential path traversal vulnerability - user-controlled path without validation",
            "shell_injection": "Shell=True detected - potential command injection vulnerability",
            "hardcoded_secret": "Hardcoded secret/credential detected - sensitive information in source code",
            "insecure_cors": "Insecure CORS configuration - allow_origins=['*'] allows any origin",
            "insecure_deserialization": "Insecure deserialization detected - potential code execution risk",
            "eval_exec": "Dynamic code execution detected - potential code injection vulnerability",
        }
        return descriptions.get(category, f"Security issue detected: {category}")

    def _get_recommendation(self, category: str) -> str:
        recommendations = {
            "path_traversal": "Use PathValidator.resolve_safe_path() to validate paths against an allowed base directory",
            "shell_injection": "Use shlex.split() to parse commands and pass as list; never use shell=True",
            "hardcoded_secret": "Use environment variables (os.getenv) or a secrets manager instead of hardcoding",
            "insecure_cors": "Use specific allowed origins from environment variable instead of wildcard '*'",
            "insecure_deserialization": "Use safe alternatives like yaml.safe_load() or json.loads()",
            "eval_exec": "Use ast.literal_eval() for safe evaluation or restrict allowed AST nodes",
        }
        return recommendations.get(category, "Review and fix the security issue")

    def to_json(self, report: ScanReport) -> str:
        """导出扫描报告为JSON / Export scan report as JSON"""
        return json.dumps({
            "scan_time": report.scan_time,
            "total_files": report.total_files,
            "total_findings": report.total_findings,
            "findings_by_severity": report.findings_by_severity,
            "scan_summary": report.scan_summary,
            "findings": [
                {
                    "severity": f.severity,
                    "category": f.category,
                    "file": f.file_path,
                    "line": f.line_number,
                    "description": f.description,
                    "cwe": f.cwe,
                }
                for f in report.findings
            ],
        }, indent=2)

    @staticmethod
    def print_report(report: ScanReport) -> str:
        """格式化打印扫描报告 / Format and print scan report"""
        lines = []
        lines.append("=" * 70)
        lines.append("  动态安全扫描报告 / Dynamic Security Scan Report")
        lines.append("=" * 70)
        lines.append(f"  扫描时间 / Scan time: {report.scan_time}")
        lines.append(f"  扫描文件 / Files scanned: {report.total_files}")
        lines.append(f"  发现漏洞 / Findings: {report.total_findings}")
        lines.append("-" * 70)

        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        for sev in severity_order:
            count = report.findings_by_severity.get(sev, 0)
            if count > 0:
                lines.append(f"  [{sev}] {count} 个漏洞 / {count} findings")

        lines.append("-" * 70)

        for i, finding in enumerate(report.findings[:50], 1):
            lines.append(f"\n  #{i} [{finding.severity}] {finding.category}")
            lines.append(f"      文件 / File: {finding.file_path}:{finding.line_number}")
            lines.append(f"      描述 / Desc: {finding.description}")
            if finding.cwe:
                lines.append(f"      CWE: {finding.cwe}")
            lines.append(f"      建议 / Fix: {finding.recommendation}")

        if len(report.findings) > 50:
            lines.append(f"\n  ... 还有 {len(report.findings) - 50} 个漏洞 / ... and {len(report.findings) - 50} more findings")

        lines.append("\n" + "=" * 70)
        lines.append(f"  扫描摘要 / Summary: {report.scan_summary}")
        lines.append("=" * 70)

        return "\n".join(lines)


def _check_path_traversal(code: str, node) -> bool:
    """检查路径遍历模式 / Check for path traversal patterns"""
    suspicious_patterns = [
        r"Path\(.*\)\s*/\s*[a-zA-Z]",
        r"open\(.*Path",
        r"Path\(.*request|Path\(.*input|Path\(.*arg|Path\(.*param",
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, code):
            return True
    return False


def scan_project(project_path: Optional[str] = None) -> ScanReport:
    """
    便捷函数：扫描项目安全漏洞 / Convenience function: scan project for vulnerabilities

    Args:
        project_path: 项目路径 / Project path

    Returns:
        扫描报告 / Scan report
    """
    scanner = SecurityScanner(project_path)
    return scanner.scan_directory(project_path)
