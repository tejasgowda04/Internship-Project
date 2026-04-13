import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

try:
    with open('db_info.txt', 'w') as f:
        f.write(f"Vendor: {connection.vendor}\n")
        f.write(f"Settings: {connection.settings_dict['NAME']}\n")
        
        # Test query
        with connection.cursor() as cursor:
            if connection.vendor == 'postgresql':
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            f.write("Tables:\n")
            for table in tables:
                f.write(f"- {table[0]}\n")
            
            # Check for django_session
            cursor.execute("SELECT count(*) FROM django_session")
            count = cursor.fetchone()[0]
            f.write(f"Sessions count: {count}\n")
except Exception as e:
    with open('db_info.txt', 'w') as f:
        f.write(f"Error: {str(e)}\n")
