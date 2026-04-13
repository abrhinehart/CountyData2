-- 018: Add progress tracking columns to bi_snapshots for UI progress bar.
ALTER TABLE bi_snapshots ADD COLUMN IF NOT EXISTS progress_current INTEGER NOT NULL DEFAULT 0;
ALTER TABLE bi_snapshots ADD COLUMN IF NOT EXISTS progress_total INTEGER NOT NULL DEFAULT 0;
