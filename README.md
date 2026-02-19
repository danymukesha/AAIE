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
pip install -r requirements.txt
python -m uvicorn aaie.api:app --reload # !!! currently under-development !!!
# at the moment you should be able see the exposed apis on an interactive 
@ Swagger UI, which Uvicorn's running on http://127.0.0.1:8000
```

All modules are typed and the implementation is deterministic.

## The problem: "Invisible architecture and fragmented knowledge""

In many AI, Cloud, and Data teams, especially in finance and regulated
sectors—teams face a recurring issue: the system architecture is invisible.

Daily reality: microservices evolve, Terraform changes infra, CI/CD pipelines
shift, data schemas mutate, AI models update. Documentation? Outdated.
Diagrams? Manual and obsolete. Knowledge? Scattered across Slack, Jira, Git,
and people’s heads.

The result: onboarding takes months, incidents take hours to debug, compliance
struggles, and architecture drift goes unnoticed. Even with Kubernetes,
Terraform, Snowflake, and ML pipelines, teams lack a continuously updated view
of their systems.

## The solution: "Auto architecture intelligence"

I original started with creating a local developer tool that:

- 1st, scans codebases, Terraform, Docker, and Kubernetes configs
- 2nd, maps service dependencies and communication
- 3rd, detects risk zones and undocumented flows
- 4th, generates living architecture diagrams
- 5th, suggests improvements

Think of: a “Copilot” for system architecture visibility, focused on
infrastructure, services, and data flows—not just code.

## Why would this matter then?

Currently, engineers manually update diagrams, rely on tribal knowledge, and
spend hours debugging cross-service issues. There is no tool that continuously
analyzes architecture, flags knowledge silos, or detects drift automatically.

For regulated industries, this gap is a major source of inefficiency and risk.

Check here for dev. mode installation: [DEV INSTALL document](./INSTALL.md)!