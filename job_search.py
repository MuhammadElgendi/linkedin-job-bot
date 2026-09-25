import os
import re
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SEEN_JOBS_FILE    = os.path.join(os.path.dirname(__file__), "seen_jobs.json")
SEEN_JOBS_TTL_DAYS = 7
TOP_N = 10

# كل عمليات البحث ريموت بس (f_WT=2، متفرضة في search_linkedin)، ومحصورة
# في المناطق المستهدفة: شمال أوروبا (الأولوية الأولى)، الخليج، مصر، وباقي
# أوروبا. غيّر القايمة دي حسب البلاد اللي إنت عايز تشتغل فيها.
LINKEDIN_SEARCHES = [

    # ============================================================
    # 🇦🇪 UAE — HIGH PRIORITY
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "United Arab Emirates"},
    {"keywords": "Senior DevOps Engineer",         "location": "United Arab Emirates"},
    {"keywords": "Cloud Engineer",                 "location": "United Arab Emirates"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "United Arab Emirates"},
    {"keywords": "Site Reliability Engineer",      "location": "United Arab Emirates"},
    {"keywords": "SRE Engineer",                   "location": "United Arab Emirates"},
    {"keywords": "Platform Engineer",              "location": "United Arab Emirates"},
    {"keywords": "Infrastructure Engineer",        "location": "United Arab Emirates"},
    {"keywords": "DevSecOps Engineer",             "location": "United Arab Emirates"},
    {"keywords": "Cloud Architect",                "location": "United Arab Emirates"},


    # ============================================================
    # 🇸🇦 Saudi Arabia — HIGH PRIORITY
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Saudi Arabia"},
    {"keywords": "Senior DevOps Engineer",         "location": "Saudi Arabia"},
    {"keywords": "Cloud Engineer",                 "location": "Saudi Arabia"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Saudi Arabia"},
    {"keywords": "Site Reliability Engineer",      "location": "Saudi Arabia"},
    {"keywords": "SRE Engineer",                   "location": "Saudi Arabia"},
    {"keywords": "Platform Engineer",              "location": "Saudi Arabia"},
    {"keywords": "Infrastructure Engineer",        "location": "Saudi Arabia"},
    {"keywords": "DevSecOps Engineer",             "location": "Saudi Arabia"},
    {"keywords": "Cloud Architect",                "location": "Saudi Arabia"},


    # ============================================================
    # 🇶🇦 Qatar
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Qatar"},
    {"keywords": "Senior DevOps Engineer",         "location": "Qatar"},
    {"keywords": "Cloud Engineer",                 "location": "Qatar"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Qatar"},
    {"keywords": "Site Reliability Engineer",      "location": "Qatar"},
    {"keywords": "Platform Engineer",              "location": "Qatar"},
    {"keywords": "Infrastructure Engineer",        "location": "Qatar"},


    # ============================================================
    # 🇰🇼 Kuwait
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Kuwait"},
    {"keywords": "Senior DevOps Engineer",         "location": "Kuwait"},
    {"keywords": "Cloud Engineer",                 "location": "Kuwait"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Kuwait"},
    {"keywords": "Site Reliability Engineer",      "location": "Kuwait"},
    {"keywords": "Platform Engineer",              "location": "Kuwait"},
    {"keywords": "Infrastructure Engineer",        "location": "Kuwait"},


    # ============================================================
    # 🇧🇭 Bahrain
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Bahrain"},
    {"keywords": "Senior DevOps Engineer",         "location": "Bahrain"},
    {"keywords": "Cloud Engineer",                 "location": "Bahrain"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Bahrain"},
    {"keywords": "Site Reliability Engineer",      "location": "Bahrain"},
    {"keywords": "Platform Engineer",              "location": "Bahrain"},
    {"keywords": "Infrastructure Engineer",        "location": "Bahrain"},


    # ============================================================
    # 🇴🇲 Oman
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Oman"},
    {"keywords": "Senior DevOps Engineer",         "location": "Oman"},
    {"keywords": "Cloud Engineer",                 "location": "Oman"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Oman"},
    {"keywords": "Site Reliability Engineer",      "location": "Oman"},
    {"keywords": "Platform Engineer",              "location": "Oman"},
    {"keywords": "Infrastructure Engineer",        "location": "Oman"},


    # ============================================================
    # 🇪🇬 Egypt
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Egypt"},
    {"keywords": "Senior DevOps Engineer",         "location": "Egypt"},
    {"keywords": "Cloud Engineer",                 "location": "Egypt"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Egypt"},
    {"keywords": "Site Reliability Engineer",      "location": "Egypt"},
    {"keywords": "SRE Engineer",                   "location": "Egypt"},
    {"keywords": "Platform Engineer",              "location": "Egypt"},
    {"keywords": "Infrastructure Engineer",        "location": "Egypt"},
    {"keywords": "DevSecOps Engineer",             "location": "Egypt"},
    {"keywords": "Cloud Architect",                "location": "Egypt"},


    # ============================================================
    # 🇨🇭 Switzerland
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Switzerland"},
    {"keywords": "Senior DevOps Engineer",         "location": "Switzerland"},
    {"keywords": "Cloud Engineer",                 "location": "Switzerland"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Switzerland"},
    {"keywords": "Site Reliability Engineer",      "location": "Switzerland"},
    {"keywords": "Platform Engineer",              "location": "Switzerland"},
    {"keywords": "Infrastructure Engineer",        "location": "Switzerland"},


    # ============================================================
    # 🇩🇰 Denmark
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Denmark"},
    {"keywords": "Cloud Engineer",                 "location": "Denmark"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Denmark"},
    {"keywords": "Site Reliability Engineer",      "location": "Denmark"},
    {"keywords": "Platform Engineer",              "location": "Denmark"},


    # ============================================================
    # 🇸🇪 Sweden
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Sweden"},
    {"keywords": "Cloud Engineer",                 "location": "Sweden"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Sweden"},
    {"keywords": "Site Reliability Engineer",      "location": "Sweden"},
    {"keywords": "Platform Engineer",              "location": "Sweden"},


    # ============================================================
    # 🇫🇮 Finland
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Finland"},
    {"keywords": "Cloud Engineer",                 "location": "Finland"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Finland"},
    {"keywords": "Site Reliability Engineer",      "location": "Finland"},
    {"keywords": "Platform Engineer",              "location": "Finland"},


    # ============================================================
    # 🇳🇴 Norway
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Norway"},
    {"keywords": "Cloud Engineer",                 "location": "Norway"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Norway"},
    {"keywords": "Site Reliability Engineer",      "location": "Norway"},
    {"keywords": "Platform Engineer",              "location": "Norway"},


    # ============================================================
    # 🇳🇱 Netherlands
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Netherlands"},
    {"keywords": "Senior DevOps Engineer",         "location": "Netherlands"},
    {"keywords": "Cloud Engineer",                 "location": "Netherlands"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Netherlands"},
    {"keywords": "Site Reliability Engineer",      "location": "Netherlands"},
    {"keywords": "Platform Engineer",              "location": "Netherlands"},


    # ============================================================
    # 🇩🇪 Germany
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Germany"},
    {"keywords": "Senior DevOps Engineer",         "location": "Germany"},
    {"keywords": "Cloud Engineer",                 "location": "Germany"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Germany"},
    {"keywords": "Site Reliability Engineer",      "location": "Germany"},
    {"keywords": "Platform Engineer",              "location": "Germany"},
    {"keywords": "Infrastructure Engineer",        "location": "Germany"},


    # ============================================================
    # 🇬🇧 United Kingdom
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "United Kingdom"},
    {"keywords": "Senior DevOps Engineer",         "location": "United Kingdom"},
    {"keywords": "Cloud Engineer",                 "location": "United Kingdom"},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "United Kingdom"},
    {"keywords": "Site Reliability Engineer",      "location": "United Kingdom"},
    {"keywords": "Platform Engineer",              "location": "United Kingdom"},
    {"keywords": "Infrastructure Engineer",        "location": "United Kingdom"},


    # ============================================================
    # 🌍 WORLDWIDE — REMOTE
    # ============================================================

    {"keywords": "DevOps Engineer",                "location": "Worldwide", "remote_only": True},
    {"keywords": "Senior DevOps Engineer",         "location": "Worldwide", "remote_only": True},
    {"keywords": "Cloud Engineer",                 "location": "Worldwide", "remote_only": True},
    {"keywords": "Cloud Infrastructure Engineer",  "location": "Worldwide", "remote_only": True},
    {"keywords": "Site Reliability Engineer",      "location": "Worldwide", "remote_only": True},
    {"keywords": "SRE Engineer",                   "location": "Worldwide", "remote_only": True},
    {"keywords": "Platform Engineer",              "location": "Worldwide", "remote_only": True},
    {"keywords": "Infrastructure Engineer",        "location": "Worldwide", "remote_only": True},
    {"keywords": "DevSecOps Engineer",             "location": "Worldwide", "remote_only": True},
    {"keywords": "Cloud Architect",                "location": "Worldwide", "remote_only": True},
]
LINKEDIN_SEARCHES = [
    # UAE
    {"keywords": "DevOps", "location": "United Arab Emirates"},
    {"keywords": "Cloud Engineer", "location": "United Arab Emirates"},
    {"keywords": "SRE", "location": "United Arab Emirates"},
    {"keywords": "Platform Engineer", "location": "United Arab Emirates"},

    # Saudi
    {"keywords": "DevOps", "location": "Saudi Arabia"},
    {"keywords": "Cloud Engineer", "location": "Saudi Arabia"},
    {"keywords": "SRE", "location": "Saudi Arabia"},
    {"keywords": "Platform Engineer", "location": "Saudi Arabia"},

    # Egypt
    {"keywords": "DevOps", "location": "Egypt"},
    {"keywords": "Cloud Engineer", "location": "Egypt"},
    {"keywords": "SRE", "location": "Egypt"},
    {"keywords": "Platform Engineer", "location": "Egypt"},

    # Europe
    {"keywords": "DevOps", "location": "Germany"},
    {"keywords": "DevOps", "location": "Netherlands"},
    {"keywords": "DevOps", "location": "United Kingdom"},
    {"keywords": "DevOps", "location": "Switzerland"},
    {"keywords": "DevOps", "location": "Sweden"},
    {"keywords": "Cloud Engineer", "location": "Germany"},
    {"keywords": "Cloud Engineer", "location": "Netherlands"},
    {"keywords": "Cloud Engineer", "location": "United Kingdom"},
    {"keywords": "SRE", "location": "Germany"},
    {"keywords": "SRE", "location": "Netherlands"},
    {"keywords": "SRE", "location": "United Kingdom"},

    # Remote
    {"keywords": "DevOps", "location": "Worldwide", "remote_only": True},
    {"keywords": "Cloud Engineer", "location": "Worldwide", "remote_only": True},
    {"keywords": "SRE", "location": "Worldwide", "remote_only": True},
    {"keywords": "Platform Engineer", "location": "Worldwide", "remote_only": True},
]

# بحث في شركات معيّنة — بيجيب أي وظيفة مفتوحة في الشركات دي، وبعدين
# بيفلترها حسب علاقتها بمهاراتك.
COMPANY_SEARCHES = [
    {"keywords": "Bayzat",    "location": "United Arab Emirates"},
    {"keywords": "Careem",    "location": "United Arab Emirates"},
    {"keywords": "G42",       "location": "United Arab Emirates"},
    {"keywords": "Talabat",   "location": "United Arab Emirates"},
    {"keywords": "Halan",     "location": "Egypt"},
    {"keywords": "Paymob",    "location": "Egypt"},
    {"keywords": "Instabug",  "location": "Egypt"},
    {"keywords": "Tamara",    "location": "Saudi Arabia"},
    {"keywords": "maids.cc",  "location": "United Arab Emirates"},
    {"keywords": "Qureos",    "location": "United Arab Emirates"},
]

# الوظيفة اللي بتيجي من بحث الشركات لازم يكون في عنوانها كلمة على الأقل من
# دول عشان تتحسب مناسبة. ضيف الكلمات بتاعة مجالك إنت هنا.
COMPANY_RELEVANCE_TITLE_WORDS = {
    # DevOps
    "devops",
    "devops engineer",
    "devops specialist",
    "devops consultant",
    "devops architect",

    # Cloud
    "cloud",
    "cloud engineer",
    "cloud infrastructure",
    "cloud architect",
    "cloud consultant",
    "cloud operations",
    "cloud platform",

    # SRE / Reliability
    "sre",
    "site reliability",
    "site reliability engineer",
    "reliability engineer",
    "production engineer",

    # Infrastructure / Operations
    "infrastructure",
    "infrastructure engineer",
    "infrastructure architect",
    "platform engineer",
    "platform engineering",
    "systems engineer",
    "systems administrator",
    "system engineer",
    "cloud operations",
    "operations engineer",

    # Kubernetes / Containers
    "kubernetes",
    "k8s",
    "container",
    "containers",
    "docker",
    "containerization",

    # CI/CD & Automation
    "ci/cd",
    "cicd",
    "continuous integration",
    "continuous delivery",
    "continuous deployment",
    "automation engineer",
    "release engineer",
    "build engineer",

    # Infrastructure as Code
    "terraform",
    "ansible",
    "cloudformation",
    "pulumi",
    "infrastructure as code",
    "iac",

    # Major Cloud Platforms
    "aws",
    "amazon web services",
    "azure",
    "microsoft azure",
    "gcp",
    "google cloud",
    "google cloud platform",
    "oci",
    "oracle cloud",

    # Observability / Reliability
    "observability",
    "monitoring",
    "logging",
    "alerting",
    "incident management",
    "incident response",
    "performance engineering",

    # Security / Cloud Infrastructure
    "cloud security",
    "devsecops",
    "security automation",

    # General technical titles
    "technical operations",
    "technical infrastructure",
    "infrastructure operations",
    "platform operations",
}

LINKEDIN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── حساب النقط ────────────────────────────────────────────────────────────────

ROLE_SCORES = {
    # Highest priority — core target roles
    "devops engineer":             50,
    "senior devops engineer":      50,
    "devops":                      48,
    "devops specialist":           46,
    "devops consultant":            44,
    "devops architect":             44,

    # SRE / Reliability
    "site reliability engineer":   48,
    "site reliability":             46,
    "sre engineer":                 46,
    "sre":                          44,
    "reliability engineer":        42,
    "production engineer":          40,

    # Cloud Infrastructure
    "cloud infrastructure engineer": 46,
    "cloud engineer":                44,
    "cloud infrastructure":          42,
    "cloud architect":               40,
    "cloud operations engineer":     40,
    "cloud operations":              38,
    "cloud consultant":              36,

    # Infrastructure
    "infrastructure engineer":      42,
    "infrastructure architect":     40,
    "infrastructure specialist":    36,
    "infrastructure operations":    36,

    # Platform Engineering
    "platform engineer":             42,
    "platform engineering":          40,
    "platform architect":            38,
    "platform operations":           36,

    # Kubernetes / Container Infrastructure
    "kubernetes engineer":           42,
    "container engineer":            36,
    "container platform engineer":   40,

    # DevSecOps
    "devsecops engineer":            42,
    "devsecops":                     40,

    # Cloud / Systems Operations
    "systems engineer":              32,
    "system engineer":               30,
    "cloud systems engineer":        38,
    "systems administrator":         24,
    "cloud administrator":           28,

    # CI/CD / Release
    "ci/cd engineer":                34,
    "cicd engineer":                 34,
    "release engineer":              30,
    "build engineer":                26,

    # Automation — useful but secondary
    "automation engineer":           30,
    "infrastructure automation":     34,
    "cloud automation":              34,
    "automation specialist":         22,

    # General operations
    "operations engineer":           28,
    "technical operations":          26,
    "cloud operations":              32,
}

SKILL_SCORES = {
    # Cloud — very important
    "aws":                    20,
    "amazon web services":    20,
    "azure":                  18,
    "microsoft azure":        18,
    "gcp":                    18,
    "google cloud":           18,
    "oracle cloud":           14,
    "oci":                    14,

    # Kubernetes / Containers
    "kubernetes":             20,
    "k8s":                    20,
    "docker":                 16,
    "containerd":             14,
    "helm":                   14,
    "openshift":              14,
    "ecs":                    12,
    "eks":                    16,
    "aks":                    16,

    # Infrastructure as Code
    "terraform":              20,
    "infrastructure as code": 18,
    "iac":                    16,
    "ansible":                16,
    "cloudformation":         14,
    "pulumi":                 14,

    # CI/CD
    "ci/cd":                  18,
    "cicd":                   18,
    "jenkins":                14,
    "github actions":         16,
    "gitlab ci":              14,
    "gitlab":                 10,
    "azure devops":           14,
    "argocd":                 16,
    "argo cd":                16,

    # Linux / Systems
    "linux":                  14,
    "ubuntu":                 10,
    "red hat":                10,
    "rhel":                   10,
    "bash":                   10,
    "shell scripting":        10,

    # Observability / SRE
    "prometheus":             16,
    "grafana":                14,
    "datadog":                14,
    "new relic":              12,
    "cloudwatch":             14,
    "observability":          18,
    "monitoring":             12,
    "logging":                10,
    "alerting":               10,

    # Networking
    "networking":             10,
    "vpc":                    12,
    "load balancer":          10,
    "dns":                    8,
    "cdn":                    8,

    # Security / DevSecOps
    "devsecops":              18,
    "cloud security":         16,
    "iam":                    12,
    "security automation":    14,

    # Automation
    "automation":             10,
    "python":                  8,
    "powershell":              6,
    "scripting":               8,

    # Databases / infrastructure services
    "redis":                   5,
    "postgresql":              5,
    "mysql":                   5,

    # Git / Version Control
    "git":                     8,
    "github":                  6,
    "gitlab":                  6,
}
LOCATION_SCORES = {
    # شمال أوروبا — الأولوية الأولى، بنقط أعلى من أي منطقة تانية
    "switzerland": 26, "zurich": 26, "geneva": 26,
    "denmark": 25, "copenhagen": 25,
    "finland": 25, "helsinki": 25,
    "sweden": 25, "stockholm": 25,
    "norway": 25, "oslo": 25,
    "ae": 20, "uae": 20, "dubai": 20, "abu dhabi": 20, "sharjah": 20, "united arab emirates": 20,
    "sa": 18, "saudi": 18, "riyadh": 18, "jeddah": 18, "saudi arabia": 18,
    "qa": 16, "qatar": 16, "doha": 16,
    "kw": 15, "kuwait": 15,
    "bh": 15, "bahrain": 15,
    "om": 15, "oman": 15, "muscat": 15,
    "eg": 16, "egypt": 16, "cairo": 16,
    "worldwide": 15, "global": 15,
    "united kingdom": 16, "uk": 16, "london": 16,
    "ireland": 16, "dublin": 16,
    "germany": 16, "berlin": 16, "munich": 16,
    "france": 16, "paris": 16,
    "netherlands": 16, "amsterdam": 16,
    "spain": 16, "madrid": 16, "barcelona": 16,
    "portugal": 16, "lisbon": 16,
    "italy": 16, "milan": 16, "rome": 16,
    "poland": 16, "warsaw": 16,
    "belgium": 16, "brussels": 16,
    "remote": 14,
}

TARGET_COMPANIES = [
    "maids", "justmop", "helperplace", "qureos", "bayzat", "huspy", "coraly",
    "halan", "paymob", "instabug", "breadfast", "rabbit",
    "g42", "presight", "careem", "noon", "talabat", "dubizzle",
    "stc", "neom", "zain", "tamara",
    "automattic", "zapier", "make.com", "n8n",
]

LOCATION_CODE_MAP = {
    "united arab emirates": "ae", "uae": "ae", "dubai": "ae", "abu dhabi": "ae",
    "saudi arabia": "sa", "riyadh": "sa", "jeddah": "sa",
    "egypt": "eg", "cairo": "eg",
    "qatar": "qa", "doha": "qa",
    "kuwait": "kw", "bahrain": "bh",
    "oman": "om", "muscat": "om",
    "worldwide": "global",
    "united kingdom": "gb", "ireland": "ie",
    "germany": "de", "france": "fr", "netherlands": "nl",
    "spain": "es", "portugal": "pt", "italy": "it", "poland": "pl",
    "belgium": "be", "switzerland": "ch",
    "denmark": "dk", "finland": "fi", "sweden": "se", "norway": "no",
}


def infer_country_code(location: str) -> str:
    loc = location.lower()
    for k, v in LOCATION_CODE_MAP.items():
        if k in loc:
            return v
    return "global"


def score_job(job: dict) -> int:
    title   = (job.get("job_title") or "").lower()
    desc    = (job.get("job_description") or "")[:500].lower()
    city    = (job.get("job_city") or "").lower()
    country = (job.get("job_country") or "").lower()
    company = (job.get("employer_name") or "").lower()
    is_remote = job.get("job_is_remote", False)

    score = 0
    for kw, pts in ROLE_SCORES.items():
        if kw in title:
            score += pts
            break
    skill_pts = sum(pts for kw, pts in SKILL_SCORES.items() if kw in title + " " + desc)
    score += min(skill_pts, 30)
    loc_hay = f"{city} {country}" + (" remote" if is_remote else "")
    for loc, pts in LOCATION_SCORES.items():
        if loc in loc_hay:
            score += pts
            break
    if any(name in company for name in TARGET_COMPANIES):
        score += 10
    if is_remote:
        score += 8
    elif any(w in title for w in ("hybrid", "remote")):
        score += 5
    return score


def score_label(score: int) -> str:
    if score >= 60: return "Excellent match"
    if score >= 45: return "Strong match"
    if score >= 30: return "Good match"
    return "Possible match"


# ── المنافسة (عدد المتقدمين) ──────────────────────────────────────────────────
# الوظايف اللي عليها متقدمين أقل بتاخد أولوية أعلى — دي أسهل حاجة فعلاً
# تتقبل فيها. عدد المتقدمين بيتجاب بس لأعلى الوظايف في كل مجموعة
# (APPLICANT_FETCH_LIMIT)، عشان عدد الطلبات الزيادة على لينكدإن يفضل محدود.

APPLICANT_FETCH_LIMIT = 15


def fetch_applicant_count(url: str) -> int | None:
    if not url:
        return None
    try:
        resp = requests.get(url, headers=LINKEDIN_HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        m = re.search(r'([\d,]+)\+?\s*(?:applicants|people clicked apply)', resp.text, re.I)
        if m:
            return int(m.group(1).replace(",", ""))
    except requests.RequestException:
        pass
    return None


def applicant_bonus(count: int | None) -> int:
    if count is None:
        return 0
    if count <= 10:
        return 20
    if count <= 25:
        return 14
    if count <= 50:
        return 8
    if count <= 100:
        return 2
    return -8  # heavily-applied jobs are deprioritized, not just unboosted


def enrich_with_competition(jobs: list) -> list:
    """بيجيب عدد المتقدمين لأعلى الوظايف نقط في المجموعة، بيضيف بونص
    المنافسة القليلة على النتيجة النهائية، وبعدين بيعيد ترتيب المجموعة
    كلها حسب النتيجة دي."""
    ranked = sorted(jobs, key=score_job, reverse=True)
    top, rest = ranked[:APPLICANT_FETCH_LIMIT], ranked[APPLICANT_FETCH_LIMIT:]
    for job in top:
        count = fetch_applicant_count(job.get("job_apply_link"))
        job["_applicants"] = count
        job["_score"] = score_job(job) + applicant_bonus(count)
        time.sleep(0.3)
    for job in rest:
        job["_applicants"] = None
        job["_score"] = score_job(job)
    return sorted(top + rest, key=lambda j: j["_score"], reverse=True)


# ── سحب البيانات من لينكدإن ───────────────────────────────────────────────────

def parse_card(card, search_location: str) -> dict | None:
    link_tag = card.find("a", class_="base-card__full-link")
    if not link_tag:
        return None
    raw_url = link_tag.get("href", "")
    # بيسيب لينك لينكدإن نضيف (بيشيل باراميترز التتبّع اللي بعد ?)
    apply_url = raw_url.split("?")[0] if raw_url else ""
    match = re.search(r"-(\d{8,})$", apply_url)
    job_id = f"li_{match.group(1)}" if match else None
    if not job_id:
        return None

    title_tag   = card.find("h3", class_="base-search-card__title")
    company_tag = card.find("h4", class_="base-search-card__subtitle")
    loc_tag     = card.find("span", class_="job-search-card__location")

    title    = (title_tag.get_text(strip=True)   if title_tag   else "").strip()
    company  = (company_tag.get_text(strip=True) if company_tag else "").strip()
    location = (loc_tag.get_text(strip=True)     if loc_tag     else search_location).strip()

    # كل سيرش بيفرض f_WT=2 (ريموت)، يعني النتايج ريموت بطبيعتها؛
    # فحص النص متسيب بس كإشارة على الهايبرد.
    is_remote = True

    return {
        "job_id":        job_id,
        "job_title":     title,
        "employer_name": company,
        "job_city":      location,
        "job_country":   search_location,
        "_search_country": infer_country_code(search_location),
        "job_is_remote": is_remote,
        "job_apply_link": apply_url,
        "job_description": "",
        "apply_options": [{"apply_link": apply_url, "is_direct": False, "publisher": "LinkedIn"}],
    }


def search_linkedin(keywords: str, location: str, remote_only: bool = False) -> list:
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    params = {
        "keywords": keywords,
        "f_TPR":    "r259200",  # last 3 days
        "start":    0,
        "f_WT":     "2",  # remote-work-type only — every search is remote-only now
    }
    if remote_only:
        # من غير فلتر بلد — بيدوّر في كل الدول بدل قايمة
        # الخليج/مصر/أوروبا المحدودة.
        params["location"] = ""
    else:
        params["location"] = location
    try:
        resp = requests.get(url, headers=LINKEDIN_HEADERS, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"Warning: LinkedIn returned {resp.status_code} for '{keywords}' / {location}")
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        for card in soup.find_all("li"):
            job = parse_card(card, location)
            if job:
                jobs.append(job)
        return jobs
    except requests.RequestException as e:
        print(f"Warning: LinkedIn search failed for '{keywords}': {e}")
        return []


# ── تليجرام ───────────────────────────────────────────────────────────────────

def esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_job(rank: int, job: dict) -> str:
    title      = esc(job.get("job_title") or "N/A")
    company    = esc(job.get("employer_name") or "N/A")
    location   = esc(job.get("job_city") or job.get("job_country") or "Unknown")
    is_remote  = job.get("job_is_remote", False)
    is_target  = job.get("_company_match", False)
    score      = job.get("_score", score_job(job))
    applicants = job.get("_applicants")

    title_lower = (job.get("job_title") or "").lower()
    if "hybrid" in title_lower or "hybrid" in location.lower():
        work_mode = "Hybrid"
    elif is_remote or "remote" in title_lower:
        work_mode = "Remote"
    else:
        work_mode = location

    apply_url  = job.get("job_apply_link") or ""
    safe_url   = apply_url.replace("&", "&amp;")
    apply_part = f' | <a href="{safe_url}">Apply on LinkedIn</a>' if safe_url else ""
    badge      = " [TARGET CO.]" if is_target else ""
    if applicants is None:
        competition = ""
    elif applicants <= 25:
        competition = f" | {applicants} applicants (low competition)"
    else:
        competition = f" | {applicants} applicants"

    return (
        f"<b>#{rank} {title}</b>{badge}\n"
        f"{company} | {work_mode}\n"
        f"<i>{score_label(score)} ({score} pts)</i>{competition}{apply_part}"
    )


def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    lines = text.split("\n")
    chunks, current = [], ""
    for line in lines:
        candidate = current + line + "\n"
        if len(candidate) > 4000:
            if current:
                chunks.append(current.rstrip())
            current = line + "\n"
        else:
            current = candidate
    if current.strip():
        chunks.append(current.rstrip())
    for chunk in chunks:
        try:
            resp = requests.post(url, json={
                "chat_id":   TELEGRAM_CHAT_ID,
                "text":      chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"Error sending Telegram message: {e}")


# ── حفظ الذاكرة ───────────────────────────────────────────────────────────────

def check_config():
    missing = [k for k in ("TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID")
               if not os.getenv(k) or "your_" in os.getenv(k)]
    if missing:
        print(f"ERROR: Missing values in .env: {', '.join(missing)}")
        sys.exit(1)


def load_seen_jobs() -> dict:
    if not os.path.exists(SEEN_JOBS_FILE):
        return {}
    with open(SEEN_JOBS_FILE, "r") as f:
        data = json.load(f)
    cutoff = (datetime.now() - timedelta(days=SEEN_JOBS_TTL_DAYS)).isoformat()
    return {jid: ts for jid, ts in data.items() if ts >= cutoff}


def save_seen_jobs(seen: dict):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(seen, f)


# ── الدالة الرئيسية ───────────────────────────────────────────────────────────

def main():
    check_config()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting LinkedIn job search...")

    seen = load_seen_jobs()
    this_run_ids: set = set()
    general_jobs: list = []
    company_jobs: list = []

    # ── الجولة ١: البحث العام عن الوظايف ──────────────────────────────────────
    print("--- General searches ---")
    for s in LINKEDIN_SEARCHES:
        jobs = search_linkedin(s["keywords"], s["location"], s.get("remote_only", False))
        kept = 0
        for job in jobs:
            job_id = job.get("job_id")
            if not job_id or job_id in seen or job_id in this_run_ids:
                continue
            this_run_ids.add(job_id)
            general_jobs.append(job)
            kept += 1
        print(f"  '{s['keywords']}' / {s['location']} -> {kept} new")

    # ── الجولة ٢: البحث في الشركات المستهدفة ──────────────────────────────────
    print("--- Target company searches ---")
    for s in COMPANY_SEARCHES:
        jobs = search_linkedin(s["keywords"], s["location"])
        kept = 0
        for job in jobs:
            job_id = job.get("job_id")
            if not job_id or job_id in seen or job_id in this_run_ids:
                continue
            # فلترة — بيسيب بس الوظايف اللي ليها علاقة بمجالك
            title_words = set((job.get("job_title") or "").lower().split())
            if not title_words & COMPANY_RELEVANCE_TITLE_WORDS:
                continue
            job["_company_match"] = True
            this_run_ids.add(job_id)
            company_jobs.append(job)
            kept += 1
        print(f"  '{s['keywords']}' / {s['location']} -> {kept} relevant")

    print(f"General: {len(general_jobs)} | Company: {len(company_jobs)}")

    all_new = general_jobs + company_jobs
    if not all_new:
        send_telegram(
            "<b>Daily Job Report - " + datetime.now().strftime("%b %d, %Y") + "</b>\n"
            "No new LinkedIn jobs since last run. Check back tomorrow!"
        )
    else:
        # بيجيب عدد المتقدمين لأعلى وظايف كل مجموعة (بونص المنافسة
        # القليلة)، بيعيد الترتيب، وبعدين بياخد أحسن ٥ من كل مجموعة.
        general_jobs = enrich_with_competition(general_jobs)
        company_jobs = enrich_with_competition(company_jobs)
        top_general  = general_jobs[:5]
        top_company  = company_jobs[:5]

        date_str = datetime.now().strftime("%b %d, %Y")
        lines = [
            f"<b>Daily Job Report - {date_str}</b>\n"
            f"Remote only | North Europe + Gulf + Egypt + Europe | LinkedIn only\n"
        ]

        if top_general:
            lines.append("<b>-- Best Role Matches --</b>")
            lines.append("")
            for i, job in enumerate(top_general, 1):
                lines.append(format_job(i, job))
                lines.append("")

        if top_company:
            lines.append("<b>-- Target Company Openings --</b>")
            lines.append("")
            for i, job in enumerate(top_company, 1):
                lines.append(format_job(i, job))
                lines.append("")

        send_telegram("\n".join(lines))
        print(f"Telegram sent: {len(top_general)} role matches + {len(top_company)} company matches.")

    now_iso = datetime.now().isoformat()
    for job_id in this_run_ids:
        seen[job_id] = now_iso
    save_seen_jobs(seen)


if __name__ == "__main__":
    main()
