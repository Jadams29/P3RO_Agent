import os

from dotenv import load_dotenv

from agents import P3RO_Graph

# --- Configuration ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if __name__ == "__main__":
    print("--- Initializing P³RO Agent ---")

    # Example User Input
    initial_prompt_example = "Write a tweet about our new productivity app, 'SyncFlow'."
    goal_example = "Make the prompt generate tweets that are more exciting, create a sense of FOMO (fear of missing out), and include a clear call to action."

    # Initial state
    initial_state = {
        "initial_prompt": initial_prompt_example,
        "goal": goal_example,
        "decomposed_criteria": "",
        "high_level_plan": "",
        "prompt_history": "",
        "current_reflection": "This is the first iteration, so the goal is to establish a baseline improvement based on the initial plan.",
        "final_prompt": "",
        "iteration_count": 0,
    }

    # Build and compile the graph
    p3ro_graph_builder = P3RO_Graph()
    app = p3ro_graph_builder.compile_graph()

    print("\n--- Starting Agent Execution ---")

    # Stream the execution to see the agent's thought process
    final_state = None
    for s in app.stream(initial_state):
        # The key is the name of the node that just ran
        node_name = list(s.keys())
        print(f"\n--- State after node '{node_name}' ---")
        # You can print the full state here for detailed debugging if needed
        # print(s[node_name])
        final_state = s[node_name]

    print("\n\n--- Agent Execution Finished ---")

    # Find the best prompt from the history
    best_prompt = ""
    best_score = -1
    if final_state and final_state.get("prompt_history"):
        for attempt in final_state["prompt_history"]:
            if "evaluation" in attempt:
                current_score = sum(s["score"] for s in attempt["evaluation"]["scores"])
                if current_score > best_score:
                    best_score = current_score
                    best_prompt = attempt["prompt_text"]

    print("\n\n=====================================")
    print("          FINAL RESULTS")
    print("=====================================")
    print("\n### Initial Prompt:")
    print(initial_state["initial_prompt"])
    print("\n### User Goal:")
    print(initial_state["goal"])
    print("\n### Best Refined Prompt:")
    if best_prompt:
        print(best_prompt)
    else:
        print("No improved prompt was finalized.")
    print("\n=====================================")
