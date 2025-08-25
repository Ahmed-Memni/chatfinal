from langchain.tools import Tool
from src.chains import full_chain, run_query
from src.database import  get_full_table_info
import matplotlib.pyplot as plt
import pandas as pd
import io, base64
from src.llm import llm
from src.chains import sql_prompt, graph_code_chain
import time
from src.chains import run_query1


def run_full_chain_tool(inputs):
    if isinstance(inputs, str):
        question = inputs
    elif isinstance(inputs, dict):
        question = inputs.get("question")
    else:
        return {"output": "Error: invalid input type", "final_answer": True}

    if not question:
        return {"output": "Error: no question provided", "final_answer": True}

    try:
        result = full_chain.run(question)
        if isinstance(result, dict):
            return {
                "output": result.get("output", str(result)),
                "final_answer": True
            }
        return {"output": str(result), "final_answer": True}
    except Exception as e:
        return {"output": f"Error executing SQL: {str(e)}", "final_answer": True}


sql_tool = Tool(
    name="sql_query",
    func=run_full_chain_tool,
    description="Execute SQL queries and return a plain text result."
)
def ask_clarification(query: str) -> str:
    # The LLM generates the actual question; this tool just outputs it
    return query

clarification_tool = Tool(
    name="ask_clarification",
    func=ask_clarification,
    description="Use this to ask the user a clarification question. The LLM should generate questions using the schema.",
    return_direct=True
)
# def generate_and_execute_graph(inputs, filepath="graph.png"):
#     """Generate and execute dynamic Matplotlib code from SQL results using LLM."""
#     question = inputs if isinstance(inputs, str) else inputs.get("question", "")
#     if not question:
#         return {"output": "Error: no question provided"}

#     try:
#         # 1️⃣ Generate SQL
#         schema_info = get_full_table_info()
#         prompt_value = sql_prompt.format_prompt(question=question, schema=schema_info)
#         query_response = llm.invoke(prompt_value)
#         query = getattr(query_response, "content", query_response).strip()

#         # 2️⃣ Execute SQL and get DataFrame
#         data = run_query1(query)  # Returns a pandas DataFrame
#         if data.empty:
#             return {"output": "SQL query returned no data, graph cannot be generated."}

#         # 3️⃣ Generate dynamic plotting code via LLM
#         graph_prompt = {
#             "question": question,
#             "sql_results": data.to_dict(orient="records"),
#             "instruction": (
#                 "Use the DataFrame named 'data' for plotting. "
#                 "Ensure the figure is saved using plt.savefig(filepath)."
#             )
#         }
#         code = graph_code_chain.invoke(graph_prompt)

#         # 4️⃣ Execute plotting code in a sandboxed environment
#         local_vars = {
#             "plt": plt,
#             "pd": pd,
#             "data": data,
#             "filepath": filepath
#         }
#         exec(code, {}, local_vars)

#         # 5️⃣ Ensure the figure is saved and closed
#         fig = plt.gcf()
#         fig.savefig(filepath, bbox_inches="tight")
#         plt.close(fig)

#         return {"output": f"Graph saved to {filepath}"}

#     except Exception as e:
#         return {"output": f"Failed to generate graph: {str(e)}"}

def generate_and_execute_graph(inputs, filepath="graph.png"):
    """Generate and execute dynamic Matplotlib code from SQL results using LLM with verbose output."""
    question = inputs if isinstance(inputs, str) else inputs.get("question", "")
    if not question:
        return {"output": "Error: no question provided", "final_answer": False}

    try:
        # 1️⃣ Generate SQL
        schema_info = get_full_table_info()
        prompt_value = sql_prompt.format_prompt(question=question, schema=schema_info)
        query_response = llm.invoke(prompt_value)
        query = getattr(query_response, "content", query_response).strip()

        # 2️⃣ Execute SQL and get DataFrame
        data = run_query1(query)  # Returns a pandas DataFrame
        print("\n[VERBOSE] SQL Query:\n")
        print(query)
        print("\n[VERBOSE] SQL Result:\n")
        print(data.head())  # Show first few rows for debugging
        start_time = time.time()  # record start time

        while data.empty:
            if time.time() - start_time > 30:  # break if > 30 seconds
                print("No data received within 30 seconds. Exiting loop.")
                break

            print("Waiting for data...")
            time.sleep(0.5)
            data = run_query1(query)
        if data.empty:
            return {"output": "SQL query returned no data, graph cannot be generated.", "final_answer": False}

        # 3️⃣ Generate dynamic plotting code via LLM
        graph_prompt = {
        "question": question,
        "sql_results": data.to_dict(orient="records"),
        "columns": list(data.columns),   # 👈 Pass real columns here
        "instruction": (
        "Use the DataFrame named 'data' for plotting. "
        "Ensure the figure is saved using plt.savefig(filepath)."
        )
        }
        
        
        code = graph_code_chain.invoke(graph_prompt)

        # 🔹 Verbose always: show the generated code
        print("\n[VERBOSE] Generated Matplotlib code:\n")
        print(code)
        print("\n[VERBOSE] End of generated code\n")

        # 4️⃣ Execute plotting code in a sandboxed environment
        local_vars = {
            "plt": plt,
            "pd": pd,
            "data": data,
            "filepath": filepath
        }
        exec(code, {}, local_vars)

        # 5️⃣ Ensure the figure is saved and closed
        fig = plt.gcf()
        fig.savefig(filepath, bbox_inches="tight")
        plt.close(fig)

        return {"output": f"Graph saved to {filepath}", "final_answer": True}

    except Exception as e:
        return {"output": f"Failed to generate graph: {str(e)}","final_answer": False}

# Tool for generating graphs from SQL results
# This tool uses the generate_and_execute_graph function to create graphs based on SQL query results.
generate_graph_tool = Tool(
    name="graph_query",
    func=generate_and_execute_graph,
    description="Generates a graph from zero"
)


def parsing_fallback_tool(error_message):
    """Return a friendly message when parsing fails."""
    return f"Parsing failed, but here’s the last readable message: {error_message}"
parsing_tool = Tool(
    name="parsing_fallback",
    func=parsing_fallback_tool,
    description="Provide a readable fallback output when parsing fails."
)
tools = [sql_tool, clarification_tool, parsing_tool, generate_graph_tool]