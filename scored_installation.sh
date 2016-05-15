#!/bin/bash
# Installation script for SCORED

# get the needed folder
# SCORED_DIR=$1
export SCORED_DIR=$1

#test for the existence of $SCORED_DIR
if [ ! -r "$SCORED_DIR" ]; then {
	mkdir -p $SCORED_DIR
	echo "*** created Scored directory ***"
}; fi


#download Nutch and Solr to that location
cd $SCORED_DIR
if [ ! -r "$NUTCH_HOME" ]; then {
	echo "*** Installing Nutch ***"
	wget https://github.com/apache/nutch/archive/master.zip
	unzip master.zip
	rm master.zip
	cd nutch-master
	ant 
	export NUTCH_HOME="$SCORED_DIR/nutch-master"
}; fi

cp ../nutch-site.xml "$NUTCH_HOME/runtime/local/config"
cp ../nutch-site.xml_sel "$NUTCH_HOME/runtime/local/config"

# echo "*** Installing Solr"


exit 0