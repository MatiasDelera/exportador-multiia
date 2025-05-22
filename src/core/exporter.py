"""
Core ▸ exporter.py
Recorre el árbol de archivos, aplica filtros y genera
un archivo .txt, .md o .json con estructura + contenido.
Incluye:
• Carpeta txt_export ignorada para evitar export recursion
• Puntuación de archivos clave para ordenar (opcional)
"""

from __future__ import annotations
import os
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Iterable


# --- Configuración global -------------------------------------------------
IGNORED_DIRS: set[str] = {
    ".git",
    "build",
    ".dart_tool",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "txt_export",
}
DEFAULT_EXTS: set[str] = {
    ".dart",
    ".yaml",
    ".json",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".py",
    ".md",
    ".txt",
}

# Archivos con “peso” para priorizar (mayor → primero)
KEY_FILES_WEIGHT = {
    "README.md": 10,
    "readme.md": 10,
    "package.json": 9,
    "requirements.txt": 9,
    "pubspec.yaml": 9,
    "pyproject.toml": 9,
}


# --- Funciones auxiliares -------------------------------------------------
def _is_relevant(fname: str, exts: set[str]) -> bool:
    return any(fname.lower().endswith(e) for e in exts)


def _file_weight(fname: str) -> int:
    """Pondera archivos clave para mostrarlos primero en el .txt."""
    return KEY_FILES_WEIGHT.get(fname.lower(), 0)


# --- Recorre proyecto -----------------------------------------------------
def walk_project(
    root: str,
    exts: set[str],
) -> tuple[list[str], list[str]]:
    """
    Devuelve (estructura, contenido)
    • estructura: lista de líneas tree-like
    • contenido : lista con bloques   //// path \n <filetext>
    """
    struct: list[str] = []
    content: list[str] = []

    # Para agrupar archivos clave arriba
    file_bucket: dict[int, list[tuple[str, str, str]]] = defaultdict(list)

    for dpath, dnames, fnames in os.walk(root):
        dnames[:] = [d for d in dnames if d not in IGNORED_DIRS]

        level = dpath.replace(root, "").count(os.sep)
        indent = "│   " * level
        struct.append(f"{indent}├── {os.path.basename(dpath)}/")

        # Ordena por peso y alfabético
        fnames_sorted = sorted(
            fnames,
            key=lambda f: (-_file_weight(f), f.lower()),
        )
        for f in fnames_sorted:
            if not _is_relevant(f, exts):
                continue
            fpath = os.path.join(dpath, f)
            rel = os.path.relpath(fpath, root)
            struct.append(f"{indent}│   └── {f}")

            try:
                with open(fpath, "r", encoding="utf-8") as fh:
                    txt = fh.read()
            except Exception as exc:
                txt = f"// Error leyendo {rel}: {exc}"

            content.append(f"\n//// {rel}\n")
            content.append(txt)

    return struct, content


# --- Exportador principal -------------------------------------------------
class Exporter:
    """
    Exporta la estructura + contenido a .txt / .md / .json
    include_content=False ⇒ sólo estructura (útil para IA tokens)
    """

    def __init__(
        self,
        root: str | Path,
        exts: Iterable[str] | None = None,
        include_content: bool = True,
        fmt: str = "txt",
    ):
        self.root = str(root)
        self.exts = set(exts) if exts else DEFAULT_EXTS
        self.include = include_content
        self.fmt = fmt.lower()

    # ---- cálculo básico de tokens ----
    @staticmethod
    def estimate_tokens(text: str) -> int:
        # heurística muy simple: 1 token ≈ 4 caracteres en inglés
        return max(1, len(text) // 4)

    def export(self) -> str:
        struct, cont = walk_project(self.root, self.exts)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = Path(self.root).name
        out_dir = Path(self.root) / "txt_export"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f"{name}_{ts}.{self.fmt}"

        if self.fmt == "json":
            payload = {
                "project": name,
                "export_date": ts,
                "structure": struct,
                "content": cont if self.include else [],
            }
            text_to_count = json.dumps(payload, ensure_ascii=False)
            payload["token_estimate"] = self.estimate_tokens(text_to_count)
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")

        else:  # txt / md
            header = [
                f"Project: {name}",
                f"Export date: {ts}",
                f"Include content: {self.include}",
                "==============================",
                "",
                "===== STRUCTURE =====",
                "",
            ]
            body = "\n".join(struct)
            pieces = header + [body]

            if self.include:
                pieces += ["", "===== CONTENT =====", "", *cont]

            full_text = "\n".join(pieces)
            token_est = self.estimate_tokens(full_text)
            full_text = f"Token estimate: {token_est}\n\n" + full_text
            out_path.write_text(full_text, "utf-8")

        return str(out_path)
