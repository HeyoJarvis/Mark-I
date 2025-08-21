from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import Optional

from .state import WorkflowState
from .nodes import IntelligenceRouterNode, BrandingNode, MarketResearchNode, SuggestionsNode
from ..persistent.persistent_system import PersistentSystem, PersistentSystemConfig


class LangGraphOrchestrator:
	"""Lightweight orchestrator that mimics a LangGraph flow using our runtime.
	This avoids changing existing code while giving us a graph-style entrypoint.
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

	async def run(self, user_request: str, session_id: str = "demo_session") -> WorkflowState:
		system = await self._ensure_system()
		state = WorkflowState(workflow_id=str(uuid.uuid4())[:8], user_request=user_request, session_id=session_id)

		# Router
		route = IntelligenceRouterNode()(state)
		# Execute nodes based on route
		if route == "branding":
			state = await BrandingNode(system).run(state)
		elif route == "market_research":
			state = await MarketResearchNode(system).run(state)
		elif route == "both":
			# Run in parallel
			await asyncio.gather(
				BrandingNode(system).run(state),
				MarketResearchNode(system).run(state),
			)
		else:
			# default to branding
			state = await BrandingNode(system).run(state)

		# Suggestions
		state = await SuggestionsNode().run(state)
		state.set_status("completed")
		return state

	async def shutdown(self) -> None:
		if self._system and self._system.is_running:
			await self._system.stop()
			self._system = None


async def demo():
	orch = LangGraphOrchestrator()
	state = await orch.run("Create a logo for an artisanal bakery and analyze foot traffic trends")
	print(json.dumps({
		"workflow_id": state.workflow_id,
		"status": state.status,
		"tasks": list(state.task_results.keys()),
		"artifacts": {k: v.path for k, v in state.artifacts.items()},
		"suggestions": state.next_steps,
	}, indent=2))
	await orch.shutdown()


if __name__ == "__main__":
	asyncio.run(demo()) 