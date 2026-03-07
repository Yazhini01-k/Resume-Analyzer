#!/usr/bin/env python
"""Custom script to apply Django migrations"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_analyzer.settings')
django.setup()

from django.core.management import call_command

def apply_migrations():
    """Apply pending migrations"""
    try:
        print("Creating migrations for any model changes...")
        call_command('makemigrations', interactive=False)
        
        print("Applying all pending migrations...")
        call_command('migrate', interactive=False)
        
        print("All migrations processed successfully!")
        return True
    except Exception as e:
        print(f"Error processing migrations: {e}")
        return False

if __name__ == '__main__':
    apply_migrations()
