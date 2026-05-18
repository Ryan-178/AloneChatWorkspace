"""
REST API - 模式管理、任务管理、Skills管理 - REST API for Mode, Task, and Skills Management
集成用户端API：认证、会话管理 - Integrates User API: Authentication, Session Management
集成MCP API：MCP服务器管理 - Integrates MCP API: MCP Server Management
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent_framework.core.types import AgentMode, TaskStatus
from agent_framework.core.task import Task, Artifact
from agent_framework.agent.mtc_agent import MTCAgent
from agent_framework.agent.code_agent import CodeAgent
from agent_framework.tools.skills_registry import SkillsRegistry, register_builtin_skills
from agent_framework.tools.skills_marketplace import SkillsMarketplace
from agent_framework.gateway.session import SessionManager
from agent_framework.gateway.user_api import create_user_api
from agent_framework.gateway.mcp_api import create_mcp_api


app = FastAPI(title="MTC/CODE Mode API", version="1.0.0")

session_manager = SessionManager()
create_user_api(app, session_manager)
create_mcp_api(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ModeSwitchRequest(BaseModel):
    """模式切换请求 - Mode Switch Request"""
    target_mode: str = Field(..., description="目标模式: MTC 或 CODE / Target mode: MTC or CODE")
    session_id: Optional[str] = Field(None, description="会话ID / Session ID")


class ModeSwitchResponse(BaseModel):
    """模式切换响应 - Mode Switch Response"""
    success: bool
    current_mode: str
    previous_mode: Optional[str] = None
    message: str


class TaskCreateRequest(BaseModel):
    """任务创建请求 - Task Create Request"""
    description: str = Field(..., description="任务描述 / Task description")
    mode: Optional[str] = Field(None, description="执行模式 / Execution mode")
    priority: Optional[str] = Field("medium", description="优先级 / Priority")


class TaskResponse(BaseModel):
    """任务响应 - Task Response"""
    id: str
    description: str
    status: str
    priority: str
    created_at: str


class SkillExecuteRequest(BaseModel):
    """Skill执行请求 - Skill Execute Request"""
    skill_name: str = Field(..., description="Skill名称 / Skill name")
    context: Dict[str, Any] = Field(default_factory=dict, description="执行上下文 / Execution context")


class SkillExecuteResponse(BaseModel):
    """Skill执行响应 - Skill Execute Response"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RemoteSkillInstallRequest(BaseModel):
    """远程Skill安装请求 - Remote Skill Install Request"""
    url: str = Field(..., description="GitHub URL 或 skills.sh URL / GitHub URL or skills.sh URL")
    skill_name: Optional[str] = Field(None, description="指定的 skill 名称 / Specified skill name")
    branch: Optional[str] = Field(None, description="指定的分支 / Specified branch")
    global_install: bool = Field(default=False, description="是否全局安装 / Whether to install globally")
    force: bool = Field(default=False, description="强制覆盖 / Force overwrite")


class ArtifactResponse(BaseModel):
    """产出物响应 - Artifact Response"""
    id: str
    name: str
    type: str
    path: str
    size: int
    created_at: str


class ModeManager:
    """
    模式管理器 - Mode Manager
    管理Agent的运行模式（MTC/CODE）
    Manages the running mode of Agents (MTC/CODE)
    """
    
    def __init__(self):
        self._current_mode = AgentMode.MTC
        self._agents: Dict[str, Any] = {}
        self._sessions: Dict[str, AgentMode] = {}
    
    def get_current_mode(self, session_id: Optional[str] = None) -> AgentMode:
        """获取当前模式 - Get current mode"""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self._current_mode
    
    def switch_mode(self, target_mode: str, session_id: Optional[str] = None) -> ModeSwitchResponse:
        """切换模式 - Switch mode"""
        try:
            new_mode = AgentMode(target_mode.upper())
        except ValueError:
            return ModeSwitchResponse(
                success=False,
                current_mode=self._current_mode.value,
                message=f"无效的模式: {target_mode} / Invalid mode: {target_mode}",
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
            message=f"模式已切换: {previous_mode.value} -> {new_mode.value} / Mode switched: {previous_mode.value} -> {new_mode.value}",
        )
    
    def get_agent(self, mode: AgentMode, llm=None) -> Any:
        """获取指定模式的Agent实例 - Get Agent instance for specified mode"""
        if mode == AgentMode.MTC:
            return MTCAgent(llm=llm)
        else:
            return CodeAgent(llm=llm)


class TaskManager:
    """
    任务管理器 - Task Manager
    管理任务的生命周期和产出物
    Manages task lifecycle and artifacts
    """
    
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._artifacts: Dict[str, Artifact] = {}
    
    def create_task(self, description: str, priority: str = "medium") -> Task:
        """创建任务 - Create task"""
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
        """获取任务 - Get task"""
        return self._tasks.get(task_id)
    
    def list_tasks(self, status: Optional[str] = None) -> List[Task]:
        """列出任务 - List tasks"""
        tasks = list(self._tasks.values())
        
        if status:
            try:
                target_status = TaskStatus(status.lower())
                tasks = [t for t in tasks if t.status == target_status]
            except ValueError:
                pass
        
        return tasks
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务 - Cancel task"""
        task = self._tasks.get(task_id)
        if task:
            task.status = TaskStatus.CANCELLED
            return True
        return False
    
    def add_artifact(self, artifact: Artifact) -> None:
        """添加产出物 - Add artifact"""
        self._artifacts[artifact.id] = artifact
    
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """获取产出物 - Get artifact"""
        return self._artifacts.get(artifact_id)
    
    def list_artifacts(self) -> List[Artifact]:
        """列出产出物 - List artifacts"""
        return list(self._artifacts.values())


mode_manager = ModeManager()
task_manager = TaskManager()
skills_registry = SkillsRegistry()
skills_marketplace = SkillsMarketplace(skills_registry)

register_builtin_skills(skills_registry)


@app.get("/api/mode")
async def get_mode(session_id: Optional[str] = Query(None)):
    """获取当前模式 - Get current mode"""
    current_mode = mode_manager.get_current_mode(session_id)
    return {
        "mode": current_mode.value,
        "session_id": session_id,
        "available_modes": [m.value for m in AgentMode],
    }


@app.post("/api/mode/switch", response_model=ModeSwitchResponse)
async def switch_mode(request: ModeSwitchRequest):
    """切换模式 - Switch mode"""
    return mode_manager.switch_mode(request.target_mode, request.session_id)


@app.get("/api/tasks")
async def list_tasks(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """获取任务列表 - Get task list"""
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
    """创建新任务 - Create new task"""
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
    """获取任务详情 - Get task details"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id} / Task not found: {task_id}")
    
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
    """取消任务 - Cancel task"""
    success = task_manager.cancel_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id} / Task not found: {task_id}")
    
    return {"success": True, "message": f"任务已取消: {task_id} / Task cancelled: {task_id}"}


@app.get("/api/skills")
async def list_skills(
    category: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
):
    """列出所有Skills - List all Skills"""
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
    """获取Skill详情 - Get Skill details"""
    details = skills_marketplace.get_details(skill_name)
    
    if not details:
        raise HTTPException(status_code=404, detail=f"Skill不存在: {skill_name} / Skill not found: {skill_name}")
    
    return details


@app.post("/api/skills/execute", response_model=SkillExecuteResponse)
async def execute_skill(request: SkillExecuteRequest):
    """执行Skill - Execute Skill"""
    skill = skills_registry.get(request.skill_name)
    
    if not skill:
        return SkillExecuteResponse(
            success=False,
            error=f"Skill不存在: {request.skill_name} / Skill not found: {request.skill_name}",
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
    """列出产出物 - List artifacts"""
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
    """获取产出物详情 - Get artifact details"""
    artifact = task_manager.get_artifact(artifact_id)
    
    if not artifact:
        raise HTTPException(status_code=404, detail=f"产出物不存在: {artifact_id} / Artifact not found: {artifact_id}")
    
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
    """获取系统统计 - Get system statistics"""
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
    """健康检查 - Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@app.get("/api/skills/remote/search")
async def search_remote_skills(query: str = Query(..., description="搜索关键词 / Search keyword")):
    """搜索远程 Skills (skills.sh) - Search remote Skills (skills.sh)"""
    skills = await skills_marketplace.search_remote(query)
    return {
        "skills": [skill.model_dump() for skill in skills],
        "total": len(skills),
        "query": query,
    }


@app.get("/api/skills/remote/trending")
async def get_trending_skills():
    """获取热门远程 Skills - Get trending remote Skills"""
    skills = await skills_marketplace.search_remote("")
    return {
        "skills": [skill.model_dump() for skill in skills[:10]],
        "period": "all",
    }


@app.get("/api/skills/remote/installed")
async def list_installed_remote_skills():
    """列出已安装的远程 Skills - List installed remote Skills"""
    skills = skills_marketplace.list_installed_remote()
    return {
        "skills": skills,
        "total": len(skills),
    }


@app.post("/api/skills/remote/install")
async def install_remote_skill(request: RemoteSkillInstallRequest):
    """从远程 URL 安装 Skill - Install Skill from remote URL"""
    result = await skills_marketplace.install_from_remote(
        url=request.url,
        skill_name=request.skill_name,
        branch=request.branch,
        global_install=request.global_install,
        force=request.force,
    )
    return result


@app.delete("/api/skills/remote/{skill_name}")
async def uninstall_remote_skill(skill_name: str):
    """卸载远程安装的 Skill - Uninstall remote Skill"""
    result = skills_marketplace.uninstall_remote(skill_name)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result
