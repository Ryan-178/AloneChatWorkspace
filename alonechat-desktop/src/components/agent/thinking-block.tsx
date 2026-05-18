"use client"

import { useState } from "react";
import { ChevronDown, ChevronRight, Brain } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ThinkingBlockProps {
  content: string;
  steps?: string[];
  durationMs?: number;
  className?: string;
}

export function ThinkingBlock({
  content,
  steps,
  durationMs,
  className,
}: ThinkingBlockProps) {
  const [expanded, setExpanded] = useState(true);

  return (
    <Card className={cn("my-2 bg-muted/50 border-primary/20", className)}>
      <div
        className="flex items-center gap-2 p-3 cursor-pointer hover:bg-muted/80 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
        <Brain className="h-4 w-4 text-primary" />
        <span className="font-medium text-sm">思考过程 / Thinking</span>
        {durationMs && (
          <span className="text-xs text-muted-foreground ml-2">
            {durationMs}ms
          </span>
        )}
        <Badge variant="secondary" className="ml-auto">
          Thinking
        </Badge>
      </div>
      {expanded && (
        <CardContent className="pt-0 text-sm text-muted-foreground">
          {steps && steps.length > 0 ? (
            <ol className="list-decimal list-inside space-y-1">
              {steps.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          ) : (
            <pre className="whitespace-pre-wrap">{content}</pre>
          )}
        </CardContent>
      )}
    </Card>
  );
}
