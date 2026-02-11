import streamlit as st
import pandas as pd
import numpy as np
import random

# --- 1. KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="ZOH 2026 Simulator", layout="wide", page_icon="🏒")

# --- 2. SÍLA TÝMŮ A REÁLNÉ VÝSLEDKY ---
# Power Index (0-100) - čím víc, tím lépe. Uprav si podle sebe!
team_powers = {
    "Kanada": 96, "USA": 94, "Švédsko": 90, "Finsko": 85,
    "Česko": 89, "Švýcarsko": 82, "Slovensko": 83, "Německo": 76,
    "Dánsko": 60, "Lotyšsko": 58, "Itálie": 40, "Francie": 35
}

# Zde dopisuj výsledky tak, jak se reálně odehrají
# Formát: ("Tým1", "Tým2"): (Góly1, Góly2, "REG" nebo "OT")
real_results = {
    ("Slovensko", "Finsko"): (4, 1, "REG"),
    # ("Česko", "Kanada"): (3, 2, "OT"), # Příklad pro budoucno
}

# --- 3. STATICKÁ DATA ---
groups_def = {
    "A": ["Česko", "Francie", "Švýcarsko", "Kanada"],
    "B": ["Finsko", "Itálie", "Slovensko", "Švédsko"],
    "C": ["Dánsko", "Německo", "Lotyšsko", "USA"]
}

dates_list = [
    "Středa 11. února", "Čtvrtek 12. února", "Pátek 13. února",
    "Sobota 14. února", "Neděle 15. února", "Úterý 17. února",
    "Středa 18. února", "Pátek 20. února", "Sobota 21. února", "Neděle 22. února"
]

# --- 4. CSS STYLING ---
st.markdown("""
<style>
    .match-box {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .team-n { font-weight: bold; font-size: 1em; color: #111; }
    .score-n { font-size: 1.5em; font-weight: 800; color: #ff4b4b; margin: 0 10px; }
    .ot-badge { font-size: 0.6em; vertical-align: middle; color: #777; }
    .stTable { font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)


# --- 5. FUNKCE PRO SIMULACI ---
def simulate_match(t1, t2, seed):
    # Kontrola reálných výsledků
    if (t1, t2) in real_results: return real_results[(t1, t2)]
    if (t2, t1) in real_results:
        r = real_results[(t2, t1)]
        return r[1], r[0], r[2]

    # Simulace náhody
    random.seed(seed + hash(t1) + hash(t2))
    p1, p2 = team_powers[t1], team_powers[t2]

    # Poissonovo rozdělení pro góly
    avg_g = 2.6
    s1 = np.random.poisson(avg_g * (p1 / p2) ** 0.5)
    s2 = np.random.poisson(avg_g * (p2 / p1) ** 0.5)

    rtype = "REG"
    if s1 == s2:
        rtype = "OT"
        if random.random() < (p1 / (p1 + p2)):
            s1 += 1
        else:
            s2 += 1
    return s1, s2, rtype


# --- 6. GENEROVÁNÍ CELÉHO TURNAJE ---
def get_tournament_data(seed):
    np.random.seed(seed)

    schedule = [
        ("Středa 11. února", "16:40", "Slovensko", "Finsko"),
        ("Středa 11. února", "21:10", "Švédsko", "Itálie"),
        ("Čtvrtek 12. února", "12:10", "Švýcarsko", "Francie"),
        ("Čtvrtek 12. února", "16:40", "Česko", "Kanada"),
        ("Čtvrtek 12. února", "21:10", "Lotyšsko", "USA"),
        ("Čtvrtek 12. února", "21:10", "Německo", "Dánsko"),
        ("Pátek 13. února", "12:10", "Finsko", "Švédsko"),
        ("Pátek 13. února", "12:10", "Itálie", "Slovensko"),
        ("Pátek 13. února", "16:40", "Francie", "Česko"),
        ("Pátek 13. února", "21:10", "Kanada", "Švýcarsko"),
        ("Sobota 14. února", "12:10", "Švédsko", "Slovensko"),
        ("Sobota 14. února", "12:10", "Německo", "Lotyšsko"),
        ("Sobota 14. února", "16:40", "Finsko", "Itálie"),
        ("Sobota 14. února", "21:10", "USA", "Dánsko"),
        ("Neděle 15. února", "12:10", "Švýcarsko", "Česko"),
        ("Neděle 15. února", "16:40", "Kanada", "Francie"),
        ("Neděle 15. února", "19:10", "Dánsko", "Lotyšsko"),
        ("Neděle 15. února", "21:10", "USA", "Německo"),
    ]

    all_matches = []
    # 1. Skupiny
    for d, t, t1, t2 in schedule:
        s1, s2, rt = simulate_match(t1, t2, seed)
        all_matches.append({"date": d, "time": t, "t1": t1, "t2": t2, "s1": s1, "s2": s2, "type": rt, "stage": "Group"})

    # Pomocná funkce pro seeding (Rank 1-12)
    def get_seeding(matches_so_far):
        st = {t: {"B": 0, "D": 0} for t in team_powers}
        for m in matches_so_far:
            if m["stage"] != "Group": continue
            st[m["t1"]]["D"] += (m["s1"] - m["s2"]);
            st[m["t2"]]["D"] += (m["s2"] - m["s1"])
            if m["type"] == "REG":
                if m["s1"] > m["s2"]:
                    st[m["t1"]]["B"] += 3
                else:
                    st[m["t2"]]["B"] += 3
            else:
                if m["s1"] > m["s2"]:
                    st[m["t1"]]["B"] += 2; st[m["t2"]]["B"] += 1
                else:
                    st[m["t2"]]["B"] += 2; st[m["t1"]]["B"] += 1

        ranked = []
        for gn, teams in groups_def.items():
            sorted_g = sorted(teams, key=lambda x: (st[x]["B"], st[x]["D"]), reverse=True)
            for i, t in enumerate(sorted_g): ranked.append({"T": t, "R": i + 1, "B": st[t]["B"], "D": st[t]["D"]})

        w = sorted([x for x in ranked if x["R"] == 1], key=lambda x: (x["B"], x["D"]), reverse=True)
        r = sorted([x for x in ranked if x["R"] == 2], key=lambda x: (x["B"], x["D"]), reverse=True)
        o = sorted([x for x in ranked if x["R"] >= 3], key=lambda x: (x["B"], x["D"]), reverse=True)
        return [x["T"] for x in w + [r[0]] + r[1:] + o]

    # 2. Playoff (OF, ČF, SF, Medaile)
    seeds = get_seeding(all_matches)

    # OF
    of_winners = {}
    for i, (h, l) in enumerate([(4, 11), (5, 10), (6, 9), (7, 8)]):
        t1, t2 = seeds[h], seeds[l]
        s1, s2, rt = simulate_match(t1, t2, seed + 100)
        of_winners[h] = t1 if s1 > s2 else t2
        all_matches.append({"date": "Úterý 17. února", "time": "OF", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "type": rt,
                            "stage": "OF"})

    # ČF
    qf_winners = []
    for i, (h, l) in enumerate([(0, 7), (1, 6), (2, 5), (3, 4)]):
        t1, t2 = seeds[h], of_winners[l]
        s1, s2, rt = simulate_match(t1, t2, seed + 200)
        qf_winners.append(t1 if s1 > s2 else t2)
        all_matches.append(
            {"date": "Středa 18. února", "time": "ČF", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "type": rt,
             "stage": "QF"})

    # SF
    sf_losers, finalists = [], []
    for i, (t1, t2) in enumerate([(qf_winners[1], qf_winners[2]), (qf_winners[3], qf_winners[0])]):
        s1, s2, rt = simulate_match(t1, t2, seed + 300)
        finalists.append(t1 if s1 > s2 else t2)
        sf_losers.append(t2 if s1 > s2 else t1)
        all_matches.append({"date": "Pátek 20. února", "time": "SF", "t1": t1, "t2": t2, "s1": s1, "s2": s2, "type": rt,
                            "stage": "SF"})

    # Medal
    s1, s2, rt = simulate_match(sf_losers[0], sf_losers[1], seed + 400)
    all_matches.append(
        {"date": "Sobota 21. února", "time": "20:40", "t1": sf_losers[0], "t2": sf_losers[1], "s1": s1, "s2": s2,
         "type": rt, "stage": "Medal", "label": "Bronz"})

    s1, s2, rt = simulate_match(finalists[0], finalists[1], seed + 500)
    all_matches.append(
        {"date": "Neděle 22. února", "time": "13:40", "t1": finalists[0], "t2": finalists[1], "s1": s1, "s2": s2,
         "type": rt, "stage": "Medal", "label": "Finále"})

    return all_matches


# --- 7. VÝPOČET AKTUÁLNÍ TABULKY ---
def get_table_at_date(all_matches, date_idx):
    target_dates = dates_list[:date_idx + 1]
    stats = {t: {"Z": 0, "B": 0, "Skóre": [0, 0]} for t in team_powers}

    for m in all_matches:
        if m["date"] in target_dates and m["stage"] == "Group":
            t1, t2 = m["t1"], m["t2"]
            stats[t1]["Z"] += 1;
            stats[t2]["Z"] += 1
            stats[t1]["Skóre"][0] += m["s1"];
            stats[t1]["Skóre"][1] += m["s2"]
            stats[t2]["Skóre"][0] += m["s2"];
            stats[t2]["Skóre"][1] += m["s1"]
            if m["type"] == "REG":
                if m["s1"] > m["s2"]:
                    stats[t1]["B"] += 3
                else:
                    stats[t2]["B"] += 3
            else:
                if m["s1"] > m["s2"]:
                    stats[t1]["B"] += 2; stats[t2]["B"] += 1
                else:
                    stats[t2]["B"] += 2; stats[t1]["B"] += 1
    return stats


# --- 8. UI STRUKTURA ---
with st.sidebar:
    st.header("Ovládání")
    sim_seed = st.number_input("Číslo simulace", value=1, min_value=1)
    sel_date = st.select_slider("Časová osa turnaje", options=dates_list)
    st.markdown("---")

all_m = get_tournament_data(sim_seed)
date_idx = dates_list.index(sel_date)

st.title(f"ZOH 2026: {sel_date}")

# DNEŠNÍ ZÁPASY
today_m = [m for m in all_m if m["date"] == sel_date]
if today_m:
    cols = st.columns(len(today_m))
    for i, m in enumerate(today_m):
        with cols[i]:
            ot_t = " <span class='ot-badge'>PP</span>" if m["type"] == "OT" else ""
            st.markdown(f"""
                <div class="match-box">
                    <span class="team-n">{m['t1']}</span>
                    <span class="score-n">{m['s1']}:{m['s2']}{ot_t}</span>
                    <span class="team-n">{m['t2']}</span>
                    <br><small>{m['time']}</small>
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("Dnes se nehrají žádné zápasy.")

st.markdown("---")

# TABULKY NEBO PAVOUK
if date_idx <= 4:
    st.subheader("Tabulky skupin")
    curr_stats = get_table_at_date(all_m, date_idx)
    t_cols = st.columns(3)
    for i, (gn, teams) in enumerate(groups_def.items()):
        g_data = []
        for t in teams:
            s = curr_stats[t]
            g_data.append({
                "Tým": t, "Z": s["Z"], "B": s["B"],
                "Skóre": f"{s['Skóre'][0]}:{s['Skóre'][1]}",
                "Diff": s["Skóre"][0] - s["Skóre"][1]
            })
        df = pd.DataFrame(g_data).sort_values(by=["B", "Diff"], ascending=False).reset_index(drop=True)
        df.index += 1
        with t_cols[i]:
            st.write(f"**Skupina {gn}**")
            st.table(df[["Tým", "Z", "B", "Skóre"]])
else:
    st.subheader("Play-off Pavouk")
    po_m = [m for m in all_m if dates_list.index(m["date"]) <= date_idx and m["stage"] != "Group"]

    if po_m:
        # Rozdělení do sloupců podle fází
        c_of, c_qf, c_sf, c_fin = st.columns(4)
        with c_of:
            st.caption("Osmifinále")
            for m in [x for x in po_m if x["stage"] == "OF"]: st.write(
                f"**{m['t1']}**-**{m['t2']}** ({m['s1']}:{m['s2']})")
        with c_qf:
            st.caption("Čtvrtfinále")
            for m in [x for x in po_m if x["stage"] == "QF"]: st.write(
                f"**{m['t1']}**-**{m['t2']}** ({m['s1']}:{m['s2']})")
        with c_sf:
            st.caption("Semifinále")
            for m in [x for x in po_m if x["stage"] == "SF"]: st.write(
                f"**{m['t1']}**-**{m['t2']}** ({m['s1']}:{m['s2']})")
        with c_fin:
            st.caption("Medaile")
            for m in [x for x in po_m if x["stage"] == "Medal"]:
                label = m.get("label", "")
                st.write(f"*{label}*: **{m['t1']}**-**{m['t2']}** ({m['s1']}:{m['s2']})")