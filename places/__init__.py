# coding=utf-8

__author__ = "Javier Cordero Martinez (javier@georemindme.com)"
__copyright__ = "Copyright 2011"
__contributors__ = []
__license__ = "AGPLv3"
__version__ = "0.2"


import httplib2
import urllib
from xml.etree import ElementTree

from django.utils import simplejson


class GPAPIError(Exception):
    def __init__(self, typ, message=''):
        super(Exception, self).__init__(self, message)
        self.type = typ

class GPRequest(httplib2.Http):
    '''
        encapsulates the queries
    '''
    _search_url = 'https://maps.googleapis.com/maps/api/place/search/json?'
    _details_url = 'https://maps.googleapis.com/maps/api/place/details/json?'
    _checkin_url = 'https://maps.googleapis.com/maps/api/place/check-in/json?'
    _add_url = 'https://maps.googleapis.com/maps/api/place/add/json?'
    _delete_url = 'https://maps.googleapis.com/maps/api/place/delete/json?'
    _geocode_url = 'http://maps.google.com/maps/api/geocode/json'
    
    headers = { 'User-Agent' : 'GeoRemindMe:0.2' }

    
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        from django.conf import settings
        self.key = settings.GOOGLE_API_PASSWORD['google_places']


    def do_search(self, pos, radius=500, types=None, language=None, name=None, sensor=False):
        """
            Realiza una busqueda en Google Places. Añade '_url' a cada resultado con la direccion para acceder
            a nuestra informacion del sitio. Si commit es True, los resultados con ids que no existan en la BD
            seran añadidos
            
                :param pos: posicion a buscar
                :type pos: :class:`db.GeoPt`
                :param radius: radio para hacer las busquedas
                :type radius: integer
                :param types: tipos de lugares a buscar
                :type types: list
                :param language: idioma para mostrar los resultados
                :type language: string
                :param name: nombre del lugar a buscar
                :type name: string
                :param sensor: indicar si la posicion se obtiene con algun sensor (GPS, ...)
                :type sensor: boolean
                :param commit: Indicar si se debe añadir los resultados que no existan a la BD
                :type commit: boolean
                
                :returns: diccionario con los resultados
                :raises: :class:`GPAPIError`
        """                
        url = 'location=%s,%s&radius=%s' % (pos.lat, pos.lon, radius)
        if types is not None:
            if type(types) != type(list()):
                types = list(types)
            types = '|'.join(types)
            url = url + '&types=%s' % types
        if language is not None:
            url = url + '&language=%s' % language
        if name is not None:
            url = url + '&name=%s' % self._parse_get(name)
        url = url + '&sensor=%s&key=%s' % ('true' if sensor else 'false', self.key)
        url = self._search_url + url
        return self._do_request(url)
    
    def retrieve_reference(self, reference, language='es', sensor=False):
        """
            Realiza una busqueda en Google Places de un lugar concreto. Añade '_url'
            al resultado con nuestra url al lugar
            
                :param pos: posicion a buscar
                :type pos: :class:`db.GeoPt`
                :param language: idioma para mostrar los resultados
                :type language: string
                :param sensor: indicar si la posicion se obtiene con algun sensor (GPS, ...)
                :type sensor: boolean
                
                :returns: diccionario con los resultados
                :raises: :class:`GPAPIError`
        """ 
        url = self._details_url + 'reference=%s' % reference
        if language is not None:
            url = url + '&language=%s' % language
        url = url + '&sensor=%s&key=%s' % ('true' if sensor else 'false', self.key)
        return self._do_request(url)
    
    def do_checkin(self, reference, sensor = True):
        url = self._checkin_url + 'sensor=%s&key=%s' % ('true' if sensor else 'false', self.key)
        return self._do_request(url, method='POST', body='reference: %s' % reference)
    
#    def add_place(self, location, accuracy, name, types, language='en-EN', sensor=False):
#        from google.appengine.ext.db import GeoPt
#        if not isinstance(location, GeoPt):
#            location = GeoPt(location)
#        body = urllib.urlencode({
#                'location': { 
#                                'lat': location.lat,
#                                'lng': location.lon,
#                            },
#                'accuracy': accuracy,
#                'name': name,
#                'language': language,
#                })
#        if types is not None:
#            dict['types'] = types
#        url = self._add_url + self._parse_get('&sensor=%s&key=%s' % ('true' if sensor else 'false', self.key))
#        return self._do_request(url, method='POST', body=body)
    
    def delete_place(self, reference, sensor = False):
        body = urllib.urlencode({'reference': str(reference)})
        url = self._delete_url + '&sensor=%s&key=%s' % ('true' if sensor else 'false', self.key)
        return self._do_request(url, method='POST', body=body)

    def _do_request(self, url, method='GET', body=None):
        """
            Realiza una peticion por GET a la direccion recibida
            
                :param url: direccion url a donde hacer la peticion
                :type url: string
                
                :returns: diccionario con el resultado
                :raises: :class:`GPAPIError`
        """
        response, content = self.request(url, method=method, body=body, headers=self.headers)
        if int(response['status']) != 200:
            raise GPAPIError(response['status'], 'ERROR IN REQUEST')
        json = simplejson.loads(content)
        return json
    
    def _parse_get(self, string):
        from urllib import quote_plus
        return quote_plus(string)
    

    def geocode(self, address, sensor="false", **geo_args):
        geo_args.update({
            'address': address,
            'sensor': sensor  
        })
    
        url = self.geocode_url + '?' + urllib.urlencode(geo_args)
        result = simplejson.load(urllib.urlopen(url))
        return simplejson.dumps([s['formatted_address'] for s in result['results']], indent=2)
    
    def _get_city(self, components):
        if components is None:
            return None
        for i in components:
            if 'locality' in i['types']:
                return i['long_name'].split(',')[0]

    def _get_region(self, components):
        if components is None:
            return None
        for i in components:
            if 'administrative_area_level_1' in i['types']:
                return { 'name': i['long_name'],
                         'code': i['short_name']
                     }       

    def _get_country(self, components):
        if components is None:
            return None
        for i in components:
            if 'country' in i['types']:
                return { 'name': i['long_name'],
                         'code': i['short_name']
                     }