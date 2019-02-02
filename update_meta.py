import dbconfig
import MySQLdb
import bs4 as bs
import urllib3
import insert
from requests_html import HTMLSession


def update_matchday_entry(match_id, cursor, db):
    """
    update the matchday for each game
    #TODO might want to move this to metadata table
    """
    url = 'http://www.football-lineups.com/match/%s' % match_id
    user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0)\
                  Gecko/20100101 Firefox/36.0'}
    http = urllib3.PoolManager(2, user_agent)
    response = http.request('GET', url)
    soup = bs.BeautifulSoup(response.data, 'lxml')

    rows = soup.findAll('tr', {'itemprop': 'description'})[0].findAll('a')
    links = [r['href'].split('/')[-1] for r in rows if 'matchday' in r['href']]
    matchday = int(links[0])
    update_query = """
                    update matches
                    set matchday = %s
                    where match_id = %s;
                    """ % (matchday, match_id)
    cursor.execute(update_query)
    db.commit()


def update_metadata(match_id, cursor, db):
    """
    update weird metadata
    """
    session = HTMLSession()
    url = 'http://www.football-lineups.com/match/%s' % match_id
    r = session.get(url)
    r.html.encoding = 'ISO-8859-1'

    # HEIGHT #
    trs = r.html.find('tr')
    trs = [tr for tr in trs if 'align' in tr.attrs.keys() and
           tr.attrs['align'] == 'center']

    for i, tr in enumerate(trs):
        if 'Height Avg' in tr.text:
            home_height = tr.find('td')[0].text[:4]
            away_height = tr.find('td')[2].text[:4]
            break

    print(match_id, home_height, away_height)

    # INSERT #
    data_dict = {'match_id': match_id,
                 'home_height': home_height,
                 'away_height': away_height}
    insert.insert(cursor, db, 'match_metadata', **data_dict)


def update_matches(tourn, cursor, db):
    """
    go through all match_ids in this tournament and update data
    """

    query = """
    select match_id
    from Matches
    where competition = '%s'
    """ % tourn
    # update matchday:
    query = query + "and matchday = 0"

    query = query + ";"

    cursor.execute(query)
    current = cursor.fetchall()
    current = [d[0] for d in current]

    metadata_query = """
    select match_id
    from match_metadata;
    """

    cursor.execute(metadata_query)
    meta = cursor.fetchall()
    meta = [d[0] for d in meta]

    for match_id in current:
        update_matchday_entry(match_id, cursor, db)
        if match_id not in meta:
            update_metadata(match_id, cursor, db)


def all_comps():
    """
    get all competitions and update their data
    """
    db_dict = dbconfig.read_db_config()
    db = MySQLdb.connect(host=db_dict['host'],
                         user=db_dict['user'],
                         passwd=db_dict['password'],
                         db=db_dict['database'])
    cursor = db.cursor()
    cursor.execute("select * from Competitions order by competition desc;")
    competitions = cursor.fetchall()
    competitions = [c[0] for c in competitions if 'FA' in c[0]]

    for c in competitions:
        update_matches(c, cursor, db)


all_comps()
