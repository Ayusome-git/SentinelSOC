import ipaddress
import uuid
import re

ALLOWED_ACTIONS = {
    "BLOCK_SOURCE_IP": ["IP_ADDRESS"],
    "LOCK_USER": ["USER_ID", "USERNAME"],
    "REVOKE_SESSION": ["SESSION_ID"],
    "RATE_LIMIT_SOURCE": ["IP_ADDRESS"],
    "DISABLE_API_ACCESS": ["API_KEY_ID", "USER_ID"]
}

def validate_action_and_target(action_type: str, target_type: str, target_value: str) -> bool:
    """
    Validates that an action type is allowed, that the target type is permitted for that action,
    and that the target value matches the expected format for that target type.
    """
    if action_type not in ALLOWED_ACTIONS:
        return False
        
    if target_type not in ALLOWED_ACTIONS[action_type]:
        return False
        
    # Prevent enormous targets
    if len(target_value) > 255:
        return False

    if target_type == "IP_ADDRESS":
        try:
            ipaddress.ip_address(target_value)
            return True
        except ValueError:
            return False
            
    elif target_type in ("USER_ID", "API_KEY_ID"):
        try:
            uuid.UUID(target_value)
            return True
        except ValueError:
            return False
            
    elif target_type == "USERNAME":
        # Alphanumeric, underscores, hyphens, @ for emails. Length 3-100.
        return bool(re.match(r"^[\w.@-]{3,100}$", target_value))
        
    elif target_type == "SESSION_ID":
        # Alphanumeric, hyphens, underscores.
        return bool(re.match(r"^[\w-]{8,128}$", target_value))
        
    return False
