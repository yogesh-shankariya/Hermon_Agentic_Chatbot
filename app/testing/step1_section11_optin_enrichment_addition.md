# Step 1 Blueprint Addition — Section 11 Opt-In Enrichment Changes

Add the following content inside **Section 11 — Acquisition and Form Data** of `demo_data_step1_blueprint.md`.

Place it after the existing **Form Question Examples** subsection.

---

## Opt-In Enrichment Fields

Add additional dummy form-answer data to make the client demo more useful, realistic, and easy to understand.

These fields should be stored in:

```text
opt_in_question_answers
```

Do not store these directly on the lead table unless the actual schema already supports it.

Use these additional form questions:

```text
What do you do for work?
What is your employment status?
Which country are you from?
Which city or region are you based in?
What is your main goal?
What is your biggest challenge right now?
How soon do you want to get started?
What is your current experience level?
What budget range are you comfortable with?
Are you the final decision maker?
```

### Controlled Profession / Industry Answers

```text
Business Owner
Employee
Self-employed
Student
Trader / Investor
Sales or Marketing
Technology
Healthcare
Retired
Unemployed
```

### Controlled Employment Status Answers

```text
Full-time
Part-time
Self-employed
Student
Business Owner
Unemployed
Retired
```

### Controlled Country / Region Answers

```text
Netherlands
Belgium
Germany
United Kingdom
Spain
France
Dubai
Amsterdam
Rotterdam
Brussels
Berlin
London
Barcelona
```

Use broad safe demo locations only.

Do not generate:

```text
street addresses
house numbers
postal codes
precise home locations
real personal location data
```

### Controlled Goal Answers

```text
Grow income
Start online business
Improve trading skills
Change career
Build side income
Get financial confidence
```

### Controlled Challenge Answers

```text
No clear plan
Lack of time
Budget concern
Needs partner approval
Not confident yet
Needs more information
```

### Controlled Start Timeline Answers

```text
Immediately
This month
In 1-3 months
Later this year
Not sure yet
```

### Controlled Budget Range Answers

```text
Below €1,000
€1,000-€2,500
€2,500-€5,000
Above €5,000
Not sure yet
```

### Controlled Decision-Maker Answers

```text
Yes, I decide myself
I need partner approval
I need team approval
I need finance approval
Not sure yet
```

### Expected Demo Questions Supported

These fields should support client-facing questions like:

```text
Which profession submitted the most opt-ins?
Which country generated the most submissions?
Which city or region generated the most submissions?
What are the most common challenges?
How many leads are ready to start immediately?
How many leads need partner approval?
Which budget range is most common?
Show opt-ins by current lead status.
Show form answer distribution for budget range.
Show form answer distribution for profession.
```

### Important Limitation

Do not use these fields to claim revenue attribution unless an approved revenue-to-form-answer attribution rule is added later.

Allowed:

```text
Opt-ins by profession
Opt-ins by country
Opt-ins by budget range
Opt-ins by decision-maker status
Current lead status by form answer
```

Avoid unless later explicitly supported:

```text
Revenue by profession
Revenue by country
Revenue by budget range
Revenue by form answer
```

---

# Step 1 Blueprint Addition — Section 16 Validation Changes

Add the following content inside **Section 16 — Validation Requirements** of `demo_data_step1_blueprint.md`.

Place it after the existing relationship/business validation blocks.

---

## Opt-In Enrichment Validation

```text
Profession answers exist for most opt-ins.
Employment-status answers exist for most opt-ins.
Country or region answers exist for most opt-ins.
Goal answers exist for most opt-ins.
Challenge answers exist for most opt-ins.
Budget range answers exist for most opt-ins.
Decision-maker answers exist for most opt-ins.
No precise addresses are generated.
No real personal location data is used.
No revenue attribution is claimed from form answers unless explicitly supported later.
```
