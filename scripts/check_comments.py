"""Fails on comments and docstrings that span more than one line."""

import ast
import io
import os
import pathlib
import re
import subprocess
import sys
import tokenize

CHECKED_FILES = re.compile(r"(\.(py|sh)|(^|/)Dockerfile[^/]*)$")
VENDORED = re.compile(r"^(\.agents|\.claude/skills)/")
TOOL_DIRECTIVE = re.compile(
    r"#\s*(noqa|type:|pragma|fmt:|ruff:|mypy:|pyright:|shellcheck|syntax=|escape=|check=)"
)


def comment_lines(path: str, text: str) -> list[int]:
    """Return the line numbers of standalone comments."""
    if path.endswith(".py"):
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        return [
            token.start[0]
            for token in tokens
            if token.type == tokenize.COMMENT
            and token.line.strip().startswith("#")
            and not TOOL_DIRECTIVE.match(token.string)
        ]
    return [
        number
        for number, line in enumerate(text.splitlines(), 1)
        if line.lstrip().startswith("#")
        and not line.startswith("#!")
        and not TOOL_DIRECTIVE.match(line.lstrip())
    ]


def run_starts(lines: list[int]) -> list[int]:
    """Return the first line of each run of consecutive lines."""
    return [
        line
        for index, line in enumerate(lines)
        if line + 1 in lines[index + 1 : index + 2]
        and (index == 0 or lines[index - 1] != line - 1)
    ]


def long_docstrings(text: str) -> list[int]:
    """Return the lines of docstrings that span several lines."""
    kinds = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    return [
        node.body[0].lineno
        for node in ast.walk(ast.parse(text))
        if isinstance(node, kinds)
        and ast.get_docstring(node, clean=False) is not None
        and node.body[0].end_lineno != node.body[0].lineno
    ]


os.chdir(
    subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
)
problems = []
for path in subprocess.check_output(["git", "ls-files"], text=True).splitlines():
    if not CHECKED_FILES.search(path) or VENDORED.match(path):
        continue
    if not pathlib.Path(path).exists():
        continue
    text = pathlib.Path(path).read_text()
    # comments
    problems += [
        f"{path}:{line}: comment spans several lines"
        for line in run_starts(comment_lines(path, text))
    ]
    # docstrings
    if path.endswith(".py"):
        problems += [
            f"{path}:{line}: docstring spans several lines"
            for line in long_docstrings(text)
        ]

# report
if problems:
    sys.exit("\n".join(problems) + "\nComments and docstrings must fit on one line.")
