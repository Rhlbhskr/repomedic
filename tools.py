from pathlib import Path


IGNORED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
}


def get_file_tree(repo_path: str) -> str:
    """
    Return a readable file tree for a repository.
    """

    root = Path(repo_path).resolve()

    if not root.exists():
        return f"Error: Repository path does not exist: {root}"

    if not root.is_dir():
        return f"Error: Repository path is not a directory: {root}"

    lines = [root.name + "/"]

    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)

        if any(part in IGNORED_DIRS for part in relative.parts):
            continue

        depth = len(relative.parts)
        indent = "    " * depth

        if path.is_dir():
            lines.append(f"{indent}{path.name}/")
        else:
            lines.append(f"{indent}{path.name}")

    return "\n".join(lines)


def read_file(repo_path: str, file_path: str) -> str:
    """
    Read an entire file from the repository.
    """

    root = Path(repo_path).resolve()
    target = (root / file_path).resolve()

    # Security check:
    # prevent access outside repository
    try:
        target.relative_to(root)
    except ValueError:
        return "Error: Access outside repository is not allowed."

    if not target.exists():
        return f"Error: File does not exist: {file_path}"

    if not target.is_file():
        return f"Error: Not a file: {file_path}"

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Error: File is not a readable UTF-8 text file: {file_path}"

    numbered_lines = []

    for number, line in enumerate(content.splitlines(), start=1):
        numbered_lines.append(f"{number:4}: {line}")

    return "\n".join(numbered_lines)


def get_file_snippet(
    repo_path: str,
    file_path: str,
    start_line: int,
    end_line: int
) -> str:
    """
    Read only a specified range of lines from a file.
    """

    root = Path(repo_path).resolve()
    target = (root / file_path).resolve()

    try:
        target.relative_to(root)
    except ValueError:
        return "Error: Access outside repository is not allowed."

    if not target.exists():
        return f"Error: File does not exist: {file_path}"

    if not target.is_file():
        return f"Error: Not a file: {file_path}"

    try:
        lines = target.read_text(
            encoding="utf-8"
        ).splitlines()
    except UnicodeDecodeError:
        return f"Error: File is not readable text: {file_path}"

    if start_line < 1:
        start_line = 1

    if end_line > len(lines):
        end_line = len(lines)

    if start_line > end_line:
        return "Error: start_line must be <= end_line."

    output = []

    for index in range(start_line - 1, end_line):
        output.append(
            f"{index + 1:4}: {lines[index]}"
        )

    return "\n".join(output)


def search_code(repo_path: str, query: str) -> str:
    """
    Search text files in the repository for a query.
    """

    root = Path(repo_path).resolve()

    if not root.exists():
        return f"Error: Repository does not exist: {root}"

    results = []

    for path in root.rglob("*"):

        if not path.is_file():
            continue

        relative = path.relative_to(root)

        if any(part in IGNORED_DIRS for part in relative.parts):
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        for line_number, line in enumerate(
            content.splitlines(),
            start=1
        ):
            if query.lower() in line.lower():
                results.append(
                    f"{relative}:{line_number}: {line.strip()}"
                )

    if not results:
        return f"No matches found for: {query}"

    # prevent enormous responses
    return "\n".join(results[:50])