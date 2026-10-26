# Output files

- `kpi_summary.json` — headline numbers for the report.
- `service_type_scorecard.csv` — volume, elapsed-time, SLA-risk, handoff, reopen and rating measures by service type.
- `team_scorecard.csv` — basic comparison by team.
- `team_mix_adjusted_risk.csv` — observed and expected team risk after a basic priority/service-type adjustment.
- `channel_scorecard.csv` — measures by intake route.
- `priority_scorecard.csv` — counts, risk and elapsed times by priority.
- `monthly_flow.csv` — monthly arrivals, resolutions and reconstructed month-end backlog.
- `queue_friction_score.csv` — ranked service types using the documented friction score.
- `queue_attention_queue.csv` — request-level triage list with the attention score and the fields needed for review.
- `dashboard_data.json` — summarized metrics plus the request-level data embedded in the HTML dashboard.
- `operations_analytics.db` — SQLite database containing `service_requests` and `request_activity_log`.

Rebuild these files by running `python src/build_project.py` from the project root. Run `python src/make_dashboard.py` afterward to refresh `index.html`.
