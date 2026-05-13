"use client"

import { Bold, Italic, AlignLeft, AlignCenter, AlignRight } from "lucide-react"
import { Button } from "@/components/ui/button"

interface SpreadsheetToolbarProps {
  onBold: () => void
  onItalic: () => void
  isBold: boolean
  isItalic: boolean
}

export function SpreadsheetToolbar({ onBold, onItalic, isBold, isItalic }: SpreadsheetToolbarProps) {
  return (
    <div className="flex items-center gap-1 px-3 py-1.5">
      <Button variant={isBold ? "secondary" : "ghost"} size="icon" className="h-7 w-7" onClick={onBold}>
        <Bold className="h-3.5 w-3.5" />
      </Button>
      <Button variant={isItalic ? "secondary" : "ghost"} size="icon" className="h-7 w-7" onClick={onItalic}>
        <Italic className="h-3.5 w-3.5" />
      </Button>
      <div className="w-px h-5 bg-border mx-1" />
      <Button variant="ghost" size="icon" className="h-7 w-7">
        <AlignLeft className="h-3.5 w-3.5" />
      </Button>
      <Button variant="ghost" size="icon" className="h-7 w-7">
        <AlignCenter className="h-3.5 w-3.5" />
      </Button>
      <Button variant="ghost" size="icon" className="h-7 w-7">
        <AlignRight className="h-3.5 w-3.5" />
      </Button>
    </div>
  )
}
