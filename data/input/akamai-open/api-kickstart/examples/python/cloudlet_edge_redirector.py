#! /usr/bin/env python
# Very basic script template.  Use this to build new
# examples for use in the api-kickstart repository
#
""" Copyright 2015 Akamai Technologies, Inc. All Rights Reserved.
 
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.

 You may obtain a copy of the License at 

    http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import requests, logging, json
from http_calls import EdgeGridHttpCaller
from random import randint
from akamai.edgegrid import EdgeGridAuth
from config import EdgeGridConfig
from urlparse import urljoin
import urllib
session = requests.Session()
debug = False
verbose = False
section_name = "cloudlet"

config = EdgeGridConfig({"verbose":debug},section_name)

if hasattr(config, "debug") and config.debug:
  debug = True

if hasattr(config, "verbose") and config.verbose:
  verbose = True

# Set the config options
session.auth = EdgeGridAuth(
            client_token=config.client_token,
            client_secret=config.client_secret,
            access_token=config.access_token
)

# Set the baseurl based on config.host
baseurl = '%s://%s/' % ('https', config.host)
httpCaller = EdgeGridHttpCaller(session, debug, verbose, baseurl)

if __name__ == "__main__":
	# Get the list of cloudlets to pick the one we want to use

	endpoint_result = httpCaller.getResult("/cloudlets/api/v2/cloudlet-info")
	
	# Result for edge redirector:
	# {
	#    "location": "/cloudlets/api/v2/cloudlet-info/2", 
	#    "cloudletId": 2, 
	#    "cloudletCode": "SA", 
	#    "apiVersion": "2.0", 
	#    "cloudletName": "SAASACCESS"
	#}, 

	# Get the group ID for the cloudlet we're looking to create
	endpoint_result = httpCaller.getResult("/cloudlets/api/v2/group-info")

	# Result for group info:
 	#	 "groupName": "API Bootcamp", 
   	#	 "location": "/cloudlets/api/v2/group-info/77649", 
    	#	 "parentId": 64867, 
    	#	 "capabilities": [
      	#	{
       #	"cloudletId": 0, 
        #	"cloudletCode": "ER", 
        #	"capabilities": [
        #	  "View", 
        #	  "Edit", 
        #	  "Activate", 
        #	  "Internal", 
        #	  "AdvancedEdit"
        #	]
      	#	}, 

	sample_post_body = {
		  "cloudletId": 0,
		  "groupId": 77649,
		  "name": "APIBootcampERv6",
		  "description": "Testing the creation of a policy"
	}
	sample_post_result = httpCaller.postResult('/cloudlets/api/v2/policies', json.dumps(sample_post_body))
	policyId = sample_post_result['policyId']
#{
  #"cloudletCode": "SA", 
  #"cloudletId": 2, 
  #"name": "APIBootcampEdgeRedirect", 
  #"propertyName": null, 
  #"deleted": false, 
  #"lastModifiedDate": 1458765299155, 
  #"description": "Testing the creation of a policy", 
  #"apiVersion": "2.0", 
  #"lastModifiedBy": "advocate2", 
  #"serviceVersion": null, 
  #"createDate": 1458765299155, 
  #"location": "/cloudlets/api/v2/policies/11434", 
  #"createdBy": "advocate2", 
  #"activations": [
    #{
      #"serviceVersion": null, 
      #"policyInfo": {
        #"status": "inactive", 
        #"name": "APIBootcampEdgeRedirect", 
        #"statusDetail": null, 
        #"detailCode": 0, 
        #"version": 0, 
        #"policyId": 11434, 
        #"activationDate": 0, 
        #"activatedBy": null

      #}, 
      #"network": "prod", 
      #"apiVersion": "2.0", 
      #"propertyInfo": null
    #}, 
    #{
      #"serviceVersion": null, 
      #"policyInfo": {
        #"status": "inactive", 
        #"name": "APIBootcampEdgeRedirect", 
        #"statusDetail": null, 
        #"detailCode": 0, 
        #"version": 0, 
        #"policyId": 11434, 
        #"activationDate": 0, 
        #"activatedBy": null
      	#}, 
      	#"network": "staging", 
      #	"apiVersion": "2.0", 
      	#"propertyInfo": null
    	#}
  	#], 
# "groupId": 77649, 
# "policyId": 11434  <<<<<<<<<<<
# }

	# Activate by associating with a specific property
	sample_post_url = "/cloudlets/api/v2/policies/%s/versions/1/activations" % policyId
	sample_post_body = {
  		"network": "staging",
  		"additionalPropertyNames": [
  			  "akamaiapibootcamp.com"
  		]
	}
	sample_post_result = httpCaller.postResult(sample_post_url, json.dumps(sample_post_body))
	
	# Next, add the behavior for cloudlets

	# PUT the update to activate the cloudlet
	
