"""
安全配置和安全初始化 - Security Configuration & Initialization
安全配置和安全初始化

集中管理所有安全相关的配置和初始化逻辑
Centralizes all security-related configuration and initialization logic

配置层次 / Configuration Hierarchy:
1. 环境变量（最高优先级） / Environment variables (highest priority)
2. YAML配置文件 / YAML config files
3. 代码默认值 / Code defaults
"""
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class SecurityConfig:
    """
    安全配置 - Security Configuration / 安全配置
    定义所有安全相关的可配置参数
    Defines all security-related configurable parameters

    认证设置 / Authentication Settings:
    - JWT密钥和过期时间 / JWT key and expiry
    - 密码策略 / Password policy
    - 账户锁定策略 / Account lockout policy

    速率限制设置 / Rate Limiting Settings:
    - 全局限制 / Global limits
    - 每IP/用户/API Key限制 / Per-IP/user/API key limits

    CORS设置 / CORS Settings:
    - 允许的域名 / Allowed origins
    - 允许的方法和头 / Allowed methods and headers

    日志设置 / Logging Settings:
    - 日志级别 / Log level
    - 输出格式 / Output format
    """
    
    # JWT配置 / JWT Configuration
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expiry_minutes: int = 30
    jwt_refresh_token_expiry_days: int = 7
    
    # 密码策略 / Password Policy
    password_min_length: int = 8
    password_max_length: int = 128
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_hash_algorithm: str = "bcrypt"  # bcrypt or pbkdf2
    password_pbkdf2_iterations: int = 200000
    
    # 账户锁定策略 / Account Lockout Policy
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    account_lockout_enabled: bool = True
    
    # 速率限制策略 / Rate Limiting Policy
    rate_limit_global_rpm: int = 60
    rate_limit_global_tpm: int = 100000
    rate_limit_per_ip_rpm: Optional[int] = 20
    rate_limit_per_user_rpm: Optional[int] = 30
    rate_limit_per_api_key_rpm: Optional[int] = 100
    rate_limit_burst_size: int = 10
    
    # CORS配置 / CORS Configuration
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_allow_headers: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization"])
    
    # 安全头 / Security Headers
    enable_security_headers: bool = True
    hsts_max_age_seconds: int = 31536000
    csp_policy: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'"
    )
    
    # CSRF保护 / CSRF Protection
    csrf_enabled: bool = True
    csrf_token_expiry_seconds: int = 3600
    
    # 输入验证 / Input Validation
    max_request_size_bytes: int = 10 * 1024 * 1024  # 10MB
    sanitize_html_output: bool = True
    validate_sql_injection: bool = True
    validate_command_injection: bool = True
    
    # 日志配置 / Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    log_include_timestamp: bool = True
    log_include_source: bool = True
    log_sensitive_data_masking: bool = True
    
    # 数据库配置 / Database Configuration
    database_path: str = "data/alonechat.db"
    database_enable_wal_mode: bool = True
    database_cleanup_interval_hours: int = 24
    
    # 审计日志 / Audit Log
    audit_log_enabled: bool = True
    audit_log_retention_days: int = 90
    
    # 调试模式 / Debug Mode
    debug_mode: bool = False
    show_detailed_errors: bool = False
    
    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """
        从环境变量加载配置 - Load configuration from environment variables
        从環境變量加載配置
        
        Returns:
            SecurityConfig实例 / SecurityConfig instance
        """
        return cls(
            # JWT / JWT
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", ""),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_access_token_expiry_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "30")),
            jwt_refresh_token_expiry_days=int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7")),
            
            # 密碼 / Password
            password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
            password_max_length=int(os.getenv("PASSWORD_MAX_LENGTH", "128")),
            password_require_uppercase=os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true",
            password_require_lowercase=os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true",
            password_require_digit=os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true",
            password_hash_algorithm=os.getenv("PASSWORD_HASH_ALGORITHM", "bcrypt"),
            password_pbkdf2_iterations=int(os.getenv("PBKDF2_ITERATIONS", "200000")),
            
            # 賬戶鎖定 / Account Lockout
            max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
            lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")),
            account_lockout_enabled=os.getenv("ACCOUNT_LOCKOUT_ENABLED", "true").lower() == "true",
            
            # 速率限制 / Rate Limiting
            rate_limit_global_rpm=int(os.getenv("RATE_LIMIT_RPM", "60")),
            rate_limit_global_tpm=int(os.getenv("RATE_LIMIT_TPM", "100000")),
            rate_limit_per_ip_rpm=int(os.getenv("RATE_LIMIT_PER_IP_RPM")) if os.getenv("RATE_LIMIT_PER_IP_RPM") else None,
            rate_limit_per_user_rpm=int(os.getenv("RATE_LIMIT_PER_USER_RPM")) if os.getenv("RATE_LIMIT_PER_USER_RPM") else None,
            rate_limit_per_api_key_rpm=int(os.getenv("RATE_LIMIT_PER_API_KEY_RPM")) if os.getenv("RATE_LIMIT_PER_API_KEY_RPM") else None,
            
            # CORS
            cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),
            
            # 日誌 / Logging
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),
            
            # 數據庫 / Database
            database_path=os.getenv("DATABASE_PATH", "data/alonechat.db"),
            
            # 調試 / Debug
            debug_mode=os.getenv("DEBUG", "").lower() in ("true", "1", "yes"),
            show_detailed_errors=os.getenv("SHOW_DETAILED_ERRORS", "").lower() == "true",
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 - Convert to dictionary / 轉換為字典"""
        import dataclasses
        return dataclasses.asdict(self)
    
    def validate(self) -> List[str]:
        """
        验证配置有效性 - Validate configuration validity / 驗證配置有效性
        
        Returns:
            错误消息列表（空列表表示有效） / Error message list (empty means valid)
        """
        errors = []
        
        if self.jwt_access_token_expiry_minutes < 1:
            errors.append("JWT access token expiry must be at least 1 minute")
        
        if self.jwt_access_token_expiry_minutes > 1440:  # 24 hours
            errors.append("JWT access token expiry should not exceed 24 hours for security")
        
        if self.password_min_length < 8:
            errors.append("Password minimum length should be at least 8 characters")
        
        if self.max_login_attempts < 1:
            errors.append("Max login attempts must be at least 1")
        
        if self.lockout_duration_minutes < 1:
            errors.append("Lockout duration must be at least 1 minute")
        
        if self.rate_limit_global_rpm < 1:
            errors.append("Global RPM limit must be at least 1")
        
        return errors


def get_security_config() -> SecurityConfig:
    """
    获取安全配置实例 - Get security configuration instance / 獲取安全配置實例
    单例模式，确保全局唯一
    Singleton pattern, ensures global uniqueness
    
    Returns:
        SecurityConfig实例 / SecurityConfig instance
    """
    return SecurityConfig.from_env()


def initialize_security_components():
    """
    初始化所有安全组件 - Initialize all security components
    初始化所有安全組件
    
    应该在应用启动时调用此函数
    This function should be called during application startup
    
    初始化顺序 / Initialization order:
    1. 加载配置 / Load configuration
    2. 验证配置 / Validate configuration
    3. 初始化数据库 / Initialize database
    4. 设置中间件 / Set up middleware
    5. 配置日志 / Configure logging
    """
    from .error_handling import get_logger
    logger = get_logger()
    
    logger.info("Initializing security components...", component="security_init")
    
    # 1. 加载配置 / Load config
    config = get_security_config()
    logger.info(f"Security config loaded, debug mode={config.debug_mode}")
    
    # 2. 验证配置 / Validate config
    validation_errors = config.validate()
    if validation_errors:
        for error in validation_errors:
            logger.warning(f"Config validation warning: {error}")
    
    # 3. 检查依赖 / Check dependencies
    _check_dependencies(logger)
    
    # 4. 初始化数据库 / Initialize database
    try:
        from .storage.database_manager import get_database
        db = get_database(config.database_path)
        logger.info(f"Database initialized: {config.database_path}", component="database")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", component="database")
        raise
    
    # 5. 完成初始化 / Complete initialization
    logger.info(
        "Security components initialized successfully",
        jwt_algo=config.jwt_algorithm,
        rate_limit_rpm=config.rate_limit_global_rpm,
        csrf_enabled=config.csrf_enabled,
        component="security_init"
    )
    
    return config


def _check_dependencies(logger):
    """检查依赖项 - Check dependencies / 檢查依賴項"""
    missing = []
    
    optional_deps = {
        "aiosqlite": "pip install aiosqlite",
        "bcrypt": "pip install bcrypt (recommended for better security)",
    }
    
    for dep, install_cmd in optional_deps.items():
        try:
            __import__(dep)
        except ImportError:
            missing.append((dep, install_cmd))
    
    if missing:
        for dep, cmd in missing:
            logger.warning(
                f"Optional dependency '{dep}' not installed. Install with: {cmd}",
                component="dependencies"
            )
