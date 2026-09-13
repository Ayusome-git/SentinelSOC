import httpx
import logging
from typing import Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

class ApplicationResponseClient:
    """
    Client for interacting with integrated applications to execute response actions securely.
    """
    
    @staticmethod
    async def execute_action(
        webhook_url: str,
        secret: str,
        action: str,
        target_type: str,
        target_value: str,
        request_id: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Executes a response action against the configured application webhook.
        
        Args:
            webhook_url: The destination endpoint
            secret: The authorization secret for the endpoint
            action: The action to perform (e.g. BLOCK_SOURCE_IP)
            target_type: The type of target (e.g. IP_ADDRESS)
            target_value: The value to block
            request_id: Idempotency key (ResponseAction ID)
            
        Returns:
            Tuple of (Success bool, Result Summary, Raw Response JSON)
        """
        payload = {
            "action": action,
            "target": {
                "type": target_type,
                "value": target_value
            },
            "request_id": str(request_id)
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {secret}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=settings.RESPONSE_ACTION_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=headers
                )
                
                response.raise_for_status()
                
                data = response.json()
                summary = data.get("message", "Action executed successfully.")
                return True, summary, data
                
        except httpx.TimeoutException:
            # Note: For timeouts, execution is uncertain. Application might have executed it.
            # Next retry will send the same request_id, requiring application-side idempotency.
            logger.error(f"Timeout executing action {action} for {request_id}")
            return False, "Application response timed out.", {}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error executing action {action} for {request_id}: {e.response.status_code}")
            try:
                err_data = e.response.json()
                summary = err_data.get("message", f"HTTP {e.response.status_code}")
            except Exception:
                summary = f"HTTP {e.response.status_code}"
            return False, summary, {}
        except Exception as e:
            logger.error(f"Error executing action {action} for {request_id}: {str(e)}")
            return False, f"Connection error: {str(e)}", {}
