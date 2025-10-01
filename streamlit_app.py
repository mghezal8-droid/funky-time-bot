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

# --- Segments ---
segments_letters = list("PLAYFUNKTIME")
segments_others = ["1", "Bar", "Disco", "VIPDisco", "StayingAlive"]
segments = segments_others + segments_letters

# --- Fonctions ---
def calc_gain(result, mult, mise):
    if result in segments_letters:
        return mise * 25 + mise
    elif result == "StayingAlive":
        return mise * mult + mise
    else:
        return -mise  # Perte totale si autre segment

def adjust_mise(bankroll, last_mise, last_gain):
    if last_gain <= 0:
        mise = min(bankroll/2, last_mise * 2)
        mise = max(1, min(mise, 5))
    else:
        mise = 1
    return mise

def suggest_strategy(last_spin, last_gain, last_mise, bankroll):
    next_segments = segments_letters.copy()
    if last_spin != "StayingAlive":
        next_segments.append("StayingAlive")
    mise = adjust_mise(bankroll, last_mise, last_gain)
    next_mises = {seg: mise for seg in next_segments}
    strategy = "❌ Perte -> Doubler/ajuster mise" if last_gain <= 0 else "✅ Gain -> Maintenir/ajuster mise"
    return strategy, next_mises

def process_spin(result, mult):
    last_mise = st.session_state.results_df["Mise"].iloc[-1] if not st.session_state.results_df.empty else 1
    last_bankroll = st.session_state.results_df["Bankroll"].iloc[-1] if not st.session_state.results_df.empty else 150
    last_gain = st.session_state.results_df["Gain"].iloc[-1] if not st.session_state.results_df.empty else 0
    last_spin_val = st.session_state.results_df["Résultat"].iloc[-1] if not st.session_state.results_df.empty else None

    # Pas de mise sur 1, ni sur Staying Alive si sorti tour précédent
    if result == "1" or (result == "StayingAlive" and last_spin_val == "StayingAlive"):
        mise_appliquee = 0
    else:
        mise_appliquee = last_mise

    gain = calc_gain(result, mult, mise_appliquee)
    new_bankroll = last_bankroll + gain

    new_row = {
        "Spin": len(st.session_state.results_df) + 1,
        "Résultat": result,
        "Multiplicateur": mult,
        "Mise": mise_appliquee,
        "Gain": gain,
        "Bankroll": new_bankroll
    }
    st.session_state.results_df = pd.concat([st.session_state.results_df, pd.DataFrame([new_row])], ignore_index=True)

    strategy, next_mises = suggest_strategy(result, gain, last_mise, new_bankroll)
    st.session_state.next_mises = next_mises

    return strategy

# --- Interface ---
st.title("🎰 Funky Time - Bot Martingale Dynamique")

# --- Sidebar historique ---
st.sidebar.header("📥 Ajouter spin à l'historique")
mult = st.sidebar.number_input("Multiplicateur (Top Slot ou Staying Alive)", min_value=1, value=1, step=1)

# Boutons pour historique
st.sidebar.subheader("Historique Spins")
for seg in segments:
    if st.sidebar.button(f"{seg} ➕ Historique"):
        spin_num = len(st.session_state.history) + 1
        st.session_state.history.append({"Spin": spin_num, "Résultat": seg, "Multiplicateur": mult})
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

        if result == "1":
            mise = 0
        elif result == "StayingAlive" and last_spin == "StayingAlive":
            mise = 0
        else:
            mise = base_mise

        gain = calc_gain(result, mult, mise)
        bankroll += gain

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
    mult_live = st.number_input("Multiplicateur Live", min_value=1, value=1, step=1)
    st.subheader("Cliquer sur un segment pour live spin")
    for seg in segments:
        if st.button(f"{seg} ➡️ Live Spin"):
            strategy = process_spin(seg, mult_live)
            st.success(f"Spin ajouté : {seg} x{mult_live} | Stratégie suggérée : {strategy}")

    if st.session_state.next_mises:
        st.subheader("📌 Mise conseillée pour le prochain spin")
        mises_df = pd.DataFrame(list(st.session_state.next_mises.items()), columns=["Segment", "Mise ($)"])
        st.dataframe(mises_df, use_container_width=True)
        st.info(f"Mise totale conseillée : {mises_df['Mise ($)'].sum():.2f} $")
