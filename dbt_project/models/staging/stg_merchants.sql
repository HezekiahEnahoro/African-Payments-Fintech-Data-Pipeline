-- models/staging/stg_merchants.sql
with source as (
    select * from {{ source('raw', 'merchants') }}
),
renamed as (
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
    from source
    where id is not null
)
select * from renamed
