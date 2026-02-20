"""
Database Schema Migration Script
Creates optimized PostgreSQL schema for dynamic job recommendations
"""

from django.db import connection, migrations
from django.conf import settings


def create_optimized_indexes():
    """
    Create optimized indexes for job recommendations performance
    These indexes are designed for handling 200+ jobs efficiently
    """
    
    indexes_sql = [
        # Core job indexes for performance
        """
        CREATE INDEX IF NOT EXISTS idx_job_active_created 
        ON jobs_job (is_active, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_job_location_active 
        ON jobs_job (location, is_active) 
        WHERE is_active = true;
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_job_company_active 
        ON jobs_job (company, is_active) 
        WHERE is_active = true;
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_job_type_exp_active 
        ON jobs_job (job_type, experience_level, is_active) 
        WHERE is_active = true;
        """,
        
        # JSON field indexes for PostgreSQL
        """
        CREATE INDEX IF NOT EXISTS idx_job_required_skills_gin 
        ON jobs_job USING GIN (required_skills);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_job_preferred_skills_gin 
        ON jobs_job USING GIN (preferred_skills);
        """,
        
        # Resume indexes for skill matching
        """
        CREATE INDEX IF NOT EXISTS idx_resume_user_completed 
        ON resumes_resume (user_id, processing_status) 
        WHERE processing_status = 'completed';
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_resume_skills_gin 
        ON resumes_resume USING GIN (extracted_skills) 
        WHERE processing_status = 'completed';
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_resume_active_created 
        ON resumes_resume (is_active, created_at DESC) 
        WHERE is_active = true;
        """,
        
        # JobMatch indexes for recommendations
        """
        CREATE INDEX IF NOT EXISTS idx_jobmatch_user_score 
        ON jobs_jobmatch (user_id, overall_score DESC, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_jobmatch_resume_score 
        ON jobs_jobmatch (resume_id, overall_score DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_jobmatch_job_score 
        ON jobs_jobmatch (job_id, overall_score DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_jobmatch_interactions 
        ON jobs_jobmatch (user_id, is_viewed, is_applied, is_saved);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_jobmatch_expires 
        ON jobs_jobmatch (expires_at) 
        WHERE expires_at > CURRENT_TIMESTAMP;
        """,
        
        # Application indexes
        """
        CREATE INDEX IF NOT EXISTS idx_application_job_status 
        ON applications_application (job_id, status, applied_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_application_candidate_status 
        ON applications_application (candidate_id, status, applied_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_application_match_score 
        ON applications_application (match_score DESC) 
        WHERE match_score > 0;
        """,
        
        # Skill profile indexes
        """
        CREATE INDEX IF NOT EXISTS idx_skillprofile_user_assessed 
        ON resumes_skillprofile (user_id, last_assessed DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_skillprofile_verification 
        ON resumes_skillprofile (verification_status, last_assessed DESC);
        """,
        
        # User profile indexes
        """
        CREATE INDEX IF NOT EXISTS idx_candidate_profile_active 
        ON accounts_candidateprofile (is_active_job_seeker, profile_visibility);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_hr_profile_verified 
        ON accounts_hrprofile (is_verified_recruiter, can_post_jobs);
        """,
        
        # Company indexes
        """
        CREATE INDEX IF NOT EXISTS idx_company_active_verified 
        ON accounts_company (is_active, is_verified, name);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_company_industry 
        ON accounts_company (industry, size) 
        WHERE is_active = true;
        """,
        
        # Composite indexes for complex queries
        """
        CREATE INDEX IF NOT EXISTS idx_job_composite_search 
        ON jobs_job (is_active, location, job_type, experience_level, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_job_salary_composite 
        ON jobs_job (is_active, salary_min, salary_max, created_at DESC) 
        WHERE salary_min IS NOT NULL;
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_resume_composite_match 
        ON resumes_resume (user_id, processing_status, is_active, created_at DESC) 
        WHERE processing_status = 'completed' AND is_active = true;
        """,
    ]
    
    with connection.cursor() as cursor:
        for index_sql in indexes_sql:
            try:
                cursor.execute(index_sql)
                print(f"✅ Index created successfully")
            except Exception as e:
                print(f"❌ Index creation failed: {e}")


def create_performance_views():
    """
    Create materialized views for common recommendation queries
    These views improve performance for frequently accessed data
    """
    
    views_sql = [
        # Active jobs summary view
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_active_jobs_summary AS
        SELECT 
            j.id,
            j.title,
            j.company,
            j.location,
            j.job_type,
            j.experience_level,
            j.salary_min,
            j.salary_max,
            j.required_skills,
            j.preferred_skills,
            j.skill_count,
            j.complexity_score,
            j.application_count,
            j.view_count,
            j.match_count,
            j.created_at,
            j.deadline,
            -- Pre-computed skill categories
            CASE 
                WHEN j.skill_count >= 10 THEN 'high_complexity'
                WHEN j.skill_count >= 5 THEN 'medium_complexity'
                ELSE 'low_complexity'
            END as complexity_category,
            -- Salary category
            CASE 
                WHEN j.salary_min >= 100000 THEN 'high_salary'
                WHEN j.salary_min >= 60000 THEN 'medium_salary'
                WHEN j.salary_min IS NOT NULL THEN 'low_salary'
                ELSE 'unspecified_salary'
            END as salary_category
        FROM jobs_job j
        WHERE j.is_active = true
        AND (j.deadline IS NULL OR j.deadline > CURRENT_TIMESTAMP);
        """,
        
        # Candidate skills summary view
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_candidate_skills_summary AS
        SELECT 
            r.user_id,
            r.id as resume_id,
            r.extracted_skills,
            r.processing_status,
            r.created_at,
            cp.preferred_locations,
            cp.salary_expectation_min,
            cp.salary_expectation_max,
            cp.preferred_job_types,
            cp.remote_work_preference,
            -- Skill count and categories
            jsonb_array_length(r.extracted_skills) as total_skills,
            CASE 
                WHEN jsonb_array_length(r.extracted_skills) >= 15 THEN 'expert_level'
                WHEN jsonb_array_length(r.extracted_skills) >= 8 THEN 'advanced_level'
                WHEN jsonb_array_length(r.extracted_skills) >= 3 THEN 'intermediate_level'
                ELSE 'beginner_level'
            END as skill_level,
            -- Top skill categories (simplified)
            CASE 
                WHEN r.extracted_skills ? 'python' OR r.extracted_skills ? 'javascript' OR r.extracted_skills ? 'java' THEN 'programming'
                WHEN r.extracted_skills ? 'sql' OR r.extracted_skills ? 'database' THEN 'database'
                WHEN r.extracted_skills ? 'aws' OR r.extracted_skills ? 'azure' OR r.extracted_skills ? 'docker' THEN 'cloud'
                ELSE 'general'
            END as primary_category
        FROM resumes_resume r
        LEFT JOIN accounts_candidateprofile cp ON r.user_id = cp.user_id
        WHERE r.processing_status = 'completed'
        AND r.is_active = true;
        """,
        
        # Job market analytics view
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_job_market_analytics AS
        SELECT 
            COUNT(*) as total_active_jobs,
            COUNT(DISTINCT company) as total_companies,
            COUNT(DISTINCT location) as total_locations,
            AVG(salary_min) as avg_salary_min,
            AVG(salary_max) as avg_salary_max,
            AVG(skill_count) as avg_skill_count,
            AVG(complexity_score) as avg_complexity_score,
            -- Job type distribution
            COUNT(*) FILTER (WHERE job_type = 'full_time') as full_time_count,
            COUNT(*) FILTER (WHERE job_type = 'part_time') as part_time_count,
            COUNT(*) FILTER (WHERE job_type = 'remote') as remote_count,
            COUNT(*) FILTER (WHERE job_type = 'contract') as contract_count,
            -- Experience level distribution
            COUNT(*) FILTER (WHERE experience_level = 'entry') as entry_count,
            COUNT(*) FILTER (WHERE experience_level = 'mid') as mid_count,
            COUNT(*) FILTER (WHERE experience_level = 'senior') as senior_count,
            COUNT(*) FILTER (WHERE experience_level = 'lead') as lead_count,
            COUNT(*) FILTER (WHERE experience_level = 'executive') as executive_count,
            -- Salary distribution
            COUNT(*) FILTER (WHERE salary_min >= 100000) as high_salary_count,
            COUNT(*) FILTER (WHERE salary_min >= 60000 AND salary_min < 100000) as medium_salary_count,
            COUNT(*) FILTER (WHERE salary_min < 60000) as low_salary_count
        FROM jobs_job
        WHERE is_active = true
        AND (deadline IS NULL OR deadline > CURRENT_TIMESTAMP);
        """,
        
        # Skill demand analytics view
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_skill_demand_analytics AS
        SELECT 
            skill_name,
            COUNT(*) as job_count,
            AVG(salary_min) as avg_salary_min,
            AVG(salary_max) as avg_salary_max,
            COUNT(DISTINCT company) as company_count,
            COUNT(DISTINCT location) as location_count,
            -- Demand level
            NTILE(5) OVER (ORDER BY COUNT(*) DESC) as demand_percentile,
            -- Salary level
            CASE 
                WHEN AVG(salary_min) >= 100000 THEN 'high_paying'
                WHEN AVG(salary_min) >= 60000 THEN 'medium_paying'
                WHEN AVG(salary_min) IS NOT NULL THEN 'low_paying'
                ELSE 'unspecified'
            END as salary_level
        FROM (
            SELECT 
                jsonb_array_elements_text(required_skills) as skill_name,
                salary_min,
                salary_max,
                company,
                location
            FROM jobs_job
            WHERE is_active = true
            AND required_skills IS NOT NULL
        ) skill_data
        GROUP BY skill_name
        HAVING COUNT(*) >= 2;  -- Only include skills that appear in at least 2 jobs
        """,
    ]
    
    with connection.cursor() as cursor:
        for view_sql in views_sql:
            try:
                cursor.execute(view_sql)
                print(f"✅ Materialized view created successfully")
            except Exception as e:
                print(f"❌ Materialized view creation failed: {e}")


def create_refresh_functions():
    """
    Create functions to refresh materialized views
    """
    
    functions_sql = [
        # Function to refresh all materialized views
        """
        CREATE OR REPLACE FUNCTION refresh_recommendation_views()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_active_jobs_summary;
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_candidate_skills_summary;
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_job_market_analytics;
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_skill_demand_analytics;
        END;
        $$ LANGUAGE plpgsql;
        """,
        
        # Function to clean up expired recommendations
        """
        CREATE OR REPLACE FUNCTION cleanup_expired_recommendations()
        RETURNS INTEGER AS $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            DELETE FROM jobs_jobmatch 
            WHERE expires_at < CURRENT_TIMESTAMP;
            
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            
            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql;
        """,
        
        # Function to update recommendation analytics
        """
        CREATE OR REPLACE FUNCTION update_recommendation_analytics()
        RETURNS void AS $$
        BEGIN
            -- Update job match counts
            UPDATE jobs_job j
            SET match_count = (
                SELECT COUNT(*)
                FROM jobs_jobmatch jm
                WHERE jm.job_id = j.id
                AND jm.expires_at > CURRENT_TIMESTAMP
            )
            WHERE j.is_active = true;
            
            -- Update recommendation ages
            UPDATE jobs_jobmatch jm
            SET recommendation_age_days = EXTRACT(DAY FROM (CURRENT_TIMESTAMP - jm.created_at))
            WHERE jm.expires_at > CURRENT_TIMESTAMP;
        END;
        $$ LANGUAGE plpgsql;
        """,
    ]
    
    with connection.cursor() as cursor:
        for function_sql in functions_sql:
            try:
                cursor.execute(function_sql)
                print(f"✅ Function created successfully")
            except Exception as e:
                print(f"❌ Function creation failed: {e}")


def create_triggers():
    """
    Create triggers for automatic data maintenance
    """
    
    triggers_sql = [
        # Trigger to update job complexity score
        """
        CREATE OR REPLACE FUNCTION update_job_complexity()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.complexity_score = (
                CASE 
                    WHEN jsonb_array_length(NEW.required_skills) >= 10 THEN 80
                    WHEN jsonb_array_length(NEW.required_skills) >= 5 THEN 60
                    WHEN jsonb_array_length(NEW.required_skills) >= 3 THEN 40
                    ELSE 20
                END +
                CASE 
                    WHEN NEW.experience_level = 'senior' THEN 20
                    WHEN NEW.experience_level = 'lead' THEN 25
                    WHEN NEW.experience_level = 'executive' THEN 30
                    ELSE 0
                END
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        DROP TRIGGER IF EXISTS trigger_update_job_complexity ON jobs_job;
        CREATE TRIGGER trigger_update_job_complexity
            BEFORE INSERT OR UPDATE ON jobs_job
            FOR EACH ROW
            EXECUTE FUNCTION update_job_complexity();
        """,
        
        # Trigger to update user profile completeness
        """
        CREATE OR REPLACE FUNCTION update_profile_completeness()
        RETURNS TRIGGER AS $$
        DECLARE
            completeness INTEGER := 0;
        BEGIN
            -- Basic info (30%)
            IF NEW.first_name IS NOT NULL AND NEW.last_name IS NOT NULL AND NEW.email_verified = true THEN
                completeness := completeness + 30;
            END IF;
            
            -- Role-specific completeness (70%)
            IF NEW.role = 'candidate' THEN
                IF EXISTS (SELECT 1 FROM accounts_candidateprofile WHERE user_id = NEW.id) THEN
                    completeness := completeness + 70;
                END IF;
            ELSIF NEW.role = 'hr' THEN
                IF EXISTS (SELECT 1 FROM accounts_hrprofile WHERE user_id = NEW.id) THEN
                    completeness := completeness + 70;
                END IF;
            END IF;
            
            NEW.profile_completeness = LEAST(completeness, 100);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        DROP TRIGGER IF EXISTS trigger_update_profile_completeness ON accounts_user;
        CREATE TRIGGER trigger_update_profile_completeness
            BEFORE INSERT OR UPDATE ON accounts_user
            FOR EACH ROW
            EXECUTE FUNCTION update_profile_completeness();
        """,
    ]
    
    with connection.cursor() as cursor:
        for trigger_sql in triggers_sql:
            try:
                cursor.execute(trigger_sql)
                print(f"✅ Trigger created successfully")
            except Exception as e:
                print(f"❌ Trigger creation failed: {e}")


def setup_database_schema():
    """
    Complete database schema setup for optimal performance
    """
    print("🚀 Setting up optimized database schema for job recommendations...")
    
    try:
        # Create indexes
        print("\n📊 Creating performance indexes...")
        create_optimized_indexes()
        
        # Create materialized views
        print("\n👁️ Creating materialized views...")
        create_performance_views()
        
        # Create functions
        print("\n⚙️ Creating maintenance functions...")
        create_refresh_functions()
        
        # Create triggers
        print("\n🔧 Creating automated triggers...")
        create_triggers()
        
        # Initial data refresh
        print("\n🔄 Initial data refresh...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT refresh_recommendation_views();")
            cursor.execute("SELECT update_recommendation_analytics();")
        
        print("\n✅ Database schema setup completed successfully!")
        print("🎯 Your system is now optimized for 200+ jobs with dynamic recommendations")
        
    except Exception as e:
        print(f"\n❌ Database schema setup failed: {e}")
        raise


if __name__ == "__main__":
    setup_database_schema()
