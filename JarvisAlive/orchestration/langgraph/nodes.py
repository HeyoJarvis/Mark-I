from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Optional
from datetime import datetime

from ..persistent.persistent_system import PersistentSystem, PersistentSystemConfig
from .state import WorkflowState, ArtifactRef


class IntelligenceRouterNode:
	"""Routes a request to branding, market_research, or both using simple heuristics.
	Keeps it self-contained; we can later swap to WorkflowBrain for richer routing.
	"""

	def __init__(self, default_route: str = "auto"):
		self.default_route = default_route

	def __call__(self, state: WorkflowState) -> str:
		text = state.user_request.lower()
		branding = any(k in text for k in ["logo", "brand", "identity", "name"])
		research = any(k in text for k in ["market", "competition", "research", "analysis"])
		if branding and research:
			return "both"
		if branding:
			return "branding"
		if research:
			return "market_research"
		return "branding" if self.default_route == "branding" else "market_research"


class BrandingNode:
	def __init__(self, system: PersistentSystem):
		self.system = system

	async def run(self, state: WorkflowState) -> WorkflowState:
		# Build task per PersistentSystem.submit_task signature
		task = {
			"task_type": "branding",
			"input_data": {
				"business_idea": state.user_request,
				"industry": state.context.get("industry", ""),
				"session_id": state.session_id
			},
		}
		ids = await self.system.submit_task(
			task=task,
			user_id=state.session_id or "langgraph_user",
			session_id=state.session_id or "langgraph_session",
			workflow_id=state.workflow_id,
			requires_approval=not getattr(self.system.config, "skip_approvals", True)
		)
		task_id = ids.get("task_id")
		result = await self.system.await_task_result(task_id, timeout_seconds=120)
		state.task_results["branding"] = result or {}
		# Optional artifact link
		if result and isinstance(result, dict) and result.get("report_path"):
			state.artifacts["branding_report"] = ArtifactRef(
				name="branding_report.json",
				path=result["report_path"],
				metadata={"created_at": datetime.utcnow().isoformat()},
			)
		return state


class MarketResearchNode:
	def __init__(self, system: PersistentSystem):
		self.system = system

	async def run(self, state: WorkflowState) -> WorkflowState:
		# Build task per PersistentSystem.submit_task signature
		task = {
			"task_type": "market_research",
			"input_data": {
				"business_idea": state.user_request,
				"industry": state.context.get("industry", ""),
				"location": state.context.get("location", "Global"),
				"session_id": state.session_id
			},
		}
		ids = await self.system.submit_task(
			task=task,
			user_id=state.session_id or "langgraph_user",
			session_id=state.session_id or "langgraph_session",
			workflow_id=state.workflow_id,
			requires_approval=not getattr(self.system.config, "skip_approvals", True)
		)
		task_id = ids.get("task_id")
		result = await self.system.await_task_result(task_id, timeout_seconds=180)
		state.task_results["market_research"] = result or {}
		if result and isinstance(result, dict) and result.get("report_path"):
			state.artifacts["market_research_report"] = ArtifactRef(
				name="market_research.json",
				path=result["report_path"],
				metadata={"created_at": datetime.utcnow().isoformat()},
			)
		return state


class SuggestionsNode:
	def __init__(self, workflow_brain: Optional[Any] = None):
		self.workflow_brain = workflow_brain  # reserved for richer future use

	async def run(self, state: WorkflowState) -> WorkflowState:
		# Simple rule-based suggestions for now
		suggestions = []
		if "market_research" in state.task_results and "branding" not in state.task_results:
			suggestions.append({
				"title": "Brand Identity Creation",
				"suggested_prompt": "Create a brand identity and logo based on the research",
				"workflow_type": "branding",
			})
		if "branding" in state.task_results and "market_research" not in state.task_results:
			suggestions.append({
				"title": "Market Research",
				"suggested_prompt": "Analyze the target market and competitors",
				"workflow_type": "market_research",
			})
		state.next_steps = suggestions
		return state 