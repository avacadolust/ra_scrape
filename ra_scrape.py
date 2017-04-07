# get album data

# impot modules for url requests
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
import pickle  # pickle for saving objects
import re  # regex model for pattern matching
from bs4 import BeautifulSoup  # beautiful soup for parsing html
from pprint import pprint  # pprint for
import datetime
import time
import logging
import random


# below settings setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh = logging.FileHandler('ra_scrape_' + datetime.datetime.now().strftime("%d%m%Y_%H%M") + '.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)
pickle_file_name = 'ra_data' + datetime.datetime.now().strftime("%d%m%Y_%H%M") + '.pickle'
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

# increase the url helper function


def increase_url(prev_url):
    return str(int(prev_url[40:44]) + 1)

# parse out event and other reviews


def is_release_review(soup):
    type_url = soup.find(['a'], {'href': ["/reviews.aspx?format=album",
                                          "/reviews.aspx?format=single"]},
                         text={'Singles ', 'Albums '}
                         )
    if type_url:
        return type_url.getText()[:-2]


def get_publishing_date(soup):
    date_published = soup.find('span',
                               {'itemprop': 'dtreviewed'}
                               )['datetime']
    return date_published


def get_release_date(soup):
    date_released = soup.find(text=re.compile('Released')).parent.parent
    _ = date_released.div.decompose()
    date_released = date_released.getText().strip()
    return date_released


def get_artist_title(soup):
    artist = soup.body.h1.text.split("-")[0].strip()
    title = soup.body.h1.text.split("-")[1].strip()
    return artist, title


def get_rating(soup):
    rating = float(soup.find('span',
                             {'class': 'rating'}).getText().split('/')[0])
    return rating


def get_label_and_cat(soup):
    ret = []
    ret = soup.find(text=re.compile('Label /')).parent.parent

    ret.div.decompose()
    label = ret.a.text.strip()
    ret.a.decompose()
    cat = (ret.text.strip())
    return label, cat


def get_review_text(soup):
    page_text = (soup.find('span', {"class": "reading-line-height"}).find_all_next(string=True))
    review_end = (page_text.index('Published /'))
    review_text = ''.join(page_text[:review_end]).strip()
    return review_text


def get_styles(soup):

    styles = soup.find(text=re.compile('Style /')).parent.parent
    styles.div.decompose()
    styles = [x.strip() for x in styles.getText().split(',')]
    return styles


def get_author(soup):
    author = soup.find('a', {'rel': 'author'}).getText()  # text=re.compile('Released')).parent.parent
    return author


def get_tracklist(soup):
    if soup.find(text=re.compile('Tracklist /')).parent.parent == True:
        tracklist = soup.find(text=re.compile('Tracklist /')).parent.parent
        tracklist.span.decompose()

        tracklist = re.split(r"[~\r\n]+", tracklist.getText().strip())
        return tracklist
    return None


def get_comments_number(soup):
    n_comments = soup.find(text=re.compile('Comments /')).parent.parent
    n_comments.div.decompose()
    n_comments = n_comments.getText().split()[0]
    return n_comments


def get_soup_elements(soup):
    review_id = int(request.geturl()[40:].rstrip("/"))
    review_type = is_release_review(soup)
    if not review_type:
        logger.info('Album or Single Review type not found : ' + request.geturl())

        return None
    logger.info('Album or Single Review type found!|  @ : ' + request.geturl())

# initialise dict
    ra_data[review_id] = {}
# fill in the rest of the elements
    ra_data[review_id]['review_type'] = review_type
    ra_data[review_id]['date_published'] = get_publishing_date(soup)
    ra_data[review_id]['date_released'] = get_release_date(soup)
    ra_data[review_id]['rating'] = get_rating(soup)
    ra_data[review_id]['n_comments'] = get_comments_number(soup)
    ra_data[review_id]['author'] = get_author(soup)
    ra_data[review_id]['styles'] = get_styles(soup)
    ra_data[review_id]['label'], ra_data[review_id]['cat'] = get_label_and_cat(soup)

    ra_data[review_id]['artist'], ra_data[review_id]['title'] = get_artist_title(soup)

    ra_data[review_id]['review_text'] = get_review_text(soup)
    try:
        ra_data[review_id]['tracklist'] = get_tracklist(soup)
    except Exception as e:
        logging.info('no tracklist tracklist provided error is ' + str(e))


def get_fresh_url(prev_url):
    while True:
        new_url = "https://www.residentadvisor.net/reviews/" + increase_url(prev_url) + "/"
        request = urlopen(new_url)
        try:
            current_url = request.geturl()  # check for redirect
        except HTTPError as e:
            logger.info(e, "@", current_url)
        if current_url == new_url:  # check for redirect
            logging.info('valid review page found @ ' + current_url)
            return request, current_url
        logging.info('Review not found, page redirected @ ' + new_url)
        # reset the new url
        prev_url = new_url


def dump_remains(soup, ra_data):

    pickle.dump(ra_data, open(pickle_file_name, "wb"), protocol=2)  # setting protocol number for py2 compatibility

# below test urls
#("https://www.residentadvisor.net/reviews/7520") # single
#(https://www.residentadvisor.net/reviews/7521) # album


if __name__ == '__main__':

    prev_url = ("https://www.residentadvisor.net/reviews/8812/")  # url to start at will be one previous
    review_id = int(prev_url[40:44])

    non_release_ids = []
    ra_data = {}
    # 21000 is greater than any known
    while review_id < 21000:

        request, prev_url = get_fresh_url(prev_url)

        review_id = int(request.geturl()[40:].rstrip("/"))

        soup = BeautifulSoup(request.read(), "html.parser")

        try:
            get_soup_elements(soup)
        except Exception as e:
            logging.error(e + " " + __name__)
        dump_remains(soup, ra_data)
        # increment previous url

        time.sleep(random.randint(1, 5))


# news feed items
