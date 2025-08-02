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
        "decomposed_criteria": [],
        "high_level_plan": "",
        "prompt_history": [],
        "current_reflection": "This is the first iteration, so the goal is to establish a baseline improvement based on the initial plan.",
        "final_prompt": "",
        "iteration_count": 0,
    }

    # Build and compile the graph
    p3ro_graph_builder = P3RO_Graph()
    app = p3ro_graph_builder.compile_graph()

    print("\n--- Starting Agent Execution ---")

    # Run the agent and get the complete final state
    final_state = app.invoke(initial_state)

    print("\n\n--- Agent Execution Finished ---")

    # Find the best prompt from the history with robust error handling
    best_prompt = ""
    best_score = -1
    
    print(f"\n--- Debugging Final State ---")
    if final_state:
        print(f"Final state keys: {list(final_state.keys())}")
        if "prompt_history" in final_state:
            print(f"Found {len(final_state['prompt_history'])} prompts in history")
        else:
            print("No 'prompt_history' key in final_state")
    else:
        print("final_state is None")
    
    if final_state and final_state.get("prompt_history"):
        for i, attempt in enumerate(final_state["prompt_history"]):
            print(f"\nAttempt {i} keys: {list(attempt.keys())}")
            if "evaluation" in attempt and attempt["evaluation"] and "scores" in attempt["evaluation"]:
                try:
                    scores = attempt["evaluation"]["scores"]
                    print(f"  Found {len(scores)} evaluation scores")
                    current_score = sum(s["score"] for s in scores if isinstance(s, dict) and "score" in s)
                    print(f"  Total score: {current_score}")
                    if current_score > best_score:
                        best_score = current_score
                        best_prompt = attempt["prompt_text"]
                        print(f"  New best prompt found with score {current_score}")
                except Exception as e:
                    print(f"  Error calculating score for attempt {i}: {e}")
            else:
                print(f"  No evaluation data for attempt {i}")
    
    # Fallback: if no evaluated prompts, use the last generated one
    if not best_prompt and final_state and final_state.get("prompt_history"):
        print("\nNo evaluated prompts found, using last generated prompt as fallback")
        last_attempt = final_state["prompt_history"][-1]
        if "prompt_text" in last_attempt:
            best_prompt = last_attempt["prompt_text"]
            print("Using last generated prompt")
    
    if not best_prompt:
        print("No prompts found in history")

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
