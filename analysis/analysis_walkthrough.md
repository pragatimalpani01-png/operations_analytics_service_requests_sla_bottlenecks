# Analysis walkthrough

## 1. Check the promise

Start with resolved SLA attainment, first response attainment, median resolution hours and the 90th percentile. Resolution attainment excludes open requests because an open request has not yet recorded a final resolution. Open cases are handled separately: the case is marked at risk after its elapsed age passes its target.

## 2. Locate service-type friction

The scatter plot places request volume against breached/at-risk share; bubble size reflects average handoffs. It helps separate high-volume queues from small queues with poor results. The scorecard then compares median and p90 elapsed time, handoffs, reopening and ratings by service type.

## 3. Look at the tail

The service-type box plots use a log scale to keep short contacts and multi-day cases readable together. The handoff curve reports median and p90 completion time by handoff count for resolved requests. This can locate patterns worth investigating, but it does not isolate the causal effect of a transfer.

## 4. Compare like with like

The adjusted team risk gap compares each team's observed risk with the risk expected from the priority/service-type groups it handled. It is intentionally modest. Better adjustments need staffing schedules, skill mix, work arriving per shift, business-hour calendars and the queue state when each request arrived.

## 5. Prioritise an individual review

`outputs/queue_attention_queue.csv` sorts requests using the documented rule-based attention score. Before acting, a supervisor should read the record, confirm the current owner and consider any context missing from the dataset. The score is a prompt for review, not an automatic decision.

## 6. Stress-test a process change

The dashboard lets readers vary handoff reduction and usable capacity. It translates the chosen assumptions into an indicative change to p90 elapsed time. It is not a forecast, an estimate of causal impact, or a budget case. A live test needs an agreed baseline, a comparison group where possible, and clear tracking of other operational changes.

## What would make this analysis stronger with real data?

Use business-hour clocks, actual queue snapshots, staffing by shift, assignment history, reason codes for transfers, ticket reopen events, customer contact count, and a measure of incoming request severity. If timestamps are available, build an event-level model of waiting states rather than treating total elapsed time as one block. Then validate findings with a random case audit and a before/after test.
