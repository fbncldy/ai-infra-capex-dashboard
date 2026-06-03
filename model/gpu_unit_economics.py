"""
GPU-backed-debt sustainability model (per-accelerator unit economics).

The NeoCloud thesis risk in one model: GPUs are bought largely with debt, but
they depreciate (and their rental rates erode) faster than the loans amortise.
This computes the Debt-Service Coverage Ratio (DSCR) and the break-even points
that decide whether a GPU-financed build is self-sustaining.

Pure functions only — no Streamlit — so the finance logic is testable in
isolation. See test_gpu_unit_economics.py.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

HOURS_PER_YEAR = 8760


@dataclass
class GpuEconomics:
    # capex & financing
    gpu_cost_usd: float = 40_000      # all-in system cost (GPU + networking + DC fit-out)
    ltv: float = 0.70                 # loan-to-value (debt / capex)
    interest_rate: float = 0.11       # annual rate on GPU-backed debt
    debt_term_yrs: int = 4            # amortisation period of the loan
    useful_life_yrs: int = 5          # depreciation life of the GPU
    # operations
    rental_rate_per_hr: float = 2.50  # $/GPU-hour charged to customers
    utilization: float = 0.90         # fraction of hours sold
    opex_per_hr: float = 0.90         # variable cost/GPU-hour (power, cooling, ops)

    # ---- derived economics -------------------------------------------------- #
    @property
    def debt(self) -> float:
        return self.ltv * self.gpu_cost_usd

    @property
    def equity(self) -> float:
        return self.gpu_cost_usd - self.debt

    @property
    def annual_revenue(self) -> float:
        return self.rental_rate_per_hr * HOURS_PER_YEAR * self.utilization

    @property
    def annual_opex(self) -> float:
        # variable opex is incurred on utilised hours
        return self.opex_per_hr * HOURS_PER_YEAR * self.utilization

    @property
    def cash_margin(self) -> float:
        """Cash available for debt service (revenue - variable opex)."""
        return self.annual_revenue - self.annual_opex

    @property
    def annual_debt_service(self) -> float:
        """Fully-amortising annuity payment (interest + principal)."""
        r, n, d = self.interest_rate, self.debt_term_yrs, self.debt
        if d == 0:
            return 0.0
        if r == 0:
            return d / n
        return d * r / (1 - (1 + r) ** -n)

    @property
    def dscr(self) -> float:
        """Debt-Service Coverage Ratio. <1 => cash flow can't cover debt."""
        ds = self.annual_debt_service
        return float("inf") if ds == 0 else self.cash_margin / ds

    @property
    def annual_depreciation(self) -> float:
        return self.gpu_cost_usd / self.useful_life_yrs

    @property
    def fcf_after_debt(self) -> float:
        return self.cash_margin - self.annual_debt_service

    # ---- break-even analysis ------------------------------------------------ #
    @property
    def breakeven_utilization(self) -> float:
        """Utilisation at which DSCR = 1, holding price/opex fixed."""
        denom = (self.rental_rate_per_hr - self.opex_per_hr) * HOURS_PER_YEAR
        return self.annual_debt_service / denom if denom > 0 else float("inf")

    @property
    def breakeven_rental_rate(self) -> float:
        """Rental rate ($/GPU-hr) at which DSCR = 1, holding utilisation fixed."""
        sold_hours = HOURS_PER_YEAR * self.utilization
        if sold_hours == 0:
            return float("inf")
        return self.annual_debt_service / sold_hours + self.opex_per_hr

    @property
    def rate_headroom_pct(self) -> float:
        """% the rental rate can fall before DSCR hits 1 (the cushion)."""
        if self.rental_rate_per_hr == 0:
            return 0.0
        return (1 - self.breakeven_rental_rate / self.rental_rate_per_hr) * 100

    def summary(self) -> dict:
        return {
            "debt": self.debt,
            "equity": self.equity,
            "annual_revenue": self.annual_revenue,
            "annual_opex": self.annual_opex,
            "cash_margin": self.cash_margin,
            "annual_debt_service": self.annual_debt_service,
            "dscr": self.dscr,
            "fcf_after_debt": self.fcf_after_debt,
            "annual_depreciation": self.annual_depreciation,
            "breakeven_utilization": self.breakeven_utilization,
            "breakeven_rental_rate": self.breakeven_rental_rate,
            "rate_headroom_pct": self.rate_headroom_pct,
            **{k: v for k, v in asdict(self).items()},
        }


def dscr_grid(base: GpuEconomics, rate_haircuts, utilizations):
    """DSCR sensitivity to rental-rate erosion (rows) x utilisation (cols)."""
    grid = []
    for hc in rate_haircuts:
        row = []
        for u in utilizations:
            scen = GpuEconomics(
                gpu_cost_usd=base.gpu_cost_usd, ltv=base.ltv,
                interest_rate=base.interest_rate, debt_term_yrs=base.debt_term_yrs,
                useful_life_yrs=base.useful_life_yrs,
                rental_rate_per_hr=base.rental_rate_per_hr * (1 - hc),
                utilization=u, opex_per_hr=base.opex_per_hr,
            )
            row.append(scen.dscr)
        grid.append(row)
    return grid
