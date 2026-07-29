# AI Workflow Platform

> Một nền tảng mã nguồn mở giúp xây dựng AI Agent và AI Workflow dành cho doanh nghiệp bằng Python.
>
> Mục tiêu của dự án là kết hợp **AI Engineering** và **Backend Engineering**, cung cấp khả năng xây dựng các Agent AI có thể đọc tài liệu, gọi công cụ, truy xuất dữ liệu và tự động hóa quy trình nghiệp vụ tương tự Microsoft Copilot Studio, n8n AI hay LangGraph Platform.

---

# Mục tiêu

AI Workflow Platform được xây dựng nhằm giải quyết các bài toán tự động hóa trong doanh nghiệp thông qua AI Agent.

Nền tảng cho phép người dùng:

- Tạo AI Agent
- Tạo Workflow nhiều bước
- Kết nối với LLM
- Xây dựng Tool riêng
- Quản lý dữ liệu
- Tích hợp Email, SharePoint, Database...
- Hỗ trợ RAG
- Hỗ trợ Multi-Agent
- Quản lý lịch sử hội thoại
- Quản lý quyền người dùng

---

# Mục tiêu học tập

Dự án được xây dựng nhằm nâng cao năng lực ở hai lĩnh vực:

## AI Engineering

- Large Language Model
- Prompt Engineering
- Tool Calling
- Function Calling
- RAG
- Embedding
- Vector Database
- Multi-Agent
- Memory
- MCP (Model Context Protocol)

## Backend Engineering

- FastAPI
- Async Python
- SQLAlchemy
- PostgreSQL
- Redis
- Celery
- Docker
- Clean Architecture
- REST API
- Authentication
- Authorization
- Background Worker
- Event Driven Architecture

---

# Kiến trúc hệ thống

```
                React / NextJS

                      │

             REST API / WebSocket

                      │

               FastAPI Backend

                      │

 ┌──────────────┬───────────────┬───────────────┐
 │              │               │               │
Auth       Workflow Engine    AI Engine     Tool Engine
 │              │               │               │
 │          DAG Executor      LLM Adapter    Email
 │          Scheduler         Memory         Database
 │          Queue             RAG            Excel
 │          Event             Agent          SharePoint
 │
 └──────────────┴───────────────┴───────────────┘

                      │

        PostgreSQL      Redis      Vector DB

```

---

# Công nghệ sử dụng

## Backend

- Python 3.13
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic V2

---

## Database

- PostgreSQL
- Redis
- Qdrant (hoặc pgvector)

---

## AI

- OpenAI
- Claude
- Gemini
- Ollama
- OpenRouter

---

## AI Framework

- LangGraph
- PydanticAI
- MCP SDK

---

## Authentication

- JWT
- OAuth2
- Google Login
- Microsoft Login

---

## Storage

- MinIO
- Local Storage

---

## DevOps

- Docker
- Docker Compose
- GitHub Actions

---

# Core Modules

## User Management

- Login
- Register
- Refresh Token
- Role
- Permission

---

## Workspace

Một Workspace đại diện cho một tổ chức hoặc nhóm người dùng.

---

## AI Agent

Cho phép tạo Agent AI với:

- Prompt
- System Prompt
- Model
- Temperature
- Memory
- Tool

---

## Workflow

Workflow được tạo từ nhiều bước.

Ví dụ:

```
Read Email

↓

Extract Information

↓

Search Database

↓

Generate Response

↓

Draft Email
```

---

## Tool

Mỗi Tool đại diện cho một khả năng mà AI có thể sử dụng.

Ví dụ:

- Search SQL
- Search Product
- Search Customer
- Read Excel
- Read PDF
- Send Email
- Generate Word
- Generate PowerPoint
- Generate Excel

---

## RAG

Cho phép AI trả lời dựa trên dữ liệu doanh nghiệp.

Quy trình:

```
Upload Document

↓

Chunking

↓

Embedding

↓

Vector Database

↓

Semantic Search

↓

LLM

↓

Answer
```

---

## Memory

Bao gồm:

- Conversation Memory
- Summary Memory
- Long-term Memory

---

## MCP

Hỗ trợ Model Context Protocol.

Ví dụ:

- Outlook MCP
- Database MCP
- Excel MCP
- SharePoint MCP

---

## Background Worker

Sử dụng Celery để xử lý:

- Embedding
- OCR
- Email
- Report
- Notification

---

# Dự kiến tính năng

## Chat

- Chat với AI
- Streaming Response
- Multi Model
- Conversation History

---

## Document

- Upload PDF
- Upload DOCX
- Upload Excel
- OCR
- Semantic Search

---

## Email

- Đọc Email
- Tóm tắt Email
- Trích xuất thông tin
- Soạn Email
- Gửi Email

---

## Database

- Natural Language to SQL
- Query Database
- Data Summary

---

## Workflow

Cho phép kéo thả các Node:

- LLM
- Tool
- Condition
- Loop
- Delay
- Branch
- HTTP Request

---

## Monitoring

- Log
- Workflow History
- Token Usage
- Cost
- Response Time

---

# Kiến trúc Backend

```
app/

├── api/
├── auth/
├── core/
├── database/
├── models/
├── repositories/
├── services/
├── workflows/
├── agents/
├── tools/
├── rag/
├── workers/
├── schemas/
├── middleware/
├── integrations/
└── utils/

```

---

# Roadmap

## Phase 1

- Authentication
- PostgreSQL
- Docker
- User Management
- Chat API

---

## Phase 2

- AI Provider
- Multi Model
- Streaming Chat

---

## Phase 3

- Tool Calling
- Workflow Engine

---

## Phase 4

- RAG
- Embedding
- Vector Database

---

## Phase 5

- MCP
- Multi-Agent

---

## Phase 6

- Monitoring
- Dashboard
- Deployment

---

# Mục tiêu cuối cùng

Xây dựng một nền tảng AI Workflow mã nguồn mở có khả năng:

- Xây dựng AI Agent
- Tạo Workflow AI
- Kết nối nhiều LLM
- Hỗ trợ RAG
- Hỗ trợ MCP
- Tích hợp Email
- Tích hợp Database
- Tích hợp SharePoint
- Quản lý Tool
- Quản lý Agent
- Quản lý Workflow

Đồng thời đây sẽ là dự án portfolio giúp thể hiện năng lực về:

- AI Engineering
- Backend Engineering
- System Design
- Distributed Systems
- Enterprise AI Development
