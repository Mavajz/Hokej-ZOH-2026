import streamlit as st
import pandas as pd
import numpy as np
import random

# --- 1. KONFIGURACE ---
st.set_page_config(page_title="MS 2026 Simulator | PRO Analytics", layout="wide", page_icon="🏒")
APP_VERSION = "11.2-SYNTAX-FIX"

# --- 2. DATA (Aktualizováno po 6. hracím dni) ---
team_powers_db = {
    # Skupina A
    "USA": {"OFF": 89, "DEF": 84, "SKILL": 96},            
    "Finsko": {"OFF": 93, "DEF": 95, "SKILL": 89},         
    "Švýcarsko": {"OFF": 99, "DEF": 95, "SKILL": 92},      
    "Německo": {"OFF": 81, "DEF": 86, "SKILL": 84},        
    "Lotyšsko": {"OFF": 67, "DEF": 77, "SKILL": 72},       
    "Rakousko": {"OFF": 65, "DEF": 58, "SKILL": 60},       
    "Velká Británie": {"OFF": 38, "DEF": 35, "SKILL": 35}, 
    "Maďarsko": {"OFF": 49, "DEF": 47, "SKILL": 40},       
    
    # Skupina B
    "Kanada": {"OFF": 99, "DEF": 89, "SKILL": 99},         
    "Švédsko": {"OFF": 92, "DEF": 90, "SKILL": 90},        
    "Česko": {"OFF": 89, "DEF": 84, "SKILL": 94},          
    "Slovensko": {"OFF": 87, "DEF": 81, "SKILL": 88},      
    "Dánsko": {"OFF": 65, "DEF": 67, "SKILL": 65},         
    "Norsko": {"OFF": 69, "DEF": 68, "SKILL": 62},         
    "Slovinsko": {"OFF": 55, "DEF": 50, "SKILL": 55},      
    "Itálie": {"OFF": 45, "DEF": 55, "SKILL": 45}          
}

# Hvězdní hráči pro generátor střelců
top_scorers_db = {
    "USA": ["M. Tkachuk", "J. Hagens", "R. Leonard", "C. Caufield"],
    "Finsko": ["A. Barkov", "T. Teräväinen", "A. Lundell", "M. Rantanen"],
    "Švýcarsko": ["N. Hischier", "T. Meier", "K. Fiala", "R. Josi"],
    "Německo": ["D. Kahun", "M. Seider", "J. Peterka", "L. Reichel"],
    "Lotyšsko": ["R. Balcers", "K. Daugaviņš", "R. Ābols"],
    "Rakousko": ["M. Rossi", "D. Zwerger", "P. Huber"],
    "Velká Británie": ["L. Kirk", "B. Perlini", "C. Neilson"],
    "Maďarsko": ["V. Galló", "J. Hári", "B. Sebők"],
    "Kanada": ["C. McDavid", "S. Crosby", "C. Bedard", "J. Tavares"],
    "Švédsko": ["L. Raymond", "W. Nylander", "E. Pettersson", "A. Kempe"],
    "Česko": ["D. Pastrňák", "M. Nečas", "R. Červenka", "D. Kubalík"],
    "Slovensko": ["J. Slafkovský", "T. Tatar", "D. Dvorský", "P. Regenda"],
    "Dánsko": ["N. Ehlers", "O. Bjorkstrand", "F. Andersen"],
    "Norsko": ["M. Zuccarello", "P. Thoresen", "M. Olimb"],
    "Slovinsko": ["A. Kopitar", "J. Drozg", "R. Tičar"],
    "Itálie": ["T. Purdeller", "L. Frigo", "D. Kostner"]
}

groups_def = {
    "A": ["Finsko", "Německo", "Švýcarsko", "USA", "Rakousko", "Velká Británie", "Maďarsko", "Lotyšsko"],
    "B": ["Švédsko", "Kanada", "Dánsko", "Česko", "Slovensko", "Norsko", "Itálie", "Slovinsko"]
}

# REÁLNÉ VÝSLEDKY - Zapsán 1. - 6. den
results_db = {
    ("Finsko", "Německo", "GA"): (3, 1, "REG"),
    ("Švédsko", "Kanada", "GB"): (3, 5, "REG"),
    ("Švýcarsko", "USA", "GA"): (3, 1, "REG"),
    ("Dánsko", "Česko", "GB"): (1, 4, "REG"),
    ("Rakousko", "Velká Británie", "GA"): (5, 2, "REG"),
    ("Slovensko", "Norsko", "GB"): (2, 1, "REG"),
    ("Finsko", "Maďarsko", "GA"): (4, 1, "REG"),
    ("Kanada", "Itálie", "GB"): (6, 0, "REG"),
    ("Švýcarsko", "Lotyšsko", "GA"): (4, 2, "REG"),
    ("Slovinsko", "Česko", "GB"): (3, 2, "PP"),
    ("USA", "Velká Británie", "GA"): (5, 1, "REG"),
    ("Itálie", "Slovensko", "GB"): (1, 4, "REG"),
    ("Rakousko", "Maďarsko", "GA"): (4, 2, "REG"),
    ("Švédsko", "Dánsko", "GB"): (6, 2, "REG"),
    ("Německo", "Lotyšsko", "GA"): (0, 2, "REG"),
    ("Norsko", "Slovinsko", "GB"): (4, 0, "REG"),
    ("Finsko", "USA", "GA"): (6, 2, "REG"),
    ("Kanada", "Dánsko", "GB"): (5, 1, "REG"),
    ("Švýcarsko", "Německo", "GA"): (6, 1, "REG"),
    ("Česko", "Švédsko", "GB"): (4, 3, "REG"),
    ("Lotyšsko", "Rakousko", "GA"): (1, 3, "REG"),
    ("Itálie", "Norsko", "GB"): (0, 4, "REG"),
    ("Maďarsko", "Velká Británie", "GA"): (5, 0, "REG"), 
    ("Slovinsko", "Slovensko", "GB"): (4, 5, "SN"),
    ("Švýcarsko", "Rakousko", "GA"): (9, 0, "REG"),
    ("Česko", "Itálie", "GB"): (3, 1, "REG"),
    ("USA", "Německo", "GA"): (4, 3, "SN"),
    ("Švédsko", "Slovinsko", "GB"): (6, 0, "REG"),
}

date_mapping = {
    "Pátek 15. května": 1, "Sobota 16. května": 2, "Neděle 17. května": 3,
    "Pondělí 18. května": 4, "Úterý 19. května": 5, "Středa 20. května": 6,
    "Čtvrtek 21. května": 7, "Pátek 22. května": 8, "Sobota 23. května": 9,
    "Neděle 24. května": 10, "Pondělí 25. května": 11, "Úterý 26. května": 12,
    "Čtvrtek 28. května (ČF)": 14, "Sobota 30. května (SF)": 16, "Neděle 31. května (Medaile)": 17
}
dates_list = list(date_mapping.keys())

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

# --- POMOCNÉ FUNKCE ---
def get_team_form(team, matches, current_date_idx):
    past_matches = [m for m in matches if m["t1"] == team or m["t2"] == team]
    past_matches = [m for m in past_matches if dates_list.index(m["d"]) < current_date_idx]
    
    form_str = ""
    streak = 0
    for m in past_matches[-3:]:
        is_t1 = m["t1"] == team
        won = (is_t1 and m["s1"] > m["s2"]) or (not is_t1 and m["s2"] > m["s1"])
        form_str += "✅" if won else "❌"
        if won: streak = streak + 1 if streak > 0 else 1
        else: streak = streak - 1 if streak < 0 else -1
    return form_str, streak

def generate_scorers(team, goals, rng):
    if goals == 0: return []
    roster = top_scorers_db.get(team, ["Neznámý hráč"])
    weights = [40, 30] + [10] * max(0, len(roster) - 2)
    weights = weights[:len(roster)] 
    scorers = rng.choices(roster, weights=weights, k=goals)
    return scorers

def color_standings(row):
    if row.name <= 4:
        return ['background-color: rgba(0, 255, 0, 0.1)'] * len(row)
    elif row.name == 8:
        return ['background-color: rgba(255, 0, 0, 0.1)'] * len(row)
    else:
        return [''] * len(row)

# --- 4. LOGIKA PRO ANALYTICS ---
def sim_match(t1, t2, match_seed, powers, db, stage, current_day, last_played_dict, form_streak1=0, form_streak2=0):
    if (t1, t2, stage) in db: 
        res = db[(t1, t2, stage)]
        return res[0], res[1], res[2], [], []
    if (t2, t1, stage) in db: 
        res = db[(t2, t1, stage)]
        return res[1], res[0], res[2], [], []
    
    curr_rng = np.random.RandomState(match_seed)
    off1, def1, skill1 = powers[t1]["OFF"], powers[t1]["DEF"], powers[t1]["SKILL"]
    off2, def2, skill2 = powers[t2]["OFF"], powers[t2]["DEF"], powers[t2]["SKILL"]
    
    if t1 == "Švýcarsko": off1 *= 1.05; def1 *= 1.05
    if t2 == "Švýcarsko": off2 *= 1.05; def2 *= 1.05
        
    rest1 = current_day - last_played_dict.get(t1, -99)
    rest2 = current_day - last_played_dict.get(t2, -99)
    
    if rest1 == 1 and rest2 > 1: off1 *= 0.95; def1 *= 0.95 
    elif rest2 == 1 and rest1 > 1: off2 *= 0.95; def2 *= 0.95 

    if form_streak1 >= 2: off1 *= 1.04; def1 *= 1.04
    elif form_streak1 <= -2: off1 *= 0.96; def1 *= 0.96
    if form_streak2 >= 2: off2 *= 1.04; def2 *= 1.04
    elif form_streak2 <= -2: off2 *= 0.96; def2 *= 0.96

    if current_day >= 7 and stage.startswith("G"):
        off1 *= curr_rng.uniform(0.9, 1.1)
        off2 *= curr_rng.uniform(0.9, 1.1)

    base_avg = 2.4 if stage.startswith("G") else 2.0
    l1 = base_avg * (off1 / def2)**1.4
    l2 = base_avg * (off2 / def1)**1.4
    
    s1 = curr_rng.poisson(l1)
    s2 = curr_rng.poisson(l2)
    
    if s1 == s2 + 1:
        if curr_rng.rand() < 0.25: s1 += 1      
        elif curr_rng.rand() < 0.35: s2 += 1    
    elif s2 == s1 + 1:
        if curr_rng.rand() < 0.25: s2 += 1      
        elif curr_rng.rand() < 0.35: s1 += 1    

    rtype = "REG"
    if s1 == s2:
        rtype = "PP" if curr_rng.rand() < 0.65 else "SN"
        if curr_rng.rand() < (skill1 / (skill1 + skill2)): s1 += 1
        else: s2 += 1
            
    sc1 = generate_scorers(t1, s1, curr_rng)
    sc2 = generate_scorers(t2, s2, curr_rng)
    
    return s1, s2, rtype, sc1, sc2

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
    last_played = {} 
    
    sched = [
        ("Pátek 15. května", "Finsko", "Německo", "A"), ("Pátek 15. května", "Švédsko", "Kanada", "B"),
        ("Pátek 15. května", "Švýcarsko", "USA", "A"), ("Pátek 15. května", "Dánsko", "Česko", "B"),
        ("Sobota 16. května", "Rakousko", "Velká Británie", "A"), ("Sobota 16. května", "Slovensko", "Norsko", "B"),
        ("Sobota 16. května", "Finsko", "Maďarsko", "A"), ("Sobota 16. května", "Kanada", "Itálie", "B"),
        ("Sobota 16. května", "Švýcarsko", "Lotyšsko", "A"), ("Sobota 16. května", "Slovinsko", "Česko", "B"),
        ("Neděle 17. května", "USA", "Velká Británie", "A"), ("Neděle 17. května", "Itálie", "Slovensko", "B"),
        ("Neděle 17. května", "Rakousko", "Maďarsko", "A"), ("Neděle 17. května", "Švédsko", "Dánsko", "B"),
        ("Neděle 17. května", "Německo", "Lotyšsko", "A"), ("Neděle 17. května", "Norsko", "Slovinsko", "B"),
        ("Pondělí 18. května", "Finsko", "USA", "A"), ("Pondělí 18. května", "Kanada", "Dánsko", "B"),
        ("Pondělí 18. května", "Švýcarsko", "Německo", "A"), ("Pondělí 18. května", "Česko", "Švédsko", "B"),
        ("Úterý 19. května", "Lotyšsko", "Rakousko", "A"), ("Úterý 19. května", "Itálie", "Norsko", "B"),
        ("Úterý 19. května", "Maďarsko", "Velká Británie", "A"), ("Úterý 19. května", "Slovinsko", "Slovensko", "B"),
        ("Středa 20. května", "Švýcarsko", "Rakousko", "A"), ("Středa 20. května", "Česko", "Itálie", "B"),
        ("Středa 20. května", "USA", "Německo", "A"), ("Středa 20. května", "Švédsko", "Slovinsko", "B"),
        ("Čtvrtek 21. května", "Finsko", "Lotyšsko", "A"), ("Čtvrtek 21. května", "Norsko", "Kanada", "B"),
        ("Čtvrtek 21. května", "Švýcarsko", "Velká Británie", "A"), ("Čtvrtek 21. května", "Dánsko", "Slovensko", "B"),
        ("Pátek 22. května", "Maďarsko", "Německo", "A"), ("Pátek 22. května", "Kanada", "Slovinsko", "B"),
        ("Pátek 22. května", "Finsko", "Velká Británie", "A"), ("Pátek 22. května", "Itálie", "Švédsko", "B"),
        ("Sobota 23. května", "USA", "Lotyšsko", "A"), ("Sobota 23. května", "Dánsko", "Slovinsko", "B"),
        ("Sobota 23. května", "Švýcarsko", "Maďarsko", "A"), ("Sobota 23. května", "Slovensko", "Česko", "B"),
        ("Sobota 23. května", "Německo", "Rakousko", "A"), ("Sobota 23. května", "Švédsko", "Norsko", "B"),
        ("Neděle 24. května", "Lotyšsko", "Velká Británie", "A"), ("Neděle 24. května", "Dánsko", "Itálie", "B"),
        ("Neděle 24. května", "Finsko", "Rakousko", "A"), ("Neděle 24. května", "Kanada", "Slovensko", "B"),
        ("Pondělí 25. května", "USA", "Maďarsko", "A"), ("Pondělí 25. května", "Česko", "Norsko", "B"),
        ("Pondělí 25. května", "Německo", "Velká Británie", "A"), ("Pondělí 25. května", "Slovinsko", "Itálie", "B"),
        ("Úterý 26. května", "Maďarsko", "Lotyšsko", "A"), ("Úterý 26. května", "Norsko", "Dánsko", "B"),
        ("Úterý 26. května", "USA", "Rakousko", "A"), ("Úterý 26. května", "Slovensko", "Švédsko", "B"),
        ("Úterý 26. května", "Švýcarsko", "Finsko", "A"), ("Úterý 26. května", "Česko", "Kanada", "B"),
    ]

    for i, (d, t1, t2, gn) in enumerate(sched):
        day_num = date_mapping[d]
        d_idx = dates_list.index(d)
        
        _, streak1 = get_team_form(t1, matches, d_idx)
        _, streak2 = get_team_form(t2, matches, d_idx)
        
        s1, s2, rt, sc1, sc2 = sim_match(t1, t2, seed * 1000 + i, powers, db, f"G{gn}", day_num, last_played, streak1, streak2)
        matches.append({"d": d, "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": f"G{gn}", "sc1": sc1, "sc2": sc2})
        last_played[t1] = day_num
        last_played[t2] = day_num

    group_rankings = {"A": [], "B": []}
    global_seed_stats = {} 
    
    for gn in ["A", "B"]:
        g_m = [m for m in matches if m["stg"] == f"G{gn}"]
        sorted_tms, stats = get_iihf_rankings(groups_def[gn], g_m)
        group_rankings[gn] = sorted_tms
        for i, t in enumerate(sorted_tms):
            global_seed_stats[t] = {"Pos": i+1, "B": stats[t]["B"], "D": stats[t]["GF"]-stats[t]["GA"], "GF": stats[t]["GF"]}

    A = group_rankings["A"]
    B = group_rankings["B"]
    qf_pairs = [(A[0], B[3]), (B[0], A[3]), (A[1], B[2]), (B[1], A[2])]
    qf_labels = ["ČF1 (16:15, Curych)", "ČF2 (16:15, Fribourg)", "ČF3 (20:15, Curych)", "ČF4 (20:15, Fribourg)"]
    qf_winners = []
    
    cf_day = date_mapping["Čtvrtek 28. května (ČF)"]
    for i, (t1, t2) in enumerate(qf_pairs):
        s1, s2, rt, sc1, sc2 = sim_match(t1, t2, seed * 1000 + 100 + i, powers, db, "PO", cf_day, last_played)
        w = t1 if s1 > s2 else t2; qf_winners.append(w)
        matches.append({"d": "Čtvrtek 28. května (ČF)", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": qf_labels[i], "w": w, "sc1": sc1, "sc2": sc2})
        last_played[t1] = cf_day; last_played[t2] = cf_day

    def reseeding_key(t):
        s = global_seed_stats[t]
        return (-s["Pos"], s["B"], s["D"], s["GF"]) 
    
    sf_seeded = sorted(qf_winners, key=reseeding_key, reverse=True)
    while len(sf_seeded) < 4: sf_seeded.append("TBD")
    
    sf_pairs = [(sf_seeded[0], sf_seeded[3]), (sf_seeded[1], sf_seeded[2])]
    sf_labels = ["SF1 (14:30, Curych)", "SF2 (18:30, Curych)"]
    sf_w, sf_l = [], []
    sf_day = date_mapping["Sobota 30. května (SF)"]
    for i, (a, b) in enumerate(sf_pairs):
        s1, s2, rt, sc1, sc2 = sim_match(a, b, seed * 1000 + 200 + i, powers, db, "PO", sf_day, last_played)
        w, l = (a, b) if s1 > s2 else (b, a)
        sf_w.append(w); sf_l.append(l)
        matches.append({"d": "Sobota 30. května (SF)", "t1": a, "t2": b, "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": sf_labels[i], "w": w, "sc1": sc1, "sc2": sc2})
        last_played[a] = sf_day; last_played[b] = sf_day

    med_day = date_mapping["Neděle 31. května (Medaile)"]
    if len(sf_l) >= 2:
        s1, s2, rt, sc1, sc2 = sim_match(sf_l[0], sf_l[1], seed * 1000 + 300, powers, db, "PO", med_day, last_played)
        matches.append({"d": "Neděle 31. května (Medaile)", "t1": sf_l[0], "t2": sf_l[1], "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": "O 3. místo (15:30, Curych)", "w": sf_l[0] if s1>s2 else sf_l[1], "sc1": sc1, "sc2": sc2})
    
    if len(sf_w) >= 2:
        s1, s2, rt, sc1, sc2 = sim_match(sf_w[0], sf_w[1], seed * 1000 + 400, powers, db, "PO", med_day, last_played)
        matches.append({"d": "Neděle 31. května (Medaile)", "t1": sf_w[0], "t2": sf_w[1], "s1": s1, "s2": s2, "rt": rt, "stg": "PO", "lbl": "Finále (20:15, Curych)", "w": sf_w[0] if s1>s2 else sf_w[1], "sc1": sc1, "sc2": sc2})
    
    return matches

@st.cache_data
def get_mc_stats(n_sims, powers, db, version):
    res_stats = {t: {"Gold": 0, "Silver": 0, "Bronze": 0, "QF": 0, "G_Seeds": [], "M_Seeds": []} for t in powers}
    for i in range(1, n_sims + 1):
        tourney = run_tourney_cached(i, powers, db, version)
        try:
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
    df["🛡️ Postup do ČF"] = (df["QF"] / n_sims * 100)
    df["🥇 Zlato"] = (df["Gold"] / n_sims * 100); df["🥈 Stříbro"] = (df["Silver"] / n_sims * 100)
    df["🥉 Bronz"] = (df["Bronze"] / n_sims * 100); df["Celkem medaile"] = ((df["Gold"] + df["Silver"] + df["Bronze"]) / n_sims * 100)
    return df.sort_values("🥇 Zlato", ascending=False), res_stats

# --- 6. UI ---
tab1, tab2, tab3 = st.tabs(["🎮 Simulace", "📊 Prediktor", "🔍 Hledač zázraků"])

with tab1:
    c1, c2 = st.columns([1, 4])
    with c1: seed = st.number_input("ID Simulace", 1, 10000, 1)
    with c2: sel_date = st.select_slider("Fáze turnaje", options=dates_list, value="Středa 20. května")
    all_m = run_tourney_cached(seed, team_powers_db, results_db, APP_VERSION)
    
    today = [m for m in all_m if m["d"] == sel_date]
    if today:
        cols = st.columns(2)
        for i, m in enumerate(today):
            with cols[i % 2]:
                label = f"<span class='ot-label'>{m['rt']}</span>" if m['rt'] != "REG" else ""
                
                scorers_html = ""
                if m.get("sc1") or m.get("sc2"):
                    sc1_str = ", ".join(m["sc1"]) if m["sc1"] else ""
                    sc2_str = ", ".join(m["sc2"]) if m["sc2"] else ""
                    scorers_html = f"<div style='font-size:0.8em; color:gray; margin-top:5px;'><div style='float:left; width:45%;'>{sc1_str}</div><div style='float:right; width:45%; text-align:right;'>{sc2_str}</div><div style='clear:both;'></div></div>"

                st.markdown(f"<div class='match-box'><div class='team-n'>{m['t1']}</div><div class='score-n'>{m['s1']}:{m['s2']}{label}</div><div class='team-n' style='text-align:right;'>{m['t2']}</div></div>{scorers_html}", unsafe_allow_html=True)
    st.markdown("---")
    
    if ("května" in sel_date and 
        "ČF" not in sel_date and 
        "SF" not in sel_date and 
        "Medaile" not in sel_date):
        
        cols_g = st.columns(2)
        for i, gn in enumerate(["A", "B"]):
            current_date_idx = dates_list.index(sel_date)
            past_dates = dates_list[:current_date_idx + 1]
            g_m = [m for m in all_m if m["stg"] == f"G{gn}" and m["d"] in past_dates]
            sorted_tms, stats = get_iihf_rankings(groups_def[gn], g_m)
            
            table_data = []
            for t in sorted_tms:
                form_str, _ = get_team_form(t, all_m, current_date_idx + 1)
                table_data.append({"Tým": t, "Forma": form_str, "Body": stats[t]["B"], "Skóre": f"{stats[t]['GF']}:{stats[t]['GA']}"})
                
            df_g = pd.DataFrame(table_data)
            df_g.index += 1
            with cols_g[i]: 
                st.write(f"**Skupina {gn}**")
                st.dataframe(df_g.style.apply(color_standings, axis=1), use_container_width=True)
    else:
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
            for m in [x for x in po if "místo" in x["lbl"] or "Finále" in x["lbl"]]:
                lbl = f" ({m['rt']})" if m['rt'] != "REG" else ""; st.markdown(f"<div class='bracket-card'><b>{m['lbl']}</b><br>{m['t1']} - {m['t2']} <br><b>{m['s1']}:{m['s2']}{lbl}</b></div>", unsafe_allow_html=True)

with tab2:
    st.header("📈 Prediktor (10 000 simulací)")
    mc_df, _ = get_mc_stats(10000, team_powers_db, results_db, APP_VERSION)
    from matplotlib.colors import LinearSegmentedColormap
    custom_cmap = LinearSegmentedColormap.from_list("custom_green", ["#ffffff", "#00ff00"])
    st.dataframe(mc_df[["🛡️ Postup do ČF", "🥇 Zlato", "🥈 Stříbro", "🥉 Bronz", "Celkem medaile"]].style.background_gradient(cmap=custom_cmap, axis=0).format("{:.2f} %"), use_container_width=True, height=600)

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
