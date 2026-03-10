import os
import json
import re
from io import BytesIO
from PIL import Image
import pdfplumber
import docx
import pytesseract
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer


class ResumeTextExtractor:
    """Extract text from various resume file formats"""
    
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
    
    def extract_text(self, file_path, file_type):
        """Extract text from resume file based on file type"""
        try:
            if file_type.lower() == 'pdf':
                return self._extract_from_pdf(file_path)
            elif file_type.lower() == 'docx':
                return self._extract_from_docx(file_path)
            elif file_type.lower() in ['jpg', 'jpeg', 'png']:
                return self._extract_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise Exception(f"Error extracting text: {str(e)}")
    
    def _extract_from_pdf(self, file_path):
        """Extract text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
        
        return text.strip() if text else ""
    
    def _extract_from_docx(self, file_path):
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")
    
    def _extract_from_image(self, file_path):
        """Extract text from image using OCR"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            raise Exception(f"Error performing OCR: {str(e)}")


class ResumeParser:
    """Parse and extract structured information from resume text"""
    
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        
        # Common skill keywords
        self.skill_keywords = [
             # Programming Languages
            'python', 'java', 'javascript', 'typescript' , 'c++', 'c#',
            'rust', 'kotlin', 'swift', 'php', 'ruby', 'dart', 'r language',
            'matlab', 'bash', 'powershell',

            # Frontend
            'html', 'css', 'sass', 'bootstrap', 'tailwind', 
            'react', 'next.js', 'angular', 'vue', 'redux',

            # Backend
            'node.js', 'express', 'django', 'flask', 'fastapi',
            'spring', 'spring boot', 'laravel', 'asp.net',

            # Mobile Development
            'android', 'ios', 'react native', 'flutter', 'xamarin',

            # Databases
            'mysql', 'postgresql', 'sql', 'mongodb', 'sqlite', 'oracle',
            'redis', 'firebase', 'cassandra', 'dynamodb',

            # Cloud Platforms
            'aws', 'azure', 'gcp', 'google cloud', 'heroku',

            # DevOps & Tools
            'docker', 'kubernetes', 'jenkins', 'github actions',
            'gitlab', 'terraform', 'ansible', 'linux', 'nginx',

            # APIs & Architecture
            'rest api', 'graphql', 'microservices',

            # Data Science & AI
            'machine learning', 'deep learning', 'data science',
            'artificial intelligence', 'nlp', 'computer vision',
            'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'matplotlib', 'seaborn',
            'opencv', 'xgboost',

            # Big Data
            'hadoop', 'spark', 'kafka', 'hive',

            # Testing
            'unit testing', 'integration testing',
            'selenium', 'jest', 'pytest',

            # UI/UX
            'ui/ux', 'figma', 'adobe xd', 'photoshop', 'illustrator',

            # Version Control
            'git', 'github', 'bitbucket',

            # Methodologies
            'agile', 'scrum',

            # Security
            'cybersecurity', 'penetration testing',
            'ethical hacking', 'owasp',

            # ERP / CRM
            'sap', 'salesforce',

            # Data & BI Tools
            'tableau', 'power bi'
        ]
        
        # Education keywords
        self.education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'degree', 'university',
            'college', 'institute', 'engineering', 'computer science', 'information technology',
            'business administration', 'mba', 'b.tech', 'm.tech', 'b.sc', 'm.sc'
        ]
    
    def parse_resume(self, text):
        """Parse resume text and extract structured information"""
        processed_text = self._preprocess_text(text)
        
        return {
            'processed_text': processed_text,
            'extracted_skills': self._extract_skills(text, processed_text),
            'extracted_education': self._extract_education(text),
            'extracted_experience': self._extract_experience(text),
            'extracted_contact_info': self._extract_contact_info(text),
            # NEW: Additional extractions
            'extracted_projects': self._extract_projects(text),
            'extracted_certificates': self._extract_certificates(text),
            'extracted_achievements': self._extract_achievements(text)
        }
    
    def _preprocess_text(self, text):
        """Preprocess text for NLP analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\-@.,]', ' ', text)
        
        # Tokenize and remove stopwords
        tokens = word_tokenize(text)
        tokens = [token for token in tokens if token not in stopwords.words('english')]
        
        # Lemmatize
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(token) for token in tokens]
        
        return ' '.join(tokens)
    
    def _extract_skills(self, original_text, processed_text):
        """Extract skills from resume text"""
        skills = set()
        text_lower = original_text.lower()
        for skill in sorted(self.skill_keywords, key=len, reverse=True):
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                skills.add(skill.lower())
        
        
        # Use NLP to extract technical terms
        doc = self.nlp(original_text)
        
        
        skills_list = list(skills)

        # Remove duplicates (case insensitive)
        unique_skills = list({
            skill.strip().lower(): skill.strip()
            for skill in skills_list
            }.values())

            # Remove long broken sentences (garbage extraction)
        unique_skills = [s for s in unique_skills if len(s.split()) <= 3]
            # Optional: Remove standalone "sql" if mysql exists
        if any("mysql" in s.lower() for s in unique_skills):
               unique_skills = [s for s in unique_skills if s.lower() != "sql"]
        if "javascript" in unique_skills and "java" in unique_skills:
            unique_skills.remove("java")

        return unique_skills
    

    def _extract_education(self, text):
        education = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # 1. Section Boundaries
        start_headers = ["education", "academic background", "academic profile"]
        end_headers = ["experience", "skills", "projects", "certifications", "additional"]

        # 2. Strict Degree Regex 
        # This looks for common degree prefixes or full names
        degree_pattern = r"(?i)\b(B\.E|BE|B\.Tech|M\.Tech|B\.Sc|M\.Sc|Bachelor|Master|MBA|PHD|SSLC|HSC)\b"

        is_in_section = False
        section_lines = []

        # Step A: Isolate the Education Section
        for line in lines:
            line_lower = line.lower()
            if any(line_lower == h or line_lower == h + ":" for h in start_headers):
                is_in_section = True
                continue
            if is_in_section:
                if any(line_lower == h or line_lower == h + ":" for h in end_headers):
                    break
                section_lines.append(line)

        # Step B: Extract Degrees from the isolated section
        for line in section_lines:
            # Ignore contact info just in case
            if any(x in line.lower() for x in ["@", "+91", "linkedin"]):
                continue

            # Check for the degree pattern
            if re.search(degree_pattern, line):
                # Clean the line: if it contains a comma (like "University, Degree"), 
                # we try to extract just the degree part.
                parts = re.split(r'[,|]', line)
                degree_found = line # Default
                
                for part in parts:
                    if re.search(degree_pattern, part):
                        degree_found = part.strip()
                        break

                education.append({
                    "degree": degree_found,
                    "institution": "",
                    "year": ""
                })

        # Step C: Deduplicate
        unique = []
        seen = set()
        for edu in education:
            if edu["degree"].lower() not in seen:
                unique.append(edu)
                seen.add(edu["degree"].lower())

        return unique
    def _extract_experience(self, text):
        experience = []
        # Split text into lines and remove empty ones
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # 1. Flexible Section Detection
        # Matches "Experience", "WORK HISTORY", "Professional Experience:", etc.
        start_headers = r"^(experience|work|employment|history|professional|career|background)"
        # Matches common following sections to know when to stop
        end_headers = r"^(education|skills|projects|certifications|technologies|additionals|languages|summary|objective)"
        
        # 2. Universal Date Regex
        # This covers: June 2024, Jun 2024, 06/2024, 2024-2026, Present, etc.
        date_regex = r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|Present|Current|\d{1,2}/\d{2,4}|\b\d{4}\b))"

        is_in_section = False
        section_lines = []

        # Step A: Collect everything between the 'Experience' and 'Education/Skills' headers
        for line in lines:
            clean_line = line.strip().lower()
            
            if re.search(start_headers, clean_line):
                is_in_section = True
                continue
                
            if is_in_section:
                if re.search(end_headers, clean_line):
                    break
                section_lines.append(line)

        # Step B: Scan the section for job entries using dates as anchors
        for i, line in enumerate(section_lines):
            # Look for a date in the current line
            date_matches = re.findall(date_regex, line, re.IGNORECASE)
            
            if date_matches:
                # We found a date! Now we need to find the title.
                # Usually, the title is on the same line as the date, or 1-2 lines ABOVE it.
                duration = " - ".join(date_matches)
                
                # Logic to find the Position Title:
                # 1. Check if there's text on the same line before the date
                title = line.split(date_matches[0])[0].strip()
                
                # 2. If same-line text is empty/too short, look at the line ABOVE
                if len(title) < 3 and i > 0:
                    title = section_lines[i-1]
                
                # 3. Clean up the title (remove bullets, company names, or locations)
                title = re.sub(r"^[•\-\*]\s*", "", title) # Remove bullets
                title = title.split("-")[0].split("|")[0].strip() # Remove " - Location"

                if title:
                    experience.append({
                        "position": title,
                        "duration": duration
                    })

        # Deduplicate entries
        unique_exp = []
        seen = set()
        for exp in experience:
            if exp["position"].lower() not in seen:
                unique_exp.append(exp)
                seen.add(exp["position"].lower())

        return unique_exp
    def _extract_projects(self, text):
        """Extract project information from resume"""

        projects = []
        text_lower = text.lower()

        # Find the project section
        project_section_match = re.search(
            r'(projects?|academic projects?|personal projects?)[:\s]*(.*?)(skills|education|experience|certifications|$)',
            text_lower,
            re.DOTALL
        )

        if project_section_match:
            project_section = project_section_match.group(2)

            # Split by bullet points or new lines
            lines = re.split(r'[\n•\-]', project_section)

            for line in lines:
                cleaned = line.strip()

                if len(cleaned) > 15:
                    projects.append(cleaned)

        return list(set(projects))
    
    def _extract_certificates(self, text):
        """Extract certificate information from resume"""
        certificates = []
        text_lower = text.lower()
        
        # Certificate patterns
        cert_patterns = [
            r'(certified\s+[^.!?]*?[a-zA-Z][^.!?]*)',
            r'([^.!?]*?certificate[s]?[^.!?]*?[a-zA-Z][^.!?]*)',
            r'([^.!?]*?certification[s]?[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(aws certified[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(google certified[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(microsoft certified[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(pmp[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(cisco[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(comptia[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(iso[^.!?]*?[a-zA-Z][^.!?]*)'
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 5:  # Filter out very short matches
                    certificates.append(match.strip())
        
        return list(set(certificates))
    
    def _extract_achievements(self, text):
        """Extract achievement information from resume"""
        achievements = []
        text_lower = text.lower()
        
        # Achievement patterns
        achievement_patterns = [
            r'[-•*]\s*([^.!?]*?(?:achieved|awarded|recognized|honor|award|trophy)[^.!?]*?[a-zA-Z][^.!?]*)',
            r'[-•*]\s*([^.!?]*?(?:promotion|increased|improved|optimized|reduced)[^.!?]*?[a-zA-Z][^.!?]*)',
            r'[-•*]\s*([^.!?]*?(?:saved|generated|led|managed|won|success)[^.!?]*?[a-zA-Z][^.!?]*)',
            r'([^.!?]*?\d+%[^.!?]*?(?:increase|decrease|improvement|reduction)[^.!?]*)',
            r'([^.!?]*?\$?\d+(?:,\d{3})*(?:\.\d{2})?[^.!?]*?(?:saved|generated|revenue|profit|cost)[^.!?]*)',
            r'([^.!?]*?(?:first|top|best|excellent|outstanding)[^.!?]*?[a-zA-Z][^.!?]*)'
        ]
        
        for pattern in achievement_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 8:  # Filter out very short matches
                    achievements.append(match.strip())
        
        return list(set(achievements))
    def _extract_contact_info(self, text):
        """Extract contact information"""
        contact_info = {}

        lines = text.split("\n")
        # Assume first line is name
        if lines:
            possible_name = lines[0].strip()

            if len(possible_name.split()) <= 4:
                contact_info['name'] = possible_name
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        # Phone
        phone_pattern = r'\+?\d[\d\s\-]{8,15}'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact_info['phone'] = phones[0]
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin_matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_matches:
            contact_info['linkedin'] = 'https://' + linkedin_matches[0]
        
        return contact_info


class FeatureVectorizer:
    """Convert resume text to feature vectors using TF-IDF"""
    
    def __init__(self, max_features=5000):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=1.0
        )
        self.is_fitted = False
    
    def fit_transform(self, documents):
        """Fit vectorizer and transform documents"""
        vectors = self.vectorizer.fit_transform(documents)
        self.is_fitted = True
        return vectors.toarray().tolist()
    
    def transform(self, documents):
        """Transform documents using fitted vectorizer"""
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted before transforming")
        vectors = self.vectorizer.transform(documents)
        return vectors.toarray().tolist()
    
    def get_feature_names(self):
        """Get feature names (vocabulary)"""
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted first")
        return self.vectorizer.get_feature_names_out().tolist()

def find_skill_gap(resume_skills, job_skills):
    resume_set = set(skill.lower() for skill in resume_skills)
    job_set = set(skill.lower() for skill in job_skills)

    gap = job_set - resume_set
    return list(gap)