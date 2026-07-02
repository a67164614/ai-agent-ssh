from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.schemas.deployment import DeploymentPlan, DeploymentStep


@dataclass(frozen=True)
class ProjectAnalysisResult:
    detected_type: str
    summary: str
    target_path: str
    manifests: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    start_commands: list[str] = field(default_factory=list)
    file_tree: list[str] = field(default_factory=list)
    package_scripts: dict[str, str] = field(default_factory=dict)


def analyze_project_directory(directory: Path, *, target_path: str) -> ProjectAnalysisResult:
    if not directory.exists() or not directory.is_dir():
        raise ValueError("待分析目录不存在。")

    files = sorted(path for path in directory.rglob("*") if path.is_file())
    relative_files = [_relative_name(directory, path) for path in files[:200]]
    names = {Path(name).name for name in relative_files}
    manifests = [name for name in relative_files if Path(name).name in _KNOWN_MANIFESTS or name.endswith(".jar")]
    package_scripts = _read_package_scripts(directory / "package.json") if "package.json" in names else {}
    detected_type = _detect_type(names, relative_files)
    dependencies, start_commands = _recommend_runtime(detected_type, package_scripts)

    return ProjectAnalysisResult(
        detected_type=detected_type,
        summary=_summary_for_type(detected_type),
        target_path=target_path,
        manifests=manifests,
        dependencies=dependencies,
        start_commands=start_commands,
        file_tree=relative_files,
        package_scripts=package_scripts,
    )


def build_deployment_plan(analysis: ProjectAnalysisResult) -> DeploymentPlan:
    workdir = analysis.target_path
    steps: list[DeploymentStep]
    if analysis.detected_type == "docker":
        steps = [DeploymentStep(name="启动 Docker Compose 服务", command="docker compose up -d", working_directory=workdir)]
    elif analysis.detected_type == "node":
        steps = [DeploymentStep(name="安装依赖", command="npm install", working_directory=workdir)]
        if "build" in analysis.package_scripts:
            steps.append(DeploymentStep(name="构建服务", command="npm run build", working_directory=workdir))
        start_command = "npm run start" if "start" in analysis.package_scripts else "node server.js"
        steps.append(DeploymentStep(name="启动服务", command=start_command, working_directory=workdir))
    elif analysis.detected_type == "python":
        steps = [
            DeploymentStep(name="创建虚拟环境", command="python3 -m venv .venv", working_directory=workdir),
            DeploymentStep(name="安装依赖", command=".venv/bin/pip install -r requirements.txt", working_directory=workdir),
            DeploymentStep(name="启动服务", command=".venv/bin/python main.py", working_directory=workdir),
        ]
    elif analysis.detected_type == "java":
        steps = [DeploymentStep(name="启动 Jar 服务", command="java -jar *.jar", working_directory=workdir)]
    elif analysis.detected_type == "go":
        steps = [
            DeploymentStep(name="构建 Go 服务", command="go build -o app", working_directory=workdir),
            DeploymentStep(name="启动 Go 服务", command="./app", working_directory=workdir),
        ]
    elif analysis.detected_type == "static":
        steps = [DeploymentStep(name="校验静态站点文件", command="ls -lah", working_directory=workdir)]
    else:
        steps = [DeploymentStep(name="查看项目文件", command="ls -lah", working_directory=workdir)]

    return DeploymentPlan(
        summary=f"{analysis.summary}，建议先确认命令和目标目录后执行。",
        risk_level="medium" if analysis.detected_type in {"docker", "node", "python", "java", "go"} else "low",
        requires_sudo=False,
        steps=steps,
    )


def result_to_dict(analysis: ProjectAnalysisResult) -> dict[str, object]:
    return {
        "detected_type": analysis.detected_type,
        "summary": analysis.summary,
        "target_path": analysis.target_path,
        "manifests": analysis.manifests,
        "dependencies": analysis.dependencies,
        "start_commands": analysis.start_commands,
        "file_tree": analysis.file_tree,
    }


def result_json_parts(analysis: ProjectAnalysisResult, plan: DeploymentPlan) -> dict[str, str]:
    return {
        "dependencies_json": json.dumps(analysis.dependencies, ensure_ascii=False),
        "start_commands_json": json.dumps(analysis.start_commands, ensure_ascii=False),
        "file_tree_json": json.dumps(analysis.file_tree, ensure_ascii=False),
        "deploy_plan_json": json.dumps(plan.model_dump(), ensure_ascii=False),
    }


_KNOWN_MANIFESTS = {
    "README.md",
    "readme.md",
    "package.json",
    "pom.xml",
    "build.gradle",
    "requirements.txt",
    "pyproject.toml",
    "go.mod",
    "Dockerfile",
    "docker-compose.yml",
    "compose.yml",
    "application.yml",
    ".env.example",
    "index.html",
    "nginx.conf",
}


def _detect_type(names: set[str], relative_files: list[str]) -> str:
    if {"docker-compose.yml", "compose.yml"} & names or "Dockerfile" in names:
        return "docker"
    if any(name.endswith(".jar") for name in relative_files) or {"pom.xml", "build.gradle", "application.yml"} & names:
        return "java"
    if "package.json" in names:
        return "node"
    if {"requirements.txt", "pyproject.toml", "app.py", "main.py", "manage.py"} & names:
        return "python"
    if {"go.mod", "main.go"} & names:
        return "go"
    if "index.html" in names or "nginx.conf" in names or any(name.startswith(("dist/", "build/")) for name in relative_files):
        return "static"
    return "unknown"


def _recommend_runtime(detected_type: str, package_scripts: dict[str, str]) -> tuple[list[str], list[str]]:
    if detected_type == "docker":
        return ["Docker", "Docker Compose"], ["docker compose up -d"]
    if detected_type == "node":
        commands = ["npm run start" if "start" in package_scripts else "node server.js"]
        if "build" in package_scripts:
            commands.insert(0, "npm run build")
        return ["Node.js", "npm"], commands
    if detected_type == "python":
        return ["Python 3", "venv", "pip"], ["python main.py"]
    if detected_type == "java":
        return ["JRE 或 JDK"], ["java -jar *.jar"]
    if detected_type == "go":
        return ["Go toolchain"], ["go build -o app", "./app"]
    if detected_type == "static":
        return ["Nginx 或静态文件服务"], ["nginx -s reload"]
    return [], ["ls -lah"]


def _summary_for_type(detected_type: str) -> str:
    return {
        "docker": "识别为 Docker/Docker Compose 服务",
        "java": "识别为 Java 服务",
        "node": "识别为 Node.js 服务",
        "python": "识别为 Python 服务",
        "go": "识别为 Go 服务",
        "static": "识别为静态站点",
    }.get(detected_type, "未识别到明确项目类型")


def _read_package_scripts(package_json: Path) -> dict[str, str]:
    try:
        payload = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = payload.get("scripts")
    if not isinstance(scripts, dict):
        return {}
    return {str(key): str(value) for key, value in scripts.items()}


def _relative_name(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()

