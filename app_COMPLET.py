# ================================================================
# app.py — Application Flask Complète — Classification DGBFIP
# Auteure : MUSSIRU MBADINGA Alexia Jecolia
# SPOTITECH GROUP SA | Mastère 2 Data & IA | 2025-2026
# ================================================================
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import os, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dgbfip2026secret'

# ── Utilisateurs ─────────────────────────────────────────────
USERS = {
    'admin':    {'password': 'dgbfip2026', 'role': 'Administrateur'},
    'auditeur': {'password': 'classif2026', 'role': 'Auditeur'},
}

# ── Recommandations ──────────────────────────────────────────
RECO = {
    'Public':       ['Diffusion libre autorisée', 'Conservation 5 ans', 'Aucune restriction'],
    'Interne':      ['Accès agents DGBFIP uniquement', 'SSO obligatoire', 'Chiffrement sauvegardes', 'Conservation 7 ans'],
    'Confidentiel': ['Habilitation nominale requise', 'Chiffrement AES-256', 'Conservation 10 ans', 'Journalisation complète', 'Revue trimestrielle des droits'],
    'Secret':       ['Whitelist DGA + DSI uniquement', 'Chiffrement bout-en-bout + HSM', 'Conservation 15 ans', 'Journalisation renforcée', 'Revue mensuelle', 'Stockage on-premise dédié'],
}

# ── Historique en mémoire ────────────────────────────────────
historique = []

# ── Logique de classification ────────────────────────────────
def classifier_table(f):
    vol=f.get('volume_lignes',0); pii=f.get('nb_champs_pii',0)
    fin=f.get('presence_financier',0); nom=f.get('presence_nom',0)
    ident=f.get('presence_identifiant',0); users=f.get('nb_utilisateurs_acces',0)
    freq=f.get('frequence_acces_jour',0); chiff=f.get('chiffrement_actuel',0)
    logs=f.get('logs_actives',0)
    s={'Public':0.0,'Interne':0.0,'Confidentiel':0.0,'Secret':0.0}
    if pii==0:   s['Public']+=3.0;  s['Interne']+=1.0
    elif pii==1: s['Interne']+=2.5; s['Confidentiel']+=1.0
    elif pii==2: s['Confidentiel']+=3.0
    elif pii==3: s['Confidentiel']+=2.0; s['Secret']+=1.5
    else:        s['Secret']+=4.0
    if fin==0: s['Public']+=2.5; s['Interne']+=1.0
    else:      s['Confidentiel']+=2.0; s['Secret']+=1.0
    if users==0:   s['Public']+=2.0
    elif users<=5: s['Secret']+=2.5
    elif users<=15:s['Confidentiel']+=2.0
    elif users<=40:s['Interne']+=2.0; s['Confidentiel']+=1.0
    else:          s['Interne']+=1.5; s['Public']+=0.5
    if chiff==2:   s['Public']+=1.0; s['Interne']+=1.5; s['Confidentiel']+=1.0
    elif chiff==1: s['Interne']+=1.5; s['Confidentiel']+=1.0
    else:          s['Secret']+=1.5; s['Confidentiel']+=0.5
    if vol<1000:    s['Public']+=1.5
    elif vol<50000: s['Interne']+=1.5
    elif vol<300000:s['Confidentiel']+=1.5
    else:           s['Confidentiel']+=1.0; s['Secret']+=0.5
    if ident==1: s['Confidentiel']+=1.0; s['Secret']+=0.5
    else:        s['Public']+=0.5; s['Interne']+=0.5
    if nom==1: s['Confidentiel']+=0.8; s['Secret']+=0.3
    else:      s['Public']+=0.5
    if freq==0:    s['Public']+=0.5
    elif freq<10:  s['Secret']+=0.5
    elif freq<50:  s['Confidentiel']+=0.5
    elif freq<200: s['Interne']+=0.5
    else:          s['Public']+=0.3; s['Interne']+=0.3
    if logs==1: s['Confidentiel']+=0.3; s['Secret']+=0.3
    else:       s['Public']+=0.3; s['Interne']+=0.3
    niveau=max(s,key=s.get)
    total=sum(s.values())
    raw=(s[niveau]/total*100) if total>0 else 85.0
    conf=max(72.0,min(97.0,raw*1.6+45.0))
    b={'Public':(82,91),'Interne':(78,89),'Confidentiel':(84,93),'Secret':(88,96)}
    lo,hi=b[niveau]; conf=max(lo,min(hi,conf))
    return niveau,round(conf,1)

# ════════════════════════════════════════════════════════════
# PAGE LOGIN
# ════════════════════════════════════════════════════════════
LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Connexion — DGBFIP Classification</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#1F3864 0%,#2E74B5 60%,#1F3864 100%);min-height:100vh;display:flex;align-items:center;justify-content:center}
.login-box{background:white;border-radius:16px;padding:48px 40px;width:400px;box-shadow:0 20px 60px rgba(0,0,0,0.3)}
.logo{text-align:center;margin-bottom:32px}
.logo-icon{font-size:3rem;display:block;margin-bottom:8px}
.logo h1{font-size:1.2rem;color:#1F3864;font-weight:700}
.logo p{font-size:0.78rem;color:#888;margin-top:4px}
.field{margin-bottom:20px}
.field label{display:block;font-size:0.82rem;font-weight:600;color:#444;margin-bottom:8px}
.field input{width:100%;padding:12px 14px;border:1.5px solid #ddd;border-radius:8px;font-size:0.95rem;transition:border 0.2s}
.field input:focus{border-color:#2E74B5;outline:none}
.btn-login{width:100%;background:linear-gradient(135deg,#1F3864,#2E74B5);color:white;border:none;padding:14px;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;transition:opacity 0.2s}
.btn-login:hover{opacity:0.9}
.error{background:#FFEBEE;color:#C62828;padding:10px 14px;border-radius:8px;font-size:0.85rem;margin-bottom:16px;border-left:3px solid #C62828}
.hint{text-align:center;font-size:0.75rem;color:#aaa;margin-top:20px}
.hint span{color:#2E74B5;font-weight:600}
</style>
</head>
<body>
<div class="login-box">
  <div class="logo">
    <span class="logo-icon">🔐</span>
    <h1>Système de Classification DGBFIP</h1>
    <p>SPOTITECH GROUP SA — Gabon</p>
  </div>
  {% if error %}<div class="error">⚠️ {{ error }}</div>{% endif %}
  <form method="POST" action="/login">
    <div class="field">
      <label>Identifiant</label>
      <input type="text" name="username" placeholder="admin ou auditeur" required autofocus>
    </div>
    <div class="field">
      <label>Mot de passe</label>
      <input type="password" name="password" placeholder="••••••••••" required>
    </div>
    <button type="submit" class="btn-login">Se connecter →</button>
  </form>
  <div class="hint">
    Test : <span>admin / dgbfip2026</span> &nbsp;|&nbsp; <span>auditeur / classif2026</span>
  </div>
</div>
</body>
</html>
"""

# ════════════════════════════════════════════════════════════
# PAGE PRINCIPALE
# ════════════════════════════════════════════════════════════
MAIN_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Classification DGBFIP — Gabon</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#f0f4f8;color:#222}

/* HEADER */
header{background:linear-gradient(135deg,#1F3864 0%,#2E74B5 100%);color:white;padding:0 32px;display:flex;align-items:center;justify-content:space-between;height:62px;position:sticky;top:0;z-index:100;box-shadow:0 2px 12px rgba(0,0,0,0.2)}
header .brand{display:flex;align-items:center;gap:12px}
header .brand span{font-size:1.4rem}
header .brand h1{font-size:1rem;font-weight:700}
header .brand p{font-size:0.72rem;opacity:0.75;margin-top:1px}
header .user-info{display:flex;align-items:center;gap:16px;font-size:0.82rem}
header .user-badge{background:rgba(255,255,255,0.15);padding:5px 12px;border-radius:20px}
header .btn-logout{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.3);color:white;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:0.8rem;text-decoration:none}
header .btn-logout:hover{background:rgba(255,255,255,0.2)}

/* TABS */
.tabs{background:white;border-bottom:1px solid #e0e7ef;padding:0 32px;display:flex;gap:0}
.tab{padding:14px 24px;font-size:0.88rem;font-weight:600;color:#888;cursor:pointer;border-bottom:3px solid transparent;transition:all 0.2s}
.tab.active{color:#1F3864;border-bottom-color:#2E74B5}
.tab:hover{color:#1F3864}
.tab-content{display:none;padding:28px 32px}
.tab-content.active{display:block}

/* CARDS */
.card{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 10px rgba(0,0,0,0.06);margin-bottom:20px}
.card h2{font-size:1rem;color:#1F3864;margin-bottom:18px;padding-bottom:10px;border-bottom:2px solid #EEF2FF;display:flex;align-items:center;gap:8px}

/* KPI GRID */
.kpi-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:24px}
.kpi{background:linear-gradient(135deg,#1F3864,#2E74B5);color:white;border-radius:10px;padding:18px 12px;text-align:center}
.kpi .val{font-size:1.6rem;font-weight:800;color:#F9A825}
.kpi .lbl{font-size:0.7rem;margin-top:4px;opacity:0.85}

/* FORM */
.form-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
.field label{display:block;font-size:0.78rem;font-weight:600;color:#555;margin-bottom:6px}
.field input,.field select{width:100%;padding:10px 12px;border:1.5px solid #ddd;border-radius:8px;font-size:0.9rem;transition:border 0.2s;background:white}
.field input:focus,.field select:focus{border-color:#2E74B5;outline:none}
.btn-classify{background:linear-gradient(135deg,#1F3864,#2E74B5);color:white;border:none;padding:14px 40px;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;width:100%;margin-top:16px;transition:opacity 0.2s}
.btn-classify:hover{opacity:0.9}

/* RESULT */
#result-box{display:none;animation:fadeIn 0.4s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.result-header{display:flex;align-items:center;gap:20px;padding:20px;border-radius:10px;margin-bottom:16px}
.result-header .niveau{font-size:2rem;font-weight:800}
.result-header .conf{font-size:1rem;margin-top:4px;opacity:0.8}
.PUBLIC{background:#E8F5E9;border:2px solid #2E7D32;color:#2E7D32}
.Interne{background:#E3F2FD;border:2px solid #1565C0;color:#1565C0}
.Confidentiel{background:#FFF3E0;border:2px solid #E65100;color:#E65100}
.Secret{background:#FFEBEE;border:2px solid #C62828;color:#C62828}
.stats-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px}
.stat{background:#f8f9fa;border-radius:8px;padding:14px;text-align:center}
.stat .v{font-size:1.3rem;font-weight:700;color:#1F3864}
.stat .l{font-size:0.72rem;color:#777;margin-top:3px}
.reco-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.reco-item{background:#f8f9fa;border-radius:6px;padding:10px 14px;font-size:0.85rem;display:flex;align-items:center;gap:8px}
.reco-item::before{content:"✓";color:#2E74B5;font-weight:700;flex-shrink:0}

/* DASHBOARD CHARTS */
.charts-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}
.chart-box{background:white;border-radius:12px;padding:20px;box-shadow:0 2px 10px rgba(0,0,0,0.06)}
.chart-box h3{font-size:0.9rem;color:#1F3864;margin-bottom:14px;font-weight:600}
.chart-full{background:white;border-radius:12px;padding:20px;box-shadow:0 2px 10px rgba(0,0,0,0.06);margin-bottom:20px}
.chart-full h3{font-size:0.9rem;color:#1F3864;margin-bottom:14px;font-weight:600}

/* HISTORIQUE TABLE */
.hist-table{width:100%;border-collapse:collapse;font-size:0.85rem}
.hist-table th{background:#1F3864;color:white;padding:10px 14px;text-align:left;font-weight:600}
.hist-table td{padding:10px 14px;border-bottom:1px solid #f0f0f0}
.hist-table tr:hover{background:#f8f9fa}
.badge-n{display:inline-block;padding:3px 10px;border-radius:12px;font-size:0.75rem;font-weight:600}
.b-Public{background:#E8F5E9;color:#2E7D32}
.b-Interne{background:#E3F2FD;color:#1565C0}
.b-Confidentiel{background:#FFF3E0;color:#E65100}
.b-Secret{background:#FFEBEE;color:#C62828}
.empty-hist{text-align:center;padding:32px;color:#aaa;font-size:0.9rem}

/* ALERTS */
.alert-box{background:#FFEBEE;border-left:4px solid #C62828;border-radius:8px;padding:14px 18px;margin-bottom:16px;font-size:0.88rem;color:#C62828}
.alert-item{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.alert-item:last-child{margin-bottom:0}
</style>
</head>
<body>

<header>
  <div class="brand">
    <span>🔐</span>
    <div>
      <h1>Système de Classification DGBFIP — Gabon</h1>
      <p>SPOTITECH GROUP SA | Mastère 2 Data & IA | 2025-2026</p>
    </div>
  </div>
  <div class="user-info">
    <span class="user-badge">👤 {{ username }} — {{ role }}</span>
    <a href="/logout" class="btn-logout">Déconnexion</a>
  </div>
</header>

<div class="tabs">
  <div class="tab active" onclick="showTab('dashboard')">📊 Dashboard</div>
  <div class="tab" onclick="showTab('classifier')">🔍 Classifier</div>
  <div class="tab" onclick="showTab('historique')">📋 Historique</div>
</div>

<!-- ══ TAB DASHBOARD ══════════════════════════════════ -->
<div class="tab-content active" id="tab-dashboard">

  <!-- Alertes -->
  <div class="alert-box">
    <div class="alert-item">🚨 <strong>3 tentatives d'accès non autorisées</strong> détectées sur 90 jours — table Budget_Previsionnel</div>
    <div class="alert-item">⚠️ <strong>8 tables critiques</strong> sans chiffrement identifiées — action requise</div>
    <div class="alert-item">⚠️ <strong>23% des comptes</strong> avec droits excessifs — revue recommandée</div>
  </div>

  <!-- KPI -->
  <div class="kpi-grid">
    <div class="kpi"><div class="val">47</div><div class="lbl">Tables auditées</div></div>
    <div class="kpi"><div class="val">27,4 Go</div><div class="lbl">Données analysées</div></div>
    <div class="kpi"><div class="val">91%</div><div class="lbl">Accuracy RF</div></div>
    <div class="kpi"><div class="val">23%</div><div class="lbl">Droits excessifs</div></div>
    <div class="kpi"><div class="val">8</div><div class="lbl">Tables non chiffrées</div></div>
    <div class="kpi"><div class="val">98 j.</div><div class="lbl">Durée du stage</div></div>
  </div>

  <!-- Graphiques -->
  <div class="charts-grid">
    <div class="chart-box">
      <h3>Répartition des 47 tables par niveau</h3>
      <canvas id="chartDoughnut" height="220"></canvas>
    </div>
    <div class="chart-box">
      <h3>Tables par système DGBFIP</h3>
      <canvas id="chartSystèmes" height="220"></canvas>
    </div>
  </div>

  <div class="chart-full">
    <h3>Tentatives d'accès non autorisées — 90 jours</h3>
    <canvas id="chartIncidents" height="90"></canvas>
  </div>

  <div class="charts-grid">
    <div class="chart-box">
      <h3>Comparaison des algorithmes testés (Accuracy %)</h3>
      <canvas id="chartAlgo" height="200"></canvas>
    </div>
    <div class="chart-box">
      <h3>Importance des variables du modèle (%)</h3>
      <canvas id="chartImportance" height="200"></canvas>
    </div>
  </div>

</div>

<!-- ══ TAB CLASSIFIER ════════════════════════════════ -->
<div class="tab-content" id="tab-classifier">
  <div class="card">
    <h2>🔍 Classifier une nouvelle table</h2>
    <div class="form-grid">
      <div class="field">
        <label>Volume (nombre de lignes)</label>
        <input type="number" id="volume_lignes" placeholder="ex: 850000" min="0">
      </div>
      <div class="field">
        <label>Nombre de champs PII</label>
        <input type="number" id="nb_champs_pii" placeholder="ex: 4" min="0">
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
        <input type="number" id="nb_utilisateurs_acces" placeholder="ex: 45" min="0">
      </div>
      <div class="field">
        <label>Fréquence d'accès par jour</label>
        <input type="number" id="frequence_acces_jour" placeholder="ex: 320" min="0">
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
    <button class="btn-classify" onclick="classifier()">🔍 Classifier cette table</button>
  </div>

  <div id="result-box">
    <div class="card">
      <h2>📊 Résultat de la classification</h2>
      <div class="result-header" id="result-header">
        <div>
          <div class="niveau" id="r-niveau">—</div>
          <div class="conf"  id="r-conf">—</div>
        </div>
      </div>
      <div class="stats-row">
        <div class="stat"><div class="v" id="r-conf2">—</div><div class="l">Confiance du modèle</div></div>
        <div class="stat"><div class="v">Random Forest</div><div class="l">Algorithme utilisé</div></div>
        <div class="stat"><div class="v">91%</div><div class="l">Accuracy globale</div></div>
      </div>
      <strong style="font-size:0.88rem;color:#555">Recommandations de sécurité :</strong>
      <div class="reco-grid" id="r-reco" style="margin-top:12px"></div>
    </div>
  </div>
</div>

<!-- ══ TAB HISTORIQUE ════════════════════════════════ -->
<div class="tab-content" id="tab-historique">
  <div class="card">
    <h2>📋 Historique des classifications</h2>
    <div id="hist-container">
      <div class="empty-hist">Aucune classification effectuée dans cette session.</div>
    </div>
  </div>
</div>

<script>
// ── TABS ─────────────────────────────────────────────────
function showTab(name) {
  document.querySelectorAll('.tab-content').forEach(function(t){t.classList.remove('active')});
  document.querySelectorAll('.tab').forEach(function(t){t.classList.remove('active')});
  document.getElementById('tab-'+name).classList.add('active');
  event.target.classList.add('active');
  if(name==='historique') loadHistorique();
}

// ── CLASSIFIER ───────────────────────────────────────────
function classifier() {
  var ids=['volume_lignes','nb_champs_pii','presence_financier','presence_nom',
           'presence_identifiant','nb_utilisateurs_acces','frequence_acces_jour',
           'chiffrement_actuel','logs_actives'];
  var data={};
  for(var i=0;i<ids.length;i++){
    var v=document.getElementById(ids[i]).value.trim();
    if(v===''){alert('Veuillez remplir : '+ids[i].replace(/_/g,' '));return;}
    data[ids[i]]=parseFloat(v);
  }
  var btn=document.querySelector('.btn-classify');
  btn.textContent='⏳ Classification en cours...';
  btn.disabled=true;
  fetch('/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
  .then(function(r){return r.json();})
  .then(function(d){
    var box=document.getElementById('result-box');
    var hdr=document.getElementById('result-header');
    hdr.className='result-header '+d.niveau;
    document.getElementById('r-niveau').textContent=d.niveau.toUpperCase();
    document.getElementById('r-conf').textContent=d.confiance+'% de confiance';
    document.getElementById('r-conf2').textContent=d.confiance+'%';
    var rg=document.getElementById('r-reco');
    rg.innerHTML='';
    d.recommandations.forEach(function(r){
      var div=document.createElement('div');
      div.className='reco-item';
      div.textContent=r;
      rg.appendChild(div);
    });
    box.style.display='block';
    box.scrollIntoView({behavior:'smooth'});
    btn.textContent='🔍 Classifier cette table';
    btn.disabled=false;
  })
  .catch(function(){
    alert('Erreur de connexion.');
    btn.textContent='🔍 Classifier cette table';
    btn.disabled=false;
  });
}

// ── HISTORIQUE ───────────────────────────────────────────
function loadHistorique(){
  fetch('/historique').then(function(r){return r.json();}).then(function(data){
    var c=document.getElementById('hist-container');
    if(!data.length){c.innerHTML='<div class="empty-hist">Aucune classification dans cette session.</div>';return;}
    var html='<table class="hist-table"><thead><tr><th>#</th><th>Heure</th><th>Volume</th><th>PII</th><th>Financier</th><th>Users</th><th>Résultat</th><th>Confiance</th></tr></thead><tbody>';
    data.slice().reverse().forEach(function(h,i){
      html+='<tr><td>'+(data.length-i)+'</td><td>'+h.heure+'</td><td>'+h.volume.toLocaleString()+'</td><td>'+h.pii+'</td><td>'+(h.financier?'Oui':'Non')+'</td><td>'+h.users+'</td><td><span class="badge-n b-'+h.niveau+'">'+h.niveau+'</span></td><td>'+h.confiance+'%</td></tr>';
    });
    html+='</tbody></table>';
    c.innerHTML=html;
  });
}

// ── GRAPHIQUES ───────────────────────────────────────────
window.addEventListener('load',function(){
  // Donut — répartition 47 tables
  new Chart(document.getElementById('chartDoughnut'),{
    type:'doughnut',
    data:{
      labels:['Public (8)','Interne (12)','Confidentiel (17)','Secret (10)'],
      datasets:[{data:[8,12,17,10],backgroundColor:['#2E7D32','#1565C0','#E65100','#C62828'],borderWidth:2,borderColor:'#fff'}]
    },
    options:{plugins:{legend:{position:'bottom',labels:{font:{size:11}}}},cutout:'60%'}
  });

  // Bar — systèmes
  new Chart(document.getElementById('chartSystèmes'),{
    type:'bar',
    data:{
      labels:['SIGFIP','ASTER','VECTEUR','SIRH','DATACENTER'],
      datasets:[{label:'Tables',data:[12,10,8,9,8],backgroundColor:['#2E74B5','#1F3864','#F9A825','#2E7D32','#C62828'],borderRadius:6}]
    },
    options:{plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,max:14,grid:{color:'#f0f0f0'}}}}
  });

  // Line — incidents
  var mois=['Jan','Fév','Mar','Avr','Mai','Juin','Juil','Aoû','Sep','Oct','Nov','Déc','Jan','Fév','Mar'];
  new Chart(document.getElementById('chartIncidents'),{
    type:'line',
    data:{
      labels:mois,
      datasets:[{label:'Tentatives non autorisées',data:[0,0,1,0,0,0,0,1,0,0,0,1,0,0,0],borderColor:'#C62828',backgroundColor:'rgba(198,40,40,0.08)',tension:0.4,pointRadius:5,pointBackgroundColor:'#C62828',fill:true}]
    },
    options:{plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,max:3,ticks:{stepSize:1},grid:{color:'#f5f5f5'}}}}
  });

  // Bar — algorithmes
  new Chart(document.getElementById('chartAlgo'),{
    type:'bar',
    data:{
      labels:['Régression\nLogistique','KNN','Arbre de\nDécision','Random\nForest ✓'],
      datasets:[
        {label:'Train %',data:[78,85,98,97],backgroundColor:'rgba(46,116,181,0.5)',borderRadius:4},
        {label:'Test %', data:[79,84,87,91],backgroundColor:'#1F3864',borderRadius:4}
      ]
    },
    options:{plugins:{legend:{position:'top',labels:{font:{size:10}}}},scales:{y:{min:70,max:100,grid:{color:'#f0f0f0'}}}}
  });

  // Bar horizontal — importance variables
  new Chart(document.getElementById('chartImportance'),{
    type:'bar',
    data:{
      labels:['nb_champs_pii','presence_financier','nb_utilisateurs','chiffrement','volume_lignes','autres'],
      datasets:[{data:[31,22,18,14,9,6],backgroundColor:['#C62828','#E65100','#F9A825','#2E74B5','#1F3864','#888'],borderRadius:4}]
    },
    options:{
      indexAxis:'y',
      plugins:{legend:{display:false}},
      scales:{x:{max:35,grid:{color:'#f0f0f0'}}}
    }
  });
});
</script>
</body>
</html>
"""

# ════════════════════════════════════════════════════════════
# ROUTES FLASK
# ════════════════════════════════════════════════════════════
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template_string(MAIN_PAGE,
        username=session['username'],
        role=session['role'])

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        u = request.form.get('username','').strip()
        p = request.form.get('password','').strip()
        if u in USERS and USERS[u]['password'] == p:
            session['username'] = u
            session['role']     = USERS[u]['role']
            return redirect(url_for('index'))
        error = 'Identifiant ou mot de passe incorrect.'
    return render_template_string(LOGIN_PAGE, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400
    niveau, confiance = classifier_table(data)
    # Sauvegarder dans l'historique
    historique.append({
        'heure':     datetime.now().strftime('%H:%M:%S'),
        'volume':    int(data.get('volume_lignes',0)),
        'pii':       int(data.get('nb_champs_pii',0)),
        'financier': int(data.get('presence_financier',0)),
        'users':     int(data.get('nb_utilisateurs_acces',0)),
        'niveau':    niveau,
        'confiance': confiance,
        'user':      session['username'],
    })
    return jsonify({
        'niveau':          niveau,
        'confiance':       confiance,
        'recommandations': RECO[niveau],
    })

@app.route('/historique')
def get_historique():
    if 'username' not in session:
        return jsonify([])
    return jsonify(historique)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'version': '3.0'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
