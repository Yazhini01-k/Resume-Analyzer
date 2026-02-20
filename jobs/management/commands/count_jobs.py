from django.core.management.base import BaseCommand
from jobs.models import Job


class Command(BaseCommand):
    help = 'Count jobs in the database'
    
    def handle(self, *args, **options):
        total_jobs = Job.objects.count()
        active_jobs = Job.objects.filter(is_active=True).count()
        inactive_jobs = Job.objects.filter(is_active=False).count()
        
        self.stdout.write(self.style.SUCCESS(f'📊 Job Database Statistics:'))
        self.stdout.write(f'   Total Jobs: {total_jobs}')
        self.stdout.write(f'   Active Jobs: {active_jobs}')
        self.stdout.write(f'   Inactive Jobs: {inactive_jobs}')
        
        if active_jobs > 0:
            self.stdout.write(self.style.SUCCESS(f'✅ Database has {active_jobs} active jobs ready for recommendations'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  No active jobs found in database'))
        
        # Show some sample jobs
        if active_jobs > 0:
            sample_jobs = Job.objects.filter(is_active=True)[:5]
            self.stdout.write(self.style.SUCCESS(f'\n📝 Sample Active Jobs:'))
            for job in sample_jobs:
                self.stdout.write(f'   • {job.title} at {job.company}')
                self.stdout.write(f'     Location: {job.location}')
                self.stdout.write(f'     Skills: {job.required_skills[:3]}...')
                self.stdout.write(f'     Created: {job.created_at.strftime("%Y-%m-%d")}')
                self.stdout.write('')
