"""
Signal — Application Constants
Constants for priority buckets, processing tiers, entity types, and defaults.
"""

# Priority Buckets
BUCKET_DO_NOW = "do_now"
BUCKET_TODAY = "today"
BUCKET_THIS_WEEK = "this_week"
BUCKET_WAITING = "waiting"
BUCKET_COMPLETED = "completed"
BUCKET_IGNORED = "ignored"

ALL_BUCKETS = [
    BUCKET_DO_NOW,
    BUCKET_TODAY,
    BUCKET_THIS_WEEK,
    BUCKET_WAITING,
    BUCKET_COMPLETED,
    BUCKET_IGNORED,
]

# Processing Tiers
TIER_AUTO_SKIP = 0    # Tier 0: Blocklisted/Marketing (auto-archive, zero AI cost)
TIER_RULE_BASED = 1   # Tier 1: Rules-based (heuristics, minimal processing)
TIER_FULL_AI = 2      # Tier 2: Full AI processing

# Entity Types
ENTITY_JOB_APP = "job_application"
ENTITY_INTERVIEW = "interview"
ENTITY_ORDER = "order"
ENTITY_DELIVERY = "delivery"
ENTITY_BILL = "bill"
ENTITY_PAYMENT = "payment"
ENTITY_SUBSCRIPTION = "subscription"
ENTITY_TRAVEL = "travel"
ENTITY_EVENT = "event"
ENTITY_PROJECT = "project"
ENTITY_PERSON = "person"
ENTITY_COMPANY = "company"
ENTITY_COURSE = "course"
ENTITY_OTHER = "other"

# Sender Types
SENDER_IMPORTANT = "important"
SENDER_REGULAR = "regular"
SENDER_NEWSLETTER = "newsletter"
SENDER_MARKETING = "marketing"
SENDER_TRANSACTIONAL = "transactional"
SENDER_AUTOMATED = "automated"
SENDER_SPAM = "spam"
SENDER_UNKNOWN = "unknown"
