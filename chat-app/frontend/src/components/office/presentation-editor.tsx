"use client"

import { useEffect, useState, useCallback } from "react"
import { OfficeLayout } from "./office-layout"
import { SlideThumbnail } from "./slide-thumbnail"
import { SlideCanvas, type SlideData, type SlideElement } from "./slide-canvas"
import { PresentationToolbar } from "./presentation-toolbar"
import { getLocalFile, updateLocalFileContent, updateLocalFileName } from "@/lib/file-store"

interface PresentationEditorProps {
  fileId: number
  onBack: () => void
}

function generateId(): string {
  return Math.random().toString(36).slice(2, 9)
}

export function PresentationEditor({ fileId, onBack }: PresentationEditorProps) {
  const [title, setTitle] = useState("未命名演示")
  const [saving, setSaving] = useState(false)
  const [slides, setSlides] = useState<SlideData[]>([{ id: generateId(), elements: [], background: undefined }])
  const [activeIndex, setActiveIndex] = useState(0)

  useEffect(() => {
    let mounted = true
    async function load() {
      const file = await getLocalFile(fileId)
      if (!file || !mounted) return
      setTitle(file.filename)
      const content = file.content || {}
      if (content.slides?.length) {
        setSlides(content.slides)
        setActiveIndex(content.activeSlideIndex || 0)
      }
    }
    load()
    return () => { mounted = false }
  }, [fileId])

  const handleSave = useCallback(async (nextSlides?: SlideData[], nextIndex?: number) => {
    setSaving(true)
    await updateLocalFileContent(fileId, {
      type: "presentation",
      slides: nextSlides || slides,
      activeSlideIndex: nextIndex ?? activeIndex,
    })
    setTimeout(() => setSaving(false), 300)
  }, [slides, activeIndex, fileId])

  const handleSlideUpdate = useCallback((updated: SlideData) => {
    const next = slides.map((s, i) => (i === activeIndex ? updated : s))
    setSlides(next)
    handleSave(next, activeIndex)
  }, [slides, activeIndex, handleSave])

  const handleAddSlide = useCallback(() => {
    const next = [...slides, { id: generateId(), elements: [], background: undefined }]
    setSlides(next)
    setActiveIndex(next.length - 1)
    handleSave(next, next.length - 1)
  }, [slides, handleSave])

  const handleDeleteSlide = useCallback((index: number) => {
    if (slides.length <= 1) return
    const next = slides.filter((_, i) => i !== index)
    setSlides(next)
    const nextIndex = Math.min(activeIndex, next.length - 1)
    setActiveIndex(nextIndex)
    handleSave(next, nextIndex)
  }, [slides, activeIndex, handleSave])

  const handleAddText = useCallback(() => {
    const slide = slides[activeIndex]
    const el: SlideElement = {
      id: generateId(),
      type: "text",
      x: 100,
      y: 100,
      width: 200,
      height: 60,
      content: "双击编辑文本",
    }
    const nextSlide = { ...slide, elements: [...slide.elements, el] }
    handleSlideUpdate(nextSlide)
  }, [slides, activeIndex, handleSlideUpdate])

  const handleAddShape = useCallback(() => {
    const slide = slides[activeIndex]
    const el: SlideElement = {
      id: generateId(),
      type: "shape",
      x: 150,
      y: 150,
      width: 120,
      height: 120,
      content: "",
    }
    const nextSlide = { ...slide, elements: [...slide.elements, el] }
    handleSlideUpdate(nextSlide)
  }, [slides, activeIndex, handleSlideUpdate])

  const currentSlide = slides[activeIndex]

  return (
    <OfficeLayout
      fileId={fileId}
      fileType="presentation"
      title={title}
      onTitleChange={async (t) => { setTitle(t); await updateLocalFileName(fileId, t) }}
      onBack={onBack}
      onSave={() => handleSave()}
      saving={saving}
      toolbar={
        <PresentationToolbar onAddText={handleAddText} onAddShape={handleAddShape} />
      }
    >
      <div className="flex h-full">
        <SlideThumbnail
          slides={slides}
          activeIndex={activeIndex}
          onSelect={setActiveIndex}
          onAdd={handleAddSlide}
          onDelete={handleDeleteSlide}
        />
        <div className="flex-1 overflow-auto">
          {currentSlide && (
            <SlideCanvas slide={currentSlide} onUpdate={handleSlideUpdate} />
          )}
        </div>
      </div>
    </OfficeLayout>
  )
}
