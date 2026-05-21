from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AuditLog


async def log_action(
    db: AsyncSession,
    action: str,
    user_id: int = None,
    entity_type: str = None,
    entity_id: str = None,
    description: str = None,
    ip_address: str = None,
    extra_data: dict = None,
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
        extra_data=extra_data,
    )
    db.add(log)
    # No commit here — commit happens at request end via get_db()
