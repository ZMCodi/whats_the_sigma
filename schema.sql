create extension if not exists timescaledb;

create table public.tickers (
  ticker character varying(25) not null,
  sector character varying(100) null,
  constraint tickers_pkey primary key (ticker)
) TABLESPACE pg_default;

create table public.daily (
  ticker character varying(25) not null,
  date date not null,
  open numeric(16, 5) not null,
  high numeric(16, 5) not null,
  low numeric(16, 5) not null,
  close numeric(16, 5) not null,
  adj_close numeric(16, 5) not null,
  volume bigint not null,
  constraint daily_pkey primary key (ticker, date),
  constraint daily_ticker_fkey foreign KEY (ticker) references tickers (ticker) on delete CASCADE,
  constraint daily_volume_check check ((volume >= 0)),
  constraint price_check check (
    (
      (high >= open)
      and (high >= low)
      and (
        high >=
        close
      )
      and (low <= open)
      and (low <= high)
      and (
        low <=
        close
      )
    )
  )
) TABLESPACE pg_default;

create index IF not exists daily_date_idx on public.daily using btree (date desc) TABLESPACE pg_default;

create index IF not exists daily_ticker_time_idx on public.daily using btree (ticker, date desc) TABLESPACE pg_default;

select create_hypertable('daily', by_range('date'));
