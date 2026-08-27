import sqlite3
import json

def update_db():
    conn = sqlite3.connect('config.db')
    c = conn.cursor()
    new_welcome = "Hello! I am from Roze BioHealth. How can I help you today?"
    c.execute("UPDATE settings SET value = ? WHERE key = 'welcome_message'", (json.dumps(new_welcome),))
    conn.commit()
    conn.close()
    print("Welcome message updated in config.db")

if __name__ == "__main__":
    update_db()
