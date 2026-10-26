-- Resolved SLA attainment and current open risk by service type.
SELECT service_type,
       COUNT(*) AS requests,
       SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved,
       ROUND(100.0 * AVG(CASE WHEN sla_breached_or_at_risk = 1 THEN 1.0 ELSE 0.0 END), 1) AS breached_or_at_risk_pct,
       ROUND(AVG(handoffs), 2) AS avg_handoffs
FROM service_requests
GROUP BY service_type
ORDER BY breached_or_at_risk_pct DESC;
