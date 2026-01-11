# General FAQ - AlTi RPC Dashboard

This document provides general guidance for using the Risk & Portfolio Analytics Dashboard, covering cross-functional topics that span multiple analysis tools.

---

## What questions can I ask here?

The AI assistant can help you understand:

**Portfolio Analysis**
- Target allocation vs. current holdings
- Portfolio drift and rebalancing recommendations
- Efficient frontier and optimization insights

**Monte Carlo Simulations**
- Interpreting percentile outcomes (5th, 50th, 95th)
- Success probability and what drives it
- Comparing multiple scenarios

**Risk Analytics**
- VaR, CVaR, and maximum drawdown
- Factor exposures and tracking error
- Sharpe ratio and risk-adjusted returns

**Capital Market Assumptions**
- Expected returns by asset class
- Volatility and correlation assumptions
- How assumptions affect projections

**ESG & Impact**
- Clarity AI sustainability metrics
- Carbon intensity vs. financed intensity
- Temperature ratings and Net Zero alignment

**Tip:** Select a specific context pill (Portfolio Eval, Monte Carlo, etc.) for more targeted suggestions, or stay on "All" for general questions.

---

## How do I interpret my risk-adjusted returns?

Risk-adjusted returns measure how much return you earn per unit of risk taken. Key metrics:

**Sharpe Ratio**
- Formula: (Portfolio Return - Risk-Free Rate) / Portfolio Volatility
- Interpretation: Higher is better
- Typical ranges: Below 0.5 (poor), 0.5-1.0 (acceptable), 1.0-2.0 (good), Above 2.0 (excellent)

**Information Ratio**
- Formula: Active Return / Tracking Error
- Measures: Skill in beating the benchmark relative to deviation from it
- Higher values indicate more consistent outperformance

**Sortino Ratio**
- Like Sharpe, but only penalizes downside volatility
- Better for portfolios with asymmetric return distributions

**Why it matters:** A portfolio with 10% returns and 5% volatility (Sharpe ~1.6) is typically preferable to one with 15% returns and 20% volatility (Sharpe ~0.6), because the first delivers returns more consistently.

---

## What metrics matter most for my portfolio?

The most important metrics depend on your investment goals:

**For Wealth Preservation:**
- Maximum Drawdown: How much could you lose in a bad market?
- VaR/CVaR: What's the worst-case loss at a given confidence level?
- Volatility: How much does your portfolio value fluctuate?

**For Wealth Growth:**
- Expected Return: What's the projected long-term growth?
- Success Probability (Monte Carlo): What's the chance of meeting your goals?
- 50th Percentile Outcome: The median projection for planning

**For Benchmark Tracking:**
- Tracking Error: How closely do you follow the benchmark?
- Active Share: How different is your portfolio from the benchmark?
- Information Ratio: Are deviations from the benchmark paying off?

**For Sustainability:**
- Temperature Rating: Is the portfolio aligned with climate goals?
- Carbon Intensity: Emissions per $M revenue
- Financed Intensity: Your attributed share of emissions

**Pro tip:** Start with the metrics that align with your primary objective, then use secondary metrics as guardrails.

---

## How do the different analysis tools connect?

The RPC Dashboard tools work together to give a complete picture:

**Portfolio Evaluation** shows your current state:
- Current vs. target allocation
- Holdings and sector exposures
- Drift from target

**Monte Carlo Simulation** projects the future:
- Uses current portfolio as starting point
- Applies Capital Market Assumptions for projections
- Shows probability distribution of outcomes

**Risk Analytics** quantifies the risks:
- Factor exposures explain return drivers
- VaR/CVaR quantify potential losses
- Tracking error measures deviation from benchmark

**Capital Market Assumptions** power the projections:
- Expected returns by asset class
- Volatility estimates
- Correlation matrix

**ESG Impact** adds sustainability dimension:
- Climate alignment metrics
- Social and governance scores
- Framework alignment (PCAF, ISSB, SFDR)

**Workflow example:** Check Portfolio Evaluation to see your current holdings, run Monte Carlo to project outcomes, use Risk Analytics to understand factor exposures, and review ESG to assess sustainability alignment.

---

## What does "confidence level" mean across the dashboard?

Confidence levels appear in several contexts:

**In Risk Analytics (VaR/CVaR):**
- 95% VaR means: "We are 95% confident losses won't exceed this amount"
- Or equivalently: "There's a 5% chance of losing more than this"
- CVaR (Conditional VaR) shows the average loss when you do exceed VaR

**In Monte Carlo Simulations:**
- 5th percentile: 95% of simulations end higher than this (pessimistic)
- 50th percentile: Half of simulations are above, half below (median)
- 95th percentile: Only 5% of simulations end higher (optimistic)

**In ESG Metrics (Confidence Scores):**
- Clarity AI provides data confidence ratings
- Higher confidence = more complete/verified data
- Lower confidence = more estimated/modeled data

**Key insight:** These are all ways of expressing uncertainty. Higher confidence levels give more "cushion" but may appear more conservative.

---

## How often should I rebalance my portfolio?

Rebalancing frequency depends on your strategy and constraints:

**Calendar-based (Quarterly/Annual):**
- Pros: Simple, predictable, lower transaction costs
- Cons: May miss opportunities, allows drift between dates
- Best for: Long-term investors, tax-sensitive accounts

**Threshold-based (When drift exceeds X%):**
- Pros: Reacts to market moves, maintains target allocation
- Cons: Unpredictable timing, may increase turnover
- Best for: Active managers, institutional portfolios

**Hybrid (Calendar + Threshold):**
- Check quarterly, rebalance if drift exceeds threshold
- Combines predictability with responsiveness

**Dashboard usage:** Use Portfolio Evaluation to see current drift from target. If drift exceeds your threshold (commonly 5% absolute or 25% relative), consider rebalancing.

---

## How do I export or share my analysis?

**Current Export Options:**
- Screenshots: Use browser tools or the dashboard export button
- PDF Reports: Available from specific analysis pages
- Data Export: CSV downloads for raw data

**Best Practices:**
- Capture full-page screenshots for client presentations
- Include key metrics in the filename for organization
- Store exports in the UX-UI-database folder structure

**For Client Communication:**
- Lead with the headline metric (success probability, Sharpe ratio, etc.)
- Provide context for what "good" looks like
- Use percentiles rather than absolute numbers when possible

---

*Last updated: January 2026*
