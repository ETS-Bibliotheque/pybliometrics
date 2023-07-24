from collections import namedtuple
from warnings import warn
from typing import List, NamedTuple, Optional, Tuple, Union, Literal

from json import loads

from pybliometrics.superclasses import Lookup
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

    def __str__(self) -> str:
        """Return a summary string."""
        date = self.get_cache_file_mdate().split()[0]
        s = f"Your choice, as of {date}:\n"\
            f"\t- Name: {self.name}\n"\
            f"\t- ID: \t{self.id}"
        return s
    
    def get_metrics(self, id_authors: str = '',
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
                    indexType: Literal['hIndex', 'h5Index', 'gIndex', 'mIndex'] = 'hIndex'):
        
        id_authors = self._id if id_authors == '' else id_authors

        params = {
            "authors": id_authors,
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