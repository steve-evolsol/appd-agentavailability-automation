import requests
import json
import sys, getopt
import re

# shows up if the wrong arugments or not enough arguments were added
expectedArgs = "appd-availability.py -c <controller> -a <application> -n <account> -u <user> -p <pass>"

# generate the base JSON structure for a dashboard
def generateDashboardBase(appName):
    return {
        "schemaVersion": None,
        "dashboardFormatVersion": "4.0",
        "name": "Agent Availability | {}".format(appName),
        "description": None,
        "properties": None,
        "templateEntityType": "APPLICATION_COMPONENT_NODE",
        "associatedEntityTemplates": None,
        "minutesBeforeAnchorTime": 5,
        "startDate": None,
        "endDate": None,
        "refreshInterval": 120000,
        "backgroundColor": 0,
        "color": 0,
        "height": 768,
        "width": 1024,
        "canvasType": "CANVAS_TYPE_GRID",
        "layoutType": "",
        "widgetTemplates": [],
        "warRoom": False,
        "template": False
    }

# generate the JSON for a dashboard tier
def generateDashboardTier(appName, tierName, locX):
    return {
        "widgetType": "HealthListWidget",
        "title": "{}".format(tierName),
        "height": 2,
        "width": 2,
        "minHeight": 0,
        "minWidth": 0,
        "x": locX,
        "y": 0,
        "label": None,
        "description": None,
        "drillDownUrl": None,
        "useMetricBrowserAsDrillDown": False,
        "drillDownActionType": None,
        "backgroundColor": 0,
        "backgroundColors": None,
        "backgroundColorsStr": "16777215,16777215",
        "color": 16777215,
        "fontSize": 12,
        "useAutomaticFontSize": False,
        "borderEnabled": False,
        "borderThickness": 0,
        "borderColor": 14408667,
        "backgroundAlpha": 1,
        "showValues": False,
        "formatNumber": None,
        "numDecimals": 0,
        "removeZeros": None,
        "compactMode": False,
        "showTimeRange": False,
        "renderIn3D": False,
        "showLegend": None,
        "legendPosition": None,
        "legendColumnCount": None,
        "startTime": None,
        "endTime": None,
        "minutesBeforeAnchorTime": 15,
        "isGlobal": True,
        "propertiesMap": None,
        "dataSeriesTemplates": None,
        "applicationReference": {
            "applicationName": "{}".format(appName),
            "entityType": "APPLICATION",
            "entityName": "{}".format(appName),
            "scopingEntityType": None,
            "scopingEntityName": None,
            "subtype": None
        },
        "entityReferences": [],
        "entityType": "POLICY",
        "entitySelectionType": "SPECIFIED",
        "iconSize": 18,
        "iconPosition": "LEFT",
        "showSearchBox": False,
        "showList": False,
        "showListHeader": False,
        "showBarPie": False,
        "showPie": True,
        "innerRadius": 0,
        "aggregationType": "MOST_SEVERE"
}

# generate the JSON for a dashboard node
def generateDashboardNode(appName, healthRuleName):
    return {
        "applicationName": "{}".format(appName),
        "entityType": "POLICY",
        "entityName": "{}".format(healthRuleName),
        "scopingEntityType": None,
        "scopingEntityName": None,
        "subtype": None
    }

# this function edits the JSON payload used to create a payload and adds in the dynamics variables for grabbing the node name 
def generateJSONPayload(machineName, tierName, nodeName, healthRuleName):
    return {
    "name": "{}".format(healthRuleName),
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

def getApplicationName(controllerURL, applicationID, authUserID, appDPass):
    # api-endpoint 
    appName = ''
    URL = "{}/controller/rest/applications?output=JSON".format(controllerURL)
    r = requests.get(URL, auth=(authUserID, appDPass))
    data = r.json()

    for app in data:
        if int(applicationID) == int(app['id']):
            appName = app['name']

    return appName

# this function uses the user input to gather all of the tier information for the application
def getApplicationTiers(controllerURL, applicationID, authUserID, appDPass):
    # api-endpoint 
    URL = "{}/controller/rest/applications/{}/tiers?output=JSON".format(controllerURL, applicationID)
    r = requests.get(URL, auth=(authUserID, appDPass))
    data = r.json()

    return data

# This function uses the identified tiers fron the getApplicationTiers function to get all of the nodes in a tier and create health rule
def getTierNodesCreateHR(controllerURL, applicationID, authUserID, appDPass, tiers, appName):
    dashboardJSON = generateDashboardBase(appName)
    
    # position of the tile on the dashboard
    xLoc = 0

    for tier in tiers:
        tierID = str(tier['id'])
        tierJSON = generateDashboardTier(appName, tier['name'], xLoc)
        
        # Move the location of the widget to the right, wrapping if need be. only 6 can fit side-by-side
        xLoc = (xLoc + 2) % 12

        URL = "{}/controller/rest/applications/{}/tiers/{}/nodes?output=JSON".format(controllerURL, applicationID, tierID)
        r = requests.get(URL, auth=(authUserID, appDPass))
        nodes = r.json()

        for node in nodes:
            machineName = node['machineName']
            tierName = node['tierName']
            nodeName = node['name']
            healthRuleName = "Availability | {} | {}".format(tierName, machineName)

            nodeJSON = generateDashboardNode(appName, healthRuleName)
            tierJSON['entityReferences'].append(nodeJSON)

            payload = generateJSONPayload(machineName, tierName, nodeName, healthRuleName)
            HRurl="{}/controller/alerting/rest/v1/applications/{}/health-rules/".format(controllerURL, applicationID)
            r = requests.post(HRurl, json = payload, auth=(authUserID, appDPass)) 
            print(r.content)
        
        # now that we're done with this tier, add the JSON and move on to the next one
        dashboardJSON['widgetTemplates'].append(tierJSON)
    
    return dashboardJSON

def pushDashboard(controllerURL, authUserID, appDPass, dashboardJSON):
    URL = "{}/controller/CustomDashboardImportExportServlet".format(controllerURL)
    filesJSON = {'File': dashboardJSON}
    r = requests.post(URL, files=filesJSON, auth=(authUserID, appDPass)) 
    print("Received status code: {} when pushing dashboard. Content is: {}".format(r.status_code, r.content))

## Main Code ##
def main(argv):
    controllerURL = ''
    appDPass = ''
    appDUser = ''
    applicationID = 0
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
    
    #  This grabs the application name that was specified 
    appName = getApplicationName(controllerURL, applicationID, authUserID, appDPass)

    # gets all the tier information and node IDs
    tiers = getApplicationTiers(controllerURL, applicationID, authUserID, appDPass)

    # uses nodeID to get information needed for health rule
    dashboardJSON = getTierNodesCreateHR(controllerURL, applicationID, authUserID, appDPass, tiers, appName)
    dashboardJSON = json.dumps(dashboardJSON)

    ## call the api to post the dashboardJSON
    pushDashboard(controllerURL, authUserID, appDPass, dashboardJSON)

if __name__ == "__main__":
   main(sys.argv[1:])
