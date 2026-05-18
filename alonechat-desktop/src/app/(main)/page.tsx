"use client";

import { useAgentStore } from "@/stores/agent-store";
import { useAuthStore } from "@/stores/auth-store";
import { AgentChat, SessionList } from "@/components/agent";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useEffect } from "react";
import { MessageSquare, Zap } from "lucide-react";

export default function HomePage() {
  const { sessions, session, fetchSessions, createSession, selectSession, deleteSession } =
    useAgentStore();
  const { isAuthenticated, token } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      fetchSessions();
    }
  }, [isAuthenticated, fetchSessions]);

  const handleCreateSession = async () => {
    const newSession = await createSession("新会话 / New Session");
    selectSession(newSession);
  };

  return (
    <div className="flex h-full">
      <div className="w-72 border-r flex flex-col">
        <SessionList
          sessions={sessions}
          currentSession={session}
          onSelect={selectSession}
          onCreate={handleCreateSession}
          onDelete={deleteSession}
        />
      </div>

      <Separator orientation="vertical" />

      <div className="flex-1 flex flex-col">
        {session ? (
          <AgentChat sessionId={session.id} />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
            <MessageSquare className="h-16 w-16 text-muted-foreground mb-4" />
            <h2 className="text-2xl font-semibold mb-2">
              欢迎使用 AloneChat / Welcome to AloneChat
            </h2>
            <p className="text-muted-foreground mb-6 max-w-md">
              选择一个会话开始对话，或创建新会话与 AI Agent 交互。
              <br />
              Select a session to start, or create a new one to interact with AI
              Agent.
            </p>

            <div className="flex gap-4">
              <Button onClick={handleCreateSession} className="gap-2">
                <MessageSquare className="h-4 w-4" />
                新建会话 / New Session
              </Button>
              <Button variant="outline" className="gap-2">
                <Zap className="h-4 w-4" />
                快速任务 / Quick Task
              </Button>
            </div>

            {!isAuthenticated && (
              <p className="text-sm text-muted-foreground mt-8">
                提示: 请先登录以保存会话历史。
                <br />
                Tip: Please login to save session history.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
