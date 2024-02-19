import os

from datetime import datetime, timedelta
from dotenv import load_dotenv

from supabase import Client, create_client
from utils import ZoteroHelper
from string import Template


class ZoteroLoader:

    def __init__(self, telegram_group_topic_id, supabase_url, supabase_key, zotero_api_key, library_id,
                 library_type='user'):
        self.creator_name = 'ZoteroLoader'
        self.group_topic_id = telegram_group_topic_id

        self.supabase_client: Client = create_client(supabase_url, supabase_key)
        self.zotero_helper = ZoteroHelper(zotero_api_key, library_id, library_type)

        self.template_path = os.path.join(os.path.dirname(__file__), 'templates', 'zotero_loader_arxiv_template.html')

    def load(self, collection_name, limit=1):
        # Get date from the latest message to the telegram table - using topic / reporter
        latest_message_date = self.get_latest_message_date()
        print(latest_message_date)
        # Get everything what is new in the defined collection after that date
        entries = (self.zotero_helper
                   .get_latest_created_after_by_collection_name(latest_message_date, collection_name, limit=5))

        for entry in entries:
            # print(entry)
            message = self.create_telegram_message(entry)
            self.save_telegram_message_to_supabase(message)

    def create_telegram_message(self, entry):
        with open(self.template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()

        template_data = {
            'title': entry['data']['title'],
            'abstractNote': entry['data']['abstractNote'],
            'date': entry['data']['date'],
            'url': entry['data']['url']
        }

        template = Template(template_content)
        return template.safe_substitute(template_data)

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

        if result.error:
            print("Fehler beim Speichern der Nachricht:", result.error)
        else:
            print("Nachricht erfolgreich gespeichert.")


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


def main():
    load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    zoter_key = os.getenv('ZOTERO_API_KEY')
    library_id = os.getenv('ZOTERO_USER_ID')
    telegram_group_topic_id = 2

    zotero_loader = ZoteroLoader(telegram_group_topic_id, supabase_url, supabase_key, zoter_key, library_id)
    zotero_loader.load('Papers/arxiv', limit=5)


if __name__ == "__main__":
    main()
