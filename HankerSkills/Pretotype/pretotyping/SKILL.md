---
name: pretotyping
description: Guide users through the Pretotyping methodology to validate product ideas before investing significant resources. Use when users want to test product ideas, validate market demand, choose validation techniques, or make go/pivot/stop decisions based on data. Helps with hypothesis formation, technique selection, validation tool creation, and data-driven decision making.
---

# Pretotyping Skill

Validate product ideas quickly and cheaply before building. This skill guides you through the complete Pretotyping process from idea to decision.

## Quick Start

Follow this 5-step process:

1. **Form Hypothesis** → Use `scripts/xyz_hypothesis.py`
2. **Select Technique** → See technique selection guide below
3. **Create Pretotype** → Use templates in `assets/` or follow technique guide
4. **Collect Data** → Track metrics (see `references/metrics.md`)
5. **Analyze & Decide** → Use `scripts/data_analyzer.py` and `scripts/decision_matrix.py`

## Core Workflow

### Step 1: Clarify the Idea

Help user articulate their product hypothesis clearly.

**Questions to ask:**
- What problem does this solve?
- Who is the target user?
- What action do you want users to take?
- What would success look like?

### Step 2: Form XYZ Hypothesis

Use the XYZ hypothesis format: "At least X% of Y (target users) will Z (take action)"

**Run the hypothesis generator:**
```bash
python scripts/xyz_hypothesis.py
```

This will:
- Validate the hypothesis structure
- Calculate required sample size
- Generate success criteria

**Interactive mode** guides user through questions.
**CLI mode** accepts X, Y, Z as arguments for automation.

### Step 3: Select Pretotyping Technique

Based on product type, recommend appropriate technique(s):

| Product Type | Recommended Technique | Reference |
|--------------|----------------------|-----------|
| SaaS / Web App | Pinocchio, Fake Door | [techniques.md](references/techniques.md#2-pinocchio-皮诺曹) |
| Mobile App | YouTube Prototype, One Feature | [techniques.md](references/techniques.md#5-youtube-prototype-youtube原型) |
| AI / Automation | Mechanical Turk | [techniques.md](references/techniques.md#1-mechanical-turk-机械土耳其人) |
| Physical Product | Cardboard Prototype, Crowdfunding | [techniques.md](references/techniques.md#6-cardboard-prototype-纸板原型) |
| New Feature | Fake Door, One Feature | [techniques.md](references/techniques.md#3-fake-door-假门面) |

**For detailed technique guides**, direct user to read [references/techniques.md](references/techniques.md).

**For real-world examples**, direct user to read [references/case_studies.md](references/case_studies.md).

### Step 4: Create the Pretotype

#### For Landing Pages (Pinocchio technique)

Use the template in `assets/templates/landing_page/`:

1. Copy `landing_page/index.html`
2. Replace all `{{PLACEHOLDERS}}` with actual content
3. Add Google Analytics tracking ID
4. Deploy to Netlify/Vercel (see README in template folder)

**Customization help** is in `assets/templates/landing_page/README.md`.

#### For Other Techniques

Guide user through implementation based on selected technique:

- **Mechanical Turk**: Create simple interface, process manually
- **Fake Door**: Add UI element to existing product, track clicks
- **YouTube Prototype**: Script video, create mockups, record demo
- **Cardboard Prototype**: Sketch dimensions, build physical mockup
- **Crowdfunding**: Create campaign page, set funding goal

Refer to [references/techniques.md](references/techniques.md) for detailed implementation steps for each technique.

### Step 5: Define Success Metrics

Help user set up tracking and define success criteria.

**Key questions:**
- What metrics directly test your hypothesis?
- What conversion rate would validate your idea?
- How much traffic/exposure do you need?

**For metrics guidance**, direct user to [references/metrics.md](references/metrics.md).

**Common metrics by technique:**
- Pinocchio: Email signup rate (target: >5%)
- Fake Door: Click-through rate (target: >10%)
- Mechanical Turk: Repeat usage rate (target: >20%)
- YouTube Prototype: View-to-signup ratio (target: >3%)
- Crowdfunding: Funding percentage (target: >100%)

### Step 6: Run the Test

**Duration**: 1-2 weeks minimum
**Sample size**: Use calculator from `xyz_hypothesis.py` output

**During the test:**
- Monitor metrics daily
- Don't make changes mid-test
- Collect qualitative feedback (but prioritize behavior data)

### Step 7: Analyze Results

Once you have sufficient data, use the analysis scripts:

#### Data Analyzer

```bash
python scripts/data_analyzer.py
```

**Interactive mode** asks for:
- Number of exposures
- Number of conversions
- Expected conversion rate
- Test duration

**Output includes:**
- Go/Pivot/Stop recommendation
- Confidence level
- Performance vs target
- Specific next steps

#### Decision Matrix

```bash
python scripts/decision_matrix.py
```

Generates visual decision framework showing:
- Performance zones (Go/Pivot/Stop)
- Your current position
- Confidence assessment
- Statistical significance

### Step 8: Make Decision

Based on analysis results:

**🟢 GO (≥100% of target)**
- Proceed to prototype development
- Consider expanding test to larger audience
- Document what worked

**🟡 PIVOT (50-99% of target)**
- Analyze why conversion is lower
- Interview engaged users
- Adjust value prop, pricing, or audience
- Run new pretotype with changes

**🔴 STOP (<50% of target)**
- Consider stopping or major pivot
- Extract learnings
- Move to different idea or fundamentally different approach

## Common Scenarios

### Scenario: User has vague idea

1. Ask clarifying questions about problem, users, solution
2. Help form specific XYZ hypothesis
3. Run `xyz_hypothesis.py` to structure it
4. Proceed to technique selection

### Scenario: User unsure which technique

1. Ask about product type (SaaS, physical, feature, etc.)
2. Ask about resources (time, money, technical skills)
3. Recommend 1-2 techniques from selection guide
4. Point to relevant sections in `references/techniques.md`

### Scenario: User needs landing page

1. Copy template from `assets/templates/landing_page/`
2. Help customize placeholders
3. Set up Google Analytics
4. Recommend deployment option (Netlify is easiest)

### Scenario: User has test results

1. Run `data_analyzer.py` with their data
2. Run `decision_matrix.py` for visualization
3. Interpret results and recommend next steps
4. If pivot, help identify what to change

### Scenario: User wants examples

Direct to specific case studies in `references/case_studies.md`:
- Dropbox (YouTube Prototype)
- Zappos (Mechanical Turk)
- Buffer (Pinocchio)
- Palm Pilot (Cardboard Prototype)
- Instagram (One Feature)

## Key Principles

### ✅ DO

- **Test behavior, not opinions** - Track actions, not surveys
- **Start simple** - Use cheapest, fastest validation method
- **Set criteria first** - Define success before testing
- **Give it time** - Run for 1-2 weeks minimum
- **Trust the data** - Make decisions based on results, not gut

### ❌ DON'T

- **Don't skip validation** - Even "obvious" ideas need testing
- **Don't over-polish** - Pretotypes should be rough
- **Don't test with friends** - Need real target users
- **Don't ignore negative signals** - Bad data is still data
- **Don't rationalize** - If it's not working, pivot or stop

## Resources

### Scripts
- `scripts/xyz_hypothesis.py` - Generate and validate hypotheses
- `scripts/data_analyzer.py` - Analyze test results, get recommendations
- `scripts/decision_matrix.py` - Visualize decision framework

### References
- `references/techniques.md` - All 7 Pretotyping techniques with examples
- `references/case_studies.md` - Real-world success stories (Dropbox, Zappos, etc.)
- `references/metrics.md` - Metrics design, tracking, and analysis guide

### Templates
- `assets/templates/landing_page/` - Ready-to-use landing page for Pinocchio technique

## Troubleshooting

**"Sample size too small"**
- Continue testing until you reach minimum (from hypothesis generator)
- Consider paid ads to increase traffic
- Extend test duration

**"Results are inconclusive"**
- Check if confidence interval includes target rate
- May need more data
- Consider if you're testing right audience

**"Conversion is zero"**
- Check if tracking is working
- Verify you're reaching target audience
- May indicate fundamental problem with idea

**"Don't know what to change for pivot"**
- Interview users who engaged but didn't convert
- A/B test different value propositions
- Try different audience segment
- Review case studies for inspiration

## Next Steps After Pretotyping

### If validated (GO)
1. Build minimal prototype (not full product yet)
2. Expand test to larger audience
3. Start planning full development
4. Consider raising funding if needed

### If needs adjustment (PIVOT)
1. Identify specific element to change
2. Create new hypothesis
3. Run new pretotype (1-2 weeks)
4. Repeat until validated or stopped

### If not validated (STOP)
1. Document learnings
2. Consider if different approach could work
3. Move to next idea
4. Don't view as failure - saved months/years of wasted effort
