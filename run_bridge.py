#!/usr/bin/env python3
"""Run the PureSwarm Bridge service.

This connects OpenClaw gateway to the PureSwarm agent swarm via Redis.

Usage:
    python run_bridge.py [--redis-url URL] [--openclaw-url URL] [--token TOKEN]

Environment Variables:
    REDIS_URL: Redis connection URL (default: redis://:[REDACTED_REDIS_PASSWORD]@localhost:6379/0)
    OPENCLAW_URL: OpenClaw WebSocket URL (default: ws://127.0.0.1:18789)
    OPENCLAW_TOKEN: Gateway authentication token

Example:
    # Local development
    python run_bridge.py

    # With custom Redis
    REDIS_URL=redis://localhost:6379/0 python run_bridge.py

    # Production with token
    OPENCLAW_TOKEN=your-token python run_bridge.py
"""

import asyncio
import logging
import os
import sys
from argparse import ArgumentParser

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pureswarm.bridge import run_bridge


def main() -> None:
    parser = ArgumentParser(description="PureSwarm Bridge Service")
    parser.add_argument(
        "--redis-url",
        default=os.environ.get("REDIS_URL", "redis://:[REDACTED_REDIS_PASSWORD]@localhost:6379/0"),
        help="Redis connection URL",
    )
    parser.add_argument(
        "--openclaw-url",
        default=os.environ.get("OPENCLAW_URL", "ws://127.0.0.1:18789"),
        help="OpenClaw WebSocket URL",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("OPENCLAW_TOKEN"),
        help="OpenClaw gateway token",
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

    logger = logging.getLogger("pureswarm.bridge.runner")
    logger.info("Starting PureSwarm Bridge...")
    logger.info("  Redis URL: %s", args.redis_url.replace(":[REDACTED_REDIS_PASSWORD]@", ":***@"))
    logger.info("  OpenClaw URL: %s", args.openclaw_url)
    logger.info("  Token: %s", "configured" if args.token else "not set")

    try:
        asyncio.run(run_bridge(
            redis_url=args.redis_url,
            openclaw_url=args.openclaw_url,
            gateway_token=args.token,
        ))
    except KeyboardInterrupt:
        logger.info("Bridge stopped by user")
    except Exception as e:
        logger.error("Bridge crashed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
