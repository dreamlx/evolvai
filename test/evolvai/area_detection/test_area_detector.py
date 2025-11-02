"""
测试AreaDetector的核心功能
"""

from unittest.mock import patch

from evolvai.area_detection.data_models import ProjectArea

# 导入我们要测试的类
from evolvai.area_detection.detector import AreaDetector


class TestAreaDetector:
    """测试AreaDetector的核心功能"""

    def test_sentinel_file_detection_go(self):
        """测试Go项目哨兵文件检测"""
        detector = AreaDetector("/tmp/test-go-project")

        # 模拟存在go.mod
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("os.listdir") as mock_listdir:
                mock_listdir.return_value = ["go.mod", "main.go"]

                areas = detector.detect_areas()

                go_area = next(area for area in areas if area.language == "go")
                assert "go.mod" in go_area.evidence
                assert go_area.confidence == "High"

    def test_sentinel_file_detection_ruby(self):
        """测试Ruby项目哨兵文件检测"""
        detector = AreaDetector("/tmp/test-ruby-project")

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("os.listdir") as mock_listdir:
                mock_listdir.return_value = ["Gemfile", "app", "config"]

                areas = detector.detect_areas()

                ruby_area = next(area for area in areas if area.language == "ruby")
                assert "Gemfile" in ruby_area.evidence
                assert ruby_area.confidence == "High"

    def test_mixed_project_detection(self):
        """测试混合项目检测 (Go+TS)"""
        detector = AreaDetector("/tmp/test-mixed-project")

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("os.listdir") as mock_listdir:
                # Simplified test: root directory has Go and TypeScript sentinel files
                mock_listdir.return_value = ["go.mod", "package.json", "main.go", "src"]

                areas = detector.detect_areas()

                # 应该检测到Go和TypeScript区域
                languages = [area.language for area in areas]
                assert "go" in languages
                assert "typescript" in languages

    def test_area_cache_mechanism(self):
        """测试区域检测缓存机制"""
        detector = AreaDetector("/tmp/test-project")

        # 首次调用
        with patch.object(detector, "_match_sentinel_files") as mock_match:
            mock_match.return_value = []

            areas1 = detector.detect_areas()
            assert mock_match.call_count == 1

            # 第二次调用应该命中缓存
            areas2 = detector.detect_areas()
            assert mock_match.call_count == 1  # 没有增加
            assert areas1 == areas2

    def test_lightweight_sampling(self):
        """测试轻量抽样统计"""
        detector = AreaDetector("/tmp/test-project")

        # 模拟抽样200个文件
        with patch.object(detector, "_lightweight_sampling") as mock_sampling:
            mock_sampling.return_value = [
                ProjectArea(
                    name="detected-python", language="python", confidence="Medium", evidence=["sampled 150 files"], file_patterns=["*.py"]
                )
            ]

            areas = detector.detect_areas(sample_limit=200)

            assert len(areas) == 1
            assert areas[0].language == "python"
            assert areas[0].confidence == "Medium"

    def test_sentinel_file_patterns(self):
        """测试各种语言的哨兵文件模式"""
        detector = AreaDetector("/tmp/test-various")

        # 测试TypeScript检测
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("os.listdir") as mock_listdir:
                mock_listdir.return_value = ["package.json", "tsconfig.json", "src"]

                areas = detector.detect_areas()

                ts_area = next(area for area in areas if area.language == "typescript")
                assert "package.json" in ts_area.evidence
                assert ts_area.confidence == "High"

    def test_no_sentinel_files_fallback(self):
        """测试无哨兵文件时的回退策略"""
        detector = AreaDetector("/tmp/test-no-sentinel")

        with patch.object(detector, "_match_sentinel_files") as mock_sentinel:
            mock_sentinel.return_value = []

            with patch.object(detector, "_lightweight_sampling") as mock_sampling:
                mock_sampling.return_value = [
                    ProjectArea(
                        name="fallback-area",
                        language="python",
                        confidence="Low",
                        evidence=["no sentinel files found"],
                        file_patterns=["*.py"],
                    )
                ]

                areas = detector.detect_areas()

                assert len(areas) == 1
                assert areas[0].confidence == "Low"

    def test_explicit_config_priority(self):
        """测试显式配置优先级"""
        # 模拟有显式配置的项目
        detector = AreaDetector("/tmp/test-explicit")

        with patch.object(detector, "_check_explicit_config") as mock_config:
            mock_config.return_value = [
                ProjectArea(
                    name="configured-go",
                    language="go",
                    confidence="VeryHigh",
                    evidence=["project.yml configuration"],
                    file_patterns=["*.go"],
                )
            ]

            areas = detector.detect_areas()

            # Should use explicit config, not check sentinel files
            assert len(areas) == 1
            assert areas[0].confidence == "VeryHigh"
            mock_config.assert_called_once()
