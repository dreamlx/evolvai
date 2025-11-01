"""
区域检测器 - 零成本混合项目区域检测
"""

import os
from pathlib import Path
from typing import Optional

from .data_models import ProjectArea


class AreaDetector:
    """零成本混合项目区域检测"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.cache = {}  # 缓存检测结果

    def detect_areas(self, sample_limit: int = 200) -> list[ProjectArea]:
        """多层检测管道，O(1)到O(小文件数)"""
        # 1. 检查缓存
        cache_key = f"{self.project_root}:{sample_limit}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        areas = []

        # 1. 显式配置优先 (Project.language)
        if explicit_config := self._check_explicit_config():
            areas = explicit_config
        # 2. 哨兵文件匹配 (go.mod, package.json, Gemfile等)
        elif sentinel_areas := self._match_sentinel_files():
            areas = sentinel_areas
        # 3. 轻量抽样统计 (N≤200, 跳过大目录)
        else:
            areas = self._lightweight_sampling(sample_limit)

        # 缓存结果
        self.cache[cache_key] = areas
        return areas

    def _check_explicit_config(self) -> Optional[list[ProjectArea]]:
        """检查显式配置（未来扩展点）"""
        # TODO: 实现项目配置文件检查
        # 例如: .project.yml, pyproject.toml配置等
        return None

    def _match_sentinel_files(self) -> Optional[list[ProjectArea]]:
        """哨兵文件检测，近乎零开销"""
        sentinel_patterns = {
            # Go: go.mod, Makefile, CMakeLists.txt, src/, internal/, cmd/
            "go": ["go.mod", "Makefile", "CMakeLists.txt", "src", "internal", "cmd"],
            # Ruby: Gemfile, *.gemspec, Rakefile, .ruby-version
            "ruby": ["Gemfile", "Rakefile", ".ruby-version"],
            # TypeScript: package.json, tsconfig.json
            "typescript": ["package.json", "tsconfig.json"],
            # Python: pyproject.toml, requirements.txt, setup.py
            "python": ["pyproject.toml", "requirements.txt", "setup.py"],
        }

        detected_areas = []
        project_root = Path(self.project_root)

        # 检查根目录的哨兵文件
        root_files = []
        try:
            root_files = os.listdir(project_root)
        except (OSError, PermissionError):
            return None

        root_files_set = set(root_files)

        for language, sentinel_files in sentinel_patterns.items():
            evidence = []

            # 检查每个哨兵文件
            for sentinel in sentinel_files:
                if sentinel.startswith("*."):
                    # Handle glob patterns, like *.gemspec
                    import glob

                    matches = glob.glob(str(project_root / sentinel))
                    if matches:
                        evidence.extend([os.path.basename(match) for match in matches])
                elif sentinel in root_files_set:
                    # 检查普通文件/目录
                    evidence.append(sentinel)

            if evidence:
                # 根据检测到的文件确定文件模式
                file_patterns = self._get_file_patterns_for_language(language)

                area = ProjectArea(
                    name=f"{language}-area",
                    language=language,
                    confidence="High",
                    evidence=evidence,
                    file_patterns=file_patterns,
                    root_path=str(project_root),
                )
                detected_areas.append(area)

        # Check subdirectories (for mixed projects)
        subdirectory_areas = self._check_subdirectory_sentinels(project_root, sentinel_patterns)
        detected_areas.extend(subdirectory_areas)

        return detected_areas if detected_areas else None

    def _check_subdirectory_sentinels(self, project_root: Path, sentinel_patterns: dict) -> list[ProjectArea]:
        """检查子目录中的哨兵文件（用于混合项目）"""
        areas = []

        try:
            for item in project_root.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    # 检查子目录中的哨兵文件
                    sub_files = []
                    try:
                        sub_files = os.listdir(item)
                    except (OSError, PermissionError):
                        continue

                    sub_files_set = set(sub_files)

                    for language, sentinel_files in sentinel_patterns.items():
                        evidence = []

                        for sentinel in sentinel_files:
                            if sentinel.startswith("*."):
                                import glob

                                matches = glob.glob(str(item / sentinel))
                                if matches:
                                    evidence.extend([os.path.basename(match) for match in matches])
                            elif sentinel in sub_files_set:
                                evidence.append(sentinel)

                        if evidence:
                            file_patterns = self._get_file_patterns_for_language(language)

                            area = ProjectArea(
                                name=f"{language}-{item.name}",
                                language=language,
                                confidence="High",
                                evidence=evidence,
                                file_patterns=file_patterns,
                                root_path=str(item),
                            )
                            areas.append(area)
                            break  # 每个目录只匹配一种语言
        except (OSError, PermissionError):
            pass

        return areas

    def _get_file_patterns_for_language(self, language: str) -> list[str]:
        """获取语言对应的文件模式"""
        patterns = {
            "go": ["*.go"],
            "ruby": ["*.rb", "*.erb"],
            "typescript": ["*.ts", "*.tsx"],
            "python": ["*.py"],
        }
        return patterns.get(language, [f"*.{language}"])

    def _lightweight_sampling(self, sample_limit: int = 200) -> list[ProjectArea]:
        """轻量抽样统计（当哨兵文件检测失败时的回退方案）"""
        # Simplified implementation: detect based on common file extensions
        language_extensions = {
            "go": [".go"],
            "python": [".py"],
            "typescript": [".ts", ".tsx"],
            "ruby": [".rb"],
            "javascript": [".js", ".jsx"],
        }

        language_counts = dict.fromkeys(language_extensions, 0)
        total_files = 0

        try:
            project_root = Path(self.project_root)
            for root, dirs, files in os.walk(project_root):
                # 跳过大目录和隐藏目录
                dirs[:] = [
                    d for d in dirs if not d.startswith(".") and d not in ["node_modules", "vendor", "target", "build", "__pycache__"]
                ]

                for file in files:
                    if total_files >= sample_limit:
                        break

                    file_ext = os.path.splitext(file)[1].lower()
                    for lang, extensions in language_extensions.items():
                        if file_ext in extensions:
                            language_counts[lang] += 1
                            total_files += 1
                            break

                if total_files >= sample_limit:
                    break
        except (OSError, PermissionError):
            pass

        # 创建区域检测结果
        areas = []
        for lang, count in language_counts.items():
            if count > 0:
                confidence = "High" if count > 10 else "Medium" if count > 3 else "Low"
                patterns = self._get_file_patterns_for_language(lang)

                area = ProjectArea(
                    name=f"detected-{lang}",
                    language=lang,
                    confidence=confidence,
                    evidence=[f"sampled {count} files"],
                    file_patterns=patterns,
                    root_path=self.project_root,
                )
                areas.append(area)

        return (
            areas
            if areas
            else [
                ProjectArea(
                    name="unknown-area",
                    language="unknown",
                    confidence="Low",
                    evidence=["no recognizable files found"],
                    file_patterns=["*"],
                    root_path=self.project_root,
                )
            ]
        )
