import json
from typing import Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from state import AgentState, DecomposedGoal, ImprovementPlan, GeneratedPrompt, EvaluationResult, Reflection


class P3RO_Agent_Tools:
    """A class to encapsulate all the tools for the P³RO agent."""

    def __init__(self, llm_model_name="gemini-2.5-pro"):
        """Initializes the toolset with a specific Gemini model."""
        self.model = ChatGoogleGenerativeAI(model=llm_model_name, temperature=1.0)
        print(f"--- Tools initialized with model: {llm_model_name} ---")

    def _invoke_llm_for_json(self, prompt: str, pydantic_class: BaseModel):
        """A helper function to invoke the LLM and parse its structured output."""
        try:
            structured_llm = self.model.with_structured_output(pydantic_class)
            response_obj = structured_llm.invoke(prompt)
            return response_obj
        except Exception as e:
            print(f"Error calling LLM or parsing output for {pydantic_class.__name__}: {e}")
            # Fallback or retry logic could be implemented here
            return None

    def decompose_goal(self, state: AgentState) -> Dict:
        """Translates the user's goal into concrete criteria."""
        print("\n>>> EXECUTING NODE: DecomposeGoal")
        goal = state["goal"]
        prompt = f"""
        **Role:** You are a meticulous requirements analyst and prompt engineering expert. Your task is to decompose a user's high-level, often vague, goal for a prompt into a set of specific, orthogonal, and actionable criteria. These criteria will be used to objectively evaluate future versions of the prompt.

        **Context:**
        - The user wants to improve an initial prompt.
        - The user has provided the following goal: "{goal}"

        **Task:**
        1.  **Analyze the Goal:** Deeply analyze the user's goal. Identify the core intent and the key qualities the user is seeking in the final prompt's output. Consider aspects like tone, structure, persona, constraints, and desired output format.
        2.  **Decompose into Criteria:** Break down the goal into 3-5 distinct, measurable criteria. Each criterion should be a concise statement describing a specific quality or characteristic.
        3.  **Ensure Actionability:** Each criterion must be something that can be reasonably judged or measured when comparing two prompts. Avoid vague terms like "make it better." Instead, use precise language like "Increase the use of sensory details," "Adopt a more formal and academic tone," or "Ensure the output is structured as a JSON object with 'name' and 'description' keys."

        **Example:**
        - **User Goal:** "I want a prompt for a marketing copywriter that is more creative and engaging."
        - **Your Decomposed Criteria Output (as JSON):**
          ```json
          {{
            "criteria": [
              "Evoke a sense of urgency in the target audience.",
              "Incorporate at least two power words related to exclusivity.",
              "Use a conversational and slightly humorous tone.",
              "End with a clear and compelling call-to-action."
            ]
          }}
          ```

        **Instructions:**
        - Generate ONLY the list of criteria.
        - Your output must be a single, valid JSON object that strictly adheres to the following Pydantic schema:
          `class DecomposedGoal(BaseModel): criteria: List[str]`

        **User Goal to Decompose:**
        "{goal}"
        """
        result = self._invoke_llm_for_json(prompt, DecomposedGoal)
        if not result:
            raise ValueError("Failed to decompose goals.")
        
        print(f"Decomposed Criteria: {result.criteria}")
        return {"decomposed_criteria": result.criteria}

    def formulate_strategy(self, state: AgentState) -> Dict:
        """Creates a high-level improvement plan."""
        print("\n>>> EXECUTING NODE: FormulateStrategy")
        prompt = f"""
        **Role:** You are an expert AI strategist and master prompt engineer. Your task is to devise a high-level, ordered plan to improve a given prompt based on a set of specific criteria. If this is a revision, you must learn from past failures.

        **Context:**
        - Initial Prompt: "{state['initial_prompt']}"
        - Improvement Criteria: {state['decomposed_criteria']}
        - History of Past Attempts (if any): "{state['prompt_history']}"

        **Task:**
        1.  **Analyze the Gap:** Compare the Initial Prompt with the Improvement Criteria. Identify the biggest gaps and areas for improvement. If a history of past attempts exists, analyze why the previous strategy failed. The last entry in the history contains the most relevant feedback.
        2.  **Formulate a Strategy:** Create a logical, step-by-step plan to address these gaps. The plan should be a sequence of general approaches. Think about the order of operations. It might be best to fix the structure first, then the tone, then the specific details. If revising a failed strategy, explicitly state a *new* approach.
        3.  **Output the Plan:** Write the plan as a concise, multi-line string, formatted as a numbered list.

        **Example (First Pass):**
        - **Initial Prompt:** "Write about our new shoes."
        - **Improvement Criteria:**
        - **Your Formulated Plan Output (as JSON):**
          ```json
          {{
            "plan": "1. First, I will rewrite the prompt to explicitly establish the persona of a professional athlete.\\n2. Second, I will add specific instructions to focus on the 'ultralight foam' technology and its benefits.\\n3. Finally, I will adjust the language to be more energetic and use slang appropriate for a young, active audience."
          }}
          ```

        **Instructions:**
        - Generate ONLY the plan string.
        - Your output must be a single, valid JSON object that strictly adheres to the following Pydantic schema:
          `class ImprovementPlan(BaseModel): plan: str`

        **Your Task:**
        - Initial Prompt: "{state['initial_prompt']}"
        - Improvement Criteria: {state['decomposed_criteria']}
        - History of Past Attempts: "{state['prompt_history']}"
        """
        result = self._invoke_llm_for_json(prompt, ImprovementPlan)
        if not result:
            raise ValueError("Failed to formulate strategy.")
        
        print(f"Formulated Plan:\n{result.plan}")
        return {"high_level_plan": result.plan}

    def generate_prompt(self, state: AgentState) -> Dict:
        """Generates a new, improved version of the prompt."""
        print("\n>>> EXECUTING NODE: GeneratePrompt")

        # Determine the prompt to improve upon
        if not state["prompt_history"]:
            base_prompt_context = f"The initial prompt to improve is: {state['initial_prompt']}"
        else:
            last_prompt = state["prompt_history"][-1]["prompt_text"]
            base_prompt_context = f"The most recent prompt to improve is: {last_prompt}"

        prompt = f"""
        **Role:** You are a creative and meticulous prompt engineer executing one step of a larger plan. Your task is to generate a single, new version of a prompt that attempts to improve upon the previous version, guided by a high-level plan and specific reflections from the last attempt.

        **Context:**
        - The overall strategic plan is: "{state['high_level_plan']}"
        - {base_prompt_context}
        - The key takeaway from the last evaluation (your primary focus for this iteration) is: "{state['current_reflection']}"

        **Task:**
        1.  **Synthesize Context:** Review the entire context. Understand the main goal, what has been tried, and what the most recent analysis concluded. 
        2.  **Formulate a Thought (Reasoning):** Based on the `current_reflection`, decide on the *single most impactful change* you can make to the most recent prompt. This could be rephrasing a sentence, adding a constraint, changing the persona, or adding an example. State this thought process clearly and concisely. This will be your `reasoning`.
        3.  **Generate the New Prompt:** Write the complete text of the new, improved prompt. Do not just write the changed part; provide the full prompt from beginning to end.

        **Instructions:**
        - Your output must be a single, valid JSON object that strictly adheres to the following Pydantic schema:
          `class GeneratedPrompt(BaseModel): prompt_text: str; reasoning: str`
        - The `reasoning` field should contain your thought process for this specific iteration.
        - The `prompt_text` field should contain the full text of the newly generated prompt.

        **Perform your task now based on the provided context.**
        """
        result = self._invoke_llm_for_json(prompt, GeneratedPrompt)
        if not result:
            raise ValueError("Failed to generate prompt.")
        
        print(f"Generator Reasoning: {result.reasoning}")
        print(f"Generated Prompt:\n---\n{result.prompt_text}\n---")

        # Update history with the new prompt and its reasoning
        history = state["prompt_history"]
        history.append({"prompt_text": result.prompt_text, "reasoning": result.reasoning})

        return {"prompt_history": history}

    def evaluate_prompt(self, state: AgentState) -> Dict:
        """Evaluates the latest prompt against the criteria."""
        print("\n>>> EXECUTING NODE: EvaluatePrompt")
        new_prompt_text = state["prompt_history"][-1]["prompt_text"]
        decomposed_criteria = state["decomposed_criteria"]

        prompt = f"""
        **Role:** You are a hyper-critical and objective AI prompt evaluator. Your task is to score a new prompt against a set of predefined criteria and provide a detailed justification for your scores. You must be impartial, rigorous, and analytical.

        **Context:**
        - The new prompt to be evaluated is: "{new_prompt_text}"
        - The evaluation criteria are: {decomposed_criteria}

        **Task:**
        1.  **Evaluate Against Each Criterion:** For each individual criterion in the list, perform the following:
            a.  Carefully assess how well the `new_prompt_text` satisfies that specific criterion.
            b.  Assign a score from 1 (fails completely) to 10 (perfectly satisfies). A score of 5 means it partially addresses the criterion but has significant room for improvement.
            c.  Write a brief, one-sentence justification for your score, citing specific evidence from the prompt text or noting its absence.
        2.  **Provide Holistic Feedback:** After scoring all criteria, write a short paragraph of overall qualitative feedback. Summarize the prompt's main strengths and weaknesses. Point out any unintended side effects of the changes and suggest the most important area for the next improvement.

        **Instructions:**
        - Your output must be a single, valid JSON object that strictly adheres to the following Pydantic schema:
          `class CriterionScore(BaseModel): criterion: str; score: int; justification: str`
          `class EvaluationResult(BaseModel): scores: List; qualitative_feedback: str`
        - Be strict and consistent in your scoring. Do not give high scores easily. Your justification is more important than the score itself.

        **Perform your evaluation now.**
        """
        result = self._invoke_llm_for_json(prompt, EvaluationResult)
        if not result:
            raise ValueError("Failed to evaluate prompt.")

        # Update the last entry in history with its evaluation
        history = state["prompt_history"]
        history[-1]["evaluation"] = result.dict()

        print("Evaluation Results:")
        for score in result.scores:
            print(f"  - {score.criterion}: {score.score}/10 ({score.justification})")
        print(f"Qualitative Feedback: {result.qualitative_feedback}")

        return {"prompt_history": history}

    def synthesize_reflection(self, state: AgentState) -> Dict:
        """Analyzes evaluation results to produce an actionable insight."""
        print("\n>>> EXECUTING NODE: SynthesizeReflection")
        evaluation_result = state["prompt_history"][-1]["evaluation"]

        prompt = f"""
        **Role:** You are a master strategist and learning algorithm. Your task is to analyze an evaluation report and synthesize a single, powerful insight that will guide the next action. You are performing the "Orient" step of the OODA loop.

        **Context:**
        - The most recent prompt was just evaluated. The results are: "{evaluation_result}"

        **Task:**
        1.  **Analyze the Data:** Look at the scores (especially the lowest ones) and the qualitative feedback.
        2.  **Identify the Core Pattern:** What is the most important story the data is telling? Did one change improve some criteria but hurt others? Was the main change ineffective? What is the root cause of the lowest scores?
        3.  **Synthesize a Reflection:** Distill your analysis into a single, concise, and actionable sentence. This reflection should state what was learned and clearly imply what should be done differently in the next iteration. It must be a directive for the `PromptGenerator`.

        **Example:**
        - **Evaluation Result:** Scores for 'clarity' went up to 8, but scores for 'creativity' went down to 3. Feedback mentions the prompt is now "too rigid and formulaic."
        - **Your Synthesized Reflection (as JSON):**
          ```json
          {{
            "summary": "The attempt to add structure made the prompt too restrictive, stifling creativity; the next iteration must introduce more flexibility, perhaps by adding an 'out-of-the-box ideas' section, while maintaining the new-found clarity."
          }}
          ```

        **Instructions:**
        - Generate ONLY the summary string.
        - Your output must be a single, valid JSON object that strictly adheres to the following Pydantic schema:
          `class Reflection(BaseModel): summary: str`

        **Perform your synthesis now.**
        """
        result = self._invoke_llm_for_json(prompt, Reflection)
        if not result:
            raise ValueError("Failed to synthesize reflection.")
        
        print(f"Synthesized Reflection: {result.summary}")
        return {"current_reflection": result.summary}
