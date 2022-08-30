from dataclasses import dataclass
from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from inspect import iscoroutinefunction, get_annotations
from pathlib import Path
from re import compile
from types import ModuleType
from typing import Awaitable, Callable, Iterable, Protocol, TypeAlias, TypeGuard

from psycopg import AsyncCursor, AsyncConnection
from psycopg.rows import TupleRow
from psycopg.sql import SQL, Identifier

from ..settings import Settings

MIGRATIONS_SCHEMA = "public"
MIGRATIONS_TABLE = "migrations"
MIGRATION_NAME = compile(
    r"\d+_[A-Za-z_]+\.py"
)  # matches:`[numbers]_[name_with_underscores].py`


CREATE_MIGRATION_TABLE = SQL(
    """
    CREATE TABLE IF NOT EXISTS {table} (
        id serial,
        name text
        CONSTRAINT name_unique UNIQUE,
        timestamp timestamp
    )
    """
).format(table=Identifier(MIGRATIONS_TABLE))

INSERT_NEW_MIGRATION = SQL(
    """
    INSERT INTO {table}(name, timestamp)
    VALUES (%s, %s)
    """
).format(table=Identifier(MIGRATIONS_TABLE))

REMOVE_MIGRATION_BY_ID = SQL(
    """
    DELETE FROM {table}
    WHERE id = %s
    """
).format(table=Identifier(MIGRATIONS_TABLE))

GET_LATEST_MIGRATION = SQL(
    """
    SELECT id, name, timestamp
    FROM {table}
    ORDER BY timestamp DESC
    LIMIT 1
    """
).format(table=Identifier(MIGRATIONS_TABLE))

GET_SECOND_LATEST_MIGRATION = SQL(
    """
    SELECT id, name, timestamp
    FROM {table}
    ORDER BY timestamp DESC
    LIMIT 1
    OFFSET 1
    """
).format(table=Identifier(MIGRATIONS_TABLE))

GET_ALL_MIGRATIONS = SQL(
    """
    SELECT id, name, timestamp
    FROM {table}
    ORDER BY timestamp DESC
    """
).format(table=Identifier(MIGRATIONS_TABLE))


MIGRATION_CORO: TypeAlias = Callable[[AsyncCursor[TupleRow]], Awaitable[None]]


class Connection:
    _db_url: str
    _inner: AsyncConnection

    def __init__(self, settings: Settings):
        self._db_url = settings.db_url

    async def __aenter__(self):
        self._inner = await AsyncConnection.connect(self._db_url, autocommit=True)
        return await self._inner.__aenter__()

    async def __aexit__(self, *args):
        return await self._inner.__aexit__(*args)


class MigrationModule(Protocol):
    up: MIGRATION_CORO
    down: MIGRATION_CORO


def is_migration_module(module: ModuleType) -> TypeGuard[MigrationModule]:
    try:
        module.up
        module.down
    except AttributeError:
        return False
    if not iscoroutinefunction(module.up) or not iscoroutinefunction(module.down):
        return False
    if not coro_takes_cursor(module.up) or not coro_takes_cursor(module.down):
        return False
    return True


def coro_takes_cursor(
    coro: MIGRATION_CORO,
) -> TypeGuard[MIGRATION_CORO]:
    annotations = get_annotations(coro)
    arg, *_ = annotations
    return issubclass(AsyncCursor, annotations[arg])


class NotFoundException(Exception):
    migration: "Migration"

    def __init__(self, migration: "Migration") -> None:
        super().__init__(f"Migration {migration} couldn't be found in local files")
        self.migration = migration


@dataclass
class Migration:
    timestamp: datetime
    name: str
    path: Path | None = None
    id: int | None = None

    @classmethod
    def from_path(cls, path: Path):
        timestamp, name = path.name.split("_", 1)
        stripped_name, _ = name.rsplit(".", 1)
        return cls(datetime.fromtimestamp(int(timestamp)), stripped_name, path)

    def load_migration_module(self) -> MigrationModule:
        if not self.path:
            raise Exception(f"Invalid migration: {self}")

        spec = spec_from_file_location(self.name, self.path)
        if not spec or not spec.loader:
            raise Exception(f"Couldn't create module from {self}")

        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        if not is_migration_module(module):
            raise Exception(f"{self} is not a valid migration module.")

        return module

    def update_from_local(self, migrations: list["Migration"]):
        matching = next(
            (
                migration
                for migration in migrations
                if migration.name == self.name and migration.timestamp == self.timestamp
            ),
            self,
        )
        if matching is self:
            raise NotFoundException(self)
        self.path = matching.path

    def get_first_older(self, migrations: list["Migration"]):
        return next(
            (
                migration
                for migration in reversed(sort_migrations(migrations))
                if migration.timestamp < self.timestamp
            ),
            None,
        )

    def __str__(self) -> str:
        return f"{round(self.timestamp.timestamp())}_{self.name}"


def override_print(module: MigrationModule, name: str, idx: int | None = None) -> None:
    index_part = "" if idx is None else f"[{idx + 1}]"

    def override_print(*values, **kwargs):
        return print(f"{index_part} [{name}]", *values, **kwargs)

    module.print = override_print  # type: ignore


def sort_migrations(migrations: Iterable[Migration]) -> list[Migration]:
    return sorted(
        migrations,
        key=lambda m: m.timestamp,
    )


async def create_migration(cursor: AsyncCursor, migration: Migration) -> None:
    await cursor.execute(INSERT_NEW_MIGRATION, (migration.name, migration.timestamp))


async def get_last_migration(cursor: AsyncCursor[Migration]) -> Migration | None:
    await cursor.execute(GET_LATEST_MIGRATION)
    return await cursor.fetchone()


async def get_all_migrations(cursor: AsyncCursor[Migration]) -> list[Migration]:
    await cursor.execute(GET_ALL_MIGRATIONS)
    return await cursor.fetchall()


async def remove_migration(cursor: AsyncCursor, migration: Migration) -> None:
    if migration.id is None:
        raise Exception("This migration wasn't created by the database")
    await cursor.execute(REMOVE_MIGRATION_BY_ID, (migration.id,))


def get_migrations_in_dir(path: Path) -> list[Migration]:
    if not path.is_dir():
        raise ValueError("`path` doesn't lead to a directory")
    return sort_migrations(
        Migration.from_path(file)
        for file in Path.iterdir(path)
        if file.is_file() and MIGRATION_NAME.match(file.name)
    )


def migrations_newer_than(
    old_migration: Migration | None, migrations: list[Migration]
) -> list[Migration]:
    return sort_migrations(
        migration
        for migration in migrations
        if not old_migration or (migration.timestamp > old_migration.timestamp)
    )  # ensure that they're sorted in chronological order
