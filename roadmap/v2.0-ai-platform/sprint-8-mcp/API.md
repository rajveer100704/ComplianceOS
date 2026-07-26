# Model Context Protocol (MCP) Ecosystem — API Specification

## `MCPServer` Interface Methods

```python
async def handle_jsonrpc(request: Dict[str, Any]) -> Dict[str, Any]:
    ...

async def list_tools() -> List[MCPTool]:
    ...

async def call_tool(name: str, arguments: Dict[str, Any], organization_id: str = "default") -> Dict[str, Any]:
    ...

async def list_resources() -> List[MCPResource]:
    ...

async def read_resource(uri: str, organization_id: str = "default") -> str:
    ...

async def list_prompts() -> List[MCPPrompt]:
    ...

async def get_prompt(name: str, arguments: Dict[str, Any]) -> str:
    ...
```
