import os
import sys

# Add project directory to Python path
project_dir = r"c:\Users\yazhi\OneDrive\yazhu\2026 final year project\new job recommandation_page\Resume-Analyzer"
sys.path.insert(0, project_dir)
sys.path.insert(0, os.path.join(project_dir, 'venv', 'Lib', 'site-packages'))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_analyzer.settings')

try:
    import django
    django.setup()
    
    from jobs.recommendation_views import get_dynamic_recommendations
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    print('🔍 Testing API Response Structure')
    print('=' * 50)
    
    # Test with a sample user
    from django.test import RequestFactory
    from django.contrib.auth.models import User
    
    # Create a test user
    test_user = User.objects.create_user(
        username='testuser',
        email='test@example.com'
    )
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/api/jobs/recommendations/')
    request.user = test_user
    
    print(f'Test User: {test_user.username}')
    
    # Call the API endpoint
    response = get_dynamic_recommendations(request)
    
    print(f'Status Code: {response.status_code}')
    print(f'Content Type: {response.get("Content-Type", "unknown")}')
    
    # Parse and display the response
    try:
        import json
        data = json.loads(response.content)
        print(f'Response Keys: {list(data.keys())}')
        
        if 'recommendations' in data:
            recommendations = data['recommendations']
            print(f'Total recommendations: {len(recommendations)}')
            
            for i, rec in enumerate(recommendations[:3], 1):
                print(f'\n📋 Recommendation {i}:')
                print(f'   Job Title: {rec.get("job", {}).get("title", "N/A")}')
                print(f'   Company: {rec.get("job", {}).get("company", "N/A")}')
                
                # Check match data
                match_data = rec.get('match', {})
                print(f'   Match Data: {list(match_data.keys())}')
                
                # Check for score fields
                if 'match_percentage' in match_data:
                    print(f'   Match Percentage: {match_data["match_percentage"]}%')
                if 'overall_score' in match_data:
                    print(f'   Overall Score: {match_data["overall_score"]}%')
                if 'skills_match_score' in match_data:
                    print(f'   Skills Match Score: {match_data["skills_match_score"]}%')
                if 'experience_match_score' in match_data:
                    print(f'   Experience Score: {match_data["experience_match_score"]}%')
                if 'education_match_score' in match_data:
                    print(f'   Education Score: {match_data["education_match_score"]}%')
                
                # Check for required/missing skills
                if 'matched_skills' in match_data:
                    print(f'   Matched Skills: {match_data["matched_skills"]}')
                if 'missing_skills' in match_data:
                    print(f'   Missing Skills: {match_data["missing_skills"]}')
        
        else:
            print('❌ No recommendations found in response')
            
    except Exception as e:
        print(f'❌ Error parsing response: {e}')
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test user
        try:
            test_user.delete()
        except:
            pass
    
    print('\n' + '=' * 50)
    print('🎯 Test Complete!')
    print('This shows the exact API response structure the frontend should expect.')
    
except Exception as e:
    print(f'❌ Test failed: {e}')
    import traceback
    traceback.print_exc()
