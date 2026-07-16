# rustdl-py

Python wrapper for [rustdl](https://github.com/KRR-Oxford/rustdl) — a Rust-native OWL 2 DL reasoner.

Zero Java. Zero C bindings. Just `cargo install owl-dl-cli` + `pip install rustdl-py`.

## Install

```bash
# 1. Install the reasoner
cargo install owl-dl-cli

# 2. Install the Python wrapper
pip install rustdl-py
```

## Quick Start

```python
import rustdl_py

# Check consistency
consistent = rustdl_py.is_consistent("my_ontology.ofn")

# Classify (compute class hierarchy)
result = rustdl_py.classify("my_ontology.ofn")
print(f"Classes: {result.classes}, Mode: {result.mode}")
for subclass, superclass in result.subsumptions:
    print(f"  {subclass} ⊑ {superclass}")

# Realize (compute individual types)
r = rustdl_py.realize("my_ontology.ofn")
for individual, types in r.types.items():
    print(f"{individual}: {', '.join(types)}")

# Explain a subsumption
explanation = rustdl_py.explain("my_ontology.ofn", ":Foo", ":Bar")
print(explanation["detail"])
```

## API

| Function | Description |
|----------|-------------|
| `classify(ontology)` | Compute full class hierarchy |
| `is_consistent(ontology)` | Check ontology consistency |
| `realize(ontology)` | Compute individual → type mapping |
| `explain(ontology, sub, sup)` | Explain subsumption entailment |
| `is_satisfiable(ontology, class)` | Check class satisfiability |
| `get_instances(ontology, class)` | List individuals of a class |

Input must be OWL Functional Syntax (`.ofn`). Use `export_to_owl.py --format ofn` to convert from Turtle.

## Requirements

- Python ≥ 3.9
- `rustdl` in PATH (install via `cargo install owl-dl-cli`)

## License

MIT
