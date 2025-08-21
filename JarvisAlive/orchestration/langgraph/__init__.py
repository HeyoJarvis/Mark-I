"""LangGraph-based orchestration scaffold (kept separate from existing runtime).

This package contains:
- state: workflow state models for the graph
- nodes: graph node implementations (router, agents, HITL, suggestions)
- graph_runner: graph assembly and execution entrypoints
- checkpointer: Redis-backed checkpointing helpers

NOTE: This module is additive and does not modify the existing orchestration.
""" 