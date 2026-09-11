import secrets
from app.core.security import pwd_context

ENV_PREFIX_MAP = {
    "DEVELOPMENT": "dev",
    "STAGING": "test",
    "PRODUCTION": "live"
}

def generate_api_key(environment: str) -> tuple[str, str, str]:
    """
    Generates a secure API key.
    
    Returns:
        tuple[str, str, str]: (raw_api_key, key_prefix, key_hash)
    """
    env_str = ENV_PREFIX_MAP.get(environment.upper(), "dev")
    
    # 4 random hex chars for the identifiable prefix
    short_prefix = secrets.token_hex(2)
    key_prefix = f"ssk_{env_str}_{short_prefix}"
    
    # Secure random secret
    secret_part = secrets.token_urlsafe(32)
    raw_api_key = f"{key_prefix}{secret_part}"
    
    # Hash the key using existing Argon2id context
    key_hash = pwd_context.hash(raw_api_key)
    
    return raw_api_key, key_prefix, key_hash

def verify_api_key(raw_api_key: str, key_hash: str) -> bool:
    """
    Verifies a raw API key against a stored hash.
    """
    return pwd_context.verify(raw_api_key, key_hash)

def extract_key_prefix(raw_api_key: str) -> str:
    """
    Extracts the prefix from a raw API key to allow database lookups.
    Example: ssk_live_a82fXXXXXXXXX -> ssk_live_a82f
    """
    parts = raw_api_key.split('_')
    if len(parts) >= 3:
        # Reconstruct the prefix: "ssk" + "_" + "live" + "_" + "a82f"
        return f"{parts[0]}_{parts[1]}_{parts[2][:4]}"
    return ""
