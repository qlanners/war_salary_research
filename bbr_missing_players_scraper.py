'''
file name: bbr_missing_players_scraper.py
date created: 3/14/19
last edited: 3/15/19
created by: Quinn Lanners
description: this python script takes the links and keys of the players missed from the original bbr_scraper.py script and scrapes their data
			 from baseballreference.
'''


'''
import all packages. 
	-Selenium used to scrape data from web using an instance of Chrome in the background.
	-pandas used for dataframe
'''
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
import math



'''
as_hours:
		args:
			s: time in seconds
		returns:
			string of 'hours minutes seconds'
		this function takes as input a time in seconds (determined by the time package) and
		returns of string of hours minutes and seconds for readability purposes
'''
def as_hours(s):
	m = math.floor(s / 60)
	h = math.floor(m / 60)
	s -= m * 60
	m -= h * 60
	return '%dh %dm %ds' % (h, m, s)


'''
look_up_function:
		args:
			link: string value of the URL link to the baseballreference page for that player
			pitcher: boolean value indicating whether the player is a pitcher
		returns:
			standard: pandas dataframe containing the standard batting table from bbr
			value: pandas dataframe containing the player value--batting table from bbr
				**returns None if these tables are unable to be found for the appropriate year
		this function scrapes statistics for a player with their baseballreference link given as an arg
'''
def look_up_function(link, pitcher=False):

	option = Options()
	option.add_argument(" - incognito")
	option.add_argument("--no-startup-window")
	option.add_argument("--headless")

	capa = DesiredCapabilities.CHROME
	capa["pageLoadStrategy"] = "none"

	'''ensure that the executable_path points to the directory where your chromedriver is installed (note this code is optimized for 
	google cloud services and thus the path will be different if being run on local computer)'''
	driver = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', chrome_options = option, desired_capabilities = capa)
	
	#have the chromedriver wait 10 seconds if page isn't instantly located
	wait = WebDriverWait(driver, 10)

	driver.get(link)

	if pitcher:
		wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='pitching_value']")))
	else:
		wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='batting_value']")))


	if pitcher:
		standard = driver.find_element_by_xpath("//*[@id='pitching_standard']").get_attribute('outerHTML')
		value = driver.find_element_by_xpath("//*[@id='pitching_value']").get_attribute('outerHTML')
	
	else:		
		standard = driver.find_element_by_xpath("//*[@id='batting_standard']").get_attribute('outerHTML')
		value = driver.find_element_by_xpath("//*[@id='batting_value']").get_attribute('outerHTML')

	driver.execute_script("window.stop();")

	driver.stop_client()
	driver.close()


	standard = pd.read_html(standard)
	value = pd.read_html(value)


	standard = standard[0]
	value = value[0]

	standard_unnamed_cols = [s for s in list(standard) if "Unnamed" in s]
	value_unnamed_cols = [s for s in list(value) if "Unnamed" in s]

	standard.drop(standard_unnamed_cols, axis=1, inplace=True)
	value.drop(value_unnamed_cols, axis=1, inplace=True)

	return standard, value


'''
scrape_data:
		args:
			player_links: list of strings of the players whose salaries you wish to be scraped
			player_keys: list of ints corresponding the the order of each player in players_links
			bbr_data_csv_path: string value incidcating the csv to which you want these players stats
								to be appended
			pitchers: boolean value indicating whether the players are pitchers or not
		returns:
			None
		This function looks up each player in the player_links and scrapes their salary data. It then attaches
		their player key to their statistics and appends their data to the bbr_data_csv_path specified. It is used
		to scrape data for players whose URL format or data input in baseballreference was in such a format that the
		original bbr_scraper.py script was unable to catch them
'''
def scrape_data(players_links, player_keys, bbr_data_csv_path, pitchers=False):
	if pitchers:
		print('Number of player salaries to match to pitching statistics: {}'.format(len(players_links)))
	else:	
		print('Number of player salaries to match to batting statistics: {}'.format(len(players_links)))

	#list of the leagues from which we desire to scrape information. Used to avoid scrapping stats from A,AA,AAA ball
	leagues = ['AL','NL','MLB']

	#empty datafame which will we add the missing players stats to
	missing_bbr_data = pd.DataFrame()

	players = list(zip(players_links, player_keys))

	start_time = time.time()

	#used to track the players which the script fails to scrape data for
	missed_players = list()
	missed_players_keys = list()
	players_done = []


	for player in players:
		try:
			standard, value = look_up_function(player[0],pitcher=pitchers)
			standard.loc[standard['Lg'].isin(leagues)]
			standard = standard.loc[standard['Lg'].isin(leagues)]
			value = value.loc[value['Lg'].isin(leagues)]
			standard['join_key_y'] = standard['Year'] + standard['Tm']
			value['join_key_y'] = value['Year'] + value['Tm']
			total_stats = standard.merge(value, on='join_key_y', how='left', suffixes=('', '_y'))
			total_stats['key'] = player[1]
			total_stats.drop(list(total_stats.filter(regex = '_y')), axis = 1, inplace = True)
			
			if missing_bbr_data.shape[1] < 20:
				all_headers = list(total_stats)
				missing_bbr_data = missing_bbr_data.reindex(columns=all_headers)
				missing_bbr_data = missing_bbr_data.astype('object')

			missing_bbr_data = missing_bbr_data.append(total_stats, ignore_index=True)


		except:
			missed_players.append(player[0])
			missed_players_keys.append(player[1])

	bbr_data = pd.read_csv(bbr_data_csv_path)

	bbr_data_full = bbr_data.append(missing_bbr_data)

	csv_name, period, extension = bbr_data_csv_path.partition('.')

	bbr_data_full.to_csv(csv_name+'_full.csv', index=False)

	#print a list of all of the missed players, along with the number of missed players
	print('')
	print(missed_players)
	print(missed_players_keys)
	print('{} players missed'.format(len(missed_players)))
	print('')
	print('Time: {}'.format(asHours(time.time()-start_time)))
	print('')
	print('')


'''These are the player links and keys that were missed when I ran the code myself. These same players are typically the exact ones missed, however
that may vary based on the reliability of your network and whether or not you change any of the settings of the other scripts'''

missing_batter_links = ['https://www.baseball-reference.com/players/c/coraal01.shtml', 'https://www.baseball-reference.com/players/l/lairdbr01.shtml', 'https://www.baseball-reference.com/players/k/kangju01.shtml','https://www.baseball-reference.com/players/p/phamth01.shtml','https://www.baseball-reference.com/players/u/uptonbj01.shtml','https://www.baseball-reference.com/players/s/sanchca01.shtml','https://www.baseball-reference.com/players/s/stantmi03.shtml','https://www.baseball-reference.com/players/w/waldrky02.shtml','https://www.baseball-reference.com/players/m/mondera02.shtml','https://www.baseball-reference.com/players/m/martios01.shtml','https://www.baseball-reference.com/players/j/johnsro07.shtml','https://www.baseball-reference.com/players/y/youklke01.shtml','https://www.baseball-reference.com/players/f/fernajo03.shtml','https://www.baseball-reference.com/players/s/shuckja01.shtml','https://www.baseball-reference.com/players/p/penato02.shtml','https://www.baseball-reference.com/players/m/murphjr01.shtml','https://www.baseball-reference.com/players/g/gourryu01.shtml','https://www.baseball-reference.com/players/y/youngma02.shtml','https://www.baseball-reference.com/players/a/alberha01.shtml','https://www.baseball-reference.com/players/c/curtico01.shtml','https://www.baseball-reference.com/players/s/scalebo01.shtml','https://www.baseball-reference.com/players/f/fieldth01.shtml','https://www.baseball-reference.com/players/t/taveros01.shtml','https://www.baseball-reference.com/players/b/bayja01.shtml','https://www.baseball-reference.com/players/m/manzeto01.shtml','https://www.baseball-reference.com/players/l/lopezfe01.shtml']

missing_batter_keys = [87,8469,16144,16031,854,14065,6864,8541,18324,7403,5366,110,21397,8691,418,14326,20806,7639,16595,7460,5199,11609,15284,691,7334,938]

missing_pitcher_links = ['https://www.baseball-reference.com/players/r/rauchjo01.shtml','https://www.baseball-reference.com/players/f/fuentbr01.shtml','https://www.baseball-reference.com/players/g/garcija01.shtml','https://www.baseball-reference.com/players/g/gutieju01.shtml','https://www.baseball-reference.com/players/n/nunezle01.shtml','https://www.baseball-reference.com/players/c/carmofa01.shtml','https://www.baseball-reference.com/players/h/hoeyja02.shtml','https://www.baseball-reference.com/players/h/herreda01.shtml','https://www.baseball-reference.com/players/c/carigan01.shtml','https://www.baseball-reference.com/players/d/delarda01.shtml','https://www.baseball-reference.com/players/v/valdelu01.shtml','https://www.baseball-reference.com/players/d/deleojo02.shtml','https://www.baseball-reference.com/players/h/hartke01.shtml','https://www.baseball-reference.com/players/s/sttuemi01.shtml','https://www.baseball-reference.com/players/g/greense01.shtml','https://www.baseball-reference.com/players/d/delarru01.shtml','https://www.baseball-reference.com/players/v/villape01.shtml','https://www.baseball-reference.com/players/m/mendero01.shtml','https://www.baseball-reference.com/players/w/wolfro01.shtml','https://www.baseball-reference.com/players/l/leech01.shtml','https://www.baseball-reference.com/players/r/rodrist02.shtml','https://www.baseball-reference.com/players/d/diazjo01.shtml','https://www.baseball-reference.com/players/g/gonzami05.shtml','https://www.baseball-reference.com/players/m/marimsu01.shtml','https://www.baseball-reference.com/players/o/ogandne01.shtml','https://www.baseball-reference.com/players/r/riverfe01.shtml','https://www.baseball-reference.com/players/d/delosab01.shtml','https://www.baseball-reference.com/players/z/zychto01.shtml','https://www.baseball-reference.com/players/e/edwarca01.shtml','https://www.baseball-reference.com/players/c/cravyty01.shtml','https://www.baseball-reference.com/players/v/valdejo03.shtml','https://www.baseball-reference.com/players/o/overtdi01.shtml','https://www.baseball-reference.com/players/d/delacjo01.shtml','https://www.baseball-reference.com/players/t/torrejo02.shtml','https://www.baseball-reference.com/players/r/reedco01.shtml','https://www.baseball-reference.com/players/d/delosen01.shtml','https://www.baseball-reference.com/players/m/makitka01.shtml','https://www.baseball-reference.com/players/v/vastoje01.shtml','https://www.baseball-reference.com/players/b/blackra01.shtml']

missing_pitcher_keys = [928, 255, 608, 13535, 416, 243, 59, 5214, 8593,  8474, 8631, 11589, 144, 8654, 755, 8759, 11456, 12045, 18851, 12049, 11570, 14091, 13519, 14190, 16574, 16020, 18036, 18163, 16514, 17563, 14144, 20499, 16654, 18332, 17722, 24687, 24728, 26288, 16585]

scrape_data(missing_batter_links,missing_batter_keys,'batters_bbr.csv')

scrape_data(missing_pitcher_links, missing_pitcher_keys,'pitchers_bbr.csv',pitchers=True)
