#!/usr/bin/env python

"""
AIDMOIt : Collect data and insert to HDFS cluster

Step :
    1/ Browse CSV file
    2/ Download File
    3/ Insert in HDFS cluster
    4/ Build ISO19139 XML describing metadata
    5/ Insert ISO19139 in geonetwork
"""
import os
import re
import urllib.request
import pandas as pd
import requests
import json


def getUrlFromOpendata3M(inputCSV):
    """
    Data from 3M opendata website are collected in 4 steps :
        1/ Parse CSV
        2/ From this file, get all links to 3M opendata website
        3/ For each link get the 3M ID of dataset
        4/ For each 3M dataset's ID get url asking 3M opendata's API:
            metadata
            data
    :return:dictionnary with id node of 3M opendata dataset as key and a dictionnary as value containing data & metadata
        Exemple of return :
        {"[u'9795']": {'data': [u'http://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_PduHierarchieVoies.zip', u'http://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_PduHierarchieVoies_geojson.zip', u'http://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_PduHierarchieVoies.ods', u'http://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_PduNotice.pdf'], 'metadata': [TO BIG TO PRINT for this example!!!]},
        "[u'3413']": {'data': [u'http://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_OccupationSol.zip', u'http://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_OccupSol_Lyr.zip', u'http://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_OccupSol_Nomenclature_2018.pdf', u'http://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_OccupationSol_Archives.zip'], 'metadata': [TO BIG TO PRINT for this example!!!]},
        " [u'9860']": {'data': [u'http://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_PopFine.zip', u'http://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_PopFine_Description.docx', u'http://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_PopFine_Schema.docx'], 'metadata': [TO BIG TO PRINT for this example!!!]},
    """
    # Step 1 and 2
    dataInvetoryFile = pd.read_csv(inputCSV, sep = ';')
    weblinks = dataInvetoryFile['datasetURL']

    # Step 3
    idNodePattern = re.compile("https{0,1}:..data.montpellier3m.fr.node.(\d+)")
    idNodeList = []
    for weblink in weblinks:
        html = requests.get(weblink)
        idNodeList.append(re.findall(idNodePattern, html.text))

     # Step 4
    opendata3mDataMetada = {}
    for node in idNodeList:
        opendata3mData = []
        nodeDataMetada = {'metadata': None, 'data': None}
        metadata = requests.get("http://data.montpellier3m.fr/api/3/action/package_show?id="+node[0]).json()
        #get resources
        for resource in metadata['result']['resources']:
            opendata3mData.append(resource['url'])
        nodeDataMetada['data'] = opendata3mData
        opendata3mDataMetada.update({str(node): nodeDataMetada})

    return opendata3mDataMetada


def downloadOpendata3MFiles(opendata3mDataMetada, pathToSaveDownloadedData):
    """
    Download all resources given

    :param opendata3mDataMetada: dictionary containing metadata and data to download by Id node from 3M opendata
    :return: None
    """
    nboffiledl = 0
    for node in opendata3mDataMetada:
        for fileToDownoald in opendata3mDataMetada[node]['data']:
            urllib.request.urlretrieve(fileToDownoald, os.path.join(pathToSaveDownloadedData, fileToDownoald.split('/')[-1]))
            nboffiledl = nboffiledl + 1

    return nboffiledl


if __name__ == '__main__':
    #Init variables
    dirname = os.path.dirname(__file__)
    inputCSV = os.path.join(dirname, '../input/datasources.csv')
    pathToSaveDownloadedData = os.path.join(dirname, '../output/data')
    pathToSaveDownloadedMeta = os.path.join(dirname, '../output/meta/meta.json')
    nboffiledl = 0
    #end of init variables

    print("AIDMOIt ingestion module starts")

    """Get URL of data and metadata from 3M Opendata website"""
    opendata3mDataMetada = getUrlFromOpendata3M(inputCSV)
    jsonfile = open(pathToSaveDownloadedMeta, "w")
    jsonfile.write(json.dumps(opendata3mDataMetada))
    jsonfile.close()
    """Download File"""
    nboffiledl = downloadOpendata3MFiles(opendata3mDataMetada, pathToSaveDownloadedData)

    print(str(nboffiledl)+" files downloaded in : " + pathToSaveDownloadedData)
    print("AIDMOIt ingestion module ends")
