#!/usr/bin/env python3
import asyncio
import argparse
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from orchestration.langgraph.real_graph import LangGraphAppBuilder, USE_LANGGRAPH
from orchestration.langgraph.state import WorkflowState


async def main():
	parser = argparse.ArgumentParser(description="Run LangGraph Orchestration App")
	parser.add_argument("prompt", nargs="+", help="User request")
	parser.add_argument("--session", dest="session_id", default="lg_session")
	args = parser.parse_args()

	if not USE_LANGGRAPH:
		print("LangGraph not installed. Install with: pip install langgraph langchain-core pydantic")
		return

	builder = LangGraphAppBuilder()
	app, system = await builder.build()

	initial = WorkflowState(workflow_id=os.urandom(4).hex(), user_request=" ".join(args.prompt), session_id=args.session_id)

	# Execute the graph
	result = await app.ainvoke(initial.__dict__)

	print(json.dumps({
		"workflow_id": result.get("workflow_id"),
		"status": result.get("status"),
		"route": result.get("context", {}).get("route"),
		"tasks": list((result.get("task_results") or {}).keys()),
		"suggestions": result.get("next_steps"),
	}, indent=2))

	await system.stop()


if __name__ == "__main__":
	asyncio.run(main()) 