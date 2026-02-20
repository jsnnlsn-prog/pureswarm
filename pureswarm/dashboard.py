import os
import time
import json
from pathlib import Path
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

def generate_layout() -> Layout:
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="main", ratio=2),
        Layout(name="side", ratio=1),
    )
    layout["main"].split_column(
        Layout(name="vitals", size=10),
        Layout(name="log"),
    )
    return layout

def get_vitals_panel(data_dir: Path):
    tenets_file = data_dir / "tenets.json"
    tenet_count = 0
    if tenets_file.exists():
        try:
            tenets = json.loads(tenets_file.read_text())
            tenet_count = len(tenets)
        except:
            pass

    # Heartbeat monitoring
    heartbeat_file = data_dir / ".heartbeat"
    heartbeat_data = {}
    if heartbeat_file.exists():
        try:
            heartbeat_data = json.loads(heartbeat_file.read_text())
        except:
            pass
    
    last_signal = "N/A"
    heartbeat_status = "[red]SILENT[/red]"
    if heartbeat_data:
        ts = heartbeat_data.get("timestamp")
        if ts:
             from datetime import datetime
             last_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
             now = datetime.now(datetime.now().astimezone().tzinfo)
             diff = (now - last_dt).total_seconds()
             last_signal = f"{int(diff)}s ago"
             if diff < 10:
                 heartbeat_status = "[green]ACTIVE[/green]"
             elif diff < 60:
                 heartbeat_status = "[yellow]DELAYED[/yellow]"
             else:
                 heartbeat_status = "[red]STALLED[/red]"

    table = Table.grid(expand=True)
    table.add_column(style="cyan", justify="left")
    table.add_column(style="magenta", justify="right")
    
    table.add_row("[b]HIVE DENSITY[/b]", f"[b]{tenet_count}[/b] Tenets")
    table.add_row("HEARTBEAT", heartbeat_status)
    table.add_row("LAST SIGNAL", last_signal)
    table.add_row("SQUAD ALPHA", "[green]REDUCING[/green]")
    table.add_row("SQUAD BETA", "[green]REDUCING[/green]")
    table.add_row("SQUAD GAMMA", "[green]REDUCING[/green]")
    
    # Calculate reduction % (starting from ~650)
    reduction = max(0, 650 - tenet_count)
    reduction_pct = (reduction / 550) * 100 if tenet_count > 100 else 100
    
    table.add_row("PRUNING EFFICIENCY", f"{reduction_pct:.1f}%")
    
    return Panel(table, title="[bold white]HIVE VITALS[/bold white]", border_style="bright_blue")

def get_log_panel(data_dir: Path):
    log_file = data_dir / "logs" / "audit.log"
    events = []
    if log_file.exists():
        try:
            lines = log_file.read_text().splitlines()
            for line in lines[-30:]:
                if "FUSE" in line or "DELETE" in line or "proposal_submitted" in line:
                    events.append(line)
        except:
            pass
            
    log_text = Text()
    if not events:
        log_text.append("Waiting for neural pruning signals...", style="white dim")
    for e in events[-10:]:
        if "action='proposal_submitted'" in e:
             log_text.append("[cyan]> [/cyan]New Consolidation Proposal Detected\n")
        elif "ADOPTED" in e or "Success" in e:
             log_text.append(f"[bold green]✓ {e[:100]}[/bold green]\n")
        else:
             log_text.append(f"{e[:100]}\n")
             
    return Panel(log_text, title="[bold white]CONSOLIDATION TICKER[/bold white]", border_style="green")

def get_header():
    return Panel(
        Text("THE GREAT CONSOLIDATION - HIERARCHICAL RESTRUCTURING ACTIVE", justify="center", style="bold red"),
        style="white on dark_red"
    )

def run_dashboard():
    data_dir = Path("data")
    layout = generate_layout()
    
    with Live(layout, refresh_per_second=2, screen=True):
        while True:
            layout["header"].update(get_header())
            layout["vitals"].update(get_vitals_panel(data_dir))
            layout["log"].update(get_log_panel(data_dir))
            
            # Auth Panel
            auth_text = Text()
            auth_text.append("EMERGENCY MODE: [red]ACTIVE[/red]\n")
            auth_text.append("SQUAD ALPHA: [green]PROPHET-1[/green]\n")
            auth_text.append("SQUAD BETA:  [green]PROPHET-2[/green]\n")
            auth_text.append("SQUAD GAMMA: [green]PROPHET-3[/green]\n\n")
            auth_text.append("Residents restricted to rule-based consensus.\n")
            auth_text.append("API usage exclusively for Triad/Researchers.")
            
            layout["side"].update(Panel(auth_text, title="SYSTEM STATUS", border_style="yellow"))
            
            # Progress bar simulation / estimation
            layout["footer"].update(Panel("Neural Pruning in Progress... [green]|||||||||||||||||||||||| [/green]", border_style="white"))
            
            time.sleep(1)

if __name__ == "__main__":
    run_dashboard()
