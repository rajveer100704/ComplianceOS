from typing import Generic, TypeVar, Type, List, Any, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic base repository mapping standard async database operations."""

    def __init__(self, session: AsyncSession, model_cls: Type[T]):
        self.session = session
        self.model_cls = model_cls

    async def get(self, id_: Any) -> Optional[T]:
        """Fetches a single entity matching primary key ID."""
        return await self.session.get(self.model_cls, id_)

    async def list(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Lists active entities supporting pagination bounds."""
        stmt = select(self.model_cls)
        # Handle soft deletes check if model contains is_deleted field
        if hasattr(self.model_cls, "is_deleted"):
            stmt = stmt.where(self.model_cls.is_deleted == False)

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, entity: T) -> None:
        """Adds a single record to session context."""
        self.session.add(entity)

    async def delete(self, entity: T) -> None:
        """Soft deletes entity if Mixin is active, otherwise removes from session."""
        if hasattr(entity, "is_deleted"):
            setattr(entity, "is_deleted", True)
            import datetime

            if hasattr(entity, "deleted_at"):
                setattr(
                    entity, "deleted_at", datetime.datetime.now(datetime.timezone.utc)
                )
        else:
            await self.session.delete(entity)

    async def bulk_add(self, entities: List[T]) -> None:
        """Appends multiple records in a single transactional batch."""
        self.session.add_all(entities)
