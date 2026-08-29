import pytest
from app.services.extractor import OTPExtractor


@pytest.fixture
def ex():
    return OTPExtractor()


def conf_for(results, code):
    """Pull the confidence float for a given code out of the result list."""
    for c, conf in results:
        if c == code:
            return conf
    return None


# ---------------------------------------------------------------------------
# is_otp_message — the gate that decides whether extraction even runs
# ---------------------------------------------------------------------------
def test_is_otp_true_on_keyword(ex):
    assert ex.is_otp_message("Your verification code", "here it is", "") is True


@pytest.mark.parametrize(
    "kw,body",
    [
        ("otp", "your otp is on the way"),
        ("security code", "security code requested"),
        ("two-factor", "two-factor auth enabled"),
        ("2fa", "2fa prompt sent"),
        ("sign-in code", "sign-in code delivered"),
        ("confirm your identity", "please confirm your identity"),
        ("one-time password", "one-time password issued"),
        ("authorization code", "authorization code generated"),
    ],
)
def test_is_otp_true_on_various_keywords(ex, kw, body):
    assert ex.is_otp_message("nothing relevant", body, "") is True


def test_is_otp_true_on_trusted_domain_sender(ex):
    # sender on a trusted DOMAIN (not a full email in the set) still passes
    assert ex.is_otp_message("hi", "random text no keywords", "bot@accounts.google.com") is True


def test_is_otp_true_on_trusted_email_sender(ex):
    # full-email entries in TRUSTED_SENDERS match via the exact-address path
    assert ex.is_otp_message("hi", "random text no keywords", "noreply@google.com") is True


def test_is_otp_false_on_untrusted_and_no_keyword(ex):
    assert ex.is_otp_message("hi", "just saying hello friend", "rand@evil.com") is False


def test_is_otp_false_on_empty(ex):
    assert ex.is_otp_message("", "", "") is False


# ---------------------------------------------------------------------------
# _is_trusted_sender — direct unit coverage of the trust resolver
# ---------------------------------------------------------------------------
def test_trusted_domain_match(ex):
    assert ex._is_trusted_sender("bot@accounts.google.com") is True


def test_trusted_email_match(ex):
    assert ex._is_trusted_sender("noreply@google.com") is True


def test_untrusted_sender(ex):
    assert ex._is_trusted_sender("someone@gmail.com") is False


def test_empty_sender_not_trusted(ex):
    assert ex._is_trusted_sender("") is False


# ---------------------------------------------------------------------------
# Happy-path extraction (kept from the original smoke suite, still valid)
# ---------------------------------------------------------------------------
def test_extract_6_digit_code(ex):
    codes = ex.extract_all_codes(
        "Your verification code",
        "Hello, your verification code is 123456. Do not share it.",
        "security@example.com",
    )
    assert len(codes) > 0
    assert codes[0][0] == "123456"


def test_extract_alphanumeric_code(ex):
    codes = ex.extract_all_codes(
        "Login attempt",
        "Use code A8B29C to log in.",
        "no-reply@service.com",
    )
    assert len(codes) > 0
    assert codes[0][0] == "A8B29C"


def test_ignore_phone_numbers(ex):
    # the real 6-digit code ranks above any phone-number fragment
    codes = ex.extract_all_codes(
        "Contact us",
        "Call us at 1-800-555-0199 or use code 987654.",
        "support@store.com",
    )
    assert len(codes) > 0
    assert codes[0][0] == "987654"


# ---------------------------------------------------------------------------
# HTML body handling
# ---------------------------------------------------------------------------
def test_strip_html_noop_without_tags(ex):
    assert ex._strip_html("plain text here") == "plain text here"


def test_extract_from_html_body(ex):
    html = "<div><span>Your code:</span> <b>483920</b></div>"
    codes = ex.extract_all_codes("verification code", html, "no-reply@accounts.google.com")
    assert "483920" in [c for c, _ in codes]


def test_html_with_google_g_code(ex):
    html = "<p>Verify: <b>G-778899</b></p>"
    codes = ex.extract_all_codes("verification code", html, "no-reply@accounts.google.com")
    assert "778899" in [c for c, _ in codes]


# ---------------------------------------------------------------------------
# Google G- prefixed codes (note: the G- prefix itself is stripped, the
# numeric payload is what gets captured — verified behavior, not a guess)
# ---------------------------------------------------------------------------
def test_extract_google_g_code_uppercase(ex):
    codes = ex.extract_all_codes(
        "Security alert",
        "G-123456 is your Google verification code.",
        "no-reply@accounts.google.com",
    )
    assert "123456" in [c for c, _ in codes]
    assert conf_for(codes, "123456") == 1.0  # 0.95 base + 0.05 sender, capped


def test_extract_lowercase_g_code(ex):
    codes = ex.extract_all_codes(
        "Google verify",
        "g-246810 is the code",
        "no-reply@accounts.google.com",
    )
    assert "246810" in [c for c, _ in codes]


# ---------------------------------------------------------------------------
# Proximity bonus — a code near a keyword scores higher than one far away
# ---------------------------------------------------------------------------
def test_proximity_bonus_applied(ex):
    # "two-factor" is the is_otp keyword but does NOT sit directly before a
    # digit, so it can't leak through pattern 2/3 — it only feeds proximity.
    # Codes are space-padded so the \b word boundaries fire (digits glued to
    # the x-run would never match).
    body = " 111111 " + ("x" * 200) + " 222222"
    codes = ex.extract_all_codes("two-factor", body, "rand@evil.com")
    c111 = conf_for(codes, "111111")
    c222 = conf_for(codes, "222222")
    assert c111 is not None and c222 is not None
    assert c111 == pytest.approx(0.70)   # 0.60 base + 0.10 proximity
    assert c222 == pytest.approx(0.60)   # no keyword within window


# ---------------------------------------------------------------------------
# Trusted-sender confidence bonus (+0.05 on every code)
# ---------------------------------------------------------------------------
def test_trusted_sender_bonus_applied(ex):
    body = " 111111 " + ("x" * 200) + " 222222"
    untrusted = ex.extract_all_codes("two-factor", body, "rand@evil.com")
    trusted = ex.extract_all_codes("two-factor", body, "noreply@google.com")
    # 222222 has no proximity in either case, so the only delta is the sender bump
    assert conf_for(untrusted, "222222") == pytest.approx(0.60)
    assert conf_for(trusted, "222222") == pytest.approx(0.65)
    # and the near code shows the same +0.05 delta
    assert conf_for(untrusted, "111111") == pytest.approx(0.70)
    assert conf_for(trusted, "111111") == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# Confidence never exceeds 1.0
# ---------------------------------------------------------------------------
def test_confidence_capped_at_one(ex):
    codes = ex.extract_all_codes(
        "your code",
        "your code G-123456",
        "no-reply@accounts.google.com",
    )
    for _, conf in codes:
        assert conf <= 1.0
    assert conf_for(codes, "123456") == 1.0


def test_confidence_never_exceeds_one_on_mixed_input(ex):
    body = "G-123456 use code 654321 " + ("x" * 200) + "999888"
    codes = ex.extract_all_codes("two-factor", body, "noreply@google.com")
    for _, conf in codes:
        assert conf <= 1.0


# ---------------------------------------------------------------------------
# Case normalization + the digit/uppercase filter
# ---------------------------------------------------------------------------
def test_lowercase_alphanumeric_normalized(ex):
    codes = ex.extract_all_codes(
        "one-time password",
        "Your one-time password is a8b29c",
        "rand@evil.com",
    )
    assert "A8B29C" in [c for c, _ in codes]


def test_titlecased_word_filtered_but_allcaps_leaks(ex):
    # trusted sender lets a keyword-less message through
    codes = ex.extract_all_codes("hello", "Hello WORLD friend", "noreply@google.com")
    found = [c for c, _ in codes]
    # "Hello" has lowercase => fails the [A-Z0-9] pattern, never captured
    assert "HELLO" not in found
    # KNOWN WEAKNESS: a fully-uppercase non-code word still leaks through
    # because it satisfies the alphanumeric pattern and the isupper() guard.
    assert "WORLD" in found


# ---------------------------------------------------------------------------
# Short-code rejection
# ---------------------------------------------------------------------------
def test_short_code_rejected(ex):
    codes = ex.extract_all_codes("otp", "your code is AB1 now", "rand@evil.com")
    assert conf_for(codes, "AB1") is None


# ---------------------------------------------------------------------------
# Sorting + top-code helpers
# ---------------------------------------------------------------------------
def test_results_sorted_by_confidence_desc(ex):
    body = "G-123456 use code 654321 " + ("x" * 200) + "999888"
    codes = ex.extract_all_codes("two-factor", body, "noreply@google.com")
    confs = [c for _, c in codes]
    assert confs == sorted(confs, reverse=True)


def test_extract_code_returns_none_when_not_otp(ex):
    assert ex.extract_code("hey", "just chatting", "rand@evil.com") is None


def test_extract_code_returns_top_code(ex):
    code = ex.extract_code(
        "verification code",
        "your verification code is 554433",
        "sec@example.com",
    )
    assert code == "554433"


def test_empty_input_returns_empty(ex):
    assert ex.extract_all_codes("", "", "") == []
