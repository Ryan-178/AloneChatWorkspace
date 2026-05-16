'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Plus } from 'lucide-react'

interface ServerFormProps {
  onSubmit: (data: {
    name: string
    command: string
    args: string[]
    env: Record<string, string>
    cwd?: string
    timeout: number
    description: string
    version: string
    auto_start: boolean
  }) => void
  isLoading: boolean
}

export function ServerForm({ onSubmit, isLoading }: ServerFormProps) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [command, setCommand] = useState('')
  const [args, setArgs] = useState('')
  const [env, setEnv] = useState('')
  const [cwd, setCwd] = useState('')
  const [timeout, setTimeout_] = useState('30')
  const [description, setDescription] = useState('')
  const [version, setVersion] = useState('1.0.0')
  const [autoStart, setAutoStart] = useState(false)

  const handleSubmit = () => {
    let parsedArgs: string[] = []
    let parsedEnv: Record<string, string> = {}

    try {
      if (args.trim()) {
        parsedArgs = JSON.parse(args)
      }
    } catch {
      parsedArgs = args.split(' ').filter(Boolean)
    }

    try {
      if (env.trim()) {
        parsedEnv = JSON.parse(env)
      }
    } catch {
      const lines = env.split('\n')
      for (const line of lines) {
        const [key, value] = line.split('=').map((s) => s.trim())
        if (key && value) {
          parsedEnv[key] = value
        }
      }
    }

    onSubmit({
      name,
      command,
      args: parsedArgs,
      env: parsedEnv,
      cwd: cwd || undefined,
      timeout: parseInt(timeout) || 30,
      description,
      version,
      auto_start: autoStart,
    })

    setOpen(false)
    resetForm()
  }

  const resetForm = () => {
    setName('')
    setCommand('')
    setArgs('')
    setEnv('')
    setCwd('')
    setTimeout_('30')
    setDescription('')
    setVersion('1.0.0')
    setAutoStart(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          添加服务器
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>添加MCP服务器</DialogTitle>
          <DialogDescription>
            配置新的MCP服务器。服务器将通过子进程启动并使用JSON-RPC协议通信。
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">名称 *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="filesystem"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="version">版本</Label>
              <Input
                id="version"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="1.0.0"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="command">启动命令 *</Label>
            <Input
              id="command"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="npx"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="args">命令参数</Label>
            <Textarea
              id="args"
              value={args}
              onChange={(e) => setArgs(e.target.value)}
              placeholder='["-y", "@modelcontextprotocol/server-filesystem", "./data"]'
              className="font-mono text-sm"
              rows={2}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="env">环境变量</Label>
            <Textarea
              id="env"
              value={env}
              onChange={(e) => setEnv(e.target.value)}
              placeholder='{"API_KEY": "xxx"} 或 KEY=value 格式'
              className="font-mono text-sm"
              rows={2}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="cwd">工作目录</Label>
              <Input
                id="cwd"
                value={cwd}
                onChange={(e) => setCwd(e.target.value)}
                placeholder="./data"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="timeout">超时时间 (秒)</Label>
              <Input
                id="timeout"
                type="number"
                value={timeout}
                onChange={(e) => setTimeout_(e.target.value)}
                placeholder="30"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">描述</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="服务器描述..."
              rows={2}
            />
          </div>
          <div className="flex items-center space-x-2">
            <Switch
              id="auto-start"
              checked={autoStart}
              onCheckedChange={setAutoStart}
            />
            <Label htmlFor="auto-start">创建后自动启动</Label>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading || !name || !command}>
            创建
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
