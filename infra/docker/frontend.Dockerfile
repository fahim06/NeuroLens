# ============================================================
# NeuroLens Frontend — Production Dockerfile
# ============================================================
# Multi-stage build for React SPA
# Serves via nginx with optimized configuration
# ============================================================

# =====================================================
# Stage 1: Builder
# =====================================================
FROM node:20-alpine as builder

WORKDIR /app

# Build arguments
ARG VITE_API_URL=/api
ARG ENVIRONMENT=production
ARG VERSION=0.0.0

# Environment for build
ENV VITE_API_URL=${VITE_API_URL} \
    VITE_ENVIRONMENT=${ENVIRONMENT} \
    VITE_VERSION=${VERSION}

# Install dependencies
COPY package*.json ./
RUN npm ci --prefer-offline

# Copy source and build
COPY . .
RUN npm run build

# =====================================================
# Stage 2: Production (nginx)
# =====================================================
FROM nginx:1.25-alpine as production

# Build arguments
ARG VERSION=0.0.0

# Labels
LABEL org.opencontainers.image.title="NeuroLens Frontend" \
    org.opencontainers.image.version="${VERSION}" \
    org.opencontainers.image.description="NeuroLens React SPA"

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf 2>/dev/null || true

# Create custom nginx config if not exists
RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
listen 80;
listen [::]:80;
server_name _;

root /usr/share/nginx/html;
index index.html;

# Gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_proxied any;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml;
gzip_disable "MSIE [1-6]\.";

# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Cache static assets
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
expires 1y;
add_header Cache-Control "public, immutable";
}

# API proxy (if backend on same host)
location /api/ {
proxy_pass http://backend:8000/api/;
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection 'upgrade';
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_cache_bypass $http_upgrade;
}

# Health check
location /health {
access_log off;
return 200 "healthy\n";
add_header Content-Type text/plain;
}

# SPA fallback - serve index.html for all routes
location / {
try_files $uri $uri/ /index.html;
}

# Deny access to hidden files
location ~ /\. {
deny all;
}
}
EOF

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1001 -S nginx-user && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx-user nginx-user && \
    chown -R nginx-user:nginx-user /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1

# Expose port
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
