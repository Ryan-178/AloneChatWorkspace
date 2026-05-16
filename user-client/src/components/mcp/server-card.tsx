'use client'

import { Play, Square, RotateCcw, Trash2, Wrench } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface MCPServer {
  id: string
  name: string
  description: string
  version: string
  status: 'inactive' | 'active' | 'error' | 'starting' | 'stopping'
  tool_count: number
  error_message?: string
  last_connected_at?: string
  created_at: string
  updated_at: string
}

interface ServerCardProps {
  server: MCPServer
  onStart: (id: string) => void
  onStop: (id: string) => void
  onRestart: (id: string) => void
  onDelete: (id: string) => void
  onSelect: (server: MCPServer) => void
  isLoading: boolean
}

const statusColors = {
  active: 'bg-green-500',
  inactive: 'bg-gray-500',
  error: 'bg-red-500',
  starting: 'bg-yellow-500',
  stopping: 'bg-orange-500',
}

const statusLabels = {
  active: '运行中',
  inactive: '已停止',
  error: '错误',
  starting: '启动中',
  stopping: '停止中',
}

export function ServerCard({
  server,
  onStart,
  onStop,
  onRestart,
  onDelete,
  onSelect,
  isLoading,
}: ServerCardProps) {
  return (
    <Card className="cursor-pointer hover:border-primary/50 transition-colors" onClick={() => onSelect(server)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{server.name}</CardTitle>
          <Badge variant="outline" className="flex items-center gap-1">
            <span className={cn('h-2 w-2 rounded-full', statusColors[server.status])} />
            {statusLabels[server.status]}
          </Badge>
        </div>
        <CardDescription className="line-clamp-2">
          {server.description || '无描述'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Wrench className="h-4 w-4" />
              {server.tool_count} 工具
            </span>
            <span>v{server.version}</span>
          </div>
          <div className="flex items-center gap-1">
            {server.status === 'inactive' && (
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => {
                  e.stopPropagation()
                  onStart(server.id)
                }}
                disabled={isLoading}
              >
                <Play className="h-4 w-4" />
              </Button>
            )}
            {server.status === 'active' && (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation()
                    onStop(server.id)
                  }}
                  disabled={isLoading}
                >
                  <Square className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation()
                    onRestart(server.id)
                  }}
                  disabled={isLoading}
                >
                  <RotateCcw className="h-4 w-4" />
                </Button>
              </>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => {
                e.stopPropagation()
                onDelete(server.id)
              }}
              disabled={isLoading || server.status === 'active'}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
        {server.error_message && (
          <p className="mt-2 text-sm text-destructive">{server.error_message}</p>
        )}
      </CardContent>
    </Card>
  )
}
