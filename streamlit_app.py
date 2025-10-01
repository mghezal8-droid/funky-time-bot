# streamlit_app.py
import streamlit as st
import pandas as pd

# =========================
# CONFIG / PAYOUTS
# =========================
PAYOUTS = {
    "1": 2,
    "Bar": 20,
    "Disco": 5,
    # Lettres PLAY F U N K T I M E
    "P": 25, "L": 25, "A": 25, "Y": 25,
    "F": 25, "U": 25, "N": 25, "K": 25,
    "T": 25, "I": 25, "M": 25, "E": 25,
    "StayingAlive": 0,
    "VIPDisco": 0
}

SEGMENT_COUNTS = {
    "1": 28,
    "Bar": 6,
    "Disco": 3,
    "P": 2, "L": 2, "A": 2, "Y": 2,
    "F": 2, "U": 2, "N": 2, "K": 2,
    "T": 2, "I": 2, "M": 2, "E": 2,
    "StayingAlive": 2,
    "VIPDisco": 1
}
TOTAL_SEGMENTS = sum(SEGMENT_COUNTS.values())
BONUS_SEGMENTS = ["StayingAlive", "VIPDisco"]
LETTERS = list("PLAYFUNKTIME")
ALL_SEGMENTS = ["1", "Bar", "Disco"] + LETTERS + BONUS_SEGMENTS

# ===========================
# SESSION STATE
# ===========================
st.set_page_config(page_title="Funky Time Bot", layout="centered")
if "history" not in st.session_state: st.session_state.history = []
if "bankroll" not in st.session_state: st.session_state.bankroll = 200.0
if "last_strategy" not in st.session_state: st.session_state.last_strategy = {}
if "last_strategy_name" not in st.session_state: st.session_state.last_strategy_name = None
if "strategy_repeat_count" not in st.session_state: st.session_state.strategy_repeat_count = 0
if "martingale_loss" not in st.session_state: st.session_state.martingale_loss = 0
if "skip_bonus" not in st.session_state: st.session_state.skip_bonus = None

# ===========================
# Helpers
# ===========================
def get_unit(bankroll: float):
    if bankroll < 200: return 1
    elif bankroll < 500: return 2
    elif bankroll < 1000: return 4
    else: return 10

def compute_probabilities(history):
    counts = {seg: 0 for seg in ALL_SEGMENTS}
    total_hist = len(history)
    for spin in history:
        seg = spin["result"].split("x")[0].strip()
        if seg in counts: counts[seg] += 1
    prob_hist = {seg: counts[seg]/total_hist for seg in ALL_SEGMENTS} if total_hist>0 else {seg:0 for seg in ALL_SEGMENTS}
    prob_theo = {seg: SEGMENT_COUNTS[seg]/TOTAL_SEGMENTS for seg in ALL_SEGMENTS}
    probs = {seg:0.5*(prob_hist.get(seg,0)+prob_theo.get(seg,0)) for seg in ALL_SEGMENTS}
    return probs

# ===========================
# STRATEGIES
# ===========================
def martingale_one(bankroll):
    unit = get_unit(bankroll)
    mise = unit * (2 ** st.session_state.martingale_loss)
    mise = min(mise, bankroll)
    return {"1": round(mise,2)}, "Martingale 1"

def god_mode(bankroll):
    unit = get_unit(bankroll)
    strat = {"Bar": 2*unit, "Disco": 1*unit}
    for l in LETTERS: strat[l] = 1*unit
    return strat, "God Mode"

def god_mode_bonus(bankroll):
    unit = get_unit(bankroll)
    strat = {"Bar": 0.8*unit, "Disco": 0.4*unit}
    for l in LETTERS: strat[l] = 0.4*unit
    for b in BONUS_SEGMENTS:
        if st.session_state.skip_bonus == b: continue
        strat[b] = 0.2*unit
    return strat, "God Mode + Bonus"

def one_plus_letters_bonus(bankroll):
    unit = get_unit(bankroll)
    strat = {}
    for l in LETTERS: strat[l] = 0.4*unit
    strat["Bar"] = 1*unit
    strat["Disco"] = 1*unit
    for b in BONUS_SEGMENTS:
        if st.session_state.skip_bonus == b: continue
        strat[b] = 0.2*unit
    return strat, "1 + Letters + Bonus"

# ===========================
# Choix stratégie
# ===========================
def expected_score_strategy(strat_dict, probs):
    return sum(probs.get(seg,0) * mise for seg, mise in strat_dict.items())

def choose_strategy(history, bankroll):
    # Priorité martingale si perte précédente
    if st.session_state.martingale_loss > 0:
        strat, name = martingale_one(bankroll)
        st.session_state.strategy_repeat_count = 0
        st.session_state.last_strategy_name = name
        return strat, name
    # Calcul probabilités
    probs = compute_probabilities(history)
    candidates = [
        god_mode(bankroll),
        god_mode_bonus(bankroll),
        one_plus_letters_bonus(bankroll)
    ]
    best = {}; best_name = "No Bets"; best_score = -1
    for strat_dict, name in candidates:
        score = expected_score_strategy(strat_dict, probs)
        if name == st.session_state.last_strategy_name and st.session_state.strategy_repeat_count >= 2:
            score *= 0.5
        if score > best_score:
            best_score = score; best = strat_dict; best_name = name
    if best_score < 0.05: best = {}; best_name = "No Bets"
    if best_name == st.session_state.last_strategy_name:
        st.session_state.strategy_repeat_count += 1
    else:
        st.session_state.strategy_repeat_count = 0
    st.session_state.last_strategy_name = best_name
    return best, best_name

# ===========================
# Calcul gain
# ===========================
def calculate_gain(spin_text, strategy):
    s = spin_text.replace("X","x")
    parts = s.split("x")
    seg = parts[0].strip()
    mult = int(parts[1]) if len(parts)>1 and parts[1].strip().isdigit() else 1
    gain = 0.0
    for bet_seg, mise in strategy.items():
        if bet_seg != seg: continue
        if bet_seg in BONUS_SEGMENTS:
            gain += mise * mult + mise
        else:
            payout = PAYOUTS.get(bet_seg,0)
            gain += mise * payout * mult
    return round(gain,2)

# ===========================
# UI / Streamlit
# ===========================
st.title("🎵 Funky Time Bot — Optimisé Long Terme")
st.sidebar.header("⚙️ Paramètres")
st.session_state.bankroll = st.sidebar.number_input(
    "Bankroll initiale ($)", min_value=50.0, max_value=5000.0,
    value=float(st.session_state.bankroll), step=1.0
)

# Historique
st.subheader("📜 Phase 1 — Entrer l'historique")
hist_input = st.text_input("Entrer un spin (ex: 'F', '1 x7', 'VIPDisco x20')", "")
if st.button("Ajouter à l'historique") and hist_input.strip():
    st.session_state.history.append({"result": hist_input.strip(), "gain":0.0})
    seg = hist_input.split("x")[0].strip()
    st.session_state.skip_bonus = seg if seg in BONUS_SEGMENTS else None
    st.success(f"Ajouté : {hist_input.strip()}")

if st.session_state.history:
    st.write(pd.DataFrame(st.session_state.history))
else:
    st.info("Ajoute des spins pour construire l'historique.")

# Bouton pour générer stratégie
if st.button("✅ Historique terminé — Générer suggestion"):
    st.session_state.last_strategy, st.session_state.last_strategy_name = choose_strategy(
        st.session_state.history, st.session_state.bankroll
    )
    st.success("Suggestion générée (voir bloc 'Suggestion prochain spin').")

# Bloc suggestion
st.subheader("💡 Suggestion prochain spin")
if st.session_state.last_strategy_name:
    st.write(f"Stratégie : **{st.session_state.last_strategy_name}**")
    if st.session_state.last_strategy:
        df_sugg = pd.DataFrame(list(st.session_state.last_strategy.items()), columns=["Segment","Mise ($)"])
        st.table(df_sugg)
else:
    st.write("Aucune suggestion (historique incomplet ou No Bets).")
st.write(f"💰 Bankroll actuelle : **{round(st.session_state.bankroll,2)} $**")

# Live spin
st.subheader("🎯 Phase Live — Entrer le résultat du spin")
live_spin = st.text_input("Résultat live (ex: '1 x7', 'Bar', 'F x5')", "")
if st.button("Résultat Spin Live"):
    if not st.session_state.last_strategy:
        st.warning("Aucune stratégie active — clique sur 'Historique terminé' pour générer une suggestion.")
    elif not live_spin.strip():
        st.warning("Entre le résultat du spin (ex: 'F x5' ou '1 x7').")
    else:
        gain = calculate_gain(live_spin.strip(), st.session_state.last_strategy)
        total_bet = sum(st.session_state.last_strategy.values())
        net = round(gain - total_bet,2)
        st.session_state.bankroll += net
        st.success(f"Résultat : {live_spin.strip()} → Gain net : {net} $ | Bankroll : {round(st.session_state.bankroll,2)} $")
        # reset martingale si hit
        if "1" in st.session_state.last_strategy and live_spin.startswith("1"):
            st.session_state.martingale_loss = 0
        elif st.session_state.last_strategy_name=="Martingale 1" and net<0:
            st.session_state.martingale_loss += 1
        # générer nouvelle suggestion
        st.session_state.last_strategy, st.session_state.last_strategy_name = choose_strategy(
            st.session_state.history, st.session_state.bankroll
        )
