-- models/marts/fct_transactions.sql
-- Core fact table joining transactions with merchant and FX context

with transactions as (
    select * from {{ ref('stg_transactions') }}
),

merchants as (
    select * from {{ ref('stg_merchants') }}
),

fx_latest as (
    select distinct on (from_currency, to_currency)
        from_currency,
        to_currency,
        rate
    from {{ source('raw', 'fx_rates') }}
    order by from_currency, to_currency, captured_at desc
),

enriched as (
    select
        t.transaction_id,
        t.transaction_reference,
        t.merchant_id,
        t.customer_id,
        m.merchant_name,
        m.business_type,
        m.merchant_tier,
        m.city                                          as merchant_city,
        t.transaction_date,
        t.transaction_created_at,
        t.amount,
        t.currency,
        t.amount_ngn,

        case
            when t.currency != 'NGN' then
                round(t.amount_ngn / coalesce(fx_usd.rate, 1580), 2)
            else round(t.amount_ngn / 1580, 2)
        end                                             as amount_usd,

        t.status,
        t.payment_channel,

        case when t.status = 'success'  then 1 else 0 end   as is_successful,
        case when t.status = 'failed'   then 1 else 0 end   as is_failed,
        case when t.status = 'reversed' then 1 else 0 end   as is_reversed,

        extract(hour from t.transaction_created_at)         as transaction_hour,
        extract(dow  from t.transaction_created_at)         as day_of_week,
        to_char(t.transaction_created_at, 'YYYY-MM')        as year_month

    from transactions t
    left join merchants m
        on t.merchant_id = m.merchant_id
    left join fx_latest fx_usd
        on fx_usd.from_currency = 'NGN'
       and fx_usd.to_currency   = 'USD'
)

select * from enriched
