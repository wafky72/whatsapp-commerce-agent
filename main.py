import os
import logging
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
import requests
import json
import re

from rag import RAGHandler
from woo_handler import WooCommerceHandler
from prompts import SYSTEM_PROMPT
from cache_handler import ResponseCache
from settings_manager import SettingsManager
from analytics_manager import AnalyticsManager
from cart_manager import CartManager
from memory_manager import MemoryManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Add CORS Middleware (Critical for ngrok and widget cross-origin requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize handlers
rag = RAGHandler()
woo = WooCommerceHandler()
settings_manager = SettingsManager()
analytics = AnalyticsManager()
cart_manager = CartManager()
memory = MemoryManager()

# Initialize Groq client (OpenAI-compatible)
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
response_cache = ResponseCache(ttl_minutes=5)  # Cache responses for 5 minutes

# Model Configuration
MODEL_NAME = "llama-3.1-8b-instant"  # High speed, high rate limits 

# ... (WATI Config remains same) ...

# ... (Startup event remains commented or we can uncomment it, but crawler handles ingestion now) ...

class TestMessage(BaseModel):
    message: str
    session_id: Optional[str] = "web_demo"

@app.get("/")
def read_root():
    return {"status": "active", "service": "AI WhatsApp Commerce Bot (Live Only)"}

def send_whatsapp_message(wa_id: str, message: str):
    """
    Send a message back to the user via WATI API.
    """
    if not WATI_TOKEN:
        logger.error("WATI_TOKEN not set. Cannot send message.")
        return

    url = f"{WATI_API_ENDPOINT}/api/v1/sendSessionMessage/{wa_id}"
    headers = {
        "Authorization": f"Bearer {WATI_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "messageText": message
    }
    
    try:
        response = requests.post(url, headers=headers, params=params)
        response.raise_for_status()
        logger.info(f"Message sent to {wa_id}: {response.json()}")
    except Exception as e:
        logger.error(f"Failed to send message to {wa_id}: {e}")

# --- TOOL DEFINITIONS (Groq-Compatible) ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_store_products",
            "description": "Search for products in the WooCommerce store. If query is empty, returns the product catalog.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Product search keyword. Use empty string to list all products."
                    }
                },
                "required": []  # Make query optional for catalog listing
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": "Retrieve order details and status by order ID number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID as a string of digits"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search website content for educational information like ingredients, benefits, policies, or company info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search topic or question"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_cart",
            "description": "Add items to the user's shopping cart. Call this when the user explicitly agrees to buy something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "remove", "view", "clear"],
                        "description": "Action to perform on the cart"
                    },
                    "product_id": {
                        "type": "string",
                        "description": "The ID of the product to add/remove (required for add/remove)"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Quantity to add (default 1)"
                    }
                },
                "required": ["action"]
            }
        }
    }
]


class BotResponse(BaseModel):
    text: str
    products: Optional[list] = []
    order_details: Optional[dict] = None
    quick_replies: Optional[list] = []
    cart_state: Optional[dict] = None  # New field for cart UI updates
    function_call: Optional[str] = None

def generate_bot_response(user_message: str, session_id: str = "demo_user", platform: str = "whatsapp") -> BotResponse:

    """
    Core logic: Agentic Tool Use (MCP Style).
    The AI decides which tool to call based on the user message.
    """
    # 1. Check Cache First (Save API Calls)
    # cache key now includes platform to differentiate formatting if needed, 
    # though for now we stick to one cache.
    cached_response_str = response_cache.get(user_message)
    if cached_response_str:
        logger.info("💾 Returning cached response")
        # For simplicity in this iteration, cache stores just text. 
        # Ideally, we cache the full JSON. Let's assume text for now to be safe or reconstruct.
        return BotResponse(text=cached_response_str)
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    try:
        # 2. First Call: Let AI decide if it needs tools
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            parallel_tool_calls=False,  # Groq works better with sequential calls
            temperature=0.7,
            max_tokens=1024
        )
        
        response_message = completion.choices[0].message
        tool_calls = response_message.tool_calls

        # 3. If no tools needed, just return the text
        if not tool_calls:
            final_response = response_message.content
            response_cache.set(user_message, final_response)
            return BotResponse(text=final_response)

        # 4. Process Tool Calls
        # IMPORTANT: Some models put tech-talk in the 'content' even when calling tools.
        # We clear it to prevent it from leaking into the final user-facing response.
        response_message.content = "" 
        messages.append(response_message) 

        # Captured data for rich UI
        found_products = []
        found_order = None

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            tool_output = ""
            
            logger.info(f"🤖 Executing Tool: {function_name} | Args: {args}")

            if function_name == "search_store_products":
                query = args.get("query", "")
                products = woo.get_products(search_term=query) if query else woo.get_products()
                if products:
                    found_products = products[:5]
                    tool_output = "FOUND LIVE PRODUCTS:\n"
                    for p in products[:5]:
                        tool_output += woo.format_product_for_chat(p) + "\n---\n"
                else:
                    tool_output = "No products found matching your request."

            elif function_name == "check_order_status":
                order_id = args.get("order_id")
                order = woo.get_order_by_id(order_id)
                if order:
                    found_order = order
                    tool_output = f"ORDER STATUS:\nID: {order['id']}\nStatus: {order['status']}\nTotal: {order['currency']} {order['total']}\nItems: {order['line_items']}"
                else:
                    tool_output = "Order not found. Please check the ID."

            elif function_name == "search_knowledge_base":
                query = args.get("query", "")
                if not query:
                    tool_output = "Please provide a topic to search."
                else:
                    docs = rag.query(query)
                    tool_output = f"KNOWLEDGE BASE INFO:\n{docs}" if docs else "No relevant info found."

            elif function_name == "manage_cart":
                action = args.get("action")
                p_id = args.get("product_id")
                qty = args.get("quantity", 1)
                # session_id passed from function signature

                if action == "add" and p_id:
                    try:
                        prod_list = woo.get_products(search_term=p_id) 
                        target_product = prod_list[0] if prod_list else None
                        if target_product:
                            cart_summary = cart_manager.add_item(session_id, target_product, qty)
                            tool_output = f"Added {target_product['name']} to cart. Total: {cart_summary['total']}"
                        else:
                            tool_output = "Product not found to add to cart."
                    except Exception as e:
                        tool_output = f"Error adding to cart: {str(e)}"
                elif action == "view":
                    cart = cart_manager.get_cart_summary(session_id)
                    tool_output = f"Cart contains {cart['count']} items. Total: {cart['total']}"
                elif action == "clear":
                    cart_manager.clear_cart(session_id)
                    tool_output = "Cart cleared."
                else:
                    tool_output = f"Action {action} performed on cart."

            # ADD PROPER TOOL MESSAGE (Standard OpenAI/Groq sequence)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": str(tool_output)
            })

        # 5. Second Call: Final response generation (STRICTLY TEXT ONLY)
        final_completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=None 
        )
        
        text = final_completion.choices[0].message.content or ""
        
        # AGGRESSIVE CLEANING: Strip technical markers and artifacts
        # Remove anything in between < > or { } that looks like code/JSON
        text = re.sub(r'<[^>]*>', '', text)  # Remove all HTML-like tags
        text = re.sub(r'\{[^{}]*"query"[^{}]*\}', '', text)  # Remove JSON queries
        text = re.sub(r'\{[^{}]*"action"[^{}]*\}', '', text)  # Remove JSON actions
        text = re.sub(r'search_store_products\(.*?\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'manage_cart\(.*?\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'search_knowledge_base\(.*?\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'check_order_status\(.*?\)', '', text, flags=re.IGNORECASE)
        
        # Remove common LLM artifacts if any leak
        text = text.replace("Tool call:", "")
        text = text.replace("Action:", "")
        text = text.replace("Observation:", "")
        
        # Final cleanup: remove double spaces/newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()

        logger.info(f"✨ Final Cleaned Response: {text[:100]}...")
        
        final_response_text = text
        response_cache.set(user_message, final_response_text)
        
        # Calculate Quick Replies based on context (ROZE Categories from Website)
        quick_replies = ["New Items", "Most Popular", "Bundles", "Gift Set", "Bathroom Essentials", "Travel"]
        if found_products:
            # If products found, emphasize relevant categories or search
            quick_replies = ["Most Popular", "Bundles", "Bathroom Essentials", "Search More"]
        elif found_order:
            quick_replies = ["Track Another", "Support", "All Items"]

        # FETCH FINAL CART STATE
        # If any cart action happened, we want to send the latest state
        current_cart = cart_manager.get_cart_summary(session_id)

        # Normalize products for UI (Web Widget)
        sanitized_products = []
        for p in found_products:
            # Create a safe copy for UI
            ui_p = p.copy()
            # Ensure image_url is easily accessible
            if p.get("images") and len(p["images"]) > 0:
                ui_p["image_url"] = p["images"][0]["src"]
            else:
                ui_p["image_url"] = "https://placehold.co/100?text=No+Image"
            sanitized_products.append(ui_p)

        return BotResponse(
            text=final_response_text,
            products=sanitized_products,
            order_details=found_order,
            quick_replies=quick_replies,
            cart_state=current_cart # Send cart state to frontend
        )

    except Exception as e:
        error_str = str(e)
        logger.error(f"Agent Loop Error: {error_str}")
        
        # If Groq function calling failed, fall back to context injection method
        if "tool_use_failed" in error_str or "function" in error_str.lower():
            logger.warning("⚠️ Function calling failed. Falling back to context injection method.")
            try:
                # Fallback: Manually build context and ask without tools
                context = ""
                
                # Try to extract RAG context
                try:
                    docs = rag.query(user_message, n_results=3)
                    if docs:
                        if isinstance(docs, list):
                            context += "=== Knowledge Base ===\n" + "\n".join(docs) + "\n\n"
                        else:
                            context += f"=== Knowledge Base ===\n{docs}\n\n"
                except:
                    pass
                
                # Try to fetch products if it seems product-related
                msg_lower = user_message.lower()
                if any(word in msg_lower for word in ["product", "price", "buy", "stock", "have", "sell", "catalog"]):
                    try:
                        products = woo.get_products()
                        if products:
                            context += "=== Available Products ===\n"
                            for p in products[:5]:
                                context += woo.format_product_for_chat(p) + "\n---\n"
                    except:
                        pass
                
                # Simple completion without tools
                fallback_messages = [
                    {"role": "system", "content": "You are a professional assistant for Roze BioHealth. Answer customer questions based on the provided context."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_message}"}
                ]
                
                fallback_completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=fallback_messages,
                    temperature=0.7,
                    max_tokens=1024
                )
                
                return BotResponse(text=fallback_completion.choices[0].message.content)
                
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return BotResponse(text="I apologize, but I'm experiencing technical difficulties at the moment. Please try rephrasing your question or contact our support team directly.")
        
        # For rate limit errors
        if "rate_limit" in error_str.lower():
            return BotResponse(text="⏱️ Our AI is experiencing high demand right now. Please try again in a moment.")
        
        # Generic professional error
        return BotResponse(text="I apologize, but I'm having trouble processing your request right now. Please try again or contact our support team for immediate assistance.")

def process_message(wa_id: str, user_message: str):
    """
    Orchestrator: 
    1. Send "Thinking" Status
    2. Generate Response (Heavy Lift)
    3. Send Final Answer
    """
    import time
    start_time = time.time()
    
    logger.info(f"Processing message from {wa_id}: {user_message}")
    
    # 1. Immediate Feedback (Professional "Thinking" State)
    # We can be smart about this: simple heuristics to guess intents for the status message
    if any(word in lower_msg for word in ["order", "track", "package", "where", "status"]):
        status_msg = "🔍 Checking live order status, please wait a moment..."
    elif any(word in lower_msg for word in ["price", "cost", "stock", "have", "list", "buy", "product", "item", "catalog"]):
        status_msg = "🛒 Browsing our live catalog for you..."
    elif any(word in lower_msg for word in ["ingredient", "benefit", "how", "what", "can", "use", "company", "info"]):
        status_msg = "📚 Consulting our knowledge base..."
    else:
        status_msg = "🤔 Analyzing your request..."
        
    send_whatsapp_message(wa_id, status_msg)

    # 2. Logic
    bot_response = generate_bot_response(user_message, session_id=wa_id, platform="whatsapp")
    
    # 3. Final Response - Flatten for WhatsApp
    # WhatsApp can't show carousels easily (unless interactive messages, but keeping it simple text for now)
    final_text = bot_response.text
    
    # Append product links if any
    if bot_response.products:
        final_text += "\n\nProducts Mentioned:"
        for p in bot_response.products:
            final_text += f"\n- {p.get('name')} ({p.get('price')} {p.get('currency')})"
            # Add Image Link for WhatsApp Preview
            if p.get("images") and len(p["images"]) > 0:
                final_text += f"\n  📷 {p['images'][0]['src']}"
    
    send_whatsapp_message(wa_id, final_text)
    
    # 4. Analytics
    response_time_ms = int((time.time() - start_time) * 1000)
    # Track conversation in background
    analytics.track_conversation(user_message, bot_response.text, response_time_ms)

@app.post("/webhook")
async def wati_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming WATI webhooks.
    """
    try:
        payload = await request.json()
        logger.info(f"Received Webhook: {payload}")
        
        # WATI payload structure varies, handling common fields
        # Usually it's a list or a dict. Let's assume a dict for now.
        # Check if it's a message
        if "waId" in payload and "text" in payload:
            wa_id = payload["waId"]
            text = payload["text"]
            
            # Run processing in background to return 200 OK quickly
            background_tasks.add_task(process_message, wa_id, text)
            
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        return {"status": "error", "message": str(e)}

# --- Local Test Interface ---

@app.post("/api/test-chat")
async def test_chat(message: TestMessage):
    """
    Endpoint for local testing without WhatsApp.
    """
    import time
    start_time = time.time()
    
    response_data = generate_bot_response(message.message, session_id=message.session_id, platform="web")
    
    # Track analytics
    response_time_ms = int((time.time() - start_time) * 1000)
    # Track only text for simplicity in analytics
    analytics.track_conversation(message.message, response_data.text, response_time_ms)
    
    return response_data

@app.get("/test", response_class=HTMLResponse)
async def test_interface():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Roze AI - Premium Widget Test</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: -apple-system, sans-serif; 
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                height: 100vh;
                margin: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #333;
            }
            .content {
                text-align: center;
                max-width: 600px;
                padding: 40px;
                background: rgba(255,255,255,0.8);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            h1 { margin-bottom: 10px; }
            p { color: #666; margin-bottom: 30px; }
            .btn {
                background: #000;
                color: white;
                padding: 12px 24px;
                border-radius: 30px;
                text-decoration: none;
                font-weight: 500;
                display: inline-block;
            }
        </style>
    </head>
    <body>
        <div class="content">
            <h1>Roze BioHealth AI</h1>
            <p>Premium Commerce Experience. The chat widget should appear in the bottom right corner.</p>
            <div style="font-size: 12px; color: #888; margin-top: 20px;">
                Voice Interaction • Product Cards • Streaming Text
            </div>
        </div>

        <!-- Load the Widget -->
        <script src="/widget/chat-widget.js"></script>
    </body>
    </html>
    """

# --- ADMIN PANEL API ROUTES ---

@app.get("/widget/chat-widget.js")
async def serve_widget_js():
    """Serve the chat widget JavaScript."""
    import os
    from fastapi.responses import FileResponse
    widget_js_path = os.path.join(os.path.dirname(__file__), "widget", "chat-widget.js")
    return FileResponse(widget_js_path, media_type="application/javascript")

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    """Serve the admin dashboard."""
    import os
    admin_html_path = os.path.join(os.path.dirname(__file__), "admin", "dashboard.html")
    with open(admin_html_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/admin/settings")
async def get_settings():
    """Get all current settings."""
    return settings_manager.get_all_settings()

@app.post("/admin/settings")
async def update_settings(settings: Dict[str, Any]):
    """Update settings."""
    try:
        settings_manager.update_settings(settings)
        return {"status": "success", "message": "Settings updated successfully"}
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/admin/settings/reset")
async def reset_settings():
    """Reset settings to defaults."""
    try:
        settings_manager.reset_to_defaults()
        return {"status": "success", "message": "Settings reset to defaults"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/analytics/stats")
async def get_analytics_stats():
    """Get analytics dashboard statistics."""
    return analytics.get_dashboard_stats()

@app.post("/api/analytics/track")
async def track_analytics(data: Dict[str, Any]):
    """Track a conversation for analytics."""
    analytics.track_conversation(
        data.get("user_message", ""),
        data.get("bot_response", ""),
        data.get("response_time_ms", 0)
    )
    return {"status": "tracked"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
