"""
Production Deployment Configuration

Comprehensive production-ready configuration management for the parallel workflow system:
- Environment-specific configurations
- Security settings and API key management
- Monitoring and observability setup
- Performance tuning and resource limits
- Health checks and service discovery
- Deployment validation and rollback procedures
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import json
from enum import Enum

logger = logging.getLogger(__name__)


class DeploymentEnvironment(Enum):
    """Deployment environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SecurityLevel(Enum):
    """Security configuration levels."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    ENTERPRISE = "enterprise"


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_ssl: bool = False
    redis_max_connections: int = 100
    redis_health_check_interval: int = 30


@dataclass
class APIConfig:
    """API service configuration."""
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_base_url: Optional[str] = None
    openai_base_url: Optional[str] = None
    api_timeout: int = 300
    max_retries: int = 3
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60


@dataclass
class AgentPoolConfig:
    """Agent pool configuration."""
    max_agents_per_type: int = 3
    agent_startup_timeout: int = 30
    agent_health_check_interval: int = 60
    agent_restart_on_failure: bool = True
    agent_max_memory_mb: int = 512
    agent_max_cpu_percent: int = 80


@dataclass
class WorkflowConfig:
    """Workflow execution configuration."""
    max_concurrent_workflows: int = 10
    workflow_timeout_seconds: int = 1800  # 30 minutes
    max_recursion_limit: int = 100
    enable_checkpointing: bool = True
    checkpoint_interval_seconds: int = 30
    enable_workflow_recovery: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    enable_metrics: bool = True
    metrics_port: int = 8080
    enable_tracing: bool = True
    enable_health_checks: bool = True
    health_check_port: int = 8081
    log_level: str = "INFO"
    log_format: str = "json"
    enable_prometheus: bool = True
    enable_grafana_dashboard: bool = True


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    security_level: SecurityLevel = SecurityLevel.ENHANCED
    enable_api_key_rotation: bool = True
    api_key_rotation_days: int = 30
    enable_request_signing: bool = False
    enable_rate_limiting: bool = True
    enable_ip_whitelisting: bool = False
    allowed_ips: List[str] = field(default_factory=list)
    enable_audit_logging: bool = True
    encrypt_at_rest: bool = True
    encrypt_in_transit: bool = True


@dataclass
class ResourceLimits:
    """Resource limit configuration."""
    max_memory_mb: int = 2048
    max_cpu_percent: int = 80
    max_disk_usage_mb: int = 5120
    max_open_files: int = 1024
    max_network_connections: int = 200


class ProductionConfig:
    """Comprehensive production configuration manager."""
    
    def __init__(self, environment: DeploymentEnvironment = DeploymentEnvironment.PRODUCTION):
        self.environment = environment
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Load configuration based on environment
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration based on deployment environment."""
        self.logger.info(f"Loading configuration for {self.environment.value} environment")
        
        if self.environment == DeploymentEnvironment.DEVELOPMENT:
            self._load_development_config()
        elif self.environment == DeploymentEnvironment.STAGING:
            self._load_staging_config()
        else:  # PRODUCTION
            self._load_production_config()
    
    def _load_development_config(self):
        """Load development environment configuration."""
        self.database = DatabaseConfig(
            redis_host="localhost",
            redis_port=6379,
            redis_max_connections=10
        )
        
        self.api = APIConfig(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            api_timeout=60,
            max_retries=2,
            rate_limit_enabled=False
        )
        
        self.agent_pool = AgentPoolConfig(
            max_agents_per_type=2,
            agent_max_memory_mb=256
        )
        
        self.workflow = WorkflowConfig(
            max_concurrent_workflows=3,
            workflow_timeout_seconds=300
        )
        
        self.monitoring = MonitoringConfig(
            log_level="DEBUG",
            enable_prometheus=False,
            enable_grafana_dashboard=False
        )
        
        self.security = SecurityConfig(
            security_level=SecurityLevel.BASIC,
            enable_api_key_rotation=False,
            enable_audit_logging=False
        )
        
        self.resources = ResourceLimits(
            max_memory_mb=1024,
            max_cpu_percent=60
        )
    
    def _load_staging_config(self):
        """Load staging environment configuration."""
        self.database = DatabaseConfig(
            redis_host=os.getenv("REDIS_HOST", "redis-staging"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_password=os.getenv("REDIS_PASSWORD"),
            redis_ssl=True,
            redis_max_connections=50
        )
        
        self.api = APIConfig(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            api_timeout=180,
            max_retries=3,
            rate_limit_enabled=True,
            rate_limit_requests_per_minute=30
        )
        
        self.agent_pool = AgentPoolConfig(
            max_agents_per_type=3,
            agent_max_memory_mb=384
        )
        
        self.workflow = WorkflowConfig(
            max_concurrent_workflows=5,
            workflow_timeout_seconds=900
        )
        
        self.monitoring = MonitoringConfig(
            log_level="INFO",
            enable_prometheus=True,
            enable_grafana_dashboard=True
        )
        
        self.security = SecurityConfig(
            security_level=SecurityLevel.ENHANCED,
            enable_api_key_rotation=True,
            enable_audit_logging=True
        )
        
        self.resources = ResourceLimits(
            max_memory_mb=1536,
            max_cpu_percent=70
        )
    
    def _load_production_config(self):
        """Load production environment configuration."""
        self.database = DatabaseConfig(
            redis_host=os.getenv("REDIS_HOST", "redis-cluster"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_password=os.getenv("REDIS_PASSWORD"),
            redis_ssl=True,
            redis_max_connections=100
        )
        
        self.api = APIConfig(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            api_timeout=300,
            max_retries=3,
            rate_limit_enabled=True,
            rate_limit_requests_per_minute=60
        )
        
        self.agent_pool = AgentPoolConfig(
            max_agents_per_type=5,
            agent_max_memory_mb=512,
            agent_restart_on_failure=True
        )
        
        self.workflow = WorkflowConfig(
            max_concurrent_workflows=10,
            workflow_timeout_seconds=1800,
            enable_checkpointing=True,
            enable_workflow_recovery=True
        )
        
        self.monitoring = MonitoringConfig(
            log_level="INFO",
            log_format="json",
            enable_prometheus=True,
            enable_grafana_dashboard=True,
            enable_tracing=True
        )
        
        self.security = SecurityConfig(
            security_level=SecurityLevel.ENTERPRISE,
            enable_api_key_rotation=True,
            enable_request_signing=True,
            enable_audit_logging=True,
            encrypt_at_rest=True,
            encrypt_in_transit=True
        )
        
        self.resources = ResourceLimits(
            max_memory_mb=2048,
            max_cpu_percent=80,
            max_disk_usage_mb=5120
        )
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the current configuration and return any issues."""
        issues = []
        warnings = []
        
        # Validate API keys
        if not self.api.anthropic_api_key:
            issues.append("Missing ANTHROPIC_API_KEY - required for branding and market research")
        
        if not self.api.openai_api_key:
            warnings.append("Missing OPENAI_API_KEY - logo generation will use mock mode")
        
        # Validate database connection
        if not self.database.redis_host:
            issues.append("Missing Redis host configuration")
        
        # Validate resource limits
        if self.resources.max_memory_mb < 512:
            warnings.append("Low memory limit may cause agent failures")
        
        if self.agent_pool.max_agents_per_type < 2:
            warnings.append("Low agent pool size may impact performance")
        
        # Security validation
        if self.environment == DeploymentEnvironment.PRODUCTION:
            if self.security.security_level == SecurityLevel.BASIC:
                issues.append("Production environment requires enhanced security level")
            
            if not self.security.enable_audit_logging:
                warnings.append("Audit logging should be enabled in production")
            
            if not self.database.redis_ssl:
                issues.append("SSL should be enabled for production database connections")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "environment": self.environment.value,
            "security_level": self.security.security_level.value
        }
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get required environment variables for deployment."""
        env_vars = {
            # Core API keys
            "ANTHROPIC_API_KEY": self.api.anthropic_api_key or "",
            "OPENAI_API_KEY": self.api.openai_api_key or "",
            
            # Database configuration
            "REDIS_HOST": self.database.redis_host,
            "REDIS_PORT": str(self.database.redis_port),
            "REDIS_SSL": str(self.database.redis_ssl).lower(),
            
            # Application configuration
            "DEPLOYMENT_ENVIRONMENT": self.environment.value,
            "LOG_LEVEL": self.monitoring.log_level,
            "LOG_FORMAT": self.monitoring.log_format,
            
            # Resource limits
            "MAX_MEMORY_MB": str(self.resources.max_memory_mb),
            "MAX_CPU_PERCENT": str(self.resources.max_cpu_percent),
            
            # Monitoring
            "METRICS_ENABLED": str(self.monitoring.enable_metrics).lower(),
            "METRICS_PORT": str(self.monitoring.metrics_port),
            "HEALTH_CHECK_PORT": str(self.monitoring.health_check_port),
            
            # Security
            "SECURITY_LEVEL": self.security.security_level.value,
            "ENABLE_AUDIT_LOGGING": str(self.security.enable_audit_logging).lower(),
        }
        
        # Add optional environment variables
        if self.database.redis_password:
            env_vars["REDIS_PASSWORD"] = self.database.redis_password
        
        if self.api.anthropic_base_url:
            env_vars["ANTHROPIC_BASE_URL"] = self.api.anthropic_base_url
        
        if self.api.openai_base_url:
            env_vars["OPENAI_BASE_URL"] = self.api.openai_base_url
        
        return env_vars
    
    def save_config_file(self, filepath: str):
        """Save configuration to JSON file."""
        config_data = {
            "environment": self.environment.value,
            "database": {
                "redis_host": self.database.redis_host,
                "redis_port": self.database.redis_port,
                "redis_ssl": self.database.redis_ssl,
                "redis_max_connections": self.database.redis_max_connections
            },
            "api": {
                "api_timeout": self.api.api_timeout,
                "max_retries": self.api.max_retries,
                "rate_limit_enabled": self.api.rate_limit_enabled,
                "rate_limit_requests_per_minute": self.api.rate_limit_requests_per_minute
            },
            "agent_pool": {
                "max_agents_per_type": self.agent_pool.max_agents_per_type,
                "agent_startup_timeout": self.agent_pool.agent_startup_timeout,
                "agent_restart_on_failure": self.agent_pool.agent_restart_on_failure,
                "agent_max_memory_mb": self.agent_pool.agent_max_memory_mb
            },
            "workflow": {
                "max_concurrent_workflows": self.workflow.max_concurrent_workflows,
                "workflow_timeout_seconds": self.workflow.workflow_timeout_seconds,
                "max_recursion_limit": self.workflow.max_recursion_limit,
                "enable_checkpointing": self.workflow.enable_checkpointing
            },
            "monitoring": {
                "log_level": self.monitoring.log_level,
                "log_format": self.monitoring.log_format,
                "enable_metrics": self.monitoring.enable_metrics,
                "enable_prometheus": self.monitoring.enable_prometheus,
                "metrics_port": self.monitoring.metrics_port
            },
            "security": {
                "security_level": self.security.security_level.value,
                "enable_audit_logging": self.security.enable_audit_logging,
                "enable_rate_limiting": self.security.enable_rate_limiting,
                "encrypt_at_rest": self.security.encrypt_at_rest
            },
            "resources": {
                "max_memory_mb": self.resources.max_memory_mb,
                "max_cpu_percent": self.resources.max_cpu_percent,
                "max_disk_usage_mb": self.resources.max_disk_usage_mb
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Configuration saved to {filepath}")
    
    def get_deployment_readiness(self) -> Dict[str, Any]:
        """Check deployment readiness and return status."""
        validation = self.validate_configuration()
        env_vars = self.get_environment_variables()
        
        # Check critical services
        critical_checks = {
            "anthropic_api_key": bool(env_vars.get("ANTHROPIC_API_KEY")),
            "redis_configured": bool(env_vars.get("REDIS_HOST")),
            "security_level_appropriate": validation["valid"] or self.environment == DeploymentEnvironment.DEVELOPMENT,
            "resource_limits_set": self.resources.max_memory_mb > 0
        }
        
        all_critical_passed = all(critical_checks.values())
        
        return {
            "ready_for_deployment": all_critical_passed,
            "environment": self.environment.value,
            "critical_checks": critical_checks,
            "validation_result": validation,
            "required_env_vars": list(env_vars.keys()),
            "deployment_timestamp": os.environ.get("DEPLOYMENT_TIMESTAMP", "not_set"),
            "configuration_version": "1.0.0"
        }


# Factory functions for easy configuration creation
def create_development_config() -> ProductionConfig:
    """Create development environment configuration."""
    return ProductionConfig(DeploymentEnvironment.DEVELOPMENT)


def create_staging_config() -> ProductionConfig:
    """Create staging environment configuration."""
    return ProductionConfig(DeploymentEnvironment.STAGING)


def create_production_config() -> ProductionConfig:
    """Create production environment configuration."""
    return ProductionConfig(DeploymentEnvironment.PRODUCTION)


def get_config_for_environment(env_name: str) -> ProductionConfig:
    """Get configuration for specified environment name."""
    env_name = env_name.lower()
    
    if env_name in ["dev", "development", "local"]:
        return create_development_config()
    elif env_name in ["stage", "staging", "test"]:
        return create_staging_config()
    elif env_name in ["prod", "production", "live"]:
        return create_production_config()
    else:
        raise ValueError(f"Unknown environment: {env_name}")