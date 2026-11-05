"""Recherche OpenSanctions (API hébergée, clé requise : https://www.opensanctions.org/api/)."""
import os
import requests

API = "https://api.opensanctions.org"

def _key():
    k = os.getenv("OPENSANCTIONS_API_KEY")
    if k:
        return k
    try:
        import streamlit as st
        return st.secrets.get("OPENSANCTIONS_API_KEY")
    except Exception:
        return None

def search(q, schema="Thing", limit=15, dataset="default"):
    k = _key()
    if not k:
        raise RuntimeError("Clé API manquante : définissez OPENSANCTIONS_API_KEY (voir README).")
    r = requests.get(f"{API}/search/{dataset}", params={"q": q, "schema": schema, "limit": limit},
                     headers={"Authorization": f"ApiKey {k}"}, timeout=20)
    r.raise_for_status()
    return r.json().get("results", [])
