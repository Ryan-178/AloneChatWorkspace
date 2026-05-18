"use client"

import type { AgentMode } from "@/types";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Zap, Code } from "lucide-react";

interface ModeSwitchProps {
  mode: AgentMode;
  onModeChange: (mode: AgentMode) => void;
  disabled?: boolean;
}

export function ModeSwitch({ mode, onModeChange, disabled }: ModeSwitchProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground">模式 / Mode:</span>
      <ToggleGroup
        type="single"
        value={mode}
        onValueChange={(v) => v && onModeChange(v as AgentMode)}
        className="border rounded-lg p-1"
        disabled={disabled}
      >
        <ToggleGroupItem
          value="MTC"
          className="gap-1.5 px-3 data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
          aria-label="MTC Mode - Multi-Step Task Completion"
        >
          <Zap className="h-3.5 w-3.5" />
          <span className="text-xs font-medium">MTC</span>
        </ToggleGroupItem>
        <ToggleGroupItem
          value="CODE"
          className="gap-1.5 px-3 data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
          aria-label="CODE Mode - Direct Code Execution"
        >
          <Code className="h-3.5 w-3.5" />
          <span className="text-xs font-medium">CODE</span>
        </ToggleGroupItem>
      </ToggleGroup>
    </div>
  );
}
