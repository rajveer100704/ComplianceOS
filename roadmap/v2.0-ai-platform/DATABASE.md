# Database Design — Version 2.0: AI-Native Enterprise SaaS & Knowledge Graph

```sql
CREATE TABLE knowledge_nodes (
    id VARCHAR(36) PRIMARY KEY,
    label VARCHAR(255) NOT NULL,
    properties_json TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE knowledge_edges (
    id VARCHAR(36) PRIMARY KEY,
    source_node_id VARCHAR(36) NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    target_node_id VARCHAR(36) NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL, -- 'supported_by', 'referenced_in', 'verified_by'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```
