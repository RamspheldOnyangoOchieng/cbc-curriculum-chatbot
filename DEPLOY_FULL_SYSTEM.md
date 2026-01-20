# 🚀 Full System Deployment Guide: Frontend + Python Backend

This guide explains how to deploy both the **Next.js Frontend** and the new **Python Backend API** so they work together in the cloud.

## 🏗️ Architecture
*   **Frontend**: Next.js (Hosted on **Vercel**). User interface and Chat.
*   **Backend**: FastAPI Python (Hosted on **Render**). Handles file uploads and ingestion to Chroma.
*   **Database**: **Chroma Cloud** (Hosted by Chroma). Stores knowledge.
*   **AI**: **Groq API**. Generates answers.

---

## 📦 Step 1: Prepare the Repository
1.  Ensure all new files (`backend_main.py`, `requirements-backend.txt`, etc.) are committed to your GitHub repository.
2.  Push your changes to GitHub.

---

## 🐍 Step 2: Deploy Python Backend (Render)
We will use **Render.com** (it has a free tier for Python web services).

1.  **Create Account/Login** to [Render.com](https://render.com).
2.  Click **New +** -> **Web Service**.
3.  Connect your GitHub repository.
4.  **Configure Service**:
    *   **Name**: `cbc-chatbot-backend` (or similar)
    *   **Root Directory**: `.` (leave empty, it defaults to root)
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements-backend.txt`
    *   **Start Command**: `uvicorn backend_main:app --host 0.0.0.0 --port $PORT`
5.  **Environment Variables** (Add these in the Render Dashboard):
    *   `CHROMA_HOST`: `https://api.trychroma.com`
    *   `CHROMA_API_KEY`: *(Your Chroma API Key)*
    *   `CHROMA_TENANT`: *(Your Tenant ID)*
    *   `CHROMA_DATABASE`: *(Your Database Name)*
    *   `PYTHON_VERSION`: `3.9.0` (Recommended)
6.  Click **Deploy Web Service**.
7.  **Wait** for deployment to finish.
8.  **Copy the Service URL** (e.g., `https://cbc-chatbot-backend.onrender.com`). You will need this for the Frontend.

---

## 🌐 Step 3: Deploy Frontend (Vercel)
1.  Go to [Vercel.com](https://vercel.com) and select your project.
2.  Go to **Settings** -> **Environment Variables**.
3.  Add/Update the following:
    *   `PYTHON_BACKEND_URL`: Paste the **Render Service URL** from Step 2 (no trailing slash).
    *   `CHROMA_HOST`, `CHROMA_API_KEY`, etc. (Same as backend).
    *   `GROQ_API_KEY`: *(Your Groq Key)*.
4.  **Redeploy** your project (Go to **Deployments** -> Redeploy) to ensure it picks up the new variables.

---

## 💻 Local Development
To run "both together" locally:

1.  **Terminal 1 (Backend)**:
    ```bash
    # Install requests (first time only)
    pip install -r requirements-backend.txt
    
    # Run Server
    uvicorn backend_main:app --reload
    ```
    *Server will start at `http://localhost:8000`*

2.  **Terminal 2 (Frontend)**:
    Ensure `.env.local` has:
    ```
    PYTHON_BACKEND_URL=http://localhost:8000
    ```
    Then run:
    ```bash
    npm run dev
    ```
    *Frontend will start at `http://localhost:3000`*

---

## ✅ usage
*   Go to your Vercel URL.
*   Navigate to the **Upload/Knowledge** page.
*   Upload a PDF.
*   The Frontend sends it to the Render Backend.
*   The Backend processes it and updates Chroma Cloud.
*   The Chatbot (Frontend) can now answer questions about it immediately (because it reads from Chroma Cloud).
