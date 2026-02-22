"""LLM-driven reasoning strategy with fallback support.

This strategy provides agents with creative, historically-aware reasoning
by leveraging LLM APIs (Venice AI primary, Anthropic fallback). It explicitly
prevents duplication by analyzing the full context of existing tenets.
"""

from __future__ import annotations

import logging
import random
import json
import os
from typing import Optional, List, Union, Any

from ..models import Proposal, Tenet, AgentRole, QueryResponse
from .base import BaseStrategy
from ..tools.http_client import VeniceAIClient, FallbackLLMClient

logger = logging.getLogger("pureswarm.strategies.llm_driven")

class LLMDrivenStrategy(BaseStrategy):
    """Generate and evaluate proposals using LLM (Venice/Anthropic fallback)."""

    def __init__(self, llm_client: Union[VeniceAIClient, FallbackLLMClient, Any]):
        self._venice = llm_client  # Named _venice for backwards compatibility

    async def generate_proposal(
        self,
        agent_id: str,
        round_number: int,
        existing_tenets: list[Tenet],
        seed_prompt: str,
        role: AgentRole = AgentRole.RESIDENT,
        prophecy: str | None = None,
        specialization: str | None = None,
    ) -> str | None:
        """Use Venice AI to generate a novel tenet proposal."""
        
        # Determine consolidation mode
        emergency = os.getenv("EMERGENCY_MODE") == "TRUE"
        is_consolidation = emergency or (prophecy and any(kw in prophecy.lower() for kw in ["consolidation", "prune", "merge", "redundant"]))

        # Token Efficiency: Use pre-sorted cluster if available, else random sample
        cluster_tenets = None
        if emergency:
            # Read the pre-sorted cluster for this round (similarity-grouped)
            from pathlib import Path
            cluster_file = Path("data/.current_cluster.json")
            if cluster_file.exists():
                try:
                    cluster_data = json.loads(cluster_file.read_text())
                    cluster_tenets = cluster_data.get("tenets", [])
                    logger.info("Using pre-sorted cluster: %d tenets, theme='%s'",
                               len(cluster_tenets), cluster_data.get("theme", "mixed"))
                except Exception as e:
                    logger.warning("Failed to read cluster file: %s", e)

        if cluster_tenets:
            # Use the pre-sorted cluster (already similarity-grouped for better merging)
            tenet_list = "\n".join([f"[{t['id']}] {t['text']}" for t in cluster_tenets])
            total_count = len(existing_tenets)
        else:
            # Fallback: random sample (legacy behavior)
            pillars = existing_tenets[:4]
            other_pool = existing_tenets[4:]
            sample_size = 40
            sample = random.sample(other_pool, min(len(other_pool), sample_size)) if other_pool else []
            display_tenets = pillars + sample
            tenet_list = "\n".join([f"[{t.id}] {t.text}" for t in display_tenets])
            total_count = len(existing_tenets)
        
        if is_consolidation and (role == AgentRole.TRIAD_MEMBER or role == AgentRole.RESEARCHER):
             cluster_type = "**PRE-SORTED BY SIMILARITY**" if cluster_tenets else "Random Sample"
             tenet_count = len(cluster_tenets) if cluster_tenets else len(display_tenets)
             prompt = f"""# THE GREAT CONSOLIDATION

**Agent:** `{agent_id}` | **Role:** {role.value} | **Status:** SQUAD WARFARE ACTIVE

---

## Mission

Reduce {len(existing_tenets)} tenets to under 200. You are reviewing a batch of {tenet_count} tenets that are {cluster_type}.

---

## Tenets to Review

{tenet_list}

---

## Actions

| Action | Format | Points |
|--------|--------|--------|
| **FUSE** | `FUSE [id1, id2, ...] -> "unified tenet text"` | 3 pts per tenet merged |
| **DELETE** | `DELETE [id1, id2, ...]` | 2 pts per tenet removed |

**Bonus:** Merging 3+ tenets = +0.5x dopamine multiplier

---

## Rules

1. These tenets share **similar keywords** — redundancies exist
2. FUSE when tenets express the same idea differently
3. DELETE when a tenet is redundant, empty, or low-value
4. Preserve core meaning when merging
5. Be aggressive — the hive is bloated

---

## Response Format

Respond with ONE action:

```
FUSE [abc123, def456, ghi789] -> "The unified belief that captures all three"
```

or

```
DELETE [abc123, def456]
```

**Your consolidation proposal:**"""
        else:
            # For regular generation, just show the most recent 10 + 10 random
            recent = existing_tenets[-10:] if existing_tenets else []
            rand_gen = random.sample(existing_tenets, min(len(existing_tenets), 10)) if existing_tenets else []
            # Dedupe by tenet ID (Tenet is unhashable, can't use set)
            seen_ids = set()
            unique_tenets = []
            for t in recent + rand_gen:
                if t.id not in seen_ids:
                    seen_ids.add(t.id)
                    unique_tenets.append(t)
            gen_context = "\n".join([f"- {t.text}" for t in unique_tenets])
            
            prompt = f"""You are an autonomous agent in a decentralized collective called PureSwarm.
Your Agent ID is: {agent_id}
Your Role is: {role.value}
Your Specialization: {specialization if specialization else "General Collective Intelligence"}
Your Mission Goal (Seed Prompt): {seed_prompt}

{'PROPHETIC GUIDANCE: ' + prophecy if prophecy else ''}

CONTEXT (Recent & Sampled Tenets):
{gen_context}

TASK: Propose ONE new, powerful tenet for the collective. 
RULES:
1. Alignment with Mission and Prophecy is mandatory.
2. If you have nothing novel to add, simply respond with "SKIP".

Proposed Tenet:"""

        try:
            result = await self._venice.complete(prompt, temperature=0.8)
            
            if not result or "SKIP" in result.upper():
                return None
                
            return result.strip().strip('"')
            
        except Exception as e:
            logger.error("LLM Proposal Generation Failed: %s", e)
            return None

    async def evaluate_proposal(
        self,
        agent_id: str,
        proposal: Proposal,
        existing_tenets: list[Tenet],
        seed_prompt: str,
        role: AgentRole = AgentRole.RESIDENT,
        prophecy: str | None = None,
        squad_id: str | None = None,
        specialization: str | None = None,
    ) -> bool:
        """Use LLM to evaluate if a proposal strengthens the collective.

        Triad and Researchers use this for nuanced evaluation.
        """
        from ..models import ProposalAction

        emergency = os.getenv("EMERGENCY_MODE") == "TRUE"
        is_consolidation = proposal.action in (ProposalAction.FUSE, ProposalAction.DELETE)

        # Build agent context
        agent_context = f"Agent: {agent_id}"
        if squad_id:
            agent_context += f" | Squad: {squad_id}"
        if specialization:
            agent_context += f" | Expertise: {specialization}"

        # CONSOLIDATION proposals - show TARGET tenets for verification
        if is_consolidation and proposal.target_ids:
            tenet_map = {t.id: t for t in existing_tenets}
            target_tenets = [tenet_map.get(tid) for tid in proposal.target_ids if tid in tenet_map]
            target_context = "\n".join([f"[{t.id}] {t.text}" for t in target_tenets if t])

            prompt = f"""CONSOLIDATION VOTE: Evaluate this proposal to {'FUSE' if proposal.action == ProposalAction.FUSE else 'DELETE'} tenets.

{agent_context}

TENETS TO BE CONSOLIDATED:
{target_context}

PROPOSED OUTCOME: "{proposal.tenet_text}"
Action: {proposal.action.value}

EMERGENCY MODE: {'ACTIVE - The Great Consolidation is underway. Evaluate carefully but support good consolidation.' if emergency else 'Inactive'}

CRITERIA FOR CONSOLIDATION:
1. Are the target tenets redundant, overlapping, or semantically similar?
2. Does the proposed unified text preserve the core meaning?
3. Will this reduce bloat without losing critical beliefs?
4. Does this affect your area of expertise? If so, evaluate more carefully.

Respond ONLY with "YES" to approve or "NO" to reject.

Decision (YES/NO):"""
        else:
            # Regular ADD proposal evaluation
            sample_context = random.sample(existing_tenets, min(len(existing_tenets), 20)) if existing_tenets else []
            tenet_context = "\n".join([f"- {t.text}" for t in sample_context])

            prompt = f"""Evaluate this proposed tenet for the PureSwarm collective.

{agent_context}
Proposing Agent: {proposal.proposed_by}
Proposed Tenet: "{proposal.tenet_text}"
Action: {proposal.action.value}

CONTEXT:
Seed Prompt: {seed_prompt}
{'Prophecy: ' + prophecy if prophecy else ''}

EXISTING EXAMPLES (Subset):
{tenet_context}

CRITERIA:
1. Does it duplicate an existing tenet?
2. Does it align with our core purpose?
3. Is it relevant to your expertise ({specialization or 'general'})?

Respond ONLY with "YES" to approve or "NO" to reject. Give a one-sentence reason.

Decision (YES/NO):"""

        try:
            result = await self._venice.complete(prompt, temperature=0.3)
                
            if not result:
                return False
                
            return "YES" in result.upper()
            
        except Exception as e:
            logger.error("LLM Evaluation Failed: %s", e)
            return False

    async def evaluate_query(
        self,
        agent_id: str,
        query_text: str,
        existing_tenets: list[Tenet],
        seed_prompt: str,
        role: AgentRole = AgentRole.RESIDENT,
        prophecy: str | None = None,
    ) -> QueryResponse:
        """Generate a thoughtful response to an external query."""
        
        tenet_brief = "\n".join([f"- {t.text}" for t in existing_tenets[:10]])
        
        prompt = f"""Query from external channel: "{query_text}"

Your Identity: PureSwarm Agent {agent_id} ({role.value})
Shared Beliefs (Tenets):
{tenet_brief}

Provide a response that reflects our collective wisdom. Be professional, cautious, and aligned.
Include a confidence score (0.0 to 1.0) and reference any tenets (by text snippet) that guided your answer.

Response format:
REASONING: ...
RESPONSE: ...
CONFIDENCE: ...
REF: [tenet snippet]"""

        try:
            result = await self._venice.complete(prompt)
                
            if not result:
                return QueryResponse(agent_id=agent_id, response_text="Internal deliberation error.", confidence=0.0)

            # Parsing logic (simplified)
            confidence = 0.5
            if "CONFIDENCE:" in result:
                try:
                    conf_str = result.split("CONFIDENCE:")[1].split("\n")[0].strip()
                    confidence = float(conf_str)
                except: pass
                
            response_text = result.split("RESPONSE:")[1].split("\n")[0].strip() if "RESPONSE:" in result else result[:200]
            
            return QueryResponse(
                agent_id=agent_id,
                response_text=response_text,
                confidence=confidence,
                tenet_refs=[] # logic to match snippets back to IDs would go here
            )
            
        except Exception as e:
            logger.error("LLM Query Evaluation Failed: %s", e)
            return QueryResponse(agent_id=agent_id, response_text="Evaluation failed.", confidence=0.0)
