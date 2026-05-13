"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import { Send, Bot, User, Loader2, ChevronDown, ChevronUp } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"
import { wsClient } from "@/lib/websocket"

interface AgentMessage {
  id: string
  role: string
  content: string
  tool_calls?: string | null
  tool_results?: string | null
  created_at: string
}

interface AgentChatProps {
  sessionId: string
  currentUser: any
}

export function AgentChat({ sessionId, currentUser }: AgentChatProps) {
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [streamingContent, setStreamingContent] = useState("")
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set())
  const bottomRef = useRef<HTMLDivElement>(null)

  const loadMessages = useCallback(async () => {
    try {
      const data = await api.agent.getSession(sessionId)
      setMessages(data.messages || [])
    } catch {
      // ignore
    }
  }, [sessionId])

  useEffect(() => {
    setMessages([])
    loadMessages()

    const unsubscribe = wsClient.onMessage((data) => {
      if (data.type === "agent_response") {
        const payload = data.payload
        if (payload.session_id === sessionId) {
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              role: "agent",
              content: payload.content,
              created_at: new Date().toISOString(),
            },
          ])
          setLoading(false)
        }
      } else if (data.type === "agent_stream") {
        const payload = data.payload
        if (payload.session_id === sessionId) {
          if (payload.event === "thinking") {
            setLoading(true)
          } else if (payload.event === "final") {
            setStreamingContent((prev) => prev + payload.content)
            setLoading(false)
          } else if (payload.event === "tool_call") {
            setMessages((prev) => [
              ...prev,
              {
                id: `tool-${Date.now()}`,
                role: "tool_call",
                content: payload.content,
                created_at: new Date().toISOString(),
              },
            ])
          } else if (payload.event === "tool_result") {
            setMessages((prev) => [
              ...prev,
              {
                id: `result-${Date.now()}`,
                role: "tool_result",
                content: payload.content,
                created_at: new Date().toISOString(),
              },
            ])
          } else if (payload.event === "error") {
            setMessages((prev) => [
              ...prev,
              {
                id: `error-${Date.now()}`,
                role: "agent",
                content: `Error: ${payload.content}`,
                created_at: new Date().toISOString(),
              },
            ])
            setLoading(false)
          }
        }
      }
    })

    return () => {
      unsubscribe()
    }
  }, [sessionId, loadMessages])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamingContent])

  const handleSend = async () => {
    if (!input.trim()) return

    const content = input.trim()
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "user",
        content,
        created_at: new Date().toISOString(),
      },
    ])
    setInput("")
    setLoading(true)
    setStreamingContent("")

    try {
      await api.agent.runTask(sessionId, content)
    } catch {
      setLoading(false)
    }
  }

  const toggleToolExpand = (id: string) => {
    setExpandedTools((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const renderMessage = (msg: AgentMessage) => {
    const isUser = msg.role === "user"
    const isToolCall = msg.role === "tool_call"
    const isToolResult = msg.role === "tool_result"

    if (isToolCall || isToolResult) {
      const isExpanded = expandedTools.has(msg.id)
      return (
        <div key={msg.id} className="flex justify-center">
          <div className="w-full max-w-[80%] rounded-lg border bg-muted/50 px-3 py-2">
            <button
              onClick={() => toggleToolExpand(msg.id)}
              className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground w-full cursor-pointer"
            >
              {isToolCall ? "Tool Call" : "Tool Result"}
              {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>
            {isExpanded && (
              <pre className="mt-2 text-xs overflow-auto max-h-40">{msg.content}</pre>
            )}
          </div>
        </div>
      )
    }

    return (
      <div
        key={msg.id}
        className={`flex gap-2 ${isUser ? "flex-row-reverse" : "flex-row"}`}
      >
        <Avatar className="h-8 w-8 shrink-0">
          <AvatarFallback className={`text-xs ${isUser ? "bg-primary text-primary-foreground" : "bg-green-100 text-green-700"}`}>
            {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
          </AvatarFallback>
        </Avatar>
        <div
          className={`max-w-[70%] rounded-lg px-3 py-2 text-sm ${
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-green-50 text-green-900 border border-green-200"
          }`}
        >
          <p className="whitespace-pre-wrap">{msg.content}</p>
          <p className={`text-xs mt-1 ${isUser ? "text-primary-foreground/70" : "text-green-700/70"}`}>
            {new Date(msg.created_at).toLocaleTimeString()}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <ScrollArea className="flex-1 px-4 py-2">
        <div className="space-y-4">
          {messages.map(renderMessage)}
          {streamingContent && (
            <div className="flex gap-2">
              <Avatar className="h-8 w-8 shrink-0">
                <AvatarFallback className="text-xs bg-green-100 text-green-700">
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <div className="max-w-[70%] rounded-lg px-3 py-2 text-sm bg-green-50 text-green-900 border border-green-200">
                <p className="whitespace-pre-wrap">{streamingContent}</p>
              </div>
            </div>
          )}
          {loading && !streamingContent && (
            <div className="flex gap-2">
              <Avatar className="h-8 w-8 shrink-0">
                <AvatarFallback className="text-xs bg-green-100 text-green-700">
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Agent is thinking...
              </div>
            </div>
          )}
        </div>
        <div ref={bottomRef} />
      </ScrollArea>

      {/* Input */}
      <div className="px-4 py-3 border-t flex gap-2">
        <Input
          placeholder="Ask the agent..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          className="flex-1"
          disabled={loading}
        />
        <Button onClick={handleSend} disabled={loading} className="cursor-pointer">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
