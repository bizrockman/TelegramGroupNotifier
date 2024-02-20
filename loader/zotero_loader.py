import os

from datetime import datetime, timedelta
from string import Template
from dotenv import load_dotenv


from utils import ZoteroHelper

from . import LoaderBase


class ZoteroLoader(LoaderBase):

    def __init__(self, telegram_group_topic_id, template_file_name, zotero_api_key,
                 zotero_library_id, zotero_library_type='user', supabase_url=None, supabase_key=None):

        self.creator_name = 'ZoteroLoader'
        self.zotero_helper = ZoteroHelper(zotero_api_key, zotero_library_id, zotero_library_type)

        super().__init__(telegram_group_topic_id, self.creator_name, template_file_name, supabase_url, supabase_key)

    def load(self, collection_name, limit=1):
        # Get date from the latest message to the telegram table - using topic / reporter
        latest_message_date = self.get_latest_message_date()
        print(latest_message_date)
        # Get everything what is new in the defined collection after that date
        entries = (self.zotero_helper
                   .get_latest_created_after_by_collection_name(latest_message_date, collection_name, limit=5))

        for entry in entries:
            # print(entry)
            template_data = {
                'title': entry['data']['title'],
                'abstractNote': entry['data']['abstractNote'],
                'date': entry['data']['date'],
                'url': entry['data']['url']
            }

            message = self.create_telegram_message(template_data)
            self.save_telegram_message_to_supabase(message)


def main():
    load_dotenv()

    zotero_key = os.getenv('ZOTERO_API_KEY')
    zotero_library_id = os.getenv('ZOTERO_USER_ID')
    telegram_group_topic_id = 2
    template_file_name = 'zotero_loader_arxiv_template.html'

    zotero_loader = ZoteroLoader(telegram_group_topic_id=telegram_group_topic_id, template_file_name=template_file_name,
                                 zotero_api_key=zotero_key, zotero_library_id=zotero_library_id)

    zotero_loader.load('Papers/arxiv', limit=5)


if __name__ == "__main__":
    main()
