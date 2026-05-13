"use client"

import { useState } from "react"
import { Plus, X } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"

interface GroupListProps {
  groups: any[]
  selectedId: string | null
  onSelect: (id: string) => void
  onRefresh: () => void
}

export function GroupList({ groups, selectedId, onSelect, onRefresh }: GroupListProps) {
  const [showCreate, setShowCreate] = useState(false)
  const [groupName, setGroupName] = useState("")
  const [creating, setCreating] = useState(false)

  const handleCreateGroup = async () => {
    if (!groupName.trim()) return
    setCreating(true)
    try {
      await api.groups.create({ name: groupName.trim() })
      setShowCreate(false)
      setGroupName("")
      onRefresh()
    } catch {
      // ignore
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-3">
        <Button
          variant="outline"
          className="w-full justify-start gap-2 cursor-pointer"
          onClick={() => setShowCreate(true)}
        >
          <Plus className="h-4 w-4" />
          新建群组
        </Button>
      </div>

      {showCreate && (
        <div className="px-3 pb-3 space-y-2">
          <div className="flex gap-2">
            <Input
              placeholder="群组名称"
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateGroup()}
            />
            <Button
              size="icon"
              variant="ghost"
              onClick={() => setShowCreate(false)}
              className="cursor-pointer"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <Button
            className="w-full cursor-pointer"
            disabled={creating || !groupName.trim()}
            onClick={handleCreateGroup}
          >
            {creating ? "创建中..." : "创建"}
          </Button>
        </div>
      )}

      <ScrollArea className="flex-1">
        <div className="divide-y">
          {groups.map((group) => (
            <button
              key={group.id}
              onClick={() => onSelect(group.id)}
              className={`w-full flex items-center gap-3 p-3 text-left transition-colors cursor-pointer ${
                selectedId === group.id ? "bg-muted" : "hover:bg-muted/50"
              }`}
            >
              <Avatar className="h-10 w-10 shrink-0">
                <AvatarFallback className="bg-secondary">
                  {group.name?.[0]?.toUpperCase() || "G"}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{group.name}</p>
                <p className="text-xs text-muted-foreground">
                  {group.members?.length || 0} 成员
                </p>
              </div>
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
