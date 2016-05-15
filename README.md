# scored

<img src="./docs/img/scored_logo.png" align="right" width="300" />

## Purpose
To access journals from a publication site.
This code has been tested on MacOS 10.10.4, FF 31.4.0, Solr 5.4.0

## Requirements
* PhantomJS (brew install phantomJS)
* Nutch 1.X
* Python 2.7x

Python libs:
* selenium 2.48.0- for getting the stuff of the site
* tika 1.9.3 - for parsing meta data
* sunburnt-0.6 - for Solr 
* httplib2-0.92 - for use with Python binding for Solr
* nutch python
* beautifulSoup
* flask-api
* markdown

## To use
* run installation script to set up Nutch installation, etc. './scored_installation.sh'
* run the python script 'python scored.py' or 'python scored.py flask' for the FLask API implementation

## TODOS
* Address TODOs in the code
* Nutch selenium config
