with settlements as (
    select * from {{ source('raw', 'settlements') }}
),

merchants as (
    select * from {{ ref('stg_merchants') }}
),

enriched as (
    select
        s.id                                                        as settlement_id,
        s.merchant_id,
        m.merchant_name,
        m.business_type,
        m.merchant_tier,
        m.city                                                      as merchant_city,

        s.period_start,
        s.period_end,
        (s.period_end - s.period_start) + 1                        as period_days,

        s.gross_amount,
        s.fee_amount,
        s.net_amount,
        round(s.fee_amount / nullif(s.gross_amount, 0) * 100, 4)   as fee_rate_pct,

        s.currency,
        s.status,
        s.settled_at,
        s.created_at,

        case
            when s.settled_at is not null
            then extract(day from s.settled_at - s.period_end::timestamp)
            else null
        end                                                         as days_to_settle,

        to_char(s.period_start, 'YYYY-MM')                         as settlement_month

    from settlements s
    left join merchants m on s.merchant_id = m.merchant_id
    where s.id is not null
)

select * from enriched
