-- Migration: add city and status to properties (tenant isolation / schema fix)
-- Run this if properties table already exists without these columns.

ALTER TABLE properties ADD COLUMN IF NOT EXISTS city TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';

DROP VIEW IF EXISTS all_properties;
CREATE VIEW all_properties AS SELECT * FROM properties;
