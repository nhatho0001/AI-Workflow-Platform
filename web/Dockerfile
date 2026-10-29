# ============================================
# Frontend Dockerfile (Vite build → nginx)
# ============================================

# ---------- Stage 1: Build ----------
FROM node:24-alpine AS builder

WORKDIR /app

# Cài dependencies trước để tận dụng Docker cache
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Biến VITE_* được nhúng vào bundle lúc build, không đổi được lúc chạy container
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_DEFAULT_MODEL_ID=00000000-0000-0000-0000-000000000001
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_DEFAULT_MODEL_ID=$VITE_DEFAULT_MODEL_ID

RUN npm run build

# ---------- Stage 2: Runtime ----------
FROM nginx:1.29-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
