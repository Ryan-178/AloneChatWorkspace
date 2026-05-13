"use client"

import { useEffect, useState, useCallback } from "react"
import { Check, Plus, Settings, Building2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"
import { WorkspaceSettings } from "./workspace-settings"

interface Workspace {
  id: string
  name: string
  description?: string
}

interface WorkspaceSwitcherProps {
  onWorkspaceChange?: () => void
}

export function WorkspaceSwitcher({ onWorkspaceChange }: WorkspaceSwitcherProps) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [currentWorkspaceId, setCurrentWorkspaceId] = useState<string | null>(null)
  const [newName, setNewName] = useState("")
  const [newDescription, setNewDescription] = useState("")
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)

  const loadWorkspaces = useCallback(async () => {
    try {
      const data = await api.workspace.list()
      setWorkspaces(data.items || [])
      const stored = localStorage.getItem("currentWorkspaceId")
      if (stored && data.items?.find((w: Workspace) => w.id === stored)) {
        setCurrentWorkspaceId(stored)
      } else if (data.items?.length > 0) {
        setCurrentWorkspaceId(data.items[0].id)
        localStorage.setItem("currentWorkspaceId", data.items[0].id)
      }
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    loadWorkspaces()
  }, [loadWorkspaces])

  const handleSelect = (id: string) => {
    setCurrentWorkspaceId(id)
    localStorage.setItem("currentWorkspaceId", id)
    onWorkspaceChange?.()
  }

  const handleCreate = async () => {
    if (!newName.trim()) return
    try {
      const ws = await api.workspace.create({
        name: newName.trim(),
        description: newDescription.trim() || undefined,
      })
      setWorkspaces((prev) => [ws, ...prev])
      setCurrentWorkspaceId(ws.id)
      localStorage.setItem("currentWorkspaceId", ws.id)
      setNewName("")
      setNewDescription("")
      setCreateDialogOpen(false)
      onWorkspaceChange?.()
    } catch {
      // ignore
    }
  }

  const currentWorkspace = workspaces.find((w) => w.id === currentWorkspaceId)

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="w-full justify-start gap-2 cursor-pointer">
            <Building2 className="h-4 w-4" />
            <span className="truncate">{currentWorkspace?.name || "选择工作区"}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-56" align="start">
          {workspaces.map((ws) => (
            <DropdownMenuItem
              key={ws.id}
              onClick={() => handleSelect(ws.id)}
              className="cursor-pointer"
            >
              <div className="flex items-center gap-2 flex-1">
                <Building2 className="h-4 w-4 text-muted-foreground" />
                <span className="truncate">{ws.name}</span>
              </div>
              {ws.id === currentWorkspaceId && <Check className="h-4 w-4 ml-auto" />}
            </DropdownMenuItem>
          ))}
          {workspaces.length === 0 && (
            <div className="px-2 py-1.5 text-sm text-muted-foreground">
              暂无工作区
            </div>
          )}
          <DropdownMenuSeparator />
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <DropdownMenuItem
                onSelect={(e) => e.preventDefault()}
                className="cursor-pointer"
              >
                <Plus className="h-4 w-4 mr-2" />
                创建工作区
              </DropdownMenuItem>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>创建工作区</DialogTitle>
              </DialogHeader>
              <div className="space-y-3">
                <Input
                  placeholder="工作区名称"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                />
                <Input
                  placeholder="描述（可选）"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                />
                <Button onClick={handleCreate} className="w-full cursor-pointer">
                  创建
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          {currentWorkspace && (
            <DropdownMenuItem
              onSelect={(e) => {
                e.preventDefault()
                setSettingsOpen(true)
              }}
              className="cursor-pointer"
            >
              <Settings className="h-4 w-4 mr-2" />
              工作区设置
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {currentWorkspace && (
        <WorkspaceSettings
          workspace={currentWorkspace}
          open={settingsOpen}
          onOpenChange={setSettingsOpen}
          onUpdate={loadWorkspaces}
        />
      )}
    </>
  )
}
