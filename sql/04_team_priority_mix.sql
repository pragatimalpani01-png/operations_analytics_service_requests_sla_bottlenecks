-- Start with a transparent raw team view. Use the mix-adjusted CSV for the second view.
SELECT team, priority, service_type,
       COUNT(*) AS requests,
       ROUND(100.0 * AVG(CASE WHEN sla_breached_or_at_risk = 1 THEN 1.0 ELSE 0.0 END), 1) AS risk_pct
FROM service_requests
GROUP BY team, priority, service_type
HAVING COUNT(*) >= 15
ORDER BY team, risk_pct DESC;
