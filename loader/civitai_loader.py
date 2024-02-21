import os
from urllib.parse import urlencode, urljoin

from dotenv import load_dotenv

from loader import LoaderBase
from loader.utils.scraping_helper import get_request_as_json


class CivitaiLoader(LoaderBase):

    VALID_PERIODS = ['AllTime', 'Year', 'Month', 'Week', 'Day']
    VALID_MEDIA_TYPES = ['image', 'video', 'model']
    VALID_NSFW_LEVELS = [None, 'Soft', 'Mature', 'X']

    def validate_parameters(self, media_type, period, nsfw):
        if period not in self.VALID_PERIODS:
            raise ValueError(f"period must be one of {self.VALID_PERIODS}")
        if media_type not in self.VALID_MEDIA_TYPES:
            raise ValueError(f"media_type must be one of {self.VALID_MEDIA_TYPES}")
        if nsfw not in self.VALID_NSFW_LEVELS:
            raise ValueError(f"nsfw must be one of {self.VALID_NSFW_LEVELS}")

    def build_url(self, base_url, media_type, nsfw, period, limit):
        path = f"{media_type}s"  # Append 's' to make it plural (image -> images, video -> videos, model -> models)
        params = {
            'nsfw': nsfw,
            'limit': limit,
            'period': period,
            'sort': 'Most Reactions'
        }
        query_string = urlencode({k: v for k, v in params.items() if v is not None})  # Exclude None values
        return urljoin(base_url, path) + '?' + query_string

    def __init__(self, telegram_group_topic_id, template_file_name, media_type='image', period='Day', nsfw=None):
        self.creator_name = 'CivitaiLoader'
        limit = 1
        self.validate_parameters(media_type, period, nsfw)
        base_url = os.getenv('CIVITAI_URL', '')
        # START - Workaround as long as there is no way to get videos directly from Civitai
        if media_type == 'video':
            media_type = 'image'
        # END - Workaround as long as there is no way to get videos directly from Civitai
        self.civitai_url = self.build_url(base_url, media_type, nsfw, period, limit)

        super().__init__(telegram_group_topic_id, self.creator_name, template_file_name)

    def retrieve(self):
        data = get_request_as_json(self.civitai_url)

        if isinstance(data, dict):
            return data
        else:
            # Fehlerbehandlung
            print(f"Es gab einen Fehler bei der Anfrage: {data}")

    def load(self):
        data = self.retrieve()

        data = data['items'][0]

        if data:
            template_data = {
                'media_url': data['url'],
                'likes': data['stats']['likeCount'],
                'hearts': data['stats']['heartCount'],
                'prompt': data['meta']['prompt'],
                'model': data['meta']['Model'].split('.')[0],
                'user': data['username'],
                'created_at': data['createdAt'],
            }
            message = self.create_telegram_message(template_data)
            self.save_telegram_message_to_supabase(message=message, media_url=template_data['media_url'],
                                                   media_type='image')


def main():
    load_dotenv()
    civitai_loader = CivitaiLoader(telegram_group_topic_id=27, template_file_name='civitai_loader_template.html',
                                   )
    civitai_loader.load()


if __name__ == '__main__':
    main()
