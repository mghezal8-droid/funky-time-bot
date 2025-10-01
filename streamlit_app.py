import streamlit as st
import pandas as pd
from collections import Counter

# -------------------------------
# CONFIG INITIALE
# -------------------------------
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 150
if "initial_bankroll" not in st.session_state:
    st.session_state.initial_bankroll = 150
if "base_bet" not in st.session_state:
    st.session_state.base_bet = 1
if "current_bet" not in st.session_state:
    st.session_state.current_bet = 1
if "history" not in st.session_state:
    st.session_state.history = []  
if "pending_history" not in st.session_state:
    st.session_state.pending_history = []  
if "last_spin" not in st.session_state:
    st.session_state.last_spin = None
if "next_mises" not in st.session_state:
    st.session_state.next_mises = {}
if "pending_result" not in st.session_state:
    st.session_state.pending_result = None
if "history_done" not in st.session_state:
    st.session_state.history_done = False

# Paiements standards
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

# -------------------------------
# FONCTIONS
# -------------------------------
def add_to_pending(resultat, multiplicateur):
    st.session_state.pending_history.append({
        "Résultat": resultat,
        "Multiplicateur": multiplicateur
    })

def compute_probabilities():
    """Calcule la fréquence de sortie de chaque segment"""
    counter = Counter([spin['Résultat'] for spin in st.session_state.history])
    total = len(st.session_state.history) if st.session_state.history else 1
    probs = {seg: counter.get(seg, 0)/total for seg in payouts.keys()}
    return probs

def process_history():
    st.session_state.history = []
    st.session_state.bankroll = st.session_state.initial_bankroll
    st.session_state.current_bet = st.session_state.base_bet
    st.session_state.last_spin = None
    for entry in st.session_state.pending_history:
        process_spin(entry["Résultat"], entry["Multiplicateur"])
    st.session_state.history_done = True

def process_spin(resultat, multiplicateur):
    mise_totale = 0
    gain = 0

    segments = ["P","L","A","Y","F","U","N","K","T","I","M","E"]
    if st.session_state.last_spin != "StayingAlive":
        segments.append("StayingAlive")

    adjust_bet_for_bankroll()

    mises = {seg: st.session_state.current_bet for seg in segments}
    mise_totale = sum(mises.values())

    if resultat in mises:
        gain = mises[resultat] * payouts[resultat] * multiplicateur

    st.session_state.bankroll += (gain - mise_totale)

    st.session_state.history.append({
        "Spin": len(st.session_state.history)+1,
        "Résultat": resultat,
        "Multiplicateur": multiplicateur,
        "Mise Totale": mise_totale,
        "Gain": gain,
        "Bankroll": st.session_state.bankroll
    })

    suggestion, next_mises = strategy_suggestion(resultat, gain, mise_totale)
    st.session_state.last_spin = resultat
    st.session_state.next_mises = next_mises

    return suggestion

def adjust_bet_for_bankroll():
    """Protection dynamique: ajuste la mise si bankroll chute trop"""
    initial = st.session_state.initial_bankroll
    current = st.session_state.bankroll
    base = st.session_state.base_bet

    if current < 0.5 * initial:
        st.session_state.current_bet = max(0.2, base * (current / initial))
    else:
        st.session_state.current_bet = base

def strategy_suggestion(resultat, gain, mise_totale):
    base = st.session_state.current_bet
    bankroll = st.session_state.bankroll
    segments = ["P","L","A","Y","F","U","N","K","T","I","M","E"]
    if st.session_state.last_spin != "StayingAlive":
        segments.append("StayingAlive")

    # Calcul probabilités
    probs = compute_probabilities()

    # Si bankroll faible et probabilité faible → No Bets
    low_prob_segments = [seg for seg, p in probs.items() if p < 0.05]
    if bankroll < 0.5 * st.session_state.initial_bankroll and len(low_prob_segments) >= 5:
        mises = {seg: 0 for seg in segments}
        return "⚠️ No Bets (probabilité faible & bankroll bas)", mises

    # Martingale classique
    if gain == 0:
        st.session_state.current_bet *= 2
        mises = {seg: st.session_state.current_bet for seg in segments}
        return f"❌ Perte ➝ Doubler la mise à {st.session_state.current_bet:.2f}$ par segment", mises
    else:
        adjust_bet_for_bankroll()
        mises = {seg: st.session_state.current_bet for seg in segments}
        return f"✅ Gain ➝ Mise ajustée à {st.session_state.current_bet:.2f}$ par segment", mises

# -------------------------------
# INTERFACE STREAMLIT
# -------------------------------
st.title("🎰 Funky Time - Bot Martingale + No Bets")

multiplicateur = st.number_input("Multiplicateur (Top Slot)", 1, 100, 1)

# Entrée historique
st.subheader("📥 Entrer l'historique des spins")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("1"): add_to_pending("1", multiplicateur)
    if st.button("Bar"): add_to_pending("Bar", multiplicateur)
    if st.button("Disco"): add_to_pending("Disco", multiplicateur)
    if st.button("VIPDisco"): add_to_pending("VIPDisco", multiplicateur)
with col2:
    if st.button("StayingAlive"): add_to_pending("StayingAlive", multiplicateur)
    if st.button("P"): add_to_pending("P", multiplicateur)
    if st.button("L"): add_to_pending("L", multiplicateur)
    if st.button("A"): add_to_pending("A", multiplicateur)
with col3:
    if st.button("Y"): add_to_pending("Y", multiplicateur)
    if st.button("F"): add_to_pending("F", multiplicateur)
    if st.button("U"): add_to_pending("U", multiplicateur)
    if st.button("N"): add_to_pending("N", multiplicateur)
with col4:
    if st.button("K"): add_to_pending("K", multiplicateur)
    if st.button("T"): add_to_pending("T", multiplicateur)
    if st.button("I"): add_to_pending("I", multiplicateur)
    if st.button("M"): add_to_pending("M", multiplicateur)
    if st.button("E"): add_to_pending("E", multiplicateur)

if st.button("✅ Fin historique et commence calcul"):
    process_history()
    st.success("Historique calculé ✅")

# Live spins
if st.session_state.history_done:
    st.subheader("🎯 Entrer le spin live")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("1 (live)"): st.session_state.pending_result = "1"
        if st.button("Bar (live)"): st.session_state.pending_result = "Bar"
        if st.button("Disco (live)"): st.session_state.pending_result = "Disco"
        if st.button("VIPDisco (live)"): st.session_state.pending_result = "VIPDisco"
    with col2:
        if st.button("StayingAlive (live)"): st.session_state.pending_result = "StayingAlive"
        if st.button("P (live)"): st.session_state.pending_result = "P"
        if st.button("L (live)"): st.session_state.pending_result = "L"
        if st.button("A (live)"): st.session_state.pending_result = "A"
    with col3:
        if st.button("Y (live)"): st.session_state.pending_result = "Y"
        if st.button("F (live)"): st.session_state.pending_result = "F"
        if st.button("U (live)"): st.session_state.pending_result = "U"
        if st.button("N (live)"): st.session_state.pending_result = "N"
    with col4:
        if st.button("K (live)"): st.session_state.pending_result = "K"
        if st.button("T (live)"): st.session_state.pending_result = "T"
        if st.button("I (live)"): st.session_state.pending_result = "I"
        if st.button("M (live)"): st.session_state.pending_result = "M"
        if st.button("E (live)"): st.session_state.pending_result = "E"

    if st.session_state.pending_result:
        suggestion = process_spin(st.session_state.pending_result, multiplicateur)
        st.success(suggestion)
        st.session_state.pending_result = None

# Affichage
st.metric("💰 Bankroll actuelle", f"{st.session_state.bankroll:.2f} $")

if st.session_state.history:
    st.subheader("📜 Historique complet")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True)
    st.line_chart(df.set_index("Spin")["Bankroll"])

if st.session_state.next_mises:
    st.subheader("📌 Répartition des mises conseillées pour le prochain spin")
    mises_df = pd.DataFrame(list(st.session_state.next_mises.items()), columns=["Segment", "Mise ($)"])
    st.dataframe(mises_df, use_container_width=True)
    st.info(f"🎯 Mise totale conseillée : **{mises_df['Mise ($)'].sum():.2f} $**")
