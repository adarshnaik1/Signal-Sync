def classify_risk(value, low_threshold, high_threshold):

    if value is None:
        return "Unknown"

    if value < low_threshold:
        return "Low"

    elif value < high_threshold:
        return "Moderate"

    else:
        return "High"


def analyze_risk(unified_schema):

    market_data = unified_schema.get(
        "market_data", {}
    )

    financial_ratios = unified_schema.get(
        "financial_ratios", {}
    )

    financial_data = unified_schema.get(
        "financial_data", {}
    )

    cash_flow = financial_data.get(
        "cash_flow", {}
    )

    # Beta Risk
    beta = market_data.get("beta")

    market_risk = classify_risk(

        beta,

        1.0,

        1.5
    )

    # Debt Risk
    debt_to_equity = financial_ratios.get(
        "debt_to_equity"
    )

    debt_risk = classify_risk(

        debt_to_equity,

        50,

        100
    )

    # Liquidity Risk
    operating_cf = cash_flow.get(
        "operating_cash_flow", {}
    )

    latest_operating_cf = None

    if operating_cf:

        latest_operating_cf = operating_cf[
            list(operating_cf.keys())[0]
        ]

    liquidity_risk = "Low"

    if latest_operating_cf is not None:

        if latest_operating_cf < 0:
            liquidity_risk = "High"

        elif latest_operating_cf < 1000000000:
            liquidity_risk = "Moderate"

    # Profitability Risk
    profit_margin = financial_ratios.get(
        "profit_margin"
    )

    profitability_risk = "Low"

    if profit_margin is not None:

        if profit_margin < 0:
            profitability_risk = "High"

        elif profit_margin < 0.05:
            profitability_risk = "Moderate"

    return {

        "market_risk":
            market_risk,

        "debt_risk":
            debt_risk,

        "liquidity_risk":
            liquidity_risk,

        "profitability_risk":
            profitability_risk,

        "beta":
            beta,

        "debt_to_equity":
            debt_to_equity,

        "profit_margin":
            profit_margin,

        "operating_cash_flow":
            latest_operating_cf
    }