create table
  public.t_telegram_group_topics (
    id uuid not null default gen_random_uuid (),
    t_telegram_group_id uuid null,
    group_topic_name character varying null,
    group_topic_id bigint null,
    created_at timestamp with time zone not null default now(),
    constraint t_telegram_group_topics_pkey primary key (id)
  ) tablespace pg_default;