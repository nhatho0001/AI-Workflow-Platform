# ============================================
# FastAPI Backend Dockerfile
# ============================================

# ---------- Stage 1: Builder ----------
FROM python:3.12-slim AS builder

WORKDIR /app

# Cài dependencies trước để tận dụng Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Tạo user non-root để chạy app (bảo mật)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy dependencies đã build từ stage 1
COPY --from=builder /install /usr/local

# Copy source code
COPY . .

# Đổi ownership cho app user
RUN chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Chạy FastAPI với uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]