"""Admin REST API router for Policy CRUD, Versioning, System Packs, Rollbacks, and Simulation."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import SecurityContext, require_permission, get_db_session
from auth.enums import Permission
from policy.repository import PolicyRepository
from policy.schemas import (
    PolicyCreate,
    PolicyResponse,
    PolicySimulationRequest,
    PolicySimulationResponse,
)
from policy_engine.compiler import PolicyCompiler
from policy_engine.validator import PolicyValidator, PolicyValidationError
from policy_engine.simulator import PolicySimulator

router = APIRouter(prefix="/admin/policies", tags=["Admin Policy Governance"])


@router.post(
    "",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.ORGANIZATIONS_WRITE))],
)
async def create_policy_api(
    org_id: str,
    payload: PolicyCreate,
    ctx: SecurityContext = Depends(require_permission(Permission.ORGANIZATIONS_WRITE)),
    db: AsyncSession = Depends(get_db_session),
):
    """Creates a new Policy with initial compiled version 1."""
    compiler = PolicyCompiler()
    validator = PolicyValidator()

    ast = compiler.compile(payload.expression)
    try:
        validator.validate(ast)
    except PolicyValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    repo = PolicyRepository(db)
    policy = await repo.create_policy(
        organization_id=org_id,
        name=payload.name,
        trigger_event=payload.trigger_event,
        expression=payload.expression,
        compiled_ast=ast,
        description=payload.description,
        priority=payload.priority,
        user_id=ctx.user.id if ctx.user else None,
    )
    await db.commit()
    return policy


@router.post(
    "/simulate",
    response_model=PolicySimulationResponse,
    dependencies=[Depends(require_permission(Permission.ORGANIZATIONS_WRITE))],
)
async def simulate_policy_api(
    org_id: str,
    payload: PolicySimulationRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Executes a dry-run simulation of an expression against historical/sample claim context sets."""
    simulator = PolicySimulator()
    sample_claims = [
        {"id": "clm-1", "risk_score": 90, "status": "UNSUPPORTED", "confidence": 0.3},
        {"id": "clm-2", "risk_score": 30, "status": "SUPPORTED", "confidence": 0.95},
        {"id": "clm-3", "risk_score": 75, "status": "UNSUPPORTED", "confidence": 0.6},
    ]
    return simulator.simulate_expression(payload.expression, sample_claims, org_id)


@router.post(
    "/{policy_id}/rollback/{target_version}",
    dependencies=[Depends(require_permission(Permission.ORGANIZATIONS_WRITE))],
)
async def rollback_policy_version_api(
    org_id: str,
    policy_id: str,
    target_version: int,
    ctx: SecurityContext = Depends(require_permission(Permission.ORGANIZATIONS_WRITE)),
    db: AsyncSession = Depends(get_db_session),
):
    """Rolls back policy to a target version number by creating a NEW copy version (preserving 100% lineage)."""
    repo = PolicyRepository(db)
    try:
        ver = await repo.rollback_version(
            policy_id=policy_id,
            target_version_number=target_version,
            user_id=ctx.user.id if ctx.user else None,
        )
        await db.commit()
        return {"status": "rolled_back", "new_version_number": ver.version}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
