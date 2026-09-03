# Déploiement sur Render — https://classif-dgbfip.onrender.com

L'application est prête pour Render. Tout est déjà configuré dans le dépôt :

| Fichier | Rôle |
|---|---|
| `render.yaml` | Blueprint Render : nom du service = `classif-dgbfip` → URL `classif-dgbfip.onrender.com` |
| `requirements.txt` | Dépendances **runtime** (Flask, gunicorn, numpy, scikit-learn, joblib) |
| `Procfile` | Commande de démarrage (compatible aussi Railway / Heroku) |
| `models/*.pkl` | Le modèle entraîné est versionné → aucun ré-entraînement au déploiement |

---

## Étapes (5 minutes, à faire une seule fois)

### 1. Pousser le code sur GitHub

```bash
git add render.yaml requirements.txt Procfile DEPLOIEMENT.md src/app_FINAL.py
git commit -m "Configuration deploiement Render"
git push origin main
```

### 2. Créer le service sur Render

1. Aller sur **https://dashboard.render.com** et se connecter (compte gratuit, connexion via GitHub).
2. Cliquer **New +** → **Blueprint**.
3. Sélectionner le dépôt **`alexiajecoliamussirumbadinga-design/classif-dgbfip`**.
4. Render détecte automatiquement `render.yaml` et propose le service **`classif-dgbfip`**.
5. Cliquer **Apply**.

> Si le nom `classif-dgbfip` est déjà pris sur Render, il faut le changer dans `render.yaml`
> (`name:`) — l'URL suivra (`<nouveau-nom>.onrender.com`).

### 3. Attendre le build

Le premier déploiement prend ~3–5 min (installation de numpy / scikit-learn).
Quand le statut passe à **Live**, l'application est accessible sur :

**https://classif-dgbfip.onrender.com**

Vérification : **https://classif-dgbfip.onrender.com/health** doit renvoyer
`{"modele":"random_forest","status":"ok"}`.

---

## Alternative sans `render.yaml` (création manuelle)

**New +** → **Web Service** → choisir le dépôt, puis :

| Réglage | Valeur |
|---|---|
| Name | `classif-dgbfip` |
| Region | Frankfurt |
| Branch | `main` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn --chdir src app_FINAL:app --bind 0.0.0.0:$PORT` |
| Instance Type | Free |
| Health Check Path | `/health` |

---

## Après le déploiement

- **Mises à jour automatiques** : à chaque `git push origin main`, Render redéploie tout seul (`autoDeploy: true`).
- **Changer de moteur** : dans Render → onglet **Environment** → variable `MOTEUR` = `rf` (Random Forest) ou `regles` (logique de règles), puis **Save** (redéploiement auto).
- **Plan gratuit** : le service s'endort après 15 min d'inactivité ; la première requête suivante met ~30–50 s à répondre (le temps du réveil). Pour une soutenance, ouvrir l'URL 1–2 min avant de commencer.
