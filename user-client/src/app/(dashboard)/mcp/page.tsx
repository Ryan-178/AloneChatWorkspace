'use client'

import { useEffect, useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { useMCPStore } from '@/stores/mcp-store'
import { ServerList } from '@/components/mcp/server-list'
import { ToolList } from '@/components/mcp/tool-list'
import { ServerForm } from '@/components/mcp/server-form'
import { Loader2, Server, Wrench, BarChart3 } from 'lucide-react'

export default function MCPPage() {
  const {
    servers,
    currentServer,
    tools,
    stats,
    isLoading,
    error,
    fetchServers,
    createServer,
    deleteServer,
    startServer,
    stopServer,
    restartServer,
    fetchTools,
    callTool,
    fetchStats,
    setCurrentServer,
    clearError,
  } = useMCPStore()

  const [activeTab, setActiveTab] = useState('servers')

  useEffect(() => {
    fetchServers()
    fetchStats()
  }, [fetchServers, fetchStats])

  useEffect(() => {
    if (currentServer && currentServer.status === 'active') {
      fetchTools(currentServer.id)
    }
  }, [currentServer, fetchTools])

  const handleCreateServer = async (data: Parameters<typeof createServer>[0]) => {
    await createServer(data)
    fetchStats()
  }

  const handleDeleteServer = async (id: string) => {
    if (confirm('确定要删除此服务器吗？')) {
      await deleteServer(id)
      fetchStats()
    }
  }

  const handleStartServer = async (id: string) => {
    await startServer(id)
    fetchStats()
  }

  const handleStopServer = async (id: string) => {
    await stopServer(id)
    fetchStats()
  }

  const handleRestartServer = async (id: string) => {
    await restartServer(id)
    fetchStats()
  }

  const handleSelectServer = (server: typeof currentServer) => {
    setCurrentServer(server)
    if (server && server.status === 'active') {
      fetchTools(server.id)
    }
    setActiveTab('tools')
  }

  const handleCallTool = async (serverId: string, toolName: string, args: Record<string, unknown>) => {
    const result = await callTool(serverId, toolName, args)
    if (result) {
      if (result.success) {
        alert(`执行成功！\n\n结果: ${JSON.stringify(result.result, null, 2)}`)
      } else {
        alert(`执行失败: ${result.error}`)
      }
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-6 border-b">
        <div>
          <h1 className="text-2xl font-bold">MCP 服务器管理</h1>
          <p className="text-muted-foreground">
            管理和监控 Model Context Protocol 服务器
          </p>
        </div>
        <ServerForm onSubmit={handleCreateServer} isLoading={isLoading} />
      </div>

      {error && (
        <div className="mx-6 mt-4 p-4 bg-destructive/10 text-destructive rounded-lg flex items-center justify-between">
          <span>{error}</span>
          <button onClick={clearError} className="text-sm underline">
            关闭
          </button>
        </div>
      )}

      <div className="flex-1 p-6">
        <div className="grid gap-6 lg:grid-cols-4">
          <div className="lg:col-span-3">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="mb-4">
                <TabsTrigger value="servers" className="flex items-center gap-2">
                  <Server className="h-4 w-4" />
                  服务器
                </TabsTrigger>
                <TabsTrigger value="tools" className="flex items-center gap-2">
                  <Wrench className="h-4 w-4" />
                  工具
                </TabsTrigger>
              </TabsList>

              <TabsContent value="servers">
                {isLoading && servers.length === 0 ? (
                  <div className="flex items-center justify-center h-64">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : (
                  <ServerList
                    servers={servers}
                    onStart={handleStartServer}
                    onStop={handleStopServer}
                    onRestart={handleRestartServer}
                    onDelete={handleDeleteServer}
                    onSelect={handleSelectServer}
                    isLoading={isLoading}
                  />
                )}
              </TabsContent>

              <TabsContent value="tools">
                {currentServer ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-semibold">{currentServer.name}</h2>
                      <Badge variant={currentServer.status === 'active' ? 'default' : 'secondary'}>
                        {currentServer.status}
                      </Badge>
                    </div>
                    <ToolList
                      tools={tools}
                      serverId={currentServer.id}
                      onCallTool={handleCallTool}
                      isLoading={isLoading}
                    />
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                    <p>请先选择一个服务器</p>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  统计信息
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {stats ? (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">总服务器</span>
                      <span className="font-medium">{stats.servers.total}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">运行中</span>
                      <span className="font-medium text-green-600">{stats.servers.active}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">已停止</span>
                      <span className="font-medium">{stats.servers.inactive}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">错误</span>
                      <span className="font-medium text-destructive">{stats.servers.error}</span>
                    </div>
                    <Separator />
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">总工具数</span>
                      <span className="font-medium">{stats.tools.total_adapters}</span>
                    </div>
                    <Separator />
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">总调用次数</span>
                      <span className="font-medium">{stats.calls.total}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">成功</span>
                      <span className="font-medium text-green-600">{stats.calls.successful}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">失败</span>
                      <span className="font-medium text-destructive">{stats.calls.failed}</span>
                    </div>
                  </>
                ) : (
                  <div className="flex items-center justify-center py-4">
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  </div>
                )}
              </CardContent>
            </Card>

            {currentServer && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">当前服务器</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-sm">
                    <span className="text-muted-foreground">名称: </span>
                    <span className="font-medium">{currentServer.name}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-muted-foreground">版本: </span>
                    <span>{currentServer.version}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-muted-foreground">工具数: </span>
                    <span>{currentServer.tool_count}</span>
                  </div>
                  {currentServer.last_connected_at && (
                    <div className="text-sm">
                      <span className="text-muted-foreground">最后连接: </span>
                      <span>{new Date(currentServer.last_connected_at).toLocaleString()}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
