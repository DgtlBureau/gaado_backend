-- Migration: Add model_name and risk columns to processed_comments table
-- Run this in Supabase SQL Editor if the columns are missing

ALTER TABLE processed_comments 
ADD COLUMN IF NOT EXISTS model_name TEXT;

ALTER TABLE processed_comments 
ADD COLUMN IF NOT EXISTS risk TEXT;

-- Add comments for documentation
COMMENT ON COLUMN processed_comments.model_name IS 'Model name used for processing (e.g., "Qwen/Qwen2.5-7B-Instruct:together")';
COMMENT ON COLUMN processed_comments.risk IS 'Risk assessment string from AI';

