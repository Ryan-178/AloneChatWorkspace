"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { LogOut, MessageSquare, Users, Bot, FolderOpen } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { ConversationList } from "@/components/conversation-list"
import { ChatArea } from "@/components/chat-area"
import { GroupList } from "@/components/group-list"
import { AgentPanel } from "@/components/agent-panel"
import { WorkspaceSwitcher } from "@/components/workspace-switcher"
import { FileExplorer } from "@/components/file-explorer"
import { OfficeArea } from "@/components/office/office-area"
import { api } from "@/lib/api"

interface ChatLayoutProps {
  user: any
}

export function ChatLayout({ user }: ChatLayoutProps) {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<"conversations" | "groups" | "agent" | "files">("conversations")
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selectedType, setSelectedType] = useState<"conversation" | "group" | "document" | "spreadsheet" | "presentation">("conversation")
  const [officeFileId, setOfficeFileId] = useState<number | null>(null)
  const [officeFileType, setOfficeFileType] = useState<"document" | "spreadsheet" | "presentation" | null>(null)
  const [conversations, setConversations] = useState<any[]>([])
  const [groups, setGroups] = useState<any[]>([])

  useEffect(() => {
    loadConversations()
    loadGroups()
  }, [])

  const loadConversations = async () => {
    try {
      const data = await api.conversations.list()
      setConversations(data)
    } catch {
      // ignore
    }
  }

  const loadGroups = async () => {
    try {
      const data = await api.groups.list()
      setGroups(data)
    } catch {
      // ignore
    }
  }

  const handleLogout = () => {
    localStorage.removeItem("token")
    router.push("/")
  }

  const handleSelectConversation = (id: string) => {
    setSelectedId(id)
    setSelectedType("conversation")
    setOfficeFileId(null)
    setOfficeFileType(null)
  }

  const handleSelectGroup = (id: string) => {
    setSelectedId(id)
    setSelectedType("group")
    setOfficeFileId(null)
    setOfficeFileType(null)
  }

  const handleSelectFile = (id: number, fileType: "document" | "spreadsheet" | "presentation") => {
    setOfficeFileId(id)
    setOfficeFileType(fileType)
    setSelectedType(fileType)
    setSelectedId(String(id))
  }

  const handleBackFromOffice = () => {
    setOfficeFileId(null)
    setOfficeFileType(null)
    setSelectedId(null)
    setSelectedType("conversation")
  }

  const isOfficeType = selectedType === "document" || selectedType === "spreadsheet" || selectedType === "presentation"

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className="w-80 border-r flex flex-col">
        {/* User info */}
        <div className="p-4 flex items-center gap-3">
          <Avatar className="h-10 w-10">
            <AvatarFallback className="bg-primary text-primary-foreground">
              {user.display_name?.[0]?.toUpperCase() || "U"}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="font-medium truncate">{user.display_name}</p>
            <p className="text-xs text-muted-foreground truncate">{user.email}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={handleLogout} className="cursor-pointer shrink-0">
            <LogOut className="h-4 w-4" />
          </Button>
        </div>

        <Separator />

        {/* Workspace Switcher */}
        <div className="px-3 py-2 border-b">
          <WorkspaceSwitcher onWorkspaceChange={() => {
            loadConversations()
            loadGroups()
          }} />
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab("conversations")}
            className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors cursor-pointer ${
              activeTab === "conversations"
                ? "text-primary border-b-2 border-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            会话
          </button>
          <button
            onClick={() => setActiveTab("groups")}
            className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors cursor-pointer ${
              activeTab === "groups"
                ? "text-primary border-b-2 border-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Users className="h-4 w-4" />
            群组
          </button>
          <button
            onClick={() => setActiveTab("agent")}
            className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors cursor-pointer ${
              activeTab === "agent"
                ? "text-primary border-b-2 border-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Bot className="h-4 w-4" />
            Agent
          </button>
          <button
            onClick={() => setActiveTab("files")}
            className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors cursor-pointer ${
              activeTab === "files"
                ? "text-primary border-b-2 border-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <FolderOpen className="h-4 w-4" />
            文件
          </button>
        </div>

        {/* List */}
        <div className="flex-1 overflow-hidden">
          {activeTab === "conversations" ? (
            <ConversationList
              conversations={conversations}
              selectedId={selectedId}
              onSelect={handleSelectConversation}
              onRefresh={loadConversations}
            />
          ) : activeTab === "groups" ? (
            <GroupList
              groups={groups}
              selectedId={selectedId}
              onSelect={handleSelectGroup}
              onRefresh={loadGroups}
            />
          ) : activeTab === "files" ? (
            <FileExplorer onSelectFile={handleSelectFile} />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground text-sm">
              切换到 Agent 标签查看 Agent 面板
            </div>
          )}
        </div>
      </div>

      {/* Main Area */}
      <div className="flex-1">
        {activeTab === "agent" ? (
          <AgentPanel currentUser={user} />
        ) : isOfficeType && officeFileId !== null && officeFileType !== null ? (
          <OfficeArea
            key={`office-${officeFileId}`}
            fileId={officeFileId}
            fileType={officeFileType}
            onBack={handleBackFromOffice}
          />
        ) : selectedId ? (
          <ChatArea
            key={`${selectedType}-${selectedId}`}
            id={selectedId}
            type={selectedType as "conversation" | "group"}
            currentUser={user}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            {activeTab === "files" ? "选择一个文件开始编辑" : "选择一个会话开始聊天"}
          </div>
        )}
      </div>
    </div>
  )
}
