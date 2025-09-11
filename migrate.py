#!/usr/bin/env python3
"""Database migration script for WeAssistant."""

import asyncio
import sys
from pathlib import Path

from app.utils.init_db import acreate_tables, adrop_tables

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    """Main migration script."""
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [create|drop]")
        print("\nCommands:")
        print("  create      - Create all main application tables")
        print("  drop        - Drop all main application tables")
        return

    command = sys.argv[1].lower()

    try:
        if command == "create":
            print("🔧 Creating main application tables...")
            await acreate_tables()

        elif command == "drop":
            print("⚠️  Dropping main application tables...")
            await adrop_tables()
        else:
            print(f"❌ Unknown command: {command}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
