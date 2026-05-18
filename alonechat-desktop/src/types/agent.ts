export type AgentMode = 'MTC' | 'CODE'

export interface AgentMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  type: 'text' | 'thinking' | 'acting' | 'observation' | 'final' | 'error'
  content: string
  metadata?: {
    tool_name?: string
    tool_args?: Record<string, unknown>
    tool_result?: unknown
    duration?: number
    duration_ms?: number
    step?: number
    thinking_steps?: string[]
  }
  created_at: string
}

export interface AgentSession {
  id: string
  title: string
  mode: AgentMode
  status: 'idle' | 'thinking' | 'acting' | 'completed' | 'error'
  messages: AgentMessage[]
  message_count: number
  last_message?: string
  created_at: string
  updated_at: string
  summary?: string
}

export interface ModeSwitchResponse {
  previous_mode: AgentMode
  new_mode: AgentMode
  success: boolean
}
