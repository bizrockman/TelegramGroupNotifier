import os
from typing import List, Any, Union

from dotenv import load_dotenv
from loader import LoaderBase

from loader.utils.allowed_github_parameter import AllowedDateRanges
from loader.utils.allowed_github_parameter import AllowedProgrammingLanguages
from loader.utils.allowed_github_parameter import AllowedSpokenLanguages

from loader.utils.scraping_helper import get_request, filter_articles, make_soup, scraping_repositories


class GitHubLoader(LoaderBase):
    def __init__(self, telegram_group_topic_id, template_file_name):
        self.creator_name = 'GitHubLoader'
        self.github_url = os.getenv('GITHUB_URL')

        super().__init__(telegram_group_topic_id, self.creator_name, template_file_name)

    def trending_repositories(self, since: AllowedDateRanges = None):
        """Returns data about trending repositories (all programming
        languages, cannot be specified on this endpoint)."""
        payload = {"since": "weekly"}

        if since:
            payload["since"] = since.value

        url = "https://github.com/trending"

        raw_html = get_request(url, payload)

        articles_html = filter_articles(raw_html)
        soup = make_soup(articles_html)
        return scraping_repositories(soup, since=payload[
            "since"])

    def retrieve(self):
        entries = self.trending_repositories()
        return entries

    def load(self, limit=5):
        entries = self.retrieve()
        entries = entries[:limit]

        final_message = 'Hier die wöchentlichen GitHub-Trends:\n\n'

        for entry in entries:

            template_data = {
                'rank': entry['rank'],
                'username': entry['username'],
                'repositoryName': entry['repositoryName'],
                'url': entry['url'],
                'description': entry['description'],
                'stars': entry['totalStars'],
                'starsSince': entry['starsSince'],
                'forks': entry['forks'],
            }

            final_message += self.create_telegram_message(template_data)

        self.save_telegram_message_to_supabase(final_message)


def main():
    load_dotenv()
    github_loader = GitHubLoader(telegram_group_topic_id=20, template_file_name='github_loader_trending_template.html')
    github_loader.load()


if __name__ == '__main__':
    main()
