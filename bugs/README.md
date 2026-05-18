# AloneChat Bug & Vulnerability Tracking System

> **项目**: AloneChat Workspace (AI Agent Framework + Chat App)
> **扫描日期**: 2026-05-14
> **Bug 编号格式**: ACW-XXXX (AloneChat Workspace)
> **扫描范围**: 82 个 Python 文件 + 30 个 TypeScript/React 文件

---

## 目录

| 文件 | 内容 |
|------|------|
| [SECURITY_VULNERABILITIES.md](SECURITY_VULNERABILITIES.md) | 安全漏洞详情（含位置、影响范围、攻击代码） |
| [FUNCTIONAL_BUGS.md](FUNCTIONAL_BUGS.md) | 功能性错误详情 |
| [SUMMARY.md](SUMMARY.md) | 汇总统计 |

## 统计概要

| 类别 | CRITICAL | HIGH | MEDIUM | LOW | 合计 | 已修复 |
|------|----------|------|--------|-----|------|--------|
| **安全漏洞** | 7 | 12 | 19 | 12 | **50** | 6 |
| **功能性错误** | 3 | 6 | 12 | 8 | **29** | 0 |
| **合计** | **10** | **18** | **31** | **20** | **79** | **6** |

> ⚠️ **更新**: 2026-05-14 分析发现 ACW-0001, ACW-0002, ACW-0010, ACW-0013, ACW-0022 等 5 个安全漏洞已被修复，实际 CRITICAL 安全漏洞从 12 降至 7。

## 已修复的安全漏洞

| Bug ID | 问题 | 修复日期 |
|--------|------|----------|
| ACW-0001 | calculator.py eval() 沙箱逃逸 → RCE | 2026-05-14 |
| ACW-0002 | loader.py 路径遍历 → 任意文件读取 | 2026-05-14 |
| ACW-0010 | deepseek_provider.py Bearer None 认证头 | 2026-05-14 |
| ACW-0013 | gateway/tools.py eval() 计算器执行 → RCE | 2026-05-14 |
| ACW-0022 | subprocess_sandbox.py 伪沙箱 → 任意命令执行 | 2026-05-14 |

## 优先级修复建议

1. **P0 - 立即修复**: CRITICAL 级别安全漏洞（RCE、认证绕过、XSS）
2. **P1 - 紧急修复**: CRITICAL 级别功能 Bug（事件循环阻塞、路径遍历）
3. **P2 - 高优先级**: HIGH 级别漏洞和功能 Bug
4. **P3 - 中优先级**: MEDIUM 级别问题
5. **P4 - 低优先级**: LOW 级别问题
