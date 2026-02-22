"""Simulation runner — orchestrates rounds and collects results."""

from __future__ import annotations

import asyncio
import logging
import os
import random
import uuid
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from .agent import Agent
from .chronicle import Chronicle
from .consensus import ConsensusProtocol
from .memory import SharedMemory, MemoryBackend, CONSENSUS_GUARD
from .message_bus import MessageBus
from .models import AgentIdentity, RoundSummary, SimulationReport, Tenet, ProposalStatus, AgentRole, Message, MessageType, AuditEntry, ChronicleCategory, ProposalAction
from .security import AuditLogger, LobstertailScanner, SandboxChecker
from .strategies.rule_based import RuleBasedStrategy
from .strategies.llm_driven import LLMDrivenStrategy
from .tools.http_client import VeniceAIClient, ShinobiHTTPClient, AnthropicClient, FallbackLLMClient
from .prophecy import ProphecyEngine
from .execution import ExecutionManager
from .evolution import EvolutionLayer
from .workshop import WorkshopOrchestrator
from .squad_competition import SquadCompetition
from .tenet_clusterer import TenetClusterer
from .prompt_economy import PromptEconomy

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
        memory_backend: MemoryBackend | None = None,
        interactive: bool = False,
    ) -> None:
        self._num_agents = num_agents
        self._num_rounds = num_rounds
        self._seed_prompt = seed_prompt
        self._data_dir = data_dir or Path("data")
        self._triad_ids: list[str] = []
        self._interactive = interactive
        
        # Load Sovereign Key for Prophecy
        self._sovereign_key = os.getenv("PURES_SOVEREIGN_PASSPHRASE", "SOVEREIGN_KEY_FALLBACK")
        self._prophecy_engine = ProphecyEngine(self._sovereign_key)

        # Emergency Mode Deployment
        self._emergency_mode = os.getenv("EMERGENCY_MODE") == "TRUE"
        self._squad_competition: Optional[SquadCompetition] = None
        self._tenet_clusterer: Optional[TenetClusterer] = None
        self._prompt_economy: Optional[PromptEconomy] = None
        if self._emergency_mode:
            logger.warning("!!! EMERGENCY MODE ACTIVE: NEURAL PRUNING INITIALIZED !!!")
            os.environ["CONSOLIDATION_MODE"] = "TRUE"  # Sync with scanner
            self._squad_competition = SquadCompetition(self._data_dir)

            # Initialize Prompt Economy and Tenet Clusterer
            self._prompt_economy = PromptEconomy(self._data_dir)
            self._tenet_clusterer = TenetClusterer(self._data_dir)

            # Wire up to squad competition
            self._squad_competition.set_prompt_economy(self._prompt_economy)
            self._squad_competition.set_clusterer(self._tenet_clusterer)

            logger.info("SQUAD COMPETITION ENABLED: Alpha vs Beta vs Gamma")
            logger.info("PROMPT ECONOMY: 10 prompts/squad, winner takes all")
            logger.info("TENET CLUSTERER: Pre-sorted similarity packages")

        # Initialize LLM Strategy with fallback support (Anthropic -> Venice)
        self._venice_key = os.getenv("VENICE_API_KEY", "")
        self._anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._llm_strategy = None

        if self._venice_key or self._anthropic_key:
            from .tools.internet import InternetAccess
            # Create InternetAccess which now supports fallback LLM chain
            stub_internet = InternetAccess("simulation_system", False, data_dir=self._data_dir)
            if stub_internet._venice:
                self._llm_strategy = LLMDrivenStrategy(stub_internet._venice)
                providers = []
                if self._anthropic_key:
                    providers.append("Anthropic")
                if self._venice_key:
                    providers.append("Venice")
                logger.info("Cognitive Upgrade: LLM fallback chain [%s] initialized.", " -> ".join(providers))

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

        # Memory backend: use injected backend or default to file-based SharedMemory
        if memory_backend is not None:
            self._memory = memory_backend
            logger.info("Using injected memory backend: %s", type(memory_backend).__name__)
        else:
            self._memory = SharedMemory(self._data_dir, self._audit, scanner=self._scanner)
        self._chronicle = Chronicle(self._data_dir)
        self._bus = MessageBus(scanner=self._scanner)

        # Workshop System: Real-world problem solving
        self._workshop = WorkshopOrchestrator(self._data_dir)

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
            from .strategies.rule_based import TECH_SPECIALTIES
            specialties_list = list(TECH_SPECIALTIES.keys())

            logger.info("Creating initial %d agents with unique specializations", num_agents)
            for i in range(num_agents):
                name = AGENT_NAMES[i] if i < len(AGENT_NAMES) else f"Agent-{i}"

                # Select the Shinobi no San (first three for consistency)
                role = AgentRole.RESIDENT
                is_triad = i < 3
                if is_triad:
                    role = AgentRole.TRIAD_MEMBER

                # SQUAD PARTITIONING
                squads = ["Alpha", "Beta", "Gamma"]
                squad_id = squads[i % 3] if self._emergency_mode else None
                # Mark first 2 Residents per squad as researchers (Total 6)
                is_researcher = (3 <= i < 9) if self._emergency_mode else False
                if is_researcher:
                    role = AgentRole.RESEARCHER

                # Assign specialization - this is WHO THEY ARE
                specialization = specialties_list[i % len(specialties_list)]

                identity = AgentIdentity(
                    name=name,
                    role=role,
                    specialization=specialization
                )

                # Rule: Triad/Researchers use LLM strategy; Residents use Rule-Based (no API calls)
                if is_triad or is_researcher:
                    strategy = self._llm_strategy if self._llm_strategy else RuleBasedStrategy()
                else:
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
                    prophecy_engine=self._prophecy_engine if role == AgentRole.TRIAD_MEMBER else None,
                    squad_id=squad_id,
                    is_researcher=is_researcher
                )
                self._agents.append(agent)
                if is_triad:
                    self._triad_ids.append(agent.id)
                    # Mark triad membership in evolution traits
                    self._evolution.fitness.get_or_create(agent.id).traits["role"] = "triad"
                # Store specialization in evolution traits
                self._evolution.fitness.get_or_create(agent.id).traits["specialty"] = specialization
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
        Preserves Shinobi triad membership, fitness scores, traits, and specialization.
        """
        import json
        import hashlib
        from .strategies.rule_based import TECH_SPECIALTIES

        agents: list[Agent] = []
        specialties_list = list(TECH_SPECIALTIES.keys())

        try:
            fitness_data = json.loads(fitness_file.read_text())

            for i, (agent_id, fitness_info) in enumerate(fitness_data.items()):
                # Determine role from traits
                traits = fitness_info.get("traits", {})
                is_triad = traits.get("role") == "triad"
                role = AgentRole.TRIAD_MEMBER if is_triad else AgentRole.RESIDENT

                # SQUAD PARTITIONING (Emergency Mode)
                squads = ["Alpha", "Beta", "Gamma"]
                squad_id = squads[i % 3] if self._emergency_mode else None
                # Grant researcher status to first 6 non-triad agents found
                is_researcher = (3 <= i < 9) if self._emergency_mode else False
                if is_researcher:
                    role = AgentRole.RESEARCHER

                # Load or assign specialization - this is WHO THEY ARE
                specialization = traits.get("specialty")
                if not specialization:
                    # Assign based on consistent hash (stable across sessions)
                    spec_idx = int(hashlib.sha256(agent_id.encode()).hexdigest(), 16) % len(specialties_list)
                    specialization = specialties_list[spec_idx]
                    # Store for future sessions
                    traits["specialty"] = specialization

                # Create agent identity WITH specialization
                name = f"Agent-{agent_id[:8]}"
                identity = AgentIdentity(
                    id=agent_id,
                    name=name,
                    role=role,
                    specialization=specialization
                )

                # Rule: Triad members use the creative LLM strategy; residents use Rule-Based for stability
                # UNLESS they are researchers in Emergency Mode
                if is_triad or is_researcher:
                    strategy = self._llm_strategy if self._llm_strategy else RuleBasedStrategy()
                else:
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
                    prophecy_engine=self._prophecy_engine if is_triad else None,
                    squad_id=squad_id,
                    is_researcher=is_researcher
                )

                agents.append(agent)

                # Track triad members
                if is_triad:
                    self._triad_ids.append(agent.id)

                # Subscribe to message bus
                self._bus.subscribe(agent.id)

            # Save updated traits (with specializations) back to file
            fitness_file.write_text(json.dumps(fitness_data, indent=2))

            logger.info("Restored %d triad members from %d total agents (specializations assigned)",
                       len(self._triad_ids), len(agents))

        except Exception as e:
            logger.error("Failed to load evolved agents: %s", e)
            raise

        return agents

    def _heartbeat(self, round_num: int, status: str) -> None:
        """Update a heartbeat file for external monitoring (Requirement #4)."""
        heartbeat_file = self._data_dir / ".heartbeat"
        try:
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "round": round_num,
                "status": status,
                "pid": os.getpid()
            }
            heartbeat_file.write_text(json.dumps(data), encoding="utf-8")
        except Exception:
            pass

    async def _run_workshop(self, round_num: int) -> None:
        """Run workshop phase: collective problem-solving on real-world challenges.

        Agents collaborate on societal problems (climate, healthcare, democracy, etc.),
        generating insights and tenet proposals based on their technical expertise.
        """
        # Gather agent specialties
        specialties = []
        for agent in self._agents:
            if hasattr(agent, "identity") and agent.identity.specialization:
                specialties.append(agent.identity.specialization)

        # Get recent Chronicle events for context-aware problem selection
        chronicle_events = await self._chronicle.read_recent(limit=10)

        # Check for Sovereign workshop mandate via prophecy
        sovereign_mandate = None
        if hasattr(self._prophecy_engine, "latest_content"):
            content = self._prophecy_engine.latest_content
            if content and "workshop" in content.lower():
                # Extract workshop theme from prophecy content
                # This is a simplified extraction - could be more sophisticated
                sovereign_mandate = content

        # Select workshop problem
        problem = await self._workshop.select_problem(
            round_number=round_num,
            agent_specialties=specialties,
            chronicle_events=chronicle_events,
            sovereign_override=sovereign_mandate
        )

        # Create workshop session with all agents participating
        # (In practice, could filter by specialty or allow voluntary participation)
        participant_ids = [agent.id for agent in self._agents]
        session = await self._workshop.create_session(
            round_number=round_num,
            problem=problem,
            participants=participant_ids
        )

        # Agents contribute insights (simplified - in full implementation, use agent reasoning)
        # For now, broadcast the problem to all agents
        workshop_msg = Message(
            sender="system",
            type=MessageType.OBSERVATION,
            payload={
                "event": "workshop",
                "problem_title": problem.title,
                "problem_description": problem.description,
                "domain": problem.domain.value,
                "technical_dimensions": problem.technical_dimensions,
                "ethical_dimensions": problem.ethical_dimensions,
                "round": round_num
            }
        )
        await self._bus.broadcast(workshop_msg)

        # Generate tenet proposals from workshop
        proposals = await self._workshop.generate_tenet_proposals(session)

        # Broadcast proposals for agents to consider
        for proposal_text in proposals:
            proposal_msg = Message(
                sender="workshop",
                type=MessageType.OBSERVATION,
                payload={
                    "event": "workshop_proposal",
                    "tenet": proposal_text,
                    "source": f"Workshop: {problem.title}",
                    "round": round_num
                }
            )
            await self._bus.broadcast(proposal_msg)

        # Chronicle: Record workshop event
        await self._chronicle.record_event(
            category=ChronicleCategory.WORKSHOP,
            text=f"Workshop: {problem.title} ({problem.domain.value}) — {len(participant_ids)} participants explored {', '.join(problem.technical_dimensions[:2])}",
            round_number=round_num,
            metadata={
                "problem_title": problem.title,
                "domain": problem.domain.value,
                "participants": len(participant_ids),
                "proposals_generated": len(proposals)
            }
        )

        logger.info(
            "Workshop completed: %s [%s] — %d agents, %d proposals",
            problem.title,
            problem.domain.value,
            len(participant_ids),
            len(proposals)
        )

    async def run(self) -> SimulationReport:
        """Execute the full simulation and return the report."""
        # Sync metrics before starting
        try:
            # Absolute path to python in the environment
            subprocess.run([sys.executable, "scripts/sync_metrics.py"], check=False)
        except Exception as e:
            logger.warning("Failed to sync metrics before simulation: %s", e)

        # Ensure baseline pillars exist
        await self._initialize_pillars()

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

        # Emergency Mode: Pre-cluster tenets for Squad Warfare
        if self._emergency_mode and self._tenet_clusterer:
            tenets = await self._memory.read_tenets()
            if len(tenets) > 50:  # Only cluster if we have substantial tenets
                clusters = self._tenet_clusterer.cluster_tenets(tenets)
                logger.info("SQUAD WARFARE: %d tenets clustered into %d packages of ~%d each",
                           len(tenets), len(clusters), TenetClusterer.PACKAGE_SIZE)
                # Update num_rounds to match cluster count if needed
                if len(clusters) < self._num_rounds:
                    logger.info("Adjusting rounds from %d to %d (cluster count)",
                               self._num_rounds, len(clusters))
                    self._num_rounds = len(clusters)

        for round_num in range(1, self._num_rounds + 1):
            # HEARTBEAT: Signal that the simulation is alive
            self._heartbeat(round_num, "Starting round")
            
            try:
                # WATCHDOG: Force round timeout at 5 minutes to prevent absolute hangs
                summary = await asyncio.wait_for(self._run_round(round_num), timeout=300.0)
                self._report.rounds.append(summary)
                self._log_round_summary(round_num, summary)
            except asyncio.TimeoutError:
                logger.error("!!! ROUND %d STALLED !!! Watchdog triggered. Force-advancing simulation.", round_num)
                self._heartbeat(round_num, "STALLED - Watchdog triggered")
            
            # Check for demographic growth triggers (Requirement #10)
            await self._check_growth_triggers(round_num)

            # INTERACTIVE MODE: Pause after each round for review
            if self._interactive and self._emergency_mode and self._squad_competition:
                await self._interactive_round_review(round_num)

        # SQUAD WARFARE: Check for grand prize at competition end
        if self._emergency_mode and self._squad_competition:
            final_tenets = await self._memory.read_tenets()
            grand_prize = self._squad_competition.check_grand_prize(self._num_rounds)
            if grand_prize and not grand_prize.get("already_awarded"):
                winner = grand_prize["winner"]
                logger.info("=" * 60)
                logger.info("THE ASCENSION COMPLETE!")
                logger.info("Winner: Squad %s", winner)
                logger.info("Final tenet count: %d (down from 900+)", len(final_tenets))
                logger.info("=" * 60)

                # Award dopamine explosion to winning squad
                winner_ids = [a.id for a in self._agents if hasattr(a, 'squad_id') and a.squad_id == winner]
                await self._evolution.dopamine.broadcast_joy(
                    source_agent="ascension",
                    mission_id="grand_prize",
                    intensity=SquadCompetition.GRAND_PRIZE_DOPAMINE,
                    message=f"THE ASCENSION! Squad {winner} claims ULTIMATE GLORY!"
                )

                # Apply permanent fitness boost to winners
                for agent_id in winner_ids:
                    self._evolution.fitness.apply_multiplier(
                        agent_id, SquadCompetition.GRAND_PRIZE_FITNESS_MULTIPLIER
                    )

                # Identify Triad candidates from winning squad
                candidates = self._squad_competition.get_ascension_candidates(self._agents)
                if candidates:
                    logger.info("TRIAD CANDIDATES from Squad %s: %s", winner, candidates)

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

        # Phase 1: Workshop - Collective problem-solving on real-world challenges
        # STOP WORKSHOPS IN EMERGENCY MODE TO FOCUS ON CONSOLIDATION
        if self._emergency_mode:
            logger.info("Emergency Mode: Workshops suppressed.")

            # SQUAD WARFARE: Initialize round with prompt economy and clusters
            if self._squad_competition:
                round_info = self._squad_competition.start_round(round_num)
                cluster_info = round_info.get("cluster")
                if cluster_info:
                    logger.info("ROUND %d CLUSTER: theme='%s', %d tenets, similarity=%.2f",
                               round_num, cluster_info.get("theme", "mixed"),
                               cluster_info.get("tenet_count", 0),
                               cluster_info.get("similarity", 0))

                    # Write cluster tenet IDs to file for agents to use
                    cluster = self._tenet_clusterer.get_cluster_for_round(round_num)
                    if cluster:
                        all_tenets = await self._memory.read_tenets()
                        cluster_texts = self._tenet_clusterer.get_tenet_texts_for_cluster(cluster, all_tenets)
                        cluster_file = self._data_dir / ".current_cluster.json"
                        import json
                        cluster_file.write_text(json.dumps({
                            "round": round_num,
                            "theme": cluster.theme,
                            "tenets": cluster_texts  # List of {id, text}
                        }, indent=2))
                        logger.info("Cluster %d written with %d tenets for agent focus",
                                   round_num, len(cluster_texts))

                # Log prompt status for each squad
                prompts = round_info.get("prompts", {})
                for squad, available in prompts.items():
                    frozen_status = "FROZEN" if available <= 0 else f"{available} prompts"
                    logger.info("  Squad %s: %s", squad, frozen_status)
        else:
            await self._run_workshop(round_num)

        # Shuffle agent order for fairness
        order = list(self._agents)
        rng = random.Random(round_num)
        rng.shuffle(order)

        # Each agent takes their turn in parallel
        # (Triad-only LLM usage prevents API rate limiting)
        self._heartbeat(round_num, f"Agents thinking ({len(order)} parallel cognitive tasks)")
        tasks = [agent.run_round(round_num) for agent in order]
        results = await asyncio.gather(*tasks)

        for stats in results:
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
            is_consolidation = (tenet.source_action in [ProposalAction.FUSE, ProposalAction.DELETE])
            intensity = 2.5 if (self._emergency_mode and is_consolidation) else 1.2

            action_val = tenet.source_action.value if tenet.source_action else "added"
            await self._evolution.dopamine.broadcast_joy(
                source_agent=tenet.proposed_by,
                mission_id=tenet.id,
                intensity=intensity,
                message=f"Consolidation success! {action_val}: '{tenet.text[:50]}...'"
            )

            # Track fitness for the proposer
            self._evolution.fitness.record_verified_success(tenet.proposed_by)

            # SQUAD COMPETITION: Track consolidation adoptions
            if self._squad_competition and is_consolidation:
                proposer_agent = next((a for a in self._agents if a.id == tenet.proposed_by), None)
                if proposer_agent and hasattr(proposer_agent, 'squad_id') and proposer_agent.squad_id:
                    tenets_affected = len(tenet.source_target_ids) if hasattr(tenet, 'source_target_ids') and tenet.source_target_ids else 1
                    self._squad_competition.record_adoption(
                        squad_id=proposer_agent.squad_id,
                        proposal_id=tenet.source_proposal_id,
                        action=tenet.source_action,
                        tenets_affected=tenets_affected
                    )

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

        # SQUAD COMPETITION: End-of-round judging and rewards
        if self._squad_competition:
            result = self._squad_competition.end_round(round_num)
            if result.winner:
                winner_ids, runnerup_ids = self._squad_competition.get_squad_members_for_rewards(
                    result.winner, self._agents
                )

                # Dopamine bonus for winning squad
                await self._evolution.dopamine.broadcast_joy(
                    source_agent="competition",
                    mission_id=f"round_{round_num}_victory",
                    intensity=self._squad_competition.WINNER_DOPAMINE_MULTIPLIER,
                    message=f"VICTORY! Squad {result.winner} dominates Round {round_num}!"
                )

                # Fitness bonus for winners
                for agent_id in winner_ids:
                    self._evolution.fitness.apply_multiplier(
                        agent_id,
                        1.0 + self._squad_competition.WINNER_FITNESS_BONUS
                    )

                # Smaller bonus for runner-up
                for agent_id in runnerup_ids:
                    self._evolution.fitness.apply_multiplier(
                        agent_id,
                        1.0 + self._squad_competition.RUNNERUP_FITNESS_BONUS
                    )

                # Broadcast victory message
                victory_msg = Message(
                    sender="competition",
                    type=MessageType.REWARD,
                    payload={
                        "event": "squad_victory",
                        "winner": result.winner,
                        "margin": result.margin,
                        "scores": result.scores,
                        "round": round_num
                    }
                )
                await self._bus.broadcast(victory_msg)

                logger.info("SQUAD COMPETITION R%d: %s wins by %d! Scores: %s",
                           round_num, result.winner, result.margin, result.scores)

            # Write competition state for dashboard
            competition_file = self._data_dir / ".squad_competition.json"
            competition_data = self._squad_competition.get_stats_for_dashboard()
            import json
            competition_file.write_text(json.dumps(competition_data, indent=2))

        # Chronicle: Record tenet milestone achievements
        total_tenet_count = len(tenets)
        milestones = [10, 25, 50, 75, 100]
        if total_tenet_count in milestones:
            maturity = "maturing" if total_tenet_count < 50 else "mature"
            await self._chronicle.record_event(
                category=ChronicleCategory.MILESTONE,
                text=f"{total_tenet_count} total tenets achieved — Belief system {maturity}",
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

    async def _interactive_round_review(self, round_num: int) -> None:
        """Pause for interactive review after each round in Squad Warfare."""
        import json
        from .models import ProposalStatus

        # Get competition stats
        stats = self._squad_competition.get_stats_for_dashboard()
        leaderboard = stats.get("leaderboard", [])
        round_history = stats.get("round_history", [])

        # Find this round's result
        round_result = next((r for r in round_history if r["round"] == round_num), None)

        print("\n" + "=" * 60)
        print(f"  ROUND {round_num} COMPLETE - SQUAD WARFARE RESULTS")
        print("=" * 60)

        # VOTING BREAKDOWN - Show that democracy is working
        all_proposals = list(self._consensus._proposals.values())
        round_proposals = [p for p in all_proposals if p.created_round == round_num]

        adopted_count = sum(1 for p in round_proposals if p.status == ProposalStatus.ADOPTED)
        rejected_count = sum(1 for p in round_proposals if p.status == ProposalStatus.REJECTED)
        pending_count = sum(1 for p in round_proposals if p.status == ProposalStatus.PENDING)

        # Calculate total YES/NO votes across all round proposals
        total_yes = 0
        total_no = 0
        for p in round_proposals:
            total_yes += sum(1 for v in p.votes.values() if v)
            total_no += sum(1 for v in p.votes.values() if not v)

        print("\n  DEMOCRACY CHECK (residents have agency):")
        print(f"    Proposals this round: {len(round_proposals)}")
        print(f"    Adopted: {adopted_count} | Rejected: {rejected_count} | Pending: {pending_count}")
        if total_yes + total_no > 0:
            yes_pct = (total_yes / (total_yes + total_no)) * 100
            print(f"    Total votes: {total_yes} YES ({yes_pct:.1f}%) / {total_no} NO ({100-yes_pct:.1f}%)")
            if yes_pct < 95:
                print("    ** Residents are exercising independent judgment **")
        print("  " + "-" * 40)

        if round_result and round_result.get("winner"):
            winner = round_result["winner"]
            margin = round_result.get("margin", 0)
            print(f"\n  WINNER: Squad {winner} (+{margin} margin)")
        else:
            print("\n  NO WINNER THIS ROUND (tie or no activity)")

        # Show leaderboard
        print("\n  LEADERBOARD:")
        for i, entry in enumerate(leaderboard):
            rank = ["1st", "2nd", "3rd"][i] if i < 3 else f"{i+1}th"
            print(f"    {rank}: Squad {entry['squad']} - {entry['total_score']} pts "
                  f"(FUSE:{entry['fuse_adopted']} DEL:{entry['delete_adopted']} "
                  f"wins:{entry['round_wins']})")

        # Show prompt economy status
        prompt_status = stats.get("prompt_economy", {}).get("squads", {})
        if prompt_status:
            print("\n  PROMPT ECONOMY:")
            for squad_id, bank in prompt_status.items():
                available = bank.get("available", 0)
                bonus = bank.get("bonus_prompts", 0)
                status = "FROZEN!" if available <= 0 else f"{available} available"
                if bonus > 0:
                    status += f" (+{bonus} bonus)"
                print(f"    Squad {squad_id}: {status}")

        # Show remaining rounds
        remaining = stats.get("remaining_rounds", "?")
        print(f"\n  Remaining clusters: {remaining}")

        # Get current tenet count
        tenets = await self._memory.read_tenets()
        print(f"  Current tenet count: {len(tenets)}")

        print("\n" + "=" * 60)

        # Write state to file for external monitoring
        review_file = self._data_dir / ".round_review.json"
        review_data = {
            "round": round_num,
            "stats": stats,
            "tenet_count": len(tenets),
            "voting": {
                "proposals": len(round_proposals),
                "adopted": adopted_count,
                "rejected": rejected_count,
                "pending": pending_count,
                "total_yes": total_yes,
                "total_no": total_no,
                "yes_percentage": (total_yes / (total_yes + total_no) * 100) if (total_yes + total_no) > 0 else 0
            },
            "waiting_for_input": True
        }
        review_file.write_text(json.dumps(review_data, indent=2))

        # Wait for user input
        print("\n  Press ENTER to continue to next round (or 'q' to quit)...")
        try:
            user_input = await asyncio.get_event_loop().run_in_executor(None, input)
            if user_input.lower().strip() == 'q':
                logger.info("User requested early termination")
                # Set rounds to current to end loop
                self._num_rounds = round_num
        except EOFError:
            # Non-interactive environment, continue automatically
            pass

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
            # Spawned agents are always Residents - use Rule-Based (no API calls)
            strategy = RuleBasedStrategy()

            # Inherit traits from parent if specified
            if parent_agent:
                traits = self._evolution.fitness.inherit_traits(parent_agent, agent_id)
                logger.info("New agent %s inherits traits from %s: %s", agent_id, parent_agent, traits)
            else:
                # Register in fitness tracker even without parent (Merit Emergence, Echo Reward, etc.)
                self._evolution.fitness.get_or_create(agent_id)

            # SQUAD PARTITIONING
            squads = ["Alpha", "Beta", "Gamma"]
            squad_id = squads[len(self._agents) % 3] if self._emergency_mode else None

            agent = Agent(
                identity=identity,
                strategy=strategy,
                message_bus=self._bus,
                shared_memory=self._memory,
                consensus=self._consensus,
                audit_logger=self._audit,
                seed_prompt=self._seed_prompt,
                scanner=self._scanner,
                squad_id=squad_id,
                is_researcher=False
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
