"""rustdl_py — Python wrapper for rustdl OWL 2 DL reasoner.

rustdl is a Rust-native OWL reasoner (cargo install owl-dl-cli).
This package wraps the CLI as a Python API for zero-Java OWL reasoning.

Install: pip install rustdl-py
Requires: rustdl binary in PATH (cargo install owl-dl-cli)

Usage:
    >>> import rustdl_py
    >>> rustdl_py.classify("ontology.ofn")
    >>> rustdl_py.is_consistent("ontology.ofn")
    >>> rustdl_py.realize("ontology.ofn")
"""

import json as _json
import os as _os
import subprocess as _subprocess
from dataclasses import dataclass as _dataclass, field as _field
from pathlib import Path as _Path
from typing import Optional as _Optional

__version__ = "0.1.0"
__all__ = [
    "classify",
    "is_consistent",
    "realize",
    "explain",
    "is_satisfiable",
    "get_instances",
    "ClassificationResult",
    "RealizationResult",
    "RustdlError",
    "RustdlNotFound",
]


class RustdlError(Exception):
    """rustdl execution error."""
    pass


class RustdlNotFound(RustdlError):
    """rustdl binary not found."""
    pass


@_dataclass
class ClassificationResult:
    """Result of rustdl classify."""

    classes: int = 0
    mode: str = ""
    fragment: str = ""
    subsumptions: list[tuple[str, str]] = _field(default_factory=list)
    saturation_count: int = 0
    tableau_count: int = 0
    wall_ms: int = 0
    raw_stderr: str = ""

    @property
    def pure_el(self) -> bool:
        return self.tableau_count == 0


@_dataclass
class RealizationResult:
    """Result of rustdl realize."""

    types: dict[str, list[str]] = _field(default_factory=dict)

    def get_types(self, individual: str) -> list[str]:
        return self.types.get(individual, [])


def _find_rustdl() -> str:
    """Find rustdl binary in PATH or common locations."""
    # Check PATH
    result = _subprocess.run(["which", "rustdl"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()

    # Check cargo home
    cargo_home = _os.environ.get("CARGO_HOME", _os.path.expanduser("~/.cargo"))
    path = _os.path.join(cargo_home, "bin", "rustdl")
    if _os.path.isfile(path):
        return path

    raise RustdlNotFound(
        "rustdl not found. Install with: cargo install owl-dl-cli"
    )


def classify(ontology_path: str) -> ClassificationResult:
    """Compute full class hierarchy.

    Args:
        ontology_path: Path to OWL Functional Syntax (.ofn) file.

    Returns:
        ClassificationResult with subsumption pairs and stats.
    """
    rustdl = _find_rustdl()
    proc = _subprocess.run(
        [rustdl, "classify", ontology_path],
        capture_output=True,
        text=True,
        timeout=120,
    )

    result = ClassificationResult()
    result.raw_stderr = proc.stderr

    # Parse stderr for stats
    for line in proc.stderr.splitlines():
        line = line.strip()
        if line.startswith("# classes:"):
            result.classes = int(line.split(":")[1].strip())
        elif line.startswith("# mode:"):
            result.mode = line.split(":")[1].strip()
        elif line.startswith("# fragment:"):
            result.fragment = line.split(":")[1].strip()
        elif "subsumption:" in line:
            parts = line.split()
            for p in parts:
                if p.startswith("saturation="):
                    result.saturation_count = int(p.split("=")[1])
                elif p.startswith("tableau="):
                    result.tableau_count = int(p.split("=")[1])

    # Parse stdout for subsumption pairs
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            result.subsumptions.append((parts[1], parts[2]))

    if proc.returncode != 0:
        raise RustdlError(f"rustdl classify failed: {proc.stderr}")

    return result


def is_consistent(ontology_path: str) -> bool:
    """Check ontology consistency."""
    rustdl = _find_rustdl()
    proc = _subprocess.run(
        [rustdl, "consistent", ontology_path],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RustdlError(f"rustdl consistent failed: {proc.stderr}")
    return "consistent" in proc.stdout.lower()


def realize(ontology_path: str) -> RealizationResult:
    """Compute per-individual most-specific entailed types."""
    rustdl = _find_rustdl()
    proc = _subprocess.run(
        [rustdl, "realize", ontology_path],
        capture_output=True,
        text=True,
        timeout=120,
    )

    result = RealizationResult()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            result.types[parts[0]] = parts[1:]

    if proc.returncode != 0:
        raise RustdlError(f"rustdl realize failed: {proc.stderr}")

    return result


def explain(ontology_path: str, subclass: str, superclass: str) -> dict:
    """Explain whether subclass ⊑ superclass is entailed."""
    rustdl = _find_rustdl()
    proc = _subprocess.run(
        [rustdl, "explain", ontology_path, subclass, superclass],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RustdlError(f"rustdl explain failed: {proc.stderr}")
    return {"entailed": "yes" in proc.stdout.lower(), "detail": proc.stdout.strip()}


def is_satisfiable(ontology_path: str, class_iri: str) -> bool:
    """Check if a class is satisfiable."""
    rustdl = _find_rustdl()
    proc = _subprocess.run(
        [rustdl, "sat", ontology_path, class_iri],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        return False  # unsat returns non-zero
    return "sat" in proc.stdout.lower()


def get_instances(ontology_path: str, class_iri: str) -> list[str]:
    """Get all individuals provably in a class."""
    rustdl = _find_rustdl()
    proc = _subprocess.run(
        [rustdl, "instances", ontology_path, class_iri],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RustdlError(f"rustdl instances failed: {proc.stderr}")
    return [l.strip() for l in proc.stdout.splitlines() if l.strip()]
