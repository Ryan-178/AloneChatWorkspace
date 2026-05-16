export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical'

export interface Task {
  id: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  progress: number
  created_at: string
  started_at?: string
  completed_at?: string
  metadata?: Record<string, unknown>
}

export interface Artifact {
  id: string
  name: string
  type: string
  path: string
  size: number
  created_at: string
}
