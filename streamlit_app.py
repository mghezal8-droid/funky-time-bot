import streamlit as st
import pandas as pd

st.set_page_config(page_title="Funky Time Bot - Auto-ajustement", layout="wide")

# --- Initialisation ---
if "history" not in st.session_state:
    st.session_state.history = []
if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame(columns=["Spin","Résultat","Multiplicateur","Total Mise","Gain Net","Bankroll"])
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 150
if "next_mises" not in st.session_state:
    st.session_state.next_mises = {}
if "mode_live" not in st.session_state:
    st.session_state.mode_live = False

# --- Segments ---
segments_letters = list("PLAYFUNKTIME")
segments_others = ["1","Bar","Disco","VIPDisco","StayingAlive"]
segments = segments_others + segments_letters

# --- Fonctions ---
def calc_gain_net(result, mises, mult):
    total_mise = sum(mises.values())
    if result in segments_letters:
        gain = mises[result]*25
        gain_net = gain - total_mise
    elif result=="StayingAlive":
        gain = mises[result]*mult
        gain_net = gain - total_mise
    else:
        gain_net = -total_mise
    return gain_net, total_mise

def adjust_mises_dynamic(bankroll,last_mises,last_gain,bankroll_base=150):
    """
    Ajustement automatique des mises selon bankroll + martingale
    """
    next_mises = {}
    multiplier = max(1, round(bankroll/bankroll_base))
    for seg,mise in last_mises.items():
        if last_gain <= 0:
            mise_new = min(bankroll/2, mise*2)
            mise_new = max(1, mise_new)  # Minimum 1$
        else:
            mise_new = mise * multiplier
        next_mises[seg]=mise_new
    return next_mises

def suggest_strategy_dynamic(last_spin,last_gain,last_mises,bankroll):
    next_mises = adjust_mises_dynamic(bankroll,last_mises,last_gain)
    strategy = "No Bets" if sum(next_mises.values())==0 else "Martingale Dynamique Auto"
    return strategy, next_mises

def process_spin_dynamic(result,mult,last_spin_val,last_bankroll):
    mises = {seg:1 for seg in segments_letters}
    if last_spin_val != "StayingAlive":
        mises["StayingAlive"]=1
    gain_net,total_mise = calc_gain_net(result,mises,mult)
    new_bankroll = last_bankroll + gain_net
    strategy,next_mises = suggest_strategy_dynamic(result,gain_net,mises,new_bankroll)
    return gain_net,total_mise,new_bankroll,strategy,next_mises

# --- Interface ---
st.title("🎰 Funky Time Bot - Auto-ajustement Dynamique")

# --- Sidebar historique ---
st.sidebar.header("📥 Ajouter spin à l'historique")
mult_input = st.sidebar.number_input("Multiplicateur Top Slot / Staying Alive",min_value=1,value=1,step=1)

st.sidebar.subheader("Historique Spins")
for seg in segments:
    if st.sidebar.button(f"{seg} ➕ Historique"):
        spin_num = len(st.session_state.history)+1
        st.session_state.history.append({"Spin":spin_num,"Résultat":seg,"Multiplicateur":mult_input})
        st.session_state.results_df = pd.DataFrame(st.session_state.history)

if st.sidebar.button("🗑 Supprimer dernier spin"):
    if st.session_state.history:
        st.session_state.history.pop()
        st.session_state.results_df = pd.DataFrame(st.session_state.history)

if st.sidebar.button("✅ Fin historique et commencer"):
    bankroll = 150
    last_spin_val = None
    results=[]
    for spin in st.session_state.history:
        result = spin["Résultat"]
        mult = spin["Multiplicateur"]
        gain_net,total_mise,new_bankroll,strategy,next_mises = process_spin_dynamic(result,mult,last_spin_val,bankroll)
        results.append({
            "Spin":spin["Spin"],
            "Résultat":result,
            "Multiplicateur":mult,
            "Total Mise":total_mise,
            "Gain Net":gain_net,
            "Bankroll":new_bankroll
        })
        last_spin_val=result
        bankroll=new_bankroll
        st.session_state.next_mises = next_mises
    st.session_state.results_df = pd.DataFrame(results)
    st.session_state.mode_live=True

# --- Tableau historique ---
st.subheader("📜 Historique des spins")
if not st.session_state.results_df.empty:
    st.dataframe(st.session_state.results_df,use_container_width=True)
    st.line_chart(st.session_state.results_df.set_index("Spin")["Bankroll"])

# --- Mode live ---
if st.session_state.mode_live:
    st.subheader("🎯 Mode Live - spin par spin")
    mult_live = st.number_input("Multiplicateur Live",min_value=1,value=1,step=1)
    st.subheader("Cliquer sur un segment pour live spin")
    for seg in segments:
        if st.button(f"{seg} ➡️ Live Spin"):
            last_bankroll = st.session_state.results_df["Bankroll"].iloc[-1] if not st.session_state.results_df.empty else 150
            last_spin_val = st.session_state.results_df["Résultat"].iloc[-1] if not st.session_state.results_df.empty else None
            gain_net,total_mise,new_bankroll,strategy,next_mises = process_spin_dynamic(seg,mult_live,last_spin_val,last_bankroll)
            new_row = {
                "Spin":len(st.session_state.results_df)+1,
                "Résultat":seg,
                "Multiplicateur":mult_live,
                "Total Mise":total_mise,
                "Gain Net":gain_net,
                "Bankroll":new_bankroll
            }
            st.session_state.results_df = pd.concat([st.session_state.results_df,pd.DataFrame([new_row])],ignore_index=True)
            st.session_state.next_mises = next_mises
            st.success(f"Spin ajouté : {seg} x{mult_live} | Stratégie suggérée : {strategy}")

    if st.session_state.next_mises:
        st.subheader("📌 Mise conseillée pour le prochain spin")
        mises_df = pd.DataFrame(list(st.session_state.next_mises.items()),columns=["Segment","Mise ($)"])
        st.dataframe(mises_df,use_container_width=True)
        st.info(f"Mise totale conseillée : {mises_df['Mise ($)'].sum():.2f} $")
