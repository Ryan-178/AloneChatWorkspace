import { create } from 'zustand'
import type { AgentMode, AgentSession, AgentMessage, SessionState } from '@/types/agent'

interface AgentStore {
  sessions: AgentSession[]
  currentSession: AgentSession | null
  messages: AgentMessage[]
  mode: AgentMode
  state: SessionState
  isConnecting: boolean
  
  setSessions: (sessions: AgentSession[]) => void
  setCurrentSession: (session: AgentSession | null) => void
  addSession: (session: AgentSession) => void
  removeSession: (sessionId: string) => void
  
  setMessages: (messages: AgentMessage[]) => void
  addMessage: (message: AgentMessage) => void
  clearMessages: () => void
  
  setMode: (mode: AgentMode) => void
  setState: (state: SessionState) => void
  setConnecting: (connecting: boolean) => void
}

export const useAgentStore = create<AgentStore>((set) => ({
  sessions: [],
  currentSession: null,
  messages: [],
  mode: 'MTC',
  state: 'idle',
  isConnecting: false,

  setSessions: (sessions) => set({ sessions }),
  setCurrentSession: (session) => set({ currentSession: session, messages: [] }),
  addSession: (session) => set((state) => ({
    sessions: [session, ...state.sessions]
  })),
  removeSession: (sessionId) => set((state) => ({
    sessions: state.sessions.filter((s) => s.session_id !== sessionId),
    currentSession: state.currentSession?.session_id === sessionId ? null : state.currentSession,
  })),

  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  clearMessages: () => set({ messages: [] }),

  setMode: (mode) => set({ mode }),
  setState: (state) => set({ state }),
  setConnecting: (isConnecting) => set({ isConnecting }),
}))
