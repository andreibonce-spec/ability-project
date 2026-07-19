import anthropic
import os
from dotenv import load_dotenv

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

strategii = """
1. Timer vizual pentru tranziții: Folosiți un cronometru vizual (clepsidră sau aplicație) 
   care arată copilului cât timp mai e până la schimbarea activității. 
   Potrivit pentru: 5-9 ani, tranziții, reglare emoțională.

2. Poveste socială pentru tranziții: Creați o poveste scurtă cu imagini care descrie 
   ce se va întâmpla: "Mai întâi facem X, apoi facem Y, la final facem Z." 
   Potrivit pentru: 5-8 ani, tranziții, comunicare.

3. Obiect de confort: Permiteți copilului să țină un obiect mic (jucărie senzorială) 
   în timpul tranzițiilor pentru a reduce anxietatea.
   Potrivit pentru: 5-10 ani, senzorial, reglare emoțională.
"""

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=f"""Ești ABILITY, un asistent educațional pentru profesori care lucrează cu elevi cu CES.
Răspunde DOAR pe baza strategiilor de mai jos. Nu inventa informații noi.
Fii practic, clar, empatic, fără jargon.

STRATEGII DISPONIBILE:
{strategii}""",
    messages=[
        {"role": "user", "content": "Am un elev de 7 ani care face crize la tranzitii intre activitati. Ce pot face?"}
    ]
)

print(message.content[0].text)
