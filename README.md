# Kubernetes Deployment Guide: React Frontend with FastAPI Backend

## Project Overview
This guide covers the deployment of a full-stack application on Google Kubernetes Engine (GKE) with:
- React frontend
- FastAPI backend
- Nginx as reverse proxy
- Container Registry for image storage

## Prerequisites
- Google Cloud Platform account
- `gcloud` CLI installed
- `kubectl` installed
- Docker installed

## 1. Project Setup

### Create GCP Project
```bash
# Create new project
gcloud projects create [PROJECT-ID] --name="[PROJECT-NAME]"

# Set current project
gcloud config set project [PROJECT-ID]

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Create Kubernetes Cluster
```bash
# Create a small cluster suitable for development
gcloud container clusters create [CLUSTER-NAME] \
    --zone [ZONE] \
    --num-nodes 2 \
    --machine-type e2-small \
    --disk-size 10GB

# Get credentials for kubectl
gcloud container clusters get-credentials [CLUSTER-NAME] --zone [ZONE]
```

## 2. Application Configuration

### Frontend Configuration

#### Dockerfile
```dockerfile
# Build stage
FROM node:16-alpine as build
WORKDIR /frontend
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /frontend/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### nginx.conf
```nginx
server {
    listen 80;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://backend-service:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Backend Configuration

#### Dockerfile
```dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 3. Container Build and Push

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and push frontend
cd frontend
docker build -t gcr.io/[PROJECT-ID]/frontend:v1 .
docker push gcr.io/[PROJECT-ID]/frontend:v1

# Build and push backend
cd ../backend
docker build -t gcr.io/[PROJECT-ID]/backend:v1 .
docker push gcr.io/[PROJECT-ID]/backend:v1
```

## 4. Kubernetes Deployment

### Deployment Files

#### Frontend Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: gcr.io/[PROJECT-ID]/frontend:v1
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 80
  selector:
    app: frontend
```

#### Backend Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: gcr.io/[PROJECT-ID]/backend:v1
        ports:
        - containerPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
  selector:
    app: backend
```

## 5. Deployment Commands

```bash
# Apply deployments
kubectl apply -f frontend-deployment.yaml
kubectl apply -f backend-deployment.yaml

# Verify deployments
kubectl get deployments
kubectl get pods
kubectl get services
```

## 6. Troubleshooting Commands

### Check Pod Status
```bash
# Get pod status
kubectl get pods

# Get pod logs
kubectl logs [POD-NAME]

# Describe pod for events
kubectl describe pod [POD-NAME]
```

### Check Services
```bash
# List services
kubectl get services

# Get service endpoints
kubectl get endpoints

# Test service connectivity
kubectl exec -it [FRONTEND-POD] -- curl http://backend-service:8000
```

### Common Issues and Solutions

1. **CrashLoopBackOff**
   - Check logs: `kubectl logs [POD-NAME]`
   - Check pod description: `kubectl describe pod [POD-NAME]`

2. **Service Connection Issues**
   - Verify service names match in nginx.conf
   - Check endpoints: `kubectl get endpoints`
   - Verify pod labels match service selectors

3. **Image Pull Issues**
   - Check image name and tag
   - Verify GCR permissions: `gcloud auth configure-docker`

4. **Network Issues**
   - Verify services are running: `kubectl get services`
   - Check service endpoints: `kubectl get endpoints`
   - Test network connectivity between pods

### Update Deployment
```bash
# Update deployment image
kubectl set image deployment/[DEPLOYMENT-NAME] [CONTAINER-NAME]=gcr.io/[PROJECT-ID]/[IMAGE]:[TAG]

# Restart deployment
kubectl rollout restart deployment [DEPLOYMENT-NAME]
```

## 7. Maintenance

### Scaling
```bash
# Scale deployment
kubectl scale deployment [DEPLOYMENT-NAME] --replicas=[NUMBER]
```

### Updates
```bash
# Update image
docker build -t gcr.io/[PROJECT-ID]/[IMAGE]:[NEW-TAG] .
docker push gcr.io/[PROJECT-ID]/[IMAGE]:[NEW-TAG]
kubectl set image deployment/[DEPLOYMENT-NAME] [CONTAINER-NAME]=gcr.io/[PROJECT-ID]/[IMAGE]:[NEW-TAG]
```

### Monitoring
```bash
# Monitor pods
kubectl get pods -w

# View logs
kubectl logs -f [POD-NAME]
```





____________________________________

# HTTPS Setup Guide for React and FastAPI on GKE

## Prerequisites
- GKE cluster running
- Docker images for frontend and backend
- kubectl configured for your cluster

## 1. Required Files Structure
```
project/
├── k8s/
│   ├── frontend-deployment.yaml
│   ├── backend-deployment.yaml
│   ├── ingress.yaml
│   └── frontend-config.yaml
├── frontend/
│   ├── Dockerfile
│   └── nginx.conf
└── backend/
    └── Dockerfile
```

## 2. Create SSL Certificate
```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
-keyout tls.key -out tls.crt \
-subj "/CN=frontend-service"

# Create Kubernetes secret for SSL
kubectl create secret tls frontend-tls \
  --key tls.key \
  --cert tls.crt
```

## 3. Create Static IP
```bash
# Reserve a static IP
gcloud compute addresses create frontend-ip --global

# Get the IP address
gcloud compute addresses describe frontend-ip --global
```

## 4. Configuration Files

### frontend-config.yaml
```yaml
apiVersion: networking.gke.io/v1beta1
kind: FrontendConfig
metadata:
  name: frontend-ingress-config
spec:
  redirectToHttps:
    enabled: false
```

### ingress.yaml
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend-ingress
  annotations:
    kubernetes.io/ingress.class: "gce"
    kubernetes.io/ingress.global-static-ip-name: "frontend-ip"
    ingress.gcp.kubernetes.io/pre-shared-cert: "frontend-tls"
    kubernetes.io/ingress.allow-http: "true"
    networking.gke.io/v1beta1.FrontendConfig: "frontend-ingress-config"
spec:
  defaultBackend:
    service:
      name: frontend-service
      port:
        number: 80
  rules:
  - http:
      paths:
      - path: /api/*
        pathType: ImplementationSpecific
        backend:
          service:
            name: backend-service
            port:
              number: 8000
      - path: /*
        pathType: ImplementationSpecific
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### Frontend Changes

#### nginx.conf
```nginx
server {
    listen 80;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend-service:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### React Frontend API Call
```javascript
const squareHandler = () => {
    axios.post("/api/square", { number: numberInt }, {
      headers: {
        'Content-Type': 'application/json',
      }
    })
    .then((res) => {
      sample(res.data);
    })
    .catch((error) => {
      console.error("Error:", error);
      sample("Error: " + error.message);
    });
};
```

### Backend Changes

#### FastAPI Endpoint
```python
@app.post("/api/square")  # Note the /api prefix
def square(data:My_Number_Class):
    number = data.number
    return str(number*number)
```

## 5. Deployment Steps

1. Apply Frontend Configuration:
```bash
kubectl apply -f frontend-config.yaml
```

2. Apply Ingress:
```bash
kubectl apply -f ingress.yaml
```

3. Update Services:
```bash
kubectl patch service frontend-service -p '{"spec": {"type": "NodePort"}}'
```

4. Verify Setup:
```bash
# Check ingress status
kubectl describe ingress frontend-ingress

# Check frontend config
kubectl get frontendconfig

# Check SSL certificate
kubectl get secrets frontend-tls
```

## 6. Monitoring and Troubleshooting

Monitor Resources:
```bash
# Check ingress status
kubectl get ingress frontend-ingress

# Check services
kubectl get services

# Check pods
kubectl get pods

# View logs
kubectl logs -l app=frontend
kubectl logs -l app=backend
```

Common Issues and Solutions:
1. 404 Errors:
   - Verify API paths match between frontend and backend
   - Check ingress path configurations

2. SSL Certificate Issues:
   - Verify certificate secret exists
   - Check certificate referenced correctly in ingress

3. Connection Issues:
   - Verify services are running
   - Check pod logs for errors
   - Verify ingress configuration

## 7. Security Considerations
- The self-signed certificate will show security warnings in browsers
- For production, use a valid SSL certificate
- Consider enabling HTTPS redirect
- Implement proper CORS policies
- Regular certificate rotation

## 8. Maintenance
- Monitor certificate expiration
- Keep track of IP address reservation
- Regular security updates
- Backup SSL certificates and configurations
