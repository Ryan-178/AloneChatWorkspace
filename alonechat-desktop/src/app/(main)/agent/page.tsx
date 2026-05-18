"use client";

import { useAgentStore } from "@/stores/agent-store";
import { AgentChat, SessionList } from "@/components/agent";
import { useEffect } from "react";

export default function AgentPage() {
  const { sessions, session, fetchSessions, createSession, selectSession, deleteSession } =
    useAgentStore();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleCreateSession = async () => {
    const newSession = await createSession("新 Agent 会话");
    selectSession(newSession);
  };

  return (
    <div className="flex h-full">
      <div className="w-72 border-r">
        <SessionList
          sessions={sessions}
          currentSession={session}
          onSelect={selectSession}
          onCreate={handleCreateSession}
          onDelete={deleteSession}
        />
      </div>

      <div className="flex-1">
        {session ? (
          <AgentChat sessionId={session.id} />
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <div className="text-center">
              <p className="text-lg font-medium mb-2">Agent 对话 / Agent Chat</p>
              <p className="text-sm mb-4">选择或创建一个会话开始对话</p>
              <button
                onClick={handleCreateSession}
                className="text-primary hover:underline"
              >
                创建新会话 / Create new session
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
