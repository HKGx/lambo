import asyncio
from datetime import datetime
from pathlib import Path
from sys import platform
import argparse
from psycopg.rows import class_row

from lambo.databasy.migrate_utils import (
    CREATE_MIGRATION_TABLE,
    Connection,
    Migration,
    create_migration,
    get_all_migrations,
    get_last_migration,
    get_migrations_in_dir,
    coro_takes_cursor,
    migrations_newer_than,
    override_print,
    remove_migration,
)


async def migrations_update(file: str | None = None):
    from lambo.main import config

    migrations_dir = Path(file if file else __file__).parent
    print(f"Seeing migrations in `{migrations_dir}`.")
    migrations = get_migrations_in_dir(migrations_dir)
    async with Connection(config) as conn:
        async with conn.cursor(row_factory=class_row(Migration)) as cursor:
            await cursor.execute(CREATE_MIGRATION_TABLE)

            last_migration = await get_last_migration(cursor)

        new_migrations: list[Migration] = migrations_newer_than(
            last_migration, migrations
        )

        new_migrations_count = len(new_migrations)
        plural = (
            "miragtions"
            if new_migrations_count > 1 or new_migrations_count == 0
            else "migration"
        )
        print(f"Found {new_migrations_count} new {plural}:")
        for idx, migration in enumerate(new_migrations):
            print(f"\t[{idx+1}] {migration.name} created on {migration.timestamp}")
        print("")

        for idx, migration in enumerate(new_migrations):
            print(f"[{idx + 1}] [{migration.name}] Loading migration module")
            module = migration.load_migration_module()
            override_print(module, migration.name, idx)
            try:
                async with conn.transaction():
                    async with conn.cursor() as cursor:
                        await module.up(cursor)
                        await create_migration(cursor, migration)
            except Exception as e:
                print(
                    f"[{idx + 1}] [{migration.name}] Migration failed. We will not continue."
                )
                raise e
            print(f"[{idx + 1}] [{migration.name}] Ended migration")


async def migrations_downgrade(file: str | None):
    from lambo.main import config

    migrations_dir = Path(file if file else __file__).parent
    print(f"Seeing migrations in `{migrations_dir}`.")
    migrations = get_migrations_in_dir(migrations_dir)
    async with Connection(config) as conn:
        async with conn.cursor(row_factory=class_row(Migration)) as cursor:
            await cursor.execute(CREATE_MIGRATION_TABLE)

            last_migration = await get_last_migration(cursor)

            if not last_migration:
                raise Exception("There are no migrations to downgrade!")

            last_migration.update_from_local(migrations)

            migration: Migration | None = last_migration.get_first_older(migrations)

        if migration is None:
            migration = last_migration
            print(
                f"Will downgrade the {migration.name} (created on {migration.timestamp}) as it's the last migration"
            )
        else:
            print(
                f"Will downgrade to {migration.name} created on {migration.timestamp} from {last_migration.name} (createed on {last_migration.timestamp})"
            )
        print("")

        module = migration.load_migration_module()
        override_print(module, last_migration.name)
        try:
            async with conn.transaction():
                async with conn.cursor() as cursor:
                    await module.down(cursor)
                    await remove_migration(cursor, last_migration)
        except Exception as e:
            print(f"[{migration.name}] Failed: ")
            raise e


async def migrations_validate(file: str | None):
    from lambo.main import config

    migrations_dir = Path(file if file else __file__).parent
    print(f"Seeing migrations in `{migrations_dir}`.")
    migrations = get_migrations_in_dir(migrations_dir)
    async with Connection(config) as conn:
        async with conn.cursor(row_factory=class_row(Migration)) as cursor:
            await cursor.execute(CREATE_MIGRATION_TABLE)
            database_migrations = await get_all_migrations(cursor)
    for idx, migration in enumerate(database_migrations):
        print(f"\t[{idx + 1}] {migration.name} created on {migration.timestamp}")
        migration.update_from_local(migrations)
    print("All migrations from the database can be found in local files.")


MIGRATION_TEMPLATE = """from psycopg import AsyncConnection, AsyncCursor


async def up(conn: AsyncCursor) -> None:
    print("XD!")


async def down(conn: AsyncCursor) -> None:
    pass
"""


def is_unique_among(migrations: list[Migration], name: str) -> bool:
    sanitized = name.replace(" ", "_")
    return all(migration.name != sanitized for migration in migrations)


def get_proper_name(raw_name: str) -> str:
    sanitized = raw_name.replace(" ", "_")
    return sanitized if sanitized.endswith(".py") else sanitized + ".py"


def create_migration_file(file: str | None, name: str):
    migrations_dir = Path(file if file else __file__).parent
    print(f"Loading migrations from {migrations_dir}")
    migrations = get_migrations_in_dir(migrations_dir)

    if not is_unique_among(migrations, name):
        raise Exception(f"Name {name} already exists!")
    proper_name = get_proper_name(name)
    timestamp = round(datetime.now().timestamp())
    file_name = f"{timestamp}_{proper_name}"
    file_path = migrations_dir / file_name
    print(f"Commencing to create a migration file in: `{migrations_dir}`.")
    file_path.write_text(MIGRATION_TEMPLATE)
    print(f"File `{file_path}` has been created!")


def main(file: str | None = None):
    if platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="subcommands", dest="action")
    update = subparsers.add_parser("update", aliases=["up", "u"])
    rollback = subparsers.add_parser("downgrade", aliases=["down", "d"])
    validate = subparsers.add_parser("validate")
    create = subparsers.add_parser("create", aliases=["c"])
    create.add_argument("name")

    args = parser.parse_args()
    match args.action:
        case "update" | "up" | "u":
            asyncio.run(migrations_update(file))
        case "downgrade" | "down" | "d":
            asyncio.run(migrations_downgrade(file))
        case "create" | "c":
            create_migration_file(file, args.name)
        case "validate":
            asyncio.run(migrations_validate(file))
        case unknown:
            raise Exception(f"Unknown option: {unknown}")


if __name__ == "__main__":
    main()
