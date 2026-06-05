def classify_pe(pe_ratio):

    if pe_ratio is None:
        return "Unknown"

    if pe_ratio < 15:
        return "Undervalued"

    elif pe_ratio < 30:
        return "Fairly Valued"

    else:
        return "Overvalued"


def classify_growth(revenue_growth):

    if revenue_growth is None:
        return "Unknown"

    if revenue_growth > 15:
        return "Strong"

    elif revenue_growth > 5:
        return "Moderate"

    else:
        return "Weak"


def analyze_valuation(unified_schema):

    financial_ratios = unified_schema.get(
        "financial_ratios", {}
    )

    financial_data = unified_schema.get(
        "financial_data", {}
    )

    income_statement = financial_data.get(
        "income_statement", {}
    )

    pe_ratio = financial_ratios.get(
        "pe_ratio"
    )

    revenue_data = income_statement.get(
        "total_revenue", {}
    )

    revenue_growth = None

    years = list(revenue_data.keys())

    if len(years) >= 2:

        latest = revenue_data[years[0]]

        previous = revenue_data[years[1]]

        if previous != 0:

            revenue_growth = (
                (latest - previous)
                / previous
            ) * 100

    pe_analysis = classify_pe(
        pe_ratio
    )

    growth_strength = classify_growth(
        revenue_growth
    )

    valuation_status = "Fairly Valued"

    if pe_analysis == "Undervalued" and growth_strength == "Strong":

        valuation_status = "Undervalued"

    elif pe_analysis == "Overvalued" and growth_strength == "Weak":

        valuation_status = "Overvalued"

    return {

        "pe_ratio":
            pe_ratio,

        "revenue_growth_percent":
            revenue_growth,

        "pe_analysis":
            pe_analysis,

        "growth_strength":
            growth_strength,

        "valuation_status":
            valuation_status
    }