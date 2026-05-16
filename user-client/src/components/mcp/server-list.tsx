'use client'

import { MCPServer } from '@/stores/mcp-store'
import { ServerCard } from './server-card'
import { ScrollArea } from '@/components/ui/scroll-area'

interface ServerListProps {
  servers: MCPServer[]
  onStart: (id: string) => void
  onStop: (id: string) => void
  onRestart: (id: string) => void
  onDelete: (id: string) => void
  onSelect: (server: MCPServer) => void
  isLoading: boolean
}

export function ServerList({
  servers,
  onStart,
  onStop,
  onRestart,
  onDelete,
  onSelect,
  isLoading,
}: ServerListProps) {
  if (servers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <p>暂无MCP服务器</p>
        <p className="text-sm">点击"添加服务器"创建新的MCP服务器</p>
      </div>
    )
  }

  return (
    <ScrollArea className="h-[calc(100vh-16rem)]">
      <div className="grid gap-4 p-1">
        {servers.map((server) => (
          <ServerCard
            key={server.id}
            server={server}
            onStart={onStart}
            onStop={onStop}
            onRestart={onRestart}
            onDelete={onDelete}
            onSelect={onSelect}
            isLoading={isLoading}
          />
        ))}
      </div>
    </ScrollArea>
  )
}
