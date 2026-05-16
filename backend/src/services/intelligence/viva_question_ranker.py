from typing import List
from ...models.context import VivaTarget

class VivaQuestionRanker:
    """
    Ranks viva questions based on implementation depth, security importance, and architectural significance.
    """
    @staticmethod
    def rank_targets(targets: List[VivaTarget]) -> List[VivaTarget]:
        # Scoring logic:
        # - Hard difficulty: +0.3
        # - Security topic: +0.2
        # - Architecture topic: +0.1
        # - Implementation depth keywords: +0.2
        
        depth_keywords = ["middleware", "lifecycle", "flow", "failure", "risk", "tradeoff", "why"]
        
        for t in targets:
            score = t.importance_score
            if t.difficulty == "hard":
                score += 0.3
            if t.topic.lower() == "security":
                score += 0.2
            if t.topic.lower() == "architecture":
                score += 0.1
                
            if any(k in t.focus.lower() for k in depth_keywords):
                score += 0.2
                
            t.importance_score = min(1.0, score)
            
        # Sort by score descending
        return sorted(targets, key=lambda x: x.importance_score, reverse=True)
