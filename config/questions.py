"""
config/questions.py

Full BFSI intake questionnaire with sector-dynamic loading.
Covers: Technology Infrastructure, Front Office, Middle/Back Office, Risk & Compliance,
        Legacy Diagnostics (ERP, HRMS, DW), and Data Governance.

--------------------------------------------------------------------------------------
INSURANCE SECTOR TUNING (this revision)
--------------------------------------------------------------------------------------
Audited from the perspective of a "Life & General Insurance" client. Changes made:

1. REWORDED (kept, but language broadened beyond capital-markets/trading framing):
   S1_LATENCY, S3_FTE_RECON, S3_ANNUAL_BREAKS, S4_UNSERVED

2. RE-SCOPED (added back for insurance, with an insurance-specific condition noted
   in help text — only applies to carriers with unit-linked / variable-fund books):
   S3_NAV_EXCEPTIONS

3. CONFIRMED CORRECTLY EXCLUDED for insurance — no change (these are genuine
   asset-management / broker-dealer execution concepts with no insurance-ops
   analogue, so they should NOT be shown to a pure insurance client):
   S2_ANALYST_COUNT, S2_NAMES_COVERED, S2_PARSING_HOURS, S2_SHORTFALL_BPS,
   S3_FAIL_EVENTS, S3_CA_VOLUME, S4_ONBOARD_DAYS

4. NEW — insurance-native questions added to close gaps the original set had
   (claims intake, fraud, reinsurance/bordereaux, persistency, telematics, and a
   policy-issuance-turnaround analogue for the S4_ONBOARD_DAYS gap):
   S2_QUOTE_TO_BIND_DAYS, S2_FNOL_DIGITAL_PCT, S3_CLAIMS_FRAUD_FLAG_PCT,
   S3_REINS_BORDEREAUX_VOL, S4_LAPSE_RATE, S4_TELEMATICS_MATURITY
--------------------------------------------------------------------------------------
"""

SECTIONS = [
    {"id": "S1", "nav_label": "Technology", "title": "Technology & Data Infrastructure"},
    {"id": "S2", "nav_label": "Front Office", "title": "Front Office Operations"},
    {"id": "S3", "nav_label": "Middle/Back", "title": "Middle & Back Office Operations"},
    {"id": "S4", "nav_label": "Risk & KYC", "title": "Risk, Compliance & Onboarding"},
    {"id": "S5", "nav_label": "Legacy", "title": "Legacy Systems & Governance"},
]

def get_section(section_id: str) -> dict:
    for s in SECTIONS:
        if s["id"] == section_id:
            return s
    return SECTIONS[0]

def get_questions_for_section(section_id: str, sector: str = "all") -> list[dict]:
    # Returns questions that match the section AND (are meant for all sectors OR match the specific sector)
    return [q for q in QUESTIONS if q["section"] == section_id and ("all" in q.get("sectors", ["all"]) or sector in q.get("sectors", ["all"]))]

OTHER_OPTION = "Other (type below)"

OBJECTIVE_INPUTS = [
    "Margin Expansion (Cost)",
    "Alpha Generation (Revenue)",
    "Regulatory Resilience (Risk)",
    "Client Coverage Scaling",
]

QUESTIONS = [

    # ─── S1: Technology & Data Infrastructure ─────────────────────────────────
    {
        "id": "S1_AUM",
        "section": "S1",
        "question": "Total AUM — Assets Under Management / Gross Written Premium ($B)",
        "type": "numeric",
        "help": "Enter in Billions USD (e.g. 50 for $50B). Primary scaling factor for all revenue levers.",
        "default": 50.0,
        "sectors": ["all"]
    },
    {
        "id": "S1_ARCH",
        "section": "S1",
        "question": "Core data warehouse / platform architecture",
        "type": "categorical",
        "options": [
            "Siloed On-Premises (Batch, T+1)",
            "Hybrid — partial cloud, many point-to-point feeds",
            "Cloud-Native (AWS / Azure / GCP)",
            "Data Mesh / Domain-Oriented",
            OTHER_OPTION,
        ],
        "default": "Hybrid — partial cloud, many point-to-point feeds",
        "help": "This drives the Fragmentation Score and sequences the Data Platform lever.",
        "sectors": ["all"]
    },
    {
        "id": "S1_API_GATEWAY",
        "section": "S1",
        "question": "API & Integration Maturity",
        "type": "categorical",
        "options": [
            "Batch processing & manual SFTP only",
            "Internal REST APIs (Point-to-point)",
            "Managed API Gateway with some microservices",
            "Event-driven architecture (Kafka/PubSub) across enterprise"
        ],
        "default": "Internal REST APIs (Point-to-point)",
        "help": "Event-driven systems are prerequisites for advanced Agentic AI triggers.",
        "sectors": ["all"]
    },
    {
        "id": "S1_UNSTRUCTURED_DATA",
        "section": "S1",
        "question": "Unstructured Data Readiness (LLMs / Document AI)",
        "type": "categorical",
        "options": [
            "No unstructured data pipelines",
            "Piloting OCR/DocAI on isolated use cases",
            "Scaled document extraction integrated into workflows",
            "Unified knowledge graph across text, audio, and structured data"
        ],
        "default": "Piloting OCR/DocAI on isolated use cases",
        "help": "Dictates readiness for automated underwriting, claims, and research parsing. For insurers, this is the FNOL documents, medical records, policy PDFs, and adjuster notes pipeline.",
        "sectors": ["all"]
    },
    {
        "id": "S1_LATENCY",
        "section": "S1",
        "question": "Average data latency for decision-making",
        "type": "categorical",
        "options": [
            "Real-time / Streaming (<1 second)",
            "Near Real-time (Minutes)",
            "Intraday (Hours)",
            "T+1 Overnight Batch",
        ],
        "default": "T+1 Overnight Batch",
        "help": "Sub-second latency mainly matters for trading execution. For insurers, 'near real-time' is usually the bar that matters — it's what enables instant policy issuance, telematics-based pricing, and claims fraud triage at FNOL.",
        "sectors": ["all"]
    },
    {
        "id": "S1_ERP",
        "section": "S1",
        "question": "Core ERP / Policy Admin System status",
        "type": "categorical",
        "options": [
            "Modern, cloud-native (e.g. Guidewire Cloud, SimCorp SaaS)",
            "On-prem with API layer",
            "Legacy monolith (>10 years old, COBOL / Java, rigid APIs)",
            "Multiple fragmented systems across business lines",
            OTHER_OPTION,
        ],
        "default": "On-prem with API layer",
        "help": "Monolithic systems dramatically inflate implementation shortfall. For insurers this is your Policy Admin System (PAS) — Guidewire, Duck Creek, legacy mainframe, etc.",
        "sectors": ["all"]
    },
    {
        "id": "S1_HRMS",
        "section": "S1",
        "question": "HRMS / People systems maturity",
        "type": "categorical",
        "options": [
            "Modern cloud HRMS (Workday / SuccessFactors)",
            "Legacy HRMS with limited API",
            "Spreadsheet / manual processes",
        ],
        "default": "Legacy HRMS with limited API",
        "help": "Feeds change-management risk scoring.",
        "sectors": ["all"]
    },
    {
        "id": "S1_KTLO",
        "section": "S1",
        "question": "Maintenance-to-Innovation ratio: % of IT budget on Run-the-Business",
        "type": "percentage",
        "help": ">70% on Run is the industry red flag. Peer median: 60% — though carriers running legacy Policy Admin Systems commonly skew higher (65-75%) given the cost of maintaining aging PAS platforms.",
        "default": 72,
        "sectors": ["all"]
    },
    {
        "id": "S1_SILO",
        "section": "S1",
        "question": "Number of distinct systems holding a core data entity (client, trade, policy)",
        "type": "numeric",
        "help": "4–6 silos = Heavy daily reconciliation. 7+ = Systemic tax on every AI lever.",
        "default": 5.0,
        "sectors": ["all"]
    },

    # ─── S2: Front Office ─────────────────────────────────────────────────────
    {
        "id": "S2_ANALYST_COUNT",
        "section": "S2",
        "question": "Number of research analysts",
        "type": "numeric",
        "help": "Multiplier for Research Coverage Amplification.",
        "default": 40.0,
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"]
    },
    {
        "id": "S2_NAMES_COVERED",
        "section": "S2",
        "question": "Average names / instruments covered per analyst",
        "type": "numeric",
        "help": "Industry ceiling without AI: 30–50 names. With AI: 90–200 names.",
        "default": 40.0,
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"]
    },
    {
        "id": "S2_PARSING_HOURS",
        "section": "S2",
        "question": "Hours per analyst/year spent on document parsing, data gathering",
        "type": "numeric",
        "help": "The hours AI can liberate. Peer median: 400–600 hrs/yr.",
        "default": 450.0,
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"]
    },
    {
        "id": "S2_ADMIN_PCT",
        "section": "S2",
        "question": "Share of RM / Agent / Sales time spent on admin (vs. client-facing)",
        "type": "percentage",
        "help": "AI can redirect 35–50% of this time to advisory work.",
        "default": 45,
        "sectors": ["all"]
    },
    {
        "id": "S2_ELECTRONIC_FLOW",
        "section": "S2",
        "question": "Share of order/application flow that is already electronic / STP",
        "type": "percentage",
        "help": "The non-electronic portion is the addressable market for Agentic Execution.",
        "default": 60,
        "sectors": ["all"]
    },
    {
        "id": "S2_SHORTFALL_BPS",
        "section": "S2",
        "question": "Average implementation shortfall in basis points",
        "type": "numeric",
        "help": "AI saves 2–5 bps across the addressable notional.",
        "default": 15.0,
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"]
    },
    {
        "id": "S2_ANNUAL_UNDERWRITING_APPS",
        "section": "S2",
        "question": "Annual life insurance / policy applications",
        "type": "numeric",
        "help": "Drives Underwriting Automation volume.",
        "default": 50000.0,
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
    },
    {
        "id": "S2_UNDERWRITER_FTE",
        "section": "S2",
        "question": "FTEs dedicated to manual underwriting & policy issuance",
        "type": "numeric",
        "help": "Drives FTE savings from automated underwriting.",
        "default": 15.0,
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
    },
    {
        "id": "S2_QUOTE_TO_BIND_DAYS",
        "section": "S2",
        "question": "Average quote-to-bind / new policy issuance turnaround (days)",
        "type": "numeric",
        "help": "The insurance analogue of 'time-to-fund' — AI-assisted underwriting compresses this to same-day/instant issuance for standard risks.",
        "default": 7.0,
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
    },
    {
        "id": "S2_FNOL_DIGITAL_PCT",
        "section": "S2",
        "question": "Share of claims First Notice of Loss (FNOL) received via digital / self-service channels",
        "type": "percentage",
        "help": "Digital FNOL (app, web, chatbot) is the entry point for AI-driven claims triage and fraud scoring. Leaders run 50-70% digital; call-center/agent-only shops are often <20%.",
        "default": 25,
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
    },

    # ─── S3: Middle & Back Office ─────────────────────────────────────────────
    {
        "id": "S3_STP",
        "section": "S3",
        "question": "Current overall Straight-Through Processing (STP) rate",
        "type": "percentage",
        "help": "Target post-AI: 90–95%. Each percentage point of STP uplift directly reduces FTE load. For insurers this spans new-business issuance, endorsements, and first-notice claims auto-adjudication.",
        "default": 65,
        "sectors": ["all"]
    },
    {
        "id": "S3_FTE_RECON",
        "section": "S3",
        "question": "FTEs dedicated to reconciliation & exception resolution",
        "type": "numeric",
        "help": "Fully-loaded cost per FTE: $120K–$180K. AI automates 50–85% of deterministic matching. Covers trade breaks in capital markets, and equally premium/bank reconciliation, bordereaux, and reinsurance settlement reconciliation in insurance.",
        "default": 8.0,
        "sectors": ["all"]
    },
    {
        "id": "S3_ANNUAL_BREAKS",
        "section": "S3",
        "question": "Total annual reconciliation breaks / exceptions",
        "type": "numeric",
        "help": "Enter actual count (e.g. 50000). Drives Error Avoidance computation — includes trade breaks, premium/bordereaux mismatches, and reinsurance recon items as applicable.",
        "default": 50000.0,
        "sectors": ["all"]
    },
    {
        "id": "S3_FAIL_EVENTS",
        "section": "S3",
        "question": "Annual operational failures / failed-settlement events",
        "type": "numeric",
        "help": "Each fail penalty: $5K–$50K.",
        "default": 200.0,
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"]
    },
    {
        "id": "S3_NAV_EXCEPTIONS",
        "section": "S3",
        "question": "Share of fund accounting / NAV effort spent on exception handling",
        "type": "percentage",
        "help": "AI predicts breaks before escalation, reducing this to <15%. For insurers: only relevant if you have a ULIP / unit-linked or variable-annuity book with daily-priced segregated funds — skip if traditional/non-linked products only.",
        "default": 40,
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services", "Life & General Insurance"]
    },
    {
        "id": "S3_CA_VOLUME",
        "section": "S3",
        "question": "Corporate action notices processed manually per month",
        "type": "numeric",
        "help": "GenAI extracts from unstructured PDFs.",
        "default": 1200.0,
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"]
    },
    {
        "id": "S3_ANNUAL_CLAIMS",
        "section": "S3",
        "question": "Annual insurance claims processed",
        "type": "numeric",
        "help": "Drives Claims Automation ROI. Peer median: 100,000.",
        "default": 100000.0,
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
    },
    {
        "id": "S3_CLAIMS_PROCESSOR_FTE",
        "section": "S3",
        "question": "FTEs dedicated to claims processing",
        "type": "numeric",
        "help": "Drives FTE savings from automated claims adjudication.",
        "default": 22.0,
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
    },
    {
        "id": "S3_CLAIMS_FRAUD_FLAG_PCT",
        "section": "S3",
        "question": "Share of claims flagged for potential fraud investigation",
        "type": "percentage",
        "help": "AI fraud-analytics models typically lift detection accuracy while cutting false referrals to SIU. Industry norm for flagged rate: roughly 5-10%.",
        "default": 7,
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
    },
    {
        "id": "S3_REINS_BORDEREAUX_VOL",
        "section": "S3",
        "question": "Reinsurance / MGA bordereaux processed manually per month",
        "type": "numeric",
        "help": "Bordereaux (premium & claims) arrive as unstructured spreadsheets/PDFs from cedants and MGAs — a high-value GenAI extraction target, directly analogous to corporate-action notice parsing in capital markets.",
        "default": 150.0,
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
    },

    # ─── S4: Risk & Compliance ────────────────────────────────────────────────
    {
        "id": "S4_ONBOARD_DAYS",
        "section": "S4",
        "question": "Average Time-to-Fund for a new institutional account (days)",
        "type": "numeric",
        "help": "AI compresses to 5–10 days.",
        "default": 45.0,
        "sectors": ["Mutual Funds / Asset Management", "Diversified Financial Services"]
    },
    {
        "id": "S4_AML_FALSE_POS",
        "section": "S4",
        "question": "AML false-positive alert rate",
        "type": "percentage",
        "help": "Industry shame: >80% of AML alerts are false positives. Each investigation: $500–$5K. Applies equally to insurer AML programs (life/annuity premium payments, large claims payouts).",
        "default": 85,
        "sectors": ["all"]
    },
    {
        "id": "S4_ONBOARD_FTE",
        "section": "S4",
        "question": "FTEs dedicated to KYC/AML and onboarding",
        "type": "numeric",
        "help": "AI automates 80–95% of structured onboarding steps.",
        "default": 6.0,
        "sectors": ["all"]
    },
    {
        "id": "S4_REG_MONTHS",
        "section": "S4",
        "question": "Time to operationalize a new regulatory reporting requirement (months)",
        "type": "numeric",
        "help": "AI-assisted compliance can cut this to 2–3 weeks.",
        "default": 6.0,
        "sectors": ["all"]
    },
    {
        "id": "S4_COMPLIANCE_FTE",
        "section": "S4",
        "question": "FTEs on regulatory reporting & trade surveillance",
        "type": "numeric",
        "help": "AI automates 60–80% of data gathering, validation, and report generation. For insurers, read as regulatory/solvency reporting and market-conduct surveillance.",
        "default": 10.0,
        "sectors": ["all"]
    },
    {
        "id": "S4_UNSERVED",
        "section": "S4",
        "question": "Unserved / underserved customer segments you cannot serve economically today",
        "type": "categorical",
        "options": [
            "Yes — significant segments not served (manual customisation uneconomical)",
            "Minor coverage gaps",
            "No — we serve all segments at acceptable margin",
        ],
        "default": "Yes — significant segments not served (manual customisation uneconomical)",
        "help": "AI makes hyper-personalisation economical at scale for previously unviable segments — wealth tiers in asset management; micro-insurance, gig-economy, and rural/low-income segments in insurance.",
        "sectors": ["all"]
    },
    {
        "id": "S4_RURAL_CUSTOMERS",
        "section": "S4",
        "question": "Target rural / semi-urban customers for digital onboarding",
        "type": "numeric",
        "help": "Drives Rural Digital Onboarding ROI.",
        "default": 100000.0,
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
    },
    {
        "id": "S4_VERNACULAR_SUPPORT",
        "section": "S4",
        "question": "Vernacular Language Support Maturity (Conversational AI)",
        "type": "categorical",
        "options": [
            "English-only / Basic Chatbot",
            "Multi-language (2-3 regional languages) for static FAQs",
            "Advanced Vernacular Voice & Text across India's 22 recognized languages"
        ],
        "default": "English-only / Basic Chatbot",
        "help": "Critical for scaling beyond tier-1 cities (960M internet users, 400M digital payment users).",
        "sectors": ["all"]
    },
    {
        "id": "S4_AGENTIC_READINESS",
        "section": "S4",
        "question": "Readiness for Agentic AI (Autonomous execution of financial workflows)",
        "type": "categorical",
        "options": [
            "Not Ready (Data silos, tribal knowledge)",
            "Exploring (Pilot projects for predictive models)",
            "Ready (Foundation models integrated, automated governance)"
        ],
        "default": "Not Ready (Data silos, tribal knowledge)",
        "help": "Measures readiness to move from predictive models to fully autonomous agentic execution.",
        "sectors": ["all"]
    },
    {
        "id": "S4_LAPSE_RATE",
        "section": "S4",
        "question": "Annual policy lapse / non-renewal rate",
        "type": "percentage",
        "help": "AI-driven early-warning models flag at-risk policyholders for targeted retention outreach before lapse — a core persistency lever for life insurers in particular.",
        "default": 12,
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
    },
    {
        "id": "S4_TELEMATICS_MATURITY",
        "section": "S4",
        "question": "Telematics / IoT usage-based insurance (UBI) data integration maturity",
        "type": "categorical",
        "options": [
            "No telematics/IoT data captured",
            "Piloting UBI on select products",
            "Integrated into pricing for select lines",
            "Fully integrated real-time dynamic pricing across the book"
        ],
        "default": "No telematics/IoT data captured",
        "help": "Primarily relevant to motor/P&C lines; leave at the default if your book is predominantly life/health with no telematics-priced products.",
        "sectors": ["Life & General Insurance", "Diversified Financial Services"]
    },

    # ─── S5: Legacy Diagnostics & Governance ─────────────────────────────────
    {
        "id": "S5_MAINTENANCE_COST",
        "section": "S5",
        "question": "Annual legacy system maintenance cost ($M) — licenses, infra, support, headcount",
        "type": "numeric",
        "help": "This is the Tech Debt numerator. Peer range: $2M–$20M for mid-tier firms.",
        "default": 6.5,
        "sectors": ["all"]
    },
    {
        "id": "S5_BIZ_VALUE",
        "section": "S5",
        "question": "Business value delivered by legacy systems annually ($M)",
        "type": "numeric",
        "help": "Tech Debt Interest Ratio = Maintenance / Value. >0.60 = Value-Destructive → Kill.",
        "default": 20.0,
        "sectors": ["all"]
    },
    {
        "id": "S5_DATA_STEWARDSHIP",
        "section": "S5",
        "question": "Data Governance & Stewardship Maturity",
        "type": "categorical",
        "options": [
            "Ad-hoc, largely tribal knowledge",
            "Defined owners but manual/spreadsheet tracking",
            "Automated metadata catalog and active stewardship",
            "Full active metadata with AI-assisted governance"
        ],
        "default": "Defined owners but manual/spreadsheet tracking",
        "help": "A prerequisite for AI models generating reliable outputs.",
        "sectors": ["all"]
    },
    {
        "id": "S5_DATA_OWNERSHIP",
        "section": "S5",
        "question": "Data ownership clarity — % of data entities with a defined, accountable owner",
        "type": "percentage",
        "help": "Governance pillar 1/5. <40% = critical gap that blocks a safe rebuild.",
        "default": 55,
        "sectors": ["all"]
    },
    {
        "id": "S5_LINEAGE",
        "section": "S5",
        "question": "Data lineage coverage — % of data lineage that is documented",
        "type": "percentage",
        "help": "Governance pillar 2/5. Required for regulatory traceability and AI audit trails.",
        "default": 35,
        "sectors": ["all"]
    },
    {
        "id": "S5_DQ_SLA",
        "section": "S5",
        "question": "Data Quality SLA adherence — % of data quality SLAs met",
        "type": "percentage",
        "help": "Governance pillar 3/5. Poor DQ silently inflates all AI lever costs.",
        "default": 72,
        "sectors": ["all"]
    },
    {
        "id": "S5_REGULATORY_TRACE",
        "section": "S5",
        "question": "Regulatory traceability — ability to trace any data point to its source for audit",
        "type": "percentage",
        "help": "Governance pillar 4/5. Critical for audit trails.",
        "default": 50,
        "sectors": ["all"]
    },
    {
        "id": "S5_CHANGE_MGMT",
        "section": "S5",
        "question": "Change management maturity — firm's ability to absorb technology change",
        "type": "percentage",
        "help": "Governance pillar 5/5. AI adoption is 70% people/process. Low score = execution risk.",
        "default": 45,
        "sectors": ["all"]
    },
]