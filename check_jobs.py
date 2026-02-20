#!/usr/bin/env python
import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_analyzer.settings')

import django
django.setup()

from jobs.models import Job

# Count jobs
total_jobs = Job.objects.count()
active_jobs = Job.objects.filter(is_active=True).count()
inactive_jobs = Job.objects.filter(is_active=False).count()

print("📊 Job Database Statistics:")
print(f"   Total Jobs: {total_jobs}")
print(f"   Active Jobs: {active_jobs}")
print(f"   Inactive Jobs: {inactive_jobs}")

if active_jobs > 0:
    print(f"✅ Database has {active_jobs} active jobs ready for recommendations")
    
    # Show some sample jobs
    sample_jobs = Job.objects.filter(is_active=True)[:5]
    print(f"\n📝 Sample Active Jobs:")
    for job in sample_jobs:
        print(f"   • {job.title} at {job.company}")
        print(f"     Location: {job.location}")
        print(f"     Skills: {job.required_skills[:3] if job.required_skills else 'None'}...")
        print(f"     Created: {job.created_at.strftime('%Y-%m-%d')}")
        print("")
else:
    print("⚠️  No active jobs found in database")

print(f"\n🎯 System Status: {'READY' if active_jobs >= 200 else 'NEEDS MORE JOBS'}")
if active_jobs < 200:
    print(f"📈 Need {200 - active_jobs} more jobs to meet requirement")
