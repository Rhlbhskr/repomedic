# RepoMedic

**RepoMedic** is an agentic codebase debugging assistant that autonomously investigates bugs inside local software repositories.

Instead of sending an entire codebase to an LLM in a single prompt, RepoMedic gives the model a controlled set of repository-inspection tools. The agent decides which tools to use, gathers evidence iteratively, updates its investigation, and produces an evidence-backed debugging report.

## Features

- Autonomous multi-step bug investigation
- Repository tree inspection
- Codebase-wide source search
- Full file inspection with line numbers
- Targeted code snippet retrieval
- Evidence-backed root-cause analysis
- Minimal patch generation
- Regression-test generation
- Read-only repository access
- Repository path sandboxing
- Tool-name whitelisting
- Recovery from malformed model-generated tool calls
- Maximum-step guard against runaway agent loops

## Architecture

```text
                        Bug Report
                            |
                            v
                  +-------------------+
                  | RepoMedic Agent   |
                  +---------+---------+
                            |
                     chooses action
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
   get_file_tree()    search_code()      read_file()
                                              |
                                      get_file_snippet()
          |                 |                 |
          +-----------------+-----------------+
                            |
                            v
                     Tool Observation
                            |
                            v
                  Agent Updates Hypothesis
                            |
                     Enough Evidence?
                       /          \
                     No            Yes
                     |              |
                     +---- loop ----+
                                    |
                                    v
                              Root Cause
                              Evidence
                              Proposed Fix
                              Regression Test
                              Confidence
```

## How It Works

RepoMedic implements a custom Python agent loop.

The language model cannot directly access the filesystem. Instead, it is given four controlled tools:

```text
get_file_tree()
search_code()
read_file()
get_file_snippet()
```

For every debugging request, the model decides which tool to call next.

A typical investigation looks like:

```text
Bug report
    |
    v
get_file_tree()
    |
    v
read_file("orders.py")
    |
    v
read_file("pricing.py")
    |
    v
read_file("config.py")
    |
    v
Root-cause diagnosis
```

Each tool result is returned to the model as a new observation, allowing the agent to continue investigating until it has enough evidence to produce a final report.

## Example

### Bug Report

```text
Orders with discounts are being charged too much tax.

A product costing 100 with quantity 2 and a discount of 50
returns 160, but the expected total is 157.50.
```

RepoMedic autonomously follows the order and pricing flow and discovers:

```python
subtotal = price * quantity
discounted_total = subtotal - discount

tax = subtotal * TAX_RATE
```

The tax is being calculated using the original subtotal rather than the discounted amount.

RepoMedic recommends:

```python
tax = discounted_total * TAX_RATE
```

It also generates a regression test covering both discounted and non-discounted orders.

## Agent Tools

### `get_file_tree`

Returns the repository structure so the agent can understand how the project is organized.

### `search_code`

Searches repository files for functions, variables, classes, error messages, routes, and other source-code text.

### `read_file`

Reads a complete file with line numbers so conclusions can reference concrete evidence.

### `get_file_snippet`

Retrieves only a specified range of lines from a file, reducing unnecessary context for larger files.

## Reliability and Safety

RepoMedic V1 is intentionally read-only.

The agent can:

```text
Inspect files
Search source code
Read selected code sections
Generate debugging recommendations
Generate proposed patches
Generate regression tests
```

The agent cannot:

```text
Modify repository files
Execute arbitrary shell commands
Apply generated patches
Run generated tests
```

Repository paths are restricted to the selected repository root.

Tool names are also validated against an explicit whitelist before local execution.

Because LLM-generated tool calls can occasionally be malformed, RepoMedic includes a normalization layer that safely recovers known tool names while rejecting unknown tools.

A maximum investigation-step limit prevents runaway agent loops.

## Tech Stack

- Python
- Groq API
- GPT-OSS
- LLM function/tool calling
- Rich CLI
- python-dotenv

## Project Structure

```text
repomedic/
|
├── main.py
├── agent.py
├── tools.py
├── prompts.py
├── config.py
├── schemas.py
|
├── sample_repo/
│   ├── app.py
│   ├── auth.py
│   ├── config.py
│   ├── orders.py
│   ├── pricing.py
│   └── users.py
|
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

Clone the repository:

```bash
git clone https://github.com/Rhlbhskr/repomedic.git
cd repomedic
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file based on `.env.example`:

```env
GROQ_API_KEY=your_groq_api_key_here
```

## Usage

Run RepoMedic against a repository:

```bash
python main.py --repo ./sample_repo
```

RepoMedic will ask:

```text
Describe the bug:
```

Enter a natural-language description such as:

```text
Orders with discounts are being charged too much tax.
```

The agent will investigate the repository and produce:

```text
ROOT CAUSE
EVIDENCE
PROPOSED FIX
REGRESSION TEST
CONFIDENCE
```

## Limitations

RepoMedic V1 does not execute generated patches or regression tests.

It currently performs text-based source-code inspection rather than AST-aware or semantic code navigation.

Large repositories may require more advanced context management, indexing, and semantic code retrieval.

The generated diagnosis and patch should be reviewed by a developer before being applied.

## Future Improvements

Potential extensions include:

- Automated patch application
- Sandboxed test execution
- Patch verification and rollback
- Git integration
- GitHub Issues integration
- AST-aware code navigation
- Tree-sitter integration
- Semantic code search
- Repository indexing
- Human approval before source-code modification

## Disclaimer

RepoMedic uses an LLM to generate debugging recommendations. Suggested fixes and tests should be reviewed before being applied to production code.
