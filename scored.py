#!/usr/bin/env python2.7
# encoding: utf-8
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

'''Purpose: To create seedlist of journal issues and extract article page metadata from journal sites 
	Inputs: URL of website
			num - 0, 1, 2 (indicating file with xpaths, classtag or xpath) 
			input1 - location of file of xpaths if num ==0; class tag string if num == 1; xpath tag string
					  if num ==2
'''

from selenium import webdriver
from bs4 import BeautifulSoup, SoupStrainer
from collections import Counter
import time, sys, os, difflib, fileinput, re, urllib2, cookielib, json, multiprocessing, random, warnings



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
		self.stopwords = ['facebook', 'twitter', 'youtube', 'linkedin', 'membership', 'subscribe', 'subscription', 'blog',\
					 'submit', 'contact', 'listserve', 'login', 'disclaim', 'editor', 'section', 'librarian', 'alert',\
					 '#', 'email', '?', 'copyright', 'license', 'charges', 'terms', 'mailto:', 'submission', 'author',\
					 'media', 'news', 'rss', 'mobile', 'help', 'award', 'meetings','job', 'access', 'privacy', 'features'\
					 'information', 'search', 'book', 'aim', 'language', 'edition', 'discuss', 'ethics', 'cited', 'review'\
					 'metrics', 'highlight', 'about', 'imprint', 'peer_review', 'comment', 'pol', 'account', '.xml', '.ris'\
					 '.bib']
		
		warnings.filterwarnings("error")


	def _tear_down(self):
		self.driver.close() 
		return True


	def get_journal_list(self):
		if os.path.exists(os.getcwd()+'/journals.txt'):
			os.remove(os.getcwd()+'/journals.txt')

		self.driver.get(self.url)
		fname = 'journals.txt'
		allTags = []
		
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
				if not soup:
					self.f.write('soup not returned \n')
					return False

				try:
					for link in soup.find_all('a'):
						if 'homepage' in link.text.lower():
							f.write('%s\n' %link.get('href'))
						else:
							allTags.append(link.get('href'))

					if allTags:
						links = [x for x in self._isSimilar_urls(allTags) if len(x.split('/')) > 3]
						for link in links: 
							f.write('%s\n' %link)
				except:
					print 'Cannot locate journals on this page!'

		self.f.write('Finished with get_journal_list\n')
		print 'Finished with get_journal_list'
		self._tear_down()
		return True


	def get_issues_list(self):
		''' get all issues '''

		if os.path.exists(os.getcwd()+'/issuelist.txt'):
			os.remove(os.getcwd()+'/issuelist.txt')

		if os.path.exists(os.getcwd()+'/issuelistTmp.txt'):
			os.remove(os.getcwd()+'/issuelistTmp.txt')

		if not os.path.exists(os.getcwd()+'/journals.txt'):
			self.f.write('No journals list available! \n')
			print 'No journals list available! \n'
			sys.exit(1)

		fname = 'issuelist.txt'
		jfname = 'journals.txt'
		useSel = False
		sel = []

		try:
			journals = [line.rstrip() for line in open(jfname)]
			random.shuffle(journals)
		except: 
			self.f.write('No journals.txt\n')
			sys.exit()
		
		for page in journals:
			if len(sel) > 1:
				# check for page similarity to the selenium pages
				# if similiar to any page in there, _get_page_soup with selenium
				for i in sel:
					curr = self._find_common_patterns(page, i)
					if len(curr[0]) == len(curr[1]):
						print 'using selenium'
						self.f.write('using selenium to access %s\n' %page)
						useSel = True
						soup = self._get_page_soup(page, selenium=True)
						if not soup:
							self.f.write('soup not returned \n')
							return False
						s = self._get_list(soup, page, fname)
						if s != [] : sel.append(s) 
						break
				if useSel == False:
					soup = self._get_page_soup(page)
					if not soup:
						self.f.write('soup not returned \n')
						return False
					s = self._get_list(soup, page, fname)
					if s != [] or s != None: sel.append(s)
			else:
				soup = self._get_page_soup(page)
				if not soup:
					self.f.write('soup not returned \n')
					return False
				s = self._get_list(soup, page, fname)
				if s != [] or s != None: sel.append(s)

			useSel = False

		self.f.write('Finished with get_issues_list\n')
		print 'Finished with get_issues_list'
		return True


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
		useSel = False
		sel = []
		
		try:
			issues = [line.rstrip() for line in open(iname)]
			random.shuffle(issues)
		except: 
			self.f.write('No issuelist.txt\n')
			sys.exit()

		for page in issues:
			if len(sel) > 1:
				# check for page similarity to the selenium pages
				# if similiar to any page in there, _get_page_soup with selenium
				for i in sel:
					curr = self._find_common_patterns(page, i)
					if len(curr[0]) == len(curr[1]):
						print 'using selenium'
						self.f.write('using selenium to access %s\n' %page)
						useSel = True
						soup = self._get_page_soup(page, selenium=True)
						if not soup:
							self.f.write('soup not returned \n')
							return False
						s = self._get_list(soup, page, fname)
						if s != [] : sel.append(s) 
						break
				if useSel == False:
					soup = self._get_page_soup(page)
					if not soup:
						self.f.write('soup not returned \n')
						return False
					s = self._get_list(soup, page, fname)
					if s != []: sel.append(s)
			else:
				soup = self._get_page_soup(page)
				if not soup:
					self.f.write('soup not returned \n')
					return False
				s = self._get_list(soup, page, fname)
				if s != []: sel.append(s)

			useSel = False

		self.f.write('Finished with get_articles_list\n')
		print 'Finished with get_articles_list'
		return True


	def get_full_text(self):
		'''Driver script to extract data from page '''
		allArticles = [line.rstrip() for line in open('seedlist.txt')]		
		jobs = []
		random.shuffle(allArticles)
		if len(allArticles) < self.xpages:
			step = 2
		else:
			step = self.xpages
		for i in range(0, len(allArticles), step):
			for j in range(i, i+step):
				try:
					p = multiprocessing.Process(target=self._extract_full_text(allArticles[j]), args=(allArticles[j],))
					jobs.append(p)
					p.start()
				except:
					jobs = []

		self.f.write('Finished with get_full_text\n')
		print 'Finished with get_full_text'
		return True


	def get_all(self):
		''' Run the full program '''
		j = self.get_journal_list()
		if j == True:
			i = self.get_issues_list()
		if i == True:
			a = self.get_articles_list()
		if a == True:
			f == self.get_full_text()

		if f == True:
			self.f.write('Finished with get_all\n')
			print 'Finished with get_all'
			return True


	def _get_html(self, link, selenium=None):
		''' reach html using urllib2 & cookies or selenium & PhantomJS'''

		print 'in _get_html ', link, selenium
		self.f.write('in _get_html with %s and selenium= %s' %(link, selenium))

		if not selenium:
			try:
				request = urllib2.Request(link)
				response = self.opener.open(request)
				time.sleep(self._get_random_time())
				self.cj.clear()
				return response.read()	
			except:
				print 'unable to reach link'
				self.f.write('unable to reach %s with urllib2' %link)
			return False
		else:
			try:
				sel = webdriver.PhantomJS() 
				sel.get(link)
				time.sleep(self._get_random_time())
				html = sel.page_source
				sel.close()
				return html	
			
			except:
				print 'unable to reach link with selenium'
				self.f.write('unable to reach %s with selenium' %link)
				return False


	def _get_page_soup(self, link, selenium = None, strain=None):
		''' return html using BS for a page '''
		
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
		else:
			return False
		

	def _get_list(self, soup, soupURL, filename, pubHouse=None):
		''' generate issuelist from all issues on a given page'''

		currLink = ''
		issues = []
		issuelist = []
		links = []
		seeds = []
		allTags = []
		eachlink = ''
		allLinks = []
		seleniumList = []
		counts = []
		
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

			currLink = self._get_link(link.get('href'), pubHouse)

			if len(currLink.split('/')) > 3:
				allLinks.append(currLink)

		allURLs = self._isSimilar_urls(allLinks)

		allURLs = list(set(allURLs))

		filter(None, allURLs)

		for i in allURLs:
			curr = self._find_common_patterns(allURLs[0], i)
			if counts == []:
				counts.append((len(curr[0]),1, curr[0][0][1]))
			else:
				loc = [counts.index(item) for item in counts if item[0] == len(curr[0])]
				if loc:
					total = counts[loc[0]][1] + 1
					counts.pop(loc[0])
					counts.append((len(curr[0]),total, curr[0][0][1]))
				else:
					counts.append((len(curr[0]),1, curr[0][0][1]))

		topLen = sorted(counts, key=lambda x:x[1])[-1][0]
		topCom = sorted(counts, key=lambda x:x[1])[-1][2]
		

		for currLink in allURLs:

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
				
				if 'issuelist.txt' in filename:
					if currLink.lower().startswith('http') or doi:
						if not(any(word in currLink.lower() for word in self.stopwords)):
							textDiff = self._compare_text(currLink.rstrip(), allLines)
							if textDiff == True:
								if re.findall('issue', currLink.lower()): 
									if re.findall('issue', currLink.lower()): #.getText().lower()):
										f.write('%s\n' %currLink)
									else:
										issuelist.append(currLink)
								elif 'articles' in currLink.lower():
									f.write('%s\n' %currLink)
								elif 'volumes' in currLink.lower():
									issuelist.append(currLink)
								else:
									links.append(currLink)
									seleniumList.append(currLink)

				elif 'seedlist.txt' in filename:
					if currLink.lower().startswith('http') or doi:	
						if not(any(word in currLink.lower() for word in self.stopwords)):
							textDiff = self._compare_text(currLink.rstrip(), allLines)
							abstract = soup.find_all(class_=re.compile("^abstr"))
							if 'abs' in currLink.lower():
								f.write('%s\n' %currLink)
								seeds.append(currLink)
							elif 'full' in currLink.lower():
								if textDiff == True:
									f.write('%s\n' %currLink)
									seeds.append(currLink)	
							elif abstract != []:
								for i in abstract:
									if i.find('p') or i.find(class_=re.compile("abstr")):
										f.write('%s\n' %currLink)
										seeds.append(currLink)
							elif topCom in currLink:
								f.write('%s\n' %currLink)
								seeds.append(currLink)
							else: #else if not abstract on page:else:
								seleniumList.append(currLink)

				else:
					if not(any(word in currLink.lower() for word in self.stopwords)):
						textDiff = self._compare_text(currLink.rstrip(), allLines)
						if textDiff == True:
							f.write('%s\n' %currLink)

		# recursion for finding issuelist if necessary
		if 'issuelist.txt' in filename:
			with open(filename,'ab+') as f:
				if len(issuelist) == 0:
					for i in links:
						if not(any(word in i.lower() for word in self.stopwords)):
							f.write('%s\n' %i)
					links = []
					return 
				else:
					with open('issuelistTmp.txt', 'ab+'
						) as t:
						t.write('%s\n' %issuelist[0])
					soup = self._get_page_soup(issuelist[0])
					if not soup:
						self.f.write('soup not returned \n')
						return False

					_ = self._get_list(soup, issuelist[0].rstrip(), filename, pubHouse)

		filter(None, seleniumList)
		return seleniumList


			
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


	def _get_random_time(self):
		'''returns a random time between 5.0s and 30.0s'''
		random.seed()
		return random.uniform(5.0, 30.0)


	def _isSimilar_urls(self, urls):
		''' compare url with those in list to determine similarity.'''
		
		similarURLs = []
		
		urlList = [x for x in urls if len(x.split('/')) > 3]
		
		counts = filter(lambda x: x[1]>1 ,Counter(map (lambda x : x.split('/')[2].split('.')[-1],urlList)).most_common())
		noHttp = [x for x in filter(lambda y: 'http' not in y[0],counts)]
		unique = [x for x in filter(lambda y: '' in y[0],noHttp)]

		fil = filter(lambda x: x.lower().split('/')[2].split('.')[-1] in unique[0][0].lower(), urlList)
		textDiffs = filter(lambda x: self._compare_text(x, fil) == False, fil)
		similarURLs = filter(lambda x: not(any(word in x.lower() for word in self.stopwords)), textDiffs)
		
		return similarURLs


	def _find_common_patterns(self, s1, s2): 
		''' This function and _longest_common_substring were adapted from 
		http://codereview.stackexchange.com/questions/21532/python-3-finding-common-patterns-in-pairs-of-strings'''
		
	    if s1 == '' or s2 == '':
	        return [], []
	    com = self._longest_common_substring(s1, s2)
	    if len(com) < 2:
	        return ([(0, s1)], [(0, s2)])
	    s1Bef, _, s1Aft = s1.partition(com)
	    s2Bef, _, s2Aft = s2.partition(com)
	    before = self._find_common_patterns(s1Bef, s2Bef)
	    after = self._find_common_patterns(s1Aft, s2Aft)
	    return (before[0] + [(1, com)] + after[0], before[1] + [(1, com)] + after[1])


	def _longest_common_substring(self, s1, s2):
	    M = [[0]*(1+len(s2)) for i in range(1+len(s1))]
	    longest, xlongest = 0, 0
	    for x in range(1,1 +len(s1)):
	        for y in range(1, 1+len(s2)):
	            if s1[x-1] == s2[y-1]:
	                M[x][y] = M[x-1][y-1] + 1
	                if M[x][y] > longest:
	                    longest = M[x][y]
	                    xlongest  = x
	            else:
	                M[x][y] = 0
	    return s1[xlongest-longest: xlongest]


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
					subject.append(tag.get('content'))

				if 'keyword' in tag.get('name').lower():
					keywords.append(tag.get('content'))

				if 'format' in tag.get('name').lower():
					format = tag.get('content')

				if 'title' in tag.get('name').lower():
					try:
						for t in tag.get('content'):
							if 'citation_title' in t.lower():
								title = t.get('content')
							else:
								title = t.get('content')
					except:
						continue

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
				if 'doi' in tag.get('name').lower():
					doiidentifier = tag.get('content')

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


	def _extract_full_text(self, page):
		''' Extract the data from a page '''
		print 'text from: ', page
		
		metaDict = {}
		contentDict = {}
		abstract = ''
		authors = []
		affilations = []

		soup = self._get_page_soup(page)

		if not soup:
			self.f.write('soup not returned \n')
			return False

		metaDict = self._get_meta_data(soup)

		self.f.write('Acquiring text from %s\n' %page)

		if not os.path.exists(os.getcwd()+'/jsonFiles'):
			os.makedirs(os.getcwd()+'/jsonFiles')

		contentDict['id'] = page

		try:
			for i in soup.find_all(class_=re.compile("^abstr")):
				if i.find('p') or i.find(class_=re.compile("abstr")):
					abstract += i.text.encode('utf-8')
		except:
			print 'Abstract was not found on this page'
			self.f.write('Abstract was not found on this page\n')

		try:
			title = soup.find_all(class_=re.compile("itle"))
			try:
				if title.text.encode('utf-8'):
					t = title.text.encode('utf-8')
			except:
				for ti in title:
					if ti.find('p') or ti.find(class_=re.compile("pub")):
						t = ti.text.encode('utf-8')
					elif 'article_title' in str(ti):
						t = (str(ti).split('</span>')[0].split("article_title")[-1]).encode('utf-8')
			contentDict['title'] = t.strip()
		except:
			print 'Title was not found on this page'
			self.f.write('Title was not found on this page')
			contentDict['title'] = 'Null'

		try:
			ack = soup.find_all(class_=re.compile("cknowledgement"))
			contentDict['acknowledgement'] = ack.text.encode('utf-8')
		except:
			print 'Acknowledgements not found on this page'
			self.f.write('Acknowledgements not found on this page\n')
			contentDict['acknowledgement'] = 'Null'

		try:
			for x in soup.find_all(class_=re.compile("uthor")):
				try:
					if x.find_all('strong'):
						for k in x.find_all('strong'):
							authors.append(k.text.encode('utf-8'))
					elif x.find_all("a", class_=re.compile("uthor")):
						for k in x.find_all("a",class_=re.compile("uthor")):
							if not(any('search' in k.text.encode('utf-8').lower())):
								authors.append(k.text.encode('utf-8'))
							for i in k:
								try:
									affilations.append(i.text.encode('utf-8').split('ffiliations')[-1])
								except:
									continue
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
			self.f.write('Citation Authors info not found on this page\n')
			contentDict['citation_authors'] = 'Null'

		try:
			for x in soup.find_all(class_=re.compile("corres")):
				contentDict['corresponding_author'] = x.text.encode('utf-8').strip()
		except:
			print 'Corresponding Author info not found on this page'
			self.f.write('Corresponding Author info not found on this page\n')
			contentDict['corresponding_author'] = 'Null'

		contentDict['abstract'] = abstract
		contentDict['citation_authors'] = authors
		contentDict['citation_affilations'] = affilations

		if metaDict:
			contentDict.update(metaDict)

		if abstract:
			filenameJSON = os.getcwd()+ '/jsonFiles/'+ page.split('://')[1].replace('/','-').replace('.','-') +'.json'
			
			with open(filenameJSON, 'w+') as f:
				json.dump(contentDict, f)


if __name__ == '__main__':
	URLlink = 'http://www.egu.eu/publications/open-access-journals/' 
	journals = scored(URLlink,-1)
	print 'Extracting Data from Journals...'
	# journals.get_journal_list() 
	# journals.get_issues_list()
	journals.get_articles_list()
	# journals.get_full_text()