import os
import time
import json
import random
from pathlib import Path
from datetime import datetime
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich import box
from rich.progress import Progress, BarColumn, TextColumn
from rich.align import Align

# Optional: plotille for terminal sparklines
try:
    import plotille
    HAS_PLOTILLE = True
except ImportError:
    HAS_PLOTILLE = False

console = Console()

class HiveHUD:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.history = []
        self.last_tenet_count = 0
        self.start_time = time.time()

    def get_header(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=2)
        grid.add_column(justify="right", ratio=1)
        
        uptime = int(time.time() - self.start_time)
        grid.add_row(
            f"[bold cyan]UPTIME: {uptime}s[/bold cyan]",
            "[bold magenta]HIVE UPLINK: THE GREAT CONSOLIDATION[/bold magenta]",
            f"[bold green]SYS_TIME: {datetime.now().strftime('%H:%M:%S')}[/bold green]"
        )
        return Panel(grid, style="bold cyan", box=box.DOUBLE)

    def get_hive_map(self) -> Panel:
        """Render an ASCII grid representing the 187 agents."""
        grid = Table.grid(padding=0)
        # 187 agents -> ~17x11 grid
        for _ in range(17):
            grid.add_column()
        
        agents = []
        for i in range(187):
            # Dynamic coloring based on "activity"
            if random.random() > 0.95:
                char = "[bold white]@[/bold white]" # Active/Broadcasting
            elif random.random() > 0.8:
                char = "[bold green]o[/bold green]" # Deliberating
            else:
                char = "[dim green]•[/dim green]" # Resting
            agents.append(char)
        
        for r in range(11):
            grid.add_row(*agents[r*17:(r+1)*17])
            
        return Panel(
            Align.center(grid),
            title="[bold magenta]NEURAL HIVE TOPOLOGY[/bold magenta]",
            border_style="magenta"
        )

    def get_vitals(self) -> Panel:
        tenets_file = self.data_dir / "tenets.json"
        tenet_count = 0
        if tenets_file.exists():
            try:
                tenets = json.loads(tenets_file.read_text())
                tenet_count = len(tenets)
            except:
                pass
        
        self.last_tenet_count = tenet_count
        self.history.append(tenet_count)
        if len(self.history) > 50:
            self.history.pop(0)

        # Heartbeat monitoring
        heartbeat_file = self.data_dir / ".heartbeat"
        heartbeat_data = {}
        if heartbeat_file.exists():
            try:
                heartbeat_data = json.loads(heartbeat_file.read_text())
            except:
                pass
        
        heartbeat_status = "[bold red]OFFLINE[/bold red]"
        if heartbeat_data:
            ts = heartbeat_data.get("timestamp")
            if ts:
                 last_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                 now = datetime.now(datetime.now().astimezone().tzinfo)
                 diff = (now - last_dt).total_seconds()
                 if diff < 15:
                     heartbeat_status = "[bold green]SYNCED[/bold green]"
                 elif diff < 60:
                     heartbeat_status = "[bold yellow]LAGGING[/bold yellow]"

        table = Table.grid(expand=True)
        table.add_column(style="cyan")
        table.add_column(justify="right", style="bold white")
        
        table.add_row("HIVE_POPULATION", "187 AGENTS")
        table.add_row("TENET_DENSITY", f"{tenet_count} PROTOCOLS")
        table.add_row("HEARTBEAT_SIGNAL", heartbeat_status)
        table.add_row("CONSENSUS_STABILITY", "[bold green]94.1%[/bold green]")
        
        # Sparkline logic
        spark = ""
        if HAS_PLOTILLE and len(self.history) > 1:
            try:
                spark = "\n" + plotille.hist(self.history, height=5, width=30)
            except:
                spark = "\n[red]Sparkline Error[/red]"
        
        content = Group(
            Text("PRUNING_PHASE: RED_CONSOLIDATION\n", style="bold yellow"),
            table,
            Text(spark if HAS_PLOTILLE else "\n[dim]Graphing unavailable[/dim]")
        )
        
        return Panel(content, title="[bold cyan]MISSION VITALS[/bold cyan]", border_style="cyan")

    def get_ticker(self) -> Panel:
        log_file = self.data_dir / "logs" / "audit.log"
        events = []
        if log_file.exists():
            try:
                lines = log_file.read_text().splitlines()
                for line in lines[-20:]:
                    if "FUSE" in line or "DELETE" in line or "proposal" in line:
                        events.append(line)
            except:
                pass
                
        ticker = Text()
        if not events:
            ticker.append("Waiting for neural uplink...", style="dim")
        for e in events[-8:]:
            if "ADOPTED" in e:
                ticker.append(" >> ", style="bold green")
                ticker.append("NEURAL CONSOLIDATION SUCCESSFUL\n", style="green")
            else:
                ticker.append(" > ", style="cyan")
                ticker.append(f"{e[:60]}...\n", style="dim white")
                
        return Panel(ticker, title="[bold green]ACTIVE UPLINK[/bold green]", border_style="green")

def run_dashboard():
    # Detect data dir relative to script
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir = Path(__file__).parent.parent / "data"

    hud = HiveHUD(data_dir)
    
    layout = Layout()
    layout.split(
        Layout(name="header", size=4),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="main", ratio=2),
        Layout(name="side", ratio=1),
    )
    layout["main"].split_column(
        Layout(name="map", ratio=1),
        Layout(name="ticker", ratio=1),
    )
    
    with Live(layout, refresh_per_second=4, screen=True):
        while True:
            layout["header"].update(hud.get_header())
            layout["map"].update(hud.get_hive_map())
            layout["side"].update(hud.get_vitals())
            layout["ticker"].update(hud.get_ticker())
            
            # Mission Progress
            # Start from 687 tenets, goal is reduction
            reduction = max(0, 687 - hud.last_tenet_count)
            progress = (reduction / 500) * 100 if hud.last_tenet_count > 100 else 100
            
            footer_text = f"CONSOLIDATION_PROGRESS: [bold green]{progress:.1f}%[/bold green] | STATUS: [blink bold green]ACTIVE PRUNING[/blink bold green]"
            layout["footer"].update(Panel(Align.center(Text.from_markup(footer_text)), border_style="white"))
            
            time.sleep(0.25)

if __name__ == "__main__":
    run_dashboard()
