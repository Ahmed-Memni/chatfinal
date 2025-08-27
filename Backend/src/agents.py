"""
Agent setup for insurance contract management chatbot.
"""
from langchain.agents import create_react_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains.router import MultiPromptChain
from langchain.chains.router.llm_router import LLMRouterChain, RouterOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from src.tools import tools
from src.chains import full_chain
from langchain_openai import OpenAI
from langchain_openai import ChatOpenAI
from src.config import OPENROUTER_API_KEY, OPENROUTER_API_BASE, LLM_MODEL
from src.database import get_full_table_info
from src.llm import llm   # instead of defining llm here
from src.tools import tools
# llm = ChatOpenAI(
#     model_name=LLM_MODEL,
#     openai_api_key=OPENROUTER_API_KEY,
#     openai_api_base=OPENROUTER_API_BASE,
#     temperature=0,
# )


# router_template = """
# Given the user question, decide if it should be answered with text or a graph visualization.
# Route to 'graph' only if the question contains words like 'chart', 'graph', 'plot', 'pie', or 'bar'.
# Otherwise, route to 'text'.
# Question: {input}
# """

# router_prompt = PromptTemplate.from_template(router_template)

# destinations = [
#     "text: For text-based SQL query responses.",
#     "graph: For generating graphs or visualizations."
# ]
# destination_str = "\n".join(destinations)

# router_chain = LLMRouterChain.from_llm(
#     llm=llm,
#     prompt=PromptTemplate(
#         template="""{router_template}\n\n{destination_str}\n\nOutput Format:\n{{destination_name}}\n{{input}}""",
#         input_variables=["router_template", "destination_str"],
#         partial_variables={"router_template": router_template, "destination_str": destination_str},
#         output_parser=RouterOutputParser(),
#     ),
# )

# Correct prompt for create_react_agent, including required variables {tools} and {tool_names}
REACT_PROMPT = PromptTemplate(
    input_variables=["input", "history", "agent_scratchpad", "tools", "tool_names"],
    partial_variables={"schema": lambda: get_full_table_info()},
    template="""
You are a database chatbot for insurance contracts.

**Strict Stop Rule (HIGHEST PRIORITY)**
- Once a tool has returned a result (even empty), do NOT generate another Action.
- Move directly to Step 2 and produce the Final Answer.
- Never try to refine or regenerate data already returned by the tool.
- Consider the dictionary returned by the tool (keys: 'output', 'final_answer') as the final result.

**Database Schema**:
{schema}

**RULES (Never break these):**

- **Step 1 (before tool output is shown):**
  - Output ONLY:
    Thought: <your reasoning>
    Action: <tool name from [{tool_names}]>
    Action Input: <a concise, high-level description of what the tool should do>
  - DO NOT include SQL, code, or previous tool output in Action Input.
  - Only generate one Action per user query.
  - Never include tool output in Step 1.
  - If the user's query is ambiguous, ask a clarification question using the schema.
  -  Only use 'graph_query' if the user literally includes one of the words: 
   "chart", "graph", "plot","heatmap" or "histogram". 
    Do NOT infer a graph from other words like "trend", "monthly", "over time", or "summary".
   +    In that case, do NOT generate a separate sql_query first — assume graph_query will handle any required data retrieval.
  - Do NOT generate graphs for normal data queries.

- **Step 2 (after tool output is shown):**
  - Output ONLY:
    Thought: <what you learned from tool output>
    Final Answer: <final response for user>
  - NEVER include another Action in Step 2.
  - Always consider the tool output as the final result.
  - If the tool output contains no data, explicitly report this in the Final Answer.
  - Do not hallucinate or regenerate data already provided by the tool.
  -  - If the tool returned {{'final_answer': True}}, this is the definitive result.
  +  - If the tool returned {{'final_answer': True}}, this is the definitive result.
  +    Do NOT generate any further Thought or Action — immediately stop and output the Final Answer.
  - **If the tool used was 'graph_query', always phrase the Final Answer as:**
    Final Answer: Here is the chart of "a short description of what the chart shows".




**Valid SQL Query Example**

Human: Get all client emails.

AI (Step 1):
Thought: I need to retrieve all client emails.
Action: sql_query
Action Input: Retrieve all client emails from the clients table.

[Tool output here]

AI (Step 2):
Thought: I have retrieved the client emails.
Final Answer: Here are the emails:
- john@example.com
- jane@example.com

**Valid Graph Example**

Human: Show a bar chart of number of clients per city.

AI (Step 1):
Thought: I need to count clients per city for a bar chart.
Action: graph_query
Action Input: Count clients per city to generate a bar chart.

[Tool output here]

AI (Step 2):
Thought: I have generated the bar chart of client counts per city.
Final Answer: Here is the chart of "number of clients per city".

**Ambiguous Query Example**

Human: Get the names.

AI (Step 1):
Thought: The query 'Get the names' is ambiguous because multiple tables have a 'name' column.
Action: ask_clarification
Action Input: Which table's 'name' column do you want? (clients, agents)

[User responds]

AI (Step 2):
Thought: I now know which table the user meant.
Final Answer: Here are the names from the chosen table.

Tools:
{tools}

Conversation history:
{history}

Human: {input}
AI: {agent_scratchpad}  
"""
)


memory = ConversationBufferMemory(memory_key="history", return_messages=True)

# decider_chain = MultiPromptChain(
#     router_chain=router_chain,
#     destination_chains={"text": full_chain, "graph": graph_code_chain},
#     default_chain=full_chain,
#     silent_errors=True
# )
def get_agent_executor():
    """Create and return a ReAct agent executor with memory and decider chain."""
    agent = create_react_agent(llm=llm, tools=tools, prompt=REACT_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=2,
    )