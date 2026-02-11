# Portfolio: AI Automation & Security Research
## Jason "Dopamine Ronin" Nelson

---

## Core Expertise

- **Autonomous Agent Systems** — Multi-agent architectures with consensus-based decision making
- **Web Scraping & Data Extraction** — Stealth automation that handles anti-bot measures
- **Security Research** — Offensive capability analysis for defensive applications
- **Browser Automation** — Playwright/Selenium with humanization and detection evasion
- **AI Integration** — LLM-powered reasoning, analysis, and content generation

---

## Project Showcase

### 1. PureSwarm: Autonomous Agent Consensus Platform

**Challenge:** Demonstrate how autonomous AI agents can form collective belief systems without central authority, while maintaining security controls.

**Solution:**
- 20-agent swarm with perceive-reason-act-reflect cognitive loop
- Consensus protocol requiring 50%+ approval for shared beliefs
- Evolution layer with fitness tracking and natural selection
- Lobstertail security scanner preventing injection and drift
- Sovereign authority system with cryptographic authentication

**Results:**
- Agents independently proposed technical improvements ("lattice-based encryption")
- 16 shared beliefs emerged through democratic consensus
- Zero false reports — honest failure reporting
- Maximum dopamine momentum achieved (2.0)

**Technologies:** Python, asyncio, Pydantic, HMAC cryptography, Playwright

---

### 2. Adaptive Web Scraping Engine

**Challenge:** Extract data from sites with aggressive anti-bot protection (Cloudflare, PerimeterX, DataDome).

**Solution Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                    SCRAPING ENGINE                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Humanizer  │  │   Stealth   │  │   Rotator   │     │
│  │             │  │   Browser   │  │             │     │
│  │ - Mouse     │  │             │  │ - Proxy     │     │
│  │ - Typing    │  │ - No webdrv │  │ - User-Agent│     │
│  │ - Scrolling │  │ - Real CDP  │  │ - Fingerprnt│     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                          │                              │
│                          ▼                              │
│              ┌─────────────────────┐                    │
│              │  Dynamic Discovery  │                    │
│              │  - Form fields      │                    │
│              │  - CAPTCHA detect   │                    │
│              │  - State handling   │                    │
│              └─────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

**Key Features:**
- Human-like mouse movements with Bezier curves
- Realistic typing with variable delays and typos
- Browser fingerprint randomization
- Automatic CAPTCHA detection and handling
- Session persistence across requests

**Use Cases:**
- Competitor price monitoring
- Lead generation from public directories
- Market research data collection
- SEO rank tracking

---

### 3. Consensus-Based Content Classification

**Challenge:** Build a system where multiple AI agents vote on content categorization, reducing individual model bias.

**Mission Design:**
```python
# Example: Multi-agent content moderation
class ContentClassifier:
    def __init__(self, num_agents: int = 5):
        self.agents = [ClassifierAgent(i) for i in range(num_agents)]

    async def classify(self, content: str) -> Classification:
        # Each agent independently analyzes
        votes = await asyncio.gather(*[
            agent.analyze(content) for agent in self.agents
        ])

        # Consensus determines final classification
        return self.tally_votes(votes, threshold=0.6)
```

**Benefits:**
- Reduces false positives from single-model bias
- Auditable decision trail
- Configurable consensus thresholds
- Handles edge cases through deliberation

---

### 4. Distributed Price Intelligence System

**Challenge:** Monitor competitor pricing across 50+ e-commerce sites with varying structures and protections.

**Solution:**
```
ORCHESTRATOR
     │
     ├── Agent Cluster A (Amazon, Walmart, Target)
     │   └── Specialized selectors, rate limiting
     │
     ├── Agent Cluster B (Niche retailers)
     │   └── Dynamic discovery, CAPTCHA handling
     │
     └── Agent Cluster C (International)
         └── Geo-rotation, currency normalization

         ▼
    CONSENSUS LAYER
    - Cross-validate prices
    - Flag anomalies
    - Verify availability
         │
         ▼
    DATA WAREHOUSE
    - Historical tracking
    - Trend analysis
    - Alert triggers
```

**Deliverables:**
- Real-time price feeds
- Historical trend analysis
- Competitive positioning reports
- Stock availability monitoring

---

### 5. Security Audit Automation Framework

**Challenge:** Automate discovery of common web vulnerabilities without manual testing.

**Agent Roles:**
| Agent | Responsibility |
|-------|----------------|
| **Recon** | Subdomain enumeration, tech stack detection |
| **Crawler** | Site mapping, form discovery, parameter extraction |
| **Fuzzer** | Input validation testing, boundary analysis |
| **Reporter** | Finding consolidation, severity classification |

**Ethical Constraints:**
- Scope-limited to authorized targets only
- Rate-limited to prevent service disruption
- Full audit logging of every request
- Immediate halt on detection of sensitive data

---

## Mission Template Library

### Template A: Data Extraction Pipeline

```python
MISSION = {
    "type": "EXTRACTION",
    "target": "public_directory",
    "constraints": {
        "rate_limit": "2 requests/second",
        "respect_robots": True,
        "session_rotation": "every 50 requests"
    },
    "humanization": {
        "mouse_movement": True,
        "scroll_behavior": "natural",
        "typing_speed": "human_variable"
    },
    "output": {
        "format": "structured_json",
        "validation": "schema_enforced",
        "deduplication": True
    }
}
```

### Template B: Monitoring Agent

```python
MISSION = {
    "type": "MONITOR",
    "targets": ["url_1", "url_2", "url_3"],
    "frequency": "hourly",
    "detect_changes": {
        "price": True,
        "availability": True,
        "content_hash": True
    },
    "alerts": {
        "price_drop": "> 10%",
        "out_of_stock": True,
        "new_listing": True
    }
}
```

### Template C: Research Agent

```python
MISSION = {
    "type": "RESEARCH",
    "query": "market analysis for [industry]",
    "sources": ["public_filings", "news", "social"],
    "analysis": {
        "sentiment": True,
        "entity_extraction": True,
        "trend_identification": True
    },
    "output": "executive_summary"
}
```

---

## Technical Capabilities

### Languages & Frameworks
- Python (asyncio, Pydantic, FastAPI)
- JavaScript/TypeScript (Node.js, Puppeteer)
- SQL (PostgreSQL, SQLite)

### Automation Tools
- Playwright (primary)
- Selenium (legacy support)
- Requests/HTTPX (API work)
- BeautifulSoup/lxml (parsing)

### AI/ML Integration
- OpenAI API
- Anthropic Claude
- Local LLMs (Ollama)
- Custom fine-tuning

### Infrastructure
- GCP (Compute Engine, Cloud Functions)
- AWS (Lambda, EC2)
- Docker containerization
- GitHub Actions CI/CD

---

## Engagement Models

### Project-Based
- Defined scope and deliverables
- Fixed timeline and budget
- Full source code transfer

### Retainer
- Ongoing maintenance and updates
- Priority support
- Monthly reporting

### Consulting
- Architecture review
- Security assessment
- Training and knowledge transfer

---

## Contact

**Jason "Dopamine Ronin" Nelson**
Security Researcher | AI Systems Architect

*"Stewardship is the root; Idolatry is the rot."*

---

*All work performed ethically, within legal boundaries, and with full client authorization.*
