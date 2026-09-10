# HireAssist — Project Proposal

*Software Architecture — Term Project*

> **Status:** Draft 2 — Project Description and Use Cases complete.
> Functional Requirements, Non-functional Requirements and ADRs pending.

---

## Project Name

**HireAssist** — an AI-assisted hiring-support layer for companies that receive more
applications than they can screen carefully and interview well.

> HireAssist is **not** a job board, **not** a job-application platform, and **not** another
> applicant-tracking system. It is an *assistant layer* that plugs into the hiring channels a
> company already uses and supplies the judgement capacity it lacks — screening every resume
> with a stated reason, preparing interview questions grounded in the specific resume and role,
> re-matching the existing talent pool, and keeping candidate data compliant.
>
> The human still decides. HireAssist makes sure they are deciding on evidence they actually
> had time to look at.

---

## Group Members

| # | Student ID | Name | Nickname |
|---|---|---|---|
| 1 | 6772055221 | Patiphon Puntusin | Me |
| 2 | 6872036421 | Thanabul Parodom | Tim |
| 3 | 6870406621 | Thanwarat Korcharoenkiat | Yo |
| 4 | 6870235621 | Rerngrit Jangsri | Frank |

---

## Problem Description

### The situation

Hiring is bursty. A position is posted on JobsDB, JobThai or LinkedIn, and applications
arrive in a concentrated wave into an email inbox or a spreadsheet. Every one of them
must be opened, read, and judged by hand — and then each surviving candidate must be
interviewed by someone who has actually studied their resume against the role.

The people doing that work are rarely dedicated to it. In a Thai tech SME it is a single
HR generalist who also owns payroll, admin and onboarding, or a founder or tech lead
hiring in between their actual job. In a larger company it is a small recruitment team
carrying many open roles at once. In both cases the same thing happens: applications
arrive faster than anyone can judge them properly.

### The core problem

> **บริษัทขนาดเล็กที่มีพนักงานไม่เพียงพอ ไม่สามารถ screen resume ได้ทัน**
>
> *Small companies with insufficient staff cannot screen incoming resumes fast enough.*

The decisive factor is not how many recruiters a company has — it is the **ratio between
the applications arriving and the capacity to judge them properly**. Screening effort
scales with applicant volume; screening capacity scales with headcount, and headcount
never keeps up. A company with one recruiter and 80 applicants and a company with five
recruiters and 2,000 applicants have the same problem.

When that ratio breaks, quality collapses in two places:

- **Screening becomes shallow.** Resumes get a 20-second skim, or are filtered on crude
  keyword matches. Good candidates are missed and weak ones advance.
- **Interviews become unprepared.** The interviewer opens the resume minutes beforehand
  and falls back on generic questions, so the interview fails to verify the very things
  screening could not confirm. An expensive hour produces little evidence.

### Consequences

| Consequence | Why it hurts |
|---|---|
| **Slow time-to-screen** | Strong candidates are interviewed and hired by a faster competitor before the SME even opens their file. |
| **Ghosted candidates** | With no time to reply, most applicants never hear back. This damages employer brand in a small, highly-networked local tech community. |
| **Unprepared, generic interviews** | With no time to study each resume against the role, interviewers ask the same stock questions of everyone. Claims on the resume go unprobed and gaps against must-have criteria go unverified, so the hiring decision rests on impression rather than evidence. |
| **No decision trail** | Rejections live in someone's head. When someone asks later "why did we pass on this person?", there is no answer, and no way to review whether screening is consistent or fair. |
| **The archive is dead weight** | Resumes from six months ago sit unused in a folder. When a similar role opens, the SME pays to source candidates all over again — including people who already applied and were a near-miss. |
| **Positions rot silently** | A requisition that has been open for 90 days looks exactly like one opened last week. Nobody is alerted, so nothing is re-scoped or re-posted. |
| **PDPA exposure** | Resumes are personal data under Thailand's PDPA. Storing them indefinitely in an inbox with no consent record, no retention limit and no deletion process is a compliance risk that SMEs are least equipped to manage. |

### Why existing options do not solve it

- **Enterprise ATS** (Workday, Greenhouse, …) — built to *track* applications, not to judge
  them. They organise the queue, route approvals and store records, but a human still reads
  every resume and still walks into the interview unprepared. They are also priced and
  scoped for companies with a recruitment department.
- **Job boards** (JobsDB, JobThai, LinkedIn) — they solve *candidate supply*, and in doing so
  make the problem worse: they deliver more resumes into the inbox without helping anyone
  read them.
- **Keyword filters and CV parsers** — fast, but mechanical. They match strings rather than
  weighing evidence, cannot explain a decision, and reject good candidates for using
  different vocabulary.
- **Spreadsheets + inbox** — the current reality for most SMEs. Free, flexible, and exactly
  the thing that is failing.

### Our position

The gap is not candidate supply, and it is not record-keeping. It is **judgement capacity**
after the applications arrive — the ability to read every resume carefully and to interview
every shortlisted candidate on evidence rather than impression.

So HireAssist deliberately does **not** build another application funnel and does not try to
replace an ATS. It attaches to the channels a company already uses and adds the layer that is
missing: explainable screening at volume, interview questions grounded in the specific resume
and role, re-matching of the existing talent pool, visibility into stalling positions, and
personal data kept compliant.

The human still decides. HireAssist's job is to make sure that when they decide, they are
deciding on evidence they actually had time to look at.

---

## Target Customers

### Who qualifies

HireAssist's customer is defined by a **ratio, not by company size**:

> **Any company that receives more applications than it can screen carefully and
> interview well.**

Headcount is not the qualifier. A 20-person startup with one HR generalist and 80
applicants per opening, and a 300-person company with three recruiters and 2,000
applicants, are the same customer — both have more resumes than judgement-hours, and
both are losing quality at the same two points.

A company qualifies when **all** of the following hold:

| Qualifying condition | Why it matters |
|---|---|
| **Application volume exceeds screening capacity** | The core trigger. Resumes are skimmed, queued, or silently dropped because there are not enough hours to read them properly — regardless of how many people are doing the reading. |
| **Screening quality is judgement-based, not mechanical** | The role cannot be filtered by a single checkbox; it needs weighing of experience, skills and evidence. This is what makes an explainable AI score valuable rather than a keyword filter. |
| **Interviews are not systematically prepared** | Interviewers open the resume minutes beforehand. The company loses the chance to verify exactly what screening could not confirm. |
| **Roles recur or overlap** | Similar positions reopen over time, so past applicants retain value and the talent pool is worth re-matching instead of re-sourcing. |
| **No adequate ATS in place** | Hiring runs on inbox, spreadsheets, or a job board's built-in tooling — or on an ATS that stores applications without helping anyone judge them. |

A company **does not** qualify simply for being small. A 15-person company hiring one
person a year has no throughput problem and does not need HireAssist.

### Primary segment (initial focus)

Within that definition, we focus first on **Thai technology companies — software houses,
product startups, digital agencies and IT service firms, roughly 10 to 200 employees.**

| Attribute | Profile |
|---|---|
| Hiring pattern | Bursty and urgent — several roles at once, and the same roles reopen (e.g. "backend engineer" every few months) |
| Application volume | ~20–200 per opening, arriving in concentrated waves after a posting |
| Screening capacity | 0–2 HR generalists, often assisted by a tech lead hiring between their actual work |
| Existing tools | Email inbox, Google Sheets, LINE, one or two job boards; rarely a real ATS |
| Budget | Price-sensitive; will not pay enterprise ATS licensing |
| Languages | Mixed Thai and English resumes; job titles and technical skills mostly English |

**Why this segment first:** tech resumes are comparatively structured (skills, stacks,
years of experience, public repositories), which makes explainable matching tractable;
technical roles are exactly the case where a generic interview wastes the hour, so
resume-specific questions pay off immediately; roles recur, so the talent pool has value
from the first re-match; and these companies adopt SaaS tools readily.

This is a **beachhead, not a boundary.** Nothing in the design assumes a small company —
the same system serves a larger firm whose recruiters are equally outnumbered by
applicants. Larger organisations are a natural expansion once multi-team workflows and
deeper ATS integration are supported.

### Users of the system

| User | Goal | What they get from HireAssist |
|---|---|---|
| **Recruiter / HR** *(primary)* | Get through the application backlog, shortlist candidates who can be defended, and interview them well | Ranked, explainable shortlist instead of a folder of unread PDFs; interview questions grounded in that specific resume and role; alerts when a position is stalling; every decision and its reason recorded |
| **Admin / company owner** | Keep hiring compliant, consistent and auditable, and control who has access | Workspace and member management, data-retention settings, plus recorded rejection reasons, consent status and retention state for every candidate |
| **Candidate** *(indirect)* | Be judged on evidence, and considered again later | A real reading rather than a 20-second skim; remains eligible for future roles through the talent pool, with consent |

---

## Scenario (use-case & description)

### Overview

HireAssist is used by a small hiring team through one recruiter-facing web application.
The flow it supports end-to-end is:

> **describe the role → drop in the resumes → get an explained shortlist → walk into the
> interview prepared → and never lose the candidates you passed on.**

| ID | Use Case | Primary Actor | Solves (see *Consequences*) |
|---|---|---|---|
| UC-0 | Authenticate and manage workspace access | Admin / Recruiter | — (foundation) |
| UC-1 | Create a job opening from natural-language requirements | Recruiter | Slow time-to-screen |
| UC-2 | Batch-screen resumes against a job opening | Recruiter | Slow time-to-screen, ghosted candidates, no decision trail |
| UC-3 | Generate candidate-specific interview questions | Recruiter | Unprepared, generic interviews |
| UC-4 | Monitor hiring pipeline and stale positions | Recruiter | Positions rot silently |
| UC-5 | Enforce candidate data retention | System Scheduler / Admin | PDPA exposure |

**Actors**

| Actor | Description |
|---|---|
| **Recruiter** | The person who runs day-to-day hiring — an HR generalist, a founder, or a tech lead hiring for their own team. Primary actor of UC-1 through UC-4: creates job openings, screens resumes, prepares interview questions, and monitors the pipeline. |
| **Admin** | The workspace owner. Has every Recruiter capability, and additionally manages members, roles and the data-retention policy (UC-0, UC-5). |
| **Candidate** | *Indirect actor.* Does not log in. Supplies a resume and a consent decision; is the subject of the data the system processes. |
| **System Scheduler** | *Supporting actor.* Time-driven trigger that runs work no human initiates: staleness checks (UC-4) and retention enforcement (UC-5). |

---

### UC-0 — Authenticate and manage workspace access

**Actors:** Admin, Recruiter
**Goal:** Ensure only authorised members of a company access its candidate data, with permissions matching their role.

**Description**

Every other use case operates on personal data, so all of them require an authenticated session;
this use case is the precondition for the rest. An Admin or Recruiter signs in and receives a
session scoped to one **workspace** (one company). An Admin invites members and assigns a role — **Admin**
or **Recruiter** — which determines what they may do: a Recruiter creates job openings, screens
resumes, prepares interview questions and monitors the pipeline, while an Admin does all of that and
additionally manage members, roles and data-retention settings. All data access is scoped to the workspace, so no company
can see another's candidates.

**Main flow**
1. Admin or Recruiter signs in with their credentials.
2. System authenticates and issues a session token carrying workspace and role.
3. Every subsequent request is authorised at the gateway against that token.
4. Admin may invite, remove, or change the role of a workspace member.

**Alternate flows**
- *1a. Invalid credentials* — access denied; repeated failures are rate-limited.
- *3a. Token expired* — the Admin or Recruiter is prompted to re-authenticate.
- *3b. Action exceeds the assigned role* — request rejected and the attempt recorded.

**Outcome:** Candidate data is accessible only to the right people in the right company, which is
both a security requirement and a PDPA obligation.

---

### UC-1 — Create a job opening from natural-language requirements

**Actor:** Recruiter
**Goal:** Turn the way a role is actually described in conversation into structured, machine-usable screening criteria — without filling in a long form.

**Precondition:** Recruiter is authenticated into a workspace (UC-0).

**Description**

Roles are rarely handed over as a formal specification. What the Recruiter is given sounds
closer to:
*"Backend engineer, 3+ years, Go or Python, must have actually shipped something with
Kafka or RabbitMQ, English good enough for a standup with our Singapore client, degree
doesn't matter."*

The Recruiter pastes exactly that into HireAssist. The system interprets it and proposes
a structured job opening: a title, and a set of criteria each marked as **must-have** or
**nice-to-have** with a weight. The Recruiter reviews the interpretation on screen — this
is the point where a human corrects the AI, not after 100 resumes have been mis-scored.
They can edit any criterion, change must-have vs nice-to-have, adjust weights, or add one
the AI missed. They also set an expected time-to-fill, which UC-4 later uses to decide
whether the position has gone stale.

On confirmation the job opening is saved in an **open** state and becomes the target that
UC-2 screens resumes against.

**Main flow**
1. Recruiter opens "New Job Opening" and pastes a free-text description (Thai or English).
2. System extracts a proposed title and a weighted, categorised criteria set.
3. System displays the proposed structure for review.
4. Recruiter edits criteria, weights, and must-have / nice-to-have flags.
5. Recruiter sets expected time-to-fill and confirms.
6. System stores the job opening as **open** and publishes a *JobOpeningCreated* event.

**Alternate flows**
- *2a. Description too vague to extract criteria* — system says which parts it could not
  interpret and asks the Recruiter to clarify or fill them in manually.
- *4a. Recruiter rejects the interpretation entirely* — they may discard it and enter
  criteria manually through the structured form.

**Outcome:** A job opening with explicit, weighted, reviewable screening criteria — created
in minutes from plain language, and traceable back to the words the role was described in.

---

### UC-2 — Batch-screen resumes against a job opening

**Actor:** Recruiter
**Goal:** Convert a pile of unread resumes into a ranked shortlist with a stated reason for every ranking.

**Precondition:** An open job opening exists (UC-1). Recruiter is authenticated.

**Description**

This is the use case that answers the core problem. The Recruiter selects an open position
and drops in a batch of resumes at once — the files that accumulated in the inbox, exported
from a job board, or dragged in as a folder (PDF / DOCX, Thai or English).

The system does not make the Recruiter wait on a spinner. It accepts the batch, returns a
batch identifier, and processes the resumes **asynchronously**: each resume is parsed into a
normalised candidate profile (contact details, work history, skills, education), then scored
against the job opening's weighted criteria. Because resumes are independent of one another,
they are processed concurrently, and the screen fills in progressively as results arrive.

Every result carries three things: a **score**, a **must-have check** (which mandatory
criteria are met or missed), and a short **written justification** citing the evidence in the
resume — *"6 years Go at two companies; Kafka used in production per the Wongnai role; no
evidence of English-language client work."* A score with no reason is not actionable by HR,
so explanation is a required output, not a feature.

The Recruiter reviews the ranked list, overrides anything the AI got wrong, and marks
candidates as **shortlisted** or **rejected**. Rejection captures the reason — the AI's
justification, edited or replaced by the Recruiter. This reason is **internal**: it exists to
give the Recruiter and Admin an audit trail and a consistency check, and is never automatically sent
to the Candidate.

Every screened candidate is added to the **talent pool** with their consent status recorded.
The pool is retained and governed by UC-5, and is the foundation the deferred re-matching
use case (D-1) will build on.

**Main flow**
1. Recruiter selects an open job opening and uploads a batch of resume files.
2. System validates the files, creates a screening batch, and returns immediately with a batch ID.
3. System parses each resume into a normalised candidate profile.
4. System scores each profile against the job criteria and generates a justification.
5. System streams results into the ranked shortlist view as they complete.
6. Recruiter reviews the ranking, adjusts any score or decision, and marks candidates shortlisted or rejected.
7. System records each decision with its reason, and adds every candidate to the talent pool with consent status.

**Alternate flows**
- *3a. A file is unreadable* (corrupt, scanned image with no text layer, unsupported format) —
  that resume is flagged for manual handling; the rest of the batch continues unaffected.
- *4a. The AI scoring service is unavailable* — affected resumes are retried; if they still
  fail they are marked *needs manual review* rather than silently scored zero.
- *6a. Recruiter disagrees with a score* — they override it; the override is stored alongside
  the original AI score so screening quality can be reviewed later.

**Outcome:** A ranked, explained shortlist produced in one pass instead of hours of reading,
with every decision and its reason recorded, and every candidate retained in the talent pool.

---

### UC-3 — Generate candidate-specific interview questions

**Actor:** Recruiter
**Goal:** Walk into an interview with questions grounded in *this* candidate's resume and *this* job's requirements.

**Precondition:** The candidate has been screened and shortlisted for the job opening (UC-2).

**Description**

Screening produces a shortlist, but the interview is still improvised — whoever is interviewing
skims the resume five minutes beforehand and asks generic questions. HireAssist closes that gap.

For a shortlisted candidate, the system generates an interview guide from the **intersection
of the resume and the job opening**. Questions target three areas: claims in the resume worth
probing (*"You list Kafka on the Wongnai project — what was the partitioning strategy and why?"*),
**gaps against must-have criteria** that the interview needs to resolve (*"We need production
Go; your Go experience appears to be side projects — talk us through the largest one"*), and
role-specific depth drawn from the job criteria. Each question is tagged with the criterion it
tests and the resume evidence it came from, so the interviewer understands *why* it is being asked.

The Recruiter can regenerate, remove, or add questions, then export or share the guide.
After the interview the guide can be used to capture notes against each question, keeping
evidence attached to the criterion it was meant to test.

**Main flow**
1. Recruiter opens a shortlisted candidate and requests an interview guide.
2. System retrieves the Candidate profile, the original resume, and the job criteria.
3. System generates questions covering resume claims, must-have gaps, and role depth — each tagged with its source criterion.
4. System presents the guide grouped by theme.
5. Recruiter edits, removes, adds, or regenerates questions.
6. Recruiter exports or shares the finalised guide with whoever is conducting the interview.

**Alternate flows**
- *3a. Thin resume, little to probe* — system falls back to criteria-driven questions and states
  that resume-specific coverage is limited.
- *5a. Recruiter wants a different emphasis* (more system design, more behavioural) — they
  regenerate with that instruction.

**Outcome:** A per-candidate interview guide that tests exactly what screening could not verify,
prepared in seconds rather than skipped.

---

### UC-4 — Monitor hiring pipeline and stale positions

**Actors:** Recruiter (primary), System Scheduler (supporting)
**Goal:** See the health of every open position at a glance, and be told when one is stalling.

**Precondition:** At least one job opening exists.

**Description**

A requisition open for 90 days looks exactly like one opened last Tuesday. Nothing in an inbox
or spreadsheet raises a hand. The result is positions that quietly rot — never re-scoped, never
re-posted, never escalated.

The dashboard gives the Recruiter one view across all open positions: for each, the funnel
(**applied → screened → shortlisted → interviewing**), days open against the expected time-to-fill
set in UC-1, screening throughput, and how many candidates are waiting on a decision. Conversion
between stages exposes *where* a pipeline is failing — a role with 200 applicants and one
shortlist has a criteria problem, not a supply problem.

Independently of anyone opening the dashboard, the System Scheduler evaluates open positions
against their staleness rules and raises an alert when a position exceeds its expected
time-to-fill, when a batch has sat unreviewed too long, or when a shortlisted candidate has had
no decision for several days. Alerts are delivered to the Recruiter responsible for the
position, and positions that trip a rule are highlighted on the dashboard. The point is that noticing does not depend on
someone remembering to look.

**Main flow**
1. Recruiter opens the dashboard.
2. System aggregates pipeline metrics across all open positions in the workspace.
3. System displays per-position funnels, days open vs. expected time-to-fill, and stage conversion.
4. System highlights positions currently flagged as stale or blocked.
5. Recruiter drills into a position to see its candidates and act.

**System-triggered flow**
1. Scheduler periodically evaluates every open position against the staleness rules.
2. Positions breaching a rule are flagged and an alert is published.
3. The Recruiter responsible for the position is notified.
4. The flag is cleared when the position is filled, closed, or the blocking condition is resolved.

**Alternate flows**
- *3a. No open positions* — the dashboard shows an empty state with recent hiring history rather than a blank screen.
- *4a. A position is deliberately paused* — it is excluded from staleness alerts while paused, so the alerts stay meaningful.

**Outcome:** Hiring problems become visible while they can still be fixed, and a stalled position
raises its own hand instead of waiting to be noticed.

---

### UC-5 — Enforce candidate data retention

**Actors:** System Scheduler (primary), Admin (configures the policy)
**Goal:** Make sure resumes and candidate data are not kept longer than the company is entitled to keep them — automatically, without anyone remembering to check.

**Preconditions:** A retention policy is configured for the workspace. Candidate records exist in the talent pool.

**Description**

Under Thailand's PDPA, personal data may only be kept as long as the purpose it was
collected for requires. In practice this obligation is almost never met: resumes stay in
an inbox or a drive forever, because deleting them is nobody's job and nothing reminds
anyone that a file has aged past its purpose. The company accumulates an unbounded
archive of personal data it has no lawful basis to hold — and the more successful the
talent pool is, the larger that liability grows.

HireAssist makes retention a property of the system rather than a task someone forgets.
An **Admin** configures the workspace's retention policy: how long a Candidate's data may
be kept (for example 12 months), measured from a defined anchor — the date consent was
given, or the Candidate's last activity in a hiring process. The Admin also chooses what
happens on expiry: **permanent deletion** of the resume and profile, or **anonymisation**,
which destroys all identifying data while preserving the aggregate counts the pipeline
dashboard (UC-4) is built from, so historical hiring metrics survive the erasure of the
person.

The **System Scheduler** then evaluates the talent pool on a recurring basis. Records
approaching expiry enter a **warning window**: the Recruiter is notified that a set of
candidates will expire on a given date, which is the moment to act — re-obtain consent
for a Candidate worth keeping, or simply let them go. Records that pass the expiry date
are removed or anonymised according to the policy, and every action is written to an
**audit log** recording what was erased, when, and under which policy. That log is the
evidence the company can show a regulator, and it deliberately contains no personal data
itself.

Expired candidates disappear from the talent pool entirely, so no later feature can
surface them — this is the gate that any future re-matching (D-1) will depend on.
Candidates in an **active hiring process** are never silently deleted: they are held and flagged for the Recruiter to decide, because the purpose that
justifies keeping their data is still live.

**Main flow**
1. Admin configures the retention period, the anchor date, and the expiry action (delete or anonymise).
2. Scheduler periodically evaluates every candidate record against the policy.
3. Records entering the warning window are flagged, and the responsible Recruiter is notified with the list and the expiry date.
4. Recruiter may extend a record by renewing consent, or take no action and allow expiry.
5. On the expiry date the system deletes or anonymises the record and everything derived from it, including stored resume files.
6. System writes an audit entry for each action and removes the Candidate from the talent pool.

**Alternate flows**
- *2a. Candidate is in an active hiring process* (shortlisted, scheduled, or awaiting a decision) — expiry is held and the record flagged for the Recruiter, since the original purpose is still active.
- *4a. Consent is renewed* — the retention clock resets from the new consent date and the warning is cleared.
- *5a. A candidate requests deletion before expiry* — the erasure runs immediately rather than waiting for the schedule.
- *5b. Deletion of a stored file fails* — the record is retained, the failure is logged and retried, and the record is reported as *deletion pending* rather than being marked erased.

**Outcome:** Candidate data ages out of the system on a defined schedule with an auditable
record of every erasure, so the talent pool stays lawful as it grows instead of becoming a
liability — and no one has to remember to do it.

---

### Use Case Diagram

```mermaid
graph LR
  AD(["Admin"])
  R(["Recruiter"])
  SCH(["System Scheduler"])
  CD(["Candidate"])

  subgraph HireAssist
    UC0(["UC-0 Authenticate &<br/>Manage Workspace Access"])
    UC1(["UC-1 Create Job Opening from<br/>Natural-Language Requirements"])
    UC2(["UC-2 Batch-Screen Resumes<br/>Against a Job Opening"])
    UC3(["UC-3 Generate Candidate-Specific<br/>Interview Questions"])
    UC4(["UC-4 Monitor Pipeline &<br/>Stale Positions"])
    UC5(["UC-5 Enforce Candidate<br/>Data Retention"])
    EXT1(["Draft Interview<br/>Invitation Email"])
  end

  AD --- UC0
  R --- UC0
  R --- UC1
  R --- UC2
  R --- UC3
  R --- UC4
  SCH --- UC4
  SCH --- UC5
  AD --- UC5
  CD -.-> UC2

  EXT1 -.->|"«extend»"| UC2
```

**Relationships used, and why**

Only one relationship is used:

- **«extend» Draft Interview Invitation Email** — optional behaviour after shortlisting. UC-2 is
  complete without it; when the Recruiter chooses to invite a Candidate, the extension adds a
  drafted invitation. It is modelled as an extension precisely because it is conditional — the
  base use case succeeds whether or not it runs.

No «include» relationships are used. Each use case here is a coherent unit of behaviour that does
not share a sub-behaviour with another, and factoring parts of a single use case out purely to
populate the diagram would add notation without adding meaning. Sub-steps such as parsing a resume
or scoring a profile are internal to UC-2 and are described in its flow, not promoted to use cases
in their own right.

*Notes:*
- *Authentication (UC-0) is a precondition of every other use case. It is shown as its own use
  case rather than as five «include» arrows, which would add clutter without adding meaning.*
- ***Admin** is a generalisation of **Recruiter**: an Admin can perform every Recruiter use case
  and additionally manages members, roles and retention settings. Only the distinguishing
  association (UC-0) is drawn, to keep the diagram readable.*
- ***Candidate** is an indirect actor — they never log in. They supply the resume and the consent
  decision that UC-2 processes, shown as a dashed association.*

---

### Deferred Use Cases

The following use case is **deliberately parked**. It is recorded here because it remains part of
the product's intended direction and shapes decisions we are making now — but it is out of scope
for the implementation delivered in this term project, and is not counted among the use cases
above or drawn in the use case diagram.

**Why it is deferred**

Re-matching is the most valuable idea in the original concept, and also the most dependent on
everything else working first. It cannot be demonstrated meaningfully until there is a talent pool
with real depth, which only exists after UC-2 has been used repeatedly over time; a re-match run
against an empty or shallow pool proves nothing. It also compounds risk: it multiplies scoring
cost across the whole archive, and it processes personal data for a purpose other than the one it
was collected for, which raises consent questions that UC-5 must be trusted to answer first.

**What we are doing now to keep it viable**

Deferring it is not abandoning it. The work already in scope is deliberately laid so that
re-matching can be added later without rework:

- UC-2 stores every screened candidate as a **normalised profile in the talent pool**, not merely
  as an attachment to one job opening — so the pool exists and grows from day one.
- Scoring is designed as a **separable behaviour** operating on *(profile, criteria)*, so it can be
  invoked over an archive rather than only over an incoming batch.
- UC-5 maintains the **consent and retention state** that any lawful re-matching would have to
  respect, and removes expired candidates from the pool entirely.

**The parked use case, for the record**

#### D-1 — Re-match the talent pool against a job opening

**Actors:** Recruiter (primary), System Scheduler (supporting)
**Goal:** Surface strong candidates the company has *already* seen, instead of sourcing from zero every time.

**Preconditions:** A talent pool exists from previous screening (UC-2), governed by UC-5. An open job opening exists (UC-1).

**Description**

An SME's resume archive is its most under-used asset. The person who was a near-miss for
Backend Engineer in March may be an obvious yes for Platform Engineer in September — but
nobody remembers them, and nobody has time to re-read six months of PDFs.

Re-matching runs the *existing* talent pool against a job opening's criteria, reusing the same
scoring logic as UC-2. It can be triggered two ways:
**on demand / on job creation**, when a Recruiter opens a new position and immediately asks
"who do we already have?"; and **periodically**, when the System Scheduler re-evaluates open
positions against candidates added since the last run. *(Which of these is primary, and how it
is triggered, would be settled by an ADR if this use case is reinstated.)*

Because re-matching processes personal data collected for an *earlier* purpose, it is
**gated by consent and retention**. Candidates whose consent was not given for future matching,
or whose retention period has expired, are excluded from the pool — they are never scored,
and the Recruiter is told how many candidates were excluded on those grounds rather than being
shown a silently shortened list.

Results arrive as a notification: *"7 candidates from your talent pool match Platform Engineer;
2 meet all must-haves."* From there the Recruiter treats them exactly like freshly screened
candidates — same ranked view, same explanations, same shortlist and rejection actions.

**Main flow**
1. Trigger fires — the Recruiter requests a re-match, or the System Scheduler initiates a periodic run.
2. System selects candidates from the talent pool that are consent-valid and within retention.
3. System scores each against the job opening's criteria (reusing UC-2's scoring behaviour).
4. System filters to matches above the relevance threshold.
5. System notifies the Recruiter with a summary of matches and the number of candidates excluded for consent/retention reasons.
6. Recruiter opens the results, reviews the ranked matches with their explanations, and shortlists or dismisses each.

**Alternate flows**
- *2a. Pool is empty or fully consent-excluded* — the system reports this explicitly instead of returning "no matches".
- *4a. No candidate clears the threshold* — the Recruiter is told the pool was searched and nothing qualified, so a null result is still informative.
- *6a. A candidate withdraws consent or requests deletion* — they are removed from the pool and excluded from all future re-matching.

**Outcome:** Qualified candidates the company already paid to attract are resurfaced automatically
and lawfully, turning a dead archive into a live sourcing channel.

---


## Functional Requirements

_TBD._

## Non-functional Requirements

_TBD._

## ADRs

_TBD — at least 3._
