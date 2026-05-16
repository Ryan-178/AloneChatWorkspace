'use client'

import { Play } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Textarea } from '@/components/ui/textarea'
import { useState } from 'react'

interface MCPToolParameter {
  name: string
  type: string
  description: string
  required: boolean
  default?: unknown
}

interface MCPTool {
  name: string
  description: string
  parameters: Record<string, MCPToolParameter>
}

interface ToolListProps {
  tools: MCPTool[]
  serverId: string
  onCallTool: (serverId: string, toolName: string, args: Record<string, unknown>) => void
  isLoading: boolean
}

export function ToolList({ tools, serverId, onCallTool, isLoading }: ToolListProps) {
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null)
  const [argumentsJson, setArgumentsJson] = useState('{}')

  if (tools.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
        <p>暂无可用工具</p>
        <p className="text-sm">启动服务器后将自动加载工具</p>
      </div>
    )
  }

  const handleCall = () => {
    if (!selectedTool) return
    try {
      const args = JSON.parse(argumentsJson)
      onCallTool(serverId, selectedTool.name, args)
    } catch {
      alert('参数JSON格式错误')
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <ScrollArea className="h-[calc(100vh-20rem)]">
        <div className="space-y-2 p-1">
          {tools.map((tool) => (
            <Card
              key={tool.name}
              className={`cursor-pointer transition-colors ${
                selectedTool?.name === tool.name ? 'border-primary' : ''
              }`}
              onClick={() => {
                setSelectedTool(tool)
                setArgumentsJson('{}')
              }}
            >
              <CardHeader className="py-3 px-4">
                <CardTitle className="text-sm">{tool.name}</CardTitle>
                <CardDescription className="text-xs line-clamp-2">
                  {tool.description}
                </CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </ScrollArea>

      {selectedTool && (
        <Card>
          <CardHeader>
            <CardTitle>{selectedTool.name}</CardTitle>
            <CardDescription>{selectedTool.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.keys(selectedTool.parameters).length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">参数</h4>
                <div className="space-y-1">
                  {Object.entries(selectedTool.parameters).map(([name, param]) => (
                    <div key={name} className="flex items-center gap-2 text-sm">
                      <span className="font-mono">{name}</span>
                      <span className="text-muted-foreground">({param.type})</span>
                      {param.required && <span className="text-destructive">*</span>}
                      <span className="text-muted-foreground">- {param.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="space-y-2">
              <h4 className="text-sm font-medium">调用参数 (JSON)</h4>
              <Textarea
                value={argumentsJson}
                onChange={(e) => setArgumentsJson(e.target.value)}
                placeholder='{"key": "value"}'
                className="font-mono text-sm"
                rows={4}
              />
            </div>
            <Button onClick={handleCall} disabled={isLoading} className="w-full">
              <Play className="h-4 w-4 mr-2" />
              执行工具
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
