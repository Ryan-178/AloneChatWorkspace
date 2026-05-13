"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import { OfficeLayout } from "./office-layout"
import { SpreadsheetToolbar } from "./spreadsheet-toolbar"
import { getLocalFile, updateLocalFileContent, updateLocalFileName } from "@/lib/file-store"

interface SpreadsheetEditorProps {
  fileId: number
  onBack: () => void
}

const COL_COUNT = 26
const ROW_COUNT = 100
const COL_WIDTH = 100
const ROW_HEIGHT = 28
const HEADER_COL_WIDTH = 50

function getColLabel(index: number): string {
  return String.fromCharCode(65 + index)
}

function getCellAddress(row: number, col: number): string {
  return `${getColLabel(col)}${row + 1}`
}

function parseAddress(addr: string): { row: number; col: number } | null {
  const match = addr.match(/^([A-Z]+)(\d+)$/)
  if (!match) return null
  const col = match[1].charCodeAt(0) - 65
  const row = parseInt(match[2], 10) - 1
  if (row < 0 || row >= ROW_COUNT || col < 0 || col >= COL_COUNT) return null
  return { row, col }
}

export function SpreadsheetEditor({ fileId, onBack }: SpreadsheetEditorProps) {
  const [title, setTitle] = useState("未命名表格")
  const [saving, setSaving] = useState(false)
  const [cells, setCells] = useState<Record<string, string>>({})
  const [formulas, setFormulas] = useState<Record<string, string>>({})
  const [selected, setSelected] = useState<{ row: number; col: number } | null>(null)
  const [editing, setEditing] = useState<{ row: number; col: number } | null>(null)
  const [editValue, setEditValue] = useState("")
  const [boldSet, setBoldSet] = useState<Set<string>>(new Set())
  const [italicSet, setItalicSet] = useState<Set<string>>(new Set())
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let mounted = true
    async function load() {
      const file = await getLocalFile(fileId)
      if (!file || !mounted) return
      setTitle(file.filename)
      const content = file.content || {}
      const sheet = content.sheets?.[content.activeSheetIndex || 0]
      if (sheet?.cells) {
        const vals: Record<string, string> = {}
        const fmls: Record<string, string> = {}
        for (const [addr, data] of Object.entries(sheet.cells)) {
          const d = data as any
          vals[addr] = d.value || ""
          if (d.formula) fmls[addr] = d.formula
        }
        setCells(vals)
        setFormulas(fmls)
      }
    }
    load()
    return () => { mounted = false }
  }, [fileId])

  const evaluateFormula = useCallback((formula: string, currentCells: Record<string, string>): string => {
    if (!formula.startsWith("=")) return formula
    const expr = formula.slice(1)
    const safeExpr = expr.replace(/([A-Z]+\d+)/g, (match) => {
      const addr = match.toUpperCase()
      const val = parseFloat(currentCells[addr] || "0")
      return String(isNaN(val) ? 0 : val)
    })
    try {
      const result = new Function(`return (${safeExpr})`)()
      return String(result)
    } catch {
      return "#ERROR"
    }
  }, [])

  const getDisplayValue = useCallback((row: number, col: number, currentCells?: Record<string, string>): string => {
    const addr = getCellAddress(row, col)
    const cs = currentCells || cells
    const formula = formulas[addr]
    if (formula) {
      return evaluateFormula(formula, cs)
    }
    return cs[addr] || ""
  }, [cells, formulas, evaluateFormula])

  const handleSave = useCallback(async (nextCells?: Record<string, string>, nextFormulas?: Record<string, string>) => {
    setSaving(true)
    const cs = nextCells || cells
    const fs = nextFormulas || formulas
    const sheetCells: Record<string, any> = {}
    const allAddrs = new Set([...Object.keys(cs), ...Object.keys(fs)])
    for (const addr of allAddrs) {
      sheetCells[addr] = {
        value: cs[addr] || "",
        formula: fs[addr] || null,
      }
    }
    await updateLocalFileContent(fileId, {
      type: "spreadsheet",
      sheets: [{ name: "Sheet1", cells: sheetCells }],
      activeSheetIndex: 0,
    })
    setTimeout(() => setSaving(false), 300)
  }, [cells, formulas, fileId])

  const handleCellClick = (row: number, col: number) => {
    setSelected({ row, col })
    setEditing(null)
  }

  const handleCellDoubleClick = (row: number, col: number) => {
    const addr = getCellAddress(row, col)
    setEditing({ row, col })
    setEditValue(formulas[addr] || cells[addr] || "")
    setTimeout(() => inputRef.current?.focus(), 0)
  }

  const commitEdit = useCallback(() => {
    if (!editing) return
    const addr = getCellAddress(editing.row, editing.col)
    const nextCells = { ...cells }
    const nextFormulas = { ...formulas }
    if (editValue.startsWith("=")) {
      nextFormulas[addr] = editValue
      nextCells[addr] = evaluateFormula(editValue, nextCells)
    } else {
      delete nextFormulas[addr]
      nextCells[addr] = editValue
    }
    setCells(nextCells)
    setFormulas(nextFormulas)
    setEditing(null)
    handleSave(nextCells, nextFormulas)
  }, [editing, editValue, cells, formulas, evaluateFormula, handleSave])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (editing) {
      if (e.key === "Enter") {
        e.preventDefault()
        commitEdit()
      } else if (e.key === "Escape") {
        setEditing(null)
      }
      return
    }
    if (!selected) return
    const { row, col } = selected
    if (e.key === "ArrowUp") {
      e.preventDefault()
      setSelected({ row: Math.max(0, row - 1), col })
    } else if (e.key === "ArrowDown") {
      e.preventDefault()
      setSelected({ row: Math.min(ROW_COUNT - 1, row + 1), col })
    } else if (e.key === "ArrowLeft") {
      e.preventDefault()
      setSelected({ row, col: Math.max(0, col - 1) })
    } else if (e.key === "ArrowRight") {
      e.preventDefault()
      setSelected({ row, col: Math.min(COL_COUNT - 1, col + 1) })
    } else if (e.key === "Enter") {
      e.preventDefault()
      handleCellDoubleClick(row, col)
    } else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
      setEditing({ row, col })
      setEditValue(e.key)
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }

  const toggleBold = () => {
    if (!selected) return
    const addr = getCellAddress(selected.row, selected.col)
    const next = new Set(boldSet)
    if (next.has(addr)) next.delete(addr)
    else next.add(addr)
    setBoldSet(next)
  }

  const toggleItalic = () => {
    if (!selected) return
    const addr = getCellAddress(selected.row, selected.col)
    const next = new Set(italicSet)
    if (next.has(addr)) next.delete(addr)
    else next.add(addr)
    setItalicSet(next)
  }

  const selectedAddr = selected ? getCellAddress(selected.row, selected.col) : ""
  const selectedValue = selected ? (formulas[selectedAddr] || cells[selectedAddr] || "") : ""

  return (
    <OfficeLayout
      fileId={fileId}
      fileType="spreadsheet"
      title={title}
      onTitleChange={async (t) => { setTitle(t); await updateLocalFileName(fileId, t) }}
      onBack={onBack}
      onSave={() => handleSave()}
      saving={saving}
      toolbar={
        <SpreadsheetToolbar
          onBold={toggleBold}
          onItalic={toggleItalic}
          isBold={selected ? boldSet.has(selectedAddr) : false}
          isItalic={selected ? italicSet.has(selectedAddr) : false}
        />
      }
    >
      <div className="flex flex-col w-full h-full bg-white" onKeyDown={handleKeyDown} tabIndex={0} ref={containerRef}>
        {/* Formula bar */}
        <div className="flex items-center gap-2 px-3 py-1.5 border-b bg-[#f8f8f8]">
          <span className="text-xs font-mono text-muted-foreground w-12 text-right">{selectedAddr || ""}</span>
          <span className="text-xs text-muted-foreground">fx</span>
          <input
            value={editing ? editValue : selectedValue}
            onChange={(e) => { if (editing) setEditValue(e.target.value) }}
            onBlur={commitEdit}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitEdit()
              if (e.key === "Escape") setEditing(null)
            }}
            className="flex-1 text-sm bg-white border rounded px-2 py-0.5 outline-none"
            readOnly={!editing}
          />
        </div>

        {/* Grid */}
        <div className="flex-1 overflow-auto">
          <div
            className="grid"
            style={{
              gridTemplateColumns: `${HEADER_COL_WIDTH}px repeat(${COL_COUNT}, ${COL_WIDTH}px)`,
              gridTemplateRows: `${ROW_HEIGHT}px repeat(${ROW_COUNT}, ${ROW_HEIGHT}px)`,
            }}
          >
            {/* Corner */}
            <div className="sticky top-0 left-0 z-20 bg-[#f3f3f3] border-r border-b" />

            {/* Column headers */}
            {Array.from({ length: COL_COUNT }).map((_, col) => (
              <div
                key={`col-${col}`}
                className="sticky top-0 z-10 bg-[#f3f3f3] border-r border-b flex items-center justify-center text-xs text-muted-foreground"
              >
                {getColLabel(col)}
              </div>
            ))}

            {/* Rows */}
            {Array.from({ length: ROW_COUNT }).map((_, row) => (
              <div key={`row-${row}`} className="contents">
                {/* Row header */}
                <div className="sticky left-0 z-10 bg-[#f3f3f3] border-r border-b flex items-center justify-center text-xs text-muted-foreground">
                  {row + 1}
                </div>
                {/* Cells */}
                {Array.from({ length: COL_COUNT }).map((_, col) => {
                  const addr = getCellAddress(row, col)
                  const isSelected = selected?.row === row && selected?.col === col
                  const isEditing = editing?.row === row && editing?.col === col
                  const display = getDisplayValue(row, col)
                  const isBold = boldSet.has(addr)
                  const isItalic = italicSet.has(addr)
                  return (
                    <div
                      key={addr}
                      className={`border-r border-b relative text-sm px-1 flex items-center overflow-hidden whitespace-nowrap ${
                        isSelected ? "ring-2 ring-[#2564cf] ring-inset z-10" : ""
                      }`}
                      style={{
                        fontWeight: isBold ? "bold" : "normal",
                        fontStyle: isItalic ? "italic" : "normal",
                      }}
                      onClick={() => handleCellClick(row, col)}
                      onDoubleClick={() => handleCellDoubleClick(row, col)}
                    >
                      {isEditing ? (
                        <input
                          ref={inputRef}
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onBlur={commitEdit}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") commitEdit()
                            if (e.key === "Escape") setEditing(null)
                          }}
                          className="absolute inset-0 w-full h-full px-1 outline-none border-2 border-[#2564cf]"
                        />
                      ) : (
                        display
                      )}
                    </div>
                  )
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </OfficeLayout>
  )
}
