from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
import utils.arxiv_helper as ah
from utils import OpenAIHelper

from loader_base import LoaderBase


class ArxivLoader(LoaderBase):

    def __init__(self, telegram_group_topic_id, template_file_name, default_category='cs.AI', supabase_url=None,
                 supabase_key=None):
        self.creator_name = 'ArxivLoader'
        self.default_category = default_category

        self.oaih = OpenAIHelper()
        super().__init__(telegram_group_topic_id, self.creator_name, template_file_name, supabase_url, supabase_key)

    def create_system_message(self, ai_translate=False, lang=None, ai_summarize=False):
        system_msg = ''

        # TODO load the prompt snippets from a file
        if ai_translate:
            if not lang:
                print('Keine Zielsprache für die Übersetzung angegeben.')
            else:
                system_msg += f'Translate the Text. Target language is {lang}.\n\n'

        if ai_summarize:
            system_msg += 'Please summarize the content in ONE sentence: \n\n'

        return system_msg

    def load(self, default_category='cs.AI', limit=3, ai_summarize=True, ai_translate=True):
        #TODO getting language from group information saved in the database
        lang = 'de'

        # Get date from the latest message to the telegram table - using topic / reporter
        latest_message_date = self.get_latest_message_date().astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = now - latest_message_date

        if time_diff < timedelta(hours=24):
            total_seconds = time_diff.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            print(f"Weniger als 24 Stunden seit der letzten Nachricht vergangen: "
                  f"Vergangen bisher: {hours:02d}:{minutes:02d}")
            return

        # Get everything what is new in the defined collection after that date
        entries = ah.do_today_search(default_category, limit)
        #result['description'] = self.oih.gpt_35_response('In einem Satz auf Deutsch zusammenfassen.\n\n',
        #                                                 result['description'])
        for entry in entries:

            if ai_translate or ai_summarize:
                system_msg = self.create_system_message(ai_translate, lang, ai_summarize)
                description = self.oaih.gpt_35_response(system_msg, entry.get('description', ''))
            else:
                description = entry.get('description', '')

            if entry.get('link'):
                template_data = {
                    'title': entry.get('title', ''),
                    'authors': entry.get('authors', ''),  # Verwendung von get() mit Standardwert
                    'abstractNote': description,
                    'date': entry.get('date', ''),
                    'url': entry.get('link', ''),
                }

                message = self.create_telegram_message(template_data)
            else:
                message = description

            self.save_telegram_message_to_supabase(message)


def main():
    load_dotenv()

    telegram_group_topic_id = 2
    template_file_name = 'arxiv_loader_template.html'
    arxiv_loader = ArxivLoader(telegram_group_topic_id=telegram_group_topic_id, template_file_name=template_file_name,
                               default_category='cs.AI')

    messages = arxiv_loader.load(ai_summarize=True, ai_translate=True)
    #for message in messages:
    #    print(message)


if __name__ == '__main__':
    main()
