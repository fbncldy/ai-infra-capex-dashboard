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
        f"scarcities AI created are easing at once: compute is getting cheaper, "
        f"frontier models are converging, and the cost of building software has "
        f"collapsed. As each becomes abundant, the pricing power it gave its "
        f"layer erodes, and value accrues to what was scarce before AI: 1/ "
        f"distribution, 2/ proprietary data, 3/ regulatory position, and 4/ "
        f"customer switching costs.\n"
        f"- **The spend has reached a scale with few precedents, and it now "
        f"leans on debt.** Big-5 capex (Microsoft, Alphabet, Amazon, Meta, "
        f"Oracle) hit about **\\${total_now:,.0f}B** in FY2025 and is guided "
        f"near **\\${guide26:,.0f}B** for 2026, more than global upstream oil "
        f"and gas investment (about \\$570B). With capex at 30 to 75% of "
        f"revenue, cash flow no longer covers it: the group issued \\$121B of "
        f"bonds in 2025, four times its five-year average. Alphabet, long the "
        f"best-insulated on search cash flow, turned free-cash-flow negative in "
        f"Q2 2026 for the first time since its 2004 IPO and raised about \\$85B "
        f"of equity, its first share sale in two decades, on top of roughly "
        f"\\$100B of new debt.\n"
        f"- **The binding constraint keeps moving downstream, and each shortage "
        f"becomes the next layer's cost.** CoWoS packaging and HBM memory are "
        f"sold out through 2026, which shows up as Microsoft attributing about "
        f"\\$25B of its 2026 guidance to memory and component inflation. Power "
        f"is next: about {gw['capacity_gw'].sum():.0f} GW of named gigawatt "
        f"projects wait on grid connections that take 3 to 5 years.\n"
        f"- **The capex baton has passed from telecoms to hyperscalers.** "
        f"Global telecom capex (about \\$295B, the lowest since 2011) is now "
        f"about nine months of the major hyperscalers' combined spending (about "
        f"\\$380B in 2025), and the equipment vendors are "
        f"following the money: Nokia bought Infinera for AI data-center optics "
        f"while Arista quadrupled and Ericsson shrank.\n"
        f"- **Infrastructure captures the value today, but the advantage is "
        f"time-limited.** Demand is shifting from one-off training runs to "
        f"always-on inference, which invites competition from AMD, custom "
        f"hyperscaler silicon and inference startups and squeezes margins over "
        f"time, even as cheaper inference widens demand. NVIDIA's training moat "
        f"looks sturdier than its inference one, and the layer drifts toward "
        f"essential but lower-margin economics, closer to cloud. Fibre earns "
        f"operating leverage because the cost is fixed once the trenches are "
        f"dug, but AI capacity scales with usage since serving more tokens "
        f"means buying more GPUs, so the buildout delivers less of that "
        f"leverage than it appears. The financing "
        f"is also circular and concentrated: lab compute commitments underwrite "
        f"NeoCloud backlogs that collateralize over \\$20B of GPU-backed debt "
        f"from a single chip vendor, so a stumble at the lab layer would travel "
        f"back through credit.\n"
        f"- **The labs face real commoditization pressure.** 900M people use "
        f"ChatGPT weekly but only 5 to 6% pay, frontier scores have converged, "
        f"cheap Chinese open-weight models (DeepSeek, Qwen, Kimi) are closing "
        f"the gap at a fraction of the price, and switching costs at the API are "
        f"near zero. The labs that stay more than low-margin utilities will be "
        f"those that 1/ own distribution, 2/ compound proprietary data, or 3/ "
        f"move up into applications before application-layer companies move "
        f"down.\n"
        f"- **In software, cheap building changes which moats matter.** When "
        f"anyone can generate code, advantages built on engineering complexity "
        f"erode, while the structurally scarce ones hold: 1/ workflow "
        f"embedding, 2/ switching costs, 3/ proprietary data, and 4/ regulatory "
        f"position. Mid-market horizontal SaaS is the most exposed, while "
        f"vertical depth and data flywheels move up the defensibility stack. "
        f"The integrators (Accenture and peers) win the near-term deployment "
        f"work, though their labor-arbitrage model is the engineering-labor "
        f"scale that AI compresses, and the market began repricing that in "
        f"mid-2026 as Accenture, IBM and the Indian IT majors sold off on "
        f"AI-driven guidance cuts.\n"
        f"- **Bottom line.** Value accrues to whoever owns what AI cannot "
        f"manufacture: distribution, data, trust and customer lock-in, which is "
        f"why the whole stack is racing to integrate. The telecom build-out is "
        f"the closest precedent, but the incumbents here produce the "
        f"intelligence itself and already span the stack, so disruption from "
        f"outside is harder than the wave that commoditized carriers."
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
        "**Sources:** company filings (EDGAR XBRL); Anthropic run-rate via Epoch "
        "AI.  \n**Notes:** aggregate ROCE (combined operating income over combined "
        "capital employed), so larger players carry more weight; the 8-11% band "
        "is a common cost-of-capital reference. Returns concentrate in the "
        "asset-light layers and thin where capital sits without pricing power; "
        "foundry is the exception, carried by TSMC's scarcity pricing. The "
        "growth row (revenue growth, above each bar) separates young sub-band "
        "layers (NeoClouds, labs, compounding in triple digits) from mature "
        "ones (telecoms +1%, integrators +5%); growth only builds value where "
        "the return clears the band. Growth basis: 3-yr revenue CAGR 2022-2025, "
        "except NeoClouds (2-yr, CoreWeave) and labs (1-yr run-rate step, small "
        "base). Labs estimated; Digital Realty, TCS, Deutsche Telekom and "
        f"Nebius excluded for lack of comparable filings. Data as of {DATA_UPDATED}.")

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
        "- **Semiconductors are a \\$792B industry (2025) that has "
        "historically moved in 3 to 4 year cycles.** AI demand drove a 26% "
        "jump in 2025 and a forecast first one-trillion-dollar year in 2026; "
        "the open question is whether this is the steepest cycle yet or a "
        "structural break.\n"
        "- **The market splits into compute, memory and a stable base.** Logic "
        "(compute, where AI accelerators sit) and memory (storage, the home of "
        "HBM) are the AI-exposed segments and the most cyclical; analog, "
        "microcontrollers and discrete chips are the steadier base. The 2025-26 "
        "surge is concentrated in logic and memory. Cloud sits downstream as "
        "the buyer of this silicon and is covered in the Hyperscalers tab.\n"
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
        "approximate).  \n**Notes:** total-company revenue; NVIDIA, Broadcom and "
        "Micron fiscal years are offset from calendar. NVIDIA's data-center "
        "segment alone was about \\$115B in FY2025; SK Hynix is the HBM leader "
        "(about 57% share).")

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
        "**Sources:** TSMC, Samsung, Intel results (Samsung USD-converted KRW).  \n"
        "**Notes:** TSMC is pure-play; Samsung and Intel are IDMs shown at "
        "total-company scale (Samsung incl. memory, phones and displays; Intel "
        "incl. products), so they overstate the foundry business but show "
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
        "guidance \\$52-56B; CoWoS is about 7-9% of TSMC revenue, with OSAT "
        "overflow to ASE and Amkor.")

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
        "**Sources:** TrendForce.  \n**Notes:** CoWoS capacity has risen roughly 10x since "
        "2023 and remains sold out; it is about 7-9% of TSMC revenue.")

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
        "**Sources:** company filings (ODM figures are server/cloud-segment "
        "estimates, currency-converted).  \n**Notes:** listed OEMs (Dell ISG, "
        "Supermicro, HPE) plus the Taiwanese ODMs that carry most AI-server "
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
        "itself runs about 60% on the same box; ODMs (Foxconn about 3-4%) sit "
        f"lowest. Data as of {DATA_UPDATED}.")

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
        "- **Five companies are spending at a scale with few precedents:** "
        "about \\$379B of capex in FY2025 and roughly \\$775B guided for 2026, "
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
        "it: hyperscaler ROCE is still about three times the telecom level but "
        "ticked down in 2025 as capital employed surged. How far it compresses "
        "as the 2025-26 capex depreciates is the central question for the "
        "whole chain.")
    st.markdown("---")

    st.caption("**Notes:** all figures are total reported capex; no AI-share is "
               "applied.")
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
        "**Sources:** 10-Q and 10-K filings (SEC EDGAR XBRL).  \n**Notes:** quarterly cash "
        "purchases of PP&E; 10-Q figures are year-to-date, so quarters are "
        "derived by differencing and sum exactly to annual totals. Grouped by "
        "the calendar quarter each fiscal quarter ends (Microsoft and Oracle "
        f"offset). Data as of {DATA_UPDATED}.")

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
    st.caption(
        "**Sources:** 10-K filings (EDGAR XBRL), Janus Henderson, Wolf Street.  \n"
        f"**Notes:** FY2025: {ratio_line}. Oracle already outspends its operations "
        "and Amazon is close; the group issued \\$121B of bonds in 2025 (4x the "
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
        "**Sources:** company 10-K filings (EDGAR XBRL); 2026 capex from "
        "guidance, 2027 capex from consensus (Moody's, Goldman, BofA); NVIDIA "
        "FY2027 from Q1 run-rate; framing after BofA Global Research.  \n"
        "**Notes:** free cash flow (operating cash flow minus capex) per basket "
        "by fiscal year; solid is reported, dotted is 2026-27E. Hyperscaler FCF "
        "peaked at \\$246B (2024) and turns deeply negative by 2027 as capex "
        "nears \\$1T (Alphabet already negative in Q2 2026), while chipmaker FCF "
        "climbs toward \\$265B, most of it NVIDIA. Forward years are estimates; "
        f"fiscal years are not calendar-aligned across baskets. Data as of {DATA_UPDATED}.")

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
        "started depreciating, so the drag builds. Amazon and Oracle sit lower "
        f"on retail and broader software mix. Data as of {DATA_UPDATED}.")

    st.markdown("---")
    st.markdown("#### 2026 forward guidance")
    st.caption(
        "**Notes:** guidance is a broader basis (total capex incl. finance leases) "
        "than the cash-PP&E actuals above, so it is a separate series; ranges "
        "are company guidance, markers are midpoints.")
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
        "**Notes:** part of the jump is definitional (guidance includes finance "
        "leases), and Microsoft flagged about \\$25B of its 2026 step-up as "
        "memory and component inflation, so higher capex is not one-to-one more "
        "compute. Oracle guidance covers its fiscal year ending May 2026.")

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
        "**Sources:** company filings and press (Nebius bar estimated from "
        "disclosed Microsoft \\$17-19B and Meta \\$27B contracts).  \n**Notes:** "
        "CoreWeave's backlog (about \\$100B, up from \\$66.8B end-2025) dwarfs "
        "revenue and is concentrated (OpenAI added \\$11.2B); Crusoe and Lambda "
        "are private (revenue only). GPUs depreciate over 4-6 years while "
        "rental pricing can move faster, and over \\$20B of sector debt is "
        f"secured against them. Data as of {DATA_UPDATED}.")

# --------------------------------------------------------------------------- #
# 8 · AI Labs (demand)
# --------------------------------------------------------------------------- #
with tab_labs:
    st.markdown("### 8 · AI Labs")
    st.markdown(
        "- **Lab revenue is large and concentrating:** Anthropic and OpenAI "
        "run-rates total above \\$70B, and their multi-year compute "
        "commitments underwrite NeoCloud backlogs and hyperscaler buildouts.\n"
        "- **Inference is profitable, the business is not yet:** serving a token "
        "runs at roughly 40 to 50% gross margin (industry estimates), but "
        "training the next model still costs more than the labs earn, so the "
        "loss sits in the model roadmap rather than in unit economics.\n"
        "- **Usage is broad but shallow:** 900M people use ChatGPT weekly, yet "
        "only about 5 to 6% pay and under 10% of US adults use generative AI "
        "daily.\n"
        "- **Frontier capability has converged**, with benchmark leaders "
        "clustered in the low 90s on GPQA-Diamond and no clear network effects "
        "at the model layer.\n"
        "- **Cheap Chinese open-weight models are the sharp edge of "
        "commoditization:** DeepSeek, Alibaba's Qwen, Zhipu's GLM and Moonshot's "
        "Kimi now sit within single digits of the closed frontier on public "
        "benchmarks while pricing at one-third to one-tenth of it (DeepSeek "
        "around \\$0.27 per million input tokens). Because the weights are open "
        "they can be self-hosted, so they set a price and capability floor the "
        "Western labs have to clear and push API switching costs toward zero.\n"
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
            "**Sources:** Epoch AI.  \n**Notes:** annualized run-rates at various dates "
            "(Anthropic May-26, OpenAI Feb-26, xAI Q3-25, Mistral Jan-26); "
            "Anthropic overtook OpenAI, going from \\$1B to \\$47B in about 18 "
            "months.")
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
        f"OpenAI above \\$70B combined). Data as of {DATA_UPDATED}.")

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
        "benchmark scores converge in the 90s; lab revenue and multi-year "
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
        "\\$5.9B (FY2025) and \\$2.2B in Q1 FY2026**, about \\$11B cumulative, "
        "after which Accenture stopped breaking the metric out as advanced AI "
        "became embedded across its delivery.\n"
        "- **The bookings-minus-revenue gap is the tell:** Accenture booked "
        "about \\$11B of cumulative GenAI work while total revenue grew only "
        "about 5% a year, so the new work is mostly substituting for shrinking "
        "legacy engagements rather than adding to them.\n"
        "- **The delivery model is now the risk:** integrators are the "
        "near-term winners on deployment, yet the labor-arbitrage pyramid is "
        "the engineering-labor scale that AI compresses. The market began "
        "pricing this in mid-2026, with Accenture down about 18% on a guidance "
        "cut (consulting revenue up 1%, bookings down 2%), IBM down about 25% "
        "as AI hardware crowded out software and services budgets, and TCS and "
        "Infosys selling off on the shift from labor arbitrage to algorithm "
        "arbitrage.")

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
        "Capgemini calendar). Deloitte and IBM Consulting are comparable but "
        "private or embedded in a larger group.")

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
        "averaged over the years shown. Only Verizon and BT reach the top of "
        "the 6-8% band; the sector earned roughly its cost of capital across "
        "the 5G buildout. One-offs distort single years but averages wash most "
        "out.")
    st.caption(
        "**BT note.** ROCE is the return on the whole asset base; TSR is the "
        "return to the thin equity slice behind it. BT carries roughly £15-20B "
        "of net debt and a large pension scheme absorbing deficit-repair cash, "
        "so an 8% asset return leaves little for equity after interest and "
        "top-ups, and the market de-rated the shares as revenue stalled and "
        "Openreach capex ramped. Sound operating returns and destroyed equity "
        "coexist through leverage, pension drag and a falling multiple. Data as "
        f"of {DATA_UPDATED}.")

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
        "**Sources:** MTN Consulting (telecom); company filings (hyperscaler).  \n"
        "**Notes:** telecom is global industry capex, 2025-26 assumes the "
        "flat-to-declining path continues; hyperscaler is the Big-5, 2026 the "
        "guidance midpoint. Dotted segments are forecasts. The lines crossed in "
        "2025 and the gap roughly doubles in 2026.")

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
