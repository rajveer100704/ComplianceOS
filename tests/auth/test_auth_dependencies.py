import pytest
import pytest_asyncio
import time
from unittest.mock import MagicMock
from fastapi import HTTPException, Request, status

from config.settings import settings
from auth.enums import Permission, MEMBERSHIP_ROLE_PERMISSIONS_MAP, has_permission
from auth.dependencies import (
    SecurityContext,
    get_token_from_request,
    get_security_context,
    get_current_user,
    get_current_active_user,
    require_permission,
    require_role,
)
from auth.services.jwt_service import JWTService
from auth.repositories.user_repository import UserRepository
from database.models.enums import MembershipRole, UserStatus
from database.models.membership import OrganizationMembership
from database.models.organization import Organization


@pytest_asyncio.fixture
async def sample_users(db_session):
    """Creates a set of users and org memberships for testing dependencies."""
    user_repo = UserRepository(db_session)

    reviewer = await user_repo.create_google_user(
        email="reviewer@complianceos.io",
        provider_user_id="g_rev_123",
        full_name="Standard Reviewer",
    )
    admin = await user_repo.create_google_user(
        email="admin_dep@complianceos.io",
        provider_user_id="g_adm_123",
        full_name="Admin User",
    )
    owner = await user_repo.create_google_user(
        email="owner@complianceos.io",
        provider_user_id="g_own_123",
        full_name="Platform Owner",
    )
    suspended = await user_repo.create_google_user(
        email="suspended@complianceos.io",
        provider_user_id="g_sus_123",
        full_name="Suspended User",
    )
    suspended.status = UserStatus.SUSPENDED.value
    suspended.is_active = False

    org = Organization(name="Test Org", slug="test-org")
    db_session.add(org)
    await db_session.flush()

    mem_rev = OrganizationMembership(organization_id=org.id, user_id=reviewer.id, role=MembershipRole.REVIEWER)
    mem_adm = OrganizationMembership(organization_id=org.id, user_id=admin.id, role=MembershipRole.ADMIN)
    mem_own = OrganizationMembership(organization_id=org.id, user_id=owner.id, role=MembershipRole.OWNER)
    mem_sus = OrganizationMembership(organization_id=org.id, user_id=suspended.id, role=MembershipRole.REVIEWER)

    db_session.add_all([mem_rev, mem_adm, mem_own, mem_sus])
    await db_session.flush()

    return {
        "reviewer": reviewer,
        "admin": admin,
        "owner": owner,
        "suspended": suspended,
        "org": org,
        "mem_rev": mem_rev,
        "mem_adm": mem_adm,
        "mem_own": mem_own,
    }


# --- 1. Permission & Wildcard Tests ---


def test_permission_wildcard_matching():
    """Test has_permission helper for exact matches, domain wildcards, and global * wildcard."""
    reviewer_perms = MEMBERSHIP_ROLE_PERMISSIONS_MAP[MembershipRole.REVIEWER]
    admin_perms = MEMBERSHIP_ROLE_PERMISSIONS_MAP[MembershipRole.ADMIN]
    owner_perms = MEMBERSHIP_ROLE_PERMISSIONS_MAP[MembershipRole.OWNER]

    # Reviewer tests
    assert has_permission(reviewer_perms, Permission.CLAIMS_READ) is True
    assert has_permission(reviewer_perms, Permission.REPORTS_READ) is True
    assert has_permission(reviewer_perms, Permission.SETTINGS_MANAGE) is False

    # Admin domain wildcard tests (Permission.CLAIMS_ALL="claims:*")
    assert has_permission(admin_perms, Permission.CLAIMS_READ) is True
    assert has_permission(admin_perms, Permission.CLAIMS_WRITE) is True
    assert has_permission(admin_perms, Permission.REPORTS_APPROVE) is True

    # Owner global wildcard test (Permission.ALL="*")
    assert has_permission(owner_perms, Permission.CLAIMS_READ) is True
    assert has_permission(owner_perms, Permission.SETTINGS_MANAGE) is True
    assert has_permission(owner_perms, Permission.USERS_MANAGE) is True


# --- 2. Token Extraction Tests ---


def test_get_token_from_request_headers_and_cookies():
    """Test extracting tokens from Authorization header, X-API-Key, or access_token cookie."""
    # Bearer header
    req_bearer = MagicMock(spec=Request)
    req_bearer.cookies = {}
    tok1 = get_token_from_request(req_bearer, bearer_token="Bearer my_jwt_token_123")
    assert tok1 == "my_jwt_token_123"

    # X-API-Key header
    req_apikey = MagicMock(spec=Request)
    req_apikey.cookies = {}
    tok2 = get_token_from_request(
        req_apikey, bearer_token=None, authorization=None, x_api_key="api_key_abc"
    )
    assert tok2 == "api_key_abc"

    # Cookie fallback
    req_cookie = MagicMock(spec=Request)
    req_cookie.cookies = {"access_token": "cookie_token_789"}
    tok3 = get_token_from_request(
        req_cookie, bearer_token=None, authorization=None, x_api_key=None
    )
    assert tok3 == "cookie_token_789"


# --- 3. SecurityContext Translation Layer & User Injector Tests ---


@pytest.mark.asyncio
async def test_get_security_context_valid_token(db_session, sample_users):
    """Test building SecurityContext with valid RS256 token and DB User lookup."""
    reviewer = sample_users["reviewer"]
    jwt_svc = JWTService()
    token = jwt_svc.generate_access_token(
        user_id=reviewer.id,
        email=reviewer.email,
        role="reviewer",
    )

    req = MagicMock(spec=Request)
    req.state.request_id = "req_test_123"
    req.headers = {}
    req.cookies = {}

    ctx = await get_security_context(request=req, token=token, db=db_session)

    assert isinstance(ctx, SecurityContext)
    assert ctx.user.id == reviewer.id
    assert ctx.user.email == reviewer.email
    assert Permission.CLAIMS_READ in ctx.permissions
    assert ctx.request_id == "req_test_123"

    # Verify get_current_user & get_current_active_user injectors
    usr1 = await get_current_user(context=ctx)
    usr2 = await get_current_active_user(context=ctx)
    assert usr1 == reviewer
    assert usr2 == reviewer


@pytest.mark.asyncio
async def test_get_security_context_missing_token_production_raises_401(
    db_session, monkeypatch
):
    """Test missing token in production mode raises 401 UNAUTHORIZED."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    req = MagicMock(spec=Request)

    with pytest.raises(HTTPException) as exc_info:
        await get_security_context(request=req, token=None, db=db_session)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "credentials were not provided" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_security_context_expired_token_raises_401(db_session, sample_users):
    """Test expired JWT token raises 401 UNAUTHORIZED."""
    reviewer = sample_users["reviewer"]
    jwt_svc = JWTService()
    token = jwt_svc.generate_access_token(
        user_id=reviewer.id,
        email=reviewer.email,
        role="reviewer",
        extra_claims={"exp": int(time.time()) - 60},
    )

    req = MagicMock(spec=Request)
    with pytest.raises(HTTPException) as exc_info:
        await get_security_context(request=req, token=token, db=db_session)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "token has expired" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_security_context_suspended_user_raises_403(db_session, sample_users):
    """Test authenticated suspended user raises 403 FORBIDDEN."""
    suspended = sample_users["suspended"]
    jwt_svc = JWTService()
    token = jwt_svc.generate_access_token(
        user_id=suspended.id,
        email=suspended.email,
        role="reviewer",
    )

    req = MagicMock(spec=Request)
    with pytest.raises(HTTPException) as exc_info:
        await get_security_context(request=req, token=token, db=db_session)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "suspended" in exc_info.value.detail.lower()


# --- 4. Permission Guards & Role Guards Tests ---


@pytest.mark.asyncio
async def test_require_permission_guard_success_and_denied(sample_users):
    """Test require_permission dependency guard passes allowed permission and rejects missing permission."""
    reviewer_ctx = SecurityContext(
        user=sample_users["reviewer"],
        permissions=MEMBERSHIP_ROLE_PERMISSIONS_MAP[MembershipRole.REVIEWER],
    )

    # 1. Success check
    checker = require_permission(Permission.CLAIMS_READ)
    res_ctx = await checker(context=reviewer_ctx)
    assert res_ctx == reviewer_ctx

    # 2. Denied check (Reviewer lacks SETTINGS_MANAGE)
    checker_denied = require_permission(Permission.SETTINGS_MANAGE)
    with pytest.raises(HTTPException) as exc_info:
        await checker_denied(context=reviewer_ctx)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "settings:manage" in exc_info.value.detail


@pytest.mark.asyncio
async def test_require_permission_multiple_permissions(sample_users):
    """Test requiring multiple permissions simultaneously."""
    admin_ctx = SecurityContext(
        user=sample_users["admin"],
        permissions=MEMBERSHIP_ROLE_PERMISSIONS_MAP[MembershipRole.ADMIN],
    )

    checker = require_permission(Permission.CLAIMS_READ, Permission.REPORTS_APPROVE)
    res = await checker(context=admin_ctx)
    assert res == admin_ctx


@pytest.mark.asyncio
async def test_require_role_guard_success_denied_and_owner(sample_users):
    """Test require_role dependency guard enforcing membership roles and allowing Owner implicitly."""
    reviewer_ctx = SecurityContext(user=sample_users["reviewer"], membership=sample_users["mem_rev"])
    admin_ctx = SecurityContext(user=sample_users["admin"], membership=sample_users["mem_adm"])
    owner_ctx = SecurityContext(user=sample_users["owner"], membership=sample_users["mem_own"])

    admin_checker = require_role(MembershipRole.ADMIN)

    # Admin passes
    res_admin = await admin_checker(context=admin_ctx)
    assert res_admin == admin_ctx

    # Owner passes (Owner always allowed)
    res_owner = await admin_checker(context=owner_ctx)
    assert res_owner == owner_ctx

    # Reviewer fails
    with pytest.raises(HTTPException) as exc_info:
        await admin_checker(context=reviewer_ctx)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "requires one of the following roles" in exc_info.value.detail
