import { create } from 'zustand'

interface MCPToolParameter {
  name: string
  type: string
  description: string
  required: boolean
  default?: unknown
  enum?: unknown[]
}

interface MCPTool {
  name: string
  description: string
  parameters: Record<string, MCPToolParameter>
}

interface MCPServer {
  id: string
  name: string
  description: string
  version: string
  status: 'inactive' | 'active' | 'error' | 'starting' | 'stopping'
  tool_count: number
  error_message?: string
  last_connected_at?: string
  created_at: string
  updated_at: string
}

interface MCPServerCreate {
  name: string
  command: string
  args?: string[]
  env?: Record<string, string>
  cwd?: string
  timeout?: number
  description?: string
  version?: string
  auto_start?: boolean
}

interface ToolCallResult {
  success: boolean
  result?: unknown
  error?: string
  execution_time_ms: number
}

interface CallHistoryItem {
  server_id: string
  tool_name: string
  arguments: Record<string, unknown>
  result?: unknown
  error?: string
  success: boolean
  execution_time_ms: number
  timestamp: string
}

interface MCPStats {
  servers: {
    total: number
    active: number
    inactive: number
    error: number
  }
  tools: {
    total_adapters: number
    adapters_per_server: Record<string, number>
  }
  calls: {
    total: number
    successful: number
    failed: number
  }
}

interface MCPState {
  servers: MCPServer[]
  currentServer: MCPServer | null
  tools: MCPTool[]
  stats: MCPStats | null
  callHistory: CallHistoryItem[]
  isLoading: boolean
  error: string | null

  fetchServers: () => Promise<void>
  fetchServer: (serverId: string) => Promise<void>
  createServer: (data: MCPServerCreate) => Promise<MCPServer | null>
  deleteServer: (serverId: string) => Promise<boolean>
  startServer: (serverId: string) => Promise<boolean>
  stopServer: (serverId: string) => Promise<boolean>
  restartServer: (serverId: string) => Promise<boolean>
  fetchTools: (serverId: string) => Promise<void>
  fetchAllTools: () => Promise<void>
  callTool: (serverId: string, toolName: string, args: Record<string, unknown>) => Promise<ToolCallResult | null>
  fetchStats: () => Promise<void>
  fetchHistory: (serverId?: string, toolName?: string) => Promise<void>
  setCurrentServer: (server: MCPServer | null) => void
  clearError: () => void
}

const API_BASE = '/api/mcp'

export const useMCPStore = create<MCPState>((set, get) => ({
  servers: [],
  currentServer: null,
  tools: [],
  stats: null,
  callHistory: [],
  isLoading: false,
  error: null,

  fetchServers: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`${API_BASE}/servers`)
      if (!response.ok) throw new Error('Failed to fetch servers')
      const data = await response.json()
      set({ servers: data.servers, isLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
    }
  },

  fetchServer: async (serverId: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`${API_BASE}/servers/${serverId}`)
      if (!response.ok) throw new Error('Failed to fetch server')
      const server = await response.json()
      set({ currentServer: server, isLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
    }
  },

  createServer: async (data: MCPServerCreate) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`${API_BASE}/servers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!response.ok) throw new Error('Failed to create server')
      const server = await response.json()
      set((state) => ({
        servers: [...state.servers, server],
        isLoading: false,
      }))
      return server
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      return null
    }
  },

  deleteServer: async (serverId: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`${API_BASE}/servers/${serverId}`, {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('Failed to delete server')
      set((state) => ({
        servers: state.servers.filter((s) => s.id !== serverId),
        currentServer: state.currentServer?.id === serverId ? null : state.currentServer,
        isLoading: false,
      }))
      return true
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      return false
    }
  },

  startServer: async (serverId: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`${API_BASE}/servers/${serverId}/start`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to start server')
      await get().fetchServers()
      set({ isLoading: false })
      return true
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      return false
    }
  },

  stopServer: async (serverId: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`${API_BASE}/servers/${serverId}/stop`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to stop server')
      await get().fetchServers()
      set({ isLoading: false })
      return true
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      return false
    }
  },

  restartServer: async (serverId: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`${API_BASE}/servers/${serverId}/restart`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to restart server')
      await get().fetchServers()
      set({ isLoading: false })
      return true
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      return false
    }
  },

  fetchTools: async (serverId: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`${API_BASE}/servers/${serverId}/tools`)
      if (!response.ok) throw new Error('Failed to fetch tools')
      const data = await response.json()
      set({ tools: data.tools, isLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
    }
  },

  fetchAllTools: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`${API_BASE}/tools`)
      if (!response.ok) throw new Error('Failed to fetch all tools')
      const data = await response.json()
      const allTools = Object.values(data).flatMap((serverTools: { tools: MCPTool[] }) => serverTools.tools)
      set({ tools: allTools, isLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
    }
  },

  callTool: async (serverId: string, toolName: string, args: Record<string, unknown>) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`${API_BASE}/tools/call`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          server_id: serverId,
          tool_name: toolName,
          arguments: args,
        }),
      })
      if (!response.ok) throw new Error('Failed to call tool')
      const result = await response.json()
      set({ isLoading: false })
      return result
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      return null
    }
  },

  fetchStats: async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`)
      if (!response.ok) throw new Error('Failed to fetch stats')
      const stats = await response.json()
      set({ stats })
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  fetchHistory: async (serverId?: string, toolName?: string) => {
    try {
      const params = new URLSearchParams()
      if (serverId) params.append('server_id', serverId)
      if (toolName) params.append('tool_name', toolName)
      const response = await fetch(`${API_BASE}/history?${params.toString()}`)
      if (!response.ok) throw new Error('Failed to fetch history')
      const data = await response.json()
      set({ callHistory: data.calls })
    } catch (error) {
      set({ error: (error as Error).message })
    }
  },

  setCurrentServer: (server: MCPServer | null) => {
    set({ currentServer: server })
  },

  clearError: () => {
    set({ error: null })
  },
}))
