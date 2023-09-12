from fastapi import  FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests, json
from fastapi_mail import FastMail, MessageSchema
from .modelDefinition import Email
from .configuration import conf
import pandas as pd
from fastapi.responses import StreamingResponse


# Import dotenv and load environment variables
from dotenv import load_dotenv
import os
load_dotenv()


app = FastAPI()
baseUrl = os.environ.get("BASE_URL")


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def replaceSpecialCharacter(termsToReplaced):
    if '&amp;' in termsToReplaced:
        termsToReplaced = termsToReplaced.replace('&amp;','&')
    elif '&' in termsToReplaced:
        termsToReplaced = termsToReplaced.replace('&','&amp;')
    return termsToReplaced


def pagination(data, page):
     size = 10
     if(len(data)==0):
        pages = 0
        finalData=[]
        return finalData
     else:
        start = size * (int(page)-1)
        newData = []
        pages = (len(data)//size)
        if (len(data)%size!=0):
            pages+=1
        if (page > pages):
            return []
        end = start+10
        if (page == pages):
            if(len(data) != size):
                end = start + (len(data)%size)    
        for i in range(start,end):
            newData.append(data[i])
        finalData=[{'pages':pages,'data':newData}]
        return finalData


def build_charts(data,types):
    values = {type: {} for type in types}

    for item in data:
        for type in types:
            type_value = item.get(type)
            if type_value is not None:
                if type_value in values[type]:
                    values[type][type_value] += 1
                else:
                    values[type][type_value] = 1

    final_list = []

    for type, data in values.items():
        value_list = []

        for value, count in data.items():
            entry = {'name': value, 'value': count}
            value_list.append(entry)

        entry = {'name': type, 'values': value_list}
        final_list.append(entry)
    return final_list


@app.get(
    "/dataset/{id}", response_description="Return dataset by ID"
)
def getDatasetByID(id: str):
    url = baseUrl+"/api/datasets/"+id
    data = []

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the response has an error status code
        data = response.json()
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []
    return data

@app.get(
    "/datasets/results/{terms}/{page}/{keywords}", response_description="Return datasets by term and keyword"
)
def getDatasetResults(terms: str,keywords: str, page: int):
    url = baseUrl+"/api/datasets"
    data = []
    final_list = []
    try:
        if page<=0:
            return []
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the response has an error status code
        data = response.json()
        terms = terms.lower()
        if terms != 'all':
            for dataset in data:
                if ((terms in  str(dataset['title']).lower()) or (terms in str(dataset['field_author_producer']).lower()) or (terms in str(dataset['field_description']).lower()) or (terms in str(dataset['term_node_tid']).lower())):
                    final_list.append(dataset)
        else:
            final_list = data
        if keywords and keywords!='none':
            filtered_list = []
            keywords = keywords.lower()
            keywords = keywords.split('+') 
            for keyword in keywords:
                searchingField = keyword.split(":")[0]
                if searchingField == 'category':
                    searchingField= 'term_node_tid'
                    keyword = replaceSpecialCharacter(keyword)
                else:
                    searchingField = 'field_'+searchingField
                searchingTerms = keyword.split(":")[1]
                searchingTerms = searchingTerms.split(",")
                for term in searchingTerms:
                    for data in final_list:
                        if (term in str(data[searchingField]).lower()) and (data not in filtered_list):
                            filtered_list.append(data)
            final_list = filtered_list
        for data in final_list:
            if '&' in data['term_node_tid']:
                data['term_node_tid']=replaceSpecialCharacter(data['term_node_tid'])
        final_list = pagination(final_list,page)
        return final_list               
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []

@app.patch(
    "/datasets/updateViews/{id}:{views}", response_description="Update number of views for dataset"
)
def updateDatasetViews(id: str,views: int):
    url = baseUrl+"/jsonapi/node/datasets/"+id
    views += 1
    payload = json.dumps({
    "data": {
        "type": "node--datasets",
        "id": id,
        "attributes": {
        "field_views": views
        }
    }
    })
    headers = {
    'Content-Type': 'application/vnd.api+json',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflare, br',
    'Connection': 'keep-alive',
    'Authorization': 'Basic Z3JhbnVsYXJBZG1pbjpzOG1uQDQ3WDNxNio='
    }

    try:
        response = requests.request("PATCH", url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an exception if the response has an error status code
        data = response.json()
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []
    return data
    

@app.get(
    "/datasets/popular", response_description="Return popular datasets "
)
def getPopularDatasets():
    url = baseUrl+"/api/datasets/popular"
    data = []
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the response has an error status code
        data = response.json()
        for dataset in data:
            if '&' in dataset['term_node_tid']:
                dataset['term_node_tid']=replaceSpecialCharacter(dataset['term_node_tid'])
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []
    return data

@app.get(
    "/datasets/recent", response_description="Return recent datasets"
)
def getRecentDatasets():
    url = baseUrl+"/api/datasets/recent"
    data = []
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the response has an error status code
        data = response.json()
        for dataset in data:
            if '&' in dataset['term_node_tid']:
                dataset['term_node_tid']=replaceSpecialCharacter(dataset['term_node_tid'])
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []
    return data

@app.get(
    "/datasets/count", response_description="Return number of datasets"
)
def getCountDatasets():
    url = baseUrl+"/api/datasets/count"
    data = []
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the response has an error status code
        data = response.json()
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []
    return data

@app.get(
    "/datasets/similar/{keyword}", response_description="Return number of datasets"
)
def getSimilarDatasets(keyword: str):
    url = baseUrl+"/api/datasets/similar/"+keyword
    data = []
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the response has an error status code
        data = response.json()
        for dataset in data:
            if '&' in dataset['term_node_tid']:
                dataset['term_node_tid']=replaceSpecialCharacter(dataset['term_node_tid'])
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []
    return data

@app.get(
    "/categories", response_description="Return available categories and number of datasets for each one"
)
def getCategories():
    url = baseUrl+"/api/categoriesTerms"
    data = []
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the response has an error status code
        data = response.json()
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []
    return data

@app.post("/email")
async def contactEmail(email: Email):
    reference="""<br>"""
    if email.subject=='dataset':
        reference="""<br><p>Datasets' reference url:</p>"""+ email.url
    body = """<p>Received from:</p>"""+email.senderName+""" """+email.senderEmail+ reference+"""<br>"""+email.description
    message = MessageSchema(
        subject=email.subject,
        recipients=['repogranular@gmail.com'],
        body= body,
        subtype='html'
        )
    
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
    except requests.exceptions.RequestException as e:
        return JSONResponse(status_code=400, content={"message": "Failed to send the email"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": "Failed to send the email"})
    return JSONResponse(status_code=200, content={"message": "Email has been sent"})

@app.get(
    "/categories/sorted", response_description="Return available categories and number of datasets for each one"
)
def getCategories():
    url = baseUrl+"/api/categories/popularity"
    data = []
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the response has an error status code
        data = response.json()
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []
    return data

@app.get("/metadatatooltip/{name}", response_description="Return definition of a metadata field")

def getMetadataTooltips(name: str):
    url = baseUrl+"/api/metadatatooltip/"+name
    data = []
    try:
        items_by_name = {
            "field_author_producer": {"description": "The person, organization, or agency responsible for creating or compiling the dataset."},
            "field_data_class": {"description": "The category of the data based on its primary characteristics, such as qualitative or quantitative data, time-series data, or cross-sectional data."},
            "field_data_type": {"description": "The type of data contained in the dataset, such as numeric data, text data, or geospatial data (points, lines, polygons, raster)"},
            "field_description": {"description":"A detailed overview of the dataset, including information about its contents, purpose, and any significant features."},
            "field_descriptors": {"description":"No definition given"},
            "field_doi": {"description":"The Digital Object Identifier (DOI) assigned to the dataset, which provides a unique and persistent link to its location on the internet."},
            "field_doi_api": {"description":"The API endpoint related to the dataset's DOI, which can be used to programmatically access the dataset or its metadata."},
            "nid": {"description":"The node ID, a unique identifier assigned to the dataset within the database system."},
            "field_imageurl": {"description":"The URL of an image associated with the dataset."},
            "field_indicator_class": {"description":"The category to which the dataset belongs"},
            "field_licence": {"description":"The license under which the dataset is released, which stipulates how the data can be used, shared, or modified. This field can also list costs of purchasing a proprietary data."},
            "field_access": {"description":"Free and open access and availability of the derived datasets, as well as raw datasets (for the analysis) and the model or code."},
            "field_living_labs": {"description":"Spatial extent of the Living Lab"},
            "field_policy_indicators": {"description":"Information about policy indicators related to the dataset."},
            "field_rural_compass": {"description":"The rural functional area - as described by the GRANULAR Rural Compass -  that this dataset describes.  The 4 rural functional areas are: Residential, Recreational, Environmental and Productive."},
            "field_spatial_extent": {"description":"The geographical coverage of the dataset, indicating the area that the data represents."},
            "field_spatial_resolution": {"description":"The level of detail of the data in terms of geographical area, such as data at different NUTS levels, municipality, country level or the spatial resolution in degrees and/meters for raster data"},
            "field_scope_coverage": {"description":"Geographic coverage of each study from local to global."},
            "field_granularity": {"description":"No definition given"},
            "field_temporal_extent": {"description":"The time period covered by the dataset."},
            "field_temporal_resolution": {"description":"The frequency or regularity with which the data was collected or updated, such as daily, monthly, or annually."},
            "field_thematic_area": {"description":"The main topic or theme of the dataset, such as health, education, or environment."},
            "field_updates": {"description":"Information about upcoming updates or revisions to the dataset."},
            "field_frequency": {"description":"No definition given"},
            "field_uploaded_date": {"description":"The date when the dataset was uploaded or added to the repository."},
            "field_views": {"description":"The number of times the dataset has been viewed or accessed."},
            "Term_node_tid": {"description":"No definition given"},
            "uuid": {"udescriptionuid":"The Universal Unique Identifier (UUID) of the dataset, a unique string of characters used to identify the dataset within the system."},
            "field_licencing_costs": {"description":"Specifies the amount or fee required to obtain the license for using this dataset. If a cost is mentioned, it indicates that the dataset is not free to use and acquiring a license involves a certain financial commitment."},
            "field_rural_compass_component": {"description":"The component of the rural compass that this dataset describes."},
            "field_created_date": {"description":"The date when the dataset was created or compiled."},
            "field_relevance": {"description":"The degree of relevance of the study in terms of supporting the rural compass."},
        }
       
        data = items_by_name.get(name, "Item not found")["description"]
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []
    return data
@app.get("/qna", response_description="Return available QnA's")

def getQnA():
    url = baseUrl+"/api/faq"
    data = []
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []
    return data


@app.get(
    "/charts/{name}", response_description=""
)

def getCharts(name: str):
    url = baseUrl+"/api/datasets"
    data = []
    name = name.split(',')
    types = []
    for item in name:
        if item == "Geographic coverage of datasets":
            types.append("field_granularity")
        elif item == "Dataset update frequency":
            types.append("field_frequency")
        elif item == "Datasets per data class":
            types.append("field_data_class")
        elif item == "Datasets per data type":
            types.append("field_data_type")
        else:
            types.append("field_access")

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json() 
        chart_data = build_charts(data,types)
        for item in chart_data:
            if item["name"] == "field_granularity":
                item["name"] = "Geographic coverage of datasets"
                continue
            elif item["name"] == "field_frequency":
                item["name"] = "Dataset update frequency"
                continue
            elif item["name"] == "field_data_class":
                item["name"] = "Datasets per data class"
                continue
            elif item["name"] == "field_data_type":
                item["name"] = "Datasets per data type"
                continue
            else:
                item["name"] = "Datasets data access"
                continue
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []
    return chart_data

@app.get(
    "/csv/{name}", response_description=""
)
def getcsv(name : str):
    frame = []
    data = getCharts(name)
    for item in data[0]["values"]: 
        frame.append( [item["name"],item["value"]] )
    
    df = pd.DataFrame(
        frame, 
        columns=[name, ""]
    )
    return StreamingResponse(
        iter([df.to_csv(index=False)]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename="+name+".csv",
                "Access-Control-Allow-Origin":"*"}
    )
