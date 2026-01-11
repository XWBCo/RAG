# Portfolio Evaluation - Interpretive FAQ

This document provides guidance on interpreting portfolio evaluation and optimization results in the AlTi Risk & Portfolio Construction Dashboard.

---

## Q: What is an efficient frontier and what does mine show?

The efficient frontier is a curve showing the best possible portfolios - those offering the highest expected return for each level of risk.

**How to read your efficient frontier:**
- X-axis: Risk (volatility, standard deviation)
- Y-axis: Expected return
- The curve represents optimal portfolios - you can't do better without taking more risk
- Portfolios below the curve are suboptimal (same risk, less return)

**Key points on the frontier:**
- **Minimum variance point**: Lowest risk portfolio possible
- **Maximum Sharpe ratio point**: Best risk-adjusted return (often marked)
- **Maximum return point**: Highest return, highest risk

**What your frontier tells you:**
- Steep curve = good reward for taking more risk
- Flat curve = diminishing returns from additional risk
- Gap between current portfolio and frontier = potential improvement

---

## Q: What do the different frontiers mean (Core, Core + Private, Unconstrained)?

The app generates multiple frontiers to show optimization under different constraints:

**Core Frontier:**
- Limited to traditional liquid assets (Global Equity, Global Aggregate Bonds)
- Most constrained, most liquid
- Represents what's achievable with simple, low-cost allocation

**Core + Private Frontier:**
- Adds private market investments (private equity, private credit, real assets)
- Typically shows higher returns for same risk level
- Reflects AlTi's full investment universe

**Unconstrained Frontier:**
- No position limits or allocation constraints
- Theoretical maximum efficiency
- May suggest impractical allocations (e.g., 100% in one asset)

**How to use the comparison:**
- Core: "What if we kept it simple?"
- Core + Private: "What's possible with our full toolkit?"
- Unconstrained: "What's theoretically optimal?" (benchmark, not target)

---

## Q: What does the optimal Sharpe ratio portfolio mean?

The optimal Sharpe ratio portfolio (often called the "tangency portfolio") offers the best risk-adjusted return.

**How to interpret:**
- This is the portfolio with the steepest line from the risk-free rate to the frontier
- It maximizes return per unit of risk
- Not necessarily the highest return or lowest risk - it's the best tradeoff

**When to recommend it:**
- Client wants the most efficient use of risk budget
- No strong preference for specific risk level
- Good default starting point for discussions

**When to choose something else:**
- Client has specific risk tolerance (may want left or right of optimal)
- Constraints make optimal impractical
- Client prefers simplicity over optimization

---

## Q: Why does my current portfolio plot below the efficient frontier?

If your portfolio appears below the frontier, it means there's a more efficient allocation available:

**Common reasons:**
1. **Historical allocation**: Built over time without optimization
2. **Constraints**: Tax considerations, client preferences, liquidity needs
3. **Implementation costs**: Actual portfolios have fees and transaction costs
4. **Estimation error**: Frontier is based on estimates that may not hold

**How far below matters:**
- Slightly below: Normal, don't over-optimize
- Significantly below: Worth reviewing allocation

**What to do:**
- Identify the nearest point on the frontier at the same risk level
- Compare allocations to see what changes would improve efficiency
- Weigh improvement against implementation costs and constraints

---

## Q: How do I interpret the asset allocation comparison?

The app compares allocations across different portfolios (benchmark, current, proposed):

**Reading the allocation tables:**
- Grouped by: Stability / Diversified / Growth assets
- Percentages show weight in each asset class
- Colors highlight over/underweight vs. benchmark

**Key comparisons:**
- **Current vs. Benchmark**: Are you taking active bets? Where?
- **Proposed vs. Current**: What changes are recommended?
- **Proposed vs. Benchmark**: How does optimization differ from market?

**What to look for:**
- Large overweights/underweights = active bets, need justification
- Missing asset classes = diversification opportunity
- Similar allocations = may not need to change

---

## Q: What does the projected growth chart show?

The projected growth chart shows expected portfolio value over time (3, 5, 10, 20, 30 years):

**How to read it:**
- Bars show projected value at each time horizon
- Based on expected return assumptions
- Assumes reinvestment, no withdrawals (unless specified)

**Comparing portfolios:**
- Current vs. Proposed growth shows impact of reallocation
- Larger bars = higher expected growth
- Gap between portfolios widens over longer horizons (compounding effect)

**Important caveats:**
- These are expected values, not guaranteed
- Actual results will vary based on market performance
- Use Monte Carlo for range of outcomes, not just point estimate

---

## Q: What do VaR and CVaR metrics mean?

Value at Risk (VaR) and Conditional Value at Risk (CVaR) measure potential losses:

**VaR (Value at Risk):**
- "There's a 95% chance losses won't exceed X%"
- Example: VaR 95% of 15% means only 5% chance of losing more than 15%
- Commonly used risk metric, easy to communicate

**CVaR (Conditional VaR / Expected Shortfall):**
- "If we're in the worst 5%, the average loss is X%"
- More conservative than VaR - shows how bad the bad scenarios are
- Better for tail risk assessment

**How to interpret together:**
- VaR 15%, CVaR 22% means: "95% chance of losing less than 15%, but if worse, expect ~22% loss"
- Large gap between VaR and CVaR = fat tails (extreme events more severe)

**Client communication:**
- VaR is easier to explain as a threshold
- CVaR better captures "how bad could it get"
- Both are based on historical/modeled distributions, not guarantees

---

## Q: How should I use the constraint templates (Standard, Conservative, etc.)?

Constraint templates set limits on allocations during optimization:

**Standard Template:**
- Balanced constraints allowing reasonable flexibility
- Good starting point for most portfolios
- Prevents extreme allocations while allowing optimization

**Conservative Template:**
- Tighter constraints, less deviation from benchmark
- Limits maximum position sizes
- Results in more diversified, less active portfolio

**Aggressive Template:**
- Looser constraints, more concentration allowed
- Permits larger bets on high-conviction assets
- Results may be more volatile

**Custom Constraints:**
- Override minimums/maximums for specific asset classes
- Use when client has specific requirements (e.g., no tobacco, minimum fixed income)

**Choosing a template:**
- Match to client's comfort with deviation from benchmark
- Conservative for risk-averse, Aggressive for return-seeking
- Always review resulting allocation, regardless of template

---

## Q: Why is the optimal allocation different from what I expected?

Optimization can produce surprising results because it considers correlations and risk contributions:

**Common surprises and explanations:**

**"Why so much in X?"**
- Asset may have excellent risk-adjusted returns in the model
- Low correlation with other holdings adds diversification value
- Check if assumption inputs are reasonable

**"Why so little in Y?"**
- High correlation with other holdings (redundant)
- Poor risk-adjusted return in current assumptions
- Better alternatives available

**"The allocation seems too concentrated"**
- Try a more constrained template
- Optimizer finds efficiency but may ignore practical concerns
- Real portfolios need buffer for liquidity, taxes, implementation

**What to do when results seem wrong:**
- Review the input assumptions (garbage in, garbage out)
- Check constraint settings
- Consider if optimizer is finding something you missed vs. being unrealistic

---

## Q: How do current market assumptions affect my optimization?

The Capital Market Assumptions (CMA) drive all optimization results:

**Key inputs from CMA:**
- Expected returns by asset class
- Volatility (risk) by asset class
- Correlations between asset classes

**Impact of different assumptions:**
- Higher expected equity returns → More equity in optimal
- Higher bond volatility → Less benefit from fixed income
- Lower correlations → More diversification benefit

**Scenario testing:**
- Base Case: Standard long-term assumptions
- Mild Recession: Lower returns, higher volatility
- Stagflation: Significantly stressed assumptions

**Best practice:**
- Run optimization under multiple scenarios
- If optimal allocation changes dramatically, current allocation may be sensitive
- Focus on allocations that are robust across scenarios

---

## Q: How do I compare my portfolio to the blended benchmark?

The blended benchmark provides a reference point for evaluation:

**What the benchmark represents:**
- Policy allocation or target asset mix
- Market-cap weighted passive alternative
- "What would you get without active management?"

**Key comparisons:**
- **Return**: Are you above or below benchmark return expectations?
- **Risk**: More or less volatile than benchmark?
- **Sharpe**: Better or worse risk-adjusted return?

**When you're above benchmark:**
- Active bets are adding value (or expected to)
- Higher return may come with higher risk
- Confirm outperformance justifies any additional risk

**When you're below benchmark:**
- Review whether active positions are justified
- Consider moving closer to benchmark
- May be acceptable if other goals are met (tax efficiency, values alignment)

---

## Q: What does "risk allocation" mean in the holdings breakdown?

Risk allocation categorizes holdings by their role in the portfolio:

**Categories:**
- **Stability**: Low volatility, capital preservation (cash, short-term bonds)
- **Diversified**: Moderate risk, diversification benefit (real assets, absolute return)
- **Growth**: Higher risk, return-seeking (equities, private equity)

**How to interpret:**
- Check balance across categories matches client's risk profile
- Conservative clients should have more Stability
- Growth-oriented clients can have more Growth assets

**Imbalance signals:**
- All Growth = too aggressive, vulnerable to drawdowns
- All Stability = may not meet return objectives
- No Diversified = missing middle-ground assets that smooth returns

---

## Q: How do I explain the efficient frontier to clients?

**Simple explanation:**
"This curve shows the best possible combinations of risk and return. You can't get more return without taking more risk, and you can't reduce risk without giving up some return."

**Using the visual:**
- Point to their current portfolio: "You're here"
- Point to the frontier: "These are the best possible portfolios"
- Show the gap: "Moving here would give you the same return with less risk" (or vice versa)

**Avoid jargon:**
- "Risk" instead of "standard deviation" or "volatility"
- "Expected return" or "target return" instead of "arithmetic mean"
- "Best risk-adjusted" instead of "optimal Sharpe ratio"

**Connect to their goals:**
- "Based on your need for stability, I'd suggest this point on the curve"
- "Your growth goals require accepting this level of risk"
- "The proposed portfolio moves you closer to the optimal line"
