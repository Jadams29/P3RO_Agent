from typing import Dict, Literal

from langgraph.graph import StateGraph, END

from state import AgentState
from tools import P3RO_Agent_Tools


class P3RO_Graph:
    """Constructs and compiles the LangGraph for the P³RO agent."""

    def __init__(self):
        self.workflow = StateGraph(AgentState)
        self.tools = P3RO_Agent_Tools()
        self._build_graph()

    def _build_graph(self):
        """Defines all nodes and edges for the agent's control flow."""
        # Add nodes
        self.workflow.add_node("decompose_goal", self.tools.decompose_goal)
        self.workflow.add_node("formulate_strategy", self.tools.formulate_strategy)
        self.workflow.add_node("generate_prompt", self.tools.generate_prompt)
        self.workflow.add_node("evaluate_prompt", self.tools.evaluate_prompt)
        self.workflow.add_node("synthesize_reflection", self.tools.synthesize_reflection)
        self.workflow.add_node("decide_next_step", self._decide_next_step)

        # Define edges
        self.workflow.set_entry_point("decompose_goal")
        self.workflow.add_edge("decompose_goal", "formulate_strategy")
        self.workflow.add_edge("formulate_strategy", "generate_prompt")
        self.workflow.add_edge("generate_prompt", "evaluate_prompt")
        self.workflow.add_edge("evaluate_prompt", "synthesize_reflection")
        self.workflow.add_edge("synthesize_reflection", "decide_next_step")

        # Define conditional edges
        self.workflow.add_conditional_edges(
            "decide_next_step",
            self._router,
            {
                "CONTINUE_PROBING": "generate_prompt",
                "REVISE_STRATEGY": "formulate_strategy",
                "FINISH": END
            }
        )

    def _decide_next_step(self, state: AgentState) -> Dict:
        """A simple node to increment the iteration count before routing."""
        print("\n>>> EXECUTING NODE: DecideNextStep")
        iteration_count = state.get("iteration_count", 0) + 1
        print(f"Iteration {iteration_count} complete.")
        return {"iteration_count": iteration_count}

    def _router(self, state: AgentState) -> Literal:
        """The routing logic based on the agent's state."""
        print("--- Routing ---")
        iteration_count = state["iteration_count"]
        history = state["prompt_history"]

        # Condition 1: FINISH
        latest_eval = history[-1]["evaluation"]
        avg_score = sum(s["score"] for s in latest_eval["scores"]) / len(latest_eval["scores"])
        print(f"Average score for last iteration: {avg_score:.2f}")

        if avg_score >= 8.5 or iteration_count >= 5:
            print("Decision: FINISH (score threshold met or max iterations reached)")
            return "FINISH"

        # Condition 2: REVISE_STRATEGY
        if iteration_count >= 2:
            prev_eval = history[-2]["evaluation"]
            prev_avg_score = sum(s["score"] for s in prev_eval["scores"]) / len(prev_eval["scores"])
            if avg_score <= prev_avg_score:
                print(f"Decision: REVISE_STRATEGY (progress stalled: {avg_score:.2f} <= {prev_avg_score:.2f})")
                return "REVISE_STRATEGY"

        # Condition 3: CONTINUE
        print("Decision: CONTINUE_PROBING")
        return "CONTINUE_PROBING"

    def compile_graph(self):
        """Compiles the graph into a runnable object."""
        return self.workflow.compile()
