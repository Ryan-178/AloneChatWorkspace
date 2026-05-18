"use client"

import { Wrench, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ToolCallCardProps {
  toolName: string;
  toolArgs?: Record<string, unknown>;
  toolResult?: unknown;
  status?: "pending" | "running" | "success" | "error";
  durationMs?: number;
  className?: string;
}

export function ToolCallCard({
  toolName,
  toolArgs,
  toolResult,
  status = "running",
  durationMs,
  className,
}: ToolCallCardProps) {
  const statusConfig = {
    pending: { icon: Loader2, color: "text-muted-foreground", animate: true },
    running: { icon: Loader2, color: "text-primary", animate: true },
    success: { icon: CheckCircle, color: "text-green-500", animate: false },
    error: { icon: XCircle, color: "text-destructive", animate: false },
  };

  const config = statusConfig[status];
  const StatusIcon = config.icon;

  return (
    <Card
      className={cn(
        "my-2 bg-muted/50",
        status === "error" && "border-destructive/50",
        className
      )}
    >
      <div className="flex items-center gap-2 p-3">
        <StatusIcon
          className={cn(
            "h-4 w-4",
            config.color,
            config.animate && "animate-spin"
          )}
        />
        <Wrench className="h-4 w-4 text-primary" />
        <span className="font-medium text-sm">{toolName}</span>
        {durationMs && (
          <span className="text-xs text-muted-foreground ml-2">
            {durationMs}ms
          </span>
        )}
        <Badge
          variant={status === "error" ? "destructive" : "secondary"}
          className="ml-auto"
        >
          {status}
        </Badge>
      </div>

      {(toolArgs || toolResult !== undefined) && (
        <CardContent className="pt-0 space-y-2">
          {toolArgs && Object.keys(toolArgs).length > 0 && (
            <div>
              <span className="text-xs font-medium text-muted-foreground">
                参数 / Args:
              </span>
              <pre className="mt-1 text-xs bg-background p-2 rounded overflow-x-auto">
                {JSON.stringify(toolArgs, null, 2)}
              </pre>
            </div>
          )}
          {toolResult !== undefined && (
            <div>
              <span className="text-xs font-medium text-muted-foreground">
                结果 / Result:
              </span>
              <pre
                className={cn(
                  "mt-1 text-xs p-2 rounded overflow-x-auto",
                  status === "error"
                    ? "bg-destructive/10 text-destructive"
                    : "bg-background"
                )}
              >
                {typeof toolResult === "string"
                  ? toolResult
                  : JSON.stringify(toolResult, null, 2)}
              </pre>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
