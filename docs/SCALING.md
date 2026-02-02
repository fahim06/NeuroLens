# NeuroLens Scaling Strategy

## Overview

This document outlines the scaling strategy for NeuroLens, covering horizontal and vertical scaling approaches, capacity planning, and performance benchmarks.

## Architecture Tiers

### 1. API Layer (FastAPI)
- **Scaling Type**: Horizontal
- **Stateless**: Yes
- **Load Balancing**: Round-robin with health checks
- **Autoscaling Trigger**: CPU > 70% or RPS > 1000/instance

### 2. Inference Layer
- **Scaling Type**: Horizontal + Vertical (GPU)
- **Stateless**: Yes (models loaded on startup)
- **Load Balancing**: Least-connections (accounts for inference time)
- **Autoscaling Trigger**: Queue size > 50 or GPU > 80%

### 3. Database Layer (PostgreSQL)
- **Scaling Type**: Vertical + Read Replicas
- **Primary-Replica**: For read-heavy workloads
- **Connection Pooling**: PgBouncer with 100 max connections per pool

### 4. Cache Layer (Redis)
- **Scaling Type**: Cluster mode for HA
- **Memory**: Monitor eviction rate
- **Persistence**: RDB + AOF for durability

## Kubernetes HPA Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: neurolens-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: neurolens-api
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

## GPU Inference Scaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: neurolens-inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: neurolens-inference
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: External
      external:
        metric:
          name: inference_queue_size
        target:
          type: AverageValue
          averageValue: "50"
    - type: External
      external:
        metric:
          name: gpu_utilization
        target:
          type: AverageValue
          averageValue: "80"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
        - type: Pods
          value: 2
          periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 600
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

## Resource Recommendations

### Small Deployment (Development/Testing)
| Component | Instances | CPU | Memory | GPU |
|-----------|-----------|-----|--------|-----|
| API | 2 | 1 core | 2 GB | - |
| Inference | 1 | 4 cores | 8 GB | 1x T4 |
| PostgreSQL | 1 | 2 cores | 4 GB | - |
| Redis | 1 | 1 core | 2 GB | - |

**Capacity**: ~100 RPS API, ~10 inference/sec

### Medium Deployment (Production)
| Component | Instances | CPU | Memory | GPU |
|-----------|-----------|-----|--------|-----|
| API | 4-8 | 2 cores | 4 GB | - |
| Inference | 2-4 | 8 cores | 16 GB | 1x A10G each |
| PostgreSQL | 1 primary + 2 replicas | 4 cores | 16 GB | - |
| Redis | 3-node cluster | 2 cores | 8 GB | - |

**Capacity**: ~2000 RPS API, ~100 inference/sec

### Large Deployment (Enterprise)
| Component | Instances | CPU | Memory | GPU |
|-----------|-----------|-----|--------|-----|
| API | 10-20 | 4 cores | 8 GB | - |
| Inference | 5-10 | 16 cores | 32 GB | 1x A100 each |
| PostgreSQL | 1 primary + 4 replicas | 8 cores | 64 GB | - |
| Redis | 6-node cluster | 4 cores | 16 GB | - |

**Capacity**: ~10000 RPS API, ~500 inference/sec

## Performance Benchmarks

### API Latency Targets

| Percentile | Target | Critical |
|------------|--------|----------|
| P50 | < 50ms | < 100ms |
| P95 | < 200ms | < 400ms |
| P99 | < 500ms | < 1000ms |

### Inference Latency Targets

| Model Size | P50 | P95 | P99 |
|------------|-----|-----|-----|
| Small (< 100MB) | 50ms | 100ms | 200ms |
| Medium (100MB-1GB) | 200ms | 500ms | 1000ms |
| Large (> 1GB) | 500ms | 1500ms | 3000ms |

## Load Testing Results

### Test Configuration
- Tool: Locust / k6
- Duration: 10 minutes
- Ramp-up: 2 minutes
- Virtual Users: 100 → 1000

### API Endpoint Results (4 replicas)
```
Endpoint          RPS    P50    P95    P99    Error%
────────────────────────────────────────────────────
GET /health       5000   2ms    5ms    10ms   0.00%
GET /v1/models    2000   15ms   50ms   100ms  0.01%
POST /v1/predict  500    100ms  300ms  500ms  0.10%
POST /v1/upload   100    200ms  600ms  1000ms 0.20%
```

### Inference Results (2 GPU replicas)
```
Model          Batch  RPS    P50     P95     P99
──────────────────────────────────────────────────
ResNet50       1      50     45ms    80ms    150ms
ResNet50       8      100    120ms   200ms   350ms
EfficientNet   1      40     55ms    100ms   180ms
NeuroLens-v3   1      30     80ms    150ms   250ms
```

## Capacity Planning

### Formula for API Replicas
```
replicas = ceil(peak_rps / rps_per_replica) * safety_factor

Where:
- rps_per_replica = 500 (conservative)
- safety_factor = 1.5
```

### Formula for Inference Replicas
```
replicas = ceil(peak_inference_rps / inference_capacity) * safety_factor

Where:
- inference_capacity = GPU_throughput / avg_latency
- safety_factor = 2.0 (account for model loading)
```

### Example: 5000 API RPS + 200 Inference RPS
```
API replicas = ceil(5000 / 500) * 1.5 = 15 replicas
Inference replicas = ceil(200 / 50) * 2.0 = 8 replicas
```

## Scaling Playbook

### Scale Up Triggers
1. **CPU > 70% for 5 minutes** → Add 2 API replicas
2. **P99 latency > 500ms for 5 minutes** → Add 1 API replica
3. **Queue size > 50 for 2 minutes** → Add 1 inference replica
4. **GPU utilization > 80% for 5 minutes** → Add 1 inference replica

### Scale Down Triggers
1. **CPU < 30% for 15 minutes** → Remove 1 API replica (min 2)
2. **Queue size < 10 for 30 minutes** → Remove 1 inference replica (min 1)
3. **GPU utilization < 30% for 30 minutes** → Remove 1 inference replica (min 1)

### Emergency Procedures

#### Traffic Surge
1. Immediately scale to max replicas
2. Enable rate limiting
3. Shed non-critical traffic
4. Notify on-call team

#### Service Degradation
1. Check error rates and latency
2. Roll back recent deployments if applicable
3. Scale up affected tier
4. Enable circuit breakers

## Cost Optimization

### Spot/Preemptible Instances
- Use for non-critical inference workloads
- Implement graceful shutdown handlers
- Maintain minimum on-demand capacity

### Right-Sizing
- Review resource utilization weekly
- Downsize over-provisioned instances
- Use burstable instances for dev/staging

### Reserved Capacity
- Reserve 60% of baseline capacity for 1-year term
- Use savings plans for predictable workloads
- Spot instances for burst capacity

## Monitoring Checklist

- [ ] CPU utilization per service
- [ ] Memory utilization per service
- [ ] GPU utilization and memory
- [ ] Request latency percentiles
- [ ] Error rates by endpoint
- [ ] Queue depths
- [ ] Database connection pool usage
- [ ] Cache hit rates
- [ ] Network I/O
- [ ] Disk I/O

## SLO Definitions

| Service | SLI | Target | Burn Rate Alert |
|---------|-----|--------|-----------------|
| API | Availability | 99.9% | 10x in 5m |
| API | Latency P99 | < 500ms | 2x in 15m |
| Inference | Availability | 99.5% | 10x in 5m |
| Inference | Latency P95 | < 1s | 2x in 15m |
| Training | Success Rate | 95% | N/A |
