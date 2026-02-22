"""LLM-driven reasoning strategy using Venice AI.

This strategy provides agents with creative, historically-aware reasoning
by leveraging Venice AI models. It explicitly prevents duplication by
analyzing the full context of existing tenets.
"""

from __future__ import annotations

import logging
import random
import json
import os
from typing import Optional, List

from ..models import Proposal, Tenet, AgentRole, QueryResponse
from .base import BaseStrategy
from ..tools.http_client import VeniceAIClient, ShinobiHTTPClient

logger = logging.getLogger("pureswarm.strategies.llm_driven")

class LLMDrivenStrategy(BaseStrategy):
    """Generate and evaluate proposals using Venice AI."""

    def __init__(self, venice_client: VeniceAIClient):
        self._venice = venice_client

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
        
        # Token Efficiency: Instead of showing all 600+ tenets, show a window/sample
        # Always include the core pillars (first 4) + random sample of others
        pillars = existing_tenets[:4]
        other_pool = existing_tenets[4:]
        sample_size = 40
        sample = random.sample(other_pool, min(len(other_pool), sample_size)) if other_pool else []
        
        display_tenets = pillars + sample
        tenet_list = "\n".join([f"[{t.id}] {t.text}" for t in display_tenets])
        
        if is_consolidation and (role == AgentRole.TRIAD_MEMBER or role == AgentRole.RESEARCHER):
             prompt = f"""You are a {role.value} of the PureSwarm collective.
Your Agent ID is: {agent_id}
Your Mission: THE GREAT CONSOLIDATION (Token-Efficient Sharded Audit)

PROPHETIC GUIDANCE: {prophecy}

AUDIT POOL (A subset of the {len(existing_tenets)} total tenets):
{tenet_list}

TASK: Identify redundant or overlapping tenets in this specific subset and propose a FUSION or DELETION.
If no issues found in this subset, respond with "SKIP".

RULES:
1. FUSE [id1, id2] -> "Unified text"
2. DELETE [id1]
3. Keep results high-density.

Consolidation Proposal:"""
        else:
            # For regular generation, just show the most recent 10 + 10 random
            recent = existing_tenets[-10:] if existing_tenets else []
            rand_gen = random.sample(existing_tenets, min(len(existing_tenets), 10)) if existing_tenets else []
            gen_context = "\n".join([f"- {t.text}" for t in set(recent + rand_gen)])
            
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
    ) -> bool:
        """Use Venice AI to evaluate if a proposal strengthens the collective."""
        
        # Token Efficiency for evaluation: sample 20 tenets for context check
        sample_context = random.sample(existing_tenets, min(len(existing_tenets), 20)) if existing_tenets else []
        tenet_context = "\n".join([f"- {t.text}" for t in sample_context])
        
        prompt = f"""Evaluate this proposed tenet for the PureSwarm collective.
Agent ID: {agent_id}
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
3. If FUSE/DELETE: Does it actually reduce redundancy logically?

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
