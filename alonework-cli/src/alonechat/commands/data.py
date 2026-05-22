"""
data命令组 - 数据收集与管理

提供交互数据收集、质量评估、导出等功能：
- data collect: 收集当前会话数据
- data list: 列出已收集的数据
- data export: 导出训练数据
- data quality: 评估数据质量
- data stats: 数据统计
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from alonechat.data.collector import DataCollector
from alonechat.data.quality import QualityEvaluator, QualityWeights
from alonechat.data.exporter import DataExporter
from alonechat.data.trajectory import TrajectoryRecorder

console = Console()


def get_data_dir() -> Path:
    data_dir = Path.home() / ".alonechat" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@click.group(name="data")
def data_commands():
    """数据收集与管理命令 / Data collection and management"""
    pass


@data_commands.command(name="collect")
@click.option("--session-id", help="指定会话ID / Session ID")
@click.option("--output-dir", help="输出目录 / Output directory", type=click.Path())
@click.option("--format", "output_format", type=click.Choice(["json", "jsonl"]), default="jsonl")
@click.option("--include-metadata", is_flag=True, help="包含元数据 / Include metadata")
@click.pass_context
def collect_data(
    ctx: click.Context,
    session_id: Optional[str],
    output_dir: Optional[str],
    output_format: str,
    include_metadata: bool,
) -> None:
    """收集当前会话的交互数据 / Collect interaction data from current session"""
    console.print("[bold cyan]正在收集交互数据... / Collecting interaction data...[/bold cyan]")
    
    data_dir = Path(output_dir) if output_dir else get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    
    collector = DataCollector()
    
    if session_id:
        session = collector.get_session(session_id)
        if not session:
            console.print(f"[red]会话未找到 / Session not found: {session_id}[/red]")
            return
    
    sessions = collector.list_sessions()
    
    if not sessions:
        console.print("[yellow]没有找到可收集的数据 / No data to collect[/yellow]")
        return
    
    console.print(f"[dim]找到 {len(sessions)} 个会话 / Found {len(sessions)} sessions[/dim]")
    
    for session in sessions:
        session_id = session["id"]
        output_file = data_dir / f"session_{session_id}.{output_format}"
        
        try:
            if output_format == "jsonl":
                data = collector.export_session_jsonl(session_id, include_metadata)
                with open(output_file, "w", encoding="utf-8") as f:
                    for item in data:
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")
            else:
                data = collector.export_session_json(session_id, include_metadata)
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            console.print(f"[green]已导出 / Exported: {output_file}[/green]")
            
        except Exception as e:
            console.print(f"[red]导出失败 / Export failed: {e}[/red]")
    
    console.print(f"[bold green]数据收集完成 / Data collection complete[/bold green]")


@data_commands.command(name="list")
@click.option("--limit", default=20, help="最大显示数量 / Max items to show")
@click.option("--sort-by", type=click.Choice(["time", "quality", "steps"]), default="time")
@click.pass_context
def list_data(
    ctx: click.Context,
    limit: int,
    sort_by: str,
) -> None:
    """列出已收集的交互数据 / List collected interaction data"""
    collector = DataCollector()
    sessions = collector.list_sessions()
    
    if not sessions:
        console.print("[yellow]没有已收集的数据 / No collected data[/yellow]")
        return
    
    if sort_by == "time":
        sessions.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
    elif sort_by == "steps":
        sessions.sort(key=lambda s: s.get("step_count", 0), reverse=True)
    
    table = Table(title="已收集数据 / Collected Data")
    table.add_column("会话ID", style="cyan", no_wrap=True)
    table.add_column("任务", style="green")
    table.add_column("步骤数", style="yellow", justify="right")
    table.add_column("时间", style="dim")
    table.add_column("状态", style="magenta")
    
    for session in sessions[:limit]:
        table.add_row(
            session.get("id", "N/A")[:12],
            session.get("task", "N/A")[:40],
            str(session.get("step_count", 0)),
            session.get("timestamp", "N/A"),
            session.get("status", "N/A"),
        )
    
    console.print(table)
    console.print(f"[dim]共 {len(sessions)} 条记录 / Total {len(sessions)} records[/dim]")


@data_commands.command(name="export")
@click.option("--session-id", help="指定会话ID（不指定则导出全部）/ Session ID (export all if not specified)")
@click.option("--output", "-o", help="输出文件路径 / Output file path")
@click.option("--format", "output_format", type=click.Choice(["json", "jsonl", "csv"]), default="jsonl")
@click.option("--min-quality", type=float, help="最低质量分数 / Minimum quality score")
@click.option("--include-stats", is_flag=True, help="包含统计信息 / Include statistics")
@click.pass_context
def export_data(
    ctx: click.Context,
    session_id: Optional[str],
    output: Optional[str],
    output_format: str,
    min_quality: Optional[float],
    include_stats: bool,
) -> None:
    """导出训练数据 / Export training data"""
    console.print("[bold cyan]正在导出数据... / Exporting data...[/bold cyan]")
    
    exporter = DataExporter()
    
    if session_id:
        data = exporter.export_session(session_id, format=output_format)
    else:
        collector = DataCollector()
        sessions = collector.list_sessions()
        
        if min_quality:
            evaluator = QualityEvaluator()
            filtered = []
            for session in sessions:
                score = evaluator.evaluate_session(session["id"]).overall_score
                if score >= min_quality:
                    filtered.append(session)
            sessions = filtered
        
        data = exporter.export_sessions(
            [s["id"] for s in sessions],
            format=output_format,
        )
    
    if not data:
        console.print("[yellow]没有数据可导出 / No data to export[/yellow]")
        return
    
    if output:
        output_path = Path(output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = get_data_dir() / f"training_data_{timestamp}.{output_format}"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if output_format == "jsonl":
            with open(output_path, "w", encoding="utf-8") as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
        elif output_format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(data)
        
        console.print(f"[green]已导出到 / Exported to: {output_path}[/green]")
        console.print(f"[dim]共 {len(data)} 条记录 / Total {len(data)} records[/dim]")
        
        if include_stats:
            stats = exporter.get_export_stats(data)
            console.print("\n[bold]统计信息 / Statistics:[/bold]")
            for key, value in stats.items():
                console.print(f"  {key}: {value}")
        
    except Exception as e:
        console.print(f"[red]导出失败 / Export failed: {e}[/red]")


@data_commands.command(name="quality")
@click.option("--session-id", help="指定会话ID / Session ID")
@click.option("--weights", help="质量权重（JSON格式）/ Quality weights (JSON)")
@click.option("--threshold", type=float, default=0.7, help="质量阈值 / Quality threshold")
@click.pass_context
def data_quality(
    ctx: click.Context,
    session_id: Optional[str],
    weights: Optional[str],
    threshold: float,
) -> None:
    """评估数据质量 / Evaluate data quality"""
    console.print("[bold cyan]正在评估数据质量... / Evaluating data quality...[/bold cyan]")
    
    quality_weights = None
    if weights:
        try:
            weights_dict = json.loads(weights)
            quality_weights = QualityWeights(**weights_dict)
        except Exception as e:
            console.print(f"[yellow]权重解析失败，使用默认权重 / Failed to parse weights: {e}[/yellow]")
    
    evaluator = QualityEvaluator(weights=quality_weights)
    
    collector = DataCollector()
    sessions = collector.list_sessions()
    
    if session_id:
        sessions = [s for s in sessions if s["id"] == session_id]
    
    if not sessions:
        console.print("[yellow]没有数据可评估 / No data to evaluate[/yellow]")
        return
    
    table = Table(title="数据质量评估 / Data Quality Evaluation")
    table.add_column("会话ID", style="cyan")
    table.add_column("总分", style="yellow", justify="right")
    table.add_column("完成度", style="green", justify="right")
    table.add_column("效率", style="blue", justify="right")
    table.add_column("奖励", style="magenta", justify="right")
    table.add_column("错误率", style="red", justify="right")
    table.add_column("状态", style="bold")
    
    total_score = 0.0
    passed_count = 0
    
    for session in sessions:
        try:
            result = evaluator.evaluate_session(session["id"])
            total_score += result.overall_score
            
            if result.overall_score >= threshold:
                passed_count += 1
                status = "[green]通过[/green]"
            else:
                status = "[red]未通过[/red]"
            
            table.add_row(
                session["id"][:12],
                f"{result.overall_score:.2f}",
                f"{result.completeness:.2f}",
                f"{result.efficiency:.2f}",
                f"{result.reward_score:.2f}",
                f"{result.error_rate:.2f}",
                status,
            )
        except Exception as e:
            console.print(f"[red]评估失败 / Evaluation failed for {session['id']}: {e}[/red]")
    
    console.print(table)
    
    if sessions:
        avg_score = total_score / len(sessions)
        console.print(f"\n[dim]平均质量分 / Average quality: {avg_score:.2f}[/dim]")
        console.print(f"[dim]通过数量 / Passed: {passed_count}/{len(sessions)}[/dim]")


@data_commands.command(name="stats")
@click.option("--session-id", help="指定会话ID / Session ID")
@click.pass_context
def data_stats(
    ctx: click.Context,
    session_id: Optional[str],
) -> None:
    """数据统计 / Data statistics"""
    collector = DataCollector()
    
    if session_id:
        session = collector.get_session(session_id)
        if not session:
            console.print(f"[red]会话未找到 / Session not found: {session_id}[/red]")
            return
        
        sessions = [session]
    else:
        sessions = collector.list_sessions()
    
    if not sessions:
        console.print("[yellow]没有数据 / No data[/yellow]")
        return
    
    total_steps = sum(s.get("step_count", 0) for s in sessions)
    total_errors = sum(s.get("error_count", 0) for s in sessions)
    total_tokens = sum(s.get("token_count", 0) for s in sessions)
    
    console.print(Panel(
        f"[bold]数据统计 / Data Statistics[/bold]\n\n"
        f"会话总数 / Total sessions: {len(sessions)}\n"
        f"总步骤数 / Total steps: {total_steps}\n"
        f"总错误数 / Total errors: {total_errors}\n"
        f"总Token数 / Total tokens: {total_tokens}\n"
        f"平均步骤数 / Avg steps: {total_steps / len(sessions):.1f}",
        title="📊 数据概览 / Data Overview",
        border_style="cyan",
    ))
    
    if len(sessions) > 1:
        table = Table(title="会话详情 / Session Details")
        table.add_column("会话ID", style="cyan")
        table.add_column("步骤数", style="yellow", justify="right")
        table.add_column("错误数", style="red", justify="right")
        table.add_column("Token数", style="blue", justify="right")
        table.add_column("时长(秒)", style="green", justify="right")
        
        for session in sessions:
            table.add_row(
                session.get("id", "N/A")[:12],
                str(session.get("step_count", 0)),
                str(session.get("error_count", 0)),
                str(session.get("token_count", 0)),
                f"{session.get('duration', 0):.1f}",
            )
        
        console.print(table)


@data_commands.command(name="clean")
@click.option("--older-than", type=int, help="删除N天前的数据 / Delete data older than N days")
@click.option("--min-quality", type=float, help="删除低于质量分数的数据 / Delete data below quality score")
@click.option("--dry-run", is_flag=True, help="预览删除（不实际删除）/ Preview only")
@click.confirmation_option(prompt="确定要清理数据吗? / Are you sure you want to clean data?")
@click.pass_context
def clean_data(
    ctx: click.Context,
    older_than: Optional[int],
    min_quality: Optional[float],
    dry_run: bool,
) -> None:
    """清理数据 / Clean up data"""
    collector = DataCollector()
    sessions = collector.list_sessions()
    
    to_delete = []
    
    for session in sessions:
        should_delete = False
        
        if older_than:
            session_time = datetime.fromisoformat(session.get("timestamp", "2000-01-01"))
            age_days = (datetime.now() - session_time).days
            if age_days > older_than:
                should_delete = True
        
        if min_quality:
            evaluator = QualityEvaluator()
            score = evaluator.evaluate_session(session["id"]).overall_score
            if score < min_quality:
                should_delete = True
        
        if should_delete:
            to_delete.append(session["id"])
    
    if not to_delete:
        console.print("[green]没有需要清理的数据 / No data to clean[/green]")
        return
    
    console.print(f"[yellow]将删除 {len(to_delete)} 个会话 / Will delete {len(to_delete)} sessions[/yellow]")
    
    if dry_run:
        console.print("[dim]预览模式，未实际删除 / Dry run, no data deleted[/dim]")
        return
    
    for session_id in to_delete:
        collector.delete_session(session_id)
    
    console.print(f"[green]已清理 {len(to_delete)} 个会话 / Cleaned {len(to_delete)} sessions[/green]")
