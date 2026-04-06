"""
Keyword-based topic classifier for admission queries.

Classifies against the normalized query so Roman Urdu terms already
translated by the normalizer still match English keywords.
"""

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "eligibility": [
        "eligible", "eligibility", "qualify", "qualification", "criteria",
        "marks", "percentage", "inter", "intermediate", "matric", "matriculation",
        "minimum", "required marks", "aggregate", "hssc", "ssc",
    ],
    "fees": [
        "fee", "fees", "payment", "cost", "amount", "charges", "voucher",
        "tuition", "prospectus fee", "kitna", "paisa", "rupee", "rs",
    ],
    "documents": [
        "document", "documents", "certificate", "transcript", "photo",
        "photograph", "attested", "original", "copy", "copies", "dmcs",
        "domicile", "cnic", "docs", "kagaz", "papers",
    ],
    "deadlines": [
        "deadline", "last date", "last day", "closing date", "schedule",
        "closing", "when", "date", "kab", "expire", "submission date",
    ],
    "merit": [
        "merit", "merit list", "result", "selected", "selection", "rank",
        "position", "waiting list", "marit", "cut off",
    ],
    "programs": [
        "program", "programme", "course", "department", "faculty", "bs",
        "ms", "mba", "bba", "bsc", "msc", "degree", "digree", "field",
        "subject", "discipline", "morning", "evening",
    ],
    "application": [
        "apply", "application", "how to apply", "submit", "submission",
        "form", "online", "process", "procedure", "registration",
        "enroll", "enrollment", "chahiye", "kaise",
    ],
}


def classify(query: str) -> str:
    """
    Classify a query into one of the topic categories.

    Args:
        query: Normalized query text (lowercase preferred)

    Returns:
        Topic name or "general" if no match found
    """
    query_lower = query.lower()

    best_topic = "general"
    best_score = 0

    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic
