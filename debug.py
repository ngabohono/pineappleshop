# debug_issue.py - Let's find out what's wrong

import os
import sys

def debug_setup():
    """Debug your Flask app setup and database location"""
    
    print("🔍 DEBUGGING YOUR SETUP")
    print("=" * 50)
    
    # 1. Check current directory
    print(f"📁 Current directory: {os.getcwd()}")
    
    # 2. List files in current directory
    print(f"\n📋 Files in current directory:")
    for item in os.listdir('.'):
        if os.path.isdir(item):
            print(f"  📂 {item}/")
        else:
            print(f"  📄 {item}")
    
    # 3. Check for common Flask files
    flask_files = ['app.py', 'run.py', 'main.py', 'wsgi.py', '__init__.py']
    print(f"\n🔍 Looking for Flask entry points:")
    for file in flask_files:
        if os.path.exists(file):
            print(f"  ✓ Found: {file}")
        else:
            print(f"  ❌ Not found: {file}")
    
    # 4. Check app directory structure
    if os.path.exists('app'):
        print(f"\n📂 Contents of 'app' directory:")
        for item in os.listdir('app'):
            print(f"  - {item}")
    else:
        print(f"\n❌ No 'app' directory found")
    
    # 5. Look for database files
    database_locations = [
        'instance/database.db',
        'database.db',
        'app.db',
        'instance/app.db',
        'data/database.db'
    ]
    
    print(f"\n🗄️ Looking for database files:")
    for db_path in database_locations:
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"  ✓ Found: {db_path} (size: {size} bytes)")
        else:
            print(f"  ❌ Not found: {db_path}")
    
    # 6. Check instance directory
    if os.path.exists('instance'):
        print(f"\n📂 Contents of 'instance' directory:")
        for item in os.listdir('instance'):
            path = os.path.join('instance', item)
            if os.path.isfile(path):
                size = os.path.getsize(path)
                print(f"  📄 {item} (size: {size} bytes)")
            else:
                print(f"  📂 {item}/")
    else:
        print(f"\n❌ No 'instance' directory found")
    
    # 7. Try to find Python path issues
    print(f"\n🐍 Python sys.path:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")
    
    return True

def try_database_connection():
    """Try to connect to database directly"""
    
    print(f"\n" + "=" * 50)
    print("🔗 TESTING DATABASE CONNECTION")
    print("=" * 50)
    
    import sqlite3
    
    # Try different database paths
    db_paths = [
        'instance/database.db',
        'database.db', 
        'app.db',
        'instance/app.db'
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                print(f"\n📊 Connecting to: {db_path}")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # List tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"  Tables: {[table[0] for table in tables]}")
                
                # Check order table structure if it exists
                if any('order' in str(table) for table in tables):
                    # Try different variations of table name
                    table_names = ['order', '"order"', '`order`']
                    for table_name in table_names:
                        try:
                            cursor.execute(f"PRAGMA table_info({table_name});")
                            columns = cursor.fetchall()
                            print(f"  Columns in {table_name}: {[col[1] for col in columns]}")
                            break
                        except sqlite3.Error:
                            continue
                
                conn.close()
                print(f"  ✓ Connection successful!")
                return db_path
                
            except sqlite3.Error as e:
                print(f"  ❌ SQLite error: {e}")
            except Exception as e:
                print(f"  ❌ Connection error: {e}")
    
    print(f"\n❌ Could not connect to any database")
    return None

def try_flask_import():
    """Try different ways to import your Flask app"""
    
    print(f"\n" + "=" * 50)
    print("🔗 TESTING FLASK IMPORTS")
    print("=" * 50)
    
    import_attempts = [
        "from app import app, db",
        "from app import create_app, db; app = create_app()",
        "from run import app, db",
        "import app; app = app.app; db = app.db",
        "from __init__ import app, db",
        "from main import app, db"
    ]
    
    for attempt in import_attempts:
        try:
            print(f"\n🔄 Trying: {attempt}")
            exec(attempt)
            print(f"  ✓ Success!")
            return True
        except ImportError as e:
            print(f"  ❌ ImportError: {e}")
        except AttributeError as e:
            print(f"  ❌ AttributeError: {e}")
        except Exception as e:
            print(f"  ❌ Other error: {e}")
    
    print(f"\n❌ All Flask import attempts failed")
    return False

def simple_column_add(db_path):
    """Try to add columns using the found database"""
    
    if not db_path:
        return False
    
    print(f"\n" + "=" * 50)
    print("🔧 ADDING COLUMNS MANUALLY")
    print("=" * 50)
    
    import sqlite3
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Simple column additions
        simple_columns = [
            "first_name TEXT",
            "last_name TEXT",
            "email TEXT",
            "phone TEXT"
        ]
        
        for col_def in simple_columns:
            col_name = col_def.split()[0]
            try:
                # Use quotes around table name for SQLite reserved word
                sql = f'ALTER TABLE "order" ADD COLUMN {col_def}'
                cursor.execute(sql)
                conn.commit()
                print(f"  ✓ Added: {col_name}")
            except sqlite3.Error as e:
                if "duplicate column" in str(e).lower():
                    print(f"  ⚠ {col_name} already exists")
                else:
                    print(f"  ❌ Error adding {col_name}: {e}")
        
        conn.close()
        print(f"\n✅ Column addition completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in column addition: {e}")
        return False

def main():
    print("🚀 COMPREHENSIVE DEBUG TOOL")
    print("This will help us figure out why the scripts aren't working")
    print("=" * 60)
    
    # Step 1: Debug setup
    debug_setup()
    
    # Step 2: Test database connection
    db_path = try_database_connection()
    
    # Step 3: Test Flask imports
    try_flask_import()
    
    # Step 4: Try simple column addition if we found a database
    if db_path:
        simple_column_add(db_path)
    
    print(f"\n" + "=" * 60)
    print("🏁 DEBUG COMPLETE")
    print("Please share the output above so I can help you fix the issue!")

if __name__ == "__main__":
    main()