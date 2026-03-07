"""
FireInsight Resource Library

Article definitions: metadata + full HTML content.
Each article is a dict consumed by /resources and /resources/{slug}.
"""

ARTICLES = [
    {
        "slug":     "neris-101",
        "title":    "NERIS 101: What the Federal Mandate Means for Your Department",
        "category": "NERIS",
        "color":    "#6366F1",
        "bg":       "rgba(99,102,241,.1)",
        "date":     "March 2026",
        "read_time": 5,
        "excerpt":  "The January 2026 deadline has passed. Here's what NERIS is, why it replaced NFIRS, and what your department needs to do right now.",
        "content":  """
<h2>What Is NERIS?</h2>
<p>NERIS — the National Emergency Response Information System — is the new federal standard for emergency incident reporting in the United States. Developed by the Fire Safety Research Institute (FSRI) on behalf of the U.S. Fire Administration, it officially replaced the 30-year-old National Fire Incident Reporting System (NFIRS) as the mandatory reporting framework beginning January 1, 2026.</p>
<p>NERIS is not just an upgrade to NFIRS. It is a ground-up redesign built around modern data standards, geocoding requirements, and the operational realities of today's fire service — including EV fires, wildland-urban interface incidents, and expanded EMS roles.</p>

<h2>Why NFIRS Had to Go</h2>
<p>NFIRS served the fire service for over three decades, but the data it produced had serious limitations:</p>
<ul>
  <li><strong>Outdated incident type codes.</strong> NFIRS used a fixed numeric code system that couldn't accommodate new incident types like EV battery fires, drone incidents, or expanded technical rescue categories.</li>
  <li><strong>No geocoding standard.</strong> NFIRS records often had inconsistent or missing location data, making geographic analysis nearly impossible at scale.</li>
  <li><strong>Weak life safety fields.</strong> Civilian and firefighter injury/fatality data was inconsistently captured, limiting national injury trend analysis.</li>
  <li><strong>Limited interoperability.</strong> Each RMS vendor implemented NFIRS differently, creating data silos that couldn't be meaningfully aggregated nationally.</li>
</ul>
<p>These limitations meant that policymakers, researchers, and grant administrators were working with incomplete national data — and departments were spending significant effort on reports that produced limited analytical value.</p>

<h2>What Changed with NERIS</h2>
<p>NERIS introduces a structured, API-first data model with six mandatory reporting modules:</p>
<ul>
  <li><strong>Core Incident:</strong> Basic incident identification, timestamps, and status</li>
  <li><strong>Location / Geocoding:</strong> Standardized address and GPS coordinates</li>
  <li><strong>Life Safety Outcomes:</strong> Civilian and firefighter injuries and fatalities</li>
  <li><strong>Actions &amp; Tactics:</strong> What was done at the scene</li>
  <li><strong>Fire Module:</strong> Required for all fire incidents — cause, area of origin, construction type</li>
  <li><strong>Aid Classification:</strong> Whether aid was given or received, and from/to whom</li>
</ul>
<p>Critically, NERIS requires geocoded location data for every incident — a major shift from NFIRS, where location accuracy was optional in practice.</p>

<h2>The Compliance Deadline Has Passed</h2>
<p>The federal mandate took effect January 1, 2026. Departments were required to begin submitting incident data in the NERIS format from that date forward. Continued NFIRS submissions are no longer accepted as compliant reporting.</p>
<p>The consequences of non-compliance extend beyond audit risk. FEMA grant programs — including AFG and SAFER — increasingly rely on NERIS data to assess department need. Incomplete or non-compliant data directly weakens your grant applications.</p>

<h2>What Your Department Should Do Now</h2>
<ol>
  <li><strong>Audit your current data.</strong> Run a compliance check against the 6 NERIS mandatory modules to identify which fields are missing.</li>
  <li><strong>Update RMS configuration.</strong> Work with your RMS vendor to enable NERIS field collection. Most major vendors (ESO, FIREHOUSE, ImageTrend) have NERIS modules — but they may not be turned on by default.</li>
  <li><strong>Train your crews.</strong> The biggest source of missing fields is not system configuration — it's crew completion at the point of entry. Dispatch time, arrival time, and cleared time are chronically missed.</li>
  <li><strong>Convert historical data if needed.</strong> If your department is still on NFIRS, use a conversion tool to transform your historical NFIRS exports into NERIS format before your next grant cycle.</li>
</ol>

<div class="article-callout">
  <strong>Key Takeaway:</strong> NERIS compliance is not optional — it is the foundation for grant eligibility, ISO rating evidence, and meaningful operational analysis. Departments that get their data house in order now will have a significant advantage in the next grant cycle.
</div>
"""
    },
    {
        "slug":     "neris-compliance-guide",
        "title":    "The NERIS Compliance Checklist: 6 Mandatory Modules Explained",
        "category": "NERIS",
        "color":    "#6366F1",
        "bg":       "rgba(99,102,241,.1)",
        "date":     "March 2026",
        "read_time": 7,
        "excerpt":  "A field-by-field breakdown of every NERIS mandatory module, the most commonly missed fields, and what's at stake when they're blank.",
        "content":  """
<h2>How NERIS Compliance Is Measured</h2>
<p>NERIS compliance is measured at the field level, not the record level. An incident can be submitted and technically accepted even if mandatory fields are blank — which means departments often believe they are compliant when their data has significant gaps.</p>
<p>Compliance audits examine what percentage of incidents have each mandatory field populated. A field is considered compliant when it is present, non-null, and logically valid (e.g., arrival time is after alarm time).</p>

<h2>Module 1: Core Incident</h2>
<p>This is the foundational module. Every incident requires all of these fields:</p>
<ul>
  <li><strong>Incident ID (neris_id_incident):</strong> The unique identifier assigned by your RMS. Nearly always present if your system is configured correctly.</li>
  <li><strong>Entity ID (neris_id_entity):</strong> Your department's NERIS-assigned identifier. Must be consistent across all records.</li>
  <li><strong>Incident Type:</strong> The NERIS incident category. This drives whether other modules (like the Fire Module) become required.</li>
  <li><strong>Incident Status:</strong> Whether the incident is open, closed, or cancelled. Often missing when records are created but not closed out in the RMS.</li>
  <li><strong>Alarm Time (call_create):</strong> When the call was received. Critical for response time calculations.</li>
  <li><strong>Dispatch Time:</strong> When the unit was dispatched. <em>This is the most commonly missing core field.</em> Many CAD-to-RMS integrations drop this timestamp.</li>
  <li><strong>Arrival Time:</strong> When the first unit arrived on scene.</li>
  <li><strong>Cleared Time:</strong> When the last unit cleared the scene. Often missing for long incidents or when crews forget to notify dispatch.</li>
</ul>

<div class="article-callout warning">
  <strong>Most Common Gap:</strong> Dispatch time is missing in 30–60% of records at departments with manual CAD-to-RMS workflows. Without it, you cannot compute turnout time — a key ISO PPC metric.
</div>

<h2>Module 2: Location / Geocoding</h2>
<ul>
  <li><strong>Latitude &amp; Longitude:</strong> GPS coordinates for the incident location. Required for NERIS — not just for geographic analysis, but for federal reporting aggregation.</li>
  <li><strong>Address:</strong> Street address of the incident. Many RMS systems capture this but don't always geocode it to coordinates automatically.</li>
</ul>
<p>If your RMS doesn't auto-geocode, you may need to enable a geocoding integration or manually verify address data. Incidents without coordinates cannot be used in community risk analysis or ISO coverage mapping.</p>

<h2>Module 3: Life Safety Outcomes</h2>
<p>All incidents must include:</p>
<ul>
  <li><strong>Civilian Injuries</strong> (count, even if zero)</li>
  <li><strong>Civilian Fatalities</strong> (count, even if zero)</li>
  <li><strong>Firefighter Injuries</strong> (count, even if zero)</li>
  <li><strong>Firefighter Fatalities</strong> (count, even if zero)</li>
</ul>
<p>The critical distinction: a zero value is valid. A blank value is non-compliant. Your RMS must require these fields and default them to zero, not leave them null when nothing happened.</p>

<h2>Module 4: Actions &amp; Tactics</h2>
<ul>
  <li><strong>Primary Action Taken:</strong> What the responding unit's primary action was (e.g., "Rescue, remove from harm," "Fire control," "Investigate"). Required for all incidents.</li>
</ul>

<h2>Module 5: Fire Module (Conditional)</h2>
<p>Required for any incident classified as a fire. If your incident type is any variant of structure fire, vehicle fire, brush/grass fire, explosion, or EV battery fire, these fields become mandatory:</p>
<ul>
  <li><strong>Area of Origin:</strong> Where the fire started within the structure or property</li>
  <li><strong>Fire Cause:</strong> The determined cause (accidental, intentional, undetermined)</li>
  <li><strong>Construction Type:</strong> The building construction class (Type I through Type V)</li>
</ul>
<p>These fields are critical for state and federal fire analysis — and for documenting the complexity of incidents in grant applications.</p>

<h2>Module 6: Aid Classification</h2>
<ul>
  <li><strong>Aid Type:</strong> Whether your department gave aid, received aid, or neither. Mutual aid tracking is increasingly important for regional planning and grant justification.</li>
</ul>

<h2>How to Identify Your Gaps</h2>
<p>The fastest way to identify compliance gaps is to run a field-level completion analysis across your recent incident data. Export your last 12 months of incidents and check what percentage of records have each mandatory field populated.</p>
<p>Common findings:</p>
<ul>
  <li>Dispatch time: 40–70% missing at departments without direct CAD integration</li>
  <li>Cleared time: 15–30% missing across all departments</li>
  <li>Life safety fields: Often null (rather than zero) because crews don't complete them on routine calls</li>
  <li>Fire module fields: Missing on 20–40% of fire incidents when the RMS doesn't force completion</li>
</ul>

<div class="article-callout">
  <strong>Practical Fix:</strong> The single highest-impact change most departments can make is requiring dispatch time to flow from CAD automatically — and making life safety fields required (not optional) in the RMS incident completion workflow.
</div>
"""
    },
    {
        "slug":     "iso-ppc-guide",
        "title":    "ISO PPC Ratings Explained: What They Are and How to Improve Yours",
        "category": "ISO",
        "color":    "#14B8A6",
        "bg":       "rgba(20,184,166,.1)",
        "date":     "February 2026",
        "read_time": 6,
        "excerpt":  "Your ISO rating affects homeowner insurance premiums across your entire district. Here's how the PPC score is calculated and what actually moves the needle.",
        "content":  """
<h2>What Is an ISO PPC Rating?</h2>
<p>The Public Protection Classification (PPC) is a 1-to-10 rating assigned by ISO (Insurance Services Office) that measures the quality of a community's fire protection capability. Class 1 is the best; Class 10 means essentially no recognized fire protection.</p>
<p>Insurance companies use PPC ratings to set homeowner and commercial property insurance premiums. A community moving from Class 5 to Class 3 can reduce homeowner fire insurance costs by 10–25% across the entire coverage area. That translates to real dollars for every family in your district — which is why this rating matters to city councils and county commissioners, not just fire chiefs.</p>

<h2>How the Score Is Calculated</h2>
<p>ISO evaluates three areas, weighted as follows:</p>
<ul>
  <li><strong>Fire Department Operations — 50% of score:</strong> Equipment, staffing, training, response times, and deployment capabilities</li>
  <li><strong>Water Supply — 40% of score:</strong> Hydrant availability, water flow rates, water system maintenance</li>
  <li><strong>Emergency Communications — 10% of score:</strong> 911 system, dispatch capability, call handling</li>
</ul>
<p>For most departments, the fire department operations category is the biggest lever — and it's where data quality matters most.</p>

<h2>Response Time Benchmarks ISO Uses</h2>
<p>Within the fire department operations scoring, ISO evaluates response time performance with specific benchmarks:</p>
<ul>
  <li><strong>Dispatch (alerting) time:</strong> 1 minute or less</li>
  <li><strong>Turnout time:</strong> 1 minute or less (career) / 2 minutes or less (volunteer)</li>
  <li><strong>Travel time to first unit:</strong> 4 minutes or less</li>
  <li><strong>Total first-unit response:</strong> 6 minutes or less</li>
</ul>
<p>Critically, ISO evaluates these at the <strong>80th percentile</strong> — not the average. That means 80% of your responses need to meet the travel time benchmark, not just your best ones. Many departments that believe they're performing well are surprised to find their 80th-percentile numbers tell a different story.</p>

<div class="article-callout warning">
  <strong>Common Misconception:</strong> Knowing your average response time is not enough for ISO preparation. You must know your 80th-percentile response time — which requires analyzing your full distribution of response times, not just the mean.
</div>

<h2>Staffing Requirements That Affect Scoring</h2>
<p>ISO evaluates whether departments can deploy an initial attack crew that meets staffing minimums. For structure fires, NFPA 1710 defines a minimum effective response force — and ISO uses similar criteria. Departments that can demonstrate:</p>
<ul>
  <li>First-arriving engine with adequate staffing within 4 minutes</li>
  <li>Full effective response force (typically 15–17 personnel) within 8 minutes</li>
</ul>
<p>...receive higher credit in the operations category. This is why staffing data — and documentation of simultaneous incident response capability — matters for ISO, not just internal planning.</p>

<h2>What Actually Improves Your Rating</h2>
<p>Based on how ISO weights its scoring:</p>
<ol>
  <li><strong>Reduce travel time.</strong> Station placement has the biggest impact. If you're establishing new station locations, ISO credit analysis should inform the decision.</li>
  <li><strong>Improve dispatch time.</strong> Direct CAD alerting (vs. phone-based notifications for volunteer departments) can cut dispatch time by 30–60 seconds — a significant gain at the 80th percentile.</li>
  <li><strong>Document training hours.</strong> ISO awards significant credit for documented training. If your department trains but doesn't log it, you're leaving points on the table.</li>
  <li><strong>Maintain your apparatus.</strong> ISO conducts apparatus inspections. Out-of-service equipment counts against you.</li>
  <li><strong>Fix your data.</strong> ISO auditors review your incident data. Incomplete records (missing timestamps, no dispatch times) directly reduce your credit in the response time category.</li>
</ol>

<h2>Preparing for an ISO Review</h2>
<p>ISO typically schedules re-evaluations every 5–7 years, but departments can request re-evaluations after making significant improvements. Before a review:</p>
<ul>
  <li>Audit your last 3 years of incident data for timestamp completeness</li>
  <li>Calculate your 80th-percentile response time by response type</li>
  <li>Compile training records and ensure they're documented in your RMS or training system</li>
  <li>Verify apparatus maintenance records are current and accessible</li>
  <li>Prepare a response time evidence narrative with supporting incident data</li>
</ul>

<div class="article-callout">
  <strong>Key Takeaway:</strong> The ISO PPC rating is not just a number — it directly affects what your community pays for property insurance. Treating it as a documentation and data quality challenge, rather than just an operational one, is how departments move the needle.
</div>
"""
    },
    {
        "slug":     "afg-grant-guide",
        "title":    "Writing an AFG Grant Narrative That Gets Funded",
        "category": "Grants",
        "color":    "#F59E0B",
        "bg":       "rgba(245,158,11,.1)",
        "date":     "January 2026",
        "read_time": 8,
        "excerpt":  "AFG grants can be worth $500K or more. The departments that win consistently treat the narrative as a data problem, not a writing problem.",
        "content":  """
<h2>What the AFG Program Funds</h2>
<p>The Assistance to Firefighters Grant (AFG) program is administered by FEMA and funds equipment, training, and wellness programs for fire departments nationwide. Individual grants typically range from $20,000 to over $1,000,000 depending on department size and request category. Since 2001, AFG has distributed over $8 billion to fire departments — making it the largest direct federal funding source for local fire services.</p>
<p>Key funding categories include:</p>
<ul>
  <li>Personal protective equipment (PPE) and SCBA</li>
  <li>Firefighting vehicles and apparatus</li>
  <li>Training and certification programs</li>
  <li>Firefighter health, safety, and wellness programs</li>
  <li>Fire prevention and safety activities</li>
</ul>

<h2>Why Most Narratives Fail</h2>
<p>AFG reviewers evaluate thousands of applications. The applications that consistently fail share a common problem: they describe what the department <em>wants</em> without documenting why the department <em>needs</em> it.</p>
<p>Reviewers look for specific evidence of need — and that evidence has to come from your incident data. Statements like "our department responds to many structure fires" score poorly. Statements like "our department responded to 47 structure fires in 2025, representing a 23% increase from 2023, with an average response time of 7 minutes 22 seconds against the NFPA 1710 benchmark of 8 minutes" score well.</p>

<h2>The Four Components of a Strong Narrative</h2>

<h3>1. Statement of Need — Data-Driven</h3>
<p>This is where most departments lose the grant. Your statement of need must:</p>
<ul>
  <li>Quantify your call volume by type over the past 2–3 years</li>
  <li>Show trend direction (increasing or changing call mix)</li>
  <li>Demonstrate how current equipment or staffing limitations affect your ability to respond</li>
  <li>Reference national benchmarks (NFPA 1710, NFPA 1720) where your data shows gaps</li>
</ul>
<p>If you're requesting SCBA upgrades, your narrative needs to show how many IDLH environments your crews entered last year. If you're requesting a new engine, you need data on apparatus age, out-of-service days, and incidents where apparatus limitations affected response.</p>

<h3>2. Project Description — Specific and Measurable</h3>
<p>Describe exactly what you're requesting and why that specific thing solves the documented need. Reviewers are skeptical of vague requests. "We need new PPE" scores poorly. "We are requesting 24 sets of structural firefighting PPE to replace gear averaging 12.3 years of service, exceeding NFPA 1851's 10-year retirement recommendation, for 24 active interior attack firefighters" scores well.</p>

<h3>3. Financial Need — Community Context</h3>
<p>AFG prioritizes departments serving communities with limited tax base. Document:</p>
<ul>
  <li>Your jurisdiction's median household income relative to state average</li>
  <li>Property tax rate and whether you're at the legal cap</li>
  <li>Budget history and what the department has already tried to fund internally</li>
  <li>What percentage of your budget comes from local sources vs. grants</li>
</ul>

<h3>4. Benefits — Measurable Outcomes</h3>
<p>State specifically what will improve as a result of the grant. Tie it back to the data in your statement of need. "This will allow us to replace aging gear" is too vague. "This grant will bring 100% of our active interior crew to NFPA 1851-compliant gear and reduce our annual gear-related out-of-service events from 8 to zero" is specific.</p>

<h2>Using NERIS Data in Your Application</h2>
<p>FEMA reviewers are increasingly familiar with NERIS data. Applications that reference NERIS incident data — including specific field completeness and response time distributions — are viewed as more credible than those relying on anecdotal evidence.</p>
<p>For a typical AFG narrative supporting an apparatus request, pull:</p>
<ul>
  <li>Total incident count by type for the past 3 years</li>
  <li>Average and 90th-percentile response times</li>
  <li>Number of simultaneous incidents (concurrent calls where the apparatus would have been deployed)</li>
  <li>Out-of-service days for the apparatus being replaced (if available)</li>
</ul>

<h2>Timeline and Deadlines</h2>
<p>AFG applications are typically open for 30–45 days in the spring. FEMA announces the opening in late January or early February. Awards are announced on a rolling basis from late summer through early fall.</p>
<p>Start preparing your data analysis 60–90 days before the application window opens. The departments that scramble to pull numbers during the application period consistently produce weaker narratives than those who have been tracking their data throughout the year.</p>

<div class="article-callout">
  <strong>Key Takeaway:</strong> AFG reviewers read hundreds of narratives. The ones that get funded use specific numbers from specific data sources to make a case that is impossible to argue with. Treat the narrative as a data presentation, not a persuasion essay.
</div>
"""
    },
    {
        "slug":     "data-quality-guide",
        "title":    "Data Quality in Fire Reporting: Why Incomplete Records Are Costing You",
        "category": "Data",
        "color":    "#EC4899",
        "bg":       "rgba(236,72,153,.1)",
        "date":     "February 2026",
        "read_time": 5,
        "excerpt":  "Bad data isn't just a compliance problem. It weakens grant applications, undermines ISO ratings, and makes every operational decision harder to justify.",
        "content":  """
<h2>The Hidden Cost of Incomplete Records</h2>
<p>Most fire departments know their data quality isn't perfect. What most don't fully appreciate is how that incompleteness cascades into real operational and financial consequences.</p>
<p>A record with a missing arrival time isn't just one bad data point — it's an incident that can't be used in response time analysis, ISO PPC evidence, grant narrative justification, or NERIS compliance reporting. Multiply that by 15–30% of your records (a typical gap rate for cleared time and dispatch time), and you've lost a significant portion of your analytical foundation.</p>

<h2>The Four Consequences of Poor Data Quality</h2>

<h3>1. Weakened Grant Applications</h3>
<p>Grant reviewers are trained to look for data-backed justification. When your response time analysis has a sample size of 60% of your actual incidents (because 40% are missing timestamps), reviewers notice — or worse, your own analysis is misleading because the missing records aren't random. Long incidents, mutual aid responses, and overnight calls are disproportionately likely to have missing cleared times, which means your average response time appears faster than it actually is.</p>

<h3>2. Reduced ISO PPC Credit</h3>
<p>ISO evaluates response times at the 80th percentile. If your response time data is incomplete, ISO will either use a smaller sample (reducing confidence) or document the data gap as evidence of poor record-keeping — which itself affects your operations score. ISO auditors look at your data discipline as a proxy for your operational discipline.</p>

<h3>3. NERIS Non-Compliance</h3>
<p>The January 2026 NERIS mandate requires specific fields to be present. Missing dispatch times, null life safety fields, and blank primary actions are compliance failures — even if the incident was otherwise fully reported. Non-compliant data affects your department's standing with USFA and, increasingly, with FEMA grant programs that use NERIS data to assess need.</p>

<h3>4. Bad Operational Decisions</h3>
<p>If your data shows average response times of 6 minutes 30 seconds but 25% of your incidents are missing arrival times, you don't actually know your response time. The decisions you make about station coverage, staffing shifts, and apparatus deployment based on that number may be based on a systematically biased sample.</p>

<h2>The Most Commonly Missing Fields</h2>
<p>Across fire departments of all sizes, these are the fields most likely to be incomplete:</p>
<ol>
  <li><strong>Dispatch time</strong> — Missing when CAD doesn't automatically push dispatch timestamps to the RMS</li>
  <li><strong>Cleared time</strong> — Missing when units clear without notifying dispatch, or when dispatch clears units without the RMS capturing it</li>
  <li><strong>Controlled time</strong> — Rarely captured for non-fire incidents; often skipped even for fire incidents</li>
  <li><strong>Life safety fields (injuries/fatalities)</strong> — Left null rather than zero on routine calls where nothing happened</li>
  <li><strong>Primary action taken</strong> — Skipped on EMS and service calls</li>
  <li><strong>Fire module fields (area of origin, cause)</strong> — Often blank when the incident is entered before the investigation is complete, and never updated</li>
</ol>

<h2>How to Fix the Most Common Problems</h2>

<h3>Dispatch Time: Automate It</h3>
<p>The only reliable fix for missing dispatch times is a direct CAD-to-RMS integration that automatically writes the dispatch timestamp when the call is dispatched. Manual entry will always have gaps. If your RMS vendor and CAD vendor don't have an integration, this should be a top priority ask — or a deciding factor in your next system evaluation.</p>

<h3>Cleared Time: Make It Required</h3>
<p>In your RMS configuration, make cleared time a required field before an incident can be closed. If crews can close incidents without entering cleared time, they will — especially on busy shifts. A soft reminder doesn't work; make it a hard stop.</p>

<h3>Life Safety Fields: Default to Zero</h3>
<p>Configure your RMS to default injury and fatality fields to zero rather than null. A zero is valid data. A null is a compliance failure. This is usually a configuration change, not a training change.</p>

<h3>Fire Module: Lock Incomplete Records</h3>
<p>Fire incidents where the fire module is incomplete should be flagged in your RMS and assigned to the incident commander for completion within 24–48 hours. Don't allow fire incidents to go to "closed" status without fire module completion.</p>

<div class="article-callout">
  <strong>Key Takeaway:</strong> Most data quality problems are workflow problems, not training problems. The field that's missing 30% of the time isn't missing because crews don't know what it means — it's missing because the system lets them skip it. Fix the system, not just the training.
</div>
"""
    },
    {
        "slug":     "staffing-justification",
        "title":    "Making the Staffing Case: How to Win the Budget Argument with Data",
        "category": "Operations",
        "color":    "#A855F7",
        "bg":       "rgba(168,85,247,.1)",
        "date":     "March 2026",
        "read_time": 6,
        "excerpt":  "The staffing budget fight is the most common battle in the fire service. Here's how to make a data-driven argument that budget committees can't dismiss.",
        "content":  """
<h2>Why Staffing Arguments Usually Fail</h2>
<p>Every fire chief who has ever stood in front of a city council or county commission asking for additional staffing has heard some version of: "We understand the need, but we can't justify the budget right now." The problem is usually not that the council doesn't believe the chief — it's that the chief hasn't given them data they can defend to their constituents.</p>
<p>Gut-feel staffing arguments fail because they're easy to dismiss. Data-driven staffing arguments are harder to dismiss — and when they're dismissed anyway, the liability exposure for the governing body becomes clear in a way that pure advocacy cannot achieve.</p>

<h2>The Two Arguments That Work</h2>

<h3>Argument 1: Simultaneous Demand</h3>
<p>The most powerful staffing argument is concurrent incident data. When two calls drop simultaneously and one crew has to cover both — or mutual aid has to be called for a call that should be within your department's capability — that is a quantifiable staffing failure.</p>
<p>Analyze your incident data to find:</p>
<ul>
  <li><strong>Maximum concurrent incidents:</strong> The highest number of active calls at any single point in time during the analysis period</li>
  <li><strong>Frequency of 2+ simultaneous calls:</strong> What percentage of your incidents occurred while another call was already active</li>
  <li><strong>Pattern by time of day and day of week:</strong> When simultaneous demand peaks</li>
</ul>
<p>Present these numbers to the board with a specific scenario: "On 47 occasions last year, we had 2 or more active calls simultaneously. On those occasions, one of those calls was responded to by a crew that was already committed. Had either call been a working structure fire, we would have been unable to meet NFPA 1710 staffing requirements for either."</p>

<h3>Argument 2: Response Time Degradation</h3>
<p>The second data argument compares your response times during normal conditions versus busy conditions. If your average response time is 6 minutes 30 seconds when you have one call active, but 8 minutes 45 seconds when you have two or more simultaneous calls — that's response time degradation caused by staffing constraints. And that degradation has a cost you can calculate in terms of NFPA standard deviation and ISO PPC impact.</p>

<h2>NFPA Standards to Reference</h2>
<p>Two NFPA standards define staffing benchmarks that are recognized by ISO, FEMA, and most state oversight bodies:</p>
<ul>
  <li><strong>NFPA 1710:</strong> Applies to career departments. Requires an initial full-alarm assignment of 15 personnel within 8 minutes (including a 1-minute dispatch, 1-minute turnout, and 4-minute travel), with an initial attack crew of 4 on the first-arriving engine.</li>
  <li><strong>NFPA 1720:</strong> Applies to volunteer and combination departments. Defines response time and staffing requirements based on population density, with specific requirements for urban, suburban, rural, and remote service areas.</li>
</ul>
<p>Your staffing request should be anchored to these standards. The question isn't "do we need more people" — it's "on how many calls last year did we fall short of the NFPA minimum effective response force, and what is that risk exposure worth?"</p>

<h2>Building the Board Presentation</h2>
<p>A staffing justification that works in a board presentation has five components:</p>
<ol>
  <li><strong>Current state:</strong> Total incident count, incidents per day, call volume trend</li>
  <li><strong>Simultaneous demand:</strong> How often multiple calls occur simultaneously, maximum concurrent incidents</li>
  <li><strong>Response time impact:</strong> Response time under normal load vs. busy periods, with specific numbers</li>
  <li><strong>Standard comparison:</strong> Where you stand against NFPA 1710/1720 benchmarks</li>
  <li><strong>The ask:</strong> A specific request (additional position, coverage change, mutual aid agreement) tied directly to the gap identified</li>
</ol>
<p>The presentation should answer two questions that every board member will have: "How bad is it?" and "What specifically would fix it?" Vague asks ("we need more people") don't get approved. Specific asks ("we need one additional daytime career position to ensure 4-person first-arriving crews on weekday peak hours, which is when 67% of our simultaneous incidents occur") get discussed seriously.</p>

<h2>The Liability Angle</h2>
<p>When data alone doesn't move the needle, documenting that the board has been informed of the staffing gap — in writing, with specific data — changes the dynamic. Governing bodies that have been formally notified of a staffing deficiency that creates a public safety risk bear a different level of liability exposure than boards that simply didn't know. Chiefs who document their data-driven staffing requests and the board's response are protecting themselves and their departments, not just making an argument.</p>

<div class="article-callout">
  <strong>Key Takeaway:</strong> A staffing argument that a budget committee can't dismiss is one that shows, with specific numbers from your own incident data, exactly how many times last year the department was unable to meet the response standard the community expects — and what that risk exposure looks like going forward.
</div>
"""
    },
    {
        "slug":      "neris-department-ids",
        "title":     "NERIS Department IDs: What They Are and How to Find Yours",
        "category":  "NERIS",
        "color":     "#6366F1",
        "bg":        "rgba(99,102,241,.1)",
        "date":      "March 2026",
        "read_time": 4,
        "excerpt":   "NERIS replaces state-scoped NFIRS FDIDs with countrywide unique department identifiers. Here's what that means for your data, your API credentials, and your grant submissions.",
        "content":   """
<h2>What Is a NERIS Department ID?</h2>
<p>A NERIS Department ID (also called a NERIS Agency ID) is a <strong>countrywide unique identifier</strong> assigned to every fire and emergency services department that reports through NERIS. It replaces the old NFIRS FDID (Fire Department Identifier), which was only unique within a single state.</p>
<p>This distinction matters more than it sounds. Because NFIRS FDIDs were state-scoped, the number "12345" could refer to a different department in Virginia, California, and Texas simultaneously. That made national data aggregation unreliable and created persistent problems in grant data, research datasets, and mutual aid records.</p>
<p>NERIS IDs are globally unique. No two departments in the country share the same NERIS ID, regardless of state or territory.</p>

<div class="article-callout">
<strong>Key difference:</strong> Your NFIRS FDID was assigned by your state. Your NERIS ID is assigned by the national NERIS registry and is unique across all 50 states and territories.
</div>

<h2>What Your NERIS ID Is Used For</h2>
<p>Your NERIS ID is embedded in everything your department does within the NERIS ecosystem:</p>
<ul>
  <li><strong>API authentication</strong> — your NERIS ID is attached to your OAuth2 credentials. Every incident record you submit is tagged with your department's NERIS ID automatically.</li>
  <li><strong>Grant submissions</strong> — FEMA uses your NERIS ID to link your incident data to AFG and SAFER applications. Reviewers can verify your reported call volume and response times directly against NERIS records.</li>
  <li><strong>Mutual aid records</strong> — when your department provides or receives mutual aid, both agencies are identified by NERIS ID in the Aid Classification module.</li>
  <li><strong>National trend analysis</strong> — USFA aggregates incident data by NERIS ID for national reports, resource planning, and research datasets that inform future federal funding priorities.</li>
  <li><strong>ISO PPC evidence</strong> — if you present incident data to support your ISO rating, your NERIS ID anchors the records to your specific department.</li>
</ul>

<h2>How to Find Your Department's NERIS ID</h2>
<p>Your NERIS ID is assigned during department registration in the NERIS portal. There are three ways to find it:</p>
<ol>
  <li><strong>Check your RMS configuration</strong> — if your RMS is already submitting NERIS data, your NERIS ID is in the system configuration, usually under "Agency Settings" or "NERIS Integration."</li>
  <li><strong>Check your NERIS portal credentials</strong> — log in to neris.fsri.org with your department's account. Your agency ID appears in your profile and credential settings.</li>
  <li><strong>Contact your state fire reporting coordinator</strong> — if your department hasn't completed NERIS registration, your state coordinator can help initiate registration and obtain your ID.</li>
</ol>

<h2>NERIS ID vs. NFIRS FDID — The Conversion Problem</h2>
<p>If your department is converting historical NFIRS data to NERIS format, you cannot simply carry over your FDID. The two systems use completely different identifier schemes.</p>
<p>When converting historical NFIRS records:</p>
<ul>
  <li>Replace the FDID in converted records with your NERIS ID in the <code>neris_id_agency</code> field</li>
  <li>Note in your data documentation that converted records used the NFIRS FDID <em>[your state]-[your FDID]</em> prior to conversion</li>
  <li>Do not submit converted records without a valid NERIS ID — the API will reject them</li>
</ul>
<p>FireInsight's NFIRS-to-NERIS converter automatically prompts for your NERIS ID and populates the correct field in converted records.</p>

<h2>What If Your Department Isn't Registered Yet?</h2>
<p>If your department hasn't obtained a NERIS ID, you are not submitting NERIS-compliant data — even if your RMS has a NERIS module installed. Registration is required before any data can be submitted to the national NERIS API.</p>
<p>To register:</p>
<ol>
  <li>Visit neris.fsri.org and create a department account</li>
  <li>Provide your department's legal name, state, county, and jurisdiction type</li>
  <li>Receive your NERIS ID and OAuth2 credentials (Client ID and Client Secret)</li>
  <li>Configure your RMS with the credentials — your vendor's support team can usually complete this in one session</li>
</ol>

<div class="article-callout">
<strong>Bottom line:</strong> Your NERIS ID is the anchor for all of your department's data in the national system. Without it, your incidents aren't tied to your department — they don't exist in NERIS. If you're uncertain whether your department is registered, check with your RMS vendor or state coordinator before your next grant cycle.
</div>
""",
    },
    {
        "slug":      "neris-codes",
        "title":     "Understanding NERIS Incident Type Codes",
        "category":  "NERIS",
        "color":     "#6366F1",
        "bg":        "rgba(99,102,241,.1)",
        "date":      "March 2026",
        "read_time": 6,
        "excerpt":   "NERIS uses a 3-tier hierarchical code system that replaces NFIRS numeric codes. Here's how the structure works, what the major categories contain, and the coding rules that trip departments up most often.",
        "content":   """
<h2>How NERIS Codes Work</h2>
<p>NERIS incident type codes follow a <strong>3-tier hierarchical structure</strong>: Group → Sub-group → Incident Type. Unlike NFIRS, which used a fixed set of numeric codes like "111" for "Structure Fire," NERIS codes are human-readable strings that describe exactly what happened.</p>
<p>The full code for a structure fire with structural involvement looks like this:</p>

<div class="article-callout" style="font-family: 'Courier New', monospace; font-size: 14px;">
FIRE / STRUCTURE_FIRE / STRUCTURAL_INVOLVEMENT_FIRE
</div>

<p>This three-part structure means you always know exactly what you're looking at — no code lookup table required. It also means the system can accommodate new incident types (like EV battery fires or drone incidents) by adding new codes within existing groups, without breaking the entire taxonomy.</p>

<h2>The Core Coding Principle</h2>
<p>Before walking through each group, there's one rule that shapes every coding decision in NERIS:</p>
<p><strong>Code the incident for what actually happened — not the worst case you feared when you dispatched.</strong></p>
<p>Examples of what this means in practice:</p>
<ul>
  <li>A smoke investigation that turned out to be cooking smoke → <code>HAZSIT / INVESTIGATION / SMOKE_INVESTIGATION</code>, not <code>FIRE</code></li>
  <li>A lift assist where the patient didn't require transport → <code>PUBLIC_SERVICE / LIFT_ASSIST</code>, not <code>MEDICAL</code></li>
  <li>A motor vehicle accident with no injuries → <code>HAZSIT / HAZARD_NONCHEM / MOTOR_VEHICLE_COLLISION</code>, not <code>RESCUE</code></li>
  <li>A motor vehicle accident with entrapment → <code>RESCUE / TRANSPORTATION / MOTOR_VEHICLE_EXTRICATION_ENTRAPPED</code></li>
</ul>
<p>The same underlying event codes differently depending on what you actually found. This requires crews to code after the incident is resolved, not at dispatch.</p>

<h2>The Six Major Code Groups</h2>

<h3>FIRE — Fire Incidents</h3>
<p>The FIRE group covers all incidents where combustion was the primary hazard. Sub-groups include structure fires, vehicle fires, wildland fires, and other fires (dumpster, outside, etc.).</p>
<ul>
  <li><code>FIRE / STRUCTURE_FIRE / STRUCTURAL_INVOLVEMENT_FIRE</code> — fire has spread to structural components</li>
  <li><code>FIRE / STRUCTURE_FIRE / CONFINED_FIRE</code> — fire contained to object of origin, no structural involvement</li>
  <li><code>FIRE / VEHICLE_FIRE / CAR_FIRE</code> — passenger vehicle fire</li>
  <li><code>FIRE / VEHICLE_FIRE / ELECTRIC_VEHICLE_FIRE</code> — EV battery or drivetrain fire</li>
  <li><code>FIRE / WILDLAND_FIRE / GRASS_FIRE</code> — grass or brush fire</li>
  <li><code>FIRE / OTHER_FIRE / DUMPSTER_FIRE</code> — trash, dumpster, or outside refuse fire</li>
</ul>

<h3>MEDICAL — Medical Emergencies</h3>
<p>The MEDICAL group covers incidents where the primary problem is a medical condition. It's divided between INJURY (trauma) and ILLNESS (medical condition) sub-groups.</p>
<ul>
  <li><code>MEDICAL / ILLNESS / CARDIAC_ARREST</code> — cardiac arrest requiring resuscitation</li>
  <li><code>MEDICAL / ILLNESS / STROKE_CVA</code> — stroke or cerebrovascular accident</li>
  <li><code>MEDICAL / ILLNESS / RESPIRATORY</code> — respiratory distress</li>
  <li><code>MEDICAL / INJURY / TRAUMATIC_INJURY</code> — trauma from a fall, assault, etc.</li>
  <li><code>MEDICAL / INJURY / MOTOR_VEHICLE_COLLISION</code> — MVC where someone was injured and transported</li>
</ul>

<h3>HAZSIT — Hazardous Situations</h3>
<p>Hazardous situations cover incidents involving chemical hazards, non-chemical hazards, and investigations where a hazard was suspected but not confirmed. This is where most coding confusion occurs.</p>
<ul>
  <li><code>HAZSIT / HAZARD_MATERIAL / GAS_LEAK</code> — confirmed natural gas or LP gas leak</li>
  <li><code>HAZSIT / HAZARD_MATERIAL / FUEL_SPILL</code> — petroleum product spill</li>
  <li><code>HAZSIT / HAZARD_NONCHEM / MOTOR_VEHICLE_COLLISION</code> — MVC with no injuries</li>
  <li><code>HAZSIT / INVESTIGATION / SMOKE_INVESTIGATION</code> — smoke reported, no fire found</li>
  <li><code>HAZSIT / INVESTIGATION / GAS_ODOR</code> — gas odor reported, leak not confirmed</li>
</ul>

<h3>RESCUE — Rescue Operations</h3>
<p>Rescue covers incidents where the primary action was extricating or recovering a person from a life-threatening situation — not a medical emergency per se, but a physical rescue.</p>
<ul>
  <li><code>RESCUE / TRANSPORTATION / MOTOR_VEHICLE_EXTRICATION_ENTRAPPED</code> — occupant trapped and requiring extrication</li>
  <li><code>RESCUE / WATER_RESCUE / SWIFT_WATER</code> — swift water rescue</li>
  <li><code>RESCUE / CONFINED_SPACE / INDUSTRIAL</code> — confined space rescue in industrial setting</li>
  <li><code>RESCUE / HIGH_ANGLE / CLIFF_RESCUE</code> — rope/high angle rescue</li>
</ul>

<h3>PUBLIC_SERVICE — Non-Emergency Responses</h3>
<p>Public service covers calls where the department responded but the incident was not an emergency in the traditional sense — alarms, lift assists, welfare checks, and service calls.</p>
<ul>
  <li><code>PUBLIC_SERVICE / LIFT_ASSIST</code> — patient on floor, department assists but no transport</li>
  <li><code>PUBLIC_SERVICE / ALARMS / SMOKE_ALARM_ACTIVATION</code> — smoke alarm activation, no fire found</li>
  <li><code>PUBLIC_SERVICE / ALARMS / CO_ALARM</code> — carbon monoxide alarm activation</li>
  <li><code>PUBLIC_SERVICE / LOST_PERSON</code> — missing person search</li>
  <li><code>PUBLIC_SERVICE / WEATHER_RESPONSE</code> — storm damage, flooding assistance</li>
  <li><code>PUBLIC_SERVICE / PERSON_IN_DISTRESS</code> — welfare check, person in need of assistance</li>
</ul>

<h3>NO_EMERGENCY — False Alarms and Good Intent</h3>
<p>Every cancelled call, false alarm, and good-intent call must still be reported in NERIS. These records are used to track false alarm trends and assess departmental workload.</p>
<ul>
  <li><code>NO_EMERGENCY / FALSE_ALARM / MALICIOUS</code> — intentional false report</li>
  <li><code>NO_EMERGENCY / FALSE_ALARM / ACCIDENTAL</code> — accidental activation, unintentional</li>
  <li><code>NO_EMERGENCY / GOOD_INTENT / CANCELLED</code> — call cancelled en route</li>
  <li><code>NO_EMERGENCY / GOOD_INTENT / WRONG_LOCATION</code> — responded to incorrect address</li>
</ul>

<h2>Common Coding Mistakes</h2>
<p>These are the coding errors that show up most frequently in NERIS data quality audits:</p>
<ul>
  <li><strong>Using MEDICAL for lift assists</strong> — lift assists with no transport should be <code>PUBLIC_SERVICE / LIFT_ASSIST</code>. Only code MEDICAL if there was a medical condition being treated.</li>
  <li><strong>Using FIRE for smoke investigations</strong> — if you responded to a smoke report and found no fire, it's <code>HAZSIT / INVESTIGATION / SMOKE_INVESTIGATION</code>.</li>
  <li><strong>Using HAZSIT for MVC with entrapment</strong> — if someone was trapped and required extrication, that's <code>RESCUE</code>, not <code>HAZSIT</code>.</li>
  <li><strong>Leaving cancelled calls out</strong> — all calls, including cancellations, must be reported. Use <code>NO_EMERGENCY / GOOD_INTENT / CANCELLED</code>.</li>
  <li><strong>Coding at dispatch, not resolution</strong> — the incident type should reflect what you found, not what dispatch thought it might be.</li>
</ul>

<div class="article-callout">
<strong>Practical tip:</strong> Build a one-page coding reference card for your most common incident types and post it at each station. The majority of your call volume — structure fires, MVCs, medical calls, alarm activations — will be covered by 10-15 codes. Once crews know those cold, coding accuracy improves dramatically.
</div>
""",
    },
    {
        "slug":      "neris-faq",
        "title":     "NERIS FAQ: Everything Fire Departments Are Asking Right Now",
        "category":  "NERIS",
        "color":     "#6366F1",
        "bg":        "rgba(99,102,241,.1)",
        "date":      "March 2026",
        "read_time": 10,
        "excerpt":   "A plain-language answer to the 20 most common questions from chiefs, data officers, and firefighters about the NERIS transition — with no bureaucratic runaround.",
        "content":   """
<h2>The Basics</h2>

<h3>What is NERIS?</h3>
<p>NERIS stands for the National Emergency Response Information System. It is the new federal standard for emergency incident data reporting, developed by the Fire Safety Research Institute (FSRI) and the U.S. Fire Administration (USFA). It replaced NFIRS effective January 1, 2026.</p>

<h3>Why did NFIRS get replaced?</h3>
<p>NFIRS was designed in the 1970s and patched repeatedly for 30 years. Its incident type codes couldn't handle EV fires, wildland-urban interface incidents, or modern EMS roles. Location data was inconsistent. Life safety fields were optional in practice. NERIS is a clean rebuild with modern data standards, mandatory geocoding, and an API-first architecture that allows real interoperability between departments and RMS vendors.</p>

<h3>Is NERIS reporting actually mandatory?</h3>
<p>Yes. The federal mandate took effect January 1, 2026. Continued NFIRS-only submissions are no longer accepted as compliant. Departments that receive federal funding — including AFG and SAFER grants — are expected to be reporting in NERIS format.</p>

<h3>What agency oversees NERIS compliance?</h3>
<p>The U.S. Fire Administration (USFA), a division of FEMA, administers NERIS. The technical infrastructure is maintained by FSRI. Grant program compliance is enforced through standard FEMA grant reporting requirements.</p>

<div class="article-callout">
<strong>Bottom line:</strong> If your department applies for federal grants or receives USFA funding, NERIS compliance is not optional. Non-compliant data directly weakens your grant applications and may disqualify future submissions.
</div>

<h2>Reporting Requirements</h2>

<h3>What are the six mandatory NERIS modules?</h3>
<p>Every incident must include data from these six modules:</p>
<ol>
  <li><strong>Core Incident</strong> — Incident ID, incident type, alarm time, dispatch time, arrival time, cleared time, and incident status</li>
  <li><strong>Location / Geocoding</strong> — Street address, city, state, and GPS coordinates (lat/lon required)</li>
  <li><strong>Life Safety Outcomes</strong> — Civilian fatalities, civilian injuries, firefighter fatalities, firefighter injuries</li>
  <li><strong>Actions &amp; Tactics</strong> — Primary action taken at the scene</li>
  <li><strong>Fire Module</strong> — Required for all fire incidents: area of origin, heat source, construction type</li>
  <li><strong>Aid Classification</strong> — Whether mutual aid was given or received, and to/from which agency</li>
</ol>

<h3>Do I have to report every single incident?</h3>
<p>Yes. All emergency incidents must be reported — not just fires. This includes EMS responses, hazmat calls, technical rescue, service calls, and good-intent calls. The threshold is the same as NFIRS was in theory, but NERIS enforcement is expected to be more consistent.</p>

<h3>What's the deadline for submitting each incident?</h3>
<p>NERIS does not specify a hard per-incident deadline the way NFIRS did at the state level. However, best practice is submission within 30 days of the incident. Many state fire marshals are setting tighter internal deadlines. Check with your state fire reporting program for local requirements.</p>

<h3>Does NERIS cover EMS incidents?</h3>
<p>Yes. EMS incidents are reportable under NERIS using the core incident and life safety outcome modules. The EMS-specific module is under development and is expected to be finalized in 2026. In the interim, departments should report EMS incidents with available fields populated.</p>

<h3>What about wildland fires?</h3>
<p>Wildland and wildland-urban interface (WUI) incidents are reportable under NERIS. There is a wildland fire supplemental module that captures acres burned, fire behavior, and suppression resource data. This module is particularly important for departments in wildland interface areas seeking federal wildfire mitigation funding.</p>

<div class="article-callout">
<strong>Key insight:</strong> The most commonly missed mandatory fields in real-world NERIS audits are: GPS coordinates (location module), dispatch time and cleared time (core incident), and primary action taken (actions &amp; tactics). These three gaps account for the majority of compliance failures we see in practice.
</div>

<h2>Technology &amp; Your RMS</h2>

<h3>Does my RMS support NERIS?</h3>
<p>The major RMS vendors have all released or announced NERIS compatibility modules:</p>
<ul>
  <li><strong>ESO</strong> — NERIS export available in current versions</li>
  <li><strong>FIREHOUSE Software</strong> — NERIS module available via update</li>
  <li><strong>ImageTrend</strong> — NERIS support included in their Elite platform</li>
  <li><strong>Emergency Reporting (ER)</strong> — NERIS export in development/available</li>
  <li><strong>Tablet Command / other CAD systems</strong> — varies; contact your vendor</li>
</ul>
<p>Important: having a NERIS module does not mean it is turned on or configured correctly. You need to verify with your vendor that the NERIS fields are being collected and exported in the correct format.</p>

<h3>What if my RMS doesn't support NERIS yet?</h3>
<p>Contact your vendor immediately. If your vendor cannot commit to a NERIS-compliant update within your budget cycle, you have two options: use a third-party conversion tool to transform your existing data exports into NERIS format, or consider switching RMS vendors. FEMA grant programs are unlikely to be sympathetic to "our vendor doesn't support it" as a long-term excuse.</p>

<h3>Can I still submit if I'm on NFIRS?</h3>
<p>You can use a conversion tool to map NFIRS fields to NERIS fields for historical data. However, NFIRS lacks several NERIS mandatory fields — particularly GPS coordinates, dispatch time precision, and some life safety outcome fields. Converted records will have known gaps. You cannot achieve full NERIS compliance from NFIRS data alone; you need to update your collection process going forward.</p>

<h3>What is the NERIS API?</h3>
<p>NERIS uses an API-first architecture. Departments and RMS vendors submit incident data via a REST API rather than file uploads. The NERIS API uses OAuth2 authentication with a Client ID and Client Secret. Your RMS vendor should handle API submission automatically. If you are submitting directly, you will need credentials from the USFA/FSRI portal.</p>

<h2>Grants &amp; Consequences</h2>

<h3>How does NERIS compliance affect AFG and SAFER grants?</h3>
<p>FEMA's AFG and SAFER grant programs increasingly rely on NERIS data to assess applicant need. Reviewers look at incident volume, response times, staffing levels relative to call volume, and community risk — all of which come from NERIS data. A department with incomplete or non-compliant NERIS data will have weaker evidence for need-based scoring criteria. This directly affects your competitive score.</p>

<h3>Could non-compliance disqualify our department from grants?</h3>
<p>Outright disqualification for non-compliance is not yet the standard, but the direction is clear. Grant guidance for 2026 and beyond explicitly references NERIS data quality as an evaluation factor. Departments that cannot demonstrate complete incident data are at a competitive disadvantage, and future grant cycles are expected to harden this requirement.</p>

<h3>Does NERIS affect our ISO PPC rating?</h3>
<p>Not directly — ISO's Public Protection Classification system has its own data collection process and does not yet formally incorporate NERIS. However, ISO evaluates response time performance, and the most defensible evidence for your response time record is your incident data. NERIS data quality directly affects the reliability of the response time evidence you can present during an ISO evaluation.</p>

<h2>Practical Questions</h2>

<h3>How do I know if our NERIS data is actually compliant?</h3>
<p>Run a compliance check against the six mandatory module fields for a sample of your recent incidents. For each incident, verify that Core Incident (alarm, dispatch, arrival, cleared times + incident type), Location (address + GPS coordinates), Life Safety Outcomes (all four injury/fatality fields present, even if zero), Actions &amp; Tactics (primary action), Fire Module (for fire incidents), and Aid Classification fields are populated. FireInsight's compliance checker automates this audit against your incident export.</p>

<h3>What are the most common NERIS data quality problems?</h3>
<ul>
  <li><strong>Missing GPS coordinates</strong> — The most common gap. Many departments collect address but not lat/lon.</li>
  <li><strong>Incomplete timestamps</strong> — Dispatch time and cleared time are frequently missing in records where the call was handled quickly or the crew forgot to update status.</li>
  <li><strong>No primary action recorded</strong> — The actions &amp; tactics module is often left blank when crews complete the report quickly.</li>
  <li><strong>Life safety fields skipped</strong> — Departments assume "no injuries = skip the field," but NERIS requires explicit zeros.</li>
  <li><strong>Fire module missing on structure fires</strong> — Area of origin and heat source are often incomplete on fire incidents.</li>
</ul>

<h3>How do we get crews to fill out records completely?</h3>
<p>Training alone is rarely enough. The most effective approach combines three things: (1) configure your RMS to require mandatory fields before submission — make incomplete records un-submissible, (2) run a monthly data quality report and share it with company officers so crews see the gaps, and (3) tie completion rates to performance feedback rather than treating it as an IT problem. Crew-level ownership of record quality is the single biggest driver of improvement.</p>

<h3>Is there a NERIS education program for firefighters?</h3>
<p>FSRI and USFA have published guidance documentation and training materials on the NERIS portal. Many state fire training organizations are incorporating NERIS record-keeping into their officer development curricula. For a practical starting point, the FireInsight resource library covers the mandatory modules, common gaps, and actionable fixes in language that works for company officers as well as data administrators.</p>

<div class="article-callout">
<strong>Where to start:</strong> If you are unsure where your department stands, run a quick compliance audit on your last 90 days of incident data. Look at completeness rates for the six mandatory modules. Identify the two or three fields with the lowest completion rates. Fix those first — typically GPS coordinates, cleared time, and primary action — and you will capture the majority of the compliance improvement available.
</div>
""",
    },
]


def get_article(slug: str) -> dict | None:
    return next((a for a in ARTICLES if a["slug"] == slug), None)
