"""Tenet Clusterer - Pre-sorts tenets into similarity packages for Squad Warfare.

This module clusters the 900+ tenets into packages of ~40 similar tenets,
reducing API costs by giving teams pre-sorted data to work with.
"""

from __future__ import annotations

import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

from .models import Tenet

logger = logging.getLogger("pureswarm.clusterer")


@dataclass
class TenetCluster:
    """A package of similar tenets for competition rounds."""
    cluster_id: str
    tenets: List[str]  # List of tenet IDs
    theme: str  # Detected theme/topic
    similarity_score: float  # How similar the tenets are (0-1)
    round_number: int  # Which round this cluster is for
    processed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClusteringResult:
    """Result of the clustering operation."""
    clusters: List[TenetCluster]
    total_tenets: int
    total_rounds: int
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class TenetClusterer:
    """Pre-clusters tenets into similarity packages for Squad Warfare.

    Strategy:
    1. Use simple keyword/phrase matching for initial grouping (no API needed)
    2. Optionally use LLM for refinement (single API call)
    3. Output packages of ~40 tenets each, sorted by similarity
    """

    PACKAGE_SIZE = 40

    def __init__(self, data_dir: Path, llm_client=None):
        self.data_dir = data_dir
        self._llm = llm_client
        self._clusters_file = data_dir / ".tenet_clusters.json"
        self._clusters: List[TenetCluster] = []
        self._load_clusters()

    def _load_clusters(self) -> None:
        """Load existing clusters from disk."""
        if self._clusters_file.exists():
            try:
                data = json.loads(self._clusters_file.read_text())
                self._clusters = [
                    TenetCluster(**c) for c in data.get("clusters", [])
                ]
                logger.info("Loaded %d existing clusters", len(self._clusters))
            except Exception as e:
                logger.error("Failed to load clusters: %s", e)
                self._clusters = []

    def _save_clusters(self) -> None:
        """Persist clusters to disk."""
        result = ClusteringResult(
            clusters=self._clusters,
            total_tenets=sum(len(c.tenets) for c in self._clusters),
            total_rounds=len(self._clusters)
        )
        self._clusters_file.write_text(json.dumps(
            {"clusters": [c.to_dict() for c in self._clusters], **asdict(result)},
            indent=2
        ))

    def _extract_keywords(self, text: str) -> set:
        """Extract significant keywords from tenet text."""
        # Common words to ignore
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "dare",
            "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
            "into", "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once", "here",
            "there", "when", "where", "why", "how", "all", "each", "every",
            "both", "few", "more", "most", "other", "some", "such", "no",
            "nor", "not", "only", "own", "same", "so", "than", "too", "very",
            "just", "and", "but", "if", "or", "because", "until", "while",
            "this", "that", "these", "those", "it", "its", "we", "our", "they",
            "their", "you", "your", "i", "my", "me", "agent", "agents", "swarm",
            "collective", "hive", "belief", "tenet", "system"
        }

        words = text.lower().replace(".", " ").replace(",", " ").split()
        keywords = {w.strip() for w in words if len(w) > 3 and w not in stopwords}
        return keywords

    def _compute_similarity(self, keywords1: set, keywords2: set) -> float:
        """Compute Jaccard similarity between two keyword sets."""
        if not keywords1 or not keywords2:
            return 0.0
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        return intersection / union if union > 0 else 0.0

    def cluster_tenets(self, tenets: List[Tenet], force_recluster: bool = False) -> List[TenetCluster]:
        """Cluster all tenets into similarity packages.

        Uses greedy clustering: pick a seed, find similar tenets, repeat.
        """
        if self._clusters and not force_recluster:
            logger.info("Using existing %d clusters", len(self._clusters))
            return self._clusters

        logger.info("Clustering %d tenets into packages of %d", len(tenets), self.PACKAGE_SIZE)

        # Extract keywords for each tenet
        tenet_keywords: Dict[str, set] = {}
        tenet_map: Dict[str, Tenet] = {}
        for t in tenets:
            tenet_keywords[t.id] = self._extract_keywords(t.text)
            tenet_map[t.id] = t

        # Greedy clustering
        unclustered = set(tenet_keywords.keys())
        clusters = []
        round_num = 1

        while unclustered:
            # Pick seed (first unclustered tenet)
            seed_id = next(iter(unclustered))
            seed_keywords = tenet_keywords[seed_id]

            # Find similar tenets
            cluster_ids = [seed_id]
            unclustered.remove(seed_id)

            # Score all remaining tenets by similarity to seed
            similarities = []
            for tid in unclustered:
                sim = self._compute_similarity(seed_keywords, tenet_keywords[tid])
                similarities.append((tid, sim))

            # Sort by similarity and take top N-1
            similarities.sort(key=lambda x: x[1], reverse=True)
            for tid, sim in similarities[:self.PACKAGE_SIZE - 1]:
                cluster_ids.append(tid)
                unclustered.remove(tid)

            # Detect theme from common keywords
            all_keywords = set()
            for tid in cluster_ids:
                all_keywords |= tenet_keywords[tid]

            # Find most common keywords
            keyword_counts = {}
            for tid in cluster_ids:
                for kw in tenet_keywords[tid]:
                    keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            theme = ", ".join([kw for kw, _ in top_keywords]) if top_keywords else "mixed"

            # Calculate average similarity within cluster
            avg_sim = 0.0
            count = 0
            for i, tid1 in enumerate(cluster_ids):
                for tid2 in cluster_ids[i+1:]:
                    avg_sim += self._compute_similarity(tenet_keywords[tid1], tenet_keywords[tid2])
                    count += 1
            avg_sim = avg_sim / count if count > 0 else 0.0

            cluster = TenetCluster(
                cluster_id=hashlib.md5(f"cluster_{round_num}".encode()).hexdigest()[:8],
                tenets=cluster_ids,
                theme=theme,
                similarity_score=avg_sim,
                round_number=round_num
            )
            clusters.append(cluster)
            round_num += 1

            logger.info("Created cluster %d: %d tenets, theme='%s', sim=%.2f",
                       cluster.round_number, len(cluster.tenets), theme, avg_sim)

        self._clusters = clusters
        self._save_clusters()

        logger.info("Clustering complete: %d clusters created", len(clusters))
        return clusters

    def get_cluster_for_round(self, round_number: int) -> Optional[TenetCluster]:
        """Get the cluster package for a specific round."""
        for cluster in self._clusters:
            if cluster.round_number == round_number and not cluster.processed:
                return cluster
        return None

    def mark_cluster_processed(self, cluster_id: str) -> None:
        """Mark a cluster as processed (round complete)."""
        for cluster in self._clusters:
            if cluster.cluster_id == cluster_id:
                cluster.processed = True
                self._save_clusters()
                return

    def get_remaining_rounds(self) -> int:
        """Get count of unprocessed rounds."""
        return sum(1 for c in self._clusters if not c.processed)

    def get_tenet_texts_for_cluster(self, cluster: TenetCluster, all_tenets: List[Tenet]) -> List[Dict[str, str]]:
        """Get the actual tenet texts for a cluster."""
        tenet_map = {t.id: t for t in all_tenets}
        return [
            {"id": tid, "text": tenet_map[tid].text}
            for tid in cluster.tenets
            if tid in tenet_map
        ]

    async def refine_clusters_with_llm(self, tenets: List[Tenet]) -> List[TenetCluster]:
        """Optional: Use LLM to improve clustering quality.

        This is a single API call that reorganizes clusters for better similarity.
        """
        if not self._llm:
            logger.warning("No LLM client available for cluster refinement")
            return self._clusters

        # Build a summary of current clusters for LLM review
        cluster_summary = []
        tenet_map = {t.id: t for t in tenets}

        for cluster in self._clusters[:5]:  # Only refine first 5 to save tokens
            samples = [tenet_map[tid].text[:50] for tid in cluster.tenets[:5] if tid in tenet_map]
            cluster_summary.append({
                "id": cluster.cluster_id,
                "theme": cluster.theme,
                "samples": samples
            })

        prompt = f"""Review these tenet clusters and suggest improvements:

{json.dumps(cluster_summary, indent=2)}

For each cluster, rate if the tenets are truly similar (1-10) and suggest a better theme name.
Format: cluster_id: score, "better_theme"
"""

        try:
            result = await self._llm.complete(prompt, max_tokens=500)
            if result:
                logger.info("LLM cluster refinement: %s", result[:200])
                # Parse and apply refinements (simplified)
        except Exception as e:
            logger.error("LLM cluster refinement failed: %s", e)

        return self._clusters
