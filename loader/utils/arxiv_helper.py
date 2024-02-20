import os

from .custom_exceptions import NoArgumentError, GetRequestError, NoCategoryError
import warnings
import datetime as dt
import requests
import feedparser
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

## @package Library.arxiv_lib
#  Small library for making requests to the arXiv and parsing the results.
#
#  This library provides some methods to send requests to the arXiv (using their API),
#  and to parse and format the results. The library includes methods to perform simple
#  searches on the arXiv, as well as to read the daily RSS feeds, and to parse and extract
#  the relevant information to be sent to the users.

"""
This class is used to load the data from the arXiv and to provide the data to the bot.

Inspired by https://github.com/carlosparaciari/ArXivBot
"""


## List of all the categories of the arXiv.
ALL_CATEGORIES = ['stat.AP', 'stat.CO', 'stat.ML', 'stat.ME', 'stat.OT', 'stat.TH', 'stat', 'q-fin.PR', 'q-fin.RM',
                  'q-fin.PM', 'q-fin.TR',
                  'q-fin.MF', 'q-fin.CP', 'q-fin.ST', 'q-fin.GN', 'q-fin.EC', 'q-fin', 'q-bio.BM', 'q-bio.GN',
                  'q-bio.MN', 'q-bio.SC', 'q-bio.CB', 'q-bio.NC',
                  'q-bio', 'q-bio.TO', 'q-bio.PE', 'q-bio.QM', 'q-bio.OT', 'cs.AI', 'cs.CL', 'cs.CC', 'cs.CE', 'cs.CG',
                  'cs.GT', 'cs.CV', 'cs.CY', 'cs.CR',
                  'cs.DS', 'cs.DB', 'cs.DL', 'cs.DM', 'cs.DC', 'cs.ET', 'cs.FL', 'cs.GL', 'cs.GR', 'cs.AR', 'cs.HC',
                  'cs.IR', 'cs.IT', 'cs.LG', 'cs.LO', 'cs.MS',
                  'cs.MA', 'cs.MM', 'cs.NI', 'cs.NE', 'cs.NA', 'cs.OS', 'cs.OH', 'cs.PF', 'cs.PL', 'cs.RO', 'cs.SI',
                  'cs.SE', 'cs.SD', 'cs.SC', 'cs.SY', 'cs',
                  'astro-ph.GA', 'astro-ph.CO', 'astro-ph.EP', 'astro-ph.HE', 'astro-ph.IM', 'astro-ph.SR', 'astro-ph',
                  'cond-mat.dis-nn', 'cond-mat.mtrl-sci',
                  'cond-mat.mes-hall', 'cond-mat.other', 'cond-mat.quant-gas', 'cond-mat.soft', 'cond-mat.stat-mech',
                  'cond-mat.str-el', 'cond-mat.supr-con',
                  'cond-mat', 'gr-qc', 'hep-ex', 'hep-lat', 'hep-ph', 'hep-th', 'math-ph', 'nlin.AO', 'nlin.CG',
                  'nlin.CD', 'nlin.SI', 'nlin.PS', 'nlin',
                  'nucl-ex', 'nucl-th', 'physics', 'physics.acc-ph', 'physics.app-ph', 'physics.ao-ph',
                  'physics.atom-ph', 'physics.atm-clus', 'physics.bio-ph',
                  'physics.chem-ph', 'physics.class-ph', 'physics.comp-ph', 'physics.data-an', 'physics.flu-dyn',
                  'physics.gen-ph', 'physics.geo-ph',
                  'physics.hist-ph', 'physics.ins-det', 'physics.med-ph', 'physics.optics', 'physics.ed-ph',
                  'physics.soc-ph', 'physics.plasm-ph',
                  'physics.pop-ph', 'physics.space-ph', 'econ', 'eess', 'quant-ph', 'math', 'math.AG', 'math.AT',
                  'math.AP', 'math.CT', 'math.CA', 'math.CO',
                  'math.AC', 'math.CV', 'math.DG', 'math.DS', 'math.FA', 'math.GM', 'math.GN', 'math.GT', 'math.GR',
                  'math.HO', 'math.IT', 'math.KT', 'math.LO',
                  'math.MP', 'math.MG', 'math.NT', 'math.NA', 'math.OA', 'math.OC', 'math.PR', 'math.QA', 'math.RT',
                  'math.RA', 'math.SP', 'math.ST', 'math.SG']

def number_categories():
    return len(ALL_CATEGORIES)


## This function takes an integer \f$i\f$ and returns the \f$i\f$-th category in the list ALL_CATEGORY.
#
#  @param category_index Integer number
def single_category(category_index):
    if not isinstance(category_index, int):
        raise TypeError('The index is not an integer.')

    if len(ALL_CATEGORIES) > category_index >= 0:
        return ALL_CATEGORIES[category_index]
    else:
        raise IndexError('The module-scope list ALL_CATEGORY has no element ' + str(category_index) + '.')


## This function reviews the dictionary obtained from parse_response and returns title, author and link for each entry.
#
#  Only title, author and link are passed since they will go to the Telegram Bot.
#  The output of this function is therefore a list of dictionary with these entries.
#  Two different behaviours are expected from this function, depending on the
#  value of feed_type, which can be API or RSS (the first is used for searches,
#  the second for new submissions)
#
#  @param dictionary This is the output of the function @ref parse_response
#  @param max_number_authors The maximum number of authors to be shown (then they are replaced by 'et al.')
#  @param feed_type The type of feed to review (can be API or RSS)
def review_response(dictionary, max_number_authors, feed_type):
    results_list = []

    if not isinstance(max_number_authors, int):
        raise TypeError('The number of authors has to be an integer.')

    if max_number_authors < 1:
        raise ValueError('The maximum number of authors has to be bigger than 1.')

    if not isinstance(dictionary, dict):
        raise TypeError('The argument passed is not a dictionary.')

    try:
        if not isinstance(dictionary['entries'], list):
            raise TypeError('The field entries is corrupted.')
    except KeyError:
        raise NoArgumentError('No entries have been found during the search.')

    for entry in dictionary['entries']:

        if not isinstance(entry, dict):
            raise TypeError('One of the entries is corrupted.')

        if feed_type == 'API':
            element = {'title': prepare_title_field_API(entry),
                       'authors': prepare_authors_field_API(entry, max_number_authors),
                       'date': find_publishing_date(entry)}
        elif feed_type == 'RSS':
            if is_update(entry):
                continue
            element = {'title': prepare_title_field_RSS(entry),
                       'authors': prepare_authors_field_RSS(entry, max_number_authors),
                       'description': is_field_there(entry, 'description')}
        else:
            raise ValueError('Wrong feed type. It can only be API or RSS.')

        element['link'] = is_field_there(entry, 'link')

        # Check whether all field in the element are None
        is_empty = element['title'] is None and element['authors'] is None and element['link'] is None

        if not is_empty:
            results_list.append(element)

    if len(results_list) == 0:
        raise NoArgumentError('No entries have been found during the search.')

    return results_list


## This function formats the title, and is needed for the review_response.
#
#  This function removes the newline symbols \n from the title, and escapes the
#  HTML symbols <, >, &, so that they are correctly interpreted by telepot.send_message().
#
#  @param dictionary This is the output of the function @ref parse_response
def prepare_title_field_API(dictionary):
    title = is_field_there(dictionary, 'title')

    if isinstance(title, str):
        title = title.replace(u'\n', u'')
        title = title.replace(u'  ', u' ')
        return title
    else:
        return None


## This function formats the authors, and is needed for the review_response.
#
#  This function unifies the name of the authors in a single one, and returns a Unicode string (if there are some authors).
#  It also cuts the number of authors after max_number_authors, and replaces the remaining with 'et al.'
#
#  @param dictionary This is the output of the function @ref parse_response
#  @param max_number_authors The maximum number of authors to be shown (then they are replaced by 'et al.')
def prepare_authors_field_API(dictionary, max_number_authors):
    authors_list = is_field_there(dictionary, 'authors')
    authors_string = ''
    authors_number = 1

    if isinstance(authors_list, list):
        for author in authors_list:
            author_name = is_field_there(author, 'name')
            if authors_number > max_number_authors:
                authors_string = authors_string + u'et al.**'
                break
            if isinstance(author_name, str) and authors_number <= max_number_authors:
                authors_number += 1
                authors_string = authors_string + author_name + ', '

    else:
        return None

    # Check if we have something in the authors string
    if len(authors_string) == 0:
        return None
    else:
        authors_string = authors_string[: -2]
        return authors_string


## This function prepares the title, and is needed for the review_response.
#
#  This function prepares the title field after receiving an entry from the RSS feed.
#  The main difference with the API search is the presence of the arXiv id, which is removed.
#
#  @param dictionary This is the output of the function @ref parse_response
def prepare_title_field_RSS(dictionary):
    title = prepare_title_field_API(dictionary)

    return title


## This function formats the authors, and is needed for the review_response.
#
#  This function prepares the authors field after receiving an entry from the RSS feed.
#  The function is different from the one used for standard search feeds as the authors
#  are given in a single line and hyper links are present. This function remove hyper links
#  and cut the number of authors if they are more than a maximum value
#
#  @param dictionary This is the output of the function @ref parse_response
#  @param max_number_authors The maximum number of authors to be shown (then they are replaced by 'et al.')
def prepare_authors_field_RSS(dictionary, max_number_authors):
    authors_string = is_field_there(dictionary, 'author')

    if isinstance(authors_string, str):
        end_string = authors_count_same_string(authors_string, max_number_authors)
        if end_string != -1:
            authors_string = authors_string[:end_string] + u', et al.'
        authors_string = remove_hyperlinks(authors_string)
        return authors_string
    else:
        return None


## This function returns the date of the RSS feed (as a datetime object).
#
#  This function looks in the dictionary prepared by @ref parse_response, and
#  finds the date in which the RSS feed was published.
#
#  @param dictionary This is the output of the function @ref parse_response
def find_date_RSS(dictionary):
    feed_details = is_field_there(dictionary, 'feed')
    feed_date = is_field_there(feed_details, 'updated')

    if feed_date is not None:
        if isinstance(feed_date, str) and len(feed_date) > 16:
            feed_date = feed_date[:16]
            feed_datetime = dt.datetime.strptime(feed_date, '%a, %d %b %Y')
            return feed_datetime
        else:
            raise TypeError('The argument passed is not a date string.')
    else:
        raise NoArgumentError('The RSS feed does not have the publication date.')


## This function removes hyper links, and is needed for the prepare_authors_field_RSS.
#
#  This function removes the hyper links (<a href = ***> ... </a>) from a string,
#  and return a unicode string.
#
#  @param string A string with hyper links inside
def remove_hyperlinks(string):
    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

    bs_string = BeautifulSoup(string, 'html.parser')

    for hlink in bs_string.findAll('a'):
        hlink.replaceWithChildren()

    return str(bs_string)


## This function finds where to put 'et al.' in the author string, and is needed for the prepare_authors_field_RSS.
#
#  This function finds the position of the "max_number_authors"-th comma in the string,
#  and returns it. If this comma doesn't exist, return -1.
#
#  @param authors_string A string with all the authors
#  @param max_number_authors The maximum number of authors to be shown (then they are replaced by 'et al.')
def authors_count_same_string(authors_string, max_number_authors):
    index = -1

    for iteration in range(max_number_authors):
        index = authors_string.find(',', index + 1)
        if index == -1:
            break

    return index


## This function checks whether the entry is new or updated, and is needed for the @ref review_response function.
#
#  This function checks if the entry is an update of a previous version of the paper.
#  Return True if it is, and False if is not. If the title field is absent, returns True.
#
#  @param dictionary This is the output of the function @ref parse_response
def is_update(dictionary):
    title = is_field_there(dictionary, 'title')

    if title is not None:
        index = title.find('UPDATED')
        if index == -1:
            return False

    return True


## This function returns the total number of results in the search.
#
#  @param dictionary This is the output of the function @ref parse_response
def total_number_results(dictionary):
    if not isinstance(dictionary, dict):
        raise TypeError('The argument passed is not a dictionary.')

    feed_information = is_field_there(dictionary, 'feed')

    if feed_information is None:
        raise NoArgumentError('No feed have been returned by the search.')

    if not isinstance(feed_information, dict):
        raise TypeError('The field feed is corrupted.')

    total_results = is_field_there(feed_information, 'opensearch_totalresults')

    if total_results is None:
        raise NoArgumentError('The feed got corrupted.')

    return int(total_results)


## This function checks if a key is inside a dictionary, and is needed for the @ref review_response function.
#
#  This function checks that the dictionary has something associated to the key, and if not, it returns None.
#
#  @param dictionary This is the output of the function @ref parse_response
#  @param key This is a key which might be in the dictionary
def is_field_there(dictionary, key):
    try:
        return dictionary[key]
    except:
        return None


## This function finds the publishing date of a given entry, and is needed for the @ref review_response function.
#
#  This function returns a datetime object.
#
#  @param dictionary This is the output of the function @ref parse_response
def find_publishing_date(dictionary):
    date = is_field_there(dictionary, 'published')

    if isinstance(date, str) and len(date) > 10:
        date = date[0:10]
        date = dt.datetime.strptime(date, '%Y-%m-%d')
        return date
    else:
        return None


## This function parses the output of the @ref request_to_arxiv function.
#
#  This function modifies the response obtained by the request library, making it a raw data (string).
#  Then, it parses the raw data using FeedParser, and returns a dictionary.
#
#  @param response This is the output of the function @ref request_to_arxiv
def parse_response(response):
    if not isinstance(response, requests.models.Response):
        raise TypeError('The argument passed is not a Response object.')

    rawdata = response.text

    parsed_response = feedparser.parse(rawdata)

    return parsed_response


## This function communicates with the arXiv and download the information.
#
#  @param arxiv_search_link The link to the arXiv website
def request_to_arxiv(arxiv_search_link):
    if not isinstance(arxiv_search_link, str):
        raise TypeError('The argument passed is not a string.')

    # Making a query to the arXiv
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        }
        response = requests.get(arxiv_search_link, headers=headers)
    except requests.exceptions.InvalidSchema as invalid_schema:
        raise invalid_schema
    except requests.exceptions.MissingSchema as missing_schema:
        raise missing_schema
    except:
        raise GetRequestError('Get from arXiv failed. Might be connection problem. Used: ' + arxiv_search_link)

    # Check the status of the response
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as connection_error:
        raise connection_error
    else:
        return response


## This function adds to the arXiv link an extra field, which specifies the number of results we want to obtain.
#
#  **NOTE**: This function is not used any more, since @ref simple_search now takes care of this.
#
#  @param arxiv_search_link The link to the arXiv website
#  @param number_of_results An integer number
def specify_number_of_results(arxiv_search_link, number_of_results):
    if number_of_results < 0:
        raise ValueError('The number of results you are interested in cannot be negative.')

    arxiv_search_link += '&max_results=' + str(number_of_results)

    return arxiv_search_link


## This function adds a specific category to the arXiv RSS link.
#
#  @param subject_category A category of the arXiv
#  @param arxiv_search_link The link to the arXiv website
def search_day_submissions(subject_category, arxiv_search_link):
    if not category_exists(subject_category):
        raise NoCategoryError('The passed category is not in the ArXiv')

    arxiv_search_link += subject_category

    return arxiv_search_link


## This function checks whether a category exists.
#
#  @param subject_category A (possible) category of the arXiv
def category_exists(subject_category):
    return subject_category in ALL_CATEGORIES


## This function prepare the query for each field
#
#  The field query is composed by a key (for example, au: for author), one or more
#  values, and some connectors (AND, or OR). Values is a list of unicode strings, and
#  each string can be a single word or a sentence. In the latter case, quotes need to be used.
#
#  @param key The field of the query
#  @param values A list of strings
#  @param connector The logic connector (can be AND or OR)
#  @param quote The quotes are needed for strings with multiple words
def prepare_field_query(key, values, connector, quote=''):
    query_search_string = ''

    if isinstance(values, list):
        for value in values:
            if isinstance(value, str):
                query_search_string += key + quote + value + quote + connector
        query_search_string = query_search_string[: - len(connector)]

    return query_search_string


## This function performs a search the arXiv.
#
#  This function assembles the link for the request to arXiv, which will be passed
#  to the @ref request_to_arxiv function. The search is made using some keywords,
#  but additional options can be added. It is possible to add one or more authors,
#  part of the title, one or more categories where to search in, and the time
#  interval (in years).
#
#  @param keywords a list of keywords of the search
#  @param arxiv_search_link The link to the arXiv website
#  @param start_num The number of the initial result
#  @param max_num The maximum number of shown results
#  @param authors The authors list (optional)
#  @param title The title (optional)
#  @param categories The categories (optional)
#  @param interval The time interval (optional)
def simple_search(keywords, arxiv_search_link, start_num, max_num, authors=None, title=None, categories=None,
                  interval=None):
    if authors is None:
        authors = []
    if title is None:
        title = []
    if categories is None:
        categories = []
    if interval is None:
        interval = []

    con_AND = '+AND+'
    con_OR = '+OR+'
    brackets = ['%28', '%29']
    start_opt = '&start='
    max_opt = '&max_results='

    length_check = len(arxiv_search_link)

    query_fields = [{'key': 'all:', 'values': keywords, 'connector': con_AND, 'quotes': ''},
                    {'key': 'au:', 'values': authors, 'connector': con_AND, 'quotes': '%22'},
                    {'key': 'ti:', 'values': title, 'connector': con_AND, 'quotes': '%22'},
                    {'key': 'cat:', 'values': categories, 'connector': con_OR, 'quotes': ''}
                    ]

    for query_field in query_fields:
        query_string = prepare_field_query(query_field['key'],
                                           query_field['values'],
                                           query_field['connector'],
                                           query_field['quotes']
                                           )
        if len(query_string) != 0:
            if query_field['key'] == 'cat:':
                query_string = brackets[0] + query_string + brackets[1]
            arxiv_search_link += query_string + con_AND

    if len(arxiv_search_link) == length_check:
        raise NoArgumentError('No arguments have been provided to the search.')
    else:
        arxiv_search_link = arxiv_search_link[: - len(con_AND)]

    # Prepare interval as submittedDate:[initial+TO+final]

    arxiv_search_link += start_opt + str(start_num) + max_opt + str(max_num)

    return arxiv_search_link


def send_and_parse_request(search_link):
    try:
        search_response = request_to_arxiv(search_link)
    except TypeError as TE:
        print('The url got corrupted. Try again!')
        # self.save_known_error_log(chat_identity, TE)
        raise
    except GetRequestError as GRE:
        print('The search arguments are fine, but the search on the arXiv failed.')
        # self.save_known_error_log(chat_identity, GRE)
        raise
    except requests.exceptions.HTTPError as HTTPE:
        print('We are currently experiencing connection problems, sorry!')
        # self.save_known_error_log(chat_identity, HTTPE)
        raise

    try:
        search_dictionary = parse_response(search_response)
    except TypeError as TE:
        print('The result of the search got corrupted.')
        # self.save_known_error_log(chat_identity, TE)
        raise

    return search_dictionary


def do_today_search(arxiv_category=None, limit=None):
    if arxiv_category is None:
        arxiv_category = os.getenv('DEFAULT_CATEGORY')

    try:
        today_search_link = search_day_submissions(arxiv_category, os.getenv('ARXIV_RSS_LINK'))
    except NoCategoryError:
        print('Please use the arXiv subjects.\nSee http://arxitics.com/help/categories for further information.')
        # TODO Make a DB logging system self.save_unknown_error_log(chat_identity, 'arxiv_lib.search_day_submissions')
        return None

    search_list, feed_date = search_and_format_RSS(today_search_link)

    total_results = len(search_list)

    max_rss_result_number = int(os.getenv('MAX_RSS_RESULT_NUMBER')) if limit is None or limit < 0 else limit
    search_list = search_list[:max_rss_result_number]
    remaining_results = total_results - max_rss_result_number

    return send_results_back_rss(search_list, remaining_results, arxiv_category, feed_date)


def search_and_format_RSS(search_link):

    search_dictionary = send_and_parse_request(search_link)
    max_number_authors = int(os.getenv('MAX_NUMBER_AUTHORS'))

    try:
        search_list = review_response(search_dictionary, max_number_authors, 'RSS')
    except NoArgumentError:
        print('There are no submissions to your favourite category today, try tomorrow!')
        raise
    except TypeError as TE:
        print('The result of the search got corrupted.')
        # self.save_known_error_log(chat_identity, TE)
        raise
    except ValueError as VE:
        print('We are experiencing some technical problems, sorry!')
        # self.save_known_error_log(chat_identity, VE)
        raise

    try:
        feed_date = find_date_RSS(search_dictionary)
    except NoArgumentError as NAE:
        print('The result of the search got corrupted.')
        # self.save_known_error_log(chat_identity, NAE)
        raise
    except TypeError as TE:
        print('The result of the search got corrupted.')
        # self.save_known_error_log(chat_identity, TE)
        raise

    return search_list, feed_date


def check_size_and_split_message(message, new_item):

    message_would_exceed = len(message) + len(new_item) >= int(os.getenv('MAX_CHARACTERS_CHAT'))
    if message_would_exceed:
        message = ''
    message += new_item

    return message


def send_results_back_rss(search_list, remaining_results, arxiv_category, feed_date):

    result_counter = 1
    today = feed_date + dt.timedelta(days=1)
    message_result = 'List of submissions to <b>' + arxiv_category + '</b> for today ' + today.strftime(
        "%a, %d %b %y") + '.\n\n'

    message_result = []
    now = dt.datetime.now()

    for result in search_list:
        description = result['description'].split('Abstract: ')[1]
        new_item = {
            'title': result['title'],
            'authors': result['authors'],
            'description': description,
            'date': now.strftime("%d.%m.%Y"),
            'link': result['link']
        }

        message_result.append(new_item)

        result_counter += 1

    if remaining_results > 0:
        remaining_information = {
            'title': 'Remaining Information',
            'description': f'There are {remaining_results} remaining submissions today. Consider visiting the '
                           f'arXiv web-page to see them.'
        }

        # Hinzufügen der verbleibenden Informationen als neues Item
        message_result.append(remaining_information)

    return message_result
