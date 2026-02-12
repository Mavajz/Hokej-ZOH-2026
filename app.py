import streamlit as st
import pandas as pd
import numpy as np
import random

# --- 1. KONFIGURACE ---
st.set_page_config(page_title="ZOH 2026 Simulator", layout="wide", page_icon="🏒")

# --- 2. DATA (Zkalibrováno podle kurzů) ---
team_powers = {
    "Kanada": 98, "USA": 97, "Švédsko": 92, "Česko": 89,
    "Finsko": 85, "Slovensko": 84, "Švýcarsko": 84, "Německo": 76,
    "Dánsko": 60, "Lotyšsko": 58, "Itálie": 40, "Francie": 33
}

real_results = {
    ("Slovensko", "Finsko"): (4, 1, "REG"),
    ("Švédsko", "Itálie"): (5, 2, "REG"),
    ("Švýcarsko", "Francie"): (4, 0, "REG")
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
        color: var(--text-color);
        border: 1px solid rgba(128, 128, 128, 0.3);
        border-radius: 10px; padding: 12px; margin-bottom: 12px; 
        display: flex; justify-content: space-between; align-items: center;
    }
    .team-n { font-weight: bold; font-size: 1.1em; width: 42%; }
    .score-n { 
        background: #ff4b4b; color: white !important; font-weight: 900; 
        font-size: 1.4em; padding: 4px 15px; border-radius: 6px;
        min-width: 80px; text-align: center;
    }
    .ot { font-size: 0.55em; display: block; line-height: 1; opacity: 0.8; }
    .bracket-card {
        background: rgba(255, 75, 75, 0.1); border-left: 5px solid #ff4b4b;
        color: var(--text-color); padding: 10px; margin-bottom: 10px; border-radius: 4px;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)


# --- 4. FUNKCE PRO SIMULACI A ŘAZENÍ ---

def sim_match(t1, t2, m_seed):
    if (t1, t2) in real_results: return real_results[(t1, t2)]
    if (t2, t1) in real_results:
        r = real_results[(t2, t1)]
        return r[1], r[0], r[2]
    random.seed(m_seed)
    np.random.seed(m_seed)
    p1, p2 = team_powers[t1], team_powers[t2]
    avg = 2.6
    s1 = np.random.poisson(avg * (p1 / p2) ** 0.5)
    s2 = np.random.poisson(avg * (p2 / p1) ** 0.5)
    rtype = "REG"
    if s1 == s2:
        rtype = "OT";
        s1, s2 = (s1 + 1, s2) if random.random() < (p1 / (p1 + p2)) else (s1, s2 + 1)
    return s1, s2, rtype


def get_iihf_rankings(group_teams, group_matches):
    """
    Seřadí týmy ve skupině podle IIHF pravidel:
    1. Body
    2. Vzájemný zápas (pro 2 týmy)
    3. Mini-tabulka (pro 3+ týmy - zjednodušeno na vzájemné zápasy)
    4. Celkový rozdíl skóre
    """
    stats = {t: {"B": 0, "GF": 0, "GA": 0, "h2h": {}} for t in group_teams}

    for m in group_matches:
        t1, t2, s1, s2, rt = m["t1"], m["t2"], m["s1"], m["s2"], m["rt"]
        stats[t1]["GF"] += s1;
        stats[t1]["GA"] += s2
        stats[t2]["GF"] += s2;
        stats[t2]["GA"] += s1

        # Uložení vzájemného výsledku pro tie-break
        stats[t1]["h2h"][t2] = 3 if (s1 > s2 and rt == "REG") else (2 if s1 > s2 else (1 if rt == "OT" else 0))
        stats[t2]["h2h"][t1] = 3 if (s2 > s1 and rt == "REG") else (2 if s2 > s1 else (1 if rt == "OT" else 0))

        if rt == "REG":
            if s1 > s2:
                stats[t1]["B"] += 3
            else:
                stats[t2]["B"] += 3
        else:
            if s1 > s2:
                stats[t1]["B"] += 2; stats[t2]["B"] += 1
            else:
                stats[t2]["B"] += 2; stats[t1]["B"] += 1

    # Funkce pro porovnání dvou týmů při rovnosti bodů
    def compare_teams(t1, t2):
        if stats[t1]["B"] != stats[t2]["B"]:
            return stats[t1]["B"] - stats[t2]["B"]
        # Vzájemný zápas
        if stats[t1]["h2h"].get(t2, 0) > stats[t2]["h2h"].get(t1, 0):
            return 1
        if stats[t1]["h2h"].get(t2, 0) < stats[t2]["h2h"].get(t1, 0):
            return -1
        # Skóre
        return (stats[t1]["GF"] - stats[t1]["GA"]) - (stats[t2]["GF"] - stats[t2]["GA"])

    from functools import cmp_to_key
    sorted_teams = sorted(group_teams, key=cmp_to_key(compare_teams), reverse=True)
    return sorted_teams, stats


@st.cache_data
def run_tourney_cached(seed):
    matches = []
    # Základní část
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

    # Výpočet pořadí ve skupinách
    all_group_stats = {}
    rnk_12 = []
    for gn, tms in groups_def.items():
        g_matches = [m for m in matches if m["t1"] in tms]
        sorted_tms, g_stats = get_iihf_rankings(tms, g_matches)
        all_group_stats.update(g_stats)
        for i, t in enumerate(sorted_tms):
            rnk_12.append({"T": t, "R": i + 1, "B": g_stats[t]["B"], "D": g_stats[t]["GF"] - g_stats[t]["GA"]})

    # Nasazení 1-12
    w = sorted([x for x in rnk_12 if x["R"] == 1], key=lambda x: (x["B"], x["D"]), reverse=True)
    r = sorted([x for x in rnk_12 if x["R"] == 2], key=lambda x: (x["B"], x["D"]), reverse=True)
    o = sorted([x for x in rnk_12 if x["R"] >= 3], key=lambda x: (x["B"], x["D"]), reverse=True)
    sd = [x["T"] for x in w + [r[0]] + r[1:] + o]

    # Playoff (OF, ČF, SF, Medal)
    of_w = {}
    for i, (h, l) in enumerate([(4, 11), (5, 10), (6, 9), (7, 8)]):
        t1, t2 = sd[h], sd[l];
        s1, s2, rt = sim_match(t1, t2, seed + 100 + i);
        of_w[h] = t1 if s1 > s2 else t2
        matches.append(
            {"d": "Úterý 17. 2.", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"OF{i + 1}",
             "w": of_w[h]})
    qf_w = []
    for i, (h, l) in enumerate([(0, 7), (1, 6), (2, 5), (3, 4)]):
        t1, t2 = sd[h], of_w[l];
        s1, s2, rt = sim_match(t1, t2, seed + 200 + i);
        w = t1 if s1 > s2 else t2;
        qf_w.append(w)
        matches.append(
            {"d": "Středa 18. 2.", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"ČF{i + 1}",
             "w": w})
    sf_w, sf_l = [], []
    for i, (a, b) in enumerate([(qf_w[1], qf_w[2]), (qf_w[3], qf_w[0])]):
        s1, s2, rt = sim_match(a, b, seed + 300 + i);
        w = a if s1 > s2 else b;
        l = b if s1 > s2 else a
        sf_w.append(w);
        sf_l.append(l)
        matches.append(
            {"d": "Pátek 20. 2.", "t1": a, "t2": b, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"SF{i + 1}",
             "w": w})
    s1, s2, rt = sim_match(sf_l[0], sf_l[1], seed + 400);
    bronze_w = sf_l[0] if s1 > s2 else sf_l[1]
    matches.append(
        {"d": "Sobota 21. 2.", "t1": sf_l[0], "t2": sf_l[1], "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": "BRONZ",
         "w": bronze_w})
    s1, s2, rt = sim_match(sf_w[0], sf_w[1], seed + 500);
    gold_w = sf_w[0] if s1 > s2 else sf_w[1]
    matches.append(
        {"d": "Neděle 22. 2.", "t1": sf_w[0], "t2": sf_w[1], "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": "FINÁLE",
         "w": gold_w})

    return matches


# --- 5. PREDIKTOR (10 000 simulací) ---
@st.cache_data
def get_monte_carlo(n_sims=10000):
    results = {t: {"Gold": 0, "Silver": 0, "Bronze": 0} for t in team_powers}
    for i in range(1, n_sims + 1):
        tourney = run_tourney_cached(i)
        results[tourney[-1]["w"]]["Gold"] += 1
        silver = tourney[-1]["t1"] if tourney[-1]["w"] == tourney[-1]["t2"] else tourney[-1]["t2"]
        results[silver]["Silver"] += 1
        results[tourney[-2]["w"]]["Bronze"] += 1

    df = pd.DataFrame.from_dict(results, orient='index')
    df["Zlato %"] = (df["Gold"] / n_sims * 100).apply(lambda x: f"{x:.2f} %")
    df["Stříbro %"] = (df["Silver"] / n_sims * 100).apply(lambda x: f"{x:.2f} %")
    df["Bronz %"] = (df["Bronze"] / n_sims * 100).apply(lambda x: f"{x:.2f} %")
    df["Celkem medaile %"] = ((df["Gold"] + df["Silver"] + df["Bronze"]) / n_sims * 100).apply(lambda x: f"{x:.2f} %")
    return df.sort_values("Gold", ascending=False)


# --- 6. UI ---
tab1, tab2 = st.tabs(["Simulace", "Prediktor"])

with tab1:
    c_ctrl1, c_ctrl2 = st.columns([1, 4])
    with c_ctrl1:
        seed = st.number_input("ID Simulace (1-10000)", 1, 10000, 1)
    with c_ctrl2:
        sel_date = st.select_slider("Časová osa", options=dates_list)
    all_m = run_tourney_cached(seed);
    date_idx = dates_list.index(sel_date)
    today = [m for m in all_m if m["d"] == sel_date]
    if today:
        rows = [today[i:i + 2] for i in range(0, len(today), 2)]
        for row in rows:
            cols = st.columns(2)
            for i, m in enumerate(row):
                with cols[i]:
                    ot = "<span class='ot'>PRODLOUŽENÍ</span>" if m["rt"] == "OT" else ""
                    st.markdown(
                        f"<div class='match-box'><div class='team-n'>{m['t1']}</div><div class='score-n'>{m['s1']}:{m['s2']}{ot}</div><div class='team-n' style='text-align:right;'>{m['t2']}</div></div>",
                        unsafe_allow_html=True)
    else:
        st.info("Dnes se nehrají žádné zápasy.")

    st.markdown("---")
    if date_idx <= 4:
        col_a, col_b, col_c = st.columns(3);
        cols = {"A": col_a, "B": col_b, "C": col_c}
        for gn, teams in groups_def.items():
            g_m = [m for m in all_m if m["stg"] == "G" and m["t1"] in teams and dates_list.index(m["d"]) <= date_idx]
            # Průběžné řazení k datu
            sorted_tms, g_stats = get_iihf_rankings(teams, g_m)
            df = pd.DataFrame(
                [{"Tým": t, "B": g_stats[t]["B"], "Skóre": f"{g_stats[t]['GF']}:{g_stats[t]['GA']}"} for t in
                 sorted_tms])
            df.index += 1
            with cols[gn]: st.write(f"**Skupina {gn}**"); st.table(df)
    else:
        c_of, c_qf, c_sf, c_fin = st.columns(4);
        po = [m for m in all_m if dates_list.index(m["d"]) <= date_idx and m["stg"] == "PO"]
        with c_of:
            st.write("**Osmifinále**")
            for m in [x for x in po if "OF" in x["lbl"]]: st.markdown(
                f"<div class='bracket-card'>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}</b></div>",
                unsafe_allow_html=True)
        with c_qf:
            st.write("**Čtvrtfinále**")
            for m in [x for x in po if "ČF" in x["lbl"]]: st.markdown(
                f"<div class='bracket-card'>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}</b></div>",
                unsafe_allow_html=True)
        with c_sf:
            st.write("**Semifinále**")
            for m in [x for x in po if "SF" in x["lbl"]]: st.markdown(
                f"<div class='bracket-card'>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}</b></div>",
                unsafe_allow_html=True)
        with c_fin:
            st.write("**Medaile**")
            for m in [x for x in po if x["lbl"] in ["BRONZ", "FINÁLE"]]: st.markdown(
                f"<div class='bracket-card'><b>{m['lbl']}</b><br>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}</b></div>",
                unsafe_allow_html=True)

with tab2:
    st.header("📈 Predikce (10 000 simulací)")
    with st.spinner('Počítám pravděpodobnosti...'): mc_df = get_monte_carlo(10000)
    st.table(mc_df[["Zlato %", "Stříbro %", "Bronz %", "Celkem medaile %"]])



