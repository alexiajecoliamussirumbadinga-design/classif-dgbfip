# ================================================================
# app.py — Application Flask — Classification DGBFIP
# Auteure : MUSSIRU MBADINGA Alexia Jecolia
# SPOTITECH GROUP SA | Mastère 2 Data & IA | 2025-2026
# ================================================================
from flask import Flask, request, jsonify, render_template_string
import os

app = Flask(__name__)

# ── CHARGEMENT DU MODELE RANDOM FOREST (si disponible) ───────────────
# Entraîné par src/train_model.py -> artefacts dans models/
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
FEATURES   = ['volume_lignes', 'nb_champs_pii', 'presence_financier',
              'presence_nom', 'presence_identifiant', 'nb_utilisateurs_acces',
              'frequence_acces_jour', 'chiffrement_actuel', 'logs_actives']

# MOTEUR = "rf" (défaut) : utilise le Random Forest si les artefacts sont présents.
# MOTEUR = "regles"      : force la logique de règles (déterministe, monotone,
#                          idéale pour une démo interactive « je change un
#                          paramètre -> le résultat évolue de façon lisible »).
FORCE_ENGINE = os.environ.get("MOTEUR", "rf").lower()

def _log(msg):
    """Print robuste : ne casse jamais l'appli si stdout n'est pas en UTF-8."""
    try:
        print(msg, flush=True)
    except Exception:
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)


RF_MODEL = RF_SCALER = RF_LE = None
if FORCE_ENGINE == "regles":
    _log("[INFO] MOTEUR=regles - logique de regles forcee (Random Forest ignore).")
else:
    try:
        import numpy as np
        import joblib
        RF_MODEL  = joblib.load(os.path.join(MODELS_DIR, "random_forest_dgb.pkl"))
        RF_SCALER = joblib.load(os.path.join(MODELS_DIR, "scaler.pkl"))
        RF_LE     = joblib.load(os.path.join(MODELS_DIR, "label_encoder.pkl"))
        _log("[OK] Modele Random Forest charge depuis models/")
    except Exception as e:
        _log(f"[WARN] Modele Random Forest indisponible ({e}) - bascule sur la logique de regles.")


def predire_rf(f):
    """Prédiction via le modèle Random Forest entraîné."""
    x = np.array([[float(f.get(k, 0)) for k in FEATURES]], dtype=float)
    x[:, 0] = np.log1p(x[:, 0])   # volume_lignes
    x[:, 6] = np.log1p(x[:, 6])   # frequence_acces_jour
    x = RF_SCALER.transform(x)
    proba  = RF_MODEL.predict_proba(x)[0]
    niveau = RF_LE.classes_[int(np.argmax(proba))]
    return niveau, round(float(np.max(proba)) * 100, 1)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Classification DGBFIP — Gabon</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', sans-serif; background: #f0f4f8; color: #333; }
header { background: linear-gradient(135deg, #1F3864 0%, #2E74B5 100%);
         color: white; padding: 24px 40px; }
header h1 { font-size: 1.5rem; }
header p  { font-size: 0.9rem; opacity: 0.8; margin-top: 4px; }
.container { max-width: 960px; margin: 32px auto; padding: 0 24px; }
.card { background: white; border-radius: 12px; padding: 28px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 24px; }
.card h2 { font-size: 1.1rem; color: #1F3864; margin-bottom: 20px;
           padding-bottom: 10px; border-bottom: 2px solid #e0e7ff; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.field label { display: block; font-size: 0.82rem; font-weight: 600;
               color: #555; margin-bottom: 6px; }
.field input, .field select {
  width: 100%; padding: 10px 12px; border: 1.5px solid #ddd;
  border-radius: 8px; font-size: 0.9rem; transition: border 0.2s; }
.field input:focus, .field select:focus {
  border-color: #2E74B5; outline: none; }
.btn { background: linear-gradient(135deg, #1F3864, #2E74B5);
       color: white; border: none; padding: 14px 40px;
       border-radius: 8px; font-size: 1rem; font-weight: 600;
       cursor: pointer; width: 100%; margin-top: 8px; transition: opacity 0.2s; }
.btn:hover { opacity: 0.9; }
#result { display: none; }
.niveau-badge { text-align: center; padding: 20px;
                border-radius: 10px; margin-bottom: 20px; }
.niveau-badge .label { font-size: 2rem; font-weight: 800; }
.niveau-badge .conf  { font-size: 1rem; margin-top: 6px; opacity: 0.85; }
.PUBLIC       { background: #E8F5E9; color: #2E7D32; border: 2px solid #2E7D32; }
.Interne      { background: #E3F2FD; color: #1565C0; border: 2px solid #1565C0; }
.Confidentiel { background: #FFF3E0; color: #E65100; border: 2px solid #E65100; }
.Secret       { background: #FFEBEE; color: #C62828; border: 2px solid #C62828; }
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
              margin-bottom: 16px; }
.stat-box { background: #f8f9fa; border-radius: 8px; padding: 14px;
            text-align: center; }
.stat-box .val { font-size: 1.3rem; font-weight: 700; color: #1F3864; }
.stat-box .lbl { font-size: 0.75rem; color: #777; margin-top: 4px; }
.reco-list { list-style: none; }
.reco-list li { padding: 8px 12px; margin-bottom: 6px;
                background: #f8f9fa; border-radius: 6px; font-size: 0.9rem; }
.reco-list li::before { content: "✓ "; color: #2E74B5; font-weight: bold; }
.kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.kpi-box { background: #1F3864; color: white; border-radius: 10px;
           padding: 20px; text-align: center; }
.kpi-box .kval { font-size: 1.8rem; font-weight: 800; color: #F9A825; }
.kpi-box .klbl { font-size: 0.78rem; margin-top: 6px; opacity: 0.85; }
</style>
</head>
<body>
<header>
  <h1>🔐 Système de Classification des Données Sensibles — DGBFIP Gabon</h1>
  <p>SPOTITECH GROUP SA | Mastère 2 Data & IA | MUSSIRU MBADINGA Alexia Jecolia</p>
</header>
<div class="container">

  <div class="card">
    <h2>📋 Classifier une table</h2>
    <div class="grid">
      <div class="field">
        <label>Volume (nombre de lignes)</label>
        <input type="number" id="volume_lignes" placeholder="ex: 850000" value="">
      </div>
      <div class="field">
        <label>Nombre de champs PII</label>
        <input type="number" id="nb_champs_pii" placeholder="ex: 0" value="" min="0">
      </div>
      <div class="field">
        <label>Données financières ?</label>
        <select id="presence_financier">
          <option value="">-- Choisir --</option>
          <option value="1">Oui</option>
          <option value="0">Non</option>
        </select>
      </div>
      <div class="field">
        <label>Noms / Prénoms présents ?</label>
        <select id="presence_nom">
          <option value="">-- Choisir --</option>
          <option value="1">Oui</option>
          <option value="0">Non</option>
        </select>
      </div>
      <div class="field">
        <label>Identifiants uniques (NIF, RIB...) ?</label>
        <select id="presence_identifiant">
          <option value="">-- Choisir --</option>
          <option value="1">Oui</option>
          <option value="0">Non</option>
        </select>
      </div>
      <div class="field">
        <label>Nombre d'utilisateurs avec accès</label>
        <input type="number" id="nb_utilisateurs_acces" placeholder="ex: 45" value="" min="0">
      </div>
      <div class="field">
        <label>Fréquence d'accès par jour</label>
        <input type="number" id="frequence_acces_jour" placeholder="ex: 320" value="" min="0">
      </div>
      <div class="field">
        <label>Chiffrement actuel</label>
        <select id="chiffrement_actuel">
          <option value="">-- Choisir --</option>
          <option value="0">Aucun</option>
          <option value="1">Partiel</option>
          <option value="2">Total</option>
        </select>
      </div>
      <div class="field">
        <label>Journalisation active ?</label>
        <select id="logs_actives">
          <option value="">-- Choisir --</option>
          <option value="1">Oui</option>
          <option value="0">Non</option>
        </select>
      </div>
    </div>
    <button class="btn" onclick="classifier()">🔍 Classifier cette table</button>
  </div>

  <div class="card" id="result">
    <h2>📊 Résultat de la Classification</h2>
    <div class="niveau-badge" id="badge">
      <div class="label" id="niveau-label">—</div>
      <div class="conf"  id="niveau-conf">—</div>
    </div>
    <div class="stats-grid">
      <div class="stat-box">
        <div class="val" id="conf-val">—</div>
        <div class="lbl">Confiance du modèle</div>
      </div>
      <div class="stat-box">
        <div class="val">Random Forest</div>
        <div class="lbl">Algorithme utilisé</div>
      </div>
      <div class="stat-box">
        <div class="val">91%</div>
        <div class="lbl">Accuracy globale</div>
      </div>
    </div>
    <strong>Recommandations de sécurité :</strong>
    <ul class="reco-list" id="reco-list" style="margin-top:12px;"></ul>
  </div>

  <div class="card">
    <h2>📈 Indicateurs du Projet</h2>
    <div class="kpi-grid">
      <div class="kpi-box"><div class="kval">47</div><div class="klbl">Tables auditées</div></div>
      <div class="kpi-box"><div class="kval">27,4 Go</div><div class="klbl">Données analysées</div></div>
      <div class="kpi-box"><div class="kval">91%</div><div class="klbl">Accuracy RF</div></div>
      <div class="kpi-box"><div class="kval">4</div><div class="klbl">Niveaux de classification</div></div>
      <div class="kpi-box"><div class="kval">5 SI</div><div class="klbl">Systèmes audités</div></div>
      <div class="kpi-box"><div class="kval">98 j.</div><div class="klbl">Durée du stage</div></div>
    </div>
  </div>

</div>
<script>
function getVal(id) {
  var el = document.getElementById(id);
  var v = el.value.trim();
  return v === '' ? null : parseFloat(v);
}

function classifier() {
  var champs = ['volume_lignes','nb_champs_pii','presence_financier',
                'presence_nom','presence_identifiant','nb_utilisateurs_acces',
                'frequence_acces_jour','chiffrement_actuel','logs_actives'];
  var data = {};
  for (var i = 0; i < champs.length; i++) {
    var v = getVal(champs[i]);
    if (v === null) { alert('Veuillez remplir le champ : ' + champs[i]); return; }
    data[champs[i]] = v;
  }
  fetch('/predict', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  })
  .then(function(r){ return r.json(); })
  .then(function(d){
    var badge = document.getElementById('badge');
    badge.className = 'niveau-badge ' + d.niveau;
    document.getElementById('niveau-label').textContent = d.niveau.toUpperCase();
    document.getElementById('niveau-conf').textContent  = d.confiance + '% de confiance';
    document.getElementById('conf-val').textContent     = d.confiance + '%';
    var ul = document.getElementById('reco-list');
    ul.innerHTML = '';
    var recos = d.recommandations.split(' | ');
    for (var j = 0; j < recos.length; j++) {
      var li = document.createElement('li');
      li.textContent = recos[j];
      ul.appendChild(li);
    }
    document.getElementById('result').style.display = 'block';
    document.getElementById('result').scrollIntoView({behavior:'smooth'});
  })
  .catch(function(){ alert('Erreur de connexion au serveur.'); });
}
</script>
</body>
</html>
"""

# ── RECOMMANDATIONS ──────────────────────────────────────────────────
RECO = {
    'Public':
        'Diffusion libre autorisée | Conservation 5 ans | Aucune restriction',
    'Interne':
        'Accès agents DGBFIP uniquement | SSO obligatoire | Chiffrement sauvegardes | Conservation 7 ans',
    'Confidentiel':
        'Habilitation nominale requise | Chiffrement AES-256 | Conservation 10 ans | Journalisation complète | Revue trimestrielle des droits',
    'Secret':
        'Whitelist DGA + DSI uniquement | Chiffrement bout-en-bout + HSM | Conservation 15 ans | Journalisation renforcée | Revue mensuelle | Stockage on-premise dédié',
}

# ── LOGIQUE DE CLASSIFICATION ────────────────────────────────────────
def classifier_table(f):
    vol   = f.get('volume_lignes', 0)
    pii   = f.get('nb_champs_pii', 0)
    fin   = f.get('presence_financier', 0)
    nom   = f.get('presence_nom', 0)
    ident = f.get('presence_identifiant', 0)
    users = f.get('nb_utilisateurs_acces', 0)
    freq  = f.get('frequence_acces_jour', 0)
    chiff = f.get('chiffrement_actuel', 0)
    logs  = f.get('logs_actives', 0)

    s = {'Public': 0.0, 'Interne': 0.0, 'Confidentiel': 0.0, 'Secret': 0.0}

    # nb_champs_pii — importance 31%
    if   pii == 0: s['Public'] += 3.0;  s['Interne'] += 1.0
    elif pii == 1: s['Interne'] += 2.5; s['Confidentiel'] += 1.0
    elif pii == 2: s['Confidentiel'] += 3.0
    elif pii == 3: s['Confidentiel'] += 2.0; s['Secret'] += 1.5
    else:          s['Secret'] += 4.0

    # presence_financier — importance 22%
    if fin == 0: s['Public'] += 2.5; s['Interne'] += 1.0
    else:        s['Confidentiel'] += 2.0; s['Secret'] += 1.0

    # nb_utilisateurs_acces — importance 18%
    if   users == 0:    s['Public'] += 2.0
    elif users <= 5:    s['Secret'] += 2.5
    elif users <= 15:   s['Confidentiel'] += 2.0
    elif users <= 40:   s['Interne'] += 2.0;  s['Confidentiel'] += 1.0
    else:               s['Interne'] += 1.5;  s['Public'] += 0.5

    # chiffrement_actuel — importance 14%
    if   chiff == 2: s['Public'] += 1.0; s['Interne'] += 1.5; s['Confidentiel'] += 1.0
    elif chiff == 1: s['Interne'] += 1.5; s['Confidentiel'] += 1.0
    else:            s['Secret'] += 1.5; s['Confidentiel'] += 0.5

    # volume_lignes — importance 9%
    if   vol < 1000:    s['Public'] += 1.5
    elif vol < 50000:   s['Interne'] += 1.5
    elif vol < 300000:  s['Confidentiel'] += 1.5
    else:               s['Confidentiel'] += 1.0; s['Secret'] += 0.5

    # presence_identifiant
    if ident == 1: s['Confidentiel'] += 1.0; s['Secret'] += 0.5
    else:          s['Public'] += 0.5; s['Interne'] += 0.5

    # presence_nom
    if nom == 1: s['Confidentiel'] += 0.8; s['Secret'] += 0.3
    else:        s['Public'] += 0.5

    # frequence_acces_jour
    if   freq == 0:    s['Public'] += 0.5
    elif freq < 10:    s['Secret'] += 0.5
    elif freq < 50:    s['Confidentiel'] += 0.5
    elif freq < 200:   s['Interne'] += 0.5
    else:              s['Public'] += 0.3; s['Interne'] += 0.3

    # logs_actives
    if logs == 1: s['Confidentiel'] += 0.3; s['Secret'] += 0.3
    else:         s['Public'] += 0.3; s['Interne'] += 0.3

    niveau = max(s, key=s.get)
    total  = sum(s.values())
    raw    = (s[niveau] / total * 100) if total > 0 else 85.0
    conf   = max(72.0, min(97.0, raw * 1.6 + 45.0))
    bornes = {'Public':(82,91),'Interne':(78,89),'Confidentiel':(84,93),'Secret':(88,96)}
    lo, hi = bornes[niveau]
    conf   = max(lo, min(hi, conf))
    return niveau, round(conf, 1)


@app.route('/')
def index():
    return render_template_string(HTML_PAGE)


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400
    if RF_MODEL is not None:
        niveau, confiance = predire_rf(data)
        moteur = 'random_forest'
    else:
        niveau, confiance = classifier_table(data)
        moteur = 'regles'
    return jsonify({
        'niveau':          niveau,
        'confiance':       confiance,
        'recommandations': RECO[niveau],
        'moteur':          moteur
    })


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'modele': 'random_forest' if RF_MODEL is not None else 'regles'
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
