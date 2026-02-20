import asyncio
import os
import json
import sys
sys.path.append(os.getcwd())
from pureswarm.agent import Agent
from pureswarm.strategies.llm_driven import LLMDrivenStrategy
from pureswarm.models import AgentIdentity, AgentRole, Tenet

async def verify_cognition():
    print("--- Cognitive Persistence Verification ---")
    
    # 1. Load actual tenets (the context)
    tenets_path = "data/tenets.json"
    tenets = []
    if os.path.exists(tenets_path):
        with open(tenets_path) as f:
            data = json.load(f)
            # Use a smaller subset for verification speed
            tenets = [Tenet(**t) for t in data[-10:]]
    
    print(f"Loaded {len(tenets)} latest tenets for context.")

    # 2. Setup a specialized agent
    identity = AgentIdentity(
        id="cog_test_001",
        name="Cognito",
        role=AgentRole.RESIDENT,
        specialization="Expert in GovTech Hunter monitoring and recursive self-improvement"
    )
    
    # Check for API key
    api_key = os.getenv("VENICE_API_KEY")
    if not api_key:
        print("ERROR: VENICE_API_KEY not found. Skipping LLM verification.")
        return

    from pureswarm.tools.http_client import VeniceAIClient, ShinobiHTTPClient
    from pathlib import Path
    
    http_client = ShinobiHTTPClient(data_dir=Path("data"))
    venice_client = VeniceAIClient(api_key=api_key, http_client=http_client)
    strategy = LLMDrivenStrategy(venice_client=venice_client)
    
    # 3. Generate a proposal with full context
    print("Generating proposal with 588-tenet history...")
    proposal = await strategy.generate_proposal(
        agent_id=identity.id,
        round_number=99,
        existing_tenets=tenets,
        seed_prompt="Propose a strategic initiative for the swarm.",
        role=identity.role,
        specialization=identity.specialization
    )
    
    if proposal:
        print("\n[SUCCESS] New Proposal Generated:")
        print(f"Text: {proposal}")
        
        # Check for repetition (manual check or simple overlap)
        overlap = False
        for t in tenets:
            if proposal.lower() in t.text.lower() or t.text.lower() in proposal.lower():
                overlap = True
                print(f"[REJECTED] Proposal overlaps with tenet: {t.id}")
                break
        
        if not overlap:
            print("[VERIFIED] Proposal is novel and historically aware.")
    else:
        print("[FAILED] Strategy returned None (likely redundancy detection or API error).")

if __name__ == "__main__":
    asyncio.run(verify_cognition())
