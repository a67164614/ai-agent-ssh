from __future__ import annotations

from pathlib import Path

from app.services.project_analyzer import analyze_project_directory, build_deployment_plan


def test_detects_node_project_and_builds_plan(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"scripts":{"build":"vite build","start":"node server.js"}}',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("demo service", encoding="utf-8")

    analysis = analyze_project_directory(tmp_path, target_path="/opt/apps/demo")
    plan = build_deployment_plan(analysis)

    assert analysis.detected_type == "node"
    assert "package.json" in analysis.manifests
    assert any(step.name == "安装依赖" for step in plan.steps)
    assert any(step.command == "npm run build" for step in plan.steps)
    assert plan.summary.startswith("识别为 Node.js")


def test_detects_docker_compose_project(tmp_path: Path) -> None:
    (tmp_path / "docker-compose.yml").write_text("services:\n  web:\n    image: nginx", encoding="utf-8")

    analysis = analyze_project_directory(tmp_path, target_path="/opt/apps/web")
    plan = build_deployment_plan(analysis)

    assert analysis.detected_type == "docker"
    assert any(step.command == "docker compose up -d" for step in plan.steps)
