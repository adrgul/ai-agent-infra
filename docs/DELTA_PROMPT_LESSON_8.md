Context
You are working inside an existing educational AI chat agent project implemented with LangGraph (Python).
The agent already covers:
– basic LangGraph nodes and edges
– simple tool usage
– sequential workflows
– memory basics

Your task is to extend the existing project with missing advanced concepts from a lecture on Complex Agents, Plan-and-Execute patterns, and Parallel Node Execution, without breaking existing functionality.

Goal

Extend the current LangGraph-based educational agent by adding advanced orchestration capabilities, focusing on:

Plan-and-Execute agent pattern

Parallel node execution (fan-out / fan-in)

Dynamic routing to multiple tools

Aggregation of parallel results

Robust state management and reducers

Enterprise-grade workflow patterns

This extension should be implemented as a delta, not a rewrite.

Architectural Requirements

Follow SOLID principles strictly

Keep LangGraph as the orchestration framework

Introduce new modules / folders instead of modifying existing logic directly

Each responsibility must be clearly separated

All new components must be educational and readable

Add clear inline comments explaining WHY, not just WHAT

Key Features to Implement (Delta Only)
1. Plan-and-Execute Workflow

Add a new planner–executor architecture:

A planner_node that:

Uses the LLM to generate a structured execution plan

Outputs a list of steps in JSON (no free text)

An executor_loop that:

Iterates over planned steps

Routes each step to the correct node or tool

Updates state after each execution

Supports retries and failure handling

The plan must be explicit, inspectable, and logged.

2. Parallel Node Execution (Fan-out / Fan-in)

Introduce true parallel execution patterns in LangGraph:

Enable one node to trigger multiple independent nodes simultaneously

Examples:

Multiple API calls in parallel

Parallel document processing

Parallel data enrichment steps

Implement:

A fan-out node that spawns parallel tasks

Independent execution nodes that operate on isolated state slices

A fan-in / aggregator node that:

Waits for all parallel executions

Merges results deterministically using reducers

Avoid shared mutable state.

3. Aggregation & Reducers

Add reducer logic that:

Merges results from parallel nodes safely

Supports:

lists

maps

typed partial states

Demonstrates LangGraph reducer patterns

Reducers must be isolated and reusable.

4. Dynamic Routing Node

Add a routing layer that:

Decides at runtime which nodes/tools should be executed

Can return:

a single next node

multiple nodes for parallel execution

Uses structured LLM output (no heuristics)

Routing decisions must be explainable and logged.

5. Educational Parallel Example

Add at least one complete example workflow, such as:

User asks for:

weather

exchange rates

related news

Workflow:

Planner creates tasks

Router selects multiple tools

Tools run in parallel

Aggregator merges results

Final response is synthesized

This example should be clearly isolated as a teaching demo.

Project Structure Guidelines

Introduce new folders like:

/advanced_agents/
  /planning/
  /parallel/
  /routing/
  /aggregation/
  /examples/


Do NOT mix this logic with existing beginner examples.

Code Quality Expectations

Use TypedDict or Pydantic models for state

Avoid large monolithic nodes

Prefer composition over inheritance

Each node should do exactly one thing

Add comments explaining:

why parallelism is used

why aggregation is needed

where LangGraph synchronization happens

Non-Goals (Do NOT Do)

Do NOT rewrite existing agent logic

Do NOT introduce external orchestration frameworks

Do NOT hardcode routing logic

Do NOT rely on implicit state mutation

Outcome

After implementation, the educational agent must clearly demonstrate:

How complex AI agents are architected

How Plan-and-Execute works in practice

How LangGraph handles parallel execution

How real-world AI workflows scale beyond simple chains

Implement the above as a clean, well-structured delta, suitable for teaching advanced AI agent architecture. Update the specification.md and the related markdown files!