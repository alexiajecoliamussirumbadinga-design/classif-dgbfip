# ================================================================
# train_model.py — Ré-entraînement du Random Forest — Classification DGBFIP
# Auteure : MUSSIRU MBADINGA Alexia Jecolia
# SPOTITECH GROUP SA | Mastère 2 Data & IA | 2025-2026
# ----------------------------------------------------------------
# Deux méthodologies disponibles :
#
#   --methode notebook  (défaut) : reproduit exactement le notebook de la thèse
#       encodage + log1p + StandardScaler + SMOTE sur le dataset COMPLET,
#       PUIS split 70/30 stratifié. Score ~91 % (annoncé dans la thèse).
#       ⚠️  SMOTE avant le split = fuite de données -> score optimiste.
#
#   --methode propre : split 70/30 stratifié D'ABORD, puis StandardScaler
#       et SMOTE ajustés sur le TRAIN uniquement. Score honnête ~67 %
#       (dataset de 47 lignes trop petit pour ce modèle).
#
# Dans les deux cas :
#   - donnees/train.csv et donnees/test.csv sont écrits à partir d'un
#     split stratifié 70/30 des lignes brutes (livrable demandé) ;
#   - les artefacts sont sauvegardés dans models/.
# ================================================================
import os
import json
import argparse
import datetime

import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from imblearn.over_sampling import SMOTE

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "donnees")
MODELS_DIR = os.path.join(BASE_DIR, "models")
RAW_CSV = os.path.join(DATA_DIR, "donnees brutes.csv")

FEATURES = ["volume_lignes", "nb_champs_pii", "presence_financier",
            "presence_nom", "presence_identifiant", "nb_utilisateurs_acces",
            "frequence_acces_jour", "chiffrement_actuel", "logs_actives"]
TARGET = "niveau_sensibilite"
LOG_COLS = [0, 6]  # volume_lignes, frequence_acces_jour
ORDER = ["Public", "Interne", "Confidentiel", "Secret"]
RANDOM_STATE = 42

PARAM_GRID = {
    "n_estimators": [50, 100, 200, 300],
    "max_depth": [None, 5, 10, 15],
    "min_samples_split": [2, 4, 6],
    "min_samples_leaf": [1, 2, 3],
}


def preprocess(X, log_cols=LOG_COLS):
    X = np.asarray(X, dtype=float).copy()
    for c in log_cols:
        X[:, c] = np.log1p(X[:, c])
    return X


def write_split_csv(df, y_labels):
    """Livrable : split stratifié 70/30 des lignes brutes -> train.csv / test.csv."""
    idx = np.arange(len(df))
    idx_train, idx_test = train_test_split(
        idx, test_size=0.30, random_state=RANDOM_STATE, stratify=y_labels
    )
    df.iloc[idx_train].to_csv(os.path.join(DATA_DIR, "train.csv"), index=False)
    df.iloc[idx_test].to_csv(os.path.join(DATA_DIR, "test.csv"), index=False)
    print(f"\nLivrable — split 70/30 stratifie des lignes brutes :")
    print(f"   donnees/train.csv : {len(idx_train)} lignes")
    print(f"   donnees/test.csv  : {len(idx_test)} lignes")
    return idx_train, idx_test


def prepare_notebook(df):
    """Méthode notebook : encodage + log1p + scaler + SMOTE sur le dataset COMPLET, puis split."""
    le = LabelEncoder().fit(df[TARGET].values)
    y_raw = le.transform(df[TARGET].values)

    X_scaled_src = preprocess(df[FEATURES].values)
    scaler = StandardScaler().fit(X_scaled_src)
    X_scaled = scaler.transform(X_scaled_src)

    print("\nDistribution AVANT SMOTE :")
    for cls, c in zip(le.classes_, np.bincount(y_raw)):
        print(f"   {cls:<13} : {c}")

    sm = SMOTE(random_state=RANDOM_STATE, k_neighbors=3)
    X_sm, y_sm = sm.fit_resample(X_scaled, y_raw)

    print("Distribution APRES SMOTE :")
    for cls, c in zip(le.classes_, np.bincount(y_sm)):
        print(f"   {cls:<13} : {c}")
    print(f"   Total : {len(y_sm)} observations")

    X_train, X_test, y_train, y_test = train_test_split(
        X_sm, y_sm, test_size=0.30, random_state=RANDOM_STATE, stratify=y_sm
    )
    print(f"\nSplit 70/30 stratifie (sur donnees SMOTE) : train={len(y_train)}  test={len(y_test)}")

    n_splits = 5
    return le, scaler, X_train, X_test, y_train, y_test, X_sm, y_sm, n_splits


def prepare_propre(df, idx_train, idx_test):
    """Méthode propre : scaler + SMOTE ajustés sur le TRAIN uniquement."""
    y_labels = df[TARGET].values
    le = LabelEncoder().fit(y_labels)
    y_train = le.transform(y_labels[idx_train])
    y_test = le.transform(y_labels[idx_test])

    X = df[FEATURES].values
    X_train_raw = preprocess(X[idx_train])
    X_test_raw = preprocess(X[idx_test])

    scaler = StandardScaler().fit(X_train_raw)
    X_train_sc = scaler.transform(X_train_raw)
    X_test_sc = scaler.transform(X_test_raw)

    print("\nDistribution TRAIN avant SMOTE :")
    for cls, c in zip(le.classes_, np.bincount(y_train)):
        print(f"   {cls:<13} : {c}")

    k = max(1, min(3, int(np.bincount(y_train).min()) - 1))
    sm = SMOTE(random_state=RANDOM_STATE, k_neighbors=k)
    X_train_bal, y_train_bal = sm.fit_resample(X_train_sc, y_train)
    print(f"SMOTE (k_neighbors={k}) sur le train : {len(y_train)} -> {len(y_train_bal)} obs.")

    n_splits = min(5, int(np.bincount(y_train_bal).min()))
    return le, scaler, X_train_bal, X_test_sc, y_train_bal, y_test, X_train_bal, y_train_bal, n_splits


def main():
    parser = argparse.ArgumentParser(description="Ré-entraînement du Random Forest DGBFIP")
    parser.add_argument("--methode", choices=["notebook", "propre"], default="notebook",
                        help="notebook = SMOTE avant split (~91%%, méthode de la thèse) ; "
                             "propre = SMOTE sur le train seul (~67%%, sans fuite)")
    args = parser.parse_args()

    os.makedirs(MODELS_DIR, exist_ok=True)

    # ---- Chargement ---------------------------------------------------
    df = pd.read_csv(RAW_CSV)
    print(f"Methode : {args.methode}")
    print(f"Dataset brut : {df.shape[0]} tables x {df.shape[1]} colonnes")
    dist = df[TARGET].value_counts()
    for niv in ORDER:
        c = int(dist.get(niv, 0))
        print(f"   {niv:<13} {c:>2} ({c / len(df) * 100:.1f}%)")

    # ---- Livrable train.csv / test.csv ------------------------------
    idx_train, idx_test = write_split_csv(df, df[TARGET].values)

    # ---- Préparation selon la méthode -----------------------------
    if args.methode == "notebook":
        le, scaler, X_tr, X_te, y_tr, y_te, X_cv, y_cv, n_splits = prepare_notebook(df)
    else:
        le, scaler, X_tr, X_te, y_tr, y_te, X_cv, y_cv, n_splits = prepare_propre(df, idx_train, idx_test)
    print("\nClasses encodees :", dict(zip(le.classes_, le.transform(le.classes_))))

    # ---- GridSearchCV --------------------------------------------
    gs = GridSearchCV(
        RandomForestClassifier(class_weight="balanced", random_state=RANDOM_STATE),
        PARAM_GRID,
        cv=StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE),
        scoring="accuracy", n_jobs=-1, verbose=0,
    )
    gs.fit(X_cv, y_cv)

    best_rf = gs.best_estimator_
    best_rf.fit(X_tr, y_tr)

    print("\nMeilleurs hyperparametres :")
    for kk, vv in gs.best_params_.items():
        print(f"   {kk:<20} : {vv}")
    print(f"Meilleur score CV : {gs.best_score_ * 100:.2f} %")

    # ---- Évaluation --------------------------------------------
    y_pred = best_rf.predict(X_te)
    acc_test = accuracy_score(y_te, y_pred)
    acc_train = accuracy_score(y_tr, best_rf.predict(X_tr))
    print("\n" + "=" * 60)
    print(f"Accuracy train : {acc_train * 100:.2f} %")
    print(f"Accuracy test  : {acc_test * 100:.2f} %")
    print(f"Ecart          : {(acc_train - acc_test) * 100:.2f} points")
    print("=" * 60)
    labels_present = np.unique(np.concatenate([y_te, y_pred]))
    print(classification_report(
        y_te, y_pred,
        labels=labels_present,
        target_names=[le.classes_[i] for i in labels_present],
        digits=4, zero_division=0,
    ))
    print("Matrice de confusion (lignes = reel, colonnes = predit) :")
    print(confusion_matrix(y_te, y_pred))

    # ---- Sauvegarde des artefacts ----------------------------
    joblib.dump(best_rf, os.path.join(MODELS_DIR, "random_forest_dgb.pkl"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.pkl"))
    joblib.dump(le, os.path.join(MODELS_DIR, "label_encoder.pkl"))

    metadata = {
        "projet": "Classification donnees sensibles DGBFIP Gabon",
        "auteure": "MUSSIRU MBADINGA Alexia Jecolia",
        "entreprise": "SPOTITECH GROUP SA",
        "client": "DGBFIP",
        "date_entrainement": datetime.datetime.now().isoformat(timespec="seconds"),
        "methodologie": args.methode,
        "modele": "RandomForestClassifier",
        "hyperparams": gs.best_params_,
        "cv_score": round(gs.best_score_ * 100, 2),
        "test_accuracy": round(acc_test * 100, 2),
        "train_accuracy": round(acc_train * 100, 2),
        "split": {"train": int(len(idx_train)), "test": int(len(idx_test)), "ratio": "70/30 stratifie"},
        "classes": list(le.classes_),
        "features": FEATURES,
        "log_transform": ["volume_lignes", "frequence_acces_jour"],
        "nb_tables": int(len(df)),
    }
    with open(os.path.join(MODELS_DIR, "model_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\nArtefacts sauvegardes dans models/ :")
    for fname in ["random_forest_dgb.pkl", "scaler.pkl", "label_encoder.pkl", "model_metadata.json"]:
        path = os.path.join(MODELS_DIR, fname)
        print(f"   OK  {fname:<28} ({os.path.getsize(path) / 1024:.1f} Ko)")


if __name__ == "__main__":
    main()
