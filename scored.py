from selenium import webdriver
from bs4 import BeautifulSoup, SoupStrainer
import time, sys, os, difflib, fileinput, re, urllib2, cookielib, json, multiprocessing, warnings

'''Purpose: To create seedlist of journal issues and extract article page metadata from journal sites 
	Inputs: URL of website
			num - 0, 1, 2 (indicating file with xpaths, classtag or xpath) 
			input1 - location of file of xpaths if num ==0; class tag string if num == 1; xpath tag string
					  if num ==2
'''

class scored(object):
	def __init__(self, url, num, input1=None):
		if os.path.exists(os.getcwd()+'/scored.log'):
			os.remove(os.getcwd()+'/scored.log')

		self.driver = webdriver.PhantomJS()
		self.driver.set_window_size(1024, 768)
		self.cj = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		self.xpages = 10
		self.url = url
		self.log = os.getcwd() + '/scored.log'
		self.f = open(self.log,'ab+')
		self.num = num
		self.input1 = input1
		warnings.filterwarnings("error")

	def _tear_down(self):
		self.driver.quit()
		return True

	def get_journal_list(self):
		if os.path.exists(os.getcwd()+'/journals.txt'):
			os.remove(os.getcwd()+'/journals.txt')

		self.driver.get(self.url)
		fname = 'journals.txt'
		
		with open(fname, 'ab+') as f:
			if self.num == 0:
				try:
					self.f.write('Name of file: %s\n' %self.input1 )
					xpathList = [line.strip() for line in open(self.input1)]
					for xpath in xpathList:
						xpathElement = self.driver.find_element_by_xpath(xpath)
						self.f.write('xpath: %s\n' %xpathElement.get_attribute('href'))
						f.write('%s\n' %xpathElement.get_attribute('href'))
				except:
					print 'The file ' + self.input1 + ' does not exist'

			elif self.num == 1:
				try:
					classTagArray = self.driver.find_elements_by_class_name(self.input1)
					self.f.write('Using %s as class tag \n' %self.input1)
					for classTag in classTagArray:
						self.f.write('class: %s\n' %classTag.find_element_by_tag_name('a').get_attribute('href'))
						f.write('%s\n' %classTag.find_element_by_tag_name('a').get_attribute('href'))
				except: 
					print 'The class_name '+ self.input1 + 'is not valid on the input site provided'
			
			elif self.num == 2:
				try:
					allXpaths = self.driver.find_elements_by_xpath(self.input1)
					for i in allXpaths:
						if 'journal' in i.find_element_by_tag_name('a').get_attribute('href'):
							if self.url in i.find_element_by_tag_name('a').get_attribute('href'):
								currLink = (i.find_element_by_tag_name('a').get_attribute('href'))+'issues'
							else:
								currLink = i.find_element_by_tag_name('a').get_attribute('href')
							f.write('%s\n' %currLink)
				except:
					print 'The xpath provided, ' + self.input1 + 'is not valid for the input site provided'
			
			else:
				soup = self._get_page_soup(self.url) 
				print soup
				try:
					for link in soup.find_all('a'):
						if 'homepage' in link.text.lower():
							f.write('%s\n' %link.get('href'))
				except:
					print 'Cannot locate journals on this page!'

		self._tear_down()


	def get_issues_list(self):
		''' get all issues '''

		if os.path.exists(os.getcwd()+'/issuelist.txt'):
			os.remove(os.getcwd()+'/issuelist.txt')

		if not os.path.exists(os.getcwd()+'/journals.txt'):
			self.f.write('No journals list available! \n')
			print 'No journals list available! \n'
			sys.exit(1)

		fname = 'issuelist.txt'
		jfname = 'journals.txt'

		try:
			journals = [line.rstrip() for line in open(jfname)]
		except: 
			self.f.write('No journals.txt\n')
			sys.exit()
		for j in journals:
			soup = self._get_page_soup(j)
			self._get_list(soup, j, fname)


	def get_articles_list(self):
		''' generate the journals lists from the issues list '''
		
		if os.path.exists(os.getcwd()+'/seedlist.txt'):
			os.remove(os.getcwd()+'/seedlist.txt')

		if not os.path.exists(os.getcwd()+'/issuelist.txt'):
			self.f.write('No issuelist available! \n')
			print 'No issuelist available! \n'
			sys.exit(1)

		fname = 'seedlist.txt'
		iname = 'issuelist.txt'
		issues = []
		again = True

		try:
			issues = [line.rstrip() for line in open(iname)]
		except: 
			self.f.write('No issuelist.txt\n')
			sys.exit()

		for page in issues:
			soup = self._get_page_soup(page)
			self._get_list(soup, page, fname)


	def _get_html(self, link, selenium=None):
		''' reach html using urllib2 & cookies '''
		if selenium:
			self.driver.get(link)
			time.sleep(5)
			self._tear_down()
			return self.driver.page_source
		else:
			try:
				request = urllib2.Request(link)
				response = self.opener.open(request)
				time.sleep(5)
				self.cj.clear()
				return response.read()	
			except:
				print 'unable to reach link'
			return False


	def _get_page_soup(self, link, selenium = None, strain=None):
		''' return html using BS for a page '''
		print 'in get_page_soup ', link

		if selenium:
			html = self._get_html(link, selenium=True)
		else:
			html = self._get_html(link)

		if html:
			if strain:
				strainer = SoupStrainer(id=strain)
				try:
					return BeautifulSoup(html, parse_only=strainer)
				except UserWarning:
					return BeautifulSoup(html, "lxml", parse_only=strainer)
				except:
					return False
			else:
				try:
					return BeautifulSoup(html)
				except UserWarning:
					return BeautifulSoup(html, "lxml")
				except:
					return False
		

	def _get_list(self, soup, soupURL, filename, pubHouse=None):
		''' generate issuelist from all issues on a given page'''

		stopwords = ['facebook', 'twitter', 'youtube', 'linkedin', 'membership', 'subscribe', 'subscription', 'blog',\
					 'submit', 'contact', 'listserve', 'login', 'disclaim', 'editor', 'section', 'librarian', 'alert',\
					 '#', 'email', '?', 'copyright', 'license', 'charges', 'terms', 'mailto:', 'submission', 'author',\
					 'media', 'news', 'rss', 'mobile', 'help', 'award', 'meetings','job', 'access', 'privacy', 'features'\
					 'information', 'search', 'book', 'aim', 'language', 'edition']
		currLink = ''
		issues = []
		issuelist = []
		links = []
		seeds = []
		eachlink = ''
		
		try:
			journals = [line.rstrip() for line in open('journals.txt')]
		except:
			journals = []
			self.f.write('No journals.txt to compare urls against. \n')
			
		if 'seedlist.txt' in filename:
			try:
				issues = [line.rstrip() for line in open('issuelist.txt')]
			except:
				issues = []
				self.f.write('No issuelist.txt to compare urls against. \n')
		
		for link in soup.find_all('a', href=True):
			if not pubHouse:
				pubHouse = 'http://'+self.url.split('http://')[1].split('/')[0]

			doi = self._link_has_doi(link.get('href'))

			try:
				allLines = [line.rstrip() for line in open(filename)]
			except:
				allLines = []
			
			try:
				issuesTmp = [line.rstrip() for line in open('issuelistTmp.txt')]
			except:
				issuesTmp = []

			allLines += journals + issues + issuesTmp

			allLines.append(soupURL)

			with open(filename,'ab+') as f:
				currLink = self._get_link(link.get('href'), pubHouse)
				textDiff = self._compare_text(currLink.rstrip(), allLines)

				if pubHouse in currLink: #not this! cause this discredits pub houses that host others e.g. egu
					if 'issuelist.txt' in filename:
						if currLink.lower().startswith('http') or doi:
							if not(any(word in currLink.lower() for word in stopwords)):
								if textDiff == True:
									if re.findall('issue', link.get('href').lower()):
										if re.findall('issue', link.getText().lower()):
											f.write('%s\n' %currLink)
										else:
											issuelist.append(currLink)
									elif 'articles' in link.text.lower():
										f.write('%s\n' %currLink)
									else:
										links.append(currLink)

					elif 'seedlist.txt' in filename:
						if currLink.lower().startswith('http') or doi:	
							if not(any(word in currLink.lower() for word in stopwords)):
								if 'abs' in currLink.lower():
									f.write('%s\n' %currLink)
									seeds.append(currLink)
								elif 'full' in currLink.lower():
									if textDiff == True:
										f.write('%s\n' %currLink)
										seeds.append(currLink)						

					else:
						if not(any(word in currLink.lower() for word in stopwords)):
							if textDiff == True:
								f.write('%s\n' %currLink)

		# recursion for finding issuelist if necessary
		if 'issuelist.txt' in filename:
			with open(filename,'ab+') as f:
				if len(issuelist) == 0:
					for i in links:
						f.write('%s\n' %i)
					links = []
					return 
				else:
					with open('issuelistTmp.txt', 'ab+') as t:
						t.write('%s\n' %issuelist[0])
					soup = self._get_page_soup(issuelist[0])
					self._get_list(soup, issuelist[0].rstrip(), filename, pubHouse)

		#try selenium to access the page
		if 'seedlist.txt' in filename:
			if len(seeds) == 0:
				soup = self._get_page_soup(soupURL, selenium=True)
				for link in soup.find_all('a', href=True):
					doi = self._link_has_doi(link.get('href'))
					currLink = self._get_link(link.get('href'), pubHouse)
					textDiff = self._compare_text(currLink.strip(), allLines)
					with open(filename,'ab+') as f:
						if currLink.lower().startswith('http') or doi:	
							if not(any(word in currLink.lower() for word in stopwords)):
								if textDiff == True:
									if 'abs' in currLink.lower():
										f.write('%s\n' %currLink)
										allLines.append(currLink)
									elif 'full' in currLink.lower():
										if textDiff == True:
											f.write('%s\n' %currLink)
											allLines.append(currLink)

			
	def _get_link (self, link, pubHouse):
		''' utility function for generating an absolute link if necessary '''
		if not link.lower().startswith('http'):
			if pubHouse:
				return pubHouse+link
		else:
			return link


	def _link_has_doi (self, link):
		''' utility function to check if a link is a doi link '''
		if not link.lower().startswith('http'):
			if 'doi/' in link:
				return True
			elif any([self._is_number(i) for i in link.split('/')]):
				return True
			else:
				return False


	def _is_number(self,s):
		''' utility function to check if a string is a decimal number'''
		try:
			float(s)
			if '.' in s:
				return True
			else: 
				return False
		except ValueError:
			return False


	def _compare_text(self, url, urlList):
		''' check for link in a urlList '''

		textDiff = ''
		diffList = []

		if self.url == url or self.url+'/' == url:
			return False

		elif urlList == [] or len(urlList) < 2:
			return True

		elif filter(lambda x: url in x, urlList):
			return False

		else:
			for i in urlList:
				textDiff = ''
				for _,s in enumerate(difflib.ndiff(url, i)):
					if s[0] == ' ': continue
					elif s[0] == '+': textDiff += s[2]
				diffList.append(textDiff)
			
			for diff in diffList:
				if diff == None or ('abs' in diff.lower() and len(diff) <= 9):
					return False
				
		return True


	def _get_meta_data(self, soup):
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

		soup = self._get_page_soup(page)
		metaDict = self._get_meta_data(soup)

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
			filenameJSON = os.getcwd()+ '/jsonFiles/'+ page.split('://')[1].replace('/','-').replace('.','-') +'.json'
			
			with open(filenameJSON, 'w+') as f:
				json.dump(contentDict, f)


def main():
	URLlink = 'http://www.egu.eu/publications/open-access-journals/'
	journals = scored(URLlink,-1)
	print 'Extracting Data from Journals...'
	# journals.get_journal_list() 
	# journals.get_issues_list()
	journals.get_articles_list()


if __name__ == '__main__':
    main()