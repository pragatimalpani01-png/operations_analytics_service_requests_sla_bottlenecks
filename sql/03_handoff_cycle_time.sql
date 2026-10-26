-- Descriptive only: more difficult requests may require more handoffs.
SELECT handoffs,
       COUNT(*) AS resolved_requests,
       ROUND(AVG(resolution_hours), 1) AS mean_hours,
       ROUND(MIN(resolution_hours), 1) AS min_hours
FROM service_requests
WHERE status = 'Resolved'
GROUP BY handoffs
ORDER BY handoffs;
