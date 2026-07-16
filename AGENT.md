# AGENT.md — ClauseIQ Engineering Guide

**Status:** Living document — single source of truth for architecture, standards, and decisions.
**Audience:** Human developer + AI coding assistants (Claude, Antigravity, Cursor, Windsurf, Codex, and future agents).
**Rule Zero:** Every AI agent MUST read this document in full before writing, modifying, or deleting any code in this repository.

---

## 1. Project Overview

### 1.1 Vision
ClauseIQ is an AI-powered Enterprise Contract Intelligence Platform that turns static legal documents into structured, searchable, analyzable data. It gives legal and business teams the ability to understand what is actually inside their contracts — obligations, risks, dates, and money — without reading every page manually.

### 1.2 Business Problem
Organizations store contracts as unstructured PDFs and DOCX files scattered across drives and email threads. Nobody outside legal can quickly answer basic questions: "What's our termination notice period with this vendor?", "Do we have unlimited liability anywhere?", "What changed between contract v1 and v2?" Manual review is slow, expensive, and error-prone, and risk is discovered only after it becomes a problem (missed renewal, unfavorable jurisdiction, uncapped liability).

### 1.3 Product Goals
- Centralize contracts into searchable, organized projects.
- Automatically extract key clauses and structured metadata from any uploaded contract.
- Surface legal and commercial risk automatically, with severity and recommendations.
- Allow natural-language conversation with contracts, backed by real citations (not hallucination).
- Allow side-by-side comparison of contract versions to see what changed.
- Provide an executive-level summary for non-lawyers (founders, ops, finance).

### 1.4 Target Users
- **In-house legal teams** at small-to-mid-size companies without large legal departments.
- **Founders / operations leads** who sign contracts but are not lawyers.
- **Procurement and vendor management teams** tracking obligations across many vendor contracts.
- **Portfolio reviewers / technical evaluators** assessing this project as a demonstration of full-stack + AI engineering capability.

### 1.5 Product Philosophy
- **Contract intelligence first, chat second.** Chat is one feature among several, not the product. Clause extraction, risk detection, comparison, and summaries are equally, if not more, important.
- **Structured over conversational wherever possible.** Prefer deterministic, structured AI outputs (JSON schemas) over free-form text, so the product feels like software, not a chatbot wrapper.
- **Traceability is non-negotiable.** Every AI-generated claim (chat answer, risk, clause) must be traceable to a source location in the original document.
- **Practical scope over academic completeness.** This is a single-developer, AI-assisted MVP. Every architectural decision optimizes for shippability and clarity over theoretical purity.
- **Enterprise look and feel.** UI, data model, and API design should resemble a real B2B SaaS product, not a hackathon demo.

---

## 2. Project Scope

### 2.1 MVP Features (In Scope)
- Email/password registration and login with JWT authentication.
- Project-based organization of contracts (a "Project" groups related contracts, e.g., by vendor or deal).
- Upload of PDF and DOCX contracts, with text extraction, cleaning, and chunking.
- Embedding generation and vector storage per contract chunk.
- AI chat with a single contract or across a project, with multi-turn memory and source citations.
- Clause extraction across 11 predefined clause categories.
- Risk detection across 8 predefined risk categories, each with severity, explanation, and recommendation.
- One-page executive summary generation per contract.
- Two-version contract comparison (added / removed / modified clauses, changed obligations).
- Dashboard with aggregate stats: total contracts, high-risk contracts, recent uploads, recent activity.
- Keyword + embedding-based semantic search across contracts within a project.
- Basic contract management: list, view, search, delete.

### 2.2 Out-of-Scope Features (Explicitly Excluded)
The following are **not** implemented in this MVP. AI agents must not add them unless the developer explicitly requests a scope change:
- Multi-tenant billing, subscription plans, or payment processing (Stripe, etc.).
- Role-based access control beyond a single "owner" role per account (no team seats, no admin/reviewer roles).
- Real-time collaborative editing of contracts.
- E-signature or contract redlining/editing capabilities.
- OCR for scanned/image-based PDFs (only text-based PDFs and DOCX are supported).
- Support for file types beyond PDF and DOCX (no .txt, .rtf, .pages, images).
- Multi-language contract support (English-only for MVP).
- Support for more than two contract versions in comparison (only pairwise A/B comparison).
- Notifications, email alerts, or scheduled jobs (e.g., renewal reminders).
- Mobile native applications (web is responsive, but no iOS/Android app).
- SSO / SAML / OAuth enterprise login.
- Audit logging / compliance certifications (SOC2, HIPAA).
- Horizontal scaling infrastructure (Kubernetes, multi-region deployment) — see Section 18 for how the architecture *permits* this later without requiring it now.

---

## 3. Functional Requirements

### 3.1 Authentication
- User registers with email, password, and full name. Passwords are hashed with bcrypt.
- User logs in and receives a JWT access token (expiration configurable via `JWT_EXPIRATION_MINUTES`, default: 60 minutes) used as a Bearer token on all subsequent requests.
- All contract, project, and AI endpoints are protected routes requiring a valid JWT.
- No refresh-token rotation in MVP; the frontend re-prompts login on 401.

### 3.2 Project Management
- User creates a Project with a name and optional description (e.g., "Acme Corp MSA Negotiation").
- Contracts are uploaded into a Project. A contract always belongs to exactly one project.
- User can rename or delete a Project (deleting a project cascades to its contracts and their derived data).

### 3.3 Contract Upload & Management
- User uploads one PDF or DOCX file at a time (max size configurable via `MAX_UPLOAD_SIZE_MB`, default: 25MB), assigned to a project.
- On upload, the system immediately runs the full document processing pipeline (Section 9) synchronously for MVP simplicity (no background job queue — see Section 3.9 for rationale).
- User can view a list of contracts per project with metadata: filename, upload date, page count, processing status, overall risk level.
- User can view a single contract's detail page: extracted clauses, detected risks, executive summary, and chat interface.
- User can delete a contract, which removes its file, extracted text, chunks, embeddings, and derived AI outputs.
- User can search contracts by filename or by semantic content within a project.

### 3.4 Document Processing Pipeline
See Section 9 for the full pipeline. Functionally, the system must:
- Extract raw text from PDF (PyMuPDF) or DOCX (python-docx).
- Clean text (remove page-break artifacts, normalize whitespace, strip headers/footers where detectable).
- Chunk text into overlapping segments sized for retrieval quality (target size configurable via `CHUNK_SIZE_TOKENS`, default: ~500 tokens; overlap configurable via `CHUNK_OVERLAP_TOKENS`, default: 50 tokens).
- Generate embeddings for each chunk (Sentence Transformers, local, no external API dependency for embeddings).
- Persist chunk text + metadata in PostgreSQL and embeddings in ChromaDB, linked by a shared chunk ID.

### 3.5 AI Chat
- User opens a chat interface scoped to a single contract (MVP default) or, optionally, a whole project (stretch — same underlying pipeline, wider retrieval scope).
- User asks a question in natural language.
- System retrieves the top-k relevant chunks (k configurable via `RETRIEVAL_TOP_K`, default: 5) via vector similarity search, constructs a prompt with retrieved context + prior conversation turns, and calls Gemini.
- Response includes an answer plus a list of source citations (contract name, page/chunk reference).
- Conversation history is persisted per contract so context is available across a session (multi-turn).

### 3.6 Clause Extraction
- On document processing, the system runs a single structured-output Gemini call (or a small number of batched calls) instructing the model to extract each of the 11 clause categories (Payment Terms, Termination, Confidentiality, Intellectual Property, Governing Law, Liability, Indemnification, Renewal, Arbitration, Force Majeure, Non-Compete).
- For each category, the output includes: whether the clause is present, the extracted clause text/summary, and the source chunk reference(s) it was derived from.
- Clauses not found in the document are explicitly marked "Not Present" rather than omitted, so risk detection (Section 3.7) can reference missing clauses.

### 3.7 Risk Detection
- Risk detection runs after clause extraction and consumes its output (it does not re-read the raw document).
- For each of the 8 predefined risk categories (Unlimited Liability, Automatic Renewal, Missing Termination, Missing Confidentiality, Missing Intellectual Property, Vendor-favorable Jurisdiction, Vague Payment Terms, Missing Notice Period), the system determines whether the risk applies.
- Every detected risk includes exactly three fields: **Severity** (Low / Medium / High), **Explanation** (why this is a risk, referencing the relevant clause), and **Recommendation** (a concrete, actionable suggestion).
- The contract's overall risk level (shown on dashboard and contract list) is derived as the highest severity among its detected risks.

### 3.8 Executive Summary
- A single Gemini call, using the full clause extraction output as context, produces a structured one-page summary containing: Important Dates, Financial Terms, Key Obligations, and Major Risks (cross-referenced from Section 3.7 output).
- Rendered as a formatted page in the UI; not stored as a separate free-text blob but as structured fields so it renders consistently.

### 3.9 Contract Comparison
- User selects two contracts (typically two versions of the same agreement) within the same project.
- System retrieves each contract's extracted clauses (from Section 3.6) and asks Gemini to diff them, returning: Added Clauses, Removed Clauses, Modified Clauses (with before/after summaries), and Changed Obligations.
- Comparison operates on extracted clause data, not raw text diffing, so results are semantically meaningful rather than a line-by-line text diff.

### 3.10 Dashboard
- Aggregates and displays: total contract count, count of high-risk contracts, most recent uploads (count configurable via `DASHBOARD_RECENT_UPLOADS_LIMIT`, default: 5), and a recent activity feed (uploads, deletions, comparisons run).
- Computed via lightweight SQL aggregate queries at request time (no caching layer needed at MVP scale).

### 3.11 Semantic Search
- User enters a natural-language query scoped to a project.
- Query is embedded and compared against stored chunk embeddings (ChromaDB) to return the most relevant contracts/chunks, ranked by similarity score, with a text snippet preview.
- This is distinct from filename search (simple SQL `ILIKE`), which remains available for exact-match lookups.

---

## 4. Non-Functional Requirements

### 4.1 Security
- Passwords hashed with bcrypt (via `passlib`); never stored or logged in plaintext.
- JWT signing secret loaded from environment variable, never hardcoded.
- All protected endpoints validate JWT via a FastAPI dependency; ownership checks ensure a user can only access their own projects/contracts.
- Uploaded files validated by MIME type and extension before processing; rejected if not PDF/DOCX.
- File size capped via `MAX_UPLOAD_SIZE_MB` (default: 25MB) to prevent resource-exhaustion attacks.
- SQL access exclusively through SQLAlchemy ORM (parameterized) — no raw string-interpolated SQL.
- CORS restricted to the known frontend origin(s) via FastAPI middleware configuration.

### 4.2 Scalability
- Stateless FastAPI backend so multiple instances can run behind a load balancer in the future.
- Vector search isolated behind a repository interface so ChromaDB could be swapped for a managed vector DB (e.g., pgvector, Pinecone) without touching business logic.
- Document processing is synchronous in MVP but isolated in its own service module so it can be moved behind a task queue (Celery/RQ) later without changing calling code (see Section 18).

### 4.3 Reliability
- All AI calls (Gemini) wrapped in try/except with clear error propagation to the API layer (never a silent failure).
- Structured-output parsing from Gemini validated against Pydantic schemas; on schema validation failure, the request fails loudly with a descriptive error rather than returning malformed data to the frontend.
- Database writes for a single contract's processing pipeline are wrapped so partial failures (e.g., embedding step fails) leave the contract in a clearly marked "failed" processing status rather than a silently incomplete state.

### 4.4 Performance
- Chunking and embedding tuned for retrieval quality over raw speed (this is an analysis tool, not a real-time chat app).
- Vector search limited to top-k (`RETRIEVAL_TOP_K`, default: 5) to keep prompt size and Gemini latency predictable.
- Dashboard aggregate queries use indexed columns (user_id, project_id, created_at) to stay fast without caching at MVP scale.

### 4.5 Maintainability
- Strict separation of routers (HTTP layer), services (business logic), and models/schemas (data layer) on the backend — see Section 11.
- Consistent component/hook structure on the frontend — see Section 12.
- No business logic in route handlers or React components beyond orchestration and presentation.

### 4.6 Portability
- Backend is a standard FastAPI + PostgreSQL app deployable to any container host (Docker-first design).
- ChromaDB runs in local persistent-client mode for MVP, avoiding an extra managed service dependency.
- No cloud-provider-specific SDKs (e.g., no direct AWS S3 SDK lock-in) — local filesystem storage for uploaded files in MVP, abstracted behind a storage service so a cloud object store can be swapped in later.

### 4.7 Deployment Readiness
- Environment-driven configuration (`.env` + Pydantic Settings) for all secrets and connection strings.
- Alembic migrations required for every schema change — no manual DB edits, no `create_all()` in production paths.
- Dockerfile provided for backend; frontend built as static assets servable by any static host or reverse proxy.

---

## 5. Technology Decisions

| Technology | Role | Why Selected | Why Not the Alternatives |
|---|---|---|---|
| **React (Vite)** | Frontend SPA framework/build tool | Fast dev server, minimal config, industry-standard for modern SPAs | Next.js adds SSR/routing complexity this project (an authenticated dashboard app, not a public content site) doesn't need |
| **Tailwind CSS** | Styling | Utility-first speeds up building a consistent enterprise UI without a separate design system build step | Hand-written CSS or CSS-in-JS slows iteration and risks inconsistency across a solo-built app |
| **React Router** | Client-side routing | De facto standard for SPA routing, integrates cleanly with protected-route patterns | Framework-level routers (Next.js) are unnecessary without SSR needs |
| **Axios** | HTTP client | Interceptors make JWT attachment and centralized error handling straightforward | Native `fetch` requires more boilerplate for interceptor-equivalent behavior |
| **React Hook Form** | Form state/validation | Minimal re-renders, easy integration with schema validation for upload/auth forms | Formik is heavier and less performant for this scale of forms |
| **shadcn/ui** | Component primitives | Accessible, unstyled-by-default components that compose well with Tailwind, giving an enterprise look fast | Full component libraries (MUI, AntD) impose their own design language that fights Tailwind customization |
| **Lucide React** | Iconography | Consistent, lightweight icon set that pairs naturally with shadcn/ui | Font-icon libraries add unnecessary weight and less flexibility |
| **FastAPI** | Backend framework | Native async support, automatic OpenAPI docs, first-class Pydantic integration for validation — ideal for an AI-heavy API | Django REST Framework is heavier and less async-native; Flask requires manual assembly of validation/docs tooling |
| **SQLAlchemy** | ORM | Mature, explicit, well-understood patterns for relational modeling with full control over queries | Raw SQL loses type safety and migration tooling; Tortoise ORM has a smaller ecosystem |
| **Alembic** | Migrations | Standard migration tool paired with SQLAlchemy, enables reviewable, versioned schema changes | Manual schema management is untenable even for a solo dev once the schema evolves |
| **Pydantic** | Validation/schemas | Shared validation model between FastAPI request/response schemas and structured AI output parsing | Manual validation is error-prone and duplicative across these two use cases |
| **JWT Authentication** | Auth mechanism | Stateless, simple to implement and reason about for a single-role MVP | Session-based auth requires server-side session storage, unnecessary complexity for this scope |
| **PostgreSQL** | Primary relational database | Reliable, relational integrity for users/projects/contracts/clauses/risks with strong JSON column support for flexible metadata | NoSQL (MongoDB) would sacrifice relational integrity this domain clearly needs (foreign keys between contracts, projects, users) |
| **ChromaDB** | Vector database | Simple to run embedded/local, purpose-built for embeddings, zero external managed-service dependency for an MVP; a single collection with `user_id`/`project_id`/`contract_id`/`page_number`/`chunk_index`/`document_type` metadata supports scoped retrieval without the operational cost of one collection per contract | Pinecone/Weaviate add hosted-service cost and setup complexity not justified at this stage; pgvector would work but ChromaDB's dedicated API is a faster path for retrieval-specific operations |
| **LangChain** | RAG orchestration | Provides tested abstractions for chunking, retrieval, and prompt assembly, reducing custom RAG plumbing | Hand-rolling the full RAG pipeline duplicates well-tested logic without a clear benefit at this scope |
| **Google Gemini** | LLM for chat, extraction, risk detection, summarization, comparison | Strong structured-output support, competitive quality/cost, generous context window for contract-length documents | OpenAI GPT-4 is a viable alternative but Gemini's pricing/context-window profile fits contract-length documents well; the architecture isolates the LLM behind a service so swapping providers later is possible |
| **Sentence Transformers** | Embedding generation | Runs locally, no per-embedding API cost or external dependency, good semantic quality for contract text | Using Gemini's embedding API for every chunk adds cost and latency for a purely mechanical step best done locally |
| **PyMuPDF** | PDF text extraction | Fast, accurate text extraction with page-level granularity, actively maintained | pdfplumber is slower at scale; PyMuPDF's page mapping also supports future citation-by-page features |
| **python-docx** | DOCX text extraction | Standard, reliable library for reading paragraph/table structure from Word documents | No serious alternative with comparable maturity for this format |

---

## 6. High-Level Architecture

ClauseIQ follows a **layered monolith** architecture: a single FastAPI backend service, a single React SPA frontend, one relational database, and one vector database. This is intentional — a distributed/microservice architecture would add operational overhead with no benefit at MVP scale, while still allowing clean internal boundaries that support future extraction into services if ever needed (Section 18).

### 6.1 Frontend Architecture
A React SPA with route-based pages (Dashboard, Projects, Project Detail, Contract Detail, Chat, Comparison, Auth). All server communication goes through a single Axios-based API layer (`src/api/`). State is handled locally per page/feature with React hooks and context for auth state only — no global state library (Redux/Zustand) is introduced at this scope (see Section 12.5).

### 6.2 Backend Architecture
FastAPI app organized in three horizontal layers:
- **Routers** (`app/api/`): HTTP concerns only — request parsing, calling services, returning responses.
- **Services** (`app/services/`): all business logic, including orchestration of the RAG pipeline and AI workflows.
- **Models & Schemas** (`app/models/`, `app/schemas/`): SQLAlchemy ORM models and Pydantic request/response/AI-output schemas.

### 6.3 Database Layer
PostgreSQL holds all relational data: users, projects, contracts, clauses, risks, executive summaries, comparisons, chunk metadata, and chat messages. See Section 8 for the full schema.

### 6.4 AI Layer
A dedicated `ai/` service module wraps all Gemini interactions behind narrow, purpose-specific functions (`extract_clauses()`, `detect_risks()`, `generate_summary()`, `compare_contracts()`, `chat_completion()`). LangChain is used within this layer for prompt templating, retrieval chaining, and structured output parsing. No router or other service calls Gemini directly — everything goes through this layer.

### 6.5 Vector Database
ChromaDB runs as a local persistent client with a **single shared collection** for all chunk embeddings (or, if justified by scale, one collection per user/workspace). Each vector is written with metadata — `user_id`, `project_id`, `contract_id`, `page_number`, `chunk_index`, and `document_type` — and retrieval queries filter on this metadata (e.g., `contract_id` for a single-contract chat, `project_id` for project-wide search) rather than being routed to a differently-named collection per contract.

This metadata-filtering approach is preferred over a one-collection-per-contract strategy for several reasons:
- **Collection sprawl doesn't scale.** A collection per contract means thousands of collections at moderate usage, each carrying its own indexing/connection overhead — this degrades ChromaDB performance and operational simplicity far faster than metadata filtering does.
- **Cross-contract and cross-project queries are native, not bolted on.** Project-wide chat and semantic search (Sections 3.5, 3.11) need to query across many contracts at once; with per-contract collections this means querying N collections and merging results in application code, whereas a metadata filter expresses the same intent as a single query.
- **Consistent with the rest of the schema.** PostgreSQL already scopes every entity by `user_id`/`project_id`/`contract_id` (Section 8); mirroring that scoping as ChromaDB metadata keeps the vector store's access pattern consistent with the relational model instead of introducing a second, collection-based scoping scheme.
- **Simpler lifecycle management.** Deleting a contract or project becomes a metadata-filtered delete against one collection, rather than dropping and recreating collections.

### 6.6 Document Processing
A `document_processing/` service module handles extraction (PyMuPDF/python-docx), cleaning, and chunking, fully decoupled from the AI layer — it produces chunks; the AI layer consumes them.

### 6.7 Authentication
JWT-based auth implemented via a `auth/` module: password hashing, token creation/verification, and a FastAPI dependency (`get_current_user`) used across all protected routers.

### 6.8 Service Layer
Every feature (contracts, projects, chat, clauses, risks, summaries, comparisons, search) has one corresponding service module. Services never import from routers; routers never contain business logic beyond calling a service and shaping the response.

### 6.9 API Layer
A versioned REST API under `/api/v1/`, resource-oriented (`/projects`, `/contracts`, `/contracts/{id}/chat`, `/contracts/{id}/clauses`, `/contracts/{id}/risks`, `/contracts/{id}/summary`, `/comparisons`, `/search`, `/dashboard`), documented automatically via FastAPI's OpenAPI schema.

---

## 7. Recommended Folder Structure

### 7.1 Backend
```
backend/
├── alembic/                    # Migration scripts (Alembic-managed, never hand-edited)
├── app/
│   ├── main.py                 # FastAPI app instantiation, middleware, router registration
│   ├── config.py               # Pydantic Settings — all env-driven configuration
│   ├── database.py             # SQLAlchemy engine/session setup
│   ├── api/
│   │   ├── v1/
│   │   │   └── One router module per resource domain (auth, projects, contracts, chat, clauses, risks, summaries, comparisons, search, dashboard), each handling only HTTP concerns for that resource per Section 11. File names follow the resource name (e.g. `contracts.py`); this set grows as new resources are added — the router-per-resource pattern is what matters, not the exact file list.
│   ├── services/
│   │   └── One service module per resource domain, named `<resource>_service.py` (e.g. `contract_service.py`, the pipeline entry point referenced in Section 18), owning all business logic for that resource per Section 11. As with routers, the pattern (one service per resource) is the architectural rule; the specific set of services tracks the current feature set.
│   ├── ai/
│   │   ├── llm_client.py        # Thin LLM API wrapper
│   │   ├── prompts/             # Prompt templates per workflow
│   │   ├── embeddings.py        # Sentence Transformers wrapper
│   │   ├── retriever.py         # ChromaDB query logic
│   │   └── schemas.py           # Pydantic schemas for structured AI outputs
│   ├── document_processing/
│   │   ├── extractor.py         # PyMuPDF / python-docx extraction
│   │   ├── cleaner.py           # Text cleaning
│   │   └── chunker.py           # Chunking logic
│   ├── models/                  # SQLAlchemy ORM models, one file per entity
│   ├── schemas/                  # Pydantic request/response schemas, one file per resource
│   ├── auth/
│   │   ├── security.py          # Password hashing, JWT creation/verification
│   │   └── dependencies.py      # get_current_user and related FastAPI dependencies
│   ├── core/
│   │   ├── exceptions.py        # Custom exception classes + handlers
│   │   └── logging_config.py    # Logging setup
│   └── storage/
│       └── file_storage.py      # Local filesystem storage abstraction (swappable later)
├── tests/
├── .env.example
├── requirements.txt
└── Dockerfile
```

### 7.2 Frontend
```
frontend/
├── src/
│   ├── main.jsx
│   ├── App.jsx                   # Route definitions
│   ├── api/
│   │   ├── axiosClient.js        # Configured Axios instance + interceptors (JWT attachment, 401 handling)
│   │   └── One API module per resource domain, named `<resource>Api.js` (e.g. `contractsApi.js`) — the only place components call the backend, per Section 12. Grows with the resource set; not an exhaustive or fixed list.
│   ├── pages/
│   │   ├── auth/                 # Login, Register pages
│   │   ├── dashboard/
│   │   ├── projects/             # Project list, Project detail
│   │   ├── contracts/            # Contract detail (clauses/risks/summary tabs)
│   │   ├── chat/
│   │   ├── comparison/
│   │   └── search/
│   ├── components/
│   │   ├── ui/                   # shadcn/ui primitives
│   │   ├── layout/                # Navbar, Sidebar, PageContainer
│   │   └── shared/                 # RiskBadge, ClauseCard, FileUploadDropzone, etc.
│   ├── context/
│   │   └── AuthContext.jsx        # Auth state + JWT storage
│   ├── hooks/
│   │   └── Feature-specific data-fetching hooks (e.g. `useAuth.js`, `useContracts.js`) and small utility hooks (e.g. `useDebounce.js`) — added as needed, not a fixed set.
│   ├── routes/
│   │   └── ProtectedRoute.jsx
│   ├── lib/
│   │   └── utils.js                # Formatting helpers, cn() for Tailwind class merging
│   └── styles/
│       └── globals.css
├── index.html
├── vite.config.js
└── tailwind.config.js
```

---

## 8. Database Design

### 8.1 Main Entities
- **User**: id, email, hashed_password, full_name, created_at.
- **Project**: id, user_id (FK), name, description, created_at.
- **Contract**: id, project_id (FK), filename, file_path, file_type (pdf/docx), page_count, processing_status (pending/processing/completed/failed), overall_risk_level, uploaded_at.
- **DocumentChunk**: id, contract_id (FK), chunk_index, text, page_number, chroma_id (the ID used to look up the corresponding vector in ChromaDB).
- **ExtractedClause**: id, contract_id (FK), clause_type (enum: the 11 categories), is_present (bool), clause_text, source_chunk_ids (JSON array).
- **DetectedRisk**: id, contract_id (FK), risk_type (enum: the 8 categories), severity (low/medium/high), explanation, recommendation.
- **ExecutiveSummary**: id, contract_id (FK, unique), important_dates (JSON), financial_terms (JSON), key_obligations (JSON), major_risks (JSON), generated_at.
- **ChatMessage**: id, contract_id (FK), role (user/assistant), content, citations (JSON), created_at.
- **Comparison**: id, project_id (FK), contract_a_id (FK), contract_b_id (FK), added_clauses (JSON), removed_clauses (JSON), modified_clauses (JSON), changed_obligations (JSON), created_at.

### 8.2 Relationships
- User 1—N Project
- Project 1—N Contract
- Contract 1—N DocumentChunk
- Contract 1—N ExtractedClause
- Contract 1—N DetectedRisk
- Contract 1—1 ExecutiveSummary
- Contract 1—N ChatMessage
- Project 1—N Comparison (each referencing two Contracts within that project)

All foreign keys cascade on delete (deleting a Contract removes its chunks, clauses, risks, summary, and chat history; deleting a Project cascades to its Contracts).

### 8.3 Metadata Strategy
Structured, model-derived data (clauses, risks, summaries) is stored in normalized columns/JSON fields directly in PostgreSQL rather than re-fetched from the vector store — ChromaDB holds embeddings only, PostgreSQL is the source of truth for all structured and textual data. JSON columns are used only for genuinely variable-shape data (e.g., `important_dates`), not as a substitute for proper relational columns.

### 8.4 Uploaded File Handling
Uploaded files are stored on the local filesystem under a structured path (`storage/{user_id}/{project_id}/{contract_id}/{filename}`), with the path recorded in the `Contract.file_path` column. This is abstracted behind `storage/file_storage.py` so the underlying storage backend can change without touching calling code (Section 18).

### 8.5 Embedding Metadata
Each `DocumentChunk` row stores a `chroma_id` linking it to its vector in the shared ChromaDB collection (Section 6.5). The corresponding vector's ChromaDB metadata (`user_id`, `project_id`, `contract_id`, `page_number`, `chunk_index`, `document_type`) is what retrieval queries filter on, while the PostgreSQL row's `page_number`/`chunk_index` columns are what the frontend uses to render citations back to a specific page and chunk of the original document.

### 8.6 Future Scalability
The schema deliberately keeps clause/risk categories as enums rather than free-text so new categories can be added via a single migration. Contract and Project are already scoped by `user_id` at the top of the hierarchy, which is the natural seam for adding team/organization-level multi-tenancy later without restructuring existing tables (Section 18).

---

## 9. Complete RAG Pipeline

**Upload → Text Extraction → Cleaning → Chunking → Embedding Generation → Vector Storage → Retriever → Prompt Construction → Gemini → Structured Output → Source Citation**

1. **Upload**: The frontend sends the file via `multipart/form-data` to `/api/v1/contracts`. The backend validates type/size, stores the file via `file_storage.py`, and creates a `Contract` row with `processing_status = pending`.
2. **Text Extraction**: `document_processing/extractor.py` selects PyMuPDF (PDF) or python-docx (DOCX) and extracts raw text with page-level boundaries preserved.
3. **Cleaning**: `document_processing/cleaner.py` normalizes whitespace, strips repeated headers/footers and page-number artifacts, and removes non-content boilerplate (e.g., decorative separators) while preserving legal formatting like numbered clauses.
4. **Chunking**: `document_processing/chunker.py` splits cleaned text into chunks sized per `CHUNK_SIZE_TOKENS` (default: ~500 tokens) with `CHUNK_OVERLAP_TOKENS` overlap (default: 50 tokens), respecting paragraph boundaries where possible so clauses aren't split mid-sentence.
5. **Embedding Generation**: `ai/embeddings.py` runs each chunk through a Sentence Transformers model to produce a vector representation.
6. **Vector Storage**: Vectors are written to the single shared ChromaDB collection (Section 6.5); each vector's metadata includes `user_id`, `project_id`, `contract_id`, `page_number`, `chunk_index`, and `document_type`. The corresponding `DocumentChunk` row is written to PostgreSQL with the matching `chroma_id`.
7. **Retriever**: At query time (chat or search), `ai/retriever.py` embeds the user's query and performs a similarity search against the shared ChromaDB collection, filtered by metadata (`contract_id` for single-contract scope, `project_id` for project-wide scope), returning the top-k chunks.
8. **Prompt Construction**: `ai/prompts/` templates assemble a system instruction, the retrieved chunk texts (each tagged with its source page/chunk), and prior conversation turns (for chat) into a single prompt via LangChain.
9. **LLM**: `ai/llm_client.py` sends the constructed prompt to the LLM (Groq), requesting a structured response where applicable (clause extraction, risk detection, summary, comparison) or a conversational response with citation markers (chat).
10. **Structured Output**: The raw Gemini response is parsed and validated against the relevant Pydantic schema in `ai/schemas.py`; validation failures raise a clear, loggable error rather than silently passing through malformed data.
11. **Source Citation**: Each answer/clause/risk is linked back to the specific `chunk_index`/`page_number` it was derived from, which the frontend renders as a clickable citation reference.

---

## 10. Internal AI Workflows

### 10.1 AI Chat
User message → retrieve top-k chunks for the contract → construct prompt with chunks + last N conversation turns → Gemini call requesting an answer with inline citation markers → parse citations against retrieved chunk metadata → persist both user and assistant `ChatMessage` rows → return answer + citations to frontend.

### 10.2 Clause Extraction
Triggered once, immediately after chunking/embedding completes during upload processing → all chunks for the contract are concatenated (or, if the document exceeds the practical context window, the most content-dense chunks are prioritized) → single structured-output Gemini call requesting all 11 clause categories in one schema → response validated against `ClauseExtractionSchema` → one `ExtractedClause` row written per category.

### 10.3 Risk Detection
Triggered immediately after clause extraction completes → the `ExtractedClause` rows (not raw chunks) are passed as input → Gemini evaluates each of the 8 risk rules against the extracted clause data (e.g., "Missing Termination" checks the Termination clause's `is_present` flag; "Unlimited Liability" checks the Liability clause's text for absence of a cap) → response validated against `RiskDetectionSchema` → one `DetectedRisk` row written per applicable risk → `Contract.overall_risk_level` updated to the highest severity found.

### 10.4 Executive Summary
Triggered after clause extraction and risk detection complete → both are passed as input to a single Gemini call requesting the four summary sections → response validated against `ExecutiveSummarySchema` → one `ExecutiveSummary` row upserted for the contract.

### 10.5 Contract Comparison
User selects Contract A and Contract B within the same project → both contracts' `ExtractedClause` sets are retrieved (already computed, not recomputed) → a single Gemini call receives both clause sets and is asked to produce a structured diff → response validated against `ComparisonSchema` → one `Comparison` row persisted.

### 10.6 Semantic Search
User query → embedded via the same Sentence Transformers model used for chunk embeddings → similarity search against the shared ChromaDB collection, filtered by `project_id` metadata → results ranked by similarity score, joined back to `DocumentChunk`/`Contract` rows in PostgreSQL for display → returned with contract name, snippet, and similarity score (no Gemini call required for search — this is a pure vector-retrieval feature).

---

## 11. Backend Engineering Standards

- **Service Layer**: All business logic lives in `app/services/`. A router function should rarely exceed ~15 lines: parse/validate input (via Pydantic), call one service function, return its result.
- **Thin Routers**: Routers must not contain conditionals implementing business rules, direct DB queries, or direct AI calls. If a router needs an `if` statement beyond basic input presence checks, that logic belongs in a service.
- **Repository Usage**: No separate repository layer is introduced for MVP — services call SQLAlchemy directly. This is a deliberate simplification; do not add a repository abstraction layer unless the developer explicitly requests it.
- **SQLAlchemy Patterns**: Use the declarative ORM with explicit relationship definitions (`relationship()`, `back_populates`) and cascade rules defined at the model level, not scattered across services as manual delete loops.
- **Dependency Injection**: Use FastAPI's `Depends()` for database sessions (`get_db`) and current-user resolution (`get_current_user`). Do not instantiate DB sessions manually inside services.
- **Exception Handling**: Define custom exceptions in `app/core/exceptions.py` (e.g., `ContractNotFoundError`, `ProcessingFailedError`) and register global exception handlers in `main.py` that map them to appropriate HTTP status codes. Services raise domain exceptions; they never raise raw `HTTPException` (that's a router/handler-layer concern).
- **Logging**: Use Python's standard `logging` module configured in `app/core/logging_config.py`. Log at `INFO` for pipeline stage completion, `WARNING` for recoverable issues (e.g., a clause not found), and `ERROR` with stack trace for AI call failures or validation errors. Never log secrets, JWTs, or full document text.
- **Configuration Management**: All configuration lives in `app/config.py` as a Pydantic `Settings` class reading from environment variables. No config values are hardcoded in service code — this includes not just secrets and connection strings (DB URL, JWT secret, Gemini API key, ChromaDB path, upload directory) but also operational values that reasonably differ across environments or deployments, such as `JWT_EXPIRATION_MINUTES` (default: 60), `MAX_UPLOAD_SIZE_MB` (default: 25), `CHUNK_SIZE_TOKENS` (default: 500), `CHUNK_OVERLAP_TOKENS` (default: 50), `RETRIEVAL_TOP_K` (default: 5), and `DASHBOARD_RECENT_UPLOADS_LIMIT` (default: 5). When adding a new tunable value, default it sensibly and expose it as an environment variable rather than a literal in code.
- **Environment Variables**: A `.env.example` file documents every required variable with a placeholder value; actual `.env` is gitignored.
- **Validation**: All request/response shapes use Pydantic schemas in `app/schemas/`. AI outputs are validated with dedicated schemas in `app/ai/schemas.py` — these are never conflated with API request/response schemas even when field names overlap.
- **Type Hints**: All function signatures (services, routers, AI wrappers) must include full type hints, including return types. This is required, not optional, to keep the codebase self-documenting for AI agents.

---

## 12. Frontend Engineering Standards

- **Component Design**: Favor small, single-responsibility components. Presentational components (e.g., `RiskBadge`, `ClauseCard`) accept props and render; page components (`pages/`) handle data fetching and compose presentational components.
- **Folder Organization**: Follow the structure in Section 7.2 exactly — `pages/` for routed views, `components/shared/` for reusable domain components, `components/ui/` for shadcn/ui primitives only.
- **Routing**: All routes are defined centrally in `App.jsx` using React Router. Protected routes are wrapped in `<ProtectedRoute>`, which checks `AuthContext` and redirects to `/login` if unauthenticated.
- **API Layer**: Components never call Axios directly. Every API interaction goes through a function in `src/api/*Api.js`, which itself uses the shared `axiosClient.js` (JWT attached via request interceptor; 401 responses trigger logout via response interceptor).
- **State Management Strategy**: No global state library. Auth state lives in `AuthContext`. All other data is fetched per-page with local `useState`/`useEffect` (or a small custom hook like `useContracts`) — this is intentional simplicity appropriate to the MVP's scope; do not introduce Redux/Zustand/React Query unless the developer explicitly requests it.
- **Form Validation**: All forms (login, register, project creation, upload) use React Hook Form with inline validation messages; no ad-hoc manual form state.
- **Loading States**: Every data-fetching page must render an explicit loading state (skeleton or spinner) — never a blank screen during fetch, and never a layout shift once data arrives.
- **Error Handling**: API errors are caught at the calling component level and rendered as a visible message (toast or inline banner) — errors must never be silently swallowed in a `catch {}` block.
- **UI Consistency**: All UI is built from shadcn/ui primitives styled with Tailwind; avoid introducing one-off custom CSS for things a primitive already covers.
- **Responsive Design**: All pages must be usable down to tablet width (768px); dashboard and contract-detail data tables collapse to stacked cards below that width.

---

## 13. Coding Standards

- **Naming Conventions**: Python — `snake_case` for functions/variables, `PascalCase` for classes. JavaScript/React — `camelCase` for functions/variables, `PascalCase` for components.
- **File Naming**: Python files `snake_case.py`. React component files `PascalCase.jsx`. Non-component JS files (hooks, utils, api) `camelCase.js`.
- **Folder Naming**: Always lowercase, `kebab-case` if multi-word (e.g., `document-processing` is acceptable but the codebase standard is `snake_case` for Python packages per Section 7.1 — do not mix conventions within the same language's directories).
- **Function Design**: Functions should do one thing. Service functions should be named as verbs describing the business action (`extract_clauses_for_contract`, `detect_risks_for_contract`), not generic names (`process`, `handle`).
- **Class Design**: Classes are used for SQLAlchemy models, Pydantic schemas, and any stateful client wrappers (`GeminiClient`, `EmbeddingModel`). Do not create classes purely to group unrelated static functions — use a module instead.
- **Comments**: Comment the *why*, not the *what*. Avoid comments that restate the code. Every non-obvious business rule (e.g., why a specific risk threshold was chosen) should have a one-line comment explaining the reasoning.
- **Logging Standards**: See Section 11 — consistent log levels, no secrets, structured messages that include the relevant entity ID (e.g., `contract_id`).
- **Error Messages**: User-facing error messages must be specific and actionable ("File exceeds the {MAX_UPLOAD_SIZE_MB}MB limit" not "Upload failed"). Internal exception messages may include technical detail for debugging.
- **Reusability**: Before writing a new component or utility function, check `components/shared/` or `lib/utils.js` (frontend) and existing `services/` (backend) for something that already does this.
- **Code Duplication Rules**: Any logic duplicated in more than two places must be extracted into a shared function/component. Do not extract on the first occurrence — premature abstraction is also a violation of this standard.

---

## 14. AI Coding Rules

These rules are mandatory for every AI coding assistant working on this repository:

1. Always read `AGENT.md` in full before writing, modifying, or deleting any code.
2. Never modify files unrelated to the current task's scope.
3. Never introduce a new framework, library, or major dependency without first explaining the tradeoff and getting explicit approval.
4. Never replace or restructure the existing architecture (layering, folder structure, tech stack) defined in this document.
5. Keep all business logic inside `app/services/` (backend) — never in routers, never in React components.
6. Keep routers thin — HTTP concerns only.
7. Keep React components small and single-responsibility; extract shared UI into `components/shared/`.
8. Never hardcode secrets, API keys, or connection strings — always read from environment variables via `app/config.py`.
9. Never write directly to ChromaDB or Gemini from a router or a React component — always go through the designated service/AI layer.
10. Every schema change must go through an Alembic migration — never edit the database manually or use `Base.metadata.create_all()` outside of initial local setup.
11. Use meaningful, scoped commit messages (see Section 16) — never a bare "fix" or "update".
12. Before implementing a structural or architectural change (e.g., changing how a workflow is triggered, adding a new entity), explain the change and its impact on this document before writing code.
13. Preserve backward compatibility of existing API endpoints whenever possible; if a breaking change is unavoidable, flag it explicitly.
14. Avoid unnecessary refactoring — do not rewrite working code as a side effect of an unrelated feature request.
15. Do not add abstractions (repository layers, global state libraries, background job queues, caching layers) not already specified in this document unless explicitly requested.
16. Do not implement any feature listed in Section 2.2 (Out-of-Scope) without explicit developer instruction to change scope.
17. When an AI output schema changes, update both `app/ai/schemas.py` and the corresponding frontend rendering component in the same change — never let them drift.
18. All new endpoints must include a corresponding Pydantic response schema — no endpoint may return a raw dict or raw ORM object.
19. When in doubt about an ambiguous requirement, make the most conservative choice consistent with this document and note the assumption in the commit message or PR description.

---

## 15. Engineering Decisions

This section records the reasoning behind key technology choices so they are not silently replaced by a future contributor or AI agent. See Section 5 for the full comparative table; summarized rationale:

- **Why FastAPI**: Async-native, automatic OpenAPI generation, and first-class Pydantic integration make it the fastest path to a well-documented, validated API for an AI-heavy backend.
- **Why PostgreSQL**: The domain is fundamentally relational (users → projects → contracts → clauses/risks/chunks), and PostgreSQL's JSON column support covers the few genuinely flexible-shape fields without needing a second database.
- **Why ChromaDB**: Zero-setup local vector store that avoids a hosted-service dependency and cost for an MVP, using a single collection scoped by metadata (`user_id`, `project_id`, `contract_id`, `page_number`, `chunk_index`, `document_type`) rather than one collection per contract — see Section 6.5 for why metadata filtering scales better than collection-per-contract.
- **Why Gemini**: Strong structured-output reliability and a context window well-suited to full-contract-length inputs, at a cost profile appropriate for a portfolio project run repeatedly during development.
- **Why LangChain**: Removes the need to hand-roll retrieval chaining and prompt template management, which are well-solved, low-differentiation problems for this project.
- **Why React**: The team (solo developer) already targets a modern SPA with a component-driven UI; React's ecosystem (shadcn/ui, React Hook Form) directly supports the enterprise-SaaS look the product needs.
- **Why Vite**: Near-instant dev server startup and HMR speeds up iteration significantly compared to older bundler-based toolchains, with no SSR requirement to justify a heavier framework.

---

## 16. Git Workflow

- **Main branch**: `main` is always deployable; no direct commits to `main` except through merged feature branches.
- **Feature branches**: One branch per feature or fix, named `feature/<short-description>` or `fix/<short-description>` (e.g., `feature/clause-extraction`, `fix/upload-file-size-validation`).
- **Commit strategy**: Small, logically scoped commits. Commit message format: `<type>: <description>` where type is one of `feat`, `fix`, `refactor`, `docs`, `chore`, `test` (e.g., `feat: add risk detection service and schema`).
- **Push strategy**: Push feature branches frequently; do not accumulate large uncommitted/unpushed diffs.
- **Merge strategy**: Squash-merge feature branches into `main` once a feature is complete and manually verified, keeping `main`'s history one commit per feature.

---

## 17. Development Roadmap

Each phase is independently implementable and should be completed and verified before moving to the next.

**Phase 1 — Foundation**
Backend project scaffolding, PostgreSQL connection, Alembic setup, User model + auth (register/login/JWT), frontend scaffolding with routing and protected routes, login/register pages.

**Phase 2 — Project & Contract Management**
Project CRUD (backend + frontend), contract upload endpoint with file validation and storage, contract list/detail pages, delete functionality.

**Phase 3 — Document Processing Pipeline**
Text extraction (PyMuPDF/python-docx), cleaning, chunking, Sentence Transformers embedding generation, ChromaDB integration, `DocumentChunk` persistence, processing-status tracking end to end.

**Phase 4 — AI Chat**
Retriever implementation, prompt construction with LangChain, Gemini client wrapper, chat endpoint with citation parsing, chat UI with multi-turn history.

**Phase 5 — Clause Extraction & Risk Detection**
Clause extraction schema + Gemini workflow, risk detection schema + Gemini workflow (consuming clause output), contract detail UI tabs for clauses and risks with severity styling.

**Phase 6 — Executive Summary & Dashboard**
Executive summary Gemini workflow + UI page, dashboard aggregate queries + UI (total contracts, high-risk count, recent uploads, recent activity).

**Phase 7 — Comparison & Search**
Contract comparison workflow (clause-diff Gemini call) + comparison UI, semantic search endpoint + search UI, filename search.

**Phase 8 — Polish & Deployment Readiness**
Responsive design pass, loading/error state audit across all pages, Dockerfile finalization, `.env.example` completeness check, README with setup instructions.

---

## 18. Future SaaS Expansion

The MVP architecture intentionally leaves these extension points open without requiring a rewrite:

- **Multi-tenancy**: Because `Project` and `Contract` are already scoped by `user_id`, introducing an `Organization` entity above `User` (with `Organization` owning `Project`s and `User`s belonging to an `Organization` with a role) is an additive schema change, not a restructuring.
- **Background processing**: The document processing pipeline is already isolated in `document_processing/` and `ai/` service modules called synchronously from `contract_service.py`. Moving to async processing later means introducing Celery/RQ and changing the *call site* to enqueue a task — the pipeline logic itself does not need to change.
- **Object storage**: `storage/file_storage.py` abstracts file persistence behind a small interface; swapping local filesystem storage for S3-compatible object storage is a change to that one module.
- **Vector database swap**: `ai/retriever.py` and the embedding-write path in the processing pipeline are the only places that talk to ChromaDB directly, so migrating to a managed vector database is isolated to those files.
- **Team roles / RBAC**: The `get_current_user` dependency is the single choke point for authorization; adding role checks (e.g., "reviewer" vs "owner") extends this dependency rather than touching every router individually.
- **Billing/subscriptions**: Would attach to the future `Organization` entity as a separate `Subscription` model and a small `billing/` service module, without touching the contract-intelligence domain logic at all.
- **LLM provider flexibility**: Because all LLM calls are isolated behind `ai/llm_client.py`, adding support for an alternative model provider is a matter of implementing an alternate client behind the same function signatures used by `ai/` workflows.

## 19. Developer Workflow

This section defines the expected workflow for every development session involving an AI coding assistant (or a human following the same discipline). It operationalizes Rule Zero and the AI Coding Rules in Section 14 into a concrete, repeatable sequence — follow it in order for every feature, fix, or change, regardless of size.

1. **Read `AGENT.md` completely.** Do not skim or jump to a section based on a keyword match — architectural decisions in one section frequently constrain what's acceptable in another (e.g., a Section 2.2 out-of-scope item interacts with the Section 17 roadmap phase you're working in).
2. **Understand the requested feature.** Restate the request in your own words, including what it does *not* ask for. If the request is ambiguous or could conflict with an existing decision in this document, resolve the ambiguity using Rule 19 in Section 14 (make the most conservative choice consistent with this document) or ask before proceeding.
3. **Identify affected modules.** Using the architecture in Sections 6–9, name the specific routers, services, models, schemas, AI workflows, or frontend components the change touches — and just as importantly, confirm which ones it does not.
4. **Explain the implementation plan before writing code.** Summarize the approach, the files to be touched, and any tradeoffs, per Section 14 Rule 12. This is especially required for anything structural (new entity, new workflow, changed data flow) but is good practice even for small changes, since it surfaces scope creep before it happens.
5. **Modify only the files required.** Resist the urge to "improve" adjacent code as part of an unrelated change (Section 14 Rules 2 and 14).
6. **Avoid unrelated refactoring.** If existing code in a touched file is suboptimal but outside the current task's scope, leave it and note it rather than rewriting it inline.
7. **Verify existing functionality still works.** Re-check the flows adjacent to your change (e.g., a chat prompt-construction change should be checked against citation rendering) before considering the task done. Add or update tests where the codebase already has test coverage for the area touched.
8. **Summarize completed work.** State what changed, which files were touched, why, and any assumptions made along the way (per Section 14 Rule 19) — this keeps the commit message (Section 16) and any PR description accurate and gives the developer a clear record to review.

Skipping steps in this workflow — particularly step 1 (reading this document) and step 4 (explaining the plan before coding) — is the most common source of architectural drift in AI-assisted development and is not acceptable practice on this project.
