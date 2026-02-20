import re
import spacy
from typing import Dict, List


class JobParser:
    """Parse job descriptions to extract skills and requirements"""
    
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        
        # Common technical skills
        self.technical_skills = [
            'python', 'java', 'javascript', 'react', 'vue', 'angular', 'node.js', 'django',
            'flask', 'spring', 'dotnet', 'php', 'ruby', 'rails', 'go', 'rust', 'scala',
            'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
            'git', 'github', 'gitlab', 'ci/cd', 'jenkins', 'travis', 'circleci',
            'html', 'css', 'sass', 'less', 'webpack', 'vite', 'babel', 'eslint',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
            'machine learning', 'data science', 'artificial intelligence', 'deep learning',
            'nlp', 'computer vision', 'data analysis', 'statistics', 'r', 'matlab',
            'linux', 'ubuntu', 'windows', 'macos', 'bash', 'powershell', 'shell scripting',
            'api', 'rest', 'graphql', 'microservices', 'soa', 'serverless', 'lambda',
            'testing', 'unit testing', 'integration testing', 'e2e testing', 'jest', 'pytest',
            'agile', 'scrum', 'kanban', 'devops', 'continuous integration', 'continuous deployment'
        ]
        
        # Soft skills
        self.soft_skills = [
            'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking',
            'creativity', 'adaptability', 'time management', 'project management', 'analytical',
            'detail oriented', 'organized', 'collaborative', 'self motivated', 'proactive',
            'interpersonal', 'presentation', 'negotiation', 'decision making', 'strategic thinking'
        ]
        
        # Experience level indicators
        self.experience_indicators = {
            'entry': ['entry level', 'junior', '0-1 year', '0-2 years', 'fresher', 'graduate'],
            'mid': ['mid level', '2-5 years', '3-5 years', 'intermediate', 'experienced'],
            'senior': ['senior', '5+ years', '5-10 years', 'lead', 'principal'],
            'executive': ['executive', 'director', 'vp', 'c-level', '10+ years']
        }
    
    def parse_job_description(self, description: str) -> Dict[str, List[str]]:
        """Parse job description and extract skills and requirements"""
        
        # Preprocess text
        text = description.lower()
        
        # Extract skills
        required_skills = self._extract_required_skills(text)
        preferred_skills = self._extract_preferred_skills(text)
        all_skills = list(set(required_skills + preferred_skills))
        
        # Extract experience level
        experience_level = self._extract_experience_level(text)
        
        # Extract education requirements
        education_requirements = self._extract_education_requirements(text)
        
        return {
            'required_skills': required_skills,
            'preferred_skills': preferred_skills,
            'all_skills': all_skills,
            'experience_level': experience_level,
            'education_requirements': education_requirements
        }
    
    def _extract_required_skills(self, text: str) -> List[str]:
        """Extract required skills from job description"""
        required_skills = []
        
        # Look for explicit requirement indicators
        requirement_patterns = [
            r'requirements?:?\s*([^.]*)',
            r'must have:?([^.]*)',
            r'required:?([^.]*)',
            r'essential:?([^.]*)',
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                skills = self._find_skills_in_text(match)
                required_skills.extend(skills)
        
        # If no explicit requirements found, look for skills in general text
        if not required_skills:
            required_skills = self._find_skills_in_text(text)[:10]  # Limit to top 10
        
        return list(set(required_skills))
    
    def _extract_preferred_skills(self, text: str) -> List[str]:
        """Extract preferred skills from job description"""
        preferred_skills = []
        
        # Look for preference indicators
        preference_patterns = [
            r'preferred:?([^.]*)',
            r'nice to have:?([^.]*)',
            r'bonus:?([^.]*)',
            r'plus:?([^.]*)',
            r'desired:?([^.]*)',
        ]
        
        for pattern in preference_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                skills = self._find_skills_in_text(match)
                preferred_skills.extend(skills)
        
        return list(set(preferred_skills))
    
    def _find_skills_in_text(self, text: str) -> List[str]:
        """Find skills mentioned in text"""
        found_skills = []
        all_skills = self.technical_skills + self.soft_skills
        
        for skill in all_skills:
            if skill in text:
                found_skills.append(skill)
        
        # Use NLP to extract additional technical terms
        doc = self.nlp(text)
        
        # Extract named entities that might be technologies
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT']:
                ent_text = ent.text.lower()
                # Check if it's likely a technology
                if any(tech in ent_text for tech in ['python', 'java', 'javascript', 'sql', 'aws']):
                    found_skills.append(ent.text)
        
        return list(set(found_skills))
    
    def _extract_experience_level(self, text: str) -> str:
        """Extract experience level from job description"""
        for level, indicators in self.experience_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    return level
        return 'mid'  # Default to mid level
    
    def _extract_education_requirements(self, text: str) -> List[str]:
        """Extract education requirements from job description"""
        education_requirements = []
        
        education_patterns = [
            r'(bachelor|master|phd|doctorate|degree|b\.tech|m\.tech|b\.sc|m\.sc|mba)',
            r'(computer science|information technology|engineering|business administration)',
            r'(university|college|institute)'
        ]
        
        for pattern in education_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            education_requirements.extend(matches)
        
        return list(set(education_requirements))


class JobMatcher:
    """Match resumes with jobs using similarity algorithms"""
    
    def __init__(self):
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        self.cosine_similarity = cosine_similarity
        self.np = np
    
    def calculate_match_score(self, resume_vector: List[float], job_vector: List[float]) -> float:
        """Calculate cosine similarity between resume and job vectors"""
        if not resume_vector or not job_vector:
            return 0.0
        
        try:
            resume_vec = self.np.array(resume_vector).reshape(1, -1)
            job_vec = self.np.array(job_vector).reshape(1, -1)
            
            similarity = self.cosine_similarity(resume_vec, job_vec)[0][0]
            return float(similarity * 100)  # Convert to percentage
        except:
            return 0.0
    
    def calculate_skills_match(self, resume_skills: List[str], job_required_skills: List[str], 
                             job_preferred_skills: List[str]) -> Dict[str, any]:
        """Calculate skills match percentage and details"""
        
        resume_skills_lower = [skill.lower() for skill in resume_skills]
        job_required_lower = [skill.lower() for skill in job_required_skills]
        job_preferred_lower = [skill.lower() for skill in job_preferred_skills]
        
        # Find matched and missing skills
        matched_required = [skill for skill in resume_skills_lower if skill in job_required_lower]
        matched_preferred = [skill for skill in resume_skills_lower if skill in job_preferred_lower]
        missing_required = [skill for skill in job_required_lower if skill not in resume_skills_lower]
        additional_skills = [skill for skill in resume_skills_lower 
                           if skill not in job_required_lower and skill not in job_preferred_lower]
        
        # Calculate scores
        if job_required_skills:
            required_match_score = (len(matched_required) / len(job_required_skills)) * 100
        else:
            required_match_score = 100
        
        if job_preferred_skills:
            preferred_match_score = (len(matched_preferred) / len(job_preferred_skills)) * 100
        else:
            preferred_match_score = 100
        
        # Overall skills score (weighted: required 70%, preferred 30%)
        overall_skills_score = (required_match_score * 0.7) + (preferred_match_score * 0.3)
        
        return {
            'overall_score': overall_skills_score,
            'required_match_score': required_match_score,
            'preferred_match_score': preferred_match_score,
            'matched_required_skills': matched_required,
            'matched_preferred_skills': matched_preferred,
            'missing_required_skills': missing_required,
            'additional_skills': additional_skills
        }
    
    def generate_match_reason(self, skills_match: Dict, experience_match: float, education_match: float) -> str:
        """Generate human-readable match reason"""
        reasons = []
        
        # Skills match reason
        if skills_match['overall_score'] >= 80:
            reasons.append("Strong skills match")
        elif skills_match['overall_score'] >= 60:
            reasons.append("Good skills match")
        elif skills_match['overall_score'] >= 40:
            reasons.append("Partial skills match")
        else:
            reasons.append("Limited skills match")
        
        # Experience match reason
        if experience_match >= 80:
            reasons.append("Experience level aligns well")
        elif experience_match >= 60:
            reasons.append("Experience level is acceptable")
        elif experience_match >= 40:
            reasons.append("Experience level may need consideration")
        
        # Education match reason
        if education_match >= 80:
            reasons.append("Education requirements met")
        elif education_match >= 60:
            reasons.append("Education partially meets requirements")
        
        # Missing skills warning
        if skills_match['missing_required_skills']:
            missing_count = len(skills_match['missing_required_skills'])
            reasons.append(f"Missing {missing_count} required skill(s)")
        
        return ". ".join(reasons) + "."
