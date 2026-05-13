import streamlit as st
import pandas as pd
import numpy as np
import random
import itertools

# --- 1. KONFIGURACE ---
st.set_page_config(page_title="MS 2026 Simulator", layout="wide", page_icon="🏒")
APP_VERSION = "5.0-MS-TEMPLATE"

# --- 2. DATA (Týmy a orientační Power Ranking - nutno upravit podle kurzů!) ---
team_powers_db = {
    # Skupina A (Příklad)
    "Kanada": 99, "Švýcarsko": 88, "Česko": 85, "Slovensko": 82, 
    "Lotyšsko": 66, "Rakousko": 55, "Francie": 40, "Polsko": 30,
    # Skupina B (Příklad)
    "USA": 97, "Švédsko": 92, "Finsko": 91, "Německo": 84, 
    "Dánsko": 62, "Norsko": 58, "Kazachstán": 45, "Maďarsko": 25
}

groups_def = {
    "A": ["Kanada", "Švýcarsko", "Česko", "Slovensko", "Lotyšsko", "Rakousko", "Francie", "Polsko"],
    "B": ["USA", "Švédsko", "Finsko", "Německo", "Dánsko", "Norsko", "Kazachstán", "Maďarsko"]
}

# Zde budeme postupně zapisovat reálné výsledky turnaje
results_db = {}

# Vygenerování mock rozpisu, dokud nebudeme mít reálný
dates_list = [f"Den {i}" for i in range(1, 15)]

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
def sim_match(t1, t2, match_seed, powers, db, stage):
    if (t1, t2, stage) in db: return db[(t1, t2, stage)]
    if (t2, t1, stage) in db: r = db[(t2, t1, stage)]; return (r[1], r[0], r[2])
    
    curr_rng = np.random.RandomState(match_seed)
    p1, p2 = powers[t1], powers[t2]
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
def run_tourney_cached(seed, powers, db, version):
    matches = []
    
    # 1. GENERACE SKUPINOVÉ FÁZE (Každý s každým ve skupině)
    g_match_id = 0
    for gn, tms in groups_def.items():
        group_pairs = list(itertools.combinations(tms, 2))
        for t1, t2 in group_pairs:
            g_match_id += 1
            # Pro zjednodušení šablony dáváme fake datumy
            fake_date = dates_list[(g_match_id % 7)]
            s1, s2, rt = sim_match(t1, t2, seed * 1000 + g_match_id, powers, db, "G")
            matches.append({"d": fake_date, "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": f"G{gn}"})

    # 2. TABULKY A POSTUPUJÍCÍ
    group_rankings = {"A": [], "B": []}
    global_seed_stats = {} # Pro re-seeding v SF
    
    for gn in ["A", "B"]:
        g_m = [m for m in matches if m["stg"] == f"G{gn}"]
        sorted_tms, stats = get_iihf_rankings(groups_def[gn], g_m)
        group_rankings[gn] = sorted_tms
        for i, t in enumerate(sorted_tms):
            global_seed_stats[t] = {"Pos": i+1, "B": stats[t]["B"], "D": stats[t]["GF"]-stats[t]["GA"], "GF": stats[t]["GF"]}

    # ČTVRTFINÁLE (Křížem)
    A = group_rankings["A"]
    B = group_rankings["B"]
    qf_pairs = [(A[0], B[3]), (B[0], A[3]), (A[1], B[2]), (B[1], A[2])]
    qf_winners = []
    
    for i, (t1, t2) in enumerate(qf_pairs):
        s1, s2, rt = sim_match(t1, t2, seed * 1000 + 100 + i, powers, db, "PO")
        w = t1 if s1 > s2 else t2; qf_winners.append(w)
        matches.append({"d": "ČF Den", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"ČF{i+1}", "w": w})

    # SEMIFINÁLE (Re-seeding podle výkonů ze skupiny)
    # Třídící klíč MS: 1. Pozice ve skupině, 2. Body, 3. Rozdíl skóre, 4. Vstřelené góly
    def reseeding_key(t):
        s = global_seed_stats[t]
        return (-s["Pos"], s["B"], s["D"], s["GF"]) # -Pos protože chceme menší číslo (1. místo) brát jako nejlepší
    
    sf_seeded = sorted(qf_winners, key=reseeding_key, reverse=True)
    while len(sf_seeded) < 4: sf_seeded.append("TBD")
    
    sf_pairs = [(sf_seeded[0], sf_seeded[3]), (sf_seeded[1], sf_seeded[2])]
    sf_w, sf_l = [], []
    for i, (a, b) in enumerate(sf_pairs):
        s1, s2, rt = sim_match(a, b, seed * 1000 + 200 + i, powers, db, "PO")
        w, l = (a, b) if s1 > s2 else (b, a)
        sf_w.append(w); sf_l.append(l)
        matches.append({"d": "SF Den", "t1": a, "t2": b, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": f"SF{i+1}", "w": w})

    # MEDAILE
    if len(sf_l) >= 2:
        s1, s2, rt = sim_match(sf_l[0], sf_l[1], seed * 1000 + 300, powers, db, "PO")
        matches.append({"d": "Finálový víkend", "t1": sf_l[0], "t2": sf_l[1], "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": "BRONZ", "w": sf_l[0] if s1>s2 else sf_l[1]})
    
    if len(sf_w) >= 2:
        s1, s2, rt = sim_match(sf_w[0], sf_w[1], seed * 1000 + 400, powers, db, "PO")
        matches.append({"d": "Finálový víkend", "t1": sf_w[0], "t2": sf_w[1], "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": "FINÁLE", "w": sf_w[0] if s1>s2 else sf_w[1]})
    
    return matches

@st.cache_data
def get_mc_stats(n_sims, powers, db, version):
    res_stats = {t: {"Gold": 0, "Silver": 0, "Bronze": 0, "QF": 0, "G_Seeds": [], "M_Seeds": []} for t in powers}
    for i in range(1, n_sims + 1):
        tourney = run_tourney_cached(i, powers, db, version)
        try:
            # Zápis čtvrtfinalistů
            qf_matches = [m for m in tourney if "ČF" in m.get("lbl", "")]
            for m in qf_matches:
                res_stats[m["t1"]]["QF"] += 1
                res_stats[m["t2"]]["QF"] += 1

            fin = tourney[-1]; bronz = tourney[-2]
            gw = fin["w"]; sw = fin["t1"] if fin["w"] == fin["t2"] else fin["t2"]; bw = bronz["w"]
            res_stats[gw]["Gold"] += 1; res_stats[sw]["Silver"] += 1; res_stats[bw]["Bronze"] += 1
            res_stats[gw]["G_Seeds"].append(i)
            for t in [gw, sw, bw]: res_stats[t]["M_Seeds"].append(i)
        except: pass
    
    df = pd.DataFrame.from_dict(res_stats, orient='index')
    df["🛡️ Čtvrtfinále"] = (df["QF"] / n_sims * 100)
    df["🥇 Zlato"] = (df["Gold"] / n_sims * 100); df["🥈 Stříbro"] = (df["Silver"] / n_sims * 100)
    df["🥉 Bronz"] = (df["Bronze"] / n_sims * 100); df["Celkem medaile"] = ((df["Gold"] + df["Silver"] + df["Bronze"]) / n_sims * 100)
    return df.sort_values("🥇 Zlato", ascending=False), res_stats

# --- 6. UI ---
tab1, tab2, tab3 = st.tabs(["🎮 Simulace", "📊 Prediktor", "🔍 Hledač zázraků"])

with tab1:
    c1, c2 = st.columns([1, 4])
    with c1: seed = st.number_input("ID Simulace", 1, 10000, 1)
    with c2: sel_date = st.select_slider("Fáze turnaje", options=dates_list + ["ČF Den", "SF Den", "Finálový víkend"], value="Finálový víkend")
    all_m = run_tourney_cached(seed, team_powers_db, results_db, APP_VERSION)
    
    today = [m for m in all_m if m["d"] == sel_date]
    if today:
        cols = st.columns(2)
        for i, m in enumerate(today):
            with cols[i % 2]:
                label = f"<span class='ot-label'>{m['rt']}</span>" if m['rt'] != "REG" else ""
                st.markdown(f"<div class='match-box'><div class='team-n'>{m['t1']}</div><div class='score-n'>{m['s1']}:{m['s2']}{label}</div><div class='team-n' style='text-align:right;'>{m['t2']}</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Kreslení tabulek pro fázi Skupin
    if "Den" in sel_date and "ČF" not in sel_date and "SF" not in sel_date:
        cols_g = st.columns(2)
        for i, gn in enumerate(["A", "B"]):
            g_m = [m for m in all_m if m["stg"] == f"G{gn}"]
            sorted_tms, stats = get_iihf_rankings(groups_def[gn], g_m)
            df_g = pd.DataFrame([{"Tým": t, "Body": stats[t]["B"], "Skóre": f"{stats[t]['GF']}:{stats[t]['GA']}"} for t in sorted_tms])
            df_g.index += 1
            with cols_g[i]: st.write(f"**Skupina {gn}**"); st.table(df_g)
    else:
        # Pavouk pro Play-off
        c_qf, c_sf, c_fin = st.columns(3); po = [m for m in all_m if m["stg"]=="PO"]
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
    st.header("📈 Prediktor (10 000 simulací)")
    mc_df, _ = get_mc_stats(10000, team_powers_db, results_db, APP_VERSION)
    from matplotlib.colors import LinearSegmentedColormap
    custom_cmap = LinearSegmentedColormap.from_list("custom_green", ["#ffffff", "#00ff00"])
    # Přidán sloupec šance na postup ze skupiny (Čtvrtfinále)
    st.dataframe(mc_df[["🛡️ Čtvrtfinále", "🥇 Zlato", "🥈 Stříbro", "🥉 Bronz", "Celkem medaile"]].style.background_gradient(cmap=custom_cmap, axis=0).format("{:.2f} %"), use_container_width=True, height=600)

with tab3:
    st.header("🔍 Hledač zázraků")
    _, mc_raw = get_mc_stats(10000, team_powers_db, results_db, APP_VERSION)
    look_t = st.selectbox("Vyber tým", options=list(team_powers_db.keys()))
    look_ty = st.radio("Cíl", ["🥇 Pouze Zlato", "🥉 Jakákoliv medaile"])
    f_seeds = mc_raw[look_t]["G_Seeds"] if "Zlato" in look_ty else mc_raw[look_t]["M_Seeds"]
    if f_seeds:
        st.success(f"Tým **{look_t}** splnil tento cíl v **{len(f_seeds)}** simulacích.")
        if st.button("Vygeneruj náhodné ID"): st.info(f"Zázrak: Seed **{random.choice(f_seeds)}**")
    else: st.error("Tento tým v 10 000 simulacích na tento cíl nedosáhl.")
