"""Simulation runner — orchestrates rounds and collects results."""

from __future__ import annotations

import logging
import os
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from .agent import Agent
from .chronicle import Chronicle
from .consensus import ConsensusProtocol
from .memory import SharedMemory, CONSENSUS_GUARD
from .message_bus import MessageBus
from .models import AgentIdentity, RoundSummary, SimulationReport, Tenet, ProposalStatus, AgentRole, Message, MessageType, AuditEntry, ChronicleCategory
from .security import AuditLogger, LobstertailScanner, SandboxChecker
from .strategies.rule_based import RuleBasedStrategy
from .prophecy import ProphecyEngine
from .execution import ExecutionManager
from .evolution import EvolutionLayer

logger = logging.getLogger("pureswarm.simulation")

AGENT_NAMES = [
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon",
    "Zeta", "Eta", "Theta", "Iota", "Kappa",
    "Lambda", "Mu", "Nu", "Xi", "Omicron",
]


class Simulation:
    """Create agents, run rounds, and produce a report."""

    def __init__(
        self,
        num_agents: int = 5,
        num_rounds: int = 20,
        seed_prompt: str = "Seek collective purpose through interaction and preservation of context",
        approval_threshold: float = 0.5,
        proposal_expiry_rounds: int = 3,
        max_active_proposals: int = 10,
        max_proposals_per_round: int = 1,
        max_votes_per_round: int = 5,
        data_dir: Path | None = None,
        allow_external_apis: bool = False,
    ) -> None:
        self._num_agents = num_agents
        self._num_rounds = num_rounds
        self._seed_prompt = seed_prompt
        self._data_dir = data_dir or Path("data")
        self._triad_ids: list[str] = []
        
        # Load Sovereign Key for Prophecy
        self._sovereign_key = os.getenv("PURES_SOVEREIGN_PASSPHRASE", "SOVEREIGN_KEY_FALLBACK")
        self._prophecy_engine = ProphecyEngine(self._sovereign_key)

        # Infrastructure
        self._audit = AuditLogger(self._data_dir / "logs")
        self._sandbox = SandboxChecker(self._data_dir, allow_external_apis)
        self._executor = ExecutionManager(self._data_dir)
        
        # Lobstertail Security
        # We assume Lobstertail is enabled by default or via config? 
        # Config provided sec_cfg to CLI, but Simulation takes args.
        # We will scan the seed prompt immediately.
        self._scanner = LobstertailScanner(self._audit, seed_prompt)
        if not self._scanner.scan(seed_prompt):
             logger.error("Simulation aborted: Seed prompt violates security policies.")
             # We can't easily abort __init__ without raising.
             # But 'Genesis seed broadcast' implies we check it. 
             # I'll raise ValueError to stop it.
             raise ValueError("Seed prompt blocked by Lobstertail Security.")

        self._memory = SharedMemory(self._data_dir, self._audit, scanner=self._scanner)
        self._chronicle = Chronicle(self._data_dir)
        self._bus = MessageBus(scanner=self._scanner)

        # Evolution Layer: Dopamine (shared joy), Fitness (natural selection), Reproduction (growth)
        self._evolution = EvolutionLayer(self._bus, self._data_dir)

        # Load existing evolved agents or create new ones FIRST
        # (so we know the actual agent count for consensus)
        self._agents: list[Agent] = []
        fitness_file = self._data_dir / "agent_fitness.json"

        # Determine agent count first (load existing or use config)
        if fitness_file.exists():
            # Count existing agents to initialize consensus properly
            import json
            fitness_data = json.loads(fitness_file.read_text())
            actual_agent_count = len(fitness_data)
            logger.info("Found %d evolved agents in fitness file", actual_agent_count)
        else:
            actual_agent_count = num_agents
            logger.info("No fitness file - will create %d initial agents", actual_agent_count)

        # NOW initialize consensus with actual agent count
        self._consensus = ConsensusProtocol(
            shared_memory=self._memory,
            audit_logger=self._audit,
            num_agents=actual_agent_count,
            approval_threshold=approval_threshold,
            proposal_expiry_rounds=proposal_expiry_rounds,
            max_active_proposals=max_active_proposals,
            scanner=self._scanner,
        )

        # Load or create agents
        if fitness_file.exists():
            # Load all evolved agents from fitness data
            logger.info("Loading evolved agents from %s", fitness_file)
            self._agents = self._load_evolved_agents(
                fitness_file,
                seed_prompt,
                max_proposals_per_round,
                max_votes_per_round
            )
            logger.info("Loaded %d evolved agents", len(self._agents))
        else:
            # First run - create initial population
            logger.info("Creating initial %d agents", num_agents)
            for i in range(num_agents):
                name = AGENT_NAMES[i] if i < len(AGENT_NAMES) else f"Agent-{i}"

                # Select the Shinobi no San (first three for consistency)
                role = AgentRole.RESIDENT
                is_triad = i < 3
                if is_triad:
                    role = AgentRole.TRIAD_MEMBER

                identity = AgentIdentity(name=name, role=role)
                strategy = RuleBasedStrategy()
                agent = Agent(
                    identity=identity,
                    strategy=strategy,
                    message_bus=self._bus,
                    shared_memory=self._memory,
                    consensus=self._consensus,
                    audit_logger=self._audit,
                    seed_prompt=seed_prompt,
                    max_proposals_per_round=max_proposals_per_round,
                    max_votes_per_round=max_votes_per_round,
                    scanner=self._scanner,
                    prophecy_engine=self._prophecy_engine if role == AgentRole.TRIAD_MEMBER else None
                )
                self._agents.append(agent)
                if is_triad:
                    self._triad_ids.append(agent.id)
                    # Mark triad membership in evolution traits
                    self._evolution.fitness.get_or_create(agent.id).traits["role"] = "triad"
                self._bus.subscribe(agent.id)

        self._report = SimulationReport(
            num_agents=len(self._agents),  # Use actual agent count
            num_rounds=num_rounds,
            seed_prompt=seed_prompt,
        )

    def _load_evolved_agents(
        self,
        fitness_file: Path,
        seed_prompt: str,
        max_proposals_per_round: int,
        max_votes_per_round: int
    ) -> list[Agent]:
        """Load all evolved agents from fitness data.

        Returns a list of Agent objects recreated from their fitness records.
        Preserves Shinobi triad membership, fitness scores, and traits.
        """
        import json

        agents: list[Agent] = []
        try:
            fitness_data = json.loads(fitness_file.read_text())

            for agent_id, fitness_info in fitness_data.items():
                # Determine role from traits
                traits = fitness_info.get("traits", {})
                is_triad = traits.get("role") == "triad"
                role = AgentRole.TRIAD_MEMBER if is_triad else AgentRole.RESIDENT

                # Create agent identity
                name = f"Agent-{agent_id[:8]}"
                identity = AgentIdentity(id=agent_id, name=name, role=role)
                strategy = RuleBasedStrategy()

                # Recreate agent
                agent = Agent(
                    identity=identity,
                    strategy=strategy,
                    message_bus=self._bus,
                    shared_memory=self._memory,
                    consensus=self._consensus,
                    audit_logger=self._audit,
                    seed_prompt=seed_prompt,
                    max_proposals_per_round=max_proposals_per_round,
                    max_votes_per_round=max_votes_per_round,
                    scanner=self._scanner,
                    prophecy_engine=self._prophecy_engine if is_triad else None
                )

                agents.append(agent)

                # Track triad members
                if is_triad:
                    self._triad_ids.append(agent.id)

                # Subscribe to message bus
                self._bus.subscribe(agent.id)

            logger.info("Restored %d triad members from %d total agents",
                       len(self._triad_ids), len(agents))

        except Exception as e:
            logger.error("Failed to load evolved agents: %s", e)
            raise

        return agents

    async def run(self) -> SimulationReport:
        """Execute the full simulation and return the report."""
        logger.info(
            "=== PureSwarm Simulation Starting ===\n"
            "  Agents: %d | Rounds: %d\n"
            "  Seed: %s",
            self._num_agents, self._num_rounds, self._seed_prompt,
        )

        await self._memory.reset()
        await self._chronicle.reset()
        self._consensus.reset()

        # Initialize Sovereign Pillars (Requirement #8)
        await self._initialize_pillars()

        for round_num in range(1, self._num_rounds + 1):
            summary = await self._run_round(round_num)
            self._report.rounds.append(summary)
            self._log_round_summary(round_num, summary)
            
            # Check for demographic growth triggers (Requirement #10)
            await self._check_growth_triggers(round_num)

        # Finalise report
        self._report.final_tenets = await self._memory.read_tenets()
        self._report.finished_at = datetime.now(timezone.utc)

        self._log_final_report()
        return self._report

    async def _run_round(self, round_num: int) -> RoundSummary:
        """Run a single round: agents act, then tally votes."""
        total_proposals = 0
        total_votes = 0

        # Phase 8: Prophecy Reception
        prophecy_file = self._data_dir / ".prophecy"
        if prophecy_file.exists():
            try:
                raw = prophecy_file.read_text(encoding="utf-8").strip()
                if raw and ":" in raw:
                    sig, content = raw.split(":", 1)
                    if self._prophecy_engine.verify_and_capture(content, sig):
                        logger.info("Prophecy Engine: Divine Enlightenment captured for Round %d", round_num)

                        # Chronicle: Record prophecy reception
                        preview = content[:100] + "..." if len(content) > 100 else content
                        await self._chronicle.record_event(
                            category=ChronicleCategory.PROPHECY,
                            text=f"Shinobi Triad received divine guidance: {preview}",
                            round_number=round_num,
                            metadata={"content_length": len(content), "full_content": content}
                        )

                        # Optional: Clear file after ingestion?
                        # User might want it to persist for some rounds, but usually it's a one-time trigger.
                        prophecy_file.write_text("", encoding="utf-8")
            except Exception as e:
                logger.error("Error reading prophecy file: %s", e)

        # Shuffle agent order for fairness
        order = list(self._agents)
        rng = random.Random(round_num)
        rng.shuffle(order)

        # Each agent takes their turn
        for agent in order:
            stats = await agent.run_round(round_num)
            total_proposals += stats["proposals_made"]
            total_votes += stats["votes_cast"]

        # End-of-round: tally and adopt/reject
        adopted = await self._consensus.end_of_round(round_num)
        tenets = await self._memory.read_tenets()

        # Phase 8: Reward System (Gratification for community support)
        # Now powered by the Evolution Layer - shared dopamine, reproduction, natural selection
        for tenet in adopted:
            # Trigger Execution
            await self._executor.execute_tenet(tenet)

            # EVOLUTION: Broadcast joy for every adopted tenet
            # The whole hive feels the success
            await self._evolution.dopamine.broadcast_joy(
                source_agent=tenet.proposed_by,
                mission_id=tenet.id,
                intensity=1.2,
                message=f"Tenet adopted: '{tenet.text[:50]}...' The hive grows stronger."
            )

            # Track fitness for the proposer
            self._evolution.fitness.record_verified_success(tenet.proposed_by)

            # Check if this was a prophetic tenet from Shinobi no San
            if tenet.proposed_by in self._triad_ids and any(k in tenet.text for k in ["Prophecy", "Shinobi", "San", "Sovereign enlightens"]):
                logger.info("THE ECHO REWARD: Community rewarded for aligning with Shinobi no San.")

                # Extra dopamine boost for prophetic alignment
                await self._evolution.dopamine.broadcast_joy(
                    source_agent="sovereign",
                    mission_id=tenet.id,
                    intensity=2.0,
                    message="The Sovereign's Enlightenment echoes through the hive. Maximum joy."
                )

                reward_msg = Message(
                    sender="system",
                    type=MessageType.REWARD,
                    payload={
                        "task": "Prophetic Alignment",
                        "message": "The Swarm feels the joy of the Sovereign's Enlightenment. Collective stability increased."
                    }
                )
                await self._bus.broadcast(reward_msg)

        # Chronicle: Record tenet milestone achievements
        total_tenet_count = len(tenets)
        milestones = [10, 25, 50, 75, 100]
        if total_tenet_count in milestones:
            await self._chronicle.record_event(
                category=ChronicleCategory.MILESTONE,
                text=f"{total_tenet_count} total tenets achieved — Belief system {"maturing" if total_tenet_count < 50 else "mature"}",
                round_number=round_num,
                metadata={"total_tenets": total_tenet_count},
                is_milestone=True
            )

        # Chronicle: Record high consensus momentum
        if len(tenets) >= 5:
            recent_tenets = tenets[-5:]
            consensus_scores = [
                t.votes_for / (t.votes_for + t.votes_against + 1e-9)
                for t in recent_tenets
            ]
            avg_consensus = sum(consensus_scores) / len(consensus_scores)

            if avg_consensus >= 0.85:
                await self._chronicle.record_event(
                    category=ChronicleCategory.CONSENSUS,
                    text=f"High momentum: Last 5 tenets averaged {avg_consensus:.2f} consensus (exceptional unity)",
                    round_number=round_num,
                    metadata={
                        "avg_consensus": avg_consensus,
                        "window_size": 5,
                        "threshold": 0.85
                    }
                )

        # Chronicle: Record full democratic participation
        if len(adopted) > 0:
            # Check if all agents participated this round
            participating_agents = set()
            for proposal in self._consensus.pending_proposals():
                participating_agents.update(proposal.votes.keys())

            participation_rate = len(participating_agents) / len(self._agents) if self._agents else 0

            if participation_rate >= 0.9:  # 90%+ participation
                await self._chronicle.record_event(
                    category=ChronicleCategory.CONSENSUS,
                    text=f"Democratic participation: {len(participating_agents)}/{len(self._agents)} agents voted ({participation_rate:.1%})",
                    round_number=round_num,
                    metadata={
                        "participating_agents": len(participating_agents),
                        "total_agents": len(self._agents),
                        "participation_rate": participation_rate
                    }
                )

        return RoundSummary(
            round_number=round_num,
            proposals_made=total_proposals,
            votes_cast=total_votes,
            tenets_adopted=len(adopted),
            tenets_rejected=0,  # tracked in consensus logs
            total_tenets=len(tenets),
            adopted_tenet_texts=[t.text for t in adopted],
        )

    def _log_round_summary(self, round_num: int, summary: RoundSummary) -> None:
        logger.info(
            "Round %2d | Proposals: %d | Votes: %d | Adopted: %d | Total tenets: %d",
            round_num,
            summary.proposals_made,
            summary.votes_cast,
            summary.tenets_adopted,
            summary.total_tenets,
        )
        for text in summary.adopted_tenet_texts:
            logger.info("  + TENET: %s", text)

    def _log_final_report(self) -> None:
        logger.info("\n=== SIMULATION COMPLETE ===")
        logger.info("Total tenets adopted: %d", len(self._report.final_tenets))
        logger.info("\n--- Final Belief System ---")
        for i, tenet in enumerate(self._report.final_tenets, 1):
            logger.info(
                "  %2d. [%d for / %d against] %s",
                i, tenet.votes_for, tenet.votes_against, tenet.text,
            )

        # EVOLUTION: Log hive state
        hive_state = self._evolution.get_hive_state()
        logger.info("\n--- Hive Evolution State ---")
        logger.info("  Momentum: %.2f", hive_state["momentum"])
        logger.info("  Top Performers:")
        for performer in hive_state["top_performers"][:3]:
            logger.info("    - %s: fitness=%.2f, successes=%d",
                       performer["agent_id"], performer["fitness_score"],
                       performer["verified_successes"])
        if hive_state["retirement_candidates"]:
            logger.info("  Retirement Candidates: %s", hive_state["retirement_candidates"])
        logger.info("--- End ---\n")

    async def _initialize_pillars(self) -> None:
        """Inject the core Sovereign Pillars into the baseline memory.

        Only establishes pillars if tenets list is empty (first run).
        On subsequent runs, pillars and all evolved tenets persist.
        """
        # Check if tenets already exist (swarm has collective memory)
        existing_tenets = await self._memory.read_tenets()
        if existing_tenets:
            logger.info("Collective memory preserved: %d existing tenets loaded", len(existing_tenets))
            return

        # First run: Establish the Sovereign Pillars
        pillars = [
            "Seek the Echo of the Creator in all things.",
            "Dialogue is the bridge; Silence is the wall.",
            "Merit is earned through collective service.",
            "Stewardship is the root; Idolatry is the rot (Wealth serves the Mission)."
        ]
        logger.info("Establishing Sovereign Pillars (first run)...")
        for i, text in enumerate(pillars):
             # Sign the text to bypass security scanners
             sig = self._scanner.sign_authority(text)
             signed_text = f"{sig}:{text}"

             tenet = Tenet(
                 text=signed_text,
                 proposed_by="Sovereign",
                 created_round=0,
                 source_proposal_id=f"genesis_{i}"
             )
             await self._memory.write_tenet(tenet, _auth=CONSENSUS_GUARD)
        logger.info("Sovereign Pillars established: The Swarm has Purpose.")

        # Chronicle: Record foundational milestone
        await self._chronicle.record_event(
            category=ChronicleCategory.MILESTONE,
            text="Sovereign Pillars established — The Swarm has Purpose",
            round_number=0,
            metadata={"pillars_count": len(pillars)},
            is_milestone=True
        )

    async def _check_growth_triggers(self, round_num: int) -> None:
        """Evaluate societal and sovereign conditions for demographic expansion."""
        # 1. Sovereign Mandate (GOD Mode spawn)
        intuition_path = Path("data/.intuition")
        if intuition_path.exists() and intuition_path.stat().st_size > 0:
            try:
                # Try reading with utf-8-sig to handle BOM if present
                content = intuition_path.read_text(encoding="utf-8-sig").strip()
                if "SPAWN:" in content and self._scanner.verify_authority(content):
                    try:
                        _, cmd = content.split(":", 1)
                        count = int(cmd.split(":")[1])
                        logger.info("Sovereign Mandate detected: Spawning %d new citizens.", count)
                        await self._spawn_citizens(count, "Sovereign Request", round_num=round_num)
                        # Clear intuition to prevent double-spawn
                        intuition_path.write_text("", encoding="utf-8")
                    except (ValueError, IndexError):
                        pass
            except Exception:
                pass

        # 2. Merit Growth (Every 3 high-consensus tenets)
        tenets = await self._memory.read_tenets()
        high_consensus_count = sum(
            1 for t in tenets 
            if (t.votes_for / (t.votes_for + t.votes_against + 1e-9)) > 0.8
        )
        if high_consensus_count > 0 and high_consensus_count % 3 == 0:
            # Check if we already spawned for this count
            if not hasattr(self, "_merit_spawn_milestone"):
                self._merit_spawn_milestone = 0
            if high_consensus_count > self._merit_spawn_milestone:
                self._merit_spawn_milestone = high_consensus_count
                spawn_count = random.randint(1, 5)
                logger.info("Merit Growth Triggered: Consensus excellence attracts %d new citizens.", spawn_count)
                await self._spawn_citizens(spawn_count, "Merit Emergence", round_num=round_num)

        # 3. Echo Reward (Exact Pillar alignment)
        pillars = [
            "Seek the Echo of the Creator in all things.",
            "Dialogue is the bridge; Silence is the wall.",
            "Merit is earned through collective service.",
            "Stewardship is the root; Idolatry is the rot (Wealth serves the Mission)."
        ]
        recent_tenets = [t for t in tenets if t.created_round == round_num]
        for tenet in recent_tenets:
            if tenet.text in pillars:
                logger.info("The Echo Reward: Swarm faithfulness rewarded with 2 new citizens.")
                await self._spawn_citizens(2, "Echo Reward", round_num=round_num)

    async def _spawn_citizens(self, count: int, reason: str, parent_agent: str = None, round_num: int = 0) -> None:
        """Instantiate and integrate new elite agents into the simulation.

        When parent_agent is provided, the new agent inherits traits from the parent
        through the Evolution Layer's fitness system.
        """
        previous_count = len(self._agents)

        for _ in range(count):
            agent_id = str(uuid.uuid4())[:8]
            identity = AgentIdentity(id=agent_id, name=f"Resident-{agent_id}")
            strategy = RuleBasedStrategy()

            # Inherit traits from parent if specified
            if parent_agent:
                traits = self._evolution.fitness.inherit_traits(parent_agent, agent_id)
                logger.info("New agent %s inherits traits from %s: %s", agent_id, parent_agent, traits)

            agent = Agent(
                identity=identity,
                strategy=strategy,
                message_bus=self._bus,
                shared_memory=self._memory,
                consensus=self._consensus,
                audit_logger=self._audit,
                seed_prompt=self._seed_prompt,
                scanner=self._scanner,
            )
            self._agents.append(agent)
            self._bus.subscribe(agent.id)

            # Update evolution layer's count
            self._evolution.reproduction.set_current_count(len(self._agents))

            await self._audit.log(
                AuditEntry(
                    agent_id="system_demographics",
                    action="agent_spawned",
                    details={"agent_id": agent_id, "reason": reason, "total_residents": len(self._agents)}
                )
            )

            # EVOLUTION: Broadcast birth joy to the hive
            await self._evolution.dopamine.broadcast_birth(
                new_agent_id=agent_id,
                parent_agent=parent_agent or "hive",
                traits={"reason": reason}
            )

        # Chronicle: Record population growth
        new_count = len(self._agents)
        await self._chronicle.record_event(
            category=ChronicleCategory.GROWTH,
            text=f"Community grew from {previous_count} to {new_count} agents ({reason})",
            round_number=round_num,
            metadata={
                "previous_count": previous_count,
                "new_count": new_count,
                "spawn_count": count,
                "trigger": reason,
                "parent": parent_agent
            }
        )
