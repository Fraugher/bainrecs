# Docker Deployment Guide - Bainrecs

## Overview

The Bainrecs application consists of two containerized services:

1. **Backend API** - Python/Flask REST API
2. **Frontend** - React SPA served by nginx

Both are containerized and can be deployed to any platform that supports Docker.

## Quick Start - Running Both Services

### 1. Start Backend
```bash
cd bainrecs
docker build -t bainrecs-backend:latest .
docker run -d -p 5000:5000 \
  -v "$(pwd)/.env:/app/.env" \
  --name bainrecs-backend \
  bainrecs-backend:latest
```

### 2. Start Frontend
```bash
cd bainrecs-fe
docker build -t bainrecs-frontend:latest .
docker run -d -p 3000:80 \
  --name bainrecs-frontend \
  bainrecs-frontend:latest
```

### 3. Verify

- Backend: http://localhost:5000/apify/health
- Frontend: http://localhost:3000

## Current Architecture
```
┌─────────────────────────────────────┐
│         User Browser                │
└─────────────┬───────────────────────┘
              │
              ├─→ http://localhost:3000
              │   ┌──────────────────────┐
              │   │  Frontend Container  │
              │   │  (React + nginx)     │
              │   └──────────────────────┘
              │
              └─→ http://localhost:5000
                  ┌──────────────────────┐
                  │  Backend Container   │
                  │  (Flask + gunicorn)  │
                  └──────────┬───────────┘
                             │
                             └─→ MySQL Database
```

## Deployment Options

### Option 1: Docker Compose (Simple Servers)

For deployment to VMs or simple servers, use docker-compose:
```yaml
version: '3.8'

services:
  backend:
    image: bainrecs-backend:latest
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
    restart: unless-stopped

  frontend:
    image: bainrecs-frontend:latest
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

### Option 2: AWS ECS/Fargate

- Push images to ECR (Elastic Container Registry)
- Create ECS task definitions for each service
- Deploy to Fargate for serverless container hosting

### Option 3: Kubernetes

- Deploy to any Kubernetes cluster (EKS, GKE, on-premises)
- Use provided manifests (backend-deployment.yaml, frontend-deployment.yaml)

### Option 4: Cloud Run / App Platform

- Google Cloud Run
- DigitalOcean App Platform
- Azure Container Instances

## Platform Agnostic Design

The Docker images are **platform-agnostic**. The same images work on:

- ✅ Local development (macOS, Windows, Linux)
- ✅ AWS (ECS, EKS, EC2)
- ✅ Google Cloud (GKE, Cloud Run)
- ✅ Azure (AKS, Container Instances)
- ✅ DigitalOcean, Linode, any VPS
- ✅ On-premises servers
- ✅ Bain internal infrastructure

**Only environment variables change, not the images.**

## Why Docker for This Project?

### Current State (PythonAnywhere + Netlify)
- ✅ Working and appropriate for current scale
- ✅ Free hosting
- ❌ Not suitable for enterprise deployment
- ❌ Limited control and customization

### With Docker
- ✅ Portable - deploy anywhere
- ✅ Consistent environments (dev = prod)
- ✅ Scalable - add more containers as needed
- ✅ Professional deployment ready
- ✅ CI/CD pipeline compatible

## Next Steps

When deployment target is decided:

1. **Set up container registry** (ECR, GCR, Docker Hub, etc.)
2. **Push images** to registry
3. **Configure orchestration** (docker-compose, Kubernetes, ECS)
4. **Set environment variables** for production
5. **Configure networking** (load balancers, DNS)
6. **Set up monitoring** and logging

## Security Notes

- Never commit `.env` files to git
- Use secrets management (AWS Secrets Manager, etc.) in production
- Images should be scanned for vulnerabilities before deployment
- Use specific version tags, not `latest` in production

## Support

For questions or issues:
- Check logs: `docker logs <container-name>`
- Verify images built: `docker images`
- Check running containers: `docker ps`