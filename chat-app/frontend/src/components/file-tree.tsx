"use client"

import { FileText, Table, Presentation, MoreVertical, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { LocalFile } from "@/lib/file-store"

interface FileTreeProps {
  files: LocalFile[]
  selectedId: number | null
  onSelect: (id: number, fileType: string) => void
  onDelete: (id: number) => void
}

function getFileIcon(fileType: string) {
  if (fileType === "document") return <FileText className="h-4 w-4 text-[#2564cf]" />
  if (fileType === "spreadsheet") return <Table className="h-4 w-4 text-green-600" />
  if (fileType === "presentation") return <Presentation className="h-4 w-4 text-orange-500" />
  return <FileText className="h-4 w-4 text-muted-foreground" />
}

function formatTime(ts: number): string {
  const d = new Date(ts)
  return d.toLocaleString("zh-CN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
}

export function FileTree({ files, selectedId, onSelect, onDelete }: FileTreeProps) {
  if (files.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground text-sm px-4 text-center">
        暂无文件<br />点击上方新建或导入
      </div>
    )
  }

  return (
    <div className="flex flex-col">
      {files.map((file) => {
        const id = file.id!
        const isSelected = selectedId === id
        return (
          <div
            key={id}
            onClick={() => onSelect(id, file.fileType)}
            className={`group flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors ${
              isSelected ? "bg-accent" : "hover:bg-accent/50"
            }`}
          >
            {getFileIcon(file.fileType)}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{file.filename}</p>
              <p className="text-xs text-muted-foreground">{formatTime(file.updatedAt)}</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              onClick={(e) => {
                e.stopPropagation()
                onDelete(id)
              }}
            >
              <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive" />
            </Button>
          </div>
        )
      })}
    </div>
  )
}
