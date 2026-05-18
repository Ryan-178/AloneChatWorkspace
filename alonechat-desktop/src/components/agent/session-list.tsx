"use client"

import { formatRelativeTime } from "@/lib/utils";
import type { AgentSession } from "@/types";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Plus, MessageSquare, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SessionListProps {
  sessions: AgentSession[];
  currentSession: AgentSession | null;
  onSelect: (session: AgentSession) => void;
  onCreate: () => void;
  onDelete: (sessionId: string) => void;
  className?: string;
}

export function SessionList({
  sessions,
  currentSession,
  onSelect,
  onCreate,
  onDelete,
  className,
}: SessionListProps) {
  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="p-3 border-b flex items-center justify-between">
        <h3 className="font-semibold text-sm">会话 / Sessions</h3>
        <Button variant="ghost" size="icon" onClick={onCreate} className="h-8 w-8">
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {sessions.length === 0 ? (
            <div className="text-center text-muted-foreground text-sm py-8">
              暂无会话 / No sessions
              <Button
                variant="link"
                size="sm"
                onClick={onCreate}
                className="block mt-2"
              >
                创建新会话 / Create new
              </Button>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={cn(
                  "group flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors",
                  currentSession?.id === session.id
                    ? "bg-primary/10 text-primary"
                    : "hover:bg-muted"
                )}
                onClick={() => onSelect(session)}
              >
                <MessageSquare className="h-4 w-4 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">
                    {session.title || "新会话"}
                  </div>
                  <div className="text-xs text-muted-foreground truncate">
                    {session.last_message || `${session.message_count} 条消息`}
                  </div>
                </div>
                <div className="text-xs text-muted-foreground shrink-0">
                  {formatRelativeTime(session.updated_at)}
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100 shrink-0"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(session.id);
                  }}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
