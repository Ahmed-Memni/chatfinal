from functools import lru_cache
import re
import psycopg
from pydantic import PrivateAttr
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import BaseOutputParser
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI  # Use ChatOpenAI instead of OpenAI
from src.database import get_db, get_full_table_info
from src.config import LLM_MODEL, OPENROUTER_API_KEY, OPENROUTER_API_BASE
import pandas as pd
from sqlalchemy import create_engine, text
from src.config import DB_URI

# -------------------------------
# FinalAnswerParser
# -------------------------------
class FinalAnswerParser(BaseOutputParser):
    """Extracts a clean 'Final Answer' from LLM output."""
    def parse(self, text: str) -> str:
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'[*_`]', '', text)
        # Remove Thought/Action lines
        lines = [
            line for line in text.splitlines()
            if not re.match(r'^\s*(Thought|Action)\s*:', line, re.IGNORECASE)
        ]
        text = "\n".join(lines).strip()
        # Extract Final Answer if present, else return everything
        match = re.search(r'Final Answer\s*:\s*(.*)', text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text  # fallback to everything remaining


# -------------------------------
# Initialize LLM and DB
# -------------------------------
llm = ChatOpenAI(
    model_name=LLM_MODEL,  # Should be set to "moonshot/kimi" or similar in src.config
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base=OPENROUTER_API_BASE,
    temperature=0,
)


db = get_db()

# -------------------------------
# Custom output parser
# -------------------------------
class StrOutputParser(BaseOutputParser):
    def parse(self, text: str) -> str:
        return text

# -------------------------------
# SQL validation & execution
# -------------------------------
@lru_cache(maxsize=100)
def validate_sql(query: str) -> str:
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]
    if any(word in query.upper() for word in forbidden):
        raise ValueError("Only SELECT queries are allowed")
    return query

def run_query(query: str):
    try:
        validate_sql(query)
        conn_str = getattr(db, "dsn", db) if isinstance(db, str) or hasattr(db, "dsn") else None
        if not conn_str:
            raise ValueError("Invalid database object format")
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
    except Exception as e:
        return f"Error executing query: {str(e)}"

def run_query1(query: str) -> pd.DataFrame:
    """Run SQL and return results as a pandas DataFrame (for plotting) using SQLAlchemy engine."""
    try:
        validate_sql(query)  # keep your validation
        engine = create_engine(DB_URI)  # use the same URI as get_full_table_info()
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.mappings().all()  # list of dicts
            if not rows:
                return pd.DataFrame()  # empty DataFrame signals no data
            df = pd.DataFrame(rows)
            return df
    except Exception as e:
        print(f"[ERROR] Failed to execute SQL: {e}")
        return pd.DataFrame()  # empty DataFrame signals failure


    # def run_query(query: str):
    # try:
    #     validate_sql(query)

    #     # Remove any LIMIT clause safely
    #     query = re.sub(r'\bLIMIT\s+\d+\b', '', query, flags=re.IGNORECASE)

    #     conn_str = getattr(db, "dsn", db) if isinstance(db, str) or hasattr(db, "dsn") else None
    #     if not conn_str:
    #         raise ValueError("Invalid database object format")

    #     with psycopg.connect(conn_str) as conn:
    #         with conn.cursor() as cur:
    #             cur.execute(query)
    #             return cur.fetchall()
    # except Exception as e:
    #     return f"Error executing query: {str(e)}"


# -------------------------------
# SQL generation chain
# -------------------------------
sql_template = """You are an expert SQL generator for a **PostgreSQL database hosted on Supabase**. Follow these rules strictly:

1. Always generate **PostgreSQL-compliant SQL**. Do NOT use functions from other SQL dialects (e.g., MySQL YEAR(), SQLite strftime()).
2. The user may request graphs, counts, aggregations, or filters on any table/column.
3. You have access to the full database schema, including column names and types. Column types may be: text, date, timestamp, numeric, integer, etc.
   - **You must use the actual column type when generating SQL**.
4. If the user wants to extract a year from a column:
   - If the column is `DATE` or `TIMESTAMP`, use `EXTRACT(YEAR FROM column)`.
   - If the column is `TEXT` containing ISO dates (YYYY-MM-DD), use `SUBSTRING(column::text FROM 1 FOR 4)` to safely extract the year.
5. If calculating a difference between two dates/timestamps:
   - If both columns are `DATE`, use plain subtraction (`date1 - date2`) which yields an integer number of days.
   - If both columns are `TIMESTAMP`, compute the day difference as `EXTRACT(EPOCH FROM (ts1 - ts2)) / 86400`.
6. Always quote identifiers with double quotes if needed to avoid errors.
7. Only generate SQL that can be executed by PostgreSQL. If unsure of a column type, default to safe casting using `::text`.
8. **For every aggregation: all non-aggregated columns in the SELECT must appear in the GROUP BY clause.**
9. Always ORDER BY the same non-aggregated columns used in GROUP BY (unless the user explicitly requests another ordering).
10. Do not output explanations or extra text — **only generate the SQL query**.
10a. **Do not wrap the SQL in Markdown code fences or add ```sql markers. Output only the raw SQL query.**
11. Always generate data suitable for plotting any type of graph: bar chart, line chart, pie chart, etc. The query must always output at least one label column and one value column.
12. Never use SQL functions or syntax from other database engines (MySQL, SQLite, SQL Server, etc.). **If a non-PostgreSQL function appears, rewrite it in PostgreSQL syntax before execution.**
13. Be consistent with table aliases: if you alias a table (e.g., "contrats c"), always use that same alias ("c") for all references to its columns.
14. **If the query involves computations, aggregations, or derived fields, wrap the logic inside a subquery with explicit column aliases, and in the outer query reference only those aliases.**
15. **If the query is a simple retrieval (e.g., SELECT with joins, no computed fields), you may return it directly without wrapping in a subquery.**

Schema reference (with types):
{schema}

User question:
{question}

Generate a **single, fully PostgreSQL-compliant SQL query** that satisfies the user's request, following the above rules.
"""

sql_prompt = ChatPromptTemplate.from_template(sql_template)

# -------------------------------
# Response generation chain
# -------------------------------
response_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are a helpful assistant that converts SQL responses into clean natural language."
    ),
    HumanMessagePromptTemplate.from_template(
        """You are given the following data:
    {input}

Instructions:
- Produce only two lines:
  Thought: <brief summary of what you learned from SQL response>
  Final Answer: <list the results in plain text, one line per record, no extra formatting>
- Do NOT add explanations, tables, or markdown.
- Always start the second line with 'Final Answer:'.

Final Answer:"""
    )
])

response_chain = RunnableSequence(response_prompt, llm, FinalAnswerParser())

# -------------------------------
# FullChain class
# -------------------------------
class FullChain:
    """Combines SQL generation, execution, and response formatting with verbose output."""
    def __init__(self, verbose: bool = True):
        self.sql_prompt = sql_prompt
        self.llm = llm
        self._response_chain = response_chain
        self.verbose = verbose

    def run(self, question: str):
        if not question:
            if self.verbose:
                print("[Verbose] No question provided")
            return {"output": "Error: no question provided"}

        schema_info = get_full_table_info()
        # if self.verbose:
        #     print(f"[Verbose] Retrieved schema info:\n{schema_info}\n")

        # Format prompt for ChatOpenAI
        prompt_value = self.sql_prompt.format_prompt(
            question=question,
            schema=schema_info  # Use the cached schema info
        )
        # if self.verbose:
        #     print(f"[Verbose] Formatted prompt:\n{prompt_value}\n")

        # Generate SQL query using LLM
        query_response = self.llm.invoke(prompt_value)
        query = query_response.content.strip()  # Extract the content
        # if self.verbose:
        #     print(f"[Verbose] Generated SQL query:\n{query}\n")

        # Execute SQL query
        sql_response = run_query(query)
        if self.verbose:
            print(f"[Verbose] SQL query response:\n{sql_response}\n")

        # Combine input for response chain
        combined_input = (
            f"Schema: {schema_info}\n"
            f"Question: {question}\n"
            f"SQL Query: {query}\n"
            f"SQL Response: {sql_response}"
        )
        if self.verbose:
            print(f"[Verbose] Combined input for final response:\n{combined_input}\n")

        # Format final answer
        answer = self._response_chain.invoke({"input": combined_input})
        if self.verbose:
            print(f"[Verbose] Final formatted answer:\n{answer}\n")

        return {"output": answer}


# Instantiate with verbose=True
full_chain = FullChain(verbose=True)


# -------------------------------
# Graph code generation chain
# -------------------------------
graph_code_template = """Based on the user's question and SQL results, generate Python code using Matplotlib to create the best graph type.
Include:
- Imports (matplotlib.pyplot as plt, pandas as pd)
- Use the DataFrame called 'data' provided in the sandbox for plotting
- Use the DataFrame called 'data' exactly as returned by the SQL query
- Save figure to the variable 'filepath' (always 'chart.png', no plt.show())
- Dynamically detect numeric columns in 'data' and convert them to float for plotting
- Fill missing numeric values with 0
- Use non-numeric columns as axes, labels, or categories
- Ensure bubble sizes in scatter/bubble charts match x and y lengths
- Set titles, labels, and legend appropriately
- Do NOT redefine 'data' or convert list of dicts
- Do NOT include markdown, code fences, or annotations
- Use the column names exactly as they appear in 'data'
- Available columns: {columns}
- IMPORTANT: 
  * When creating a stackplot with multiple numeric series (columns), unpack each numeric series as a separate argument using '*' to avoid blank graphs. 
  * When creating a Sankey diagram (multi-node flows), use Plotly Sankey (plotly.graph_objects) instead of matplotlib.sankey to avoid shape mismatches. Do not change this behavior for other chart types.

Question: {question}

Generated Python code (no markdown):
"""
graph_code_prompt = ChatPromptTemplate.from_template(graph_code_template)
graph_code_chain = RunnableSequence(graph_code_prompt, llm, StrOutputParser())
