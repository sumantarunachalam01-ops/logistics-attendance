import logging

logger = logging.getLogger('audit')

def log_audit(user_id: int, action: str, entity_type: str = None, entity_id: int = None, description: str = None):
    """Log audit actions cleanly without requiring a separate table."""
    logger.info(f"[AUDIT] user={user_id} action={action} entity={entity_type}:{entity_id} - {description}")
