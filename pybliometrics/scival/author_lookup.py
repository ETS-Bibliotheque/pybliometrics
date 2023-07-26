from collections import namedtuple
from warnings import warn
from typing import List, NamedTuple, Optional, Tuple, Union, Literal

import pandas as pd

from json import loads

from pybliometrics.superclasses import Lookup
from pybliometrics.scopus import AuthorRetrieval
from pybliometrics.utils import chained_get, check_parameter_value,\
    filter_digits, get_content, get_link, html_unescape, listify, make_int_if_possible,\
    parse_affiliation, parse_date_created, URLS

class AuthorLookup(Lookup):
    @property
    def name(self):
        return chained_get(self._results, ['author', 'name'], 'Unknown')
    
    @property
    def id(self):
        return chained_get(self._results, ['author', 'id'])
    
    @property
    def irl(self):
        return chained_get(self._results, ['author', 'irl'])

    @property
    def dataSource(self):
        return [[key, value] for key, value in self._dataSource.items()]

    def __init__(self,
                 author_id: Union[int, str],
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
        self._id = str(author_id).split('-')[-1]
        self._refresh = refresh

        Lookup.__init__(self,
                        api='AuthorLookup',
                        identifier=self._id,
                        complement="metrics",
                        **kwds)
        self.kwds = kwds

        # Parse json
        self._results = self._json['results'][0]
        self._dataSource = self._json['dataSource']
        # self._current_institution = AuthorRetrieval(self._id, refresh=self._refresh).affiliation_current
        
        # # Retrieve the id of the first institution from the list of current institutions
        # self._default_current_institution_id = str(self._current_institution[0]).split("id=")[1].split(",")[0].strip()

        # Définition de args avec les arguments, leur type et leur valeur par défaut
        args_inst = (
            ('institutionId', Union[str, int], 0),
            ('yearRange', Literal['3yrs', '3yrsAndCurrent', '3yrsAndCurrentAndFuture', '5yrs', '5yrsAndCurrent', '5yrsAndCurrentAndFuture', '10yrs'], '5yrs'),
            ('limit', int, 500),
            ('offset', int, 0)
        )


    def __str__(self) -> str:
        """Return a summary string."""
        date = self.get_cache_file_mdate().split()[0]
        s = f"Your choice, as of {date}:\n"\
            f"\t- Name: {self.name}\n"\
            f"\t- ID: \t{self.id}"
        return s
    
    def get_metrics(self, 
                    author_ids: str = '',
                    metricType: Literal['AcademicCorporateCollaboration', 'AcademicCorporateCollaborationImpact', 'Collaboration',
                                        'CitationCount', 'CitationsPerPublication', 'CollaborationImpact', 'CitedPublications',
                                        'FieldWeightedCitationImpact', 'ScholarlyOutput', 'PublicationsInTopJournalPercentiles', 
                                        'OutputsInTopCitationPercentiles'] = 'ScholarlyOutput',
                    yearRange: Literal['3yrs', '3yrsAndCurrent', '3yrsAndCurrentAndFuture', '5yrs', '5yrsAndCurrent', 
                                       '5yrsAndCurrentAndFuture', '10yrs'] = '5yrs',
                    subjectAreaFilterURI: str = '',
                    includeSelfCitations: bool = True,
                    byYear: bool = True,
                    includedDocs: Literal['AllPublicationTypes', 'ArticlesOnly', 'ArticlesReviews', 'ArticlesReviewsConferencePapers', 
                                          'ArticlesReviewsConferencePapersBooksAndBookChapters', 'ConferencePapersOnly', 
                                          'ArticlesConferencePapers', 'BooksAndBookChapters'] = 'AllPublicationTypes',
                    journalImpactType: Literal['CiteScore', 'SNIP', 'SJR'] = 'CiteScore',
                    showAsFieldWeighted: bool = False,
                    indexType: Literal['hIndex', 'h5Index', 'gIndex', 'mIndex'] = 'hIndex') -> any:
        
        author_ids = self._id if author_ids == '' else author_ids

        params = {
            "authors": author_ids,
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

        response = get_content(url=URLS['AuthorLookup']+'metrics', api='AuthorLookup', params=params, **self.kwds)
        data = response.json()['results'][0]['metrics'][0]
        last_key = list(data.keys())[-1]
        return data[last_key]
    

    def get_metrics_DataFrame_Collaboration  (self, 
                author_ids: str = '',
                metricType: Literal['AcademicCorporateCollaboration', 'AcademicCorporateCollaborationImpact', 'Collaboration',
                                    'CollaborationImpact'] = 'AcademicCorporateCollaboration',
                collabType: Literal['Academic-corporate collaboration', 'No academic-corporate collaboration', 'Institutional collaboration',
                                    'International collaboration', 'National collaboration', 'Single authorship'] = 'No academic-corporate collaboration',
                value_or_percentage: Literal['valueByYear', 'percentageByYear'] = 'valueByYear',
                yearRange: Literal['3yrs', '3yrsAndCurrent', '3yrsAndCurrentAndFuture', '5yrs', '5yrsAndCurrent', 
                                    '5yrsAndCurrentAndFuture', '10yrs'] = '5yrs',
                subjectAreaFilterURI: str = '',
                includeSelfCitations: bool = True,
                byYear: bool = True,
                includedDocs: Literal['AllPublicationTypes', 'ArticlesOnly', 'ArticlesReviews', 'ArticlesReviewsConferencePapers', 
                                        'ArticlesReviewsConferencePapersBooksAndBookChapters', 'ConferencePapersOnly', 
                                        'ArticlesConferencePapers', 'BooksAndBookChapters'] = 'AllPublicationTypes',
                journalImpactType: Literal['CiteScore', 'SNIP', 'SJR'] = 'CiteScore',
                showAsFieldWeighted: bool = False,
                indexType: Literal['hIndex', 'h5Index', 'gIndex', 'mIndex'] = 'hIndex'):
        
        if metricType in ('AcademicCorporateCollaboration', 'AcademicCorporateCollaborationImpact'):
            self._check_args(collabType, metricType, ('Academic-corporate collaboration', 'No academic-corporate collaboration'))
        elif metricType in ('Collaboration', 'CollaborationImpact'):
            self._check_args(collabType, metricType, ('Institutional collaboration', 'International collaboration', 'National collaboration', 'Single authorship'))
        if metricType in ('AcademicCorporateCollaborationImpact', 'CollaborationImpact'):
            value_or_percentage = 'valueByYear'

        author_ids = self._id if author_ids == '' else author_ids

        data = self.get_metrics(author_ids, metricType, yearRange, subjectAreaFilterURI, includeSelfCitations, byYear, 
                                includedDocs, journalImpactType, showAsFieldWeighted, indexType)
        
        for item in data:
            if item['collabType'] == collabType:
                by_year = item[value_or_percentage]
                break
        column_name = 'Percentage' if value_or_percentage == 'percentageByYear' else 'Value'
        df = pd.DataFrame.from_dict(by_year, orient='index', columns=[column_name])
        df.index.name = 'Year'

        return df
    
    def get_metrics_DataFrame_Percentile  (self, 
                author_ids: str = '',
                metricType: Literal['PublicationsInTopJournalPercentiles', 'OutputsInTopCitationPercentiles'] = 'OutputsInTopCitationPercentiles',
                threshold: Literal[1, 5, 10, 25] = 10,
                value_or_percentage: Literal['valueByYear', 'percentageByYear'] = 'valueByYear',
                yearRange: Literal['3yrs', '3yrsAndCurrent', '3yrsAndCurrentAndFuture', '5yrs', '5yrsAndCurrent', 
                                    '5yrsAndCurrentAndFuture', '10yrs'] = '5yrs',
                subjectAreaFilterURI: str = '',
                includeSelfCitations: bool = True,
                byYear: bool = True,
                includedDocs: Literal['AllPublicationTypes', 'ArticlesOnly', 'ArticlesReviews', 'ArticlesReviewsConferencePapers', 
                                        'ArticlesReviewsConferencePapersBooksAndBookChapters', 'ConferencePapersOnly', 
                                        'ArticlesConferencePapers', 'BooksAndBookChapters'] = 'AllPublicationTypes',
                journalImpactType: Literal['CiteScore', 'SNIP', 'SJR'] = 'CiteScore',
                showAsFieldWeighted: bool = False,
                indexType: Literal['hIndex', 'h5Index', 'gIndex', 'mIndex'] = 'hIndex'):

        author_ids = self._id if author_ids == '' else author_ids

        data = self.get_metrics(author_ids, metricType, yearRange, subjectAreaFilterURI, includeSelfCitations, byYear, 
                                includedDocs, journalImpactType, showAsFieldWeighted, indexType)
        
        for item in data:
            if item['threshold'] == threshold:
                by_year = item[value_or_percentage]
                break
        column_name = 'Percentage' if value_or_percentage == 'percentageByYear' else 'Value'
        df = pd.DataFrame.from_dict(by_year, orient='index', columns=[column_name])
        df.index.name = 'Year'

        return df
    
    def get_metrics_DataFrame_Other  (self, 
                author_ids: str = '',
                metricType: Literal['CitationCount', 'CitationsPerPublication', 'CitedPublications',
                                    'FieldWeightedCitationImpact', 'ScholarlyOutput'] = 'ScholarlyOutput',
                yearRange: Literal['3yrs', '3yrsAndCurrent', '3yrsAndCurrentAndFuture', '5yrs', '5yrsAndCurrent', 
                                    '5yrsAndCurrentAndFuture', '10yrs'] = '5yrs',
                subjectAreaFilterURI: str = '',
                includeSelfCitations: bool = True,
                byYear: bool = True,
                includedDocs: Literal['AllPublicationTypes', 'ArticlesOnly', 'ArticlesReviews', 'ArticlesReviewsConferencePapers', 
                                        'ArticlesReviewsConferencePapersBooksAndBookChapters', 'ConferencePapersOnly', 
                                        'ArticlesConferencePapers', 'BooksAndBookChapters'] = 'AllPublicationTypes',
                journalImpactType: Literal['CiteScore', 'SNIP', 'SJR'] = 'CiteScore',
                showAsFieldWeighted: bool = False,
                indexType: Literal['hIndex', 'h5Index', 'gIndex', 'mIndex'] = 'hIndex'):

        author_ids = self._id if author_ids == '' else author_ids

        data = self.get_metrics(author_ids, metricType, yearRange, subjectAreaFilterURI, includeSelfCitations, byYear, 
                                includedDocs, journalImpactType, showAsFieldWeighted, indexType)
        
        df = pd.DataFrame.from_dict(data, orient='index', columns=['Values'])
        df.index.name = 'Year'

        return df

    
    def _check_args(self, collabType: tuple, metricType: str, valid_collab_types):
        if collabType not in valid_collab_types:
            raise ValueError(f"Invalid collabType '{collabType}' for metricType '{metricType}'. "
                             f"Valid collabTypes are: {', '.join(valid_collab_types)}")
        
    def get_institution_metrics(self,
                                institutionId: Union[str, int],
                                yearRange: Literal['3yrs', '3yrsAndCurrent', '3yrsAndCurrentAndFuture', '5yrs', '5yrsAndCurrent', 
                                                   '5yrsAndCurrentAndFuture', '10yrs'] = '5yrs',
                                limit: int = 500,
                                offset: int = 0):
        
        # institutionId = self._default_current_institution_id if institutionId == 0 else str(institutionId)
        limit = 1 if limit < 1 else (500 if limit > 500 else limit)

        params = {
            "yearRange": yearRange,
            "limit": limit,
            "offset": offset
        }

        response = get_content(url=URLS['AuthorLookup']+'institutionId/'+str(institutionId), api='AuthorLookup', params=params, **self.kwds)
        data = response.json()
        del data['link']
        return data
        
    def institutional_authors(self, institutionId: Union[str, int], yearRange: Literal['3yrs', '3yrsAndCurrent', '3yrsAndCurrentAndFuture', '5yrs', '5yrsAndCurrent', 
                                                                                        '5yrsAndCurrentAndFuture', '10yrs'] = '5yrs'):
        return self.get_institution_metrics(institutionId=institutionId, yearRange=yearRange)['authors']
    
    def institutional_total_count(self, institutionId: Union[str, int], yearRange: Literal['3yrs', '3yrsAndCurrent', '3yrsAndCurrentAndFuture', '5yrs', '5yrsAndCurrent', 
                                                                                            '5yrsAndCurrentAndFuture', '10yrs'] = '5yrs'):
        return self.get_institution_metrics(institutionId=institutionId, yearRange=yearRange)['totalCount']


