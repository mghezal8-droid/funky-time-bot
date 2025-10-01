import streamlit as st
import pandas as pd

st.set_page_config(page_title="Funky Time Bot - Martingale Sécurisée", layout="wide")

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
if "base_option" not in st.session_state:
    st.session_state.base_option = 1  # 1 pour 13$, 2 pour 6.5$

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

def generate_mises_option(option=1):
    if option==1:
        mises = {seg:1 for seg in segments_letters}
        mises["StayingAlive"]=1
    else:
        mises = {seg:0.5 for seg in segments_letters}
        mises["StayingAlive"]=0.5
    return mises

def adjust_mises_martingale(last_gain, last_mises, bankroll):
    base_mises = generate_mises_option(st.session_state.base_option)
    if last_gain >= 0:
        next_mises = base_mises.copy()
        warning = ""
    else:
        next_mises = {seg:m*2 for seg,m in last_mises.items()}
        total_next = sum(next_mises.values())
        warning = ""
        if total_next > bankroll:
            scale = bankroll / total_next
            next_mises = {seg:m*scale for seg,m in next_mises.items()}
            warning = f"⚠️ Attention : bankroll insuffisant pour doubler, mise ajustée à {bankroll:.2f}$"
    return next_mises, warning

def process_spin(result,mult,mises_utilisees,last_bankroll,last_gain):
    gain_net,total_mise = calc_gain_net(result,mises_utilisees,mult)
    new_bankroll = last_bankroll + gain_net
    next_mises, warning = adjust_mises_martingale(gain_net, mises_utilisees, new_bankroll)
    strategy = "Martingale Lettres+Staying Alive"
    return gain_net,total_mise,new_bankroll,strategy,next_mises, warning

# --- Interface ---
st.title("🎰 Funky Time Bot - Martingale Sécurisée")

# --- Choix mise de base pour toute la simulation ---
st.sidebar.header("⚙️ Paramètres de simulation")
base_option = st.sidebar.radio("Mise de base :", ["13$ (1$ par segment)","6.5$ (0.5$ par segment)"])
st.session_state.base_option = 1 if base_option=="13$ (1$ par segment)" else 2

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
    last_mises = generate_mises_option(st.session_state.base_option)
    results=[]
    warning_msg=""
    for spin in st.session_state.history:
        result = spin["Résultat"]
        mult = spin["Multiplicateur"]
        mises_utilisees = last_mises.copy()
        if last_spin_val=="StayingAlive":
            mises_utilisees["StayingAlive"]=0
        gain_net,total_mise,new_bankroll,strategy,next_mises, warning = process_spin(result,mult,mises_utilisees,bankroll,last_gain)
        if warning:
            warning_msg = warning
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
    if warning_msg:
        st.warning(warning_msg)

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
            gain_net,total_mise,new_bankroll,strategy,next_mises, warning = process_spin(seg,mult_live,mises_utilisees,last_bankroll,last_gain)
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
            if warning:
                st.warning(warning)

    if st.session_state.next_mises:
        st.subheader("📌 Mise conseillée pour le prochain spin")
        mises_df = pd.DataFrame(list(st.session_state.next_mises.items()),columns=["Segment","Mise ($)"])
        st.dataframe(mises_df,use_container_width=True)
        st.info(f"Mise totale conseillée : {mises_df['Mise ($)'].sum():.2f} $")
