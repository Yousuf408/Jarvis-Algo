"""
Dhan authentication and credentials management.
"""
import time
import requests
from core.config import PROXIES, DHAN_AUTH_URL, DHAN_TOKEN_TTL, DHAN_AUTO_RENEW_LEAD

# ================================================================
# Credentials Store
# ================================================================
_DHAN_CREDS = {
    "client_id": "",
    "pin": "",
    "totp_secret": "",
    "access_token": "",
    "broker_name": None,
    "connected_at": None,
    "token_issued_at": None,
    "token_last_renewed_at": None,
}

class _Cred:
    """Proxy that resolves to current value of a key."""
    __slots__ = ("_key",)
    def __init__(self, key):
        self._key = key
    def __str__(self):
        return _DHAN_CREDS.get(self._key) or ""
    def __bool__(self):
        return bool(_DHAN_CREDS.get(self._key))
    def __repr__(self):
        return f"_Cred({self._key!r}={str(self)!r})"

# Module-level proxies
DHAN_CLIENT_ID = _Cred("client_id")
DHAN_PIN = _Cred("pin")
DHAN_TOTP_SECRET = _Cred("totp_secret")
DHAN_ACCESS_TOKEN = _Cred("access_token")

def _cred(key):
    """Public reader."""
    return _DHAN_CREDS.get(key) or ""

def set_dhan_credentials(client_id, pin, totp_secret, broker_name="dhan"):
    _DHAN_CREDS["client_id"] = str(client_id or "").strip()
    _DHAN_CREDS["pin"] = str(pin or "").strip()
    _DHAN_CREDS["totp_secret"] = str(totp_secret or "").strip()
    _DHAN_CREDS["broker_name"] = broker_name
    _DHAN_CREDS["connected_at"] = time.time()

def set_dhan_access_token(token):
    tok = str(token or "").strip()
    _DHAN_CREDS["access_token"] = tok
    now = time.time()
    if tok:
        if not _DHAN_CREDS.get("token_issued_at"):
            _DHAN_CREDS["token_issued_at"] = now
        _DHAN_CREDS["token_last_renewed_at"] = now
    else:
        _DHAN_CREDS["token_issued_at"] = None
        _DHAN_CREDS["token_last_renewed_at"] = None

def clear_dhan_credentials():
    for key in _DHAN_CREDS:
        _DHAN_CREDS[key] = None if key in ("broker_name", "connected_at", "token_issued_at", "token_last_renewed_at") else ""

def renew_dhan_access_token():
    """Renew Dhan access token via /RenewToken endpoint."""
    cid = _DHAN_CREDS.get("client_id") or ""
    cur = _DHAN_CREDS.get("access_token") or ""
    
    if not cid or not cur:
        return {"ok": False, "detail": "not connected"}
    
    try:
        r = requests.get(
            "https://api.dhan.co/RenewToken",
            headers={"access-token": cur, "dhanClientId": cid},
            proxies=PROXIES,
            timeout=10,
        )
    except Exception as e:
        return {"ok": False, "detail": f"network error: {e}", "status_code": 0}
    
    if r.status_code == 200 and r.text:
        try:
            data = r.json()
        except Exception:
            data = {}
        new_token = (data.get("accessToken") or data.get("access_token") or "").strip()
        if new_token:
            set_dhan_access_token(new_token)
            return {"ok": True, "connected": True, "detail": "renewed", "status_code": 200}
    
    return {"ok": False, "connected": bool(cur), "detail": (r.text or "")[:200], "status_code": r.status_code}

# ================================================================
# Auto-renew loop
# ================================================================
async def dhan_auto_renew_loop():
    """Background task to auto-renew Dhan token."""
    while True:
        sleep_for = 60.0
        try:
            issued = _cred("token_issued_at")
            tok = _cred("access_token")
            if issued and tok:
                age = time.time() - float(issued)
                renew_at_age = DHAN_TOKEN_TTL - DHAN_AUTO_RENEW_LEAD
                if age >= renew_at_age:
                    print(f"[dhan] auto-renewing token (age={age/3600:.2f}h)")
                    res = await asyncio.to_thread(renew_dhan_access_token)
                    print(f"[dhan] auto-renew result: {res.get('ok')}")
                age = time.time() - float(issued)
                remaining = max(0.0, renew_at_age - age)
                sleep_for = min(max(30.0, remaining + 5.0), 15 * 60.0)
        except Exception as e:
            print(f"[dhan] auto-renew error: {e!r}")
        await asyncio.sleep(sleep_for)
