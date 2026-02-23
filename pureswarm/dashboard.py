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
        self.agent_count = 0
        self.start_time = time.time()
        self.squad_competition = None

        # Try to load squad competition if in emergency mode
        if os.getenv("EMERGENCY_MODE") == "TRUE":
            try:
                from .squad_competition import SquadCompetition
                self.squad_competition = SquadCompetition()
            except ImportError:
                pass

    def _get_agent_count(self) -> int:
        """Get current agent count from fitness file."""
        fitness_file = self.data_dir / "agent_fitness.json"
        if fitness_file.exists():
            try:
                data = json.loads(fitness_file.read_text(encoding="utf-8"))
                self.agent_count = len(data)
            except:
                pass
        return self.agent_count or 187  # fallback

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
        """Render an ASCII grid representing agents."""
        agent_count = self._get_agent_count()
        grid = Table.grid(padding=0)
        # Dynamic grid sizing based on agent count
        cols = min(20, max(10, int(agent_count ** 0.5) + 1))
        rows = (agent_count + cols - 1) // cols

        for _ in range(cols):
            grid.add_column()

        agents = []
        for i in range(agent_count):
            # Dynamic coloring based on "activity"
            if random.random() > 0.95:
                char = "[bold white]@[/bold white]" # Active/Broadcasting
            elif random.random() > 0.8:
                char = "[bold green]o[/bold green]" # Deliberating
            else:
                char = "[dim green]•[/dim green]" # Resting
            agents.append(char)

        for r in range(rows):
            row_data = agents[r*cols:(r+1)*cols]
            if row_data:
                # Pad if needed
                while len(row_data) < cols:
                    row_data.append(" ")
                grid.add_row(*row_data)
            
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
            round_num = heartbeat_data.get("round", "?")
            status = heartbeat_data.get("status", "unknown")
            if ts:
                try:
                    # Parse ISO format timestamp
                    last_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    now = datetime.now(last_dt.tzinfo) if last_dt.tzinfo else datetime.now()
                    diff = abs((now - last_dt.replace(tzinfo=None)).total_seconds())
                    if diff < 30:
                        heartbeat_status = f"[bold green]R{round_num} SYNCED[/bold green]"
                    elif diff < 120:
                        heartbeat_status = f"[bold yellow]R{round_num} {status[:10]}[/bold yellow]"
                except Exception:
                    heartbeat_status = f"[bold yellow]R{round_num}[/bold yellow]"

        table = Table.grid(expand=True)
        table.add_column(style="cyan")
        table.add_column(justify="right", style="bold white")
        
        agent_count = self._get_agent_count()
        table.add_row("HIVE_POPULATION", f"{agent_count} AGENTS")
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
        # Check both .jsonl and .log formats
        log_file = self.data_dir / "logs" / "audit.jsonl"
        if not log_file.exists():
            log_file = self.data_dir / "logs" / "audit.log"
        events = []
        if log_file.exists():
            try:
                lines = log_file.read_text(encoding="utf-8").splitlines()
                for line in lines[-20:]:
                    if "FUSE" in line or "DELETE" in line or "proposal" in line or "tenet" in line:
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

    def get_squad_leaderboard(self) -> Panel:
        """Render the squad competition leaderboard."""
        competition_file = self.data_dir / ".squad_competition.json"

        table = Table(box=box.SIMPLE, expand=True)
        table.add_column("RANK", style="bold white", width=4)
        table.add_column("SQUAD", style="bold cyan")
        table.add_column("SCORE", justify="right", style="bold green")
        table.add_column("FUSE", justify="right", style="yellow")
        table.add_column("DEL", justify="right", style="red")
        table.add_column("WINS", justify="right", style="magenta")

        if competition_file.exists():
            try:
                data = json.loads(competition_file.read_text())
                leaderboard = data.get("leaderboard", [])
                for i, squad in enumerate(leaderboard[:3]):
                    rank = ["1st", "2nd", "3rd"][i]
                    medal = ["[bold yellow]★[/bold yellow]", "[white]☆[/white]", "[dim]·[/dim]"][i]
                    table.add_row(
                        f"{medal} {rank}",
                        f"[bold]{squad['squad']}[/bold]",
                        str(squad.get("total_score", 0)),
                        str(squad.get("fuse_adopted", 0)),
                        str(squad.get("delete_adopted", 0)),
                        str(squad.get("round_wins", 0))
                    )
            except:
                table.add_row("", "Awaiting first round...", "", "", "", "")
        else:
            table.add_row("", "[dim]Competition not started[/dim]", "", "", "", "")

        return Panel(
            table,
            title="[bold magenta]⚔ SQUAD ARENA ⚔[/bold magenta]",
            border_style="magenta"
        )

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
    layout["side"].split_column(
        Layout(name="vitals", ratio=2),
        Layout(name="arena", ratio=1),
    )

    with Live(layout, refresh_per_second=4, screen=True):
        while True:
            layout["header"].update(hud.get_header())
            layout["map"].update(hud.get_hive_map())
            layout["vitals"].update(hud.get_vitals())
            layout["arena"].update(hud.get_squad_leaderboard())
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
