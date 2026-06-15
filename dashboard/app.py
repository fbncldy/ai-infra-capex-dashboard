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
    page_title="The AI Value Chain",
    page_icon="🛰️",
    layout="wide",
)

# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def load_capex() -> pd.DataFrame:
    df = pd.read_csv(DATA / "hyperscaler_capex.csv")
    df["capex_usd_b"] = df["capex_usd_m"] / 1000.0
    return df


def load_guidance() -> pd.DataFrame:
    return pd.read_csv(DATA / "capex_guidance_2026.csv")


def load_neoclouds() -> pd.DataFrame:
    return pd.read_csv(DATA / "neoclouds.csv")


def load_cowos() -> pd.DataFrame:
    return pd.read_csv(DATA / "cowos_capacity.csv")


def load_hbm() -> pd.DataFrame:
    return pd.read_csv(DATA / "hbm_market.csv")


def load_gw_projects() -> pd.DataFrame:
    return pd.read_csv(DATA / "gigawatt_projects.csv")


def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name)


capex = load_capex()
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
capex_q = load_csv("hyperscaler_capex_quarterly.csv")
accel_rev = load_csv("accelerator_dc_revenue.csv")
telco_us = load_csv("telecom_us_series.csv")
ocf = load_csv("hyperscaler_ocf.csv")
si = load_csv("system_integrators.csv")
genai_bookings = load_csv("accenture_genai_bookings.csv")
semis = load_csv("semis_billings.csv")
net_full = load_csv("network_players_full.csv")
mobile_net = load_csv("mobile_networks.csv")
mobile_traffic = load_csv("mobile_traffic.csv")
fixed_traffic = load_csv("fixed_traffic.csv")
server_margins = load_csv("server_margins.csv")
hyp_returns = load_csv("hyperscaler_returns.csv")
vint = load_csv("vertical_integration.csv")
inference_prices = load_csv("inference_prices.csv")
telco_tsr = load_csv("telco_tsr.csv")
telco_roce = load_csv("telco_roce.csv")
usage_depth = load_csv("ai_usage_depth.csv")
ent_spend = load_csv("enterprise_ai_spend.csv")
yc_share = load_csv("yc_ai_share.csv")

DATA_UPDATED = "June 2026"

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


st.title("The AI Value Chain")
st.caption(
    "Who builds, who pays and who earns across the AI buildout: company "
    "financials, capacity constraints and demand signals from silicon and "
    "power through hyperscalers and the AI labs to the telecom networks that "
    "distribute the output. Figures from filings and primary sources."
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
    st.markdown("### 0 · Overview")

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
        f"- **The build-out is redistributing value across the chain.** The "
        f"scarcities AI created are all easing at once: "
        f"compute is getting cheaper, frontier models are converging, and the "
        f"cost of building software has collapsed. As those rents compress, "
        f"value flows toward what was already scarce before AI, namely "
        f"distribution, proprietary data, regulatory position and customer "
        f"switching costs. The rest of this summary traces where it is moving, "
        f"layer by layer.\n"
        f"- **The spend has reached a scale with few precedents, and it now "
        f"leans on debt.** Big-5 capex (Microsoft, Alphabet, Amazon, Meta, "
        f"Oracle) hit about **\\${total_now:,.0f}B** in FY2025 and is guided "
        f"near **\\${guide26:,.0f}B** for 2026, more than global upstream oil "
        f"and gas investment (about \\$570B). With capex at 30 to 75% of "
        f"revenue, cash flow no longer covers it: the group issued \\$121B of "
        f"bonds in 2025, four times its five-year average.\n"
        f"- **The binding constraint keeps moving downstream, and each shortage "
        f"becomes the next layer's cost.** CoWoS packaging and HBM memory are "
        f"sold out through 2026, which already shows up as Microsoft "
        f"attributing about \\$25B of its 2026 guidance to memory and component "
        f"inflation. Power is next in line: about {gw['capacity_gw'].sum():.0f} "
        f"GW of named gigawatt projects wait on grid connections that take 3 to "
        f"5 years.\n"
        f"- **The capex baton has passed from telecoms to hyperscalers.** "
        f"Global telecom capex (about \\$295B, the lowest since 2011) is now a "
        f"few weeks of hyperscaler spending, and the equipment vendors are "
        f"following the money: Nokia bought Infinera for AI data-center optics "
        f"while Arista quadrupled and Ericsson shrank.\n"
        f"- **Infrastructure captures the value today, but on a clock.** Demand "
        f"is shifting from one-off training runs to always-on inference, which "
        f"invites competition from AMD, custom hyperscaler silicon and "
        f"inference startups and squeezes margins over time, even as cheaper "
        f"inference keeps widening demand. NVIDIA's training moat looks sturdier "
        f"than its inference one, and the layer likely drifts toward essential "
        f"but lower-margin economics, closer to cloud. The financing is also "
        f"circular and concentrated: lab compute commitments underwrite "
        f"NeoCloud backlogs that collateralise over \\$20B of GPU-backed debt "
        f"from a single chip vendor, so a stumble at the lab layer would travel "
        f"back through credit.\n"
        f"- **The labs face real commoditisation pressure.** 900M people use "
        f"ChatGPT weekly but only 5 to 6% pay, frontier scores have converged, "
        f"open models are closing the gap, and switching costs at the API are "
        f"near zero. The labs that stay more than low-margin utilities will be "
        f"the ones that own distribution, compound proprietary data, or move "
        f"up into applications before application companies move down.\n"
        f"- **In software, cheap building changes which moats matter.** When "
        f"anyone can generate code, advantages built on engineering complexity "
        f"erode, while the structurally scarce ones hold: workflow embedding, "
        f"switching costs, proprietary data and regulatory position. Mid-market horizontal SaaS is the most exposed, "
        f"while vertical depth and data flywheels move up the defensibility "
        f"stack. The integrators (Accenture and peers) are early winners "
        f"because getting AI into production is still services-heavy.\n"
        f"- **Bottom line: value accrues to whoever owns what AI cannot "
        f"manufacture,** distribution, data, trust and lock-in, which is why "
        f"the whole stack is racing to integrate (matrix below). The telecom "
        f"precedent rhymes, but the incumbents here produce the intelligence "
        f"itself and already span the stack, so disruption from outside is "
        f"harder than the wave that commoditised carriers."
    )
    st.caption(f"Data last updated {DATA_UPDATED}.")
    st.markdown("---")

    st.markdown("##### Spend & demand (downstream)")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric(f"Big-5 total capex FY{YR}", f"${total_now:,.0f}B", f"{yoy:+.0f}% YoY")
    d2.metric("Big-5 2026E guidance", f"${guide26:,.0f}B",
              f"+{(guide26/total_now-1)*100:.0f}% vs FY25")
    d3.metric(f"Capex CAGR FY{first_yr}-{YR}", f"{cagr*100:.0f}%/yr",
              "AI-era acceleration")
    d4.metric("NeoCloud backlog (CoreWeave)", "~$100B", "Q1 2026")

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
        "Figures are total reported capex; companies do not disclose an "
        "AI-only split. Totals are shown above each bar. Bars for "
        "2018 to 2025 are reported cash PP&E; the hatched 2026E bar is the "
        "guidance midpoint, which is reported on a broader basis (total capex "
        "including finance leases). Microsoft's fiscal year ends in June and "
        "Oracle's in May, so their years are not calendar-aligned.")
    st.caption(
        f"FY24 to FY25, the five companies went from \\${total_prev:,.0f}B to "
        f"\\${total_now:,.0f}B. Guidance points to about \\${totals[2026]:,.0f}B in "
        "2026.")

    st.markdown("#### Value-chain map")
    st.caption("The ten steps, upstream to downstream, and what each one does.")
    vc_rows = [
        ("1 · Silicon & IP",
         "Designs the accelerators and the high-bandwidth memory stacked beside "
         "them. NVIDIA dominates the logic; HBM supply is the first hard limit "
         "on how many chips can ship."),
        ("2 · Foundry & Packaging",
         "Manufactures and packages the chips. TSMC makes nearly all of them, "
         "and its CoWoS advanced packaging is the single tightest physical "
         "bottleneck in the chain."),
        ("3 · Servers",
         "Assembles accelerators, memory and networking into deployable racks. "
         "Margins stay thin because the scarce input is priced by NVIDIA, "
         "leaving system builders little pricing power."),
        ("4 · Networking",
         "Wires servers into clusters and links data centers to each other. The "
         "one layer that sells into both the AI buildout upstream and the "
         "carrier networks at the far end of the chain."),
        ("5 · Data Centers",
         "Houses, cools and powers the clusters. Power has become the binding "
         "constraint ahead of capital or land, with grid connections taking 3 "
         "to 5 years."),
        ("6 · Hyperscalers",
         "Operate the data centers and rent compute at scale. They are the "
         "demand pull of the whole chain, funding the upstream buildout from "
         "cash flow and, increasingly, debt."),
        ("7 · NeoClouds",
         "Specialist providers that rent GPUs alongside the hyperscalers, "
         "financed largely by debt secured against the GPUs themselves and by "
         "anchor-tenant backlogs."),
        ("8 · AI Labs",
         "Consume compute to train and serve models. Their multi-year compute "
         "commitments are the contracts that underwrite the buildout below "
         "them."),
        ("9 · System Integrators",
         "Deploy models into enterprises. A services-heavy channel and one of "
         "the most measurable reads on real, paid adoption."),
        ("10 · Telecoms",
         "Distribute model output to users over fixed and mobile networks. "
         "Essential to delivery, yet a decade of traffic growth shows the layer "
         "captures little of the value it carries."),
    ]
    vc_html = [
        "<table style='width:100%;border-collapse:collapse;font-size:0.92rem;"
        "line-height:1.4;'>",
        "<thead><tr>"
        "<th style='text-align:left;padding:8px 12px;width:200px;"
        "border-bottom:2px solid #c8ccd0;'>Step</th>"
        "<th style='text-align:left;padding:8px 12px;"
        "border-bottom:2px solid #c8ccd0;'>Role in the value chain</th>"
        "</tr></thead><tbody>",
    ]
    for step, role in vc_rows:
        vc_html.append(
            "<tr>"
            "<td style='padding:8px 12px;vertical-align:top;"
            "border-bottom:1px solid #ebedf0;font-weight:600;'>"
            f"{step}</td>"
            "<td style='padding:8px 12px;vertical-align:top;"
            f"border-bottom:1px solid #ebedf0;'>{role}</td>"
            "</tr>")
    vc_html.append("</tbody></table>")
    st.markdown("".join(vc_html), unsafe_allow_html=True)

    st.markdown("#### Who is integrating across the chain")
    st.caption(
        "Where the major players sit and where they are pushing. The striking "
        "pattern is that almost everyone is integrating: NVIDIA pushing down "
        "from silicon into systems and cloud, the hyperscalers building their "
        "own chips, OpenAI building data centers, and Google spanning the most "
        "of the chain. The focused players (TSMC in foundry, Broadcom in "
        "silicon) are the exception.")
    layer_cols = [("silicon", "Silicon"), ("foundry", "Foundry"),
                  ("servers", "Servers"), ("networking", "Network"),
                  ("datacenters", "Data ctr"), ("cloud", "Cloud"),
                  ("neoclouds", "NeoCloud"), ("labs", "Labs"),
                  ("integrators", "Integr."), ("telecoms", "Telco")]
    cell = {"core": ("●", "background:#4285F4;color:#fff;"),
            "expanding": ("◐", "background:#c6dafc;color:#1a3a6b;"),
            "": ("", "")}
    vi_html = ["<table style='width:100%;border-collapse:collapse;"
               "font-size:0.8rem;text-align:center;'>",
               "<thead><tr><th style='text-align:left;padding:6px 8px;"
               "border-bottom:2px solid #c8ccd0;'>Player</th>"]
    for _, label in layer_cols:
        vi_html.append("<th style='padding:6px 4px;border-bottom:2px solid "
                       f"#c8ccd0;font-weight:600;'>{label}</th>")
    vi_html.append("</tr></thead><tbody>")
    for _, r in vint.iterrows():
        vi_html.append("<tr><td style='text-align:left;padding:6px 8px;"
                       "border-bottom:1px solid #ebedf0;font-weight:600;'>"
                       f"{r['player']}</td>")
        for col, _ in layer_cols:
            val = r[col] if isinstance(r[col], str) else ""
            sym, style = cell.get(val, ("", ""))
            vi_html.append(f"<td style='padding:6px 4px;border-bottom:1px "
                           f"solid #ebedf0;{style}'>{sym}</td>")
        vi_html.append("</tr>")
    vi_html.append("</tbody></table>")
    st.markdown("".join(vi_html), unsafe_allow_html=True)
    st.caption(
        "● core business · ◐ expanding into. Telco stays empty: no AI-stack "
        "player has moved into carrier networks, the one layer still left to "
        "others. Assessment based on disclosed products and announced projects.")

# --------------------------------------------------------------------------- #
# 1 · Silicon & IP  (accelerator design + HBM memory)
# --------------------------------------------------------------------------- #
with tab_silicon:
    st.markdown("### 1 · Silicon & IP")
    st.markdown(
        "- **Semiconductors are a \\$792B industry (2025) that has "
        "historically moved in 3 to 4 year cycles.** AI demand drove a 26% "
        "jump in 2025 and a forecast first one-trillion-dollar year in 2026; "
        "the open question is whether this is the steepest cycle yet or a "
        "structural break.\n"
        "- **NVIDIA dominates the accelerator layer**, with about \\$115B of "
        "data-center revenue in FY2025; AMD is a distant second, and the "
        "hyperscalers are building in-house alternatives (Google TPU, Amazon "
        "Trainium) with Broadcom and Marvell.\n"
        "- **High-bandwidth memory is the supply-constrained input:** SK Hynix "
        "(about 57% share), Micron and Samsung are sold out through 2026.\n"
        "- **Silicon is the first gate on AI capacity:** shipping more "
        "accelerators requires more HBM and more advanced packaging alongside "
        "fab starts.")

    st.markdown("---")
    st.markdown("#### Global semiconductor sales since 1990 (\\$B)")
    figsem = go.Figure()
    hist = semis[semis["source_type"] == "reported"]
    fc = semis[semis["source_type"] == "forecast"]
    figsem.add_trace(go.Bar(x=hist["year"], y=hist["sales_b"],
                            marker_color=BLUE, name="Reported"))
    figsem.add_trace(go.Bar(x=fc["year"], y=fc["sales_b"], marker_color=BLUE,
                            marker_pattern_shape="/", name="2026 forecast"))
    figsem.update_layout(height=380, yaxis_title="Annual sales ($B)",
                         xaxis_title="Year", legend_title="",
                         hovermode="x unified")
    st.plotly_chart(figsem, width="stretch")
    st.caption(
        "WSTS / SIA worldwide semiconductor billings, annual. The industry has "
        "cycled repeatedly (2001 down 32%, 2009, 2019, 2023) but each cycle has "
        "peaked higher. The current AI-driven leg (+26% in 2025, about "
        "\\$1T forecast for 2026) is the steepest rise since the dot-com era. "
        f"Sources: WSTS, SIA. Data as of {DATA_UPDATED}.")

    st.markdown("#### Revenue by key player (\\$B)")
    figsi = px.bar(
        silicon_rev, x="fy", y="revenue_b", color="company", barmode="group",
        labels={"fy": "Fiscal year", "revenue_b": "Revenue ($B)", "company": ""},
        color_discrete_map={"NVIDIA": GREEN, "AMD": RED, "Broadcom": BLUE,
                            "Micron": YELLOW, "SK Hynix": PURPLE})
    figsi.update_layout(height=400, hovermode="x unified", legend_title="")
    st.plotly_chart(figsi, width="stretch")
    st.caption(
        "Total company revenue. NVIDIA / Broadcom / Micron fiscal years are "
        "offset from calendar. NVIDIA's data-center segment alone was about "
        "\\$115B in FY2025. On memory, SK Hynix is the HBM leader (about 57% "
        "share) and the key supplier of the constrained input; Micron is the "
        "US-listed peer. SK Hynix and Micron figures are currency-converted "
        "and approximate. Sources: company filings.")

# --------------------------------------------------------------------------- #
# 2 · Foundry & Packaging  (TSMC CoWoS + the supply ceiling)
# --------------------------------------------------------------------------- #
with tab_foundry:
    st.markdown("### 2 · Foundry & Packaging")
    st.markdown(
        "- **Leading-edge manufacturing is effectively a one-company market:** "
        "TSMC holds about 70% of foundry revenue and makes nearly every AI "
        "accelerator.\n"
        "- **Samsung Electronics and Intel are the only credible challengers** "
        "and both are spending tens of billions a year on fabs with limited "
        "share gains; both cut capex in 2025 while TSMC raised it.\n"
        "- **The chokepoint is CoWoS advanced packaging**, the step that "
        "mounts logic dies and HBM on one interposer: capacity grew roughly "
        "10x since 2023 and is still fully booked, with OSAT partners (ASE, "
        "Amkor) absorbing overflow.\n"
        "- **Whoever controls packaging allocation decides which AI chips "
        "ship**, which gives this single process step strategic weight far "
        "beyond its 7 to 9% share of TSMC revenue.")

    st.markdown("---")
    st.markdown("#### Revenue & capex by key player (\\$B)")
    st.caption(
        "TSMC is the pure-play foundry. Samsung Electronics and Intel are IDMs: "
        "figures are total company (Samsung includes memory, phones and "
        "displays; Intel includes products), so they overstate the foundry "
        "businesses but show the relative investment scale. Samsung in "
        "USD-converted KRW.")
    fc1, fc2 = st.columns(2)
    fcolors = {"TSMC": BLUE, "Samsung Electronics": GREEN, "Intel": GREY}
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
        "Sources: TSMC, Samsung and Intel results. TSMC 2026E "
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
    st.markdown(
        "- **Server makers turn GPUs into deployable systems and were among "
        "the first beneficiaries of the AI buildout**, with revenue inflecting "
        "from 2023.\n"
        "- **The listed players are Dell (ISG), Supermicro and HPE**, but the "
        "largest AI-server volumes flow through Taiwanese ODMs (Foxconn, "
        "Quanta, Wistron) building directly for hyperscalers, a lower-margin "
        "and far less disclosed channel.\n"
        "- **GPU allocation drives value in this layer:** vendors who secured "
        "NVIDIA supply early, like Supermicro, grew from \\$3B revenue toward "
        "a \\$40B guidance in six years, and Dell's ISG jumped 40% in its "
        "latest fiscal year.\n"
        "- **Margins stay thin and volatile** because the scarce input, the "
        "accelerator, is priced by NVIDIA, leaving system builders little "
        "pricing power.")

    st.markdown("---")
    st.markdown("#### Server revenue by vendor (\\$B)")
    figsy = px.bar(
        systems, x="year", y="revenue_b", color="company", barmode="group",
        color_discrete_map={"Dell ISG": BLUE, "Supermicro": GREEN,
                            "HPE Server": YELLOW,
                            "Foxconn (Cloud & Networking)": RED,
                            "Quanta (servers)": PURPLE,
                            "Wistron (servers)": "#00838F"},
        labels={"year": "Fiscal year", "revenue_b": "Revenue ($B)",
                "company": ""})
    figsy.update_layout(height=400, hovermode="x unified", legend_title="")
    st.plotly_chart(figsy, width="stretch")
    st.caption(
        "Listed OEMs (Dell ISG, Supermicro, HPE) plus the Taiwanese ODMs that "
        "carry most AI-server volume. Foxconn's Cloud & Networking segment "
        "alone (about \\$90B in 2025) is larger than any branded OEM, which is "
        "the point: the visible brands are a minority of the build. ODM figures "
        "are server/cloud-segment estimates (currency-converted, approximate); "
        "their group totals are far larger but mostly non-server. Dell fiscal "
        "years are plotted against the calendar year they mostly cover (FY2026, "
        "\\$60.8B, appears as 2025); 2026 bars for Supermicro (\\$38.9-40.4B) "
        "and HPE are guidance. Sources: company filings.")

    st.markdown("#### Operating margin: assembly vs the chip it ships (%)")
    sm = server_margins.sort_values("op_margin_pct")
    figsm = px.bar(
        sm, x="op_margin_pct", y="company", orientation="h",
        color=sm["company"].eq("NVIDIA").map({True: "chip", False: "assembler"}),
        color_discrete_map={"chip": GREEN, "assembler": GREY},
        text="op_margin_pct",
        labels={"op_margin_pct": "Operating margin (%)", "company": ""})
    figsm.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
    figsm.update_layout(height=300, showlegend=False,
                        xaxis_range=[0, 70])
    st.plotly_chart(figsm, width="stretch")
    st.caption(
        "Latest-year segment or group operating margin. The server makers earn "
        "single digits to low teens because the scarce input, the accelerator, "
        "is priced by NVIDIA, which itself runs about a 60% operating margin on "
        "the same box. The ODMs (Foxconn around 3-4%) sit lowest of all. HPE and "
        "Foxconn figures are estimates; others are reported. Sources: company "
        f"filings. Data as of {DATA_UPDATED}.")

# --------------------------------------------------------------------------- #
# 4 · Networking
# --------------------------------------------------------------------------- #
with tab_network:
    st.markdown("### 4 · Networking")
    st.markdown(
        "- **As clusters pass 100k GPUs the network increasingly sets "
        "training efficiency, shifting value to back-end fabrics and "
        "optics.** NVIDIA bundles its own interconnect (NVLink, "
        "InfiniBand), Arista is the clearest listed pure-play beneficiary with "
        "revenue roughly quadrupling since 2020, and Broadcom supplies the "
        "switch silicon (covered under Silicon & IP).\n"
        "- **The industry is splitting into a data-center camp and a mobile "
        "camp with opposite trajectories.** Data-center networking grows with "
        "AI capex, while mobile-network equipment (Ericsson, Nokia Mobile "
        "Networks, Huawei) shrinks or stagnates as 5G buildouts mature.\n"
        "- **Nokia's \\$2.3B acquisition of Infinera (completed February "
        "2025) is the clearest strategic signal:** a mobile-era vendor buying "
        "optical networking scale specifically to chase AI data-center "
        "interconnect, repositioning away from its shrinking mobile core.\n"
        "- **The revenue base is moving from carriers to hyperscalers.** US "
        "carrier capex guidance for 2026 sits near \\$50B with no 6G cycle "
        "ahead, so vendors selling to telecoms face a flat market while "
        "hyperscaler-facing vendors ride a budget that doubled in two years; "
        "Arista's quadrupling and Ericsson's decline track that divide.\n"
        "- **Optics and switch-ASIC supply are the layer's bottlenecks** as "
        "training spreads across sites and rack power density rises.")

    st.markdown("---")
    st.markdown("#### Key players: total revenue and capex (\\$B)")
    npcolors = {"Arista": GREEN, "Ciena": BLUE, "Nokia": YELLOW,
                "Ericsson": "#0082F0"}
    np1, np2 = st.columns(2)
    with np1:
        fignr = px.bar(net_full, x="year", y="revenue_b", color="company",
                       barmode="group", color_discrete_map=npcolors,
                       labels={"year": "Year", "revenue_b": "Revenue ($B)",
                               "company": ""})
        fignr.update_layout(height=340, hovermode="x unified",
                            legend_title="", title="Revenue")
        st.plotly_chart(fignr, width="stretch")
    with np2:
        fignc = px.bar(net_full, x="year", y="capex_b", color="company",
                       barmode="group", color_discrete_map=npcolors,
                       labels={"year": "Year", "capex_b": "Capex ($B)",
                               "company": ""})
        fignc.update_layout(height=340, hovermode="x unified",
                            legend_title="", title="Capex")
        st.plotly_chart(fignc, width="stretch")
    st.caption(
        "Total company figures. Nokia and Ericsson in USD-converted EUR/SEK "
        "(approximate). Equipment vendors are asset-light: all four run capex "
        "in the low hundreds of millions, about 1 to 3% of revenue (capex "
        "values approximate). The growth divergence is the story: Arista has "
        "roughly quadrupled since 2020 while Nokia and Ericsson have shrunk.")

    st.markdown("#### Network infrastructure and data-center networking (\\$B)")
    fign4 = px.bar(
        networking, x="year", y="revenue_b", color="company", barmode="group",
        color_discrete_map={"Arista": GREEN, "Ciena": BLUE, "Nokia NI": YELLOW},
        labels={"year": "Year", "revenue_b": "Revenue ($B)", "company": ""})
    fign4.update_layout(height=340, hovermode="x unified", legend_title="")
    st.plotly_chart(fign4, width="stretch")
    st.caption(
        "The AI-exposed side. Arista and Ciena are pure-plays (total revenue); "
        "Nokia is the Network Infrastructure segment only (fixed, IP and "
        "optical networks, excludes mobile; grew 9% in 2025 and now includes "
        "Infinera). Cisco's Networking segment (about \\$28-30B) sits inside a "
        "diversified firm and is left out to keep the comparison clean. "
        "Sources: company filings.")

    st.markdown("#### Mobile networks (\\$B)")
    figmn = px.bar(
        mobile_net, x="year", y="revenue_b", color="vendor", barmode="group",
        color_discrete_map={"Ericsson Networks": "#0082F0",
                            "Nokia Mobile Networks": YELLOW,
                            "Huawei ICT infrastructure": RED},
        labels={"year": "Year", "revenue_b": "Revenue ($B)", "vendor": ""})
    figmn.update_layout(height=340, hovermode="x unified", legend_title="")
    st.plotly_chart(figmn, width="stretch")
    st.caption(
        "The mobile side, for contrast: flat to declining since the 5G "
        "buildout peaked. Ericsson Networks and Nokia Mobile Networks are "
        "segment figures (currency-converted, approximate); Nokia Mobile "
        "Networks fell sharply after losing the AT&T contract in 2024. Huawei "
        "is the ICT infrastructure division (carrier-led; segment definitions "
        "changed over time, approximate). Samsung Networks and ZTE are the "
        f"other notable vendors, not charted. Data as of {DATA_UPDATED}.")

# --------------------------------------------------------------------------- #
# 4 · Power & Data Centers
# --------------------------------------------------------------------------- #
with tab_dc:
    st.markdown("### 5 · Data Centers")
    st.markdown(
        "- **US data center construction is overtaking office construction**, "
        "crossing on a monthly run-rate basis in late 2025 and on track to "
        "pass it for the full year in 2026, the clearest physical-economy "
        "signal of the AI buildout.\n"
        "- **Capacity comes from hyperscaler self-build, colocation providers "
        "(Equinix, Digital Realty) and dedicated AI campuses:** the named "
        "gigawatt-scale pipeline (Stargate, Hyperion, Colossus and others) "
        "totals about 17 GW of announced capacity.\n"
        "- **The binding constraint is shifting from buildings to "
        "electricity:** high-voltage substations take 3 to 5 years, 7 of 13 US "
        "grid regions are projected below safety margins by 2030, and Goldman "
        "estimates about \\$720B of grid investment is needed this decade.\n"
        "- **Power availability increasingly decides where and when capacity "
        "gets built**, making behind-the-meter generation and nuclear deals a "
        "competitive differentiator.")

    st.markdown("---")
    st.markdown("#### Data center vs office construction (US, \\$B/year)")
    st.caption("Annual spend; the two are converging as offices fall and data "
               "centers climb.")
    figdc = go.Figure()
    figdc.add_trace(go.Scatter(
        x=dc_con["year"], y=dc_con["datacenter_b"], name="Data centers",
        mode="lines+markers", line=dict(color=BLUE, width=3)))
    figdc.add_trace(go.Scatter(
        x=dc_con["year"], y=dc_con["office_b"], name="Offices",
        mode="lines+markers", line=dict(color=GREY, width=3, dash="dot")))
    figdc.update_layout(height=320, legend_title="", yaxis_title="$B / year",
                        xaxis_title="Year", hovermode="x unified")
    figdc.update_xaxes(dtick=1, tickangle=-45)
    st.plotly_chart(figdc, width="stretch")
    st.caption(
        "US Census construction spending. Data center construction was about "
        "\\$3B a year in 2015 and roughly \\$9-10B through 2020-2022, then "
        "tripled in three years to about \\$41B (2025). Office construction "
        "peaked near \\$72B in 2020 and fell to \\$49B, its lowest since 2015. "
        "On a monthly run-rate the two crossed in Dec 2025. Data center values "
        "for 2015-2022 are from the Census monthly series (via Our World in "
        "Data) and 2023-25 from benchmark-revised Census annuals; office "
        "mid-years are approximate, flagged in the data file. Data as of "
        f"{DATA_UPDATED}.")

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
        "horizons (for example, Hyperion's 5 GW scales out to 2030); most of "
        "this capacity is still under construction. Read it as the build "
        "pipeline.")

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
    st.markdown(
        "- **Five companies are spending at a scale with few precedents:** "
        "about \\$379B of capex in FY2025 and roughly \\$760B guided for 2026, "
        "more than global upstream oil and gas investment.\n"
        "- **Microsoft, Alphabet, Amazon, Meta and Oracle are the demand pull "
        "behind every upstream layer:** their orders set accelerator volumes, "
        "packaging allocation and the gigawatt pipeline.\n"
        "- **The funding mix is the new story:** capex has outgrown operating "
        "cash flow at Oracle (102% in FY2025) and nearly so at Amazon (94%), "
        "and the group issued \\$121B of bonds in 2025, four times the "
        "five-year average.\n"
        "- **Capex intensity has reached 30 to 75% of revenue** for businesses "
        "that were asset-light a decade ago, and returns are starting to feel "
        "it: hyperscaler ROCE is still 3 to 4 times the telecom level but "
        "ticked down in 2025 as capital employed surged. How far it compresses "
        "as the 2025-26 capex depreciates is the central question for the "
        "whole chain.")
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

    st.caption(
        "Microsoft's fiscal year ends June 30 and Oracle's May 31 (not "
        "calendar-aligned). Amazon capex includes fulfilment and logistics, "
        "not only AWS, which matters when comparing totals across companies.")

    st.markdown("---")
    st.markdown("#### Does the capex still earn its keep? ROCE over time")
    st.caption(
        "Return on capital employed (operating income over total assets minus "
        "current liabilities). The shaded band is an estimated 8-10% cost of "
        "capital for these companies (Damodaran, software and internet "
        "sectors).")
    fighr = px.line(
        hyp_returns, x="year", y="roce_pct", color="company", markers=True,
        color_discrete_map=COMPANY_COLORS,
        labels={"year": "Year", "roce_pct": "ROCE (%)", "company": ""})
    fighr.add_hrect(y0=8, y1=10, fillcolor="rgba(154,160,166,0.20)",
                    line_width=0, annotation_text="hyperscaler WACC ~8-10%",
                    annotation_position="bottom right")
    fighr.update_layout(height=380, hovermode="x unified", legend_title="",
                        yaxis_range=[0, 35])
    st.plotly_chart(fighr, width="stretch")
    st.caption(
        "Returns are still comfortably above their own roughly 8-10% cost of "
        "capital, and 3 to 4 times the level telecoms earn, which is what "
        "justifies the spending. The 2025 dip is the signal to watch: Alphabet "
        "fell from 31% to 26%, with Microsoft and Meta also easing, as capital "
        "employed jumped (Alphabet from \\$361B to \\$493B in one year) faster "
        "than operating income. Most of the 2025-26 capex has not yet started "
        "depreciating, so the drag builds from here; the open question is how "
        "far the spread over cost of capital narrows. Amazon and Oracle sit "
        "lower because their figures include retail and a broader software "
        "base. Sources: 10-K filings (EDGAR XBRL). Data as of "
        f"{DATA_UPDATED}.")

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
        "component cost inflation, so higher capex "
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
    st.markdown(
        "- **GPU rental specialists went from niche to roughly \\$100B of "
        "contracted backlog in about two years**, financed largely with "
        "GPU-backed debt; CoreWeave and Nebius are listed, Crusoe and Lambda "
        "private.\n"
        "- **Backlogs are concentrated on a few anchor tenants** (the OpenAI "
        "deal added \\$11.2B to CoreWeave's backlog, Meta committed \\$27B to "
        "Nebius). The strength is that a multi-year contract with a "
        "creditworthy counterparty is what lets a NeoCloud raise GPU-backed "
        "debt cheaply and pre-fund its buildout. The risk is the mirror image: "
        "if that one tenant slows, renegotiates or fails, a large share of the "
        "backlog and the debt secured against it is exposed at once.\n"
        "- **The sector carries over \\$20B of debt secured against GPUs that "
        "depreciate over 4 to 6 years**, so durability depends on rental "
        "pricing holding up through successive accelerator generations.\n"
        "- **NeoClouds are effectively a leveraged bet on sustained AI compute "
        "scarcity.**")
    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    c1.metric("CoreWeave backlog (Q1 2026)", "~$100B", "$66.8B end-2025")
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
        "CoreWeave's backlog (about \\$100B as of Q1 2026, up from \\$66.8B "
        "at end-2025) dwarfs its current revenue and is concentrated (the "
        "OpenAI deal added \\$11.2B). The Nebius bar is an estimate built "
        "from its disclosed Microsoft (\\$17-19B) and Meta (\\$27B) "
        "contracts. Crusoe and Lambda are private and disclose no backlog, "
        "so they show revenue only. GPUs depreciate on a 4 to 6 year "
        "schedule while rental pricing can move faster, and over \\$20B of "
        "sector debt is secured against them. Sources: company filings and "
        f"press. Data as of {DATA_UPDATED}.")

# --------------------------------------------------------------------------- #
# 8 · AI Labs (demand)
# --------------------------------------------------------------------------- #
with tab_labs:
    st.markdown("### 8 · AI Labs")
    st.markdown(
        "- **Lab revenue is large and concentrating:** Anthropic and OpenAI "
        "run-rates total above \\$70B, and their multi-year compute "
        "commitments underwrite NeoCloud backlogs and hyperscaler buildouts.\n"
        "- **Usage is broad but shallow:** 900M people use ChatGPT weekly, yet "
        "only about 5 to 6% pay and under 10% of US adults use generative AI "
        "daily.\n"
        "- **Frontier capability has converged**, with benchmark leaders "
        "clustered in the low 90s on GPQA-Diamond, Chinese models close "
        "behind, and no clear network effects at the model layer.\n"
        "- **Where the value settles is the open question:** enterprise spend "
        "patterns and startup formation (both charted below) suggest the bet "
        "is being placed on the application layer.")

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

    st.markdown("#### Inference price collapse ($ per million tokens, log scale)")
    ip = inference_prices.copy()
    ip["date"] = pd.to_datetime(ip["date"])
    figip = px.line(
        ip.sort_values("date"), x="date", y="price_per_m",
        color="capability_class", markers=True, log_y=True,
        color_discrete_map={"GPT-3 class": GREY, "GPT-4 class": BLUE},
        hover_data=["model"],
        labels={"date": "", "price_per_m": "$ / million tokens (log)",
                "capability_class": ""})
    figip.update_layout(height=320, hovermode="x unified", legend_title="")
    st.plotly_chart(figip, width="stretch")
    st.caption(
        "Blended list price (3:1 input:output) for a fixed capability level "
        "over time. The price of GPT-3-class capability fell from \\$60 to "
        "about \\$0.06 per million tokens in three years, roughly 1000x, and "
        "GPT-4-class capability has fallen about 100x since 2023. As capability "
        "converges across labs and price falls about 10x a year, the model "
        "layer struggles to hold value, which pushes it toward the "
        "infrastructure below and the applications above. Sources: a16z "
        "(\"LLMflation\"), company price lists. Data as of "
        f"{DATA_UPDATED}.")

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

    ud1, ud2 = st.columns(2)
    with ud1:
        st.markdown("#### Depth of use: broad but shallow (% of US adults)")
        figud = px.bar(usage_depth, x="share_pct", y="measure",
                       orientation="h", text="share_pct",
                       labels={"share_pct": "% of US adults (18-64)",
                               "measure": ""})
        figud.update_traces(marker_color=BLUE,
                            texttemplate="%{text:.0f}%",
                            textposition="outside")
        figud.update_layout(height=300,
                            xaxis_range=[0, 50],
                            yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(figud, width="stretch")
        st.caption(
            "About 40% of US working-age adults have used generative AI, but "
            "under 10% use it daily. Adoption is broad and shallow. Source: "
            "Bick, Blandin and Deming, Real-Time Population Survey (NBER), "
            "late 2024.")
    with ud2:
        st.markdown("#### Enterprise AI application spend, 2025 (\\$B)")
        figes = px.bar(ent_spend.sort_values("spend_b"), x="spend_b",
                       y="category", orientation="h", text="spend_b",
                       labels={"spend_b": "Annual spend ($B)", "category": ""})
        figes.update_traces(marker_color=GREEN,
                            texttemplate="$%{text:.1f}B",
                            textposition="outside")
        figes.update_layout(height=300,
                            xaxis_range=[0, ent_spend["spend_b"].max() * 1.25])
        st.plotly_chart(figes, width="stretch")
        st.caption(
            "Enterprise generative AI application spend reached \\$19B in 2025 "
            "(of \\$37B total enterprise genAI spend, up from \\$11.5B in "
            "2024). Coding tools are the largest single use case at \\$4.2B. "
            "Source: Menlo Ventures, State of Generative AI in the Enterprise "
            "2025.")

    st.markdown("#### Y Combinator: AI share of startup batches (%)")
    figyc = go.Figure()
    figyc.add_trace(go.Bar(x=yc_share["year"], y=yc_share["ai_share_pct"],
                           name="AI startups", marker_color=RED))
    figyc.add_trace(go.Bar(x=yc_share["year"],
                           y=100 - yc_share["ai_share_pct"],
                           name="Other startups", marker_color="#dadce0"))
    figyc.update_layout(barmode="stack", height=320, legend_title="",
                        yaxis_title="% of batch",
                        yaxis_range=[0, 100])
    st.plotly_chart(figyc, width="stretch")
    st.caption(
        "Share of Y Combinator batch companies tagged as AI. Roughly 5 to 15% "
        "of batches from 2015 to 2022, then 44% (2023), about 70% (2024) and "
        "about 80% (2025). Startup formation has concentrated almost entirely "
        "on AI. Compiled from YC directory analyses and press reports; "
        f"2015-2022 values are approximate. Data as of {DATA_UPDATED}.")

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

# --------------------------------------------------------------------------- #
# 9 · System Integrators
# --------------------------------------------------------------------------- #
with tab_si:
    st.markdown("### 9 · System Integrators")
    st.markdown(
        "- **Deploying AI into enterprises is services-heavy work**, which "
        "makes integrators one of the most measurable reads on real "
        "adoption.\n"
        "- **Accenture, TCS, Infosys and Capgemini sell the integration work "
        "that turns models into production systems**, and enterprises often "
        "pay them before they pay model vendors at scale.\n"
        "- **Accenture's GenAI bookings compounded from \\$0.3B (FY2023) to "
        "\\$5.9B (FY2025)**, with cumulative bookings past \\$9B, the steepest "
        "new-offering ramp in the firm's disclosures.\n"
        "- **The integrators are also a check on the hype:** overall revenue "
        "grows single digits, so GenAI work has so far been additive for the "
        "services industry itself.")

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

    st.markdown("#### Accenture GenAI new bookings since 2023 (\\$B)")
    gb = genai_bookings.copy()
    gb["cumulative_b"] = gb["bookings_b"].cumsum()
    figgb = go.Figure()
    figgb.add_trace(go.Bar(x=gb["period"], y=gb["bookings_b"],
                           name="New bookings per period",
                           marker_color="#A100FF"))
    figgb.add_trace(go.Scatter(x=gb["period"], y=gb["cumulative_b"],
                               name="Cumulative since 2023",
                               mode="lines+markers",
                               line=dict(color="#202124", width=3)))
    figgb.update_layout(height=340, legend_title="",
                        yaxis_title="$B", hovermode="x unified")
    st.plotly_chart(figgb, width="stretch")
    st.caption(
        "GenAI new bookings as disclosed in Accenture's quarterly results: "
        "\\$0.3B in the first two quarters of disclosure (FY2023), \\$3.0B in "
        "FY2024, \\$5.9B in FY2025. Cumulative bookings since 2023 passed "
        f"\\$9B. Source: Accenture 8-K filings. Data as of {DATA_UPDATED}.")

# --------------------------------------------------------------------------- #
# 10 · Telecoms (context)
# --------------------------------------------------------------------------- #
with tab_telco:
    st.markdown("### 10 · Telecoms")
    st.markdown(
        "- **Telecoms are the distribution layer of the value chain:** every "
        "model reaches its user over a fixed or mobile network. They are also "
        "its sharpest precedent, because a decade of carrying exponential "
        "traffic has shown that being essential to distribution does not "
        "translate into capturing value. The network is horizontal "
        "infrastructure that carries AI the way it carries video, so it cannot "
        "price the AI load specifically.\n"
        "- **They built the last infrastructure wave on the same pattern:** "
        "mobile traffic grew roughly 30x since 2015 while sector capex stayed "
        "flat near \\$300B.\n"
        "- **Even with dividends reinvested, shareholders earned bond-like "
        "returns on an equity-risk buildout:** total shareholder return since "
        "2015 ran about 5% a year for Verizon and 7% for AT&T against about "
        "12% for the MSCI World; BT shareholders lost roughly half their "
        "money, and only Deutsche Telekom came close to market returns.\n"
        "- **Returns on capital tell the same story:** ROCE for the major "
        "developed-market telcos averaged roughly 4 to 9% over 2020-25, at or "
        "below the 6 to 8% cost-of-capital band, so a decade of network capex "
        "earned about its cost of capital at best.\n"
        "- **Carrier capex has settled into a steady state with no 6G "
        "spike ahead:** global telecom capex in 2024 was the lowest since "
        "2011, and US carrier guidance for 2026 (AT&T \\$23-24B, Verizon "
        "\\$16-16.5B, T-Mobile \\$10B) points to a flat \\$50B run-rate. "
        "Lower capex lifts carrier free cash flow and dividends, and it caps "
        "growth for the equipment vendors that sell to them.\n"
        "- **Carriers never converted traffic growth into value, and AI is "
        "the next wave that confirms the pattern rather than breaking it:** "
        "traffic rose roughly 30x since 2015 while shareholder returns went "
        "sideways (the two charts below), because connectivity is sold in "
        "flat-rate plans that do not scale with bytes carried. AI changes the "
        "destination of the load, not the economics: the heavy flows run "
        "inside and between data centers on fiber backbones, so the optical "
        "and data-center interconnect layer absorbs the growth while the "
        "carrier access network sees little of it.\n"
        "- **The telecom era is the cautionary precedent for AI "
        "infrastructure:** enormous capex and real usage growth did not "
        "translate into returns once the layer above commoditized the "
        "network.")

    st.markdown("---")
    tt1, tt2 = st.columns(2)
    with tt1:
        st.markdown("#### Global data traffic: mobile vs fixed (EB per month)")
        figmt = go.Figure()
        mt = mobile_traffic.copy()
        ft = fixed_traffic.copy()
        figmt.add_trace(go.Bar(
            x=ft["year"], y=ft["traffic_eb_month"], name="Fixed",
            marker_color=GREEN,
            marker_pattern_shape=["/" if s == "forecast" else ""
                                  for s in ft["source_type"]]))
        figmt.add_trace(go.Bar(
            x=mt["year"], y=mt["traffic_eb_month"], name="Mobile",
            marker_color=BLUE,
            marker_pattern_shape=["/" if s == "forecast" else ""
                                  for s in mt["source_type"]]))
        figmt.update_layout(height=340, barmode="group", legend_title="",
                            yaxis_title="EB per month",
                            hovermode="x unified")
        st.plotly_chart(figmt, width="stretch")
        st.caption(
            "Mobile traffic (excluding fixed wireless access) is from "
            "successive Ericsson Mobility Reports; about 4.4 EB per month in "
            "2015 to about 126 EB in 2024, with roughly 145 (2025) and 162 "
            "(2026) on Ericsson's trajectory. Fixed/wireline traffic is an "
            "estimate compiled from Cisco VNI history and ITU/TeleGeography "
            "data and carries most of the world's data, roughly 3x mobile. "
            "Hatched bars are forecasts. AI workloads land mainly on the "
            "fixed and data-center side; mobile growth is decelerating.")
    with tt2:
        st.markdown("#### Total shareholder return, indexed (2015 = 100)")
        ts = telco_tsr.copy()
        base = ts[ts["year"] == 2015].set_index("company")["adj"]
        ts["indexed"] = ts.apply(
            lambda r: r["adj"] / base[r["company"]] * 100, axis=1)
        figts2 = px.line(ts, x="year", y="indexed", color="company",
                         markers=True,
                         color_discrete_map={"AT&T": BLUE, "Verizon": RED,
                                             "Deutsche Telekom": "#E20074",
                                             "BT Group": "#5514B4",
                                             "MSCI World (URTH)": GREY},
                         labels={"year": "Year", "indexed": "Index (2015 = 100)",
                                 "company": ""})
        figts2.add_hline(y=100, line_dash="dash", line_color=GREY)
        figts2.update_layout(height=340, hovermode="x unified",
                             legend_title="")
        st.plotly_chart(figts2, width="stretch")
        st.caption(
            "Total shareholder return: dividend- and split-adjusted prices "
            "(dividends reinvested), indexed to 100 at the start of 2015 "
            "(Yahoo Finance adjusted closes). Through early 2026 that is "
            "roughly +72% for Verizon (about 5% a year), +107% for AT&T "
            "(about 7%), +175% for Deutsche Telekom (about 10%) and -53% for "
            "BT Group, versus +235% (about 12% a year) for the MSCI World "
            "ETF. Price-only comparisons understate telco returns because "
            "the sector pays out 4 to 7% dividend yields.")

    st.markdown("#### Return on capital employed vs cost of capital")
    figroce = go.Figure()
    figroce.add_hrect(y0=6, y1=8, fillcolor="rgba(154,160,166,0.25)",
                      line_width=0,
                      annotation_text="WACC band 6-8% (Damodaran, "
                                      "developed-market telecom)",
                      annotation_position="top right")
    figroce.add_trace(go.Bar(
        x=telco_roce["company"], y=telco_roce["roce_pct"],
        marker_color=[BLUE, RED, "#E20074", "#E60000", "#0066FF", "#5514B4"],
        text=telco_roce["roce_pct"],
        customdata=telco_roce["years"],
        hovertemplate="%{x}: %{y:.1f}% (avg %{customdata})<extra></extra>"))
    figroce.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    figroce.update_layout(height=360, yaxis_title="Average ROCE (%)",
                          showlegend=False,
                          yaxis_range=[0, 11])
    st.plotly_chart(figroce, width="stretch")
    st.caption(
        "ROCE is computed as operating income divided by capital employed "
        "(total assets minus current liabilities), averaged over the years "
        "shown per company, from 10-K and 20-F filings (SEC EDGAR XBRL); "
        "Deutsche Telekom and BT are approximated from annual reports as "
        "neither files with the SEC today. One-offs distort single years "
        "(AT&T's 2022 impairments, tower-sale gains at Telefonica 2021 and "
        "Vodafone FY2023) but averages wash most of this out. Only Verizon "
        "and BT reach the top of the 6 to 8% band; the sector as a whole "
        "earned roughly its cost of capital across the 5G buildout.")
    st.caption(
        "**BT note:** ROCE "
        "measures the return on the whole operating asset base, while TSR is "
        "the return to the thin slice of equity that sits behind everything "
        "else. BT carries roughly £15-20B of net debt and a very large pension "
        "scheme that has absorbed billions in deficit-repair cash, so an "
        "8% asset return, after interest and pension top-ups, leaves little "
        "for equity holders. On top of that the market steadily de-rated the "
        "shares as revenue stalled and Openreach fibre capex ramped. Decent "
        "asset returns and a destroyed equity coexist because of leverage, "
        "pension drag and a falling multiple. The gap is the whole point: "
        "being a sound operating business does not guarantee value for "
        f"shareholders. Data as of {DATA_UPDATED}.")

    hyp_year = capex.groupby("fiscal_year")["capex_usd_b"].sum()
    guide_total = float(guidance["capex_mid_b"].sum())

    k1, k2, k3 = st.columns(3)
    k1.metric("Global telecom capex 2024", "~$295B", "lowest since 2011")
    k2.metric("Big-5 hyperscaler capex 2025", f"${hyp_year.loc[2025]:.0f}B",
              "overtook telecom")
    k3.metric("Big-5 2026E", f"${guide_total:.0f}B",
              f"~{guide_total/295:.1f}x global telecom")

    st.markdown("#### Capex: hyperscalers vs telecoms (\\$B)")
    tc = telco_capex.copy()
    tc_hist = tc[tc["source_type"] != "forecast"]
    tc_fc = tc[tc["year"] >= int(tc_hist["year"].max())]
    hyp_hist_y = [y for y in range(2020, 2026) if y in hyp_year.index]
    figt = go.Figure()
    figt.add_trace(go.Scatter(
        x=tc_hist["year"], y=tc_hist["telecom_capex_b"],
        name="Global telecom capex", mode="lines+markers",
        line=dict(color=GREY, width=3)))
    figt.add_trace(go.Scatter(
        x=tc_fc["year"], y=tc_fc["telecom_capex_b"],
        name="Global telecom capex (forecast)", mode="lines+markers",
        line=dict(color=GREY, width=3, dash="dot")))
    figt.add_trace(go.Scatter(
        x=hyp_hist_y, y=[float(hyp_year.loc[y]) for y in hyp_hist_y],
        name="Big-5 hyperscaler capex", mode="lines+markers",
        line=dict(color=BLUE, width=3)))
    figt.add_trace(go.Scatter(
        x=[2025, 2026], y=[float(hyp_year.loc[2025]), guide_total],
        name="Big-5 hyperscaler capex (guidance)", mode="lines+markers",
        line=dict(color=BLUE, width=3, dash="dot")))
    figt.update_layout(height=380, hovermode="x unified", legend_title="",
                       yaxis_title="Capex ($B)", xaxis_title="Year")
    st.plotly_chart(figt, width="stretch")
    st.caption(
        "Telecom is global industry capex (MTN Consulting); 2025-26 assumes "
        "the flat-to-declining trajectory continues, consistent with carrier "
        "guidance and the absence of a 6G investment cycle. Hyperscaler is "
        "the Big-5 (Alphabet, Amazon, Meta, Microsoft, Oracle); 2026 is the "
        "guidance midpoint. Dotted segments are forecasts. The two lines "
        "crossed in 2025 and the gap roughly doubles in 2026: the world's "
        "infrastructure capex engine has changed hands.")

    st.markdown("#### US carriers: capex and revenue, with 2026 guidance (\\$B)")
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
        "2020-2024 are reported figures; 2025 is an approximate full year and "
        "2026 is company guidance (AT&T \\$23-24B on fiber, Verizon "
        "\\$16-16.5B cut, T-Mobile about \\$10B; revenue per low-single-digit "
        "service growth guidance). AT&T revenue includes WarnerMedia until "
        "its spin-off in April 2022. Verizon's 2022 capex peak reflects the "
        "C-Band buildout; T-Mobile's 2021-22 peak reflects Sprint "
        "integration. The shape that emerges is steady-state capex near "
        "\\$50B combined with no 6G spike: better for carrier free cash flow "
        "and dividends, flat for the vendors selling into it. Data as of "
        f"{DATA_UPDATED}.")
