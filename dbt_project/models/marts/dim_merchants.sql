-- models/marts/dim_merchants.sql
-- SCD Type 2: tracks merchant history when tier or status changes

with source as (
    select * from {{ ref('stg_merchants') }}
),

-- Generate a row hash to detect changes between runs
with_hash as (
    select
        merchant_id,
        merchant_name,
        business_type,
        merchant_tier,
        is_active,
        city,
        settlement_bank,
        merchant_created_at,
        merchant_updated_at,
        md5(
            coalesce(merchant_name,  '') ||
            coalesce(business_type,  '') ||
            coalesce(merchant_tier::text, '') ||
            coalesce(is_active::text, '') ||
            coalesce(city,           '')
        ) as row_hash
    from source
),

-- SCD Type 2: each unique (merchant_id, row_hash) gets its own record
scd as (
    select
        {{ dbt_utils.generate_surrogate_key(['merchant_id', 'row_hash']) }}
                                        as merchant_key,
        merchant_id,
        merchant_name,
        business_type,
        merchant_tier,
        is_active,
        city,
        settlement_bank,
        row_hash,
        merchant_created_at             as effective_from,
        lead(merchant_updated_at)
            over (partition by merchant_id order by merchant_updated_at)
                                        as effective_to,
        case
            when lead(merchant_updated_at)
                     over (partition by merchant_id order by merchant_updated_at)
                 is null
            then true
            else false
        end                             as is_current
    from with_hash
)

select * from scd
