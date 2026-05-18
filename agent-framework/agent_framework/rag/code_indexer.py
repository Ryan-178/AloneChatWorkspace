"""
Code Indexer - 代码库索引器
支持大型代码库的智能索引、增量更新、多语言解析
"""
import os
import hashlib
import json
import time
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import chromadb
from chromadb.config import Settings

from agent_framework.rag.local_embedding import LocalEmbeddingProvider, LocalEmbeddingConfig
from agent_framework.rag.splitter import RecursiveCharacterTextSplitter
from agent_framework.rag.loader import Document


class ProgrammingLanguage(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    C = "c"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    UNKNOWN = "unknown"


@dataclass
class CodeChunk:
    content: str
    file_path: str
    language: ProgrammingLanguage
    chunk_type: str
    name: Optional[str] = None
    start_line: int = 0
    end_line: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IndexStats:
    total_files: int = 0
    total_chunks: int = 0
    total_tokens: int = 0
    indexed_at: float = field(default_factory=time.time)
    languages: Dict[str, int] = field(default_factory=dict)
    file_hashes: Dict[str, str] = field(default_factory=dict)


class LanguageDetector:
    EXTENSION_MAP = {
        ".py": ProgrammingLanguage.PYTHON,
        ".js": ProgrammingLanguage.JAVASCRIPT,
        ".jsx": ProgrammingLanguage.JAVASCRIPT,
        ".ts": ProgrammingLanguage.TYPESCRIPT,
        ".tsx": ProgrammingLanguage.TYPESCRIPT,
        ".java": ProgrammingLanguage.JAVA,
        ".go": ProgrammingLanguage.GO,
        ".rs": ProgrammingLanguage.RUST,
        ".cpp": ProgrammingLanguage.CPP,
        ".cc": ProgrammingLanguage.CPP,
        ".cxx": ProgrammingLanguage.CPP,
        ".c": ProgrammingLanguage.C,
        ".h": ProgrammingLanguage.C,
        ".hpp": ProgrammingLanguage.CPP,
        ".kt": ProgrammingLanguage.KOTLIN,
        ".kts": ProgrammingLanguage.KOTLIN,
        ".swift": ProgrammingLanguage.SWIFT,
    }
    
    @classmethod
    def detect(cls, file_path: str) -> ProgrammingLanguage:
        ext = Path(file_path).suffix.lower()
        return cls.EXTENSION_MAP.get(ext, ProgrammingLanguage.UNKNOWN)


class CodeParser:
    """
    代码解析器 - 解析不同语言的代码结构
    Code Parser - Parse code structures for different languages
    """
    
    def __init__(self, max_chunk_size: int = 2000, chunk_overlap: int = 200):
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
    
    def parse_file(self, file_path: str) -> List[CodeChunk]:
        language = LanguageDetector.detect(file_path)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return []
        
        if language == ProgrammingLanguage.PYTHON:
            return self._parse_python(file_path, content)
        elif language in (ProgrammingLanguage.JAVASCRIPT, ProgrammingLanguage.TYPESCRIPT):
            return self._parse_js_ts(file_path, content, language)
        else:
            return self._parse_generic(file_path, content, language)
    
    def _parse_python(self, file_path: str, content: str) -> List[CodeChunk]:
        chunks = []
        lines = content.split("\n")
        
        try:
            import ast
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    chunk = self._extract_function_chunk(file_path, lines, node, "function")
                    if chunk:
                        chunks.append(chunk)
                elif isinstance(node, ast.ClassDef):
                    chunk = self._extract_class_chunk(file_path, lines, node)
                    if chunk:
                        chunks.append(chunk)
        except SyntaxError:
            pass
        
        if not chunks:
            chunks = self._chunk_by_lines(file_path, content, ProgrammingLanguage.PYTHON)
        
        return chunks
    
    def _extract_function_chunk(
        self, 
        file_path: str, 
        lines: List[str], 
        node: Any,
        chunk_type: str
    ) -> Optional[CodeChunk]:
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
        
        content = "\n".join(lines[start_line:end_line])
        
        if len(content) > self.max_chunk_size:
            content = content[:self.max_chunk_size]
        
        return CodeChunk(
            content=content,
            file_path=file_path,
            language=ProgrammingLanguage.PYTHON,
            chunk_type=chunk_type,
            name=node.name,
            start_line=start_line + 1,
            end_line=end_line,
            metadata={"lineno": node.lineno}
        )
    
    def _extract_class_chunk(
        self, 
        file_path: str, 
        lines: List[str], 
        node: Any
    ) -> Optional[CodeChunk]:
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
        
        content = "\n".join(lines[start_line:end_line])
        
        if len(content) > self.max_chunk_size:
            docstring_end = self._find_docstring_end(lines, start_line)
            method_lines = self._find_method_lines(node)
            important_lines = sorted(set([start_line, docstring_end] + method_lines[:5]))
            content = "\n".join(lines[start_line:min(important_lines[-1] + 20, end_line)])
        
        return CodeChunk(
            content=content,
            file_path=file_path,
            language=ProgrammingLanguage.PYTHON,
            chunk_type="class",
            name=node.name,
            start_line=start_line + 1,
            end_line=end_line,
            metadata={"lineno": node.lineno}
        )
    
    def _find_docstring_end(self, lines: List[str], start_line: int) -> int:
        for i in range(start_line + 1, min(start_line + 5, len(lines))):
            line = lines[i].strip()
            if line.startswith('"""') or line.startswith("'''"):
                return i
        return start_line
    
    def _find_method_lines(self, node: Any) -> List[int]:
        import ast
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.lineno - 1)
        return methods
    
    def _parse_js_ts(
        self, 
        file_path: str, 
        content: str, 
        language: ProgrammingLanguage
    ) -> List[CodeChunk]:
        return self._chunk_by_lines(file_path, content, language)
    
    def _parse_generic(
        self, 
        file_path: str, 
        content: str, 
        language: ProgrammingLanguage
    ) -> List[CodeChunk]:
        return self._chunk_by_lines(file_path, content, language)
    
    def _chunk_by_lines(
        self, 
        file_path: str, 
        content: str, 
        language: ProgrammingLanguage
    ) -> List[CodeChunk]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        doc = Document(content=content, source=file_path)
        split_docs = splitter.split_document(doc)
        
        return [
            CodeChunk(
                content=sd.content,
                file_path=file_path,
                language=language,
                chunk_type="code_block",
                metadata=sd.metadata
            )
            for sd in split_docs
        ]


class CodeIndexer:
    """
    代码库索引器
    支持大型代码库索引、增量更新、本地向量存储
    
    Code Indexer
    Supports large codebase indexing, incremental updates, local vector storage
    """
    
    IGNORE_DIRS = {
        "node_modules", "venv", ".venv", "env", ".env",
        "__pycache__", ".git", ".svn", ".hg",
        "dist", "build", "target", "out", "bin",
        ".idea", ".vscode", ".tox", ".pytest_cache",
        "migrations", "docs", "tests", "test",
    }
    
    IGNORE_EXTENSIONS = {
        ".lock", ".log", ".tmp", ".bak",
        ".pyc", ".pyo", ".pyd", ".so", ".dll",
        ".exe", ".bin", ".dat", ".db", ".sqlite",
        ".jpg", ".jpeg", ".png", ".gif", ".ico",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
        ".zip", ".tar", ".gz", ".rar",
    }
    
    def __init__(
        self,
        persist_path: str = "./code_index",
        embedding_config: Optional[LocalEmbeddingConfig] = None,
        collection_name: str = "codebase",
        max_file_size_mb: int = 10,
    ):
        self.persist_path = persist_path
        self.collection_name = collection_name
        self.max_file_size = max_file_size_mb * 1024 * 1024
        
        Path(persist_path).mkdir(parents=True, exist_ok=True)
        
        self.embedding = LocalEmbeddingProvider(embedding_config)
        self.parser = CodeParser()
        
        self._client = chromadb.PersistentClient(
            path=persist_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        self._stats = self._load_stats()
    
    def _load_stats(self) -> IndexStats:
        stats_file = Path(self.persist_path) / "index_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return IndexStats(**data)
            except Exception:
                pass
        return IndexStats()
    
    def _save_stats(self) -> None:
        stats_file = Path(self.persist_path) / "index_stats.json"
        try:
            with open(stats_file, "w", encoding="utf-8") as f:
                json.dump({
                    "total_files": self._stats.total_files,
                    "total_chunks": self._stats.total_chunks,
                    "total_tokens": self._stats.total_tokens,
                    "indexed_at": self._stats.indexed_at,
                    "languages": self._stats.languages,
                    "file_hashes": self._stats.file_hashes,
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _compute_file_hash(self, file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _should_index(self, file_path: str) -> bool:
        path = Path(file_path)
        
        for part in path.parts:
            if part in self.IGNORE_DIRS:
                return False
        
        if path.suffix.lower() in self.IGNORE_EXTENSIONS:
            return False
        
        try:
            if path.stat().st_size > self.max_file_size:
                return False
        except Exception:
            return False
        
        return True
    
    def _collect_files(self, root_path: str) -> List[str]:
        files = []
        root = Path(root_path)
        
        for file_path in root.rglob("*"):
            if file_path.is_file() and self._should_index(str(file_path)):
                files.append(str(file_path))
        
        return files
    
    def index_directory(
        self, 
        root_path: str, 
        incremental: bool = True,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        索引目录
        Index a directory
        """
        start_time = time.time()
        files = self._collect_files(root_path)
        
        new_files = []
        modified_files = []
        skipped_files = []
        
        for file_path in files:
            file_hash = self._compute_file_hash(file_path)
            stored_hash = self._stats.file_hashes.get(file_path)
            
            if incremental and stored_hash == file_hash:
                skipped_files.append(file_path)
            elif stored_hash is None:
                new_files.append(file_path)
            else:
                modified_files.append(file_path)
            
            self._stats.file_hashes[file_path] = file_hash
        
        files_to_index = new_files + modified_files
        
        if modified_files:
            self._remove_from_collection(modified_files)
        
        total_chunks = 0
        indexed_files = 0
        
        for i, file_path in enumerate(files_to_index):
            if show_progress and (i + 1) % 10 == 0:
                print(f"Indexing: {i + 1}/{len(files_to_index)} files")
            
            chunks = self.parser.parse_file(file_path)
            if not chunks:
                continue
            
            self._add_chunks_to_collection(chunks)
            total_chunks += len(chunks)
            indexed_files += 1
            
            lang = chunks[0].language.value
            self._stats.languages[lang] = self._stats.languages.get(lang, 0) + 1
        
        self._stats.total_files = len(self._stats.file_hashes)
        self._stats.total_chunks = self._collection.count()
        self._stats.indexed_at = time.time()
        self._save_stats()
        
        duration = time.time() - start_time
        
        return {
            "total_files_found": len(files),
            "new_files": len(new_files),
            "modified_files": len(modified_files),
            "skipped_files": len(skipped_files),
            "indexed_files": indexed_files,
            "total_chunks": total_chunks,
            "duration_seconds": duration,
        }
    
    def _add_chunks_to_collection(self, chunks: List[CodeChunk]) -> None:
        texts = [c.content for c in chunks]
        embeddings = self.embedding.embed(texts)
        
        ids = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(
                f"{chunk.file_path}:{chunk.start_line}:{chunk.end_line}".encode()
            ).hexdigest()[:16]
            ids.append(chunk_id)
            
            metadatas.append({
                "file_path": chunk.file_path,
                "language": chunk.language.value,
                "chunk_type": chunk.chunk_type,
                "name": chunk.name or "",
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
            })
        
        self._collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
    
    def _remove_from_collection(self, file_paths: List[str]) -> None:
        existing = self._collection.get()
        
        ids_to_remove = []
        for i, metadata in enumerate(existing["metadatas"]):
            if metadata.get("file_path") in file_paths:
                ids_to_remove.append(existing["ids"][i])
        
        if ids_to_remove:
            self._collection.delete(ids=ids_to_remove)
    
    def search(
        self, 
        query: str, 
        k: int = 10,
        language: Optional[ProgrammingLanguage] = None,
        file_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索代码
        Search code
        """
        query_embedding = self.embedding.embed_query(query)
        
        where_filter = None
        if language or file_path:
            conditions = []
            if language:
                conditions.append({"language": language.value})
            if file_path:
                conditions.append({"file_path": {"$contains": file_path}})
            
            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}
        
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "content": results["documents"][0][i],
                "score": 1 - results["distances"][0][i],
                "file_path": results["metadatas"][0][i].get("file_path", ""),
                "language": results["metadatas"][0][i].get("language", ""),
                "chunk_type": results["metadatas"][0][i].get("chunk_type", ""),
                "name": results["metadatas"][0][i].get("name", ""),
                "start_line": results["metadatas"][0][i].get("start_line", 0),
                "end_line": results["metadatas"][0][i].get("end_line", 0),
            })
        
        return output
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_files": self._stats.total_files,
            "total_chunks": self._stats.total_chunks,
            "total_tokens": self._stats.total_tokens,
            "indexed_at": self._stats.indexed_at,
            "languages": self._stats.languages,
            "embedding_dimension": self.embedding.get_dimension(),
        }
    
    def clear_index(self) -> None:
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self._stats = IndexStats()
        self._save_stats()
