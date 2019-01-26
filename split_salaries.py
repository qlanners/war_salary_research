'''
file name: split_salaries.py
date created: 1/20/19
last edited: 1/25/19
created by: Quinn Lanners
description: this python script creates two seperate csv files from the csv file produced by salary_scraper.py. These
			 two new csv files are simply all of the information from the master salary csv file split based on whether
			 the player was a pitcher or a batter/positional player
'''


'''
import all packages. 
	-pandas used for dataframe
'''
import pandas as pd

'''
split_salaries:
		args:
			salaries_path: string of a csv file containing scraped salary information on both batters and pitchers
			batter_salaries_path: string value used as title to create new csv file containing salary data on only batters
			pitcher_salaries_path: string value used as title to create new csv file containing salary data on only pitchers
		returns:
			None
		This function splits a csv file containing salary data into two seperate csv files: one containing salary data only for batters
		and one containing salary data only for pitchers
'''
def split_salaries(salaries_path, batter_salaries_path, pitcher_salaries_path):
	salaries = pd.read_csv(salaries_path)

	headers = list(salaries)


	batters = pd.DataFrame(columns=headers)
	pitchers = pd.DataFrame(columns=headers)


	for index, row in salaries.iterrows():
		if "P" in row['position']:
			pitchers = pitchers.append(row, ignore_index=True)
		else:
			batters = batters.append(row, ignore_index=True)

	pitchers.to_csv(pitcher_salaries_path)
	batters.to_csv(batter_salaries_path)