import os
from string import Template

from datetime import datetime, timedelta

from supabase import Client, create_client


class LoaderBase:

    def __init__(self, group_topic_id, creator_name, template_file_name, supabase_url=None, supabase_key=None):

        supabase_url = os.getenv("SUPABASE_URL") if not supabase_url else supabase_url
        supabase_key = os.getenv("SUPABASE_KEY") if not supabase_key else supabase_key

        self.supabase_client: Client = create_client(supabase_url, supabase_key)

        self.group_topic_id = group_topic_id
        self.creator_name = creator_name

        self.template_path = os.path.join(os.path.dirname(__file__), 'templates', template_file_name)

    def get_latest_message_date(self):
        # Get date from the latest message to the telegram table - using topic / reporter
        result = self.supabase_client.table('v_telegram_messages_with_topics') \
            .select('created_at') \
            .eq('group_topic_id', self.group_topic_id) \
            .eq('creator', self.creator_name) \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()

        if result.data:
            # Gehe davon aus, dass `created_at` das Datum beinhaltet
            return datetime.fromisoformat(result.data[0]['created_at'])
        else:
            return datetime.now() - timedelta(weeks=1)

    def find_group_topic_uuid(self):
        result = self.supabase_client.table('t_telegram_group_topics') \
            .select('id') \
            .eq('group_topic_id', self.group_topic_id) \
            .execute()

        if result.data:
            # Nehmen Sie die erste Übereinstimmung an
            return result.data[0]['id']
        else:
            return None

    def create_telegram_message(self, template_data):
        with open(self.template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()

        template = Template(template_content)
        return template.safe_substitute(template_data)

    def save_telegram_message_to_supabase(self, message, schedule_for=None):
        group_topic_uuid = self.find_group_topic_uuid()
        if not group_topic_uuid:
            print("Keine entsprechende group_topic_id gefunden.")
            return

        # Datenstruktur für die neue Nachricht
        message_data = {
            't_telegram_group_topic_id': group_topic_uuid,
            'content': message,
            'creator': self.creator_name,
            'status': 'planned'
        }

        # Füge `schedule_for` hinzu, wenn ein Zeitpunkt angegeben ist
        if schedule_for:
            message_data['schedule_for'] = schedule_for

        # Speichern der Nachricht in der Tabelle `t_telegram_messages`
        result = self.supabase_client.table('t_telegram_messages') \
            .insert(message_data) \
            .execute()
