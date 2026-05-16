export type ChatType = 'direct' | 'group'

export interface Message {
  id: string
  conversation_id: string
  sender_id: string
  content: string
  content_type: 'text' | 'markdown' | 'file' | 'image'
  created_at: string
  updated_at?: string
  metadata?: Record<string, unknown>
}

export interface Conversation {
  id: string
  name?: string
  type: ChatType
  participants: string[]
  last_message?: Message
  unread_count: number
  created_at: string
  updated_at: string
}

export interface TypingIndicator {
  conversation_id: string
  user_id: string
  is_typing: boolean
}
