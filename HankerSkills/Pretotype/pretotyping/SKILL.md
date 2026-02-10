---
name: pretotyping
description: Generate standardized product validation plans using Pretotyping methodology. Takes user's product idea (with optional follow-up questions) and outputs a three-part plan - XYZ hypothesis, localized pretotype implementation steps, and YODA data evaluation guide. Use when users want to validate product ideas, test market demand, or make data-driven go/pivot/stop decisions before investing in development.
---

# Pretotyping Skill V2

Transform product ideas into actionable validation plans using the Pretotyping methodology from "做对产品".

## Core Function

**Input**: User's product idea (any level of detail)
**Output**: Standardized three-part validation plan

## Workflow

### Step 1: Collect Product Idea

Accept user's product idea in any format:
- Simple: "我想做一个AI健身教练"
- Detailed: Complete product description with target users, features, etc.

### Step 2: Gather Missing Information (Max 2 Rounds)

If information is insufficient, ask clarifying questions:

**Round 1 Questions** (ask only if needed):
- 这个产品解决什么问题？
- 目标用户是谁？
- 用户会采取什么行动来使用它？

**Round 2 Questions** (ask only if still needed):
- 你认为有多少比例的目标用户会使用？
- 产品形态是什么？（app/网站/实体产品/新功能等）

**Important**: Don't force users to answer all questions. Generate plan with reasonable assumptions if user provides limited info.

### Step 3: Generate Standardized Output

Use the template in `templates/output_template.md` to create a complete validation plan with three parts:

#### Part 1: XYZ Market Validation Hypothesis (Detailed)

Transform idea into quantifiable hypothesis:
- **X**: Expected conversion rate (with justification)
- **Y**: Target user segment (specific demographics, pain points)
- **Z**: Target action (measurable behavior with skin-in-the-game)
- Validation criteria (sample size, success threshold, timeframe)
- Key risk assumptions

#### Part 2: Pretotype Implementation Plan (Detailed - Priority)

Provide executable, localized validation plan:
- **Recommended technique** (from 7 pretotyping techniques)
- **Step-by-step checklist** (4 phases: Prepare, Build, Reach Users, Collect Data)
- **Localized for China** (WeChat, Xiaohongshu, Douyin, etc.)
- **Resource list** (templates, tools, examples)
- **Cost & time estimate** (realistic breakdown)
- **FAQ** (common problems and solutions)

#### Part 3: YODA Data Evaluation Guide (Concise)

Help users evaluate results with their own data:
- **YODA principle** (Your Own DAta - trust only real behavior)
- **Skin-in-the-game scale** (money > time > effort > words)
- **TRI framework** (Think-Refine-Iterate decision logic)
- **Quick decision tool** (input data → get GO/PIVOT/STOP recommendation)

## Technique Selection Logic

Match product type to appropriate pretotyping technique:

| Product Type | Primary Technique | Secondary |
|--------------|-------------------|-----------|
| SaaS / Web App | Pinocchio (Landing Page) | Fake Door |
| Mobile App | YouTube Prototype | One Feature |
| AI / Automation | Mechanical Turk | Pinocchio |
| Physical Product | Cardboard Prototype | Crowdfunding |
| New Feature (existing product) | Fake Door | One Feature |
| Hardware / IoT | YouTube Prototype | Crowdfunding |

**Selection criteria**:
1. Product complexity
2. Available resources (time, money, skills)
3. Target user accessibility
4. Validation strength needed

## Localization Guidelines

### For China Market

**Platforms**:
- Social: 微信 (WeChat), 小红书 (Xiaohongshu), 抖音 (Douyin)
- Community: 知乎 (Zhihu), 豆瓣 (Douban), V2EX
- E-commerce: 淘宝 (Taobao), 京东 (JD), 拼多多 (Pinduoduo)

**Payment**: 微信支付, 支付宝

**Tools**:
- Analytics: 友盟 (Umeng), 神策 (Sensors Data)
- Forms: 问卷星 (Wenjuanxing), 金数据 (JinShuju)
- Landing pages: 上线了 (Sxl.cn), Strikingly

**Compliance**: Mention ICP filing if needed for websites

## Key Principles

### ✅ DO

1. **Generate complete plan** even with minimal input
2. **Be specific** in implementation steps (exact tools, platforms, costs)
3. **Localize** for user's market (default to China unless specified)
4. **Provide templates** and examples wherever possible
5. **Set realistic expectations** for time and cost

### ❌ DON'T

1. **Don't ask too many questions** (max 2 rounds)
2. **Don't leave placeholders** (fill in reasonable assumptions)
3. **Don't be vague** ("use social media" → specify "小红书, 知乎")
4. **Don't skip cost estimates** (always provide ranges)
5. **Don't forget localization** (tools, platforms, language)

## Example Usage

### Scenario 1: Minimal Input

**User**: "我想做一个帮助职场人学编程的产品"

**Agent**:
1. Ask 1-2 clarifying questions
2. Generate complete plan with assumptions
3. Output all three parts using template

### Scenario 2: Detailed Input

**User**: [Provides complete product description with target users, features, pricing]

**Agent**:
1. Skip clarifying questions
2. Generate complete plan based on provided info
3. Output all three parts using template

### Scenario 3: User Has Test Results

**User**: "我已经测试了2周，有数据了"

**Agent**:
1. Ask for data (exposures, conversions, expected rate)
2. Run `scripts/data_analyzer.py` logic
3. Provide GO/PIVOT/STOP recommendation with next steps

## Resources

### Templates
- `templates/output_template.md` - Standard three-part output format

### Scripts
- `scripts/xyz_hypothesis.py` - Calculate sample size and success criteria
- `scripts/data_analyzer.py` - Analyze test results and recommend decision
- `scripts/decision_matrix.py` - Visualize performance vs target

### References
- `references/techniques.md` - All 7 pretotyping techniques with examples
- `references/case_studies.md` - Real success stories (Dropbox, Zappos, etc.)
- `references/metrics.md` - Metrics design and tracking guide

### Assets
- `assets/templates/landing_page/` - Ready-to-use landing page template

## Output Quality Standards

Every generated plan should:

✅ **Be actionable** - User can start immediately
✅ **Be specific** - Exact tools, platforms, costs mentioned
✅ **Be localized** - Appropriate for user's market
✅ **Be realistic** - Honest about time and cost
✅ **Be complete** - All three parts filled in (no TBD/TODO)

## Common Scenarios

### User unsure about conversion rate

Provide industry benchmarks and suggest conservative estimate (5-10% for most cases)

### User has no budget

Focus on free channels and tools, provide "zero-cost" alternative plan

### User has no technical skills

Recommend no-code tools, provide step-by-step tutorials, suggest Mechanical Turk technique

### User wants to test multiple ideas

Generate separate plan for each, recommend testing sequentially (not parallel)

## Integration with Scripts

While the main output is the markdown plan, you can use scripts for:

1. **XYZ Hypothesis** - Use `xyz_hypothesis.py` logic to calculate sample size
2. **Data Analysis** - When user has results, run `data_analyzer.py` logic
3. **Decision Matrix** - Generate visual framework with `decision_matrix.py`

**Note**: Don't require users to run scripts manually. Integrate the logic into your output.

## Success Metrics

A good validation plan should enable users to:
- Start validation within 3 days
- Complete test within 1-2 weeks
- Spend < ¥1000 (ideally < ¥500)
- Get clear GO/PIVOT/STOP decision

---

**Remember**: The goal is to help users validate ideas quickly and cheaply before investing in full development. Every plan should embody "用一周验证想法，避免一年的弯路".
