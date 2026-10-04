"""
Question bank.

Provides a curated set of interview questions across the categories required
by the project spec (HR, Behavioural, Technical, Situational) with technical CS
subcategories (Data Structures, OOP, DBMS, Operating Systems, System Design
Basics), plus difficulty levels and industry tags.

The questions are seeded into MongoDB (collection `questions`) on first use so
the API can support filtering/search/pagination and scale to 500+ questions
without hard-coding low-quality duplicates. The curated seed below is the
authoritative starter set; more can be inserted through the DB at any time.
"""

CATEGORIES = ["HR", "Behavioural", "Technical", "Situational"]
TECHNICAL_SUBCATEGORIES = [
    "Data Structures", "OOP", "DBMS", "Operating Systems", "System Design Basics",
]
DIFFICULTIES = ["Easy", "Medium", "Hard"]


def _q(text, category, difficulty="Medium", subcategory=None, industry="General"):
    return {
        "text": text,
        "category": category,
        "subcategory": subcategory,
        "difficulty": difficulty,
        "industry": industry,
    }


# --- Curated seed set -------------------------------------------------------
SEED_QUESTIONS = [
    # HR
    _q("Tell me about yourself.", "HR", "Easy"),
    _q("Why do you want to work here?", "HR", "Easy"),
    _q("What are your greatest strengths?", "HR", "Easy"),
    _q("What is your greatest weakness?", "HR", "Medium"),
    _q("Where do you see yourself in five years?", "HR", "Medium"),
    _q("Why are you leaving your current job?", "HR", "Medium"),
    _q("What are your salary expectations?", "HR", "Medium"),
    _q("What motivates you at work?", "HR", "Easy"),
    _q("How do you handle stress and pressure?", "HR", "Medium"),
    _q("Why should we hire you?", "HR", "Medium"),

    # Behavioural
    _q("Tell me about a time you led a team.", "Behavioural", "Medium"),
    _q("Describe a challenge you overcame.", "Behavioural", "Medium"),
    _q("Give an example of a conflict at work and how you resolved it.", "Behavioural", "Medium"),
    _q("Tell me about a time you failed and what you learned.", "Behavioural", "Hard"),
    _q("Describe a situation where you had to meet a tight deadline.", "Behavioural", "Medium"),
    _q("Give an example of when you showed initiative.", "Behavioural", "Medium"),
    _q("Tell me about a time you disagreed with your manager.", "Behavioural", "Hard"),
    _q("Describe your greatest professional achievement.", "Behavioural", "Medium"),
    _q("Tell me about a time you worked with a difficult teammate.", "Behavioural", "Medium"),
    _q("Describe a time you had to learn something new quickly.", "Behavioural", "Medium"),

    # Situational
    _q("How would you handle a project that is falling behind schedule?", "Situational", "Medium"),
    _q("What would you do if you disagreed with a decision made by your team?", "Situational", "Medium"),
    _q("How would you prioritise multiple urgent tasks with the same deadline?", "Situational", "Medium"),
    _q("If a client was unhappy with your work, how would you respond?", "Situational", "Medium"),
    _q("How would you onboard yourself in the first 90 days of a new role?", "Situational", "Medium"),
    _q("What would you do if you noticed a colleague making a serious mistake?", "Situational", "Hard"),
    _q("How would you handle receiving critical feedback on your work?", "Situational", "Medium"),
    _q("If you were assigned a task outside your expertise, how would you approach it?", "Situational", "Medium"),

    # Technical - Data Structures
    _q("How does a binary search tree work?", "Technical", "Medium", "Data Structures"),
    _q("Explain the difference between an array and a linked list.", "Technical", "Easy", "Data Structures"),
    _q("What is a hash table and how does it handle collisions?", "Technical", "Medium", "Data Structures"),
    _q("Explain the difference between a stack and a queue.", "Technical", "Easy", "Data Structures"),
    _q("What is the time complexity of common operations on a balanced BST?", "Technical", "Hard", "Data Structures"),
    _q("Explain the concept of recursion with an example.", "Technical", "Medium", "Data Structures"),

    # Technical - OOP
    _q("Explain the four pillars of object-oriented programming.", "Technical", "Medium", "OOP"),
    _q("What is the difference between composition and inheritance?", "Technical", "Medium", "OOP"),
    _q("What is polymorphism and give an example.", "Technical", "Medium", "OOP"),
    _q("Explain the difference between an abstract class and an interface.", "Technical", "Medium", "OOP"),
    _q("What are SOLID principles?", "Technical", "Hard", "OOP"),

    # Technical - DBMS
    _q("What is the difference between SQL and NoSQL databases?", "Technical", "Medium", "DBMS"),
    _q("How does indexing work in databases?", "Technical", "Medium", "DBMS"),
    _q("Explain database normalization and its normal forms.", "Technical", "Hard", "DBMS"),
    _q("What are ACID properties in a database transaction?", "Technical", "Medium", "DBMS"),
    _q("Explain the difference between a primary key and a foreign key.", "Technical", "Easy", "DBMS"),

    # Technical - Operating Systems
    _q("What is the difference between a process and a thread?", "Technical", "Medium", "Operating Systems"),
    _q("What is a deadlock and how do you prevent it?", "Technical", "Hard", "Operating Systems"),
    _q("Explain the difference between paging and segmentation.", "Technical", "Hard", "Operating Systems"),
    _q("What is a context switch?", "Technical", "Medium", "Operating Systems"),
    _q("Explain how virtual memory works.", "Technical", "Hard", "Operating Systems"),

    # Technical - System Design Basics
    _q("What is a RESTful API and what are its principles?", "Technical", "Medium", "System Design Basics"),
    _q("Explain the difference between REST and GraphQL.", "Technical", "Medium", "System Design Basics"),
    _q("What is load balancing and why is it used?", "Technical", "Medium", "System Design Basics"),
    _q("Explain the difference between horizontal and vertical scaling.", "Technical", "Medium", "System Design Basics"),
    _q("What is caching and where would you apply it in a system?", "Technical", "Medium", "System Design Basics"),
    _q("Explain the MVC architecture pattern.", "Technical", "Medium", "System Design Basics"),
    _q("What is the difference between TCP and UDP?", "Technical", "Medium", "System Design Basics"),
]


def seed_questions(db):
    """Insert the curated seed set once (idempotent on question text)."""
    col = db.questions
    try:
        col.create_index("text", unique=True)
    except Exception:  # noqa: BLE001 - index may already exist
        pass
    inserted = 0
    for q in SEED_QUESTIONS:
        try:
            res = col.update_one({"text": q["text"]}, {"$setOnInsert": q}, upsert=True)
            if res.upserted_id is not None:
                inserted += 1
        except Exception:  # noqa: BLE001
            continue
    return inserted


def query_questions(db, category=None, subcategory=None, difficulty=None,
                    industry=None, search=None, limit=100, skip=0):
    """Filterable, searchable query over the questions collection."""
    query = {}
    if category:
        query["category"] = category
    if subcategory:
        query["subcategory"] = subcategory
    if difficulty:
        query["difficulty"] = difficulty
    if industry and industry != "General":
        query["industry"] = industry
    if search:
        query["text"] = {"$regex": _escape_regex(search), "$options": "i"}

    cursor = db.questions.find(query).skip(int(skip)).limit(int(limit))
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    total = db.questions.count_documents(query)
    return {"questions": results, "total": total}


def _escape_regex(text):
    import re
    return re.escape(str(text))
