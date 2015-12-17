# scored
README for using getAGUAbs.py - the AGU challenge put forth by Lewis

## Purpose
To access each journal on the AGU journal site and extract selected fields for each article in each issue. 
The fields to be selected are: page metadaa, Abstract, Acknowledgements and Data/Methodology
This code has been tested on MacOS 10.10.4, FF 31.4.0, Solr 5.4.0

## Requirements
* Firefox
* Solr 5.x 
* Python 2.7x

Python libs:
* selenium 2.48.0- for getting the stuff of the site
* tika 1.9.3 - for parsing meta data
* sunburnt-0.6 - for Solr 
* httplib2-0.92 - for use with Python binding for Solr

## To use
* Ensure Solr is installed. Set up a Solr core called 'scored', and ensure Solr is accessible at http://localhost:8983/solr/scored
The schema to use is available in this repo as scored.xml. Note that
* run the python script 'python getAGUAbs.py -s 'solrDBinstallation''
* wait for a bit
* check out the Sorl DB
* check the log file - agu.log


## TODOS
* Address TODOs in the code
* Consider extending tika by adding the extraction done with selenium on the 'full html sites' to parser.py in tika instead 
* Change over to remoteDriver
