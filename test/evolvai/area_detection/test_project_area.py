"""
测试ProjectArea数据类
"""

from evolvai.area_detection.data_models import ProjectArea


class TestProjectArea:
    """测试ProjectArea数据类"""

    def test_project_area_creation(self):
        """测试ProjectArea创建"""
        area = ProjectArea(name="backend-go", language="go", confidence="High", evidence=["go.mod", "cmd/"], file_patterns=["*.go"])

        assert area.name == "backend-go"
        assert area.language == "go"
        assert area.confidence == "High"
        assert "go.mod" in area.evidence
        assert "*.go" in area.file_patterns
        assert area.root_path is None

    def test_project_area_with_root_path(self):
        """测试带根路径的ProjectArea"""
        area = ProjectArea(
            name="frontend-ts",
            language="typescript",
            confidence="Medium",
            evidence=["package.json"],
            file_patterns=["*.ts", "*.tsx"],
            root_path="/tmp/project/frontend",
        )

        assert area.root_path == "/tmp/project/frontend"

    def test_project_area_evidence_list(self):
        """测试证据列表操作"""
        evidence = ["go.mod", "Makefile", "cmd/"]
        area = ProjectArea(name="go-project", language="go", confidence="High", evidence=evidence, file_patterns=["*.go"])

        # 验证证据可以被添加
        area.evidence.append("internal/")
        assert "internal/" in area.evidence
        assert len(area.evidence) == 4

    def test_project_area_file_patterns(self):
        """测试文件模式列表"""
        patterns = ["*.ts", "*.tsx", "*.js"]
        area = ProjectArea(
            name="typescript-project", language="typescript", confidence="High", evidence=["package.json"], file_patterns=patterns
        )

        # 验证模式可以被修改
        area.file_patterns.append("*.jsx")
        assert "*.jsx" in area.file_patterns
        assert len(area.file_patterns) == 4
