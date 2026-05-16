import { create } from 'zustand'
import type { Conversation, Message, TypingIndicator } from '@/types/chat'

interface ChatStore {
  conversations: Conversation[]
  currentConversation: Conversation | null
  messages: Message[]
  typingIndicators: TypingIndicator[]
  isLoading: boolean
  
  setConversations: (conversations: Conversation[]) => void
  setCurrentConversation: (conversation: Conversation | null) => void
  addConversation: (conversation: Conversation) => void
  updateConversation: (id: string, updates: Partial<Conversation>) => void
  removeConversation: (id: string) => void
  
  setMessages: (messages: Message[]) => void
  addMessage: (message: Message) => void
  updateMessage: (id: string, updates: Partial<Message>) => void
  
  setTypingIndicator: (indicator: TypingIndicator) => void
  clearTypingIndicator: (conversationId: string, userId: string) => void
  
  setLoading: (loading: boolean) => void
}

export const useChatStore = create<ChatStore>((set) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  typingIndicators: [],
  isLoading: false,

  setConversations: (conversations) => set({ conversations }),
  setCurrentConversation: (conversation) => set({ 
    currentConversation: conversation,
    messages: []
  }),
  addConversation: (conversation) => set((state) => ({
    conversations: [conversation, ...state.conversations]
  })),
  updateConversation: (id, updates) => set((state) => ({
    conversations: state.conversations.map((c) =>
      c.id === id ? { ...c, ...updates } : c
    ),
  })),
  removeConversation: (id) => set((state) => ({
    conversations: state.conversations.filter((c) => c.id !== id),
    currentConversation: state.currentConversation?.id === id ? null : state.currentConversation,
  })),

  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  updateMessage: (id, updates) => set((state) => ({
    messages: state.messages.map((m) =>
      m.id === id ? { ...m, ...updates } : m
    ),
  })),

  setTypingIndicator: (indicator) => set((state) => {
    const existing = state.typingIndicators.findIndex(
      (t) => t.conversation_id === indicator.conversation_id && t.user_id === indicator.user_id
    )
    if (existing >= 0) {
      const updated = [...state.typingIndicators]
      updated[existing] = indicator
      return { typingIndicators: updated }
    }
    return { typingIndicators: [...state.typingIndicators, indicator] }
  }),
  clearTypingIndicator: (conversationId, userId) => set((state) => ({
    typingIndicators: state.typingIndicators.filter(
      (t) => !(t.conversation_id === conversationId && t.user_id === userId)
    ),
  })),

  setLoading: (isLoading) => set({ isLoading }),
}))
