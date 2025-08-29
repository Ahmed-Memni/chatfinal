# Database Chatbot

A conversational AI chatbot that interacts with your Supabase database. It translates natural language queries into SQL commands, executes them, and returns results. It also supports generating visualizations like graphs using Matplotlib, asks clarifying questions when needed, and maintains conversation history for context-aware responses.

## Features

- **Natural Language Queries:** Ask questions like `"Give me clients' names"`, and the chatbot will generate and execute the appropriate SQL query on your Supabase database to fetch and display the results.
- **Graph Generation:** Request visualizations, e.g., `"Give me clients' birthdays per year graph"`. The chatbot generates SQL, runs it, creates Matplotlib code, executes it, and returns the chart.
- **Clarification Questions:** If a query is ambiguous (e.g., `"Give me names"`), the chatbot will ask follow-up questions like `"What table's names?"` to refine the request.
- **Conversation History:** Maintains context across interactions. For example, after `"Give me clients' names"`, a follow-up like `"Give me their emails"` will automatically reference the clients from the previous query.
- **Backend Integration:** Powered by Python with Supabase connectivity for database operations.
- **Frontend Interface:** A web-based chat interface built with modern JavaScript frameworks.

## Technologies used 
### Backend
- **Python 3.11+** – Core programming language for backend logic.
- **FastAPI** – Modern web framework for building APIs.
- **SQLAlchemy & psycopg / pg8000** – Database connection, ORM, and query execution for PostgreSQL.
- **LangChain** – Orchestration of LLM workflows, SQL query generation, and AI tools.
- **Pandas & NumPy** – Data manipulation and processing.
- **Matplotlib & Seaborn** – Data visualization and dynamic graph generation.
- **Uvicorn & Starlette** – ASGI server and request handling.
- **Python utilities** – pydantic (data validation), python-dotenv (environment variables), tenacity (retrying), requests (HTTP requests), functools.lru_cache (caching utilities).

### Frontend
- **Next.js** – React-based framework for frontend UI and server-side rendering.

### Other Tools
- **Docker** – Containerization for development and deployment.
- **OpenRouter** – API key-based interface for LLMs.
- **Kimi2** – LLM model used in the project.

## Current Limitations & Future Improvements

- **Single Query Handling** – Currently, the chatbot executes one query at a time and returns a single result per interaction. Supporting multi-step or batch queries is planned for future updates.

- **Database Flexibility** – At the moment, the project is tested primarily with Supabase (PostgreSQL). Future versions aim to support other database types like MySQL, SQLite, and more.

### Running with Docker

If you want to run it in Docker, clone the repository:

```bash
# Clone the repository
git clone https://github.com/Ahmed-Memni/chatfinal.git
```

Then, run these commands in two separate terminals:

```bash
docker compose up --build frontend
```

```bash
docker compose up --build backend
```

## Installation Running locally 

```bash
# Clone the repository
git clone https://github.com/Ahmed-Memni/chatfinal.git

# Navigate to the backend directory
cd ./Backend

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn src.main:app --host 0.0.0.0 --port 8000

# In a new terminal, navigate to the frontend directory
cd ./Frontend

# Install frontend dependencies
npm install

# Run the frontend development server
npm run dev
```
The application should now be running on your localhost (typically at `http://localhost:5173` for the frontend, connecting to the backend at port `8000`).


### Usage

1. Open the frontend in your browser.
2. On startup, the frontend will prompt you to provide your Supabase connection string. i used these 2 to test
   ```bash
   postgresql://postgres.wuexesqrlvgavywvcqwz:eTzesgYI6NMcc0Ky@aws-0-eu-north-1.pooler.supabase.com:5432/postgres
   postgresql://postgres.mdpxecatdmtjslfzoiqk:Rdw9ltvbSAMaojJd@aws-1-eu-north-1.pooler.supabase.com:6543/postgres?sslmode=require
   ```
3. After entering the connection string, the chatbot interface will load.
4. Start chatting with the bot by typing natural language queries related to your database.
5. For graphs, the bot will generate and display Matplotlib-based charts directly in the chat interface which u can download.

Here’s a clearer version with the step-by-step guide included:

---

## Troubleshooting

If you encounter the error `[Error] Error: Server error: 500`, it means the API key for OpenRouter is no longer available. You need to get a new one from OpenRouter and update both these variables in the `.env` file: `OPENROUTER_API_KEY` and `OPENAI_API_KEY`.

### How to get a new OpenRouter API key:

1. Go to [https://openrouter.ai](https://openrouter.ai).
2. Log in (or sign up if you don’t already have an account).
3. Once logged in, click on your **profile picture** (top-right corner).
4. Select **API Keys** from the dropdown menu.
5. Click **Create Key** and copy the generated API key.
6. Open your project’s `.env` file.
7. Replace the old values with your new key:

   ```env
   OPENROUTER_API_KEY=your_new_key_here
   OPENAI_API_KEY=your_new_key_here
   ```
8. Save the file and restart your server/app.

## Agent Reasoning (Thought Process)

The chatbot doesn't just blindly run queries—it uses an **AgentExecutor chain** to plan its actions step by step. This allows it to generate SQL, run visualizations, handle errors, and give context-aware responses. Here’s how it works:

### Example: Retrieving Client Emails

**User Query:**
`Give me clients' emails`

**Agent Thought Process:**

```
> Entering new AgentExecutor chain...
Thought: I need to retrieve all client emails from the clients table.
Action: sql_query
Action Input: Retrieve all client emails from the clients table.
```

**SQL Generated:**

```sql
SELECT email FROM clients ORDER BY email;
```

**SQL Response:**

```
jean.dupont@example.com
sophie.martin@example.com
jean.lemoine@example.com
...
```

**Agent Final Answer:**

```
Here are the emails:
- jean.dupont@example.com
- sophie.martin@example.com
- jean.lemoine@example.com
...
> Finished chain.
```

---

### Example: Generating a Graph

**User Query:**
`Give me clients' birthdays per year graph`

**Agent Thought Process:**

```
> Entering new AgentExecutor chain...
Thought: I need to count clients' birthdays per year to generate a graph.
Action: graph_query
Action Input: Count clients' birthdays per year to generate a graph.
```

**SQL Generated:**

```sql
SELECT EXTRACT(YEAR FROM "date_naissance") AS "year",
       COUNT(*) AS "count"
FROM clients
GROUP BY EXTRACT(YEAR FROM "date_naissance")
ORDER BY "year";
```

**SQL Result:**

```
   count  year
0      1  1975
1      1  1985
2      1  1988
...
```

**Matplotlib Code Generated:** (internal)

```python
plt.bar(data['year'], data['count'], color='skyblue')
plt.title('Client Birthdays per Year')
plt.xlabel('Year')
plt.ylabel('Count')
plt.savefig('chart.png')
```

**Agent Final Answer:**

```
Here is the chart of "clients' birthdays per year".
> Finished chain.
```
<img width="790" height="490" alt="chart-1756122524747" src="https://github.com/user-attachments/assets/64c4883a-ba0c-4447-8774-662394dce14f" />

### Example: Graphs Generated :
<img width="1000" height="800" alt="image" src="https://github.com/user-attachments/assets/7ef67f7f-67e8-461c-8e5c-bad25005e847" />
<img width="800" height="500" alt="image" src="https://github.com/user-attachments/assets/96429a29-b925-4341-8b34-a1405dc73e4f" />
<img width="1000" height="600" alt="image" src="https://github.com/user-attachments/assets/0020c3e7-2290-4dfb-a9a1-90e19053ab67" />
<img width="500" height="353" alt="Screenshot 2025-08-27 110334" src="https://github.com/user-attachments/assets/1c84983f-c654-4491-a46c-ff7fec515707" />
<img width="451" height="268" alt="image" src="https://github.com/user-attachments/assets/a81dcda7-4f93-4d76-ba94-3a46ae81f55e" />

<img width="859" height="547" alt="image" src="https://github.com/user-attachments/assets/63303838-73d3-4d35-86ce-ef13da7c8df9" />

**Agent Reasoning example and steps followed with each result :**

<img width="1333" height="799" alt="image" src="https://github.com/user-attachments/assets/41625808-8fbe-4cb4-a2a3-1dffdaa0ffc5" />


