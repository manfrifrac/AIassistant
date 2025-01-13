# Agent Flow Overview

## Supervisor Agent: Request Analysis and Context Generation
**Input**  
- `{user_message}`, `{interaction_id}`, `{stm_data}`, `{ltm_data}`

**Operations**  
- Determines `{selected_agent}` based on `{user_message}`  
- Builds `{context}` with relevant short-term and long-term memory

**Output**  
- `{selected_agent}`  
- `{context}`

## Greeting Agent
**Input**  
- `{user_message}`, `{context}`

**Operations**  
- Generates a personalized response using preferences from `ltm_data`

**Output**  
- `{assistant_message}`  
- Routes back to Supervisor Agent

## Researcher Agent
**Input**  
- `{user_message}`, `{context}`

**Operations**  
- Performs queries or research  
- Builds an informational response

**Output**  
- `{assistant_message}`  
- Routes back to Supervisor Agent

## Memory Agent
**Input**  
- `{user_message}`, `{context}`, `{assistant_message}`, `{session_id}`

**Operations**  
- Updates short-term and long-term memory  
- Logs the interaction

**Output**  
- `{updated_stm}`, `{updated_ltm}`, `{interaction_log}`  
- Routes back to Supervisor Agent

## Interaction Flow
1. The Supervisor decides which agent to invoke.  
2. The selected agent produces an `assistant_message`.  
3. The Memory Agent updates STM/LTM and logs the interaction.  
4. The flow routes back to the Supervisor Agent for the next interaction or ends if completed.