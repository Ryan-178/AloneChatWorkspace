'use client'

import { useTranslations } from 'next-intl'
import { Plus, Bot, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/common/empty-state'

export default function AgentPage() {
  const t = useTranslations('nav')
  
  return (
    <div className="flex h-full">
      <aside className="w-80 border-r flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Agent 会话</h2>
            <Button size="sm">
              <Plus className="mr-2 h-4 w-4" />
              新建
            </Button>
          </div>
        </div>
        <div className="flex-1 overflow-auto p-2">
          <EmptyState
            icon={<Bot className="h-8 w-8 text-muted-foreground" />}
            title="暂无会话"
            description="开始一个新的 Agent 会话"
            action={
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                新建会话
              </Button>
            }
          />
        </div>
      </aside>
      <main className="flex-1 flex flex-col">
        <div className="flex-1 flex items-center justify-center p-8">
          <Card className="w-full max-w-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5" />
                AI Agent
              </CardTitle>
              <CardDescription>
                选择一个模式开始与 AI Agent 对话
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Card className="cursor-pointer hover:border-primary transition-colors">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">MTC 模式</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      意图澄清模式，自动识别模糊需求并生成追问表单
                    </p>
                    <Badge variant="secondary" className="mt-2">
                      <Zap className="mr-1 h-3 w-3" />
                      推荐
                    </Badge>
                  </CardContent>
                </Card>
                <Card className="cursor-pointer hover:border-primary transition-colors">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">CODE 模式</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      代码模式，专注于代码生成和软件开发任务
                    </p>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
