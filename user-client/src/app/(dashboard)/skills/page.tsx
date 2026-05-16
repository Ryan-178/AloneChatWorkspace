'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Search, Puzzle, Download, Star, Trash2, ExternalLink } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { EmptyState } from '@/components/common/empty-state'
import { skillsApi } from '@/lib/api/skills'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { RemoteSkill, InstalledRemoteSkill } from '@/types/skill'

export default function SkillsPage() {
  const t = useTranslations('nav')
  const [tab, setTab] = useState<'local' | 'remote' | 'installed'>('local')
  const [searchQuery, setSearchQuery] = useState('')
  const [installUrl, setInstallUrl] = useState('')
  const [skillName, setSkillName] = useState('')
  const queryClient = useQueryClient()

  const { data: localData, isLoading: localLoading } = useQuery({
    queryKey: ['skills', 'local', searchQuery],
    queryFn: () => skillsApi.list(undefined, searchQuery || undefined),
  })

  const { data: remoteData, isLoading: remoteLoading } = useQuery({
    queryKey: ['skills', 'remote', searchQuery],
    queryFn: () => skillsApi.searchRemote(searchQuery),
    enabled: tab === 'remote',
  })

  const { data: installedData, isLoading: installedLoading } = useQuery({
    queryKey: ['skills', 'installed'],
    queryFn: () => skillsApi.getInstalledRemote(),
    enabled: tab === 'installed',
  })

  const installMutation = useMutation({
    mutationFn: (request: { url: string; skill_name?: string }) =>
      skillsApi.installFromRemote(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills', 'installed'] })
      setInstallUrl('')
      setSkillName('')
    },
  })

  const uninstallMutation = useMutation({
    mutationFn: (skillName: string) => skillsApi.uninstallRemote(skillName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills', 'installed'] })
    },
  })

  const handleInstall = () => {
    if (!installUrl) return
    installMutation.mutate({
      url: installUrl,
      skill_name: skillName || undefined,
    })
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">{t('skills')}</h1>
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索 Skills"
            className="pl-9"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <Tabs value={tab} onValueChange={(v) => setTab(v as typeof tab)}>
        <TabsList className="mb-6">
          <TabsTrigger value="local">本地 Skills</TabsTrigger>
          <TabsTrigger value="remote">远程 Skills</TabsTrigger>
          <TabsTrigger value="installed">已安装</TabsTrigger>
        </TabsList>

        <TabsContent value="local">
          {localData?.categories && localData.categories.length > 0 && (
            <div className="flex gap-2 mb-6 flex-wrap">
              <Badge variant="default">全部</Badge>
              {localData.categories.map((category) => (
                <Badge key={category} variant="outline" className="cursor-pointer">
                  {category}
                </Badge>
              ))}
            </div>
          )}

          {localLoading ? (
            <div className="text-center py-8 text-muted-foreground">加载中...</div>
          ) : localData?.skills && localData.skills.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {localData.skills.map((skill) => (
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
              title="暂无本地 Skills"
              description="从远程安装 Skills 或添加本地 Skills"
            />
          )}
        </TabsContent>

        <TabsContent value="remote">
          <div className="mb-6 p-4 border rounded-lg bg-muted/50">
            <h3 className="text-sm font-medium mb-3">从 URL 安装</h3>
            <div className="flex gap-2">
              <Input
                placeholder="GitHub URL (例如: https://github.com/owner/repo)"
                value={installUrl}
                onChange={(e) => setInstallUrl(e.target.value)}
                className="flex-1"
              />
              <Input
                placeholder="Skill 名称 (可选)"
                value={skillName}
                onChange={(e) => setSkillName(e.target.value)}
                className="w-40"
              />
              <Button
                onClick={handleInstall}
                disabled={!installUrl || installMutation.isPending}
              >
                <Download className="h-4 w-4 mr-1" />
                安装
              </Button>
            </div>
            {installMutation.isError && (
              <p className="text-sm text-destructive mt-2">
                安装失败: {(installMutation.error as Error).message}
              </p>
            )}
            {installMutation.isSuccess && installMutation.data.success && (
              <p className="text-sm text-green-600 mt-2">
                ✓ 已安装: {installMutation.data.skill}
              </p>
            )}
          </div>

          {remoteLoading ? (
            <div className="text-center py-8 text-muted-foreground">搜索中...</div>
          ) : remoteData?.skills && remoteData.skills.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {remoteData.skills.map((skill: RemoteSkill) => (
                <Card key={skill.id} className="hover:border-primary transition-colors">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-base">{skill.name}</CardTitle>
                        <CardDescription className="line-clamp-2">
                          {skill.description}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                      <span className="flex items-center gap-1">
                        <Star className="h-3 w-3" />
                        {skill.stars}
                      </span>
                      <span className="flex items-center gap-1">
                        <Download className="h-3 w-3" />
                        {skill.installs}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <Badge variant="outline">{skill.owner}/{skill.repo}</Badge>
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => window.open(skill.github_url, '_blank')}
                        >
                          <ExternalLink className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => installMutation.mutate({ url: skill.github_url })}
                          disabled={installMutation.isPending}
                        >
                          <Download className="h-3 w-3 mr-1" />
                          安装
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<Search className="h-8 w-8 text-muted-foreground" />}
              title="搜索远程 Skills"
              description="输入关键词搜索 skills.sh 上的 Skills"
            />
          )}
        </TabsContent>

        <TabsContent value="installed">
          {installedLoading ? (
            <div className="text-center py-8 text-muted-foreground">加载中...</div>
          ) : installedData?.skills && installedData.skills.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {installedData.skills.map((skill: InstalledRemoteSkill) => (
                <Card key={skill.name}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-base">{skill.name}</CardTitle>
                        <CardDescription>{skill.source}</CardDescription>
                      </div>
                      <Badge variant={skill.scope === 'global' ? 'default' : 'secondary'}>
                        {skill.scope === 'global' ? '全局' : '本地'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-muted-foreground mb-3 truncate">
                      {skill.path}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">
                        {skill.files?.length || 0} 文件
                      </span>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => uninstallMutation.mutate(skill.name)}
                        disabled={uninstallMutation.isPending}
                      >
                        <Trash2 className="h-3 w-3 mr-1" />
                        移除
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<Puzzle className="h-8 w-8 text-muted-foreground" />}
              title="暂无已安装的远程 Skills"
              description="从远程 Skills 市场安装 Skills"
            />
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
