# Système de Classification des Données Sensibles — DGBFIP Gabon

![Python](https://img.shields.io/badge/Python-3.11-blue)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4.0-orange)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![Accuracy](https://img.shields.io/badge/Accuracy-91%25-brightgreen)

> **Thèse professionnelle — Mastère 2 Data & Intelligence Artificielle**  
> NEXA Digital School / Doranco Espace Multimédia  
> Étudiante : MUSSIRU MBADINGA Alexia Jecolia  
> Entreprise : SPOTITECH GROUP SA — Client : DGBFIP, Libreville, Gabon  
> Période : 08 décembre 2025 – 08 avril 2026 (98 jours)

---

## Description du projet

Ce projet implémente un système automatisé de classification des données sensibles pour la Direction Générale du Budget et des Finances Publiques (DGBFIP) du Gabon, basé sur un algorithme Random Forest (accuracy 91%).

| Niveau | Label | Exemples |
|--------|-------|----------|
| 1 | PUBLIC | Loi de finances publiée, organigramme |
| 2 | INTERNE | Procédures internes, calendrier budgétaire |
| 3 | CONFIDENTIEL | Salaires, marchés publics, budgets détaillés |
| 4 | SECRET | Déclarations fiscales, prévisions macro-économiques |

---

## Résultats

- 47 tables auditées, 27,4 Go de données analysées
- Random Forest — Accuracy : **91%** (après optimisation GridSearchCV)
- Application Flask/Dash avec dashboard KPI temps réel

---

## Installation

```bash
git clone https://github.com/alexiajecoliamussirumbadinga-design/classif-dgbfip.git
cd classif-dgbfip
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Application accessible sur : http://localhost:5000

---

## Identifiants de test

| Rôle | Login | Mot de passe |
|------|-------|--------------|
| Administrateur DSI | `admin` | `dgbfip2026` |
| Utilisateur standard | `auditeur` | `classif2026` |

---

## Stack technique

- Python 3.11 / scikit-learn / pandas / numpy
- Flask 3.0 / Dash 2.16 / Plotly
- Modèle : Random Forest (200 arbres, GridSearchCV)
- Base : SQLite (logs audit)

---

## Auteure

**MUSSIRU MBADINGA Alexia Jecolia**  
Mastère 2 Data & Intelligence Artificielle  
NEXA Digital School / Doranco — 2025-2026
