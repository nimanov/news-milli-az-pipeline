import time
import psycopg2
import datetime
import psycopg2.extras
from psycopg2 import errors
from datetime import date, timedelta
from psycopg2.errorcodes import UNIQUE_VIOLATION
from utils import request_handler, could_not_scraped


def category_scraping(category_news, category_url):
    # DATABASE INFO
    hostname = '172.18.0.2'
    database = 'neurotime'
    pwd = 1234
    username = 'nurlan'
    port_id = 5432
    conn = None
    months_mapping = {1: "yanvar", 2: "fevral", 3: "mart", 4: "aprel", 5: "may", 6: "iyin",
                      7: "iyul", 8: "avqust", 9: "sentyabr", 10: "oktyabr", 11: "noyabr", 12: "dekabr"}
    page_index = 0
    # Go through each page in the given category
    while True:
        rest_part_is_old_news = False  # Since the news are orderes due to day, month and year
        page_index += 1
        page_url = category_url + "?page=" + str(page_index)
        soup_page = request_handler(page_url, 10, 60)
        if soup_page == "NOT RESPONDING":
            could_not_scraped(page_url)
            continue
        for li in soup_page.find(class_="post-list2").find_all("li"):
            news_url = li.find("a")["href"].strip()
            time_news = li.find(class_="time").text.strip()
            if "weather.day.az" not in news_url:
                if len(time_news.split()) not in [1, 3, 4]:
                    could_not_scraped(news_url, additional_msg="REASON: time.split is not in [1, 3, 4] ")
                    continue
                if len(time_news.split()) == 4:  # Means this news belongs to previous years
                    # Since news are ordered rest part is not needed
                    rest_part_is_old_news = True
                    break
                if len(time_news.split()) == 3:  # Means this news belongs to this year but not today
                    yesterday_day = (date.today() - timedelta(1)).day
                    current_month = months_mapping[datetime.datetime.now().month]
                    news_published_day = time_news.split()[0]
                    news_published_month = time_news.split()[1].replace("İ", "i").replace("I", "ı").lower()
                    if news_published_day != str(yesterday_day) or news_published_month != current_month:
                        rest_part_is_old_news = True
                        break
                soup_news = request_handler(news_url, 10, 60)
                if soup_news == "NOT RESPONDING":
                    could_not_scraped(news_url)
                    continue
                header = soup_news.find(class_="quiz-holder").find("h1").text
                date_news = soup_news.find(class_="date-info").text
                img_link = soup_news.find(class_="content-img")["src"]
                category_inside_news = soup_news.find(class_="category").text.strip()
                category_news_main = category_news
                if category_news.replace("İ", "i").replace("I", "ı").lower() != category_inside_news.replace("İ",
                                                                                                             "i").replace(
                    "I", "ı").lower():
                    category_news_main = category_news + "(" + category_inside_news + ")"
                content = ""
                for p in soup_news.find(class_="article_text").find_all("p"):
                    content += p.text.strip().replace(u'\xa0', u' ') + " "
                content = content.strip()
                tags = ""
                if soup_news.find(class_="tags_list") != None:
                    for tag in soup_news.find(class_="tags_list").find_all("a"):
                        tags += tag.text + ", "
                    tags = tags.strip().strip(",")
                if tags == "":
                    tags = None
                scraped_date = str(datetime.datetime.now())
                try:
                    with psycopg2.connect(
                            host=hostname,
                            dbname=database,
                            user=username,
                            password=pwd,
                            port=port_id) as conn:

                        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                            create_script = ''' CREATE TABLE IF NOT EXISTS news_az (
                                                    id      BIGSERIAL NOT NULL PRIMARY KEY,
                                                    url     VARCHAR UNIQUE,
                                                    title     VARCHAR ,
                                                    date     VARCHAR ,
                                                    img_link     VARCHAR ,
                                                    content     VARCHAR ,
                                                    category     VARCHAR ,
                                                    tags     VARCHAR,
                                                    scraped_date VARCHAR)
                                                    '''
                            cur.execute(create_script)
                            insert_script = '''INSERT INTO news_az 
                                                (url, title, date, img_link, content, 
                                                category, tags, scraped_date) 
                                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                             '''
                            record = (news_url, header, date_news,
                                      img_link, content.strip(), category_news_main, tags, scraped_date,)
                            cur.execute(insert_script, record)
                            print("Written to database", str(datetime.datetime.now()), category_news_main, news_url)
                except errors.lookup(UNIQUE_VIOLATION):  # Means this url already scraped
                    continue
                except Exception as error:
                    f_error_log = open("error.log", "a", encoding="utf-8")
                    msg = "DATABASE ERROR " + str(datetime.datetime.now()) + " "
                    f_error_log.write(msg + " ==> " + str(error) + "\n")
                    f_error_log.close()
                    return -1
                finally:
                    if conn is not None:
                        conn.close()

        if rest_part_is_old_news:
            break
    return 1


def news_az_scraper():
    all_categories = set()
    news_az_url = "https://news.milli.az"
    soup = request_handler(news_az_url, 10, 60)
    if soup == "NOT RESPONDING":
        could_not_scraped(news_az_url)
        return -1
    for li in soup.find(id="nav").find_all("li"):
        category_name = li.find("a").text.replace("I", "ı").replace("İ", "i").lower().strip()
        if category_name not in ["xəbər lenti", "newstube", ""]:
            for a in li.find_all("a"):
                if a["href"] not in all_categories:
                    all_categories.add(a["href"])
                    category_news = a.text
                    category_url = news_az_url + a["href"]
                    return_value = category_scraping(category_news, category_url)
                    if return_value == -1:
                        return -1
    return 1


while True:
    news_az_scraper()
    print("Finished the cycle", str(datetime.datetime.now()))
    time.sleep(3600)
