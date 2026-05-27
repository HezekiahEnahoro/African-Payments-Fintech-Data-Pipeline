-- models/staging/stg_transactions.sql
-- Cleans and casts raw transaction data

with source as (
    select * from {{ source('raw', 'transactions') }}
),

renamed as (
    select
        id                                      as transaction_id,
        reference                               as transaction_reference,
        merchant_id,
        customer_id,
        amount::numeric(15,2)                   as amount,
        upper(trim(currency))                   as currency,
        amount_ngn::numeric(15,2)               as amount_ngn,
        lower(trim(status))                     as status,
        lower(trim(channel))                    as payment_channel,
        description,
        metadata,
        created_at                              as transaction_created_at,
        updated_at                              as transaction_updated_at,
        date_trunc('day', created_at)::date     as transaction_date
    from source
    where id is not null
      and merchant_id is not null
      and amount > 0
)

select * from renamed
