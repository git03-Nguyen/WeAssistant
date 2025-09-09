#!/usr/bin/env python3
"""Database migration script for WeAssistant."""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.init_db import (
    create_chat_history_tables,
    create_qdrant_collection,
    create_tables,
    drop_chat_history_tables,
    drop_qdrant_collection_func,
    drop_tables,
    initialize_database,
)


async def main():
    """Main migration script."""
    if len(sys.argv) < 2:
        print(
            "Usage: python migrate.py [init|create|drop|chat-init|chat-drop|qdrant-init|qdrant-drop]"
        )
        print("\nCommands:")
        print(
            "  init        - Initialize all database tables and collections (recommended)"
        )
        print("  create      - Create only main application tables")
        print("  chat-init   - Create only chat history tables")
        print("  qdrant-init - Create only Qdrant collection")
        print("  drop        - Drop all main application tables")
        print("  chat-drop   - Drop only chat history tables")
        print("  qdrant-drop - Drop only Qdrant collection")
        return

    command = sys.argv[1].lower()

    try:
        if command == "init":
            print("🚀 Initializing complete database...")
            await initialize_database()

        elif command == "create":
            print("🔧 Creating main application tables...")
            await create_tables()

        elif command == "chat-init":
            print("💬 Creating chat history tables...")
            await create_chat_history_tables()

        elif command == "qdrant-init":
            print("📊 Creating Qdrant collection...")
            await create_qdrant_collection()

        elif command == "drop":
            print("⚠️  Dropping main application tables...")
            confirm = input("Are you sure? This will delete all data! (yes/no): ")
            if confirm.lower() == "yes":
                await drop_tables()
            else:
                print("❌ Operation cancelled")

        elif command == "chat-drop":
            print("⚠️  Dropping chat history tables...")
            confirm = input(
                "Are you sure? This will delete all chat history! (yes/no): "
            )
            if confirm.lower() == "yes":
                await drop_chat_history_tables()
            else:
                print("❌ Operation cancelled")

        elif command == "qdrant-drop":
            print("⚠️  Dropping Qdrant collection...")
            confirm = input(
                "Are you sure? This will delete all vector data! (yes/no): "
            )
            if confirm.lower() == "yes":
                await drop_qdrant_collection_func()
            else:
                print("❌ Operation cancelled")

        else:
            print(f"❌ Unknown command: {command}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
