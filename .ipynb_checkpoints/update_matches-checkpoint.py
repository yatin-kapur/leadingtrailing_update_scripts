import dbconfig
import MySQLdb
import bs4 as bs
import urllib3
from update_meta import update_metadata, update_matchday_entry
import add_game_entry

db_dict = dbconfig.read_db_config()
db = MySQLdb.connect(host=db_dict['host'],
                     user=db_dict['user'],
                     passwd=db_dict['password'],
                     db=db_dict['database'])


def update_games(tourn):
    cursor = db.cursor()
    url = 'http://www.football-lineups.com/tourn/%s' % tourn
    user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0)\
                  Gecko/20100101 Firefox/36.0'}
    http = urllib3.PoolManager(2, user_agent)
    response = http.request('GET', url)
    soup = bs.BeautifulSoup(response.data, 'lxml')

    links = soup.find('article').find('td', 'TDmain')
    links = links.findAll('a')

    match_ids = []
    for link in links:
        if link['href'][:7] == '/match/':
            match_ids.append(int(link['href'][7:-1]))

    cursor.execute("select * from Matches;")
    current = cursor.fetchall()
    current = [d[0] for d in current]

    for match in match_ids:
        if match not in current:
            print(match)
            try:
                add_game_entry.create_match_record(match, tourn, db, cursor)
                update_matchday_entry(match, cursor, db)
                update_metadata(match, cursor, db)
            except Exception as e:
                print(match)
                print('ERROR: ' + str(e))
                if 'MATCHERROR' in str(e):
                    continue
                else:
                    break


def all_comps():
    cursor = db.cursor()
    cursor.execute("select * from Competitions order by competition desc;")
    competitions = cursor.fetchall()
    competitions = [c[0] for c in competitions if c[1] == 0]

    for c in competitions:
        print('updating games')
        update_games(c)

all_comps()
