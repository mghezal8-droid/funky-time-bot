import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Config ---
st.set_page_config(page_title="Funky Time Bot", layout="wide")

# --- Initialisation ---
if "history" not in st.session_state:
    st.session_state.history = []
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 150
if "mode_live" not in st.session_state:
    st.session_state.mode_live = False
if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame(columns=["Spin", "Résultat", "Multiplicateur", "Gain", "Bankroll"])

# --- Stratégie simple Funky Time ---
def calc_gain(result, mult, mise):
    """Calcule le gain pour Funky Time (simplifié pour Martingale sur lettres et Staying Alive)."""
    lettres = list("PLAYFUNKTIME")
    gain = 0

    if result in lettres:
        gain = 25 * mise * mult
    elif result == "StayingAlive":
        gain = 50 * mise * mult
    else:
        gain = 0

    return gain

# --- Ajouter un spin ---
st.sidebar.header("Ajouter un spin")
col1, col2 = st.sidebar.columns([2,1])

with col1:
    result = st.radio("Résultat du spin :", 
                      ["1", "Bar", "Disco", "VIPDisco", "StayingAlive"] + list("PLAYFUNKTIME"), 
                      horizontal=True)

with col2:
    multiplicateur = st.number_input("Multiplicateur", min_value=1, value=1, step=1)

if st.sidebar.button("➕ Ajouter au tableau"):
    spin_num = len(st.session_state.history) + 1
    st.session_state.history.append({"Spin": spin_num, "Résultat": result, "Multiplicateur": multiplicateur})
    st.session_state.results_df = pd.DataFrame(st.session_state.history)

if st.sidebar.button("🗑 Supprimer dernier spin"):
    if st.session_state.history:
        st.session_state.history.pop()
        st.session_state.results_df = pd.DataFrame(st.session_state.history)

# --- Tableau d’historique ---
st.subheader("📜 Historique des spins")
if not st.session_state.results_df.empty:
    st.dataframe(st.session_state.results_df, use_container_width=True)

# --- Lancer calcul bankroll ---
if st.sidebar.button("✅ Fin historique et commencer"):
    bankroll = 150
    mises = []
    bankrolls = []
    results = []

    mise_base = 1
    mise_courante = mise_base
    last_spin = None

    for spin in st.session_state.history:
        result = spin["Résultat"]
        mult = spin["Multiplicateur"]

        # On joue Martingale sur lettres + Staying Alive sauf si ça vient de sortir
        if result == "StayingAlive" and last_spin == "StayingAlive":
            mise = 0
        else:
            mise = mise_courante

        gain = calc_gain(result, mult, mise)
        bankroll += gain - mise

        # Ajustement Martingale
        if gain > 0:
            mise_courante = mise_base
        else:
            mise_courante *= 2

        mises.append(mise)
        bankrolls.append(bankroll)
        results.append(gain)

        last_spin = result

    # DataFrame résultat
    df = pd.DataFrame({
        "Spin": [i+1 for i in range(len(mises))],
        "Mise": mises,
        "Gain": results,
        "Bankroll": bankrolls
    })

    st.session_state.results_df = df
    st.session_state.mode_live = True

    # Affichage
    st.subheader("📊 Résultats calculés")
    st.dataframe(df, use_container_width=True)

    # Courbe bankroll
    st.subheader("📈 Évolution du bankroll")
    plt.plot(df["Spin"], df["Bankroll"], marker="o")
    plt.xlabel("Spin")
    plt.ylabel("Bankroll")
    plt.title("Évolution du bankroll (historique)")
    st.pyplot(plt)

# --- Mode Live après l’historique ---
if st.session_state.mode_live:
    st.subheader("🎬 Mode Live - entrez les spins un par un")

    live_col1, live_col2 = st.columns([2,1])
    with live_col1:
        live_result = st.radio("Résultat du spin (Live)", 
                               ["1", "Bar", "Disco", "VIPDisco", "StayingAlive"] + list("PLAYFUNKTIME"),
                               horizontal=True)
    with live_col2:
        live_mult = st.number_input("Multiplicateur (Live)", min_value=1, value=1, step=1)

    if st.button("➡️ Entrer le spin Live"):
        last_bankroll = st.session_state.results_df["Bankroll"].iloc[-1]
        last_mise = st.session_state.results_df["Mise"].iloc[-1] if not st.session_state.results_df.empty else 1

        gain = calc_gain(live_result, live_mult, last_mise)
        new_bankroll = last_bankroll + gain - last_mise

        new_row = {
            "Spin": len(st.session_state.results_df) + 1,
            "Mise": last_mise,
            "Gain": gain,
            "Bankroll": new_bankroll
        }
        st.session_state.results_df = pd.concat([st.session_state.results_df, pd.DataFrame([new_row])], ignore_index=True)

        # Affichage
        st.dataframe(st.session_state.results_df, use_container_width=True)
        st.success(f"Résultat enregistré : {live_result} x{live_mult} | Gain {gain}$ | Bankroll {new_bankroll}$")
