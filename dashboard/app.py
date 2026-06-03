"""
AI Infrastructure Capex Dashboard
Technical Intelligence proof-of-work — supply-side view of the AI compute market.

Anchor data (Alphabet) is extracted and cross-validated from 10-K filings in
data/raw/alphabet. Other figures are flagged as public placeholders to be
verified or replaced by dropping the relevant reports into data/raw.
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

COMPANIES = sorted(capex["company"].unique())
YEARS = sorted(capex["fiscal_year"].unique())

# --------------------------------------------------------------------------- #
# Sidebar — controls & assumptions
# --------------------------------------------------------------------------- #
st.sidebar.title("🛰️ Controls")
st.sidebar.caption(
    "A supply-side intelligence view of AI infrastructure spend across the "
    "compute value chain."
)

selected = st.sidebar.multiselect(
    "Companies", COMPANIES, default=COMPANIES
)
yr_min, yr_max = st.sidebar.select_slider(
    "Fiscal-year range",
    options=YEARS,
    value=(min(YEARS), max(YEARS)),
)

st.sidebar.markdown("---")
st.sidebar.subheader("AI-attributable share")
st.sidebar.caption(
    "Headline capex is not all AI. Estimate the AI-attributable fraction per "
    "company to model AI-specific infrastructure spend. Defaults are "
    "illustrative analyst assumptions — adjust and watch the model respond."
)
ai_share = {
    "Alphabet": st.sidebar.slider("Alphabet AI share %", 0, 100, 70) / 100,
    "Microsoft": st.sidebar.slider("Microsoft AI share %", 0, 100, 75) / 100,
    "Amazon": st.sidebar.slider("Amazon AI share %", 0, 100, 45) / 100,
    "Meta": st.sidebar.slider("Meta AI share %", 0, 100, 80) / 100,
}

st.sidebar.markdown("---")
st.sidebar.subheader("Unit economics")
gpu_price_k = st.sidebar.number_input(
    "Blended accelerator system cost ($k / unit)", 10, 80, 40, step=5,
    help="All-in cost per accelerator incl. networking, power provisioning, "
         "DC fit-out. Used to translate AI capex into implied unit volume.",
)

view = capex[
    (capex["company"].isin(selected))
    & (capex["fiscal_year"].between(yr_min, yr_max))
].copy()
view["ai_share"] = view["company"].map(ai_share).fillna(0.6)
view["ai_capex_usd_b"] = view["capex_usd_b"] * view["ai_share"]
view["implied_units_k"] = view["ai_capex_usd_b"] * 1000 / gpu_price_k

# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.title("AI Infrastructure Capex — Supply-Side Intelligence")
st.caption(
    "Tracking how compute is financed, built, and priced across the AI value "
    "chain. Anchor data extracted & cross-validated from Alphabet 10-K filings."
)

(tab_overview, tab_capex, tab_neo, tab_bottleneck,
 tab_chain, tab_sources) = st.tabs(
    ["📊 Overview", "🏗️ Hyperscaler Deep-Dive", "🌩️ NeoClouds",
     "⛓️ Upstream Bottleneck", "🔗 Value Chain", "📚 Sources & Method"]
)

# --------------------------------------------------------------------------- #
# Overview
# --------------------------------------------------------------------------- #
with tab_overview:
    latest = view[view["fiscal_year"] == yr_max]
    prev = view[view["fiscal_year"] == (yr_max - 1)]

    total_now = latest["capex_usd_b"].sum()
    total_prev = prev["capex_usd_b"].sum()
    ai_now = latest["ai_capex_usd_b"].sum()
    yoy = (total_now / total_prev - 1) * 100 if total_prev else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"FY{yr_max} total capex", f"${total_now:,.0f}B", f"{yoy:+.0f}% YoY")
    c2.metric(f"FY{yr_max} AI-attributable", f"${ai_now:,.0f}B",
              f"{ai_now/total_now*100:.0f}% of capex" if total_now else "—")
    c3.metric("Companies tracked", f"{view['company'].nunique()}")
    c4.metric("Implied accelerator units",
              f"{latest['implied_units_k'].sum():,.0f}k",
              help="AI capex / blended unit cost")

    st.markdown("#### Total reported capex by company")
    fig = px.area(
        view.sort_values("fiscal_year"),
        x="fiscal_year", y="capex_usd_b", color="company",
        labels={"fiscal_year": "Fiscal year", "capex_usd_b": "Capex ($B)"},
    )
    fig.update_layout(height=420, hovermode="x unified", legend_title="")
    st.plotly_chart(fig, width="stretch")

    st.info(
        "**Reading the signal:** the FY24→FY25 step-change is the AI-capex "
        "inflection. Alphabet alone moved from \\$52.5B to \\$91.4B (+74%) — "
        "a single datapoint that reframes the supply-side narrative."
    )

# --------------------------------------------------------------------------- #
# Hyperscaler deep-dive
# --------------------------------------------------------------------------- #
with tab_capex:
    st.markdown("### Hyperscaler capex deep-dive")

    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Reported capex trajectory ($B)**")
        fig2 = px.line(
            view.sort_values("fiscal_year"),
            x="fiscal_year", y="capex_usd_b", color="company", markers=True,
            labels={"fiscal_year": "Fiscal year", "capex_usd_b": "Capex ($B)"},
        )
        fig2.update_layout(height=380, hovermode="x unified", legend_title="")
        st.plotly_chart(fig2, width="stretch")
    with colB:
        st.markdown("**AI-attributable capex ($B)** — after applying share assumptions")
        fig3 = px.bar(
            view.sort_values("fiscal_year"),
            x="fiscal_year", y="ai_capex_usd_b", color="company", barmode="group",
            labels={"fiscal_year": "Fiscal year", "ai_capex_usd_b": "AI capex ($B)"},
        )
        fig3.update_layout(height=380, hovermode="x unified", legend_title="")
        st.plotly_chart(fig3, width="stretch")

    st.markdown("**Capex intensity & YoY growth**")
    g = view.sort_values(["company", "fiscal_year"]).copy()
    g["yoy_%"] = g.groupby("company")["capex_usd_b"].pct_change() * 100
    show = g[["company", "fiscal_year", "capex_usd_b", "ai_share",
              "ai_capex_usd_b", "implied_units_k", "yoy_%", "source_type"]]
    st.dataframe(
        show.rename(columns={
            "company": "Company", "fiscal_year": "FY",
            "capex_usd_b": "Capex $B", "ai_share": "AI share",
            "ai_capex_usd_b": "AI capex $B", "implied_units_k": "Units (k)",
            "yoy_%": "YoY %", "source_type": "Source",
        }).style.format({
            "Capex $B": "{:.1f}", "AI share": "{:.0%}",
            "AI capex $B": "{:.1f}", "Units (k)": "{:.0f}", "YoY %": "{:+.0f}",
        }),
        width="stretch", hide_index=True,
    )
    st.caption(
        "⚠️ Fiscal-year caveat: Microsoft's FY ends June 30, so its years are "
        "not calendar-aligned with the others. Amazon capex includes "
        "fulfilment/logistics, not only AWS — hence its lower AI-share default."
    )

    st.markdown("---")
    st.markdown("### 2026 forward guidance — the parabolic year")
    st.caption(
        "Forward guidance is reported on a **broader basis (total capex, incl. "
        "finance leases)** than the cash-PP&E actuals above, so it is shown as a "
        "separate series — not a continuation of the historical line. Ranges are "
        "company guidance; point markers are midpoints."
    )
    actual25 = (capex[capex["fiscal_year"] == 2025]
                .set_index("company")["capex_usd_b"])
    gtbl = guidance.copy()
    gtbl["fy2025_actual_b"] = gtbl["company"].map(actual25)
    gtbl["implied_growth_%"] = (
        gtbl["capex_mid_b"] / gtbl["fy2025_actual_b"] - 1) * 100

    figg = go.Figure()
    figg.add_trace(go.Bar(
        x=gtbl["company"], y=gtbl["fy2025_actual_b"],
        name="FY2025 actual (cash PP&E)", marker_color="#9aa0a6",
    ))
    figg.add_trace(go.Bar(
        x=gtbl["company"], y=gtbl["capex_mid_b"],
        name="2026E guidance (midpoint, total capex)", marker_color="#4285F4",
        error_y=dict(
            type="data", symmetric=False,
            array=gtbl["capex_high_b"] - gtbl["capex_mid_b"],
            arrayminus=gtbl["capex_mid_b"] - gtbl["capex_low_b"],
        ),
    ))
    figg.update_layout(
        barmode="group", height=380, legend_title="",
        yaxis_title="Capex ($B)", hovermode="x unified",
    )
    st.plotly_chart(figg, width="stretch")

    total26 = gtbl["capex_mid_b"].sum()
    st.metric(
        "Big-4 2026E capex (sum of midpoints)", f"${total26:,.0f}B",
        f"+{(total26/actual25.sum()-1)*100:.0f}% vs FY2025 actual",
    )
    st.dataframe(
        gtbl[["company", "fy2025_actual_b", "capex_low_b", "capex_mid_b",
              "capex_high_b", "implied_growth_%", "definition", "source"]]
        .rename(columns={
            "company": "Company", "fy2025_actual_b": "FY25 actual $B",
            "capex_low_b": "26E low", "capex_mid_b": "26E mid",
            "capex_high_b": "26E high", "implied_growth_%": "Growth %",
            "definition": "Definition", "source": "Source",
        }).style.format({
            "FY25 actual $B": "{:.1f}", "26E low": "{:.0f}", "26E mid": "{:.0f}",
            "26E high": "{:.0f}", "Growth %": "{:+.0f}",
        }),
        width="stretch", hide_index=True,
    )
    st.info(
        "**Signal:** part of the headline jump is definitional (guidance "
        "includes finance leases), but the underlying ramp is real — and "
        "Microsoft flagged that ~\\$25B of its 2026 step-up is **memory/component "
        "cost inflation**, not added capacity. A capex number going up is not the "
        "same as compute going up: the HBM bottleneck is now showing up in price."
    )

# --------------------------------------------------------------------------- #
# NeoClouds
# --------------------------------------------------------------------------- #
with tab_neo:
    st.markdown("### NeoClouds — the GPU-as-a-service layer")
    st.caption(
        "Specialised GPU-rental providers sitting between silicon and AI labs. "
        "The strategic question isn't revenue — it's **financing durability**: "
        "much of the build is funded by GPU-backed debt against assets that "
        "depreciate faster than the loans amortise."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("CoreWeave backlog (end-2025)", "$66.8B", "~$100B by Q1'26")
    c2.metric("Nebius 2026E capex", "$20–25B", "raised on secured demand")
    c3.metric("Sector GPU-backed debt", ">$20B", "the key fragility")

    st.markdown("**Contracted backlog vs revenue ($B)** — visibility, not just scale")
    plot = neo.copy()
    fign = go.Figure()
    fign.add_trace(go.Bar(
        x=plot["company"], y=plot["revenue_2025_b"],
        name="2025 revenue", marker_color="#34A853",
    ))
    fign.add_trace(go.Bar(
        x=plot["company"], y=plot["backlog_b"],
        name="Contracted backlog", marker_color="#4285F4",
    ))
    fign.update_layout(barmode="group", height=340, legend_title="",
                       yaxis_title="$B", hovermode="x unified")
    st.plotly_chart(fign, width="stretch")
    st.caption(
        "CoreWeave's backlog dwarfs current revenue — multi-year contracted "
        "visibility, but concentrated (the OpenAI deal alone added $11.2B). "
        "Blanks = not disclosed; private names (Crusoe, Lambda) report little."
    )

    st.markdown("**Provider snapshot**")
    st.dataframe(
        neo[[
            "company", "ownership", "revenue_2025_b", "revenue_2026e_b",
            "backlog_b", "capex_2026e_b", "power_contracted_gw", "valuation_b",
            "key_financing_signal",
        ]].rename(columns={
            "company": "Company", "ownership": "Ownership",
            "revenue_2025_b": "Rev 2025 $B", "revenue_2026e_b": "Rev 2026E $B",
            "backlog_b": "Backlog $B", "capex_2026e_b": "Capex 2026E $B",
            "power_contracted_gw": "Power contracted GW",
            "valuation_b": "Valuation $B", "key_financing_signal": "Financing signal",
        }),
        width="stretch", hide_index=True,
    )
    st.warning(
        "**Sustainability watch (the JD's \"assess sustainability of competitor "
        "strategies\"):** NeoClouds carry >$20B in GPU-backed debt. GPUs "
        "depreciate on a ~4–6yr schedule while demand/pricing can move faster — "
        "if utilisation or rental rates fall, debt service against a depreciating "
        "asset base is the failure mode to monitor. Customer concentration "
        "(hyperscaler/lab anchor tenants) is both the backlog's strength and its "
        "single-point risk."
    )

    st.markdown("---")
    st.markdown("### 🧮 GPU-backed-debt sustainability model")
    st.caption(
        "Per-accelerator unit economics. The question a TI analyst asks: does "
        "rental cash flow cover the debt — and how much can pricing or "
        "utilisation fall before it doesn't? All assumptions are editable; the "
        "model recomputes live. Logic lives in `model/gpu_unit_economics.py` "
        "(unit-tested separately)."
    )

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

    eco = GpuEconomics(
        gpu_cost_usd=gpu_cost, rental_rate_per_hr=rate, utilization=util,
        opex_per_hr=opex, ltv=ltv, interest_rate=rate_int,
    )
    s = eco.summary()

    m1, m2, m3, m4 = st.columns(4)
    dscr = s["dscr"]
    m1.metric("DSCR", f"{dscr:.2f}x",
              "covers debt" if dscr >= 1 else "shortfall",
              delta_color="normal" if dscr >= 1 else "inverse")
    m2.metric("Annual cash margin / GPU", f"${s['cash_margin']:,.0f}",
              f"debt service ${s['annual_debt_service']:,.0f}")
    m3.metric("Break-even utilisation", f"{s['breakeven_utilization']*100:.0f}%",
              help="Utilisation at which DSCR = 1, holding price fixed")
    m4.metric("Rental-rate headroom", f"{s['rate_headroom_pct']:.0f}%",
              help="How far the hourly rate can fall before DSCR hits 1")

    if dscr < 1:
        st.error(
            f"**Underwater:** at these assumptions cash flow covers only "
            f"{dscr:.2f}x of debt service — the build does not self-finance."
        )
    elif s["rate_headroom_pct"] < 20:
        st.warning(
            f"**Thin cushion:** only {s['rate_headroom_pct']:.0f}% rental-rate "
            f"headroom before DSCR < 1. Pricing power erosion is the live risk."
        )
    else:
        st.success(
            f"**Self-financing** at these assumptions: {dscr:.2f}x coverage with "
            f"{s['rate_headroom_pct']:.0f}% rate headroom."
        )

    st.markdown("**DSCR sensitivity — rental-rate erosion × utilisation**")
    haircuts = [0.0, 0.15, 0.30, 0.45, 0.60]
    utils = [0.60, 0.70, 0.80, 0.90, 1.00]
    grid = dscr_grid(eco, haircuts, utils)
    sens = pd.DataFrame(
        grid,
        index=[f"-{int(h*100)}% rate" for h in haircuts],
        columns=[f"{int(u*100)}% util" for u in utils],
    )
    def dscr_color(v):
        if v < 1.0:
            return "background-color: #f4c7c3; color: #7f1d1d"   # red: underwater
        if v < 1.25:
            return "background-color: #fde8b0; color: #7c4a03"   # amber: thin
        return "background-color: #c6e7c6; color: #14532d"       # green: covered
    st.dataframe(
        sens.style.format("{:.2f}x").map(dscr_color),
        width="stretch",
    )
    st.caption(
        "Red cells = DSCR < 1 (debt not covered). The diagonal collapse shows why "
        "NeoCloud durability hinges on holding **both** utilisation and pricing — "
        "a correlated shock (e.g. an H-series price war as new accelerators ship) "
        "moves you down *and* right at once. This is the mechanism behind the "
        "GPU-backed-debt concern, made quantitative."
    )

# --------------------------------------------------------------------------- #
# Upstream bottleneck — CoWoS & HBM
# --------------------------------------------------------------------------- #
with tab_bottleneck:
    st.markdown("### The binding constraint: advanced packaging & memory")
    st.caption(
        "Hyperscaler budgets can double overnight; the physical supply of CoWoS "
        "(TSMC advanced packaging) and HBM (stacked memory) cannot. This is where "
        "demand meets a hard ceiling — so **allocation and price**, not capital, "
        "clear the market."
    )

    cowos25 = float(cowos.loc[cowos.year == 2025, "cowos_kwpm"].iloc[0])
    cowos26 = float(cowos.loc[cowos.year == 2026, "cowos_kwpm"].iloc[0])
    cowos26_lo = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_low"].iloc[0])
    cowos26_hi = float(cowos.loc[cowos.year == 2026, "cowos_kwpm_high"].iloc[0])
    hbm25 = float(hbm.loc[hbm.year == 2025, "hbm_revenue_b"].iloc[0])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("CoWoS capacity 2025", f"{cowos25:.0f}k wpm", "~2× vs 2024")
    k2.metric("CoWoS 2026E", f"{cowos26_lo:.0f}–{cowos26_hi:.0f}k wpm",
              "wide range")
    k3.metric("HBM TAM 2025", f"${hbm25:.0f}B", "sold out")
    k4.metric("HBM TAM 2028E", "$100B", "~40% CAGR")

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown("**TSMC CoWoS capacity (k wafers/month)** — ~10× in 3 yrs")
        cf = cowos.copy()
        err_hi = cf["cowos_kwpm_high"] - cf["cowos_kwpm"]
        err_lo = cf["cowos_kwpm"] - cf["cowos_kwpm_low"]
        figc = go.Figure(go.Bar(
            x=cf["year"], y=cf["cowos_kwpm"], marker_color="#4285F4",
            error_y=dict(type="data", symmetric=False,
                         array=err_hi, arrayminus=err_lo),
        ))
        figc.update_layout(height=340, yaxis_title="k wafers/month",
                           xaxis_title="Year")
        st.plotly_chart(figc, width="stretch")
    with cc2:
        st.markdown("**HBM market ($B TAM) & 2025 supplier share**")
        figh = px.bar(hbm, x="year", y="hbm_revenue_b",
                      labels={"hbm_revenue_b": "$B TAM", "year": "Year"})
        figh.update_traces(marker_color="#34A853")
        figh.update_layout(height=240, showlegend=False)
        st.plotly_chart(figh, width="stretch")
        shares = {"SK Hynix": 57, "Micron": 21, "Samsung": 22}
        figp = go.Figure(go.Pie(
            labels=list(shares), values=list(shares.values()), hole=0.5,
            marker_colors=["#4285F4", "#FBBC04", "#EA4335"]))
        figp.update_layout(height=200, margin=dict(t=10, b=10),
                           annotations=[dict(text="Q3'25", showarrow=False)])
        st.plotly_chart(figp, width="stretch")

    st.markdown("---")
    st.markdown("### Supply ceiling vs capex-implied demand")
    st.caption(
        "Convert CoWoS wafer capacity into an accelerator-output ceiling, then "
        "compare it to the unit demand implied by hyperscaler AI capex. The "
        "conversion is **illustrative** — net of yield, ramp and shared (non-"
        "hyperscaler) usage — so treat it as order-of-magnitude, not a forecast."
    )
    eff = st.slider(
        "Effective accelerators per CoWoS wafer (net)", 4, 20, 7,
        help="Theoretical max ~16 (B200, CoWoS-L) to ~25-29 (Hopper); net "
             "effective is lower after yield, ramp and non-NVIDIA usage.")
    ceil25 = cowos25 * 1000 * 12 * eff / 1e6      # millions of accelerators/yr
    ceil26 = cowos26 * 1000 * 12 * eff / 1e6

    # demand proxy from the capex model (all 4 hyperscalers, current assumptions)
    dem = capex[capex["fiscal_year"] == 2025].copy()
    dem["ai_share"] = dem["company"].map(ai_share).fillna(0.6)
    demand25 = (dem["capex_usd_b"] * dem["ai_share"]).sum() * 1000 / gpu_price_k / 1000

    b1, b2, b3 = st.columns(3)
    b1.metric("CoWoS accelerator ceiling 2025", f"~{ceil25:.1f}M/yr")
    b2.metric("CoWoS ceiling 2026E", f"~{ceil26:.1f}M/yr",
              f"+{(ceil26/ceil25-1)*100:.0f}%")
    b3.metric("Big-4 FY25 implied demand", f"~{demand25:.1f}M",
              help="From AI capex / blended unit cost, current sidebar assumptions")

    comp = pd.DataFrame({
        "metric": ["CoWoS ceiling 2025", "Big-4 implied demand FY25",
                   "CoWoS ceiling 2026E"],
        "units_m": [ceil25, demand25, ceil26],
        "kind": ["Supply", "Demand", "Supply"],
    })
    figd = px.bar(comp, x="metric", y="units_m", color="kind",
                  color_discrete_map={"Supply": "#4285F4", "Demand": "#EA4335"},
                  labels={"units_m": "Accelerators (M/yr)", "metric": ""})
    figd.update_layout(height=340, legend_title="")
    st.plotly_chart(figd, width="stretch")

    st.info(
        "**The strategic read:** four hyperscalers' AI capex alone implies unit "
        "demand on the same order as the *entire* global advanced-packaging "
        "ceiling — before NeoClouds, sovereign AI, or enterprise are counted. "
        "That is the definition of a bottleneck. Two consequences a TI analyst "
        "should flag: (1) **CoWoS/HBM capacity, not budgets, is the true governor "
        "of who trains the largest models**; (2) Microsoft attributing ~\\$25B of "
        "its 2026 step-up to memory cost is the bottleneck **leaking into price** "
        "— rising capex that buys *less* incremental compute than the headline "
        "implies. Google's TPU + in-house packaging is a structural hedge here."
    )

# --------------------------------------------------------------------------- #
# Value chain
# --------------------------------------------------------------------------- #
with tab_chain:
    st.markdown("### The AI compute value chain")
    st.caption(
        "Capex flows downstream from silicon to models. Each layer has its own "
        "bottleneck — the binding constraint that gates the whole stack."
    )
    for _, row in chain.iterrows():
        with st.expander(
            f"**{row['layer_order']}. {row['layer']} — {row['segment']}**",
            expanded=False,
        ):
            st.markdown(f"- **Key players:** {row['key_players']}")
            st.markdown(f"- **Role in stack:** {row['role_in_stack']}")
            st.markdown(f"- **Key metric to track:** {row['key_metric']}")
            st.markdown(f"- **Bottleneck:** :red[{row['bottleneck']}]")

    st.markdown("---")
    st.markdown(
        "**Why this matters for strategy:** the hyperscaler capex tracked in the "
        "deep-dive is the *demand pull* on layers 1–4. A $40B step-up in "
        "Alphabet capex converts — via advanced packaging (CoWoS) and HBM "
        "availability — into the binding supply constraints upstream."
    )

# --------------------------------------------------------------------------- #
# Sources & method
# --------------------------------------------------------------------------- #
with tab_sources:
    st.markdown("### Sources & methodology")
    st.markdown(
        "**Data integrity model.** Every figure is primary-sourced and carries "
        "a `source_type`:\n"
        "- `10-K (extracted)` — parsed from the 10-K PDFs in `data/raw/alphabet` "
        "and cross-validated across overlapping filing years (Alphabet).\n"
        "- `10-K (EDGAR XBRL)` — pulled from SEC EDGAR's XBRL company-concept API "
        "using the *as-originally-reported* annual value, citing each filing's "
        "accession number (Microsoft / Amazon / Meta).\n"
    )
    st.markdown("**Full provenance — every datapoint and its source:**")
    st.dataframe(
        capex[[
            "company", "fiscal_year", "capex_usd_m", "source_type",
            "source_doc", "source_page",
        ]].rename(columns={
            "company": "Company", "fiscal_year": "FY", "capex_usd_m": "Capex $M",
            "source_type": "Source type", "source_doc": "Source doc / accession",
            "source_page": "Page",
        }),
        width="stretch", hide_index=True, height=320,
    )
    st.markdown(
        "**Key assumptions (editable in the sidebar):**\n"
        "- *AI-attributable share* — fraction of headline capex tied to AI "
        "infrastructure. Defaults are illustrative, not company-disclosed.\n"
        "- *Blended accelerator system cost* — all-in $/unit incl. networking, "
        "power and DC fit-out; used to derive implied unit volumes.\n\n"
        "These are deliberately exposed as controls so a reviewer can stress-test "
        "the conclusions rather than take them on faith."
    )
    st.caption(
        "Capex series for all four hyperscalers is now primary-sourced. Next to "
        "harden: add NeoCloud contracted backlog, gigawatt-scale power "
        "commitments, and the upstream supply constraint (TSMC CoWoS / HBM)."
    )
