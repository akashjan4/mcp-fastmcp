# FastMCP – Detailed Documentation

## 1. Introduction

**FastMCP** is a Python framework for building **MCP (Model Context Protocol) servers** quickly and cleanly. It provides a FastAPI-like developer experience to expose:

* **Tools** (functions callable by LLMs)
* **Resources** (read-only data or documents)
* **Prompts** (structured prompt templates)

FastMCP is commonly used to:

* Connect LLMs to real systems (databases, APIs, files)
* Build agent backends
* Integrate with tools like Claude Desktop, Cursor, Continue, OpenAI-compatible agents, etc.

If you know **FastAPI**, **Flask**, or modern Python async patterns, FastMCP will feel very natural.

---

## 2. Key Concepts

### 2.1 MCP (Model Context Protocol)

MCP is a standard that allows AI models to:

* Discover available tools
* Call tools with structured arguments
* Read external resources
* Use predefined prompts

FastMCP is a **server-side implementation** of MCP.

### 2.2 Core Abstractions

| Concept  | Description                              |
| -------- | ---------------------------------------- |
| Tool     | A callable function exposed to the model |
| Resource | Read-only data accessible via URI        |
| Prompt   | Reusable prompt templates                |
| Server   | MCP runtime that exposes all above       |

---

## 3. Prerequisites

* Python **3.10+** (recommended: 3.11)
* Basic knowledge of async Python
* `uv` package manager (recommended)

---

## 4. Installing FastMCP using `uv`

### 4.1 Why `uv`?

`uv` is a **fast, modern Python package manager** and virtual environment tool. It replaces:

* `pip`
* `virtualenv`
* `pip-tools`

Benefits:

* Much faster dependency resolution
* Reproducible environments
* Single tool for venv + install

---

### 4.2 Install `uv`

#### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows (PowerShell)

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Verify:

```bash
uv --version
```

---

### 4.3 Create a New Project

```bash
mkdir fastmcp-demo
cd fastmcp-demo
uv init
```

This creates:

```
fastmcp-demo/
├── pyproject.toml
└── .venv/
```

---

### 4.4 Install FastMCP

```bash
uv add fastmcp
```

This automatically:

* Creates a virtual environment
* Pins dependencies
* Updates `pyproject.toml`

---

## 5. Project Structure (Recommended)

```
fastmcp-demo/
├── app/
│   ├── __init__.py
│   ├── server.py
│   ├── tools.py
│   ├── resources.py
│   └── prompts.py
├── pyproject.toml
└── README.md
```

---

## 6. Creating a Basic FastMCP Server

### 6.1 server.py

```python
from fastmcp import FastMCP

mcp = FastMCP("Demo MCP Server")

if __name__ == "__main__":
    mcp.run()
```

Run the server:

```bash
uv run python app/server.py
```

---

## 7. Defining Tools

Tools are functions that the LLM can call.

### 7.1 tools.py

```python
from fastmcp import FastMCP

mcp = FastMCP.get_instance()

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b
```

### Key Rules for Tools

* Must have **type hints**
* Docstring is exposed to the model
* Can be sync or async

### Async Tool Example

```python
@mcp.tool()
async def fetch_user(user_id: int) -> dict:
    return {"id": user_id, "name": "Akash"}
```

---

## 8. Defining Resources

Resources expose read-only data via URI.

### 8.1 resources.py

```python
from fastmcp import FastMCP

mcp = FastMCP.get_instance()

@mcp.resource("users://{user_id}")
def get_user(user_id: int) -> str:
    return f"User profile for {user_id}"
```

### Resource URI Examples

| URI            | Meaning        |
| -------------- | -------------- |
| `users://123`  | Fetch user 123 |
| `config://app` | App config     |

---

## 9. Defining Prompts

Prompts are reusable templates.

### 9.1 prompts.py

```python
from fastmcp import FastMCP

mcp = FastMCP.get_instance()

@mcp.prompt()
def summarize_text(text: str) -> str:
    return f"Summarize the following text:\n{text}"
```

---

## 10. Registering Modules

Ensure all modules are imported so FastMCP can register them.

### server.py (final)

```python
from fastmcp import FastMCP
import app.tools
import app.resources
import app.prompts

mcp = FastMCP("Demo MCP Server")

if __name__ == "__main__":
    mcp.run()
```

---

## 11. Running the Server

```bash
uv run python app/server.py
```

By default:

* Runs on stdio (for desktop tools)
* Compatible with MCP clients

---

## 12. Using with Claude Desktop / Cursor

### Claude Desktop

`claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fastmcp-demo": {
      "command": "uv",
      "args": ["run", "python", "app/server.py"],
      "cwd": "/absolute/path/fastmcp-demo"
    }
  }
}
```

---

## 13. Logging & Debugging

```python
mcp = FastMCP(
    "Demo MCP Server",
    log_level="DEBUG"
)
```

Use:

```bash
uv run python app/server.py --debug
```

---

## 14. Error Handling Best Practices

```python
@mcp.tool()
def safe_divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b
```

Errors are returned to the LLM in structured form.

---

## 15. Security Best Practices

* Never expose raw DB credentials
* Validate inputs strictly
* Use allow-lists for file access
* Avoid shell execution

---

## 16. Production Deployment Patterns

| Pattern   | Use Case                  |
| --------- | ------------------------- |
| Stdio     | Local tools, desktop apps |
| HTTP      | Remote MCP servers        |
| Container | Team / enterprise usage   |

Docker example:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install fastmcp
CMD ["python", "app/server.py"]
```

---

## 17. When to Use FastMCP vs Alternatives

| Framework  | Use When               |
| ---------- | ---------------------- |
| FastMCP    | Tool-driven AI systems |
| FastAPI    | Traditional REST APIs  |
| LangChain  | Chains & orchestration |
| LlamaIndex | Heavy RAG pipelines    |

---

## 18. Common Pitfalls

* Forgetting to import tool modules
* Missing type hints
* Returning non-JSON-serializable objects
* Blocking I/O in async tools

---

## 19. Next Steps

* Add database-backed tools
* Combine with RAG pipelines
* Integrate authentication
* Add observability

---

## 20. Summary

FastMCP enables:

* Clean AI-tool interfaces
* Strong typing & discoverability
* Simple deployment

Using `uv` makes the setup fast, reproducible, and production-ready.

---

If you want, I can also provide:

* Enterprise architecture with FastMCP
* FastMCP + RAG + Vector DB example
* Comparison with LangChain tools
* Testing strategy for MCP servers
