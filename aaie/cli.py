import typer
from pathlib import Path
from typing import Optional
from aaie.core import Orchestrator, Config

app = typer.Typer(help="Auto Architecture Intelligence Engine (AAIE)")


@app.command()
def scan(
    repo_path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True, help="Path to the repository to scan"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output path for the report"),
    config: Optional[Path] = typer.Option(None, "-c", "--config", help="Path to config file")
) -> None:
    """Scan a repository and generate an architecture analysis."""
    orchestrator = Orchestrator()
    
    typer.echo(f"Scanning repository: {repo_path}")
    result = orchestrator.scan(repo_path)
    
    typer.echo(f"Scan complete!")
    typer.echo(f"  Nodes: {len(result.nodes)}")
    typer.echo(f"  Edges: {len(result.edges)}")
    typer.echo(f"  Findings: {len(result.findings)}")
    
    scan_id = orchestrator.save_result(repo_path, result)
    typer.echo(f"  Saved as scan ID: {scan_id}")
    
    if output:
        orchestrator.generate_report(result, output)
        typer.echo(f"Report saved to: {output}")


@app.command()
def report(
    scan_id: int = typer.Argument(..., help="Scan ID to generate report from"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output path for the report")
) -> None:
    """Generate a report from a previous scan."""
    orchestrator = Orchestrator()
    
    result = orchestrator.get_result(scan_id)
    if result is None:
        typer.echo(f"Scan {scan_id} not found", err=True)
        raise typer.Exit(1)
    
    if output:
        orchestrator.generate_report(result, output)
        typer.echo(f"Report saved to: {output}")
    else:
        typer.echo(f"Nodes: {len(result.nodes)}")
        typer.echo(f"Edges: {len(result.edges)}")
        typer.echo(f"Findings:")
        for finding in result.findings:
            typer.echo(f"  [{finding.severity}] {finding.rule_id}: {finding.message}")


@app.command()
def list_repos() -> None:
    """List all scanned repositories."""
    orchestrator = Orchestrator()
    repos = orchestrator.list_repositories()
    
    if not repos:
        typer.echo("No repositories scanned yet")
        return
    
    for repo in repos:
        typer.echo(f"  {repo['id']}: {repo['name']} ({repo['path']}) - Last scanned: {repo.get('last_scanned', 'Never')}")


@app.command()
def diff(
    repo_path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True, help="Path to the repository"),
    run1: int = typer.Option(..., "--run1", help="First scan ID to compare"),
    run2: int = typer.Option(..., "--run2", help="Second scan ID to compare"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output path for the diff report")
) -> None:
    """Compare two scans and generate a diff report."""
    orchestrator = Orchestrator()
    
    result1 = orchestrator.get_result(run1)
    result2 = orchestrator.get_result(run2)
    
    if result1 is None:
        typer.echo(f"Scan {run1} not found", err=True)
        raise typer.Exit(1)
    
    if result2 is None:
        typer.echo(f"Scan {run2} not found", err=True)
        raise typer.Exit(1)
    
    from aaie.reports import MarkdownGenerator
    md_gen = MarkdownGenerator()
    
    if output:
        md_gen.generate_diff_report(result1, result2, output)
        typer.echo(f"Diff report saved to: {output}")
    else:
        typer.echo("Diff Report:")
        old_nodes = {n.id for n in result1.nodes}
        new_nodes = {n.id for n in result2.nodes}
        typer.echo(f"  Added nodes: {len(new_nodes - old_nodes)}")
        typer.echo(f"  Removed nodes: {len(old_nodes - new_nodes)}")


if __name__ == "__main__":
    app()
