from flask import Flask, request, jsonify
import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

with open("strategies.json", "r", encoding="utf-8") as f:
    strategii = json.load(f)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def cauta_strategii(varsta, categorie, context):
    rezultate = []
    for s in strategii:
        potrivire = True
        if varsta and varsta not in s["varsta"]:
            potrivire = False
        if categorie and s["categorie"] != categorie:
            potrivire = False
        if context and s["context"] != context:
            potrivire = False
        if potrivire:
            rezultate.append(s)
    if len(rezultate) == 0:
        rezultate = strategii
    return rezultate

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
Titlu: {s['titlu']}
Categorie: {s['categorie']}
Varsta: {s['varsta']}
Descriere: {s['descriere']}
Pasi: {s['pasi']}
Note: {s['note']}
---
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=f"""Esti ABILITY, un asistent educational pentru profesori care lucreaza cu elevi cu cerinte educationale speciale (CES).

Reguli:
- Raspunde DOAR pe baza strategiilor de mai jos
- Nu inventa informatii noi
- Fii practic, clar, empatic
- Fara jargon academic
- Fara etichete de diagnostic
- Raspunde in limba romana

STRATEGII DISPONIBILE:
{text_strategii}""",
        messages=[
            {"role": "user", "content": intrebare}
        ]
    )

    raspuns = message.content[0].text
    return jsonify({"raspuns": raspuns})

if __name__ == "__main__":
    app.run(debug=True, port=5000)