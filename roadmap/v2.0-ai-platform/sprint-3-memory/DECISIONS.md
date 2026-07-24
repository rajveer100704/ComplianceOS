# Shared Memory Engine — Key Design Decisions Log

## Summary of Decisions

1. **Memory as Infrastructure**: Memory is treated as core infrastructure, managed via `MemoryManager`, not as an autonomous agent.
2. **Context Builder Abstraction**: Agents never query individual storage tiers directly; they call `MemoryManager.build_context()`.
3. **Stateless Agents**: Agents remain stateless orchestrators consuming token-budgeted `MemoryContext` objects.
