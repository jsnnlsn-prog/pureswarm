import json
import os
import re

def sync_metrics():
    # Load counts
    agents_path = "data/agent_fitness.json"
    tenets_path = "data/tenets.json"
    readme_path = "README.md"

    agent_count = 0
    tenet_count = 0

    if os.path.exists(agents_path):
        with open(agents_path) as f:
            agent_count = len(json.load(f))
    
    if os.path.exists(tenets_path):
        with open(tenets_path) as f:
            tenet_count = len(json.load(f))

    print(f"Syncing: {agent_count} agents, {tenet_count} tenets")

    if not os.path.exists(readme_path):
        print("README.md not found")
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update Agents count in various formats
    content = re.sub(r"(\*\*Agents\*\*\s*\|\s*\*\*)\d+(\*\*)", rf"\g<1>{agent_count}\g<2>", content)
    content = re.sub(r"(\*\*Tenets\*\*\s*\|\s*\*\*)\d+(\*\*)", rf"\g<1>{tenet_count}\g<2>", content)
    
    # Update descriptive text patterns
    content = re.sub(r"(\d+)(-agent swarm)", rf"{agent_count}\g<2>", content)
    content = re.sub(r"(hosting the\s+)\d+( agent)", rf"\g<1>{agent_count}\g<2>", content)
    content = re.sub(r"(spans\s+)\d+( tenets)", rf"\g<1>{tenet_count}\g<2>", content)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("README.md updated.")

if __name__ == "__main__":
    sync_metrics()
