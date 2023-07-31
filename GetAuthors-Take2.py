#Importing Libraries#
import json
import requests as req
import pandas as pd
from progressbar import ProgressBar
import time
import os

os.chdir('E:\Library Strategic Research - Intelligence\Scopus API - Testyard\RootFolder-Take2')
pbar = ProgressBar()
start = time.time()
####################################
#Initializing the Lists

con_file_location = 'E:\Library Strategic Research - Intelligence\Scopus API - Testyard\RootFolder-Take2\config.json'

Data_Source = []
Last_Updated = []
metric_Start_Year=[]
metric_End_Year=[]
Full_Name = []
Author_ID = []
H_value = []
indexType = []

FNs = []
Lns = []

All_Data = {}

###################################################
#Accessing the information from the Config file

con_file = open(con_file_location)
config = json.load(con_file)
con_file.close()

API_Key = config['apikey']
Base_API_Hindices = config['baseapi_Hindices']    #Scival
Base_API_AUID = config['baseapi_AUID']            #Scopus
AU_Name_file_csv_location = config['Author_Name_file_location']
Output_Result_csv_location = config['Output_Data_file_location']
Aff_ID = config['Virginia_Tech_AFID']

####################################
#Function to pass the parameters to the H_index API - Generate the Parameter String
def Getparameters_Hindex(Author_ID,API_Key):
    parameters_hindex = {'metricTypes':'HIndices','authors': Author_ID,'yearRange':'5yrs','includeSelfCitations':'true','byYear':'false','includedDocs':'AllPublicationTypes','journalImpactType':'CiteScore','showAsFieldWeighted':'false','indexType':'hIndex','apiKey': API_Key}
    return parameters_hindex

####################################
#Function to pass the parameters to the AUID API - Generate the Parameter String

def Getparameters_AUID(First_name,Last_name,AFID,API_Key):
    Genstring = "authlast(" + Last_name + ") and authfirst(" + First_name + ") and af-id(" + AFID + ")"
    parameters_AUID = {'query': Genstring,'apiKey': API_Key}
    return parameters_AUID

#######################################
#Execute the API for getting H-indices
def ExecuteAPI_Hindices(parameters):
    response = req.get(Base_API_Hindices,params=parameters)
    Response_code = response.status_code

    if Response_code == 200:
            
        APIresponse = response.json()

        if(APIresponse):
            if(APIresponse['dataSource']):
                
                APIresponse_dataSource = APIresponse['dataSource']  
                Data_Source.append(APIresponse_dataSource['sourceName'])
                Last_Updated.append(APIresponse_dataSource['lastUpdated'])
                metric_Start_Year.append(APIresponse_dataSource['metricStartYear'])
                metric_End_Year.append(APIresponse_dataSource['metricEndYear'])
            else:
                print("No Data source found")
               
            if(APIresponse['results']):      

                APIresponse_Results_Metrics = APIresponse['results'][0]['metrics'][0]
                    
                APIresponse_Results_Authors = APIresponse['results'][0]['author']  
               
                Author_ID.append(APIresponse_Results_Authors['id'])
                indexType.append(APIresponse_Results_Metrics['indexType'])
                H_value.append(APIresponse_Results_Metrics['value']) 
            else:
                print("No Results found")       

        else:
            print("API response unavailable")
    else:
        print("Connection Error\n")
        print(response.status_code)

#######################################################
# Execute API for getting Author AUID
def ExecuteAPI_AUID(parameters):
    response = req.get(Base_API_AUID,parameters)
    Response_code = response.status_code

    if Response_code == 200:
        APIresponse = response.json()
        if(APIresponse):

            Results = APIresponse['search-results']
            Search_Results = int(Results['opensearch:totalResults'])    #Gives total results

            if(Search_Results !=  0):
                    
                Temp_auid = Results['entry'][0]['dc:identifier']
                Auth_ID = Temp_auid.split(':')[1]
                return (Auth_ID)
            
            else:
                Auth_ID = '0000'
                return Auth_ID
        else:
            print("API response Unavailable")
    else:
        print("Connection Error\n")
        print(response.status_code)

###################################################
# Generate the Dictionary of Results
def Generate_Results(AuthNames):
        
    All_Data = {
    'Data Source': Data_Source,
    'Last Updated': Last_Updated,
    'Start Year': metric_Start_Year,
    'End Year': metric_End_Year,
    'Author Full Name': AuthNames,
    'Author ID': Author_ID,
    'Index Type': indexType,
    'H-index value': H_value,
    }

    return All_Data

################################################
## Populate Invalid Entry

def Send_NA(Invalid):
 
    Data_Source.append(Invalid)
    Last_Updated.append(Invalid)
    metric_Start_Year.append(Invalid)
    metric_End_Year.append(Invalid)
    Author_ID.append(Invalid)
    indexType.append(Invalid)
    H_value.append(Invalid) 

#################################################
# Generate Output CSV file
def Generate_csv(data):
    try:
        df = pd.DataFrame(data)
        df.to_csv(Output_Result_csv_location, sep=',', index=False, encoding='utf-8')
        print("File Generated")
    except ValueError:
        print(data)
        exit()

################################################
#Get Author Names from the csv file
def Fetch_Author_Names(AU_Name_File):
    File_Data = pd.read_csv(AU_Name_File)
    authdata = pd.DataFrame(File_Data)
    Full_Names = authdata['Author-Full-Name'].values.tolist()
    count = 0
    
    for names in Full_Names:
        try:
            count  = count  + 1
            Full_Name.append(names)
            if ", " in names:
                Last_name = names.split(", ")[0]
                Lns.append(Last_name)
                First_name = names.split(", ")[1].split()[0]
                FNs.append(First_name)
            elif "," in names:
                Last_name = names.split(",")[0]
                Lns.append(Last_name)
                First_name = names.split(",")[1].split()[0]
                FNs.append(First_name)
            else:
                print("Incorrect Name in Input file - Pattern Uneven")
        except IndexError:
            print(names)
            print("Error Detected")
            exit()
    return(count,Full_Name)

#################################################
def PrepareOutputFile(AF_ID):

    for i,j in pbar(zip(FNs,Lns)):
        Params1 = Getparameters_AUID(i,j,AF_ID,API_Key)
        Author_ID = ExecuteAPI_AUID(Params1)
        time.sleep(0.5)
        if(Author_ID == '0000'):
            Send_NA('N/A')
        else:
            Params2 = Getparameters_Hindex(Author_ID,API_Key)
            ExecuteAPI_Hindices(Params2)

########## Main Program Execution####################

Authors,Author_Names = Fetch_Author_Names(AU_Name_file_csv_location)
PrepareOutputFile(Aff_ID)
Result_Data = Generate_Results(Author_Names)
Generate_csv(Result_Data)

end = time.time()

print("Execution Complete")
print("Number of authors: ", Authors)
print("Time elapsed: ",end - start)

