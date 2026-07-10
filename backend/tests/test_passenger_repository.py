from app.repositories import passengers as passenger_repository_module
from app.repositories.passengers import PostgresPassengerTemplateRepository


class ScriptedCursor:
    def __init__(self, rowcount: int):
        self.rowcount = rowcount


class ScriptedConnection:
    def __init__(self, rowcounts: list[int]):
        self.rowcounts = rowcounts
        self.queries: list[tuple[str, tuple[object, ...] | None]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        return False

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> ScriptedCursor:
        self.queries.append((query, params))
        return ScriptedCursor(self.rowcounts.pop(0))


def test_delete_passenger_template_unlinks_historical_order_items(monkeypatch):
    connection = ScriptedConnection([2, 1])
    monkeypatch.setattr(passenger_repository_module, "connect_db", lambda: connection)

    deleted = PostgresPassengerTemplateRepository().delete(template_id=10, owner_visitor_id=7)

    assert deleted is True
    assert len(connection.queries) == 2
    unlink_query, unlink_params = connection.queries[0]
    delete_query, delete_params = connection.queries[1]
    assert "UPDATE ticket_order_item" in unlink_query
    assert "passenger_template_id = NULL" in unlink_query
    assert "visitor_id = %s" in unlink_query
    assert unlink_params == (10, 7)
    assert "DELETE FROM visitor_passenger_template" in delete_query
    assert delete_params == (10, 7)
