#!/usr/bin/env python3
"""Run the PureSwarm Query Listener service.

This service runs alongside the simulation on pureswarm-node, listening for
external queries via Redis pub/sub and triggering agent deliberation.

Usage:
    python run_query_listener.py [--redis-url URL] [--data-dir DIR]

Environment Variables:
    REDIS_URL: Redis connection URL (default: redis://:[REDACTED_REDIS_PASSWORD]@localhost:6379/0)
    DATA_DIR: Data directory path (default: data)
    AGENT_SAMPLE_SIZE: Number of agents to sample per query (default: 15)
    LOG_LEVEL: Logging level (default: INFO)

Example:
    # Local development
    python run_query_listener.py

    # Production (on pureswarm-node)
    REDIS_URL=redis://localhost:6379/0 python run_query_listener.py

    # With custom sample size
    AGENT_SAMPLE_SIZE=25 python run_query_listener.py
"""

import asyncio
import logging
import os
import sys
from argparse import ArgumentParser

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pureswarm.query_listener import run_query_listener


def main() -> None:
    parser = ArgumentParser(description="PureSwarm Query Listener Service")
    parser.add_argument(
        "--redis-url",
        default=os.environ.get("REDIS_URL", "redis://:[REDACTED_REDIS_PASSWORD]@localhost:6379/0"),
        help="Redis connection URL",
    )
    parser.add_argument(
        "--data-dir",
        default=os.environ.get("DATA_DIR", "data"),
        help="Data directory path",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=int(os.environ.get("AGENT_SAMPLE_SIZE", "15")),
        help="Number of agents to sample for each query (default: 15)",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger("pureswarm.query_listener.runner")
    logger.info("Starting PureSwarm Query Listener...")
    logger.info("  Redis URL: %s", args.redis_url.replace(":[REDACTED_REDIS_PASSWORD]@", ":***@"))
    logger.info("  Data dir: %s", args.data_dir)
    logger.info("  Sample size: %d agents per query", args.sample_size)

    try:
        asyncio.run(run_query_listener(
            redis_url=args.redis_url,
            data_dir=args.data_dir,
            agent_sample_size=args.sample_size,
        ))
    except KeyboardInterrupt:
        logger.info("Query listener stopped by user")
    except Exception as e:
        logger.error("Query listener crashed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
