"""
Test V2 endpoint with context-aware prompting for the 3 core dashboard apps.

Tests:
1. Monte Carlo Simulation (MCS) - monte_carlo_interpreter_cited
2. Portfolio Evaluation - results_interpreter_cited
3. Risk Factor Analysis - risk_metrics_interpreter_cited

Run: pytest tests/test_v2_context_aware.py -v
Or standalone: python tests/test_v2_context_aware.py
"""

import json
import requests
import sys
from typing import Any

# API base URL
BASE_URL = "http://localhost:8080"


# =============================================================================
# Test Data: Realistic app_context payloads for each page type
# =============================================================================

MCS_APP_CONTEXT = {
    "page": "monte_carlo",
    "initial_portfolio": 5000000,
    "currency": "USD",
    "num_simulations": 1000,
    "inflation_rate_pct": 2.5,
    "simulations": {
        "aggressive": {
            "name": "Aggressive Growth",
            "duration_years": 10,
            "percentile_5th": 3200000,
            "percentile_50th": 7500000,
            "percentile_95th": 15000000,
            "prob_outperform_inflation": 85.2,
            "prob_loss_50pct": 3.1,
            "annual_return_pct": 8.5,
            "annual_risk_pct": 18.2,
        },
        "balanced": {
            "name": "Balanced Portfolio",
            "duration_years": 10,
            "percentile_5th": 4100000,
            "percentile_50th": 6800000,
            "percentile_95th": 11000000,
            "prob_outperform_inflation": 92.5,
            "prob_loss_50pct": 0.8,
            "annual_return_pct": 6.2,
            "annual_risk_pct": 12.5,
        }
    }
}

PORTFOLIO_EVAL_APP_CONTEXT = {
    "page": "portfolio_evaluation",
    "frontier_summaries": {
        "core_only": {
            "name": "Core Assets Only",
            "min_risk_pct": 8.5,
            "max_risk_pct": 22.0,
            "min_return_pct": 4.2,
            "max_return_pct": 9.8,
            "optimal_sharpe": 0.72,
            "optimal_return_pct": 7.1,
            "optimal_risk_pct": 12.3,
        },
        "core_private": {
            "name": "Core + Private Markets",
            "min_risk_pct": 9.2,
            "max_risk_pct": 25.0,
            "min_return_pct": 5.1,
            "max_return_pct": 12.5,
            "optimal_sharpe": 0.85,
            "optimal_return_pct": 8.8,
            "optimal_risk_pct": 14.1,
        }
    },
    "optimal_allocation": {
        "US Equity": 35.0,
        "International Equity": 15.0,
        "Core Fixed Income": 25.0,
        "Private Equity": 12.0,
        "Private Credit": 8.0,
        "Diversified Strategies": 5.0,
    },
    "benchmark": {
        "return": 0.065,
        "risk": 0.11,
    },
    "caps_template": "balanced"
}

RISK_ANALYTICS_APP_CONTEXT = {
    "page": "risk_analytics",
    "portfolio_name": "Client Growth Portfolio",
    "benchmark_name": "60/40 Benchmark",
    "portfolio_volatility_pct": 14.5,
    "benchmark_volatility_pct": 11.2,
    "tracking_error_pct": 4.8,
    "factor_explained_pct": 78.5,
    "idiosyncratic_pct": 21.5,
    "portfolio_cagr_pct": 8.9,
    "benchmark_cagr_pct": 6.5,
    "portfolio_sharpe": 0.82,
    "benchmark_sharpe": 0.65,
    "portfolio_max_dd_pct": -18.5,
    "total_beta": 1.15,
    "growth_beta": 0.85,
    "defensive_beta": 0.25,
    "avg_correlation": 0.62,
    "effective_n": 18.5,
    "concentration_ratio": 42.0,
    "top_risk_contributors": [
        {"security": "AAPL", "contribution_pct": 8.5},
        {"security": "MSFT", "contribution_pct": 7.2},
        {"security": "GOOGL", "contribution_pct": 6.1},
        {"security": "AMZN", "contribution_pct": 5.8},
        {"security": "NVDA", "contribution_pct": 4.9},
    ]
}


# =============================================================================
# Test Cases
# =============================================================================

TEST_CASES = [
    # MCS Tests
    {
        "name": "MCS: Explain percentiles",
        "query": "What do my percentile outcomes mean?",
        "domain": "app_education",
        "prompt_name": "monte_carlo_interpreter_cited",
        "app_context": MCS_APP_CONTEXT,
        "expected_keywords": ["percentile", "5th", "95th", "pessimistic", "optimistic"],
    },
    {
        "name": "MCS: Probability interpretation",
        "query": "What does the 85% probability of outperforming inflation mean?",
        "domain": "app_education",
        "prompt_name": "monte_carlo_interpreter_cited",
        "app_context": MCS_APP_CONTEXT,
        "expected_keywords": ["probability", "inflation", "85"],
    },
    {
        "name": "MCS: Compare scenarios",
        "query": "How does my aggressive scenario compare to the balanced one?",
        "domain": "app_education",
        "prompt_name": "monte_carlo_interpreter_cited",
        "app_context": MCS_APP_CONTEXT,
        "expected_keywords": ["aggressive", "balanced", "risk", "return"],
    },
    # Portfolio Evaluation Tests
    {
        "name": "Portfolio: Explain efficient frontier",
        "query": "What does the efficient frontier show me?",
        "domain": "app_education",
        "prompt_name": "results_interpreter_cited",
        "app_context": PORTFOLIO_EVAL_APP_CONTEXT,
        "expected_keywords": ["frontier", "risk", "return", "optimal"],
    },
    {
        "name": "Portfolio: Optimal allocation",
        "query": "Why is my optimal allocation weighted towards US Equity?",
        "domain": "app_education",
        "prompt_name": "results_interpreter_cited",
        "app_context": PORTFOLIO_EVAL_APP_CONTEXT,
        "expected_keywords": ["allocation", "equity", "35"],
    },
    {
        "name": "Portfolio: Private markets benefit",
        "query": "How do private markets improve my portfolio?",
        "domain": "app_education",
        "prompt_name": "results_interpreter_cited",
        "app_context": PORTFOLIO_EVAL_APP_CONTEXT,
        "expected_keywords": ["private", "sharpe", "return"],
    },
    # Risk Analytics Tests
    {
        "name": "Risk: Explain Sharpe ratio",
        "query": "Is my Sharpe ratio of 0.82 good?",
        "domain": "app_education",
        "prompt_name": "risk_metrics_interpreter_cited",
        "app_context": RISK_ANALYTICS_APP_CONTEXT,
        "expected_keywords": ["sharpe", "0.82", "risk-adjusted"],
    },
    {
        "name": "Risk: Beta interpretation",
        "query": "What does my total beta of 1.15 mean?",
        "domain": "app_education",
        "prompt_name": "risk_metrics_interpreter_cited",
        "app_context": RISK_ANALYTICS_APP_CONTEXT,
        "expected_keywords": ["beta", "1.15", "market"],
    },
    {
        "name": "Risk: Top contributors",
        "query": "Why is AAPL my biggest risk contributor?",
        "domain": "app_education",
        "prompt_name": "risk_metrics_interpreter_cited",
        "app_context": RISK_ANALYTICS_APP_CONTEXT,
        "expected_keywords": ["AAPL", "8.5", "contribution", "concentration"],
    },
]


def run_test(test_case: dict) -> dict[str, Any]:
    """Run a single test case against the V2 endpoint."""
    payload = {
        "query": test_case["query"],
        "domain": test_case["domain"],
        "prompt_name": test_case["prompt_name"],
        "app_context": test_case["app_context"],
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/v2/query",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()

        # Check for expected keywords in response
        answer = result.get("answer", "").lower()
        found_keywords = [kw for kw in test_case["expected_keywords"] if kw.lower() in answer]
        missing_keywords = [kw for kw in test_case["expected_keywords"] if kw.lower() not in answer]

        return {
            "name": test_case["name"],
            "status": "PASS" if len(found_keywords) >= len(test_case["expected_keywords"]) // 2 else "PARTIAL",
            "answer": result.get("answer", "")[:500],
            "sources": len(result.get("sources", [])),
            "intent": result.get("intent"),
            "retrieval_quality": result.get("retrieval_quality"),
            "found_keywords": found_keywords,
            "missing_keywords": missing_keywords,
            "error": None,
        }

    except requests.exceptions.ConnectionError:
        return {
            "name": test_case["name"],
            "status": "ERROR",
            "answer": None,
            "error": "Connection failed - is the server running?",
        }
    except Exception as e:
        return {
            "name": test_case["name"],
            "status": "ERROR",
            "answer": None,
            "error": str(e),
        }


def run_all_tests():
    """Run all test cases and print results."""
    print("\n" + "=" * 80)
    print("V2 Context-Aware Prompting Tests")
    print("=" * 80)

    results = {"PASS": 0, "PARTIAL": 0, "ERROR": 0}

    for test_case in TEST_CASES:
        print(f"\n[{test_case['name']}]")
        print(f"  Query: {test_case['query']}")
        print(f"  Prompt: {test_case['prompt_name']}")

        result = run_test(test_case)
        results[result["status"]] = results.get(result["status"], 0) + 1

        if result["status"] == "ERROR":
            print(f"  Status: ❌ ERROR - {result['error']}")
        else:
            status_icon = "✅" if result["status"] == "PASS" else "🟡"
            print(f"  Status: {status_icon} {result['status']}")
            print(f"  Quality: {result['retrieval_quality']}")
            print(f"  Sources: {result['sources']}")
            print(f"  Keywords found: {result['found_keywords']}")
            if result['missing_keywords']:
                print(f"  Keywords missing: {result['missing_keywords']}")
            print(f"  Answer preview: {result['answer'][:200]}...")

    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"  PASS: {results['PASS']}")
    print(f"  PARTIAL: {results['PARTIAL']}")
    print(f"  ERROR: {results['ERROR']}")
    print(f"  Total: {sum(results.values())}")

    return results


if __name__ == "__main__":
    results = run_all_tests()
    sys.exit(0 if results.get("ERROR", 0) == 0 else 1)
