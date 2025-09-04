"""
Semantic Architecture Feature Flags

Provides safe rollout and testing capabilities for the semantic orchestration system.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FeatureState(str, Enum):
    """Feature state options."""
    DISABLED = "disabled"
    TESTING = "testing"      # A/B testing mode
    BETA = "beta"           # Limited rollout
    ENABLED = "enabled"     # Full rollout


@dataclass
class FeatureConfig:
    """Configuration for a feature flag."""
    name: str
    state: FeatureState = FeatureState.DISABLED
    rollout_percentage: float = 0.0  # 0.0 to 1.0
    user_whitelist: list = None      # Specific users/sessions
    user_blacklist: list = None      # Excluded users/sessions
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.user_whitelist is None:
            self.user_whitelist = []
        if self.user_blacklist is None:
            self.user_blacklist = []
        if self.metadata is None:
            self.metadata = {}


class SemanticFeatureFlags:
    """
    Feature flag system for semantic architecture rollout.
    
    Provides safe, controlled rollout of semantic features with:
    - A/B testing capabilities
    - Gradual percentage rollout
    - User-specific overrides
    - Performance monitoring integration
    """
    
    def __init__(self, config_source: Optional[str] = None):
        """
        Initialize feature flags.
        
        Args:
            config_source: Path to JSON config file, or None to use environment/defaults
        """
        self.config_source = config_source
        self.features: Dict[str, FeatureConfig] = {}
        self._load_configuration()
    
    def _load_configuration(self):
        """Load feature flag configuration."""
        try:
            if self.config_source and os.path.exists(self.config_source):
                # Load from JSON file
                with open(self.config_source, 'r') as f:
                    config_data = json.load(f)
                self._parse_config_data(config_data)
                logger.info(f"Loaded feature flags from {self.config_source}")
            else:
                # Load from environment or defaults
                self._load_default_configuration()
                logger.info("Loaded default feature flag configuration")
                
        except Exception as e:
            logger.error(f"Failed to load feature configuration: {e}")
            self._load_default_configuration()
    
    def _parse_config_data(self, config_data: Dict[str, Any]):
        """Parse configuration data into FeatureConfig objects."""
        for feature_name, feature_data in config_data.items():
            try:
                # Handle datetime parsing
                if 'start_date' in feature_data and feature_data['start_date']:
                    feature_data['start_date'] = datetime.fromisoformat(feature_data['start_date'])
                if 'end_date' in feature_data and feature_data['end_date']:
                    feature_data['end_date'] = datetime.fromisoformat(feature_data['end_date'])
                
                self.features[feature_name] = FeatureConfig(
                    name=feature_name,
                    **feature_data
                )
                
            except Exception as e:
                logger.error(f"Failed to parse feature config for {feature_name}: {e}")
    
    def _load_default_configuration(self):
        """Load default feature configuration from environment variables."""
        # Semantic Parser Feature
        semantic_parser_state = os.getenv('SEMANTIC_PARSER_STATE', 'disabled').lower()
        semantic_parser_rollout = float(os.getenv('SEMANTIC_PARSER_ROLLOUT', '0.0'))
        
        self.features['semantic_parser'] = FeatureConfig(
            name='semantic_parser',
            state=FeatureState(semantic_parser_state) if semantic_parser_state in [s.value for s in FeatureState] else FeatureState.DISABLED,
            rollout_percentage=min(max(semantic_parser_rollout, 0.0), 1.0),
            metadata={'description': 'SemanticRequestParser instead of IntentParser'}
        )
        
        # Direct Agent Access Feature
        direct_access_state = os.getenv('DIRECT_AGENT_ACCESS_STATE', 'disabled').lower()
        direct_access_rollout = float(os.getenv('DIRECT_AGENT_ACCESS_ROLLOUT', '0.0'))
        
        self.features['direct_agent_access'] = FeatureConfig(
            name='direct_agent_access',
            state=FeatureState(direct_access_state) if direct_access_state in [s.value for s in FeatureState] else FeatureState.DISABLED,
            rollout_percentage=min(max(direct_access_rollout, 0.0), 1.0),
            metadata={'description': 'Bypass department routing for direct agent access'}
        )
        
        # Semantic State Management Feature
        semantic_state_state = os.getenv('SEMANTIC_STATE_MANAGEMENT_STATE', 'disabled').lower()
        semantic_state_rollout = float(os.getenv('SEMANTIC_STATE_MANAGEMENT_ROLLOUT', '0.0'))
        
        self.features['semantic_state_management'] = FeatureConfig(
            name='semantic_state_management',
            state=FeatureState(semantic_state_state) if semantic_state_state in [s.value for s in FeatureState] else FeatureState.DISABLED,
            rollout_percentage=min(max(semantic_state_rollout, 0.0), 1.0),
            metadata={'description': 'Enhanced state management with semantic context'}
        )
        
        # Full Semantic Orchestration Feature
        full_semantic_state = os.getenv('FULL_SEMANTIC_ORCHESTRATION_STATE', 'disabled').lower()
        full_semantic_rollout = float(os.getenv('FULL_SEMANTIC_ORCHESTRATION_ROLLOUT', '0.0'))
        
        self.features['full_semantic_orchestration'] = FeatureConfig(
            name='full_semantic_orchestration',
            state=FeatureState(full_semantic_state) if full_semantic_state in [s.value for s in FeatureState] else FeatureState.DISABLED,
            rollout_percentage=min(max(full_semantic_rollout, 0.0), 1.0),
            metadata={'description': 'Complete semantic architecture replacement'}
        )
    
    def is_enabled(self, feature_name: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> bool:
        """
        Check if a feature is enabled for a specific user/session.
        
        Args:
            feature_name: Name of the feature
            user_id: User identifier (optional)
            session_id: Session identifier (optional)
        
        Returns:
            bool: True if feature is enabled for this user/session
        """
        if feature_name not in self.features:
            logger.warning(f"Unknown feature flag: {feature_name}")
            return False
        
        feature = self.features[feature_name]
        
        # Check if feature is completely disabled
        if feature.state == FeatureState.DISABLED:
            return False
        
        # Check date constraints
        now = datetime.now()
        if feature.start_date and now < feature.start_date:
            return False
        if feature.end_date and now > feature.end_date:
            return False
        
        # Check explicit blacklist
        identifier = user_id or session_id
        if identifier and identifier in feature.user_blacklist:
            return False
        
        # Check explicit whitelist (overrides percentage)
        if identifier and identifier in feature.user_whitelist:
            return True
        
        # Check if fully enabled
        if feature.state == FeatureState.ENABLED:
            return True
        
        # Apply percentage rollout for testing/beta
        if feature.state in [FeatureState.TESTING, FeatureState.BETA]:
            return self._check_rollout_percentage(feature, identifier)
        
        return False
    
    def _check_rollout_percentage(self, feature: FeatureConfig, identifier: Optional[str]) -> bool:
        """Check if identifier falls within rollout percentage."""
        if not identifier:
            # No identifier, use random but consistent approach
            import random
            import time
            random.seed(int(time.time() / 3600))  # Changes hourly
            return random.random() < feature.rollout_percentage
        
        # Use hash of identifier for consistent rollout
        import hashlib
        hash_value = int(hashlib.md5(identifier.encode()).hexdigest()[:8], 16)
        bucket = (hash_value % 10000) / 10000.0  # 0.0 to 1.0
        
        return bucket < feature.rollout_percentage
    
    def get_feature_info(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a feature flag."""
        if feature_name not in self.features:
            return None
        
        feature = self.features[feature_name]
        return {
            'name': feature.name,
            'state': feature.state.value,
            'rollout_percentage': feature.rollout_percentage,
            'whitelist_size': len(feature.user_whitelist),
            'blacklist_size': len(feature.user_blacklist),
            'start_date': feature.start_date.isoformat() if feature.start_date else None,
            'end_date': feature.end_date.isoformat() if feature.end_date else None,
            'metadata': feature.metadata
        }
    
    def update_feature(self, feature_name: str, **kwargs):
        """Update a feature flag configuration."""
        if feature_name not in self.features:
            logger.warning(f"Cannot update unknown feature: {feature_name}")
            return False
        
        feature = self.features[feature_name]
        
        # Update allowed fields
        if 'state' in kwargs:
            feature.state = FeatureState(kwargs['state'])
        if 'rollout_percentage' in kwargs:
            feature.rollout_percentage = min(max(float(kwargs['rollout_percentage']), 0.0), 1.0)
        if 'user_whitelist' in kwargs:
            feature.user_whitelist = kwargs['user_whitelist']
        if 'user_blacklist' in kwargs:
            feature.user_blacklist = kwargs['user_blacklist']
        if 'start_date' in kwargs:
            feature.start_date = kwargs['start_date']
        if 'end_date' in kwargs:
            feature.end_date = kwargs['end_date']
        if 'metadata' in kwargs:
            feature.metadata.update(kwargs['metadata'])
        
        logger.info(f"Updated feature flag {feature_name}")
        return True
    
    def save_configuration(self, filepath: Optional[str] = None):
        """Save current configuration to file."""
        output_path = filepath or self.config_source or 'semantic_feature_flags.json'
        
        try:
            # Convert to serializable format
            config_data = {}
            for feature_name, feature in self.features.items():
                feature_dict = asdict(feature)
                # Handle datetime serialization
                if feature_dict['start_date']:
                    feature_dict['start_date'] = feature.start_date.isoformat()
                if feature_dict['end_date']:
                    feature_dict['end_date'] = feature.end_date.isoformat()
                # Convert enum to string
                feature_dict['state'] = feature.state.value
                # Remove name field (it's the key)
                feature_dict.pop('name', None)
                
                config_data[feature_name] = feature_dict
            
            with open(output_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Saved feature flag configuration to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_all_features(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all features."""
        return {name: self.get_feature_info(name) for name in self.features.keys()}
    
    def enable_feature_for_testing(self, feature_name: str, rollout_percentage: float = 0.1):
        """Quick enable a feature for testing."""
        return self.update_feature(
            feature_name,
            state='testing',
            rollout_percentage=rollout_percentage
        )
    
    def enable_feature_for_user(self, feature_name: str, user_id: str):
        """Add a user to the whitelist for a feature."""
        if feature_name in self.features:
            feature = self.features[feature_name]
            if user_id not in feature.user_whitelist:
                feature.user_whitelist.append(user_id)
                logger.info(f"Added {user_id} to whitelist for {feature_name}")
                return True
        return False
    
    def disable_feature_for_user(self, feature_name: str, user_id: str):
        """Add a user to the blacklist for a feature."""
        if feature_name in self.features:
            feature = self.features[feature_name]
            if user_id not in feature.user_blacklist:
                feature.user_blacklist.append(user_id)
                logger.info(f"Added {user_id} to blacklist for {feature_name}")
                return True
        return False


# Global instance for easy access
_global_flags: Optional[SemanticFeatureFlags] = None


def get_feature_flags() -> SemanticFeatureFlags:
    """Get global feature flags instance."""
    global _global_flags
    if _global_flags is None:
        _global_flags = SemanticFeatureFlags()
    return _global_flags


def is_semantic_enabled(feature_name: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> bool:
    """Quick check if a semantic feature is enabled."""
    return get_feature_flags().is_enabled(feature_name, user_id, session_id)


# Example usage and testing
if __name__ == "__main__":
    # Create feature flags
    flags = SemanticFeatureFlags()
    
    # Test different scenarios
    test_cases = [
        ("semantic_parser", "test_user_1", "session_1"),
        ("direct_agent_access", "test_user_2", "session_2"),
        ("full_semantic_orchestration", "test_user_3", "session_3"),
    ]
    
    print("Feature Flag Test Results:")
    print("=" * 50)
    
    for feature, user, session in test_cases:
        enabled = flags.is_enabled(feature, user, session)
        info = flags.get_feature_info(feature)
        print(f"{feature}:")
        print(f"  User {user}: {'✅ ENABLED' if enabled else '❌ DISABLED'}")
        print(f"  State: {info['state']}, Rollout: {info['rollout_percentage']:.1%}")
        print()
    
    # Test enabling a feature for testing
    print("Enabling semantic_parser for testing (10% rollout)...")
    flags.enable_feature_for_testing('semantic_parser', 0.1)
    
    # Test whitelisting a user
    print("Whitelisting test_user_1 for direct_agent_access...")
    flags.enable_feature_for_user('direct_agent_access', 'test_user_1')
    
    # Show updated results
    print("\nUpdated Results:")
    print("=" * 50)
    
    for feature, user, session in test_cases[:2]:  # Test first two
        enabled = flags.is_enabled(feature, user, session)
        print(f"{feature} for {user}: {'✅ ENABLED' if enabled else '❌ DISABLED'}")
    
    # Save configuration
    flags.save_configuration('test_flags.json')
    print("\n✅ Configuration saved to test_flags.json")