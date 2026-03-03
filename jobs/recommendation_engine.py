"""
Dynamic Job Recommendation Engine
Handles real-time job recommendations based on resume skills and job requirements
"""

from django.db import models
from django.utils import timezone
from django.db.models import Q, F, Count, Avg
from django.contrib.auth import get_user_model
from collections import defaultdict
import math

User = get_user_model()


class JobRecommendationEngine:
    """
    Dynamic job recommendation engine that calculates matches based on:
    1. Skill overlap percentage
    2. Experience level matching
    3. Location preferences
    4. Salary expectations
    5. Job type preferences
    """
    
    def __init__(self):
        self.skill_weight = 0.6  # 60% weight for skills
        self.experience_weight = 0.2  # 20% weight for experience
        self.location_weight = 0.1  # 10% weight for location
        self.salary_weight = 0.1  # 10% weight for salary
    
    def get_user_recommendations(self, user, limit=10, min_score=30.0):
        """
        Get personalized job recommendations for a user based on their resume skills
        """
        from resumes.models import Resume, SkillProfile
        from jobs.models import Job, JobMatch
        
        # Get user's latest processed resume
        latest_resume = Resume.objects.filter(
            user=user,
            processing_status='completed'
        ).order_by('-created_at').first()
        
        if not latest_resume or not latest_resume.extracted_skills:
            return []
        
        # Get user's preferences from candidate profile
        candidate_profile = getattr(user, 'candidate_profile', None)
        preferences = self._extract_user_preferences(candidate_profile)
        
        # Get all active jobs
        active_jobs = Job.objects.filter(is_active=True)
        
        recommendations = []
        for job in active_jobs:
            match_result = self._calculate_job_match(latest_resume, job, preferences)
            
            if match_result['overall_score'] >= 0:
                # Create or update JobMatch record
                job_match, created = JobMatch.objects.get_or_create(
                    resume=latest_resume,
                    job=job,
                    user=user,
                    defaults={
                        'overall_score': match_result['overall_score'],
                        'skills_match_score': match_result['skills_score'],
                        'experience_match_score': match_result['experience_score'],
                        'location_match_score': match_result['location_score'],
                        'salary_match_score': match_result['salary_score'],
                        'matched_skills': match_result['matched_skills'],
                        'missing_skills': match_result['missing_skills'],
                        'skill_match_details': match_result['skill_details'],
                        'match_reason': match_result['reason'],
                        'confidence_level': match_result['confidence'],
                        'recommendation_source': 'skill_match'
                    }
                )
                
                if not created:
                    # Update existing match with new scores
                    job_match.overall_score = match_result['overall_score']
                    job_match.skills_match_score = match_result['skills_score']
                    job_match.experience_match_score = match_result['experience_score']
                    job_match.location_match_score = match_result['location_score']
                    job_match.salary_match_score = match_result['salary_score']
                    job_match.matched_skills = match_result['matched_skills']
                    job_match.missing_skills = match_result['missing_skills']
                    job_match.skill_match_details = match_result['skill_details']
                    job_match.match_reason = match_result['reason']
                    job_match.confidence_level = match_result['confidence']
                    job_match.save()
                
                # Increment job match count for analytics
                job.increment_match_count()
                
                recommendations.append({
                    'job': job,
                    'match': job_match,
                    'match_percentage': match_result['overall_score'],
                    'matched_skills': match_result['matched_skills'],
                    'missing_skills': match_result['missing_skills'],
                    'reason': match_result['reason']
                })
        
        # Sort by match percentage descending
        recommendations.sort(key=lambda x: x['match_percentage'], reverse=True)
        return recommendations[:limit]
    
    def _calculate_job_match(self, resume, job, user_preferences):
        """
        Calculate detailed match score between resume and job
        """
        # Skills matching (60% weight)
        skills_score, matched_skills, missing_skills, skill_details = self._calculate_skills_match(
            resume.extracted_skills, job.required_skills, job.preferred_skills
        )
        
        # Experience matching (20% weight)
        experience_score = self._calculate_experience_match(
            resume.extracted_experience, job.experience_level
        )
        
        # Location matching (10% weight)
        location_score = self._calculate_location_match(
            user_preferences.get('preferred_locations', []), job.location
        )
        
        # Salary matching (10% weight)
        salary_score = self._calculate_salary_match(
            user_preferences.get('salary_min'), user_preferences.get('salary_max'),
            job.salary_min, job.salary_max
        )
        
        # Calculate overall score
        overall_score = (
            skills_score * self.skill_weight +
            experience_score * self.experience_weight +
            location_score * self.location_weight +
            salary_score * self.salary_weight
        )
        
        # Generate match reason
        reason = self._generate_match_reason(
            skills_score, experience_score, location_score, salary_score,
            len(matched_skills), len(job.required_skills)
        )
        
        # Calculate confidence level
        confidence = self._calculate_confidence(
            skills_score, len(matched_skills), len(job.required_skills)
        )
        
        return {
            'overall_score': round(overall_score, 2),
            'skills_score': round(skills_score, 2),
            'experience_score': round(experience_score, 2),
            'location_score': round(location_score, 2),
            'salary_score': round(salary_score, 2),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'skill_details': skill_details,
            'reason': reason,
            'confidence': round(confidence, 2)
        }
    
    def _calculate_skills_match(self, resume_skills, job_required_skills, job_preferred_skills=None):
        """
        Calculate skills match percentage with detailed breakdown
        """
        if not resume_skills or not job_required_skills:
            return 0.0, [], [], {}
        
        # Normalize skills to lowercase for comparison
        resume_skill_set = set(skill.lower().strip() for skill in resume_skills if skill)
        required_skill_set = set(skill.lower().strip() for skill in job_required_skills if skill)
        
        # Calculate required skills match (70% of skills score)
        matched_required = resume_skill_set & required_skill_set
        required_match_percentage = (len(matched_required) / len(required_skill_set)) * 70
        
        # Calculate preferred skills match (30% of skills score)
        preferred_match_percentage = 0
        matched_preferred = set()
        if job_preferred_skills:
            preferred_skill_set = set(skill.lower().strip() for skill in job_preferred_skills if skill)
            matched_preferred = resume_skill_set & preferred_skill_set
            if preferred_skill_set:
                preferred_match_percentage = (len(matched_preferred) / len(preferred_skill_set)) * 30
        
        # Total skills score
        total_skills_score = required_match_percentage + preferred_match_percentage
        
        # Detailed skill breakdown
        skill_details = {}
        for skill in required_skill_set:
            skill_details[skill] = {
                'matched': skill in matched_required,
                'required': True,
                'match_percentage': 100.0 if skill in matched_required else 0.0
            }
        
        for skill in (job_preferred_skills or []):
            skill_lower = skill.lower().strip()
            if skill_lower not in skill_details:
                skill_details[skill_lower] = {
                    'matched': skill_lower in matched_preferred,
                    'required': False,
                    'match_percentage': 100.0 if skill_lower in matched_preferred else 0.0
                }
        
        # Combine matched skills
        all_matched = list(matched_required | matched_preferred)
        missing_required = list(required_skill_set - matched_required)
        
        return min(total_skills_score, 100.0), all_matched, missing_required, skill_details
    
    def _calculate_experience_match(self, resume_experience, job_experience_level):
        """
        Calculate experience level match
        """
        if not resume_experience:
            return 50.0  # Neutral score if no experience data
        
        # Extract years of experience from resume
        total_years = 0
        for exp in resume_experience:
            if isinstance(exp, dict) and 'years' in exp:
                total_years += max(0, exp['years'])
            elif isinstance(exp, str):
                # Try to extract years from string
                import re
                years_match = re.search(r'(\d+)\s*(?:years?|yrs?)', exp.lower())
                if years_match:
                    total_years += int(years_match.group(1))
        
        # Map job levels to required years
        level_requirements = {
            'entry': 0,
            'mid': 2,
            'senior': 5,
            'lead': 7,
            'executive': 10
        }
        
        required_years = level_requirements.get(job_experience_level, 2)
        
        if total_years >= required_years:
            return 100.0
        elif total_years >= required_years * 0.5:
            return 75.0
        elif total_years >= required_years * 0.25:
            return 50.0
        else:
            return 25.0
    
    def _calculate_location_match(self, preferred_locations, job_location):
        """
        Calculate location preference match
        """
        if not preferred_locations or not job_location:
            return 50.0  # Neutral score
        
        job_location_lower = job_location.lower()
        
        # Check for exact matches or partial matches
        for pref_loc in preferred_locations:
            pref_loc_lower = pref_loc.lower()
            if pref_loc_lower in job_location_lower or job_location_lower in pref_loc_lower:
                return 100.0
        
        # Check for remote work preference
        if 'remote' in [loc.lower() for loc in preferred_locations]:
            if 'remote' in job_location_lower:
                return 100.0
        
        return 0.0
    
    def _calculate_salary_match(self, user_salary_min, user_salary_max, job_salary_min, job_salary_max):
        """
        Calculate salary expectation match
        """
        if not user_salary_min or not job_salary_min:
            return 50.0  # Neutral score if no salary data
        
        # Convert to same units (assuming thousands)
        user_min = user_salary_min or 0
        user_max = user_salary_max or user_min * 1.5  # Default 50% higher than min
        job_min = job_salary_min or 0
        job_max = job_salary_max or job_min * 1.5
        
        # Calculate overlap percentage
        overlap_min = max(user_min, job_min)
        overlap_max = min(user_max, job_max)
        
        if overlap_max >= overlap_min:
            # There's an overlap
            overlap_range = overlap_max - overlap_min
            user_range = user_max - user_min
            if user_range > 0:
                return min((overlap_range / user_range) * 100, 100.0)
        
        # No overlap, calculate distance
        if user_max < job_min:
            # User expects less than job offers (good)
            return 100.0
        else:
            # User expects more than job offers
            distance = user_min - job_max
            user_range = user_max - user_min
            if user_range > 0:
                return max(0, 100 - (distance / user_range * 100))
        
        return 50.0
    
    def _extract_user_preferences(self, candidate_profile):
        """
        Extract user preferences from candidate profile
        """
        if not candidate_profile:
            return {}
        
        return {
            'preferred_locations': candidate_profile.preferred_locations or [],
            'salary_min': candidate_profile.salary_expectation_min,
            'salary_max': candidate_profile.salary_expectation_max,
            'preferred_job_types': candidate_profile.preferred_job_types or [],
            'preferred_industries': candidate_profile.preferred_industries or [],
            'remote_work_preference': candidate_profile.remote_work_preference
        }
    
    def _generate_match_reason(self, skills_score, experience_score, location_score, 
                              salary_score, matched_count, required_count):
        """
        Generate human-readable match reason
        """
        reasons = []
        
        if skills_score >= 70:
            reasons.append(f"Strong skills match ({matched_count}/{required_count} skills)")
        elif skills_score >= 40:
            reasons.append(f"Good skills match ({matched_count}/{required_count} skills)")
        elif skills_score > 0:
            reasons.append(f"Partial skills match ({matched_count}/{required_count} skills)")
        
        if experience_score >= 75:
            reasons.append("Experience level matches requirements")
        elif experience_score >= 50:
            reasons.append("Experience level is acceptable")
        
        if location_score >= 75:
            reasons.append("Location matches preferences")
        elif location_score > 0:
            reasons.append("Location is acceptable")
        
        if salary_score >= 75:
            reasons.append("Salary expectations align")
        elif salary_score > 0:
            reasons.append("Salary may be negotiable")
        
        return "; ".join(reasons) if reasons else "Basic match found"
    
    def _calculate_confidence(self, skills_score, matched_count, required_count):
        """
        Calculate confidence level in the recommendation
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on skills match
        if skills_score >= 80:
            confidence += 0.3
        elif skills_score >= 60:
            confidence += 0.2
        elif skills_score >= 40:
            confidence += 0.1
        
        # Increase confidence based on number of matched skills
        if required_count > 0:
            match_ratio = matched_count / required_count
            confidence += match_ratio * 0.2
        
        return min(confidence, 1.0)
    
    def refresh_recommendations_for_user(self, user):
        """
        Refresh all recommendations for a user
        """
        # Delete old recommendations
        from jobs.models import JobMatch
        JobMatch.objects.filter(user=user).delete()
        
        # Generate new recommendations
        return self.get_user_recommendations(user, limit=50, min_score=20.0)
    
    def get_recommendation_analytics(self, user):
        """
        Get analytics about user's recommendations
        """
        from jobs.models import JobMatch
        
        matches = JobMatch.objects.filter(user=user)
        
        return {
            'total_recommendations': matches.count(),
            'viewed_recommendations': matches.filter(is_viewed=True).count(),
            'applied_recommendations': matches.filter(is_applied=True).count(),
            'saved_recommendations': matches.filter(is_saved=True).count(),
            'average_match_score': matches.aggregate(Avg('overall_score'))['overall_score__avg'] or 0,
            'top_skills': self._get_top_matched_skills(matches),
            'recommendation_sources': matches.values('recommendation_source').annotate(
                count=Count('id')
            ).order_by('-count')
        }
    
    def _get_top_matched_skills(self, matches):
        """
        Get most commonly matched skills across recommendations
        """
        skill_counts = defaultdict(int)
        
        for match in matches:
            if match.matched_skills:
                for skill in match.matched_skills:
                    skill_counts[skill] += 1
        
        # Return top 10 skills
        return sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]


# Global instance
recommendation_engine = JobRecommendationEngine()
