reate table
  public.t_telegram_messages (
    id uuid not null default uuid_generate_v4 (),
    t_telegram_group_topic_id uuid null default gen_random_uuid (),
    content text null,
    media_content text null,
    media_url text null,
    media_type character varying(50) null,
    created_at timestamp with time zone null default current_timestamp,
    creator character varying(255) null,
    schedule_for timestamp with time zone null,
    sent_at timestamp with time zone null,
    status character varying(50) null default 'planned'::character varying,
    constraint t_telegram_messages_pkey primary key (id)
  ) tablespace pg_default;