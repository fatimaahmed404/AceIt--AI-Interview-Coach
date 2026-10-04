"""Unit tests for question_bank query logic using a minimal fake collection."""
import question_bank


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    def skip(self, n):
        self._docs = self._docs[n:]
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    def __iter__(self):
        return iter(self._docs)


class FakeCollection:
    def __init__(self, docs):
        self.docs = docs

    def find(self, query):
        return FakeCursor(self._match(query))

    def count_documents(self, query):
        return len(self._match(query))

    def _match(self, query):
        out = []
        for d in self.docs:
            ok = True
            for k, v in query.items():
                if isinstance(v, dict) and "$regex" in v:
                    import re
                    if not re.search(v["$regex"], str(d.get(k, "")), re.I):
                        ok = False
                        break
                elif d.get(k) != v:
                    ok = False
                    break
            if ok:
                out.append(dict(d))
        return out


class FakeDB:
    def __init__(self, docs):
        self.questions = FakeCollection(docs)


def _docs():
    return [
        {"_id": 1, "text": "Tell me about yourself.", "category": "HR", "difficulty": "Easy", "subcategory": None, "industry": "General"},
        {"_id": 2, "text": "How does a binary search tree work?", "category": "Technical", "difficulty": "Medium", "subcategory": "Data Structures", "industry": "General"},
        {"_id": 3, "text": "What is a deadlock?", "category": "Technical", "difficulty": "Hard", "subcategory": "Operating Systems", "industry": "General"},
    ]


def test_filter_by_category():
    db = FakeDB(_docs())
    res = question_bank.query_questions(db, category="Technical")
    assert res["total"] == 2
    assert all(q["category"] == "Technical" for q in res["questions"])


def test_filter_by_subcategory():
    db = FakeDB(_docs())
    res = question_bank.query_questions(db, subcategory="Data Structures")
    assert res["total"] == 1


def test_search_is_case_insensitive_substring():
    db = FakeDB(_docs())
    res = question_bank.query_questions(db, search="BINARY")
    assert res["total"] == 1
    assert "binary" in res["questions"][0]["text"].lower()


def test_seed_set_covers_required_categories():
    cats = {q["category"] for q in question_bank.SEED_QUESTIONS}
    assert {"HR", "Behavioural", "Technical", "Situational"} <= cats


def test_seed_covers_all_technical_subcategories():
    subs = {q["subcategory"] for q in question_bank.SEED_QUESTIONS if q["category"] == "Technical"}
    assert set(question_bank.TECHNICAL_SUBCATEGORIES) <= subs
