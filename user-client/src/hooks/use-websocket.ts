import { useCallback, useEffect, useRef, useState } from 'react'
import { GatewayWebSocket } from '@/lib/websocket/gateway'
import type { GatewayMessage, GatewayMessageType } from '@/lib/websocket/types'

export function useWebSocket(userId: string | null) {
  const wsRef = useRef<GatewayWebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Event | null>(null)

  useEffect(() => {
    if (!userId) return

    const ws = new GatewayWebSocket()
    wsRef.current = ws

    ws.onConnect(() => {
      setIsConnected(true)
      setError(null)
    })

    ws.onDisconnect(() => {
      setIsConnected(false)
    })

    ws.onError((e) => {
      setError(e)
    })

    ws.connect(userId).catch(console.error)

    return () => {
      ws.disconnect()
    }
  }, [userId])

  const subscribe = useCallback((channel: string) => {
    wsRef.current?.subscribe(channel)
  }, [])

  const unsubscribe = useCallback((channel: string) => {
    wsRef.current?.unsubscribe(channel)
  }, [])

  const sendMessage = useCallback((body: string, type?: string) => {
    wsRef.current?.sendMessage(body, type)
  }, [])

  const onMessage = useCallback((type: GatewayMessageType | '*', handler: (message: GatewayMessage) => void) => {
    if (!wsRef.current) return () => {}
    return wsRef.current.onMessage(type, handler)
  }, [])

  return {
    isConnected,
    error,
    subscribe,
    unsubscribe,
    sendMessage,
    onMessage,
  }
}
