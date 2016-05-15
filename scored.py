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
from nutch.nutch import Nutch
from nutch.nutch import SeedClient
from nutch.nutch import Server
from nutch.nutch import JobClient
from apscheduler.schedulers.background import BackgroundScheduler
import time, sys, os, difflib, fileinput, re, urllib2, cookielib, json, multiprocessing, random, \
       warnings, subprocess, nutch

class scored(object):
	def __init__(self, nutchLoc, url, num, input1=None):
		
		self.driver = webdriver.PhantomJS()
		self.driver.set_window_size(1024, 768)
		self.cj = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		self.xpages = 10
		self.url = url
		self.storage = '/'+url.split('/')[2].replace('.','_')
		if not os.path.exists(os.getcwd()+self.storage):
			os.makedirs(os.getcwd()+self.storage)

		if os.path.exists(os.getcwd() + self.storage + '/scored.log'):
			os.remove(os.getcwd() + self.storage + '/scored.log')
		
		self.log = os.getcwd() + '/scored.log'
		self.f = open(self.log,'ab+')
		self.num = num
		self.input1 = input1
		self.count = 0
		self.seedStep = 25
		self.stopwords = ['facebook', 'twitter', 'youtube', 'linkedin', 'membership', 'subscribe', 'subscription', 'blog',\
					 'submit', 'contact', 'listserve', 'login', 'disclaim', 'editor', 'section', 'librarian', 'alert',\
					 '#', 'email', '?', 'copyright', 'license', 'charges', 'terms', 'mailto:', 'submission', 'author',\
					 'media', 'news', 'rss', 'mobile', 'help', 'award', 'meetings','job', 'access', 'privacy', 'features',\
					 'information', 'search', 'book', 'aim', 'language', 'edition', 'discuss', 'ethics', 'cited', 'review',\
					 'metrics', 'highlight', 'about', 'imprint', 'peer_review', 'comment', 'pol', 'account', '.xml', '.ris',\
					 '.bib','keyword']
		self.extensions = ['zip', 'png', 'jpeg', 'xml', 'bib', 'rss', 'gif', 'tar', 'bzip']
		
		if not os.path.exists(nutchLoc+'/runtime/local'):
			print 'No Nutch installation supplied! \n'
			self.f.write('No Nutch installation supplied! \n')
			# sys.exit()
			self.useNutch = False
		else:
			os.environ['NUTCH_HOME'] = nutchLoc
			self.nutchPID = self._start_Nutch_server()
			# self.f.write('Started Nutch Server PID %s\n' %self.nutchPID)
			# print 'Started Nutch Server PID %s\n' %self.nutchPID
			self.sv = Server('http://localhost:8081')
			self.sc = SeedClient(self.sv)
			self.useNutch = True

		warnings.filterwarnings("error")


	def _start_Nutch_server(self):
		'''
		Start NUTCH service
		Assumes:
		Returns: PID of the service
		Inputs:
		'''
		ps = subprocess.Popen("ps -ef | grep NutchServer | grep -v grep", shell=True, stdout=subprocess.PIPE).communicate()[0]
		if ps:
			self.f.write('Nutch Server is already running \n')
			print 'Nutch Server is already running \n'
			return False
		else:
			self.f.write('Starting Nutch server \n')
			print 'Starting Nutch server \n'
			nPID = subprocess.Popen([os.getenv('NUTCH_HOME')+'/runtime/local/bin/nutch','startserver']).pid
			return nPID


	def _tear_down(self):
		self.driver.close() 
		return True


	def get_journal_list(self):
		'''
		Writes the journal lists to a file
		Assumes: The URL(s) passed is (are) the landing pages for the publication house and/or the discipline
		Returns: Boolean to indicate if completed successfully
		Outputs: A text file with all of the URLs of journals from the URL supplied
		'''
		if os.path.exists(os.getcwd() + self.storage  + '/journals.txt'):
			os.remove(os.getcwd()  + self.storage + '/journals.txt')

		self.driver.get(self.url)
		fname = os.getcwd() + self.storage + '/journals.txt'
		allTags = []
		
		with open(fname, 'ab+') as f:
			if self.num == 0:
				try:
					self.f.write('Name of file: %s\n' %self.input1 )
					xpathList = [line.strip() for line in open(self.input1)]
					for xpath in xpathList:
						xpathElement = self.driver.find_element_by_xpath(xpath)
						print 'here ', xpathElement
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
							print link
							f.write('%s\n' %link)
				except:
					print 'Cannot locate journals on this page!'

		self.f.write('Finished with get_journal_list\n')
		print 'Finished with get_journal_list'
		self._tear_down()
		return True


	def get_issues_list(self):
		'''
		Writes the issues associated with a journal URL to a file
		Assumes: The URL(s) passed is (are) the landing pages for the landing page for a journal
		Returns: Boolean to indicate if completed successfully
		Outputs: A text file with all of the URLs of issues from the journal from the URL supplied
		'''
		
		if os.path.exists(os.getcwd() + self.storage + '/issuelist.txt'):
			os.remove(os.getcwd() + self.storage + '/issuelist.txt')

		if os.path.exists(os.getcwd() + self.storage + '/issuelistTmp.txt'):
			os.remove(os.getcwd() + self.storage + '/issuelistTmp.txt')

		if not os.path.exists(os.getcwd() + self.storage + '/journals.txt'):
			self.f.write('No journals list available! \n')
			print 'No journals list available! \n'
			sys.exit(1)

		fname = os.getcwd() + self.storage + '/issuelist.txt'
		jfname = os.getcwd() + self.storage + '/journals.txt'
		useSel = False
		sel = []

		try:
			journals = [line.rstrip() for line in open(jfname)]
			random.shuffle(journals)
		except: 
			self.f.write('No journals.txt\n')
			sys.exit()
		
		for page in journals:
			sel,_ = self._use_selenium(page, sel, fname)
		self.f.write('Finished with get_issues_list\n')
		print 'Finished with get_issues_list'
		self._tear_down()
		return True


	def get_articles_list(self):
		'''
		Writes the articles lists to a file
		Assumes: The URL(s) passed is (are) the landing pages for the issues associated with a particular journal
		Returns: Boolean to indicate if completed successfully
		Outputs: A text file with all of the articles URLs from the URL supplied
		'''

		# global count 
		# count = 0
		ccList = []
		continueServer = True
		current = 0

		if os.path.exists(os.getcwd() + self.storage + '/seedlist.txt'):
			os.remove(os.getcwd() + self.storage + '/seedlist.txt')

		if not os.path.exists(os.getcwd() + self.storage + '/issuelist.txt'):
			self.f.write('No issuelist available! \n')
			print 'No issuelist available! \n'
			sys.exit(1)

		fname = os.getcwd() + self.storage + '/seedlist.txt'
		iname = os.getcwd() + self.storage + '/issuelist.txt'
		useSel = False
		sel = []
		
		try:
			fissues = [line.rstrip() for line in open(iname)]
			print len(fissues)
			issues = self._remove_unwanted(fissues)
			print 'issuse '
			random.shuffle(issues)
		except: 
			self.f.write('No issuelist.txt\n')
			sys.exit()

		# if self.useNutch == True:
		# 	print 'useNutch == True'
		# 	#timer for nutch job to check every 10mins
		# 	scheduler = BackgroundScheduler()
		# 	# scheduler.add_job(self._get_seeds, 'interval', seconds=36000)
		# 	scheduler.start()
		# current = self.seedStep
		self.count = self.seedStep

		for page in issues:
			sel, useSel = self._use_selenium(page, sel, fname)
			print '** ', useSel, self.useNutch
			if self.useNutch == True:
				currSeeds = [line.rstrip() for line in open(fname)]
				# if len(currSeeds) <= self.count:
				# 	seeds = currSeeds[(len(currSeeds)/self.seedStep)*self.seedStep + (len(currSeeds)%self.seedStep):]
				# else:
				# 	seeds = currSeeds[self.count:self.count+self.seedStep]
				if len(currSeeds) > self.count and len(currSeeds) - self.count >= self.seedStep:
					seeds = currSeeds[self.count:(self.count+self.seedStep)]
					self.count += self.seedStep
					random.shuffle(seeds)
				# random.shuffle(seeds)
				# self.count += self.seedStep
					if useSel == True:
						nt = Nutch('default')#('selenium')
						config = 'default'#'selenium'
					else:
						nt = Nutch('default')
						config = 'default'
					print '========================= end config ===================='

					sd = self.sc.create('scored', seeds)
					jc = JobClient(self.sv, 'scored', config)
					cc = nt.Crawl(sd, self.sc, jc)
					ccList.append(cc)
			else:

				# while True:
				#     job = cc.progress() # gets the current job if no progress, else iterates and makes progress
				#     if job == None:
				#         break
				# currCC = self._get_seeds
				# if useSel == True:
				# 	# use nutch config for selenium
				# 	scheduler.add_job(self._get_seeds, 'interval', seconds=3)#6000)
				# else:
				# 	scheduler.add_job(self._get_seeds, 'interval', seconds=3) #6000)
			

		print ccList
		# ccListCopy = ccList
		currSeeds = [line.rstrip() for line in open(fname)]
		if len(currSeeds) > self.count:
			seeds = currSeeds[self.count:]
			random.shuffle(seeds)
			if useSel == True:
				nt = Nutch('default')#('selenium')
				config = 'default' #'selenium'
			else:
				nt = Nutch('default')
				config = 'default'
			print '========================= end config ===================='

			sd = self.sc.create('scored', seeds)
			jc = JobClient(self.sv, 'scored', config)
			cc = nt.Crawl(sd, self.sc, jc)
			ccList.append(cc)

		# stop Nutch server
		while len(ccList) != 0:
			for i in ccList:
				while True:
				    job = i.progress() # gets the current job if no progress, else iterates and makes progress
				    if job == None:
				    	ccList.remove(i)
				        break

		nt.stopServer
		self.f.write('Finished with get_articles_list\n')
		print 'Finished with get_articles_list'
		self._tear_down()

		# if self.useNutch == True:
		# 	#stop nutch server
		# 	while continueServer == True:
		# 		if count >= len([line.rstrip() for line in open(fname)]):
		# 			scheduler.shutdown()
		# 			continueServer = False

		return True


	def _get_seeds(self):
		'''
		Writes the paper lists to a file
		Assumes: The URL(s) passed is (are) the landing pages for the particular issue/ volume associated with a particular journal
		Returns: 
		Outputs: A text file with all of the paper URLs from the URL supplied
		'''
		print '^^^^ _get_seeds ', self.count
		fname = os.getcwd() + self.storage + '/seedlist.txt'
		#logic to check the how much of the file has been read
		seedStep = 5 #100
		currSeeds = [line.rstrip() for line in open(fname)]
		currlen = len(currSeeds)
		print 'len currSeeds ', len(currSeeds),' ', currlen, ' ', self.count 
		# sys.exit()

		# while self.count <= currlen:
		print ('*'*40)
		print self.count
		if currlen <= self.count:
			# print 'in if ', (currlen/seedStep)*seedStep + (currlen%seedStep)
			seeds = currSeeds[(currlen/seedStep)*seedStep + (currlen%seedStep):]
			print 'in if ',seeds
			# random.shuffle(seeds)
			# nt = self.ds(self, seeds)
		else:
			seeds = currSeeds[self.count:self.count+seedStep]
			print 'in else ', seeds #self.count+seedStep
		random.shuffle(seeds)
		self.count += seedStep
		# nt = self._send_seeds(seeds)
		# print '^^^^^^^^^^^^^ ', nt
		# nt.stopServer	
		return self._send_seeds(seeds)	


	def get_full_text(self, allArticles=None):
		'''
		Driver script to extract data from page 
		Assumes:
		Inputs: allArticles - a list of URLs 
		Returns: Boolean to indicate if completed successfully
		Outputs: JSON files from the URLs
		'''
		if not allArticles:
			allArticles = [line.rstrip() for line in open( os.getcwd() + self.storage + '/seedlist.txt')]	

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


	def _use_selenium(self, page, sel, fname):
		''' 
		Check if to use selenium 
		Inputs: page - 
				sel - 
				fname - 
		Returns:
		Outputs: sel - a list of URL to use with selenium
		         useSel - boolean to indicate whether to use selenium or not
		'''
		
		useSel = False
		if sel:
			sel = filter(None, sel)

		if sel and len(sel) > 1:
			# check for page similarity to the selenium pages
			# if similiar to any page in there, _get_page_soup with selenium
			for i in sel:
				curr = self._find_common_patterns(page, i)
				if len(curr[0]) == len(curr[1]):
					print 'using selenium'
					self.f.write('\nusing selenium to access %s\n' %page)
					useSel = True
					soup = self._get_page_soup(page, selenium=True)
					if not soup:
						self.f.write('\nsoup not returned \n')
						#break #return False
						return #False
					s = self._get_list(soup, page, fname)
					if s != [] or s != None: sel.append(s) 
					break
			if useSel == False:
				soup = self._get_page_soup(page)
				if not soup:
					self.f.write('\nsoup not returned \n')
					# break #return False
					return #False
				s = self._get_list(soup, page, fname)
				if s != [] or s != None: sel.append(s)
		else:
			soup = self._get_page_soup(page)
			if not soup:
				self.f.write('\nsoup not returned \n')
				# break #return False
				return #False
			s = self._get_list(soup, page, fname)
			if s != [] or s != None: sel.append(s)

		return sel, useSel


	def _remove_unwanted(self, URLlist):
		''' remove links with extensions that aren't needed '''
		#if journals, or issuelist open to remove the duplicates
		cleanedList = []
		try:
			pdfs = [line.strip() for line in open(os.getcwd() + self.storage + '/pdfs.txt')]
		except:
			pdfs = []

		if os.path.exists(os.getcwd() + self.storage + '/pdfs.txt'):
			os.remove(os.getcwd() + self.storage + '/pdfs.txt')

		for link in URLlist:
			try:
				extension = link.split('.')[-1]
			except:
				extension = ''

			if ('pdf' in extension.lower() or 'pdf' in link) and not link in pdfs:
				with open(os.getcwd() + self.storage + '/pdfs.txt') as p:
					p.write('%s\n' %link)
					self.f.write('PDF found: %s\n' %link)
			elif extension == '' or 'htm' in extension.lower():
				cleanedList.append(link)
			elif not(any(word in extension.lower() for word in self.extensions)):
				cleanedList.append(link)

		return cleanedList


	def _get_html(self, link, selenium=None):
		''' reach html using urllib2 & cookies or selenium & PhantomJS'''

		print 'in _get_html ', link, selenium
		self.f.write('\nin _get_html with %s and selenium= %s' %(link, selenium))

		if not selenium:
			try:
				request = urllib2.Request(link)
				response = self.opener.open(request)
				time.sleep(self._get_random_time())
				self.cj.clear()
				return response.read()	
			except Exception as e:
				print 'unable to reach link'
				self.f.write('\nunable to reach %s with urllib2\n %s' %(link,e))
				return False
		else:
			try:
				sel = webdriver.PhantomJS() 
				sel.get(link)
				time.sleep(self._get_random_time())
				html = sel.page_source
				sel.close()
				return html	
			
			except Exception as e:
				print 'unable to reach link with selenium'
				self.f.write('\nunable to reach %s with selenium\n %s' %(link,e))
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
			journals = [line.rstrip() for line in open(os.getcwd() + self.storage + '/journals.txt')]
		except:
			journals = []
			self.f.write('No journals.txt to compare urls against. \n')
			
		if 'seedlist.txt' in filename:
			try:
				issues = [line.rstrip() for line in open(os.getcwd() + self.storage + '/issuelist.txt')]
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

		allURLs = filter(None, allURLs)

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
				issuesTmp = [line.rstrip() for line in open(os.getcwd() + self.storage + '/issuelistTmp.txt')]
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
									if re.search('\\bissue\\b', currLink.lower()): #.getText().lower()):
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
					with open(os.getcwd() + self.storage + '/issuelistTmp.txt', 'ab+') as t:
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
			#return False
		else:
			metaDict = self._get_meta_data(soup)

			self.f.write('Acquiring text from %s\n' %page)

			if not os.path.exists(os.getcwd() + self.storage + '/jsonFiles'):
				os.makedirs(os.getcwd() + self.storage + '/jsonFiles')

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
				filenameJSON = os.getcwd() + self.storage + '/jsonFiles/'+ page.split('://')[1].replace('/','-').replace('.','-') +'.json'
				with open(filenameJSON, 'w+') as f:
					json.dump(contentDict, f)


	def _send_seeds(self, seedlist, config=None):
		'''Read data from file to kick into nutch'''
		'''
		Open file, while more urls to check if filelen 1-100, grab 100 and randomize, and send to nutch server.
		'''
		print '-------------------------- IN HERE -------------------', config

		if config:
			nt = Nutch(config)
		else:
			nt = Nutch('default')
			config = 'default'
		print '========================= end config ===================='
		# count = 0
		# seedStep = 5
		# currSeeds = [line.rstrip() for line in open(seedlist)]
		# currlen = len(currSeeds)

		# while count < currlen:
		# 	if currlen <= count:
		# 		seeds = currSeeds[(currlen/seedStep)*seedStep + (currlen%seedStep):]
		# 		random.shuffle(seeds)
		# 		sd = self.sc.create('scored', seeds)
		# 	else:
		# 		seeds = currSeeds[count:count+seedStep]
		# 		random.shuffle(seeds)
		sd = self.sc.create('scored', seedlist)
		print('^'*60)
		print 'CONFIG GOOD'
		jc = JobClient(self.sv, 'scoredTEST', config)
		cc = nt.Crawl(sd, self.sc, jc)
		while True:
		    job = cc.progress() # gets the current job if no progress, else iterates and makes progress
		    if job == None:
		        break
		# self.count += seedStep
		# return nt
		return cc


# class crawler(object):
# 	def __init__(self, nutchLoc):
# 		reload(sys)  
# 		sys.setdefaultencoding('utf8')
# 		self.log = os.getcwd() + '/scored.log'
# 		self.f = open(self.log,'ab+')
# 		if not os.path.exists(nutchLoc+'/runtime/local'):
# 			print 'No Nutch installation supplied. Exiting! \n'
# 			self.f.write('No Nutch installation supplied. Exiting! \n')
# 			sys.exit()
# 		else:
# 			os.environ['NUTCH_HOME'] = nutchLoc
# 			self.nutchPID = self._start_Nutch_server()
# 			self.sv = Server('http://localhost:8081')
# 			self.sc = SeedClient(self.sv)

	# def _start_Nutch_server(self):
	# 	ps = subprocess.Popen("ps -ef | grep NutchServer | grep -v grep", shell=True, stdout=subprocess.PIPE).communicate()[0]
	# 	if ps:
	# 		self.f.write('Nutch Server is already running \n')
	# 		print 'Nutch Server is already running \n'
	# 		return False
	# 	else:
	# 		self.f.write('Starting Nutch server \n')
	# 		print 'Starting Nutch server \n'
	# 		nPID = subprocess.Popen([os.getenv('NUTCH_HOME')+'/runtime/local/bin/nutch','startserver']).pid
	# 		return nPID

	# def send_seeds(self, seedlist, config=None):
	# 	'''Read data from file to kick into nutch'''
	# 	'''
	# 	Open file, while more urls to check if filelen 1-100, grab 100 and randomize, and send to nutch server.
	# 	'''
	# 	if config:
	# 		nt = Nutch(config)
	# 	else:
	# 		nt = Nutch('default')
	# 		config = 'default'

	# 	count = 0
	# 	seedStep = 100
	# 	currSeeds = [line.rstrip() for line in open(seedlist)]
	# 	currlen = len(currSeeds)

	# 	while count < currlen:
	# 		if currlen <= count:
	# 			seeds = currSeeds[(currlen/seedStep)*seedStep + (currlen%seedStep):]
	# 			random.shuffle(seeds)
	# 			sd = self.sc.create('scored', seeds)
	# 		else:
	# 			seeds = currSeeds[count:count+seedStep]
	# 			random.shuffle(seeds)
	# 			sd = self.sc.create('scored', seeds)
	# 			jc = JobClient(self.sv, 'scored', config)
	# 			cc = nt.Crawl(sd, self.sc, jc)
	# 			while True:
	# 			    job = cc.progress() # gets the current job if no progress, else iterates and makes progress
	# 			    if job == None:
	# 			        break
	# 			count += seedStep

if __name__ == '__main__':
	nutchLoc = '/Users/kwhitehall/Documents/nutch' #apache-nutch-1.11'
	# seeds = '/Users/kwhitehall/Documents/githubRepos/scored/www_egu_eu/seedlist.txt'
	URLlink =  'http://www.egu.eu/publications/open-access-journals'
	# nutchc = crawler(nutchLoc)
	# nutchc.send_seeds(seeds)
	journals = scored(nutchLoc, URLlink, -1) 
	# print 'Extracting Data from Journals...'
	# journals.get_journal_list() 
	# journals.get_issues_list()
	journals.get_articles_list()
	# journals.get_full_text()