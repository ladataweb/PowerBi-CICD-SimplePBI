r'''.
           @@@@@@@@@@
       @@@@..........@@@@
    @@@         .        @@@
  @@.           .         . @@
 @  .     _     .         .   @
@........| |...................@    *********************************************
@      . | |   _____  .        @
@      . | |  |  __ \ .        @    La Data Web Script
@      . | |__| |  | |.   ***  @
@........|____| |  | |...*   *.@    Copyright © 2025 La Data Web - All rights reserved.
@   .       . | |__| |. *     *@    This software is proprietary and confidential
@   .       . |_____/ . *     *@    Unauthorized copying of this file, via any medium, is strictly prohibited
@   .       .         . *     *@    Written by Ignacio Barrau <igna_barrau@hotmail.com>
@   .       .         . *******@    
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@    *********************************************

This script is used to deploy Power BI reports or semantic models to a workspace. It is called from the GitHub Action. It uses the simplepbi library to deploy.
 
'''

import sys 
import json
from simplepbi import token
from simplepbi.fabric import core

# Set variables
Throw_exception = ""
Workspace = sys.argv[1]

# Get list of file path folders with changes
list_files = " ".join(sys.argv[5:])
#print("The arguments are: " , str(sys.argv))
print("The modified files are: " , list_files)

if ".Report" not in list_files and ".SemanticModel" not in list_files and ".Dataset" not in list_files:
    sys.exit()


try:
    Workspace_Name = list_files.split(",")[0].split("/")[:-1][1]
except IndexError as e:
    print("Caught IndexError list out of index, proceding alternative method.")
    Workspace_Name = list_files.split(",")[0].split("/")[1]

# Show extraction
print("Folder_Name/Workspace: " + Workspace_Name, "\nFolders: " + str(list_files))

# Get list of files to import
#list_files = [item for item in Files.split(",") if item[-4:]=="pbix" and item.split("/")[0] ==Folder_Name]
#print("list_files: " + str(list_files))

# Log into Power BI
TENANT_ID = sys.argv[2]
power_bi_client_id = sys.argv[3]
power_bi_secret = sys.argv[4]
print("Environment Variables loaded.")

# Get token for Fabric API
t = token.Token(TENANT_ID, power_bi_client_id, None, None, power_bi_secret, use_service_principal=True)

# Create item objects to deploy and workspace to find the id by name
it = core.Items(t.token)
wp = core.Workspaces(t.token)
lg = core.LongRunningOperations(t.token)

# Find workspace id by name
try:
    areas = wp.list_workspaces(roles="admin, member, contributor, viewer")
    workspace_id = [i['id'] for i in areas['value'] if i['displayName']==Workspace_Name and i['type']=="Workspace" ]
    if workspace_id == []:
        raise Exception("Workspace {} does not exist.".format(Workspace_Name))
except Exception as e:
    print("Error: ", e)
    sys.exit(1)

print("Token generated.\nWorkspace id found: " + str(workspace_id))

# Remove text after .SemanticModel or .Report to optimize deployment when modify multiple files of single item
sm_items_deploy = []
re_items_deploy = []
# Creating two lists to organize semantic models first at deploys and then reports
for files in list_files.split(","):
    try:
        if ".Report" in files: # Another alternative check specific folder .split(".")[-1] == "Report"            
            item_path = files.split(".Report")[0]+".Report"
            re_items_deploy.append(item_path)
        else:            
            if ".SemanticModel" in files:
                item_path = files.split(".SemanticModel")[0]+".SemanticModel"
            else:
                item_path = files.split(".Dataset")[0]+".Dataset"
            sm_items_deploy.append(item_path)        
    except Exception as e:
        print("Error_: ", e)
        raise Exception(e)
items_deploy = list(set(sm_items_deploy)) + list(set(re_items_deploy))
print("Order of items to deploy: " + str(items_deploy) )

# Deploy Report or semantic model change by checking files modification at Report or SemanticModel folder.
workspaces = {}
for pbi_item in list(items_deploy):
    wp_name = pbi_item.split("/")[1]
    if wp_name not in workspaces:
        try:
            areas = wp.list_workspaces()
            workspace_id = [i['id'] for i in areas['value'] if i['displayName']==wp_name and i['type']=="Workspace" ]
            if workspace_id == []:
                raise Exception("Workspace {} does not exist.".format(wp_name))
            workspaces[wp_name] = workspace_id[0]
        except Exception as e:
            print("Error: ", e)
            sys.exit(1)
    try:
        status="Running"
        if ".Report" in pbi_item: # Another alternative check specific folder .split(".")[-1] == "Report"
            print("Running report deployment to path: " + pbi_item + " to workspace id: " + workspaces[wp_name])
            res = it.simple_deploy_report(workspaces[wp_name], workspaces[wp_name], pbi_item)                    
        else:
            print("Running semantic model deployment to path: " + pbi_item + " to workspace id: " + workspaces[wp_name])                        
            res = it.simple_deploy_semantic_model(workspaces[wp_name], pbi_item)
        print("Running Operation ID check for: " + res.headers['x-ms-operation-id'])
        while status == "Running":
            try:
                ope = lg.get_operation_state(res.headers['x-ms-operation-id'])
                status = json.loads(ope)["status"]
            except Exception as e:
                pass
        print("Status: " + status)            

    except Exception as e:
        print("Error_: ", e)
        raise Exception(e)

    
