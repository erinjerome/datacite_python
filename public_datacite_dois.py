# -*- coding: utf-8 -*-
"""public_datacite_dois.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1jwzE-mXtmJTjrRmr1Ho1GiJ3dDWgjoFC
"""

import requests
import json
import random
import string
import pandas as pd
#import xlsxwriter

def rando_gen():
    '''Generates a random four-character alphanumeric string'''
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(4))

def new_doi():
    '''Combines two rando_gen() functions for DOI'''
    return '{0}-{1}'.format(rando_gen(), rando_gen())

def pull_dois():
    '''Pulls current crop of DOIs from Datacite API'''
    response = requests.get('https://api.datacite.org/dois?client-id=username')#production enviroment api, add username after id

    dois = json.loads(response.text)
    doi_data = dois['data']
    known_idents = []
    for doi in doi_data:
        ident = doi['id'].split('/')[1]
        known_idents.append(ident)
    return known_idents



def data_munger(x, xx):
    '''Reads in the metadata from your export CSV and readies it for import. Note: the row.creator refers to a column titled creator in OUR csv of metadata. You will need to make sure that your row.name matches the corresponding column name in your csv file in order for the metadata to be read correctly.'''
    input_csv = pd.read_csv(xx, encoding='utf-8')
    data_package = []
    for row in input_csv.itertuples():
        doi_ext = new_doi()
        while rando_gen() in x:
            doi_ext = new_doi()
        else:
            data_package.append(
                {'id': row.context_key,
                 'creators': [
                     {'name': row.creator,
                      'nameType': 'Personal',
                      'givenName': row.author1_fname,
                      'familyName': row.author1_lname,
                      'affiliation': ['author institution'],
                      #to include ORCID
                      'nameIdentifiers':[
                          {
                            'schemeUri':'https://orcid.org',
                            'nameIdentifier': row.orcid,
                            'nameIdentifierScheme':'ORCID'
                          }
                                        ]
                      }
                              ],
                      'year': row.date,
                      'uri': row.source,
                      'title': row.title,
                      'types': {
                                'resourceType': '',
                                'resourceTypeGeneral': 'Text' #'Text' for theses, 'Dissertation' for dissertations
                               },
                      'descriptions': [
                          {
                              'description': row.description,
                              '#descriptionType': 'Abstract'
                          }
                                      ],
                      'publisher': 'YOUR INSTITUTION',
                      'language': "English",
                      'doi': '10.0000/{0}'.format(row.context_key)})
            '''Be sure to enter your doi prefix above where it says 10.#####.'''
    return data_package

def doi_packager(y):
    '''Submits new DOI packages to Datacite. Be sure to add your credentials for DataCite production where it says USERNAME and PASSWORD.'''
    headers = {'Content-Type': 'application/vnd.api+json'}
    export_list = []
    for doi_data in y:
        export_dict = {}
        data_pack = {'data': {'id': doi_data['doi'], 'type': 'dois', 'attributes':
                         {'event': 'publish', 'doi': doi_data['doi'], 'creators': doi_data['creators'],
                          'titles': [{'title': doi_data['title']}], 'publisher': doi_data['publisher'],
                          'publicationYear': doi_data['year'], 'descriptions': doi_data['descriptions'],
                          'types': doi_data['types'],
                          'url': doi_data['uri'], 'schemaVersion': 'http://datacite.org/schema/kernel-4'}}}
        jsonized = json.dumps(data_pack, ensure_ascii=False)
        response = requests.post('https://api.datacite.org/dois',
                                 headers=headers, data=jsonized.encode('utf-8'),

                                 auth=('USERNAME', 'PASSWORD')) #this is production login
        print('{0} processed, response: {1}'.format(doi_data['doi'], response.status_code))
        export_dict['id'] = doi_data['id']
        export_dict['doi'] = 'https://doi.org/{0}'.format(doi_data['doi'])
        export_dict['status'] = response.status_code
        export_list.append(export_dict)
    return export_list

def csv_machine(z):
    '''Barfs out a CSV file of your results'''
    output = pd.DataFrame(z)
    output = output.set_index('id')
    output.to_csv('metadata_update.csv')

file_name = input('Please enter the name of your CSV file. (Make sure the filename has no spaces!)')

existing_dois = pull_dois()
new_dois = data_munger(existing_dois, file_name)
results = doi_packager(new_dois)
csv_machine(results)
