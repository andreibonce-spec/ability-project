from flask import Flask, request, jsonify, render_template
import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Încărcăm strategiile (am adăugat o protecție în caz că fișierul lipsește)
try:
    with open("strategies.json", "r", encoding="utf-8") as f:
        strategii = json.load(f)
except FileNotFoundError:
    strategii = [] 
    print("Atenție: Fișierul strategies.json nu a fost găsit!")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def cauta_strategii(varsta, categorie, context):
    rezultate = []
    for s in strategii:
        potrivire = True
        # Am folosit .get() pentru a evita erorile dacă o cheie lipsește din JSON
        if varsta and varsta not in s.get("varsta", ""):
            potrivire = False
        if categorie and s.get("categorie", "") != categorie:
            potrivire = False
        if context and s.get("context", "") != context:
            potrivire = False
        if potrivire:
            rezultate.append(s)
            
    if len(rezultate) == 0:
        rezultate = strategii
    return rezultate

# ---- RUTA NOUĂ PENTRU INTERFAȚĂ ----
@app.route("/")
def home():
    return render_template("index.html")

# ---- RUTA TA EXISTENTĂ DE API ----
@app.route("/api/intrebare", methods=["POST"])
def raspunde():
    date = request.get_json()
    intrebare = date.get("intrebare", "")
    varsta = date.get("varsta", "")
    categorie = date.get("categorie", "")
    context_elev = date.get("context", "")

    strategii_gasite = cauta_strategii(varsta, categorie, context_elev)
    
    text_strategii = ""
    for s in strategii_gasite:
        text_strategii += f"""
Titlu: {s.get('titlu', '')}
Categorie: {s.get('categorie', '')}
Vârsta: {s.get('varsta', '')}
Descriere: {s.get('descriere', '')}
Pași: {s.get('pasi', '')}
Note: {s.get('note', '')}
---
"""

    try:
        # ATENȚIE: Am actualizat numele modelului la cel real și funcțional
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system=f"""Ești ABILITY, un asistent educațional pentru profesori care lucrează cu elevi cu cerințe educaționale speciale (CES).

Reguli:
- Răspunde DOAR pe baza strategiilor de mai jos
- Nu inventa informații noi
- Fii practic, clar, empatic
- Fără jargon academic
- Fără etichete de diagnostic
- Răspunde în limba română

STRATEGII DISPONIBILE:
{text_strategii}""",
            messages=[
                {"role": "user", "content": intrebare}
            ]
        )
        raspuns = message.content[0].text
        return jsonify({"raspuns": raspuns})
    
    except Exception as e:
        # Protecție: dacă pică API-ul, aplicația nu crapă, ci afișează eroarea în chat
        return jsonify({"raspuns": f"Eroare de la serverul AI: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
