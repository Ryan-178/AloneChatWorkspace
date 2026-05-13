"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import { Send, UserPlus, Bot } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"
import { wsClient } from "@/lib/websocket"

interface ChatAreaProps {
  id: string
  type: "conversation" | "group"
  currentUser: any
}

interface Message {
  id: string
  sender_id: string | null
  content: string
  created_at: string
  sender?: any
}

export function ChatArea({ id, type, currentUser }: ChatAreaProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [title, setTitle] = useState("")
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [participants, setParticipants] = useState<any[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const [showAddMember, setShowAddMember] = useState(false)
  const [memberEmail, setMemberEmail] = useState("")
  const [showAgentMention, setShowAgentMention] = useState(false)
  const [agentSessionId, setAgentSessionId] = useState<string | null>(null)

  const getOtherUserId = useCallback(() => {
    if (type === "conversation" && participants.length > 0) {
      const other = participants.find((p) => p.id !== currentUser.id)
      return other?.id || ""
    }
    return ""
  }, [type, participants, currentUser.id])

  useEffect(() => {
    setMessages([])
    setPage(1)
    setHasMore(true)
    loadInfo()
    loadMessages(1)

    if (type === "group") {
      wsClient.joinGroup(id)
    }

    const unsubscribe = wsClient.onMessage((data) => {
      if (data.type === "message") {
        const payload = data.payload
        const otherId = getOtherUserId()
        const isRelevant =
          (type === "conversation" &&
            ((payload.sender_id === currentUser.id && payload.recipient_id === otherId) ||
              (payload.sender_id === otherId && payload.recipient_id === currentUser.id))) ||
          (type === "group" && payload.group_id === id)

        if (isRelevant) {
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              sender_id: payload.sender_id,
              content: payload.content,
              created_at: new Date().toISOString(),
            },
          ])
        }
      } else if (data.type === "agent_response") {
        const payload = data.payload
        if (payload.sender_id === "__agent__") {
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              sender_id: "__agent__",
              content: payload.content,
              created_at: new Date().toISOString(),
            },
          ])
        }
      }
    })

    return () => {
      unsubscribe()
      if (type === "group") {
        wsClient.leaveGroup(id)
      }
    }
  }, [id, type, currentUser.id, getOtherUserId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const loadInfo = async () => {
    try {
      if (type === "conversation") {
        const data = await api.conversations.get(id)
        const other = data.participants?.find((p: any) => p.id !== currentUser.id)
        setTitle(other?.display_name || "会话")
        setParticipants(data.participants || [])
      } else {
        const data = await api.groups.get(id)
        setTitle(data.name)
      }
    } catch {
      // ignore
    }
  }

  const loadMessages = async (p: number) => {
    if (loading || !hasMore) return
    setLoading(true)
    try {
      const data =
        type === "conversation"
          ? await api.conversations.messages(id, p)
          : await api.groups.messages(id, p)

      const newMessages = data.items || []
      if (p === 1) {
        setMessages(newMessages.reverse())
      } else {
        setMessages((prev) => [...newMessages.reverse(), ...prev])
      }
      setHasMore(p < data.pages)
      setPage(p)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const handleSend = () => {
    if (!input.trim()) return

    const trimmed = input.trim()
    const otherId = getOtherUserId()

    if (trimmed.startsWith("@Agent ") && agentSessionId) {
      wsClient.send({
        type: "agent",
        payload: {
          content: trimmed.slice(7),
          session_id: agentSessionId,
        },
      })
    } else if (type === "conversation" && otherId) {
      wsClient.sendMessage(trimmed, otherId)
    } else {
      wsClient.sendMessage(trimmed, undefined, id)
    }

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        sender_id: currentUser.id,
        content: trimmed,
        created_at: new Date().toISOString(),
      },
    ])
    setInput("")
    setShowAgentMention(false)
  }

  const handleInputChange = (value: string) => {
    setInput(value)
    if (value === "@") {
      setShowAgentMention(true)
    } else if (!value.includes("@")) {
      setShowAgentMention(false)
    }
  }

  const handleAgentSelect = async () => {
    try {
      const session = await api.agent.createSession({ title: "Chat Agent Session" })
      setAgentSessionId(session.id)
      setInput("@Agent ")
      setShowAgentMention(false)
    } catch {
      setShowAgentMention(false)
    }
  }

  const handleAddMember = async () => {
    if (!memberEmail.trim()) return
    try {
      const users = await api.users.search(memberEmail)
      if (users.length > 0) {
        await api.groups.addMember(id, users[0].id)
        setMemberEmail("")
        setShowAddMember(false)
      }
    } catch {
      // ignore
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <h2 className="font-semibold">{title}</h2>
        {type === "group" && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowAddMember(!showAddMember)}
            className="cursor-pointer"
          >
            <UserPlus className="h-4 w-4" />
          </Button>
        )}
      </div>

      {showAddMember && type === "group" && (
        <div className="px-4 py-2 border-b flex gap-2">
          <Input
            placeholder="用户邮箱"
            value={memberEmail}
            onChange={(e) => setMemberEmail(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddMember()}
          />
          <Button onClick={handleAddMember} className="cursor-pointer">
            添加
          </Button>
        </div>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 px-4 py-2">
        {hasMore && page > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => loadMessages(page + 1)}
            className="w-full mb-4 cursor-pointer"
          >
            加载更多
          </Button>
        )}
        <div className="space-y-4">
          {messages.map((msg) => {
            const isMe = msg.sender_id === currentUser.id
            const isAgent = msg.sender_id === "__agent__"
            return (
              <div
                key={msg.id}
                className={`flex gap-2 ${isMe ? "flex-row-reverse" : "flex-row"}`}
              >
                <Avatar className="h-8 w-8 shrink-0">
                  <AvatarFallback className={`text-xs ${isAgent ? "bg-green-100 text-green-700" : "bg-secondary"}`}>
                    {isAgent ? <Bot className="h-4 w-4" /> : (msg.sender?.display_name?.[0]?.toUpperCase() || (isMe ? "我" : "U"))}
                  </AvatarFallback>
                </Avatar>
                <div
                  className={`max-w-[70%] rounded-lg px-3 py-2 text-sm ${
                    isMe
                      ? "bg-primary text-primary-foreground"
                      : isAgent
                      ? "bg-green-50 text-green-900 border border-green-200"
                      : "bg-muted"
                  }`}
                >
                  <p>{msg.content}</p>
                  <p className={`text-xs mt-1 ${isMe ? "text-primary-foreground/70" : isAgent ? "text-green-700/70" : "text-muted-foreground"}`}>
                    {new Date(msg.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
        <div ref={bottomRef} />
      </ScrollArea>

      {/* Input */}
      <div className="px-4 py-3 border-t flex gap-2 relative">
        <div className="flex-1 relative">
          <Input
            placeholder="输入消息... (输入 @ 唤起 Agent)"
            value={input}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            className="flex-1"
          />
          {showAgentMention && (
            <div className="absolute bottom-full left-0 mb-1 w-48 bg-popover border rounded-md shadow-md p-1 z-10">
              <button
                onClick={handleAgentSelect}
                className="flex items-center gap-2 w-full px-2 py-1.5 text-sm hover:bg-accent rounded-sm cursor-pointer"
              >
                <Bot className="h-4 w-4 text-green-600" />
                <span>Agent</span>
              </button>
            </div>
          )}
        </div>
        <Button onClick={handleSend} className="cursor-pointer">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
