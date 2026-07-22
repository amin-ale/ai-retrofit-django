from django.db.migrations.loader import MigrationLoader
from django.db.migrations.operations.models import CreateModel

HOST_TABLE_PREFIX = "helpdesk_"
COPILOT_TABLE_PREFIX = "copilot_"


def _copilot_migrations():
    loader = MigrationLoader(None)
    return [
        migration
        for (app_label, _name), migration in loader.graph.nodes.items()
        if app_label == "copilot"
    ]


def test_copilot_migrations_only_create_copilot_tables():
    for migration in _copilot_migrations():
        for operation in migration.operations:
            assert isinstance(operation, CreateModel)
            db_table = operation.options.get("db_table", "")
            assert db_table.startswith(COPILOT_TABLE_PREFIX)


def test_copilot_migrations_never_touch_host_tables():
    for migration in _copilot_migrations():
        for operation in migration.operations:
            db_table = operation.options.get("db_table", "")
            assert not db_table.startswith(HOST_TABLE_PREFIX)


def test_copilot_does_not_depend_on_host_migrations():
    for migration in _copilot_migrations():
        assert all(dependency[0] != "helpdesk" for dependency in migration.dependencies)
