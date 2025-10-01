# streamlit_app.py
import streamlit as st
import pandas as pd

# ================
# CONFIG / Payouts
# ================
# on définit les segments et les payouts fixes pour les segments "normaux"
PAYOUTS = {
    "1": 2,
    "Bar": 20,
    "Disco": 5,
    # Lettres (F U N K Y T I M E) - payout fixe 25:1
    "F": 25, "U": 25, "N": 25, "K": 25, "Y": 25, "T": 25, "I": 25, "M": 25, "E": 25,
    # bonus-type (on traitera VIP & StayingAlive comme bonus à multiplicateur manuel)
    # si tu veux des payouts fixes pour eux, on les ignore ici pour le bonus réel
}

BONUS_SEGMENTS = ["StayingAlive", "VIPDisco"]  # ces deux sont traitées comme bonus (multiplicateur manuel)
ALL_SEGMENTS = ["1", "Bar", "Disco"] + ["F","U","N","K","Y","T","I","M","E"] + BONUS_SEGMENTS

# ===========================
# Session state initialisation
# ===========================
st.set_page_config(page_title="Funky Time Bot", layout="centered")
if "history" not in st.session_state:
    st.session_state.history = []         # liste de dicts {"result": "F x5", "gain": ...}
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 200.0
if "last_strategy" not in st.session_state:
    st.session_state.last_strategy = {}
if "last_strategy_name" not in st.session_state:
    st.session_state.last_strategy_name = None
if "strategy_repeat_count" not in st.session_state:
    st.session_state.strategy_repeat_count = 0
if "martingale_loss" not in st.session_state:
    st.session_state.martingale_loss = 0
if "skip_bonus" not in st.session_state:
    st.session_state.skip_bonus = None

# ===========================
# Helpers: unité réaliste
# ===========================
def get_unit(bankroll: float):
    """Retourne une unité réaliste selon bankroll (1,2,4,10)."""
    if bankroll < 200:
        return 1
    elif bankroll < 500:
        return 2
    elif bankroll < 1000:
        return 4
    else:
        return 10

# ===========================
# Probabilités améliorées
# ===========================
def compute_probabilities(history):
    """Compte les occurrences et normalise en probas."""
    counts = {seg: 0 for seg in ALL_SEGMENTS}
    total = len(history)
    for spin in history:
        seg = spin["result"].split("x")[0].strip()
        if seg in counts:
            counts[seg] += 1
        else:
            # si l'utilisateur a entré un nom différent, on ignore
            counts.setdefault(seg, 0)
            counts[seg] += 1
            if seg not in ALL_SEGMENTS:
                # on l'ajoute temporairement
                pass
    if total == 0:
        # proba uniforme par défaut
        return {seg: 1/len(ALL_SEGMENTS) for seg in ALL_SEGMENTS}
    probs = {seg: counts.get(seg,0)/total for seg in ALL_SEGMENTS}
    # normaliser (juste au cas où)
    s = sum(probs.values())
    if s > 0:
        probs = {k: v/s for k,v in probs.items()}
    return probs

# ===========================
# Stratégies (Funky Time)
# ===========================
def martingale_one(bankroll):
    unit = get_unit(bankroll)
    mise = unit * (2 ** st.session_state.martingale_loss)
    # protéger contre dépassement bankroll
    mise = min(mise, bankroll)
    return {"1": round(mise,2)}, "Martingale 1"

def god_mode(bankroll):
    unit = get_unit(bankroll)
    # 2 unités sur Bar, 1 unité sur Disco, 1 unité sur chaque lettre
    strat = {"Bar": 2*unit, "Disco": 1*unit}
    for l in ["F","U","N","K","Y","T","I","M","E"]:
        strat[l] = 1*unit
    return strat, "God Mode"

def god_mode_bonus(bankroll):
    unit = get_unit(bankroll)
    # pondération: 2>letters/disco>bonus
    strat = {"Bar": 0.8*unit, "Disco": 0.4*unit}
    for l in ["F","U","N","K","Y","T","I","M","E"]:
        strat[l] = 0.4*unit
    # bonus segments petits apports (skip si dernier bonus)
    for b in BONUS_SEGMENTS:
        if st.session_state.skip_bonus == b:
            continue
        strat[b] = 0.2*unit
    return strat, "God Mode + Bonus"

def one_plus_bonus(bankroll):
    unit = get_unit(bankroll)
    strat = {}
    # on place des petites mises sur bonus+letters (les "autres")
    for l in ["F","U","N","K","Y","T","I","M","E"]:
        strat[l] = 0.5*unit
    for b in BONUS_SEGMENTS:
        if st.session_state.skip_bonus == b: continue
        strat[b] = 0.5*unit
    total_other = sum(strat.values())
    # règle pour break-even : mise sur 1 = total_other
    strat["1"] = round(total_other, 2)
    return strat, "1 + Bonus (Break-even si 1)"

# ===========================
# Choix stratégie (scoring équilibré)
# ===========================
def expected_score_strategy(strat_dict, probs):
    """Score simple = somme(proba(seg) * mise_sur_seg)."""
    return sum(probs.get(seg,0) * mise for seg, mise in strat_dict.items())

def choose_strategy(history, bankroll):
    # Martingale prioritaire si en cours
    if st.session_state.martingale_loss > 0:
        strat, name = martingale_one(bankroll)
        st.session_state.strategy_repeat_count = 0
        st.session_state.last_strategy_name = name
        return strat, name

    probs = compute_probabilities(history)
    candidates = [
        god_mode(bankroll),
        god_mode_bonus(bankroll),
        one_plus_bonus(bankroll)
    ]

    best = {}
    best_name = "No Bets"
    best_score = -1.0
    for strat_dict, name in candidates:
        score = expected_score_strategy(strat_dict, probs)
        # pénalité si répété >2 tours
        if name == st.session_state.last_strategy_name and st.session_state.strategy_repeat_count >= 2:
            score *= 0.5
        if score > best_score:
            best_score = score
            best = strat_dict
            best_name = name

    # seuil pour No Bets (si pas d'opportunité)
    if best_score < 0.05:
        best = {}
        best_name = "No Bets"

    # mise à jour répétition
    if best_name == st.session_state.last_strategy_name:
        st.session_state.strategy_repeat_count += 1
    else:
        st.session_state.strategy_repeat_count = 0
    st.session_state.last_strategy_name = best_name
    return best, best_name

# ===========================
# Calcul des gains (multiplicateur appliqué correctement)
# - pour segments "normaux" : gain = mise * payout * mult
# - pour bonus segments : gain = mise * mult + mise  (le résultat du bonus est un "xN")
# ===========================
def calculate_gain(spin_text, strategy):
    """
    spin_text examples: "F x5", "1 x7", "Bar", "VIPDisco x20"
    """
    # format tolerant (X ou x)
    s = spin_text.replace("X","x")
    parts = s.split("x")
    seg = parts[0].strip()
    mult = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else 1

    gain = 0.0
    for bet_seg, mise in strategy.items():
        if bet_seg != seg:
            continue
        # si c'est un bonus-type (multiplicateur variable)
        if bet_seg in BONUS_SEGMENTS:
            # gain = mise * mult + mise  (on suit la logique CT)
            gain += mise * mult + mise
        else:
            payout = PAYOUTS.get(bet_seg, 0)
            gain += mise * payout * mult
    return round(gain,2)

# ===========================
# AFFICHAGE / UI
# ===========================
st.title("🎵 Funky Time Bot — Streamlit")

# Sidebar : bankroll initiale
st.sidebar.header("⚙️ Paramètres")
st.session_state.bankroll = st.sidebar.number_input(
    "Bankroll initiale ($)",
    min_value=50.0, max_value=5000.0,
    value=float(st.session_state.bankroll), step=1.0
)

# Historique - saisie
st.subheader("📜 Phase 1 — Entrer l'historique (avant mises)")
col1, col2 = st.columns([3,1])
with col1:
    hist_input = st.text_input("Entrer un spin (ex: 'F', '1 x7', 'VIPDisco x20')", "")
with col2:
    add_hist = st.button("Ajouter à l'historique")
if add_hist and hist_input.strip():
    st.session_state.history.append({"result": hist_input.strip(), "gain": 0.0})
    # si c'est un bonus, on marque skip_bonus (on ne misera pas dessus le tour suivant)
    seg = hist_input.split("x")[0].strip()
    if seg in BONUS_SEGMENTS:
        st.session_state.skip_bonus = seg
    else:
        st.session_state.skip_bonus = None
    st.success(f"Ajouté : {hist_input.strip()}")

# Afficher historique (table)
if st.session_state.history:
    st.write(pd.DataFrame(st.session_state.history))
else:
    st.info("Ajoute des spins pour construire l'historique (phase préalable).")

# Bouton pour terminer l'historique et générer la 1ère suggestion
if st.button("✅ Historique terminé — Générer suggestion"):
    st.session_state.last_strategy, st.session_state.last_strategy_name = choose_strategy(
        st.session_state.history, st.session_state.bankroll
    )
    st.success("Suggestion générée (voir bloc 'Suggestion prochain spin').")

# Bloc suggestion / info
st.subheader("💡 Suggestion prochain spin")
if st.session_state.last_strategy_name:
    st.write(f"Stratégie : **{st.session_state.last_strategy_name}**")
else:
    st.write("Aucune suggestion (Historique incomplet ou No Bets).")

if st.session_state.last_strategy:
    df_sugg = pd.DataFrame(list(st.session_state.last_strategy.items()), columns=["Segment","Mise ($)"])
    st.table(df_sugg)
else:
    st.info("No Bets ou aucune mise suggérée.")

st.write(f"💰 Bankroll actuelle : **{round(st.session_state.bankroll,2)} $**")

# Live spin - entrer résultat (après avoir la suggestion)
st.subheader("🎯 Phase Live — Entrer le résultat du spin")
live_spin = st.text_input("Résultat live (ex: '1 x7' ou 'Bar' ou 'F x5')", "")
if st.button("Résultat Spin Live"):
    if not st.session_state.last_strategy:
        st.warning("Aucune stratégie active — clique sur 'Historique terminé' pour générer une suggestion.")
    elif not live_spin.strip():
        st.warning("Entre le résultat du spin (ex: 'F x5' ou '1 x7').")
    else:
        # calcul du gain selon la stratégie suggérée (celle affichée)
        gain = calculate_gain(live_spin.strip(), st.session_state.last_strategy)
        total_bet = sum(st.session_state.last_strategy.values())
        net = round(gain - total_bet, 2)
        st.session_state.bankroll = round(st.session_state.bankroll + net, 2)

        # Martingale update : si on misait sur 1, update martingale counter
        if "1" in st.session_state.last_strategy:
            if live_spin.strip().split("x")[0].strip() == "1":
                st.session_state.martingale_loss = 0
            else:
                st.session_state.martingale_loss += 1

        # Historique append
        st.session_state.history.append({"result": live_spin.strip(), "gain": gain})

        # skip_bonus logic : si bonus est sorti, on skip le bonus suivant
        seg_out = live_spin.strip().split("x")[0].strip()
        if seg_out in BONUS_SEGMENTS:
            st.session_state.skip_bonus = seg_out
        else:
            st.session_state.skip_bonus = None

        st.success(f"Résultat : {live_spin.strip()} → Gain brut: {gain} $ | Net: {net} $ | Bankroll: {st.session_state.bankroll} $")

        # recalculer stratégie pour le prochain spin
        st.session_state.last_strategy, st.session_state.last_strategy_name = choose_strategy(
            st.session_state.history, st.session_state.bankroll
        )

# Afficher petit résumé des probabilités (utile pour comprendre choix)
st.subheader("📈 Probabilités observées (historique)")
probs = compute_probabilities(st.session_state.history)
st.write(pd.DataFrame(list(probs.items()), columns=["Segment","Proba estimée"]))

# Footer
st.markdown("---")
st.markdown("⚠️ **Important** : outil d'aide, pas garantie de gain. Jouez responsablement.")
