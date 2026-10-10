#!/usr/bin/env python3
"""Backup / restore the FolioTrack SQLite database to / from a JSON file.

Examples:
    ./backup.py --backup                      # writes backup-YYYYMMDD-HHMMSS.json
    ./backup.py --backup out.json --db /data/tracker.db
    ./backup.py --restore out.json --db /data/tracker.db

Exit codes: 0 success, 1 error (database left untouched on restore errors).
"""
import sys
import os
import json
import argparse
import tempfile
from datetime import datetime

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Parents first; restore clears in reverse order.
TABLE_SPECS = [
    ("accounts", "Account"),
    ("audit_log", "AuditLog"),
    ("share_holdings", "ShareHolding"),
    ("properties", "Property"),
    ("mortgage_parts", "MortgagePart"),
    ("property_value_audit_log", "PropertyValueAuditLog"),
    ("mortgage_part_audit_log", "MortgagePartAuditLog"),
    ("app_settings", "AppSetting"),
]


def default_backup_filename():
    return f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.strptime(value.split(".")[0], "%Y-%m-%dT%H:%M:%S")


# Tables added after older backups were made: if a backup lacks them, restore leaves
# the current rows alone instead of emptying them.
OPTIONAL_TABLES = {"app_settings"}


def _load():
    """Import database/models lazily so DB_PATH can be set first (--db)."""
    import database
    import models
    tables = [(name, getattr(models, cls)) for name, cls in TABLE_SPECS]
    return database, models, tables


def build_backup_data(db):
    """Dump every table to a JSON-serialisable dict using an open session."""
    _database, _models, tables = _load()
    data = {}
    for name, model in tables:
        data[name] = [
            {c.name: getattr(r, c.name) for c in r.__table__.columns}
            for r in db.query(model).all()
        ]
    return data


def write_backup(db, output_file):
    """Write a backup atomically (temp file + fsync + rename). Returns the path."""
    data = build_backup_data(db)
    output_file = os.path.abspath(output_file)
    out_dir = os.path.dirname(output_file)
    os.makedirs(out_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".backup-", suffix=".tmp", dir=out_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, default=serialize_datetime, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, output_file)
        tmp_path = None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
    return output_file


def run_backup(output_file):
    database, _models, _tables = _load()
    db = database.SessionLocal()
    try:
        write_backup(db, output_file)
        print(f"Backup written to: {output_file}")
        return 0
    except Exception as e:
        print(f"Error during backup: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


def _build_objects(backup_data, models, tables):
    """Validate the structure and parse every row into model instances."""
    if not isinstance(backup_data, dict):
        raise ValueError("backup file must contain a JSON object at the top level")
    known = {name for name, _ in tables}
    unknown = set(backup_data) - known
    if unknown:
        raise ValueError(f"unknown table(s) in backup: {', '.join(sorted(unknown))}")
    if not any(name in backup_data for name in known):
        raise ValueError("backup file contains none of the expected tables")

    objects = []
    for name, model in tables:
        rows = backup_data.get(name)
        if rows is None and name in OPTIONAL_TABLES:
            continue
        if rows is None:
            print(f"Warning: table '{name}' missing from backup; it will be empty.", file=sys.stderr)
            continue
        if not isinstance(rows, list):
            raise ValueError(f"table '{name}' must be a list of rows")
        columns = {c.name: c for c in model.__table__.columns}
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"{name}[{i}] must be an object")
            bad = set(row) - set(columns)
            if bad:
                raise ValueError(f"{name}[{i}] has unknown column(s): {', '.join(sorted(bad))}")
            kwargs = dict(row)
            for cname, col in columns.items():
                if isinstance(col.type, models.DateTime) and kwargs.get(cname):
                    kwargs[cname] = parse_datetime(kwargs[cname])
            objects.append((name, model(**kwargs)))
    return objects


def run_restore(input_file):
    if not os.path.exists(input_file):
        print(f"Error: backup file '{input_file}' not found.", file=sys.stderr)
        return 1
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            backup_data = json.load(f)
    except (OSError, ValueError) as e:
        print(f"Error: cannot read backup file: {e}", file=sys.stderr)
        return 1

    database, models, tables = _load()
    try:
        objects = _build_objects(backup_data, models, tables)
    except Exception as e:
        print(f"Error: invalid backup file, database not modified: {e}", file=sys.stderr)
        return 1

    # Ensure tables exist on a brand-new DB file (no-op for existing tables).
    database.Base.metadata.create_all(bind=database.engine)

    db = database.SessionLocal()
    try:
        for name, model in reversed(tables):
            if name in OPTIONAL_TABLES and name not in backup_data:
                continue
            db.query(model).delete()
        for name, obj in objects:
            db.add(obj)
        db.commit()
        print(f"Database restored from: {input_file} ({len(objects)} rows)")
        return 0
    except Exception as e:
        db.rollback()
        print(f"Error during restore (rolled back, existing data kept): {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Backup or restore the FolioTrack SQLite database to/from JSON.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--backup", metavar="FILE", nargs="?", const="",
                       help="Write a JSON backup (default name: backup-YYYYMMDD-HHMMSS.json)")
    group.add_argument("--restore", metavar="FILE", help="Restore the DB from a JSON backup (replaces current data)")
    parser.add_argument("--db", metavar="PATH", help="SQLite file to use (default: $DB_PATH or backend/tracker.db)")
    args = parser.parse_args(argv)

    if args.db:
        os.environ["DB_PATH"] = os.path.abspath(args.db)

    if args.restore:
        return run_restore(args.restore)
    return run_backup(args.backup or default_backup_filename())


if __name__ == "__main__":
    sys.exit(main())
