import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pickle
import json
from typing import List, Dict, Tuple, Any
import time


class SkillExtractor:
    """Advanced skill extraction using NLP and machine learning"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),
            stop_words='english',
            min_df=2,
            max_df=0.8
        )
        self.skill_classifier = None
        self.is_trained = False
        
        # Predefined skill categories
        self.skill_categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'ruby', 'go', 'rust', 'swift'],
            'web_development': ['html', 'css', 'react', 'vue', 'angular', 'django', 'flask', 'node.js'],
            'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible'],
            'data_science': ['tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'r', 'matlab'],
            'devops': ['git', 'jenkins', 'ci/cd', 'linux', 'bash', 'powershell', 'agile', 'scrum'],
            'mobile': ['ios', 'android', 'react native', 'flutter', 'swift', 'kotlin', 'xamarin'],
            'ai_ml': ['machine learning', 'deep learning', 'nlp', 'computer vision', 'ai', 'ml']
        }
        
        # Flatten all skills for training
        self.all_skills = []
        for category_skills in self.skill_categories.values():
            self.all_skills.extend(category_skills)
    
    def extract_skills(self, text: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """Extract skills from text with confidence scores"""
        start_time = time.time()
        
        # Preprocess text
        processed_text = self._preprocess_text(text)
        
        # Extract skills using multiple methods
        keyword_skills = self._extract_skills_by_keywords(text)
        pattern_skills = self._extract_skills_by_patterns(text)
        contextual_skills = self._extract_skills_by_context(text)
        
        # Combine and score skills
        all_extracted_skills = {}
        
        # Add keyword skills with high confidence
        for skill in keyword_skills:
            all_extracted_skills[skill] = min(1.0, all_extracted_skills.get(skill, 0) + 0.8)
        
        # Add pattern skills with medium confidence
        for skill in pattern_skills:
            all_extracted_skills[skill] = min(1.0, all_extracted_skills.get(skill, 0) + 0.6)
        
        # Add contextual skills with variable confidence
        for skill, confidence in contextual_skills.items():
            all_extracted_skills[skill] = min(1.0, all_extracted_skills.get(skill, 0) + confidence)
        
        # Filter by confidence threshold
        filtered_skills = {
            skill: confidence for skill, confidence in all_extracted_skills.items()
            if confidence >= confidence_threshold
        }
        
        # Categorize skills
        categorized_skills = self._categorize_skills(list(filtered_skills.keys()))
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            'extracted_skills': list(filtered_skills.keys()),
            'confidence_scores': filtered_skills,
            'categorized_skills': categorized_skills,
            'processing_time_ms': processing_time
        }
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for skill extraction"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Normalize common variations
        text = text.replace('c++', 'cplus')
        text = text.replace('c#', 'csharp')
        text = text.replace('.js', 'javascript')
        text = text.replace('node.js', 'nodejs')
        text = text.replace('react.js', 'react')
        
        return text
    
    def _extract_skills_by_keywords(self, text: str) -> List[str]:
        """Extract skills using keyword matching"""
        found_skills = []
        text_lower = text.lower()
        
        for skill in self.all_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_skills_by_patterns(self, text: str) -> List[str]:
        """Extract skills using regex patterns"""
        import re
        
        found_skills = []
        
        # Programming language patterns
        prog_patterns = [
            r'\b(python|java|javascript|c\+\+|ruby|go|rust|swift|kotlin|scala)\b',
            r'\b(html5|css3|node\.js|react\.js|vue\.js|angular\.js)\b',
            r'\b(sql|mysql|postgresql|mongodb|redis|elasticsearch)\b',
            r'\b(aws|azure|gcp|docker|kubernetes|terraform)\b',
        ]
        
        for pattern in prog_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_skills.extend(matches)
        
        return list(set(found_skills))
    
    def _extract_skills_by_context(self, text: str) -> Dict[str, float]:
        """Extract skills using contextual analysis"""
        skills_with_confidence = {}
        
        # Look for skills in specific contexts
        contexts = {
            'experience': ['experience with', 'worked with', 'developed using', 'built with'],
            'proficiency': ['proficient in', 'skilled in', 'expert in', 'knowledge of'],
            'projects': ['project used', 'implemented', 'designed', 'created'],
        }
        
        text_lower = text.lower()
        
        for skill in self.all_skills:
            skill_lower = skill.lower()
            if skill_lower in text_lower:
                confidence = 0.3  # Base confidence
                
                # Boost confidence based on context
                for context_type, context_phrases in contexts.items():
                    for phrase in context_phrases:
                        if phrase in text_lower:
                            # Check if skill appears near context phrase
                            skill_index = text_lower.find(skill_lower)
                            phrase_index = text_lower.find(phrase)
                            
                            if abs(skill_index - phrase_index) < 50:  # Within 50 characters
                                confidence += 0.2
                                break
                
                skills_with_confidence[skill] = min(confidence, 1.0)
        
        return skills_with_confidence
    
    def _categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize skills into predefined categories"""
        categorized = {category: [] for category in self.skill_categories.keys()}
        categorized['other'] = []
        
        for skill in skills:
            skill_lower = skill.lower()
            categorized_flag = False
            
            for category, category_skills in self.skill_categories.items():
                if any(cat_skill.lower() in skill_lower or skill_lower in cat_skill.lower() 
                      for cat_skill in category_skills):
                    categorized[category].append(skill)
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                categorized['other'].append(skill)
        
        return categorized


class JobMatcher:
    """Advanced job matching using multiple algorithms"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words='english',
            min_df=2,
            max_df=0.8
        )
        self.skill_weight = 0.4
        self.experience_weight = 0.3
        self.education_weight = 0.2
        self.semantic_weight = 0.1
    
    def calculate_comprehensive_match(self, resume_data: Dict, job_data: Dict) -> Dict[str, Any]:
        """Calculate comprehensive match score using multiple factors"""
        start_time = time.time()
        
        # Skills matching
        skills_result = self._calculate_skills_match(
            resume_data.get('skills', []),
            job_data.get('required_skills', []),
            job_data.get('preferred_skills', [])
        )
        
        # Experience matching
        experience_result = self._calculate_experience_match(
            resume_data.get('experience', []),
            job_data.get('experience_level', 'mid')
        )
        
        # Education matching
        education_result = self._calculate_education_match(
            resume_data.get('education', []),
            job_data.get('education_requirements', [])
        )
        
        # Semantic similarity
        semantic_result = self._calculate_semantic_similarity(
            resume_data.get('processed_text', ''),
            job_data.get('description', '') + ' ' + job_data.get('requirements', '')
        )
        
        # Calculate weighted overall score
        overall_score = (
            skills_result['score'] * self.skill_weight +
            experience_result['score'] * self.experience_weight +
            education_result['score'] * self.education_weight +
            semantic_result['score'] * self.semantic_weight
        )
        
        # Generate match explanation
        match_explanation = self._generate_match_explanation(
            skills_result, experience_result, education_result, semantic_result
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            'overall_score': overall_score,
            'skills_score': skills_result['score'],
            'experience_score': experience_result['score'],
            'education_score': education_result['score'],
            'semantic_score': semantic_result['score'],
            'matched_skills': skills_result['matched_skills'],
            'missing_skills': skills_result['missing_skills'],
            'additional_skills': skills_result['additional_skills'],
            'skill_gap_analysis': skills_result['gap_analysis'],
            'match_explanation': match_explanation,
            'processing_time_ms': processing_time
        }
    
    def _calculate_skills_match(self, resume_skills: List[str], 
                              required_skills: List[str], 
                              preferred_skills: List[str]) -> Dict[str, Any]:
        """Calculate skills match with detailed analysis"""
        resume_skills_lower = [skill.lower() for skill in resume_skills]
        required_skills_lower = [skill.lower() for skill in required_skills]
        preferred_skills_lower = [skill.lower() for skill in preferred_skills]
        
        # Find matched skills
        matched_required = [skill for skill in resume_skills_lower if skill in required_skills_lower]
        matched_preferred = [skill for skill in resume_skills_lower if skill in preferred_skills_lower]
        
        # Find missing skills
        missing_required = [skill for skill in required_skills_lower if skill not in resume_skills_lower]
        missing_preferred = [skill for skill in preferred_skills_lower if skill not in resume_skills_lower]
        
        # Find additional skills (skills candidate has that aren't required/preferred)
        all_job_skills = set(required_skills_lower + preferred_skills_lower)
        additional_skills = [skill for skill in resume_skills_lower if skill not in all_job_skills]
        
        # Calculate scores
        if required_skills:
            required_score = (len(matched_required) / len(required_skills)) * 100
        else:
            required_score = 100  # No required skills means full score
        
        if preferred_skills:
            preferred_score = (len(matched_preferred) / len(preferred_skills)) * 100
        else:
            preferred_score = 100  # No preferred skills means full score
        
        # Overall skills score (70% required, 30% preferred)
        overall_score = (required_score * 0.7) + (preferred_score * 0.3)
        
        # Gap analysis
        gap_analysis = {
            'critical_missing': missing_required[:5],  # Top 5 critical missing skills
            'nice_to_have_missing': missing_preferred[:3],  # Top 3 nice-to-have missing skills
            'strength_areas': matched_required[:5],  # Top 5 strength areas
            'additional_strengths': additional_skills[:5]  # Top 5 additional strengths
        }
        
        return {
            'score': overall_score,
            'matched_skills': matched_required + matched_preferred,
            'missing_skills': missing_required + missing_preferred,
            'additional_skills': additional_skills,
            'gap_analysis': gap_analysis,
            'required_match_rate': len(matched_required) / len(required_skills) if required_skills else 1.0,
            'preferred_match_rate': len(matched_preferred) / len(preferred_skills) if preferred_skills else 1.0
        }
    
    def _calculate_experience_match(self, resume_experience: List[str], job_experience_level: str) -> Dict[str, Any]:
        """Calculate experience level match"""
        # Simple experience matching based on keywords
        experience_keywords = {
            'entry': ['0', '1', 'fresher', 'graduate', 'intern', 'junior'],
            'mid': ['2', '3', '4', '5', 'intermediate', 'experienced'],
            'senior': ['6', '7', '8', 'senior', 'lead', 'principal'],
            'executive': ['9', '10', 'director', 'vp', 'c-level', 'executive']
        }
        
        experience_text = ' '.join(resume_experience).lower()
        job_level = job_experience_level.lower()
        
        # Check if experience level matches
        if job_level in experience_keywords:
            required_keywords = experience_keywords[job_level]
            match_count = sum(1 for keyword in required_keywords if keyword in experience_text)
            score = (match_count / len(required_keywords)) * 100
        else:
            score = 50  # Default score if level not recognized
        
        return {
            'score': min(score, 100),
            'level_match': job_level,
            'evidence': experience_text[:100] if experience_text else ''
        }
    
    def _calculate_education_match(self, resume_education: List[str], job_education: List[str]) -> Dict[str, Any]:
        """Calculate education match"""
        education_text = ' '.join(resume_education).lower()
        job_requirements = ' '.join(job_education).lower()
        
        # Education level hierarchy
        education_levels = {
            'phd': 4,
            'master': 3,
            'bachelor': 2,
            'associate': 1,
            'diploma': 1,
            'certificate': 0.5
        }
        
        max_resume_level = 0
        max_job_level = 0
        
        # Find highest education level in resume
        for level, score in education_levels.items():
            if level in education_text:
                max_resume_level = max(max_resume_level, score)
        
        # Find highest education level required
        for level, score in education_levels.items():
            if level in job_requirements:
                max_job_level = max(max_job_level, score)
        
        # Calculate match score
        if max_job_level == 0:
            score = 100  # No specific education requirement
        else:
            score = min((max_resume_level / max_job_level) * 100, 100)
        
        return {
            'score': score,
            'resume_level': max_resume_level,
            'required_level': max_job_level
        }
    
    def _calculate_semantic_similarity(self, resume_text: str, job_text: str) -> Dict[str, Any]:
        """Calculate semantic similarity using TF-IDF"""
        if not resume_text or not job_text:
            return {'score': 0, 'similarity': 0}
        
        try:
            # Create TF-IDF vectors
            documents = [resume_text, job_text]
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            score = similarity * 100
            
            return {
                'score': score,
                'similarity': similarity
            }
        except:
            return {'score': 0, 'similarity': 0}
    
    def _generate_match_explanation(self, skills_result: Dict, experience_result: Dict, 
                                  education_result: Dict, semantic_result: Dict) -> str:
        """Generate human-readable match explanation"""
        explanations = []
        
        # Skills explanation
        if skills_result['score'] >= 80:
            explanations.append("Strong skills alignment with job requirements")
        elif skills_result['score'] >= 60:
            explanations.append("Good skills match with some gaps")
        elif skills_result['score'] >= 40:
            explanations.append("Partial skills match - significant gaps exist")
        else:
            explanations.append("Limited skills match")
        
        # Experience explanation
        if experience_result['score'] >= 80:
            explanations.append("Experience level aligns well")
        elif experience_result['score'] >= 60:
            explanations.append("Experience level is acceptable")
        else:
            explanations.append("Experience level may not meet requirements")
        
        # Education explanation
        if education_result['score'] >= 80:
            explanations.append("Education requirements met")
        elif education_result['score'] >= 60:
            explanations.append("Education partially meets requirements")
        else:
            explanations.append("Education may not meet requirements")
        
        # Missing skills warning
        critical_missing = skills_result['gap_analysis']['critical_missing']
        if critical_missing:
            explanations.append(f"Missing critical skills: {', '.join(critical_missing[:3])}")
        
        return ". ".join(explanations)


class RecommendationEngine:
    """Advanced recommendation engine using multiple algorithms"""
    
    def __init__(self):
        self.skill_extractor = SkillExtractor()
        self.job_matcher = JobMatcher()
        
    def get_job_recommendations(self, resume_data: Dict, all_jobs: List[Dict], 
                              top_k: int = 10, diversity_threshold: float = 0.7) -> List[Dict]:
        """Get diverse job recommendations"""
        recommendations = []
        
        # Calculate match scores for all jobs
        job_scores = []
        for job in all_jobs:
            match_result = self.job_matcher.calculate_comprehensive_match(resume_data, job)
            job_scores.append({
                'job': job,
                'score': match_result['overall_score'],
                'details': match_result
            })
        
        # Sort by score
        job_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Apply diversity selection
        selected_recommendations = []
        selected_companies = set()
        selected_job_types = set()
        
        for job_score in job_scores:
            if len(selected_recommendations) >= top_k:
                break
            
            job = job_score['job']
            company = job.get('company', '')
            job_type = job.get('job_type', '')
            
            # Check diversity constraints
            company_diversity = company not in selected_companies or len(selected_companies) >= 3
            type_diversity = job_type not in selected_job_types or len(selected_job_types) >= 2
            
            if company_diversity and type_diversity:
                selected_recommendations.append(job_score)
                selected_companies.add(company)
                selected_job_types.add(job_type)
        
        # Format recommendations
        for i, rec in enumerate(selected_recommendations):
            recommendations.append({
                'rank': i + 1,
                'job': rec['job'],
                'match_score': rec['score'],
                'match_details': rec['details'],
                'recommendation_reason': rec['details']['match_explanation']
            })
        
        return recommendations
    
    def get_upskilling_suggestions(self, resume_skills: List[str], 
                                 target_jobs: List[Dict]) -> List[Dict]:
        """Get upskilling suggestions based on skill gaps"""
        skill_gap_frequency = {}
        skill_importance = {}
        
        # Analyze skill gaps across target jobs
        for job in target_jobs:
            required_skills = job.get('required_skills', [])
            missing_skills = [skill for skill in required_skills if skill.lower() not in [s.lower() for s in resume_skills]]
            
            for skill in missing_skills:
                skill_gap_frequency[skill] = skill_gap_frequency.get(skill, 0) + 1
                skill_importance[skill] = skill_importance.get(skill, 0) + 1  # Could be weighted by job match score
        
        # Generate suggestions
        suggestions = []
        for skill, frequency in skill_gap_frequency.items():
            if frequency >= 2:  # Skill appears in at least 2 target jobs
                suggestion = {
                    'skill_name': skill,
                    'priority_score': frequency * 10,  # Simple priority calculation
                    'target_jobs': frequency,
                    'learning_resources': self._get_learning_resources(skill),
                    'estimated_time_hours': self._estimate_learning_time(skill),
                    'difficulty_level': self._assess_difficulty(skill)
                }
                suggestions.append(suggestion)
        
        # Sort by priority
        suggestions.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return suggestions[:10]  # Top 10 suggestions
    
    def _get_learning_resources(self, skill: str) -> List[Dict]:
        """Get learning resources for a skill"""
        # This would typically integrate with external APIs
        # For now, return mock data
        return [
            {
                'type': 'online_course',
                'title': f'Complete {skill} Course',
                'provider': 'Udemy',
                'duration': '20 hours',
                'rating': 4.5
            },
            {
                'type': 'tutorial',
                'title': f'{skill} Tutorial',
                'provider': 'YouTube',
                'duration': '2 hours',
                'rating': 4.2
            }
        ]
    
    def _estimate_learning_time(self, skill: str) -> int:
        """Estimate learning time for a skill in hours"""
        # Simple estimation based on skill complexity
        complex_skills = ['machine learning', 'deep learning', 'kubernetes', 'terraform']
        medium_skills = ['python', 'javascript', 'react', 'docker']
        simple_skills = ['html', 'css', 'git', 'sql']
        
        skill_lower = skill.lower()
        
        if any(complex in skill_lower for complex in complex_skills):
            return 100
        elif any(medium in skill_lower for medium in medium_skills):
            return 40
        elif any(simple in skill_lower for simple in simple_skills):
            return 20
        else:
            return 50  # Default estimation
    
    def _assess_difficulty(self, skill: str) -> str:
        """Assess difficulty level of a skill"""
        complex_skills = ['machine learning', 'deep learning', 'kubernetes', 'terraform', 'microservices']
        medium_skills = ['python', 'javascript', 'react', 'docker', 'aws']
        
        skill_lower = skill.lower()
        
        if any(complex in skill_lower for complex in complex_skills):
            return 'advanced'
        elif any(medium in skill_lower for medium in medium_skills):
            return 'intermediate'
        else:
            return 'beginner'
