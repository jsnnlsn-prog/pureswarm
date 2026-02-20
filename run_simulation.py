#!/usr/bin/env python3
"""CLI entry point for running a PureSwarm simulation."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

import argparse

load_dotenv()

try:
    import tomllib
except ModuleNotFoundError:
    # Python < 3.11 fallback
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

from pureswarm.simulation import Simulation
from pureswarm.memory import create_memory_backend
from pureswarm.security import AuditLogger, LobstertailScanner


def load_config(path: Path) -> dict:
    if tomllib is None:
        # Minimal manual TOML parser for simple flat configs
        raise SystemExit(
            "Python 3.11+ required for built-in TOML support, "
            "or install 'tomli' package."
        )
    with open(path, "rb") as f:
        return tomllib.load(f)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)-28s | %(levelname)-5s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


async def main() -> None:
    setup_logging()
    logger = logging.getLogger("pureswarm.cli")

    parser = argparse.ArgumentParser(description="PureSwarm Simulation Runner")
    parser.add_argument("--emergency", action="store_true", help="Enable Emergency Mode")
    parser.add_argument("--config", type=str, default="config.toml", help="Path to config file")
    args = parser.parse_args()

    if args.emergency:
        os.environ["EMERGENCY_MODE"] = "TRUE"
        logger.info("CORE COMMAND: EMERGENCY MODE SIGNAL DETECTED")

    config_path = Path(args.config)
    if not config_path.exists():
        logger.error("config.toml not found in current directory")
        sys.exit(1)

    cfg = load_config(config_path)
    sim_cfg = cfg.get("simulation", {})
    con_cfg = cfg.get("consensus", {})
    sec_cfg = cfg.get("security", {})
    agt_cfg = cfg.get("agent", {})

    data_dir = Path(sec_cfg.get("data_directory", "data"))

    # Create memory backend from config (file or redis)
    seed_prompt = sim_cfg.get(
        "seed_prompt",
        "Seek collective purpose through interaction and preservation of context",
    )
    audit_logger = AuditLogger(data_dir / "logs")
    scanner = LobstertailScanner(audit_logger, seed_prompt)
    memory_backend = await create_memory_backend(cfg, audit_logger, scanner)
    logger.info("Memory backend initialized: %s", type(memory_backend).__name__)

    sim = Simulation(
        num_agents=sim_cfg.get("num_agents", 5),
        num_rounds=sim_cfg.get("num_rounds", 20),
        seed_prompt=seed_prompt,
        approval_threshold=con_cfg.get("approval_threshold", 0.5),
        proposal_expiry_rounds=con_cfg.get("proposal_expiry_rounds", 3),
        max_active_proposals=con_cfg.get("max_active_proposals", 10),
        max_proposals_per_round=agt_cfg.get("max_proposals_per_round", 1),
        max_votes_per_round=agt_cfg.get("max_votes_per_round", 5),
        data_dir=data_dir,
        allow_external_apis=sec_cfg.get("allow_external_apis", False),
        memory_backend=memory_backend,
    )

    report = await sim.run()

    # Write report to file
    report_path = data_dir / "simulation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2, default=str)

    logger.info("Report saved to %s", report_path)
    logger.info(
        "Simulation finished: %d tenets emerged from %d rounds with %d agents.",
        len(report.final_tenets),
        report.num_rounds,
        report.num_agents,
    )


def cli() -> None:
    """Entry point for the ``pureswarm`` console script."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
