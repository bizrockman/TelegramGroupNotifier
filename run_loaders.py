import datetime
import time

from dotenv import load_dotenv

from loader import ZoteroLoader, ArxivLoader, GitHubLoader, CivitaiLoader

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


def zotero_arxiv_loader_job():
    telegram_group_topic_id = 2
    template_file_name = 'arxiv_loader_template.html'
    arxiv_csai_loader = ArxivLoader(telegram_group_topic_id=telegram_group_topic_id,
                                    template_file_name=template_file_name,
                                    default_category='cs.AI')
    arxiv_csai_loader.load()


def zotero_github_loader_job():
    telegram_group_topic_id = 20
    template_file_name = 'zotero_loader_github_template.html'
    zotero_github_loader = ZoteroLoader(telegram_group_topic_id=telegram_group_topic_id,
                                        template_file_name=template_file_name, collection_name='Github', limit=5)
    zotero_github_loader.load()


def zotero_prompts_loader_job():
    telegram_group_topic_id = 26
    template_file_name = 'zotero_loader_prompts_template.html'
    zotero_github_loader = ZoteroLoader(telegram_group_topic_id=telegram_group_topic_id,
                                        template_file_name=template_file_name,
                                        collection_name='Projekte/Prompts/PromptSammlung',
                                        limit=5,
                                        all_types=True)
    zotero_github_loader.load()


def github_loader_job():
    telegram_group_topic_id = 20
    template_file_name = 'github_loader_trending_template.html'
    github_loader = GitHubLoader(telegram_group_topic_id=telegram_group_topic_id,
                                 template_file_name=template_file_name)
    github_loader.load()


def civitas_image_loader_job():
    telegram_group_topic_id = 27
    template_file_name = 'civitas_loader_template.html'
    civitai_image_loader = CivitaiLoader(telegram_group_topic_id=telegram_group_topic_id,
                                         template_file_name=template_file_name)
    civitai_image_loader.load()


def civitas_video_loader_job():
    telegram_group_topic_id = 28
    template_file_name = 'civitas_loader_template.html'
    civitai_video_loader = CivitaiLoader(telegram_group_topic_id=telegram_group_topic_id,
                                         template_file_name=template_file_name,
                                         media_type='video')
    civitai_video_loader.load()


def main():
    load_dotenv()

    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    }

    # Berechne die Startzeiten
    now = datetime.datetime.now()
    start_in_10_min = now + datetime.timedelta(minutes=10)
    start_in_30_min = now + datetime.timedelta(minutes=30)

    scheduler = BackgroundScheduler(jobstores=jobstores)
    scheduler.add_job(zotero_arxiv_loader_job, 'interval', hours=1, next_run_time=now)
    scheduler.add_job(zotero_github_loader_job, 'interval', hours=1, next_run_time=start_in_10_min)
    scheduler.add_job(zotero_prompts_loader_job, 'interval', hours=1, next_run_time=start_in_30_min)
    scheduler.add_job(github_loader_job, 'interval', weeks=1, next_run_time=now)
    scheduler.add_job(civitas_image_loader_job, 'interval', days=1, next_run_time=now)
    scheduler.add_job(civitas_video_loader_job, 'interval', days=1, next_run_time=start_in_10_min)
    scheduler.start()

    try:
        # Damit das Skript läuft, bis es manuell gestoppt wird
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
