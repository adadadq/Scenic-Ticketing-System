ALTER TABLE IF EXISTS admin_export_job_alert_event
    ADD COLUMN IF NOT EXISTS occurrence_count INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP;

UPDATE admin_export_job_alert_event
SET last_seen_at = created_at
WHERE last_seen_at IS NULL;

WITH ranked_open_events AS (
    SELECT
        id,
        MIN(id) OVER (
            PARTITION BY job_id, error_code, alert_source
        ) AS keep_id,
        SUM(occurrence_count) OVER (
            PARTITION BY job_id, error_code, alert_source
        ) AS merged_occurrence_count,
        MAX(last_seen_at) OVER (
            PARTITION BY job_id, error_code, alert_source
        ) AS merged_last_seen_at,
        FIRST_VALUE(error_message) OVER (
            PARTITION BY job_id, error_code, alert_source
            ORDER BY last_seen_at DESC, id DESC
        ) AS latest_error_message
    FROM admin_export_job_alert_event
    WHERE closed_at IS NULL
)
UPDATE admin_export_job_alert_event event
SET
    occurrence_count = ranked.merged_occurrence_count,
    last_seen_at = ranked.merged_last_seen_at,
    error_message = ranked.latest_error_message
FROM ranked_open_events ranked
WHERE event.id = ranked.id
    AND ranked.id = ranked.keep_id
    AND EXISTS (
        SELECT 1
        FROM ranked_open_events duplicate
        WHERE duplicate.keep_id = ranked.keep_id
            AND duplicate.id <> ranked.keep_id
    );

WITH ranked_open_events AS (
    SELECT
        id,
        MIN(id) OVER (
            PARTITION BY job_id, error_code, alert_source
        ) AS keep_id
    FROM admin_export_job_alert_event
    WHERE closed_at IS NULL
)
UPDATE admin_export_job_alert_event event
SET
    closed_at = COALESCE(event.closed_at, CURRENT_TIMESTAMP),
    close_note = COALESCE(event.close_note, 'deduplicated by migration')
FROM ranked_open_events ranked
WHERE event.id = ranked.id
    AND ranked.id <> ranked.keep_id;

ALTER TABLE IF EXISTS admin_export_job_alert_event
    ALTER COLUMN last_seen_at SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN last_seen_at SET NOT NULL;

DO $$
BEGIN
    ALTER TABLE IF EXISTS admin_export_job_alert_event
        ADD CONSTRAINT ck_admin_export_job_alert_event_occurrence_count
        CHECK (occurrence_count >= 1);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uk_admin_export_job_alert_event_open_dedupe
    ON admin_export_job_alert_event (job_id, error_code, alert_source)
    WHERE closed_at IS NULL;
