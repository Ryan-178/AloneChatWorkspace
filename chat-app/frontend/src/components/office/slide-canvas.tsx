"use client"

import { useState, useRef, useCallback } from "react"

export interface SlideElement {
  id: string
  type: "text" | "shape"
  x: number
  y: number
  width: number
  height: number
  content: string
}

export interface SlideData {
  id: string
  elements: SlideElement[]
  background?: string
}

interface SlideCanvasProps {
  slide: SlideData
  onUpdate: (slide: SlideData) => void
}

const CANVAS_WIDTH = 960
const CANVAS_HEIGHT = 540

export function SlideCanvas({ slide, onUpdate }: SlideCanvasProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editText, setEditText] = useState("")
  const [dragging, setDragging] = useState<{ id: string; offsetX: number; offsetY: number } | null>(null)
  const canvasRef = useRef<HTMLDivElement>(null)

  const updateElement = useCallback((id: string, patch: Partial<SlideElement>) => {
    const next = {
      ...slide,
      elements: slide.elements.map((el) => (el.id === id ? { ...el, ...patch } : el)),
    }
    onUpdate(next)
  }, [slide, onUpdate])

  const handleCanvasClick = (e: React.MouseEvent) => {
    if (e.target === canvasRef.current) {
      setSelectedId(null)
      setEditingId(null)
    }
  }

  const handleMouseDown = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    const el = slide.elements.find((x) => x.id === id)
    if (!el) return
    const rect = canvasRef.current!.getBoundingClientRect()
    const offsetX = e.clientX - rect.left - el.x
    const offsetY = e.clientY - rect.top - el.y
    setSelectedId(id)
    setDragging({ id, offsetX, offsetY })
  }

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragging || !canvasRef.current) return
    const rect = canvasRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left - dragging.offsetX
    const y = e.clientY - rect.top - dragging.offsetY
    updateElement(dragging.id, {
      x: Math.max(0, Math.min(CANVAS_WIDTH - 50, x)),
      y: Math.max(0, Math.min(CANVAS_HEIGHT - 20, y)),
    })
  }, [dragging, updateElement])

  const handleMouseUp = useCallback(() => {
    setDragging(null)
  }, [])

  const handleDoubleClick = (id: string) => {
    const el = slide.elements.find((x) => x.id === id)
    if (!el) return
    setEditingId(id)
    setEditText(el.content)
  }

  const commitEdit = () => {
    if (!editingId) return
    updateElement(editingId, { content: editText })
    setEditingId(null)
  }

  return (
    <div className="flex items-center justify-center bg-[#f3f3f3] p-8" style={{ minHeight: "100%" }}>
      <div
        ref={canvasRef}
        className="relative bg-white shadow-lg"
        style={{ width: CANVAS_WIDTH, height: CANVAS_HEIGHT }}
        onClick={handleCanvasClick}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {slide.elements.map((el) => {
          const isSelected = selectedId === el.id
          const isEditing = editingId === el.id
          return (
            <div
              key={el.id}
              className={`absolute cursor-move ${isSelected ? "ring-2 ring-[#2564cf]" : ""}`}
              style={{
                left: el.x,
                top: el.y,
                width: el.width,
                height: el.height,
              }}
              onMouseDown={(e) => handleMouseDown(e, el.id)}
              onDoubleClick={() => handleDoubleClick(el.id)}
            >
              {isEditing ? (
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  onBlur={commitEdit}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault()
                      commitEdit()
                    }
                  }}
                  className="w-full h-full resize-none outline-none border-2 border-[#2564cf] p-1 text-sm"
                  autoFocus
                />
              ) : (
                <div className="w-full h-full p-1 text-sm overflow-hidden whitespace-pre-wrap">
                  {el.content}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
