-- models/marts/dim_merchants.sql
-- SCD Type 2: reads merchant history from the merchants_snapshot,
-- which is what actually captures a new version whenever tier/status/etc. change.

with snapshot as (
    select * from {{ ref('merchants_snapshot') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['merchant_id', 'dbt_valid_from']) }}
                                    as merchant_key,
    merchant_id,
    merchant_name,
    business_type,
    merchant_tier,
    is_active,
    city,
    settlement_bank,
    dbt_valid_from                 as effective_from,
    dbt_valid_to                   as effective_to,
    case when dbt_valid_to is null then true else false end
                                    as is_current
from snapshot
