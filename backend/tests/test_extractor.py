import pytest
from app.services.extractor import OTPExtractor

@pytest.fixture
def extractor():
    return OTPExtractor()

def test_extract_6_digit_code(extractor):
    subject = "Your verification code"
    body = "Hello, your verification code is 123456. Do not share it."
    sender = "security@example.com"
    
    codes = extractor.extract_all_codes(subject, body, sender)
    assert len(codes) > 0
    assert codes[0][0] == "123456"

def test_extract_alphanumeric_code(extractor):
    subject = "Login attempt"
    body = "Use code A8B29C to log in."
    sender = "no-reply@service.com"
    
    codes = extractor.extract_all_codes(subject, body, sender)
    assert len(codes) > 0
    assert codes[0][0] == "A8B29C"

def test_ignore_phone_numbers(extractor):
    subject = "Contact us"
    body = "Call us at 1-800-555-0199 or use code 987654."
    sender = "support@store.com"
    
    codes = extractor.extract_all_codes(subject, body, sender)
    assert len(codes) > 0
    # Should extract the 6-digit code, not the phone number
    assert codes[0][0] == "987654"

def test_confidence_scoring(extractor):
    subject1 = "Your Amazon authentication code"
    body1 = "889922"
    sender1 = "account-update@amazon.com"
    
    subject2 = "Random email"
    body2 = "Here is a number 889922"
    sender2 = "friend@gmail.com"
    
    codes1 = extractor.extract_all_codes(subject1, body1, sender1)
    codes2 = extractor.extract_all_codes(subject2, body2, sender2)
    
    # Trusted sender + keyword should yield higher confidence
    assert codes1[0][1] > codes2[0][1]
