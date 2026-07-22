from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from database.models.enums import MembershipRole, OrganizationPlan, InvitationStatus


class CreateOrganizationRequest(BaseModel):
    """Request body for POST /api/v1/organizations."""

    name: str = Field(..., min_length=2, max_length=255, description="Display name of the organization")
    slug: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=80,
        pattern=r"^[a-z0-9-]+$",
        description="URL-safe unique slug (auto-generated from name if omitted)",
    )
    plan: OrganizationPlan = Field(default=OrganizationPlan.FREE)


class OrganizationResponse(BaseModel):
    """Organization resource response DTO."""

    id: str
    name: str
    slug: str
    plan: str
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class MembershipResponse(BaseModel):
    """Caller's membership within an organization."""

    membership_id: str
    role: str
    joined_at: Optional[str] = None


class OrganizationWithMembershipResponse(BaseModel):
    """Organization + caller's membership role (used in /me response)."""

    organization: OrganizationResponse
    membership: MembershipResponse


class InviteMemberRequest(BaseModel):
    """Request body for POST /api/v1/organizations/{org_id}/invitations."""

    email: str = Field(..., description="Email address of the invitee")
    role: MembershipRole = Field(
        default=MembershipRole.REVIEWER,
        description="Role to assign when the invitation is accepted",
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class InvitationResponse(BaseModel):
    """Response DTO for a created invitation."""

    invitation_id: str
    organization_id: str
    email: str
    role: str
    expires_at: str
    status: str
    debug_token: Optional[str] = Field(
        default=None,
        description="Raw invitation token — only present in development mode.",
    )


class MemberResponse(BaseModel):
    """A single organization member DTO."""

    membership_id: str
    user_id: str
    role: str
    joined_at: Optional[str] = None
    invited_by: Optional[str] = None


class MemberListResponse(BaseModel):
    """Response DTO for GET /api/v1/organizations/{org_id}/members."""

    organization_id: str
    members: List[MemberResponse]
    total: int
