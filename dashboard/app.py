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


capex = load_capex()
chain = load_value_chain()
guidance = load_guidance()
neo = load_neoclouds()
cowos = load_cowos()
hbm = load_hbm()

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

(tab_overview, tab_silicon, tab_foundry, tab_systems, tab_power,
 tab_hyper, tab_neo, tab_labs, tab_assume, tab_sources) = st.tabs([
    "📊 Overview",
    "⚙️ 1·Silicon & IP",
    "🏭 2·Foundry & Packaging",
    "🔌 3·Systems & Networking",
    "⚡ 4·Power & Data Centers",
    "☁️ 5·Hyperscalers",
    "🌩️ 6·NeoClouds",
    "🧠 7·AI Labs",
    "🎛️ Assumptions",
    "📚 Sources & Method",
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

    st.markdown("#### AI-attributable share of capex")
    st.caption(
        "Headline capex is not all AI. Set the AI-attributable fraction per "
        "company to model AI-specific infrastructure spend."
    )
    a1, a2, a3, a4 = st.columns(4)
    ai_share = {
        "Alphabet": a1.slider("Alphabet", 0, 100, 70) / 100,
        "Microsoft": a2.slider("Microsoft", 0, 100, 75) / 100,
        "Amazon": a3.slider("Amazon", 0, 100, 45) / 100,
        "Meta": a4.slider("Meta", 0, 100, 80) / 100,
    }
    st.caption(
        "Amazon defaults lowest — its capex includes fulfilment/logistics, not "
        "only AWS. Meta highest — near-pure AI/datacentre build."
    )

    st.markdown("#### Unit economics")
    u1, u2 = st.columns(2)
    gpu_price_k = u1.number_input(
        "Blended accelerator system cost ($k / unit)", 10, 80, 40, step=5,
        help="All-in cost per accelerator incl. networking, power provisioning, "
             "DC fit-out. Translates AI capex into implied unit volume.")
    eff_per_wafer = u2.slider(
        "Effective accelerators per CoWoS wafer (net)", 4, 20, 7,
        help="Theoretical max ~16 (B200, CoWoS-L) to ~25-29 (Hopper); net "
             "effective is lower after yield, ramp and non-NVIDIA usage. Drives "
             "the Foundry & Packaging supply ceiling.")
    st.info(
        "These levers feed the **Hyperscalers** (AI-attributable capex, implied "
        "units) and **Foundry & Packaging** (supply ceiling vs demand) tabs."
    )

# Derived capex view (all companies, all years — no filtering)
view = capex.copy()
view["ai_share"] = view["company"].map(ai_share).fillna(0.6)
view["ai_capex_usd_b"] = view["capex_usd_b"] * view["ai_share"]
view["implied_units_k"] = view["ai_capex_usd_b"] * 1000 / gpu_price_k

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
    ai_now = latest["ai_capex_usd_b"].sum()
    yoy = (total_now / total_prev - 1) * 100 if total_prev else 0
    guide26 = guidance["capex_mid_b"].sum()
    cowos25 = float(cowos.loc[cowos.year == 2025, "cowos_kwpm"].iloc[0])
    cowos26_lo = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_low"].iloc[0])
    cowos26_hi = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_high"].iloc[0])
    hbm25 = float(hbm.loc[hbm.year == 2025, "hbm_revenue_b"].iloc[0])

    st.markdown("##### Spend & demand (downstream)")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric(f"Big-4 capex FY{YR}", f"${total_now:,.0f}B", f"{yoy:+.0f}% YoY")
    d2.metric("Big-4 2026E guidance", f"${guide26:,.0f}B",
              f"+{(guide26/total_now-1)*100:.0f}% vs FY25")
    d3.metric(f"AI-attributable FY{YR}", f"${ai_now:,.0f}B",
              f"{ai_now/total_now*100:.0f}% of capex")
    d4.metric("NeoCloud backlog (CoreWeave)", "$66.8B", "~$100B by Q1'26")

    st.markdown("##### Supply & constraint (upstream)")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("CoWoS capacity 2025", f"{cowos25:.0f}k wpm", "~2× vs 2024")
    s2.metric("CoWoS 2026E", f"{cowos26_lo:.0f}–{cowos26_hi:.0f}k wpm", "sold out")
    s3.metric("HBM TAM 2025", f"${hbm25:.0f}B", "sold out thru 2026")
    s4.metric("HBM TAM 2028E", "$100B", "~40% CAGR")

    st.markdown("#### Hyperscaler capex by company ($B, absolute)")
    figo = px.bar(
        view.sort_values("fiscal_year"),
        x="fiscal_year", y="capex_usd_b", color="company", barmode="stack",
        labels={"fiscal_year": "Fiscal year", "capex_usd_b": "Capex ($B)",
                "company": ""},
        color_discrete_map={"Alphabet": BLUE, "Amazon": YELLOW,
                            "Meta": GREEN, "Microsoft": RED},
    )
    figo.update_layout(height=420, hovermode="x unified", legend_title="")
    st.plotly_chart(figo, width="stretch")
    st.info(
        "**Reading the signal:** the FY24→FY25 step-change is the AI-capex "
        "inflection — the Big-4 jumped from "
        f"${total_prev:,.0f}B to ${total_now:,.0f}B in one year."
    )

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
    st.markdown("### 1 · Silicon & IP — accelerators and memory")
    st.caption(
        "The compute engines (GPUs / TPUs / ASICs) and the high-bandwidth memory "
        "stacked beside them. HBM is the supply-constrained input that gates "
        "every advanced accelerator."
    )
    render_layer_card(1)

    st.markdown("---")
    st.markdown("#### High-bandwidth memory (HBM) — the gating input")
    h1, h2 = st.columns([3, 2])
    with h1:
        figh = px.bar(hbm, x="year", y="hbm_revenue_b",
                      labels={"hbm_revenue_b": "$B TAM", "year": "Year"})
        figh.update_traces(marker_color=GREEN)
        figh.update_layout(height=320, showlegend=False,
                           title="HBM market TAM ($B)")
        st.plotly_chart(figh, width="stretch")
    with h2:
        shares = {"SK Hynix": 57, "Micron": 21, "Samsung": 22}
        figp = go.Figure(go.Pie(
            labels=list(shares), values=list(shares.values()), hole=0.5,
            marker_colors=[BLUE, YELLOW, RED]))
        figp.update_layout(height=320, title="HBM share (Q3'25)",
                           margin=dict(t=40, b=10))
        st.plotly_chart(figp, width="stretch")
    st.info(
        "**Signal:** HBM TAM ~$35B (2025) → ~$100B (2028E), and suppliers are "
        "**sold out through 2026**. SK Hynix leads (~57%), Micron has overtaken "
        "Samsung. HBM bit-supply — not logic — is the first hard ceiling on "
        "accelerator output. The HBM4 transition (2026+) is the next inflection."
    )

# --------------------------------------------------------------------------- #
# 2 · Foundry & Packaging  (TSMC CoWoS + the supply ceiling)
# --------------------------------------------------------------------------- #
with tab_foundry:
    st.markdown("### 2 · Foundry & Packaging — TSMC CoWoS")
    st.caption(
        "Advanced packaging (CoWoS) co-locates logic and HBM. It is the single "
        "most-cited physical bottleneck in the AI supply chain — and where "
        "hyperscaler demand meets a hard ceiling."
    )
    render_layer_card(2)

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
        "Convert CoWoS capacity into an accelerator-output ceiling (using the "
        "*effective accelerators per wafer* lever in Assumptions), then compare "
        "to the unit demand implied by hyperscaler AI capex. **Illustrative** — "
        "net of yield, ramp and shared usage; order-of-magnitude, not a forecast."
    )
    ceil25 = cowos25 * 1000 * 12 * eff_per_wafer / 1e6
    ceil26 = cowos26 * 1000 * 12 * eff_per_wafer / 1e6
    demand25 = latest["implied_units_k"].sum() / 1000  # millions

    b1, b2, b3 = st.columns(3)
    b1.metric("CoWoS accel. ceiling 2025", f"~{ceil25:.1f}M/yr")
    b2.metric("CoWoS ceiling 2026E", f"~{ceil26:.1f}M/yr",
              f"+{(ceil26/ceil25-1)*100:.0f}%")
    b3.metric("Big-4 FY25 implied demand", f"~{demand25:.1f}M",
              f"{demand25/ceil25*100:.0f}% of ceiling")

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
        "**The strategic read:** four hyperscalers' AI capex alone implies unit "
        f"demand (~{demand25:.1f}M) on the order of the *entire* global packaging "
        f"ceiling (~{ceil25:.1f}M) — before NeoClouds, sovereign AI or enterprise. "
        "Two flags: (1) **CoWoS/HBM capacity, not budgets, governs who trains the "
        "largest models**; (2) Microsoft attributing ~\\$25B of its 2026 step-up "
        "to memory cost is the bottleneck **leaking into price**. Google's TPU + "
        "in-house packaging is a structural hedge."
    )

# --------------------------------------------------------------------------- #
# 3 · Systems & Networking
# --------------------------------------------------------------------------- #
with tab_systems:
    st.markdown("### 3 · Systems & Networking")
    st.caption(
        "Racks, servers and the high-speed fabric (NVLink, Ethernet/InfiniBand, "
        "optics) that turn accelerators into clusters. Increasingly the "
        "scale-up/scale-out fabric — not the chip — sets training efficiency."
    )
    render_layer_card(3)
    st.warning(
        "**Data to add:** rack/system shipments, optical-transceiver volumes, and "
        "switch-ASIC supply (Broadcom Tomahawk/Jericho). Networking is an "
        "under-tracked second-order bottleneck as cluster sizes cross 100k+ GPUs."
    )

# --------------------------------------------------------------------------- #
# 4 · Power & Data Centers
# --------------------------------------------------------------------------- #
with tab_power:
    st.markdown("### 4 · Power & Data Centers")
    st.caption(
        "Shells, cooling and — the real scarce input — electricity. Once "
        "packaging eases, grid interconnection and power availability become the "
        "next binding constraint on gigawatt-scale clusters."
    )
    render_layer_card(4)

    pw = neo.dropna(subset=["power_contracted_gw"])
    if not pw.empty:
        st.markdown("---")
        st.markdown("#### Announced power — NeoCloud sample (GW)")
        c1, c2 = st.columns([2, 3])
        c1.metric("Sample contracted/active power",
                  f"{pw['power_contracted_gw'].sum():.1f} GW",
                  f"{len(pw)} NeoCloud providers")
        figpw = px.bar(pw.sort_values("power_contracted_gw"),
                       x="power_contracted_gw", y="company", orientation="h",
                       labels={"power_contracted_gw": "GW", "company": ""})
        figpw.update_traces(marker_color=YELLOW)
        figpw.update_layout(height=240, margin=dict(t=10))
        c2.plotly_chart(figpw, width="stretch")
    st.warning(
        "**Data to add (the next layer):** gigawatt-scale project pipeline across "
        "hyperscalers, $/MW build costs, PUE, and grid-interconnection queues. "
        "Power is the constraint that bites *after* CoWoS/HBM."
    )

# --------------------------------------------------------------------------- #
# 5 · Hyperscalers — capex deep-dive
# --------------------------------------------------------------------------- #
with tab_hyper:
    st.markdown("### 5 · Hyperscalers — capex deep-dive")
    st.caption(
        "Google Cloud, Azure, AWS, Oracle. The demand engine of the value chain: "
        "their capex is the pull on every upstream layer."
    )
    render_layer_card(5)
    st.markdown("---")

    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Reported capex trajectory ($B)**")
        fig2 = px.line(
            view.sort_values("fiscal_year"),
            x="fiscal_year", y="capex_usd_b", color="company", markers=True,
            labels={"fiscal_year": "Fiscal year", "capex_usd_b": "Capex ($B)"})
        fig2.update_layout(height=360, hovermode="x unified", legend_title="")
        st.plotly_chart(fig2, width="stretch")
    with colB:
        st.markdown("**AI-attributable capex ($B)** — after share assumptions")
        fig3 = px.bar(
            view.sort_values("fiscal_year"),
            x="fiscal_year", y="ai_capex_usd_b", color="company", barmode="group",
            labels={"fiscal_year": "Fiscal year", "ai_capex_usd_b": "AI capex ($B)"})
        fig3.update_layout(height=360, hovermode="x unified", legend_title="")
        st.plotly_chart(fig3, width="stretch")

    st.markdown("**Capex intensity & YoY growth**")
    g = view.sort_values(["company", "fiscal_year"]).copy()
    g["yoy_%"] = g.groupby("company")["capex_usd_b"].pct_change() * 100
    st.dataframe(
        g[["company", "fiscal_year", "capex_usd_b", "ai_share", "ai_capex_usd_b",
           "implied_units_k", "yoy_%", "source_type"]].rename(columns={
            "company": "Company", "fiscal_year": "FY", "capex_usd_b": "Capex $B",
            "ai_share": "AI share", "ai_capex_usd_b": "AI capex $B",
            "implied_units_k": "Units (k)", "yoy_%": "YoY %",
            "source_type": "Source",
        }).style.format({
            "Capex $B": "{:.1f}", "AI share": "{:.0%}", "AI capex $B": "{:.1f}",
            "Units (k)": "{:.0f}", "YoY %": "{:+.0f}"}),
        width="stretch", hide_index=True)
    st.caption(
        "⚠️ Microsoft's FY ends June 30 (not calendar-aligned). Amazon capex "
        "includes fulfilment/logistics, not only AWS — hence its lower AI-share.")

    st.markdown("---")
    st.markdown("#### 2026 forward guidance — the parabolic year")
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
    st.markdown("### 6 · NeoClouds — the GPU-as-a-service layer")
    st.caption(
        "Specialised GPU-rental providers between silicon and AI labs. The "
        "strategic question isn't revenue — it's **financing durability**: much "
        "of the build is funded by GPU-backed debt against assets that depreciate "
        "faster than the loans amortise.")
    render_layer_card(6)
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
# 7 · AI Labs (demand)
# --------------------------------------------------------------------------- #
with tab_labs:
    st.markdown("### 7 · AI Labs — the demand source")
    st.caption(
        "Model developers consume the compute the whole chain exists to supply. "
        "Their compute commitments and burn rates are the ultimate demand signal "
        "— and increasingly the financing counterparty behind NeoCloud backlogs.")
    render_layer_card(7)

    st.markdown("---")
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
    st.warning(
        "**Data to add:** per-lab compute commitments, estimated training-run "
        "spend and burn rate. Labs rarely disclose — triangulate from NeoCloud "
        "backlog deals, hyperscaler partner commentary and funding rounds. The "
        "binding constraints here are **capital and power**, not algorithms.")

# --------------------------------------------------------------------------- #
# Sources & method
# --------------------------------------------------------------------------- #
with tab_sources:
    st.markdown("### Sources & methodology")
    st.markdown(
        "**Data integrity model.** Every figure is primary-sourced and carries a "
        "`source_type`:\n"
        "- `10-K (extracted)` — parsed from 10-K PDFs in `data/raw/alphabet` and "
        "cross-validated across overlapping filing years (Alphabet).\n"
        "- `10-K (EDGAR XBRL)` — pulled from SEC EDGAR's XBRL API using the "
        "*as-originally-reported* annual value, citing each accession (MSFT / "
        "AMZN / META).\n"
        "- Upstream (CoWoS / HBM), guidance and NeoCloud figures are sourced to "
        "filings / earnings / industry research — see `notes/sources.md` for URLs.")
    st.markdown("**Full capex provenance — every datapoint and its source:**")
    st.dataframe(
        capex[["company", "fiscal_year", "capex_usd_m", "source_type",
               "source_doc", "source_page"]].rename(columns={
            "company": "Company", "fiscal_year": "FY", "capex_usd_m": "Capex $M",
            "source_type": "Source type", "source_doc": "Source doc / accession",
            "source_page": "Page"}),
        width="stretch", hide_index=True, height=320)
    st.markdown(
        "**Assumptions** live in the 🎛️ Assumptions tab (AI-attributable share, "
        "blended unit cost, accelerators-per-wafer). They are exposed as controls "
        "so a reviewer can stress-test the conclusions rather than take them on "
        "faith.")
    st.caption(
        "Hyperscaler capex is fully primary-sourced. Next to harden: gigawatt-"
        "scale power pipeline, systems/networking volumes, and per-lab compute "
        "commitments.")
