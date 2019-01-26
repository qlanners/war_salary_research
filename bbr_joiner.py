'''
file name: bbr_joiner.py
date created: 1/23/19
last edited: 1/25/19
created by: Quinn Lanners
description: this python script takes as input a csv file of a list of players and their salary information scraped from www.Spotrac.com
			 using the salary_scraper.py file. It then matches each row of this inputted csv file with that players corresponding batting
			 statistics from www.baseballreference.com. Along with saving a csv file to the current working directory (with the name passsed
			 as an argument in the function), the script also prints a list of the players which it failed to retrieve batting stats for
'''


'''
import all packages. 
	-Selenium used to scrape data from web using an instance of Chrome in the background.
	-pandas used for dataframe
	-time used to time how long the process takes
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


'''
look_up_function:
		args:
			name: string value of the name of the player in the format [first 5 letters of last name]+[first two letters of first name]
			year: int or string value of year
			number: string of a number in the format '01','02',... which is appended to name to create bbr ID
		returns:
			batting_standard: pandas dataframe containing the standard batting table from bbr
			batting_value: pandas dataframe containing the player value--batting table from bbr
				**returns None if these tables are unable to be found for the appropriate year
		this function creates a url given the args with which it attempts to open a headless version of chrome and scrape the
		'Standard Batting' and the 'Player Value--Batting' tables from the correct baseball reference page.
'''
def look_up_function(name, year, number):

	option = Options()
	option.add_argument(" - incognito")
	option.add_argument("--no-startup-window")
	option.add_argument("--headless")

	capa = DesiredCapabilities.CHROME
	capa["pageLoadStrategy"] = "none"

	driver = webdriver.Chrome(executable_path='/Applications/chromedriver', chrome_options = option, desired_capabilities = capa)
	wait = WebDriverWait(driver, 60)


	url = "https://www.baseball-reference.com/players/"+name[0]+"/"+name+number+".shtml"

	driver.get(url)

	wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='batting_value']")))

	batting_standard = driver.find_element_by_xpath("//*[@id='batting_standard']").get_attribute('outerHTML')

	batting_value = driver.find_element_by_xpath("//*[@id='batting_value']").get_attribute('outerHTML')

	driver.execute_script("window.stop();")

	driver.stop_client()
	driver.close()

	batting_standard = pd.read_html(batting_standard)
	batting_value = pd.read_html(batting_value)


	batting_standard = batting_standard[0]
	batting_value = batting_value[0]

	if str(year) not in batting_standard.Year.values:
		return None

	batting_standard_unnamed_cols = [s for s in list(batting_standard) if "Unnamed" in s]
	batting_value_unnamed_cols = [s for s in list(batting_value) if "Unnamed" in s]

	batting_standard.drop(batting_standard_unnamed_cols, axis=1, inplace=True)
	batting_value.drop(batting_value_unnamed_cols, axis=1, inplace=True)

	return batting_standard, batting_value


'''
join_data:
		args:
			salary_csv_path: string value indicating the location of the csv containing player salary data
							 scraped using salary_scraper.py
			joined_csv_path: string value indicating the name of the new csv file to be created containing
							 the joined salary and batting statistics data
		returns:
			None
		This function iterates throw each row in the salary_csv_path file and joins the player and year salary
		data to the corresponding player and year batting statistics from baseballreference. While doing so, it
		keeps track of the player/year combos which are unable to be retrieved.In the end, this function saves a
		csv to the current working directory which contains the joined salary and batting data, along with prints
		a summary of the player/year combos which were not retrieved.
'''
def join_data(salary_csv_path, joined_csv_path):
	#imports the salaries_batters.csv which contains informaton on all player contracts
	salaries = pd.read_csv(salary_csv_path)
	print('Number of player salaries to match to batting statistics: ' + str(salaries.shape[0]))

	#list of the leagues from which we desire to scrape information. Used to avoid scrapping stats from A,AA,AAA ball
	leagues = ['AL','NL','MLB']

	#empty datafame which will we add joined salary and stat data from bbr
	joined = pd.DataFrame()

	start_time = time.time()

	#used to track the players which the script fails to join data on
	missed_players = list()
	misses = 0


	#iterates through each row in the salary dataframe, taking the year, age, and name value out of each row to input into the look_up_function
	for salary_index, salary_row in salaries.iterrows():

		year = str(salary_row['year']).split('.')[0]
		age = salary_row['age']
		name_parts = str(salary_row['name']).replace('.','').replace("'","").lower().split()
		#used to deal with players that may have multiple last names/two parts to last name (ex. 'Abel De Los Santos')
		if len(name_parts) == 2:
			name = name_parts[0][:5]+name_parts[1][:2]
		if len(name_parts) == 3:
			name = name_parts[0][:5] + name_parts[1][:(5-len(name_parts[0][:5]))] + name_parts[2][:2]
		
		'''
		these numbers are inputted to the look_up_function. The first time through, 01 is inputted to create an id with [name]01. If
		this combination doesnt work, then the second time through 02 is inputted into the look_up_function, creating an id with [name]02
		and the loop continues like this, trying up to the id [name]05. This is used to deal with the fact that bbr makes player ids based
		off of a name/number combo, where they simply count up starting at 01 as player names are duplicated
		'''
		numbers = ['01','02','03','04','05','06','07','08','09','10','11']
		
		count = 0
		while count <= 10:
			try:
				batting_standard, batting_value = look_up_function(name,year,numbers[count])
				#this line adds the necessary column names to joined, but only does so through first time through (when joined has no columns)
				if joined.shape[1] < 20:
					all_headers = list(salaries) + list(batting_standard) + list(batting_value)
					joined = joined.reindex(columns=all_headers)
					joined = joined.astype('object')

				#dictionary used to store standard batting stats, most players will only have one entry, but players that played for multiple teams in
				#the same year will have an entry for each team (i.e. each row in bbr)
				joined_part_ones = {}
				for index, row in batting_standard.iterrows():
					if str(row['Year']) == str(year) and str(row['Age']) == str(age) and str(row['Lg']) in leagues:
						joined_part_ones[row['Tm']] = salaries.iloc[[salary_index]].values.tolist()[0][:13] + batting_standard.iloc[[index]].values.tolist()[0]

				#this part combines the correct advanced batting stats with the corresponding standard batting stats and adds a new row to the joined dataframe
				for index, row in batting_value.iterrows():
					if str(row['Year']) == str(year) and str(row['Age']).split('.')[0] == str(age) and str(row['Lg']) in leagues:
						joined = joined.append(pd.Series(joined_part_ones.get(row['Tm']) + batting_value.iloc[[index]].values.tolist()[0], index=all_headers), ignore_index=True)
				count = 21
			
			# if the url lookup didn't work for this player ID, try again using next number
			except:
				count += 1

		#if the player information could not be scraped for ID number 01-05, then print name and add to missed players list
		if count > 10 and count != 21:
			print(salary_row['name']+' '+str(year) + ' ' + name)
			missed_players.append(salary_row['name']+' '+str(year) + ' ' + name)
			misses += 1

		#print a time after every 100 analyzed players
		else:
			if (salary_index % 100) == 0:
				print('...'+str(salary_index)+'...')
				print("--- %s seconds ---" % (time.time() - start_time))
				print('')


	#delete duplicate columns from the joined table
	joined = joined.loc[:,~joined.columns.duplicated()]

	#save the joined table to a csv in the current directory
	joined.to_csv(joined_csv_path)

	#print a list of all of the missed players, along with the number of missed players
	print(missed_players)
	print('')
	print('Missed '+str(misses)+' of '+str(salaries.shape[0]))




join_data('salaries_batters.csv','joined_salaries_bbr_2.csv')
