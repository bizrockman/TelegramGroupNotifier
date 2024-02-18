create table
  public.t_telegram_groups (
    id uuid not null default gen_random_uuid (),
    telegram_group_name character varying null,
    telegram_group_chat_id bigint null,
    created_at timestamp with time zone not null default now(),
    constraint t_telegram_groups_pkey primary key (id)
  ) tablespace pg_default;