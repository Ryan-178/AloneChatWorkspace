export interface Skill {
  name: string
  description: string
  category: string
  version: string
  author?: string
  tags: string[]
  input_schema?: Record<string, unknown>
  output_schema?: Record<string, unknown>
}

export interface SkillExecutionRequest {
  skill_name: string
  context: Record<string, unknown>
}

export interface SkillExecutionResponse {
  success: boolean
  result?: Record<string, unknown>
  error?: string
}
