# Operations Analytics: Service Requests, SLA Proxies and Bottlenecks

A service desk can close most requests on time and still have a stubborn group of cases that keep customers waiting. This project looks at that group, asks where time is being lost, and turns the findings into a short list of operational changes worth testing.

The work is deliberately different from a sales, marketing or inventory project. The centre of the analysis is **how work moves through a service operation**: incoming demand, elapsed time, SLA promises, handoffs, repeated work, queue pressure and the difference between a typical case and a slow one.

All records are synthetic, made for this portfolio project. They do not describe a real company or customer.

## Start here

- `index.html` - interactive dashboard with filters, three story chapters, a ranked review queue and a small what-if sandbox.
- `reports/operations_analytics_review.pdf` - business-facing review with findings, charts, cautions and recommended next steps.
- `OUTCOMES.md` - the findings in plain language.
- `analysis/analysis_walkthrough.md` - how the measures are defined and what they can and cannot tell us.
- `DATA_DICTIONARY.md` - field definitions and data notes.
- `data/service_requests.csv` - one row per request.
- `data/request_activity_log.csv` - a plausible event path for each request.
- `outputs/operations_analytics.db` - the same data in SQLite, ready for SQL exploration.
- `outputs/` - scorecards, monthly flow, the attention queue and the data used by the dashboard.
- `visualizations/` - publication-ready charts used in the report.
- `sql/` - example queries for common operational questions.

## The questions this project tries to answer

1. Does the usual resolution time tell the same story as the 90th percentile?
2. Which request types combine meaningful volume with a high share of SLA breaches or at-risk open cases?
3. Does time rise as work moves through more teams, and which cases should be inspected to understand why?
4. How does each team look after allowing for the priority and type of work it receives?
5. Which open requests should a supervisor review first, and what assumptions sit behind that order?
6. What might happen if a team reduced avoidable handoffs or added usable capacity?

## Run the project

Use Python 3.10 or later. From the repository folder:

```bash
python -m pip install -r requirements.txt
python src/build_project.py
python src/make_dashboard.py
python -m unittest discover -s tests -v
```

The first script regenerates the sample records, scorecards, SQLite database, visualizations and PDF report. The second embeds the dashboard data into `index.html`, so it can be opened directly in a browser or published with GitHub Pages. Chart drawing uses Chart.js from a CDN; the charts need an internet connection. The filters and queue table are still part of the local page, but full chart rendering needs the CDN to load.

To explore the database with SQLite:

```sql
SELECT request_id, priority, service_type, team, observed_elapsed_hours, sla_target_hours
FROM service_requests
WHERE status = 'Open'
  AND observed_elapsed_hours > sla_target_hours
ORDER BY observed_elapsed_hours / sla_target_hours DESC;
```

## What the dashboard does

The story is split into three chapters rather than putting every chart on one page.

- **The promise** compares arrival and closure patterns, resolved SLA performance, the current open queue and the long tail.
- **Where work sticks** compares request types, handoffs and team risk after a simple case-mix adjustment.
- **The next shift** ranks requests for review and lets a reader try an illustrative handoff/capacity scenario.

Filters for request type, team, priority, intake channel and date apply across the story. The request queue can also be searched.

## Main findings in this generated run

The sample contains 8,200 requests from July 2025 through mid-January 2026. Of these, 8,105 are resolved and 95 remain open at the snapshot date. Among resolved requests, 66.5% met their resolution target. The median resolution time is 13.8 hours; the 90th percentile is 47.1 hours.

Technical fault requests show the highest combined SLA-breach/at-risk share in the service-type scorecard, at about 51%. Returns and refunds follow at about 40%. Roughly 63% of all requests have at least one handoff. Open requests that have passed their SLA are kept visible as a separate review list.

These are descriptive results from generated records. They demonstrate the analysis, not the performance of an actual operation. See `OUTCOMES.md` for the practical interpretation and `MODEL_CARD.md` for limits and appropriate use.

## Data and measurement choices

- The snapshot date is 15 January 2026.
- The sample includes request priority, type, intake channel, assigned team, region, complexity, handoffs, reopens, first-response time and resolution time.
- Resolution SLA results are calculated for resolved cases. Open requests are marked at risk when elapsed age has passed the request's stated target.
- The team comparison expects risk within each priority and service-type group, then compares observed risk with that mix-weighted expectation. It is a lightweight adjustment and leaves out staffing, shift coverage, skill mix and live workload.
- The attention score is a transparent triage ordering. It is not a measure of a customer's worth or an employee's quality.
- The activity log is a synthetic plausible event path, not an audited operational history.

## Publish on GitHub

1. Create a new public or private repository.
2. Upload the contents of this folder (not the ZIP file inside another folder).
3. Open **Settings → Pages** and choose deployment from the `main` branch and `/ (root)`.
4. Save, then use the generated Pages URL to share the dashboard.

The report PDF and PNG charts are in the repository for hiring managers and reviewers who prefer a static walkthrough.

## Folder map

```text
.
├── index.html
├── README.md
├── DESCRIPTION.md
├── OUTCOMES.md
├── DATA_DICTIONARY.md
├── MODEL_CARD.md
├── ACTION_PLAN.md
├── data/
├── analysis/
├── outputs/
├── reports/
├── sql/
├── src/
├── tests/
└── visualizations/
```

## License

Code is covered by the MIT License in `LICENSE`. The generated data is covered by `DATA_LICENSE.md`.
