import re
from typing import List, Dict, Any
from ...models.context import EvidenceModel

class EntityExtractor:
    """
    Rule-based entity extraction for technologies, algorithms, and APIs.
    """
    
    TECH_PATTERNS = {
        "React": [r"React\.?js", r"React Native"],
        "Angular": [r"Angular"],
        "Vue": [r"Vue\.?js"],
        "Python": [r"Python"],
        "FastAPI": [r"FastAPI"],
        "Flask": [r"Flask"],
        "Django": [r"Django"],
        "Node.js": [r"Node\.?js"],
        "MongoDB": [r"MongoDB", r"Mongoose"],
        "PostgreSQL": [r"PostgreSQL", r"Postgres"],
        "MySQL": [r"MySQL"],
        "Redis": [r"Redis"],
        "Docker": [r"Docker", r"containerization"],
        "Kubernetes": [r"Kubernetes", r"K8s"]
    }
    
    ALGO_PATTERNS = {
        "CNN": [r"CNN", r"Convolutional Neural Network"],
        "RNN": [r"RNN", r"Recurrent Neural Network"],
        "LSTM": [r"LSTM"],
        "Dijkstra": [r"Dijkstra"],
        "A* Search": [r"A\*"],
        "Random Forest": [r"Random Forest"],
        "K-Means": [r"K-Means", r"K Means"]
    }
    
    API_PATTERNS = {
        "Stripe": [r"Stripe"],
        "Twilio": [r"Twilio"],
        "SendGrid": [r"SendGrid"],
        "AWS S3": [r"AWS S3", r"Simple Storage Service"],
        "Google Maps": [r"Google Maps API"]
    }

    @classmethod
    def extract_entities(cls, text: str) -> Dict[str, List[EvidenceModel]]:
        results = {
            "tech_stack": [],
            "algorithms": [],
            "apis": []
        }
        
        # Helper to match patterns and create EvidenceModels
        def match_and_append(patterns_dict, category_key):
            for name, patterns in patterns_dict.items():
                evidence = []
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        # Extract context around match
                        start = max(0, match.start() - 30)
                        end = min(len(text), match.end() + 30)
                        evidence.append(f"...{text[start:end]}...")
                
                if evidence:
                    results[category_key].append(EvidenceModel(
                        value=name,
                        confidence=0.8, # Base confidence for keyword match
                        evidence=list(set(evidence))[:3] # Top 3 unique pieces of evidence
                    ))

        match_and_append(cls.TECH_PATTERNS, "tech_stack")
        match_and_append(cls.ALGO_PATTERNS, "algorithms")
        match_and_append(cls.API_PATTERNS, "apis")
        
        return results
