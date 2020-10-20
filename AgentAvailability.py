import requests
import json
import sys, getopt
import re

# shows up if the wrong arugments or not enough arguments were added
expectedArgs = "appd-availability.py -c <controller> -a <application> -n <account> -u <user> -p <pass>"

# this function edits the jason payload used to create a payload and adds in the dynamics variables for grabbing the node name 
def returnJSONPayload(machineName, tierName, nodeName):
    return {
    "name": "Availability | {} | {}".format(tierName, machineName),
    "enabled": True,
    "useDataFromLastNMinutes": 5,
    "waitTimeAfterViolation": 30,
    "scheduleName": "Always",
    "affects": {
        "affectedEntityType": "TIER_NODE_HARDWARE",
        "affectedEntities": {
            "tierOrNode": "NODE_AFFECTED_ENTITIES",
            "typeofNode": "ALL_NODES",
            "affectedNodes": {
                "affectedNodeScope": "SPECIFIC_NODES",
                "nodes": [
                    "{}".format(nodeName)
                ]
            }
        }
    },
    "evalCriterias": {
        "criticalCriteria": {
            "conditionAggregationType": "ALL",
            "conditionExpression": None,
            "conditions": [
                {
                    "name": "Condition 1",
                    "shortName": "A",
                    "evaluateToTrueOnNoData": True,
                    "evalDetail": {
                        "evalDetailType": "SINGLE_METRIC",
                        "metricAggregateFunction": "SUM",
                        "metricPath": "Agent|App|Availability",
                        "metricEvalDetail": {
                            "metricEvalDetailType": "SPECIFIC_TYPE",
                            "compareCondition": "LESS_THAN_SPECIFIC_VALUE",
                            "compareValue": 1
                        }
                    },
                    "triggerEnabled": False,
                    "minimumTriggers": 0
                }
            ],
            "evalMatchingCriteria": None
        },
        "warningCriteria": None
    }
}

# this function uses the user input to gather all of the tier information for the application
def getApplicationTiers(controllerURL, applicationID, authUserID, appDPass):
    # api-endpoint 
    URL = controllerURL + "/controller/rest/applications/{}/tiers?output=JSON".format(applicationID)
    r = requests.get(URL, auth=(authUserID, appDPass))
    data = r.json()

    return data

# This function uses the identified tiers fron the getApplicationTiers function to get all of the nodes in a tier and create health rule
def getTierNodesCreateHR(controllerURL, applicationID, authUserID, appDPass, tiers):

    for tier in tiers:
        tierID = str(tier['id'])
        URL = controllerURL + "/controller/rest/applications/{}/tiers/{}/nodes?output=JSON".format(applicationID, tierID)
        r = requests.get(URL, auth=(authUserID, appDPass))
        nodes = r.json()

        for node in nodes:
            machineName = node['machineName']
            tierName = node['tierName']
            nodeName = node['name']
            payload = returnJSONPayload(machineName, tierName, nodeName)
            HRurl="{}/controller/alerting/rest/v1/applications/{}/health-rules/".format(controllerURL, applicationID)
            r = requests.post(HRurl, json = payload, auth=(authUserID, appDPass)) 
            print(r.content)

## Main Code ##
def main(argv):
    controllerURL = ''
    appDPass = ''
    appDUser = ''
    applicationID = ''
    appDaccountname = ''

    # this regex captures everything but the first and last character
    regex = "(?<!^).(?!$)"

    try:
        opts, args = getopt.getopt(argv,"hc:p:u:a:n:",["controller=","pass=","user=","application=","account="])
    except getopt.GetoptError:
        print ('Error retrieving options, expected: test.py -c <controller> -a <application> -n <account> -u <user> -p <pass>')
        sys.exit(2)

    ## enforce all opts to exist
    hasController = False
    hasApp = False
    hasUser = False
    hasPass = False
    hasAccount = False

    for opt, arg in opts:
        if opt == '-h':
            print ("Usage is: {}".format(expectedArgs))
            sys.exit()
        elif opt in ("-c", "-controller"):
            controllerURL = arg
            hasController = True
        elif opt in ("-a", "-application"):
            applicationID = arg
            hasApp = True
        elif opt in ("-u", "-user"):
            appDUser = arg
            hasUser = True
        elif opt in ("-p", "-pass"):
            appDPass = arg
            hasPass = True
        elif opt in ("-n", "-account"):
            appDaccountname = arg
            hasAccount = True

    if not (hasController & hasApp & hasUser & hasPass & hasAccount):
        print("Missing required param. Received {}. Expected: {}".format(opts, expectedArgs))
        sys.exit(2)
    
    authUserID = appDUser + "@" + appDaccountname
    tiers = None
   
    # These two commands create a "hidden" password on the console
    hiddenPassword = ""
    hiddenPassword = re.sub(regex, '*', appDPass)

    print ("Controller is {}, App is {}, User is {}, Password is {}, Account is {}".format(controllerURL, applicationID, appDUser, hiddenPassword, appDaccountname))
    
    # gets all the tier information and node IDs
    tiers = getApplicationTiers(controllerURL, applicationID, authUserID, appDPass)

    # uses nodeID to get information needed for health rule
    getTierNodesCreateHR(controllerURL, applicationID, authUserID, appDPass, tiers)

if __name__ == "__main__":
   main(sys.argv[1:])
