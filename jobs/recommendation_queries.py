"""
Optimized SQL Queries for Dynamic Job Recommendations
These queries are designed for PostgreSQL with proper indexing for 200+ jobs
"""

# 1. CORE JOB MATCHING QUERY
# This query finds jobs matching a candidate's skills with calculated match percentages

CORE_JOB_MATCH_QUERY = """
WITH candidate_skills AS (
    SELECT 
        r.id as resume_id,
        r.user_id,
        jsonb_array_elements_text(r.extracted_skills) as skill_name
    FROM resumes_resume r
    WHERE r.user_id = %s 
    AND r.processing_status = 'completed'
    AND r.is_active = true
    ORDER BY r.created_at DESC
    LIMIT 1
),

skill_matches AS (
    SELECT 
        j.id as job_id,
        j.title,
        j.company,
        j.location,
        j.description,
        j.requirements,
        j.responsibilities,
        j.salary_range,
        j.salary_min,
        j.salary_max,
        j.job_type,
        j.experience_level,
        j.required_skills,
        j.preferred_skills,
        j.application_count,
        j.view_count,
        j.created_at,
        j.deadline,
        j.external_url,
        j.company_logo,
        COUNT(cs.skill_name) FILTER (
            WHERE cs.skill_name = ANY(
                SELECT jsonb_array_elements_text(j.required_skills)
            )
        ) as required_skills_matched,
        COUNT(cs.skill_name) FILTER (
            WHERE cs.skill_name = ANY(
                SELECT jsonb_array_elements_text(j.preferred_skills)
            )
        ) as preferred_skills_matched,
        jsonb_array_length(j.required_skills) as total_required_skills,
        jsonb_array_length(j.preferred_skills) as total_preferred_skills
    FROM jobs_job j
    CROSS JOIN candidate_skills cs
    WHERE j.is_active = true
    AND j.deadline IS NULL OR j.deadline > CURRENT_TIMESTAMP
    GROUP BY j.id, j.title, j.company, j.location, j.description, 
             j.requirements, j.responsibilities, j.salary_range, 
             j.salary_min, j.salary_max, j.job_type, j.experience_level,
             j.required_skills, j.preferred_skills, j.application_count,
             j.view_count, j.created_at, j.deadline, j.external_url, j.company_logo
),

calculated_matches AS (
    SELECT 
        *,
        CASE 
            WHEN total_required_skills = 0 THEN 0
            ELSE (required_skills_matched::float / total_required_skills::float) * 70
        END as required_skills_score,
        CASE 
            WHEN total_preferred_skills = 0 THEN 0
            ELSE (preferred_skills_matched::float / total_preferred_skills::float) * 30
        END as preferred_skills_score,
        CASE 
            WHEN total_required_skills = 0 THEN 0
            ELSE ((required_skills_matched::float / total_required_skills::float) * 70) + 
                 CASE 
                     WHEN total_preferred_skills = 0 THEN 0
                     ELSE (preferred_skills_matched::float / total_preferred_skills::float) * 30
                 END
        END as overall_score
    FROM skill_matches
    WHERE total_required_skills > 0
)

SELECT 
    job_id,
    title,
    company,
    location,
    description,
    requirements,
    responsibilities,
    salary_range,
    salary_min,
    salary_max,
    job_type,
    experience_level,
    required_skills,
    preferred_skills,
    application_count,
    view_count,
    created_at,
    deadline,
    external_url,
    company_logo,
    required_skills_matched,
    preferred_skills_matched,
    total_required_skills,
    total_preferred_skills,
    required_skills_score,
    preferred_skills_score,
    overall_score,
    -- Generate matched and missing skills arrays
    (
        SELECT array_agg(skill_name) 
        FROM jsonb_array_elements_text(required_skills) 
        WHERE skill_name = ANY(
            SELECT jsonb_array_elements_text(r.extracted_skills)
            FROM resumes_resume r 
            WHERE r.user_id = %s 
            AND r.processing_status = 'completed'
            ORDER BY r.created_at DESC 
            LIMIT 1
        )
    ) as matched_skills,
    (
        SELECT array_agg(skill_name) 
        FROM jsonb_array_elements_text(required_skills) 
        WHERE skill_name NOT IN (
            SELECT jsonb_array_elements_text(r.extracted_skills)
            FROM resumes_resume r 
            WHERE r.user_id = %s 
            AND r.processing_status = 'completed'
            ORDER BY r.created_at DESC 
            LIMIT 1
        )
    ) as missing_skills
FROM calculated_matches
WHERE overall_score >= %s
ORDER BY overall_score DESC, created_at DESC
LIMIT %s;
"""

# 2. SKILL DEMAND ANALYSIS QUERY
# Analyzes market demand for specific skills

SKILL_DEMAND_QUERY = """
WITH skill_demand AS (
    SELECT 
        skill_name,
        COUNT(*) as job_count,
        AVG(salary_min) as avg_salary_min,
        AVG(salary_max) as avg_salary_max,
        array_agg(DISTINCT company) as companies,
        array_agg(DISTINCT location) as locations
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
        AND jsonb_array_length(required_skills) > 0
    ) skill_data
    GROUP BY skill_name
),

skill_rankings AS (
    SELECT 
        skill_name,
        job_count,
        avg_salary_min,
        avg_salary_max,
        companies,
        locations,
        NTILE(4) OVER (ORDER BY job_count DESC) as demand_quartile
    FROM skill_demand
)

SELECT 
    skill_name,
    job_count,
    avg_salary_min,
    avg_salary_max,
    companies,
    locations,
    CASE 
        WHEN demand_quartile = 1 THEN 'Very High'
        WHEN demand_quartile = 2 THEN 'High'
        WHEN demand_quartile = 3 THEN 'Medium'
        ELSE 'Low'
    END as demand_level
FROM skill_rankings
WHERE skill_name = ANY(%s)
ORDER BY job_count DESC;
"""

# 3. JOB MARKET INSIGHTS QUERY
# Provides comprehensive market analysis

JOB_MARKET_INSIGHTS_QUERY = """
WITH market_overview AS (
    SELECT 
        COUNT(*) as total_active_jobs,
        COUNT(DISTINCT company) as total_companies,
        COUNT(DISTINCT location) as total_locations,
        AVG(salary_min) as avg_salary_min,
        AVG(salary_max) as avg_salary_max,
        MIN(salary_min) as min_salary,
        MAX(salary_max) as max_salary
    FROM jobs_job
    WHERE is_active = true
),

company_insights AS (
    SELECT 
        company,
        COUNT(*) as job_count,
        AVG(salary_min) as avg_salary_min,
        AVG(salary_max) as avg_salary_max,
        array_agg(DISTINCT job_type) as job_types
    FROM jobs_job
    WHERE is_active = true
    GROUP BY company
    ORDER BY job_count DESC
    LIMIT 10
),

location_insights AS (
    SELECT 
        location,
        COUNT(*) as job_count,
        AVG(salary_min) as avg_salary_min,
        AVG(salary_max) as avg_salary_max,
        COUNT(DISTINCT company) as company_count
    FROM jobs_job
    WHERE is_active = true
    GROUP BY location
    ORDER BY job_count DESC
    LIMIT 10
),

skill_insights AS (
    SELECT 
        skill_name,
        COUNT(*) as job_count,
        AVG(salary_min) as avg_salary_min,
        AVG(salary_max) as avg_salary_max
    FROM (
        SELECT 
            jsonb_array_elements_text(required_skills) as skill_name,
            salary_min,
            salary_max
        FROM jobs_job
        WHERE is_active = true
        AND required_skills IS NOT NULL
    ) skill_data
    WHERE skill_name = ANY(%s)
    GROUP BY skill_name
    ORDER BY job_count DESC
)

SELECT 
    mo.*,
    ci as top_companies,
    li as top_locations,
    si as skill_demand
FROM market_overview mo,
LATERAL (SELECT jsonb_agg(ci) as top_companies FROM (
    SELECT company, job_count, avg_salary_min, avg_salary_max, job_types
    FROM company_insights
) ci) ci,
LATERAL (SELECT jsonb_agg(li) as top_locations FROM (
    SELECT location, job_count, avg_salary_min, avg_salary_max, company_count
    FROM location_insights
) li) li,
LATERAL (SELECT jsonb_agg(si) as skill_demand FROM (
    SELECT skill_name, job_count, avg_salary_min, avg_salary_max
    FROM skill_insights
) si) si;
"""

# 4. RECOMMENDATION PERFORMANCE QUERY
# Tracks recommendation effectiveness

RECOMMENDATION_PERFORMANCE_QUERY = """
WITH recommendation_stats AS (
    SELECT 
        jm.user_id,
        COUNT(*) as total_recommendations,
        COUNT(*) FILTER (WHERE jm.is_viewed = true) as viewed_count,
        COUNT(*) FILTER (WHERE jm.is_applied = true) as applied_count,
        COUNT(*) FILTER (WHERE jm.is_saved = true) as saved_count,
        AVG(jm.overall_score) as avg_match_score,
        AVG(jm.skills_match_score) as avg_skills_score,
        AVG(jm.experience_match_score) as avg_experience_score,
        AVG(jm.location_match_score) as avg_location_score,
        AVG(jm.salary_match_score) as avg_salary_score
    FROM jobs_jobmatch jm
    WHERE jm.user_id = %s
    AND jm.expires_at > CURRENT_TIMESTAMP
    GROUP BY jm.user_id
),

interaction_rates AS (
    SELECT 
        user_id,
        CASE 
            WHEN total_recommendations > 0 
            THEN (viewed_count::float / total_recommendations::float) * 100 
            ELSE 0 
        END as view_rate,
        CASE 
            WHEN total_recommendations > 0 
            THEN (applied_count::float / total_recommendations::float) * 100 
            ELSE 0 
        END as application_rate,
        CASE 
            WHEN total_recommendations > 0 
            THEN (saved_count::float / total_recommendations::float) * 100 
            ELSE 0 
        END as save_rate
    FROM recommendation_stats
),

top_matched_skills AS (
    SELECT 
        skill_name,
        COUNT(*) as match_count
    FROM (
        SELECT 
            jsonb_array_elements_text(jm.matched_skills) as skill_name
        FROM jobs_jobmatch jm
        WHERE jm.user_id = %s
        AND jm.expires_at > CURRENT_TIMESTAMP
        AND jm.matched_skills IS NOT NULL
    ) skill_matches
    GROUP BY skill_name
    ORDER BY match_count DESC
    LIMIT 10
)

SELECT 
    rs.*,
    ir.view_rate,
    ir.application_rate,
    ir.save_rate,
    (SELECT jsonb_agg(tms) FROM (
        SELECT skill_name, match_count
        FROM top_matched_skills
    ) tms) as top_matched_skills
FROM recommendation_stats rs
JOIN interaction_rates ir ON rs.user_id = ir.user_id;
"""

# 5. CANDIDATE-JOB COMPATIBILITY QUERY
# Advanced compatibility analysis

COMPATIBILITY_ANALYSIS_QUERY = """
WITH candidate_profile AS (
    SELECT 
        r.user_id,
        r.extracted_skills,
        r.extracted_experience,
        r.extracted_education,
        cp.preferred_locations,
        cp.salary_expectation_min,
        cp.salary_expectation_max,
        cp.preferred_job_types,
        cp.remote_work_preference
    FROM resumes_resume r
    LEFT JOIN accounts_candidateprofile cp ON r.user_id = cp.user_id
    WHERE r.user_id = %s
    AND r.processing_status = 'completed'
    ORDER BY r.created_at DESC
    LIMIT 1
),

job_compatibility AS (
    SELECT 
        j.id as job_id,
        j.title,
        j.company,
        j.location,
        j.job_type,
        j.experience_level,
        j.required_skills,
        j.preferred_skills,
        j.salary_min,
        j.salary_max,
        j.deadline,
        
        -- Skills compatibility (70% weight)
        CASE 
            WHEN j.required_skills IS NULL OR jsonb_array_length(j.required_skills) = 0 THEN 0
            ELSE (
                SELECT (
                    COUNT(*)::float / jsonb_array_length(j.required_skills)::float
                ) * 70
                FROM jsonb_array_elements_text(j.required_skills) skill
                WHERE skill = ANY(cp.extracted_skills)
            )
        END as skills_compatibility,
        
        -- Location compatibility (15% weight)
        CASE 
            WHEN cp.preferred_locations IS NULL OR array_length(cp.preferred_locations, 1) = 0 THEN 50
            WHEN j.location ILIKE ANY(cp.preferred_locations) OR 
                 cp.remote_work_preference = 'remote' AND j.location ILIKE '%remote%' THEN 100
            WHEN cp.remote_work_preference = 'hybrid' AND j.location ILIKE '%remote%' THEN 75
            ELSE 0
        END as location_compatibility,
        
        -- Salary compatibility (15% weight)
        CASE 
            WHEN cp.salary_expectation_min IS NULL OR j.salary_min IS NULL THEN 50
            WHEN cp.salary_expectation_min <= j.salary_max AND cp.salary_expectation_max >= j.salary_min THEN 100
            WHEN cp.salary_expectation_max >= j.salary_min THEN 75
            WHEN cp.salary_expectation_min <= j.salary_max THEN 75
            ELSE 25
        END as salary_compatibility
        
    FROM jobs_job j
    CROSS JOIN candidate_profile cp
    WHERE j.is_active = true
    AND (j.deadline IS NULL OR j.deadline > CURRENT_TIMESTAMP)
),

final_scores AS (
    SELECT 
        *,
        (skills_compatibility + location_compatibility + salary_compatibility) as overall_compatibility
    FROM job_compatibility
    WHERE skills_compatibility > 0 OR location_compatibility > 0 OR salary_compatibility > 0
)

SELECT 
    job_id,
    title,
    company,
    location,
    job_type,
    experience_level,
    required_skills,
    preferred_skills,
    salary_min,
    salary_max,
    deadline,
    skills_compatibility,
    location_compatibility,
    salary_compatibility,
    overall_compatibility,
    
    -- Detailed skill analysis
    (
        SELECT array_agg(skill_name)
        FROM jsonb_array_elements_text(required_skills)
        WHERE skill_name = ANY(cp.extracted_skills)
    ) as matched_skills,
    
    (
        SELECT array_agg(skill_name)
        FROM jsonb_array_elements_text(required_skills)
        WHERE skill_name NOT IN (
            SELECT skill_name
            FROM jsonb_array_elements_text(required_skills)
            WHERE skill_name = ANY(cp.extracted_skills)
        )
    ) as missing_skills
    
FROM final_scores
WHERE overall_compatibility >= %s
ORDER BY overall_compatibility DESC, skills_compatibility DESC
LIMIT %s;
"""

# 6. BATCH RECOMMENDATION UPDATE QUERY
# Efficiently update recommendations for multiple users

BATCH_RECOMMENDATION_UPDATE = """
INSERT INTO jobs_jobmatch (
    resume_id, 
    job_id, 
    user_id, 
    overall_score, 
    skills_match_score, 
    experience_match_score, 
    location_match_score, 
    salary_match_score,
    matched_skills, 
    missing_skills, 
    skill_match_details,
    match_reason, 
    confidence_level, 
    recommendation_source,
    created_at,
    updated_at,
    expires_at
)
SELECT 
    r.id as resume_id,
    j.id as job_id,
    r.user_id,
    compatibility.overall_compatibility as overall_score,
    compatibility.skills_compatibility as skills_match_score,
    50.0 as experience_match_score,  -- Default value
    compatibility.location_compatibility as location_match_score,
    compatibility.salary_compatibility as salary_match_score,
    compatibility.matched_skills,
    compatibility.missing_skills,
    jsonb_build_object(
        'skills_score', compatibility.skills_compatibility,
        'location_score', compatibility.location_compatibility,
        'salary_score', compatibility.salary_compatibility
    ) as skill_match_details,
    'Skills and preferences match' as match_reason,
    compatibility.overall_compatibility / 100 as confidence_level,
    'skill_match' as recommendation_source,
    CURRENT_TIMESTAMP as created_at,
    CURRENT_TIMESTAMP as updated_at,
    CURRENT_TIMESTAMP + INTERVAL '30 days' as expires_at
FROM resumes_resume r
CROSS JOIN LATERAL (
    SELECT 
        j.*,
        CASE 
            WHEN j.required_skills IS NULL OR jsonb_array_length(j.required_skills) = 0 THEN 0
            ELSE (
                SELECT (
                    COUNT(*)::float / jsonb_array_length(j.required_skills)::float
                ) * 70
                FROM jsonb_array_elements_text(j.required_skills) skill
                WHERE skill = ANY(r.extracted_skills)
            )
        END as skills_compatibility,
        50.0 as location_compatibility,  -- Simplified for batch
        50.0 as salary_compatibility,    -- Simplified for batch
        (
            SELECT array_agg(skill_name)
            FROM jsonb_array_elements_text(j.required_skills)
            WHERE skill_name = ANY(r.extracted_skills)
        ) as matched_skills,
        (
            SELECT array_agg(skill_name)
            FROM jsonb_array_elements_text(j.required_skills)
            WHERE skill_name NOT IN (
                SELECT skill_name
                FROM jsonb_array_elements_text(j.required_skills)
                WHERE skill_name = ANY(r.extracted_skills)
            )
        ) as missing_skills,
        (skills_compatibility + 50.0 + 50.0) as overall_compatibility
    FROM jobs_job j
    WHERE j.is_active = true
    AND (j.deadline IS NULL OR j.deadline > CURRENT_TIMESTAMP)
) compatibility
WHERE r.processing_status = 'completed'
AND r.is_active = true
AND compatibility.overall_compatibility >= 30.0
AND compatibility.overall_compatibility <= 100.0
ON CONFLICT (resume_id, job_id, user_id) 
DO UPDATE SET 
    overall_score = EXCLUDED.overall_score,
    skills_match_score = EXCLUDED.skills_match_score,
    experience_match_score = EXCLUDED.experience_match_score,
    location_match_score = EXCLUDED.location_match_score,
    salary_match_score = EXCLUDED.salary_match_score,
    matched_skills = EXCLUDED.matched_skills,
    missing_skills = EXCLUDED.missing_skills,
    skill_match_details = EXCLUDED.skill_match_details,
    match_reason = EXCLUDED.match_reason,
    confidence_level = EXCLUDED.confidence_level,
    updated_at = CURRENT_TIMESTAMP,
    expires_at = CURRENT_TIMESTAMP + INTERVAL '30 days';
"""

# Query execution helper functions
def execute_job_match_query(user_id, min_score=30.0, limit=10):
    """Execute the core job matching query"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute(CORE_JOB_MATCH_QUERY, [user_id, user_id, user_id, min_score, limit])
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return results

def execute_skill_demand_query(skills):
    """Execute skill demand analysis query"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute(SKILL_DEMAND_QUERY, [skills])
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return results

def execute_market_insights_query(skills):
    """Execute job market insights query"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute(JOB_MARKET_INSIGHTS_QUERY, [skills])
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return results

def execute_recommendation_performance_query(user_id):
    """Execute recommendation performance query"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute(RECOMMENDATION_PERFORMANCE_QUERY, [user_id, user_id])
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return results[0] if results else None

def execute_compatibility_analysis_query(user_id, min_score=30.0, limit=10):
    """Execute candidate-job compatibility analysis"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute(COMPATIBILITY_ANALYSIS_QUERY, [user_id, min_score, limit])
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return results

def execute_batch_recommendation_update():
    """Execute batch recommendation update for all users"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute(BATCH_RECOMMENDATION_UPDATE)
        return cursor.rowcount  # Number of rows affected
