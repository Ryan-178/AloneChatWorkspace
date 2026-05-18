export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical'

export interface Task {
  id: string
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  progress: number
  session_id?: string
  artifacts: string[]
  created_at: string
  updated_at: string
  completed_at?: string
  error?: string
  metadata?: Record<string, unknown>
}

export interface TaskProgress {
  task_id: string
  status: TaskStatus
  progress: number
  message: string
  timestamp: string
}

export interface CreateTaskRequest {
  title: string
  description: string
  priority?: TaskPriority
  session_id?: string
}
