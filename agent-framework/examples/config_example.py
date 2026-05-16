"""
配置管理示例
展示如何使用配置系统
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_framework.observability.logger import get_logger, LogLevel
from agent_framework.config import (
    get_config,
    get_config_manager,
    AgentConfig,
    LLMSettings,
    GatewaySettings,
    MemorySettings
)


# 初始化日志
logger = get_logger("config_example", level=LogLevel.INFO)


def example_basic_config():
    """基础配置使用示例"""
    logger.info("=" * 50)
    logger.info("Example 1: Basic Config Usage")
    logger.info("=" * 50)
    
    # 获取配置
    config = get_config()
    
    logger.info(f"Debug mode: {config.debug}")
    logger.info(f"Data directory: {config.data_dir}")
    
    # LLM配置
    logger.info(f"\nLLM Provider: {config.llm.provider}")
    logger.info(f"LLM Model: {config.llm.model}")
    logger.info(f"LLM Temperature: {config.llm.temperature}")
    
    # Gateway配置
    logger.info(f"\nGateway Host: {config.gateway.host}")
    logger.info(f"Gateway Port: {config.gateway.port}")
    
    # 配置转换为字典
    config_dict = config.to_dict()
    logger.info(f"\nConfig dict keys: {list(config_dict.keys())}")


def example_config_from_dict():
    """从字典创建配置示例"""
    logger.info("\n" + "=" * 50)
    logger.info("Example 2: Config from Dict")
    logger.info("=" * 50)
    
    custom_config = AgentConfig.from_dict({
        "debug": True,
        "llm": {
            "provider": "anthropic",
            "model": "claude-3-sonnet",
            "temperature": 0.7
        },
        "gateway": {
            "port": 9090,
            "enable_cors": True
        }
    })
    
    logger.info(f"Custom debug: {custom_config.debug}")
    logger.info(f"Custom LLM: {custom_config.llm.provider}/{custom_config.llm.model}")
    logger.info(f"Custom port: {custom_config.gateway.port}")


def example_config_save_load():
    """配置保存和加载示例"""
    logger.info("\n" + "=" * 50)
    logger.info("Example 3: Config Save & Load")
    logger.info("=" * 50)
    
    # 创建临时配置
    config = AgentConfig(
        debug=True,
        llm=LLMSettings(
            provider="openai",
            model="gpt-4o",
            temperature=0.5
        ),
        gateway=GatewaySettings(
            port=8787,
            host="0.0.0.0"
        ),
        memory=MemorySettings(
            window_size=20,
            enable_persistence=True
        )
    )
    
    # 保存为YAML
    yaml_path = Path(__file__).parent.parent / "data" / "config_example.yaml"
    yaml_path.parent.mkdir(exist_ok=True)
    config.to_yaml(str(yaml_path))
    logger.info(f"Saved config to: {yaml_path}")
    
    # 从YAML加载
    loaded_config = AgentConfig.from_yaml(str(yaml_path))
    logger.info(f"Loaded config from YAML")
    logger.info(f"  Debug: {loaded_config.debug}")
    logger.info(f"  LLM Model: {loaded_config.llm.model}")
    logger.info(f"  Gateway Port: {loaded_config.gateway.port}")
    
    # 保存为JSON
    json_path = Path(__file__).parent.parent / "data" / "config_example.json"
    config.to_json(str(json_path))
    logger.info(f"\nSaved config to: {json_path}")


def example_config_manager():
    """配置管理器示例"""
    logger.info("\n" + "=" * 50)
    logger.info("Example 4: Config Manager")
    logger.info("=" * 50)
    
    # 获取配置管理器
    manager = get_config_manager()
    
    # 注册变更回调
    config_changes = []
    
    def on_config_change(new_config: AgentConfig):
        config_changes.append(new_config)
        logger.info(f"Config changed! New debug mode: {new_config.debug}")
    
    manager.add_change_callback(on_config_change)
    
    # 获取当前配置
    logger.info(f"Initial debug mode: {manager.config.debug}")
    
    # 更新配置
    logger.info("\nUpdating config...")
    manager.update({
        "debug": True,
        "llm": {
            "temperature": 0.9
        }
    })
    
    # 验证变更
    logger.info(f"Updated debug mode: {manager.config.debug}")
    logger.info(f"Updated LLM temperature: {manager.config.llm.temperature}")
    logger.info(f"Config changes recorded: {len(config_changes)}")
    
    # 重新加载（模拟文件变更）
    logger.info("\nReloading config...")
    manager.reload()


def example_config_validation():
    """配置验证示例"""
    logger.info("\n" + "=" * 50)
    logger.info("Example 5: Config Validation")
    logger.info("=" * 50)
    
    try:
        # 正常配置
        valid_config = LLMSettings(
            provider="openai",
            model="gpt-4",
            temperature=0.7,
            max_tokens=4096
        )
        logger.info("Valid config created successfully")
        
        # 无效温度（会被Pydantic验证）
        try:
            invalid_config = LLMSettings(
                temperature=1.5,  # 超过1.0会有问题
                max_tokens=100
            )
            logger.info(f"Created config with temperature: {invalid_config.temperature}")
        except Exception as e:
            logger.error(f"Expected validation error: {e}")
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


async def example_config_hot_reload():
    """配置热加载示例"""
    logger.info("\n" + "=" * 50)
    logger.info("Example 6: Hot Reload (simulated)")
    logger.info("=" * 50)
    
    # 创建临时配置文件
    config_path = Path(__file__).parent.parent / "data" / "watch_config.yaml"
    config_path.parent.mkdir(exist_ok=True)
    
    # 初始配置
    initial_config = AgentConfig(debug=False, llm=LLMSettings(model="gpt-3.5-turbo"))
    initial_config.to_yaml(str(config_path))
    
    # 创建带文件路径的配置管理器
    manager = get_config_manager(str(config_path))
    
    # 初始状态
    logger.info(f"Initial model: {manager.config.llm.model}")
    logger.info(f"Initial debug: {manager.config.debug}")
    
    # 模拟配置文件更新
    logger.info("\nSimulating config file update...")
    updated_config = AgentConfig(debug=True, llm=LLMSettings(model="gpt-4o"))
    updated_config.to_yaml(str(config_path))
    
    # 手动触发重新加载（实际应用中会自动监测）
    manager.reload()
    
    # 检查新配置
    logger.info(f"Updated model: {manager.config.llm.model}")
    logger.info(f"Updated debug: {manager.config.debug}")
    
    # 清理
    if config_path.exists():
        config_path.unlink()


def main():
    """主函数"""
    logger.info("⚙️ Config Management Examples")
    
    try:
        example_basic_config()
        example_config_from_dict()
        example_config_save_load()
        example_config_manager()
        example_config_validation()
        
        # 异步示例
        logger.info("\n" + "=" * 50)
        logger.info("Running async examples...")
        logger.info("=" * 50)
        asyncio.run(example_config_hot_reload())
        
        logger.info("\n✅ All examples completed!")
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
