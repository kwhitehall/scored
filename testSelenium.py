from selenium import webdriver
#from bs4 import BeautifulSoup


driver = webdriver.PhantomJS()

driver.set_window_size(1024, 768)
driver.get('http://journals.ametsoc.org')
content = driver.page_source

def info_from_ams():

	allIssues = driver.find_elements_by_link_text('Available Issues')

	for issue in allIssues:
		print issue.text.encode('utf-8')
		get_issue_info(issue.text.encode('utf-8'))

def get_issue_info(issue):

	driver.find_element_by_link_text(issue).click()

	allCollapsed = driver.find_elements_by_css_selector('.loiListHeading.collapsed')

	for link in allCollapsed:
		link.click()

	issueList = driver.find_elements_by_class_name('loiTocUrl')

	for issue in issueList:
		print issue.text.encode('utf-8')
		get_info(issue.text.encode('utf-8'))

	print len(issueList)

def get_info(issue):

	driver.find_element_by_link_text(issue).click()

	allFullText = driver.find_elements_by_link_text('Full Text')

	currURL = driver.current_url

	print currURL

	#for link in allFullText:
		#print link.text.encode('utf-8')
		#get_full_text(link, currURL)

	lengthOfArray = len(allFullText)
	for i in range(1,lengthOfArray+1):
		get_full_text((('//*[@id="tocContent"]/table[%d]/tbody/tr/td[3]/a[2]') % (i)), currURL)


def get_full_text(xpath, currLink):

	scrapeDriver = webdriver.PhantomJS()
	
	scrapeDriver.get(currLink)
	scrapeDriver.find_element_by_xpath(xpath).click()

	try:
		URL = scrapeDriver.current_url
		print 'URL: ' + URL
	except:
		print 'URL was not found'

	try:
		title = scrapeDriver.find_element_by_class_name('arttitle')
		print 'Title: ' + title.text.encode('utf-8')
	except:
		print 'Title was not found on this page'


	try:
		abstract = scrapeDriver.find_element_by_class_name('abstractSection')
		print 'Abstract: ' + abstract.text.encode('utf-8')
	except:
		print 'Abstract was not found on this page'


	try:
		ack = scrapeDriver.find_element_by_class_name('ack')
		print 'Acknowledgement: ' + ack.text.encode('utf-8')
	except:
		print 'Acknowledgements not found on this page'


	try:
		author = scrapeDriver.find_element_by_class_name('artAuthors')
		print 'Citation Authors: ' + artAuthors.text.encode('utf-8')
	except:
		print 'Citation Authors not found on this page'


	try:
		author = scrapeDriver.find_element_by_class_name('references')
		print 'References: ' + references.text.encode('utf-8')
	except:
		print 'References not found on this page'


	try:
		citationDOI = scrapeDriver.find_element_by_xpath('//*[@id="rightColumn"]/div[3]/a')
		print 'citationDOI: ' + citationDOI.text.encode('utf-8')
	except:
		print 'Citation DOI was not found on this page'

info_from_ams() 

#//*[@id="tocContent"]/table[1]/tbody/tr/td[3]/a[1]
#//*[@id="tocContent"]/table[2]/tbody/tr/td[3]/a[1]