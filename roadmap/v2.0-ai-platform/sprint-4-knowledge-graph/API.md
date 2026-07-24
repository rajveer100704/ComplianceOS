# Regulatory Knowledge Graph Engine — API & Contract Specifications

## `KnowledgeGraphManager` Public Interface

```python
async def add_node(node: GraphNode) -> str:
    """Adds a new node or resolves an existing canonical node."""
    ...

async def add_edge(edge: GraphEdge) -> str:
    """Adds a directed relationship edge between source and target nodes."""
    ...

async def get_node(node_id: str) -> Optional[GraphNode]:
    """Retrieves a single graph node by ID."""
    ...

async def find_paths(
    source_node_id: str,
    target_node_id: Optional[str] = None,
    target_node_types: Optional[List[NodeType]] = None,
    max_depth: int = 4,
    organization_id: str = "default",
) -> List[GraphPath]:
    """Executes multi-hop path traversal up to max_depth."""
    ...

async def get_neighborhood(
    node_id: str,
    depth: int = 1,
    organization_id: str = "default",
) -> SubGraph:
    """Extracts a sub-graph neighborhood surrounding target node."""
    ...

async def query_impact(
    regulation_node_id: str,
    organization_id: str = "default",
) -> ImpactAnalysisResult:
    """Calculates all claims, requirements, decisions, and reports impacted by a regulation revision."""
    ...
```
