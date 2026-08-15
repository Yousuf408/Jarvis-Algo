"""
Angel One authentication using SmartConnect SDK.
"""
import time
from SmartApi import SmartConnect
from core.config import PROXIES, ANGEL_TOKEN_TTL, ANGEL_AUTO_RENEW_LEAD

# ================================================================
# Credentials Store
# ================================================================
_CREDS = {
    "api_key": "",
    "client_id": "",
    "password": "",
    "totp_secret": "",
    "access_token": "",
    "refresh_token": "",
    "feed_token": "",
    "token_issued_at": 0,
}

_SMART_API = None

def set_angel_credentials(api_key, client_id, password, totp_secret=None):
    _CREDS["api_key"] = str(api_key or "").strip()
    _CREDS["client_id"] = str(client_id or "").strip()
    _CREDS["password"] = str(password or "").strip()
    _CREDS["totp_secret"] = str(totp_secret or "").strip() if totp_secret else ""

def get_access_token():
    return _CREDS.get("access_token", "")

def get_feed_token():
    return _CREDS.get("feed_token", "")

def is_connected():
    return bool(_CREDS.get("access_token"))

def disconnect():
    global _SMART_API
    for key in _CREDS:
        _CREDS[key] = ""
    _SMART_API = None

def _make_smart_connect():
    sc = SmartConnect(api_key=_CREDS.get("api_key"))
    sc.proxies = PROXIES
    return sc

def authenticate():
    """Authenticate with Angel One using SmartConnect SDK."""
    api_key = _CREDS.get("api_key")
    client_id = _CREDS.get("client_id")
    password = _CREDS.get("password")
    totp_secret = _CREDS.get("totp_secret")
    
    if not api_key or not client_id or not password:
        return {"ok": False, "error": "Missing credentials"}
    
    try:
        smart_api = _make_smart_connect()
        
        totp_code = None
        if totp_secret:
            try:
                import pyotp
                totp_code = pyotp.TOTP(totp_secret).now()
            except Exception:
                pass
        
        data = smart_api.generateSession(client_id, password, totp_code or "")
        
        if data is None:
            return {"ok": False, "error": "SmartConnect returned None"}
        
        if data.get("status") == False:
            return {"ok": False, "error": data.get("message") or data.get("error") or "Authentication failed"}
        
        jwt_token_raw = data["data"].get("jwtToken", "")
        refresh_token = data["data"].get("refreshToken", "")
        
        if not jwt_token_raw:
            return {"ok": False, "error": "No jwtToken in response"}
        
        jwt_token = jwt_token_raw.replace("Bearer ", "")
        
        try:
            feed_token = smart_api.getfeedToken()
        except Exception:
            feed_token = data["data"].get("feedToken") or data["data"].get("feed_token", "")
        
        _CREDS["access_token"] = jwt_token
        _CREDS["refresh_token"] = refresh_token
        _CREDS["token_issued_at"] = str(time.time())
        if feed_token:
            _CREDS["feed_token"] = str(feed_token)
        
        global _SMART_API
        smart_api.setAccessToken(jwt_token)
        smart_api.setUserId(client_id)
        _SMART_API = smart_api
        
        return {"ok": True, "access_token": jwt_token, "refresh_token": refresh_token, "feed_token": feed_token or ""}
    
    except Exception as e:
        err = str(e)
        if "Request Rejected" in err:
            return {"ok": False, "error": "WAF blocked - verify API key and proxy whitelisting"}
        return {"ok": False, "error": err}

# ================================================================
# Auto-renew loop
# ================================================================
async def angel_auto_renew_loop():
    """Background task to auto-renew Angel One token."""
    while True:
        sleep_for = 300.0
        try:
            issued_str = _CREDS.get("token_issued_at", "0")
            tok = _CREDS.get("access_token", "")
            if issued_str and tok:
                try:
                    issued = float(issued_str) if issued_str else 0
                except ValueError:
                    issued = 0
                age = time.time() - issued
                renew_at_age = ANGEL_TOKEN_TTL - ANGEL_AUTO_RENEW_LEAD
                if age >= renew_at_age:
                    print(f"[angel] auto-renewing token (age={age/3600:.2f}h)")
                    res = await asyncio.to_thread(authenticate)
                    print(f"[angel] auto-renew result: ok={res.get('ok')}")
                age = time.time() - float(issued or "0")
                remaining = max(0.0, renew_at_age - age)
                sleep_for = min(max(30.0, remaining + 5.0), 15 * 60.0)
        except Exception as e:
            print(f"[angel] auto-renew error: {e!r}")
        await asyncio.sleep(sleep_for)
