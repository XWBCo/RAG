# Risk Analytics - Interpretive FAQ

This document provides guidance on interpreting risk analytics results in the AlTi Risk & Portfolio Construction Dashboard.

---

## Q: What is tracking error and how do I interpret it?

Tracking error (TE) measures how much a portfolio's returns deviate from its benchmark over time. It's expressed as an annualized percentage.

**How to interpret your tracking error:**
- 0-1%: Very close to benchmark (near-index behavior)
- 1-3%: Moderate active management, controlled deviation
- 3-5%: Significant active bets, meaningful deviation from benchmark
- 5%+: High conviction active management, substantially different from benchmark

**What tracking error tells you:**
- Higher TE means the portfolio behaves differently from the benchmark
- This can be good (outperformance potential) or bad (underperformance risk)
- TE alone doesn't indicate whether deviations are positive or negative

**Client conversation:**
- "Your portfolio has X% tracking error, meaning it will behave differently from the market"
- "This deviation is intentional - it reflects our active positioning in [factors/sectors]"
- "Higher tracking error gives opportunity to outperform but also risk of underperformance"

---

## Q: Why is my tracking error high? What's causing it?

Tracking error is driven by several factors:

**Common causes of high tracking error:**
1. **Sector tilts**: Overweight/underweight in specific sectors vs. benchmark
2. **Factor exposures**: Different beta, style, or size tilts
3. **Concentration**: Fewer holdings = higher security-specific risk
4. **Asset class differences**: Including alternatives not in benchmark

**How to identify the source:**
- Check the Factor Contribution chart to see which factors drive TE
- Review the Security Contribution table for single-stock impacts
- Compare asset class weights to benchmark weights

**When high tracking error is acceptable:**
- Intentional active management with clear investment thesis
- Client understands and accepts the deviation
- Historical risk-adjusted returns justify the active risk

**When to reduce tracking error:**
- Client wants benchmark-like returns with less volatility
- Active bets haven't been rewarded historically
- Portfolio is deviating in unintended ways

---

## Q: What is beta and what does my portfolio's beta mean?

Beta measures how sensitive a portfolio is to market movements. A beta of 1.0 means the portfolio moves in line with the market.

**How to interpret your beta:**
- Beta < 1.0: Less volatile than market (defensive)
- Beta = 1.0: Moves with the market
- Beta > 1.0: More volatile than market (aggressive)

**Examples:**
- Beta 0.8: If market drops 10%, portfolio expected to drop ~8%
- Beta 1.2: If market drops 10%, portfolio expected to drop ~12%

**Growth Beta vs. Defensive Beta:**
- Growth Beta: Sensitivity to equity market/growth factors
- Defensive Beta: Sensitivity to defensive factors (bonds, low-vol stocks)
- High Growth Beta + Low Defensive Beta = aggressive equity-like portfolio
- Low Growth Beta + High Defensive Beta = conservative, bond-like portfolio

**Client implication:**
- High beta clients will see larger swings in both directions
- Low beta provides smoother ride but may lag in bull markets
- Match beta to client's risk tolerance and time horizon

---

## Q: What does "Factor Explained" vs "Idiosyncratic" risk mean?

Portfolio risk breaks down into two components:

**Factor Risk (Systematic):**
- Risk from exposure to common market factors (equity, duration, credit, etc.)
- Can be hedged or adjusted by changing factor exposures
- Typically 60-90% of total risk for diversified portfolios

**Idiosyncratic Risk (Security-Specific):**
- Risk unique to individual holdings
- Not explained by common factors
- Can only be reduced through diversification

**How to interpret your split:**
- 80% factor / 20% idiosyncratic: Well-diversified, factor-driven portfolio
- 60% factor / 40% idiosyncratic: Concentrated bets on specific securities
- High idiosyncratic risk: Either concentrated portfolio OR holdings with unique characteristics

**What to do with this information:**
- If factor risk is too high in one area, adjust allocations
- If idiosyncratic risk is high, consider if concentration is intentional
- Diversification primarily reduces idiosyncratic risk

---

## Q: How do I interpret the risk contribution by security?

The risk contribution table shows how much each holding adds to total portfolio risk.

**Key insights:**
- Contributions should roughly align with weight (unless security is unusually volatile)
- A small position with high contribution = very volatile or highly correlated security
- A large position with low contribution = diversifying holding

**What to look for:**
- **Concentration risk**: Top 5 holdings contributing >50% of risk
- **Unintended risk**: Small positions contributing outsized risk
- **Diversification opportunities**: Similar securities both contributing significant risk

**Example interpretation:**
- "AAPL is 8% of portfolio but 15% of risk" → Higher volatility than average
- "Bond fund is 30% of portfolio but 5% of risk" → Low volatility, provides stability
- "Top 3 stocks contribute 40% of risk" → Concentrated equity risk

---

## Q: What does the Sharpe Ratio tell me?

The Sharpe ratio measures risk-adjusted return: how much return you get per unit of risk taken.

**How to interpret:**
- Sharpe < 0.5: Poor risk-adjusted returns
- Sharpe 0.5-1.0: Acceptable risk-adjusted returns
- Sharpe > 1.0: Good risk-adjusted returns
- Sharpe > 1.5: Excellent (rare for portfolios)

**Comparing portfolio to benchmark:**
- Portfolio Sharpe > Benchmark Sharpe: Adding value through better risk-adjusted returns
- Portfolio Sharpe < Benchmark Sharpe: Taking risk inefficiently

**Limitations:**
- Based on historical data - may not predict future
- Assumes returns are normally distributed (may miss tail risks)
- Can be gamed by strategies that hide risk

**Client conversation:**
- "Your portfolio's Sharpe of X means you're earning Y% return for each 1% of risk"
- "Compared to the benchmark, your portfolio is [more/less] efficient"

---

## Q: What does diversification ratio and diversification benefit mean?

These metrics quantify how much diversification helps reduce portfolio risk.

**Diversification Ratio (DR):**
- Ratio of weighted-average individual volatilities to portfolio volatility
- DR > 1 means diversification is reducing risk (good)
- Higher DR = more diversification benefit
- Typical range: 1.2 to 2.0 for diversified portfolios

**Diversification Benefit %:**
- Percentage reduction in risk from diversification
- 30% benefit means portfolio is 30% less volatile than if holdings were perfectly correlated
- Higher is better

**How to interpret:**
- Low diversification benefit (< 20%): Holdings are highly correlated, moving together
- High diversification benefit (> 40%): True diversification, holdings offset each other

**Improving diversification:**
- Add assets with low correlation to existing holdings
- Avoid clustering in similar sectors or factors
- Consider alternatives, international, or different asset classes

---

## Q: How do I read the factor exposure heatmap?

The factor heatmap shows your portfolio's sensitivity to various risk factors.

**Reading the heatmap:**
- Darker colors = higher exposure (positive or negative)
- Rows = securities, Columns = factors
- Look for patterns across securities

**Key factors to understand:**
- **Equity/Market**: Overall stock market sensitivity
- **Duration**: Sensitivity to interest rate changes
- **Credit**: Exposure to credit spreads
- **Size**: Small vs. large cap tilt
- **Value/Growth**: Style factor exposure
- **Momentum**: Trend-following exposure

**What patterns mean:**
- All securities high on one factor = concentrated factor bet
- Mixed exposures = diversified factor exposure
- Unexpected exposures = may indicate misalignment with investment thesis

---

## Q: What do the historical scenario results mean?

Scenario analysis shows how your portfolio would have performed during past market events.

**Common scenarios analyzed:**
- **GFC (2008-2009)**: Global Financial Crisis - credit and equity crash
- **COVID (2020)**: Sharp drawdown and recovery
- **2022 Rates**: Rising interest rates hurt both stocks and bonds
- **Latest Year**: Most recent 12-month performance

**How to interpret:**
- Compare portfolio loss to benchmark loss in each scenario
- Smaller loss than benchmark = defensive characteristics
- Larger loss than benchmark = aggressive positioning or concentration

**Using scenarios for planning:**
- Ask client: "If 2008 repeated, could you handle a X% decline?"
- Scenarios help illustrate real-world risk beyond statistics
- Past may not predict future, but shows how portfolio would behave in stress

---

## Q: Why do Growth and Defensive sleeves show different tracking error?

Portfolios are often split into Growth and Defensive components to manage risk:

**Growth Sleeve:**
- Higher expected return, higher volatility
- Equity-heavy, more factor exposure
- Typically contributes most of the tracking error

**Defensive Sleeve:**
- Lower return, lower volatility
- Bond-heavy, shorter duration
- Provides stability and income

**Interpreting the split:**
- Growth TE 4%, Defensive TE 1% is typical
- If both have high TE, entire portfolio is active
- If defensive has higher TE than expected, may have unintended risk

**Diversification benefit between sleeves:**
- Low correlation between Growth and Defensive reduces total portfolio TE
- This is the core of traditional asset allocation
- Report shows how much TE is "diversified away" by combining sleeves

---

## Q: What's the difference between Default and Proxied analysis modes?

The app offers two analysis modes for handling securities with limited data:

**Default Mode:**
- Uses only actual historical return data
- More accurate when data exists
- May exclude securities without full history
- Best for: Established portfolios, backtesting

**Proxied Mode:**
- Fills gaps using proxy return series for securities without long history
- Better coverage of all holdings
- Slightly less precise due to approximations
- Best for: New securities, alternative investments, comprehensive analysis

**When to use each:**
- Use Default for precise analysis of liquid, established holdings
- Use Proxied when you need full portfolio coverage
- Compare both if results differ significantly

---

## Q: How should I explain risk analytics to clients?

**Keep it simple:**
- "Tracking error shows how different your portfolio behaves from the market"
- "Beta tells us if your portfolio is more or less aggressive than the market"
- "Diversification benefit shows you're not putting all eggs in one basket"

**Visual aids:**
- Use the cumulative performance chart to show actual behavior
- The scenario analysis makes risk concrete with real examples
- Risk contribution pie chart shows concentration simply

**Connect to their goals:**
- "Your beta of 0.8 means smoother returns, matching your preference for stability"
- "The 3% tracking error reflects our active management seeking to outperform"
- "Your diversification benefit of 35% shows the portfolio is well-balanced"

---

## Q: What is maximum drawdown and how should I use it?

Maximum drawdown measures the largest peak-to-trough decline in portfolio value over a specific period. It answers: "What was the worst loss from any high point?"

**How to interpret:**
- -10% max drawdown: Relatively stable, limited historical losses
- -20% to -30%: Moderate drawdowns, typical for balanced portfolios
- -40% or worse: Significant historical losses, aggressive positioning

**Why it matters:**
- Shows actual worst-case historical experience, not just volatility statistics
- Clients often find drawdowns more intuitive than standard deviation
- Reveals whether the portfolio could survive extreme market stress

**Real-world application:**
- Compare portfolio drawdown to benchmark drawdown during same period
- Ask clients: "Could you stay invested through a X% decline?"
- Lower drawdown than benchmark = more defensive characteristics

**Client conversation:**
- "Your portfolio's maximum drawdown was 25%, versus 35% for the benchmark"
- "This means during the worst period, you lost less than the market"
- "However, past drawdowns don't guarantee future ones - they show risk tolerance needed"

**Pairing with recovery time:**
- Consider how long recovery took
- A 30% drawdown that recovered in 6 months is different from 3 years
- Full picture = depth of loss + time to recover

---

## Q: What is Effective N and what does it tell me about diversification?

Effective N measures the "effective number of holdings" in a portfolio, accounting for concentration. A portfolio with 100 holdings where 90% is in the top 5 has a low Effective N.

**How to calculate (simplified):**
```
Effective N = 1 / Σ(weight²)

Example:
- Equal weight 10 stocks (10% each): Effective N = 10
- 5 stocks at 18% each + 5 at 2% each: Effective N ≈ 5.6
```

**How to interpret:**
- Effective N = Actual holdings: Well-diversified, equal-ish weights
- Effective N << Actual holdings: Concentrated portfolio
- Effective N close to 1: Single-stock-like behavior

**Benchmarks:**
- Effective N > 20: Good diversification for most portfolios
- Effective N 10-20: Moderate concentration
- Effective N < 10: Highly concentrated, equity-like risk

**Why it matters:**
- High Effective N reduces security-specific (idiosyncratic) risk
- Shows true diversification beyond just counting holdings
- Helps identify hidden concentration risk

**Client conversation:**
- "Your portfolio has 50 holdings but an Effective N of 15"
- "This means the risk behaves more like 15 equally-weighted positions"
- "Your top holdings are driving most of the portfolio behavior"

---

## Q: What does the "factor explained" percentage mean?

The "factor explained" percentage shows how much of your portfolio's risk can be attributed to systematic market factors (equity, duration, credit, etc.) versus security-specific factors.

**How to interpret:**
- 80-90% factor explained: Portfolio driven by broad market exposures
- 60-80% factor explained: Mix of systematic and specific risk
- Below 60% factor explained: High security-specific or idiosyncratic risk

**What drives factor explained %:**
- More diversified portfolios → higher factor explained
- Concentrated bets on individual stocks → lower factor explained
- Alternative investments → often lower factor explained

**Example interpretation:**
- "85% of your portfolio's risk is explained by market factors"
- "The remaining 15% comes from security-specific characteristics"
- "Your well-diversified portfolio behaves predictably with the market"

**Why it matters:**
- Factor risk can be managed by adjusting allocations
- Security-specific risk requires diversification to reduce
- Understanding the split helps with risk management strategy

**Client implication:**
- High factor explained = behaves like the market, easier to predict
- Low factor explained = more unique behavior, harder to benchmark
