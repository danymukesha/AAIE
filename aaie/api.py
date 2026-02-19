from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from aaie.core import Orchestrator
from aaie.graph.models import ScanResult
from aaie.graph import GraphSerializer

app = FastAPI(title="AAIE API", description="Auto Architecture Intelligence Engine API")
orchestrator = Orchestrator()


class ScanRequest(BaseModel):
    repo_path: str


class ScanResponse(BaseModel):
    scan_id: int
    repo_id: str
    nodes_count: int
    edges_count: int
    findings_count: int


class GraphResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]


class FindingsResponse(BaseModel):
    scan_id: int
    findings: list[dict]


@app.post("/scan", response_model=ScanResponse)
async def scan_repo(request: ScanRequest) -> ScanResponse:
    """Scan a repository and return the results."""
    repo_path = Path(request.repo_path)
    
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail="Repository path not found")
    
    result = orchestrator.scan(repo_path)
    scan_id = orchestrator.save_result(repo_path, result)
    
    return ScanResponse(
        scan_id=scan_id,
        repo_id=result.repo_id,
        nodes_count=len(result.nodes),
        edges_count=len(result.edges),
        findings_count=len(result.findings)
    )


@app.get("/report/{scan_id}")
async def get_report(scan_id: int) -> dict:
    """Get a detailed report for a scan."""
    result = orchestrator.get_result(scan_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return {
        "scan_id": scan_id,
        "repo_id": result.repo_id,
        "nodes": [
            {
                "id": n.id,
                "name": n.name,
                "type": n.type,
                "metadata": n.metadata
            }
            for n in result.nodes
        ],
        "edges": [
            {
                "source": e.source,
                "target": e.target,
                "type": e.type,
                "metadata": e.metadata
            }
            for e in result.edges
        ],
        "findings": [
            {
                "rule_id": f.rule_id,
                "severity": f.severity,
                "message": f.message,
                "node_ids": f.node_ids,
                "metadata": f.metadata
            }
            for f in result.findings
        ]
    }


@app.get("/graph/{scan_id}", response_model=GraphResponse)
async def get_graph(scan_id: int) -> GraphResponse:
    """Get the graph for a scan."""
    result = orchestrator.get_result(scan_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    from aaie.graph.graph_builder import GraphBuilder
    builder = GraphBuilder()
    builder.add_nodes_from(result.nodes)
    builder.add_edges_from(result.edges)
    
    return GraphResponse(
        nodes=[
            {
                "id": n.id,
                "name": n.name,
                "type": n.type,
                "metadata": n.metadata
            }
            for n in result.nodes
        ],
        edges=[
            {
                "source": e.source,
                "target": e.target,
                "type": e.type,
                "metadata": e.metadata
            }
            for e in result.edges
        ]
    )


@app.get("/findings/{scan_id}", response_model=FindingsResponse)
async def get_findings(scan_id: int) -> FindingsResponse:
    """Get findings for a scan."""
    result = orchestrator.get_result(scan_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return FindingsResponse(
        scan_id=scan_id,
        findings=[
            {
                "rule_id": f.rule_id,
                "severity": f.severity,
                "message": f.message,
                "node_ids": f.node_ids,
                "metadata": f.metadata
            }
            for f in result.findings
        ]
    )


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}
