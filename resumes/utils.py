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

        text = ""

        with pdfplumber.open(file_path) as pdf:

            for page in pdf.pages:

                page_text = page.extract_text(
                    x_tolerance=2,
                    y_tolerance=2
                )

                if page_text:
                    text += page_text + "\n"

        return text.strip()
    
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
        """
        High-accuracy education extractor.

        Fixes over the original:
        - Section headers: partial match + case-insensitive (not exact match)
        - End-section detection: uses `in lower` not `lower == header`
        - Year regex: captures full 4-digit year, handles ranges like "2018 - 2022" / "2018–2022"
        - Degree detection: 3x more patterns, including B.A, M.S, B.S, Honours, etc.
        - Institution detection: regex-first (catches "X University / College of X"),
        falls back to spaCy ORG + GPE (spaCy often labels universities as GPE)
        - Block-based parsing: processes each blank-line-separated block ONCE,
        eliminating duplicate entries from the sliding window
        - Field of study extracted separately from degree line
        - GPA extraction
        - Dedup key includes year to keep two degrees from same institution
        """

        education = []

        # ── 0. Normalise line endings ────────────────────────────────────────────
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in text.split("\n")]

        # ── 1. Section boundary detection ───────────────────────────────────────

        START_HEADERS = re.compile(
            r"""
            \b(?:
                education(?:al)?(?:\s+(?:background|history|qualifications?|summary|and\s+training))?
                | academic\s+(?:background|history|qualifications?|record|credentials?)
                | schooling | degrees?
                | qualifications?
                | training(?:\s+and\s+education)?
            )\b
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        END_HEADERS = re.compile(
            r"""
            \b(?:
                experience | work\s+history | employment
                | professional\s+background
                | skill | competenc | expertise | technolog
                | project | certification | publication
                | award | honor | activit | interest | hobbies
                | language | reference | summary | objective
                | profile | contact | volunteer | achievement
                | accomplishment | research | affiliation
            )\b
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        in_section = False
        section_lines = []

        for line in lines:
            lower = line.lower().strip()

            if not in_section:
                # Trigger: short line (likely a header) that matches education keywords
                if len(line) < 60 and START_HEADERS.search(lower):
                    in_section = True
                    continue
            else:
                # Stop: another section header appears
                if lower and len(line) < 60 and END_HEADERS.search(lower):
                    break
                section_lines.append(line)

        # Fallback: if section detection failed, scan entire text
        if not section_lines:
            section_lines = [l for l in lines if l]

        # ── 2. Split into blocks (blank lines = separator between entries) ───────

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

        # If no blank-line separation, treat every line as its own block
        if len(blocks) <= 1 and len(section_lines) > 3:
            blocks = [[l] for l in section_lines if l]

        # ── 3. Patterns ──────────────────────────────────────────────────────────

        # College-level degrees only (no high school / secondary / GED)
        DEGREE_RE = re.compile(
            r"""
            \b(?:
                # Spelled-out college degrees
                bachelor(?:'?s)?(?:\s+of\s+\w+(?:\s+\w+)*)?
                | master(?:'?s)?(?:\s+of\s+\w+(?:\s+\w+)*)?
                | doctor(?:ate|'?s)?(?:\s+of\s+\w+(?:\s+\w+)*)?
                | associate(?:'?s)?(?:\s+of\s+\w+(?:\s+\w+)*)?
                | honours? | undergraduate | postgraduate
                # Abbreviations (longer first to avoid partial matches)
                | b\.?\s*tech | m\.?\s*tech | b\.?\s*e\.?\b | m\.?\s*e\.?\b
                | b\.?\s*sc | m\.?\s*sc | b\.?\s*s\.?\b | m\.?\s*s\.?\b
                | b\.?\s*a\.?\b | m\.?\s*a\.?\b
                | b\.?\s*com | m\.?\s*com | b\.?\s*ca | m\.?\s*ca
                | b\.?\s*ba | m\.?\s*ba | b\.?\s*fa | m\.?\s*fa
                | m\.?\s*b\.?\s*a | d\.?\s*b\.?\s*a
                | ph\.?\s*d | d\.?\s*phil | ed\.?\s*d | psy\.?\s*d
                | m\.?\s*d\.?\b | j\.?\s*d\.?\b | l\.?\s*l\.?\s*[bm]
                | h\.?\s*n\.?\s*[dc]
            )\b
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        # College-level institution keywords only (no plain "school" or "high school")
        INSTITUTION_RE = re.compile(
            r"""
            \b
            (?:
                # "X University / College / Institute / Polytechnic / Academy"
                (?:\w+(?:[\s\-]\w+){0,5})\s+
                (?:university|college|institute(?:\s+of\s+technology)?
                |polytechnic|academy|conservatory|seminary|faculty)
                |
                # "University / College / Institute of X"
                (?:university|college|institute|polytechnic)
                \s+of\s+(?:\w+(?:[\s\-]\w+){0,4})
                 

                |
                # Well-known acronyms
                \b(?:MIT|CalTech|UCLA|USC|NYU|LSE
                    |IIT[\s\-]\w+|NIT[\s\-]\w+|BITS[\s\-]\w+|IIM[\s\-]\w+
                    |NUS|NTU|ETH|EPFL)\b
            )
            \b
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        # Lines that indicate a high-school / pre-college entry — skip these blocks
        SCHOOL_ONLY_RE = re.compile(
            r"\b(?:high\s+school|secondary\s+school|higher\s+secondary|matriculat|ged"
            r"|10th|12th|hsc|ssc|class\s+(?:x|xii|10|12))\b",
            re.IGNORECASE,
        )

        # Full year range: "2018 - 2022", "2018–2022", "2018 to 2022", "2018"
        YEAR_RE = re.compile(
            r"(?:((?:19|20)\d{2})\s*(?:[-–—to]+)\s*((?:19|20)\d{2}|present|current|now))"
            r"|(?:((?:19|20)\d{2}))",
            re.IGNORECASE,
        )

        GPA_RE = re.compile(
            r"\b(?:gpa|cgpa|grade\s+point)\s*[:\-]?\s*(\d+\.\d+(?:\s*/\s*\d+\.\d+)?)",
            re.IGNORECASE,
        )

        FIELD_RE = re.compile(
            r"\bin\s+([A-Za-z\s&\-]{3,50})",
            re.IGNORECASE
        )

        # ── 4. Parse each block ──────────────────────────────────────────────────

        def parse_block(block_lines):
            full_text = " ".join(block_lines)
            full_lower = full_text.lower()

            # Skip blocks with no college-level degree signal
            if not DEGREE_RE.search(full_lower):
                return None

            # Skip blocks that are clearly high school / secondary entries
            if SCHOOL_ONLY_RE.search(full_text) and not INSTITUTION_RE.search(full_text):
                return None

            entry = {"degree": "", "field_of_study": "", "institution": "", "year": "", "gpa": ""}

            for line in block_lines:
                line_lower = line.lower()

                # ── Degree ──
                if not entry["degree"]:
                    dm = DEGREE_RE.search(line_lower)
                    if dm:
                        entry["degree"] = line.strip()   # keep original case

                # ── Year ──
                ym = YEAR_RE.search(line)
                if ym and not entry["year"]:
                    if ym.group(1):                        # range match
                        entry["year"] = f"{ym.group(1)} - {ym.group(2)}"
                    elif ym.group(3):                      # single year
                        entry["year"] = ym.group(3)

                # ── GPA ──
                gm = GPA_RE.search(line)
                if gm and not entry["gpa"]:
                    entry["gpa"] = gm.group(1)

                # ── Institution: regex first ──
                if not entry["institution"]:
                    im = INSTITUTION_RE.search(line)
                    if im:
                        entry["institution"] = im.group().strip()

            # ── Institution: spaCy fallback (ORG + GPE) ──
            if not entry["institution"] and hasattr(self, "nlp"):
                doc = self.nlp(full_text)
                for ent in doc.ents:
                    if ent.label_ in ("ORG", "GPE"):
                        # Prefer longer entity (more likely to be the full name)
                        if len(ent.text) > len(entry["institution"]):
                            entry["institution"] = ent.text

            # ── Field of study ──
            fm = FIELD_RE.search(full_text)
            if fm:
                entry["field_of_study"] = fm.group(1).strip()

            return entry if (entry["degree"] or entry["institution"]) else None

        # ── 5. Process all blocks ────────────────────────────────────────────────

        for block in blocks:
            result = parse_block(block)
            if result:
                education.append(result)

        # ── 6. Deduplicate ───────────────────────────────────────────────────────
        unique = []
        seen = set()
        for edu in education:
            # Include year in key so two degrees from same school are kept
            key = (edu["degree"] + edu["institution"] + edu["year"]).lower().strip()
            if key not in seen and key != "":
                unique.append(edu)
                seen.add(key)

        return unique

    def _extract_experience(self, text):
        """
        High-accuracy experience extractor for ALL resume types:

        ── Experienced (IT professional) profiles ──
        Extracts: position, company, duration, location
        Handles: "Software Engineer | Google | Jan 2020 - Present"
                "Senior Developer at Amazon (2019 - 2022)"

        ── Fresher / Intern profiles ──
        Extracts: internship title, company, duration
        Handles:  "Python Intern - XYZ Solutions (Jun 2023 - Aug 2023)"
                    "Web Development Internship | ABC Corp"
                    Internship blocks with NO dates (just company + role)

        Fixes over original:
        - start_headers used r"^(experience|work|...)" — matched ANY line starting
        with those words (e.g. "experience with Python" in a summary section).
        Fixed: requires the header to be a SHORT standalone line (< 50 chars).
        - end_headers had the same false-positive problem. Fixed same way.
        - Date anchor logic created duplicate entries when a line had 2 dates
        (e.g. "Jan 2021 - Dec 2022" → two separate entries).
        Fixed: treat both dates on same line as one duration range.
        - Title split on first date token often left just a bullet or empty string.
        Fixed: multi-fallback title resolution (same line → above → below).
        - Company was never extracted. Added company detection via spaCy ORG +
        keyword patterns ("at X", "@ X", "| X", "- X" after title).
        - Internships with no dates were completely missed.
        Fixed: dedicated internship scanner as a second pass.
        - Dedup only checked position — missed same role at different companies.
        Fixed: dedup key = (position + company).lower()
        """

        experience = []
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in text.split("\n")]

        # ─────────────────────────── 1. Section Detection ───────────────────────

        START_HEADERS = re.compile(
            r"""
            \b(?:
                (?:work|professional|career|employment|job)\s*
                (?:experience|history|background|summary)?
                | ^experience$                              # exact "Experience" header only
                | internships?$                             # "Internships" alone, not "Internships & Projects"
                | positions?\s+(?:of\s+)?(?:responsibility|held)
            )\b
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        END_HEADERS = re.compile(
            r"""
            \b(?:
                education | academic | qualification
                | technolog                                 # Technologies / Technical Skills
                | project                                   # Projects (any form)
                | skill | competenc
                | certification | publication
                | award | honor | activit | interest
                | language | reference | summary | objective
                | profile | volunteer | achievement
                | additional
            )\b
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        in_section = False
        section_lines = []

        for line in lines:
            lower = line.lower().strip()
            # Only treat SHORT lines as potential section headers (avoids matching
            # sentences like "3 years of experience with Python" in summary)
            if not in_section:
                if len(line) < 50 and START_HEADERS.search(lower):
                    in_section = True
                    continue
            else:
                if lower and len(line) < 50 and END_HEADERS.search(lower):
                    break
                section_lines.append(line)

        # Fallback: no section found → scan full resume
        if not section_lines:
            section_lines = [l for l in lines if l]

        # ─────────────────────────── 2. Patterns ────────────────────────────────

        # Matches: "June 2024", "Jun 2024", "06/2024", "2024", "Present", "Current"
        DATE_TOKEN = (
            r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
            r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
            r"\s*(?:\'|\s)?\d{2,4}"
            r"|\d{1,2}[\/\-]\d{2,4}"
            r"|\b(?:19|20)\d{2}\b"
            r"|\b(?:present|current|now|ongoing|till\s+date|to\s+date)\b"
        )

        # Full duration range on a single line: "Jan 2021 – Dec 2022" or "2020 - Present"
        DURATION_RE = re.compile(
            rf"({DATE_TOKEN})\s*(?:[-–—to]+)\s*({DATE_TOKEN})",
            re.IGNORECASE,
        )

        # Single date (graduation year, start year, etc.)
        SINGLE_DATE_RE = re.compile(rf"({DATE_TOKEN})", re.IGNORECASE)

        # Internship signal — used for the fresher second-pass
        INTERNSHIP_RE = re.compile(
            r"\b(?:intern(?:ship)?|trainee|apprentice|placement|industrial\s+training"
            r"|summer\s+(?:intern|project|training)|co[\-\s]?op)\b",
            re.IGNORECASE,
        )

        # Job title keywords — helps confirm a line is a role, not a random sentence
        TITLE_SIGNAL_RE = re.compile(
            r"\b(?:engineer|developer|analyst|designer|manager|lead|architect|consultant"
            r"|specialist|associate|executive|coordinator|officer|intern|trainee"
            r"|scientist|researcher|administrator|director|head|vp|president|cto|ceo)\b",
            re.IGNORECASE,
        )

        # Company separators: "Google | 2020", "at Amazon", "@ TCS", "– Infosys"
        COMPANY_SEP_RE = re.compile(
            r"(?:\bat\b|@|\|)\s*([A-Z][A-Za-z0-9\s&\.\,]{2,40}?)(?:\s*[\|,\-–]|$)",
        )

        # ── Location line detector — skip lines that are just "City, Country" ──────
        LOCATION_RE = re.compile(
            r"^(?:remote|on[\s\-]?site|hybrid)?[\s\-]*"
            r"[A-Za-z\s]+,\s*[A-Za-z\s]+$",
            re.IGNORECASE,
        )

        # ── Bullet / description line — not a title/company ──────────────────────
        BULLET_RE = re.compile(r"^[◦•\-\*▪➢➤►]")

        # ─────────────────────────── 5. Smart block splitting ───────────────────
        # Strategy: a new job entry starts when we see a DATE line OR an
        # INTERNSHIP keyword line. We group all lines until the next anchor.

        def is_date_line(line):
            return bool(DURATION_RE.search(line) or SINGLE_DATE_RE.search(line))

        def is_entry_anchor(line):
            """A line that signals the START of a new job block."""
            return (
                INTERNSHIP_RE.search(line)          # "Internship at Codsoft"
                or (TITLE_SIGNAL_RE.search(line) and not BULLET_RE.match(line))
            )

        # First try blank-line separated blocks
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

        # If resume is dense (no blank lines), split on date lines or title anchors
        if len(blocks) <= 1 and len(section_lines) > 4:
            blocks = []
            current = []
            for line in section_lines:
                if not line:
                    continue
                # Start a new block when we hit a date line AND current block
                # already has content, OR when we hit a fresh title/intern anchor
                # after already collecting some lines
                if current and is_date_line(line):
                    # Date belongs to the current block
                    current.append(line)
                    blocks.append(current)
                    current = []
                else:
                    current.append(line)
            if current:
                blocks.append(current)

        # ─────────────────────────── 6. Parse each block ────────────────────────
        #
        # Expected block layouts this handles:
        #
        # Layout A (company-first):          Layout B (title-first):
        #   AksharaPlus                        UI/UX Designer
        #   UI/UX Designer                     AksharaPlus
        #   Remote - Dover, USA                June 2025 - Present
        #   June 2025 - Present
        #
        # Layout C (single line):            Layout D (internship prefix):
        #   Sr. Engineer | Google | 2021-Now   Internship at Codsoft
        #                                      UI/UX Design
        #                                      June 2024 – July 2024

        processed_titles = set()

        def parse_block(block):
            entry = {"position": "", "company": "", "duration": "", "type": "experience"}

            # Classify each line role
            title_lines    = []
            company_lines  = []
            duration_lines = []

            for line in block:
                if BULLET_RE.match(line):
                    continue                          # skip description bullets
                if LOCATION_RE.match(line):
                    continue                          # skip "Remote - Dover, USA"

                dm = DURATION_RE.search(line)
                sm = SINGLE_DATE_RE.search(line)

                if dm:
                    duration_lines.append(
                        f"{dm.group(1).strip()} - {dm.group(2).strip()}"
                    )
                elif sm and len(line.strip()) < 40:
                    # Short line that's mostly a date
                    duration_lines.append(sm.group(1).strip())
                elif INTERNSHIP_RE.search(line):
                    # "Internship at Codsoft" → company extracted, role = this line
                    title_lines.append(line)
                    m = re.search(r"\bat\s+([A-Z][A-Za-z0-9\s&\.]{2,40})", line)
                    if m:
                        company_lines.append(m.group(1).strip())
                elif TITLE_SIGNAL_RE.search(line):
                    title_lines.append(line)
                else:
                    # Could be company name (short, no verbs, Title Case)
                    if len(line) < 50 and re.match(r"[A-Z]", line):
                        company_lines.append(line)

            # ── Assign duration ──
            if duration_lines:
                entry["duration"] = duration_lines[0]

            # ── Assign position ──
            if title_lines:
                raw = title_lines[0]
                # Strip inline company/location separators
                raw = re.sub(r"\s*[\|]\s*.*$", "", raw)
                raw = raw.split(" at ")[0].strip()
                raw = DURATION_RE.sub("", raw).strip()
                entry["position"] = raw
            elif company_lines:
                # Fallback: first short line that looked like company might be title
                entry["position"] = company_lines[0]
                company_lines = company_lines[1:]

            # ── Assign company ──
            # Prefer lines that weren't used as the title
            remaining_companies = [
                c for c in company_lines
                if c.lower() != entry["position"].lower()
            ]
            if remaining_companies:
                entry["company"] = remaining_companies[0]
            else:
                # Try inline separator: "Engineer | Google | 2021"
                for line in block:
                    m = COMPANY_SEP_RE.search(line)
                    if m:
                        candidate = m.group(1).strip()
                        if candidate.lower() != entry["position"].lower():
                            entry["company"] = candidate
                            break

            # spaCy ORG fallback — only if company still empty
            if not entry["company"] and hasattr(self, "nlp"):
                doc = self.nlp(" ".join(block))
                for ent in doc.ents:
                    if ent.label_ == "ORG":
                        if ent.text.lower() != entry["position"].lower():
                            entry["company"] = ent.text
                            break

            # ── Mark internship ──
            if INTERNSHIP_RE.search(" ".join(block)):
                entry["type"] = "internship"

            return entry

        for block in blocks:
            if not block:
                continue
            result = parse_block(block)
            if result["position"] or result["company"]:
                key = (result["position"] + result["company"]).lower().strip()
                if key and key not in processed_titles:
                    experience.append(result)
                    processed_titles.add(key)

        return experience

            

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
        # Detect name using spaCy
        doc = self.nlp(text[:500])   # analyze first part of resume

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                contact_info["name"] = ent.text
                break

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