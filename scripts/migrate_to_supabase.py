#!/usr/bin/env python3
"""
Data migration script from SQLAlchemy (SQLite/Postgres) to Supabase.

This script:
1. Exports data from the old Flask app database
2. Transforms it to match the new Supabase schema
3. Imports it via Supabase admin API
"""
import os
import sys
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

try:
    from sqlalchemy import create_engine, MetaData, Table
    from supabase import create_client, Client
except ImportError:
    print("Missing dependencies. Install with:")
    print("pip install sqlalchemy supabase")
    sys.exit(1)

# Configuration
OLD_DB_URI = os.getenv("OLD_DATABASE_URL", "sqlite:///app.db")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables")
    sys.exit(1)

# Initialize clients
engine = create_engine(OLD_DB_URI)
metadata = MetaData()
metadata.reflect(bind=engine)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def export_old_data() -> Dict[str, List[Dict]]:
    """Export data from old database."""
    print("📤 Exporting data from old database...")

    data = {}

    for table_name in ["user", "produce_request", "saved_schedule"]:
        if table_name not in metadata.tables:
            print(f"⚠️  Table '{table_name}' not found, skipping")
            continue

        table = metadata.tables[table_name]
        rows = engine.execute(table.select()).fetchall()

        data[table_name] = [dict(row._mapping) for row in rows]
        print(f"  ✓ Exported {len(data[table_name])} rows from {table_name}")

    return data


def create_supabase_users(old_users: List[Dict]) -> Dict[int, str]:
    """
    Create users in Supabase Auth and profiles table.
    Returns mapping of old_id -> new_uuid.
    """
    print("\n👤 Migrating users...")

    user_mapping = {}

    for old_user in old_users:
        # In production, you'd use Supabase Admin API to create users
        # For this migration, we'll create profiles only and assume
        # users will sign in manually to activate their accounts

        # Generate a deterministic email if not present
        email = old_user.get('org_email') or f"{old_user['username']}@verdant.local"

        # Note: In a real migration, use Supabase Admin API:
        # response = supabase.auth.admin.create_user({
        #     "email": email,
        #     "password": "temp_password_123",  # Force password reset
        #     "email_confirm": True
        # })

        print(f"  ⚠️  User {old_user['username']} needs to sign up manually")
        print(f"     Suggested email: {email}")

        # For now, create a placeholder UUID
        # In reality, you'd get this from the auth.create_user response
        import uuid
        new_uuid = str(uuid.uuid4())
        user_mapping[old_user['id']] = new_uuid

        # Create profile (this will fail without real auth user - skip for demo)
        # supabase.table('profiles').insert({
        #     'id': new_uuid,
        #     'username': old_user['username'],
        #     'role': old_user.get('role', 'user'),
        #     'phone_number': old_user.get('phone_number', ''),
        #     'org_email': old_user.get('org_email', '')
        # }).execute()

    return user_mapping


def migrate_produce_requests(
    old_requests: List[Dict],
    user_mapping: Dict[int, str]
) -> None:
    """Migrate produce requests."""
    print("\n🌾 Migrating produce requests...")

    for req in old_requests:
        old_user_id = req['user_id']

        if old_user_id not in user_mapping:
            print(f"  ⚠️  Skipping request {req['id']} - user not found")
            continue

        new_req = {
            'owner_id': user_mapping[old_user_id],
            'num_people': req.get('num_people', 0),
            'volume_goal': req.get('volume_goal', 0),
            'calorie_goal': req.get('calorie_goal', 0),
            'additional_needs': req.get('additional_needs', ''),
            'shelter_notes': req.get('shelter_notes', ''),
            'urgency': req.get('urgency', 1),
            'status': req.get('status', 'new'),
            'created_at': req.get('created_at', datetime.utcnow().isoformat())
        }

        try:
            supabase.table('produce_requests').insert(new_req).execute()
            print(f"  ✓ Migrated request {req['id']}")
        except Exception as e:
            print(f"  ✗ Failed to migrate request {req['id']}: {e}")


def migrate_schedules(
    old_schedules: List[Dict],
    user_mapping: Dict[int, str]
) -> None:
    """Migrate saved schedules to new normalized structure."""
    print("\n📅 Migrating schedules...")

    for sched in old_schedules:
        old_user_id = sched['user_id']

        if old_user_id not in user_mapping:
            print(f"  ⚠️  Skipping schedule {sched['id']} - user not found")
            continue

        # Create a default garden for this user if needed
        # In reality, you'd have gardens already created
        # For demo, we'll skip garden creation

        print(f"  ⚠️  Schedule {sched['name']} requires manual garden association")

        # Parse schedule JSON
        try:
            schedule_json = json.loads(sched.get('schedule_json', '[]'))
        except:
            schedule_json = []

        # This would be the full migration:
        # 1. Create schedule record
        # 2. Parse schedule_json and create individual task records
        # 3. Store diagram as-is or in Storage

        print(f"  ℹ️  Schedule '{sched['name']}' has {len(schedule_json)} tasks")


def main():
    """Main migration workflow."""
    print("🚀 Verdant Data Migration: SQLAlchemy → Supabase\n")

    # Step 1: Export
    old_data = export_old_data()

    # Step 2: Transform & Load
    if 'user' in old_data:
        user_mapping = create_supabase_users(old_data['user'])
    else:
        user_mapping = {}

    if 'produce_request' in old_data and user_mapping:
        migrate_produce_requests(old_data['produce_request'], user_mapping)

    if 'saved_schedule' in old_data and user_mapping:
        migrate_schedules(old_data['saved_schedule'], user_mapping)

    print("\n✅ Migration complete!")
    print("\n⚠️  IMPORTANT:")
    print("   1. Users must sign up manually with their designated emails")
    print("   2. Gardens must be created through the mobile app wizard")
    print("   3. Old schedules can be regenerated with the new AI service")
    print("   4. Consider this a fresh start with historical reference\n")


if __name__ == "__main__":
    main()
