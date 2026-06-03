"""Sanity tests for the GPU unit-economics model. Run: python model/test_gpu_unit_economics.py"""
from gpu_unit_economics import GpuEconomics, HOURS_PER_YEAR


def approx(a, b, tol=1e-6):
    return abs(a - b) < tol


def test_debt_equity_split():
    e = GpuEconomics(gpu_cost_usd=40_000, ltv=0.7)
    assert e.debt == 28_000 and e.equity == 12_000


def test_zero_rate_amortisation():
    e = GpuEconomics(gpu_cost_usd=10_000, ltv=1.0, interest_rate=0.0, debt_term_yrs=4)
    assert approx(e.annual_debt_service, 2_500)


def test_breakeven_rate_gives_dscr_one():
    base = GpuEconomics()
    be = base.breakeven_rental_rate
    scen = GpuEconomics(rental_rate_per_hr=be, utilization=base.utilization,
                        opex_per_hr=base.opex_per_hr, ltv=base.ltv,
                        interest_rate=base.interest_rate)
    assert approx(scen.dscr, 1.0, tol=1e-4), scen.dscr


def test_breakeven_utilization_gives_dscr_one():
    base = GpuEconomics()
    bu = base.breakeven_utilization
    scen = GpuEconomics(utilization=bu, rental_rate_per_hr=base.rental_rate_per_hr,
                        opex_per_hr=base.opex_per_hr, ltv=base.ltv,
                        interest_rate=base.interest_rate)
    assert approx(scen.dscr, 1.0, tol=1e-4), scen.dscr


def test_dscr_falls_with_rate():
    hi = GpuEconomics(rental_rate_per_hr=3.0).dscr
    lo = GpuEconomics(rental_rate_per_hr=2.0).dscr
    assert hi > lo


if __name__ == "__main__":
    base = GpuEconomics()
    s = base.summary()
    print("Base case:")
    print(f"  Annual revenue/GPU : ${s['annual_revenue']:,.0f}")
    print(f"  Cash margin/GPU    : ${s['cash_margin']:,.0f}")
    print(f"  Debt service/GPU   : ${s['annual_debt_service']:,.0f}")
    print(f"  DSCR               : {s['dscr']:.2f}x")
    print(f"  Break-even util    : {s['breakeven_utilization']*100:.0f}%")
    print(f"  Break-even rate    : ${s['breakeven_rental_rate']:.2f}/hr "
          f"(headroom {s['rate_headroom_pct']:.0f}%)")
    n_pass = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n_pass += 1
    print(f"\nALL {n_pass} TESTS PASSED")
