# Open questions

Updated 2026-11-09 after implementation audit. Earlier questions saying the product name and
all formulas were undecided are superseded by actual Plexus code; the final target decision is still open.

| ID | Question | Why it matters | Status |
|---|---|---|---|
| Q1 | Is the submission cutoff 10 November 23:39 or 23:59, and in which timezone? What is the defense time on 13 November? | Primary message 266 preserved verbatim in brief/QA.md; use earlier 23:39 for planning, timezone unconfirmed. | Verify primary message; no new organizer message sent in this audit. |
| Q2 | Where is the submission form, exact passport template and receipt? | No completed team passport or receipt found in checkout. | Open |
| Q3 | Are scoring weights or format rules published beyond the four qualitative criteria? | Avoid inventing score estimates. | No weights in inspected sources |
| Q4 | Where is the authoritative input snapshot / DuckDB used for national results? | data/ missing, EDA raw ZIP missing; cannot reproduce published aggregate results here. | Open |
| Q5 | Is the primary decision economic market access or seasonal access of remote residents to named centres? Which pilot and trips? | README promise and Hansen target do not yet align. Audit recommends a checked local pilot, with national map as context. | Resolved in project-plan.md: national Hansen + Tuva centre trips. |
| Q6 | Which concrete improvements are compared, and what waiting model/seasonal closure rules apply? | Seasons alone are not a final intervention comparison. 24h cap loses frequency sensitivity. | Open |
| Q7 | Which AI outputs and validation records go into submission? | work/ is scrubbed; evidence must survive in the final attachments. | Open |

Original A2 PDF explicitly permits a number or system of indicators, so a single scalar is not
an established mandatory constraint. The transport briefing is marked 2026. Whether every historical
transport link remains active is unverified; source URLs alone do not establish that.
