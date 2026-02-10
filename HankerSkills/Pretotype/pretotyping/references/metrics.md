# Metrics Design Guide for Pretotyping

How to design, track, and analyze metrics for your Pretotyping experiments.

---

## Core Principle

> **Track behavior, not opinions**

The only metrics that matter are those that reflect real user actions with real commitment (time, money, effort).

---

## Metric Selection Framework

### 1. Identify Your Core Assumption

Every pretotype tests a hypothesis. Your metrics should directly measure that hypothesis.

**Examples:**
- Hypothesis: "10% of fitness enthusiasts will sign up for AI coaching"
  - **Metric**: Signup conversion rate
  
- Hypothesis: "Users will pay $10/month for this tool"
  - **Metric**: Payment completion rate at $10 price point
  
- Hypothesis: "People will use this daily"
  - **Metric**: Daily active users (DAU)

### 2. Choose Leading Indicators

Don't wait for lagging indicators. Track actions that predict success.

| Lagging (Slow) | Leading (Fast) |
|----------------|----------------|
| Revenue | Signup rate |
| Retention | Repeat visits |
| Referrals | Share clicks |
| Purchases | Add-to-cart rate |

---

## Essential Metrics by Pretotype Type

### Pinocchio (Landing Page)

**Primary Metrics:**
- **Visitor count**: Total exposures
- **Email signup rate**: Conversions / Visitors
- **Click-through rate**: CTA clicks / Visitors

**Secondary Metrics:**
- Time on page
- Scroll depth
- Traffic sources
- Bounce rate

**Success Thresholds:**
- Email signup: > 5% (good), > 10% (excellent)
- CTA click-through: > 3% (good), > 8% (excellent)

**Tracking Implementation:**
```html
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
  
  // Track email signup
  function trackSignup() {
    gtag('event', 'signup', {
      'event_category': 'engagement',
      'event_label': 'email_signup'
    });
  }
</script>
```

---

### Mechanical Turk

**Primary Metrics:**
- **Request volume**: How many people try it
- **Completion rate**: Requests completed / Requests started
- **Repeat usage rate**: Users who come back / Total users

**Secondary Metrics:**
- Time to completion
- User satisfaction (NPS)
- Feature usage patterns

**Success Thresholds:**
- Completion rate: > 60% (good), > 80% (excellent)
- Repeat usage: > 20% (good), > 40% (excellent)

**Tracking Implementation:**
- Log every request with timestamp, user ID
- Track completion status
- Monitor repeat users (same email/ID)

---

### Fake Door

**Primary Metrics:**
- **Click-through rate**: Clicks / Impressions
- **Email capture rate**: Emails / Clicks

**Secondary Metrics:**
- User segment analysis (who clicked?)
- Time of day patterns
- Device type

**Success Thresholds:**
- Click-through: > 10% (good), > 20% (excellent)
- Email capture: > 30% (good), > 50% (excellent)

**Tracking Implementation:**
```javascript
// Track fake door click
document.getElementById('new-feature-btn').addEventListener('click', function() {
  gtag('event', 'fake_door_click', {
    'feature_name': 'ai_assistant',
    'user_id': getCurrentUserId()
  });
  showComingSoonModal();
});
```

---

### YouTube Prototype

**Primary Metrics:**
- **View count**: Total views
- **View-through rate**: Watched >50% / Total views
- **Conversion rate**: Signups / Views

**Secondary Metrics:**
- Engagement rate (likes, comments, shares)
- Traffic sources
- Audience retention graph

**Success Thresholds:**
- View-through rate: > 40% (good), > 60% (excellent)
- Conversion rate: > 3% (good), > 8% (excellent)
- Engagement rate: > 5% (good), > 15% (excellent)

---

### Crowdfunding

**Primary Metrics:**
- **Funding percentage**: Raised / Goal
- **Backer count**: Number of backers
- **Average pledge**: Total raised / Backers

**Secondary Metrics:**
- Conversion rate: Backers / Page visitors
- Pledge tier distribution
- Daily funding velocity
- Referral sources

**Success Thresholds:**
- Funding %: > 100% (success), > 200% (strong validation)
- Conversion rate: > 2% (good), > 5% (excellent)

---

## Statistical Significance

### Minimum Sample Sizes

Don't make decisions on tiny samples. Use these minimums:

| Expected Rate | Minimum Sample Size |
|---------------|---------------------|
| 1% | 1,000 |
| 5% | 400 |
| 10% | 200 |
| 20% | 100 |
| 50% | 50 |

**Formula:**
```
n = (Z² × p × (1-p)) / e²

Where:
- Z = 1.96 (for 95% confidence)
- p = expected conversion rate (as decimal)
- e = margin of error (typically 0.05)
```

### Confidence Intervals

Always report confidence intervals, not just point estimates.

**Example:**
- "Conversion rate: 8.5% (95% CI: 5.2% - 11.8%)"
- This means: We're 95% confident the true rate is between 5.2% and 11.8%

**Interpretation:**
- If your target was 10%, and CI includes 10% → Continue testing
- If your target was 10%, and CI is entirely below 10% → Pivot or stop
- If your target was 10%, and CI is entirely above 10% → Go!

---

## Tracking Implementation

### Google Analytics 4 (Free)

**Setup:**
1. Create GA4 property at analytics.google.com
2. Add tracking code to all pages
3. Set up custom events for key actions

**Key Events to Track:**
```javascript
// Page view (automatic)

// Email signup
gtag('event', 'generate_lead', {
  'currency': 'USD',
  'value': 0
});

// Button click
gtag('event', 'select_content', {
  'content_type': 'button',
  'content_id': 'cta_signup'
});

// Video play
gtag('event', 'video_start', {
  'video_title': 'Product Demo'
});
```

### Simple Custom Tracking

For minimal setup, use a simple backend log:

```python
# track.py
import json
from datetime import datetime

def track_event(event_name, user_id=None, properties=None):
    event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event': event_name,
        'user_id': user_id,
        'properties': properties or {}
    }
    
    with open('events.jsonl', 'a') as f:
        f.write(json.dumps(event) + '\n')
```

---

## Analysis Framework

### 1. Calculate Core Metrics

```python
# Example analysis
total_visitors = 1000
signups = 75
conversions = 8

signup_rate = (signups / total_visitors) * 100  # 7.5%
conversion_rate = (conversions / signups) * 100  # 10.7%
```

### 2. Compare to Hypothesis

```python
expected_rate = 10.0
actual_rate = 7.5
performance = (actual_rate / expected_rate) * 100  # 75%

if performance >= 100:
    decision = "GO"
elif performance >= 50:
    decision = "PIVOT"
else:
    decision = "STOP"
```

### 3. Segment Analysis

Break down by:
- **Traffic source**: Organic, paid, social, referral
- **Device**: Mobile, desktop, tablet
- **Time**: Weekday vs weekend, time of day
- **Geography**: Country, city
- **User type**: New vs returning

**Why:** Often you'll find one segment performs well while others don't.

**Example:**
```
Overall conversion: 5%
├─ Mobile: 3% ❌
├─ Desktop: 8% ✅
└─ Tablet: 4% ❌

Decision: Focus on desktop users
```

---

## Common Pitfalls

### ❌ Vanity Metrics

Metrics that look good but don't predict success:

- Page views (without conversion)
- Social media followers (without engagement)
- Email list size (without open rates)
- App downloads (without usage)

### ❌ Premature Conclusions

- Testing for too short a time (< 1 week)
- Too small sample size (< 100 for most tests)
- Ignoring confidence intervals
- Cherry-picking favorable data

### ❌ Tracking Opinions Instead of Actions

**Bad:**
- "Would you use this?" survey
- "How much would you pay?" question
- "Do you like this?" feedback

**Good:**
- Email signup (commitment of attention)
- Pre-order (commitment of money)
- Waitlist join (commitment of time)

---

## Metric Dashboard Template

Create a simple dashboard to track progress:

```
PRETOTYPE METRICS DASHBOARD
===========================

Hypothesis: At least 10% of fitness enthusiasts will sign up

Test Period: Feb 1-14, 2024 (14 days)
Status: ACTIVE

CORE METRICS
------------
Visitors:        847
Signups:         68
Conversion:      8.0%
Target:          10.0%
Performance:     80% of target

CONFIDENCE
----------
95% CI:          6.1% - 10.2%
Sample size:     Adequate ✓
Statistical sig: Not yet

DECISION
--------
Current:         CONTINUE TESTING
Reason:          CI includes target, need more data
Next milestone:  1,000 visitors

SEGMENTS
--------
Mobile:          6.2% (n=423)
Desktop:         10.1% (n=424) ✓
Organic:         9.5% (n=312) ✓
Paid:            7.1% (n=535)
```

---

## Tools & Resources

### Free Tools
- **Google Analytics 4**: Comprehensive web analytics
- **Plausible**: Privacy-friendly, simple analytics
- **Umami**: Self-hosted, open-source analytics
- **Mixpanel**: Event-based analytics (free tier)

### Paid Tools (Optional)
- **Amplitude**: Advanced product analytics
- **Heap**: Automatic event tracking
- **Hotjar**: Heatmaps and session recordings

### Spreadsheet Template

Use this structure for manual tracking:

| Date | Visitors | Signups | Conversion % | Notes |
|------|----------|---------|--------------|-------|
| 2/1  | 45       | 3       | 6.7%         | Launched |
| 2/2  | 67       | 5       | 7.5%         | Reddit post |
| 2/3  | 89       | 9       | 10.1%        | HN front page |

---

## Next Steps

1. **Define your hypothesis** using XYZ format
2. **Choose 2-3 key metrics** that directly test it
3. **Set up tracking** (GA4 or custom)
4. **Determine success threshold** before launching
5. **Run test** for 1-2 weeks minimum
6. **Analyze results** using the scripts in this skill
7. **Make decision**: Go, Pivot, or Stop
