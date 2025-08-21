from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional

try:
	from langgraph.graph import StateGraph, START, END
	USE_LANGGRAPH = True
except Exception:
	# LangGraph is optional; this module will no-op if missing
	USE_LANGGRAPH = False

from .state import WorkflowState, ArtifactRef
from .nodes import IntelligenceRouterNode, BrandingNode, MarketResearchNode, SuggestionsNode
from ..persistent.persistent_system import PersistentSystem, PersistentSystemConfig


async def _branding_node(state: Dict[str, Any], system: PersistentSystem) -> Dict[str, Any]:
	wf = WorkflowState(**state)
	wf = await BrandingNode(system).run(wf)
	return wf.__dict__


async def _market_node(state: Dict[str, Any], system: PersistentSystem) -> Dict[str, Any]:
	wf = WorkflowState(**state)
	wf = await MarketResearchNode(system).run(wf)
	return wf.__dict__


async def _router_node(state: Dict[str, Any]) -> Dict[str, Any]:
	wf = WorkflowState(**state)
	route = IntelligenceRouterNode()(wf)
	wf.context["route"] = route
	return wf.__dict__


def _route_condition(state: Dict[str, Any]) -> str:
	return state.get("context", {}).get("route", "branding")


async def _suggestions_node(state: Dict[str, Any]) -> Dict[str, Any]:
	wf = WorkflowState(**state)
	wf = await SuggestionsNode().run(wf)
	return wf.__dict__


class LangGraphAppBuilder:
	"""Builds a LangGraph app wired to the existing PersistentSystem.
	If LangGraph is not available, raises RuntimeError.
	"""

	def __init__(self, redis_url: Optional[str] = None, skip_approvals: bool = True):
		self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
		self.skip_approvals = skip_approvals
		self._system: Optional[PersistentSystem] = None

	async def _ensure_system(self) -> PersistentSystem:
		if self._system:
			return self._system
		config = PersistentSystemConfig(redis_url=self.redis_url, skip_approvals=self.skip_approvals)
		self._system = PersistentSystem(config)
		await self._system.start()
		return self._system

	async def build(self):
		if not USE_LANGGRAPH:
			raise RuntimeError("LangGraph is not installed. Install 'langgraph' to use this pipeline.")
		system = await self._ensure_system()

		graph = StateGraph(dict)

		# Async wrappers that close over system
		async def branding_fn(state: Dict[str, Any]) -> Dict[str, Any]:
			return await _branding_node(state, system)
		async def market_fn(state: Dict[str, Any]) -> Dict[str, Any]:
			return await _market_node(state, system)

		# Register nodes with async callables directly
		graph.add_node("router", _router_node)
		graph.add_node("branding", branding_fn)
		graph.add_node("market_research", market_fn)
		graph.add_node("suggestions", _suggestions_node)

		# Edges
		graph.add_edge(START, "router")
		graph.add_conditional_edges(
			"router",
			_route_condition,
			{
				"branding": "branding",
				"market_research": "market_research",
				"both": "branding",  # run branding first, then decide chain
			},
		)
		# From branding, conditionally chain to market_research only when route == both
		graph.add_conditional_edges(
			"branding",
			lambda s: "to_mr" if _route_condition(s) == "both" else "to_sugg",
			{
				"to_mr": "market_research",
				"to_sugg": "suggestions",
			},
		)
		# After market research, go to suggestions, then END
		graph.add_edge("market_research", "suggestions")
		graph.add_edge("suggestions", END)

		app = graph.compile()
		return app, system 