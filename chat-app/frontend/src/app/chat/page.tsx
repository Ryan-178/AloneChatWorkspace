"use client"

import { useEffect, useState, Suspense } from "react"
import { useRouter } from "next/navigation"
import { ChatLayout } from "@/components/chat-layout"
import { api } from "@/lib/api"
import { wsClient } from "@/lib/websocket"
import { syncService } from "@/lib/sync-service"

function ChatPageContent() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/")
      return
    }

    api.users.me()
      .then((u) => {
        setUser(u)
        wsClient.connect(token)
        const stopSync = syncService.startAutoSync(30000)
        return () => {
          stopSync()
        }
      })
      .catch(() => {
        localStorage.removeItem("token")
        router.push("/")
      })
      .finally(() => setLoading(false))

    return () => {
      wsClient.disconnect()
    }
  }, [router])

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (!user) return null

  return <ChatLayout user={user} />
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    }>
      <ChatPageContent />
    </Suspense>
  )
}
