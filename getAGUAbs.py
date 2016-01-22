# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from pyvirtualdisplay import Display
from tika import parser
import unittest, time, re, os, sys, random, subprocess, shlex, signal
import sunburnt, json, argparse, httplib2, getopt


'''
Purpose:: To extract just the page meta data Abstract, keywords, Acknowledgements, & section after Intro (Methodology/ Data) if available
            from AGU site. 
'''
class AguChallenge(object): 
    def __init__(self):
        display = Display(visible=0, size=(800, 600))
        display.start()
        self.driver = webdriver.Firefox() #Remote(command_executor='http://127.0.0.1:4444/wd/hub', desired_capabilities=DesiredCapabilities.FIREFOX) #Firefox()
        self.driver.implicitly_wait(3)
        self.base_url = "http://agupubs.onlinelibrary.wiley.com/agu/" 
        self.verificationErrors = []
        self.accept_next_alert = True
        self.log = os.getcwd()+'/agu.log'
        self.f = open(self.log,'ab+')
        h = httplib2.Http(cache="/var/tmp/solr_cache")
        s = os.getcwd()+'/scored.xml'
        self.solr = sunburnt.SolrInterface(url='http://localhost:8983/solr/scored', http_connection=h, schemadoc=s)

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True
    
    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True
    
    def tearDown(self):
        self.driver.quit()
        display.stop()
        self.assertEqual([], self.verificationErrors)

    def info_from_agu(self):
        '''
             Purpose:: to get the journal link for each journal on AGU homepage
        '''
        driver = self.driver
        driver.get(self.base_url)
        driver.implicitly_wait(5)
        time.sleep(3)

        allJournals = driver.find_elements_by_xpath("//div[@class='content-area']/div/div/div/ul/li")
        
        for journal in allJournals:
            currJournalURL = journal.find_element_by_tag_name('a').get_attribute('href') 
            print journal.find_element_by_tag_name('a').text.encode('utf-8'), '  ', currJournalURL
            self.f.write('Working on %s\n' %journal.find_element_by_tag_name('a').text.encode('utf-8'))
            self.info_from_agu_journal(currJournalURL)

        allJournals.close()
        self.f.close()


    def info_from_agu_journal(self, journalPageUrl):
        '''
            Purpose:: driver function for retrieving information from a given AGU journal
        '''
        next = True
        count_debug = 1
        allIssuesURLs = []
        journal = webdriver.Firefox() #Remote(command_executor='http://127.0.0.1:4444/wd/hub', desired_capabilities=DesiredCapabilities.FIREFOX) #Firefox()
        journal.get(journalPageUrl)
        time.sleep(3)

        journal.find_element_by_link_text("All Issues").click()
        journal.implicitly_wait(3)
        time.sleep(3)
        
        allIssues = journal.find_elements_by_xpath("//ol[contains(@class,'js-issues-volume-list')]/li")
        for issue in allIssues:
            try:
                currVolumeURL = issue.find_element_by_tag_name('a').get_attribute('href')
                allIssuesURLs.append(currVolumeURL)
            except:
                continue

        
        for currVolumeURL in allIssuesURLs:
            try:
                currVolume = webdriver.Firefox() #Remote(command_executor='http://127.0.0.1:4444/wd/hub', desired_capabilities=DesiredCapabilities.FIREFOX) #Firefox()  
                currVolume.get(currVolumeURL)
                currVolume.implicitly_wait(3)
                time.sleep(3)
                # time.sleep(random.randint(4,20)) 
                #scrape on the page
                self.get_info_from_agu_journal(currVolume)
                currVolume.quit() #close()
                display.stop()
            except:
                self.get_info_from_agu_journal(journal)
                continue
            
        journal.close()
        

    def get_info_from_agu_journal(self, currVolumeDriver):
        '''
            Purpose:: Actually get the data off the page
        '''
        print 'get_info_from_agu_journal'
        try:        
            volArticles = currVolumeDriver.find_elements_by_xpath("//ol[contains(@class,'js-issues-list')]/li")
            
            for thisArticle in volArticles:
                currIssue = webdriver.Firefox() #Remote(command_executor='http://127.0.0.1:4444/wd/hub', desired_capabilities=DesiredCapabilities.FIREFOX) #Firefox() 
                currIssue.get(thisArticle.find_element_by_tag_name('a').get_attribute('href'))
                currIssue.implicitly_wait(3)
                allArticles = currIssue.find_elements_by_xpath("//div[contains(@id,'issue-toc__ajax')]/section/article/ul[contains(@class,'search__list-style2')]/li") #/article")
                
                for currArticle in allArticles:
                    try:
                        if '/full' in currArticle.find_element_by_tag_name('a').get_attribute('href') and\
                                not '#references' in currArticle.find_element_by_tag_name('a').get_attribute('href'):
                            self.f.write('parse full: %s\n'%(currArticle.find_element_by_tag_name('a').get_attribute('href')))
                            self.extract_from_full(currArticle.find_element_by_tag_name('a').get_attribute('href'))
                        
                    except:
                        continue
                
                currIssue.close()
        except:
            print 'no journals on this'
            
        currVolumeDriver.close()
        

    def extract_from_full(self, url):
        '''
        Purpose: Extract the full info when html is available
        '''
        title = ''
        abstract = ''
        methodology = ''
        acknowledgments = ''

        si = self.solr

        thisArticle = webdriver.Firefox() #Remote(command_executor='http://127.0.0.1:4444/wd/hub', desired_capabilities=DesiredCapabilities.FIREFOX) #Firefox()
        thisArticle.get(url)
        time.sleep(3)

        pageMetaData = parser.parse1('meta',url)[1]
        title = thisArticle.title

        try:
            abstract = (thisArticle.find_element_by_id("abstract").find_element_by_tag_name('p')).text.encode('utf-8')
            sections = thisArticle.find_elements_by_xpath("//article[contains(@id,'main-content')]/section[contains(@id,'eft')]")
        
            for section in sections:
                try:
                    if section.find_element_by_tag_name('h2').text in 'Acknowledgments':
                        for i in section.find_elements_by_tag_name('p'): 
                            acknowledgments += i.text.encode('utf-8')
                except:
                    try:
                        if True in [i in ['data', 'methodology', 'method'] for i in (section.find_element_by_tag_name('h2').text).lower().split(' ')]:
                            # methodology = section.find_element_by_tag_name('p').text.encode('utf-8')
                            for i in section.find_elements_by_tag_name('p'):
                                methodology += i.text.encode('utf-8')
                    except:
                        continue
        except:
            # this article is not a 'research' document, maybe like http://onlinelibrary.wiley.com/doi/10.1002/2015EF000307/full
            print 'skipping %s' %url
            self.f.write('skipping %s\n' %url)

        #TODO: place extractors here to get spatial & temporal data from extracted text to index
        thisArticle.close()

        thisArticleJSON = {'id':url, 'title': title, 'abstract':abstract, 'methodology':methodology, 'acknowledgment':acknowledgments}
        
        #add pageMetadata 
        # thisArticleJSON.update(json.loads(pageMetaData))
        partMeta = {}
        i = json.loads(pageMetaData.encode('utf-8'))
        partMeta = {"citation_author":i["citation_author"], "article_references":i["article_references"].encode('utf-8'),"citation_author_institution":i["citation_author_institution"], \
            "citation_doi":i["citation_doi"].encode('utf-8'), "citation_journal_title":i["citation_journal_title"].encode('utf-8'),\
            "citation_keywords":i["citation_keywords"],"citation_publisher":i["citation_publisher"].encode('utf-8'), "citation_online_date":i["citation_online_date"].encode('utf-8')}
        thisArticleJSON.update(partMeta)

        #index data into solr
        si.add(thisArticleJSON)
        self.f.write('added entry to solr DB\n')
    

    def extract_from_abs(self,url):
        '''
        Purpose:: Extract the info when only abs is available
        '''
        #TODO: mirror extract_from_full

    def extract_from_pdf(self):
        '''
        Purpose:: Extract the info when pdf is available
        '''
        #TODO: mirror extract_from_full

        
def main(argv):
    reload(sys)  
    sys.setdefaultencoding('utf8')
    ps = subprocess.Popen("ps -ef | grep selenium-server-standalone | grep -v grep", shell=True, stdout=subprocess.PIPE).communicate()[0]
    startSeleniumCmd = 'java -jar selenium-server-standalone-2.49.0.jar'
    if ps:
	print 'Selenium server is already running ... PID is %s' %(ps.split(' ')[2])
    else:
        subprocess.Popen(["java","-jar","selenium-server-standalone-2.49.0.jar"])
        seleniumPID = subprocess.Popen("ps -ef | grep selenium-server-standalone | grep -v grep", shell=True, stdout=subprocess.PIPE).communicate()[0]
        print 'Started Selenium server ... PID is %s: ' %(seleniumPID.split('(')[1].split(')')[0].split('=')[1])

    journalsList = AguChallenge()

    try:
        opts, args = getopt.getopt(argv,"hs:")
    except:
        print 'python getAGUAbs.py -s <solr_installation>'
        sys.exit(2)

    if len(opts) != 1:
        print 'python getAGUAbs.py -s <solr_installation>'
    else:
        for opt, arg in opts:
            if opt in '-h':
                print 'python getAGUAbs.py -s <solr_installation>'
                sys.exit()
            elif opt in '-s':
                startSolrCmd = arg+' start'
                print startSolrCmd

    journalsList.f.write('Selenium server is running ... PID is %s\n' %(ps.split(' ')[2]))
    ps = subprocess.Popen("ps -ef | grep solr | grep start | grep -v grep", shell=True, stdout=subprocess.PIPE).communicate()[0]
    if ps:
        print 'Solr database is already running ... PID is %s' %(ps.split(' ')[2])
        journalsList.f.write('Solr database is already running ... PID is %s\n' %(ps.split(' ')[2]))

        # # kill the process?
        # os.kill(int(ps.split(' ')[1]), signal.SIGKILL)
    else:
        solrPID = subprocess.Popen(shlex.split(startSolrCmd), stdout=subprocess.PIPE, shell=False).communicate()[0]
        print 'Started Solr database ... PID is %s: ' %(solrPID.split('(')[1].split(')')[0].split('=')[1])
        journalsList.f.write('Started Solr database ... PID is %s\n' %(solrPID.split('(')[1].split(')')[0].split('=')[1]))

    AguChallenge.info_from_agu(journalsList)

    # AguChallenge.info_from_agu_journal(datasetsList)
    
    # AguChallenge.extract_from_full(datasetsList,"http://onlinelibrary.wiley.com/doi/10.1002/2015EF000306/full")

    # endSolrCmd = 'kill -9 '+ solrPID.split('(')[1].split(')')[0].split('=')[1]
    # subprocess.call(endSolrCmd, shell=True)
    

if __name__ == "__main__":
    main(sys.argv[1:])
