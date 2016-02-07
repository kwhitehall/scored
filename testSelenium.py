from selenium import webdriver
import json, os
#from bs4 import BeautifulSoup


driver = webdriver.PhantomJS()

driver.set_window_size(1024, 768)
driver.get('http://journals.ametsoc.org')
content = driver.page_source

def info_from_ams():

	allIssues = driver.find_elements_by_link_text('Available Issues')


	currLink = driver.current_url
	lengthOfArray = len(allIssues)

	for i in range(2,4):
		get_issue_info((('//*[@id="middleCol"]/div[%d]/div[2]/div[2]/a') % (i)), currLink)
		print "Next AVailable issue"

	for i in range(4,7):
		get_issue_info((('//*[@id="middleCol"]/div[%d]/div[2]/div[3]/a') % (i)), currLink)
		print "Next AVailable issue"

	get_issue_info(('//*[@id="middleCol"]/div[7]/div[2]/a'), currLink)

	get_issue_info(('//*[@id="middleCol"]/div[8]/div[2]/div[3]/a'), currLink)

	get_issue_info(('//*[@id="middleCol"]/div[9]/div[2]/div[2]/a'), currLink)

	get_issue_info(('//*[@id="middleCol"]/div[10]/div[2]/div[3]/a'), currLink)

	get_issue_info(('//*[@id="middleCol"]/div[11]/div[2]/div[3]/a'), currLink)

	get_issue_info(('//*[@id="middleCol"]/div[12]/div[2]/div[2]/a'), currLink)


def get_issue_info(xpath, currLink):

	issueDriver = webdriver.PhantomJS()
	issueDriver.get(currLink)

	issueDriver.find_element_by_xpath(xpath).click()

	allCollapsed = issueDriver.find_elements_by_css_selector('.loiListHeading.collapsed')

	for link in allCollapsed:
		link.click()

	currLink = issueDriver.current_url

	issueList = issueDriver.find_elements_by_class_name('loiTocUrl')

	for issue in issueList:
		print issue.text.encode('utf-8')
		get_info(issue.text.encode('utf-8'), currLink)

	print len(issueList)

def get_info(issue, currLink):

	fullTextDriver = webdriver.PhantomJS()
	fullTextDriver.get(currLink)

	fullTextDriver.find_element_by_link_text(issue).click()

	allFullText = fullTextDriver.find_elements_by_link_text('Full Text')

	currURL = fullTextDriver.current_url

	print currURL
	print "TEST scrapeDriver"

	#for link in allFullText:
		#print link.text.encode('utf-8')
		#get_full_text(link, currURL)

	lengthOfArray = len(allFullText)
	for i in range(1,lengthOfArray+1):
		get_full_text((('//*[@id="tocContent"]/table[%d]/tbody/tr/td[3]/a[2]') % (i)), currURL)

	print "TEST scrapeDriver"

def get_full_text(xpath, currLink):

	scrapeDriver = webdriver.PhantomJS()
	
	scrapeDriver.get(currLink)
	scrapeDriver.find_element_by_xpath(xpath).click()

	json_dict = {}

	if not os.path.exists(os.getcwd()+'/jsonFilesAMS'):
		os.makedirs(os.getcwd()+'/jsonFilesAMS')


	print "TEST scrapeDriver"

	try:
		URL = scrapeDriver.current_url
		json_dict['id'] = URL
	except:
		print 'ID was not found on this page'
		json_dict['id'] = 'Null'


	try:
		title = scrapeDriver.find_element_by_class_name('arttitle')
		json_dict['title'] = title.text.encode('utf-8')
		#print 'Title: ' + title.text.encode('utf-8')
	except:
		print 'Title was not found on this page'
		json_dict['title'] = 'Null'


	try:
		abstract = scrapeDriver.find_element_by_class_name('abstractSection')
		#print 'Abstract: ' + abstract.text.encode('utf-8')
		json_dict['abstract'] = abstract.text.encode('utf-8')
	except:
		print 'Abstract was not found on this page'
		json_dict['abstract'] = 'Null'


	try:
		ack = scrapeDriver.find_element_by_class_name('ack')
		#print 'Acknowledgement: ' + ack.text.encode('utf-8')
		json_dict['acknowledgement'] = ack.text.encode('utf-8')
	except:
		print 'Acknowledgements not found on this page'
		json_dict['acknowledgement'] = 'Null'


	try:
		author = scrapeDriver.find_element_by_class_name('artAuthors')
		#print 'Citation Authors: ' + artAuthors.text.encode('utf-8')
		json_dict['citation_author'] = artAuthors.text.encode('utf-8')
	except:
		print 'Citation Authors not found on this page'
		json_dict['citation_author'] = 'Null'


	try:
		references = scrapeDriver.find_element_by_class_name('references')
		#print 'References: ' + references.text.encode('utf-8')
		json_dict['article_references'] = references.text.encode('utf-8')
	except:
		print 'References not found on this page'
		json_dict['article_references'] = 'Null'


	try:
		citationDOI = scrapeDriver.find_element_by_xpath('//*[@id="rightColumn"]/div[3]/a')
		#print 'citationDOI: ' + citationDOI.text.encode('utf-8')
		json_dict['citation_doi'] = citationDOI.text.encode('utf-8')
	except:
		print 'Citation DOI was not found on this page'
		json_dict['citationDOI'] = 'Null'

	filenameJSON = os.getcwd()+'/jsonFilesAMS/'+ json_dict['id'].split('://')[1].replace('/','-')+'.json'
	with open(filenameJSON, 'w+') as f:
		json.dump(json_dict, f)


info_from_ams() 

#//*[@id="tocContent"]/table[1]/tbody/tr/td[3]/a[1]
#//*[@id="tocContent"]/table[2]/tbody/tr/td[3]/a[1]