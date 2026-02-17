import streamlit as st
import pandas as pd
import numpy as np
import random
from functools import cmp_to_key

# --- 1. KONFIGURACE ---
st.set_page_config(page_title="ZOH 2026 Simulator", layout="wide", page_icon="🏒")

# --- 2. DATA (Rekalibrace před Čtvrtfinále - 17. 2. 2026) ---
team_powers = {
    "Kanada": 99, "USA": 97, "Finsko": 91, "Švédsko": 90, 
    "Švýcarsko": 87, "Slovensko": 84, "Německo": 84, "Česko": 83, # GER s SVK jsou teď nastejno
    "Lotyšsko": 66, "Dánsko": 62, "Francie": 38, "Itálie": 35
}

real_results = { 
    ("Slovensko", "Finsko"): (4, 1, "REG"), ("Švédsko", "Itálie"): (5, 2, "REG"),
    ("Švýcarsko", "Francie"): (4, 0, "REG"), ("Česko", "Kanada"): (0, 5, "REG"),
    ("Lotyšsko", "USA"): (1, 5, "REG"), ("Německo", "Dánsko"): (3, 1, "REG"),
    ("Finsko", "Švédsko"): (4, 1, "REG"), ("Itálie", "Slovensko"): (2, 3, "REG"),
    ("Francie", "Česko"): (3, 6, "REG"), ("Kanada", "Švýcarsko"): (5, 1, "REG"),
    ("Německo", "Lotyšsko"): (3, 4, "REG"), ("Švédsko", "Slovensko"): (5, 3, "REG"),
    ("Finsko", "Itálie"): (11, 0, "REG"), ("USA", "Dánsko"): (6, 3, "REG"),
    ("Švýcarsko", "Česko"): (4, 3, "PP"), ("Kanada", "Francie"): (10, 2, "REG"),
    ("Dánsko", "Lotyšsko"): (4, 2, "REG"), ("USA", "Německo"): (5, 1, "REG"),
    # OSMIFINÁLE
    ("Německo", "Francie"): (5, 1, "REG"), # NOVÉ
    ("Švýcarsko", "Itálie"): (3, 0, "REG")  # NOVÉ
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

# --- 4. LOGIKA ---

def sim_match(t1, t2, match_seed, is_playoff=False):
    if not is_playoff:
        if (t1, t2) in real_results: return real_results[(t1, t2)]
        if (t2, t1) in real_results: 
            r = real_results[(t2, t1)]; return r[1], r[0], r[2]
    
    curr_rng = np.random.RandomState(match_seed)
    p1, p2 = team_powers[t1], team_powers[t2]
    avg = 2.7
    s1 = curr_rng.poisson(avg * (p1 / p2)**1.15)
    s2 = curr_rng.poisson(avg * (p2 / p1)**1.15)
    
    rtype = "REG"
    if s1 == s2:
        rtype = "PP" if curr_rng.rand() < 0.5 else "SN"
        if curr_rng.rand() < (p1/(p1+p2)): s1 += 1
        else: s2 += 1
    return s1, s2, rtype

def get_iihf_rankings(group_teams, group_matches):
    full_stats = {t: {"B": 0, "GF": 0, "GA": 0} for t in group_teams}
    for m in group_matches:
        t1, t2, s1, s2, rt = m["t1"], m["t2"], m["s1"], m["s2"], m["rt"]
        full_stats[t1]["GF"] += s1; full_stats[t1]["GA"] += s2
        full_stats[t2]["GF"] += s2; full_stats[t2]["GA"] += s1
        if rt == "REG":
            if s1 > s2: full_stats[t1]["B"] += 3
            else: full_stats[t2]["B"] += 3
        else:
            if s1 > s2: full_stats[t1]["B"] += 2; full_stats[t2]["B"] += 1
            else: full_stats[t2]["B"] += 2; full_stats[t1]["B"] += 1

    def solve_tie(tied_teams):
        if len(tied_teams) <= 1: return tied_teams
        mini_stats = {t: {"B": 0, "D": 0, "GF": 0} for t in tied_teams}
        for m in group_matches:
            if m["t1"] in tied_teams and m["t2"] in tied_teams:
                t1, t2, s1, s2, rt = m["t1"], m["t2"], m["s1"], m["s2"], m["rt"]
                mini_stats[t1]["GF"] += s1; mini_stats[t1]["D"] += (s1 - s2)
                mini_stats[t2]["GF"] += s2; mini_stats[t2]["D"] += (s2 - s1)
                if rt == "REG":
                    if s1 > s2: mini_stats[t1]["B"] += 3
                    else: mini_stats[t2]["B"] += 3
                else:
                    if s1 > s2: mini_stats[t1]["B"] += 2; mini_stats[t2]["B"] += 1
                    else: mini_stats[t2]["B"] += 2; mini_stats[t1]["B"] += 1
        return sorted(tied_teams, key=lambda t: (mini_stats[t]["B"], mini_stats[t]["D"], mini_stats[t]["GF"]), reverse=True)

    points_groups = {}
    for t in group_teams:
        b = full_stats[t]["B"]; points_groups.setdefault(b, []).append(t)
    sorted_final = []
    for b in sorted(points_groups.keys(), reverse=True):
        sorted_final.extend(solve_tie(points_groups[b]))
    return sorted_final, full_stats

@st.cache_data
def run_tourney_cached(seed):
    matches = []
    # Základní program
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
        s1, s2, rt = sim_match(t1, t2, seed * 100 + i, is_playoff=False)
        matches.append({"d": d, "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "G"})

    # GLOBAL SEEDING
    group_rankings = []
    for gn, tms in groups_def.items():
        g_m = [m for m in matches if m["t1"] in tms]
        sorted_tms, stats = get_iihf_rankings(tms, g_m)
        for i, t in enumerate(sorted_tms):
            group_rankings.append({"T": t, "Pos": i+1, "B": stats[t]["B"], "D": stats[t]["GF"]-stats[t]["GA"], "GF": stats[t]["GF"]})

    d1_3 = sorted([x for x in group_rankings if x["Pos"]==1], key=lambda x: (x["B"], x["D"], x["GF"]), reverse=True)
    d4_6 = sorted([x for x in group_rankings if x["Pos"]==2], key=lambda x: (x["B"], x["D"], x["GF"]), reverse=True)
    d7_9 = sorted([x for x in group_rankings if x["Pos"]==3], key=lambda x: (x["B"], x["D"], x["GF"]), reverse=True)
    d10_12 = sorted([x for x in group_rankings if x["Pos"]==4], key=lambda x: (x["B"], x["D"], x["GF"]), reverse=True)
    sd = [x["T"] for x in d1_3 + d4_6 + d7_9 + d10_12]

    # OF
    of_pairs = [("Švýcarsko", "Itálie"), ("Švédsko", "Lotyšsko"), ("Německo", "Francie"), ("Česko", "Dánsko")]
    of_res = {}
    for i, (t1, t2) in enumerate(of_pairs):
        s1, s2, rt = sim_match(t1, t2, seed * 100 + 20 + i, is_playoff=True)
        w = t1 if s1 > s2 else t2; of_res[i] = w
        matches.append({"d": "Úterý 17. 2.", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"OF{i+1}", "w": w})

    # ČF
    qf_pairs = [("Kanada", of_res[3]), ("USA", of_res[1]), ("Slovensko", of_res[2]), ("Finsko", of_res[0])]
    qf_winners = []
    for i, (t1, t2) in enumerate(qf_pairs):
        s1, s2, rt = sim_match(t1, t2, seed * 100 + 30 + i, is_playoff=True)
        w = t1 if s1 > s2 else t2; qf_winners.append(w)
        matches.append({"d": "Středa 18. 2.", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"ČF{i+1}", "w": w})

    # SF (Re-seeding)
    sf_seeded = sorted(qf_winners, key=lambda t: sd.index(t))
    sf_pairs = [(sf_seeded[0], sf_seeded[3]), (sf_seeded[1], sf_seeded[2])]
    sf_w, sf_l = [], []
    for i, (a, b) in enumerate(sf_pairs):
        s1, s2, rt = sim_match(a, b, seed * 100 + 40 + i, is_playoff=True)
        w, l = (a, b) if s1 > s2 else (b, a)
        sf_w.append(w); sf_l.append(l)
        matches.append({"d": "Pátek 20. 2.", "t1": a, "t2": b, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"SF{i+1}", "w": w})

    # Medaile
    s1, s2, rt = sim_match(sf_l[0], sf_l[1], seed * 100 + 50, is_playoff=True)
    matches.append({"d": "Sobota 21. 2.", "t1": sf_l[0], "t2": sf_l[1], "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": "BRONZ", "w": sf_l[0] if s1>s2 else sf_l[1]})
    s1, s2, rt = sim_match(sf_w[0], sf_w[1], seed * 100 + 60, is_playoff=True)
    matches.append({"d": "Neděle 22. 2.", "t1": sf_w[0], "t2": sf_w[1], "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": "FINÁLE", "w": sf_w[0] if s1>s2 else sf_w[1]})
    return matches

# --- 5. STATISTIKA ---
@st.cache_data
def get_mc_stats(n_sims=10000):
    res_stats = {t: {"Gold": 0, "Silver": 0, "Bronze": 0, "G_Seeds": [], "M_Seeds": []} for t in team_powers}
    for i in range(1, n_sims + 1):
        tourney = run_tourney_cached(i)
        gw = tourney[-1]["w"]; sw = tourney[-1]["t1"] if tourney[-1]["w"] == tourney[-1]["t2"] else tourney[-1]["t2"]; bw = tourney[-2]["w"]
        res_stats[gw]["Gold"] += 1; res_stats[sw]["Silver"] += 1; res_stats[bw]["Bronze"] += 1
        res_stats[gw]["G_Seeds"].append(i)
        for t in [gw, sw, bw]: res_stats[t]["M_Seeds"].append(i)
    df = pd.DataFrame.from_dict(res_stats, orient='index')
    df["🥇 Zlato"] = (df["Gold"] / n_sims * 100); df["🥈 Stříbro"] = (df["Silver"] / n_sims * 100)
    df["🥉 Bronz"] = (df["Bronze"] / n_sims * 100); df["Celkem medaile"] = ((df["Gold"] + df["Silver"] + df["Bronze"]) / n_sims * 100)
    return df.sort_values("🥇 Zlato", ascending=False), res_stats

# --- 6. UI ---
tab1, tab2, tab3 = st.tabs(["🎮 Simulace", "📊 Prediktor", "🔍 Hledač zázraků"])

with tab1:
    c1, c2 = st.columns([1, 4])
    with c1: seed = st.number_input("ID Simulace", 1, 10000, 1)
    with c2: sel_date = st.select_slider("Osa turnaje", options=dates_list, value="Úterý 17. 2.")
    all_m = run_tourney_cached(seed); date_idx = dates_list.index(sel_date)
    today = [m for m in all_m if m["d"] == sel_date]
    if today:
        cols = st.columns(2)
        for i, m in enumerate(today):
            with cols[i % 2]:
                label = f"<span class='ot-label'>{m['rt']}</span>" if m["rt"] != "REG" else ""
                st.markdown(f"<div class='match-box'><div class='team-n'>{m['t1']}</div><div class='score-n'>{m['s1']}:{m['s2']}{label}</div><div class='team-n' style='text-align:right;'>{m['t2']}</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    if date_idx <= 4:
        cols_g = st.columns(3); mapping = {"A": cols_g[0], "B": cols_g[1], "C": cols_g[2]}
        for gn, tms in groups_def.items():
            g_m = [m for m in all_m if m["stg"]=="G" and m["t1"] in tms and dates_list.index(m["d"]) <= date_idx]
            sorted_tms, stats = get_iihf_rankings(tms, g_m)
            df_g = pd.DataFrame([{"Tým": t, "B": stats[t]["B"], "Skóre": f"{stats[t]['GF']}:{stats[t]['GA']}"} for t in sorted_tms])
            df_g.index += 1
            with mapping[gn]: st.write(f"**Skupina {gn}**"); st.table(df_g)
    else:
        c_of, c_qf, c_sf, c_fin = st.columns(4); po = [m for m in all_m if dates_list.index(m["d"]) <= date_idx and m["stg"]=="PO"]
        with c_of:
            st.write("**Osmifinále**")
            for m in [x for x in po if "OF" in x["lbl"]]:
                lbl = f" ({m['rt']})" if m['rt'] != "REG" else ""; st.markdown(f"<div class='bracket-card'>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}{lbl}</b></div>", unsafe_allow_html=True)
        with c_qf:
            st.write("**Čtvrtfinále**")
            for m in [x for x in po if "ČF" in x["lbl"]]:
                lbl = f" ({m['rt']})" if m['rt'] != "REG" else ""; st.markdown(f"<div class='bracket-card'>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}{lbl}</b></div>", unsafe_allow_html=True)
        with c_sf:
            st.write("**Semifinále**")
            for m in [x for x in po if "SF" in x["lbl"]]:
                lbl = f" ({m['rt']})" if m['rt'] != "REG" else ""; st.markdown(f"<div class='bracket-card'>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}{lbl}</b></div>", unsafe_allow_html=True)
        with c_fin:
            st.write("**Medaile**")
            for m in [x for x in po if x["lbl"] in ["BRONZ", "FINÁLE"]]:
                lbl = f" ({m['rt']})" if m['rt'] != "REG" else ""; st.markdown(f"<div class='bracket-card'><b>{m['lbl']}</b><br>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}{lbl}</b></div>", unsafe_allow_html=True)

with tab2:
    st.header("📈 Prediktor")
    mc_df, _ = get_mc_stats(10000)
    from matplotlib.colors import LinearSegmentedColormap
    custom_cmap = LinearSegmentedColormap.from_list("custom_green", ["#ffffff", "#00ff00"])
    st.dataframe(mc_df[["🥇 Zlato", "🥈 Stříbro", "🥉 Bronz", "Celkem medaile"]].style.background_gradient(cmap=custom_cmap, axis=0).format("{:.2f} %"), use_container_width=True, height=455)

with tab3:
    st.header("🔍 Hledač zázraků")
    _, mc_raw = get_mc_stats(10000)
    look_t = st.selectbox("Vyber tým", options=list(team_powers.keys()))
    look_ty = st.radio("Cíl", ["🥇 Pouze Zlato", "🥉 Jakákoliv medaile"])
    f_seeds = mc_raw[look_t]["G_Seeds"] if "Zlato" in look_ty else mc_raw[look_t]["M_Seeds"]
    if f_seeds:
        st.success(f"Tým **{look_t}** splnil tento cíl v **{len(f_seeds)}** simulacích.")
        if st.button("Vygeneruj náhodné ID"): st.info(f"Zázrak: Seed **{random.choice(f_seeds)}**")
    else: st.error("Nenalezeno.")
