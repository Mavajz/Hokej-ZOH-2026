import streamlit as st
import pandas as pd
import numpy as np
import random
from functools import cmp_to_key

# --- 1. KONFIGURACE ---
st.set_page_config(page_title="ZOH 2026 Simulator", layout="wide", page_icon="🏒")

# --- 2. DATA (Zkalibrováno po dohrání skupiny A) ---
team_powers = {
    "Kanada": 99, "USA": 98, "Švédsko": 92, "Finsko": 88, 
    "Slovensko": 85, "Švýcarsko": 85, "Česko": 83, "Německo": 72, 
    "Lotyšsko": 63, "Dánsko": 59, "Itálie": 38, "Francie": 35
}

real_results = { 
    ("Slovensko", "Finsko"): (4, 1, "REG"),
    ("Švédsko", "Itálie"): (5, 2, "REG"),
    ("Švýcarsko", "Francie"): (4, 0, "REG"),
    ("Česko", "Kanada"): (0, 5, "REG"),
    ("Lotyšsko", "USA"): (1, 5, "REG"),
    ("Německo", "Dánsko"): (3, 1, "REG"),
    ("Finsko", "Švédsko"): (4, 1, "REG"),
    ("Itálie", "Slovensko"): (2, 3, "REG"),
    ("Francie", "Česko"): (3, 6, "REG"),
    ("Kanada", "Švýcarsko"): (5, 1, "REG"),
    ("Německo", "Lotyšsko"): (3, 4, "REG"),
    ("Švédsko", "Slovensko"): (5, 3, "REG"),
    ("Finsko", "Itálie"): (11, 0, "REG"),
    ("USA", "Dánsko"): (6, 3, "REG"),
    ("Švýcarsko", "Česko"): (4, 3, "PP") # NOVÝ VÝSLEDEK
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
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.3);
        border-radius: 10px; padding: 12px; margin-bottom: 12px; 
        display: flex; justify-content: space-between; align-items: center;
    }
    .team-n { font-weight: bold; font-size: 1.1em; width: 42%; }
    .score-n { 
        background: #ff4b4b; color: white !important; font-weight: 900; 
        font-size: 1.4em; padding: 4px 15px; border-radius: 6px;
        min-width: 90px; text-align: center;
    }
    .ot-label { font-size: 0.55em; display: block; line-height: 1; opacity: 0.9; font-weight: bold; color: white; }
    .bracket-card {
        background: rgba(255, 75, 75, 0.1); border-left: 5px solid #ff4b4b;
        padding: 10px; margin-bottom: 10px; border-radius: 4px; font-size: 0.95em;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIKA SIMULACE ---
def sim_match(t1, t2, m_seed):
    if (t1, t2) in real_results: return real_results[(t1, t2)]
    if (t2, t1) in real_results: 
        r = real_results[(t2, t1)]; return r[1], r[0], r[2]
    
    random.seed(m_seed); np.random.seed(m_seed)
    p1, p2 = team_powers[t1], team_powers[t2]
    avg = 2.6
    s1 = np.random.poisson(avg * (p1 / p2)**0.5)
    s2 = np.random.poisson(avg * (p2 / p1)**0.5)
    
    rtype = "REG"
    if s1 == s2:
        rtype = "PP" if random.random() < 0.5 else "SN"
        if random.random() < (p1/(p1+p2)): s1 += 1
        else: s2 += 1
    return s1, s2, rtype

def get_iihf_rankings(group_teams, group_matches):
    stats = {t: {"B": 0, "GF": 0, "GA": 0, "h2h": {}} for t in group_teams}
    for m in group_matches:
        t1, t2, s1, s2, rt = m["t1"], m["t2"], m["s1"], m["s2"], m["rt"]
        stats[t1]["GF"] += s1; stats[t1]["GA"] += s2
        stats[t2]["GF"] += s2; stats[t2]["GA"] += s1
        stats[t1]["h2h"][t2] = 3 if (s1 > s2 and rt == "REG") else (2 if s1 > s2 else (1 if rt != "REG" else 0))
        stats[t2]["h2h"][t1] = 3 if (s2 > s1 and rt == "REG") else (2 if s2 > s1 else (1 if rt != "REG" else 0))
        if rt == "REG":
            if s1 > s2: stats[t1]["B"] += 3
            else: stats[t2]["B"] += 3
        else:
            if s1 > s2: stats[t1]["B"] += 2; stats[t2]["B"] += 1
            else: stats[t2]["B"] += 2; stats[t1]["B"] += 1
    def compare_teams(t1, t2):
        if stats[t1]["B"] != stats[t2]["B"]: return stats[t1]["B"] - stats[t2]["B"]
        if stats[t1]["h2h"].get(t2, 0) > stats[t2]["h2h"].get(t1, 0): return 1
        if stats[t1]["h2h"].get(t2, 0) < stats[t2]["h2h"].get(t1, 0): return -1
        return (stats[t1]["GF"] - stats[t1]["GA"]) - (stats[t2]["GF"] - stats[t2]["GA"])
    return sorted(group_teams, key=cmp_to_key(compare_teams), reverse=True), stats

@st.cache_data
def run_tourney_cached(seed):
    matches = []
    # Základní skupina
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
    for i, (d, t1, t2) in enumerate(sched):
        s1, s2, rt = sim_match(t1, t2, seed + i)
        matches.append({"d": d, "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "G"})

    # GLOBAL SEEDING (D1-D12)
    group_rankings = []
    for gn, tms in groups_def.items():
        g_m = [m for m in matches if m["t1"] in tms]
        sorted_tms, stats = get_iihf_rankings(tms, g_m)
        for i, t in enumerate(sorted_tms):
            group_rankings.append({"T": t, "Pos": i+1, "B": stats[t]["B"], "D": stats[t]["GF"]-stats[t]["GA"], "GF": stats[t]["GF"]})

    # Rozdělení na 1., 2., 3. a 4. místa pro cross-group srovnání
    d1_3 = sorted([x for x in group_rankings if x["Pos"]==1], key=lambda x: (x["B"], x["D"], x["GF"]), reverse=True)
    d4_6 = sorted([x for x in group_rankings if x["Pos"]==2], key=lambda x: (x["B"], x["D"], x["GF"]), reverse=True)
    d7_9 = sorted([x for x in group_rankings if x["Pos"]==3], key=lambda x: (x["B"], x["D"], x["GF"]), reverse=True)
    d10_12 = sorted([x for x in group_rankings if x["Pos"]==4], key=lambda x: (x["B"], x["D"], x["GF"]), reverse=True)
    
    sd = [x["T"] for x in d1_3 + d4_6 + d7_9 + d10_12]

    # Playoff
    # Osmifinále (OF): D5 vs D12 (OF1), D6 vs D11 (OF2), D7 vs D10 (OF3), D8 vs D9 (OF4)
    of_pairs = [(4,11), (5,10), (6,9), (7,8)]
    of_results = {}
    for i, (h, l) in enumerate(of_pairs):
        t1, t2 = sd[h], sd[l]
        s1, s2, rt = sim_match(t1, t2, seed + 100 + i)
        winner = t1 if s1 > s2 else t2
        of_results[i] = winner
        matches.append({"d": "Úterý 17. 2.", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"OF{i+1}", "w": winner})

    # Čtvrtfinále (ČF): D1 vs winner OF4, D2 vs winner OF3, D3 vs winner OF2, D4 vs winner OF1
    qf_pairs = [(0, 3), (1, 2), (2, 1), (3, 0)] # Indexy: (D1-4, Index of_results)
    qf_winners = []
    for i, (d_idx, of_idx) in enumerate(qf_pairs):
        t1, t2 = sd[d_idx], of_results[of_idx]
        s1, s2, rt = sim_match(t1, t2, seed + 200 + i)
        winner = t1 if s1 > s2 else t2
        qf_winners.append(winner)
        matches.append({"d": "Středa 18. 2.", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"ČF{i+1}", "w": winner})

    # Semifinále (SF)
    sf_winners, sf_losers = [], []
    for i, (a, b) in enumerate([(qf_winners[0], qf_winners[3]), (qf_winners[1], qf_winners[2])]):
        s1, s2, rt = sim_match(a, b, seed + 300 + i)
        w, l = (a, b) if s1 > s2 else (b, a)
        sf_winners.append(w); sf_losers.append(l)
        matches.append({"d": "Pátek 20. 2.", "t1": a, "t2": b, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"SF{i+1}", "w": w})

    # Bronz
    s1, s2, rt = sim_match(sf_losers[0], sf_losers[1], seed + 400)
    bronze_w = sf_losers[0] if s1 > s2 else sf_losers[1]
    matches.append({"d": "Sobota 21. 2.", "t1": sf_losers[0], "t2": sf_losers[1], "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": "BRONZ", "w": bronze_w})

    # Finále
    s1, s2, rt = sim_match(sf_winners[0], sf_winners[1], seed + 500)
    gold_w = sf_winners[0] if s1 > s2 else sf_winners[1]
    matches.append({"d": "Neděle 22. 2.", "t1": sf_winners[0], "t2": sf_winners[1], "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": "FINÁLE", "w": gold_w})
    
    return matches

# --- 5. STATISTIKA ---
@st.cache_data
def get_mc_stats(n_sims=10000):
    res_stats = {t: {"Gold": 0, "Silver": 0, "Bronze": 0, "G_Seeds": [], "M_Seeds": []} for t in team_powers}
    for i in range(1, n_sims + 1):
        tourney = run_tourney_cached(i)
        gw = tourney[-1]["w"]
        sw = tourney[-1]["t1"] if tourney[-1]["w"] == tourney[-1]["t2"] else tourney[-1]["t2"]
        bw = tourney[-2]["w"]
        res_stats[gw]["Gold"] += 1; res_stats[sw]["Silver"] += 1; res_stats[bw]["Bronze"] += 1
        res_stats[gw]["G_Seeds"].append(i)
        for t in [gw, sw, bw]: res_stats[t]["M_Seeds"].append(i)
    df = pd.DataFrame.from_dict(res_stats, orient='index')
    df["Zlato"] = (df["Gold"] / n_sims * 100)
    df["Stříbro"] = (df["Silver"] / n_sims * 100)
    df["Bronz"] = (df["Bronze"] / n_sims * 100)
    df["Celkem medaile"] = ((df["Gold"] + df["Silver"] + df["Bronze"]) / n_sims * 100)
    return df.sort_values("Zlato", ascending=False), res_stats

# --- 6. UI ---
tab1, tab2, tab3 = st.tabs(["Simulace", "Prediktor", "Hledač zázraků"])

with tab1:
    c_ctrl1, c_ctrl2 = st.columns([1, 4])
    with c_ctrl1: seed = st.number_input("ID Simulace (1-10000)", 1, 10000, 1)
    with c_ctrl2: sel_date = st.select_slider("Časová osa turnaje", options=dates_list)
    all_m = run_tourney_cached(seed); date_idx = dates_list.index(sel_date)
    today = [m for m in all_m if m["d"] == sel_date]
    if today:
        cols = st.columns(2)
        for i, m in enumerate(today):
            with cols[i % 2]:
                # V UI v tab1 zobrazujeme PP/SN pod skóre
                label = f"<span class='ot-label'>{m['rt']}</span>" if m["rt"] != "REG" else ""
                st.markdown(f"<div class='match-box'><div class='team-n'>{m['t1']}</div><div class='score-n'>{m['s1']}:{m['s2']}{label}</div><div class='team-n' style='text-align:right;'>{m['t2']}</div></div>", unsafe_allow_html=True)
    else: st.info("Dnes se nehrají žádné zápasy.")
    st.markdown("---")
    if date_idx <= 4:
        col_a, col_b, col_c = st.columns(3); cols = {"A": col_a, "B": col_b, "C": col_c}
        for gn, teams in groups_def.items():
            g_m = [m for m in all_m if m["stg"]=="G" and m["t1"] in teams and dates_list.index(m["d"]) <= date_idx]
            sorted_tms, g_stats = get_iihf_rankings(teams, g_m)
            df_g = pd.DataFrame([{"Tým": t, "B": g_stats[t]["B"], "Skóre": f"{g_stats[t]['GF']}:{g_stats[t]['GA']}"} for t in sorted_tms])
            df_g.index += 1
            with cols[gn]: st.write(f"**Skupina {gn}**"); st.table(df_g)
    else:
        c_of, c_qf, c_sf, c_fin = st.columns(4); po = [m for m in all_m if dates_list.index(m["d"]) <= date_idx and m["stg"]=="PO"]
        # Osmifinále
        with c_of:
            st.write("**Osmifinále**")
            for m in [x for x in po if "OF" in x["lbl"]]:
                label = f" ({x['rt']})" if x["rt"] != "REG" else ""
                st.markdown(f"<div class='bracket-card'>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}{label}</b></div>", unsafe_allow_html=True)
        # Čtvrtfinále
        with c_qf:
            st.write("**Čtvrtfinále**")
            for m in [x for x in po if "ČF" in x["lbl"]]:
                label = f" ({x['rt']})" if x["rt"] != "REG" else ""
                st.markdown(f"<div class='bracket-card'>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}{label}</b></div>", unsafe_allow_html=True)
        # Semifinále
        with c_sf:
            st.write("**Semifinále**")
            for m in [x for x in po if "SF" in x["lbl"]]:
                label = f" ({x['rt']})" if x["rt"] != "REG" else ""
                st.markdown(f"<div class='bracket-card'>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}{label}</b></div>", unsafe_allow_html=True)
        # Medaile
        with c_fin:
            st.write("**Medaile**")
            for m in [x for x in po if x["lbl"] in ["BRONZ", "FINÁLE"]]:
                label = f" ({x['rt']})" if x["rt"] != "REG" else ""
                st.markdown(f"<div class='bracket-card'><b>{m['lbl']}</b><br>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}{label}</b></div>", unsafe_allow_html=True)

with tab2:
    st.header("Prediktor (10 000 simulací)")
    mc_df, _ = get_mc_stats(10000)
    from matplotlib.colors import LinearSegmentedColormap
    custom_cmap = LinearSegmentedColormap.from_list("custom_green", ["#ffffff", "#00ff00"])
    st.dataframe(mc_df[["Zlato", "Stříbro", "Bronz", "Celkem medaile"]].style.background_gradient(cmap=custom_cmap, axis=0).format("{:.2f} %"), use_container_width=True, height=455)

with tab3:
    st.header("🔍 Hledač hokejových zázraků")
    _, mc_raw = get_mc_stats(10000)
    look_team = st.selectbox("Vyber tým", options=list(team_powers.keys()))
    look_type = st.radio("Co hledáme?", ["Pouze Zlato", "Jakoukoliv medaili"])
    seeds_found = mc_raw[look_team]["G_Seeds"] if "Zlato" in look_type else mc_raw[look_team]["M_Seeds"]
    if seeds_found:
        st.success(f"Tým **{look_team}** splnil tento cíl v **{len(seeds_found)}** simulacích.")
        if st.button("Vygeneruj ID zázraku"): st.info(f"Zkus zadat Seed ID: **{random.choice(seeds_found)}**")
    else: st.error(f"Tým {look_team} v 10 000 simulacích tento cíl nesplnil.")
