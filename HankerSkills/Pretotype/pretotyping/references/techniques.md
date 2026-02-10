# Pretotyping Techniques Reference

Complete guide to all 7 Pretotyping techniques with implementation details, use cases, and examples.

---

## 1. Mechanical Turk (机械土耳其人)

### What It Is
Manually simulate automated or AI-powered features using human operators behind the scenes.

### When to Use
- Testing AI/ML features before building the technology
- Validating automation workflows
- Complex backend systems that would take months to build

### How to Implement
1. Create the user-facing interface (simple web form, email, chat)
2. Manually process requests behind the scenes
3. Deliver results as if automated
4. Track: request volume, completion rates, user satisfaction

### Example: Zappos
- Founder photographed shoes at local stores
- Listed them online without inventory
- When orders came in, bought shoes and shipped them
- **Result**: Validated online shoe retail before building infrastructure

### Pros
- ✅ Zero technical investment
- ✅ Learn what users actually need
- ✅ Iterate on UX before automation

### Cons
- ❌ Not scalable
- ❌ Labor intensive
- ❌ Can't test performance-critical features

---

## 2. Pinocchio (皮诺曹)

### What It Is
Create a "fake but realistic" product experience - usually a landing page or demo that looks real but doesn't have backend functionality.

### When to Use
- Testing market interest before building
- Validating value proposition and messaging
- A/B testing different product concepts

### How to Implement
1. Create professional landing page describing the product
2. Add email signup or "Get Started" button
3. Track clicks, signups, and engagement
4. (Optional) Show "coming soon" or waitlist message

### Example: Buffer
- Created simple landing page explaining the product
- Added pricing tiers and signup buttons
- Tracked which tier got most interest
- **Result**: Validated pricing model before writing code

### Pros
- ✅ Can be built in 1-2 days
- ✅ Tests messaging and positioning
- ✅ Builds email list for launch

### Cons
- ❌ Doesn't validate actual product usage
- ❌ Can disappoint early users if delayed
- ❌ Only tests initial interest, not retention

---

## 3. Fake Door (假门面)

### What It Is
Add a menu item, button, or feature announcement to an existing product that doesn't actually work yet. Track how many users click it.

### When to Use
- Testing new features in existing products
- Prioritizing feature roadmap
- Validating demand before development

### How to Implement
1. Add UI element for the "new feature"
2. When clicked, show "Coming Soon" message
3. (Optional) Collect email for early access
4. Track click-through rate

### Example: Amazon
- Frequently tests new features with "Coming Soon" badges
- Measures interest before full development
- **Result**: Data-driven feature prioritization

### Pros
- ✅ Minimal development effort
- ✅ Tests with existing user base
- ✅ Clear demand signal

### Cons
- ❌ Can frustrate users if overused
- ❌ Only works with existing products
- ❌ Doesn't test actual usage patterns

---

## 4. One Feature (单一功能版本)

### What It Is
Build only the absolute core feature, stripping away everything else. The most minimal viable product possible.

### When to Use
- When you have multiple feature ideas but unsure which is core
- Testing if core value prop is compelling enough
- Limited development resources

### How to Implement
1. Identify the ONE core value proposition
2. Build only that feature (ignore nice-to-haves)
3. Launch to small audience
4. Measure: usage frequency, retention, willingness to pay

### Example: Instagram
- Started as Burbn (location check-in app with many features)
- Noticed photo-sharing was most used
- Stripped everything except photo filters and sharing
- **Result**: Explosive growth after focusing on one feature

### Pros
- ✅ Fast to build
- ✅ Validates core value
- ✅ Easy to iterate

### Cons
- ❌ Still requires development
- ❌ May seem incomplete to users
- ❌ Hard to know which feature to keep

---

## 5. YouTube Prototype (YouTube原型)

### What It Is
Create a video demonstrating your product concept, showing how it would work and what problems it solves.

### When to Use
- Complex products hard to explain in text
- Physical products or hardware
- Novel interaction paradigms

### How to Implement
1. Script the video (problem → solution → demo)
2. Create mockups or use existing tools to simulate
3. Record 2-5 minute video
4. Share on YouTube, social media, landing page
5. Track: views, engagement, comments, signup rate

### Example: Dropbox
- Created 3-minute demo video showing file syncing
- Posted to Hacker News
- **Result**: Waitlist grew from 5,000 to 75,000 overnight

### Pros
- ✅ Shows complex concepts clearly
- ✅ Shareable and viral potential
- ✅ No actual product needed

### Cons
- ❌ Requires video production skills
- ❌ Doesn't validate actual usage
- ❌ Can set wrong expectations

---

## 6. Cardboard Prototype (纸板原型)

### What It Is
Use cardboard, paper, or other cheap materials to create a physical mockup of your product.

### When to Use
- Physical products or hardware
- Testing form factor and ergonomics
- User interaction patterns

### How to Implement
1. Sketch product dimensions
2. Build mockup with cardboard/foam/paper
3. Carry it with you or give to test users
4. Observe: Do they actually use it? How? When?

### Example: Palm Pilot
- Founder carved wood block to size of planned PDA
- Carried it for weeks, pretending to use it
- Noted when he "needed" to check calendar, take notes
- **Result**: Informed actual product design and features

### Pros
- ✅ Extremely cheap (< $10)
- ✅ Fast iteration (hours, not weeks)
- ✅ Tests real-world usage

### Cons
- ❌ Only for physical products
- ❌ Can't test functionality
- ❌ Limited to form factor testing

---

## 7. Crowdfunding (众筹预售)

### What It Is
Launch a crowdfunding campaign (Kickstarter, Indiegogo) to validate demand and pre-sell your product before building it.

### When to Use
- Physical products with clear concept
- When you need funding anyway
- Testing price sensitivity

### How to Implement
1. Create compelling campaign page (video, images, story)
2. Set funding goal (minimum viable production run)
3. Offer product as reward at target price
4. Launch campaign for 30-60 days
5. Measure: funding %, backer count, average pledge

### Example: Pebble Watch
- Set $100K goal for smartwatch
- Raised $10M+ from 68,000 backers
- **Result**: Validated massive demand + funded production

### Pros
- ✅ Real money commitment (strongest signal)
- ✅ Funds development if successful
- ✅ Builds community pre-launch

### Cons
- ❌ Public failure if unsuccessful
- ❌ Obligation to deliver
- ❌ Requires polished presentation

---

## Technique Selection Guide

| Product Type | Recommended Techniques | Timeframe |
|--------------|------------------------|-----------|
| **SaaS / Web App** | Pinocchio, Fake Door, YouTube Prototype | 3-7 days |
| **Mobile App** | YouTube Prototype, One Feature, Pinocchio | 5-14 days |
| **AI / Automation** | Mechanical Turk, Pinocchio | 7-14 days |
| **Physical Product** | Cardboard Prototype, Crowdfunding, YouTube | 7-30 days |
| **New Feature** | Fake Door, One Feature | 1-3 days |
| **Hardware / IoT** | YouTube Prototype, Cardboard, Crowdfunding | 14-60 days |

## Combining Techniques

Often the best approach is to use multiple techniques in sequence:

1. **Week 1**: YouTube Prototype → Measure interest
2. **Week 2**: Pinocchio Landing Page → Collect emails
3. **Week 3**: Mechanical Turk → Test actual usage
4. **Week 4**: Analyze data → Go/Pivot/Stop decision

## Success Metrics by Technique

| Technique | Key Metrics | Good Threshold |
|-----------|-------------|----------------|
| Mechanical Turk | Completion rate, repeat usage | > 20% repeat |
| Pinocchio | Email signup rate | > 5% |
| Fake Door | Click-through rate | > 10% |
| One Feature | Daily active users, retention | > 40% D7 retention |
| YouTube Prototype | View-to-signup ratio | > 3% |
| Cardboard Prototype | Usage frequency | Daily use |
| Crowdfunding | Funding % achieved | > 100% |

---

## Common Mistakes

### ❌ Making it too polished
- Pretotypes should be rough
- Don't waste time on perfection
- Focus on validating the core assumption

### ❌ Testing with friends/family
- They'll be too nice
- Need real target users
- Pay for ads if needed to reach strangers

### ❌ Ignoring negative signals
- If people don't engage, that's data
- Don't rationalize away bad results
- Pivot or stop quickly

### ❌ Running test too short
- Need at least 1-2 weeks
- Allow time for word-of-mouth
- Weekday vs weekend behavior differs

---

## Next Steps After Pretotyping

### If GO (≥ 100% of target)
1. Build minimal prototype
2. Expand test to larger audience
3. Start planning full development

### If PIVOT (50-99% of target)
1. Interview users who engaged
2. Identify what to change
3. Run new pretotype with adjustments

### If STOP (< 50% of target)
1. Document learnings
2. Consider fundamental pivot
3. Move to different idea
