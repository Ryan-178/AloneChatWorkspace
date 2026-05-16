'use client'

import { Search, Puzzle } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/common/empty-state'
import { skillsApi } from '@/lib/api/skills'
import { useQuery } from '@tanstack/react-query'

export default function SkillsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: () => skillsApi.list(),
  })

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Skills 市场</h1>
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="搜索 Skills" className="pl-9" />
        </div>
      </div>

      {data?.categories && data.categories.length > 0 && (
        <div className="flex gap-2 mb-6 flex-wrap">
          <Badge variant="default">全部</Badge>
          {data.categories.map((category) => (
            <Badge key={category} variant="outline" className="cursor-pointer">
              {category}
            </Badge>
          ))}
        </div>
      )}

      {data?.skills && data.skills.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.skills.map((skill) => (
            <Card key={skill.name} className="cursor-pointer hover:border-primary transition-colors">
              <CardHeader>
                <CardTitle className="text-base">{skill.name}</CardTitle>
                <CardDescription>{skill.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <Badge variant="secondary">{skill.category}</Badge>
                  <Button size="sm" variant="outline">查看</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<Puzzle className="h-8 w-8 text-muted-foreground" />}
          title="暂无 Skills"
          description="Skills 将在这里显示"
        />
      )}
    </div>
  )
}
