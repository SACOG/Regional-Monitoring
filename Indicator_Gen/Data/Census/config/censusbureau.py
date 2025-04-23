


import warnings
from functools import wraps, lru_cache
from importlib.metadata import version

__version__ = version('census')

ALL = '*'


def new_session(*args, **kwargs):
    import requests
    return requests.session(*args, **kwargs)


class APIKeyError(Exception):
    """ Invalid API key
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def list_or_str(v):
    """ Convert a single value into a list.
    """
    if isinstance(v, (list, tuple)):
        return v
    return [v]


def float_or_str(v):
    try:
        return float(v)
    except ValueError:
        return str(v)


def supported_years(*years):
    def inner(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            year = kwargs.get('year', self.default_year)
            _years = years if years else self.years
            if int(year) not in _years:
                raise UnsupportedYearException(
                    'Geography is not available in {}. Available years include {}'.format(year, _years))
            return func(self, *args, **kwargs)
        return wrapper
    return inner


def retry_on_transient_error(func):

    def wrapper(self, *args, **kwargs):
        for _ in range(max(self.retries - 1, 0)):
            try:
                result = func(self, *args, **kwargs)
            except CensusException as e:
                if "There was an error while running your query.  We've logged the error and we'll correct it ASAP.  Sorry for the inconvenience." in str(e):
                    pass
                else:
                    raise
            else:
                return result
        else:
            return func(self, *args, **kwargs)

    return wrapper


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def merge(dicts):
    return dict(item for d in dicts for item in d.items())


class CensusException(Exception):
    pass


class UnsupportedYearException(CensusException):
    pass


class Client(object):
    endpoint_url    = 'https://api.census.gov/data/%s/%s'
    definitions_url = 'https://api.census.gov/data/%s/%s/variables.json'
    definition_url  = 'https://api.census.gov/data/%s/%s/variables/%s.json'
    groups_url      = 'https://api.census.gov/data/%s/%s/groups.json'

    def __init__(self, key, year=None, session=None, retries=3):
        self._key = key
        self.session = session or new_session()
        if year:
            self.default_year = year
        self.retries = retries

    def tables(self, year=None):
        """
        Returns a list of the data tables available from this source.
        """
        # Set the default year if one hasn't been passed
        if year is None:
            year = self.default_year

        # Query the table metadata as raw JSON
        tables_url = self.groups_url % (year, self.dataset)
        resp = self.session.get(tables_url)

        # Pass it out
        return resp.json()['groups']

    @supported_years()
    def fields(self, year=None, flat=False):
        if year is None:
            year = self.default_year

        data = {}

        fields_url = self.definitions_url % (year, self.dataset)

        resp = self.session.get(fields_url)
        obj = resp.json()

        if flat:

            for key, elem in obj['variables'].items():
                if key in ['for', 'in']:
                    continue
                data[key] = "{}: {}".format(elem['concept'], elem['label'])

        else:

            data = obj['variables']
            if 'for' in data:
                data.pop("for", None)
            if 'in' in data:
                data.pop("in", None)

        return data

    def get(self, fields, geo, year=None, **kwargs):
        """
        The API only accepts up to 50 fields on each query.
        Chunk requests, and use the unique GEO_ID to match up the chunks
        in case the responses are in different orders.
        GEO_ID is not reliably present in pre-2010 requests.
        """
        sort_by_geoid = len(fields) > 49 and (not year or year > 2009)
        all_results = (self.query(forty_nine_fields, geo, year, sort_by_geoid=sort_by_geoid, **kwargs)
                       for forty_nine_fields in chunks(fields, 49))
        merged_results = [merge(result) for result in zip(*all_results)]

        return merged_results

    @retry_on_transient_error
    def query(self, fields, geo, year=None, sort_by_geoid=False, **kwargs):
        if year is None:
            year = self.default_year

        fields = list_or_str(fields)
        if sort_by_geoid:
            if isinstance(fields, list):
                fields += ['GEO_ID']
            elif isinstance(fields, tuple):
                fields += ('GEO_ID',)

        url = self.endpoint_url % (year, self.dataset)

        params = {
            'get': ",".join(fields),
            'for': geo['for'],
            'key': self._key,
        }

        if 'in' in geo:
            params['in'] = geo['in']

        resp = self.session.get(url, params=params)

        if resp.status_code == 200:
            try:
                data = resp.json()
            except ValueError as ex:
                if '<title>Invalid Key</title>' in resp.text:
                    raise APIKeyError(' '.join(resp.text.splitlines()))
                else:
                    raise ex

            headers = data.pop(0)
            types = [self._field_type(header, year) for header in headers]
            results = [{header: (cast(item) if item is not None else None)
                        for header, cast, item
                        in zip(headers, types, d)}
                       for d in data]
            if sort_by_geoid:
                if 'GEO_ID' in fields:
                    results = sorted(results, key=lambda x: x['GEO_ID'])
                else:
                    results = sorted(results, key=lambda x: x.pop('GEO_ID'))
            return results

        elif resp.status_code == 204:
            return []

        else:
            raise CensusException(resp.text)

    @lru_cache(maxsize=1024)
    def _field_type(self, field, year):
        url = self.definition_url % (year, self.dataset, field)
        resp = self.session.get(url)

        types = {
            "fips-for": str,
            "fips-in" : str,
            "int"     : float_or_str,
            "long"    : float_or_str,
            "float"   : float,
            "string"  : str
        }

        if resp.status_code == 200:
            predicate_type = resp.json().get("predicateType", "string")
            return types[predicate_type]
        else:
            return str


class ACSClient(Client):

    def _switch_endpoints(self, year):

        if year >= 2005:
            self.endpoint_url    = 'https://api.census.gov/data/%s/acs/%s'
            self.definitions_url = 'https://api.census.gov/data/%s/acs/%s/variables.json'
            self.definition_url  = 'https://api.census.gov/data/%s/acs/%s/variables/%s.json'
            self.groups_url      = 'https://api.census.gov/data/%s/acs/%s/groups.json'
        else:
            self.endpoint_url    = super(ACSClient, self).endpoint_url
            self.definitions_url = super(ACSClient, self).definitions_url
            self.definition_url  = super(ACSClient, self).definition_url
            self.groups_url      = super(ACSClient, self).groups_url

    def tables(self, *args, **kwargs):
        self._switch_endpoints(kwargs.get('year', self.default_year))
        return super(ACSClient, self).tables(*args, **kwargs)

    def get(self, *args, **kwargs):
        self._switch_endpoints(kwargs.get('year', self.default_year))

        return super(ACSClient, self).get(*args, **kwargs)


class ACS5Client(ACSClient):

    default_year = 2023
    dataset = 'acs5'

    years = (2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009)


class ACS1Client(ACSClient):

    default_year = 2023
    dataset = 'acs1'

    years = (2023, 2022, 2021, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005)



class Census(object):

    ALL = ALL

    def __init__(self, key, year=None, session=None):

        if not session:
            session = new_session()

        self.session = session
        self.session.headers.update({
            'User-Agent': ('python-census/{} '.format(__version__) +
                           'github.com/datamade/census')
        })

        self._acs = ACS5Client(key, year, session)  # deprecated
        self.acs5 = ACS5Client(key, year, session)
        self.acs1 = ACS1Client(key, year, session)

    @property
    def acs(self):
        warnings.warn('Use acs5 instead of acs', DeprecationWarning)
        return self._acs



    

def set_parameters(geography, year, **kwargs):
    if geography == 'Places':
        params = {'for': f'place:*', 'in': f'state:{state}'}
    if geography == 'Block Groups':
        params = {'for': f'block group:*', 'in': f'county:{counties} state:{state}'}
    if geography == 'Tracts':
        params = {'for': f'tract:*', 'in': f'county:{counties} state:{state}'}
    if geography == 'Counties':
        params = {'for': f'county:{counties}', 'in': f'state:{state}'}
    if geography == 'MSA':
        params = {'for': f'metropolitan statistical area/micropolitan statistical area:{msa}'}            
    if geography == 'Congressional Districts':
        params = {'for': f'congressional district:*', 'in': f'state:{state}'}
    if geography == 'State Legislative Upper Districts':
        params = {'for': f'state legislative district (upper chamber):*', 'in': f'state:{state}'}
    if geography == 'State Legislative Lower Districts':
        params = {'for': f'state legislative district (lower chamber):*', 'in': f'state:{state}'}
    if geography == 'PUMA':
        params = {'for': f'public use microdata area:{pumas}', 'in': f'state:{state}'}
    if geography == 'States':
        params = {'for': f'state:{state}'}
    if geography == 'National':
        params = {'for': 'us:*'}

    return params


def clean_fips(df):
    if 'State FIPS' in df.columns:
        df['State FIPS'] = df['State FIPS'].astype(str).apply('{:0>2}'.format)
    if 'Place ID' in df.columns:
        df['Place ID'] = df['Place ID'].astype(str).apply('{:0>5}'.format)
    if 'County FIPS' in df.columns:
        df['County FIPS'] = df['County FIPS'].astype(str).apply('{:0>3}'.format)
    if 'Congressional District' in df.columns:
        df['Congressional District'] = df['Congressional District'].astype(str).apply('{:0>2}'.format)
    if 'State Legislative Upper District' in df.columns:
        df['State Legislative Upper District'] = df['State Legislative Upper District'].astype(str).apply('{:0>3}'.format)
    if 'State Legislative Lower District' in df.columns:
        df['State Legislative Lower District'] = df['State Legislative Lower District'].astype(str).apply('{:0>3}'.format)

    return df