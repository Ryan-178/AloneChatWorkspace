"use client"

import { Type, Square, Image } from "lucide-react"
import { Button } from "@/components/ui/button"

interface PresentationToolbarProps {
  onAddText: () => void
  onAddShape: () => void
}

export function PresentationToolbar({ onAddText, onAddShape }: PresentationToolbarProps) {
  return (
    <div className="flex items-center gap-1 px-3 py-1.5">
      <Button variant="ghost" size="sm" className="gap-1 h-7" onClick={onAddText}>
        <Type className="h-3.5 w-3.5" />
        文本框
      </Button>
      <Button variant="ghost" size="sm" className="gap-1 h-7" onClick={onAddShape}>
        <Square className="h-3.5 w-3.5" />
        形状
      </Button>
    </div>
  )
}
