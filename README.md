# scored

<img src="./docs/img/scored_logo.png" align="right" width="300" />

README for using getAGUAbs.py 

## Purpose
To access each journal on the AGU journal site and extract selected fields for each article in each issue. 
The fields to be selected are: page metadaa, Abstract, Acknowledgements and Data/Methodology
This code has been tested on MacOS 10.10.4, FF 31.4.0, Solr 5.4.0

## Requirements
* PhantomJS (brew install phantomJS)
* Solr 5.x 
* Python 2.7x

Python libs:
* selenium 2.48.0- for getting the stuff of the site
* tika 1.9.3 - for parsing meta data
* sunburnt-0.6 - for Solr 
* httplib2-0.92 - for use with Python binding for Solr

## To use
* Optional: install  Apache Solr. Set up a Solr core called 'scored', and ensure Solr is accessible at http://localhost:8983/solr/scored
The schema to use is available in this repo as scored.xml. 
* run the python script 'python getCorpus.py' or 'python getCorpus.py -s 'solrDBinstallation'' for Solr integration
* wait for a bit
* check the log files - agu.log for the script, ghostdriver.log for the PhantomJS driver
* check out the JSON files being generated in /jsonFiles
* check out the Sorl DB (if Solr integration was requested on the CL)


## TODOS
* Address TODOs in the code
* Consider extending tika by adding the extraction done with selenium on the 'full html sites' to parser.py in tika instead 
* ~~Change over to remoteDriver~~ (DONE using PhanthomJS)
