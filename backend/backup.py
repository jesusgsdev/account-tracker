#!/usr/bin/env python3
import sys
import os
import json
import argparse
from datetime import datetime

# Add the current directory to sys.path so we can import database and models
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database import SessionLocal
import models

TABLES = [
    ("accounts", models.Account),
    ("audit_log", models.AuditLog),
    ("properties", models.Property),
    ("mortgage_parts", models.MortgagePart),
    ("property_value_audit_log", models.PropertyValueAuditLog),
    ("mortgage_part_audit_log", models.MortgagePartAuditLog),
]


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def parse_datetime(iso_str):
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str)
    except ValueError:
        return datetime.strptime(iso_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")


def run_backup(output_file):
    db = SessionLocal()
    backup_data = {}
    try:
        for name, model in TABLES:
            records = db.query(model).all()
            backup_data[name] = []
            for r in records:
                # Convert model columns to dictionary
                row = {c.name: getattr(r, c.name) for c in r.__table__.columns}
                backup_data[name].append(row)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, default=serialize_datetime, indent=2)
        print(f"✅ Backup successfully written to: {output_file}")
    except Exception as e:
        print(f"❌ Error during backup: {e}", file=sys.stderr)
    finally:
        db.close()


def run_restore(input_file):
    if not os.path.exists(input_file):
        print(f"❌ Error: Backup file '{input_file}' not found.", file=sys.stderr)
        return

    with open(input_file, "r", encoding="utf-8") as f:
        backup_data = json.load(f)

    db = SessionLocal()
    try:
        # 1. Clear tables in reverse dependency order
        print("Clearing existing database tables...")
        for _, model in reversed(TABLES):
            db.query(model).delete()
        db.commit()

        # 2. Restore tables in dependency order
        print("Restoring data from backup...")
        for name, model in TABLES:
            rows = backup_data.get(name, [])
            for row in rows:
                # Convert datetime strings back to datetime objects
                for col in model.__table__.columns:
                    if isinstance(col.type, models.DateTime) and row.get(col.name):
                        row[col.name] = parse_datetime(row[col.name])
                
                obj = model(**row)
                db.add(obj)
            db.flush()
        db.commit()
        print(f"✅ Database successfully restored from: {input_file}")
    except Exception as e:
        db.rollback()
        print(f"❌ Error during restore: {e}", file=sys.stderr)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Backup or restore FolioTrack SQLite database to/from JSON.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--backup", metavar="FILE", help="Create a JSON backup of the DB to this file path")
    group.add_argument("--restore", metavar="FILE", help="Restore the DB from a JSON backup file path")

    args = parser.parse_args()

    if args.backup:
        run_backup(args.backup)
    elif args.restore:
        run_restore(args.restore)


if __name__ == "__main__":
    main()
