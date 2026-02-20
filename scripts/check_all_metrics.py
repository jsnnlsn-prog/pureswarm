import json
import os

paths = [
    ("Local Data", "data/agent_fitness.json", "data/tenets.json"),
    ("Backup VM 0213", "backup_vm_data_20260213/data/agent_fitness.json", "backup_vm_data_20260213/data/tenets.json"),
    ("Cloud Swarm", "backups/cloud_swarm_backup/agent_fitness.json", "backups/cloud_swarm_backup/tenets.json"),
    ("Local Backup 0213", "data_local_backup_20260213/agent_fitness.json", "data_local_backup_20260213/tenets.json")
]

for name, ap, tp in paths:
    agents = 0
    tenets = 0
    if os.path.exists(ap):
        try:
            with open(ap) as f: agents = len(json.load(f))
        except: pass
    if os.path.exists(tp):
        try:
            with open(tp) as f: tenets = len(json.load(f))
        except: pass
    print(f"{name:20}: {agents} agents, {tenets} tenets")
