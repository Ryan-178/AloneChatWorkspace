"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { FileText, Table, Presentation, Upload, Plus, ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { FileTree } from "./file-tree"
import {
  getAllLocalFiles,
  createLocalFile,
  deleteLocalFile,
  type LocalFile,
} from "@/lib/file-store"
import { fileApi } from "@/lib/file-api"

interface FileExplorerProps {
  onSelectFile: (id: number, fileType: "document" | "spreadsheet" | "presentation") => void
}

export function FileExplorer({ onSelectFile }: FileExplorerProps) {
  const [files, setFiles] = useState<LocalFile[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [showNewMenu, setShowNewMenu] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)

  const loadFiles = useCallback(async () => {
    const all = await getAllLocalFiles()
    setFiles(all)
  }, [])

  useEffect(() => {
    loadFiles()
  }, [loadFiles])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowNewMenu(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleCreate = async (fileType: "document" | "spreadsheet" | "presentation") => {
    const defaultNames: Record<string, string> = {
      document: "未命名文档.docx",
      spreadsheet: "未命名表格.xlsx",
      presentation: "未命名演示.pptx",
    }
    const defaultContents: Record<string, any> = {
      document: { type: "document", paragraphs: [{ text: "", runs: [], style: "Normal", alignment: null }] },
      spreadsheet: { type: "spreadsheet", sheets: [{ name: "Sheet1", cells: {} }], activeSheetIndex: 0 },
      presentation: { type: "presentation", slides: [{ id: "0", elements: [], background: null }], activeSlideIndex: 0 },
    }
    const id = await createLocalFile(defaultNames[fileType], fileType, defaultContents[fileType])
    await loadFiles()
    setSelectedId(id)
    onSelectFile(id, fileType)
    setShowNewMenu(false)
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const remote = await fileApi.upload(file)
      const fileType = remote.file_type as "document" | "spreadsheet" | "presentation"
      const content = remote.preview_data || {}
      const id = await createLocalFile(remote.filename, fileType, content)
      await loadFiles()
      setSelectedId(id)
      onSelectFile(id, fileType)
    } catch {
      // ignore
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const handleSelect = (id: number, fileType: string) => {
    setSelectedId(id)
    onSelectFile(id, fileType as any)
  }

  const handleDelete = async (id: number) => {
    await deleteLocalFile(id)
    if (selectedId === id) setSelectedId(null)
    await loadFiles()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-3 py-2 border-b">
        <div className="relative" ref={menuRef}>
          <Button
            variant="default"
            size="sm"
            className="gap-1 bg-[#2564cf] hover:bg-[#1e4fa3]"
            onClick={() => setShowNewMenu((v) => !v)}
          >
            <Plus className="h-4 w-4" />
            新建
            <ChevronDown className="h-3 w-3" />
          </Button>
          {showNewMenu && (
            <div className="absolute top-full left-0 mt-1 w-40 bg-popover border rounded-md shadow-lg z-50 py-1">
              <button
                className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent cursor-pointer"
                onClick={() => handleCreate("document")}
              >
                <FileText className="h-4 w-4 text-[#2564cf]" />
                文档
              </button>
              <button
                className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent cursor-pointer"
                onClick={() => handleCreate("spreadsheet")}
              >
                <Table className="h-4 w-4 text-green-600" />
                表格
              </button>
              <button
                className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent cursor-pointer"
                onClick={() => handleCreate("presentation")}
              >
                <Presentation className="h-4 w-4 text-orange-500" />
                演示
              </button>
            </div>
          )}
        </div>
        <Button variant="outline" size="sm" className="gap-1" onClick={() => fileInputRef.current?.click()}>
          <Upload className="h-4 w-4" />
          导入
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".docx,.xlsx,.pptx"
          className="hidden"
          onChange={handleImport}
        />
      </div>

      {/* File list */}
      <div className="flex-1 overflow-y-auto">
        <FileTree
          files={files}
          selectedId={selectedId}
          onSelect={handleSelect}
          onDelete={handleDelete}
        />
      </div>
    </div>
  )
}
