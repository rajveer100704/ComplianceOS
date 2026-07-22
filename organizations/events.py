"""Domain event name constants for the organizations module.

Follows the pattern: <domain>.<action>
These strings are stored in the outbox and consumed by the worker dispatcher.
"""


ORG_CREATED = "organization.created"
ORG_DELETED = "organization.deleted"

MEMBER_INVITED = "member.invited"
MEMBER_JOINED = "member.joined"
MEMBER_REMOVED = "member.removed"
ROLE_CHANGED = "membership.role_changed"
