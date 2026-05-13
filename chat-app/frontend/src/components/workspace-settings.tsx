"use client"

import { useEffect, useState, useCallback } from "react"
import { Crown, Shield, User, Trash2, LogOut, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { api } from "@/lib/api"

interface Member {
  id: string
  user_id: string
  role: string
  user?: {
    display_name?: string
    email?: string
  }
}

interface Workspace {
  id: string
  name: string
  description?: string
}

interface WorkspaceSettingsProps {
  workspace: Workspace
  open: boolean
  onOpenChange: (open: boolean) => void
  onUpdate?: () => void
}

export function WorkspaceSettings({ workspace, open, onOpenChange, onUpdate }: WorkspaceSettingsProps) {
  const [name, setName] = useState(workspace.name)
  const [description, setDescription] = useState(workspace.description || "")
  const [members, setMembers] = useState<Member[]>([])
  const [inviteEmail, setInviteEmail] = useState("")
  const [inviteRole, setInviteRole] = useState("member")
  const [currentUserRole, setCurrentUserRole] = useState<string>("member")
  const [currentUserId, setCurrentUserId] = useState<string>("")

  const loadMembers = useCallback(async () => {
    try {
      const data = await api.workspace.getMembers(workspace.id)
      setMembers(data || [])
    } catch {
      // ignore
    }
  }, [workspace.id])

  const loadCurrentUser = useCallback(async () => {
    try {
      const me = await api.users.me()
      setCurrentUserId(me.id)
      const myMembership = members.find((m) => m.user_id === me.id)
      if (myMembership) {
        setCurrentUserRole(myMembership.role)
      }
    } catch {
      // ignore
    }
  }, [members])

  useEffect(() => {
    if (open) {
      loadMembers()
    }
  }, [open, loadMembers])

  useEffect(() => {
    loadCurrentUser()
  }, [loadCurrentUser])

  const handleUpdate = async () => {
    try {
      await api.workspace.update(workspace.id, {
        name: name || undefined,
        description: description || undefined,
      })
      onUpdate?.()
    } catch {
      // ignore
    }
  }

  const handleInvite = async () => {
    if (!inviteEmail.trim()) return
    try {
      await api.workspace.inviteMember(workspace.id, {
        email: inviteEmail.trim(),
        role: inviteRole,
      })
      setInviteEmail("")
      loadMembers()
    } catch {
      // ignore
    }
  }

  const handleRemove = async (userId: string) => {
    try {
      await api.workspace.removeMember(workspace.id, userId)
      loadMembers()
    } catch {
      // ignore
    }
  }

  const handleUpdateRole = async (userId: string, role: string) => {
    try {
      await api.workspace.updateMemberRole(workspace.id, userId, role)
      loadMembers()
    } catch {
      // ignore
    }
  }

  const handleLeave = async () => {
    try {
      await api.workspace.removeMember(workspace.id, currentUserId)
      onOpenChange(false)
      onUpdate?.()
    } catch {
      // ignore
    }
  }

  const getRoleIcon = (role: string) => {
    if (role === "owner") return <Crown className="h-3.5 w-3.5 text-yellow-500" />
    if (role === "admin") return <Shield className="h-3.5 w-3.5 text-blue-500" />
    return <User className="h-3.5 w-3.5 text-muted-foreground" />
  }

  const canManage = currentUserRole === "owner" || currentUserRole === "admin"
  const isOwner = currentUserRole === "owner"

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>工作区设置</DialogTitle>
        </DialogHeader>
        <Tabs defaultValue="info">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="info">基本信息</TabsTrigger>
            <TabsTrigger value="members">成员管理</TabsTrigger>
          </TabsList>

          <TabsContent value="info" className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">名称</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={!canManage}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">描述</label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={!canManage}
              />
            </div>
            {canManage && (
              <Button onClick={handleUpdate} className="cursor-pointer">
                保存
              </Button>
            )}
            {!isOwner && (
              <Button variant="destructive" onClick={handleLeave} className="cursor-pointer">
                <LogOut className="h-4 w-4 mr-2" />
                离开工作区
              </Button>
            )}
          </TabsContent>

          <TabsContent value="members" className="space-y-4">
            {canManage && (
              <div className="flex gap-2">
                <Input
                  placeholder="成员邮箱"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleInvite()}
                />
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="border rounded-md px-2 text-sm"
                >
                  <option value="member">成员</option>
                  <option value="admin">管理员</option>
                </select>
                <Button onClick={handleInvite} className="cursor-pointer">
                  邀请
                </Button>
              </div>
            )}

            <div className="space-y-2">
              {members.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center gap-3 p-2 rounded-md hover:bg-muted group"
                >
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="text-xs">
                      {member.user?.display_name?.[0]?.toUpperCase() || "U"}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {member.user?.display_name || "未知用户"}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">
                      {member.user?.email || ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {getRoleIcon(member.role)}
                    <span className="text-xs capitalize">{member.role}</span>
                    {canManage && member.role !== "owner" && member.user_id !== currentUserId && (
                      <>
                        <select
                          value={member.role}
                          onChange={(e) => handleUpdateRole(member.user_id, e.target.value)}
                          className="border rounded-md px-1 text-xs"
                        >
                          <option value="member">成员</option>
                          <option value="admin">管理员</option>
                        </select>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 opacity-0 group-hover:opacity-100 cursor-pointer"
                          onClick={() => handleRemove(member.user_id)}
                        >
                          <Trash2 className="h-3 w-3 text-destructive" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
