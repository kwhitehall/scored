from selenium import webdriver
from bs4 import BeautifulSoup, SoupStrainer
import time, sys, os, difflib, fileinput, re, urllib2, cookielib, json, multiprocessing


if os.path.exists(os.getcwd()+'/seedList.txt'):
	os.remove(os.getcwd()+'/seedList.txt')
# if os.path.exists(os.getcwd()+'/issuelist.txt'):
# 	os.remove(os.getcwd()+'/issuelist.txt')


class scrapeAMSJournal(object):
	def __init__(self):
		self.driver = webdriver.PhantomJS()
		self.driver.set_window_size(1024, 768)
		self.driver.get('http://agupubs.onlinelibrary.wiley.com/agu/')#('http://journals.ametsoc.org')
		self.cj = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		self.xpages = 10

	def info_from_agu(self):
		'''
			Purpose: To Iterate through each AMS Journal page within the website.  
		'''

		# allIssues = self.driver.find_elements_by_xpath("//div[@class='content-area']/div/div/div/ul/li")
		# fname = 'issuelist.txt'
		# url ='http://agupubs.onlinelibrary.wiley.com/agu/'
		# with open(fname, 'ab+') as f:
		# 	for i in allIssues:
		# 		if 'journal' in i.find_element_by_tag_name('a').get_attribute('href'):
		# 			if url in i.find_element_by_tag_name('a').get_attribute('href'):
		# 				f.write('%s\n' %((i.find_element_by_tag_name('a').get_attribute('href'))+'(issues)'))
		# 			else:
		# 				f.write('%s\n' %i.find_element_by_tag_name('a').get_attribute('href'))
		# 			print i.find_element_by_tag_name('a').text
		# self.driver.close()
		# sys.exit()
		
		fname = 'issuelist.txt'
		allIssues = [line.rstrip() for line in open(fname)]
		jobs = []
		
		#get every xpages in parallel
		for i in range(0, len(allIssues), self.xpages):
			for j in range(i, i+self.xpages):
				p = multiprocessing.Process(target=self.get_articles_list(allIssues[j]), args=(allIssues[j],))
				jobs.append(p)
				p.start()
			jobs = []

		#get info from pages - also in parallel
		allArticles = [line.rstrip() for line in open('seedList.txt')]
		jobs = []
		for i in range(0, len(allArticles), self.xpages):
			for j in range(i, i+self.xpages):
				try:
					p = multiprocessing.Process(target=self.get_full_text(allArticles[j]), args=(allArticles[j],))
					jobs.append(p)
					p.start()
				except:
					print 'finished'
			jobs = []

	def info_from_ams(self):
		'''
			Purpose: To Iterate through each AMS Journal page within the website.  
		'''

		# currLink = self.driver.current_url

		allIssues = self.driver.find_elements_by_partial_link_text('Available')
		strain = "middleCol"
		fname = 'issuelist.txt'

		for i in allIssues:
			print i.get_attribute('href')
			soup = self.get_page_soup(i.get_attribute('href'), strain)
		
			self.get_issues_list(soup, fname)

		self.driver.close()
		
		fname = 'issuelist.txt'
		allIssues = [line.rstrip() for line in open(fname)]
		jobs = []
		
		#get every xpages in parallel
		for i in range(0, len(allIssues), self.xpages):
			for j in range(i, i+self.xpages):
				p = multiprocessing.Process(target=self.get_articles_list(allIssues[j]), args=(allIssues[j],))
				jobs.append(p)
				p.start()
			jobs = []

		#get info from pages - also in parallel
		allArticles = [line.rstrip() for line in open('seedList.txt')]
		jobs = []
		for i in range(0, len(allArticles), self.xpages):
			for j in range(i, i+self.xpages):
				try:
					p = multiprocessing.Process(target=self.get_full_text(allArticles[j]), args=(allArticles[j],))
					jobs.append(p)
					p.start()
				except:
					print 'finished'
			jobs = []

	def get_html(self, link):
		''' reach html using urllib2 & cookies '''
		try:
			request = urllib2.Request(link)
			response = self.opener.open(request)
			time.sleep(5)
			return response.read()
		except:
			print 'unable to reach link'
			return False

	def get_page_soup(self, link, strain=None):
		''' return html using BS for a page '''
		html = self.get_html(link)

		if html:
			if strain:
				strainer = SoupStrainer(id=strain)
				return BeautifulSoup(html, parse_only=strainer)
			else:
				return BeautifulSoup(html)
		

	def get_issues_list(self, soup, filename, pubHouse=None):
		''' generate issuelist from all issues on a given page'''

		stopwords = ['facebook', 'twitter', 'youtube', 'linkedin', 'membership', 'subscribe', 'subscription', 'blog'\
					 'submit', 'contact', 'listserve', 'login', 'disclaim']
		currLink = ''
		lastURL = ''
		penulURL = ''

		for link in soup.find_all('a'):
			
			if 'seedList' in filename:
				try:
					allLines = [line.rstrip() for line in open(filename)]
				except:
					allLines = []
				
				with open(filename,'ab+') as f:
					if (link.get('href')).lower().startswith('http') or 'doi/' in link.get('href'):	
						if (link.get('href')).lower().startswith('/doi'):
							if pubHouse:
								currLink = pubHouse+link.get('href')
						else:
							currLink = link.get('href')
						
						if not(any(word in currLink.lower() for word in stopwords)):
							print 'currLink: ',currLink
							if 'abs' in currLink.lower():
								f.write('%s\n' %currLink)
							if 'full' in currLink.lower():
								textDiff = self.compare_text(currLink, allLines)
								
								if textDiff == True:
									f.write('%s\n' %currLink)
			else:
				with open(filename,'ab+') as f:
					if (link.get('href')).lower().startswith('http') or 'doi/' in link.get('href'):	
						if currLink.lower().startswith('/doi'):
							if pubHouse:
								currLink = pubHouse+link.get('href')
						else:
							currLink = link.get('href')
						
						if not(any(word in currLink.lower() for word in stopwords)):
							f.write('%s\n' %currLink)
					

	def compare_text(self, url, urlList):
		''' check for link in a urlList '''

		textDiff = ''
		diffList = []

		if urlList == [] or len(urlList) < 2:
			return True

		for i in urlList:
			textDiff = ''
			for _,s in enumerate(difflib.ndiff(url, i)):
				if s[0] == ' ': continue
				elif s[0] == '+': textDiff += s[2]
			diffList.append(textDiff)
		
		for diff in diffList:
			if ('abs' in diff.lower() and len(diff) <= 9) or (diff == None):
				return False

		return True
	
	def get_articles_list(self, page):
		''' generate the journals lists from the issues list '''
		
		soup = self.get_page_soup(page)
		fname = 'seedList.txt'
		pubHouse = 'http://'+page.split('http://')[1].split('/')[0]
		print 'pubHouse ', pubHouse
		self.get_issues_list(soup,fname, pubHouse)


	def get_meta_data(self, soup):
		''' get page metadata using BS'''

		metaDict = {}
		authors = []
		pubdate = []
		subject = []
		keywords = []
		format = ''
		fileType = ''
		doiidentifier = ''
		pubidentifier = ''
		source = ''
		title = ''
		rights = ''
		contentType = ''

		try:
			allMeta = soup.findAll('meta')
		except:
			print 'no metaData'
			return False

		for tag in allMeta:
			if tag.get('name'):
				if 'creator' in tag.get('name').lower() or 'author' in tag.get('name').lower():
					authors.append(tag.get('content'))

				if 'type' in tag.get('name').lower():
					fileType = tag.get('content')
				
				if 'subject' in tag.get('name').lower():
					subjet.append(tag.get('content'))

				if 'keyword' in tag.get('name').lower():
					keywords.append(tag.get('content'))

				if 'format' in tag.get('name').lower():
					format = tag.get('content')

				if 'title' in tag.get('name').lower():
					title = tag.get('content')

				if 'source' in tag.get('name').lower():
					source = tag.get('content')

				if 'rights' in tag.get('name').lower():
					rights = tag.get('content')

				if 'date' in tag.get('name').lower():
					pubdate.append(tag.get('content'))
					try:
						pubdate.append(tag.get('scheme'))
					except:
						continue

				if 'identifier' in tag.get('name').lower():
					try:
						if 'doi' in tag.get('scheme').lower():
							doiidentifier = tag.get('content')
					except:
						continue

					try:
						if 'publisher' in tag.get('scheme').lower():
							pubidentifier = tag.get('content')
					except:
						continue

		return {'metaAuthors':authors,
					'date':pubdate,
					'subject':subject,
					'keywords':keywords,
					'format':format,
					'fileType':fileType,
					'doi':doiidentifier,
					'pubid':pubidentifier,
					'source':source,
					'metaTitle':title,
					'rights':rights,
					'contentType':contentType}

	
	def get_full_text(self, page):
		''' Extract the data from a page '''
		metaDict = {}
		contentDict = {}
		abstract = ''
		authors = []
		affilations = []

		soup = self.get_page_soup(page)
		metaDict = self.get_meta_data(soup)

		print 'text from: ', page

		if not os.path.exists(os.getcwd()+'/jsonFilesAMS'):
			os.makedirs(os.getcwd()+'/jsonFilesAMS')

		contentDict['id'] = page

		try:
			for i in soup.find_all(class_=re.compile("^abstr")):
				abstract += i.find('p').text.encode('utf-8')
		except:
			print 'Abstract was not found on this page'

		try:
			title = soup.find_all(class_=re.compile("itle"))
			contentDict['title'] = title.text.encode('utf-8')
		except:
			print 'Title was not found on this page'
			contentDict['title'] = 'Null'

		try:
			ack = soup.find_all(class_=re.compile("cknowledgement"))
			contentDict['acknowledgement'] = ack.text.encode('utf-8')
		except:
			print 'Acknowledgements not found on this page'
			contentDict['acknowledgement'] = 'Null'

		try:
			for x in soup.find_all(class_=re.compile("uthor")):
				try:
					for k in x.find_all('strong'):
						authors.append(k.text.encode('utf-8'))
				except:
					continue
				try:
					y = x.find_all('p')
					if not authors:
						for z in y:
							authors.append(z.text.encode('utf-8'))
					else:
						for z in y:
							affilations.append(z.text.encode('utf-8'))
				except:
					continue
		except:
			print 'Citation Authors info not found on this page'
			contentDict['citation_authors'] = 'Null'

		contentDict['abstract'] = abstract
		contentDict['citation_authors'] = authors
		contentDict['citation_affilations'] = affilations

		if metaDict:
			contentDict.update(metaDict)

		if abstract:
			filenameJSON = os.getcwd()+ '/jsonFilesAMS/'+ page.split('://')[1].replace('/','-').replace('.','-') +'.json'
			
			with open(filenameJSON, 'w+') as f:
				json.dump(contentDict, f)


def main():
	print 'Extracting Data from Journals...'
	journals = scrapeAMSJournal()
	journals.info_from_agu() 

if __name__ == '__main__':
    main()

#//*[@id="tocContent"]/table[1]/tbody/tr/td[3]/a[1]
#//*[@id="tocContent"]/table[2]/tbody/tr/td[3]/a[1]