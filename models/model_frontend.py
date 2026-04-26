from pathlib import Path
import sys

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.pipeline import predict


st.set_page_config(
    page_title="Financial Profile",
    page_icon="INR",
    layout="centered",
)


INVESTOR_LABELS = {
    0: "Conservative Investor",
    1: "Balanced Investor",
    2: "Growth Investor",
}

INVESTOR_DESCRIPTIONS = {
    0: "Focuses on capital protection, steadier returns, and lower risk exposure.",
    1: "Balances growth potential with stability across multiple asset classes.",
    2: "Comfortable with higher volatility in pursuit of stronger long-term growth.",
}

ASSET_LABELS = {
    "equity": "Equity",
    "debt": "Debt",
    "gold": "Gold",
    "cash": "Cash",
}

def render_result(result: dict) -> None:
    investor_type = result["investor_type"]
    allocation = result["allocation"]
    investor_label = INVESTOR_LABELS.get(investor_type, f"Investor Type {investor_type}")
    investor_description = INVESTOR_DESCRIPTIONS.get(
        investor_type,
        "Portfolio allocation generated from the model output.",
    )

    st.divider()
    st.subheader("Recommended Profile")
    st.success(investor_label)
    st.write(investor_description)

    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.metric("Investor Type Code", investor_type)
    with metric_col2:
        top_asset = max(allocation, key=allocation.get)
        st.metric("Highest Allocation", f"{ASSET_LABELS[top_asset]} ({allocation[top_asset]:.2f}%)")

    st.subheader("Portfolio Allocation")
    allocation_df = pd.DataFrame(
        [{"Asset Class": ASSET_LABELS[key], "Allocation (%)": value} for key, value in allocation.items()]
    )
    st.dataframe(allocation_df, use_container_width=True, hide_index=True)

    allocation_cols = st.columns(len(allocation))
    for col, (asset, value) in zip(allocation_cols, allocation.items()):
        with col:
            st.metric(ASSET_LABELS[asset], f"{value:.2f}%")
            st.progress(min(max(int(round(value)), 0), 100))

    with st.expander("View raw output"):
        st.json(
            {
                "investor_type": investor_type,
                "investor_label": investor_label,
                "allocation": allocation,
            }
        )


st.title("Financial Profile Questionnaire")
st.markdown(
    "Complete the details below to generate your investor profile and suggested portfolio allocation."
)

with st.form("financial_profile_form"):
    st.subheader("Basic Details")

    age = st.number_input("1. What is your age?", min_value=18, max_value=100, step=1, value=25)

    educ_map = {"School or below": 1, "Graduate": 2, "Postgraduate+": 3, "Other": -1}
    educ_choice = st.selectbox("2. What is your highest education level?", list(educ_map.keys()))
    educ = educ_map[educ_choice]

    married_map = {"Single": 0, "Married": 1}
    married_choice = st.selectbox("3. What is your marital status?", list(married_map.keys()))
    married = married_map[married_choice]

    kids_map = {"0": 0, "1": 1, "2": 2, "3+": 3}
    kids_choice = st.selectbox("4. How many dependents do you have?", list(kids_map.keys()))
    kids = kids_map[kids_choice]

    st.subheader("Income")

    income_ranges = {
        "Less than Rs 5 Lakh": 300000,
        "Rs 5 - 10 Lakh": 750000,
        "Rs 10 - 20 Lakh": 1500000,
        "More than Rs 20 Lakh": 3000000,
    }
    income_choice = st.select_slider(
        "5. What is your annual income?",
        options=list(income_ranges.keys()),
    )
    income = income_ranges[income_choice]

    st.subheader("Financial Position")

    asset_ranges = {
        "Less than Rs 1 Lakh": 50000,
        "Rs 1 - 5 Lakh": 300000,
        "Rs 5 - 10 Lakh": 750000,
        "More than Rs 10 Lakh": 1500000,
    }
    asset_choice = st.select_slider(
        "6. What is your total savings/investments?",
        options=list(asset_ranges.keys()),
    )
    asset = asset_ranges[asset_choice]

    debt_ranges = {
        "None": 0,
        "Less than Rs 1 Lakh": 50000,
        "Rs 1 - 5 Lakh": 300000,
        "More than Rs 5 Lakh": 800000,
    }
    debt_choice = st.select_slider(
        "7. What is your total outstanding loans/debt?",
        options=list(debt_ranges.keys()),
    )
    debt = debt_ranges[debt_choice]

    st.subheader("Financial Behavior")

    saved_choice = st.radio("8. Do you save money regularly?", ["Yes", "No"], horizontal=True)
    saved = 1 if saved_choice == "Yes" else 0

    emerg_choice = st.radio(
        "9. Do you have an emergency fund covering 3-6 months of your expenses?",
        ["Yes", "No"],
        horizontal=True,
    )
    emergsav = 1 if emerg_choice == "Yes" else 0

    st.subheader("Risk and Awareness")

    risk_scenario = st.radio(
        "10. How would you react to a high-risk, high-return investment opportunity?",
        [
            "I will avoid it and keep my money safe",
            "I will invest a small portion only",
            "I will invest the full amount for maximum returns",
        ],
    )
    risk_map = {
        "I will avoid it and keep my money safe": 0,
        "I will invest a small portion only": 1,
        "I will invest the full amount for maximum returns": 2,
    }
    yesfinrisk = risk_map[risk_scenario]

    st.markdown("**11. Quick financial knowledge check**")
    mcq_questions = [
        {
            "q": "If inflation is 6% and your savings account earns 4%, what happens to your purchasing power?",
            "options": ["It increases", "It stays the same", "It decreases", "Cannot be determined"],
            "answer": "It decreases",
        },
        {
            "q": "What does diversification mean in investing?",
            "options": [
                "Putting all money in one asset",
                "Spreading investments across assets to reduce risk",
                "Investing only in bonds",
                "Withdrawing money frequently",
            ],
            "answer": "Spreading investments across assets to reduce risk",
        },
        {
            "q": "Which is generally considered the highest-risk investment?",
            "options": ["Fixed Deposit", "Government Bond", "Equity/Stocks", "Savings Account"],
            "answer": "Equity/Stocks",
        },
    ]

    mcq_answers = []
    for index, item in enumerate(mcq_questions):
        answer = st.radio(
            f"Q{index + 1}. {item['q']}",
            item["options"],
            key=f"mcq_{index}",
            index=None,
        )
        mcq_answers.append(answer)

    st.subheader("Current Investments")

    stocks_ranges = {
        "None": 0,
        "Less than Rs 1 Lakh": 50000,
        "Rs 1 - 5 Lakh": 300000,
        "More than Rs 5 Lakh": 800000,
    }
    stocks_choice = st.select_slider(
        "12. How much have you invested in stocks/equity?",
        options=list(stocks_ranges.keys()),
    )
    stocks = stocks_ranges[stocks_choice]

    liquid_ranges = {
        "Less than Rs 1 Lakh": 50000,
        "Rs 1 - 5 Lakh": 300000,
        "More than Rs 5 Lakh": 800000,
    }
    liquid_choice = st.select_slider(
        "13. How much money do you keep in cash/bank/FD?",
        options=list(liquid_ranges.keys()),
    )
    liquid = liquid_ranges[liquid_choice]

    submitted = st.form_submit_button("Generate Recommendation", type="primary", use_container_width=True)


if submitted:
    if any(answer is None for answer in mcq_answers):
        st.warning("Please answer all 3 financial knowledge questions before generating the recommendation.")
    else:
        correct_answers = sum(
            1 for index, answer in enumerate(mcq_answers) if answer == mcq_questions[index]["answer"]
        )
        if correct_answers <= 1:
            finlit = 0
        elif correct_answers == 2:
            finlit = 1
        else:
            finlit = 2

        profile = {
            "AGE": age,
            "EDUC": educ,
            "MARRIED": married,
            "KIDS": kids,
            "INCOME": income,
            "ASSET": asset,
            "DEBT": debt,
            "SAVED": saved,
            "EMERGSAV": emergsav,
            "YESFINRISK": yesfinrisk,
            "FINLIT": finlit,
            "STOCKS": stocks,
            "LIQ": liquid,
        }

        try:
            result = predict(profile)
        except Exception as exc:
            st.error(f"Unable to run the model pipeline: {exc}")
        else:
            st.caption("Input profile")
            st.json(profile)
            render_result(result)
