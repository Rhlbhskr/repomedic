import json

from groq import Groq

from config import (
    GROQ_API_KEY,
    MODEL_NAME,
    MAX_AGENT_STEPS,
)
from prompts import SYSTEM_PROMPT
from tools import (
    get_file_tree,
    read_file,
    search_code,
    get_file_snippet,
)


# ---------------------------------------------------------
# Groq client
# ---------------------------------------------------------

client = Groq(api_key=GROQ_API_KEY)


# ---------------------------------------------------------
# Allowed tool names
# ---------------------------------------------------------

ALLOWED_TOOLS = {
    "get_file_tree",
    "search_code",
    "read_file",
    "get_file_snippet",
}


# ---------------------------------------------------------
# Tool schemas exposed to the model
# ---------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_file_tree",
            "description": (
                "Show the directory and file structure of the repository. "
                "Use this when you need to understand how the project is "
                "organized or locate relevant files."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": (
                "Search the repository for a string such as a function "
                "name, variable, class, route, error message, or other "
                "piece of source code."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Text or symbol to search for across "
                            "the repository."
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the complete contents of a repository file with "
                "line numbers. file_path MUST be relative to the "
                "repository root. Never include the repository folder "
                "name itself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": (
                            "Path relative to repository root. "
                            "Examples: 'auth.py', 'src/app.py'."
                        ),
                    }
                },
                "required": ["file_path"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_file_snippet",
            "description": (
                "Read only a selected range of lines from a repository "
                "file. The path must be relative to the repository root."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": (
                            "Path relative to repository root."
                        ),
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "First line to read.",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Last line to read.",
                    },
                },
                "required": [
                    "file_path",
                    "start_line",
                    "end_line",
                ],
            },
        },
    },
]


# ---------------------------------------------------------
# Tool-name cleanup
# ---------------------------------------------------------

def normalize_tool_name(tool_name: str) -> str:
    """
    Recover from occasional malformed model-generated tool
    names such as:

        search_code<|channel|>commentary

    Only known RepoMedic tool prefixes are accepted.
    """

    if tool_name in ALLOWED_TOOLS:
        return tool_name

    for allowed_name in ALLOWED_TOOLS:
        if tool_name.startswith(allowed_name):
            print(
                "\n[Warning] Model generated malformed tool name:"
            )
            print(f"  {tool_name}")
            print(f"Recovered as:")
            print(f"  {allowed_name}")

            return allowed_name

    return tool_name


# ---------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------

def execute_tool(
    repo_path: str,
    tool_name: str,
    arguments: dict,
) -> str:

    if tool_name == "get_file_tree":
        return get_file_tree(repo_path)

    if tool_name == "search_code":
        return search_code(
            repo_path,
            arguments["query"],
        )

    if tool_name == "read_file":
        return read_file(
            repo_path,
            arguments["file_path"],
        )

    if tool_name == "get_file_snippet":
        return get_file_snippet(
            repo_path,
            arguments["file_path"],
            arguments["start_line"],
            arguments["end_line"],
        )

    return f"Error: Unknown tool: {tool_name}"


# ---------------------------------------------------------
# LLM call
# ---------------------------------------------------------

def call_model(messages):
    """
    Request the next action from the model.

    Tool validation is disabled at Groq's API boundary so that
    malformed model-generated tool names can be safely validated
    and recovered by RepoMedic itself.
    """

    return client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0,

        # Important:
        # allow our application to validate generated calls.
        disable_tool_validation=True,
    )


# ---------------------------------------------------------
# Main agent loop
# ---------------------------------------------------------

def run_debugging_agent(
    repo_path: str,
    bug_report: str,
) -> str:

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": f"""
You have access to a local software repository through
repository inspection tools.

Repository:
{repo_path}

Bug report:
{bug_report}

Investigate this bug autonomously.

Use repository tools to gather evidence before reaching a
conclusion.

You may use ONLY these exact tools:

- get_file_tree
- search_code
- read_file
- get_file_snippet

Rules:

- Never invent another tool name.
- File paths must be relative to the repository root.
- Never include the repository folder name in file paths.
- Gather enough evidence before diagnosing the bug.
- You cannot execute tests.
- Proposed tests must be clearly described as unexecuted.
""",
        },
    ]

    # -----------------------------------------------------
    # Agent investigation loop
    # -----------------------------------------------------

    for step in range(MAX_AGENT_STEPS):

        print(
            f"\n=== AGENT STEP "
            f"{step + 1}/{MAX_AGENT_STEPS} ==="
        )

        try:
            response = call_model(messages)

        except Exception as exc:
            return (
                "RepoMedic could not continue because the "
                "language model request failed.\n\n"
                f"Error: {type(exc).__name__}: {exc}"
            )

        message = response.choices[0].message

        messages.append(message)

        # -------------------------------------------------
        # No tool calls → final answer
        # -------------------------------------------------

        if not message.tool_calls:

            final_answer = (
                message.content
                or "RepoMedic returned no final diagnosis."
            )

        
            

            return final_answer

        # -------------------------------------------------
        # Execute requested tools
        # -------------------------------------------------

        for tool_call in message.tool_calls:

            raw_tool_name = tool_call.function.name

            tool_name = normalize_tool_name(
                raw_tool_name
            )

            # ---------------------------------------------
            # Reject genuinely unknown tools.
            # ---------------------------------------------

            if tool_name not in ALLOWED_TOOLS:

                result = (
                    f"Error: '{raw_tool_name}' is not an "
                    "available RepoMedic tool. "
                    "Use one of: "
                    + ", ".join(sorted(ALLOWED_TOOLS))
                )

                print("\nTool rejected:")
                print(raw_tool_name)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

                continue

            # ---------------------------------------------
            # Decode arguments
            # ---------------------------------------------

            try:
                arguments = json.loads(
                    tool_call.function.arguments
                )

            except json.JSONDecodeError as exc:

                result = (
                    "Tool call contained invalid JSON "
                    f"arguments: {exc}"
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

                continue

            print(f"\nTool: {tool_name}")
            print(f"Arguments: {arguments}")

            # ---------------------------------------------
            # Execute repository tool
            # ---------------------------------------------

            try:
                result = execute_tool(
                    repo_path=repo_path,
                    tool_name=tool_name,
                    arguments=arguments,
                )

            except KeyError as exc:

                result = (
                    "Tool execution failed because a required "
                    f"argument was missing: {exc}"
                )

            except Exception as exc:

                result = (
                    "Tool execution failed: "
                    f"{type(exc).__name__}: {exc}"
                )

            print("\nTool result:")
            print(result)

            # ---------------------------------------------
            # Return observation to model
            # ---------------------------------------------

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    return (
        "RepoMedic stopped because it reached the maximum "
        f"number of investigation steps "
        f"({MAX_AGENT_STEPS}) without producing a diagnosis."
    )