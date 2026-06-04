"""
AI Infrastructure Capex Dashboard
Technical Intelligence proof-of-work — supply-side view of the AI compute market.

Structure: an Overview of the whole value chain, then one deep-dive tab per
value-chain step (upstream → downstream), a central Assumptions tab for all
model levers, and a Sources tab. Anchor data (Alphabet) is extracted and
cross-validated from 10-K filings; other figures are primary-sourced and flagged.
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
sys.path.append(str(ROOT / "model"))
from gpu_unit_economics import GpuEconomics, dscr_grid  # noqa: E402

st.set_page_config(
    page_title="AI Infrastructure Capex — Technical Intelligence",
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

YEARS = sorted(capex["fiscal_year"].unique())
YR = max(YEARS)  # latest reported fiscal year (2025)

BLUE, GREEN, YELLOW, RED, GREY = "#4285F4", "#34A853", "#FBBC04", "#EA4335", "#9aa0a6"


def render_layer_card(order: int):
    """Render the structured value-chain card(s) for a given layer."""
    for _, r in chain[chain["layer_order"] == order].iterrows():
        st.markdown(f"**{r['segment']}**")
        st.markdown(f"- **Key players:** {r['key_players']}")
        st.markdown(f"- **Role in stack:** {r['role_in_stack']}")
        st.markdown(f"- **Metric to track:** {r['key_metric']}")
        st.markdown(f"- **Bottleneck:** :red[{r['bottleneck']}]")


# --------------------------------------------------------------------------- #
# Sidebar (descriptive only — controls live in the Assumptions tab)
# --------------------------------------------------------------------------- #
st.sidebar.title("🛰️ AI Infra Capex")
st.sidebar.caption(
    "Supply-side intelligence across the AI compute value chain.\n\n"
    "**Overview** maps the whole chain; each following tab is a deep-dive on one "
    "step, upstream → downstream. Tune every model lever in the **🎛️ Assumptions** "
    "tab — the deep-dives respond live."
)

st.title("AI Infrastructure Capex — Supply-Side Intelligence")
st.caption(
    "How AI compute is financed, built, and priced across the value chain — "
    "from silicon and packaging to hyperscalers, NeoClouds, and the AI labs."
)

(tab_overview, tab_silicon, tab_foundry, tab_systems, tab_network,
 tab_dc, tab_hyper, tab_neo, tab_labs, tab_telco, tab_assume) = st.tabs([
    "📊 Overview",
    "⚙️ 1·Silicon & IP",
    "🏭 2·Foundry & Packaging",
    "🖥️ 3·Servers",
    "🔌 4·Networking",
    "⚡ 5·Data Centers",
    "☁️ 6·Hyperscalers",
    "🌩️ 7·NeoClouds",
    "🧠 8·AI Labs",
    "📡 9·Telecoms",
    "🎛️ Assumptions",
])

# --------------------------------------------------------------------------- #
# Assumptions — defined FIRST so deep-dive tabs can consume the values
# --------------------------------------------------------------------------- #
with tab_assume:
    st.markdown("### 🎛️ Model assumptions")
    st.caption(
        "Every estimate in the dashboard is driven by the levers below. They are "
        "deliberately exposed so a reviewer can stress-test conclusions rather "
        "than take them on faith. Defaults are illustrative analyst assumptions, "
        "not company-disclosed."
    )

    st.markdown("#### Capex basis")
    st.caption(
        "The dashboard reports **total reported capex**, unadjusted. Companies "
        "don't disclose an AI-vs-non-AI split, and inventing a per-company "
        "'AI share' would bake an unfounded assumption into the headline. The "
        "post-2023 surge is overwhelmingly AI / AI-adjacent infrastructure — we "
        "flag that rather than pretend to quantify it. No capex multiplier is "
        "applied anywhere in the charts or KPIs."
    )

    st.markdown("#### Unit economics")
    st.caption(
        "These three levers exist solely to turn capex dollars into an "
        "accelerator-unit estimate for the **Foundry & Packaging** supply-vs-"
        "demand comparison. They do **not** touch the reported capex series."
    )
    u1, u2, u3 = st.columns(3)
    gpu_price_k = u1.number_input(
        "Blended accelerator system cost ($k / unit)", 10, 80, 40, step=5,
        help="All-in cost per accelerator incl. networking, power provisioning, "
             "DC fit-out.")
    accel_share = u2.slider(
        "Accelerator share of capex (%)", 0, 100, 50,
        help="The single lever bridging capex $ to units: the fraction of total "
             "capex that buys accelerators + immediate fit-out (vs land, "
             "buildings, networking, non-AI). Used ONLY for the demand proxy.") / 100
    eff_per_wafer = u3.slider(
        "Effective accelerators per CoWoS wafer (net)", 4, 20, 7,
        help="Theoretical max ~16 (B200, CoWoS-L) to ~25-29 (Hopper); net "
             "effective is lower after yield, ramp and non-NVIDIA usage. Drives "
             "the supply ceiling.")
    st.info(
        "The capex series itself is shown as **total capex, unadjusted**. Only "
        "the Foundry & Packaging demand proxy uses the levers above."
    )

# Capex view (all companies, all years) — total capex, no AI adjustment
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

    st.markdown("##### Spend & demand (downstream)")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric(f"Big-4 total capex FY{YR}", f"${total_now:,.0f}B", f"{yoy:+.0f}% YoY")
    d2.metric("Big-4 2026E guidance", f"${guide26:,.0f}B",
              f"+{(guide26/total_now-1)*100:.0f}% vs FY25")
    d3.metric(f"Capex CAGR FY{first_yr}–{YR}", f"{cagr*100:.0f}%/yr",
              "AI-era acceleration")
    d4.metric("NeoCloud backlog (CoreWeave)", "$66.8B", "~$100B by Q1'26")

    st.markdown("##### Supply & constraint (upstream)")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("CoWoS capacity 2025", f"{cowos25:.0f}k wpm", "~2× vs 2024")
    s2.metric("CoWoS 2026E", f"{cowos26_lo:.0f}–{cowos26_hi:.0f}k wpm", "sold out")
    s3.metric("TSMC revenue 2025", f"${tsmc25:.0f}B", "~70% foundry share")
    s4.metric("Named GW-scale pipeline", f"{gw['capacity_gw'].sum():.0f} GW",
              f"{len(gw)} flagship projects")

    st.markdown("#### Hyperscaler capex by company ($B, absolute)")
    color_map = {"Alphabet": BLUE, "Amazon": YELLOW, "Meta": GREEN,
                 "Microsoft": RED}
    comp_order = ["Alphabet", "Amazon", "Meta", "Microsoft"]
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
        "Figures are **total reported capex — not an AI-only carve-out** "
        "(companies don't disclose the split; the post-2023 surge is "
        "overwhelmingly AI / AI-adjacent). Totals shown above each bar. Bars "
        "2018–2025 are reported cash PP&E; the hatched **2026E** bar is the "
        "**guidance midpoint** on a broader basis (total capex incl. finance "
        "leases) — shown for trajectory, not a like-for-like extension.")
    st.info(
        "**Reading the signal:** the FY24→FY25 step-change is the AI-capex "
        "inflection — the Big-4 jumped from "
        f"${total_prev:,.0f}B to ${total_now:,.0f}B in one year, with guidance "
        f"pointing to ~${totals[2026]:,.0f}B in 2026.")

    st.markdown("#### Value-chain map")
    st.caption("Each step, its key metric, and the bottleneck that gates it.")
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
    st.markdown("#### Revenue by key player ($B)")
    figsi = px.line(
        silicon_rev, x="fy", y="revenue_b", color="company", markers=True,
        labels={"fy": "Fiscal year", "revenue_b": "Revenue ($B)", "company": ""},
        color_discrete_map={"NVIDIA": GREEN, "AMD": RED, "Broadcom": BLUE,
                            "Micron": YELLOW})
    figsi.update_layout(height=400, hovermode="x unified", legend_title="")
    st.plotly_chart(figsi, width="stretch")
    st.caption(
        "Total company revenue. NVIDIA / Broadcom / Micron fiscal years are "
        "offset from calendar. NVIDIA's data-center segment alone was ~$115B in "
        "FY2025. Memory: HBM is the supply-constrained input (SK Hynix ~57% "
        "share, sold out through 2026); Micron shown as the US-listed memory "
        "proxy. Sources: company filings.")

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
    st.markdown("#### Revenue & capex by key player ($B)")
    st.caption(
        "Pure-play foundries. TSMC has ~70% market share; GlobalFoundries and UMC "
        "are specialty / mature-node players. Samsung Foundry (#2) and Intel "
        "Foundry are loss-making segments inside larger firms, omitted here.")
    fc1, fc2 = st.columns(2)
    fcolors = {"TSMC": BLUE, "GlobalFoundries": GREEN, "UMC": YELLOW}
    with fc1:
        figfr = px.line(foundry, x="year", y="revenue_b", color="company",
                        markers=True, color_discrete_map=fcolors,
                        labels={"year": "Year", "revenue_b": "Revenue ($B)",
                                "company": ""})
        figfr.update_layout(height=340, hovermode="x unified", legend_title="",
                            title="Revenue")
        st.plotly_chart(figfr, width="stretch")
    with fc2:
        figfc = px.line(foundry, x="year", y="capex_b", color="company",
                        markers=True, color_discrete_map=fcolors,
                        labels={"year": "Year", "capex_b": "Capex ($B)",
                                "company": ""})
        figfc.update_layout(height=340, hovermode="x unified", legend_title="",
                            title="Capex")
        st.plotly_chart(figfc, width="stretch")
    st.caption(
        "Sources: TSMC / GlobalFoundries / UMC results (SEC filings). TSMC 2026E "
        "capex guidance $52–56B; CoWoS ≈ 7–9% of TSMC revenue. OSAT packaging "
        "partners: ASE, Amkor.")

    cowos25 = float(cowos.loc[cowos.year == 2025, "cowos_kwpm"].iloc[0])
    cowos26 = float(cowos.loc[cowos.year == 2026, "cowos_kwpm"].iloc[0])
    cowos26_lo = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_low"].iloc[0])
    cowos26_hi = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_high"].iloc[0])

    st.markdown("---")
    k1, k2, k3 = st.columns(3)
    k1.metric("CoWoS capacity 2025", f"{cowos25:.0f}k wpm", "~2× vs 2024")
    k2.metric("CoWoS 2026E", f"{cowos26_lo:.0f}–{cowos26_hi:.0f}k wpm", "fully booked")
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

    st.markdown("#### Supply ceiling vs capex-implied demand")
    st.caption(
        "Convert CoWoS capacity into an accelerator-output ceiling (via the "
        "*effective accelerators per wafer* lever), then compare to the unit "
        "demand implied by hyperscaler capex. Demand applies the single "
        "*accelerator share of capex* lever to **total** capex — the one "
        "assumption in this bridge. **Illustrative**, order-of-magnitude.")
    ceil25 = cowos25 * 1000 * 12 * eff_per_wafer / 1e6
    ceil26 = cowos26 * 1000 * 12 * eff_per_wafer / 1e6
    cap25_total = latest["capex_usd_b"].sum()
    demand25 = cap25_total * accel_share / gpu_price_k  # millions of units

    b1, b2, b3 = st.columns(3)
    b1.metric("CoWoS accel. ceiling 2025", f"~{ceil25:.1f}M/yr")
    b2.metric("CoWoS ceiling 2026E", f"~{ceil26:.1f}M/yr",
              f"+{(ceil26/ceil25-1)*100:.0f}%")
    b3.metric("Big-4 FY25 implied demand", f"~{demand25:.1f}M",
              f"{demand25/ceil25*100:.0f}% of ceiling",
              help=f"Total FY25 capex ${cap25_total:,.0f}B × "
                   f"{accel_share*100:.0f}% accelerator share ÷ ${gpu_price_k}k/unit")

    comp = pd.DataFrame({
        "metric": ["CoWoS ceiling 2025", "Big-4 implied demand FY25",
                   "CoWoS ceiling 2026E"],
        "units_m": [ceil25, demand25, ceil26],
        "kind": ["Supply", "Demand", "Supply"],
    })
    figd = px.bar(comp, x="metric", y="units_m", color="kind",
                  color_discrete_map={"Supply": BLUE, "Demand": RED},
                  labels={"units_m": "Accelerators (M/yr)", "metric": ""})
    figd.update_layout(height=320, legend_title="")
    st.plotly_chart(figd, width="stretch")
    st.info(
        "**The strategic read:** four hyperscalers' capex alone implies unit "
        f"demand (~{demand25:.1f}M) on the order of the *entire* global packaging "
        f"ceiling (~{ceil25:.1f}M) — before NeoClouds, sovereign AI or enterprise. "
        "Two flags: (1) **CoWoS/HBM capacity, not budgets, governs who trains the "
        "largest models**; (2) Microsoft attributing ~\\$25B of its 2026 step-up "
        "to memory cost is the bottleneck **leaking into price**. Google's TPU + "
        "in-house packaging is a structural hedge."
    )

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
    st.markdown("#### Server revenue by vendor ($B)")
    figsy = px.line(
        systems, x="year", y="revenue_b", color="company", markers=True,
        color_discrete_map={"Dell ISG": BLUE, "Supermicro": GREEN,
                            "HPE Server": YELLOW},
        labels={"year": "Fiscal year", "revenue_b": "Revenue ($B)",
                "company": ""})
    figsy.update_layout(height=380, hovermode="x unified", legend_title="")
    st.plotly_chart(figsy, width="stretch")
    st.caption(
        "Fiscal years differ (Dell ~Jan, Supermicro ~Jun, HPE ~Oct). Dell ISG "
        "includes storage; Supermicro 2026 is the company revenue target "
        "(guidance); HPE server segment partly estimated. The largest AI-server "
        "*volume* flows through Taiwanese ODMs (Foxconn/Hon Hai, Quanta, Wistron) "
        "— lower-margin and under-disclosed. Sources: Dell/Supermicro/HPE filings.")

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
    st.markdown("#### Revenue by vendor ($B)")
    fign4 = px.line(
        networking, x="year", y="revenue_b", color="company", markers=True,
        color_discrete_map={"Arista": GREEN, "Ciena": BLUE, "Nokia NI": YELLOW},
        labels={"year": "Year", "revenue_b": "Revenue ($B)", "company": ""})
    fign4.update_layout(height=380, hovermode="x unified", legend_title="")
    st.plotly_chart(fign4, width="stretch")
    st.caption(
        "Segment-appropriate figures: Arista and Ciena are pure-plays (total "
        "revenue); Nokia is the **Network Infrastructure segment only** — "
        "excludes mobile networks (EUR→USD approx). Cisco's Networking segment "
        "(~$28–30B) is larger but sits inside a diversified firm (security, "
        "collaboration), so it is omitted to keep the comparison clean. Switch "
        "silicon (Broadcom) sits in Silicon & IP. Sources: company filings.")

# --------------------------------------------------------------------------- #
# 4 · Power & Data Centers
# --------------------------------------------------------------------------- #
with tab_dc:
    st.markdown("### 5 · Data Centers")
    st.caption(
        "Shells, cooling and — the real scarce input — electricity. Once "
        "packaging eases, grid interconnection and power become the next binding "
        "constraint. You can buy chips in months; you cannot buy a high-voltage "
        "substation in under 3–5 years."
    )
    render_layer_card(5)

    st.markdown("---")
    st.markdown("#### Data center vs office construction (US, $B/year)")
    st.caption(
        "A clean macro signal of the buildout: US data-center construction has "
        "overtaken office construction — unthinkable just a few years ago.")
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
        "US Census construction spending. Data-center spend ~$9B (2020) → ~$41B "
        "(2025, +344%); office ~$72B → ~$49B (lowest since 2015). On a **monthly "
        "run-rate** the two crossed in **Dec 2025** (DC ~$45B > office ~$44B). "
        "Mid-years interpolated between Census anchor points.")

    st.markdown("---")
    st.markdown("#### Gigawatt-scale buildout")
    gw_named = gw["capacity_gw"].sum()
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Named GW-scale pipeline", f"{gw_named:.0f} GW",
              f"{len(gw)} flagship projects")
    p2.metric("Global DC capacity", "103 → 200 GW", "by 2030 (~2×)")
    p3.metric("DC power demand", "+165%", "by 2030 (Goldman, vs '23)")
    p4.metric("HV substation lead time", "3–5 yrs", "the hard constraint")

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
        "Capacity figures are **announced / planned site totals at varying "
        "horizons** (e.g. Hyperion's 5 GW scales out to 2030) — not all online "
        "today. Treat as the build pipeline, not installed base.")

    st.warning(
        "**The grid is the new bottleneck.** High-voltage substation lead times "
        "run 3–5 years and 7 of 13 US grid regions are projected below safety "
        "margins by 2030; Goldman estimates ~$720B of grid spend needed through "
        "2030. Strategic reads for a TI analyst: (1) **power, not capital, gates "
        "the 2027+ buildout** — interconnection queues and turbine/transformer "
        "lead times set the schedule; (2) self-generation and behind-the-meter "
        "deals (gas, nuclear/SMR, on-site) become a competitive differentiator; "
        "(3) site selection shifts to where power is *available*, not where it is "
        "cheap. This is the constraint that bites **after** CoWoS/HBM ease.")

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

    st.caption("All figures are **total reported capex** — no AI-share applied.")
    g = view.sort_values(["company", "fiscal_year"]).copy()
    g["yoy_%"] = g.groupby("company")["capex_usd_b"].pct_change() * 100

    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Reported capex trajectory ($B)**")
        fig2 = px.line(
            g, x="fiscal_year", y="capex_usd_b", color="company", markers=True,
            labels={"fiscal_year": "Fiscal year", "capex_usd_b": "Capex ($B)"})
        fig2.update_layout(height=360, hovermode="x unified", legend_title="")
        st.plotly_chart(fig2, width="stretch")
    with colB:
        st.markdown("**YoY capex growth (%)** — the acceleration")
        fig3 = px.bar(
            g[g["fiscal_year"] >= 2021], x="fiscal_year", y="yoy_%",
            color="company", barmode="group",
            labels={"fiscal_year": "Fiscal year", "yoy_%": "YoY growth (%)"})
        fig3.update_layout(height=360, hovermode="x unified", legend_title="")
        st.plotly_chart(fig3, width="stretch")

    st.markdown("**Capex & YoY growth by company**")
    st.dataframe(
        g[["company", "fiscal_year", "capex_usd_b", "yoy_%", "source_type"]]
        .rename(columns={
            "company": "Company", "fiscal_year": "FY", "capex_usd_b": "Capex $B",
            "yoy_%": "YoY %", "source_type": "Source"}).style.format({
            "Capex $B": "{:.1f}", "YoY %": "{:+.0f}"}),
        width="stretch", hide_index=True)
    st.caption(
        "⚠️ Microsoft's FY ends June 30 (not calendar-aligned). Amazon capex "
        "includes fulfilment/logistics, not only AWS — material when comparing "
        "the totals across companies.")

    st.markdown("---")
    st.markdown("#### 2026 forward guidance")
    st.caption(
        "Guidance is reported on a **broader basis (total capex, incl. finance "
        "leases)** than the cash-PP&E actuals above — shown as a separate series, "
        "not a continuation. Ranges are company guidance; markers are midpoints.")
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
    st.metric("Big-4 2026E capex (sum of midpoints)",
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
    st.info(
        "**Signal:** part of the jump is definitional (guidance includes finance "
        "leases), but the underlying ramp is real — and Microsoft flagged ~\\$25B "
        "of its 2026 step-up as **memory/component cost inflation**, not capacity. "
        "Capex up ≠ compute up: the HBM bottleneck is showing up in price.")

# --------------------------------------------------------------------------- #
# 6 · NeoClouds
# --------------------------------------------------------------------------- #
with tab_neo:
    st.markdown("### 7 · NeoClouds")
    st.caption(
        "Specialised GPU-rental providers between silicon and AI labs. The "
        "strategic question isn't revenue — it's **financing durability**: much "
        "of the build is funded by GPU-backed debt against assets that depreciate "
        "faster than the loans amortise.")
    render_layer_card(7)
    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    c1.metric("CoreWeave backlog (end-2025)", "$66.8B", "~$100B by Q1'26")
    c2.metric("Nebius 2026E capex", "$20–25B", "raised on secured demand")
    c3.metric("Sector GPU-backed debt", ">$20B", "the key fragility")

    st.markdown("**Contracted backlog vs revenue ($B)** — visibility, not just scale")
    fign = go.Figure()
    fign.add_trace(go.Bar(x=neo["company"], y=neo["revenue_2025_b"],
                          name="2025 revenue", marker_color=GREEN))
    fign.add_trace(go.Bar(x=neo["company"], y=neo["backlog_b"],
                          name="Contracted backlog", marker_color=BLUE))
    fign.update_layout(barmode="group", height=320, legend_title="",
                       yaxis_title="$B", hovermode="x unified")
    st.plotly_chart(fign, width="stretch")
    st.caption(
        "CoreWeave's backlog dwarfs current revenue — multi-year visibility, but "
        "concentrated (the OpenAI deal alone added $11.2B). Blanks = not "
        "disclosed; private names (Crusoe, Lambda) report little.")

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
    st.warning(
        "**Sustainability watch:** NeoClouds carry >$20B in GPU-backed debt. GPUs "
        "depreciate on a ~4–6yr schedule while pricing can move faster — debt "
        "service against a depreciating asset base is the failure mode. Customer "
        "concentration (anchor tenants) is both the backlog's strength and its "
        "single-point risk.")

    st.markdown("---")
    st.markdown("### 🧮 GPU-backed-debt sustainability model")
    st.caption(
        "Per-accelerator unit economics: does rental cash flow cover the debt, "
        "and how far can pricing/utilisation fall before it doesn't? Logic lives "
        "in `model/gpu_unit_economics.py` (unit-tested separately).")

    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        gpu_cost = st.slider("All-in system cost ($k/GPU)", 20, 70, 40, 5) * 1000
        rate = st.slider("Rental rate ($/GPU-hr)", 1.0, 5.0, 2.5, 0.1)
    with ic2:
        util = st.slider("Utilisation (%)", 40, 100, 90, 5) / 100
        opex = st.slider("Variable opex ($/GPU-hr)", 0.2, 2.0, 0.9, 0.1)
    with ic3:
        ltv = st.slider("Loan-to-value (%)", 0, 100, 70, 5) / 100
        rate_int = st.slider("Debt interest rate (%)", 4, 18, 11, 1) / 100

    eco = GpuEconomics(gpu_cost_usd=gpu_cost, rental_rate_per_hr=rate,
                       utilization=util, opex_per_hr=opex, ltv=ltv,
                       interest_rate=rate_int)
    s = eco.summary()
    m1, m2, m3, m4 = st.columns(4)
    dscr = s["dscr"]
    m1.metric("DSCR", f"{dscr:.2f}x", "covers debt" if dscr >= 1 else "shortfall",
              delta_color="normal" if dscr >= 1 else "inverse")
    m2.metric("Annual cash margin / GPU", f"${s['cash_margin']:,.0f}",
              f"debt service ${s['annual_debt_service']:,.0f}")
    m3.metric("Break-even utilisation", f"{s['breakeven_utilization']*100:.0f}%",
              help="Utilisation at which DSCR = 1, holding price fixed")
    m4.metric("Rental-rate headroom", f"{s['rate_headroom_pct']:.0f}%",
              help="How far the hourly rate can fall before DSCR hits 1")

    if dscr < 1:
        st.error(f"**Underwater:** cash flow covers only {dscr:.2f}x of debt "
                 f"service — the build does not self-finance.")
    elif s["rate_headroom_pct"] < 20:
        st.warning(f"**Thin cushion:** only {s['rate_headroom_pct']:.0f}% "
                   f"rental-rate headroom before DSCR < 1.")
    else:
        st.success(f"**Self-financing:** {dscr:.2f}x coverage with "
                   f"{s['rate_headroom_pct']:.0f}% rate headroom.")

    st.markdown("**DSCR sensitivity — rental-rate erosion × utilisation**")
    haircuts, utils = [0.0, 0.15, 0.30, 0.45, 0.60], [0.60, 0.70, 0.80, 0.90, 1.00]
    sens = pd.DataFrame(
        dscr_grid(eco, haircuts, utils),
        index=[f"-{int(h*100)}% rate" for h in haircuts],
        columns=[f"{int(u*100)}% util" for u in utils])

    def dscr_color(v):
        if v < 1.0:
            return "background-color: #f4c7c3; color: #7f1d1d"
        if v < 1.25:
            return "background-color: #fde8b0; color: #7c4a03"
        return "background-color: #c6e7c6; color: #14532d"
    st.dataframe(sens.style.format("{:.2f}x").map(dscr_color), width="stretch")
    st.caption(
        "Red = DSCR < 1. The diagonal collapse shows durability hinges on holding "
        "**both** utilisation and pricing — a correlated shock (price war as new "
        "accelerators ship) moves you down *and* right at once.")

# --------------------------------------------------------------------------- #
# 8 · AI Labs (demand)
# --------------------------------------------------------------------------- #
with tab_labs:
    st.markdown("### 8 · AI Labs")
    st.caption(
        "Model developers consume the compute the whole chain exists to supply. "
        "Their revenue and compute commitments are the ultimate demand signal — "
        "and increasingly the financing counterparty behind NeoCloud backlogs.")
    render_layer_card(8)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Frontier-lab revenue (annualized run-rate, $B)")
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
            "Feb-26, xAI Q3-25, Mistral Jan-26). Anthropic has overtaken OpenAI; "
            "Anthropic went $1B→$47B in ~18 months. Source: Epoch AI revenue data.")
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
            "Representative best-published score per lab at major model releases "
            "(GPQA-Diamond; MMLU already saturated ~93%). Chinese labs "
            "(DeepSeek/Qwen) have closed most of the gap. Approximate — see "
            "notes/sources.md. Source: Epoch AI / leaderboards.")

    st.markdown("#### ChatGPT weekly active users (millions)")
    figw = px.area(chatgpt, x="date", y="wau_m",
                   labels={"date": "", "wau_m": "Weekly active users (M)"})
    figw.update_traces(line_color="#10A37F",
                       fillcolor="rgba(16,163,127,0.2)")
    figw.update_layout(height=280)
    st.plotly_chart(figw, width="stretch")
    st.caption(
        "OpenAI disclosures: 100M (Aug-23) → 900M (Feb-26) weekly active users — "
        "among the fastest consumer-technology adoption curves on record.")

    st.info(
        "**The strategic read:** revenue is enormous and concentrating (Anthropic "
        "+ OpenAI), yet frontier *capability* is converging — benchmarks cluster "
        "in the 90s. As raw capability commoditizes, competition shifts to "
        "**distribution, price and reliability**. For the supply side: lab revenue "
        "and multi-year compute commitments are the demand that ultimately "
        "underwrites the *entire* capex stack — and the binding constraints "
        "remain **capital and power**, not algorithms.")

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
# 9 · Telecoms (context)
# --------------------------------------------------------------------------- #
with tab_telco:
    st.markdown("### 9 · Telecoms")
    st.caption(
        "The previous era's infrastructure-capex leaders, shown for context. "
        "Telecom capex has stayed roughly flat (~$300B globally) while "
        "hyperscaler capex has surged past it.")

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
                         "series": "Big-4 hyperscaler capex"})
    rows.append({"year": 2026, "capex_b": guide_total,
                 "series": "Big-4 hyperscaler capex"})
    cmpdf = pd.DataFrame(rows)

    k1, k2, k3 = st.columns(3)
    k1.metric("Global telecom capex 2024", "~$295B", "lowest since 2011")
    k2.metric("Big-4 hyperscaler capex 2025", f"${hyp_year.loc[2025]:.0f}B",
              "overtook telecom")
    k3.metric("Big-4 2026E", f"${guide_total:.0f}B",
              f"~{guide_total/295:.1f}× global telecom")

    st.markdown("#### Capex — hyperscalers vs telecoms ($B)")
    figt = px.line(cmpdf, x="year", y="capex_b", color="series", markers=True,
                   color_discrete_map={"Global telecom capex": GREY,
                                       "Big-4 hyperscaler capex": BLUE},
                   labels={"year": "Year", "capex_b": "Capex ($B)", "series": ""})
    figt.update_layout(height=360, hovermode="x unified", legend_title="")
    st.plotly_chart(figt, width="stretch")
    st.caption(
        "Telecom = global industry capex (MTN Consulting); hyperscaler = Big-4 "
        "(Alphabet/Amazon/Meta/Microsoft), 2026 = guidance midpoint. AI "
        "infrastructure capex has overtaken the entire global telecom industry's.")

    st.markdown("#### Major telcos — revenue & capex (latest year, $B)")
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
