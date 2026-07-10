from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_legacy_node_baseline_is_archived_outside_current_runtime_roots():
    legacy_root = PROJECT_ROOT / "legacy-node"

    required_legacy_files = [
        legacy_root / "README.md",
        legacy_root / "package.json",
        legacy_root / "package-lock.json",
        legacy_root / "src" / "server.js",
        legacy_root / "public" / "index.html",
        legacy_root / "tests" / "health.test.js",
    ]
    for path in required_legacy_files:
        assert path.exists(), f"legacy Node baseline file is missing: {path.relative_to(PROJECT_ROOT)}"

    assert not (legacy_root / ".env").exists()
    assert not (PROJECT_ROOT / "src" / "server.js").exists()
    assert not (PROJECT_ROOT / "public" / "index.html").exists()
    assert not (PROJECT_ROOT / "tests" / "health.test.js").exists()


def test_legacy_node_archive_does_not_keep_known_demo_password_literals():
    legacy_root = PROJECT_ROOT / "legacy-node"
    forbidden_literals = [
        "admin" + "123",
        "123" + "456",
        "ddx" + "20060220.",
    ]

    checked_files = [
        path
        for path in legacy_root.rglob("*")
        if path.is_file() and path.suffix in {".js", ".json", ".md", ".html"}
    ]
    assert checked_files

    leaked = {
        str(path.relative_to(PROJECT_ROOT)): literal
        for path in checked_files
        for literal in forbidden_literals
        if literal in path.read_text(encoding="utf-8")
    }
    assert not leaked
