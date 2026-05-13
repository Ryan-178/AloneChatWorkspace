"use client"

import { useEffect, useState, useCallback } from "react"
import { Plus, Trash2, Bot, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { AgentChat } from "./agent-chat"
import { api } from "@/lib/api"

interface AgentSession {
  id: string
  title: string
  status: string
  updated_at: string
}

interface AgentPanelProps {
  currentUser: any
}

export function AgentPanel({ currentUser }: AgentPanelProps) {
  const [sessions, setSessions] = useState<AgentSession[]>([])
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [newTitle, setNewTitle] = useState("")
  const [dialogOpen, setDialogOpen] = useState(false)

  const loadSessions = useCallback(async () => {
    try {
      const data = await api.agent.getSessions()
      setSessions(data.items || [])
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  const handleCreate = async () => {
    if (!newTitle.trim()) return
    try {
      const session = await api.agent.createSession({ title: newTitle.trim() })
      setSessions((prev) => [session, ...prev])
      setSelectedSessionId(session.id)
      setNewTitle("")
      setDialogOpen(false)
    } catch {
      // ignore
    }
  }

  const handleDelete = async (sessionId: string) => {
    try {
      await api.agent.deleteSession(sessionId)
      setSessions((prev) => prev.filter((s) => s.id !== sessionId))
      if (selectedSessionId === sessionId) {
        setSelectedSessionId(null)
      }
    } catch {
      // ignore
    }
  }

  return (
    <div className="flex h-full">
      {/* Session List */}
      <div className="w-64 border-r flex flex-col">
        <div className="p-3 border-b flex items-center justify-between">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            <Bot className="h-4 w-4" />
            Agent Sessions
          </h3>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7 cursor-pointer">
                <Plus className="h-4 w-4" />
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>New Agent Session</DialogTitle>
              </DialogHeader>
              <div className="space-y-3">
                <Input
                  placeholder="Session title..."
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                />
                <Button onClick={handleCreate} className="w-full cursor-pointer">
                  Create
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {sessions.length === 0 && (
              <p className="text-xs text-muted-foreground text-center py-4">
                No sessions yet
              </p>
            )}
            {sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => setSelectedSessionId(session.id)}
                className={`flex items-center gap-2 px-2 py-2 rounded-md cursor-pointer group ${
                  selectedSessionId === session.id
                    ? "bg-accent"
                    : "hover:bg-muted"
                }`}
              >
                <Avatar className="h-7 w-7 shrink-0">
                  <AvatarFallback className="bg-green-100 text-green-700 text-xs">
                    <Bot className="h-3 w-3" />
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{session.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(session.updated_at).toLocaleDateString()}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100 cursor-pointer"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(session.id)
                  }}
                >
                  <Trash2 className="h-3 w-3 text-destructive" />
                </Button>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Chat Area */}
      <div className="flex-1">
        {selectedSessionId ? (
          <AgentChat sessionId={selectedSessionId} currentUser={currentUser} />
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <MessageSquare className="h-12 w-12 mb-4 opacity-50" />
            <p className="text-sm">Select or create a session to start chatting with the agent</p>
          </div>
        )}
      </div>
    </div>
  )
}
