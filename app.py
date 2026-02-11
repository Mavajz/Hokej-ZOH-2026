import streamlit as st
import pandas as pd
import numpy as np
import random

# --- 1. KONFIGURACE ---
st.set_page_config(page_title="ZOH 2026 Simulator", layout="wide", page_icon="🏒")

# --- 2. DATA ---
team_powers = {
    "Kanada": 96, "USA": 94, "Švédsko": 90, "Česko": 89,
    "Finsko": 85, "Slovensko": 83, "Švýcarsko": 82, "Německo": 76,
    "Dánsko": 60, "Lotyšsko": 58, "Itálie": 40, "Francie": 35
}

real_results = {
    ("Slovensko", "Finsko"): (4, 1, "REG"),
}

groups_def = {
    "A": ["Česko", "Francie", "Švýcarsko", "Kanada"],
    "B": ["Finsko", "Itálie", "Slovensko", "Švédsko"],
    "C": ["Dánsko", "Německo", "Lotyšsko", "USA"]
}

dates_list = ["Středa 11. 2.", "Čtvrtek 12. 2.", "Pátek 13. 2.", "Sobota 14. 2.", "Neděle 15. 2.",
              "Úterý 17. 2.", "Středa 18. 2.", "Pátek 20. 2.", "Sobota 21. 2.", "Neděle 22. 2."]

# --- 3. CSS DESIGN ---
st.markdown("""
<style>
    .match-box {
        background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px;
        padding: 10px 15px; margin-bottom: 10px; display: flex;
        justify-content: space-between; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .team-n { font-weight: bold; font-size: 1em; width: 40%; }
    .score-n { 
        background: #f1f3f5; color: #e03131; font-weight: 900; 
        font-size: 1.3em; padding: 2px 10px; border-radius: 5px;
        min-width: 65px; text-align: center;
    }
    .ot { font-size: 0.5em; color: #868e96; display: block; line-height: 1; }
    .bracket-card {
        background: #f8f9fa; border-left: 4px solid #ff4b4b;
        padding: 8px; margin-bottom: 8px; border-radius: 4px; font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)


# --- 4. LOGIKA SIMULACE ---
def sim_match(t1, t2, seed):
    if (t1, t2) in real_results: return real_results[(t1, t2)]
    if (t2, t1) in real_results: r = real_results[(t2, t1)]; return r[1], r[0], r[2]
    random.seed(seed + hash(t1) + hash(t2))
    p1, p2 = team_powers[t1], team_powers[t2]
    avg = 2.7
    s1, s2 = np.random.poisson(avg * (p1 / p2) ** 0.6), np.random.poisson(avg * (p2 / p1) ** 0.6)
    rtype = "REG"
    if s1 == s2:
        rtype = "OT";
        s1, s2 = (s1 + 1, s2) if random.random() < (p1 / (p1 + p2)) else (s1, s2 + 1)
    return s1, s2, rtype


def run_tourney(seed):
    # --- SKUPINY ---
    sched = [
        ("Středa 11. 2.", "Slovensko", "Finsko"), ("Středa 11. 2.", "Švédsko", "Itálie"),
        ("Čtvrtek 12. 2.", "Švýcarsko", "Francie"), ("Čtvrtek 12. 2.", "Česko", "Kanada"),
        ("Čtvrtek 12. 2.", "Lotyšsko", "USA"), ("Čtvrtek 12. 2.", "Německo", "Dánsko"),
        ("Pátek 13. 2.", "Finsko", "Švédsko"), ("Pátek 13. 2.", "Itálie", "Slovensko"),
        ("Pátek 13. 2.", "Francie", "Česko"), ("Pátek 13. 2.", "Kanada", "Švýcarsko"),
        ("Sobota 14. 2.", "Švédsko", "Slovensko"), ("Sobota 14. 2.", "Německo", "Lotyšsko"),
        ("Sobota 14. 2.", "Finsko", "Itálie"), ("Sobota 14. 2.", "USA", "Dánsko"),
        ("Neděle 15. 2.", "Švýcarsko", "Česko"), ("Neděle 15. 2.", "Kanada", "Francie"),
        ("Neděle 15. 2.", "Dánsko", "Lotyšsko"), ("Neděle 15. 2.", "USA", "Německo")
    ]
    matches, st = [], {t: {"B": 0, "GF": 0, "GA": 0} for t in team_powers}
    for d, t1, t2 in sched:
        s1, s2, rt = sim_match(t1, t2, seed)
        matches.append({"d": d, "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "G"})
        st[t1]["GF"] += s1;
        st[t1]["GA"] += s2;
        st[t2]["GF"] += s2;
        st[t2]["GA"] += s1
        if rt == "REG":
            if s1 > s2:
                st[t1]["B"] += 3
            else:
                st[t2]["B"] += 3
        else:
            if s1 > s2:
                st[t1]["B"] += 2; st[t2]["B"] += 1
            else:
                st[t2]["B"] += 2; st[t1]["B"] += 1

    # --- SEEDING (Ranking 1-12) ---
    rnk = []
    for gn, tms in groups_def.items():
        sorted_g = sorted(tms, key=lambda x: (st[x]["B"], st[x]["GF"] - st[x]["GA"]), reverse=True)
        for i, t in enumerate(sorted_g): rnk.append(
            {"T": t, "R": i + 1, "B": st[t]["B"], "D": st[t]["GF"] - st[t]["GA"]})
    w = sorted([x for x in rnk if x["R"] == 1], key=lambda x: (x["B"], x["D"]), reverse=True)
    r = sorted([x for x in rnk if x["R"] == 2], key=lambda x: (x["B"], x["D"]), reverse=True)
    o = sorted([x for x in rnk if x["R"] >= 3], key=lambda x: (x["B"], x["D"]), reverse=True)
    sd = [x["T"] for x in w + [r[0]] + r[1:] + o]

    # --- PLAY-OFF ---
    # Osmifinále (OF)
    of_w = {}
    for i, (h, l) in enumerate([(4, 11), (5, 10), (6, 9), (7, 8)]):
        t1, t2 = sd[h], sd[l];
        s1, s2, rt = sim_match(t1, t2, seed + 10)
        of_w[h] = t1 if s1 > s2 else t2
        matches.append(
            {"d": "Úterý 17. 2.", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"OF{i + 1}"})

    # Čtvrtfinále (ČF)
    qf_w = []
    for i, (h, l) in enumerate([(0, 7), (1, 6), (2, 5), (3, 4)]):
        t1, t2 = sd[h], of_w[l];
        s1, s2, rt = sim_match(t1, t2, seed + 20)
        qf_w.append(t1 if s1 > s2 else t2)
        matches.append(
            {"d": "Středa 18. 2.", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"ČF{i + 1}"})

    # Semifinále (SF)
    sf_w, sf_l = [], []
    for i, (a, b) in enumerate([(qf_w[1], qf_w[2]), (qf_w[3], qf_w[0])]):
        s1, s2, rt = sim_match(a, b, seed + 30)
        sf_w.append(a if s1 > s2 else b);
        sf_l.append(b if s1 > s2 else a)
        matches.append(
            {"d": "Pátek 20. 2.", "t1": a, "t2": b, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"SF{i + 1}"})

    # Medaile
    s1, s2, rt = sim_match(sf_l[0], sf_l[1], seed + 40)
    matches.append(
        {"d": "Sobota 21. 2.", "t1": sf_l[0], "t2": sf_l[1], "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": "BRONZ"})
    s1, s2, rt = sim_match(sf_w[0], sf_w[1], seed + 50)
    matches.append({"d": "Neděle 22. 2.", "t1": sf_w[0], "t2": sf_w[1], "s1": s1, "s2": s2, "rt": rt, "stg": "PO",
                    "lbl": "FINÁLE"})

    return matches


# --- 5. UI ZOBRAZENÍ ---
st.write("### ZOH 2026 Simulator")

c_ctrl1, c_ctrl2 = st.columns([1, 4])
with c_ctrl1: seed = st.number_input("Seed", 1, 10000, 1, label_visibility="collapsed")
with c_ctrl2: sel_date = st.select_slider("Osa", options=dates_list, label_visibility="collapsed")

all_m = run_tourney(seed)
date_idx = dates_list.index(sel_date)

# Horní panel - Dnešní zápasy (Grid 2x2)
today = [m for m in all_m if m["d"] == sel_date]
if today:
    rows = [today[i:i + 2] for i in range(0, len(today), 2)]
    for row in rows:
        cols = st.columns(2)
        for i, m in enumerate(row):
            with cols[i]:
                ot = "<span class='ot'>PP/SN</span>" if m["rt"] == "OT" else ""
                st.markdown(
                    f"<div class='match-box'><div class='team-n' style='text-align:right;'>{m['t1']}</div><div class='score-n'>{m['s1']}:{m['s2']}{ot}</div><div class='team-n' style='text-align:left;'>{m['t2']}</div></div>",
                    unsafe_allow_html=True)
else:
    st.info("Dnes volno.")

st.markdown("---")

# Spodní panel - Tabulky nebo Pavouk
if date_idx <= 4:
    col_a, col_b, col_c = st.columns(3)
    cols = {"A": col_a, "B": col_b, "C": col_c}
    for gn, teams in groups_def.items():
        st_d = {t: {"B": 0, "GF": 0, "GA": 0, "Z": 0} for t in teams}
        for m in [x for x in all_m if dates_list.index(x["d"]) <= date_idx and x["stg"] == "G" and x["t1"] in teams]:
            for t in [m["t1"], m["t2"]]:
                st_d[t]["Z"] += 1
                if t == m["t1"]:
                    st_d[t]["GF"] += m["s1"]; st_d[t]["GA"] += m["s2"]
                else:
                    st_d[t]["GF"] += m["s2"]; st_d[t]["GA"] += m["s1"]
                if m["rt"] == "REG":
                    if (t == m["t1"] and m["s1"] > m["s2"]) or (t == m["t2"] and m["s2"] > m["s1"]): st_d[t]["B"] += 3
                else:
                    if (t == m["t1"] and m["s1"] > m["s2"]) or (t == m["t2"] and m["s2"] > m["s1"]):
                        st_d[t]["B"] += 2
                    else:
                        st_d[t]["B"] += 1
        df = pd.DataFrame(
            [{"Tým": k, "Z": v["Z"], "B": v["B"], "Skóre": f"{v['GF']}:{v['GA']}", "Diff": v['GF'] - v['GA']} for k, v
             in st_d.items()]).sort_values(["B", "Diff"], ascending=False).reset_index(drop=True)
        df.index += 1
        with cols[gn]:
            st.write(f"**Skupina {gn}**"); st.table(df)
else:
    # --- PAVOUK PLAY-OFF (4 Sloupce) ---
    c_of, c_qf, c_sf, c_fin = st.columns(4)
    po = [m for m in all_m if dates_list.index(m["d"]) <= date_idx and m["stg"] == "PO"]

    with c_of:
        st.write("**Osmifinále**")
        for m in [x for x in po if "OF" in x["lbl"]]:
            st.markdown(
                f"<div class='bracket-card'><b>{m['t1']}</b> vs <b>{m['t2']}</b><br><span style='color:red'>{m['s1']}:{m['s2']}</span></div>",
                unsafe_allow_html=True)

    with c_qf:
        st.write("**Čtvrtfinále**")
        for m in [x for x in po if "ČF" in x["lbl"]]:
            st.markdown(
                f"<div class='bracket-card'><b>{m['t1']}</b> vs <b>{m['t2']}</b><br><span style='color:red'>{m['s1']}:{m['s2']}</span></div>",
                unsafe_allow_html=True)

    with c_sf:
        st.write("**Semifinále**")
        for m in [x for x in po if "SF" in x["lbl"]]:
            st.markdown(
                f"<div class='bracket-card'><b>{m['t1']}</b> vs <b>{m['t2']}</b><br><span style='color:red'>{m['s1']}:{m['s2']}</span></div>",
                unsafe_allow_html=True)

    with c_fin:
        st.write("**Finále / Bronz**")
        for m in [x for x in po if x["lbl"] in ["BRONZ", "FINÁLE"]]:
            icon = "🥇" if m["lbl"] == "FINÁLE" else "🥉"
            st.markdown(
                f"<div class='bracket-card'>{icon} <b>{m['t1']}</b> vs <b>{m['t2']}</b><br><span style='color:red'>{m['s1']}:{m['s2']}</span></div>",
                unsafe_allow_html=True)
