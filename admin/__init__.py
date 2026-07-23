"""Admin package re-exporting REST routers."""

from admin.policies import router as admin_policies_router
from admin.audit import router as admin_audit_router
from admin.workers import router as admin_workers_router

__all__ = ["admin_policies_router", "admin_audit_router", "admin_workers_router"]
