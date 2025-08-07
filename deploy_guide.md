# Hướng dẫn Deploy Ứng dụng Prostate Care AI lên Google Cloud

## Tùy chọn 1: Google Cloud Run (Khuyến nghị)

### Bước 1: Chuẩn bị môi trường
```bash
# Cài đặt Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Đăng nhập và chọn project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Bước 2: Tạo PostgreSQL Database trên Cloud SQL
```bash
# Tạo Cloud SQL instance
gcloud sql instances create prostate-care-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=asia-southeast1

# Tạo database
gcloud sql databases create prostate_care \
    --instance=prostate-care-db

# Tạo user
gcloud sql users create appuser \
    --instance=prostate-care-db \
    --password=your-secure-password
```

### Bước 3: Cấu hình Secret Manager
```bash
# Tạo secrets
echo -n "your-session-secret-key" | gcloud secrets create session-secret --data-file=-
echo -n "your-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-
echo -n "postgresql://appuser:password@/prostate_care?host=/cloudsql/PROJECT_ID:asia-southeast1:prostate-care-db" | gcloud secrets create database-url --data-file=-
```

### Bước 4: Deploy với Cloud Run
```bash
# Build và deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/prostate-care-ai

# Deploy to Cloud Run
gcloud run deploy prostate-care-ai \
    --image gcr.io/YOUR_PROJECT_ID/prostate-care-ai \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 1 \
    --add-cloudsql-instances YOUR_PROJECT_ID:asia-southeast1:prostate-care-db \
    --set-env-vars SESSION_SECRET=projects/YOUR_PROJECT_ID/secrets/session-secret/versions/latest \
    --set-env-vars GEMINI_API_KEY=projects/YOUR_PROJECT_ID/secrets/gemini-api-key/versions/latest \
    --set-env-vars DATABASE_URL=projects/YOUR_PROJECT_ID/secrets/database-url/versions/latest
```

## Tùy chọn 2: Google App Engine

### Bước 1: Chuẩn bị app.yaml
Chỉnh sửa file `app.yaml` với thông tin thực của bạn:
```yaml
runtime: python311

env_variables:
  SESSION_SECRET: "your-actual-session-secret"
  DATABASE_URL: "postgresql://username:password@host:port/database"
  GEMINI_API_KEY: "your-actual-gemini-api-key"
```

### Bước 2: Deploy
```bash
gcloud app deploy app.yaml
```

## Tùy chọn 3: Google Kubernetes Engine (GKE)

### Bước 1: Tạo cluster
```bash
gcloud container clusters create prostate-care-cluster \
    --zone asia-southeast1-a \
    --num-nodes 3 \
    --machine-type e2-medium
```

### Bước 2: Tạo ConfigMap và Secrets
```bash
# ConfigMap cho cấu hình
kubectl create configmap app-config \
    --from-literal=FLASK_ENV=production

# Secrets cho thông tin nhạy cảm
kubectl create secret generic app-secrets \
    --from-literal=SESSION_SECRET=your-session-secret \
    --from-literal=DATABASE_URL=your-database-url \
    --from-literal=GEMINI_API_KEY=your-gemini-api-key
```

### Bước 3: Tạo Deployment
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prostate-care-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: prostate-care-ai
  template:
    metadata:
      labels:
        app: prostate-care-ai
    spec:
      containers:
      - name: app
        image: gcr.io/YOUR_PROJECT_ID/prostate-care-ai:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
```

## Bước quan trọng sau khi deploy:

### 1. Cấu hình Domain (Tùy chọn)
```bash
# Map custom domain
gcloud run domain-mappings create \
    --service prostate-care-ai \
    --domain your-domain.com \
    --region asia-southeast1
```

### 2. Cấu hình SSL Certificate
```bash
# Tự động với Cloud Run
gcloud run services update prostate-care-ai \
    --region asia-southeast1 \
    --add-custom-audiences your-domain.com
```

### 3. Thiết lập Monitoring
```bash
# Enable logging
gcloud logging sinks create prostate-care-logs \
    bigquery.googleapis.com/projects/YOUR_PROJECT_ID/datasets/app_logs
```

### 4. Backup Database
```bash
# Tạo automated backup
gcloud sql backups create \
    --instance=prostate-care-db \
    --description="Daily backup"
```

## Chi phí ước tính (USD/tháng):

### Cloud Run + Cloud SQL:
- Cloud Run: $10-30 (tùy traffic)
- Cloud SQL (db-f1-micro): $7-15
- Storage: $1-5
- **Tổng: $18-50/tháng**

### App Engine:
- App Engine: $20-50 (tùy usage)
- Cloud SQL: $7-15
- **Tổng: $27-65/tháng**

### GKE:
- GKE Cluster: $70-150
- Cloud SQL: $7-15
- **Tổng: $77-165/tháng**

## Khuyến nghị:
1. **Bắt đầu với Cloud Run** - Dễ deploy, cost-effective
2. **Sử dụng Cloud SQL** cho database production
3. **Cấu hình Secret Manager** cho bảo mật
4. **Enable monitoring** và logging
5. **Thiết lập backup** tự động

## Liên hệ hỗ trợ:
- Google Cloud Support: https://cloud.google.com/support
- Documentation: https://cloud.google.com/docs