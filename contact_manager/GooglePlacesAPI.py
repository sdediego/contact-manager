#!/usr/bin/python

import json
import requests

from decimal import Decimal


__all__ = ['GooglePlaces', 'GooglePlacesSearchRequest',
           'GooglePlacesSearchResponse', 'GooglePlacesResponsePlace',
           'GooglePlacesAttributes', 'GooglePlacesError',
           'GooglePlacesAPIkeyError']
__version__ = 1.0


class GooglePlacesError(Exception):
    """
    Exception for Google Places API errors.
    """

    def __init__(self, msg, original_exception=None):
        if original_exception is not None:
            msg += ": {}".format(original_exception)
        super(GooglePlacesError, self).__init__(msg)
        self.original_exception = original_exception


class GooglePlacesAPIkeyError(Exception):
    """
    Exception for Google Places API key credentials errors.
    """
    pass


class GooglePlaces(object):
    """
    Class to enable Google Places API use.
    """
    # Define API's bound parameters.
    MAX_RADIUS = 50000  # in meters.
    MIN_ABS_LATITUDE = 0
    MAX_ABS_LATITUDE = 90
    MIN_ABS_LONGITUDE= 0
    MAX_ABS_LONGITUDE = 180
    # Define API's url for search.
    BASE_API_URL = 'https://maps.googleapis.com/maps/api/place'
    TEXT_SEARCH_API_URL = BASE_API_URL + '/textsearch/json?'

    def __init__(self, api_key):
        """
        Initializes Google Places class.
        """
        self._api_key = self._get_api_key()
        self._request_params = {}

    def __str__(self):
        """
        Returns a string representation of class params.
        """
        queries = {'classname': self.__class__.__name__}
        for key, value in self.request_params.items():
            queries.update({'{}'.format(key): value})
        return str(queries)

    def _get_api_key(self, api_key=None, filename='contact_manager.ini', section='googleplaces'):
        """
        Parses Google Places API key.
        """
        parser = configparser.ConfigParser()
        parser.read(filename)
        if parser.has_section(section):
            api_key = parser.get('api_key', section)
        else:
            msg = 'Section {} not found in {} filename'.format(section, filename)
            raise GooglePlacesAPIkeyError(msg)
        return api_key

    def text_search(self, query=None, latitude=None, longitude=None, location=None,
                    radius=100, types=[], language=None, pagetoken=None):
        """
        Perform a text search using the Google Places API.
        """
        # Set parameters.
        self._set_request_params(query, latitude, longitude, location, radius,
                                 types, language, pagetoken)
        # Perform search.
        request = GooglePlacesSearchRequest(self.__class__.TEXT_SEARCH_API_URL,
                                           self._request_params)
        request_url, response = request.fetch_json_response()
        search_result = GooglePlacesSearchResponse(request_url, response)
        search_result._validate_response_status(request_url, response)
        return search_result

    def _set_request_params(self, query, latitude, longitude, location,
                            radius, types, language, pagetoken):
        """
        Sets request parameters for search.
        """
        # Search params.
        self._request_params['query'] = query
        self._request_params['location'] = self._search_location(latitude, longitude, location)
        self._request_params['radius'] = self._search_radius(radius)
        if len(types) >= 1 and types[0] in GooglePlacesAttributes.types_dict().values():
            self._request_params['type'] = types[0]
        if language is not None and language in GooglePlacesAttributes.languages_dict().values():
            self._request_params['language'] = language
        if pagetoken is not None:
            self._request_params['pagetoken'] = pagetoken
        # Other required params.
        self._request_params['key'] = self.api_key

    def _search_location(self, latitude, longitude, location):
        """
        Establishes location search parameter.
        """
        try:
            if latitude is not None and longitude is not None:
                location = self._generate_location_param(latitude, longitude)
            elif location is not None:
                location = self._validate_location_param(location)
            return location
        except ValueError as msg:
            raise GooglePlacesError('Input data value error', msg)

    def _generate_location_param(self, latitude, longitude):
        """
        Generate location search parameter from latitude
        and longitude parameters.
        """
        if self._valid_geographic_coordinates(latitude, longitude):
            location = '{latitude},{longitude}'.format(latitude, longitude)
            return location
        else:
            raise ValueError('Coordinate parameters out of bounds.')

    def _validate_location_param(self, location):
        """
        Validates location parameter format and value.
        """
        regex = re.compile(r'((-)?(\d{,2}\.\d*))(\s+|,|-)?((-)?(\d{,3}\.\d*))')
        match_object = regex.search(location)
        latitude, longitude = match_object.group(1)), match_object.group(5)
        if self._valid_geographic_coordinates(latitude, longitude):
            location = ','.join([latitude, longitude])
            return location
        else:
            raise ValueError('Coordinate parameters out of bounds.')

    def _valid_geographic_coordinates(self, latitude, longitude):
        """
        Checks if coordinates are within the valid bounds.
        """
        if self.__class__.MIN_ABS_LATITUDE <= abs(float(latitude)) <= self.__class__.MAX_ABS_LATITUDE and
           self.__class__.MIN_ABS_LONGITUDE <= abs(float(longitude)) <= self.__class__.MAX_ABS_LONGITUDE:
            return True
        return False

    def _search_radius(self, radius):
        """
        Selects search radius between provided
        radius or maximum radius allowed.
        """
        if int(radius) <= self.__class__.MAX_RADIUS:
            return radius
        return str(self.__class__.MAX_RADIUS)

    @property
    def request_params(self):
        """
        Returns the Google Places API request parameters.
        """
        return self._request_params

    @property
    def api_key(self):
        """
        Returns the Google Places API key.
        """
        return self._api_key


class GooglePlacesSearchRequest(object):
    """
    Class to enable Google Places API search requests.
    """

    def __init__(self, service_url=None, params=None):
        """
        Initializes Google Places class.
        """
        self._service_url = service_url
        self._params = params

    def __str__(self):
        """
        Returns a string representation of class params.
        """
        queries = {'classname': self.__class__.__name__}
        for key, value in self.request_params.items():
            queries.update({'{}'.format(key): value})
        return str(queries)

    def fetch_json_response(self):
        """
        Retrieves a JSON object from a URL.
        """
        if self._service_url is not None and self._params is not None:
            response = self._search_request()
            request_url = response.url
            decoded_response = response.text.decode(encoding='utf-8')
            json_response = json.loads(decoded_response, parse_float=Decimal))
            return request_url, json_response
        else:
            raise GooglePlacesError('Search request params not provided.')

    def _search_request(self):
        """
        Retrieves a JSON object from a URL.
        """
        encoded_params = {}
        for key, value in self._params.items():
            if isinstance(value, str):
                value = value.encode(encoding='utf-8')
            encoded_params.update({key: value})

        response = requests.get(service_url, params=encoded_params)
        if response.status_code == requests.codes.ok:
            return response
        else:
            response.raise_for_status()

    @property
    def request_params(self):
        """
        Returns the Google Places API request parameters.
        """
        return self._request_params


class GooglePlacesSearchResponse(object):
    """
    Class to enable Google Places API JSON response treatment.
    """
    # Response status codes.
    STATUS_OK = 'OK'
    STATUS_ZERO_RESULTS = 'ZERO_RESULTS'
    STATUS_OVER_QUERY_LIMIT = 'OVER_QUERY_LIMIT'
    STATUS_REQUEST_DENIED = 'REQUEST_DENIED'
    STATUS_INVALID_REQUEST = 'INVALID_REQUEST'

    def __init__(self, request_url, response):
        """
        Initializes Google Places Search Result class.
        """
        self._request_url = request_url
        self._response = response
        self._places = []
        for place in response['results']:
            self._places.append(GooglePlacesResultPlace(place))
        self._html_attributions = response.get('html_attributions', None)
        self._next_page_token = response.get('next_page_token', None)

    def __str__(self):
        """
        Return a string representation of the number of results.
        """
        results = {
            'classname': self.__class__.__name__,
            'num_results': len(self.places),
        }
        return '<{classname} with {num_results} result(s)>'.format(**results)

    def _validate_response_status(self):
        """
        Validates the status from Google Places API JSON response.
        """
        response_success_status = [
            self.__class__.STATUS_OK,
            self.__class__.STATUS_ZERO_RESULTS,
        ]
        response_fail_status = [
            self.__class__.STATUS_OVER_QUERY_LIMIT,
            self.__class__.STATUS_REQUEST_DENIED,
            self.__class__.STATUS_INVALID_REQUEST,
        ]
        if self.response['status'] in response_success_status:
            msg = ('Successfull request to URL {} with status code: {}'.format(
                    self.request_url, self.response['status'])
            print(msg)
        elif self.response['status'] in response_fail_status:
            msg = ('Failed request to URL {} with status code: {}'.format(
                    self.request_url, self.response['status'])
            raise GooglePlacesError(msg)

    @property
    def request_url(self):
        """
        Returns the request url to Google Places API.
        """
        return self._request_url

    @property
    def response(self):
        """
        Returns the JSON response returned by Google Places API.
        """
        return self._response

    @property
    def places(self):
        """
        Returns the parsed response returned by Google Places API.
        """
        return self._places

    @property
    def html_attributions(self):
        """
        Returns the HTML attributions of the response.
        """
        return self._html_attributions

    @property
    def next_page_token(self):
        """
        Returns the next page token of the response.
        """
        return self._next_page_token


class GooglePlacesResponsePlace(object):
    """
    Class to represents a place from the results of JSON response.
    """
    def __init__(self, place):
        """
        Initializes Google Places Search Result class.
        """
        self._place = place
        self._icon = place.get('icon', None)
        self._place_id = place.get('place_id', None)
        self._geometry = place.get('geometry', None)
        self._name = place.get('name', None)
        self._rating = place.get('rating', None)
        self._reference = place.get('reference', None)
        self._types = place.get('types', None)
        self._formatted_address = place.get('formatted_address', None)

    def __str__(self):
        """
        Return a string representation of the place from the results.
        """
        place = {
            'classname': self.__class__.__name__,
            'place': str(self._place),
        }
        return '<{classname}:\nPlace from JSON response: {place}>'.format(**results)

    @property
    def place(self):
        """
        Returns the JSON response place from Google Places API.
        """
        return self._place

    @property
    def icon(self):
        """
        Returns the URL of a recommended icon for display.
        """
        return self._icon

    @property
    def place_id(self):
        """
        Returns the unique identifier for this place.
        """
        return self._place_id

    @property
    def geometry(self):
        """
        Returns the latitude and longitude geographical
        coordinates of the place.
        """
        location = self._geometry.get('location', None)
        if location is not None:
            self._latitude = location.get.('lat', None)
            self._longitude = location.get('lng', None)
            return self._latitude, self._longitude
        return self._geometry

    @property
    def name(self):
        """
        Returns the human-readable name of the place.
        """
        return self._name

    @property
    def rating(self):
        """
        Returns the place rating.
        """
        return self._rating

    @property
    def types(self):
        """
        Returns a list of feature types describing the given result.
        """
        return self._types

    @property
    def formatted_address(self):
        """
        Returns a string containing the human-readable address of this place.
        """
        return self._formatted_address


class GooglePlacesAttributes(object):
    """
    Class defining valid attributes lists
    for Google Places API parameters.
    """

    TYPES_DICT = {
        'ACCOUNTING': 'accounting',
        'AIRPORT': 'airport',
        'AMUSEMENT_PARK': 'amusement_park',
        'AQUARIUM': 'aquarium',
        'ART_GALLERY': 'art_gallery',
        'ATM': 'atm',
        'BAKERY': 'bakery',
        'BANK': 'bank',
        'BAR': 'bar',
        'BEAUTY_SALON': 'beauty_salon',
        'BICYCLE_STORE': 'bicycle_store',
        'BOOK_STORE': 'book_store',
        'BOWLING_ALLEY': 'bowling_alley',
        'BUS_STATION': 'bus_station',
        'CAFE': 'cafe',
        'CAMPGROUND': 'campground',
        'CAR_DEALER': 'car_dealer',
        'CAR_RENTAL': 'car_rental',
        'CAR_REPAIR': 'car_repair',
        'CAR_WASH': 'car_wash',
        'CASINO': 'casino',
        'CEMETERY': 'cemetery',
        'CHURCH': 'church',
        'CITY_HALL': 'city_hall',
        'CLOTHING_STORE': 'clothing_store',
        'CONVENIENCE_STORE': 'convenience_store',
        'COURTHOUSE': 'courthouse',
        'DENTIST': 'dentist',
        'DEPARTMENT_STORE': 'department_store',
        'DOCTOR': 'doctor',
        'ELECTRICIAN': 'electrician',
        'ELECTRONICS_STORE': 'electronics_store',
        'EMBASSY': 'embassy',
        'ESTABLISHMENT': 'establishment',
        'FINANCE': 'finance',
        'FIRE_STATION': 'fire_station',
        'FLORIST': 'florist',
        'FOOD': 'food',
        'FUNERAL_HOME': 'funeral_home',
        'FURNITURE_STORE': 'furniture_store',
        'GAS_STATION': 'gas_station',
        'GENERAL_CONTRACTOR': 'general_contractor',
        'GEOCODE': 'geocode',
        'GROCERY_OR_SUPERMARKET': 'grocery_or_supermarket',
        'GYM': 'gym',
        'HAIR_CARE': 'hair_care',
        'HARDWARE_STORE': 'hardware_store',
        'HEALTH': 'health',
        'HINDU_TEMPLE': 'hindu_temple',
        'HOME_GOODS_STORE': 'home_goods_store',
        'HOSPITAL': 'hospital',
        'INSURANCE_AGENCY': 'insurance_agency',
        'JEWELRY_STORE': 'jewelry_store',
        'LAUNDRY': 'laundry',
        'LAWYER': 'lawyer',
        'LIBRARY': 'library',
        'LIQUOR_STORE': 'liquor_store',
        'LOCAL_GOVERNMENT_OFFICE': 'local_government_office',
        'LOCKSMITH': 'locksmith',
        'LODGING': 'lodging',
        'MEAL_DELIVERY': 'meal_delivery',
        'MEAL_TAKEAWAY': 'meal_takeaway',
        'MOSQUE': 'mosque',
        'MOVIE_RENTAL': 'movie_rental',
        'MOVIE_THEATER': 'movie_theater',
        'MOVING_COMPANY': 'moving_company',
        'MUSEUM': 'museum',
        'NIGHT_CLUB': 'night_club',
        'PAINTER': 'painter',
        'PARK': 'park',
        'PARKING': 'parking',
        'PET_STORE': 'pet_store',
        'PHARMACY': 'pharmacy',
        'PHYSIOTHERAPIST': 'physiotherapist',
        'PLACE_OF_WORSHIP': 'place_of_worship',
        'PLUMBER': 'plumber',
        'POLICE': 'police',
        'POST_OFFICE': 'post_office',
        'REAL_ESTATE_AGENCY': 'real_estate_agency',
        'RESTAURANT': 'restaurant',
        'ROOFING_CONTRACTOR': 'roofing_contractor',
        'RV_PARK': 'rv_park',
        'SCHOOL': 'school',
        'SHOE_STORE': 'shoe_store',
        'SHOPPING_MALL': 'shopping_mall',
        'SPA': 'spa',
        'STADIUM': 'stadium',
        'STORAGE': 'storage',
        'STORE': 'store',
        'SUBWAY_STATION': 'subway_station',
        'SYNAGOGUE': 'synagogue',
        'TAXI_STAND': 'taxi_stand',
        'TRAIN_STATION': 'train_station',
        'TRAVEL_AGENCY': 'travel_agency',
        'UNIVERSITY': 'university',
        'VETERINARY_CARE': 'veterinary_care',
        'ZOO' 'zoo',
    }

    LANGUAGES_DICT = {
        'ARABIC': 'ar',
        'BASQUE': 'eu',
        'BENGALI': 'bn',
        'BULGARIAN': 'bg',
        'CATALAN': 'ca',
        'CHINESE_SIMPLIFIED': 'zh-CN',
        'CHINESE_TRADITIONAL': 'zh-TW',
        'CROATIAN': 'hr',
        'CZECH': 'cs',
        'DANISH': 'da',
        'DUTCH': 'nl',
        'ENGLISH': 'en',
        'ENGLISH_AUSTRALIAN': 'en-AU',
        'ENGLISH_GREAT_BRITAIN': 'en-GB',
        'FARSI': 'fa',
        'FINNISH': 'fi',
        'FILIPINO': 'fil',
        'FRENCH': 'fr',
        'GALICAIN': 'gl',
        'GERMAN': 'de',
        'GREEK': 'el',
        'GUJURATI': 'gu',
        'HEBREW': 'iw',
        'HINDI': 'hi',
        'HUNGARIAN': 'hu',
        'INDONESIAN': 'id',
        'ITALIAN': 'it',
        'JAPANESE': 'ja',
        'KANNADA': 'kn',
        'KOREAN': 'ko',
        'LATVIAN': 'lv',
        'LITHUANIAN': 'lt',
        'MALAYALAM': 'ml',
        'MARATHI': 'mr',
        'NORWEGIAN_NYNORSK': 'nn',
        'NORWEGIAN': 'no',
        'ORIYA': 'or',
        'POLISH': 'pl',
        'PORTUGUESE': 'pt',
        'PORTUGUESE_BRAZIL': 'pt-BR',
        'PORTUGUESE_PORTUGAL': 'pt-PT',
        'ROMANIAN': 'ro',
        'ROMANSCH': 'rm',
        'RUSSIAN': 'ru',
        'SERBIAN': 'sr',
        'SLOVAK': 'sk',
        'SLOVENIAN': 'sl',
        'SPANISH': 'es',
        'SWEDISH': 'sv',
        'TAGALOG': 'tl',
        'TAMIL': 'ta',
        'TELUGU': 'te',
        'THAI': 'th',
        'TURKISH': 'tr',
        'UKRANIAN': 'uk',
        'VIETNAMESE': 'vi',
    }

    @classmethod
    def types_list(self):
        """
        Returns a dictionary containing allowed types.
        """
        return self.__class__.TYPES_DICT

    @classmethod
    def languages_dict(self):
        """
        Returns a dictionary containing allowed languages.
        """
        return self.__class__.LANGUAGES_DICT
