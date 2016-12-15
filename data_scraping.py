import time
import sys
import csv
import json
import urllib.request

import xml.etree.ElementTree as ET

def write_csv(filename,lst):
	global writer
	prog_ratio=0
	prog_exp=0
	temp_net_asset=0
	unres_net_asset=0
	tree = ET.parse(filename)
	root=tree.getroot()
	break_out=False

	for child in root[0]:
		if child.tag.split('}')[1]=="Filer":
			for grandchild in child:
				if grandchild.tag.split('}')[1]=="EIN":
					ein=grandchild.text
					break
		if break_out==True:
			break
	break_out=False
	for child in root[1]:
		if child.tag.split('}')[1]!="IRS990":  #REMOVING IRS990 EZ and IRS990 PF
			lst[1]+=1
			#os.remove(filename)
			return None
		else:
			lst[0]+=1
			break
	for child in root[1]:
		for grandchild in child:
			if grandchild.tag.split('}')[1]=="DoNotFollowSFAS117" or grandchild.tag.split('}')[1]=="OrgDoesNotFollowSFAS117Ind":
				#os.remove(filename)
				lst[3]+=1
				return None
			else:
				if grandchild.tag.split('}')[1]=="TotalFunctionalExpensesGrp" or grandchild.tag.split('}')[1]=="TotalFunctionalExpenses": #TOTAL AMT ON PROGRAM SHOULD BE ABOVE 75%
					for great_grandchild in grandchild:
						if great_grandchild.tag.split('}')[1]=="TotalAmt" or great_grandchild.tag.split('}')[1]=="Total":
							total_amt=int(great_grandchild.text)
						if great_grandchild.tag.split('}')[1]=="ProgramServicesAmt":
							prog_exp=int(great_grandchild.text)
				 
				if grandchild.tag.split('}')[1]=="TotalAssetsGrp" or grandchild.tag.split('}')[1]=="TotalAssets":
					for great_grandchild in grandchild:
						if great_grandchild.tag.split('}')[1]=="EOYAmt" or great_grandchild.tag.split('}')[1]=="EOY":
							end_total_asset=int(great_grandchild.text)
						if great_grandchild.tag.split('}')[1]=="BOYAmt" or great_grandchild.tag.split('}')[1]=="BOY":
							beg_total_assets=int(great_grandchild.text)
				if grandchild.tag.split('}')[1]=="TotalLiabilitiesGrp" or grandchild.tag.split('}')[1]=="TotalLiabilities":
					for great_grandchild in grandchild:
						if great_grandchild.tag.split('}')[1]=="EOYAmt" or great_grandchild.tag.split('}')[1]=="EOY":
							total_liability=int(great_grandchild.text)
				if grandchild.tag.split('}')[1]=="UnrestrictedNetAssetsGrp":
					for great_grandchild in grandchild:
						if great_grandchild.tag.split('}')[1]=="EOYAmt":
							unres_net_asset=int(great_grandchild.text)
#								if total_amt==0:
#									dic[ein][2]="N/A"
#								else:
#									dic[ein][2]=unres_net_asset/total_amt
				if grandchild.tag.split('}')[1]=="TemporarilyRstrNetAssetsGrp":  #ONLY A FEW HAVE THIS
					for great_grandchild in grandchild:
						if great_grandchild.tag.split('}')[1]=="EOYAmt": 
							temp_net_asset=int(great_grandchild.text)
				if grandchild.tag.split('}')[1]  =="CYTotalRevenueAmt" or grandchild.tag.split('}')[1]== "TotalRevenueCurrentYear":
					total_rev=int(grandchild.text)
				if grandchild.tag.split('}')[1] =="TotalNetAssetsFundBalanceGrp" or grandchild.tag.split('}')[1] =="TotalNetAssetsFundBalances":
					for great_grandchild in grandchild:
						if great_grandchild.tag.split('}')[1]=="BOYAmt" or great_grandchild.tag.split('}')[1]=="BOY":
							lst[2]+=1
							beg_net_assets=int(great_grandchild.text)
						if great_grandchild.tag.split('}')[1]=="EOYAmt" or great_grandchild.tag.split('}')[1]=="EOY":
							end_net_assets=int(great_grandchild.text)
							
	if total_amt!=0 and prog_exp!=0:
		prog_ratio=prog_exp/total_amt
	else:
		prog_ratio=0
		
	if total_rev!=0:			
		surplus_margin=((end_net_assets-beg_net_assets)/total_rev)		
	else:
		surplus_margin=0
	if end_total_asset==0 or total_amt==0:
		work_cap_ratio=0
		lia_asset_ratio=0
	else:
		work_cap_ratio=((unres_net_asset+temp_net_asset)/total_amt)
		lia_asset_ratio=total_liability/end_total_asset

	#with open('team_out.txt', 'a') as f:
	writer.writerow([filename,ein,prog_ratio,lia_asset_ratio,work_cap_ratio,surplus_margin,total_amt])
		#os.remove(filename)


# In[ ]:

import ijson

filename="index_2016.json"

# Download json file
url = "https://s3.amazonaws.com/irs-form-990/index_2016.json"

urllib.request.urlretrieve(url,"index_2016.json")

with open(filename,'r') as f:
	objects=ijson.items(f,'Filings2016')
	columns=list(objects)


import urllib.request
import xml.etree.ElementTree as E
import os

ObjectId=[]
form_types = ['990EZ', '990PF']
ignore_types = 0
use_types = 0


for i in range(len(columns[0])):
	if columns[0][i]['FormType'] not in form_types:
		use_types += 1
		ObjectId+=[columns[0][i]['ObjectId']]
	else:
		ignore_types += 1

print("Objects other than 990EZ and 990PF: " + str(use_types))
print("Objects 990EZ and 990PF: " + str(ignore_types))
print("Length of ObjectId: " + str(len(ObjectId)))

base_url = "https://s3.amazonaws.com/irs-form-990/"
end_url = "_public.xml"
error_file = open('error_file.txt', 'w')
team_out = open('team_out.txt', 'w')
writer = csv.writer(team_out,quoting=csv.QUOTE_MINIMAL)

lst=[0,0,0,0]

for i in range(len(ObjectId)):

	if i == 50000:
		print("processed 50,000 records, exit now")
		sys.exit()

	new_url = base_url + ObjectId[i] + end_url
	filename = ObjectId[i] + ".xml"

	try:
		urllib.request.urlretrieve(new_url,filename)
		write_csv(filename,lst)
		time.sleep(1)
	except:
		error_string = str(new_url) + ' ' + '\n'
		error_file.write(error_string)
		#continue

	os.remove(filename)

	if i % 500 == 0:
		print(" " + str(i) + " records processed, now sleep for 5 seconds")
		time.sleep(5)
		#print(lst)


