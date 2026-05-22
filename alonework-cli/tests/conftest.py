"""
Pytest 配置和共享 fixtures
"""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """提供临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_trajectory_data():
    """提供示例轨迹数据"""
    return {
        "session_id": "test-session-001",
        "task": "测试任务",
        "steps": [
            {
                "step_id": "step-1",
                "action": {"type": "code", "content": "print('hello')"},
                "observation": {"output": "hello", "status": "success"},
                "reward": 1.0,
                "timestamp": "2024-01-01T00:00:00",
            },
            {
                "step_id": "step-2",
                "action": {"type": "code", "content": "x = 1 + 1"},
                "observation": {"output": "2", "status": "success"},
                "reward": 1.0,
                "timestamp": "2024-01-01T00:00:01",
            },
        ],
        "metadata": {"model": "deepseek-v4-flash"},
    }


@pytest.fixture
def sample_workflow_definition():
    """提供示例工作流定义"""
    return {
        "id": "test-workflow-001",
        "name": "测试工作流",
        "description": "用于测试的工作流",
        "nodes": {
            "start": {
                "id": "start",
                "name": "开始",
                "type": "start",
                "config": {},
                "metadata": {},
            },
            "action1": {
                "id": "action1",
                "name": "行动1",
                "type": "action",
                "config": {"agent": "code_agent"},
                "metadata": {},
            },
            "end": {
                "id": "end",
                "