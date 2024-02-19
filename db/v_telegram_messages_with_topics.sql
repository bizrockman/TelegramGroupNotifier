CREATE VIEW v_telegram_messages_with_topics AS
SELECT
    msg.id,
    msg.content,
    msg.media_content,
    msg.media_url,
    msg.media_type,
    msg.created_at,
    msg.creator,
    msg.schedule_for,
    msg.sent_at,
    msg.status,
    tpc.group_topic_name,
    tpc.group_topic_id
FROM
    public.t_telegram_messages AS msg
LEFT JOIN
    public.t_telegram_group_topics AS tpc
ON
    msg.t_telegram_group_topic_id = tpc.id;