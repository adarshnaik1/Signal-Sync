#!/usr/bin/env python
import json
import sys
from dotenv import load_dotenv

from signal_sync.ta.crew import TAAnalysisCrew

load_dotenv()


def run_ta(ticker: str, horizon: str = "medium-term") -> str:
    crew = TAAnalysisCrew(ticker=ticker, horizon=horizon)
    return crew.run()


def run() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "TCS.NS"
    horizon = sys.argv[2] if len(sys.argv) > 2 else "medium-term"

    output = run_ta(ticker=ticker, horizon=horizon)
    print("\n=== TA Analysis Output ===\n")
    print(output)


if __name__ == "__main__":
    run()
