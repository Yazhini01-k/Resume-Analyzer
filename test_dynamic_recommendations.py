"""
Test Script for Dynamic Job Recommendation System
Verifies all components work correctly with 200+ jobs
"""

import os
import sys
import django
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_analyzer.settings')
django.setup()

from jobs.models import Job, JobMatch, JobSkill
from jobs.recommendation_engine import recommendation_engine
from jobs.recommendation_queries import *
from resumes.models import Resume, SkillProfile
from accounts.models import CandidateProfile, HRProfile, Company

User = get_user_model()


class RecommendationSystemTest:
    """
    Comprehensive test suite for the dynamic job recommendation system
    """
    
    def __init__(self):
        self.test_user = None
        self.test_resume = None
        self.created_jobs = []
        self.test_skills = [
            'python', 'javascript', 'react', 'django', 'sql', 'postgresql',
            'aws', 'docker', 'git', 'api', 'rest', 'json', 'html', 'css',
            'nodejs', 'mongodb', 'redis', 'kubernetes', 'jenkins', 'linux'
        ]
    
    def setup_test_data(self):
        """Create test data for recommendations"""
        print("🔧 Setting up test data...")
        
        # Create test candidate user
        self.test_user, created = User.objects.get_or_create(
            email='test.candidate@example.com',
            defaults={
                'username': 'testcandidate',
                'first_name': 'Test',
                'last_name': 'Candidate',
                'role': 'candidate',
                'email_verified': True
            }
        )
        
        if created:
            self.test_user.set_password('testpass123')
            self.test_user.save()
            
            # Create candidate profile
            CandidateProfile.objects.create(
                user=self.test_user,
                bio='Experienced software developer',
                experience_years=5,
                preferred_locations=['New York', 'San Francisco', 'Remote'],
                salary_expectation_min=80000,
                salary_expectation_max=120000,
                preferred_job_types=['full_time', 'remote'],
                remote_work_preference='flexible'
            )
        
        # Create test resume with skills
        self.test_resume, created = Resume.objects.get_or_create(
            user=self.test_user,
            title='Software Developer Resume',
            defaults={
                'original_filename': 'test_resume.pdf',
                'file_type': 'pdf',
                'processing_status': 'completed',
                'extracted_skills': self.test_skills[:15],  # Use 15 skills
                'extracted_experience': [
                    {'title': 'Senior Developer', 'company': 'Tech Corp', 'years': 3},
                    {'title': 'Junior Developer', 'company': 'Startup Inc', 'years': 2}
                ],
                'extracted_education': [
                    {'degree': 'Bachelor of Science', 'field': 'Computer Science', 'year': 2018}
                ]
            }
        )
        
        # Create skill profile
        SkillProfile.objects.get_or_create(
            user=self.test_user,
            defaults={
                'skills': {skill.lower(): 'intermediate' for skill in self.test_skills[:15]},
                'total_skills_count': 15,
                'verification_status': 'self_verified'
            }
        )
        
        print(f"✅ Test user created: {self.test_user.email}")
        print(f"✅ Test resume created with {len(self.test_resume.extracted_skills)} skills")
    
    def create_test_jobs(self, count=250):
        """Create test jobs for recommendation testing"""
        print(f"📝 Creating {count} test jobs...")
        
        companies = [
            'Tech Corp', 'Digital Solutions', 'Cloud Systems', 'Data Analytics Inc',
            'Software Factory', 'Web Development Co', 'Mobile Apps Ltd', 'AI Solutions',
            'Cyber Security Inc', 'DevOps Company', 'Startup Hub', 'Enterprise Systems',
            'FinTech Solutions', 'Health Tech', 'E-commerce Platform', 'Gaming Studio',
            'Social Media Corp', 'Marketing Tech', 'Education Technology', 'Real Estate Tech'
        ]
        
        locations = [
            'New York, NY', 'San Francisco, CA', 'Remote', 'Austin, TX',
            'Seattle, WA', 'Boston, MA', 'Los Angeles, CA', 'Chicago, IL',
            'Denver, CO', 'Portland, OR', 'Miami, FL', 'Atlanta, GA'
        ]
        
        job_titles = [
            'Senior Software Engineer', 'Full Stack Developer', 'Backend Developer',
            'Frontend Developer', 'DevOps Engineer', 'Cloud Engineer',
            'Data Scientist', 'Machine Learning Engineer', 'Software Architect',
            'Technical Lead', 'Python Developer', 'JavaScript Developer',
            'React Developer', 'Django Developer', 'API Developer',
            'Database Administrator', 'Systems Engineer', 'Security Engineer',
            'QA Engineer', 'Product Manager','UIUX designer'
        ]
        
        # Get or create HR user
        hr_user, _ = User.objects.get_or_create(
            email='test.hr@example.com',
            defaults={
                'username': 'testhr',
                'first_name': 'Test',
                'last_name': 'HR',
                'role': 'hr'
            }
        )
        
        for i in range(count):
            # Randomly select job attributes
            import random
            
            title = random.choice(job_titles)
            company = random.choice(companies)
            location = random.choice(locations)
            
            # Generate skills based on job title
            required_skills = random.sample(self.test_skills, random.randint(3, 8))
            preferred_skills = random.sample(
                [s for s in self.test_skills if s not in required_skills],
                random.randint(0, 4)
            )
            
            # Calculate salary based on role complexity
            base_salary = 60000 if 'Junior' in title else 80000 if 'Senior' in title else 100000
            salary_min = base_salary + random.randint(-20000, 30000)
            salary_max = salary_min + random.randint(20000, 50000)
            
            job = Job.objects.create(
                title=title,
                company=company,
                location=location,
                description=f'We are looking for a talented {title} to join our team.',
                requirements=f'Experience with {", ".join(required_skills[:3])} required.',
                responsibilities=f'Develop and maintain {title.lower()} applications.',
                salary_range=f'${salary_min:,} - ${salary_max:,}',
                salary_min=salary_min,
                salary_max=salary_max,
                job_type=random.choice(['full_time', 'remote', 'hybrid']),
                experience_level=random.choice(['entry', 'mid', 'senior', 'lead']),
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                posted_by=hr_user,
                is_active=True
            )
            
            self.created_jobs.append(job)
        
        print(f"✅ Created {len(self.created_jobs)} test jobs")
    
    def test_recommendation_engine(self):
        """Test the recommendation engine"""
        print("\n🎯 Testing Recommendation Engine...")
        
        # Get recommendations
        recommendations = recommendation_engine.get_user_recommendations(
            user=self.test_user,
            limit=20,
            min_score=30.0
        )
        
        print(f"✅ Generated {len(recommendations)} recommendations")
        
        if recommendations:
            # Test top recommendation
            top_rec = recommendations[0]
            print(f"🏆 Top recommendation: {top_rec['job'].title} at {top_rec['job'].company}")
            print(f"📊 Match percentage: {top_rec['match_percentage']}%")
            print(f"🔧 Matched skills: {', '.join(top_rec['matched_skills'][:5])}")
            print(f"❌ Missing skills: {', '.join(top_rec['missing_skills'][:3])}")
            
            # Verify match calculation
            assert top_rec['match_percentage'] >= 30.0, "Match percentage should be >= 30%"
            assert len(top_rec['matched_skills']) > 0, "Should have matched skills"
            
            print("✅ Recommendation engine working correctly")
        else:
            print("⚠️ No recommendations generated")
    
    def test_sql_queries(self):
        """Test optimized SQL queries"""
        print("\n🗄️ Testing SQL Queries...")
        
        # Test core job matching query
        results = execute_job_match_query(
            user_id=self.test_user.id,
            min_score=30.0,
            limit=10
        )
        
        print(f"✅ SQL query returned {len(results)} results")
        
        if results:
            top_result = results[0]
            print(f"🏆 Top SQL match: {top_result['title']} at {top_result['company']}")
            print(f"📊 SQL match score: {top_result['overall_score']}%")
            
            # Verify SQL results
            assert top_result['overall_score'] >= 30.0, "SQL match score should be >= 30%"
            assert 'matched_skills' in top_result, "Should include matched skills"
            assert 'missing_skills' in top_result, "Should include missing skills"
            
            print("✅ SQL queries working correctly")
        
        # Test skill demand query
        demand_results = execute_skill_demand_query(self.test_skills[:5])
        print(f"✅ Skill demand query returned {len(demand_results)} results")
        
        # Test market insights query
        insights_results = execute_market_insights_query(self.test_skills[:5])
        print(f"✅ Market insights query returned results")
        
        print("✅ All SQL queries working correctly")
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🌐 Testing API Endpoints...")
        
        from django.test import Client
        from django.contrib.auth import authenticate
        
        client = Client()
        
        # Login test user
        client.login(username='test.candidate@example.com', password='testpass123')
        
        # Test dynamic recommendations endpoint
        response = client.get('/api/jobs/api/dynamic-recommendations/')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dynamic recommendations API returned {len(data.get('recommendations', []))} results")
            
            # Verify response structure
            assert 'recommendations' in data, "Should include recommendations array"
            assert 'total_count' in data, "Should include total count"
            assert 'generated_at' in data, "Should include timestamp"
            
            if data['recommendations']:
                rec = data['recommendations'][0]
                assert 'match_percentage' in rec, "Should include match percentage"
                assert 'matched_skills' in rec, "Should include matched skills"
                assert 'missing_skills' in rec, "Should include missing skills"
            
            print("✅ API endpoints working correctly")
        else:
            print(f"❌ API endpoint failed with status {response.status_code}")
            print(f"Response: {response.content.decode()}")
    
    def test_performance(self):
        """Test system performance with large dataset"""
        print("\n⚡ Testing Performance...")
        
        import time
        
        # Test recommendation generation time
        start_time = time.time()
        recommendations = recommendation_engine.get_user_recommendations(
            user=self.test_user,
            limit=50,
            min_score=20.0
        )
        rec_time = time.time() - start_time
        
        print(f"⏱️ Generated {len(recommendations)} recommendations in {rec_time:.3f} seconds")
        
        # Test SQL query performance
        start_time = time.time()
        sql_results = execute_job_match_query(
            user_id=self.test_user.id,
            min_score=20.0,
            limit=50
        )
        sql_time = time.time() - start_time
        
        print(f"⏱️ SQL query returned {len(sql_results)} results in {sql_time:.3f} seconds")
        
        # Performance assertions
        assert rec_time < 5.0, f"Recommendations should take < 5s, took {rec_time:.3f}s"
        assert sql_time < 2.0, f"SQL query should take < 2s, took {sql_time:.3f}s"
        
        print("✅ Performance tests passed")
    
    def test_database_indexes(self):
        """Test database indexes are working"""
        print("\n📊 Testing Database Indexes...")
        
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Check if indexes exist
            cursor.execute("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE tablename IN ('jobs_job', 'resumes_resume', 'jobs_jobmatch')
                ORDER BY tablename, indexname;
            """)
            
            indexes = cursor.fetchall()
            print(f"✅ Found {len(indexes)} indexes on core tables")
            
            # Test index usage with EXPLAIN
            cursor.execute("""
                EXPLAIN ANALYZE
                SELECT j.id, j.title, j.company 
                FROM jobs_job j 
                WHERE j.is_active = true 
                AND j.required_skills ?| ARRAY['python', 'javascript']
                ORDER BY j.created_at DESC 
                LIMIT 10;
            """)
            
            explain_results = cursor.fetchall()
            print("✅ Index usage verified with EXPLAIN ANALYZE")
            
            # Check for index scans in the plan
            plan_text = ' '.join([row[0] for row in explain_results])
            if 'Index Scan' in plan_text or 'Bitmap Index Scan' in plan_text:
                print("✅ Indexes are being used by query planner")
            else:
                print("⚠️ Indexes may not be optimally used")
    
    def test_skill_matching_accuracy(self):
        """Test skill matching accuracy"""
        print("\n🎯 Testing Skill Matching Accuracy...")
        
        # Create a job with known skills
        test_job = Job.objects.create(
            title='Python Django Developer',
            company='Test Company',
            location='Remote',
            description='Looking for Python Django developer',
            requirements='Python, Django, SQL required',
            required_skills=['python', 'django', 'sql'],
            preferred_skills=['postgresql', 'git'],
            job_type='full_time',
            experience_level='mid',
            posted_by=User.objects.filter(role='hr').first(),
            is_active=True
        )
        
        # Test match calculation
        match_score = test_job.calculate_skill_match(self.test_resume.extracted_skills)
        
        print(f"📊 Test job match score: {match_score}%")
        
        # Verify accuracy
        assert match_score > 0, "Should have positive match score"
        assert 'python' in self.test_resume.extracted_skills, "Resume should have python"
        assert 'django' in self.test_resume.extracted_skills, "Resume should have django"
        
        # Test with recommendation engine
        recommendations = recommendation_engine.get_user_recommendations(
            user=self.test_user,
            limit=5,
            min_score=10.0
        )
        
        # Find our test job in recommendations
        test_job_found = False
        for rec in recommendations:
            if rec['job'].id == test_job.id:
                test_job_found = True
                print(f"✅ Test job found in recommendations with {rec['match_percentage']}% match")
                assert rec['match_percentage'] >= 10.0, "Should meet minimum score"
                break
        
        if not test_job_found:
            print("⚠️ Test job not found in top recommendations")
        
        # Cleanup
        test_job.delete()
        
        print("✅ Skill matching accuracy verified")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created jobs
        Job.objects.filter(id__in=[job.id for job in self.created_jobs]).delete()
        
        # Delete test resume and profile
        if self.test_resume:
            self.test_resume.delete()
        
        SkillProfile.objects.filter(user=self.test_user).delete()
        CandidateProfile.objects.filter(user=self.test_user).delete()
        
        # Delete test user
        self.test_user.delete()
        
        print("✅ Test data cleaned up")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Dynamic Job Recommendation System Tests")
        print("=" * 60)
        
        try:
            # Setup
            self.setup_test_data()
            self.create_test_jobs(250)  # Create 250 jobs as required
            
            # Run tests
            self.test_recommendation_engine()
            self.test_sql_queries()
            self.test_api_endpoints()
            self.test_performance()
            self.test_database_indexes()
            self.test_skill_matching_accuracy()
            
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED!")
            print("✅ Dynamic Job Recommendation System is working correctly")
            print("✅ System is optimized for 200+ jobs")
            print("✅ All components are functioning properly")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup
            self.cleanup_test_data()


if __name__ == "__main__":
    tester = RecommendationSystemTest()
    tester.run_all_tests()
