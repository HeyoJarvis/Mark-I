#!/usr/bin/env python3
import asyncio
import argparse

from orchestration.langgraph.graph_runner import LangGraphOrchestrator


async def main():
	parser = argparse.ArgumentParser(description="Demo: LangGraph-style Orchestrator")
	parser.add_argument("prompt", nargs="+", help="User request")
	parser.add_argument("--session", dest="session_id", default="demo_session")
	args = parser.parse_args()

	orch = LangGraphOrchestrator()
	state = await orch.run(" ".join(args.prompt), session_id=args.session_id)

	print("Status:", state.status)
	print("Tasks:", list(state.task_results.keys()))
	if state.next_steps:
		print("Suggestions:")
		for s in state.next_steps:
			print("-", s.get("title"), "=>", s.get("suggested_prompt"))

	await orch.shutdown()


if __name__ == "__main__":
	asyncio.run(main()) 