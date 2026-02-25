# Generated manually to fix database schema mismatch

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resumes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='resume',
            name='job_match_count',
            field=models.IntegerField(default=0),
        ),
    ]
