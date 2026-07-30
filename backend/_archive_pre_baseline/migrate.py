#!/usr/bin/env python3
"""
Complyo Database Migration Helper
==================================

Usage:
    python migrate.py upgrade              # Apply all migrations
    python migrate.py downgrade            # Rollback one migration
    python migrate.py current              # Show current revision
    python migrate.py history              # Show migration history
    python migrate.py new "description"    # Create new migration
    python migrate.py stamp head           # Mark DB as current (for existing DBs)

Environment:
    DATABASE_URL must be set
"""

import os
import sys
import subprocess

def check_database_url():
    """Ensure DATABASE_URL is set."""
    if not os.getenv("DATABASE_URL"):
        print("❌ ERROR: DATABASE_URL environment variable is required!")
        print("\nExample:")
        print("  export DATABASE_URL=postgresql://user:pass@localhost:5432/complyo_db")
        sys.exit(1)

def run_alembic(args: list):
    """Run alembic command."""
    cmd = ["alembic"] + args
    print(f"🔄 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Commands that don't need DATABASE_URL
    if command == "help":
        print(__doc__)
        sys.exit(0)
    
    check_database_url()
    
    if command == "upgrade":
        # Apply all pending migrations
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        exit_code = run_alembic(["upgrade", revision])
        if exit_code == 0:
            print("✅ Migrations applied successfully!")
        sys.exit(exit_code)
    
    elif command == "downgrade":
        # Rollback one migration
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        exit_code = run_alembic(["downgrade", revision])
        if exit_code == 0:
            print("✅ Downgrade completed!")
        sys.exit(exit_code)
    
    elif command == "current":
        # Show current revision
        sys.exit(run_alembic(["current"]))
    
    elif command == "history":
        # Show migration history
        sys.exit(run_alembic(["history", "--verbose"]))
    
    elif command == "new":
        # Create new migration
        if len(sys.argv) < 3:
            print("❌ Please provide a migration description")
            print("Usage: python migrate.py new \"add user preferences table\"")
            sys.exit(1)
        description = sys.argv[2]
        exit_code = run_alembic(["revision", "-m", description])
        if exit_code == 0:
            print(f"✅ New migration created: {description}")
        sys.exit(exit_code)
    
    elif command == "autogenerate":
        # Auto-generate migration from model changes (requires models)
        if len(sys.argv) < 3:
            print("❌ Please provide a migration description")
            sys.exit(1)
        description = sys.argv[2]
        exit_code = run_alembic(["revision", "--autogenerate", "-m", description])
        if exit_code == 0:
            print(f"✅ Auto-generated migration: {description}")
            print("⚠️  Review the generated migration before applying!")
        sys.exit(exit_code)
    
    elif command == "stamp":
        # Mark database at specific revision (for existing databases)
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        exit_code = run_alembic(["stamp", revision])
        if exit_code == 0:
            print(f"✅ Database stamped at: {revision}")
        sys.exit(exit_code)
    
    elif command == "check":
        # Check if there are pending migrations
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        if "head" in result.stdout:
            print("✅ Database is up to date!")
        else:
            print("⚠️  There are pending migrations. Run: python migrate.py upgrade")
        sys.exit(0)
    
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()


