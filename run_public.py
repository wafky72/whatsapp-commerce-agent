"""
Expose local backend to the internet for staging/production testing.
Uses ngrok to create a public URL.
"""
from pyngrok import ngrok
import os
import time
import threading
import subprocess

# Get ngrok auth token (optional but recommended for stability)
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN", None)

if NGROK_AUTH_TOKEN:
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)

# Get ngrok static domain if provided
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN", None)

# Start ngrok tunnel
print("🚀 Starting ngrok tunnel...")
try:
    if NGROK_DOMAIN:
        public_url = ngrok.connect(8002, domain=NGROK_DOMAIN, bind_tls=True)
    else:
        public_url = ngrok.connect(8002, bind_tls=True)
except Exception as e:
    print(f"❌ Failed to start ngrok: {e}")
    print("💡 Tip: If you are using a static domain, make sure it's valid and your account supports it.")
    exit(1)

print(f"\n✅ Your AI Agent is now PUBLIC at:")
print(f"   📍 {public_url}\n")
print(f"📝 COPY THIS URL and paste it in:")
print(f"   WordPress > AI Chat > API Endpoint\n")
print(f"🌐 Test it at: {public_url}/test")
print(f"⚙️  Admin Panel: {public_url}/admin\n")
print("⏸️  Keep this window open. Press CTRL+C to stop\n")
print("-" * 60)

# Start uvicorn in a separate thread so we can keep the script running
def start_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run(["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"])

server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n🛑 Shutting down...")
    ngrok.disconnect(public_url)
    print("✅ Tunnel closed. Goodbye!")
