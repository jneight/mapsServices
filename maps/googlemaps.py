#coding=utf-8


from httplib2 import Http
try:
    import json as simplejson
except:
    from django.utils import simplejson
import urllib


class MapsAPIError(Exception):
    def __init__(self, type, message=''):
        Exception.__init__(self, message)
        self.type = type

class MapsRequest(Http):
    _reverse_url = 'http://maps.googleapis.com/maps/api/geocode/json?'
    headers = { 'User-Agent' : 'Georemindme:0.1' }

    def get_address(self, location, sensor=False):
        url = self._reverse_url + 'latlng=%f,%f&sensor=%s' % (location.lat,
                                                    location.lon,
                                                    ('true' if sensor else 'false')
                                                    )
        return self._do_request(url)

    def get_coords(self, address, sensor=False):
        url = self._reverse_url + 'address=%s&sensor=%s' % (
            urllib.quote_plus(address),
            ('true' if sensor else 'false'))
        return self._do_request(url)

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
            raise MapsAPIError(response['status'], content)
        json = simplejson.loads(content)
        return json