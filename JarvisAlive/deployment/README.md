# HeyJarvis Production Deployment Guide

This directory contains production-ready deployment configurations for the HeyJarvis parallel workflow system.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (for container deployment)
- Kubernetes & kubectl (for K8s deployment)
- Python 3.11+ 
- Required API keys (Anthropic Claude, OpenAI)

### Environment Setup

1. **Set API Keys:**
   ```bash
   export ANTHROPIC_API_KEY="your-anthropic-key"
   export OPENAI_API_KEY="your-openai-key"
   ```

2. **Validate Configuration:**
   ```bash
   python deploy.py --validate-only --environment production
   ```

3. **Deploy with Docker:**
   ```bash
   python deploy.py --environment production --type docker
   ```

4. **Deploy to Kubernetes:**
   ```bash
   python deploy.py --environment production --type kubernetes
   ```

## 📁 File Structure

```
deployment/
├── production_config.py     # Configuration management
├── deploy.py               # Automated deployment script
├── Dockerfile             # Multi-stage Docker build
├── docker-compose.yml     # Docker Compose services
├── kubernetes.yaml        # Kubernetes manifests
├── prometheus.yml         # Monitoring configuration
└── README.md             # This guide
```

## 🔧 Configuration

### Environment Types

- **Development**: Local development with minimal resources
- **Staging**: Pre-production environment with full monitoring
- **Production**: High-availability production deployment

### Key Features

- **Auto-scaling**: Kubernetes HPA based on CPU/memory
- **High Availability**: Multiple replicas with load balancing
- **Monitoring**: Prometheus + Grafana dashboards
- **Security**: Non-root containers, network policies
- **Persistence**: Persistent storage for reports and logs
- **Health Checks**: Liveness and readiness probes

## 🐳 Docker Deployment

### Single Command Deploy
```bash
# Production deployment
docker-compose up -d

# With specific environment
docker-compose --env-file .env.production up -d
```

### Services Included
- **heyjarvis**: Main application (3 replicas)
- **redis**: Message bus and session storage
- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboards
- **nginx**: Load balancer (optional)

### Access Points
- Application: http://localhost:8000
- Metrics: http://localhost:8080/metrics
- Health: http://localhost:8081/health
- Grafana: http://localhost:3000 (admin/admin)

## ☸️ Kubernetes Deployment

### Deploy to Cluster
```bash
# Create namespace and deploy
kubectl apply -f kubernetes.yaml

# Check deployment status
kubectl get pods -n heyjarvis

# Port forward for local access
kubectl port-forward -n heyjarvis svc/heyjarvis-service 8000:8000
```

### Features
- **Namespace**: Isolated heyjarvis namespace
- **Auto-scaling**: 3-10 replicas based on load
- **Persistent Storage**: 50GB for reports, 20GB for logs
- **Network Policies**: Security-first networking
- **Ingress**: External access with TLS termination
- **Service Monitor**: Prometheus integration

## 📊 Monitoring & Observability

### Metrics Available
- Workflow execution times
- Agent success/failure rates
- Resource utilization (CPU, memory)
- API call counts and latencies
- Error rates and patterns

### Grafana Dashboards
- **Workflow Overview**: High-level metrics
- **Agent Performance**: Individual agent metrics
- **System Health**: Infrastructure metrics
- **Error Analysis**: Failure tracking

### Alerting Rules
- High error rates (>10%)
- Long-running workflows (>30min)
- Resource exhaustion (>90% CPU/memory)
- API failures or timeouts

## 🔒 Security

### Production Security Features
- **Non-root containers**: Enhanced container security
- **Network policies**: Restricted pod-to-pod communication  
- **API key management**: Kubernetes secrets
- **TLS encryption**: In-transit data protection
- **Audit logging**: Complete action tracking
- **Resource limits**: DoS protection

### Security Checklist
- [ ] API keys stored in secrets (not environment)
- [ ] TLS certificates configured
- [ ] Network policies applied
- [ ] Resource limits set
- [ ] Audit logging enabled
- [ ] Container images scanned

## 🔧 Troubleshooting

### Common Issues

**1. API Key Errors**
```bash
# Check if keys are set
kubectl get secret heyjarvis-secrets -n heyjarvis -o yaml

# Update API keys
kubectl create secret generic heyjarvis-secrets \
  --from-literal=ANTHROPIC_API_KEY="your-key" \
  --from-literal=OPENAI_API_KEY="your-key" \
  -n heyjarvis --dry-run=client -o yaml | kubectl apply -f -
```

**2. Redis Connection Issues**
```bash
# Check Redis pod
kubectl get pods -n heyjarvis -l app=redis

# Test Redis connection
kubectl exec -it -n heyjarvis deployment/redis -- redis-cli ping
```

**3. Resource Constraints**
```bash
# Check resource usage
kubectl top pods -n heyjarvis

# Scale deployment
kubectl scale deployment heyjarvis -n heyjarvis --replicas=5
```

### Health Checks

```bash
# Application health
curl http://localhost:8081/health

# Detailed status
python deploy.py --status --environment production

# View logs
kubectl logs -f deployment/heyjarvis -n heyjarvis
```

## 🚀 Performance Tuning

### Scaling Configuration

**Docker Compose:**
```yaml
deploy:
  replicas: 5
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

**Kubernetes:**
```yaml
spec:
  replicas: 3
  resources:
    limits:
      memory: 2Gi
      cpu: 1000m
```

### Agent Pool Tuning

Adjust in `production_config.py`:
```python
agent_pool = AgentPoolConfig(
    max_agents_per_type=5,     # More agents = more concurrency
    agent_max_memory_mb=512,   # Memory per agent
    agent_restart_on_failure=True
)
```

## 📈 Maintenance

### Regular Tasks

**Weekly:**
- Review error logs and metrics
- Check resource utilization
- Validate backup integrity

**Monthly:**
- Update API keys (if rotation enabled)
- Review security policies
- Performance optimization

**Quarterly:**
- Update base images
- Security audit
- Disaster recovery testing

### Backup Strategy

- **Database**: Redis snapshots every 6 hours
- **Reports**: Daily backup to external storage
- **Logs**: 30-day retention with archival
- **Configuration**: Version controlled in Git

## 🆘 Emergency Procedures

### Rollback Deployment
```bash
# Docker
python deploy.py --rollback --environment production

# Kubernetes
kubectl rollout undo deployment/heyjarvis -n heyjarvis
```

### Scale Down (Emergency)
```bash
# Reduce load immediately
kubectl scale deployment heyjarvis -n heyjarvis --replicas=1
```

### Debug Mode
```bash
# Enable debug logging
kubectl set env deployment/heyjarvis -n heyjarvis LOG_LEVEL=DEBUG
```

## 📞 Support

For deployment issues:
1. Check this guide and troubleshooting section
2. Review application logs
3. Validate configuration with `deploy.py --validate-only`
4. Check system resources and scaling

## 🔄 Updates

To update the deployment:

1. **Update code**: Pull latest changes
2. **Rebuild**: `docker-compose build` or update K8s image
3. **Deploy**: `python deploy.py --environment production`
4. **Validate**: Check health and metrics
5. **Monitor**: Watch for any issues in first 30 minutes

---

**Production Deployment Checklist:**

- [ ] API keys configured
- [ ] Environment validated
- [ ] Resources allocated
- [ ] Monitoring enabled
- [ ] Security policies applied
- [ ] Health checks passing
- [ ] Backups configured
- [ ] Documentation updated