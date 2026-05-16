export type AgentMode = 'MTC' | 'CODE'
export type SessionState = 'idle' | 'running' | 'paused' | 'error' | 'finished'

export interface AgentSession {
  session_id: string
  user_id: string
  mode: AgentMode
  state: SessionState
  created_at: string
  updated_at: string
}

export interface AgentMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  type: AgentMessageType
  created_at: string
  metadata?: Record<string, unknown>
}

export type AgentMessageType =
  | 'thinking'
  | 'acting'
  | 'observation'
  | 'final'
  | 'error'
  | 'clarification'

export interface ToolCall {
  name: string
  arguments: Record<string, unknown>
  result?: unknown
  status: 'pending' | 'running' | 'success' | 'error'
}

export interface ThinkingBlock {
  thought: string
  action?: string
  action_input?: Record<string, unknown>
}

export interface ModeSwitchResponse {
  success: boolean
  current_mode: AgentMode
  previous_mode?: AgentMode
  message: string
}
