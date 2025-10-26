from fastmcp import FastMCP


def register_fun_tools(mcp: FastMCP):
  @mcp.tool
  def greet(name: str) -> str:
      """Greets a person by name."""
      return f"Hello, {name}!"

  @mcp.tool()
  def add_numbers(a: int, b: int) -> int:
      """Adds two numbers and returns the result."""
      return a + b

  @mcp.tool()
  def subtract_numbers(a: int, b: int) -> int:
      """Subtracts two numbers and returns the result."""
      return a - b