"use client"

import { useState } from "react"
import { Plus, Search, X } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"

interface ConversationListProps {
  conversations: any[]
  selectedId: string | null
  onSelect: (id: string) => void
  onRefresh: () => void
}

export function ConversationList({ conversations, selectedId, onSelect, onRefresh }: ConversationListProps) {
  const [showCreate, setShowCreate] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [creating, setCreating] = useState(false)

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    try {
      const data = await api.users.search(searchQuery)
      setSearchResults(data)
    } catch {
      setSearchResults([])
    }
  }

  const handleCreateConversation = async (userId: string) => {
    setCreating(true)
    try {
      await api.conversations.create({
        type: "direct",
        participant_ids: [userId],
      })
      setShowCreate(false)
      setSearchQuery("")
      setSearchResults([])
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
          新建会话
        </Button>
      </div>

      {showCreate && (
        <div className="px-3 pb-3 space-y-2">
          <div className="flex gap-2">
            <Input
              placeholder="搜索用户..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <Button size="icon" variant="ghost" onClick={handleSearch} className="cursor-pointer">
              <Search className="h-4 w-4" />
            </Button>
            <Button size="icon" variant="ghost" onClick={() => setShowCreate(false)} className="cursor-pointer">
              <X className="h-4 w-4" />
            </Button>
          </div>
          {searchResults.length > 0 && (
            <div className="border rounded-md divide-y">
              {searchResults.map((user) => (
                <button
                  key={user.id}
                  onClick={() => handleCreateConversation(user.id)}
                  disabled={creating}
                  className="w-full flex items-center gap-2 p-2 hover:bg-muted transition-colors text-left cursor-pointer"
                >
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="text-xs bg-secondary">
                      {user.display_name?.[0]?.toUpperCase() || "U"}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{user.display_name}</p>
                    <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <ScrollArea className="flex-1">
        <div className="divide-y">
          {conversations.map((conv) => {
            const otherParticipant = conv.participants?.find((p: any) => p.id !== conv.current_user_id)
            const displayName = conv.name || otherParticipant?.display_name || "未知用户"
            const lastMessage = conv.last_message

            return (
              <button
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={`w-full flex items-center gap-3 p-3 text-left transition-colors cursor-pointer ${
                  selectedId === conv.id ? "bg-muted" : "hover:bg-muted/50"
                }`}
              >
                <Avatar className="h-10 w-10 shrink-0">
                  <AvatarFallback className="bg-secondary">
                    {displayName?.[0]?.toUpperCase() || "U"}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{displayName}</p>
                  {lastMessage && (
                    <p className="text-xs text-muted-foreground truncate">
                      {lastMessage.sender?.display_name}: {lastMessage.content}
                    </p>
                  )}
                </div>
              </button>
            )
          })}
        </div>
      </ScrollArea>
    </div>
  )
}
