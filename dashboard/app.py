"""
AI Infrastructure Capex Dashboard.

An overview of the AI compute value chain, then one tab per step from silicon
through the AI labs. Alphabet capex is extracted from 10-K filings; other figures
are sourced from company filings and industry data, with each source flagged.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"

st.set_page_config(
    page_title="AI Infrastructure Capex",
    page_icon="🛰️",
    layout="wide",
)

# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
@st.cache_data
def load_capex() -> pd.DataFrame:
    df = pd.read_csv(DATA / "hyperscaler_capex.csv")
    df["capex_usd_b"] = df["capex_usd_m"] / 1000.0
    return df


@st.cache_data
def load_value_chain() -> pd.DataFrame:
    return pd.read_csv(DATA / "value_chain.csv").sort_values("layer_order")


@st.cache_data
def load_guidance() -> pd.DataFrame:
    return pd.read_csv(DATA / "capex_guidance_2026.csv")


@st.cache_data
def load_neoclouds() -> pd.DataFrame:
    return pd.read_csv(DATA / "neoclouds.csv")


@st.cache_data
def load_cowos() -> pd.DataFrame:
    return pd.read_csv(DATA / "cowos_capacity.csv")


@st.cache_data
def load_hbm() -> pd.DataFrame:
    return pd.read_csv(DATA / "hbm_market.csv")


@st.cache_data
def load_gw_projects() -> pd.DataFrame:
    return pd.read_csv(DATA / "gigawatt_projects.csv")


@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name)


capex = load_capex()
chain = load_value_chain()
guidance = load_guidance()
neo = load_neoclouds()
cowos = load_cowos()
hbm = load_hbm()
gw = load_gw_projects()
foundry = load_csv("foundry_players.csv")
systems = load_csv("systems_vendors.csv")
networking = load_csv("networking_vendors.csv")
dc_con = load_csv("dc_construction.csv")
labrev = load_csv("ai_lab_revenue.csv")
bench = load_csv("llm_benchmark.csv")
silicon_rev = load_csv("silicon_revenue.csv")
chatgpt = load_csv("chatgpt_users.csv")
bench_lab = load_csv("llm_benchmark_by_lab.csv")
telco_capex = load_csv("telecom_capex.csv")
telco_players = load_csv("telecom_players.csv")
capex_q = load_csv("hyperscaler_capex_quarterly.csv")
accel_rev = load_csv("accelerator_dc_revenue.csv")
telco_us = load_csv("telecom_us_series.csv")
ocf = load_csv("hyperscaler_ocf.csv")
si = load_csv("system_integrators.csv")
genai_bookings = load_csv("accenture_genai_bookings.csv")

DATA_UPDATED = "June 4, 2026"

YEARS = sorted(capex["fiscal_year"].unique())
YR = max(YEARS)  # latest reported fiscal year (2025)

BLUE, GREEN, YELLOW, RED, GREY = "#4285F4", "#34A853", "#FBBC04", "#EA4335", "#9aa0a6"
PURPLE = "#9334E6"

# One color per company, used consistently across all tabs.
COMPANY_COLORS = {
    "Alphabet": BLUE,
    "Amazon": YELLOW,
    "Meta": GREEN,
    "Microsoft": RED,
    "Oracle": PURPLE,
}


def render_layer_card(order: int):
    """Render the structured value-chain card(s) for a given layer."""
    for _, r in chain[chain["layer_order"] == order].iterrows():
        st.markdown(f"**{r['segment']}**")
        st.markdown(f"- **Key players:** {r['key_players']}")
        st.markdown(f"- **Role in stack:** {r['role_in_stack']}")
        st.markdown(f"- **Metric to track:** {r['key_metric']}")
        st.markdown(f"- **Bottleneck:** :red[{r['bottleneck']}]")


st.title("AI Infrastructure Capex")
st.caption(
    "How AI compute is financed, built, and priced across the value chain, from "
    "silicon and packaging through hyperscalers, NeoClouds, and the AI labs."
)

(tab_overview, tab_silicon, tab_foundry, tab_systems, tab_network,
 tab_dc, tab_hyper, tab_neo, tab_labs, tab_si, tab_telco) = st.tabs([
    "📊 Overview",
    "⚙️ 1·Silicon & IP",
    "🏭 2·Foundry & Packaging",
    "🖥️ 3·Servers",
    "🔌 4·Networking",
    "⚡ 5·Data Centers",
    "☁️ 6·Hyperscalers",
    "🌩️ 7·NeoClouds",
    "🧠 8·AI Labs",
    "🧩 9·System Integrators",
    "📡 10·Telecoms",
])

# Capex view (all companies, all years), total capex
view = capex.copy()
latest = view[view["fiscal_year"] == YR]
prev = view[view["fiscal_year"] == (YR - 1)]

# --------------------------------------------------------------------------- #
# Overview — whole value chain
# --------------------------------------------------------------------------- #
with tab_overview:
    st.markdown("### The AI compute value chain, end to end")
    st.caption(
        "Capex flows downstream from silicon to models; each layer has a binding "
        "bottleneck. Key metrics across the chain, then a deep-dive per step in "
        "the tabs to the right."
    )

    total_now = latest["capex_usd_b"].sum()
    total_prev = prev["capex_usd_b"].sum()
    first_yr = min(YEARS)
    total_first = view[view["fiscal_year"] == first_yr]["capex_usd_b"].sum()
    cagr = (total_now / total_first) ** (1 / (YR - first_yr)) - 1
    yoy = (total_now / total_prev - 1) * 100 if total_prev else 0
    guide26 = guidance["capex_mid_b"].sum()
    cowos25 = float(cowos.loc[cowos.year == 2025, "cowos_kwpm"].iloc[0])
    cowos26_lo = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_low"].iloc[0])
    cowos26_hi = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_high"].iloc[0])
    tsmc25 = float(foundry.loc[(foundry.company == "TSMC") &
                               (foundry.year == 2025), "revenue_b"].iloc[0])

    st.markdown("#### Executive summary")
    st.markdown(
        f"- **Hyperscalers can no longer fund AI infrastructure from free cash "
        f"flow alone.** Big-5 capex (Microsoft, Alphabet, Amazon, Meta, Oracle) "
        f"reached **\\${total_now:,.0f}B** in FY2025 ({yoy:+.0f}%) and is guided "
        f"to about **\\${guide26:,.0f}B** for 2026, larger than global upstream "
        f"oil and gas investment (about \\$570B, IEA) and approaching total "
        f"fossil-fuel investment (about \\$1.1T). Capex now runs at roughly 30 "
        f"to 75% of revenue "
        f"for previously asset-light businesses, and the gap is increasingly "
        f"debt-financed: hyperscalers issued \\$121B of bonds in 2025, four times "
        f"the five-year average, including Meta's \\$30B, the largest corporate "
        f"bond since 2023.\n"
        f"- **Supply remains the constraint.** TSMC's CoWoS packaging capacity "
        f"roughly doubled in 2025 to about {cowos25:.0f}k wafers per month and "
        f"is fully booked; HBM suppliers are sold out through 2026. Microsoft "
        f"attributed about \\$25B of its 2026 guidance increase to memory and "
        f"component cost inflation rather than added capacity. CoreWeave's "
        f"contracted backlog reached about \\$100B in Q1 2026.\n"
        f"- **Power is the next gate.** About {gw['capacity_gw'].sum():.0f} GW "
        f"of named gigawatt-scale projects are in the pipeline, while "
        f"high-voltage substation lead times run 3 to 5 years.\n"
        f"- **Demand is keeping pace, but value capture is an open question.** "
        f"ChatGPT reached 900M weekly active users in Feb 2026; Anthropic and "
        f"OpenAI report run-rate revenue of \\$47B and \\$25B. Only about 5 to 6% "
        f"of ChatGPT users pay, and frontier capability has converged across "
        f"labs with no clear network effects, which raises the question of "
        f"whether value migrates to infrastructure below and applications "
        f"above the model layer.\n"
        f"- **System integrators are quiet winners of the deployment phase.** "
        f"Accenture booked \\$5.9B of GenAI work in FY2025, up from about \\$3B in "
        f"FY2024, because deploying AI into enterprises remains services-heavy."
    )
    st.caption(f"Data last updated {DATA_UPDATED}. Sources are cited per chart "
               "and logged in notes/sources.md in the repository.")
    st.markdown("---")

    st.markdown("##### Spend & demand (downstream)")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric(f"Big-5 total capex FY{YR}", f"${total_now:,.0f}B", f"{yoy:+.0f}% YoY")
    d2.metric("Big-5 2026E guidance", f"${guide26:,.0f}B",
              f"+{(guide26/total_now-1)*100:.0f}% vs FY25")
    d3.metric(f"Capex CAGR FY{first_yr}-{YR}", f"{cagr*100:.0f}%/yr",
              "AI-era acceleration")
    d4.metric("NeoCloud backlog (CoreWeave)", "$66.8B", "~$100B by Q1'26")

    st.markdown("##### Supply & constraint (upstream)")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("CoWoS capacity 2025", f"{cowos25:.0f}k wpm", "~2× vs 2024")
    s2.metric("CoWoS 2026E", f"{cowos26_lo:.0f}-{cowos26_hi:.0f}k wpm", "sold out")
    s3.metric("TSMC revenue 2025", f"${tsmc25:.0f}B", "~70% foundry share")
    s4.metric("Named GW-scale pipeline", f"{gw['capacity_gw'].sum():.0f} GW",
              f"{len(gw)} flagship projects")

    st.markdown("#### Hyperscaler capex by company (\\$B, absolute)")
    color_map = COMPANY_COLORS
    comp_order = ["Alphabet", "Amazon", "Meta", "Microsoft", "Oracle"]
    act = view.pivot_table(index="company", columns="fiscal_year",
                           values="capex_usd_b", aggfunc="sum")
    gmid = guidance.set_index("company")["capex_mid_b"]
    hist_years = sorted(view["fiscal_year"].unique())
    years = hist_years + [2026]
    xcat = [str(y) for y in years]

    figo = go.Figure()
    for comp in comp_order:
        yvals = [float(act.loc[comp, y]) if y in act.columns else 0.0
                 for y in hist_years] + [float(gmid.get(comp, 0))]
        figo.add_trace(go.Bar(
            name=comp, x=xcat, y=yvals, marker_color=color_map[comp],
            marker_pattern_shape=[""] * len(hist_years) + ["/"]))
    figo.update_layout(barmode="stack", height=440, legend_title="",
                       yaxis_title="Capex ($B)", xaxis_title="Fiscal year",
                       hovermode="x unified")

    totals = {y: float(sum(act.loc[c, y] for c in comp_order
                           if y in act.columns)) for y in hist_years}
    totals[2026] = float(gmid.reindex(comp_order).sum())
    for y in years:
        label = f"${totals[y]:,.0f}B" + ("E" if y == 2026 else "")
        figo.add_annotation(x=str(y), y=totals[y], text=f"<b>{label}</b>",
                            showarrow=False, yshift=12,
                            font=dict(size=12, color="#202124"))
    figo.update_yaxes(range=[0, max(totals.values()) * 1.12])
    st.plotly_chart(figo, width="stretch")
    st.caption(
        "Figures are total reported capex, not an AI-only carve-out (companies "
        "do not disclose the split). Totals are shown above each bar. Bars for "
        "2018 to 2025 are reported cash PP&E; the hatched 2026E bar is the "
        "guidance midpoint, which is reported on a broader basis (total capex "
        "including finance leases). Microsoft's fiscal year ends in June and "
        "Oracle's in May, so their years are not calendar-aligned.")
    st.caption(
        f"FY24 to FY25, the five companies went from \\${total_prev:,.0f}B to "
        f"\\${total_now:,.0f}B. Guidance points to about \\${totals[2026]:,.0f}B in "
        "2026.")

    st.markdown("#### Value-chain map")
    st.caption("Each step, its key metric, and its main bottleneck.")
    cmap = chain[["layer_order", "layer", "segment", "key_metric", "bottleneck"]]
    st.dataframe(
        cmap.rename(columns={
            "layer_order": "#", "layer": "Step", "segment": "Segment",
            "key_metric": "Key metric", "bottleneck": "Bottleneck",
        }),
        width="stretch", hide_index=True,
    )

# --------------------------------------------------------------------------- #
# 1 · Silicon & IP  (accelerator design + HBM memory)
# --------------------------------------------------------------------------- #
with tab_silicon:
    st.markdown("### 1 · Silicon & IP")
    st.caption(
        "The compute engines (GPUs / TPUs / ASICs) and the high-bandwidth memory "
        "stacked beside them.")
    render_layer_card(1)

    st.markdown("---")
    st.markdown("#### Revenue by key player (\\$B)")
    figsi = px.bar(
        silicon_rev, x="fy", y="revenue_b", color="company", barmode="group",
        labels={"fy": "Fiscal year", "revenue_b": "Revenue ($B)", "company": ""},
        color_discrete_map={"NVIDIA": GREEN, "AMD": RED, "Broadcom": BLUE,
                            "Micron": YELLOW})
    figsi.update_layout(height=400, hovermode="x unified", legend_title="")
    st.plotly_chart(figsi, width="stretch")
    st.caption(
        "Total company revenue. NVIDIA / Broadcom / Micron fiscal years are "
        "offset from calendar. NVIDIA's data-center segment alone was about "
        "\\$115B in FY2025. Memory: HBM is the supply-constrained input (SK "
        "Hynix about 57% share, sold out through 2026); Micron shown as the "
        "US-listed memory proxy. Sources: company filings.")

# --------------------------------------------------------------------------- #
# 2 · Foundry & Packaging  (TSMC CoWoS + the supply ceiling)
# --------------------------------------------------------------------------- #
with tab_foundry:
    st.markdown("### 2 · Foundry & Packaging")
    st.caption(
        "Where chips are manufactured and packaged. Advanced packaging (CoWoS) "
        "co-locates logic and HBM and is the single most-cited physical "
        "bottleneck in the AI supply chain."
    )
    render_layer_card(2)

    st.markdown("---")
    st.markdown("#### Revenue & capex by key player (\\$B)")
    st.caption(
        "Pure-play foundries. TSMC has about 70% market share; GlobalFoundries "
        "and UMC "
        "are specialty / mature-node players. Samsung Foundry (#2) and Intel "
        "Foundry are loss-making segments inside larger firms, omitted here.")
    fc1, fc2 = st.columns(2)
    fcolors = {"TSMC": BLUE, "GlobalFoundries": GREEN, "UMC": YELLOW}
    with fc1:
        figfr = px.bar(foundry, x="year", y="revenue_b", color="company",
                       barmode="group", color_discrete_map=fcolors,
                       labels={"year": "Year", "revenue_b": "Revenue ($B)",
                               "company": ""})
        figfr.update_layout(height=340, hovermode="x unified", legend_title="",
                            title="Revenue")
        st.plotly_chart(figfr, width="stretch")
    with fc2:
        figfc = px.bar(foundry, x="year", y="capex_b", color="company",
                       barmode="group", color_discrete_map=fcolors,
                       labels={"year": "Year", "capex_b": "Capex ($B)",
                               "company": ""})
        figfc.update_layout(height=340, hovermode="x unified", legend_title="",
                            title="Capex")
        st.plotly_chart(figfc, width="stretch")
    st.caption(
        "Sources: TSMC / GlobalFoundries / UMC results (SEC filings). TSMC 2026E "
        "capex guidance \\$52-56B; CoWoS is about 7-9% of TSMC revenue. OSAT "
        "partners: ASE, Amkor.")

    cowos25 = float(cowos.loc[cowos.year == 2025, "cowos_kwpm"].iloc[0])
    cowos26 = float(cowos.loc[cowos.year == 2026, "cowos_kwpm"].iloc[0])
    cowos26_lo = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_low"].iloc[0])
    cowos26_hi = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_high"].iloc[0])

    st.markdown("---")
    k1, k2, k3 = st.columns(3)
    k1.metric("CoWoS capacity 2025", f"{cowos25:.0f}k wpm", "~2× vs 2024")
    k2.metric("CoWoS 2026E", f"{cowos26_lo:.0f}-{cowos26_hi:.0f}k wpm", "fully booked")
    k3.metric("Growth 2023→2026E", "~10×", "still supply-short")

    st.markdown("#### TSMC CoWoS capacity (k wafers/month)")
    cf = cowos.copy()
    figc = go.Figure(go.Bar(
        x=cf["year"], y=cf["cowos_kwpm"], marker_color=BLUE,
        error_y=dict(type="data", symmetric=False,
                     array=cf["cowos_kwpm_high"] - cf["cowos_kwpm"],
                     arrayminus=cf["cowos_kwpm"] - cf["cowos_kwpm_low"])))
    figc.update_layout(height=320, yaxis_title="k wafers/month", xaxis_title="Year")
    st.plotly_chart(figc, width="stretch")

    st.caption(
        "Source: TrendForce. CoWoS capacity has risen roughly 10x since 2023 and "
        "remains sold out. CoWoS is about 7 to 9% of TSMC revenue.")

# --------------------------------------------------------------------------- #
# 3 · Systems
# --------------------------------------------------------------------------- #
with tab_systems:
    st.markdown("### 3 · Servers")
    st.caption(
        "The OEMs/ODMs that assemble accelerators, memory and networking into "
        "deployable racks.")
    render_layer_card(3)

    st.markdown("---")
    st.markdown("#### Server revenue by vendor (\\$B)")
    figsy = px.bar(
        systems, x="year", y="revenue_b", color="company", barmode="group",
        color_discrete_map={"Dell ISG": BLUE, "Supermicro": GREEN,
                            "HPE Server": YELLOW},
        labels={"year": "Fiscal year", "revenue_b": "Revenue ($B)",
                "company": ""})
    figsy.update_layout(height=380, hovermode="x unified", legend_title="")
    st.plotly_chart(figsy, width="stretch")
    st.caption(
        "Fiscal years differ (Dell ends in January, Supermicro in June, HPE in "
        "October). Dell ISG "
        "includes storage; Supermicro 2026 is the company revenue target "
        "(guidance); the HPE server segment is partly estimated. Most AI-server "
        "volume flows through Taiwanese ODMs (Foxconn/Hon Hai, Quanta, Wistron), "
        "which are lower-margin and under-disclosed. Sources: company filings.")

# --------------------------------------------------------------------------- #
# 4 · Networking
# --------------------------------------------------------------------------- #
with tab_network:
    st.markdown("### 4 · Networking")
    st.caption(
        "Back-end GPU fabric (NVLink, InfiniBand/Ethernet) and front-end / "
        "data-centre interconnect.")
    render_layer_card(4)

    st.markdown("---")
    st.markdown("#### Revenue by vendor (\\$B)")
    fign4 = px.bar(
        networking, x="year", y="revenue_b", color="company", barmode="group",
        color_discrete_map={"Arista": GREEN, "Ciena": BLUE, "Nokia NI": YELLOW},
        labels={"year": "Year", "revenue_b": "Revenue ($B)", "company": ""})
    fign4.update_layout(height=380, hovermode="x unified", legend_title="")
    st.plotly_chart(fign4, width="stretch")
    st.caption(
        "Segment-appropriate figures. Arista and Ciena are pure-plays (total "
        "revenue). Nokia is the Network Infrastructure segment only, which "
        "excludes mobile networks (EUR to USD approx). Cisco's Networking segment "
        "(about \\$28-30B) is larger but sits inside a diversified firm, so it is "
        "left out to keep the comparison clean. Switch silicon (Broadcom) sits in "
        "Silicon & IP. Sources: company filings.")

# --------------------------------------------------------------------------- #
# 4 · Power & Data Centers
# --------------------------------------------------------------------------- #
with tab_dc:
    st.markdown("### 5 · Data Centers")
    st.caption(
        "Shells, cooling and electricity. After packaging eases, grid "
        "interconnection and power become the next constraint. Chips ship in "
        "months; a high-voltage substation takes 3 to 5 years."
    )
    render_layer_card(5)

    st.markdown("---")
    st.markdown("#### Data center vs office construction (US, \\$B/year)")
    st.caption("US data center construction has overtaken office construction.")
    figdc = go.Figure()
    figdc.add_trace(go.Scatter(
        x=dc_con["year"], y=dc_con["datacenter_b"], name="Data centers",
        mode="lines+markers", line=dict(color=BLUE, width=3)))
    figdc.add_trace(go.Scatter(
        x=dc_con["year"], y=dc_con["office_b"], name="Offices",
        mode="lines+markers", line=dict(color=GREY, width=3, dash="dot")))
    figdc.update_layout(height=320, legend_title="", yaxis_title="$B / year",
                        xaxis_title="Year", hovermode="x unified")
    st.plotly_chart(figdc, width="stretch")
    st.caption(
        "US Census construction spending. Data center spend went from about \\$9B "
        "(2020) to about \\$41B (2025, up 344%); office fell from about \\$72B to "
        "about \\$49B (lowest since 2015). On a monthly run-rate the two crossed in "
        "Dec 2025 (data centers about \\$45B vs offices about \\$44B). Data center "
        "values for 2023 and 2024 are derived from Census-reported growth rates; "
        "2021-22 and the office mid-years are interpolated, flagged in the data "
        f"file. Data as of {DATA_UPDATED}.")

    st.markdown("---")
    st.markdown("#### Gigawatt-scale buildout")
    gw_named = gw["capacity_gw"].sum()
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Named GW-scale pipeline", f"{gw_named:.0f} GW",
              f"{len(gw)} flagship projects")
    p2.metric("Global DC capacity", "103 to 200 GW", "by 2030 (~2x)")
    p3.metric("DC power demand", "+165%", "by 2030 (Goldman, vs '23)")
    p4.metric("HV substation lead time", "3-5 yrs")

    st.markdown("#### Flagship gigawatt-scale projects (announced capacity, GW)")
    gwp = gw.sort_values("capacity_gw")
    figg4 = px.bar(
        gwp, x="capacity_gw", y="project", orientation="h", color="operator",
        text="capacity_gw",
        labels={"capacity_gw": "Capacity (GW)", "project": "", "operator": ""},
        hover_data={"location": True, "status_2026": True, "capacity_gw": ":.1f"})
    figg4.update_traces(texttemplate="%{text:.1f} GW", textposition="outside")
    figg4.update_layout(height=360, legend_title="",
                        xaxis_range=[0, gw["capacity_gw"].max() * 1.18])
    st.plotly_chart(figg4, width="stretch")

    st.markdown("**Project detail**")
    st.dataframe(
        gw[["project", "operator", "location", "capacity_gw", "status_2026",
            "note"]].rename(columns={
            "project": "Project", "operator": "Operator", "location": "Location",
            "capacity_gw": "GW", "status_2026": "Status", "note": "Note"}),
        width="stretch", hide_index=True)
    st.caption(
        "Capacity figures are announced or planned site totals at varying "
        "horizons (for example, Hyperion's 5 GW scales out to 2030), not all "
        "online today. Read them as the build pipeline, not installed base.")

    st.caption(
        "Grid context: high-voltage substation lead times run 3 to 5 years, 7 of "
        "13 US grid regions are projected below safety margins by 2030, and "
        "Goldman estimates about \\$720B of grid spend needed through 2030. Power, "
        "not capital, is the likely gate on the 2027+ buildout. Sources: Goldman "
        "Sachs, IEA, NextBigFuture, Introl, Sherwood, Data Center Knowledge.")

# --------------------------------------------------------------------------- #
# 5 · Hyperscalers — capex deep-dive
# --------------------------------------------------------------------------- #
with tab_hyper:
    st.markdown("### 6 · Hyperscalers")
    st.caption(
        "Google Cloud, Azure, AWS, Oracle. The demand engine of the value chain: "
        "their capex is the pull on every upstream layer."
    )
    render_layer_card(6)
    st.markdown("---")

    st.caption("All figures are total reported capex. No AI-share is applied.")
    g = view.sort_values(["company", "fiscal_year"]).copy()
    g["yoy_%"] = g.groupby("company")["capex_usd_b"].pct_change() * 100

    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Reported annual capex (\\$B)**")
        fig2 = px.bar(
            g, x="fiscal_year", y="capex_usd_b", color="company",
            barmode="group", color_discrete_map=COMPANY_COLORS,
            labels={"fiscal_year": "Fiscal year", "capex_usd_b": "Capex ($B)"})
        fig2.update_layout(height=360, hovermode="x unified", legend_title="")
        st.plotly_chart(fig2, width="stretch")
    with colB:
        st.markdown("**YoY capex growth (%)**")
        fig3 = px.bar(
            g[g["fiscal_year"] >= 2021], x="fiscal_year", y="yoy_%",
            color="company", barmode="group",
            color_discrete_map=COMPANY_COLORS,
            labels={"fiscal_year": "Fiscal year", "yoy_%": "YoY growth (%)"})
        fig3.update_layout(height=360, hovermode="x unified", legend_title="")
        st.plotly_chart(fig3, width="stretch")

    st.markdown("**Quarterly capex (\\$B)**")
    qv = capex_q.copy()
    qv["period_end"] = pd.to_datetime(qv["period_end"])
    qv["capex_b"] = qv["capex_usd_m"] / 1000.0
    qv["quarter"] = (qv["period_end"].dt.year.astype(str) + " Q" +
                     qv["period_end"].dt.quarter.astype(str))
    figq = px.bar(
        qv.sort_values("period_end"), x="quarter", y="capex_b",
        color="company", barmode="group", color_discrete_map=COMPANY_COLORS,
        labels={"quarter": "Calendar quarter of period end",
                "capex_b": "Capex ($B)"})
    figq.update_layout(height=380, hovermode="x unified", legend_title="")
    st.plotly_chart(figq, width="stretch")
    st.caption(
        "Quarterly cash purchases of PP&E from 10-Q and 10-K filings (SEC EDGAR "
        "XBRL). Cash-flow figures in 10-Qs are year-to-date, so quarters are "
        "derived by differencing; derived quarters sum exactly to the reported "
        "annual figures. Grouped by the calendar quarter in which each fiscal "
        "quarter ends (Microsoft and Oracle quarters are offset). Data as of "
        f"{DATA_UPDATED}.")

    st.markdown("---")
    st.markdown("#### How the capex is funded: capex vs operating cash flow")
    st.caption(
        "Capex as a share of operating cash flow, both from 10-K filings. Above "
        "100%, a company is spending more on capex than its operations "
        "generate and must fund the difference externally.")
    fund = capex.merge(
        ocf, on=["company", "fiscal_year"], suffixes=("", "_ocf"))
    fund = fund[fund["fiscal_year"] >= 2020].copy()
    fund["capex_pct_ocf"] = fund["capex_usd_m"] / fund["ocf_usd_m"] * 100
    figf = px.line(
        fund.sort_values("fiscal_year"), x="fiscal_year", y="capex_pct_ocf",
        color="company", markers=True, color_discrete_map=COMPANY_COLORS,
        labels={"fiscal_year": "Fiscal year",
                "capex_pct_ocf": "Capex / operating cash flow (%)"})
    figf.add_hline(y=100, line_dash="dash", line_color=GREY,
                   annotation_text="capex = operating cash flow")
    figf.update_layout(height=380, hovermode="x unified", legend_title="")
    st.plotly_chart(figf, width="stretch")
    fy25 = fund[fund["fiscal_year"] == 2025].sort_values(
        "capex_pct_ocf", ascending=False)
    ratio_line = ", ".join(
        f"{r.company} {r.capex_pct_ocf:.0f}%" for r in fy25.itertuples())
    st.caption(
        f"FY2025: {ratio_line}. Oracle already spends more than its operations "
        "generate and Amazon is close. The funding gap has moved to the bond "
        "market: hyperscalers issued \\$121B of bonds in 2025, four times the "
        "five-year average of about \\$28B, including Meta's \\$30B (the largest "
        "corporate bond since 2023), an Alphabet 100-year bond, and repeated "
        "Oracle issuance, at sub-5% average rates. Sources: 10-K filings (EDGAR "
        f"XBRL), Janus Henderson, Wolf Street. Data as of {DATA_UPDATED}.")

    st.markdown("**Capex & YoY growth by company**")
    st.dataframe(
        g[["company", "fiscal_year", "capex_usd_b", "yoy_%", "source_type"]]
        .rename(columns={
            "company": "Company", "fiscal_year": "FY", "capex_usd_b": "Capex $B",
            "yoy_%": "YoY %", "source_type": "Source"}).style.format({
            "Capex $B": "{:.1f}", "YoY %": "{:+.0f}"}),
        width="stretch", hide_index=True)
    st.caption(
        "Microsoft's fiscal year ends June 30 (not calendar-aligned). Amazon "
        "capex includes fulfilment and logistics, not only AWS, which matters "
        "when comparing totals across companies.")

    st.markdown("---")
    st.markdown("#### 2026 forward guidance")
    st.caption(
        "Guidance is reported on a broader basis (total capex including finance "
        "leases) than the cash PP&E actuals above, so it is shown as a separate "
        "series. Ranges are company guidance; markers are midpoints.")
    actual25 = view[view["fiscal_year"] == 2025].set_index("company")["capex_usd_b"]
    gtbl = guidance.copy()
    gtbl["fy2025_actual_b"] = gtbl["company"].map(actual25)
    gtbl["implied_growth_%"] = (gtbl["capex_mid_b"] / gtbl["fy2025_actual_b"] - 1) * 100

    figg = go.Figure()
    figg.add_trace(go.Bar(x=gtbl["company"], y=gtbl["fy2025_actual_b"],
                          name="FY2025 actual (cash PP&E)", marker_color=GREY))
    figg.add_trace(go.Bar(
        x=gtbl["company"], y=gtbl["capex_mid_b"],
        name="2026E guidance (midpoint, total capex)", marker_color=BLUE,
        error_y=dict(type="data", symmetric=False,
                     array=gtbl["capex_high_b"] - gtbl["capex_mid_b"],
                     arrayminus=gtbl["capex_mid_b"] - gtbl["capex_low_b"])))
    figg.update_layout(barmode="group", height=360, legend_title="",
                       yaxis_title="Capex ($B)", hovermode="x unified")
    st.plotly_chart(figg, width="stretch")
    st.metric("Big-5 2026E capex (sum of midpoints)",
              f"${gtbl['capex_mid_b'].sum():,.0f}B",
              f"+{(gtbl['capex_mid_b'].sum()/actual25.sum()-1)*100:.0f}% vs FY25 actual")
    st.dataframe(
        gtbl[["company", "fy2025_actual_b", "capex_low_b", "capex_mid_b",
              "capex_high_b", "implied_growth_%", "definition", "source"]].rename(
            columns={"company": "Company", "fy2025_actual_b": "FY25 actual $B",
                     "capex_low_b": "26E low", "capex_mid_b": "26E mid",
                     "capex_high_b": "26E high", "implied_growth_%": "Growth %",
                     "definition": "Definition", "source": "Source"}).style.format({
            "FY25 actual $B": "{:.1f}", "26E low": "{:.0f}", "26E mid": "{:.0f}",
            "26E high": "{:.0f}", "Growth %": "{:+.0f}"}),
        width="stretch", hide_index=True)
    st.caption(
        "Part of the jump is definitional (guidance includes finance leases). "
        "Microsoft also flagged about \\$25B of its 2026 step-up as memory and "
        "component cost inflation rather than added capacity, so higher capex "
        "does not map one-to-one to more compute. Oracle guidance covers its "
        "fiscal year ending May 2026.")

    st.markdown("---")
    st.markdown("#### Hyperscaler capex vs accelerator vendor revenue (\\$B)")
    st.caption(
        "Two reported series: combined Big-5 capex against NVIDIA and AMD "
        "data-center segment revenue. Shows how much of the capex lands at the "
        "chip vendors.")
    cap_by_year = (view.groupby("fiscal_year")["capex_usd_b"].sum()
                   .loc[lambda s: s.index >= 2020])
    av = accel_rev.groupby("calendar_year")["dc_revenue_b"].sum()
    figr = go.Figure()
    figr.add_trace(go.Bar(
        x=cap_by_year.index, y=cap_by_year.values,
        name="Big-5 hyperscaler capex", marker_color=GREY))
    figr.add_trace(go.Bar(
        x=av.index, y=av.values,
        name="NVIDIA + AMD data-center revenue", marker_color=GREEN))
    figr.update_layout(barmode="group", height=360, legend_title="",
                       yaxis_title="$B", xaxis_title="Year",
                       hovermode="x unified")
    st.plotly_chart(figr, width="stretch")
    st.caption(
        "NVIDIA's fiscal year ends in late January, so its FY2026 (\\$194B "
        "data-center revenue) is mapped to calendar 2025. AMD's data-center "
        "segment starts in 2022, when it was first reported. Hyperscaler capex "
        "also funds land, buildings, power and networking, and accelerator "
        "vendors sell to buyers beyond these five companies, so the two series "
        "are not a closed loop. Sources: company filings. Data as of "
        f"{DATA_UPDATED}.")

# --------------------------------------------------------------------------- #
# 6 · NeoClouds
# --------------------------------------------------------------------------- #
with tab_neo:
    st.markdown("### 7 · NeoClouds")
    st.caption(
        "Specialised GPU-rental providers between silicon and the AI labs. Much "
        "of the build is funded by GPU-backed debt.")
    render_layer_card(7)
    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    c1.metric("CoreWeave backlog (end-2025)", "$66.8B", "~$100B by Q1'26")
    c2.metric("Nebius 2026E capex", "$20-25B")
    c3.metric("Sector GPU-backed debt", ">$20B")

    st.markdown("**Contracted backlog vs 2025 revenue (\\$B)**")
    fign = go.Figure()
    fign.add_trace(go.Bar(x=neo["company"], y=neo["revenue_2025_b"],
                          name="2025 revenue", marker_color=GREEN))
    fign.add_trace(go.Bar(x=neo["company"], y=neo["backlog_b"],
                          name="Contracted backlog", marker_color=BLUE))
    fign.update_layout(barmode="group", height=320, legend_title="",
                       yaxis_title="$B", hovermode="x unified")
    st.plotly_chart(fign, width="stretch")
    st.caption(
        "CoreWeave's backlog is far larger than its current revenue, and "
        "concentrated (the OpenAI deal added \\$11.2B). Blanks are not disclosed; "
        "Crusoe and Lambda are private and report little.")

    st.markdown("**Provider snapshot**")
    st.dataframe(
        neo[["company", "ownership", "revenue_2025_b", "revenue_2026e_b",
             "backlog_b", "capex_2026e_b", "power_contracted_gw", "valuation_b",
             "key_financing_signal"]].rename(columns={
            "company": "Company", "ownership": "Ownership",
            "revenue_2025_b": "Rev 2025 $B", "revenue_2026e_b": "Rev 2026E $B",
            "backlog_b": "Backlog $B", "capex_2026e_b": "Capex 2026E $B",
            "power_contracted_gw": "Power GW", "valuation_b": "Valuation $B",
            "key_financing_signal": "Financing signal"}),
        width="stretch", hide_index=True)
    st.caption(
        "NeoClouds carry over \\$20B in GPU-backed debt. GPUs depreciate on a 4 to "
        "6 year schedule, and rental pricing can move faster. Customer "
        "concentration on a few anchor tenants is the main risk. Sources: company "
        "filings and press.")

# --------------------------------------------------------------------------- #
# 8 · AI Labs (demand)
# --------------------------------------------------------------------------- #
with tab_labs:
    st.markdown("### 8 · AI Labs")
    st.caption(
        "Model developers consume the compute the rest of the chain supplies. "
        "Their revenue and compute commitments are the demand signal, and "
        "increasingly the financing counterparty behind NeoCloud backlogs.")
    render_layer_card(8)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Frontier-lab revenue (annualized run-rate, \\$B)")
        figlr = px.bar(
            labrev.sort_values("revenue_b"), x="revenue_b", y="company",
            orientation="h", text="revenue_b", color="company",
            color_discrete_map={"Anthropic": "#D2691E", "OpenAI": "#10A37F",
                                "xAI": GREY, "Mistral": RED},
            labels={"revenue_b": "Run-rate revenue ($B)", "company": ""})
        figlr.update_traces(texttemplate="$%{text:.1f}B", textposition="outside")
        figlr.update_layout(height=320, showlegend=False,
                            xaxis_range=[0, labrev["revenue_b"].max() * 1.2])
        st.plotly_chart(figlr, width="stretch")
        st.caption(
            "Annualized run-rates at various dates (Anthropic May-26, OpenAI "
            "Feb-26, xAI Q3-25, Mistral Jan-26). Anthropic has overtaken OpenAI, "
            "going from \\$1B to \\$47B in about 18 months. Source: Epoch AI.")
    with c2:
        st.markdown("#### Frontier capability by lab (GPQA-Diamond, %)")
        figb = px.line(
            bench_lab, x="date", y="score", color="lab", markers=True,
            color_discrete_map={"OpenAI": "#10A37F", "Anthropic": "#D2691E",
                                "Google": BLUE, "Meta": "#7B68EE",
                                "DeepSeek (China)": RED},
            labels={"date": "", "score": "GPQA-Diamond (%)", "lab": ""},
            hover_data=["model"])
        figb.add_hline(y=65, line_dash="dash", line_color=GREY,
                       annotation_text="PhD-expert ~65%")
        figb.update_layout(height=320, legend_title="", yaxis_range=[0, 100],
                           hovermode="x unified")
        st.plotly_chart(figb, width="stretch")
        st.caption(
            "Best published GPQA-Diamond score per lab at major model releases. "
            "Scores are taken from model and system cards where published "
            "(GPT-4 35.7 from the GPQA paper, Claude 3.5 Sonnet 59.4, o1 78.0, "
            "Gemini 2.5 Pro 84.0, DeepSeek R1 71.5); two points are estimates, "
            "flagged in the data file. Chinese labs have closed most of the "
            f"gap. Data as of {DATA_UPDATED}.")

    st.markdown("#### ChatGPT weekly active users (millions)")
    figw = px.area(chatgpt, x="date", y="wau_m",
                   labels={"date": "", "wau_m": "Weekly active users (M)"})
    figw.update_traces(line_color="#10A37F",
                       fillcolor="rgba(16,163,127,0.2)")
    figw.update_layout(height=280)
    st.plotly_chart(figw, width="stretch")
    st.caption(
        "OpenAI disclosures. Weekly active users went from 100M (Aug-23) to 900M "
        "(Feb-26).")

    st.caption(
        "Revenue is concentrating in Anthropic and OpenAI, while frontier "
        "benchmark scores are converging in the 90s. Lab revenue and multi-year "
        "compute commitments are the demand that underwrites the capex stack.")

    st.markdown("#### Notable compute-commitment signals")
    deals = pd.DataFrame([
        {"Lab": "OpenAI", "Counterparty": "CoreWeave",
         "Signal": "$11.2B backlog deal (multi-year GPU capacity)"},
        {"Lab": "Meta AI", "Counterparty": "Nebius",
         "Signal": "$27B compute deal (2027 capacity secured)"},
        {"Lab": "Anthropic", "Counterparty": "Google / Amazon",
         "Signal": "Anchor tenant on TPU & Trainium capacity"},
        {"Lab": "xAI", "Counterparty": "Self-build (Colossus)",
         "Signal": "100k+ GPU clusters; vertical power build-out"},
    ])
    st.dataframe(deals, width="stretch", hide_index=True)
    st.caption(
        "Full data provenance for every figure in the dashboard is logged in "
        "`notes/sources.md` (URLs + SEC accession numbers).")

# --------------------------------------------------------------------------- #
# 9 · System Integrators
# --------------------------------------------------------------------------- #
with tab_si:
    st.markdown("### 9 · System Integrators")
    st.caption(
        "The services firms that deploy AI into enterprises. Model capability "
        "is converging, but getting it into production workflows remains "
        "services-heavy, which makes integrators a measurable read on actual "
        "enterprise adoption.")

    st.markdown("---")
    st.markdown("#### Revenue by key player (\\$B)")
    sicolors = {"Accenture": "#A100FF", "TCS": BLUE, "Infosys": GREEN,
                "Capgemini": YELLOW}
    figsi2 = px.bar(
        si, x="year", y="revenue_b", color="company", barmode="group",
        color_discrete_map=sicolors,
        labels={"year": "Fiscal year", "revenue_b": "Revenue ($B)",
                "company": ""})
    figsi2.update_layout(height=380, hovermode="x unified", legend_title="")
    st.plotly_chart(figsi2, width="stretch")
    st.caption(
        "Fiscal years differ (Accenture ends August, TCS and Infosys end March, "
        "Capgemini is calendar-year). Capgemini reports in EUR; USD conversion "
        "is approximate and flagged in the data. Deloitte and IBM Consulting "
        "are comparable players but are private or embedded in a larger group. "
        "Sources: company results.")

    st.markdown("#### Accenture GenAI new bookings (\\$B)")
    figgb = px.bar(
        genai_bookings, x="period", y="bookings_b",
        labels={"period": "", "bookings_b": "New bookings ($B)"})
    figgb.update_traces(marker_color="#A100FF")
    figgb.update_layout(height=300)
    st.plotly_chart(figgb, width="stretch")
    st.caption(
        "GenAI new bookings as disclosed by Accenture: about \\$3B in FY2024, "
        "then \\$5.9B in FY2025 with a rising quarterly run-rate (\\$1.2B to \\$1.8B "
        "through the year). The clearest public number on enterprise AI "
        f"deployment demand. Source: Accenture 8-K filings. Data as of "
        f"{DATA_UPDATED}.")

# --------------------------------------------------------------------------- #
# 10 · Telecoms (context)
# --------------------------------------------------------------------------- #
with tab_telco:
    st.markdown("### 10 · Telecoms")
    st.caption(
        "Shown for context. Global telecom capex has stayed roughly flat at about "
        "\\$300B while hyperscaler capex has grown past it.")

    hyp_year = capex.groupby("fiscal_year")["capex_usd_b"].sum()
    guide_total = float(guidance["capex_mid_b"].sum())
    rows = []
    for y in range(2020, 2025):
        rows.append({"year": y, "capex_b": float(
            telco_capex.loc[telco_capex.year == y, "telecom_capex_b"].iloc[0]),
            "series": "Global telecom capex"})
    for y in range(2020, 2026):
        if y in hyp_year.index:
            rows.append({"year": y, "capex_b": float(hyp_year.loc[y]),
                         "series": "Big-5 hyperscaler capex"})
    rows.append({"year": 2026, "capex_b": guide_total,
                 "series": "Big-5 hyperscaler capex"})
    cmpdf = pd.DataFrame(rows)

    k1, k2, k3 = st.columns(3)
    k1.metric("Global telecom capex 2024", "~$295B", "lowest since 2011")
    k2.metric("Big-5 hyperscaler capex 2025", f"${hyp_year.loc[2025]:.0f}B",
              "overtook telecom")
    k3.metric("Big-5 2026E", f"${guide_total:.0f}B",
              f"~{guide_total/295:.1f}x global telecom")

    st.markdown("#### Capex: hyperscalers vs telecoms (\\$B)")
    figt = px.line(cmpdf, x="year", y="capex_b", color="series", markers=True,
                   color_discrete_map={"Global telecom capex": GREY,
                                       "Big-5 hyperscaler capex": BLUE},
                   labels={"year": "Year", "capex_b": "Capex ($B)", "series": ""})
    figt.update_layout(height=360, hovermode="x unified", legend_title="")
    st.plotly_chart(figt, width="stretch")
    st.caption(
        "Telecom is global industry capex (MTN Consulting). Hyperscaler is the "
        "Big-5 (Alphabet, Amazon, Meta, Microsoft, Oracle); 2026 is the guidance "
        "midpoint. Hyperscaler capex has passed the whole global telecom "
        "industry's.")

    st.markdown("#### US carriers: capex and revenue since 2020 (\\$B)")
    tc1, tc2 = st.columns(2)
    uscolors = {"AT&T": BLUE, "Verizon": RED, "T-Mobile US": "#E20074"}
    with tc1:
        figuc = px.bar(telco_us, x="year", y="capex_b", color="company",
                       barmode="group", color_discrete_map=uscolors,
                       labels={"year": "Year", "capex_b": "Capex ($B)",
                               "company": ""})
        figuc.update_layout(height=330, hovermode="x unified", legend_title="",
                            title="Capex")
        st.plotly_chart(figuc, width="stretch")
    with tc2:
        figur = px.bar(telco_us, x="year", y="revenue_b", color="company",
                       barmode="group", color_discrete_map=uscolors,
                       labels={"year": "Year", "revenue_b": "Revenue ($B)",
                               "company": ""})
        figur.update_layout(height=330, hovermode="x unified", legend_title="",
                            title="Revenue")
        st.plotly_chart(figur, width="stretch")
    st.caption(
        "Reported figures from company results. AT&T revenue includes "
        "WarnerMedia until its spin-off in April 2022, which explains the step "
        "down. Verizon's 2022 capex peak reflects the C-Band spectrum buildout; "
        "T-Mobile's 2021-22 peak reflects Sprint network integration. Combined "
        "big-3 capex has been flat to declining since 2022 while hyperscaler "
        f"capex tripled. Data as of {DATA_UPDATED}.")

    st.markdown("#### Major telcos: revenue & capex (latest year, \\$B)")
    figtp = px.scatter(
        telco_players, x="revenue_b", y="capex_b", color="region",
        text="company", size="capex_b", size_max=28,
        color_discrete_map={"US": BLUE, "Europe": GREEN},
        labels={"revenue_b": "Revenue ($B)", "capex_b": "Capex ($B)",
                "region": ""})
    figtp.update_traces(textposition="top center")
    figtp.update_layout(height=400, legend_title="")
    st.plotly_chart(figtp, width="stretch")
    st.dataframe(
        telco_players[["company", "region", "revenue_b", "capex_b", "year",
                       "note"]].rename(columns={
            "company": "Company", "region": "Region", "revenue_b": "Revenue $B",
            "capex_b": "Capex $B", "year": "Year", "note": "Note"}),
        width="stretch", hide_index=True)
    st.caption(
        "Latest available year (mostly 2024); some figures approximate. Deutsche "
        "Telekom revenue/capex include T-Mobile US (overlaps the US row). Major "
        "US + European operators, not exhaustive. Sources: company filings / "
        "MTN Consulting.")
