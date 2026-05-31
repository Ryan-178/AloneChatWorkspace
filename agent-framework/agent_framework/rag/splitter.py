from typing import List, Optional

from agent_framework.rag.loader import Document


class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, separators: Optional[List[str]] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        if not text or len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            if end >= len(text):
                chunks.append(text[start:])
                break

            split_pos = end
            for sep in self.separators:
                pos = text.rfind(sep, start, end)
                if pos > start:
                    split_pos = pos + len(sep)
                    break

            chunk = text[start:split_pos]
            chunks.append(chunk)
            start = split_pos - self.chunk_overlap
            if start <= 0:
                start = split_pos
            if start >= len(text):
                break

        return chunks

    def split_document(self, document: Document) -> List[Document]:
        chunks = self.split_text(document.content)
        return [
            Document(
                content=chunk,
                source=document.source,
                metadata={
                    **document.metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            )
            for i, chunk in enumerate(chunks)
        ]
