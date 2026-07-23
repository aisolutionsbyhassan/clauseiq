# ClauseIQ ⚡

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

**An enterprise-grade, AI-powered Contract Intelligence Platform.**

[Watch the Demo Video](https://youtube.com/your-video-link-here) <!-- Replace with actual link -->

</div>

## 📖 Overview

ClauseIQ is a full-stack, AI-driven legal tech platform designed to automate the extraction, analysis, and risk assessment of complex legal contracts. Leveraging advanced **Retrieval-Augmented Generation (RAG)**, Vector Databases, and state-of-the-art LLMs (Llama-3 via Groq), ClauseIQ allows users to upload contracts (PDF/DOCX) and instantly interact with them through semantic search, side-by-side comparisons, and conversational AI.

## ✨ Key Features

- **Document Processing Pipeline:** Instantly parses and chunks PDF and DOCX files.
- **AI Risk Detection:** Automatically identifies and highlights critical risks (e.g., Unlimited Liability, IP Ownership loss, strict Non-Competes).
- **Hybrid Search & RAG:** Powered by a local **ChromaDB** vector database with LLM-based Query Expansion (HyDE) for hyper-accurate retrieval.
- **"Ask Your Contracts" Chat:** Multi-turn conversational memory allowing users to interrogate their contracts with sub-second latency.
- **Contract Comparison:** Side-by-side semantic comparison of multiple contracts within a project.
- **Secure Authentication:** JWT-based user authentication with secure password hashing via `bcrypt`.

## 🏗️ Architecture

ClauseIQ follows a modern, modular microservices-inspired architecture:

- **Frontend:** React + Vite, styled with Tailwind CSS and Radix UI primitives.
- **Backend:** FastAPI (Python), entirely async for high-concurrency performance.
- **Database:** PostgreSQL (with Alembic for migrations) for relational data management.
- **Vector Engine:** Local ChromaDB for ultra-fast, low-latency embedding retrieval.
- **AI Inference:** Groq API integration (Llama-3.3-70b) for lightning-fast generative AI responses.

## 🚀 Quick Start (Docker)

The entire platform is fully dockerized. You can spin up the Frontend, Backend, and Database with a single command. No dependencies required other than Docker!

### Prerequisites
- Docker & Docker Compose installed.
- A Groq API Key (Free tier works perfectly).

### 1-Click Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/clauseiq.git
   cd clauseiq
   ```

2. **Set your API Keys & Environment Variables:**
   The project requires a `.env` file which is ignored by Git for security. We have provided a template file.
   Copy `backend/.env.example` and rename it to `backend/.env`. Then open it and replace the placeholder with your actual Groq key:
   ```env
   GROQ_API_KEY=your_actual_api_key_here
   ```

3. **Spin up the stack:**
   ```bash
   docker-compose up -d --build
   ```

4. **Access the Application:**
   - Frontend: `http://localhost:3000`
   - Backend API Docs: `http://localhost:8000/docs`

The database schema will automatically migrate on startup. You can immediately register a new account and start uploading contracts!

## 🧪 Running Locally (Without Docker)

<details>
<summary>Click to expand local development instructions</summary>

**Backend:**
1. Navigate to the `backend` directory.
2. Install dependencies: `pip install -r requirements.txt`
3. Ensure PostgreSQL is running locally and update `DATABASE_URL` in `.env`.
4. Run migrations: `alembic upgrade head`
5. Start server: `uvicorn app.main:app --reload`

**Frontend:**
1. Navigate to the `frontend` directory.
2. Install dependencies: `npm install`
3. Start server: `npm run dev`

</details>

## 🛡️ License
This project is open-source and available under the MIT License.
