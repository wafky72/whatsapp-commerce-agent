# AI WhatsApp Commerce Bot 🤖🛍️

This is a premium FastAPI-based backend for an AI-powered WhatsApp Commerce Assistant, specifically designed for Ecommerce business. It integrates WATI (WhatsApp API), Groq (Llama 3.1 8B/70B), ChromaDB (Vector RAG), and WooCommerce to provide a professional, data-driven shopping experience.

## ✨ Features

-   **High-Performance AI**: Powered by Groq for lightning-fast response times.
-   **Strict RAG Context**: Uses ChromaDB and Local Embeddings (`all-MiniLM-L6-v2`) to ensure 100% data adherence to product and FAQ files.
-   **WooCommerce Engine**: Live interaction with WooCommerce for product search, status, and cart management.
-   **Premium Admin Dashboard**: Sleek, glassmorphic dashboard for real-time analytics, behavior configuration, and appearance customization.
-   **WhatsApp Native**: Seamless integration with WATI for professional messaging and order tracking.
-   **Stateless Intelligence**: Optimized for standalone request processing with aggressive hallucination prevention.

## 🚀 Quick Start

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file with the following:
    ```env
    GROQ_API_KEY=gsk_...
    WATI_TOKEN=...
    WATI_API_ENDPOINT=https://live-server-XXXX.wati.io
    WOO_URL=https://yourwebsite.com
    WOO_KEY=ck_...
    WOO_SECRET=cs_...
    ```

3.  **Run the Server**:
    ```bash
    python main.py
    ```
    The server will start at `http://localhost:8003`.

4.  **Expose to Internet**:
    Expose the port using ngrok:
    ```bash
    ngrok http 8003
    ```
    Set your WATI webhook to: `https://your-ngrok-url.ngrok.io/webhook`

## 📂 Project Structure

-   `main.py`: Core logic, FastAPI routes, and Agentic Tool calling engine.
-   `rag.py`: Vector store management and similarity retrieval.
-   `woo_handler.py`: WooCommerce API interface and product formatting.
-   `prompts.py`: Highly tuned system prompts for Roze BioHealth compliance.
-   `admin/`: Premium glassmorphic administrative control panel.
-   `widget/`: Embeddable web chat widget for cross-platform support.
-   `data/`: Source documents for the knowledge base.

## 🛠️ Admin Dashboard

Access the dashboard at `http://localhost:8003/admin` to customize the widget appearance, adjust AI creativity, and monitor real-time conversation analytics.
