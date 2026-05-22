"use client"

import type { InteractionMode } from "@/types/agent";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Search, Bot, Rocket } from "lucide-react";

interface ModeSwitchProps {
  mode: InteractionMode;
  onModeChange: (mode: InteractionMode) => void;
  disabled?: boolean;
  showLabels?: boolean;
}

const modeConfig = {
  plan: {
    icon: Search,
    label: "PLAN",
    description: "只读探索模式 / Read-only exploration mode",
    color: "data-[state=on]:bg-blue-500 data-[state=on]:text-white",
  },
  agent: {
    icon: Bot,
    label: "AGENT",
    description: "默认交互模式 / Default interaction mode",
    color: "data-[state=on]:bg-green-500 data-[state=on]:text-white",
  },
  yolo: {
    icon: Rocket,
    label: "YOLO",
    description: "自动批准模式 / Auto-approve mode",
    color: "data-[state=on]:bg-yellow-500 data-[state=on]:text-white",
  },
};

export function ModeSwitch({ 
  mode, 
  onModeChange, 
  disabled,
  showLabels = true 
}: ModeSwitchProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground">
        交互模式 / Mode:
      </span>
      <ToggleGroup
        type="single"
        value={mode}
        onValueChange={(v) => v && onModeChange(v as InteractionMode)}
        className="border rounded-lg p-1"
        disabled={disabled}
      >
        {Object.entries(modeConfig).map(([key, config]) => {
          const Icon = config.icon;
          return (
            <ToggleGroupItem
              key={key}
              value={key}
              className={`gap-1.5 px-3 ${config.color}`}
              aria-label={config.description}
              title={config.description}
            >
              <Icon className="h-3.5 w-3.5" />
              {showLabels && (
                <span className="text-xs font-medium">{config.label}</span>
              )}
            </ToggleGroupItem>
          );
        })}
      </ToggleGroup>
    </div>
  );
}

export function ModeIndicator({ mode }: { mode: InteractionMode }) {
  const config = modeConfig[mode];
  const Icon = config.icon;
  
  return (
    <div 
      className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs"
      title={config.description}
    >
      <Icon className="h-3.5 w-3.5" />
      <span className="font-medium">{config.label}</span>
    </div>
  );
}

export function ModeDescription({ mode }: { mode: InteractionMode }) {
  const descriptions = {
    plan: {
      title: "🔍 PLAN 模式",
      content: "只读探索模式，仅允许读取和搜索操作，适合代码分析和理解。",
      features: [
        "允许文件读取和搜索",
        "禁止文件修改和删除",
        "禁止Shell命令执行",
        "适合代码审查和理解",
      ],
    },
    agent: {
      title: "🤖 AGENT 模式",
      content: "默认交互模式，危险操作需要用户确认，平衡安全性和效率。",
      features: [
        "允许所有工具使用",
        "危险操作需要确认",
        "Shell命令需审批",
        "文件修改需确认",
      ],
    },
    yolo: {
      title: "🚀 YOLO 模式",
      content: "自动批准模式，所有操作自动执行，适合信任的工作区。",
      features: [
        "所有工具自动批准",
        "无需用户确认",
        "高效快速执行",
        "适合信任环境",
      ],
    },
  };

  const desc = descriptions[mode];

  return (
    <div className="space-y-2">
      <h4 className="font-semibold">{desc.title}</h4>
      <p className="text-sm text-muted-foreground">{desc.content}</p>
      <ul className="text-sm space-y-1">
        {desc.features.map((feature, i) => (
          <li key={i} className="flex items-center gap-2">
            <span className="text-primary">•</span>
            {feature}
          </li>
        ))}
      </ul>
    </div>
  );
}
