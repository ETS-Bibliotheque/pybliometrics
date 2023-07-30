from collections import namedtuple
from warnings import warn
from typing import Any, List, NamedTuple, Optional, Tuple, Union, Literal

import pandas as pd

from json import loads

from pybliometrics.superclasses import Lookup
from pybliometrics.utils import chained_get, get_content, URLS


class CountryLookup(Lookup):
    # Class variables
    yearRange_list = Literal['3yrs', '3yrsAndCurrent', '3yrsAndCurrentAndFuture', '5yrs', '5yrsAndCurrent', '5yrsAndCurrentAndFuture', '10yrs']
    metricType_liste = Literal['AcademicCorporateCollaboration', 'AcademicCorporateCollaborationImpact', 'Collaboration','CitationCount', 'CitationsPerPublication', 'CollaborationImpact', 'CitedPublications','FieldWeightedCitationImpact', 'ScholarlyOutput', 'PublicationsInTopJournalPercentiles', 'OutputsInTopCitationPercentiles']
    includedDocs_list = Literal['AllPublicationTypes', 'ArticlesOnly', 'ArticlesReviews', 'ArticlesReviewsConferencePapers', 'ArticlesReviewsConferencePapersBooksAndBookChapters', 'ConferencePapersOnly', 'ArticlesConferencePapers', 'BooksAndBookChapters']
    journalImpactType_list = Literal['CiteScore', 'SNIP', 'SJR']
    indexType_list = Literal['hIndex', 'h5Index', 'gIndex', 'mIndex']

    @property
    def name(self):
        return chained_get(self._results, ['name'], 'Unknown')
    
    @property
    def id(self):
        return chained_get(self._results, ['id'], 'Unknown')
   
    @property
    def uri(self):
        return chained_get(self._results, ['uri'], 'Unknown')
    
    @property
    def code(self):
        return chained_get(self._results, ['countryCode'], 'Unknown')

    def __init__(self,
                 country_name: str,
                 refresh: Union[bool, int] = False,
                 **kwds: str
                 ) -> None:
        """Interaction with the Author Retrieval API.

        :param author_id: The ID or the EID of the author.
        :param refresh: Whether to refresh the cached file if it exists or not.
                        If int is passed, cached file will be refreshed if the
                        number of days since last modification exceeds that value.
        :param view: The view of the file that should be downloaded.  Allowed
                     values: METRICS, LIGHT, STANDARD, ENHANCED, where STANDARD
                     includes all information of LIGHT view and ENHANCED
                     includes all information of any view.  For details see
                     https://dev.elsevier.com/sc_author_retrieval_views.html.
                     Note: Neither the BASIC nor the DOCUMENTS view are active,
                     although documented.
        :param kwds: Keywords passed on as query parameters.  Must contain
                     fields and values mentioned in the API specification at
                     https://dev.elsevier.com/documentation/AuthorRetrievalAPI.wadl.

        Raises
        ------
        ValueError
            If any of the parameters `refresh` or `view` is not
            one of the allowed values.

        Notes
        -----
        The directory for cached results is `{path}/ENHANCED/{author_id}`,
        where `path` is specified in your configuration file, and `author_id`
        is stripped of an eventually leading `'9-s2.0-'`.
        """
        # Load json
        self._refresh = refresh
        self._country_name = country_name

        Lookup.__init__(self,
                        identifier=country_name,
                        api='CountryLookup',
                        complement="search",
                        **kwds)
        self.kwds = kwds

        # Parse json
        self._results = self._json['results'][0]


    def __str__(self) -> str:
        """Return a summary string."""
        date = self.get_cache_file_mdate().split()[0]
        s = f"Your choice, as of {date}:\n"\
            f"\t- Country name: {self.name}\n"\
            f"\t- ID: \t\t{self.id}"
        return s
    

    def _query(self,
               query: Union[str, int] = '',
               field: Literal['name', 'region'] = 'name',
               limit: int = 100,
               offset: int = 0) -> dict:
        
        query = self._country_name if query == '' else query

        if field != 'region':
            query = field + '(' + str(query).lower() + ')'
        else:
            query = field + '(' + str(query).lower().capitalize() + ')'

        params = {
            "query": query,
            "limit": limit,
            "offset": offset
        }

        response = get_content(url=URLS['CountryLookup']+'search', api='CountryLookup', params=params, **self.kwds)
        data = response.json()['results']
        return data
 
    def get_country(self,
                    name: str ='',
                    limit: int = 100,
                    offset: int = 0) -> dict:
        name = self._country_name if name == '' else name
        result = self._query(query=name, field='name', limit=limit, offset=offset)[0]
        del result['link']
        return result
    
    def get_region(self,
                   name: str,
                   limit: int = 100,
                   offset: int = 0) -> dict:
        result = self._query(query=name, field='region', limit=limit, offset=offset)
        return RegionFormatage(result)
    


    def _get_metrics_rawdata(self, 
                    metricType: metricType_liste = 'ScholarlyOutput',
                    yearRange: yearRange_list = '5yrs',
                    country_ids: str = '',
                    subjectAreaFilterURI: str = '',
                    includeSelfCitations: bool = True,
                    byYear: bool = True,
                    includedDocs: includedDocs_list = 'AllPublicationTypes',
                    journalImpactType: journalImpactType_list = 'CiteScore',
                    showAsFieldWeighted: bool = False,
                    indexType: indexType_list = 'hIndex') -> any:
        
        country_ids = self.id if country_ids == '' else country_ids

        params = {
            "countryIds": country_ids,
            "metricTypes": metricType,
            "yearRange": yearRange,
            "subjectAreaFilterURI": subjectAreaFilterURI,
            "includeSelfCitations": includeSelfCitations,
            "byYear": byYear,
            "includedDocs": includedDocs,
            "journalImpactType": journalImpactType,
            "showAsFieldWeighted": showAsFieldWeighted,
            "indexType": indexType
        }

        response = get_content(url=URLS['CountryLookup']+'metrics', api='CountryLookup', params=params, **self.kwds)
        data = response.json()['results'][0]['metrics'][0]
        last_key = list(data.keys())[-1]
        return data[last_key]
    
    def get_metrics_Collaboration(self, 
                metricType: Literal['AcademicCorporateCollaboration', 'AcademicCorporateCollaborationImpact', 'Collaboration', 'CollaborationImpact'] = 'AcademicCorporateCollaboration',
                collabType: Literal['Academic-corporate collaboration', 'No academic-corporate collaboration', 'Institutional collaboration', 'International collaboration', 'National collaboration', 'Single authorship'] = 'No academic-corporate collaboration',
                value_or_percentage: Literal['valueByYear', 'percentageByYear'] = 'valueByYear', 
                yearRange: yearRange_list = '5yrs',
                country_ids: str = '',
                subjectAreaFilterURI: str = '',
                includeSelfCitations: bool = True,
                byYear: bool = True,
                includedDocs: includedDocs_list = 'AllPublicationTypes',
                journalImpactType: journalImpactType_list = 'CiteScore',
                showAsFieldWeighted: bool = False,
                indexType: indexType_list = 'hIndex'):
        if metricType in ('AcademicCorporateCollaboration', 'AcademicCorporateCollaborationImpact'):
            self._check_args(collabType, metricType, ('Academic-corporate collaboration', 'No academic-corporate collaboration'))
        elif metricType in ('Collaboration', 'CollaborationImpact'):
            self._check_args(collabType, metricType, ('Institutional collaboration', 'International collaboration', 'National collaboration', 'Single authorship'))
        if metricType in ('AcademicCorporateCollaborationImpact', 'CollaborationImpact'):
            value_or_percentage = 'valueByYear'

        return MetricsFormatage(self._for_advanced_metrics(metricType,yearRange,subjectAreaFilterURI,includeSelfCitations,byYear,includedDocs,journalImpactType,showAsFieldWeighted,indexType,
                                                    country_ids, 'collabType', collabType, value_or_percentage))
    
    def get_metrics_Percentile  (self, 
                metricType: Literal['PublicationsInTopJournalPercentiles', 'OutputsInTopCitationPercentiles'] = 'OutputsInTopCitationPercentiles',
                threshold: Literal[1, 5, 10, 25] = 10,
                value_or_percentage: Literal['valueByYear', 'percentageByYear'] = 'valueByYear',
                yearRange: yearRange_list = '5yrs',
                country_ids: str = '',
                subjectAreaFilterURI: str = '',
                includeSelfCitations: bool = True,
                byYear: bool = True,
                includedDocs: includedDocs_list = 'AllPublicationTypes',
                journalImpactType: Literal['CiteScore', 'SNIP', 'SJR'] = 'CiteScore',
                showAsFieldWeighted: bool = False,
                indexType: Literal['hIndex', 'h5Index', 'gIndex', 'mIndex'] = 'hIndex'):
        return MetricsFormatage(self._for_advanced_metrics(metricType,yearRange,subjectAreaFilterURI,includeSelfCitations,byYear,includedDocs,journalImpactType,showAsFieldWeighted,indexType,
                                                    country_ids, 'threshold', threshold, value_or_percentage))
    
    def get_metrics_Other  (self, 
                metricType: Literal['CitationCount', 'CitationsPerPublication', 'CitedPublications', 'FieldWeightedCitationImpact', 'ScholarlyOutput'] = 'ScholarlyOutput',
                yearRange: yearRange_list = '5yrs',
                country_ids: str = '',
                subjectAreaFilterURI: str = '',
                includeSelfCitations: bool = True,
                byYear: bool = True,
                includedDocs: includedDocs_list = 'AllPublicationTypes',
                journalImpactType: Literal['CiteScore', 'SNIP', 'SJR'] = 'CiteScore',
                showAsFieldWeighted: bool = False,
                indexType: Literal['hIndex', 'h5Index', 'gIndex', 'mIndex'] = 'hIndex'):
        return MetricsFormatage({'valueByYear': self._for_advanced_metrics(metricType,yearRange,subjectAreaFilterURI,includeSelfCitations,byYear,includedDocs,journalImpactType,showAsFieldWeighted,indexType,
                                                    country_ids)})


    def _check_args(self, collabType: tuple, metricType: str, valid_collab_types):
        if collabType not in valid_collab_types:
            raise ValueError(f"Invalid collabType '{collabType}' for metricType '{metricType}'. "
                             f"Valid collabTypes are: {', '.join(valid_collab_types)}")

    def _for_advanced_metrics(self, metricType, yearRange, subjectAreaFilterURI, includeSelfCitations, byYear, includedDocs, journalImpactType, showAsFieldWeighted, indexType,
                                country_ids: str, key_name: str = '', value: Union[int, str] = '', value_or_percentage: str = 'valueByYear'):
        country_ids = self.id if country_ids == '' else country_ids
        data_dict = self._get_metrics_rawdata(country_ids, metricType, yearRange, subjectAreaFilterURI, includeSelfCitations, byYear, includedDocs, journalImpactType, showAsFieldWeighted, indexType)
        
        result_dict = {}
        if not key_name == '':
            for data in data_dict:
                collab_type = data[key_name]
                if collab_type == value:
                    result_dict[key_name] = collab_type
                    result_dict[value_or_percentage] = data[value_or_percentage]
        else:
            result_dict = data_dict

        return result_dict


class MetricsFormatage():
    @property
    def Raw(self):
        return self._dict
        
    @property
    def Dictionary(self):
        return self._dict[list(self._dict.keys())[-1]]

    @property
    def DataFrame(self):
        data_type = list(self._dict.keys())[-1]
        column_name = 'Percentage' if data_type == 'percentageByYear' else 'Value'
        df = pd.DataFrame.from_dict(self._dict[data_type], orient='index', columns=[column_name])
        df.index.name = 'Year'
        return df

    @property
    def List(self):
        data_type = list(self._dict.keys())[-1]
        return [[int(cle) for cle in self._dict[data_type].keys()], list(self._dict[data_type].values())]
    

    def __init__(self, data: dict) -> None:
        self._dict = data

    def __repr__(self):
        return str("You must select a property: 'Raw', 'List', 'Dictionary', 'DataFrame' after calling the AuthorLookup class method!")  


class RegionFormatage():
    @property
    def Raw(self):
        return self._dict
    
    @property
    def Dictionary(self):
        return {item['countryCode']: {'name': item['name'], 'id': item['id']} for item in self._dict}
    
    @property
    def List(self):
        noms_pays = []
        ids = []
        codes_pays = []

        for dictionnaire in self._dict:
            noms_pays.append(dictionnaire['name'])
            ids.append(dictionnaire['id'])
            codes_pays.append(dictionnaire['countryCode'])

        return[noms_pays, codes_pays, ids]
    
    @property
    def DataFrame(self):
        df = pd.DataFrame(self._dict)
        df.columns = ['Name', 'ID', 'Code']
        df.set_index('Name', inplace=True)
        
        return df

    def __init__(self, data: dict) -> None:
        for item in data:
            del item['link']
            del item['uri']
        self._dict = data

    def __repr__(self):
        return str("You must select a property: 'List', 'Dictionary', 'DataFrame' after calling the CountryLookup class method!")