"""
Test Mode Manager - 测试模式管理器 - Test Mode Manager
"""
import pytest
from agent_framework.agent.mode_manager import (
    AgentModeManager,
    ExecutionMode,
    ModeConfig,
    ModeSwitchEvent,
    create_mode_manager,
)
from agent_framework.agent.mode_router import (
    ModeRouter,
    RoutingResult,
    TaskCategory,
    RouterConfig,
    create_router,
)


class TestExecutionMode:
    """测试ExecutionMode枚举"""
    
    def test_mode_values(self):
        """测试模式值"""
        assert ExecutionMode.CODE.value == "code"
        assert ExecutionMode.WORK.value == "work"
    
    def test_mode_comparison(self):
        """测试模式比较"""
        assert ExecutionMode.CODE == ExecutionMode.CODE
        assert ExecutionMode.WORK == ExecutionMode.WORK
        assert ExecutionMode.CODE != ExecutionMode.WORK


class TestModeConfig:
    """测试ModeConfig"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = ModeConfig()
        assert config.mode == ExecutionMode.WORK
        assert config.allow_mode_switch is True
        assert config.auto_detect_mode is False
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = ModeConfig(
            mode=ExecutionMode.CODE,
            allow_mode_switch=False,
            auto_detect_mode=True,
        )
        assert config.mode == ExecutionMode.CODE
        assert config.allow_mode_switch is False
        assert config.auto_detect_mode is True


class TestAgentModeManager:
    """测试AgentModeManager"""
    
    def test_create_manager(self):
        """测试创建管理器"""
        manager = AgentModeManager()
        assert manager is not None
        assert manager.current_mode == ExecutionMode.WORK
    
    def test_create_manager_with_code_mode(self):
        """测试创建CODE模式管理器"""
        config = ModeConfig(mode=ExecutionMode.CODE)
        manager = AgentModeManager(config=config)
        assert manager.current_mode == ExecutionMode.CODE
        assert manager.is_code_mode is True
        assert manager.is_work_mode is False
    
    def test_mode_properties(self):
        """测试模式属性"""
        manager = AgentModeManager()
        assert manager.is_work_mode is True
        assert manager.is_code_mode is False
    
    def test_switch_mode(self):
        """测试模式切换"""
        manager = AgentModeManager()
        
        event = manager.switch_mode(ExecutionMode.CODE, reason="测试切换")
        assert event.to_mode == ExecutionMode.CODE
        assert event.from_mode == ExecutionMode.WORK
        assert manager.current_mode == ExecutionMode.CODE
    
    def test_switch_mode_disabled(self):
        """测试禁用模式切换"""
        config = ModeConfig(allow_mode_switch=False)
        manager = AgentModeManager(config=config)
        
        with pytest.raises(RuntimeError):
            manager.switch_mode(ExecutionMode.CODE)
    
    def test_mode_history(self):
        """测试模式历史"""
        manager = AgentModeManager()
        manager.switch_mode(ExecutionMode.CODE, reason="切换1")
        manager.switch_mode(ExecutionMode.WORK, reason="切换2")
        
        info = manager.get_mode_info()
        assert len(info["switch_history"]) == 2
    
    def test_get_mode_info(self):
        """测试获取模式信息"""
        manager = AgentModeManager()
        info = manager.get_mode_info()
        
        assert "current_mode" in info
        assert "is_code_mode" in info
        assert "is_work_mode" in info
        assert "allow_mode_switch" in info
        assert info["current_mode"] == "work"
    
    def test_reset(self):
        """测试重置"""
        manager = AgentModeManager()
        manager.switch_mode(ExecutionMode.CODE)
        manager.reset()
        
        assert manager.current_mode == ExecutionMode.WORK


class TestCreateModeManager:
    """测试便捷函数"""
    
    def test_create_default(self):
        """测试默认创建"""
        manager = create_mode_manager()
        assert manager.current_mode == ExecutionMode.WORK
    
    def test_create_with_code_mode(self):
        """测试创建CODE模式"""
        manager = create_mode_manager(mode="code")
        assert manager.current_mode == ExecutionMode.CODE
    
    def test_create_with_auto_detect(self):
        """测试自动检测模式"""
        manager = create_mode_manager(auto_detect_mode=True)
        assert manager.config.auto_detect_mode is True


class TestModeRouter:
    """测试ModeRouter"""
    
    def test_create_router(self):
        """测试创建路由器"""
        router = ModeRouter()
        assert router is not None
    
    def test_analyze_code_task(self):
        """测试分析代码任务"""
        router = ModeRouter()
        category, confidence, reasons = router.analyze_task("写一个Python函数")
        
        assert category == TaskCategory.CODE_GENERATION
        assert confidence > 0
    
    def test_analyze_document_task(self):
        """测试分析文档任务"""
        router = ModeRouter()
        category, confidence, reasons = router.analyze_task("写一份项目报告")
        
        assert category == TaskCategory.DOCUMENT_WRITING
        assert confidence > 0
    
    def test_route_code_task(self):
        """测试路由代码任务"""
        router = ModeRouter()
        result = router.route("实现一个排序算法")
        
        assert result.mode == ExecutionMode.CODE
        assert result.category == TaskCategory.CODE_GENERATION
    
    def test_route_document_task(self):
        """测试路由文档任务"""
        router = ModeRouter()
        result = router.route("生成一份销售报告")
        
        assert result.mode == ExecutionMode.WORK
        assert result.category == TaskCategory.DOCUMENT_WRITING
    
    def test_route_with_user_choice(self):
        """测试用户选择优先"""
        router = ModeRouter()
        result = router.route("写一个函数", user_choice=ExecutionMode.WORK)
        
        assert result.mode == ExecutionMode.WORK
        assert result.confidence == 1.0
    
    def test_get_routing_info(self):
        """测试获取路由信息"""
        router = ModeRouter()
        info = router.get_routing_info("修复这个bug")
        
        assert "recommended_mode" in info
        assert "category" in info
        assert "confidence" in info
        assert info["recommended_mode"] == "code"


class TestTaskCategory:
    """测试TaskCategory"""
    
    def test_category_values(self):
        """测试类别值"""
        assert TaskCategory.CODE_GENERATION.value == "code_generation"
        assert TaskCategory.CODE_DEBUG.value == "code_debug"
        assert TaskCategory.DOCUMENT_WRITING.value == "document_writing"
        assert TaskCategory.DATA_ANALYSIS.value == "data_analysis"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
