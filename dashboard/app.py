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
fcf_transfer = load_csv("fcf_transfer.csv")
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
roce_layer = load_csv("roce_by_layer.csv")
semis_segments = load_csv("semis_segments.csv")
telco_tsr = load_csv("telco_tsr.csv")
telco_roce = load_csv("telco_roce.csv")
usage_depth = load_csv("ai_usage_depth.csv")
ent_spend = load_csv("enterprise_ai_spend.csv")
yc_share = load_csv("yc_ai_share.csv")

DATA_UPDATED = "October 2026"

YEARS = sorted(capex["fiscal_year"].unique())
# Latest fiscal year in which every company has reported. Microsoft (Jun)
# and Oracle (May) close their years earlier, so the newest year in the
# file can cover only part of the group; totals must not mix the two.
_per_year = capex.groupby("fiscal_year")["company"].nunique()
YR = int(_per_year[_per_year == capex["company"].nunique()].index.max())

# Capex outlook, single source for every chart and sentence that describes the
# trajectory. Same fiscal-year basis as the reported history: a company whose
# fiscal 2026 has closed (Microsoft Jun, Oracle May) uses its actual, the rest
# their guidance midpoint.
FC_YEAR = int(guidance["year"].iloc[0])
_closed = capex[capex["fiscal_year"] == FC_YEAR].set_index("company")["capex_usd_b"]
CAPEX_FC = float(sum(_closed.get(co, mid) for co, mid
                     in zip(guidance["company"], guidance["capex_mid_b"])))
# 2027 aggregate consensus (Moody's, Goldman, BofA all near $1T); no company split
CAPEX_CONSENSUS_B = 1000.0
# Free cash flow by basket and year (built by model/build_fcf_transfer.py)
_fcf = fcf_transfer.pivot(index="year", columns="group", values="fcf_b")
HYP_FCF, SEMI_FCF = _fcf["Hyperscalers"], _fcf["Semiconductors"]

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
view = capex[capex["fiscal_year"] <= YR].copy()
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
    cowos25 = float(cowos.loc[cowos.year == 2025, "cowos_kwpm"].iloc[0])
    cowos26_lo = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_low"].iloc[0])
    cowos26_hi = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_high"].iloc[0])
    tsmc25 = float(foundry.loc[(foundry.company == "TSMC") &
                               (foundry.year == 2025), "revenue_b"].iloc[0])

    st.markdown("#### Executive summary")
    st.markdown(
        f"- **AI is moving value to what it cannot make cheap.** Compute, "
        f"frontier models and software development are all becoming abundant, "
        f"eroding the pricing power each gave its layer. Value accrues to what "
        f"stays scarce: 1/ distribution, 2/ proprietary data, 3/ regulatory "
        f"position and 4/ customer switching costs.\n"
        f"- **Hyperscalers increasingly fund capex with debt and equity.** Big-5 "
        f"capex (Microsoft, Alphabet, Amazon, Meta, Oracle) rises from "
        f"**\\${total_now:,.0f}B** in FY2025 to **\\${CAPEX_FC:,.0f}B** in "
        f"fiscal 2026 and around **\\${CAPEX_CONSENSUS_B/1000:.0f}T** in 2027, "
        f"above global upstream oil and gas investment (about \\$570B). Free "
        f"cash flow falls from \\${HYP_FCF[2024]:.0f}B in 2024 to about "
        f"\\${HYP_FCF[2026]:.0f}B in fiscal 2026 and turns negative in 2027; "
        f"Oracle's capex already reached 174% of its operating cash flow. The "
        f"group issued \\$121B of bonds in 2025, "
        f"four times its five-year average, and Alphabet raised about \\$85B of "
        f"equity after its first negative free-cash-flow quarter since listing.\n"
        f"- **Each shortage becomes the next layer's cost and its supplier's "
        f"windfall.** Packaging and memory are sold out through 2026: Microsoft "
        f"attributes about \\$25B of its 2026 capex to memory and component "
        f"inflation, and Amazon added \\$20B on memory alone. Micron's revenue "
        f"more than tripled to \\$133B in its year to September 2026 at an 81% "
        f"gross margin. Power is next: about {gw['capacity_gw'].sum():.0f} GW "
        f"of named projects wait on grid connections that take 3 to 5 years.\n"
        f"- **Hyperscalers have replaced telecoms as the largest infrastructure "
        f"spenders.** Global telecom capex (about \\$295B, the lowest since "
        f"2011) equals about nine months of Big-5 spending. Equipment vendors "
        f"follow the money: Nokia bought Infinera for data-center optics, "
        f"Arista's revenue quadrupled and Ericsson's shrank.\n"
        f"- **Infrastructure margins compress as inference becomes the main "
        f"workload.** Demand is moving from training (building a model) to "
        f"inference (serving it every day), where AMD, hyperscaler custom chips "
        f"and startups compete with NVIDIA. Capacity also grows with usage, "
        f"since more tokens need more GPUs, so AI infrastructure lacks the "
        f"operating leverage of fixed-cost networks like fiber.\n"
        f"- **The infrastructure debt rests on lab revenue.** Lab compute "
        f"contracts back NeoCloud backlogs, which secure over \\$20B of "
        f"GPU-backed debt tied to one chip vendor, so trouble at the labs would "
        f"travel back through credit.\n"
        f"- **Model makers face fast commoditization.** 900M to 1B people use "
        f"ChatGPT weekly but only 5 to 6% pay, leading labs score within a few "
        f"points of each other, Chinese open-weight models (DeepSeek, Qwen, "
        f"Kimi) trail by single digits at a fraction of the price, and API "
        f"switching costs are near zero. Labs that escape utility margins will "
        f"1/ own distribution, 2/ compound proprietary data or 3/ move into "
        f"applications first.\n"
        f"- **Cheap code erodes software moats built on engineering effort.** "
        f"Workflow embedding, switching costs, proprietary data and regulatory "
        f"position hold up. Mid-market horizontal SaaS is most exposed; vertical "
        f"software with data flywheels is best placed.\n"
        f"- **Integrators win deployment work while AI shrinks their "
        f"labor-based model.** The market began pricing this in mid-2026, when "
        f"Accenture, IBM and the Indian IT majors fell on AI-related guidance, "
        f"and TCS revenue declined in its latest fiscal year.\n"
        f"- **Integrated incumbents will be harder to displace than carriers "
        f"were.** Every layer is racing to own distribution, data and customer "
        f"lock-in, and today's leaders produce the intelligence itself and "
        f"already span the stack."
    )
    st.caption(f"Data last updated {DATA_UPDATED}.")
    st.markdown("---")

    st.markdown("##### Spend & demand (downstream)")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric(f"Big-5 total capex FY{YR}", f"${total_now:,.0f}B", f"{yoy:+.0f}% YoY")
    d2.metric("Big-5 capex FY2026E", f"${CAPEX_FC:,.0f}B",
              f"+{(CAPEX_FC/total_now-1)*100:.0f}% vs FY25")
    d3.metric(f"Capex CAGR FY{first_yr}-{YR}", f"{cagr*100:.0f}%/yr",
              "AI-era acceleration")
    d4.metric("NeoCloud backlog (CoreWeave)", "~$104B", "Q2 2026")

    st.markdown("##### Supply & constraint (upstream)")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("CoWoS capacity 2025", f"{cowos25:.0f}k wpm", "~2× vs 2024")
    s2.metric("CoWoS 2026E", f"{cowos26_lo:.0f}-{cowos26_hi:.0f}k wpm",
              f"~{cowos26_lo/cowos25:.1f} to {cowos26_hi/cowos25:.1f}× vs 2025")
    s3.metric("TSMC revenue 2025", f"${tsmc25:.0f}B", "~70% foundry share")
    s4.metric("Named GW-scale pipeline", f"{gw['capacity_gw'].sum():.0f} GW",
              f"{len(gw)} flagship projects")

    st.markdown("#### Where value is captured: return on capital by layer")
    st.caption(
        "Aggregate ROCE of the representative players in each layer against a "
        "typical cost-of-capital band, with annual revenue growth for the same "
        "baskets shown above each bar. Returns show who captures value today "
        "and growth shows which layers are still early.")
    rl = roce_layer.sort_values("order")

    def _band(v):
        if v < 0:
            return "Below zero"
        return "Above cost of capital" if v >= 12 else "At or below cost of capital"
    rl = rl.assign(band=rl["roce_pct"].apply(_band))
    figrl = px.bar(
        rl, x="layer", y="roce_pct", color="band", text="roce_pct",
        color_discrete_map={"Above cost of capital": GREEN,
                            "At or below cost of capital": GREY,
                            "Below zero": RED},
        labels={"layer": "", "roce_pct": "Average ROCE (%)", "band": ""})
    figrl.update_traces(texttemplate="%{text:.0f}%", textposition="outside",
                        cliponaxis=False)
    figrl.add_hrect(y0=8, y1=11, fillcolor="rgba(154,160,166,0.20)",
                    line_width=0, annotation_text="typical cost of capital "
                    "(8 to 11%)", annotation_position="top right")
    figrl.add_annotation(xref="paper", x=0, y=1.13, yref="paper",
                         text="<b>Revenue growth p.a.</b>", showarrow=False,
                         xanchor="left", font=dict(size=11, color="#5f6368"))
    for _, gr in rl.iterrows():
        figrl.add_annotation(x=gr["layer"], y=1.04, yref="paper",
                             text=f"+{gr['growth_pct']:.0f}%", showarrow=False,
                             font=dict(size=11, color=BLUE))
    figrl.update_layout(height=460, legend_title="", yaxis_range=[-40, 80],
                        xaxis_tickangle=-30, margin=dict(t=80))
    st.plotly_chart(figrl, width="stretch")
    st.caption(
        "**Sources:** company filings (EDGAR XBRL); lab run-rates via Bloomberg "
        "and Epoch AI.  \n**Notes:** aggregate ROCE for the latest fiscal year "
        "(combined operating income over combined capital employed), so larger "
        "players carry more weight; the Telecoms and Hyperscalers tabs show the "
        "same measure over time. The 8-11% band "
        "is a common cost-of-capital reference. Returns concentrate in the "
        "asset-light layers and thin where capital sits without pricing power; "
        "foundry is the exception, carried by TSMC's scarcity pricing. The "
        "growth row (revenue growth, above each bar) separates young sub-band "
        "layers (NeoClouds, labs, compounding in triple digits) from mature "
        "ones (telecoms +1%, integrators +5%); growth only builds value where "
        "the return clears the band. Growth basis: 3-yr revenue CAGR 2022-2025, "
        "except NeoClouds (2-yr, CoreWeave) and the labs (Anthropic and OpenAI "
        "combined run-rate \\$29B in Dec-25 to \\$105B in Jul-26, annualized), "
        "both off a small base. Labs estimated; Digital Realty, TCS, Deutsche Telekom and "
        f"Nebius excluded for lack of comparable filings. Data as of {DATA_UPDATED}.")

    st.markdown("#### Value-chain map")
    st.caption("The ten steps, upstream to downstream, and what each one does.")
    vc_rows = [
        ("1 · Silicon & IP",
         "Designs the accelerators (the specialized chips, mostly NVIDIA GPUs,"
         "that train and run AI models) and the high-bandwidth memory (HBM) "
         "stacked beside them to feed data in fast enough. NVIDIA dominates "
         "the chip design; HBM supply is the first hard limit on how many "
         "chips can ship."),
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
    cell = {"core": "background:#0d3b8c;",
            "scaled": "background:#4a7fd4;",
            "emerging": "background:#bcd6f7;",
            "": "background:#f4f6f9;"}
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
                       "border-bottom:1px solid #fff;font-weight:600;'>"
                       f"{r['player']}</td>")
        for col, _ in layer_cols:
            val = r[col] if isinstance(r[col], str) else ""
            style = cell.get(val, "background:#f4f6f9;")
            vi_html.append("<td style='padding:6px 4px;border:2px solid #fff;"
                           f"{style}'>&nbsp;</td>")
        vi_html.append("</tr>")
    vi_html.append("</tbody></table>")
    st.markdown("".join(vi_html), unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.8rem;color:#5f6368;margin-top:6px;'>"
        "<span style='display:inline-block;width:12px;height:12px;"
        "background:#0d3b8c;vertical-align:middle;margin-right:4px;'></span>"
        "core business "
        "<span style='display:inline-block;width:12px;height:12px;"
        "background:#4a7fd4;vertical-align:middle;margin:0 4px 0 12px;'></span>"
        "at scale "
        "<span style='display:inline-block;width:12px;height:12px;"
        "background:#bcd6f7;vertical-align:middle;margin:0 4px 0 12px;'></span>"
        "emerging</div>", unsafe_allow_html=True)
    st.caption(
        "**Sources:** disclosed products and announced projects.  \n**Notes:** shade shows "
        "depth, darkest for a core business, mid-blue at scale, lightest where "
        "the move is still early. Hyperscalers have pushed into connectivity, "
        "Google (Fiber, Fi, subsea cables) and Meta and Microsoft (subsea "
        "cables) at scale, Amazon (Project Kuiper) still emerging, as "
        "infrastructure owners rather than retail carriers.")

# --------------------------------------------------------------------------- #
# 1 · Silicon & IP  (accelerator design + HBM memory)
# --------------------------------------------------------------------------- #
with tab_silicon:
    st.markdown("### 1 · Silicon & IP")
    st.markdown(
        "- **AI has driven the sharpest chip upswing since the dot-com era.** "
        "Sales reached \\$792B in 2025 (+26%) and are forecast to pass \\$1T in "
        "2026. Past cycles turned every 3 to 4 years.\n"
        "- **The surge sits in compute and memory, the two most cyclical "
        "segments.** Logic (where accelerators sit) and memory (including HBM) "
        "drive the 2025-26 growth; analog, microcontrollers and discrete chips "
        "grow with the wider economy.\n"
        "- **NVIDIA dominates accelerators.** Data-center revenue was \\$194B "
        "in FY2026 and \\$89B in the July 2026 quarter alone, about 92% of "
        "company revenue; AMD is a distant second.\n"
        "- **Hyperscaler custom chips are becoming a real check on NVIDIA.** "
        "Broadcom, which builds Google's TPU and other in-house accelerators, "
        "reported \\$16.7B of AI chip revenue in its July 2026 quarter (+221%), "
        "guides to about \\$58B for FY2026 and sees a path to \\$115B in "
        "FY2027.\n"
        "- **Memory makers earn the most per dollar of revenue.** High-bandwidth "
        "memory (HBM) is sold out through 2026 at SK Hynix (about 57% share), "
        "Micron and Samsung. Micron's revenue went from \\$37B to \\$133B in its "
        "year to September 2026 at an 81% gross margin, with most 2027 HBM "
        "supply contracted at higher prices. Memory is the industry's most "
        "cyclical segment; management expects tight supply through 2028.")

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
        "**Sources:** WSTS, SIA (worldwide semiconductor billings, annual).  \n**Notes:** "
        "the industry cycles (2001 down 32%, 2009, 2019, 2023) but each peak is "
        "higher; the AI leg (+26% in 2025, about \\$1T forecast for 2026) is "
        f"the steepest rise since the dot-com era. Data as of {DATA_UPDATED}.")

    st.markdown("#### Market by segment: compute, memory and the base (\\$B)")
    figseg = px.bar(
        semis_segments, x="year", y="sales_b", color="segment", barmode="stack",
        color_discrete_map={"Logic (compute)": BLUE,
                            "Memory (storage)": GREEN,
                            "Other (analog/micro/discrete)": GREY},
        labels={"year": "Year", "sales_b": "Sales ($B)", "segment": ""})
    figseg.update_layout(height=380, legend_title="", hovermode="x unified")
    st.plotly_chart(figseg, width="stretch")
    st.caption(
        "**Sources:** WSTS (segment splits approximate; 2026 forecast).  \n**Notes:** "
        "logic (compute) is the largest segment and hosts AI accelerators; "
        "memory is the most cyclical, swinging from a \\$92B trough (2023) to a "
        "forecast \\$300B (2026) on HBM. The AI surge concentrates in logic and "
        f"memory, which set the chain's supply constraints. Data as of {DATA_UPDATED}.")

    st.markdown("#### Revenue by key player (\\$B)")
    figsi = px.bar(
        silicon_rev, x="fy", y="revenue_b", color="company", barmode="group",
        labels={"fy": "Fiscal year", "revenue_b": "Revenue ($B)", "company": ""},
        color_discrete_map={"NVIDIA": GREEN, "AMD": RED, "Broadcom": BLUE,
                            "Micron": YELLOW, "SK Hynix": PURPLE})
    figsi.update_layout(height=400, hovermode="x unified", legend_title="")
    st.plotly_chart(figsi, width="stretch")
    st.caption(
        "**Sources:** company filings (SK Hynix and Micron currency-converted, "
        "approximate).  \n**Notes:** total-company revenue. NVIDIA, Broadcom and "
        "Micron fiscal years are offset from calendar and plotted against the "
        "calendar year they mostly cover (NVIDIA FY2026, \\$215.9B, appears as "
        "2025). NVIDIA's data-center segment was about \\$194B; SK Hynix is the "
        "HBM leader (about 57% share).")

# --------------------------------------------------------------------------- #
# 2 · Foundry & Packaging  (TSMC CoWoS + the supply ceiling)
# --------------------------------------------------------------------------- #
with tab_foundry:
    st.markdown("### 2 · Foundry & Packaging")
    st.markdown(
        "- **TSMC is effectively the only leading-edge foundry.** It holds about "
        "70% of foundry revenue and makes nearly every AI accelerator.\n"
        "- **Samsung and Intel spend heavily without closing the gap.** Both "
        "invest tens of billions a year in fabs with limited share gains, and "
        "both cut capex in 2025 while TSMC raised it.\n"
        "- **CoWoS packaging is the tightest manufacturing bottleneck.** It "
        "mounts the processor and its memory side by side on one base so they "
        "can talk at full speed. Capacity rose about 5.5x from 2023 to 2025, "
        "reaches about 9x by end-2026 and remains fully booked, with overflow "
        "going to outsourced assembly firms (ASE, Amkor).\n"
        "- **Packaging allocation decides which AI chips ship**, giving a step "
        "worth 7 to 9% of TSMC revenue outsized strategic weight.")

    st.markdown("---")
    st.markdown("#### Revenue & capex by key player (\\$B)")
    st.caption(
        "**Sources:** TSMC, Samsung, Intel results (Samsung USD-converted KRW).  \n"
        "**Notes:** TSMC only manufactures chips others design; Samsung and "
        "Intel both design and make their own, so they are shown at "
        "total-company scale (Samsung incl. memory, phones and displays; Intel "
        "incl. products) and overstate the foundry business while showing "
        "relative investment scale.")
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
        "**Sources:** TSMC, Samsung, Intel results.  \n**Notes:** TSMC 2026E capex "
        "guidance \\$52-56B; CoWoS is about 7-9% of TSMC revenue, with packaging "
        "overflow going to ASE and Amkor.")

    cowos25 = float(cowos.loc[cowos.year == 2025, "cowos_kwpm"].iloc[0])
    cowos26 = float(cowos.loc[cowos.year == 2026, "cowos_kwpm"].iloc[0])
    cowos26_lo = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_low"].iloc[0])
    cowos26_hi = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_high"].iloc[0])

    st.markdown("---")
    k1, k2, k3 = st.columns(3)
    k1.metric("CoWoS capacity 2025", f"{cowos25:.0f}k wpm", "~2× vs 2024")
    k2.metric("CoWoS 2026E", f"{cowos26_lo:.0f}-{cowos26_hi:.0f}k wpm", "fully booked")
    cowos23 = float(cowos.loc[cowos.year == 2023, "cowos_kwpm"].iloc[0])
    k3.metric("Growth 2023→2026E", f"~{cowos26/cowos23:.0f}×", "still supply-short")

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
        "**Sources:** TrendForce.  \n**Notes:** CoWoS capacity rose about 5.5x "
        "from 2023 to 2025 and reaches about 9x on the 2026 midpoint (the bar "
        "range spans 6x to 11x); it remains sold out and is about 7-9% of TSMC "
        "revenue.")

# --------------------------------------------------------------------------- #
# 3 · Systems
# --------------------------------------------------------------------------- #
with tab_systems:
    st.markdown("### 3 · Servers")
    st.markdown(
        "- **Server makers were among the first to profit from the AI "
        "buildout.** They turn GPUs into deployable racks, and their revenue "
        "inflected from 2023.\n"
        "- **Most AI servers come from Taiwanese contract manufacturers.** "
        "Foxconn, Quanta and Wistron build unbranded machines to hyperscaler "
        "designs, a lower-margin and less disclosed channel than the listed "
        "Dell (ISG), Supermicro and HPE.\n"
        "- **Access to NVIDIA supply drives growth.** Supermicro, an early "
        "allocation winner, grew from \\$3B of revenue toward \\$40B guidance in "
        "six years, and Dell's ISG grew 40% in its latest fiscal year.\n"
        "- **Margins stay thin because NVIDIA prices the scarce input.** System "
        "builders earn single digits to low teens while NVIDIA earns about 60% "
        "on the same box.")

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
        "**Sources:** company filings (contract-manufacturer figures are "
        "server/cloud-segment estimates, currency-converted).  \n**Notes:** the "
        "branded vendors (Dell ISG, Supermicro, HPE) plus the Taiwanese "
        "contract manufacturers that carry most AI-server "
        "volume; Foxconn's Cloud & Networking segment alone (about \\$90B in "
        "2025) tops any branded OEM. Dell fiscal years are plotted on the "
        "calendar year they mostly cover; 2026 Supermicro and HPE bars are "
        "guidance.")

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
        "**Sources:** company filings (HPE and Foxconn estimated; others reported).  \n"
        "**Notes:** latest-year segment or group operating margin. Assemblers earn "
        "single digits to low teens because NVIDIA prices the scarce input and "
        "itself runs about 60% on the same box; the contract manufacturers "
        "(Foxconn about 3-4%) sit "
        f"lowest. Data as of {DATA_UPDATED}.")

# --------------------------------------------------------------------------- #
# 4 · Networking
# --------------------------------------------------------------------------- #
with tab_network:
    st.markdown("### 4 · Networking")
    st.markdown(
        "- **As clusters pass 100,000 GPUs, the network sets training "
        "efficiency.** Value shifts to back-end fabrics and optics: NVIDIA "
        "bundles its own interconnect (NVLink, InfiniBand), Arista's revenue "
        "roughly quadrupled since 2020, and Broadcom supplies the switch chips.\n"
        "- **Data-center networking grows while mobile equipment shrinks.** "
        "Data-center gear tracks AI capex; mobile-network vendors (Ericsson, "
        "Nokia Mobile Networks, Huawei) stagnate as 5G buildouts mature.\n"
        "- **Vendors are buying their way into data-center optics.** Nokia's "
        "\\$2.3B Infinera acquisition (completed February 2025) moved a "
        "mobile-era vendor into optical interconnect for AI data centers.\n"
        "- **Vendors selling to carriers face a flat market.** US carrier capex "
        "guidance for 2026 sits near \\$50B with no 6G cycle ahead, while the "
        "hyperscaler budget grew about 2.5x in two years; Arista's growth and "
        "Ericsson's decline track that split.\n"
        "- **Optics and switch-chip supply are the layer's bottlenecks** as "
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
        "**Sources:** company filings (Nokia and Ericsson USD-converted, capex "
        "approximate).  \n**Notes:** total-company figures. All four are asset-light, "
        "capex about 1-3% of revenue; the divergence is the story, Arista has "
        "roughly quadrupled since 2020 while Nokia and Ericsson have shrunk.")

    st.markdown("#### Network infrastructure and data-center networking (\\$B)")
    fign4 = px.bar(
        networking, x="year", y="revenue_b", color="company", barmode="group",
        color_discrete_map={"Arista": GREEN, "Ciena": BLUE, "Nokia NI": YELLOW},
        labels={"year": "Year", "revenue_b": "Revenue ($B)", "company": ""})
    fign4.update_layout(height=340, hovermode="x unified", legend_title="")
    st.plotly_chart(fign4, width="stretch")
    st.caption(
        "**Sources:** company filings.  \n**Notes:** the AI-exposed side. Arista and Ciena "
        "are pure-plays (total revenue); Nokia is Network Infrastructure only "
        "(fixed, IP and optical, excludes mobile; +9% in 2025, now includes "
        "Infinera). Cisco's Networking segment (about \\$28-30B) sits in a "
        "diversified firm and is left out.")

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
        "**Sources:** company filings (segment figures currency-converted, "
        "approximate).  \n**Notes:** the mobile side, flat to declining since the 5G "
        "peak. Nokia Mobile Networks fell after losing the AT&T contract in "
        "2024; Huawei is the ICT infrastructure division (definitions changed "
        f"over time). Samsung and ZTE not charted. Data as of {DATA_UPDATED}.")

# --------------------------------------------------------------------------- #
# 4 · Power & Data Centers
# --------------------------------------------------------------------------- #
with tab_dc:
    st.markdown("### 5 · Data Centers")
    st.markdown(
        "- **US data-center construction is overtaking office construction.** "
        "The two crossed on a monthly run-rate in late 2025, and data centers "
        "are on track to lead for the full year in 2026.\n"
        f"- **About {gw['capacity_gw'].sum():.0f} GW of gigawatt-scale capacity "
        "is announced.** It comes from hyperscaler self-build, colocation "
        "providers (Equinix, Digital Realty, who own the building and power and "
        "rent space to tenants who bring their own hardware) and dedicated AI "
        "campuses such as Stargate, Hyperion and Colossus.\n"
        "- **Electricity is now the binding constraint.** High-voltage "
        "substations take 3 to 5 years, 7 of 13 US grid regions are projected "
        "below safety margins by 2030, and Goldman estimates about \\$720B of "
        "grid investment is needed this decade.\n"
        "- **Power access decides where capacity gets built**, making on-site "
        "generation and nuclear deals a competitive edge.")

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
        "**Sources:** US Census construction spending (2015-2022 monthly via Our "
        "World in Data; 2023-25 benchmark-revised annuals; office mid-years "
        "approximate).  \n**Notes:** data-center spend went from about \\$3B (2015) to "
        "about \\$41B (2025); office peaked near \\$72B (2020) and fell to "
        "\\$49B. On a monthly run-rate the two crossed in Dec 2025. Data as of "
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
        "**Sources:** company and project announcements.  \n**Notes:** announced or "
        "planned site totals at varying horizons (Hyperion's 5 GW scales to "
        "2030); most is still under construction, so read it as the build "
        "pipeline.")

    st.caption(
        "**Sources:** Goldman Sachs, IEA, NextBigFuture, Introl, Sherwood, Data "
        "Center Knowledge.  \n**Notes:** high-voltage substations take 3-5 years, 7 of "
        "13 US grid regions are projected below safety margins by 2030, and "
        "about \\$720B of grid spend is needed through 2030. Power, not capital, "
        "is the likely gate on the 2027+ buildout.")

# --------------------------------------------------------------------------- #
# 5 · Hyperscalers — capex deep-dive
# --------------------------------------------------------------------------- #
with tab_hyper:
    st.markdown("### 6 · Hyperscalers")
    st.markdown(
        "- **Big-5 capex roughly doubles in 2026 and nears \\$1T in 2027.** It "
        f"rises from \\${total_now:,.0f}B in FY2025 to \\${CAPEX_FC:,.0f}B in "
        "fiscal 2026, above global upstream oil and gas investment. These orders "
        "set accelerator volumes, packaging allocation and the gigawatt "
        "pipeline for every layer upstream.\n"
        "- **They increasingly fund capex with debt and equity.** Capex reached "
        "174% of operating cash flow at Oracle in its year to May 2026 and 94% "
        "at Amazon in 2025; the group issued \\$121B of bonds in 2025, four "
        "times its five-year average, and Alphabet raised about \\$85B of "
        "equity.\n"
        "- **Capex has doubled as a share of revenue since 2023**, from 9-20% "
        "to 18-37% in FY2025 (Oracle reached 83% in its year to May 2026), for "
        "businesses that were asset-light a decade ago.\n"
        "- **Returns are starting to compress.** ROCE is still about three times "
        "the telecom level but fell in 2025 as capital employed surged; how far "
        "it falls as the 2025-26 capex depreciates is the central question for "
        "the whole chain.")
    st.markdown("---")

    st.caption("**Notes:** actuals are total reported capex with no AI share "
               "applied; hatched bars are forecasts.")
    g = view.sort_values(["company", "fiscal_year"]).copy()
    g["yoy_%"] = g.groupby("company")["capex_usd_b"].pct_change() * 100
    # One stacking order for both capex charts: largest spender in the latest
    # complete year at the bottom; the legend is reversed so it reads like the
    # stack, top to bottom.
    stack_order = (view[view["fiscal_year"] == YR]
                   .groupby("company")["capex_usd_b"].sum()
                   .sort_values(ascending=False).index.tolist())

    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Annual capex with 2026-27 outlook (\\$B)**")
        fc_year = FC_YEAR                                # 2026
        cons_year = fc_year + 1                          # 2027, aggregate only
        hist = capex[capex["fiscal_year"] <= fc_year]
        fig2 = go.Figure()
        totals = {}
        for co in stack_order:
            col = COMPANY_COLORS.get(co, GREY)
            act = hist[hist["company"] == co].sort_values("fiscal_year")
            fig2.add_trace(go.Bar(
                x=act["fiscal_year"], y=act["capex_usd_b"], name=co,
                marker_color=col, legendgroup=co))
            for y_, v in zip(act["fiscal_year"], act["capex_usd_b"]):
                totals[y_] = totals.get(y_, 0) + v
            # Guidance midpoint only where the fiscal year has not closed yet
            if fc_year not in set(act["fiscal_year"]):
                mid = float(guidance.loc[guidance["company"] == co,
                                         "capex_mid_b"].iloc[0])
                fig2.add_trace(go.Bar(
                    x=[fc_year], y=[mid], name=f"{co} (guidance midpoint)",
                    marker_color=col, marker_pattern_shape="/",
                    legendgroup=co, showlegend=False))
                totals[fc_year] = totals.get(fc_year, 0) + mid
        fig2.add_trace(go.Bar(
            x=[cons_year], y=[CAPEX_CONSENSUS_B], name="Big-5 (consensus)",
            marker_color=GREY, marker_pattern_shape="/", showlegend=False))
        totals[cons_year] = CAPEX_CONSENSUS_B
        tx = sorted(totals)
        fig2.add_trace(go.Scatter(
            x=tx, y=[totals[x] for x in tx], mode="text",
            text=[f"~${totals[x]/1000:.1f}T" if x == cons_year
                  else f"${totals[x]:,.0f}B" for x in tx],
            textposition="top center", showlegend=False, hoverinfo="skip"))
        fig2.update_xaxes(
            tickmode="array", tickvals=tx,
            ticktext=[f"{x}E" if x >= fc_year else str(x) for x in tx])
        fig2.update_layout(barmode="stack", height=360, hovermode="x unified",
                           legend_title="", legend_traceorder="reversed",
                           yaxis_title="Capex ($B)", xaxis_title="Fiscal year",
                           yaxis_range=[0, max(totals.values()) * 1.15])
        st.plotly_chart(fig2, width="stretch")
        st.caption(
            "**Sources:** 10-K filings (EDGAR XBRL); 2026 company guidance; 2027 "
            "consensus (Moody's, Goldman, BofA).  \n"
            "**Notes:** hatched bars are forecasts. Microsoft and Oracle have "
            "already closed fiscal 2026, so their 2026 bars are actuals; "
            "Alphabet, Amazon and Meta show guidance midpoints. 2027 is an "
            "aggregate with no company split.")
    with colB:
        st.markdown("**YoY capex growth (%)**")
        fig3 = px.bar(
            g[g["fiscal_year"] >= 2021], x="fiscal_year", y="yoy_%",
            color="company", barmode="group",
            color_discrete_map=COMPANY_COLORS,
            category_orders={"company": stack_order},
            labels={"fiscal_year": "Fiscal year", "yoy_%": "YoY growth (%)"})
        fig3.update_layout(height=360, hovermode="x unified", legend_title="",
                           legend_traceorder="reversed")
        st.plotly_chart(fig3, width="stretch")

    st.markdown("**Quarterly capex (\\$B)**")
    qv = capex_q.copy()
    qv["period_end"] = pd.to_datetime(qv["period_end"])
    qv["capex_b"] = qv["capex_usd_m"] / 1000.0
    qv = qv[qv["period_end"] >= "2023-01-01"]
    qv["quarter"] = (qv["period_end"].dt.year.astype(str) + " Q" +
                     qv["period_end"].dt.quarter.astype(str))
    # Oracle's quarters close a month early, so a new quarter can briefly hold
    # only Oracle; show a quarter only once every company has reported it.
    qv = qv[qv.groupby("quarter")["company"].transform("nunique")
            == capex_q["company"].nunique()]
    qv = qv.sort_values("period_end")
    figq = px.bar(
        qv, x="quarter", y="capex_b",
        color="company", barmode="stack", color_discrete_map=COMPANY_COLORS,
        category_orders={"company": stack_order},
        labels={"quarter": "Calendar quarter of period end",
                "capex_b": "Capex ($B)"})
    q_tot = qv.groupby("quarter", sort=False)["capex_b"].sum()
    figq.add_trace(go.Scatter(
        x=q_tot.index, y=q_tot.values, mode="text",
        text=[f"${v:,.0f}B" for v in q_tot.values],
        textposition="top center", showlegend=False, hoverinfo="skip"))
    figq.update_layout(height=380, hovermode="x unified", legend_title="",
                       legend_traceorder="reversed",
                       yaxis_range=[0, q_tot.max() * 1.15])
    st.plotly_chart(figq, width="stretch")
    cal25 = qv.loc[qv["period_end"].dt.year == 2025, "capex_b"].sum()
    st.caption(
        "**Sources:** 10-Q and 10-K filings (SEC EDGAR XBRL).  \n**Notes:** "
        "quarterly cash purchases of PP&E, derived from year-to-date 10-Q "
        "figures; each company's quarters sum exactly to its fiscal-year total. "
        "Bars group quarters by the calendar quarter they end in, so calendar "
        f"2025 sums to \\${cal25:,.0f}B against \\${total_now:,.0f}B for fiscal "
        "2025 in the annual chart: Microsoft's and Oracle's fiscal years end "
        f"mid-year. Data as of {DATA_UPDATED}.")

    st.markdown("---")
    st.markdown("#### How the capex is funded: capex vs operating cash flow")
    st.caption(
        "**Notes:** capex as a share of operating cash flow, both from 10-K "
        "filings; above 100% a company funds the gap externally.")
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
    fy26 = fund[fund["fiscal_year"] == FC_YEAR]
    ratio26 = " and ".join(f"{r.company} {r.capex_pct_ocf:.0f}%"
                           for r in fy26.itertuples())
    st.caption(
        "**Sources:** 10-K filings (EDGAR XBRL), Janus Henderson, Wolf Street.  \n"
        f"**Notes:** FY2025: {ratio_line}. Fiscal 2026, closed so far: "
        f"{ratio26}. The group issued \\$121B of bonds in 2025 (4x the "
        "\\$28B five-year average) incl. Meta's \\$30B and an Alphabet 100-year "
        f"bond, at sub-5% rates. Data as of {DATA_UPDATED}.")

    st.caption(
        "**Notes:** Microsoft's fiscal year ends June 30 and Oracle's May 31 (not "
        "calendar-aligned); Amazon capex includes fulfilment and logistics, not "
        "only AWS.")

    st.markdown("---")
    st.markdown("#### The free-cash-flow transfer: hyperscalers to chipmakers")
    ftr = fcf_transfer.copy()
    ftcolors = {"Hyperscalers": "#4FC3F7", "Semiconductors": BLUE}
    figft = go.Figure()
    for grp, col in ftcolors.items():
        g = ftr[ftr["group"] == grp].sort_values("year")
        rep = g[g["source_type"] == "reported"]
        figft.add_trace(go.Scatter(
            x=rep["year"], y=rep["fcf_b"], name=grp, mode="lines+markers",
            line=dict(color=col, width=3)))
        # dotted forecast segment, anchored to the last reported point
        fc = g[(g["source_type"] == "forecast") |
               (g["year"] == rep["year"].max())].sort_values("year")
        figft.add_trace(go.Scatter(
            x=fc["year"], y=fc["fcf_b"], name=f"{grp} (2026E)",
            mode="lines+markers", line=dict(color=col, width=3, dash="dot"),
            showlegend=False))
    figft.add_hline(y=0, line_dash="dash", line_color=GREY)
    figft.update_layout(height=380, hovermode="x unified", legend_title="",
                        yaxis_title="Free cash flow ($B)", xaxis_title="Fiscal year")
    st.plotly_chart(figft, width="stretch")
    st.caption(
        "**Sources:** company 10-K and 10-Q filings (EDGAR XBRL); 2026 capex as "
        "in the annual chart; 2027 capex from consensus (Moody's, Goldman, "
        "BofA); NVIDIA FY2028 from its 70% growth guidance; Broadcom 2027 from "
        "its own line of sight; framing after BofA Global Research.  \n"
        "**Notes:** free cash flow is operating cash flow minus capex; solid is "
        "reported, dotted is 2026-27E. Hyperscaler FCF falls from "
        f"\\${HYP_FCF[2024]:.0f}B (2024) to about \\${HYP_FCF[2026]:.0f}B in "
        "fiscal 2026, with Oracle and Amazon negative, and to about "
        f"\\${HYP_FCF[2027]:.0f}B in 2027 as capex nears \\$1T. Chipmaker FCF "
        f"rises from \\${SEMI_FCF[2025]:.0f}B (2025) to about "
        f"\\${SEMI_FCF[2026]:.0f}B in 2026 and \\${SEMI_FCF[2027]:.0f}B in 2027, "
        "led by NVIDIA and Micron. Hyperscalers use fiscal years; chipmakers "
        "use the calendar year each fiscal year mostly covers, as in the "
        f"Silicon tab. Data as of {DATA_UPDATED}.")

    st.markdown("---")
    st.markdown("#### Does the capex still earn its keep? ROCE over time")
    st.caption(
        "**Notes:** return on capital employed (operating income over total assets "
        "minus current liabilities); the shaded band is an estimated 8-10% cost "
        "of capital (Damodaran, software and internet sectors).")
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
        "**Sources:** 10-K filings (EDGAR XBRL).  \n**Notes:** returns are still above the "
        "roughly 8-10% cost of capital and 3-4x telecom levels. The 2025 dip is "
        "the signal: Alphabet fell 31% to 26% as capital employed jumped "
        "(\\$361B to \\$493B) faster than income; most 2025-26 capex has not "
        "started depreciating, so the drag builds. Watch the depreciation "
        "assumptions: Microsoft extended data-center useful life from 15 to 25 "
        "years from FY2027, which lowers annual depreciation and lifts reported "
        "returns, though roughly two-thirds of recent capex is short-lived GPUs "
        "on a much faster replacement cycle. Amazon and Oracle sit lower "
        f"on retail and broader software mix. Data as of {DATA_UPDATED}.")

    st.markdown("---")
    st.markdown("#### 2026 outlook by company")
    st.caption(
        "**Notes:** same basis as the annual chart: the reported actual where a "
        "company's fiscal 2026 has closed (Microsoft, Oracle), otherwise the "
        "guidance midpoint, with the guided range shown as an error bar.")
    actual25 = view[view["fiscal_year"] == 2025].set_index("company")["capex_usd_b"]
    closed26 = capex[capex["fiscal_year"] == FC_YEAR].set_index("company")["capex_usd_b"]
    gtbl = guidance.copy()
    is_act = gtbl["company"].isin(closed26.index)
    for col in ("capex_low_b", "capex_mid_b", "capex_high_b"):
        gtbl[col] = gtbl[col].where(~is_act, gtbl["company"].map(closed26))
    gtbl["fy2025_actual_b"] = gtbl["company"].map(actual25)
    gtbl["growth_%"] = (gtbl["capex_mid_b"] / gtbl["fy2025_actual_b"] - 1) * 100
    gtbl["basis"] = is_act.map({True: "FY2026 actual", False: "Guidance midpoint"})
    act_note = {
        "Microsoft": "Year to June 2026; separately guides $175B for calendar "
                     "2026, incl. finance leases",
        "Oracle": "Year to May 2026; guides $90-95B for FY2027"}
    gtbl["note"] = [act_note.get(c, d) for c, d
                    in zip(gtbl["company"], gtbl["definition"])]
    gtbl["source"] = gtbl["source"].where(~is_act, "10-K (EDGAR XBRL)")
    gtbl = gtbl.set_index("company").loc[stack_order].reset_index()

    figg = go.Figure()
    figg.add_trace(go.Bar(x=gtbl["company"], y=gtbl["fy2025_actual_b"],
                          name="FY2025 actual", marker_color=GREY))
    figg.add_trace(go.Bar(
        x=gtbl["company"], y=gtbl["capex_mid_b"],
        name="FY2026 (hatched = guidance midpoint)", marker_color=BLUE,
        marker_pattern_shape=["" if b == "FY2026 actual" else "/"
                              for b in gtbl["basis"]],
        error_y=dict(type="data", symmetric=False,
                     array=gtbl["capex_high_b"] - gtbl["capex_mid_b"],
                     arrayminus=gtbl["capex_mid_b"] - gtbl["capex_low_b"])))
    figg.update_layout(barmode="group", height=360, legend_title="",
                       yaxis_title="Capex ($B)", hovermode="x unified")
    st.plotly_chart(figg, width="stretch")
    st.metric("Big-5 capex FY2026E", f"${gtbl['capex_mid_b'].sum():,.0f}B",
              f"+{(gtbl['capex_mid_b'].sum()/actual25.sum()-1)*100:.0f}% vs FY25")
    st.dataframe(
        gtbl[["company", "fy2025_actual_b", "capex_low_b", "capex_mid_b",
              "capex_high_b", "growth_%", "basis", "note", "source"]].rename(
            columns={"company": "Company", "fy2025_actual_b": "FY25 $B",
                     "capex_low_b": "FY26 low", "capex_mid_b": "FY26 mid",
                     "capex_high_b": "FY26 high", "growth_%": "Growth %",
                     "basis": "Basis", "note": "Note",
                     "source": "Source"}).style.format({
            "FY25 $B": "{:.1f}", "FY26 low": "{:.0f}", "FY26 mid": "{:.0f}",
            "FY26 high": "{:.0f}", "Growth %": "{:+.0f}"}),
        width="stretch", hide_index=True)
    st.caption(
        "**Notes:** memory inflation absorbs part of the increase (Microsoft "
        "flagged about \\$25B, Amazon added \\$20B on memory alone), so higher "
        "capex is not one-to-one more compute. Meta's guidance includes "
        "finance-lease payments, a slightly broader basis than the cash actuals. "
        "Microsoft trimmed its calendar-2026 guide from \\$190B to \\$175B through "
        "an accounting change, with the plan itself unchanged: a longer useful "
        "life for data centers (15 to 25 years) moves more leases to operating "
        "treatment, outside reported capex.")

    st.markdown("---")
    st.markdown("#### Hyperscaler capex vs accelerator vendor revenue (\\$B)")
    st.caption(
        "**Notes:** combined Big-5 capex against NVIDIA and AMD data-center segment "
        "revenue, both reported; shows how much of the capex lands at the chip "
        "vendors.")
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
        "**Sources:** company filings.  \n**Notes:** NVIDIA's fiscal year ends in late "
        "January, so FY2026 (\\$194B data-center revenue) maps to calendar "
        "2025; AMD's data-center segment starts in 2022. Capex also funds land, "
        "buildings, power and networking, and the vendors sell beyond these "
        f"five buyers, so the series are not a closed loop. Data as of {DATA_UPDATED}.")

# --------------------------------------------------------------------------- #
# 6 · NeoClouds
# --------------------------------------------------------------------------- #
with tab_neo:
    st.markdown("### 7 · NeoClouds")
    st.markdown(
        "- **NeoClouds sell access to scarce GPUs, financed against the GPUs "
        "themselves.** They buy accelerators (the specialized chips, mostly "
        "NVIDIA GPUs, that train and run AI models), install them in leased "
        "data-center space and rent the capacity by the hour or on multi-year "
        "contracts. Customers are AI labs (OpenAI, Anthropic, Meta AI), "
        "enterprises training their own models and the hyperscalers themselves "
        "when their own buildout lags demand: Microsoft has been CoreWeave's "
        "largest customer and signed \\$17-19B with Nebius. Suppliers often "
        "guarantee the leases or extend the credit.\n"
        "- **The largest players built about \\$100B of backlog in two years.** "
        "CoreWeave holds about \\$104B, Nscale \\$103B and Nebius \\$45B. "
        "CoreWeave and Nebius are listed, Crusoe and Lambda private, and Nscale "
        "filed for a New York listing in September 2026 at a \\$30-35B target, "
        "up from \\$14.6B privately.\n"
        "- **The economics behind those backlogs are deeply negative.** Nscale "
        "lost \\$1.02B on \\$140.6M of revenue in the first half of 2026, about "
        "seven times revenue; Oracle, running the same model at far greater "
        "scale, spent \\$28B on capex in one quarter with free cash flow of "
        "minus \\$5B.\n"
        "- **A few anchor tenants carry most of the backlog.** OpenAI added "
        "\\$11.2B to CoreWeave's backlog and Meta committed \\$27B to Nebius. "
        "These contracts let NeoClouds borrow cheaply against their GPUs, and "
        "if one tenant slows or fails, much of the backlog and the debt behind "
        "it is exposed at once.\n"
        "- **Some backlog can be cancelled at short notice.** The Anthropic and "
        "xAI agreement signed in May 2026, priced near \\$38B per gigawatt a "
        "year, lets either side exit on 90 days' notice, according to SpaceX's "
        "listing prospectus.\n"
        "- **Contracts outlast the chips that serve them.** Over \\$20B of "
        "sector debt is secured against GPUs that depreciate over 4 to 6 years, "
        "while rental contracts can run past ten, leaving operators exposed to "
        "reinvestment costs they cannot price today. The industry expects later "
        "tenants to accept older chips at lower prices, which is untested.\n"
        "- **NVIDIA finances its own customers.** It is supplier, investor and "
        "in places guarantor to the firms buying its chips. Vendor finance of "
        "this kind preceded the 2000 telecom overbuild, because the capital came "
        "from the party that benefited from more capacity.\n"
        "- **NeoClouds are a leveraged bet on sustained compute scarcity.**")
    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    c1.metric("CoreWeave backlog (Q2 2026)", "$104.2B", "+246% YoY")
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
        "**Sources:** company filings and press; FT on Nscale (Nebius bar "
        "estimated from disclosed Microsoft \\$17-19B and Meta \\$27B "
        "contracts).  \n**Notes:** "
        "CoreWeave's backlog (\\$104.2B at Q2 2026, up 246% YoY from \\$30.1B) dwarfs "
        "revenue and is concentrated (OpenAI added \\$11.2B); Crusoe and Lambda "
        "are private (revenue only) and Nscale shows about \\$103B of total "
        "contract value from its September 2026 IPO filing. Backlog is "
        "contracted intent, not "
        "guaranteed revenue: terms vary and some carry 90-day termination "
        "rights. GPUs depreciate over 4-6 years while "
        "rental pricing can move faster, and over \\$20B of sector debt is "
        f"secured against them. Data as of {DATA_UPDATED}.")

# --------------------------------------------------------------------------- #
# 8 · AI Labs (demand)
# --------------------------------------------------------------------------- #
with tab_labs:
    st.markdown("### 8 · AI Labs")
    st.markdown(
        "- **Revenue is concentrating in two labs.** Anthropic (\\$65B) and "
        "OpenAI (\\$40B) run at about \\$105B combined, and their compute "
        "commitments underwrite NeoCloud backlogs and hyperscaler buildouts.\n"
        "- **Serving models is profitable; training the next one is where labs "
        "lose money.** Inference runs at roughly 40 to 50% gross margin "
        "(industry estimates), but each new model costs more to train than the "
        "labs earn.\n"
        "- **Usage is broad but shallow.** 900M to 1B people use ChatGPT weekly "
        "but only 5 to 6% pay, and 55% of US adults have tried generative AI "
        "but only about 12% use it every workday.\n"
        "- **Frontier capability has converged.** Leading labs score within "
        "about six points of each other (88 to 94) on GPQA-Diamond, and the "
        "model layer shows no clear network effects.\n"
        "- **Chinese open-weight models set the price floor.** DeepSeek, "
        "Alibaba's Qwen, Zhipu's GLM and Moonshot's Kimi trail the closed "
        "frontier by single digits at one-third to one-tenth of the price "
        "(DeepSeek about \\$0.27 per million input tokens). Open weights can be "
        "self-hosted, which pushes API switching costs toward zero.\n"
        "- **Spending and startups are moving to the application layer.** "
        "Enterprise AI application spend reached \\$19B in 2025, and about 80% "
        "of Y Combinator's 2025 companies are AI startups.")

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
            "**Sources:** Bloomberg via TechCrunch; Sacra; Epoch AI.  \n"
            "**Notes:** annualized run-rates at various dates (Anthropic Jul-26, "
            "OpenAI Aug-26, xAI Dec-25, Mistral Jan-26). Anthropic overtook "
            "OpenAI, going from \\$1B to \\$65B in about 19 months. The two are "
            "not strictly comparable: Anthropic reports gross of cloud-reseller "
            "spend, OpenAI closer to net.")
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
            "**Sources:** model and system cards (GPT-4 35.7, Claude 3.5 Sonnet "
            "59.4, o1 78.0, Gemini 2.5 Pro 84.0, DeepSeek R1 71.5; two points "
            "estimated).  \n**Notes:** best published GPQA-Diamond score per lab at "
            f"major releases; Chinese labs have closed most of the gap. Data as of {DATA_UPDATED}.")

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
        "**Sources:** a16z (\"LLMflation\"), company price lists, Benedict Evans on "
        "token pricing.  \n**Notes:** blended list price (3:1 input:output) for a "
        "fixed capability level. GPT-3-class fell from \\$60 to about \\$0.06 "
        "in three years (about 1000x); GPT-4-class about 100x since 2023 and "
        "around \\$0.30-0.50 by 2026, the decline slowing toward compute cost. "
        "Falling price per token has not meant falling revenue: usage outgrows "
        "price, so total spend and lab run-rates keep rising (Anthropic and "
        f"OpenAI about \\$105B combined). Data as of {DATA_UPDATED}.")

    st.markdown("#### ChatGPT weekly active users (millions)")
    figw = px.area(chatgpt, x="date", y="wau_m",
                   labels={"date": "", "wau_m": "Weekly active users (M)"})
    figw.update_traces(line_color="#10A37F",
                       fillcolor="rgba(16,163,127,0.2)")
    figw.update_layout(height=280)
    st.plotly_chart(figw, width="stretch")
    st.caption(
        "**Sources:** OpenAI disclosures (May-2026 figure a third-party estimate, "
        "flagged in data).  \n**Notes:** weekly active users went from 100M (Aug-23) "
        "to 900M (Feb-26), with estimates past 1B by May 2026.")

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
                            xaxis_range=[0, 60],
                            yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(figud, width="stretch")
        st.caption(
            "**Sources:** Bick, Blandin and Deming, Real-Time Population Survey "
            "(NBER / St. Louis Fed / Fed FEDS note).  \n**Notes:** about 55% of US "
            "working-age adults have used generative AI (2025 wave, up from 40% "
            "in late 2024), but daily use stays low (about 12% every workday); "
            "the two past-week measures are late-2024 readings, flagged in "
            "data.")
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
            "**Sources:** Menlo Ventures, State of Generative AI in the Enterprise "
            "2025.  \n**Notes:** enterprise genAI application spend reached \\$19B in "
            "2025 (of \\$37B total, up from \\$11.5B in 2024); coding tools are "
            "the largest single use case at \\$4.2B.")

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
        "**Sources:** YC directory analyses and press reports (2015-2022 "
        "approximate).  \n**Notes:** AI share of YC batches ran 5-15% (2015-2022), "
        "then 44% (2023), about 70% (2024) and about 80% (2025); startup "
        f"formation has concentrated almost entirely on AI. Data as of {DATA_UPDATED}.")

    st.caption(
        "**Notes:** revenue is concentrating in Anthropic and OpenAI while "
        "benchmark scores converge around 90; lab revenue and multi-year "
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
        "- **Integrators are a measurable read on real AI adoption.** Deploying "
        "AI in enterprises is services-heavy work, and companies often pay "
        "integrators (Accenture, TCS, Infosys, Capgemini) before they pay model "
        "vendors at scale.\n"
        "- **Accenture booked about \\$11B of GenAI work in under three "
        "years.** Bookings grew from \\$0.3B (FY2023) to \\$5.9B (FY2025) and "
        "\\$2.2B in Q1 FY2026, after which Accenture stopped reporting the "
        "metric as AI became embedded across its delivery.\n"
        "- **GenAI work mostly replaces legacy work.** Despite those bookings, "
        "Accenture's total revenue grew only about 5% a year.\n"
        "- **AI is shrinking the labor-based delivery model.** The market began "
        "pricing this in mid-2026: Accenture fell about 18% on a guidance cut "
        "(consulting revenue +1%, bookings -2%), IBM about 25% as AI hardware "
        "crowded out software and services budgets, and TCS and Infosys sold "
        "off.\n"
        "- **The pressure lands first on the most standardized work.** TCS "
        "revenue fell 0.5% in dollars (2.4% in constant currency) in its year "
        "to March 2026, while Accenture, weighted to higher-end transformation "
        "work, grew 6% in dollars (5% in local currency) in its year to August "
        "2026 and guides 3 to 6% for FY2027.")

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
        "**Sources:** company results (Capgemini EUR-to-USD approximate).  \n**Notes:** "
        "fiscal years differ (Accenture ends August, TCS and Infosys March, "
        "Capgemini calendar), so 2026 has no Capgemini bar until it reports in "
        "early 2027. Deloitte and IBM Consulting are comparable but private or "
        "embedded in a larger group.")

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
        "**Sources:** Accenture 8-K filings.  \n**Notes:** GenAI new bookings ran \\$0.3B "
        "(FY2023), \\$3.0B (FY2024), \\$5.9B (FY2025) and a final \\$2.2B in Q1 "
        "FY2026 (about \\$11B cumulative); Accenture said Q1 FY2026 was the last "
        "quarter it would report the metric separately as advanced AI became "
        f"embedded across its work. Data as of {DATA_UPDATED}.")

# --------------------------------------------------------------------------- #
# 10 · Telecoms (context)
# --------------------------------------------------------------------------- #
with tab_telco:
    st.markdown("### 10 · Telecoms")
    st.markdown(
        "- **Telecoms carry AI to users but capture little of its value.** "
        "Every model reaches users over a fixed or mobile network, but "
        "connectivity is sold in flat-rate plans that do not scale with the "
        "traffic carried.\n"
        "- **A decade of 30x traffic growth produced bond-like returns.** Mobile "
        "traffic grew about 30x since 2015 while sector capex held near "
        "\\$300B. Shareholder returns since 2015 ran about 5% a year at Verizon "
        "and 7% at AT&T against about 12% for the MSCI World; BT shareholders "
        "lost about half, and only Deutsche Telekom came close to the market.\n"
        "- **Network capex earned about its cost of capital at best.** ROCE for "
        "major developed-market telcos averaged 4 to 9% over 2020-25, against a "
        "6 to 8% cost of capital.\n"
        "- **Carrier capex has flattened with no 6G cycle ahead.** Global "
        "telecom capex in 2024 was the lowest since 2011, and US carrier "
        "guidance for 2026 (AT&T \\$23-24B, Verizon \\$16-16.5B, T-Mobile "
        "\\$10B) points to about \\$50B. That lifts carrier free cash flow and "
        "dividends and caps growth for their equipment vendors.\n"
        "- **AI traffic grows inside and between data centers, away from "
        "carrier access networks.** The heavy flows run on fiber backbones, so "
        "optical and data-center interconnect vendors absorb the growth.\n"
        "- **Telecoms are the cautionary precedent for AI infrastructure.** "
        "Heavy capex and real usage growth did not produce returns once the "
        "layer above commoditized the network.")

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
            "**Sources:** Ericsson Mobility Reports (mobile); Cisco VNI, ITU / "
            "TeleGeography (fixed, estimated).  \n**Notes:** mobile traffic rose from "
            "about 4.4 EB/month (2015) to about 126 EB (2024), with about 145 "
            "(2025) and 162 (2026) on Ericsson's path; fixed carries roughly 3x "
            "mobile. Hatched bars are forecasts; AI load lands mainly on the "
            "fixed and data-center side.")
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
            "**Sources:** Yahoo Finance adjusted closes (dividends reinvested, "
            "indexed to 100 at start-2015).  \n**Notes:** through early 2026, about "
            "+72% Verizon (about 5%/yr), +107% AT&T (about 7%), +175% Deutsche "
            "Telekom (about 10%) and -53% BT, versus +235% (about 12%/yr) for "
            "the MSCI World ETF. Price-only comparisons understate telco "
            "returns given 4-7% dividend yields.")

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
        "**Sources:** 10-K and 20-F filings (SEC EDGAR XBRL); Deutsche Telekom and "
        "BT approximated from annual reports (neither files with the SEC "
        "today).  \n**Notes:** ROCE is operating income over capital employed, "
        "averaged over the years shown, so it can differ from the latest-year "
        "figure on the Overview (AT&T averages 4% because of 2022 impairments, "
        "against about 7% in 2025). Only Verizon and BT reach the top of "
        "the 6-8% band; the sector earned roughly its cost of capital across "
        "the 5G buildout. One-offs distort single years but averages wash most "
        "out.")
    st.caption(
        "**BT earned an 8% return on its assets while shareholders lost half "
        "their money.** ROCE measures the whole asset base, while shareholder "
        "return goes to the thin equity slice behind it. BT carries roughly "
        "£15-20B of net debt and a large pension deficit, so little of the asset "
        "return reaches equity after interest and pension top-ups, and the "
        "shares de-rated as revenue stalled and Openreach capex rose. Data as "
        f"of {DATA_UPDATED}.")

    hyp_year = capex.groupby("fiscal_year")["capex_usd_b"].sum()

    k1, k2, k3 = st.columns(3)
    k1.metric("Global telecom capex 2024", "~$295B", "lowest since 2011")
    k2.metric("Big-5 hyperscaler capex 2025", f"${hyp_year.loc[2025]:.0f}B",
              "overtook telecom")
    k3.metric("Big-5 FY2026E", f"${CAPEX_FC:.0f}B",
              f"~{CAPEX_FC/295:.1f}x global telecom")

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
        x=[2025, FC_YEAR], y=[float(hyp_year.loc[2025]), CAPEX_FC],
        name="Big-5 hyperscaler capex (2026E)", mode="lines+markers",
        line=dict(color=BLUE, width=3, dash="dot")))
    figt.update_layout(height=380, hovermode="x unified", legend_title="",
                       yaxis_title="Capex ($B)", xaxis_title="Year")
    st.plotly_chart(figt, width="stretch")
    st.caption(
        "**Sources:** MTN Consulting (telecom); company filings (hyperscaler).  \n"
        "**Notes:** telecom is global industry capex, 2025-26 assumes the "
        "flat-to-declining path continues; hyperscaler is the Big-5 on the same "
        "2026 basis as the Hyperscalers tab. Dotted segments are forecasts. The "
        "lines crossed in 2025, and by 2026 hyperscaler capex is about "
        f"{CAPEX_FC/295:.1f} times global telecom capex.")

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
        "**Sources:** company filings and 2026 guidance (2025 approximate).  \n**Notes:** "
        "2026 guidance AT&T \\$23-24B (fiber), Verizon \\$16-16.5B (cut), "
        "T-Mobile about \\$10B. AT&T revenue includes WarnerMedia until the "
        "April 2022 spin-off; Verizon's 2022 capex peak is C-Band, T-Mobile's "
        "2021-22 peak is Sprint integration. Steady-state capex near \\$50B "
        f"with no 6G spike. Data as of {DATA_UPDATED}.")
