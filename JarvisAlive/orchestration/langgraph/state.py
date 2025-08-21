from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class ArtifactRef:
	"""Reference to a generated artifact (e.g., file path or URL)."""
	name: str
	path: str
	metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowState:
	"""Minimal state shared across graph nodes.
	This is intentionally simple to avoid new dependencies.
	"""
	workflow_id: str
	user_request: str
	session_id: str = ""
	status: str = "pending"
	errors: List[str] = field(default_factory=list)
	artifacts: Dict[str, ArtifactRef] = field(default_factory=dict)
	task_results: Dict[str, Any] = field(default_factory=dict)
	next_steps: List[Dict[str, Any]] = field(default_factory=list)
	context: Dict[str, Any] = field(default_factory=dict)
	created_at: datetime = field(default_factory=datetime.utcnow)
	updated_at: datetime = field(default_factory=datetime.utcnow)

	def add_error(self, message: str) -> None:
		self.errors.append(message)
		self.status = "error"
		self.updated_at = datetime.utcnow()

	def set_status(self, status: str) -> None:
		self.status = status
		self.updated_at = datetime.utcnow() 