    -- Add normalized fields to link_metadata table

    ALTER TABLE link_metadata
    ADD COLUMN IF NOT EXISTS normalized_category TEXT,
    ADD COLUMN IF NOT EXISTS normalized_price_range TEXT,
    ADD COLUMN IF NOT EXISTS normalized_tags TEXT[]; -- Array of strings

    -- Add check constraint for price range (optional but good for data integrity)
    -- We only allow $, $$, $$$, $$$$ or NULL
    ALTER TABLE link_metadata
    ADD CONSTRAINT check_normalized_price_range
    CHECK (normalized_price_range IN ('$', '$$', '$$$', '$$$$') OR normalized_price_range IS NULL);

    -- Add index on category for faster filtering
    CREATE INDEX IF NOT EXISTS idx_link_metadata_normalized_category ON link_metadata(normalized_category);

    -- Add index on tags for faster searching (using gin index for array)
    CREATE INDEX IF NOT EXISTS idx_link_metadata_normalized_tags ON link_metadata USING GIN (normalized_tags);
