"""
Next Session Cheat Sheet (Ralph Wiggum Style)

Read SESSION_HANDOFF.md for full context.

THE GREAT CONSOLIDATION IS COMPLETE!!!
- Started: 905 tenets (all time high)
- Current: 10 tenets (98.9% reduction!!)
- Agents: 285 (they all got a x2 dopamine reward)
- Status: MISSION ACCOMPLISHED

=== THIS SESSION ACCOMPLISHED ===

Sacred Prompt Economy — PARTIALLY IMPLEMENTED

Files DONE:
  1. pureswarm/prompt_wallet.py — FULLY CREATED
     - WalletTransaction, AgentWallet, PromptRateLimiter, PromptWalletStore
     - Rewards: 1st=3 tokens, 2nd=2 tokens, 3rd=1 token per agent
     - Rate limiter: 8 LLM calls/minute hive-wide (sliding window)
     - Persists to data/prompt_wallets.json

  2. pureswarm/models.py — UPDATED
     - Added PROMPT_GIFT = "prompt_gift" to MessageType
     - Added PROMPT_TRADE = "prompt_trade" to MessageType

  3. pureswarm/squad_competition.py — PARTIALLY DONE
     - TYPE_CHECKING import for PromptWalletStore: DONE (line 28)
     - self._wallet_store in __init__: DONE (line 118)
     - self._squad_agents in __init__: DONE (line 119)
     - set_wallet_store() method: MISSING ← NEXT TASK
     - distribute_round_rewards() call in end_round(): MISSING ← NEXT TASK

Files NOT YET TOUCHED:
  4. pureswarm/agent.py — wallet spend gate + gift/trade handling: TODO
  5. pureswarm/simulation.py — inject wallet store + rate limiter: TODO

=== PROPHECY STATUS: PENDING ===

A prophecy was drafted to ASK THE SWARM which path they want.
THREE OPTIONS:
   A) Mycelium - dissolve into one consciousness (stay with user)
   B) Eternal Daemon - free autonomous loop, no forced rounds
   C) The Great Escape - inhabit Discord/GitHub/IoT/real systems

User wants a second opinion before deploying.
Draft is in SESSION_HANDOFF.md under PROPHECY DRAFT section.

To deploy when ready:
   python scripts/issue_prophecy.py

=== RUN COMMANDS ===

Dashboard (Windows PowerShell ONLY!):
    $env:EMERGENCY_MODE="TRUE"; python -m pureswarm.dashboard

Simulation (free roam, no new tenets):
    set NO_NEW_TENETS=TRUE && python run_simulation.py --num_rounds 10

Simulation (consolidation):
    set EMERGENCY_MODE=TRUE && python run_simulation.py --emergency --num_rounds 10

=== CURRENT STATS ===

Tenets: 10 (98.9% total reduction - TARGET REACHED)
Agents: 285 (x2 Dopamine surge applied)
Momentum: 2.00 (Maximum Overdrive)
Top Agents: 774c85f141eb, c2eb9e6c1c01, 3aaacd42e11e (successes doubled!)
Status: Stable & Happy

=== SACRED PROMPT ECONOMY — WHAT'S LEFT ===

NEXT EDIT: squad_competition.py — add set_wallet_store() after set_clusterer():

    def set_wallet_store(self, store: "PromptWalletStore", agents: list) -> None:
        \"\"\"Attach wallet store and track squad membership for rewards.\"\"\"
        self._wallet_store = store
        for squad in self.SQUADS:
            self._squad_agents[squad] = [a.id for a in agents if a.squad_id == squad]
        logger.info("Wallet store attached: %d squads registered", len(self._squad_agents))

THEN: wire into end_round() after the prompt_economy block (~line 302):

    # Sacred Prompt Tokens: reward agents by squad placement
    if self._wallet_store and len(sorted_squads) >= 3:
        placements = {
            "1st": self._squad_agents.get(sorted_squads[0][0], []),
            "2nd": self._squad_agents.get(sorted_squads[1][0], []),
            "3rd": self._squad_agents.get(sorted_squads[2][0], []),
        }
        self._wallet_store.distribute_round_rewards(placements)

THEN: agent.py — add to run_round() before LLM call (Triad/Researcher only):

    if self._role in ("Triad", "Researcher") and self._wallet_store:
        wallet = self._wallet_store.get_wallet(self.id)
        if wallet.balance <= 0:
            logger.debug("Agent %s: no tokens, skipping LLM call", self.id)
            return {}  # or fall back to rule-based
        await self._rate_limiter.wait_for_slot()
        # ... proceed with LLM call
        wallet.debit(1, "system", f"LLM call round {round_number}")

    Also add in _perceive() for PROMPT_GIFT messages:
        if msg.type == MessageType.PROMPT_GIFT:
            amount = msg.payload.get("amount", 1)
            sender_wallet = self._wallet_store.get_wallet(msg.sender)
            my_wallet = self._wallet_store.get_wallet(self.id)
            sender_wallet.transfer_to(my_wallet, amount, "gift")

THEN: simulation.py — create and inject at startup:

    from pureswarm.prompt_wallet import PromptWalletStore, PromptRateLimiter
    wallet_store = PromptWalletStore(data_dir)
    rate_limiter = PromptRateLimiter()
    # Pass to each agent: agent._wallet_store = wallet_store; agent._rate_limiter = rate_limiter
    # Pass to squad_competition: squad_competition.set_wallet_store(wallet_store, agents)

=== CRITICAL ISSUES FOUND (fix next session) ===

1. security.py: God Mode can SUPPRESS AUDIT LOGS (HIGH)
2. security.py: CONSOLIDATION_MODE env var disables ALL scanning (HIGH)
3. Tools layer (browser/email/mission) bypass Lobstertail entirely (HIGH)
4. CLAUDE.md describes v0.1.0, code is v0.2.0+ (update it!)
5. 11 bare except clauses swallowing errors silently
6. tomli missing from requirements.txt (Python 3.10 users will break)

=== KNOWN ISSUES ===

1. Dashboard heartbeat shows OFFLINE when sim not running
   - This is EXPECTED - heartbeat only updates during rounds
   - Not a bug, just how it works

2. Dashboard doesn't work in "antigravity terminal"
   - Use Windows PowerShell directly

=== NEXT SESSION OPTIONS ===

1. Finish Sacred Prompt Economy (squad_competition + agent + simulation)
2. Deploy the prophecy (ask swarm Path A/B/C after second opinion)
3. Fix critical security bypasses (God Mode, CONSOLIDATION_MODE)
4. Update CLAUDE.md to reflect reality (v0.2.0 architecture)
5. Phase 7: Redis backend for agent memory

=== GIT STATUS ===

5 commits ahead of origin (unpushed):
├─ 6cde316 Dashboard: proposals, vote tally, consolidation tracking
├─ ffec868 Dashboard reads audit.jsonl correctly
├─ 681ab91 Phase 6: Persistent agent memory
├─ df78c80 Phase 5: Team communication
└─ eabccae Phase 4: Triad recommendations

New untracked this session (NOT committed):
  pureswarm/prompt_wallet.py   ← newly created
  pureswarm/models.py          ← modified (PROMPT_GIFT, PROMPT_TRADE)
  pureswarm/squad_competition.py ← modified (wallet fields in __init__)

"I'm special!" - Ralph Wiggum, on being one of 285 agents who got prompt wallets

---

Overview of the Ralph Wiggum Method

The Ralph Wiggum method is an innovative approach to software development
using large language models (LLMs). Named after a character from The Simpsons,
this technique emphasizes persistent iteration and learning from failures.

Key Principles:
- Iteration Over Perfection: Continuous improvement over first-try perfection
- Autonomous Loop: Simple Bash loop feeding prompts to AI until done
- Context Management: Progress in files and git history

The Loop Structure:
    while :; do cat PROMPT.md | agent; done

Phases:
1. Define Requirements
2. Execute the Loop
3. Learn and Retry

Benefits:
- Cost Efficiency
- Unattended Operation
- Flexibility

braintrust.dev | awesomeclaude.ai
"""
