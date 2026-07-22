from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.user import User
from database.models.oauth_account import OAuthAccount
from database.models.enums import UserStatus


class UserRepository:
    """Domain repository for user persistence operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Fetch user by ID with loaded OAuth accounts."""
        stmt = (
            select(User)
            .options(selectinload(User.oauth_accounts))
            .where(User.id == user_id, User.is_deleted.is_(False))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> Optional[User]:
        """Fetch user by normalized email address."""
        stmt = (
            select(User)
            .options(selectinload(User.oauth_accounts))
            .where(User.email == email.lower().strip(), User.is_deleted.is_(False))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_provider(
        self, provider: str, provider_user_id: str
    ) -> Optional[User]:
        """Fetch user by OAuth provider and provider user ID."""
        stmt = (
            select(User)
            .join(OAuthAccount, User.id == OAuthAccount.user_id)
            .options(selectinload(User.oauth_accounts))
            .where(
                OAuthAccount.provider == provider.lower(),
                OAuthAccount.provider_user_id == provider_user_id,
                User.is_deleted.is_(False),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_google_user(
        self,
        email: str,
        full_name: str,
        provider_user_id: str,
        avatar_url: Optional[str] = None,
        provider_metadata: Optional[str] = None,
    ) -> User:
        """Create a new user and link Google OAuth account in a single transaction.

        Note: role is no longer set on User. Assign a role via OrganizationMembership.
        """
        user = User(
            email=email.lower().strip(),
            email_verified=True,
            full_name=full_name,
            avatar_url=avatar_url,
            status=UserStatus.ACTIVE.value,
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()

        oauth_acc = OAuthAccount(
            user_id=user.id,
            provider="google",
            provider_user_id=provider_user_id,
            provider_email=email.lower().strip(),
            provider_picture=avatar_url,
            provider_metadata=provider_metadata,
        )
        self.session.add(oauth_acc)
        await self.session.flush()
        return user

    async def link_oauth_account(
        self,
        user_id: str,
        provider: str,
        provider_user_id: str,
        provider_email: Optional[str] = None,
        provider_picture: Optional[str] = None,
        provider_username: Optional[str] = None,
        provider_metadata: Optional[str] = None,
    ) -> OAuthAccount:
        """Link an additional OAuth provider to an existing user."""
        oauth_acc = OAuthAccount(
            user_id=user_id,
            provider=provider.lower(),
            provider_user_id=provider_user_id,
            provider_email=provider_email.lower().strip() if provider_email else None,
            provider_picture=provider_picture,
            provider_username=provider_username,
            provider_metadata=provider_metadata,
        )
        self.session.add(oauth_acc)
        await self.session.flush()
        return oauth_acc

    async def record_login(self, user_id: str) -> None:
        """Update last login timestamp and increment login count."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                last_login_at=now,
                login_count=User.login_count + 1,
                updated_at=now,
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def deactivate(self, user_id: str) -> Optional[User]:
        """Deactivate user account."""
        user = await self.find_by_id(user_id)
        if user:
            user.is_active = False
            user.status = UserStatus.INACTIVE
            user.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
        return user

    async def activate(self, user_id: str) -> Optional[User]:
        """Activate user account."""
        user = await self.find_by_id(user_id)
        if user:
            user.is_active = True
            user.status = UserStatus.ACTIVE
            user.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
        return user
