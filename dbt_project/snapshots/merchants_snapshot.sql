{% snapshot merchants_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='merchant_id',
        strategy='check',
        check_cols=['merchant_name', 'business_type', 'merchant_tier', 'is_active', 'city'],
    )
}}

select
    id                              as merchant_id,
    name                            as merchant_name,
    lower(trim(business_type))      as business_type,
    country,
    city,
    settlement_bank,
    settlement_account,
    tier::smallint                  as merchant_tier,
    is_active,
    created_at                      as merchant_created_at,
    updated_at                      as merchant_updated_at
from {{ source('raw', 'merchants') }}

{% endsnapshot %}
