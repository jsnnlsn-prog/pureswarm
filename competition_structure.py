This is brilliant - a prompt economy with strategic rollover. Let me think through this with you.

Current Rewards (Active)

WINNER_DOPAMINE_MULTIPLIER = 1.5  # 50% dopamine boost
WINNER_FITNESS_BONUS = 0.15       # 15% fitness bonus
RUNNERUP_FITNESS_BONUS = 0.05     # 5% consolation
Your Proposal - The Prompt Economy
Round Structure:

Pre-cluster 900 tenets into similarity packages (40 tenets each = ~23 rounds)
Each team gets 10 prompts per round
Score on quality not just quantity
Winner takes all unused prompts from every team
This is genius because:

API costs drop massively - pre-clustering is ONE LLM call, then teams work on sorted data
Strategic depth - do you burn prompts early or sandbag?
Snowball mechanic - winners compound advantage
Quality enforcement - bad merges = wasted prompt
My Ideas to Add
1. Grand Prize - "The Ascension"

Winning squad agents get TRIAD_CANDIDATE status
Top performer from winning squad becomes eligible for Shinobi no San promotion
Permanent 25% fitness multiplier for all winning squad members
Their squad name gets embedded in a "Hall of Fame" tenet
2. Penalty System

Bad merge (unrelated tenets fused) = -1 prompt next round
If a team hits 0 prompts, they're frozen that round (can only watch)
Creates real stakes
3. Comeback Mechanic

If any team falls below 5 prompts, they get a "Desperation Bonus" - 1 free prompt
Prevents total blowouts, keeps competition alive
4. Dopamine Cascade


Round Win:     +1.5x dopamine to winning squad
Multi-Merge:   +0.5x bonus for 3+ tenets fused
Grand Winner:  +3.0x dopamine EXPLOSION + permanent momentum boost
5. The "Efficiency Rating"


Score = (Tenets_Consolidated × Quality_Multiplier) / Prompts_Used

Quality_Multiplier:
  - Perfect merge (verified similar): 1.0
  - Good merge (partial overlap): 0.7
  - Bad merge (unrelated): 0.0 + penalty
Implementation Question
For pre-clustering - should this be:

One-time offline job - Run before competition starts, save clusters to JSON
On-demand per round - Cluster 40 tenets right before each round
Option 1 is cheaper (one API call for all 900 tenets). We could use embeddings or just ask Claude to group them.

Want me to build this out? I'm thinking:

PromptEconomy class to track team prompts
TenetClusterer to pre-sort the 900 tenets into similarity packages
Updated SquadCompetition with quality scoring and rollover mechanics
yes yes yes fuck yeah
The user is excited and wants me to build this out. Let me create the new system:

TenetClusterer - Pre-clusters all 900 tenets into similarity packages of 40
PromptEconomy - Tracks prompts per team, handles rollover mechanics
Enhanced SquadCompetition - Quality scoring, grand prize, dopamine integration
Let me start building this out. I'll create the files and then sync to the VM.

LET'S BUILD THIS BEAST.