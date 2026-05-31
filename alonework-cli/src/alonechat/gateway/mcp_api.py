"""
MCP API - REST API endpoints for MCP server management.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from alonechat.deepseek_optimization.mcp_marketplace import (
    MCPServerConfig,
    ServerStatus,
    MCPManager,
    get_mcp_manager,
)
from alonechat.deepseek_optimization.mcp_marketplace.config import (
    MCPServerDefinition,
)


router = APIRouter(prefix="/api/mcp", tags=["MCP"])


class ServerCreateRequest(BaseModel):
    """Request to create a new MCP server."""
    name: str = Field(..., description="Server name")
    command: str = Field(..., description="Command to start the server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    cwd: Optional[str] = Field(default=None, description="Working directory")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    description: str = Field(default="", description="Server description")
    version: str = Field(default="1.0.0", description="Server version")
    auto_start: bool = Field(default=False, description="Auto-start the server")


class ServerUpdateRequest(BaseModel):
    """Request to update an MCP server."""
    name: Optional[str] = Field(None, description="Server name")
    command: Optional[str] = Field(None, description="Command to start the server")
    args: Optional[List[str]] = Field(None, description="Command arguments")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    cwd: Optional[str] = Field(None, description="Working directory")
    timeout: Optional[int] = Field(None, description="Request timeout in seconds")
    description: Optional[str] = Field(None, description="Server description")
    version: Optional[str] = Field(None, description="Server version")


class ServerResponse(BaseModel):
    """Response for a single server."""
    id: str
    name: str
    description: str
    version: str
    status: str
    tool_count: int
    error_message: Optional[str] = None
    last_connected_at: Optional[str] = None
    created_at: str
    updated_at: str


class ServerListResponse(BaseModel):
    """Response for server list."""
    servers: List[ServerResponse]
    total: int


class ToolResponse(BaseModel):
    """Response for a single tool."""
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolListResponse(BaseModel):
    """Response for tool list."""
    tools: List[ToolResponse]
    total: int


class ToolCallRequest(BaseModel):
    """Request to call a tool."""
    server_id: str = Field(..., description="Server ID")
    tool_name: str = Field(..., description="Tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    timeout: Optional[float] = Field(None, description="Timeout override")


class ToolCallResponse(BaseModel):
    """Response for tool call."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float


class StatsResponse(BaseModel):
    """Response for MCP statistics."""
    servers: Dict[str, int]
    tools: Dict[str, Any]
    calls: Dict[str, int]


class CallHistoryResponse(BaseModel):
    """Response for call history."""
    calls: List[Dict[str, Any]]
    total: int


def get_manager() -> MCPManager:
    """Dependency to get MCP manager."""
    return get_mcp_manager()


@router.get("/servers", response_model=ServerListResponse)
async def list_servers(
    status: Optional[str] = Query(None, description="Filter by status"),
    manager: MCPManager = Depends(get_manager),
):
    """List all MCP servers."""
    servers = manager.get_all_servers()
    
    if status:
        try:
            target_status = ServerStatus(status.lower())
            servers = [s for s in servers if s.status == target_status]
        except ValueError:
            pass
    
    return ServerListResponse(
        servers=[
            ServerResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                version=s.version,
                status=s.status.value,
                tool_count=len(s.tools),
                error_message=s.error_message,
                last_connected_at=s.last_connected_at.isoformat() if s.last_connected_at else None,
                created_at=s.created_at.isoformat(),
                updated_at=s.updated_at.isoformat(),
            )
            for s in servers
        ],
        total=len(servers),
    )


@router.post("/servers", response_model=ServerResponse)
async def create_server(
    request: ServerCreateRequest,
    manager: MCPManager = Depends(get_manager),
):
    """Create and optionally start a new MCP server."""
    config = MCPServerConfig(
        command=request.command,
        args=request.args,
        env=request.env,
        cwd=request.cwd,
        timeout=request.timeout,
    )
    
    server = await manager.register_server(
        name=request.name,
        config=config,
        description=request.description,
        version=request.version,
        auto_start=request.auto_start,
    )
    
    return ServerResponse(
        id=server.id,
        name=server.name,
        description=server.description,
        version=server.version,
        status=server.status.value,
        tool_count=len(server.tools),
        error_message=server.error_message,
        last_connected_at=server.last_connected_at.isoformat() if server.last_connected_at else None,
        created_at=server.created_at.isoformat(),
        updated_at=server.updated_at.isoformat(),
    )


@router.get("/servers/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: str,
    manager: MCPManager = Depends(get_manager),
):
    """Get a specific MCP server."""
    server = manager.get_server(server_id)
    
    if not server:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")
    
    return ServerResponse(
        id=server.id,
        name=server.name,
        description=server.description,
        version=server.version,
        status=server.status.value,
        tool_count=len(server.tools),
        error_message=server.error_message,
        last_connected_at=server.last_connected_at.isoformat() if server.last_connected_at else None,
        created_at=server.created_at.isoformat(),
        updated_at=server.updated_at.isoformat(),
    )


@router.patch("/servers/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: str,
    request: ServerUpdateRequest,
    manager: MCPManager = Depends(get_manager),
):
    """Update an MCP server configuration."""
    server = manager.get_server(server_id)
    
    if not server:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")
    
    if request.name is not None:
        server.name = request.name
    if request.description is not None:
        server.description = request.description
    if request.version is not None:
        server.version = request.version
    if request.command is not None:
        server.config.command = request.command
    if request.args is not None:
        server.config.args = request.args
    if request.env is not None:
        server.config.env = request.env
    if request.cwd is not None:
        server.config.cwd = request.cwd
    if request.timeout is not None:
        server.config.timeout = request.timeout
    
    return ServerResponse(
        id=server.id,
        name=server.name,
        description=server.description,
        version=server.version,
        status=server.status.value,
        tool_count=len(server.tools),
        error_message=server.error_message,
        last_connected_at=server.last_connected_at.isoformat() if server.last_connected_at else None,
        created_at=server.created_at.isoformat(),
        updated_at=server.updated_at.isoformat(),
    )


@router.delete("/servers/{server_id}")
async def delete_server(
    server_id: str,
    manager: MCPManager = Depends(get_manager),
):
    """Delete an MCP server."""
    success = await manager.unregister_server(server_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")
    
    return {"success": True, "message": f"Server deleted: {server_id}"}


@router.post("/servers/{server_id}/start")
async def start_server(
    server_id: str,
    manager: MCPManager = Depends(get_manager),
):
    """Start an MCP server."""
    success = await manager.start_server(server_id)
    
    if not success:
        server = manager.get_server(server_id)
        error_msg = server.error_message if server else "Unknown error"
        raise HTTPException(
            status_code=400,
            detail=f"Failed to start server: {error_msg}",
        )
    
    return {"success": True, "message": f"Server started: {server_id}"}


@router.post("/servers/{server_id}/stop")
async def stop_server(
    server_id: str,
    manager: MCPManager = Depends(get_manager),
):
    """Stop an MCP server."""
    success = await manager.stop_server(server_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to stop server: {server_id}",
        )
    
    return {"success": True, "message": f"Server stopped: {server_id}"}


@router.post("/servers/{server_id}/restart")
async def restart_server(
    server_id: str,
    manager: MCPManager = Depends(get_manager),
):
    """Restart an MCP server."""
    success = await manager.restart_server(server_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to restart server: {server_id}",
        )
    
    return {"success": True, "message": f"Server restarted: {server_id}"}


@router.get("/servers/{server_id}/tools", response_model=ToolListResponse)
async def get_server_tools(
    server_id: str,
    manager: MCPManager = Depends(get_manager),
):
    """Get tools provided by a server."""
    server = manager.get_server(server_id)
    
    if not server:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")
    
    tools = [
        ToolResponse(
            name=t.name,
            description=t.description,
            parameters={k: v.model_dump() for k, v in t.parameters.items()},
        )
        for t in server.tools
    ]
    
    return ToolListResponse(tools=tools, total=len(tools))


@router.get("/tools", response_model=Dict[str, ToolListResponse])
async def get_all_tools(
    manager: MCPManager = Depends(get_manager),
):
    """Get all available tools grouped by server."""
    result = {}
    
    for server_id, tools in manager.get_all_tools().items():
        server = manager.get_server(server_id)
        result[server.name if server else server_id[:8]] = ToolListResponse(
            tools=[
                ToolResponse(
                    name=t.name,
                    description=t.description,
                    parameters={k: v.model_dump() for k, v in t.parameters.items()},
                )
                for t in tools
            ],
            total=len(tools),
        )
    
    return result


@router.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(
    request: ToolCallRequest,
    manager: MCPManager = Depends(get_manager),
):
    """Call a tool on an MCP server."""
    result = await manager.call_tool(
        server_id=request.server_id,
        tool_name=request.tool_name,
        arguments=request.arguments,
        timeout=request.timeout,
    )
    
    return ToolCallResponse(
        success=result.get("success", False),
        result=result.get("result"),
        error=result.get("error"),
        execution_time_ms=result.get("execution_time_ms", 0),
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    manager: MCPManager = Depends(get_manager),
):
    """Get MCP statistics."""
    stats = manager.get_stats()
    return StatsResponse(**stats)


@router.get("/history", response_model=CallHistoryResponse)
async def get_call_history(
    server_id: Optional[str] = Query(None, description="Filter by server ID"),
    tool_name: Optional[str] = Query(None, description="Filter by tool name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    manager: MCPManager = Depends(get_manager),
):
    """Get tool call history."""
    history = manager.get_call_history(
        server_id=server_id,
        tool_name=tool_name,
        limit=limit,
    )
    
    return CallHistoryResponse(calls=history, total=len(history))


@router.get("/servers/{server_id}/resources")
async def get_server_resources(
    server_id: str,
    manager: MCPManager = Depends(get_manager),
):
    """Get resources provided by a server."""
    server = manager.get_server(server_id)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")

    return {
        "resources": [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description,
                "mime_type": r.mime_type,
            }
            for r in server.resources
        ],
        "templates": [
            {
                "uri_template": t.uri_template,
                "name": t.name,
                "description": t.description,
                "mime_type": t.mime_type,
            }
            for t in server.resource_templates
        ],
    }


@router.get("/servers/{server_id}/instructions")
async def get_server_instructions(
    server_id: str,
    manager: MCPManager = Depends(get_manager),
):
    """Get server instructions."""
    instructions = manager.get_server_instructions(server_id)

    if not manager.get_server(server_id):
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")

    return {
        "server_id": server_id,
        "instructions": instructions,
    }


@router.get("/resources/search")
async def search_resources(
    query: str = Query(..., description="Search query"),
    manager: MCPManager = Depends(get_manager),
):
    """Search resources across all servers (@-mention support)."""
    results = manager.search_resources(query)

    return {
        "results": [
            {
                "server_name": server_name,
                "resource": {
                    "uri": r.uri,
                    "name": r.name,
                    "description": r.description,
                    "mime_type": r.mime_type,
                },
            }
            for server_name, r in results
        ],
        "total": len(results),
    }


@router.post("/servers/{server_id}/check-lazy-load")
async def check_lazy_load(
    server_id: str,
    context_window: int = Query(100000, description="Estimated context window size"),
    manager: MCPManager = Depends(get_manager),
):
    """Check if tool descriptions exceed lazy-load threshold."""
    if not manager.get_server(server_id):
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")

    deferred = await manager.check_and_lazy_load_tools(server_id, context_window)

    return {
        "server_id": server_id,
        "lazy_load_deferred": deferred,
    }


@router.get("/project")
async def get_project_scope():
    """Get project-scoped MCP configuration."""
    from alonechat.deepseek_optimization.mcp_marketplace.config import (
        discover_project_mcp_json,
        load_project_mcp_json,
    )

    path = discover_project_mcp_json()

    if not path:
        return {"found": False, "path": None, "servers": []}

    servers = load_project_mcp_json(path)
    return {
        "found": True,
        "path": path,
        "servers": [
            {
                "name": s.name,
                "command": s.command,
                "args": s.args,
                "transport": s.transport,
                "url": s.url,
                "client_id": s.client_id,
            }
            for s in servers
        ],
    }


def create_mcp_api(app, manager: Optional[MCPManager] = None):
    """
    Create and attach MCP API to a FastAPI app.

    Args:
        app: FastAPI application
        manager: Optional MCP manager instance
    """
    if manager:
        from alonechat.deepseek_optimization.mcp_marketplace.manager import init_mcp_manager
        init_mcp_manager(
            tool_registry=getattr(manager, 'tool_registry', None),
            auto_register_tools=getattr(manager, 'auto_register_tools', True),
            default_timeout=getattr(manager, 'default_timeout', 30.0),
        )

    app.include_router(router)
