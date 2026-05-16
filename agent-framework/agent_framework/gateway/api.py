"""
REST API - 模式管理、任务管理、Skills管理
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agent_framework.core.types import AgentMode, TaskStatus
from agent_framework.core.task import Task, Artifact
from agent_framework.agent.mtc_agent import MTCAgent
from agent_framework.agent.code_agent import CodeAgent
from agent_framework.tools.skills_registry import SkillsRegistry, register_builtin_skills
from agent_framework.tools.skills_marketplace import SkillsMarketplace


app = FastAPI(title="MTC/CODE Mode API", version="1.0.0")


class ModeSwitchRequest(BaseModel):
    target_mode: str = Field(..., description="目标模式: MTC 或 CODE")
    session_id: Optional[str] = Field(None, description="会话ID")


class ModeSwitchResponse(BaseModel):
    success: bool
    current_mode: str
    previous_mode: Optional[str] = None
    message: str


class TaskCreateRequest(BaseModel):
    description: str = Field(..., description="任务描述")
    mode: Optional[str] = Field(None, description="执行模式")
    priority: Optional[str] = Field("medium", description="优先级")


class TaskResponse(BaseModel):
    id: str
    description: str
    status: str
    priority: str
    created_at: str


class SkillExecuteRequest(BaseModel):
    skill_name: str = Field(..., description="Skill名称")
    context: Dict[str, Any] = Field(default_factory=dict, description="执行上下文")


class SkillExecuteResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ArtifactResponse(BaseModel):
    id: str
    name: str
    type: str
    path: str
    size: int
    created_at: str


class ModeManager:
    """模式管理器"""
    
    def __init__(self):
        self._current_mode = AgentMode.MTC
        self._agents: Dict[str, Any] = {}
        self._sessions: Dict[str, AgentMode] = {}
    
    def get_current_mode(self, session_id: Optional[str] = None) -> AgentMode:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self._current_mode
    
    def switch_mode(self, target_mode: str, session_id: Optional[str] = None) -> ModeSwitchResponse:
        try:
            new_mode = AgentMode(target_mode.upper())
        except ValueError:
            return ModeSwitchResponse(
                success=False,
                current_mode=self._current_mode.value,
                message=f"无效的模式: {target_mode}",
            )
        
        previous_mode = self._current_mode
        
        if session_id:
            self._sessions[session_id] = new_mode
        else:
            self._current_mode = new_mode
        
        return ModeSwitchResponse(
            success=True,
            current_mode=new_mode.value,
            previous_mode=previous_mode.value,
            message=f"模式已切换: {previous_mode.value} -> {new_mode.value}",
        )
    
    def get_agent(self, mode: AgentMode, llm=None) -> Any:
        if mode == AgentMode.MTC:
            return MTCAgent(llm=llm)
        else:
            return CodeAgent(llm=llm)


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._artifacts: Dict[str, Artifact] = {}
    
    def create_task(self, description: str, priority: str = "medium") -> Task:
        from agent_framework.core.types import TaskPriority
        
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "critical": TaskPriority.CRITICAL,
        }
        
        task = Task(
            description=description,
            priority=priority_map.get(priority.lower(), TaskPriority.MEDIUM),
        )
        
        self._tasks[task.id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)
    
    def list_tasks(self, status: Optional[str] = None) -> List[Task]:
        tasks = list(self._tasks.values())
        
        if status:
            try:
                target_status = TaskStatus(status.lower())
                tasks = [t for t in tasks if t.status == target_status]
            except ValueError:
                pass
        
        return tasks
    
    def cancel_task(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task:
            task.status = TaskStatus.CANCELLED
            return True
        return False
    
    def add_artifact(self, artifact: Artifact) -> None:
        self._artifacts[artifact.id] = artifact
    
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        return self._artifacts.get(artifact_id)
    
    def list_artifacts(self) -> List[Artifact]:
        return list(self._artifacts.values())


mode_manager = ModeManager()
task_manager = TaskManager()
skills_registry = SkillsRegistry()
skills_marketplace = SkillsMarketplace(skills_registry)

register_builtin_skills(skills_registry)


@app.get("/api/mode")
async def get_mode(session_id: Optional[str] = Query(None)):
    """获取当前模式"""
    current_mode = mode_manager.get_current_mode(session_id)
    return {
        "mode": current_mode.value,
        "session_id": session_id,
        "available_modes": [m.value for m in AgentMode],
    }


@app.post("/api/mode/switch", response_model=ModeSwitchResponse)
async def switch_mode(request: ModeSwitchRequest):
    """切换模式"""
    return mode_manager.switch_mode(request.target_mode, request.session_id)


@app.get("/api/tasks")
async def list_tasks(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """获取任务列表"""
    tasks = task_manager.list_tasks(status)
    
    return {
        "tasks": [
            TaskResponse(
                id=t.id,
                description=t.description,
                status=t.status.value,
                priority=t.priority.value,
                created_at=t.created_at.isoformat(),
            )
            for t in tasks[:limit]
        ],
        "total": len(tasks),
    }


@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(request: TaskCreateRequest):
    """创建新任务"""
    task = task_manager.create_task(
        description=request.description,
        priority=request.priority or "medium",
    )
    
    return TaskResponse(
        id=task.id,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        created_at=task.created_at.isoformat(),
    )


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """获取任务详情"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    return {
        "id": task.id,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "dependencies": [d.model_dump() for d in task.dependencies],
        "metadata": task.metadata,
    }


@app.delete("/api/tasks/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    success = task_manager.cancel_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    return {"success": True, "message": f"任务已取消: {task_id}"}


@app.get("/api/skills")
async def list_skills(
    category: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
):
    """列出所有Skills"""
    if query:
        skills = skills_marketplace.search(query)
    else:
        skills = skills_marketplace.list_skills(category)
    
    return {
        "skills": skills,
        "total": len(skills),
        "categories": skills_registry.get_categories(),
    }


@app.get("/api/skills/{skill_name}")
async def get_skill(skill_name: str):
    """获取Skill详情"""
    details = skills_marketplace.get_details(skill_name)
    
    if not details:
        raise HTTPException(status_code=404, detail=f"Skill不存在: {skill_name}")
    
    return details


@app.post("/api/skills/execute", response_model=SkillExecuteResponse)
async def execute_skill(request: SkillExecuteRequest):
    """执行Skill"""
    skill = skills_registry.get(request.skill_name)
    
    if not skill:
        return SkillExecuteResponse(
            success=False,
            error=f"Skill不存在: {request.skill_name}",
        )
    
    try:
        result = await skill.execute(request.context)
        return SkillExecuteResponse(
            success=result.get("success", True),
            result=result,
        )
    except Exception as e:
        return SkillExecuteResponse(
            success=False,
            error=str(e),
        )


@app.get("/api/artifacts")
async def list_artifacts():
    """列出产出物"""
    artifacts = task_manager.list_artifacts()
    
    return {
        "artifacts": [
            ArtifactResponse(
                id=a.id,
                name=a.name,
                type=a.type,
                path=a.path,
                size=a.size,
                created_at=a.created_at.isoformat(),
            )
            for a in artifacts
        ],
        "total": len(artifacts),
    }


@app.get("/api/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    """获取产出物详情"""
    artifact = task_manager.get_artifact(artifact_id)
    
    if not artifact:
        raise HTTPException(status_code=404, detail=f"产出物不存在: {artifact_id}")
    
    return ArtifactResponse(
        id=artifact.id,
        name=artifact.name,
        type=artifact.type,
        path=artifact.path,
        size=artifact.size,
        created_at=artifact.created_at.isoformat(),
    )


@app.get("/api/stats")
async def get_stats():
    """获取系统统计"""
    return {
        "mode": {
            "current": mode_manager.get_current_mode().value,
        },
        "tasks": {
            "total": len(task_manager.list_tasks()),
        },
        "skills": skills_registry.get_stats(),
        "marketplace": skills_marketplace.get_stats(),
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }
