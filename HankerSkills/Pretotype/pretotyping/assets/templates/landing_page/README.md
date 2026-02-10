# Landing Page Template - Customization Guide

## Quick Start

1. Open `index.html`
2. Replace all `{{PLACEHOLDERS}}` with your content
3. Add your Google Analytics tracking ID
4. Deploy to any static hosting (Netlify, Vercel, GitHub Pages)

## Placeholders to Replace

### Product Information
- `{{PRODUCT_NAME}}` - Your product name (e.g., "FitAI Coach")
- `{{TAGLINE}}` - One-line value proposition (e.g., "Your AI-powered fitness companion")
- `{{META_DESCRIPTION}}` - SEO description for search engines

### Features
- `{{FEATURE_1_TITLE}}` - First feature headline
- `{{FEATURE_1_DESCRIPTION}}` - First feature description
- `{{FEATURE_2_TITLE}}` - Second feature headline
- `{{FEATURE_2_DESCRIPTION}}` - Second feature description
- `{{FEATURE_3_TITLE}}` - Third feature headline
- `{{FEATURE_3_DESCRIPTION}}` - Third feature description

### Social Proof
- `{{NUMBER_OF_USERS}}` - Number on waitlist (e.g., "500+")

### Tracking
- `G-XXXXXXXXXX` - Your Google Analytics 4 measurement ID (appears twice)

## Email Collection Options

### Option 1: Google Forms (Easiest)
1. Create a Google Form with email field
2. Get the form's pre-filled link
3. Update the `handleSubmit` function to redirect to that URL

### Option 2: Airtable (Recommended)
```javascript
// In handleSubmit function, replace TODO section with:
fetch('https://api.airtable.com/v0/YOUR_BASE/Signups', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer YOUR_API_KEY',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        fields: {
            Email: email,
            Source: formId,
            Timestamp: new Date().toISOString()
        }
    })
});
```

### Option 3: EmailOctopus / Mailchimp
Use their API to add subscribers directly to your mailing list.

## Deployment

### Netlify (Free, Easiest)
1. Create account at netlify.com
2. Drag and drop the `landing_page` folder
3. Done! You get a URL like `your-product.netlify.app`

### Vercel
```bash
npm install -g vercel
cd landing_page
vercel
```

### GitHub Pages
1. Create GitHub repo
2. Push files
3. Enable GitHub Pages in settings
4. Access at `username.github.io/repo-name`

## Customization Tips

### Change Colors
Edit the CSS gradient in `.hero`:
```css
background: linear-gradient(135deg, #YOUR_COLOR_1 0%, #YOUR_COLOR_2 100%);
```

### Add More Features
Copy a `.feature` div and add to `.feature-grid`

### Change Button Color
Edit `.email-form button` background color

## Tracking Setup

1. Go to analytics.google.com
2. Create new GA4 property
3. Copy measurement ID (starts with G-)
4. Replace `G-XXXXXXXXXX` in the template
5. Deploy and test

## Success Metrics

Track these in Google Analytics:
- **Page views**: Total visitors
- **generate_lead events**: Email signups
- **Conversion rate**: Signups / Visitors

Aim for:
- 5%+ conversion rate = Good validation
- 10%+ conversion rate = Strong validation
