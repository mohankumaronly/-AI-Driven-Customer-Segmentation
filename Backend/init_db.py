import sys
from app import create_app
from extensions import db
from sqlalchemy import inspect

def main():
    print("=" * 60)
    print("Creating table schema on Neon PostgreSQL...")
    print("=" * 60)
    
    app = create_app()
    with app.app_context():
        # Create all tables defined in models
        db.create_all()
        print("\n[SUCCESS] db.create_all() executed.")
        
        # Inspect created tables in database
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print("\nTables present in database:")
        for table in tables:
            print(f"\n  Table: '{table}'")
            columns = inspector.get_columns(table)
            for col in columns:
                col_name = col["name"]
                col_type = col["type"]
                nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
                print(f"    - {col_name:<25} {str(col_type):<20} {nullable}")
                
        expected_tables = ["users", "auth_otps", "auth_sessions", "password_reset_tokens"]
        missing = [t for t in expected_tables if t not in tables]
        
        print("\n" + "=" * 60)
        if missing:
            print(f"[ERROR] Missing expected tables: {missing}")
            sys.exit(1)
        else:
            print("[SUCCESS] All required Phase 1 tables are present on Neon DB!")
        print("=" * 60)

if __name__ == "__main__":
    main()
