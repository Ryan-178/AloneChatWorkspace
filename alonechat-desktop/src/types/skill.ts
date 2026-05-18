export interface Skill {
  name: string
  title: string
  description: string
  category: string
  version: string
  author?: string
  icon?: string
  tags: string[]
  parameters: SkillParameter[]
  examples: SkillExample[]
  is_installed: boolean
  is_remote: boolean
  created_at: string
}

export interface SkillParameter {
  name: string
  type: 'string' | 'number' | 'boolean' | 'array' | 'object'
  description: string
  required: boolean
  default?: unknown
  enum?: string[]
}

export interface SkillExample {
  description: string
  input: Record<string, unknown>
  output?: unknown
}

export interface ExecuteSkillRequest {
  skill_name: string
  parameters: Record<string, unknown>
  session_id?: string
}

export interface ExecuteSkillResponse {
  execution_id: string
  status: 'running' | 'completed' | 'failed'
  result?: unknown
  error?: string
  duration_ms?: number
}
