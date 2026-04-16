def allocate_portfolio(investor_type, age, wealth_ratio, debt_ratio,
                       liquidity_ratio, emergency_savings):

    BASE_ALLOC = {
        0: {"equity": 20, "debt": 50, "gold": 20, "cash": 10},
        1: {"equity": 50, "debt": 30, "gold": 10, "cash": 10},
        2: {"equity": 75, "debt": 15, "gold": 5,  "cash": 5}
    }

    alloc = BASE_ALLOC[investor_type].copy()

    equity = alloc["equity"]
    debt = alloc["debt"]
    gold = alloc["gold"]
    cash = alloc["cash"]

    # --- Adjustments ---

    if age > 50:
        equity -= 15; debt += 10; cash += 5
    elif age < 30:
        equity += 5; debt -= 5

    if debt_ratio > 0.5:
        equity -= 10; debt += 10
    elif debt_ratio < 0.2:
        equity += 5; debt -= 5

    if liquidity_ratio < 0.1:
        equity -= 5; cash += 5

    if emergency_savings == 1:
        equity += 5
    else:
        equity -= 5; cash += 5

    if wealth_ratio > 3:
        equity += 5
    elif wealth_ratio < 1:
        equity -= 5; debt += 5

    # --- Clamp ---
    equity = max(equity, 0)
    debt = max(debt, 0)
    gold = max(gold, 0)
    cash = max(cash, 0)

    # --- Normalize ---
    total = equity + debt + gold + cash

    return {
        "equity": round(equity / total * 100, 2),
        "debt": round(debt / total * 100, 2),
        "gold": round(gold / total * 100, 2),
        "cash": round(cash / total * 100, 2)
    }