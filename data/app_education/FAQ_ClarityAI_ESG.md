# Clarity AI ESG Metrics - Interpretive FAQ

This document provides guidance on interpreting Clarity AI ESG metrics in the AlTi Risk & Portfolio Construction Dashboard.

---

## About Clarity AI

### Q: What is Clarity AI?

Clarity AI is a leading sustainability technology company that uses AI and machine learning to provide ESG (Environmental, Social, Governance) data and analytics. Founded in 2017 and headquartered in New York, Clarity AI powers AlTi's Impact Analytics module.

**Key facts:**
- **Coverage**: 70,000+ companies, 360,000+ funds, 198 countries
- **Focus**: Primarily public equities and fixed income; limited coverage of private investments
- **Technology**: AI/ML-powered data collection, NLP, and LLMs for scalable analysis
- **Recognition**: Named a Leader in Forrester Wave™ ESG Data & Analytics (2024), TIME's Top GreenTech Companies (2025)
- **Investors**: BlackRock, SoftBank, Balderton Capital ($335M+ raised)

**How Clarity AI differs from traditional ESG providers:**

| Traditional ESG | Clarity AI |
|----------------|------------|
| Opaque analyst opinions | Transparent, scientifically grounded methodology |
| Manual data collection | AI-powered extraction and validation |
| Periodic updates | Continuous improvement with GenAI and NLP |
| Limited coverage | 70,000+ companies globally |

**What Clarity AI provides in the AlTi dashboard:**
- Environmental metrics (carbon intensity, temperature ratings, emissions)
- Social metrics (gender pay gap, board diversity, labor practices)
- Governance metrics (board independence, anti-bribery, executive compensation)
- Climate scenario analysis and regulatory reporting tools
- Portfolio-level sustainability scoring and benchmarking

**Why this matters for wealth advisors:**
Clarity AI enables advisors to quantify sustainability impact with institutional-grade data, helping clients align investments with values while meeting regulatory disclosure requirements (SFDR, SEC climate rules).

---

## Climate & Environment

### Q: What is Temperature Rating (Scope 1+2) and how do I interpret it?

Temperature Rating Scope 1+2 measures how a company's near-term emissions reduction targets for Scopes 1 and 2 align with global climate goals, specifically the Paris Agreement's 1.5°C target. Lower temperatures indicate stronger climate action.

**How to interpret:**
- Below 1.5°C: Paris-aligned, climate leader
- 1.5°C - 2°C: Well-below 2°C pathway, good progress
- 2°C - 3°C: Moderate ambition, room for improvement
- Above 3°C: Climate laggard, misaligned with Paris Agreement

**Real-world application:**
Screen portfolio companies to identify climate leaders (those aligned with <2°C pathways) versus laggards (>3°C). Use this to engage with underperformers on setting more ambitious near-term reduction targets for their direct operations and energy use.

**Unit:** °C

---

### Q: What is Temperature Rating (Scope 3) and why does it matter?

Temperature Rating Scope 3 measures how a company's near-term emissions reduction targets for Scope 3 align with global climate goals. Lower temperatures indicate stronger climate action across the value chain.

**Why Scope 3 matters:**
- For many companies, Scope 3 represents 80-90% of total emissions
- Shows commitment to influencing suppliers and product lifecycle
- Indicates long-term business model adaptation

**Real-world application:**
Assess value chain climate commitments for companies with significant supply chain or product-use emissions (e.g., consumer goods, automotive). Companies with strong Scope 3 alignment demonstrate supply chain influence and long-term business model adaptation.

**Unit:** °C

---

### Q: What is the Net Zero Target score and what does a high score mean?

Net Zero Target evaluates whether the company has set a net zero greenhouse gas (GHG) emission reduction target and assesses the robustness of the plan to meet that target. Score (0-100) reflects both the existence of the target and the quality of the implementation strategy.

**How to interpret the score:**
- 80-100: Validated science-based targets (e.g., SBTi-approved), clear transition plan
- 60-79: Net zero commitment with interim milestones
- 40-59: Net zero target set but limited detail on implementation
- Below 40: Weak or no net zero commitment

**Real-world application:**
Assess long-term climate strategy credibility. Higher scores indicate not just target-setting but validated science-based targets (e.g., SBTi-approved), interim milestones, and clear transition plans. Essential for evaluating alignment with portfolio-level net-zero commitments and climate transition risk.

**Unit:** Score (0-100)

---

### Q: How do I calculate and interpret Financed Emissions Intensity?

Financed Intensity measures the carbon footprint attributable to your investment based on your ownership share of the company's emissions.

**Components:**
| Variable | Definition |
|----------|------------|
| **Investment** | Dollar amount invested in the company ($) |
| **Company Enterprise Value** | Total economic value of the company ($) |
| **Ownership Share** | Investment ÷ Enterprise Value—your proportional stake in the company |
| **Company Emissions** | Company's total GHG emissions in tonnes CO₂ equivalent (tCO₂e) |
| **Financed Emissions** | Company Emissions × Ownership Share—your attributed share of emissions |

**Formula:**
```
                        Investment ($)
Ownership Share  =  ─────────────────────────────
                    Company Enterprise Value ($)

                           Financed Emissions (tCO₂e)
Financed Intensity  =  ─────────────────────────────────
                            Investment ($M)
```

**Example Calculation:**
```
Investment = $5M | Company enterprise value = $250M | Company emissions = 50,000 tCO₂e (Scope 1+2)

Ownership share = $5M / $250M = 2%
Financed emissions = 2% × 50,000 = 1,000 tCO₂e
Financed Intensity = 1,000 / 5 = 200 tCO₂e/$M invested
```

**Real-world application:**
Calculate your portfolio's carbon footprint for regulatory reporting (e.g., SFDR Principal Adverse Impacts). Aggregate this metric across all holdings to report total financed emissions. Track year-over-year to demonstrate decarbonization progress.

**Unit:** tCO₂e / $M invested

---

### Q: What is Carbon Intensity and how does it differ from Financed Intensity?

These metrics measure emissions differently—one based on company revenue, the other on your investment.

**Components:**
| Variable | Definition |
|----------|------------|
| **Company Emissions** | Total GHG emissions (tCO₂e) for Scope 1+2, Scope 3, or Total |
| **Company Revenue** | Company's total revenue in millions of dollars ($M) |
| **Investment** | Dollar amount you invested in the company ($) |
| **Enterprise Value** | Total economic value of the company ($) |
| **Ownership Share** | Investment ÷ Enterprise Value |
| **Financed Emissions** | Company Emissions × Ownership Share |

**Carbon Intensity Formula:**
```
                       Company Emissions (tCO₂e)
Carbon Intensity  =  ─────────────────────────────
                        Company Revenue ($M)
```
- Measures how efficiently a company generates revenue relative to its emissions
- Use to compare operational efficiency across peers in the same sector

**Financed Intensity Formula:**
```
                        Investment ($)
Ownership Share  =  ─────────────────────────────
                    Company Enterprise Value ($)

                         Financed Emissions (tCO₂e)
Financed Intensity  =  ─────────────────────────────────
                              Investment ($M)
```
- Measures the carbon footprint attributable to your investment
- Use for portfolio carbon reporting (SFDR, PCAF)

**Key difference:**
| Metric | Denominator | Measures |
|--------|-------------|----------|
| Carbon Intensity | Company Revenue | Operational efficiency |
| Financed Intensity | Your Investment | Portfolio carbon footprint |

**Example Calculations:**
```
Carbon Intensity:
  Company emissions = 10,000 tCO₂e (Scope 1+2) | Revenue = $50M
  Carbon Intensity = 10,000 / 50 = 200 tCO₂e/$M revenue

Financed Intensity:
  Company emissions = 10,000 tCO₂e | Investment = $5M | Enterprise value = $250M
  Ownership share = $5M / $250M = 2%
  Financed emissions = 10,000 × 2% = 200 tCO₂e
  Financed Intensity = 200 / 5 = 40 tCO₂e/$M invested
```

**When to use each:**
- **Carbon Intensity**: Compare operational efficiency across peers in same sector
- **Financed Intensity**: Portfolio reporting (PCAF, SFDR Principal Adverse Impacts)

**Unit:** tCO₂e / $M

---

### Q: What are Scope 1, 2, and 3 emissions?

Understanding the three scopes is fundamental to interpreting climate metrics:

**Scope 1 (Direct emissions):**
Emissions from sources your company owns or controls—fleet vehicles, on-site fuel combustion, manufacturing processes.

**Scope 2 (Indirect from energy):**
Indirect emissions from purchased electricity and energy to power operations.

**Scope 3 (Value chain):**
All other indirect emissions across the value chain—suppliers' operations, product use, business travel, employee commutes. Often the largest category but most difficult to measure.

**Why this matters:**
- For manufacturing companies, Scope 1 dominates
- For office-based companies, Scope 2 may be largest
- For consumer products, retail, and technology, Scope 3 often represents 80-90% of total emissions

---

### Q: What is the Environmental Score and how should I use it?

The Environmental Score (0-100) evaluates a company's management of environmental risks across areas such as climate change mitigation and adaptation, natural capital preservation (such as water, biodiversity, and forests), and pollution and waste management.

**How to interpret:**
- 70-100: Strong environmental governance
- 50-69: Moderate environmental management
- Below 50: Weak environmental practices, higher risk

**Real-world application:**
Use as a holistic environmental screening tool for portfolio construction. Companies with scores >70 demonstrate strong environmental governance. Combine with sector-specific metrics (e.g., carbon intensity for energy companies, water recycling for manufacturing) for more nuanced analysis.

**Unit:** Score (0-100)

---

### Q: What does the Water Recycled Ratio tell me?

Water Recycled Ratio measures the proportion of total water withdrawal that is treated and reused for operations, expressed as a percentage. Higher ratios indicate more efficient water management and reduced freshwater dependency.

**How to interpret:**
- Above 50%: Strong water management, operational resilience
- 25-50%: Moderate recycling practices
- Below 25%: High freshwater dependency, potential risk in water-stressed regions

**Real-world application:**
Critical for water-intensive industries (semiconductors, beverages, textiles). Companies with high recycling ratios (>50%) demonstrate operational resilience in water-stressed regions. Use to assess long-term viability in areas facing water scarcity.

**Unit:** % of total water use

---

### Q: What is the Waste Recycling Ratio?

Waste Recycling Ratio measures total recycled and reused waste produced in tonnes divided by total waste produced in tonnes. It indicates circular economy practices and waste management efficiency.

**Real-world application:**
Evaluate circular economy leadership and operational efficiency. Higher ratios indicate better resource management and potential cost savings. Particularly relevant for manufacturing, retail, and packaging companies adapting to extended producer responsibility regulations.

**Unit:** % of total waste

---

## Social Metrics

### Q: What is the Social Score and what does it measure?

The Social Score (0-100) assesses a company's ability to manage risks related to its impact on people, including employees, customers, and communities. This includes labor practices, human rights, product safety, and community relations.

**How to interpret:**
- 70-100: Strong stakeholder management
- 50-69: Moderate social performance
- Below 50: Elevated social risks

**Real-world application:**
Use for holistic social risk assessment in portfolio screening. Companies with scores >70 demonstrate strong stakeholder management. Particularly important for consumer-facing brands where reputational risks from labor practices or product safety can materially impact valuation.

**Unit:** Score (0-100)

---

### Q: How do I interpret the Gender Pay Gap metric?

Gender Pay Gap measures the percentage of remuneration of women to men. A value below 100% indicates that women are, on average, paid less than men for comparable work.

**How to interpret:**
- 95-100%: Near pay parity
- 85-94%: Moderate gap, improvement needed
- Below 85%: Significant gap, reputational and litigation risk

**Real-world application:**
Assess pay equity and potential regulatory risks. Companies with significant gaps (<85%) face reputational risk and potential litigation. Increasingly relevant as pay transparency regulations expand globally. Use to engage with companies on closing gaps and improving disclosure.

**Unit:** % difference

---

### Q: What does Female Board Members percentage tell me about governance?

Female Board Members measures the percentage of female board members, indicating gender diversity in corporate leadership and decision-making.

**Benchmarks:**
- Above 30%: Research suggests better governance outcomes
- 20-30%: Meeting minimum requirements in some jurisdictions
- Below 20%: Laggard, engagement opportunity

**Real-world application:**
Track board diversity and compliance with emerging regulations (e.g., California mandates, EU directives). Research suggests boards with >30% women demonstrate better governance outcomes. Use to identify laggards (<20%) for engagement on diversity improvements.

**Unit:** % of board members

---

### Q: What is the Diversity Targets score?

Diversity Targets evaluates whether the company has set targets or objectives to be achieved on diversity and equal opportunity, and assesses the comprehensiveness and robustness of these commitments. Score (0-100) reflects both the existence of targets and their quality.

**Real-world application:**
Identify companies with credible diversity commitments. Higher scores indicate not just target-setting but measurable goals, clear timelines, and accountability mechanisms. Essential for assessing alignment with stakeholder expectations on DEI and talent management quality.

**Unit:** Score (0-100)

---

## Governance Metrics

### Q: What is the Governance Score and why does it matter?

The Governance Score (0-100) evaluates a company's ability to manage risks related to ethical conduct, leadership structure, transparency, and shareholder rights. This includes board independence, executive compensation, audit practices, and business ethics.

**How to interpret:**
- 70-100: Strong governance, often correlates with better long-term performance
- 50-69: Adequate governance
- Below 50: Warrants deeper due diligence on board structure, shareholder rights, business ethics

**Real-world application:**
Use as a foundation for governance risk assessment. Companies with scores <50 warrant deeper due diligence on board structure, shareholder rights, and business ethics. Strong governance (>70) often correlates with better long-term financial performance and lower operational risk.

**Unit:** Score (0-100)

---

### Q: What's the difference between Non-Executive Board and Independent Board metrics?

**Non-Executive Board:**
Percentage of board members who do not form part of the company's executive management team. Higher percentages indicate greater oversight independence from day-to-day operations.

**Independent Board:**
Percentage of board members classified as "independent," meaning they have no material relationship with the company that could compromise their objectivity. As reported by the company.

**Best practices:**
- Both should be >50%
- Non-executive captures operational separation
- Independent captures financial/relationship independence

**Real-world application:**
Assess board independence and oversight quality. Lower percentages may indicate insufficient checks on management decisions and potential conflicts of interest. Use both metrics together for comprehensive governance assessment.

**Unit:** % of board members

---

### Q: What is the Anti-Bribery Score?

Anti-Bribery Score analyzes incidents that relate to companies paying bribes or kickbacks to government officials or private individuals to obtain business or regulatory advantages. It evaluates ethical conduct and compliance risks.

**Real-world application:**
Screen for governance and ethical risks, particularly for companies operating in high-risk jurisdictions. Past incidents signal weak internal controls and potential future violations. Critical for due diligence and exclusionary screening in compliance-sensitive portfolios.

**Unit:** Score (0-100)

---

## General Interpretation Guidelines

### Q: How is impact measured?

Impact is measured using a combination of scores (0-100) and raw metrics. **Important: not all metrics follow the "higher is better" rule.**

**Higher is better (scores 0-100):**
- Environmental Score, Social Score, Governance Score
- Net Zero Target (80-100 = validated science-based targets)
- Anti-Bribery Score, Diversity Targets Score
- Water Recycled Ratio, Waste Recycling Ratio
- Female Board Members %

**Lower is better (intensity/temperature metrics):**
- Temperature Rating Scope 1+2 (<1.5°C = Paris-aligned leader)
- Temperature Rating Scope 3 (<2°C = strong value chain commitment)
- Carbon Intensity (lower tCO₂e/$M revenue = more efficient)
- Financed Emissions Intensity (lower = smaller carbon footprint per $ invested)

**Closer to 100% is better:**
- Gender Pay Gap (95-100% = near parity; below 85% = significant gap)

**Examples:**
- A company with Temperature Rating 1.2°C is **better** than one with 2.8°C
- A company with Environmental Score 85 is **better** than one with 45
- A company with Carbon Intensity 50 tCO₂e/$M is **better** than one with 500 tCO₂e/$M

---

### Q: How should I interpret Score metrics (0-100)?

Score metrics (0-100) evaluate both existence and robustness. Higher scores indicate not just that a practice exists, but that it's comprehensive, well-structured, and credible.

**Examples:**
- **Net Zero Target**: Assesses both target-setting AND implementation quality
- **Diversity Targets**: Evaluates existence of targets AND measurable goals, timelines, accountability

**General interpretation:**
- 80-100: Best-in-class
- 60-79: Above average
- 40-59: Average/meeting minimum
- Below 40: Below average, improvement needed

---

### Q: What frameworks do Clarity AI metrics align with?

All metrics align with leading ESG and climate frameworks including:

- **PCAF** (Partnership for Carbon Accounting Financials) - for financed emissions
- **ISSB** (International Sustainability Standards Board) - global sustainability disclosure
- **SFDR** (Sustainable Finance Disclosure Regulation) - EU regulatory reporting
- **NZIF** (Net Zero Investment Framework) - climate portfolio alignment
- **SBTi** (Science Based Targets initiative) - emissions reduction targets
- **TNFD** (Taskforce on Nature-related Financial Disclosures) - biodiversity

---

### Q: What are the data limitations I should be aware of?

**Self-reported metrics:**
Some metrics rely on company self-reporting (e.g., Independent Board, Gender Pay Gap). Verify independently for critical decisions.

**Historical incident metrics:**
Others evaluate historical incidents (e.g., Land Use & Biodiversity, Anti-Bribery). Past performance may not predict future conduct.

**Disclosure metrics:**
Still others measure disclosure practices rather than actual performance (e.g., Biodiversity Reduction measures whether companies report on biodiversity, not actual outcomes).

**Recommendation:**
Consider these limitations when making investment decisions. Use multiple metrics together for a more complete picture.

---

*Last updated: January 2026*
