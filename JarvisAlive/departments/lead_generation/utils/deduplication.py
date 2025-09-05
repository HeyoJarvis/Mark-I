"""Lead deduplication utilities."""

import logging
from typing import List, Set, Dict, Tuple
from ..models.lead_models import Lead

logger = logging.getLogger(__name__)


class LeadDeduplicator:
    """Handles lead deduplication to prevent duplicate contacts."""
    
    def __init__(self):
        self.seen_emails: Set[str] = set()
        self.seen_combinations: Set[Tuple[str, str]] = set()
    
    def deduplicate(self, leads: List[Lead]) -> List[Lead]:
        """Remove duplicate leads based on email and name+company combinations."""
        unique_leads = []
        duplicate_count = 0
        
        for lead in leads:
            if self._is_duplicate(lead):
                duplicate_count += 1
                logger.debug(f"Skipping duplicate lead: {lead.email}")
                continue
            
            # Mark as seen
            self._mark_as_seen(lead)
            unique_leads.append(lead)
        
        if duplicate_count > 0:
            logger.info(f"Removed {duplicate_count} duplicate leads from {len(leads)} total leads")
        
        return unique_leads
    
    def _is_duplicate(self, lead: Lead) -> bool:
        """Check if lead is a duplicate based on multiple criteria."""
        
        # Primary check: email address
        if lead.email.lower() in self.seen_emails:
            return True
        
        # Secondary check: name + company combination
        name_company_combo = (
            f"{lead.first_name} {lead.last_name}".lower().strip(),
            lead.company_name.lower().strip()
        )
        
        if name_company_combo in self.seen_combinations:
            return True
        
        return False
    
    def _mark_as_seen(self, lead: Lead):
        """Mark lead as seen to prevent future duplicates."""
        # Mark email as seen
        self.seen_emails.add(lead.email.lower())
        
        # Mark name+company combination as seen
        name_company_combo = (
            f"{lead.first_name} {lead.last_name}".lower().strip(),
            lead.company_name.lower().strip()
        )
        self.seen_combinations.add(name_company_combo)
    
    def reset(self):
        """Reset the deduplicator state."""
        self.seen_emails.clear()
        self.seen_combinations.clear()
    
    def get_duplicate_stats(self) -> Dict[str, int]:
        """Get statistics about seen leads."""
        return {
            "unique_emails": len(self.seen_emails),
            "unique_name_company_combos": len(self.seen_combinations)
        }
    
    @staticmethod
    def find_similar_leads(leads: List[Lead], similarity_threshold: float = 0.8) -> List[Tuple[Lead, Lead, float]]:
        """Find potentially similar leads that might be duplicates."""
        similar_pairs = []
        
        for i, lead1 in enumerate(leads):
            for lead2 in leads[i+1:]:
                similarity = LeadDeduplicator._calculate_similarity(lead1, lead2)
                if similarity >= similarity_threshold:
                    similar_pairs.append((lead1, lead2, similarity))
        
        return similar_pairs
    
    @staticmethod
    def _calculate_similarity(lead1: Lead, lead2: Lead) -> float:
        """Calculate similarity score between two leads."""
        score = 0.0
        total_checks = 0
        
        # Email similarity (exact match only)
        total_checks += 1
        if lead1.email.lower() == lead2.email.lower():
            score += 1.0
        
        # Name similarity
        total_checks += 1
        name1 = f"{lead1.first_name} {lead1.last_name}".lower().strip()
        name2 = f"{lead2.first_name} {lead2.last_name}".lower().strip()
        if name1 == name2:
            score += 1.0
        elif LeadDeduplicator._fuzzy_match(name1, name2):
            score += 0.7
        
        # Company similarity
        total_checks += 1
        if lead1.company_name.lower().strip() == lead2.company_name.lower().strip():
            score += 1.0
        elif LeadDeduplicator._fuzzy_match(lead1.company_name.lower(), lead2.company_name.lower()):
            score += 0.8
        
        # Job title similarity
        total_checks += 1
        if lead1.job_title.lower().strip() == lead2.job_title.lower().strip():
            score += 1.0
        elif LeadDeduplicator._fuzzy_match(lead1.job_title.lower(), lead2.job_title.lower()):
            score += 0.6
        
        return score / total_checks
    
    @staticmethod
    def _fuzzy_match(str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Simple fuzzy string matching."""
        if not str1 or not str2:
            return False
        
        # Simple character overlap method
        set1 = set(str1.replace(' ', ''))
        set2 = set(str2.replace(' ', ''))
        
        if not set1 or not set2:
            return False
        
        overlap = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return (overlap / union) >= threshold
