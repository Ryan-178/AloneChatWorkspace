"use client"

import { useEffect, useRef } from "react";
import { useAgentStore } from "@/stores/agent-store";
import { MessageBubble } from "./message-bubble";
import { ThinkingBlock } from "./thinking-block";
import { ToolCallCard } from "./tool-call-card";
import { MessageInput } from "./message-input";
import { ModeSwitch } from "./mode-switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Loader2 } from "lucide-react";

interface AgentChatProps {
  sessionId?: string;
}

export function AgentChat({ sessionId }: AgentChatProps) {
  const {
    session,
    messages,
    mode,
    isThinking,
    currentTool,
    sendMessage,
    switchMode,
  } = useAgentStore();

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h2 className="font-semibold">
            {session?.title || "Agent 对话 / Agent Chat"}
          </h2>
          {session && (
            <p className="text-xs text-muted-foreground">
              {messages.length} 条消息 / messages
            </p>
          )}
        </div>
        <ModeSwitch mode={mode} onModeChange={switchMode} disabled={isThinking} />
      </div>

      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
            <p className="text-lg font-medium mb-2">
              开始对话 / Start Conversation
            </p>
            <p className="text-sm">
              输入您的问题或任务，Agent 将帮助您完成。
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {messages.map((msg) => {
              if (msg.type === "thinking") {
                return (
                  <ThinkingBlock
                    key={msg.id}
                    content={msg.content}
                    steps={msg.metadata?.thinking_steps}
                    durationMs={msg.metadata?.duration_ms}
                  />
                );
              }

              if (msg.type === "acting") {
                return (
                  <ToolCallCard
                    key={msg.id}
                    toolName={msg.metadata?.tool_name || "unknown"}
                    toolArgs={msg.metadata?.tool_args}
                    status="running"
                  />
                );
              }

              if (msg.type === "observation") {
                return (
                  <ToolCallCard
                    key={msg.id}
                    toolName={currentTool || "unknown"}
                    toolResult={msg.metadata?.tool_result}
                    status="success"
                    durationMs={msg.metadata?.duration_ms}
                  />
                );
              }

              if (msg.type === "error") {
                return (
                  <ToolCallCard
                    key={msg.id}
                    toolName={currentTool || "error"}
                    toolResult={msg.content}
                    status="error"
                  />
                );
              }

              return <MessageBubble key={msg.id} message={msg} />;
            })}

            {isThinking && (
              <div className="flex items-center gap-2 text-muted-foreground py-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">思考中... / Thinking...</span>
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      <Separator />

      <div className="p-4">
        <MessageInput
          onSend={sendMessage}
          isLoading={isThinking}
          disabled={!session}
          placeholder={
            session
              ? "输入消息... / Type a message..."
              : "请先创建或选择会话 / Create or select a session first"
          }
        />
      </div>
    </div>
  );
}
