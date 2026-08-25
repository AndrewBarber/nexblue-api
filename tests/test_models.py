"""Tests for NexBlue API data models."""

import base64
import json

from nexblue_api.models import ChargerStatus, TokenBundle


def _access_token_with_claims(claims: dict[str, object]) -> str:
    """Return a non-sensitive JWT-shaped token for model tests."""
    header = base64.urlsafe_b64encode(b'{"alg":"RS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.signature"


def test_token_bundle_extracts_cognito_subject() -> None:
    """Expose the stable Cognito subject from an access token."""
    token = TokenBundle.from_api(
        {
            "access_token": _access_token_with_claims(
                {"sub": "00000000-0000-0000-0000-000000000001"}
            ),
            "refresh_token": "refresh-token",
            "expires_in": 600,
        }
    )

    assert token.account_id == "00000000-0000-0000-0000-000000000001"


def test_token_bundle_omits_account_id_for_invalid_or_missing_subject() -> None:
    """Do not expose an account ID when the access token cannot provide one."""
    malformed = TokenBundle.from_api(
        {"access_token": "not-a-jwt", "refresh_token": None, "expires_in": 600}
    )
    missing_subject = TokenBundle.from_api(
        {
            "access_token": _access_token_with_claims({"token_use": "access"}),
            "refresh_token": None,
            "expires_in": 600,
        }
    )

    assert malformed.account_id is None
    assert missing_subject.account_id is None


def test_charger_status_uses_numeric_charging_state() -> None:
    """Normalize the required charging state to an integer."""
    status = ChargerStatus.from_api(
        "NB123456",
        {"charging_state": 2},
    )

    assert status.charging_state == 2
