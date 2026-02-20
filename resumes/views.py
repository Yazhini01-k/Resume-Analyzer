import os
import json
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Resume, SkillProfile, ResumeAnalysis
from .serializers import (
    ResumeSerializer, ResumeCreateSerializer, ResumeDetailSerializer,
    SkillProfileSerializer, ResumeAnalysisSerializer
)
from .utils import ResumeTextExtractor, ResumeParser, FeatureVectorizer
from accounts.models import User


class ResumeUploadView(generics.CreateAPIView):
    """Upload and process resume"""
    serializer_class = ResumeCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        # Save the resume file
        resume = serializer.save(user=self.request.user)
        
        # Start async processing (in production, use Celery)
        try:
            self._process_resume(resume)
        except Exception as e:
            resume.processing_status = 'failed'
            resume.error_message = str(e)
            resume.save()
    
    def _process_resume(self, resume):
        """Process uploaded resume"""
        # Update status
        resume.processing_status = 'processing'
        resume.save()
        
        # Extract file extension
        file_extension = resume.file.name.split('.')[-1].lower()
        resume.file_type = file_extension
        resume.file_size = resume.file.size
        resume.original_filename = resume.file.name.split('/')[-1]
        
        # Extract text
        extractor = ResumeTextExtractor()
        file_path = resume.file.path
        raw_text = extractor.extract_text(file_path, file_extension)
        resume.raw_text = raw_text
        
        # Parse resume content
        parser = ResumeParser()
        parsed_data = parser.parse_resume(raw_text)
        
        # Update resume with parsed data
        resume.processed_text = parsed_data['processed_text']
        resume.extracted_skills = parsed_data['extracted_skills']
        resume.extracted_education = parsed_data['extracted_education']
        resume.extracted_experience = parsed_data['extracted_experience']
        resume.extracted_contact_info = parsed_data['extracted_contact_info']
        
        # Create feature vector
        vectorizer = FeatureVectorizer(max_features=settings.TF_IDF_MAX_FEATURES)
        try:
            # Get all processed resumes for fitting
            all_resumes = Resume.objects.filter(
                processing_status='completed'
            ).exclude(id=resume.id)
            
            if all_resumes.exists():
                # Fit on existing resumes and transform new one
                documents = [r.processed_text for r in all_resumes if r.processed_text]
                documents.append(resume.processed_text)
                vectors = vectorizer.fit_transform(documents)
                resume.feature_vector = vectors[-1]  # Get last vector (new resume)
                resume.skill_keywords = vectorizer.get_feature_names()
            else:
                # First resume, fit on just this one
                vectors = vectorizer.fit_transform([resume.processed_text])
                resume.feature_vector = vectors[0]
                resume.skill_keywords = vectorizer.get_feature_names()
                
        except Exception as e:
            # If vectorization fails, continue without it
            resume.feature_vector = []
            resume.skill_keywords = []
        
        # Update processing status
        resume.processing_status = 'completed'
        resume.save()
        
        # Update user's skill profile using STRICT method
        self._create_strict_skill_profile(resume.user, resume.extracted_skills)
        
        # Create analysis
        self._create_resume_analysis(resume)
    
    def _create_strict_skill_profile(self, user, skills):
        """STRICT: Create or update user's skill profile based ONLY on extracted skills"""
        if not skills:
            return
        
        # Create skills dictionary ONLY from extracted skills
        skills_dict = {}
        for skill in skills:
            if isinstance(skill, str) and skill.strip():
                skills_dict[skill.lower().strip()] = 'intermediate'
        
        if not skills_dict:
            return
        
        # Get or create skill profile
        skill_profile, created = SkillProfile.objects.get_or_create(
            user=user,
            defaults={
                'skills': skills_dict,
                'total_skills_count': len(skills_dict)
            }
        )
        
        if not created:
            # Update existing skill profile with new skills ONLY from this resume
            skill_profile.skills = skills_dict
            skill_profile.total_skills_count = len(skills_dict)
            skill_profile.save()
    
    def _create_resume_analysis(self, resume):
        """Create resume analysis"""
        analysis = ResumeAnalysis.objects.create(resume=resume)
        
        # Calculate scores (simplified version)
        text = resume.raw_text or ""
        
        # Word count
        words = text.split()
        analysis.word_count = len(words)
        
        # Sentence count
        import nltk
        try:
            analysis.sentence_count = len(nltk.sent_tokenize(text))
        except:
            analysis.sentence_count = text.count('.') + text.count('!') + text.count('?')
        
        # Completeness score (based on sections present)
        completeness_score = 0
        if resume.extracted_skills:
            completeness_score += 25
        if resume.extracted_education:
            completeness_score += 25
        if resume.extracted_experience:
            completeness_score += 25
        if resume.extracted_contact_info:
            completeness_score += 25
        analysis.completeness_score = completeness_score
        
        # Skills score (based on number of skills)
        skills_count = len(resume.extracted_skills) if resume.extracted_skills else 0
        analysis.skills_score = min(100, skills_count * 5)
        
        # Experience score (simplified)
        exp_count = len(resume.extracted_experience) if resume.extracted_experience else 0
        analysis.experience_score = min(100, exp_count * 20)
        
        # Education score
        edu_count = len(resume.extracted_education) if resume.extracted_education else 0
        analysis.education_score = min(100, edu_count * 25)
        
        # Overall score (average)
        analysis.overall_score = (
            analysis.completeness_score + 
            analysis.skills_score + 
            analysis.experience_score + 
            analysis.education_score
        ) / 4
        
        analysis.save()


class ResumeListView(generics.ListAPIView):
    """List user's resumes"""
    serializer_class = ResumeDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)


class ResumeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Resume detail view"""
    serializer_class = ResumeDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)


class SkillProfileView(generics.RetrieveUpdateAPIView):
    """User skill profile view"""
    serializer_class = SkillProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = SkillProfile.objects.get_or_create(user=self.request.user)
        return profile


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def resume_analysis(request, resume_id):
    """Get detailed analysis for a specific resume"""
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    
    try:
        analysis = resume.analysis
        serializer = ResumeAnalysisSerializer(analysis)
        return Response(serializer.data)
    except ResumeAnalysis.DoesNotExist:
        return Response(
            {'error': 'Analysis not found for this resume'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reprocess_resume(request, resume_id):
    """Reprocess a resume (useful for debugging or updated parsing logic)"""
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    
    try:
        # Reset processing status
        resume.processing_status = 'pending'
        resume.error_message = None
        resume.save()
        
        # Reprocess
        upload_view = ResumeUploadView()
        upload_view._process_resume(resume)
        
        return Response({
            'message': 'Resume reprocessed successfully',
            'status': resume.processing_status
        })
    except Exception as e:
        resume.processing_status = 'failed'
        resume.error_message = str(e)
        resume.save()
        return Response(
            {'error': f'Failed to reprocess resume: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
