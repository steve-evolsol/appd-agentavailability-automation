import requests
import json
import sys, getopt


expectedArgs = "appd-availability.py -c <controller> -a <application> -n <account> -u <user> -p <pass>"

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

def getApplicationTiers(controllerURL, applicationID, authUserID, appDPass):
    # api-endpoint 
    URL = controllerURL + "/controller/rest/applications/" + applicationID + "/tiers?output=JSON"
    print(URL)
    print(authUserID)
    print(appDPass)
    r = requests.get(URL, auth=(authUserID, appDPass))
    print("Response Code: {}, Response Body: {}, Reason: {}".format(r, r.content, r.reason))
    data = r.json()

    return data

def getTierNodesCreateHR(controllerURL, applicationID, authUserID, appDPass, tiers):
    # api-endpoint
    for tier in tiers:
        tierID = str(tier['id'])
        URL = controllerURL + "/controller/rest/applications/" + applicationID + "/tiers/" + tierID + "/nodes?output=JSON"
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

## Main(?) Code ##
def main(argv):
    controllerURL = ''
    appDPass = ''
    appDUser = ''
    applicationID = ''
    appDaccountname = ''

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
    
    print ("Controller is {}, App is {}, User is {}, Password is {}, Account is {}".format(controllerURL, applicationID, appDUser, appDPass, appDaccountname))
    
    tiers = getApplicationTiers(controllerURL, applicationID, authUserID, appDPass)
    getTierNodesCreateHR(controllerURL, applicationID, authUserID, appDPass, tiers)
if __name__ == "__main__":
   main(sys.argv[1:])
