# Data dictionary

## `data/service_requests.csv`
One row per service request. All fields describe a generated example request.

| Field | Meaning |
|---|---|
| `request_id` | Stable synthetic identifier such as `SR-000123`. |
| `created_at` | Request arrival timestamp. |
| `first_response_at` | Timestamp of the first response, capped at the snapshot for illustration. |
| `resolved_at` | Resolution timestamp; blank when the request is open at the snapshot. |
| `status` | `Resolved` or `Open` at the snapshot. |
| `priority` | Illustrative priority category, P1 urgent through P4 low. |
| `service_type` | Type of help requested. |
| `channel` | Intake route: email, web form, phone, live chat or internal transfer. |
| `team` | Current handling group. |
| `region` | Illustrative operating region. |
| `complexity` | Low, medium or high case complexity. |
| `handoffs` | Number of team handoffs in the generated path. |
| `reopened_count` | Number of times the request is recorded as reopened. |
| `sla_target_hours` | Illustrative resolution target for the request's priority. |
| `first_response_target_hours` | Illustrative first-response target for the request's priority. |
| `first_response_hours` | Time from creation to first response, in hours. |
| `resolution_hours` | Completed resolution duration in hours. Blank while open. |
| `age_at_snapshot_hours` | Age at 15 January 2026. |
| `observed_elapsed_hours` | Resolution time for resolved requests; current age for open requests. |
| `first_response_sla_met` | Whether first response met its target. |
| `resolution_sla_met_or_not_yet_breached` | True if a resolved request met its target, or an open request has not yet passed it. |
| `sla_breached_or_at_risk` | Inverse of the preceding flag: the resolution target was missed or an open request has already passed it. |
| `elapsed_vs_sla` | Observed elapsed time divided by the target, used as one part of the attention score. |
| `priority_base` | Numerical base assigned to the priority for the queue-attention score. |
| `expected_risk_given_mix` | Expected risk rate for the request's priority and service-type group, used in the team mix comparison. |
| `queue_attention_score` | Rule-based 0-to-100 review score; see `MODEL_CARD.md` for the components. |
| `customer_rating_1_to_5` | Generated 1-to-5 rating used as a directional satisfaction proxy. |
| `is_weekend_arrival` | Whether arrival was on Saturday or Sunday. |
| `is_month_end_arrival` | Whether arrival was at month end. |

## `data/request_activity_log.csv`
A plausible sequence of events for each request: creation, first response, generated handoffs and resolution when resolved. It is useful for path and process analysis. The times and notes are synthetic and should not be treated as an audited event history.

## Important metric definitions

- **Resolved SLA attainment:** share of resolved cases where resolution time is less than or equal to the SLA target.
- **Breached or at risk:** share of requests that have already passed the target. For resolved cases, this means the target was missed; for open cases, it means current age has crossed the target.
- **p90 elapsed time:** the 90th percentile of completed resolution hours in a group. It describes the slow end of the completed case distribution, not the open backlog.
- **Queue friction score:** a 0–100 ranking built from percentile ranks of p90 elapsed time divided by the median target, average handoffs and the breached/at-risk share.
- **Mix-adjusted team risk gap:** observed risk minus expected risk after averaging the risk rate for the same priority/service-type groups in the selected records. It is a simple adjustment, not a causal or complete case-mix model.
- **Queue attention score:** a rule-based request review score from priority, elapsed time relative to target, handoffs, complexity and reopen status. Higher means review sooner under these assumptions.
