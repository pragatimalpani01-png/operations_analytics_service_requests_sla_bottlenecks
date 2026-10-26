# Outcomes and practical takeaways

## What the sample shows

**The typical case and the slow case are very different.** The median resolution time is 13.8 hours. The 90th percentile is 47.1 hours. Reporting just the median would hide the experience of requests that run much longer.

**Resolution targets are being missed often enough to merit a queue-level review.** In this sample, 66.5% of resolved requests met their target. The rate is a property of the chosen synthetic data and the illustrative SLA rules, not a real service benchmark.

**Technical faults are the first queue to inspect.** About 51% of technical fault requests were breached or at risk in this run. Returns and refunds were next, at about 40%. The friction score ranks service types using p90 elapsed time relative to target, average handoffs and risk share. It is a shortlisting tool, not a verdict.

**Handoffs are common.** About 63% of requests have at least one handoff. Median resolution time rises across several handoff counts. That relationship does not prove that transferring ownership creates the full delay: more complicated cases are also more likely to be transferred. The next step is to inspect a sample of long-running cases with repeated handoffs.

**Raw team comparisons miss the type of work.** The mix-adjusted view compares each team's observed risk with the risk expected from its priority and service-type mix. It is a better conversation starter than a league table, but it is not a complete adjustment for staffing, shift coverage, skills or queue size.

**A useful queue review is more specific than “reduce backlog”.** The attention list ranks requests using priority, elapsed time relative to target, handoffs, complexity and reopening. It is intended to help a supervisor decide what to look at first. It should not be used to score customers or employees.

## Suggested actions

1. Begin each shift by reviewing open requests that have passed their target. Record an owner and a next action for each one.
2. Pull a small sample of requests with two or more handoffs and a long elapsed time. Look for unclear ownership, missing information at intake or an avoidable transfer rule.
3. Start with technical faults and returns/refunds when reviewing service promises and specialist routing.
4. Keep median and 90th percentile resolution time side by side in operational reporting.
5. Test one process change in one queue before rolling it out. Compare the change with a similar queue and record staffing or demand changes at the same time.

## Before using this in a real operation

Replace the generated data with timestamped records from the ticketing system. Confirm the SLA clock rules, business-hour calendars, pause states, priority definitions, resolution/reopen logic and queue ownership. Then validate the measures with the people who run the service. The generated results are a demonstration, not a real-world diagnosis.
