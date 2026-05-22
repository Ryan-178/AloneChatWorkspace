export type ToolCategory = 'shell' | 'file' | 'git' | 'web' | 'code' | 'general'

export type PermissionLevel = 'read' | 'write' | 'execute' | 'dangerous'

export interface ToolInfo {
  name: string
  description: string
  category: ToolCategory
  permission_level: PermissionLevel
  estimated_cost: number
  is_dangerous: boolean
  needs_confirmation: boolean
}

export interface ToolParameter {
  name: string
  type: string
  description: string
  required: boolean
  default?: unknown
  enum?: unknown[]
}

export interface ToolDefinition {
  name: string
  description: string
  parameters: Record<string, ToolParameter>
  category: ToolCategory
  permission_level: PermissionLevel
  estimated_cost: number
}

export interface ToolResult {
  success: boolean
  data?: unknown
  error?: string
  execution_time_ms: number
  timestamp: string
  metadata: Record<string, unknown>
}

export interface ToolApprovalRequest {
  id: string
  tool_name: string
  params: Record<string, unknown>
  permission_level: PermissionLevel
  category: ToolCategory
  description: string
  created_at: string
}

export interface ToolApprovalResponse {
  request_id: string
  approved: boolean
  remember: boolean
}

export interface ToolExecutionRequest {
  tool_name: string
  params: Record<string, unknown>
  session_id?: string
}

export interface ToolExecutionResponse {
  success: boolean
  result?: ToolResult
  error?: string
}
