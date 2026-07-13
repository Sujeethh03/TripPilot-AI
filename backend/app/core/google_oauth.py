"""Verify Google Sign-In ID tokens.

The frontend uses Google Sign-In to obtain an ID token (a signed JWT) and posts
it to `POST /auth/google`. We verify the signature + audience against Google's
public keys here. The network/crypto call is isolated in `verify_google_token`
so the endpoint (and its tests) mock a single seam — same pattern as the LLM
node boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config import get_settings


@dataclass(frozen=True)
class GoogleIdentity:
    google_id: str  # the stable Google account id ("sub")
    email: str
    name: str | None


def verify_google_token(token: str) -> GoogleIdentity | None:
    """Return the verified identity, or None if the token is invalid/untrusted.

    Validates signature, expiry, issuer, and audience (our client id). Returns
    None rather than raising so the endpoint maps cleanly to a 401.
    """
    client_id = get_settings().google_client_id
    if not client_id:
        return None
    try:
        claims = google_id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
            token, google_requests.Request(), client_id
        )
    except ValueError:
        return None

    sub = claims.get("sub")
    email = claims.get("email")
    if not sub or not email:
        return None
    return GoogleIdentity(google_id=sub, email=email, name=claims.get("name"))
