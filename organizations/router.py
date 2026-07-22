from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_db_session, get_security_context
from auth.schemas import SecurityContext
from organizations.service import OrganizationService
from organizations.schemas import (
    CreateOrganizationRequest,
    OrganizationResponse,
    OrganizationWithMembershipResponse,
    MembershipResponse,
    InviteMemberRequest,
    InvitationResponse,
    MemberResponse,
    MemberListResponse,
)

router = APIRouter()


# ──────────────────────────────────────────────────────────────
# POST /api/v1/organizations — Create organization
# ──────────────────────────────────────────────────────────────


@router.post(
    "",
    summary="Create a new organization workspace",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    body: CreateOrganizationRequest,
    context: SecurityContext = Depends(get_security_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Creates a new organization and assigns the authenticated user as OWNER."""
    svc = OrganizationService(db)
    org, membership = await svc.create_organization(
        name=body.name,
        slug=body.slug,
        plan=body.plan,
        creator=context.user,
    )
    await db.commit()

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        plan=org.plan if isinstance(org.plan, str) else org.plan.value,
        is_active=org.is_active,
        created_at=org.created_at.isoformat(),
    )


# ──────────────────────────────────────────────────────────────
# GET /api/v1/organizations/me — List my organizations
# ──────────────────────────────────────────────────────────────


@router.get(
    "/me",
    summary="List organizations for the authenticated user",
    response_model=list[OrganizationWithMembershipResponse],
)
async def list_my_organizations(
    context: SecurityContext = Depends(get_security_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Returns all organizations the authenticated user belongs to, with their role in each."""
    svc = OrganizationService(db)
    user_orgs = await svc.list_user_organizations(context.user.id)

    result = []
    for item in user_orgs:
        org = item["organization"]
        mem = item["membership"]
        result.append(
            OrganizationWithMembershipResponse(
                organization=OrganizationResponse(
                    id=org.id,
                    name=org.name,
                    slug=org.slug,
                    plan=org.plan if isinstance(org.plan, str) else org.plan.value,
                    is_active=org.is_active,
                    created_at=org.created_at.isoformat(),
                ),
                membership=MembershipResponse(
                    membership_id=mem.id,
                    role=(
                        mem.role.value if hasattr(mem.role, "value") else str(mem.role)
                    ),
                    joined_at=mem.joined_at.isoformat() if mem.joined_at else None,
                ),
            )
        )
    return result


# ──────────────────────────────────────────────────────────────
# POST /api/v1/organizations/{org_id}/invitations — Invite member
# ──────────────────────────────────────────────────────────────


@router.post(
    "/{org_id}/invitations",
    summary="Invite a new team member to the organization",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_member(
    org_id: str,
    body: InviteMemberRequest,
    context: SecurityContext = Depends(get_security_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Creates an invitation for a new member. Only Owners and Admins may invite."""
    svc = OrganizationService(db)
    invitation, debug_token = await svc.invite_member(
        org_id=org_id,
        email=body.email,
        role=body.role,
        security_context=context,
    )
    await db.commit()

    return InvitationResponse(
        invitation_id=invitation.id,
        organization_id=invitation.organization_id,
        email=invitation.email,
        role=(
            invitation.role.value
            if hasattr(invitation.role, "value")
            else str(invitation.role)
        ),
        expires_at=invitation.expires_at.isoformat(),
        status=(
            invitation.status.value
            if hasattr(invitation.status, "value")
            else str(invitation.status)
        ),
        debug_token=debug_token,
    )


# ──────────────────────────────────────────────────────────────
# GET /api/v1/organizations/{org_id}/members — List members
# ──────────────────────────────────────────────────────────────


@router.get(
    "/{org_id}/members",
    summary="List all members of an organization",
    response_model=MemberListResponse,
)
async def list_members(
    org_id: str,
    context: SecurityContext = Depends(get_security_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Lists all active members of an organization. Requires membership in that organization."""
    svc = OrganizationService(db)
    memberships = await svc.list_members(
        org_id=org_id,
        security_context=context,
    )

    return MemberListResponse(
        organization_id=org_id,
        members=[
            MemberResponse(
                membership_id=m.id,
                user_id=m.user_id,
                role=m.role.value if hasattr(m.role, "value") else str(m.role),
                joined_at=m.joined_at.isoformat() if m.joined_at else None,
                invited_by=m.invited_by,
            )
            for m in memberships
        ],
        total=len(memberships),
    )
