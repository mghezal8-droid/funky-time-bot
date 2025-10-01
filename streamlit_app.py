import streamlit as st
import pandas as pd

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
    st.session_state.results_df = pd.DataFrame(columns=["Spin", "Résultat", "Multiplicateur", "Mise", "Gain", "Bankroll"])
if "next_mises" not in st.session_state:
    st.session_state.next_mises = {}

# --- Paiements ---
payouts = {
    "1": 1,
    "Bar": 20,
    "Disco": 25,
    "VIPDisco": 50,
    "StayingAlive": 20,
    "P": 25, "L": 25, "A": 25, "Y": 25,
    "F": 25, "U": 25, "N": 25, "K": 25,
    "T": 25, "I": 25, "M": 25, "E": 25,
}

# --- Fonctions ---
def calc_gain(result, mult, mise):
    lettres = list("PLAYFUNKTIME")
    if result in lettres:
        return 25 * mise * mult
    elif result == "StayingAlive":
        return 50 * mise * mult
    else:
        return 0

def adjust_mise(bankroll, base_mise, last_gain):
    """Ajustement dynamique de la mise selon bankroll et dernier gain/perte"""
    if last_gain == 0:
        # Perte -> doubler mise (Martingale)
        mise = min(base_mise * 2, bankroll/2)
    else:
        # Gain -> mise de base ajustée selon bankroll
        mise = min(base_mise, bankroll/2)
    # Limiter mise minimale
    return max(mise, 1)

def suggest_strategy(last_spin, last_gain, last_mise, bankroll):
    segments = list("PLAYFUNKTIME")
    if last_spin != "StayingAlive":
        segments.append("StayingAlive")

    next_mises = {}
    mise = adjust_mise(bankroll, last_mise, last_gain)
    
    if last_gain == 0:
        strategy = "❌ Perte -> Doubler/ajuster mise (Martingale)"
    else:
        strategy = "✅ Gain -> Maintenir/ajuster mise"

    for seg in segments:
        next_mises[seg] = mise

    return strategy, next_mises

def process_spin(result, mult):
    last_mise = st.session_state.results_df["Mise"].iloc[-1] if not st.session_state.results_df.empty else 1
    last_bankroll = st.session_state.results_df["Bankroll"].iloc[-1] if not st.session_state.results_df.empty else 150
    last_spin_val = st.session_state.results_df["Résultat"].iloc[-1] if not st.session_state.results_df.empty else None
    last_gain = st.session_state.results_df["Gain"].iloc[-1] if not st.session_state.results_df.empty else 0

    gain = calc_gain(result, mult, last_mise)
    new_bankroll = last_bankroll + gain - last_mise

    new_row = {
        "Spin": len(st.session_state.results_df) + 1,
        "Résultat": result,
        "Multiplicateur": mult,
        "Mise": last_mise,
        "Gain": gain,
        "Bankroll": new_bankroll
    }
    st.session_state.results_df = pd.concat([st.session_state.results_df, pd.DataFrame([new_row])], ignore_index=True)

    strategy, next_mises = suggest_strategy(result, gain, last_mise, new_bankroll)
    st.session_state.next_mises = next_mises

    return strategy

# --- Interface ---
st.title("🎰 Funky Time - Bot Martingale Dynamique")

# Sidebar: ajouter spins
st.sidebar.header("📥 Ajouter spin à l'historique")
result = st.sidebar.radio("Résultat :", ["1","Bar","Disco","VIPDisco","StayingAlive"] + list("PLAYFUNKTIME"), horizontal=True)
mult = st.sidebar.number_input("Multiplicateur (Top Slot)", min_value=1, value=1, step=1)

if st.sidebar.button("➕ Ajouter au tableau"):
    spin_num = len(st.session_state.history) + 1
    st.session_state.history.append({"Spin": spin_num, "Résultat": result, "Multiplicateur": mult})
    st.session_state.results_df = pd.DataFrame(st.session_state.history)

if st.sidebar.button("🗑 Supprimer dernier spin"):
    if st.session_state.history:
        st.session_state.history.pop()
        st.session_state.results_df = pd.DataFrame(st.session_state.history)

if st.sidebar.button("✅ Fin historique et commencer"):
    bankroll = 150
    base_mise = 1
    last_spin = None
    mises = []
    bankrolls = []
    gains = []

    for spin in st.session_state.history:
        result = spin["Résultat"]
        mult = spin["Multiplicateur"]

        if result == "StayingAlive" and last_spin == "StayingAlive":
            mise = 0
        else:
            mise = base_mise

        gain = calc_gain(result, mult, mise)
        bankroll += gain - mise

        # Ajustement dynamique
        base_mise = adjust_mise(bankroll, base_mise, gain)

        mises.append(mise)
        gains.append(gain)
        bankrolls.append(bankroll)
        last_spin = result

    st.session_state.results_df = pd.DataFrame({
        "Spin": list(range(1, len(mises)+1)),
        "Résultat": [s["Résultat"] for s in st.session_state.history],
        "Multiplicateur": [s["Multiplicateur"] for s in st.session_state.history],
        "Mise": mises,
        "Gain": gains,
        "Bankroll": bankrolls
    })
    st.session_state.mode_live = True

# --- Tableau historique ---
st.subheader("📜 Historique des spins")
if not st.session_state.results_df.empty:
    st.dataframe(st.session_state.results_df, use_container_width=True)
    st.line_chart(st.session_state.results_df.set_index("Spin")["Bankroll"])

# --- Mode live ---
if st.session_state.mode_live:
    st.subheader("🎯 Mode Live - spin par spin")
    live_result = st.radio("Spin Live :", ["1","Bar","Disco","VIPDisco","StayingAlive"] + list("PLAYFUNKTIME"), horizontal=True)
    live_mult = st.number_input("Multiplicateur Live", min_value=1, value=1, step=1)

    if st.button("➡️ Entrer spin Live"):
        strategy = process_spin(live_result, live_mult)
        st.success(f"Spin ajouté : {live_result} x{live_mult} | Stratégie suggérée : {strategy}")

    # Affichage mises conseillées
    if st.session_state.next_mises:
        st.subheader("📌 Mise conseillée pour le prochain spin")
        mises_df = pd.DataFrame(list(st.session_state.next_mises.items()), columns=["Segment", "Mise ($)"])
        st.dataframe(mises_df, use_container_width=True)
        st.info(f"Mise totale conseillée : {mises_df['Mise ($)'].sum():.2f} $")
