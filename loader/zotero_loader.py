import os

from dotenv import load_dotenv
from loader.utils import ZoteroHelper

from loader import LoaderBase


class ZoteroLoader(LoaderBase):

    def __init__(self, telegram_group_topic_id, template_file_name, collection_name=None, limit=None, all_types=False,
                 zotero_api_key=None, zotero_library_id=None, zotero_library_type='user', supabase_url=None,
                 supabase_key=None):

        zotero_api_key = os.getenv('ZOTERO_API_KEY') if zotero_api_key is None else zotero_api_key
        zotero_library_id = os.getenv('ZOTERO_USER_ID') if zotero_library_id is None else zotero_library_id

        self.collection_name = collection_name
        self.limit = limit
        self.all_types = all_types

        self.creator_name = 'ZoteroLoader'
        self.zotero_helper = ZoteroHelper(zotero_api_key, zotero_library_id, zotero_library_type)

        super().__init__(telegram_group_topic_id, self.creator_name, template_file_name, supabase_url, supabase_key)

    def retrieve(self, collection_name=None, limit=None):

        collection_name = self.collection_name if collection_name is None else collection_name
        limit = self.limit if limit is None else limit

        if collection_name is None or limit is None:
            raise ValueError('collection_name and limit must be defined')

        # Get date from the latest message to the telegram table - using topic / reporter
        latest_message_date = self.get_latest_message_date()
        print(latest_message_date)
        # Get everything what is new in the defined collection after that date
        entries = (self.zotero_helper
                   .get_latest_created_after_by_collection_name(latest_message_date, collection_name, limit=5,
                                                                all_types=self.all_types))
        return entries

    def load(self, collection_name=None, limit=None):
        entries = self.retrieve(collection_name, limit)
        for entry in entries:
            print(entry)
            template_data = {
                'title': entry['data'].get('title', ''),
                'abstractNote': entry['data'].get('abstractNote', ''),
                'date': entry['data'].get('date', ''),
                'rights': entry['data'].get('rights', ''),
                'url': entry['data'].get('url', ''),
            }

        #message = self.create_telegram_message(template_data)
        #self.save_telegram_message_to_supabase(message)


def main():
    load_dotenv()

    telegram_group_topic_id = 2
    template_file_name = 'zotero_loader_arxiv_template.html'

    zotero_loader = ZoteroLoader(telegram_group_topic_id=telegram_group_topic_id, template_file_name=template_file_name,)

    zotero_loader.load('Papers/arxiv', limit=5)


if __name__ == "__main__":
    main()
