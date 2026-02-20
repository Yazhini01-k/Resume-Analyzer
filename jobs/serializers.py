from rest_framework import serializers
from .models import Job, JobCategory, JobSkill, JobSkillRequirement, JobMatch


class JobSkillSerializer(serializers.ModelSerializer):
    """Serializer for JobSkill model"""
    
    class Meta:
        model = JobSkill
        fields = ['id', 'name', 'category', 'description']


class JobSkillRequirementSerializer(serializers.ModelSerializer):
    """Serializer for JobSkillRequirement model"""
    skill = JobSkillSerializer(read_only=True)
    skill_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = JobSkillRequirement
        fields = ['id', 'skill', 'skill_id', 'importance', 'experience_years']


class JobSerializer(serializers.ModelSerializer):
    """Serializer for Job model"""
    posted_by_name = serializers.CharField(source='posted_by.get_full_name', read_only=True)
    skill_requirements = JobSkillRequirementSerializer(source='skill_requirements_set', many=True, read_only=True)
    
    class Meta:
        model = Job
        fields = ['id', 'title', 'company', 'location', 'description', 'requirements', 
                 'responsibilities', 'salary_range', 'job_type', 'experience_level',
                 'required_skills', 'preferred_skills', 'skill_keywords', 'feature_vector',
                 'posted_by', 'posted_by_name', 'is_active', 'application_count', 
                 'view_count', 'external_url', 'company_logo', 'created_at', 
                 'updated_at', 'deadline', 'skill_requirements']
        read_only_fields = ['id', 'posted_by', 'application_count', 'view_count', 
                           'created_at', 'updated_at', 'feature_vector', 'skill_keywords']


class JobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating jobs"""
    skill_requirements = JobSkillRequirementSerializer(source='skill_requirements_set', many=True, required=False)
    
    class Meta:
        model = Job
        fields = ['title', 'company', 'location', 'description', 'requirements', 
                 'responsibilities', 'salary_range', 'job_type', 'experience_level',
                 'deadline', 'external_url', 'skill_requirements']
    
    def create(self, validated_data):
        skill_requirements_data = validated_data.pop('skill_requirements_set', [])
        job = Job.objects.create(**validated_data)
        
        # Create skill requirements
        for skill_req_data in skill_requirements_data:
            skill_id = skill_req_data.pop('skill_id')
            skill = JobSkill.objects.get(id=skill_id)
            JobSkillRequirement.objects.create(
                job=job,
                skill=skill,
                **skill_req_data
            )
        
        # Process job description to extract skills
        self._extract_job_skills(job)
        
        return job
    
    def _extract_job_skills(self, job):
        """Extract skills from job description"""
        from .utils import JobParser
        
        parser = JobParser()
        parsed_skills = parser.parse_job_description(
            job.description + ' ' + (job.requirements or '')
        )
        
        job.required_skills = parsed_skills['required_skills']
        job.preferred_skills = parsed_skills['preferred_skills']
        job.skill_keywords = parsed_skills['all_skills']
        
        # Create feature vector
        from resumes.utils import FeatureVectorizer
        from django.conf import settings
        
        vectorizer = FeatureVectorizer(max_features=settings.TF_IDF_MAX_FEATURES)
        try:
            # Get all jobs for fitting
            all_jobs = Job.objects.exclude(id=job.id)
            
            if all_jobs.exists():
                documents = [j.description + ' ' + (j.requirements or '') for j in all_jobs]
                documents.append(job.description + ' ' + (job.requirements or ''))
                vectors = vectorizer.fit_transform(documents)
                job.feature_vector = vectors[-1]
            else:
                vectors = vectorizer.fit_transform([job.description + ' ' + (job.requirements or '')])
                job.feature_vector = vectors[0]
                
        except Exception:
            job.feature_vector = []
        
        job.save()


class JobCategorySerializer(serializers.ModelSerializer):
    """Serializer for JobCategory model"""
    
    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'description', 'parent']


class JobMatchSerializer(serializers.ModelSerializer):
    """Serializer for JobMatch model"""
    resume_title = serializers.CharField(source='resume.title', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_company = serializers.CharField(source='job.company', read_only=True)
    
    class Meta:
        model = JobMatch
        fields = ['id', 'resume', 'resume_title', 'job', 'job_title', 'job_company',
                 'overall_score', 'skills_match_score', 'experience_match_score', 
                 'education_match_score', 'matched_skills', 'missing_skills', 
                 'additional_skills', 'match_reason', 'recommendation_rank', 'created_at']
        read_only_fields = ['id', 'created_at']


class JobRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for job recommendations (includes match score)"""
    match_score = serializers.FloatField(source='jobmatch.overall_score', read_only=True)
    match_reason = serializers.CharField(source='jobmatch.match_reason', read_only=True)
    missing_skills = serializers.ListField(source='jobmatch.missing_skills', read_only=True)
    
    class Meta:
        model = Job
        fields = ['id', 'title', 'company', 'location', 'description', 'salary_range',
                 'job_type', 'experience_level', 'required_skills', 'application_count',
                 'view_count', 'created_at', 'deadline', 'match_score', 'match_reason',
                 'missing_skills']
