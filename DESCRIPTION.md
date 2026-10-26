# Project description

## Operations Analytics: Service Requests, SLA Proxies and Bottlenecks

This project studies the part of service operations that often gets hidden by a single average: the long-running requests, the work that passes between teams, and the open items that have already used up their promised response time.

The analysis follows 8,200 synthetic service requests across eight request types, four priority levels, five intake channels and five teams. It compares typical and slow resolution times, checks SLA performance, identifies queues with high friction, and builds a transparent queue-attention score for an operational review.

The distinctive element is the combination of **long-tail analysis, team mix adjustment and request-level triage**. A team handling a greater share of difficult or urgent work should not be compared with another team on raw SLA rate alone. In the same way, a queue that appears fine at the median can still be driving the worst customer waits.

The dashboard tells that story in three steps: understand the promise, find where the work sticks, and test changes for the next shift. It includes filters, a searchable request queue and a scenario sandbox for exploring the approximate effect of fewer handoffs and more usable capacity.

The records are synthetic and the SLA rules are examples. The findings are useful for demonstrating analysis and dashboard design, not as evidence about a real service desk.
