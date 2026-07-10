from pathlib import Path


def test_opengauss_write_repositories_do_not_use_postgres_on_conflict():
    repo_root = Path(__file__).resolve().parents[1]

    for relative_path in [
        "app/repositories/admin_settings.py",
        "app/repositories/admin_tickets.py",
        "app/repositories/orders.py",
    ]:
        source = (repo_root / relative_path).read_text()
        assert "ON CONFLICT" not in source
