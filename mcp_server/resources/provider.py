"""Exposed MCP read-only resource providers wired to live GovernanceManager."""

import json
import logging
from typing import Dict, List
from mcp_server.schemas import MCPResource
from governance import GovernanceManager

logger = logging.getLogger("mcp_server.resources.provider")


class MCPResourcesProvider:
    """Provider exposing ComplianceOS system resources to MCP clients."""

    def __init__(self):
        self._resources: Dict[str, MCPResource] = {}
        self.gov_manager = GovernanceManager()
        self._register_default_resources()

    def _register_default_resources(self):
        self._resources["resource://compliance/rules"] = MCPResource(
            uri="resource://compliance/rules",
            name="Compliance Rules Registry",
            description="Active regulatory sign-off rules and threshold configurations.",
            mimeType="application/json",
        )
        self._resources["resource://audit/ledger"] = MCPResource(
            uri="resource://audit/ledger",
            name="Cryptographic Audit Ledger",
            description="Immutable SHA-256 block-chained compliance audit log.",
            mimeType="application/json",
        )

    def list_resources(self) -> List[MCPResource]:
        return list(self._resources.values())

    async def read_resource(self, uri: str, organization_id: str = "default") -> str:
        if uri not in self._resources:
            raise KeyError(f"Resource URI '{uri}' is not registered")

        logger.info(f"Reading MCP resource '{uri}' org='{organization_id}'")

        if uri == "resource://compliance/rules":
            return json.dumps(
                [
                    {
                        "rule_id": "rule-grounding",
                        "metric": "grounding_score",
                        "threshold": 0.85,
                        "is_blocking": True,
                    }
                ]
            )

        elif uri == "resource://audit/ledger":
            entries = await self.gov_manager.get_audit_trail(
                organization_id=organization_id
            )
            if not entries:
                return json.dumps(
                    [
                        {
                            "sequence_number": 1,
                            "prev_hash": "0" * 64,
                            "event_type": "INITIAL_LEDGER_BLOCK",
                            "organization_id": organization_id,
                        }
                    ]
                )
            return json.dumps([e.model_dump() for e in entries], default=str)

        return json.dumps({"status": "empty"})
