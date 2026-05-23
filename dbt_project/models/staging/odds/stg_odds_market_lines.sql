WITH base AS (
    SELECT
        data,
        batch_id,
        loaded_at
    FROM {{ source('bronze', 'odds_raw') }}

    {% if is_incremental() %}
        WHERE loaded_at > (SELECT MAX(loaded_at) FROM {{ this }})
    {% endif %}
),

markets AS (
    SELECT
        b.data:event_id::string AS odds_event_id,
        b.data:event_date::timestamp_ntz AS event_at_utc,
        m.value:market_id::integer AS market_id,
        m.value:name::string AS market_name,
        m.value:market_description::string AS market_description,
        p.value:id::integer AS participant_id,
        p.value:name::string AS participant_name_raw,  
        p.value:type::string AS participant_type,
        l.value:id::string AS line_id,
        l.value:value::string AS line_value,
        pr.key::integer AS sportsbook_id,
        pr.value:id::string AS price_id,
        pr.value:price::integer AS odds_price,
        pr.value:price_delta::integer AS price_delta,
        pr.value:is_main_line::boolean AS is_main_line,
        pr.value:updated_at::timestamp_ntz AS odds_updated_at,
        pr.value:closed_at::timestamp_ntz AS odds_closed_at,
        b.batch_id,
        b.loaded_at
    FROM base b,
    LATERAL FLATTEN(input => b.data:markets) m,
    LATERAL FLATTEN(input => m.value:participants) p,
    LATERAL FLATTEN(input => p.value:lines) l,
    LATERAL FLATTEN(input => l.value:prices) pr
),

-- mapowanie nazw po flatteningu
markets_with_clean_names AS (
    SELECT
        m.*,
        COALESCE(pm.participant_name_clean, NULLIF(m.participant_name_raw, '')) AS participant_name
    FROM markets m
    LEFT JOIN {{ ref('map_participants') }} pm
        ON m.participant_name_raw = pm.participant_name_raw
),

deduplicated AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY price_id
               ORDER BY loaded_at DESC
           ) AS rn
    FROM markets_with_clean_names
)

SELECT
    odds_event_id,
    event_at_utc,
    market_id,
    market_name,
    market_description,
    participant_id,
    participant_name_raw,
    participant_name,
    participant_type,
    line_id,
    line_value,
    sportsbook_id,
    price_id,
    odds_price,
    price_delta,
    is_main_line,
    odds_updated_at,
    odds_closed_at,
    batch_id,
    loaded_at
FROM deduplicated
WHERE rn = 1