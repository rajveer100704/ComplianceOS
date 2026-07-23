"""Data access repository for Policy storage, versioning, packs, and rollbacks."""

import uuid
import hashlib
import json
from typing import Optional, List, Sequence
from datetime import datetime, UTC
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from policy.models import (
    PolicyModel,
    PolicyVersionModel,
    PolicyRuleModel,
    PolicyVersionStatus,
    SystemPolicyPackModel,
    OrganizationPolicyPackModel,
    PolicyDependencyModel,
)


class PolicyRepository:
    """Repository managing policy CRUD, immutable versioning, rollbacks, and policy packs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_policy(
        self,
        organization_id: str,
        name: str,
        trigger_event: str,
        expression: str,
        compiled_ast: dict,
        description: Optional[str] = None,
        pack_id: Optional[str] = None,
        priority: int = 100,
        user_id: Optional[str] = None,
    ) -> PolicyModel:
        """Creates a new policy with version 1."""
        policy_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())

        checksum = hashlib.sha256(expression.encode("utf-8")).hexdigest()

        version_model = PolicyVersionModel(
            id=version_id,
            policy_id=policy_id,
            version=1,
            expression=expression,
            compiled_expression_json=compiled_ast,
            checksum=checksum,
            status=PolicyVersionStatus.ACTIVE,
            created_by_user_id=user_id,
            created_at=datetime.now(UTC),
        )

        policy_model = PolicyModel(
            id=policy_id,
            organization_id=organization_id,
            pack_id=pack_id,
            name=name,
            description=description,
            trigger_event=trigger_event,
            current_version_id=version_id,
            is_active=True,
            priority=priority,
            created_at=datetime.now(UTC),
        )

        self.session.add(policy_model)
        self.session.add(version_model)
        await self.session.flush()
        return policy_model

    async def create_version(
        self,
        policy_id: str,
        expression: str,
        compiled_ast: dict,
        user_id: Optional[str] = None,
        activate: bool = True,
    ) -> PolicyVersionModel:
        """Creates a new immutable PolicyVersion for an existing Policy."""
        stmt = (
            select(PolicyVersionModel)
            .where(PolicyVersionModel.policy_id == policy_id)
            .order_by(PolicyVersionModel.version.desc())
        )
        res = await self.session.execute(stmt)
        latest = res.scalars().first()
        next_ver = (latest.version + 1) if latest else 1

        version_id = str(uuid.uuid4())
        checksum = hashlib.sha256(expression.encode("utf-8")).hexdigest()

        status = PolicyVersionStatus.ACTIVE if activate else PolicyVersionStatus.DRAFT

        version_model = PolicyVersionModel(
            id=version_id,
            policy_id=policy_id,
            version=next_ver,
            expression=expression,
            compiled_expression_json=compiled_ast,
            checksum=checksum,
            status=status,
            created_by_user_id=user_id,
            created_at=datetime.now(UTC),
        )
        self.session.add(version_model)

        if activate:
            # Update current policy pointer and archive previous active versions
            await self.session.execute(
                update(PolicyVersionModel)
                .where(
                    PolicyVersionModel.policy_id == policy_id,
                    PolicyVersionModel.id != version_id,
                )
                .values(status=PolicyVersionStatus.ARCHIVED)
            )
            await self.session.execute(
                update(PolicyModel)
                .where(PolicyModel.id == policy_id)
                .values(current_version_id=version_id)
            )

        await self.session.flush()
        return version_model

    async def rollback_version(
        self, policy_id: str, target_version_number: int, user_id: Optional[str] = None
    ) -> PolicyVersionModel:
        """Rolls back to a target version number by creating a NEW version with target content (preserving lineage)."""
        stmt = select(PolicyVersionModel).where(
            PolicyVersionModel.policy_id == policy_id,
            PolicyVersionModel.version == target_version_number,
        )
        res = await self.session.execute(stmt)
        target = res.scalars().first()
        if not target:
            raise ValueError(
                f"Version {target_version_number} not found for policy {policy_id}"
            )

        return await self.create_version(
            policy_id=policy_id,
            expression=target.expression,
            compiled_ast=target.compiled_expression_json,
            user_id=user_id,
            activate=True,
        )

    async def get_active_policies_for_event(
        self, organization_id: str, trigger_event: str
    ) -> Sequence[PolicyModel]:
        """Queries all active policies for a given organization and trigger event, ordered by priority."""
        stmt = (
            select(PolicyModel)
            .where(
                PolicyModel.organization_id == organization_id,
                PolicyModel.trigger_event == trigger_event,
                PolicyModel.is_active == True,
            )
            .order_by(PolicyModel.priority.asc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def install_system_pack(
        self, organization_id: str, system_pack_id: str
    ) -> OrganizationPolicyPackModel:
        """Installs a system policy pack into an organization, creating tenant-owned editable policy copies."""
        stmt = select(SystemPolicyPackModel).where(
            SystemPolicyPackModel.id == system_pack_id
        )
        res = await self.session.execute(stmt)
        pack = res.scalars().first()
        if not pack:
            raise ValueError(f"System policy pack {system_pack_id} not found")

        inst_id = str(uuid.uuid4())
        org_pack = OrganizationPolicyPackModel(
            id=inst_id,
            organization_id=organization_id,
            system_pack_id=system_pack_id,
            name=f"{pack.name} (Installed)",
            installed_at=datetime.now(UTC),
        )
        self.session.add(org_pack)
        await self.session.flush()
        return org_pack
