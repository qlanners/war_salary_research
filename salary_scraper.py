'''
file name: salary_scraper.py
date created: 1/18/19
last edited: 1/25/19
created by: Quinn Lanners
description: this python script creates a new csv file to which it appends salary data scraped from www.Spotrac.com for each 
			 team in the MLB from over a specified time period. The script scraps salary data from players in both the Active 
			 Roster and Disabled List tables from Spotrac. Furthermore, if specified, this script also produces two additional
			 csv files alongside the master salary csv file: one for all batters/position players salaries and one for all
			 pitchers salaries
'''


'''
import all packages. 
	-Selenium used to scrape data from web using an instance of Chrome in the background.
	-pandas used for dataframe
	-time used to time how long the process takes
	-BeautifulSoup used to extract text from HTML
	-split_salaries is used to split salary data into seperate files for batters and pitchers
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
from bs4 import BeautifulSoup
from split_salaries import split_salaries


#Dictionary of team abbreviations and corresponding url component used by spotrac for that team. Used to create unique URLs for each team
teams = {
	'LAA':'los-angeles-angels',
	'CHW':'chicago-white-sox',
	'CLE':'cleveland-indians',
	'KC':'kansas-city-royals',
	'MIL':'milwaukee-brewers',
	'OAK':'oakland-athletics',
	'SEA':'seattle-mariners',
	'TEX':'texas-rangers',
	'CHC':'chicago-cubs',
	'CIN':'cincinnati-reds',
	'LAD':'los-angeles-dodgers',
	'SD':'san-diego-padres',
	'SF':'san-francisco-giants',
	'COL':'colorado-rockies',
	'ARI':'arizona-diamondbacks',
	'BAL':'baltimore-orioles',
	'BOS':'boston-red-sox',
	'DET':'detroit-tigers',
	'MIN':'minnesota-twins',
	'NYY':'new-york-yankees',
	'TOR':'toronto-blue-jays',
	'ATL':'atlanta-braves',
	'HOU':'houston-astros',
	'WSH':'washington-nationals',
	'NYM':'new-york-mets',
	'PHI':'philadelphia-phillies',
	'PIT':'pittsburgh-pirates',
	'STL':'st.-louis-cardinals',
	'MIA':'miami-marlins',
	'TB':'tampa-bay-rays'

}

#The names of the columns of the tables extracted from Spotrac. Since the exact headers used in Spotrac vary based on the team/year, these generic
#headers are used to avoid confusion
spotrac_col_names = ['name','age','position','status','base_salary','signing_bonus','incentives','total_salary','adjusted_salary','payroll_perc','active','year','team']


'''
remove_duplicates:
		args:
			name: a list of a name split using the split() function in python
		returns:
			shortened_name: a list which removed all duplicate words
		this function was created to deal with a strange error that occurs when scraping from Spotrac, where every player's name
		is repeated twice in the name column. This function in turn returns once instance of their last name in the form of a list
		which is then joined together to produce one name in the format 'Last_Name First_Name'
'''
def remove_duplicate(name):
    shortened_name = []
    [shortened_name.append(x) for x in name if x not in shortened_name]
    return shortened_name


'''
check_website:
		args:
			team: string of the unique portion of the spotrac url for the desired team. For example, for Minnesota Twins, is minnesota-twins
			year: string/int value for the desired year
		returns:
			None
		this function can be used to simply ensure that the desired team and year page is available. Although not used in the main script,
		this may be helpful when checking to see if Spotrac has salary information for a desired team in a specific year. Prints '.' if the
		page is found, otherwise returns a message saying their was a failure to do so.
'''
def check_website(team, year):
	try:
		option = Options()
		option.add_argument(" - incognito")
		option.add_argument("--no-startup-window")
		option.add_argument("--headless")

		capa = DesiredCapabilities.CHROME
		capa["pageLoadStrategy"] = "none"

		driver = webdriver.Chrome(executable_path='/Applications/chromedriver', chrome_options = option, desired_capabilities = capa)
		wait = WebDriverWait(driver, 60)

		url = "https://www.spotrac.com/mlb/"+team+"/payroll/"+str(year)+"/"

		driver.get(url)

		wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='main']/div[4]/table[3]")))

		active = driver.find_element_by_xpath("//*[@id='main']/div[4]/table[1]").get_attribute('outerHTML')

		disabled = driver.find_element_by_xpath("//*[@id='main']/div[4]/table[2]").get_attribute('outerHTML')

		retained = driver.find_element_by_xpath("//*[@id='main']/div[4]/table[3]").get_attribute('outerHTML')


		driver.execute_script("window.stop();")

		driver.stop_client()
		driver.close()
		print('.')

	except:
		print('Failure for '+team+' '+str(year))


'''
salary_scraper:
		args:
			team: string of the abbrevation for a team (ex. Minnesota Twins = MIN)
			team_url: string of the unique portion of the spotrac url for the desired team. For example, for Minnesota Twins, is minnesota-twins
			year: strin/int value for the desired year
			csv_path: string of the path to the csv to which the information is to be appended to
		returns:
			None
		This function scrapes salary data for a specified team for a specified year and appends the scraped data to the csv specified with the
		csv_path arg. Salary data is scraped for both active and disables list players. The function appends to data to the csv and prints '.'
		if succesful, else the function prints a message indicating the failure to do so.
'''
def salary_scraper(team, team_url, year, csv_path):

	try:
		option = Options()
		option.add_argument(" - incognito")
		option.add_argument("--no-startup-window")
		option.add_argument("--headless")

		capa = DesiredCapabilities.CHROME
		capa["pageLoadStrategy"] = "none"

		driver = webdriver.Chrome(executable_path='/Applications/chromedriver', chrome_options = option, desired_capabilities = capa)
		wait = WebDriverWait(driver, 60)

		#create the unique url for the payroll site for the team and year
		url = "https://www.spotrac.com/mlb/"+team_url+"/payroll/"+str(year)+"/"

		driver.get(url)

		wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='main']/div[4]/table[1]")))

		#get the active players salary table
		active = driver.find_element_by_xpath("//*[@id='main']/div[4]/table[1]").get_attribute('outerHTML')

		#get the title of the second salary table
		table_two_title = driver.find_element_by_xpath("//*[@id='main']/div[4]/header[1]/h2").get_attribute('outerHTML')

		
		table_two_title_soup = BeautifulSoup(table_two_title, "lxml")
		table_two_title = table_two_title_soup.get_text()

		#if the second table on the page is for players on the disabled list, get table, else don't get table
		if 'Disabled' in table_two_title:
			disabled = driver.find_element_by_xpath("//*[@id='main']/div[4]/table[2]").get_attribute('outerHTML')

		driver.execute_script("window.stop();")

		driver.stop_client()
		driver.close()



		active = pd.read_html(active)
		active = active[0]
		active['type'] = 'A'

		if 'Disabled' in table_two_title:
			disabled = pd.read_html(disabled)
			disabled = disabled[0]
			disabled['type'] = 'D'
			for index, row in disabled.iterrows():
				if '7' in disabled.iloc[index,0]:
					disabled.iloc[index,0] = disabled.iloc[index,0][:-8]
				elif '(' in disabled.iloc[index,0]:
					disabled.iloc[index,0] = disabled.iloc[index,0][:-9]
			disabled.columns = list(active)
			all_salaries = pd.concat([active,disabled])
		
		else:
			all_salaries = active
		
		all_salaries['year'] = year
		all_salaries['team'] = team

		player_name_row = list(active)[0]

		#use the remove duplicate functions to deal with Spotrac issue of duplicating players names when scraping
		for index, row in all_salaries.iterrows():
			
			all_salaries.at[index,player_name_row] = ' '.join(remove_duplicate(row[player_name_row].split()))

		#append the scraped table to the speicifed csv
		with open(csv_path, 'a') as salaries:
			all_salaries.to_csv(salaries, encoding='utf-8', index=False, header=False)

			print('.')

	#print a failure message if the data for this team in this year cannot be retrieved
	except:
		print('Failure for '+team+' '+str(year))


'''
create_empty_csv:
		args:
			csv_path: string name of file path for new csv file
			col_names: list of strings of the names of the columns for the new csv file
		returns:
			None
		This function creates a new, empty, csv file with nothing other than column headers. This is the csv file that all of the scraped
		salary data is subsequently added to, and is used in part to deal with the fact that the col names for the Spotrac salary pages are
		not entirely consistent.
'''
def create_empty_csv(csv_path, col_names):
	df = pd.DataFrame(columns=col_names)
	df.to_csv(csv_path, encoding='utf-8', index=False)


'''
main:
		args:
			csv_path: string value of the name of the new csv file to be created which will contain salary information for both batters and pitchers
					  for all MLB teams over the specified years
			years: list of ints/strings indicating over which years to scrape salary data for all teams for
			split: boolean value indicating whether or not the master salary csv file should be split into two csv files of seperate batter and
				   pitcher salary information
			batter_salaries_path: string value used as title to create new csv file containing salary data on only batters
			pitcher_salaries_path: string value used as title to create new csv file containing salary data on only pitchers
		returns:
			None
		This function combines all of the previous functions into a master script, which scrapes data for all MLB teams over the specified years
		from Spotrac.com, and then creates a csv file in the working directory with the given name. Furthermore, this function has the option to
		create two additional csv files: one for all of the batter salary info and one for all of the pitcher salary info
'''
def main(csv_path, years, split=True, batter_salaries_path='salaries_batters.csv', pitcher_salaries_path='salaries_pitchers.csv'):
	create_empty_csv(csv_path,spotrac_col_names)
	start_time = time.time()
	for year in years:
		print('Year '+str(year)+' started at:')
		print("--- %s seconds ---" % (time.time() - start_time))
		for key , value in teams.items():
			salary_scraper(key,value,year,csv_path)
	if split:
		split_salaries(csv_path,batter_salaries_path,pitcher_salaries_path)



#list of the years from which to scrape salary data from
years = [2012,2013,2014,2015,2016,2017,2018]

main('salaries2.csv', years=years, split=True, batter_salaries_path='salaries_batters2.csv', pitcher_salaries_path='salaries_pitchers2.csv')

