"""
Tests for the keyword topic classifier — in particular that it matches whole
words, not substrings.
"""
from app.services.analytics.topic_classifier import classify


class TestTopicClassifier:
    def test_fees(self):
        assert classify("how much is the admission fee") == "fees"

    def test_documents(self):
        assert classify("which documents and certificates are required") == "documents"

    def test_deadlines(self):
        assert classify("what is the last date to submit the form") in ("deadlines", "application")

    def test_no_match_is_general(self):
        assert classify("tell me about the campus cafeteria") == "general"

    def test_substring_does_not_falsely_match(self):
        # "date" must not fire on "candidate", "rs" must not fire on "courses",
        # "inter" must not fire on "internet" — none of these should land in
        # deadlines / fees / eligibility on substring alone.
        assert classify("is the internet good for candidates") == "general"

    def test_normalized_roman_urdu_terms(self):
        # 'chahiye' / 'kaise' survive normalization and map to application
        assert classify("apply kaise karna hai") == "application"
