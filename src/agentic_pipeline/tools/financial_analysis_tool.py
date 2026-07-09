def calculate_growth(current, previous):

    try:

        if previous in [0, None]:
            return None

        growth = ((current - previous) / previous) * 100

        return round(growth, 2)

    except Exception:
        return None


def analyze_financials(unified_schema):

    financial_data = unified_schema.get(
        "financial_data", {}
    )

    financial_ratios = unified_schema.get(
        "financial_ratios", {}
    )

    income_statement = financial_data.get(
        "income_statement", {}
    )

    balance_sheet = financial_data.get(
        "balance_sheet", {}
    )

    cash_flow = financial_data.get(
        "cash_flow", {}
    )

    # ----------------------------
    # Revenue Growth
    # ----------------------------

    revenue_data = income_statement.get(
        "total_revenue", {}
    )

    revenue_growth = None

    if len(revenue_data) >= 2:

        years = list(revenue_data.keys())

        revenue_growth = calculate_growth(
            revenue_data[years[0]],
            revenue_data[years[1]]
        )

    # ----------------------------
    # Profit Growth
    # ----------------------------

    profit_data = income_statement.get(
        "net_income", {}
    )

    profit_growth = None

    if len(profit_data) >= 2:

        years = list(profit_data.keys())

        profit_growth = calculate_growth(
            profit_data[years[0]],
            profit_data[years[1]]
        )

    # ----------------------------
    # Latest Debt
    # ----------------------------

    debt_data = balance_sheet.get(
        "total_debt", {}
    )

    latest_debt = None

    if debt_data:

        latest_debt = debt_data[
            list(debt_data.keys())[0]
        ]

    # ----------------------------
    # Latest Cash
    # ----------------------------

    cash_data = balance_sheet.get(
        "cash_and_cash_equivalents", {}
    )

    latest_cash = None

    if cash_data:

        latest_cash = cash_data[
            list(cash_data.keys())[0]
        ]

    # ----------------------------
    # Cash-to-Debt Ratio
    # ----------------------------

    cash_to_debt_ratio = None

    try:

        if latest_cash is not None and latest_debt not in [0, None]:

            cash_to_debt_ratio = round(
                latest_cash / latest_debt,
                2
            )

    except Exception:
        pass

    # ----------------------------
    # Operating Cash Flow
    # ----------------------------

    operating_cf = cash_flow.get(
        "operating_cash_flow", {}
    )

    latest_operating_cf = None

    if operating_cf:

        latest_operating_cf = operating_cf[
            list(operating_cf.keys())[0]
        ]

    # ----------------------------
    # Free Cash Flow
    # ----------------------------

    free_cf = cash_flow.get(
        "free_cash_flow", {}
    )

    latest_free_cf = None

    if free_cf:

        latest_free_cf = free_cf[
            list(free_cf.keys())[0]
        ]

    # ----------------------------
    # Additional Ratios
    # ----------------------------

    roe = financial_ratios.get(
        "roe"
    )

    roa = financial_ratios.get(
        "roa"
    )

    profit_margin = financial_ratios.get(
        "profit_margin"
    )

    debt_to_equity = financial_ratios.get(
        "debt_to_equity"
    )

    return {

        "revenue_growth_percent":
            revenue_growth,

        "profit_growth_percent":
            profit_growth,

        "latest_total_debt":
            latest_debt,

        "latest_cash":
            latest_cash,

        "cash_to_debt_ratio":
            cash_to_debt_ratio,

        "latest_operating_cash_flow":
            latest_operating_cf,

        "latest_free_cash_flow":
            latest_free_cf,

        "roe":
            round(roe * 100, 2)
            if roe is not None else None,

        "roa":
            round(roa * 100, 2)
            if roa is not None else None,

        "profit_margin":
            round(profit_margin * 100, 2)
            if profit_margin is not None else None,

        "debt_to_equity":
            debt_to_equity
    }
