-- Open work that has already used up its resolution target.
SELECT request_id, priority, service_type, team, channel,
       ROUND(observed_elapsed_hours, 1) AS elapsed_hours,
       sla_target_hours,
       ROUND(observed_elapsed_hours / NULLIF(sla_target_hours, 0), 2) AS target_multiple,
       queue_attention_score
FROM service_requests
WHERE status = 'Open'
  AND observed_elapsed_hours > sla_target_hours
ORDER BY target_multiple DESC, queue_attention_score DESC;
