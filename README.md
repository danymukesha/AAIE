# The AAIE (Auto Architecture Intelligence Engine)

The project structure

```
aaie/
├── __init__.py, main.py, cli.py, api.py
├── core/         - Orchestrator, Config
├── parsers/      - Python, Terraform, Docker, K8s, Package parsers
├── graph/        - NetworkX DiGraph builder, models, serializer
├── rules/        - Circular dependency, SPF, secret detector
├── storage/      - SQLite database, repository store
└── reports/      - Markdown & diagram generators
```

The fundamental features

- Parsers: Python (AST), Terraform, Docker, Kubernetes, npm/pip
- Graph: NetworkX DiGraph with JSON/GEXF/DOT export
- Rules: Circular dependency detection, single point of failure, secret scanning
- Storage: SQLite with historical scans and diff support
- CLI: aaie scan <path>, aaie report <scan_id>, aaie diff
- API: FastAPI with /scan, /report, /graph, /findings endpoints

Usage 

```python
# CLI
python -m aaie.cli scan /path/to/repo

# API
python -m uvicorn aaie.api:app --reload
```

All modules are typed and the implementation is deterministic.
