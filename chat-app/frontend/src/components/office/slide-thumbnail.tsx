"use client"

import { Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { SlideData } from "./slide-canvas"

interface SlideThumbnailProps {
  slides: SlideData[]
  activeIndex: number
  onSelect: (index: number) => void
  onAdd: () => void
  onDelete: (index: number) => void
}

const THUMB_WIDTH = 192
const THUMB_HEIGHT = 120

export function SlideThumbnail({ slides, activeIndex, onSelect, onAdd, onDelete }: SlideThumbnailProps) {
  return (
    <div className="w-48 bg-[#f3f3f3] border-r flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b">
        <span className="text-sm font-medium">幻灯片</span>
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onAdd}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {slides.map((slide, index) => {
          const isActive = activeIndex === index
          return (
            <div
              key={slide.id}
              className={`relative cursor-pointer rounded border-2 ${
                isActive ? "border-[#2564cf]" : "border-transparent hover:border-gray-300"
              }`}
              onClick={() => onSelect(index)}
            >
              <div
                className="bg-white mx-auto"
                style={{ width: THUMB_WIDTH - 16, height: THUMB_HEIGHT - 10 }}
              >
                {slide.elements.map((el) => (
                  <div
                    key={el.id}
                    className="absolute text-[6px] overflow-hidden"
                    style={{
                      left: (el.x / 960) * (THUMB_WIDTH - 16),
                      top: (el.y / 540) * (THUMB_HEIGHT - 10),
                      width: (el.width / 960) * (THUMB_WIDTH - 16),
                      height: (el.height / 540) * (THUMB_HEIGHT - 10),
                    }}
                  >
                    {el.content.slice(0, 20)}
                  </div>
                ))}
              </div>
              <div className="absolute top-0.5 right-0.5 opacity-0 hover:opacity-100 transition-opacity">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5 bg-white/80"
                  disabled={slides.length <= 1}
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(index)
                  }}
                >
                  <Trash2 className="h-3 w-3 text-muted-foreground hover:text-destructive" />
                </Button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
