from flask import Flask, request, jsonify, render_template
import anthropic
import json
import os
from dotenv import load_dotenv


#  COMENZI RULARE SITE DEBUG
#  source venv/bin/activate
#  python3 app.py



load_dotenv()

app = Flask(__name__)

# ==========================================
#      ÎNCĂRCARE STRATEGII (Pentru AI)
# ==========================================

try:
    with open("strategies.json", "r", encoding="utf-8") as f:
        strategii = json.load(f)
except FileNotFoundError:
    strategii = [] 
    print("Atenție: Fișierul strategies.json nu a fost găsit!")

# ==========================================
#   CONFIGURARE FUNCȚII BAZĂ DE DATE (ELEVI)
# ==========================================

FISIER_DB = "baza_date.json"

import datetime # Adaugă acest import sus de tot, sub 'import os'

# --- 1. ÎNLOCUIEȘTE FUNCȚIA citeste_db CU ACEASTA ---
def citeste_db():
    try:
        with open(FISIER_DB, "r", encoding="utf-8") as f:
            db = json.load(f)
            # Upgradăm baza de date automat pentru noul sistem
            if "email" not in db.get("utilizator", {}):
                db["utilizator"]["email"] = "profesor.abilitati@scoala.ro"
            if "colaborare" not in db:
                db["colaborare"] = [
                    {"autor": "Maria Ionescu", "ora": "10:30", "mesaj": "Bună dimineața colegi! Are cineva materiale vizuale pentru fracții adaptate pentru discalculie?"},
                    {"autor": "Prof. Mihai B.", "ora": "10:45", "mesaj": "Salut! Da, folosesc eu niște planșe cu pizza tăiată în felii. Le poți face foarte ușor din carton colorat."}
                ]
            return db
    except FileNotFoundError:
        return {
            "utilizator": {"nume": "Profesoară", "email": "profesor@scoala.ro"}, 
            "elevi": [], 
            "colaborare": []
        }

def salveaza_db(date):
    with open(FISIER_DB, "w", encoding="utf-8") as f:
        json.dump(date, f, ensure_ascii=False, indent=4)


# ==========================================
#     CONFIGURARE ASISTENT AI (Claude)
# ==========================================

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def cauta_strategii(varsta, categorie, context):
    rezultate = []
    for s in strategii:
        potrivire = True
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


# ==========================================
#    RUTE PENTRU AFIȘARE PAGINI WEB (HTML)
# ==========================================

# Pagina Principală (Dashboard)
@app.route("/")
def home():
    baza_date = citeste_db() # citeste elevii din JSON
    # trimite baza de date către pagina HTML ca să o poată afișa
    return render_template("dashboard.html", db=baza_date) 

# Pagina pentru Asistentul AI
@app.route("/asistent")
def asistent():
    return render_template("chat.html")


# ======================================================
#   RUTE PENTRU FUNCȚIONALITĂȚI API
# ======================================================

# Funcția care adaugă un elev nou când apeși butonul "Salvează"
@app.route("/api/adauga_elev", methods=["POST"])
def adauga_elev():
    date_noi = request.get_json()
    db = citeste_db()
    
    elev_nou = {
        "nume": date_noi.get("nume"),
        "diagnostic": date_noi.get("diagnostic"),
        "varsta": int(date_noi.get("varsta", 0)),
        "progres": 0, # Progresul începe mereu de la 0%
        "activitate_recenta": "Adăugat recent în sistem",
        "avatar_id": len(db["elevi"]) + 1 
    }
    
    db["elevi"].append(elev_nou)
    salveaza_db(db)
    
    return jsonify({"succes": True})

#=============================
# RUTA MESAJE INTRE PROFESORI
#=============================

@app.route("/colaborare")
def colaborare():
    baza_date = citeste_db()
    return render_template("colaborare.html", db=baza_date)

@app.route("/api/trimite_mesaj", methods=["POST"])
def trimite_mesaj():
    date = request.get_json()
    db = citeste_db()
    
    mesaj_nou = {
        "autor": db["utilizator"]["nume"], # Numele tău din cont
        "ora": datetime.datetime.now().strftime("%H:%M"), # Ora actuală
        "mesaj": date.get("mesaj", "")
    }
    
    db["colaborare"].append(mesaj_nou)
    salveaza_db(db)
    return jsonify({"succes": True})

# Funcția care vorbește cu Claude
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
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=f"""Ești ABILITY, un asistent educațional pentru profesori care lucrează cu elevi cu cerințe educaționale speciale (CES).

Reguli:
 - Răspunde DOAR pe baza strategiilor de mai jos
- Nu inventa informații noi
- Fii practic, clar, empatic
- Fără jargon academic complicat
- Fără etichete de diagnostic jignitoare sau ofensatoare
- Răspunde în limba română si in alta limba doar daca ti se specifica clar 

STRATEGII DISPONIBILE:
{text_strategii}""",
            messages=[
                {"role": "user", "content": intrebare}
            ]
        )
        raspuns = message.content[0].text
        return jsonify({"raspuns": raspuns})
    
    except Exception as e:
        return jsonify({"raspuns": f"Eroare de la serverul AI: {str(e)}"}), 500


@app.route("/adapteaza")
def adapteaza():
    return render_template("adapteaza.html")

@app.route("/api/adapteaza", methods = ["POST"])
def adapteaza_activitate():
    date = request.get_json()
    activitate = date.get("activitate", "")
    nevoie = date.get("nevoie", "")
    varsta = date.get("varsta", "")

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="""Esti ABILITY, un asistent educational pentru profesori care lucreaza cu elevi cu cerinte educationale speciale (CES).

Profesorul iti da o activitate si nevoia unui elev. Tu trebuie sa adaptezi activitatea pentru acel elev.

Reguli:
- Pastreaza obiectivul original al activitatii
- Ofera 2-3 variante de adaptare
- Fii concret si practic
- Explica DE CE fiecare adaptare ajuta
- Fara jargon academic
- Raspunde in limba romana""",
            messages=[
                {"role": "user", "content": f"Activitatea: {activitate}\nNevoia elevului: {nevoie}\nVarsta elevului: {varsta}"}
            ]
        )
        raspuns = message.content[0].text
        return jsonify({"raspuns": raspuns})
    except Exception as e:
        return jsonify({"raspuns": f"Eroare: {str(e)}"}), 500




# ==========================================
#             PORNIREA APLICAȚIEI
# ==========================================
if __name__ == "__main__":
    app.run(debug=True, port=5000, host = "0.0.0.0")
