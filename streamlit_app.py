import streamlit as st
import pandas as pd

st.set_page_config(page_title="Funky Time Bot - Martingale Base", layout="wide")

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
if "last_spin_val" not in st.session_state:
    st.session_state.last_spin_val = None
if "last_gain" not in st.session_state:
    st.session_state.last_gain = 0

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

def adjust_mises_after_spin(last_gain, bank_base=150):
    """
    Martingale : doubler après perte, revenir à base après gain
    """
    base_mises = {seg:1 for seg in segments_letters}
    base_mises["StayingAlive"] = 1
    if last_gain < 0:
        # Perte → double la mise
        next_mises = {seg:m*2 for seg,m in base_mises.items()}
    else:
        # Gain → retour à la base
        next_mises = base_mises.copy()
    return next_mises

def process_spin(result,mult,mises_utilisees,last_bankroll):
    gain_net,total_mise = calc_gain_net(result,mises_utilisees,mult)
    new_bankroll = last_bankroll + gain_net
    next_mises = adjust_mises_after_spin(gain_net)
    strategy = "Martingale sur Lettres+Staying Alive"
    return gain_net,total_mise,new_bankroll,strategy,next_mises

# --- Interface ---
st.title("🎰 Funky Time Bot - Martingale Base 13$")

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
    last_gain = 0
    last_mises = {seg:1 for seg in segments_letters}
    last_mises["StayingAlive"]=1
    results=[]
    for spin in st.session_state.history:
        result = spin["Résultat"]
        mult = spin["Multiplicateur"]
        mises_utilisees = last_mises.copy()
        if last_spin_val=="StayingAlive":
            mises_utilisees["StayingAlive"]=0
        gain_net,total_mise,new_bankroll,strategy,next_mises = process_spin(result,mult,mises_utilisees,bankroll)
        results.append({
            "Spin":spin["Spin"],
            "Résultat":result,
            "Multiplicateur":mult,
            "Total Mise":total_mise,
            "Gain Net":gain_net,
            "Bankroll":new_bankroll
        })
        last_spin_val=result
        last_gain=gain_net
        last_mises=next_mises.copy()
        bankroll=new_bankroll
        st.session_state.next_mises=next_mises
    st.session_state.results_df = pd.DataFrame(results)
    st.session_state.mode_live=True
    st.session_state.last_spin_val=last_spin_val
    st.session_state.last_gain=last_gain

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
            last_gain = st.session_state.last_gain
            mises_utilisees = st.session_state.next_mises.copy()
            if last_spin_val=="StayingAlive":
                mises_utilisees["StayingAlive"]=0
            gain_net,total_mise,new_bankroll,strategy,next_mises = process_spin(seg,mult_live,mises_utilisees,last_bankroll)
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
            st.session_state.last_spin_val = seg
            st.session_state.last_gain = gain_net
            st.success(f"Spin ajouté : {seg} x{mult_live} | Stratégie suggérée : {strategy}")

    if st.session_state.next_mises:
        st.subheader("📌 Mise conseillée pour le prochain spin")
        mises_df = pd.DataFrame(list(st.session_state.next_mises.items()),columns=["Segment","Mise ($)"])
        st.dataframe(mises_df,use_container_width=True)
        st.info(f"Mise totale conseillée : {mises_df['Mise ($)'].sum():.2f} $")
