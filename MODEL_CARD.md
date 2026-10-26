# Model and score card

## Purpose

The project contains two simple decision aids: a queue-friction score for comparing service types, and an attention score for sorting individual requests for supervisor review. Both are meant to make the reasoning visible rather than hide it behind a complex model.

## Queue-friction score

For each service type, the score combines percentile ranks for:

- 45%: p90 elapsed time divided by the median SLA target;
- 30%: average number of handoffs;
- 25%: share breached or at risk.

Each component is ranked within the service types in the current sample, scaled to a percentile, then blended. A high score means “inspect this queue first,” not “this is the objectively worst service.” The score changes if the set of service types changes.

## Queue-attention score

The request-level score blends:

- 36%: priority base score;
- 30%: elapsed time relative to the SLA target;
- 13%: handoff count, capped at four;
- 12%: high-complexity flag;
- 9%: whether the request has been reopened.

Elapsed time is capped for scoring, so very old requests do not make every other factor irrelevant. Scores are intended to order human review, not to automate service decisions.

## Team mix adjustment

Within the selected sample, the analysis calculates the breached/at-risk share for each priority and service-type combination. Each request is assigned the rate from its own combination; each team's expected rate is the average of those rates. The gap is observed team risk minus expected risk, in percentage points.

This is a basic descriptive adjustment. It does not use a fitted predictive model, and it does not include staffing, shift timing, current queue volume, tenure, specialist skill or case-level history.

## Where it can go wrong

- The score weights are judgement calls. Different operations may need different weights.
- Generated labels, handoffs, times and ratings are not real service records.
- SLA target hours use simple elapsed hours, not a business-hours calendar or paused SLA clock.
- Team comparisons can be misleading when sample sizes differ or important case-mix fields are missing.
- A high priority should trigger attention, not automatically override customer context or safety needs.
- Scores should never be used to measure employee worth or to deny service to a customer.

## Appropriate next test

In a live operation, compare the queue attention list with supervisor decisions for a few weeks. Measure whether it brings late, high-impact cases to the surface earlier. Review false alarms and cases that the score ranks too low. Adjust the weights with operations staff and keep the score advisory.
