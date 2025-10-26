"""
EvolvAI Smart Indexing System

高性能、缓存的文件和符号索引系统。
基于专家建议：持久化索引、增量更新、智能缓存策略。
"""

import hashlib
import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import subprocess
from datetime import datetime


@dataclass
class FileIndex:
    """文件索引信息"""
    path: str
    hash: str
    size: int
    mtime: float
    language: Optional[str] = None
    is_binary: bool = False
    is_ignored: bool = False


@dataclass
class SymbolIndex:
    """符号索引信息"""
    name: str
    file_path: str
    line: int
    column: int
    symbol_type: str  # function, class, variable, etc.
    language: str
    confidence: float = 1.0


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    content: str
    hash: str
    access_count: int = 0
    last_access: float = 0.0
    created_at: float = 0.0
    expires_at: Optional[float] = None


class SmartIndexingSystem:
    """智能索引系统"""

    def __init__(self, project_root: str, cache_dir: Optional[str] = None):
        self.project_root = Path(project_root)
        self.cache_dir = Path(cache_dir or self.project_root / ".evolvai" / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # SQLite 数据库
        self.db_path = self.cache_dir / "index.db"
        self._init_database()

        # 内存缓存
        self._file_cache: Dict[str, FileIndex] = {}
        self._symbol_cache: Dict[str, List[SymbolIndex]] = {}
        self._content_cache: Dict[str, CacheEntry] = {}

        # 配置
        self.max_cache_size = 1000
        self.cache_ttl = 3600  # 1小时
        self.indexing_threads = min(4, os.cpu_count() or 1)

        # 性能统计
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'index_time': 0.0,
            'search_time': 0.0,
        }

        # 文件监听器
        self._file_watcher = None
        self._last_index_time = 0.0

    def _init_database(self):
        """初始化 SQLite 数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    hash TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    mtime REAL NOT NULL,
                    language TEXT,
                    is_binary BOOLEAN,
                    is_ignored BOOLEAN,
                    indexed_at REAL DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS symbols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line INTEGER NOT NULL,
                    column INTEGER NOT NULL,
                    symbol_type TEXT NOT NULL,
                    language TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    indexed_at REAL DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(symbol_type)
            ''')

    def _get_file_hash(self, file_path: Path) -> str:
        """获取文件内容的哈希值"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except (OSError, PermissionError):
            return ""

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """检测文件语言"""
        ext = file_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
            '.kt': 'kotlin',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
        }
        return language_map.get(ext)

    def _is_binary_file(self, file_path: Path) -> bool:
        """检测是否为二进制文件"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except (OSError, PermissionError):
            return True

    def _should_ignore_file(self, file_path: Path) -> bool:
        """判断文件是否应该被忽略"""
        path_str = str(file_path)

        # 常见忽略目录
        ignore_dirs = {
            '.git', '.svn', '.hg',
            'node_modules', '__pycache__', '.pytest_cache',
            '.venv', 'venv', 'env',
            'build', 'dist', 'target', 'out',
            '.idea', '.vscode',
            'coverage', '.coverage',
        }

        # 常见忽略文件扩展名
        ignore_extensions = {
            '.pyc', '.pyo', '.pyd',
            '.so', '.dll', '.dylib',
            '.exe', '.app', '.dmg',
            '.log', '.tmp', '.swp',
        }

        # 检查路径
        parts = path_str.split('/')
        for part in parts:
            if part in ignore_dirs:
                return True

        # 检查扩展名
        if file_path.suffix.lower() in ignore_extensions:
            return True

        return False

    def index_file(self, file_path: Path) -> Optional[FileIndex]:
        """索引单个文件"""
        if self._should_ignore_file(file_path):
            return None

        try:
            stat = file_path.stat()
            file_hash = self._get_file_hash(file_path)
            language = self._detect_language(file_path)
            is_binary = self._is_binary_file(file_path)
            is_ignored = self._should_ignore_file(file_path)

            return FileIndex(
                path=str(file_path.relative_to(self.project_root)),
                hash=file_hash,
                size=stat.st_size,
                mtime=stat.st_mtime,
                language=language,
                is_binary=is_binary,
                is_ignored=is_ignored
            )
        except (OSError, PermissionError):
            return None

    def index_directory(self, max_files: Optional[int] = None,
                        parallel: bool = True) -> Tuple[int, float]:
        """索引目录"""
        start_time = time.time()

        # 收集文件
        all_files = list(self.project_root.rglob('*'))
        source_files = [
            f for f in all_files
            if f.is_file() and not self._should_ignore_file(f)
        ]

        if max_files:
            # 优先索引热点目录
            hot_dirs = {'src', 'lib', 'app', 'packages', 'components'}
            hot_files = []
            other_files = []

            for f in source_files:
                if any(part in hot_dirs for part in f.parts):
                    hot_files.append(f)
                else:
                    other_files.append(f)

            source_files = hot_files + other_files[:max_files - len(hot_files)]

        # 并行索引
        if parallel and len(source_files) > 10:
            indexed_count = self._index_files_parallel(source_files)
        else:
            indexed_count = self._index_files_sequential(source_files)

        index_time = time.time() - start_time
        self.stats['index_time'] += index_time
        self._last_index_time = time.time()

        return indexed_count, index_time

    def _index_files_parallel(self, files: List[Path]) -> int:
        """并行索引文件"""
        indexed_count = 0

        with ThreadPoolExecutor(max_workers=self.indexing_threads) as executor:
            future_to_file = {
                executor.submit(self.index_file, file): file
                for file in files
            }

            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    if result:
                        self._save_file_index(result)
                        indexed_count += 1
                except Exception as e:
                    print(f"Error indexing file: {e}")

        return indexed_count

    def _index_files_sequential(self, files: List[Path]) -> int:
        """顺序索引文件"""
        indexed_count = 0

        for file in files:
            try:
                result = self.index_file(file)
                if result:
                    self._save_file_index(result)
                    indexed_count += 1
            except Exception as e:
                print(f"Error indexing file {file}: {e}")

        return indexed_count

    def _save_file_index(self, file_index: FileIndex):
        """保存文件索引到数据库和内存"""
        # 保存到内存
        self._file_cache[file_index.path] = file_index

        # 保存到数据库
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO files
                (path, hash, size, mtime, language, is_binary, is_ignored)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_index.path, file_index.hash, file_index.size,
                file_index.mtime, file_index.language,
                file_index.is_binary, file_index.is_ignored
            ))

    def get_file_index(self, path: str) -> Optional[FileIndex]:
        """获取文件索引"""
        # 先查内存缓存
        if path in self._file_cache:
            return self._file_cache[path]

        # 再查数据库
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT path, hash, size, mtime, language, is_binary, is_ignored
                FROM files WHERE path = ?
            ''', (path,))

            row = cursor.fetchone()
            if row:
                file_index = FileIndex(*row)
                self._file_cache[path] = file_index
                return file_index

        return None

    def search_files(self, pattern: str, max_results: int = 100) -> List[FileIndex]:
        """搜索文件"""
        # 使用 ripgrep 进行高效搜索
        try:
            cmd = ['rg', '--files', '--max-count', str(max_results), pattern, str(self.project_root)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                files = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        rel_path = str(Path(line).relative_to(self.project_root))
                        file_index = self.get_file_index(rel_path)
                        if file_index:
                            files.append(file_index)

                return files
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # 降级到数据库搜索
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT path, hash, size, mtime, language, is_binary, is_ignored
                FROM files
                WHERE path LIKE ? AND is_binary = 0 AND is_ignored = 0
                LIMIT ?
            ''', (f'%{pattern}%', max_results))

            return [FileIndex(*row) for row in cursor.fetchall()]

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        hit_rate = (self.stats['cache_hits'] / total_requests * 100
                   if total_requests > 0 else 0)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM files')
            file_count = cursor.fetchone()[0]

            cursor = conn.execute('SELECT COUNT(*) FROM symbols')
            symbol_count = cursor.fetchone()[0]

        return {
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'cached_files': len(self._file_cache),
            'indexed_files': file_count,
            'indexed_symbols': symbol_count,
            'index_time_seconds': round(self.stats['index_time'], 2),
            'search_time_seconds': round(self.stats['search_time'], 2),
            'last_index_time': self._last_index_time,
        }