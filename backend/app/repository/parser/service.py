import ast
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

PYTHON_EXT = {".py"}
TS_EXT = {".ts", ".tsx", ".mts", ".cts"}
JS_EXT = {".js", ".jsx", ".mjs", ".cjs"}


class SymbolParser:
    def parse(self, filepath: str, content: str, language: str) -> list[dict]:
        symbols = []
        if language == "python":
            symbols = self._parse_python(filepath, content)
        elif language in ("typescript", "javascript"):
            symbols = self._parse_ts_js(filepath, content, language)
        else:
            symbols = self._parse_generic(filepath, content, language)
        return symbols

    def _parse_python(self, filepath: str, content: str) -> list[dict]:
        symbols = []
        try:
            tree = ast.parse(content, filename=filepath)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    doc = ast.get_docstring(node)
                    decorators = [self._node_name(d) for d in node.decorator_list]
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    symbols.append({
                        "name": node.name, "symbol_type": "class", "line_start": node.lineno,
                        "line_end": getattr(node, "end_lineno", node.lineno),
                        "column_start": node.col_offset, "column_end": getattr(node, "end_col_offset", node.col_offset),
                        "signature": f"class {node.name}(...)", "docstring": doc,
                        "decorators": decorators, "parameters": [], "visibility": "public",
                        "children": methods, "complexity": self._estimate_complexity(node),
                    })
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if isinstance(node.parent, ast.ClassDef) if hasattr(node, "parent") else False:
                        continue
                    doc = ast.get_docstring(node)
                    params = [{"name": a.arg, "annotation": self._annotation_name(a.annotation)} for a in node.args.args]
                    decorators = [self._node_name(d) for d in node.decorator_list]
                    symbols.append({
                        "name": node.name, "symbol_type": "function", "line_start": node.lineno,
                        "line_end": getattr(node, "end_lineno", node.lineno),
                        "column_start": node.col_offset, "column_end": getattr(node, "end_col_offset", node.col_offset),
                        "signature": f"def {node.name}({', '.join(a.arg for a in node.args.args)})",
                        "docstring": doc, "decorators": decorators, "parameters": params,
                        "visibility": "public", "complexity": self._estimate_complexity(node),
                    })
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            symbols.append({
                                "name": target.id, "symbol_type": "variable", "line_start": node.lineno,
                                "line_end": getattr(node, "end_lineno", node.lineno),
                                "signature": f"{target.id} = ...",
                            })
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({"source": alias.name, "imported_name": alias.asname or alias.name, "line": node.lineno, "is_relative": False})
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append({"source": module, "imported_name": alias.asname or alias.name, "line": node.lineno, "is_relative": node.level > 0})
            return symbols + [{"symbol_type": "_imports", "imports": imports}]
        except SyntaxError as e:
            logger.debug(f"Parse error {filepath}: {e}")
            return symbols

    def _parse_ts_js(self, filepath: str, content: str, language: str) -> list[dict]:
        symbols = []
        for m in re.finditer(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(", content):
            symbols.append({"name": m.group(1), "symbol_type": "function", "line_start": content[:m.start()].count("\n") + 1})
        for m in re.finditer(r"(?:export\s+)?class\s+(\w+)", content):
            symbols.append({"name": m.group(1), "symbol_type": "class", "line_start": content[:m.start()].count("\n") + 1})
        for m in re.finditer(r"(?:export\s+)?(?:const|let|var)\s+(\w+)", content):
            next_chars = content[m.end():m.end()+10]
            if "=>" in next_chars or "function" in next_chars:
                symbols.append({"name": m.group(1), "symbol_type": "function", "line_start": content[:m.start()].count("\n") + 1})
            else:
                symbols.append({"name": m.group(1), "symbol_type": "variable", "line_start": content[:m.start()].count("\n") + 1})
        for m in re.finditer(r"(?:export\s+)?interface\s+(\w+)", content):
            symbols.append({"name": m.group(1), "symbol_type": "interface", "line_start": content[:m.start()].count("\n") + 1})
        for m in re.finditer(r"(?:export\s+)?type\s+(\w+)\s*=", content):
            symbols.append({"name": m.group(1), "symbol_type": "type", "line_start": content[:m.start()].count("\n") + 1})
        imports = []
        for m in re.finditer(r"(?:import|require)\s+.*?from\s+['\"]([^'\"]+)['\"]", content):
            imports.append({"source": m.group(1), "imported_name": "", "line": content[:m.start()].count("\n") + 1, "is_relative": m.group(1).startswith(".")})
        for m in re.finditer(r"import\s+['\"]([^'\"]+)['\"]", content):
            imports.append({"source": m.group(1), "imported_name": "", "line": content[:m.start()].count("\n") + 1, "is_relative": m.group(1).startswith(".")})
        symbols.append({"symbol_type": "_imports", "imports": imports})
        return symbols

    def _parse_generic(self, filepath: str, content: str, language: str) -> list[dict]:
        symbols = []
        for m in re.finditer(r"^(?:def|function|fun|func|sub)\s+(\w+)", content, re.MULTILINE):
            symbols.append({"name": m.group(1), "symbol_type": "function", "line_start": content[:m.start()].count("\n") + 1})
        for m in re.finditer(r"^(?:class|struct|trait|module)\s+(\w+)", content, re.MULTILINE):
            symbols.append({"name": m.group(1), "symbol_type": "class", "line_start": content[:m.start()].count("\n") + 1})
        return symbols

    def _estimate_complexity(self, node: ast.AST) -> float:
        score = 1.0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.AsyncFor)):
                score += 1
            elif isinstance(child, (ast.BoolOp,)):
                score += 0.5
        return score

    def _node_name(self, node: ast.AST | None) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._node_name(node.value)}.{node.attr}"
        if isinstance(node, ast.Call):
            return self._node_name(node.func)
        return ""

    def _annotation_name(self, node: ast.AST | None) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Subscript):
            return f"{self._node_name(node.value)}[...]"
        return ""

    def extract_imports(self, content: str, language: str) -> list[dict]:
        symbols = self.parse("", content, language)
        for s in symbols:
            if s.get("symbol_type") == "_imports":
                return s.get("imports", [])
        return []

    def extract_comments(self, content: str, language: str) -> list[dict]:
        comments = []
        if language == "python":
            for i, line in enumerate(content.split("\n"), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    comments.append({"text": stripped[1:].strip(), "line": i, "type": "line"})
                elif '"""' in stripped or "'''" in stripped:
                    comments.append({"text": stripped, "line": i, "type": "docstring"})
        elif language in ("typescript", "javascript"):
            for i, line in enumerate(content.split("\n"), 1):
                stripped = line.strip()
                if stripped.startswith("//"):
                    comments.append({"text": stripped[2:].strip(), "line": i, "type": "line"})
                elif stripped.startswith("/*") and "*/" in stripped:
                    comments.append({"text": stripped[2:-2].strip(), "line": i, "type": "block"})
        return comments
