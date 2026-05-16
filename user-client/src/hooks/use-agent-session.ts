import { useCallback, useEffect, useState } from 'react'
import { useAgentStore } from '@/stores/agent-store'
import { useWebSocket } from './use-websocket'
import { agentApi } from '@/lib/api/agent'
import type { AgentMessage, AgentMode } from '@/types/agent'
import type { GatewayMessage } from '@/lib/websocket/types'

export function useAgentSession(sessionId: string | null) {
  const { currentSession, messages, mode, state, addMessage, setMode, setState, clearMessages } = useAgentStore()
  const { isConnected, subscribe, unsubscribe, sendMessage, onMessage } = useWebSocket(
    currentSession?.user_id || null
  )
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (!sessionId || !isConnected) return

    subscribe(`session:${sessionId}`)

    const unsubscribers = [
      onMessage('thinking', (msg: GatewayMessage) => {
        addMessage({
          id: crypto.randomUUID(),
          session_id: sessionId,
          role: 'assistant',
          content: msg.content as string,
          type: 'thinking',
          created_at: new Date().toISOString(),
        })
      }),

      onMessage('acting', (msg: GatewayMessage) => {
        addMessage({
          id: crypto.randomUUID(),
          session_id: sessionId,
          role: 'assistant',
          content: msg.content as string,
          type: 'acting',
          created_at: new Date().toISOString(),
        })
      }),

      onMessage('observation', (msg: GatewayMessage) => {
        addMessage({
          id: crypto.randomUUID(),
          session_id: sessionId,
          role: 'assistant',
          content: JSON.stringify(msg.content),
          type: 'observation',
          created_at: new Date().toISOString(),
        })
      }),

      onMessage('final', (msg: GatewayMessage) => {
        addMessage({
          id: crypto.randomUUID(),
          session_id: sessionId,
          role: 'assistant',
          content: msg.content as string,
          type: 'final',
          created_at: new Date().toISOString(),
        })
        setState('finished')
      }),

      onMessage('error', (msg: GatewayMessage) => {
        addMessage({
          id: crypto.randomUUID(),
          session_id: sessionId,
          role: 'assistant',
          content: (msg.content as { error_message?: string })?.error_message || 'Unknown error',
          type: 'error',
          created_at: new Date().toISOString(),
        })
        setState('error')
      }),
    ]

    return () => {
      unsubscribe(`session:${sessionId}`)
      unsubscribers.forEach((unsub) => unsub())
    }
  }, [sessionId, isConnected, subscribe, unsubscribe, onMessage, addMessage, setState])

  const switchMode = useCallback(async (newMode: AgentMode) => {
    setIsLoading(true)
    try {
      const result = await agentApi.switchMode(newMode, sessionId || undefined)
      if (result.success) {
        setMode(result.current_mode as AgentMode)
      }
      return result
    } finally {
      setIsLoading(false)
    }
  }, [sessionId, setMode])

  const sendAgentMessage = useCallback((content: string) => {
    if (!isConnected || state === 'running') return

    const userMessage: AgentMessage = {
      id: crypto.randomUUID(),
      session_id: sessionId || '',
      role: 'user',
      content,
      type: 'final',
      created_at: new Date().toISOString(),
    }
    addMessage(userMessage)
    setState('running')
    sendMessage(content)
  }, [isConnected, state, sessionId, addMessage, setState, sendMessage])

  return {
    session: currentSession,
    messages,
    mode,
    state,
    isConnected,
    isLoading,
    switchMode,
    sendMessage: sendAgentMessage,
    clearMessages,
  }
}
