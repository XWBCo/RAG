# Monte Carlo Simulation - Interpretive FAQ

This document provides guidance on interpreting Monte Carlo simulation results in the AlTi Risk & Portfolio Construction Dashboard.

---

## Q: What does the 5th percentile mean in my Monte Carlo simulation?

The 5th percentile represents your **pessimistic but plausible scenario**. Out of all simulated outcomes, 95% were better than this value, and only 5% were worse.

**How to interpret your 5th percentile:**
- This is your "bad luck" scenario - not the worst possible, but reasonably pessimistic
- If your 5th percentile after 20 years shows $1.2M on a $1M starting portfolio, there's a 95% probability you'll have at least $1.2M
- Compare this to your client's minimum required outcome or floor amount

**When to be concerned:**
- 5th percentile falls below the client's minimum acceptable portfolio value
- 5th percentile shows significant capital loss (e.g., below starting amount after many years)
- Large gap between 5th and 50th percentile indicates high outcome uncertainty

**What to discuss with clients:**
- "Even in a pessimistic scenario, your portfolio is projected to reach X"
- "There's only a 5% chance of ending below this amount"
- Consider if the downside is acceptable given their goals and risk tolerance

---

## Q: What does the 50th percentile (median) mean in Monte Carlo?

The 50th percentile is the **median outcome** - half of all simulations ended above this value, half below. This represents the "middle of the road" expectation.

**How to interpret your median:**
- This is your base case planning scenario
- More reliable than average (mean) because it's not skewed by extreme outcomes
- Use this for primary retirement projections and goal planning

**Comparing median to other percentiles:**
- If median is much closer to 95th than 5th percentile, outcomes are skewed positive (good)
- If median is closer to 5th percentile, there's more downside risk than upside potential
- Symmetric distribution (median equidistant from 5th and 95th) suggests balanced risk

---

## Q: What does the 95th percentile mean?

The 95th percentile represents your **optimistic scenario**. Only 5% of simulations produced better results than this.

**How to interpret:**
- Don't plan around this number - it requires exceptional market conditions
- Useful for understanding upside potential
- Gap between 50th and 95th shows how much could be gained in favorable markets

**Client communication:**
- "In the best 5% of scenarios, your portfolio could reach X"
- "This is the upside potential, but we shouldn't count on it"

---

## Q: What does "Probability of Outperforming Inflation" mean?

This metric shows what percentage of simulations ended with your portfolio's real (inflation-adjusted) value higher than the starting amount.

**How to interpret:**
- 80%+ probability: Strong likelihood of maintaining purchasing power
- 60-80%: Moderate confidence, some inflation risk
- Below 60%: Significant risk of losing purchasing power over time

**Why it matters:**
- A portfolio that grows nominally but loses to inflation is effectively shrinking
- Retirees need to outpace inflation to maintain their lifestyle
- This metric accounts for the inflation rate you specified in settings

**What to do if probability is low:**
- Consider higher expected return allocation (more growth assets)
- Reduce planned withdrawals
- Extend the time horizon if possible
- Accept some real value erosion as a tradeoff for lower volatility

---

## Q: What does "Probability of Loss Greater than 50%" mean?

This shows the percentage of simulations where the portfolio lost more than half its value at some point during the projection period.

**How to interpret:**
- Below 5%: Very low probability of catastrophic drawdown
- 5-15%: Moderate tail risk present
- Above 15%: Significant risk of severe losses - reconsider allocation

**Important context:**
- This measures the worst point during the period, not the ending value
- A portfolio might recover from a 50%+ drawdown but the client may not stay the course
- This is crucial for assessing whether the client can emotionally handle the strategy

**Client conversation:**
- "There's an X% chance your portfolio could temporarily drop by half or more"
- "Could you stay invested if you saw your $2M become $1M, even temporarily?"
- Consider if the client would panic-sell during a drawdown

---

## Q: How should I interpret the Monte Carlo line chart?

The line chart shows simulated portfolio paths over time:

**Reading the chart:**
- Grey lines: Individual simulation paths (typically 50 shown out of 1,000)
- Blue line: Median (50th percentile) path
- Teal band: 25th to 75th percentile range (middle 50% of outcomes)
- Dashed line: Inflation benchmark (purchasing power of initial amount)

**What to look for:**
- Do most grey paths stay above the inflation line? (Good)
- How wide is the teal band? (Wider = more uncertainty)
- Do paths generally trend upward or flat/down?
- Are there many paths that dip significantly? (Volatility risk)

---

## Q: How do return and risk assumptions affect my Monte Carlo results?

Your simulation uses expected annual return and volatility (risk) assumptions:

**Higher expected return:**
- Shifts all percentiles upward
- Increases median outcome
- But remember: higher return expectations usually require more risk

**Higher volatility/risk:**
- Widens the gap between 5th and 95th percentiles
- May lower the 5th percentile even if median stays similar
- Creates more uncertainty in outcomes

**Common scenarios to test:**
- Base case: Your standard CMA assumptions
- Conservative: Lower returns, similar or lower volatility
- Stress test: Lower returns AND higher volatility

---

## Q: How does the withdrawal rate affect Monte Carlo results?

Withdrawals (spending) significantly impact portfolio survival:

**Key relationships:**
- Higher withdrawal rate → Lower ending values across all percentiles
- Higher withdrawal rate → Higher probability of running out of money
- Front-loaded withdrawals hurt more than back-loaded (less compounding time)

**The 4% rule context:**
- Traditional 4% rule assumes 30-year horizon with balanced portfolio
- Adjust down for longer horizons or conservative allocations
- Adjust up for shorter horizons or aggressive allocations

**Testing withdrawal scenarios:**
- Try different annual withdrawal amounts
- Compare constant vs. inflation-adjusted withdrawals
- Model one-time large withdrawals (home purchase, etc.)

---

## Q: Why are my three simulations showing different results?

The Monte Carlo app allows up to three parallel simulations with different assumptions:

**Common comparison scenarios:**
1. Current portfolio vs. proposed portfolio
2. Different withdrawal strategies
3. Different risk levels (conservative vs. growth)

**How to compare:**
- Look at the same percentile across simulations (e.g., compare all 5th percentiles)
- Check which scenario has better probability of meeting goals
- Consider the tradeoff: higher median often means lower 5th percentile

**Interpreting the combined summary:**
- Side-by-side percentile comparison shows relative outcomes
- Probability metrics help choose between scenarios
- No scenario is "best" - depends on client's priorities (upside vs. downside protection)

---

## Q: What time horizon should I use for Monte Carlo simulation?

The projection period significantly affects interpretation:

**Short horizon (5-10 years):**
- More uncertainty, percentiles are closer together
- Sequence of returns risk is high
- Good for near-term goals (college funding, home purchase)

**Medium horizon (10-20 years):**
- Returns tend toward expected values
- Better for retirement onset planning
- Still meaningful uncertainty in outcomes

**Long horizon (20-30+ years):**
- Compounding effects dominate
- Percentiles spread wider in dollar terms
- Small assumption changes have big endpoint impacts

**Rule of thumb:**
- Match horizon to the actual goal timeline
- For retirement, model to age 90-95 for longevity risk
- Consider multiple horizons to see how outcomes evolve

---

## Q: How reliable are Monte Carlo simulation results?

Monte Carlo simulations are **planning tools, not predictions**:

**What they do well:**
- Show range of possible outcomes given assumptions
- Quantify uncertainty and risk
- Compare different strategies under same conditions
- Stress-test plans against adverse scenarios

**Limitations to understand:**
- Results depend entirely on input assumptions (garbage in, garbage out)
- Historical returns may not predict future returns
- Models assume markets behave according to statistical distributions
- Black swan events may not be captured

**Best practices:**
- Use conservative assumptions for critical goals
- Update simulations as assumptions or circumstances change
- Treat percentiles as ranges, not precise predictions
- Focus on relative comparisons between scenarios, not absolute numbers
