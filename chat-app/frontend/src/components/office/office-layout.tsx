"use client"

import { ArrowLeft, Save, Download, FileText, Table, Presentation } from "lucide-react"
import { Button } from "@/components/ui/button"

interface OfficeLayoutProps {
  fileId: number
  fileType: "document" | "spreadsheet" | "presentation"
  title: string
  onTitleChange?: (title: string) => void
  onBack: () => void
  onSave?: () => void
  onExport?: () => void
  saving?: boolean
  toolbar?: React.ReactNode
  children: React.ReactNode
}

function FileTypeIcon({ type }: { type: string }) {
  if (type === "document") return <FileText className="h-5 w-5 text-[#2564cf]" />
  if (type === "spreadsheet") return <Table className="h-5 w-5 text-green-600" />
  if (type === "presentation") return <Presentation className="h-5 w-5 text-orange-500" />
  return <FileText className="h-5 w-5" />
}

export function OfficeLayout({
  fileType,
  title,
  onTitleChange,
  onBack,
  onSave,
  onExport,
  saving = false,
  toolbar,
  children,
}: OfficeLayoutProps) {
  return (
    <div className="flex flex-col h-full bg-[#f3f3f3]">
      {/* Title bar */}
      <div className="flex items-center gap-3 px-4 py-2 bg-white border-b">
        <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={onBack}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <FileTypeIcon type={fileType} />
        <input
          value={title}
          onChange={(e) => onTitleChange?.(e.target.value)}
          className="flex-1 min-w-0 bg-transparent text-sm font-medium outline-none border-none focus:ring-0"
        />
        <div className="flex items-center gap-2 shrink-0">
          {saving && <span className="text-xs text-muted-foreground">保存中...</span>}
          <Button variant="ghost" size="sm" className="gap-1" onClick={onSave}>
            <Save className="h-4 w-4" />
            保存
          </Button>
          <Button variant="ghost" size="sm" className="gap-1" onClick={onExport}>
            <Download className="h-4 w-4" />
            导出
          </Button>
        </div>
      </div>

      {/* Toolbar */}
      {toolbar && <div className="bg-white border-b">{toolbar}</div>}

      {/* Canvas */}
      <div className="flex-1 overflow-auto flex justify-center p-8">{children}</div>
    </div>
  )
}
