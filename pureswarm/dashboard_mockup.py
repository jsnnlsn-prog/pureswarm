import time
import random
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text

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

def get_vitals_panel(tenet_count: int, api_latency: float):
    table = Table.grid(expand=True)
    table.add_column(style="cyan", justify="left")
    table.add_column(style="magenta", justify="right")
    
    table.add_row("[b]HIVE DENSITY[/b]", f"[b]{tenet_count}[/b] Tenets")
    table.add_row("API RESONANCE", f"{api_latency:.2f}s Latency")
    table.add_row("SQUAD ALPHA", "[green]SYNTROPIC[/green]")
    table.add_row("SQUAD BETA", "[yellow]ENTROPIC[/yellow]")
    table.add_row("SQUAD GAMMA", "[blue]ANALYSIS[/blue]")
    
    return Panel(table, title="[bold white]HIVE VITALS[/bold white]", border_style="bright_blue")

def get_log_panel(events):
    log_text = Text()
    for e in events[-8:]:
        log_text.append(f"{e}\n")
    return Panel(log_text, title="[bold white]CONSOLIDATION TICKER[/bold white]", border_style="green")

def get_header():
    return Panel(
        Text("THE GREAT CONSOLIDATION - HIERARCHICAL RESTRUCTURING ACTIVE", justify="center", style="bold red"),
        style="white on dark_green"
    )

def run_dashboard():
    layout = generate_layout()
    events = [
        "[white]System Initialized[/white]",
        "[cyan]Prophet Alpha assumed command[/cyan]",
        "[cyan]Prophet Beta assumed command[/cyan]",
        "[cyan]Prophet Gamma assumed command[/cyan]",
        "[yellow]Lobstertail Scanner: OFFLINE[/yellow]",
    ]
    
    tenet_count = 636
    
    with Live(layout, refresh_per_second=4, screen=True):
        while True:
            # Simulated update
            if random.random() > 0.8:
                action = random.choice(["FUSED", "DELETED"])
                count = random.randint(1, 4)
                tenet_count -= count
                events.append(f"[bold green]ADOPTED: {action} {count} redundant iterations.[/bold green]")
            
            layout["header"].update(get_header())
            layout["vitals"].update(get_vitals_panel(tenet_count, random.uniform(0.5, 2.5)))
            layout["log"].update(get_log_panel(events))
            layout["side"].update(Panel("[b]EMERGENCY MODE[/b]\n\nAdditives: [red]OFF[/red]\nWorkshops: [red]PAUSED[/red]\nTriad Auth: [green]FULL[/green]", title="AUTH"))
            layout["footer"].update(Panel(f"Round Progress: [green]|||||||||||||||||||| [/green] 85%", border_style="white"))
            
            time.sleep(0.5)

if __name__ == "__main__":
    run_dashboard()
