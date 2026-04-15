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
from pdf2image import convert_from_path


class ResumeTextExtractor:
    """Extract text from various resume file formats"""
    
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

    def extract_text(self, file_path, file_type):
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
        text = ""

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if page_text:
                    text += page_text + "\n"

        # 🔥 If no text → use OCR
        if len(text.strip()) < 50:
            images = convert_from_path(file_path)
            for img in images:
                text += pytesseract.image_to_string(img)

        return text.strip()

    def _extract_from_docx(self, file_path):
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")

    def _extract_from_image(self, file_path):
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

        self.skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#',
            'rust', 'kotlin', 'swift', 'php', 'ruby', 'dart', 'r language',
            'matlab', 'bash', 'powershell',
            'html', 'css', 'sass', 'bootstrap', 'tailwind',
            'react', 'next.js', 'angular', 'vue', 'redux',
            'node.js', 'express', 'django', 'flask', 'fastapi',
            'spring', 'spring boot', 'laravel', 'asp.net',
            'android', 'ios', 'react native', 'flutter', 'xamarin',
            'mysql', 'postgresql', 'sql', 'mongodb', 'sqlite', 'oracle',
            'redis', 'firebase', 'cassandra', 'dynamodb',
            'aws', 'azure', 'gcp', 'google cloud', 'heroku',
            'docker', 'kubernetes', 'jenkins', 'github actions',
            'gitlab', 'terraform', 'ansible', 'linux', 'nginx',
            'rest api', 'graphql', 'microservices',
            'machine learning', 'deep learning', 'data science',
            'artificial intelligence', 'nlp', 'computer vision',
            'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'matplotlib', 'seaborn',
            'opencv', 'xgboost',
            'hadoop', 'spark', 'kafka', 'hive',
            'unit testing', 'integration testing',
            'selenium', 'jest', 'pytest',
            'ui/ux', 'figma', 'adobe xd', 'photoshop', 'illustrator',
            'git', 'github', 'bitbucket',
            'agile', 'scrum',
            'cybersecurity', 'penetration testing',
            'ethical hacking', 'owasp',
            'sap', 'salesforce',
            'tableau', 'power bi'
        ]

        self.education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'degree', 'university',
            'college', 'institute', 'engineering', 'computer science', 'information technology',
            'business administration', 'mba', 'b.tech', 'm.tech', 'b.sc', 'm.sc'
        ]

    def parse_resume(self, text):
        processed_text = self._preprocess_text(text)
        return {
            'processed_text': processed_text,
            'extracted_skills': self._extract_skills(text, processed_text),
            'extracted_education': self._extract_education(text),
            'extracted_experience': self._extract_experience(text),
            'extracted_contact_info': self._extract_contact_info(text),
            'extracted_projects': self._extract_projects(text),
            'extracted_certificates': self._extract_certificates(text),
            'extracted_achievements': self._extract_achievements(text)
        }

    def _preprocess_text(self, text):
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\-@.,]', ' ', text)
        tokens = word_tokenize(text)
        tokens = [token for token in tokens if token not in stopwords.words('english')]
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(token) for token in tokens]
        return ' '.join(tokens)

    def _extract_skills(self, original_text, processed_text):
        skills = set()
        text_lower = original_text.lower()
        for skill in sorted(self.skill_keywords, key=len, reverse=True):
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                skills.add(skill.lower())
        skills_list = list(skills)
        unique_skills = list({
            skill.strip().lower(): skill.strip()
            for skill in skills_list
        }.values())
        unique_skills = [s for s in unique_skills if len(s.split()) <= 3]
        if any("mysql" in s.lower() for s in unique_skills):
            unique_skills = [s for s in unique_skills if s.lower() != "sql"]
        if "javascript" in unique_skills and "java" in unique_skills:
            unique_skills.remove("java")
        return unique_skills

    def _extract_education(self, text):
        """Extract education details."""

        education = []
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in text.split("\n")]

        DEGREE_RE = re.compile(
            r"\b(?:"
            r"bachelor(?:'?s)?(?:\s+of\s+\w+(?:\s+\w+)*)?"
            r"|master(?:'?s)?(?:\s+of\s+\w+(?:\s+\w+)*)?"
            r"|doctor(?:ate|'?s)?(?:\s+of\s+\w+(?:\s+\w+)*)?"
            r"|associate(?:'?s)?(?:\s+of\s+\w+(?:\s+\w+)*)?"
            r"|honours?|undergraduate|postgraduate"
            r"|b\.?\s*tech|m\.?\s*tech"
            r"|b\.?\s*e\.?\b|m\.?\s*e\.?\b"
            r"|b\.?\s*sc|m\.?\s*sc"
            r"|b\.?\s*s\.?\b|m\.?\s*s\.?\b"
            r"|b\.?\s*a\.?\b|m\.?\s*a\.?\b"
            r"|b\.?\s*com|m\.?\s*com"
            r"|m\.?\s*b\.?\s*a|ph\.?\s*d"
            r"|be\b|me\b"
            r")\b",
            re.IGNORECASE,
        )

        YEAR_RE = re.compile(
            r"((?:19|20)\d{2})\s*(?:[-–—\u2013\u2014]|to)\s*((?:19|20)\d{2}|present|current|now)"
            r"|((?:19|20)\d{2})",
            re.IGNORECASE,
        )

        MONTH_YEAR_RE = re.compile(
            r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
            r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
            r"\s*\d{4}\s*(?:[-–—\u2013\u2014to]+)\s*"
            r"(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
            r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*\d{4}"
            r"|present|current|now)",
            re.IGNORECASE,
        )

        INSTITUTION_RE = re.compile(
            r"\b(?:"
            r"(?:\w+(?:[\s\-]\w+){0,6})\s+(?:university|college|institute(?:\s+of\s+technology)?|polytechnic|academy|conservatory|seminary|faculty)"
            r"|(?:university|college|institute|polytechnic)\s+of\s+(?:\w+(?:[\s\-]\w+){0,5})"
            r"|college\s+of\s+(?:engineering|arts?|science|technology|medicine|law|commerce)"
            r"|\b(?:MIT|CalTech|UCLA|USC|NYU|LSE|VIT|SRM|PSG|SASTRA|BITS|SRMIST|IIT|NIT)\b"
            r")\b",
            re.IGNORECASE,
        )

        INSTITUTION_KEYWORDS = re.compile(
            r'\b(?:university|college|institute|polytechnic|academy|iit|nit|bits|vit|srm|sastra|psg)\b',
            re.IGNORECASE
        )

        SCHOOL_ONLY_RE = re.compile(
            r"\b(?:high\s+school|secondary\s+school|higher\s+secondary|matriculat|ged"
            r"|10th|12th|hsc|ssc|class\s+(?:x|xii|10|12)|matric|hr\.?\s*sec)\b",
            re.IGNORECASE,
        )

        GPA_RE = re.compile(
            r"\b(?:o?gpa|cgpa|grade\s+point)\s*[:\-]?\s*(\d+\.\d+(?:\s*/\s*\d+\.\d+)?)",
            re.IGNORECASE,
        )

        FIELD_RE = re.compile(
            r"\b(?:in|of)\s+([A-Za-z][A-Za-z\s&\-]{2,50}?)(?=\s{2,}|\t|,\s*[A-Z]|$)",
            re.IGNORECASE
        )

        KNOWN_FIELDS = re.compile(
            r"\b(?:computer\s+science|information\s+technology|electronics|electrical"
            r"|mechanical|civil|chemical|biotechnology|data\s+science|artificial\s+intelligence"
            r"|machine\s+learning|mathematics|physics|chemistry|biology|commerce"
            r"|business\s+administration|finance|accounting|economics|law|medicine)\b",
            re.IGNORECASE
        )

        FIELD_NOISE = re.compile(
            r"\b(?:with|and|the|a|an|for|from|at|in|on|by|\d+)\s*$",
            re.IGNORECASE
        )

        LOCATION_NOISE = re.compile(
            r'\s*[,\-]?\s*\b(?:chennai|mumbai|delhi|bangalore|bengaluru|hyderabad|pune|kolkata'
            r'|chidambaram|coimbatore|madurai|trichy|tiruchirappalli|salem|vellore|erode'
            r'|tirunelveli|thoothukudi|tuticorin|kanchipuram|tiruppur|nagercoil|thanjavur'
            r'|pondicherry|puducherry|tiruvannamalai|dover'
            r'|tamil\s+nadu|maharashtra|karnataka|kerala|andhra\s+pradesh|telangana'
            r'|india|usa|uk|remote)\b.*$',
            re.IGNORECASE
        )

        START_HEADERS = re.compile(
            r"\b(?:education(?:al)?(?:\s+(?:background|history|qualifications?|summary))?"
            r"|academic\s+(?:background|history|qualifications?|record)"
            r"|schooling|degrees?|qualifications?)\b",
            re.IGNORECASE,
        )

        END_HEADERS = re.compile(
            r"\b(?:experience|work\s+history|employment|professional\s+background"
            r"|skill|competenc|expertise|technolog|project|certification|publication"
            r"|award|honor|activit|interest|hobbies|language|reference|summary|objective"
            r"|profile|contact|volunteer|achievement|accomplishment|research|affiliation)\b",
            re.IGNORECASE,
        )

        in_section = False
        section_lines = []

        for line in lines:
            lower = line.lower().strip()
            if not in_section:
                if len(line) < 60 and START_HEADERS.search(lower):
                    in_section = True
                    continue
            else:
                if lower and len(line) < 60 and END_HEADERS.search(lower):
                    break
                section_lines.append(line)

        if not section_lines:
            section_lines = [l for l in lines if l]

        def clean_location(value):
            return LOCATION_NOISE.sub("", value).strip(" ,;-–")

        def extract_year(line):
            my = MONTH_YEAR_RE.search(line)
            if my:
                return my.group().strip()
            ym = YEAR_RE.search(line)
            if ym:
                if ym.group(1):
                    end = ym.group(2).capitalize() if ym.group(2).lower() in ('present', 'current', 'now') else ym.group(2)
                    return f"{ym.group(1)} - {end}"
                elif ym.group(3):
                    return ym.group(3)
            return ""

        def line_has_year(line):
            return bool(YEAR_RE.search(line) or MONTH_YEAR_RE.search(line))

        blocks = []
        current = []
        for line in section_lines:
            if line:
                current.append(line)
            else:
                if current:
                    blocks.append(current)
                    current = []
        if current:
            blocks.append(current)

        if len(blocks) <= 1 and len(section_lines) > 3:
            blocks = []
            i = 0
            while i < len(section_lines):
                line = section_lines[i]
                lhas_year = line_has_year(line)
                lhas_degree = bool(DEGREE_RE.search(line.lower()))
                lhas_institution = bool(INSTITUTION_KEYWORDS.search(line))
                lhas_gpa = bool(GPA_RE.search(line))

                if (lhas_year or lhas_institution) and not lhas_degree:
                    group = [line]
                    if i + 1 < len(section_lines):
                        group.append(section_lines[i + 1])
                        i += 2
                    else:
                        i += 1
                    blocks.append(group)
                elif lhas_gpa and not lhas_degree and not lhas_institution:
                    if blocks:
                        blocks[-1].append(line)
                    else:
                        blocks.append([line])
                    i += 1
                elif lhas_degree and not lhas_year and not lhas_institution:
                    if blocks:
                        blocks[-1].append(line)
                    else:
                        blocks.append([line])
                    i += 1
                else:
                    blocks.append([line])
                    i += 1

        def parse_block(block_lines):
            full_text = " ".join(block_lines)
            full_lower = full_text.lower()

            if not DEGREE_RE.search(full_lower):
                return None
            if SCHOOL_ONLY_RE.search(full_text) and not INSTITUTION_RE.search(full_text):
                return None

            entry = {"degree": "", "field_of_study": "", "institution": "", "year": "", "gpa": ""}
            degree_line = ""

            for line in block_lines:
                line_lower = line.lower()

                if not entry["degree"]:
                    dm = DEGREE_RE.search(line_lower)
                    if dm:
                        degree_line = line.strip()
                        raw = line[dm.start():].strip()
                        raw = re.split(r',\s*(?=[A-Z])', raw)[0].strip()
                        raw = re.split(r'\s{2,}', raw)[0].strip()
                        raw = clean_location(raw)
                        entry["degree"] = raw

                if not entry["year"]:
                    entry["year"] = extract_year(line)

                gm = GPA_RE.search(line)
                if gm and not entry["gpa"]:
                    entry["gpa"] = gm.group(1)

                if not entry["institution"] and line.strip() != degree_line:
                    line_no_year = YEAR_RE.sub("", MONTH_YEAR_RE.sub("", line)).strip(" –-—")
                    im = INSTITUTION_RE.search(line_no_year)
                    if im:
                        entry["institution"] = clean_location(im.group().strip())

            if not entry["institution"]:
                best_line, best_score = "", 0
                for ln in block_lines:
                    if ln.strip() == degree_line:
                        continue
                    score = len(INSTITUTION_KEYWORDS.findall(ln))
                    if score > best_score:
                        best_score, best_line = score, ln.strip()
                if best_score > 0:
                    cleaned = YEAR_RE.sub("", MONTH_YEAR_RE.sub("", best_line)).strip(" –-—")
                    inst_match = INSTITUTION_RE.search(cleaned)
                    if inst_match:
                        entry["institution"] = clean_location(inst_match.group().strip())
                    else:
                        entry["institution"] = clean_location(cleaned.split(",")[0].strip())

            if not entry["institution"] and hasattr(self, "nlp"):
                doc = self.nlp(full_text)
                for ent in doc.ents:
                    if ent.label_ in ("ORG", "GPE"):
                        if ent.text.strip().lower() != degree_line.lower():
                            entry["institution"] = ent.text
                            break

            for source in [degree_line, full_text]:
                if entry["field_of_study"]:
                    break
                for m in FIELD_RE.finditer(source):
                    candidate = FIELD_NOISE.sub("", m.group(1)).strip(" ,;-–")
                    candidate = clean_location(candidate)
                    if candidate and len(candidate.split()) <= 6 and not INSTITUTION_KEYWORDS.search(candidate):
                        entry["field_of_study"] = candidate
                        break

            if not entry["field_of_study"]:
                fm = KNOWN_FIELDS.search(full_text)
                if fm:
                    entry["field_of_study"] = fm.group().strip().title()

            return entry if (entry["degree"] or entry["institution"]) else None

        for block in blocks:
            result = parse_block(block)
            if result:
                if not result["year"] or not result["gpa"]:
                    for line in section_lines:
                        if not result["year"]:
                            y = extract_year(line)
                            if y:
                                result["year"] = y
                        if not result["gpa"]:
                            gm = GPA_RE.search(line)
                            if gm:
                                result["gpa"] = gm.group(1)
                        if result["year"] and result["gpa"]:
                            break
                education.append(result)

        unique = []
        seen = set()
        for edu in education:
            key = (edu["degree"] + edu["institution"] + edu["year"]).lower().strip()
            if key not in seen and key != "":
                unique.append(edu)
                seen.add(key)

        return unique

    def _extract_experience(self, text):
        """Extract work experience — handles company-first and title-first layouts."""

        experience = []
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in text.split("\n")]

        EXPERIENCE_HEADERS = {
            'experience', 'work experience', 'internships', 'internship',
            'professional experience', 'employment history', 'work history',
            'career history', 'positions of responsibility'
        }

        END_HEADERS = re.compile(
            r"^(?:education|academic|qualification|technical\s+skills?|skills?"
            r"|technologies|tools|projects?|certifications?|publications?"
            r"|awards?|honors?|activities|interests|languages?|references?"
            r"|summary|objective|profile|volunteer|achievements?|additional"
            r"|extra.curricular|hobbies|additionals?)\s*$",
            re.IGNORECASE,
        )

        in_section = False
        section_lines = []

        for line in lines:
            lower = line.strip().lower()
            if not in_section:
                if lower in EXPERIENCE_HEADERS:
                    in_section = True
                    continue
            else:
                if lower and len(line.strip()) < 40 and END_HEADERS.match(lower):
                    break
                section_lines.append(line)

        if not section_lines:
            for i, line in enumerate(lines):
                if line.strip().lower() in EXPERIENCE_HEADERS:
                    for subsequent in lines[i + 1:]:
                        slow = subsequent.strip().lower()
                        if slow and len(subsequent.strip()) < 40 and END_HEADERS.match(slow):
                            break
                        section_lines.append(subsequent.strip())
                    break

        if not section_lines:
            return experience

        # ── Patterns ──────────────────────────────────────────────────────────────

        DATE_TOKEN = (
            r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
            r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
            r"\s*(?:\'|\s)?\d{2,4}"
            r"|\d{1,2}[\/\-]\d{2,4}"
            r"|\b(?:19|20)\d{2}\b"
            r"|\b(?:present|current|now|ongoing|till\s+date|to\s+date)\b"
        )

        DURATION_RE = re.compile(
            rf"({DATE_TOKEN})\s*(?:[-–—\u2013\u2014to]+)\s*({DATE_TOKEN})",
            re.IGNORECASE,
        )

        INTERNSHIP_RE = re.compile(
            r"\b(?:intern(?:ship)?|trainee|apprentice|placement|industrial\s+training"
            r"|summer\s+(?:intern|project|training)|co[\-\s]?op)\b",
            re.IGNORECASE,
        )

        TITLE_SIGNAL_RE = re.compile(
            r"\b(?:engineer|developer|analyst|designer|manager|lead|architect|consultant"
            r"|specialist|associate|executive|coordinator|officer|intern|trainee"
            r"|scientist|researcher|administrator|director|head|vp|president|cto|ceo"
            r"|development|testing|design|ui\/ux|frontend|backend|fullstack|full.stack"
            r"|marketing|sales|support|operations|devops|qa|sre)\b",
            re.IGNORECASE,
        )

        BULLET_RE = re.compile(r"^[◦•\*▪➢➤►–\-]")

        LOCATION_STRIP_RE = re.compile(
            r'\s*[-–]?\s*(?:remote|on[\-\s]?site|hybrid)?\s*[-–]?\s*'
            r'(?:dover|usa|uk|india|chennai|bangalore|mumbai|delhi|pune|hyderabad'
            r'|pondicherry|chidambaram|coimbatore|tamil\s+nadu)[^$]*$',
            re.IGNORECASE
        )

        def strip_location(text):
            return LOCATION_STRIP_RE.sub("", text).strip(" ,–-")

        def truncate_company(name):
            """Truncate overly long company names at ' - ' separator."""
            if name and len(name) > 50:
                parts = re.split(r'\s+[-–]\s+', name)
                return parts[0].strip()
            return name

        # ── Block splitting: split when a line has content BEFORE a date range ─────
        blocks = []
        current = []
        for line in section_lines:
            if not line:
                continue
            dm = DURATION_RE.search(line)
            if dm and current:
                before = line[:dm.start()].strip()
                if before and len(before) > 5 and not BULLET_RE.match(before):
                    # New entry line — end previous block, start new one with this line
                    blocks.append(current)
                    current = [line]
                    blocks.append(current)
                    current = []
                else:
                    # Date at end of bullet/continuation — belongs to current block
                    current.append(line)
                    blocks.append(current)
                    current = []
            else:
                current.append(line)
        if current:
            blocks.append(current)
        # Merge consecutive no-date blocks together, then merge with next dated block
        merged_blocks = []
        i = 0
        while i < len(blocks):
            block = blocks[i]
            has_dur = any(DURATION_RE.search(l) for l in block)
            if not has_dur:
                # Keep merging with next blocks until we hit one with a date or run out
                combined = block[:]
                j = i + 1
                while j < len(blocks):
                    next_has_dur = any(DURATION_RE.search(l) for l in blocks[j])
                    combined += blocks[j]
                    j += 1
                    if next_has_dur:
                        break
                merged_blocks.append(combined)
                i = j
            else:
                merged_blocks.append(block)
                i += 1
        blocks = merged_blocks

        processed_titles = set()

        def parse_block(block):
            entry = {"position": "", "company": "", "duration": "", "type": "experience"}

            # Skip blocks with no date range
            non_bullet = [l for l in block if not BULLET_RE.match(l.strip()) and l.strip()]
            if not non_bullet:
                return None
            if not non_bullet:
                return None
 
            # Also skip if no real company/title signal at all
            full_text_nb = " ".join(non_bullet)
            if len(full_text_nb.strip()) < 5:
                return None

            title_lines = []
            company_lines = []
            duration_lines = []

            for line in block:
                stripped = line.strip()
                if not stripped or BULLET_RE.match(stripped):
                    continue

                dm = DURATION_RE.search(stripped)
                if dm:
                    duration_lines.append(f"{dm.group(1).strip()} - {dm.group(2).strip()}")
                    before = stripped[:dm.start()].strip().rstrip(",-– (")
                    before = strip_location(before)
                    before = re.sub(r'\s*\((?:remote|on.?site|hybrid)\)', '', before, flags=re.IGNORECASE).strip(" -–")
                    if before and len(before) > 2:
                        if TITLE_SIGNAL_RE.search(before) or INTERNSHIP_RE.search(before):
                            title_lines.append(before)
                        elif not re.search(r'[.!?]$', before):
                            company_lines.append(before)
                elif INTERNSHIP_RE.search(stripped):
                    clean = strip_location(stripped)
                    title_lines.append(clean)
                    m = re.search(r"\bat\s+([A-Z][A-Za-z0-9\s&\.]{2,40})", clean)
                    if m:
                        company_lines.append(m.group(1).strip())
                elif TITLE_SIGNAL_RE.search(stripped) and not DURATION_RE.search(stripped):
                    if not re.search(r'[.!?]$', stripped) and len(stripped.split()) <= 6:
                        title_lines.append(stripped)
                else:
                    if (len(stripped) < 80
                            and re.match(r"[A-Z]", stripped)
                            and not re.search(r'[.!?]$', stripped)
                            and len(stripped.split()) <= 10):
                        company_lines.append(strip_location(stripped))

            # Assign duration
            if duration_lines:
                entry["duration"] = duration_lines[0]

            # Assign position
            if title_lines:
                raw = title_lines[0]
                raw = re.sub(r"\s*[\|]\s*.*$", "", raw)
                raw = raw.split(" at ")[0].strip()
                raw = DURATION_RE.sub("", raw).strip()
                entry["position"] = raw
            elif company_lines and duration_lines:
                for line in block:
                    s = line.strip()
                    if (s and not BULLET_RE.match(s)
                            and not DURATION_RE.search(s)
                            and s not in company_lines
                            and len(s) < 60
                            and re.match(r"[A-Z]", s)
                            and not re.search(r'[.!?]$', s)):
                        entry["position"] = s
                        break

            # Assign company
            remaining = [c for c in company_lines if c.lower() != entry["position"].lower()]
            if remaining:
                entry["company"] = truncate_company(strip_location(remaining[0]))
            else:
                for line in block:
                    m = re.search(r"(?:\bat\b|@|\|)\s*([A-Z][A-Za-z0-9\s&\.]{2,40}?)(?:\s*[\|,]|$)", line)
                    if m:
                        candidate = strip_location(m.group(1).strip())
                        if candidate.lower() != entry["position"].lower():
                            entry["company"] = truncate_company(candidate)
                            break

            # If position and company ended up the same, clear position
            # (frontend will use type fallback: "Internship" etc.)
            if (entry["position"] and entry["company"]
                    and entry["position"].lower() == entry["company"].lower()):
                entry["position"] = ""

            # Truncate overly long company names
            if entry["company"] and len(entry["company"]) > 50:
                entry["company"] = truncate_company(entry["company"])

            # spaCy ORG fallback
            if not entry["company"] and hasattr(self, "nlp"):
                doc = self.nlp(" ".join(non_bullet))
                for ent in doc.ents:
                    if ent.label_ == "ORG":
                        if ent.text.lower() != entry["position"].lower():
                            entry["company"] = ent.text
                            break

            if INTERNSHIP_RE.search(" ".join(block)):
                entry["type"] = "internship"

            return entry
        #print("=== EXP BLOCKS ===")
        #for i, b in enumerate(blocks):
        #    print(f"Block {i}: {b}")
        #print("==================")

        for block in blocks:
            if not block:
                continue
            result = parse_block(block)
            if result and (result["position"] or result["company"]):
                key = (result["position"] + result["company"]).lower().strip()
                if key and key not in processed_titles:
                    experience.append(result)
                    processed_titles.add(key)

        return experience

    def _extract_projects(self, text):
        projects = []
        text_lower = text.lower()
        project_section_match = re.search(
            r'(projects?|academic projects?|personal projects?)[:\s]*(.*?)(skills|education|experience|certifications|$)',
            text_lower, re.DOTALL
        )
        if project_section_match:
            project_section = project_section_match.group(2)
            lines = re.split(r'[\n•\-]', project_section)
            for line in lines:
                cleaned = line.strip()
                if len(cleaned) > 15:
                    projects.append(cleaned)
        return list(set(projects))

    def _extract_certificates(self, text):
        certificates = []
        text_lower = text.lower()
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
                if len(match.strip()) > 5:
                    certificates.append(match.strip())
        return list(set(certificates))

    def _extract_achievements(self, text):
        achievements = []
        text_lower = text.lower()
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
                if len(match.strip()) > 8:
                    achievements.append(match.strip())
        return list(set(achievements))

    def _extract_contact_info(self, text):
        contact_info = {}
        doc = self.nlp(text[:500])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                contact_info["name"] = ent.text
                break
        lines = text.split("\n")
        if lines:
            possible_name = lines[0].strip()
            if len(possible_name.split()) <= 4:
                contact_info['name'] = possible_name
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        phone_pattern = r'\+?\d[\d\s\-]{8,15}'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact_info['phone'] = phones[0]
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
        vectors = self.vectorizer.fit_transform(documents)
        self.is_fitted = True
        return vectors.toarray().tolist()

    def transform(self, documents):
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted before transforming")
        vectors = self.vectorizer.transform(documents)
        return vectors.toarray().tolist()

    def get_feature_names(self):
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted first")
        return self.vectorizer.get_feature_names_out().tolist()


def find_skill_gap(resume_skills, job_skills):
    resume_set = set(skill.lower() for skill in resume_skills)
    job_set = set(skill.lower() for skill in job_skills)
    gap = job_set - resume_set
    return list(gap)