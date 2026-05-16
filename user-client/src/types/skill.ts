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

export interface RemoteSkill {
  id: string
  name: string
  description: string
  owner: string
  repo: string
  skill_path?: string
  version: string
  installs: number
  stars: number
  url: string
  github_url: string
  raw_url?: string
}

export interface RemoteSkillInstallRequest {
  url: string
  skill_name?: string
  branch?: string
  global_install?: boolean
  force?: boolean
}

export interface RemoteSkillInstallResponse {
  success: boolean
  skill?: string
  path?: string
  files?: string[]
  source?: string
  error?: string
}

export interface InstalledRemoteSkill {
  name: string
  path: string
  scope: 'local' | 'global'
  installed_at?: string
  source?: string
  branch?: string
  files?: string[]
}
