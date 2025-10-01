import streamlit as st
import pandas as pd

# -------------------------------
# CONFIG INITIALE
# -------------------------------
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 100  # bankroll initiale
if "base_bet" not in st.session_state:
    st.session_state.base_bet = 1    # mise de base par segment
if "current_bet" not in st.session_state:
    st.session_state.current_bet = 1
if "history" not in st.session_state:
    st.session_state.history = []    # historique des spins
if "last_spin" not in st.session_state:
    st.session_state.last_spin = None
if "next_mises" not in st.session_state:
    st.session_state.next_mises = {}
if "pending_result" not in st.session_state:
    st.session_state.pending_result = None

# Paiements standards (sans multiplicateurs)
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
# MISE À JOUR BANQUE + HISTORIQUE
# -------------------------------
def process_spin(resultat, multiplicateur):
    mise_totale = 0
    gain = 0

    # Segments joués (Martingale sur lettres + Staying Alive sauf si sorti précédemment)
    segments = ["P","L","A","Y","F","U","N","K","T","I","M","E"]
    if st.session_state.last_spin != "StayingAlive":
        segments.append("StayingAlive")

    # Mise appliquée
    mises = {seg: st.session_state.current_bet for seg in segments}
    mise_totale = sum(mises.values())

    # Calcul du gain si résultat correspond
    if resultat in mises:
        gain = mises[resultat] * payouts[resultat] * multiplicateur

    # Mise à jour bankroll
    st.session_state.bankroll += (gain - mise_totale)

    # Sauvegarde historique
    st.session_state.history.append({
        "Spin": len(st.session_state.history) + 1,
        "Résultat": resultat,
        "Multiplicateur": multiplicateur,
        "Mise Totale": mise_totale,
        "Gain": gain,
        "Bankroll": st.session_state.bankroll
    })

    # Ajustement stratégie pour le prochain tour
    suggestion, next_mises = strategy_suggestion(resultat, gain, mise_totale)
    st.session_state.last_spin = resultat
    st.session_state.next_mises = next_mises

    return suggestion

# -------------------------------
# STRATÉGIE CONSEILLÉE
# -------------------------------
def strategy_suggestion(resultat, gain, mise_totale):
    base = st.session_state.base_bet
    bankroll = st.session_state.bankroll

    # Segments à jouer
    segments = ["P","L","A","Y","F","U","N","K","T","I","M","E"]
    if st.session_state.last_spin != "StayingAlive":
        segments.append("StayingAlive")

    # Martingale : si perte ➝ doubler
    if gain == 0:
        st.session_state.current_bet *= 2
        mises = {seg: st.session_state.current_bet for seg in segments}
        return f"❌ Perte ➝ Doubler la mise à {st.session_state.current_bet}$ par segment", mises

    # Si hit : revenir à la mise de base
    else:
        st.session_state.current_bet = base
        # Ajuster la base si bankroll a doublé/triplé
        if bankroll >= 2 * 100:
            st.session_state.base_bet += 1
        if bankroll <= 50:  # Protection -50%
            st.session_state.base_bet = max(1, st.session_state.base_bet - 1)
        st.session_state.current_bet = st.session_state.base_bet
        mises = {seg: st.session_state.current_bet for seg in segments}
        return f"✅ Gain ➝ Revenir à {st.session_state.current_bet}$ par segment", mises

# -------------------------------
# INTERFACE STREAMLIT
# -------------------------------
st.title("🎰 Funky Time - Bot Martingale (simulateur live)")

# Entrée du multiplicateur
multiplicateur = st.number_input("Multiplicateur (Top Slot)", 1, 100, 1)

# Boutons pour entrer le résultat
st.subheader("➡️ Sélectionne le résultat du spin")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("1"): st.session_state.pending_result = "1"
    if st.button("Bar"): st.session_state.pending_result = "Bar"
    if st.button("Disco"): st.session_state.pending_result = "Disco"
    if st.button("VIPDisco"): st.session_state.pending_result = "VIPDisco"
with col2:
    if st.button("StayingAlive"): st.session_state.pending_result = "StayingAlive"
    if st.button("P"): st.session_state.pending_result = "P"
    if st.button("L"): st.session_state.pending_result = "L"
    if st.button("A"): st.session_state.pending_result = "A"
with col3:
    if st.button("Y"): st.session_state.pending_result = "Y"
    if st.button("F"): st.session_state.pending_result = "F"
    if st.button("U"): st.session_state.pending_result = "U"
    if st.button("N"): st.session_state.pending_result = "N"
with col4:
    if st.button("K"): st.session_state.pending_result = "K"
    if st.button("T"): st.session_state.pending_result = "T"
    if st.button("I"): st.session_state.pending_result = "I"
    if st.button("M"): st.session_state.pending_result = "M"
    if st.button("E"): st.session_state.pending_result = "E"

# Validation du spin
if st.session_state.pending_result:
    suggestion = process_spin(st.session_state.pending_result, multiplicateur)
    st.success(suggestion)
    st.session_state.pending_result = None

# Afficher bankroll
st.metric("💰 Bankroll actuelle", f"{st.session_state.bankroll:.2f} $")

# Afficher les mises exactes
if st.session_state.next_mises:
    st.subheader("📌 Répartition des mises conseillées")
    mises_df = pd.DataFrame(list(st.session_state.next_mises.items()), columns=["Segment", "Mise ($)"])
    st.dataframe(mises_df, use_container_width=True)
    st.info(f"🎯 Mise totale conseillée : **{mises_df['Mise ($)'].sum():.2f} $**")

# Historique
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.subheader("📜 Historique")
    st.dataframe(df, use_container_width=True)
    st.line_chart(df.set_index("Spin")["Bankroll"])
