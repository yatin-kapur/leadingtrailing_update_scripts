#import bs4 as bs
import insert
#import urllib3
#import re
import create_leading
from requests_html import HTMLSession


def create_match_record(match_id, tourn, db, cursor):
    print(match_id, ' starting this shit')
    session = HTMLSession()
    url = 'http://www.football-lineups.com/match/%s' % match_id
    r = session.get(url)
    r.html.encoding = 'ISO-8859-1'

#    user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0)\
#                  Gecko/20100101 Firefox/36.0'}
#    http = urllib3.PoolManager(2, user_agent)
#    response = http.request('GET', url)
#    soup = bs.BeautifulSoup(response.data, 'lxml')
#
#    date = soup.find_all('a', {'href': re.compile('^/date/[0-9]')})[0]['href']
#    date = date.split('/')[-2]
    links = r.html.absolute_links
    date = [link.split('/')[-2] for link in links if 'date' in link]
    date = [date for date in date if date != 'today'][0]

    print(date)
#
#    teams = soup.find_all('span', {'id': 'titequip'})
#    teams = [t.text.strip() for t in teams]
    teams = r.html.find('span')
    teams = [t.text for t in teams if 'id' in t.attrs and t.attrs['id'] == 'titequip']
    home_team = teams[0]
    away_team = teams[1]

    tds = r.html.find('td')
    times = [td.text[:-1] for td in tds if 'width' in td.attrs and 'align' in td.attrs and td.attrs['width'] == '30' and td.attrs['align'] == 'middle']
    scores = [td.text for td in tds if 'width' in td.attrs and 'align' in td.attrs and td.attrs['width'] == '25' and td.attrs['align'] == 'middle']
    final = r.html.find('font')
    final = [f.text for f in final if 'size' in f.attrs and f.attrs['size'] == '+2']
    home_final = int(final[2].strip())
    away_final = int(final[4].strip())

#    goal_times_html = soup.find_all('td', {'width': '30', 'align': 'middle'})
#    goal_times = []
#    for gt in goal_times_html:
#        try:
#            goal_times.append(int(gt.text[:-1]))
#        except:
#            continue

#    score = soup.find_all('td', {'width': '25', 'align': 'middle'})
#    score = [s.text for s in score]

    # check for 0-0
#    final = soup.find_all('font', {'size': '+2'})
#    home_final = int(final[2].text.strip())
#    away_final = int(final[4].text.strip())

    goals = [[int(times[i]), int(scores[i][0]), int(scores[i][-1])]
             for i in range(len(scores)) if scores[i] != '']

#    goals = [[goal_times[i], int(score[i][0]), int(score[i][-1])]
#             for i in range(len(score))
#             if score[i] != ' ' and score[i] != '\xa0\xa0\xa0']
    if home_final == 0 and away_final == 0:
        goals = [[0, 0, 0], [90, 0, 0]]

    if goals == []:
        raise ValueError("MATCHERROR: This match has not completed yet")


    # dictionary to load in scores
    insert_dict = {'match_id': match_id}
    for entry in goals:
        insert_dict['minute'] = entry[0]
        insert_dict['home_score'] = entry[1]
        insert_dict['away_score'] = entry[2]
        # call insert function
        insert.insert(cursor, db, 'Scores', **insert_dict)
        create_leading.create_lead(cursor, db, match_id)

    # insert into the match the data of this match after this is successful
    match_dict = {'match_id': match_id, 'home_team': home_team, 'matchday': 0,
                  'away_team': away_team, 'competition': tourn, 'date': date}
    insert.insert(cursor, db, 'Matches', **match_dict)
