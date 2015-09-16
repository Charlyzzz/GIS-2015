# coding: utf-8
import math
from collections import OrderedDict

import geomag
from bottle import get, run, request

Radio_Medio = 6371.0 * 1000
Radio_Ecuat = 6378.1 * 1000
Radio_Polar = 6356.8 * 1000
Orbita_Geo = 35786.0 * 1000
Foot = 0.3048
Satellites = {'AR1': -71.8, 'AR2': -81.0}
Geocoding_Key = 'AIzaSyC8agUhPelme7iIcLiQcNJJqcY8Ke7Jg_8'


class SatError(Exception):
    pass


def google_geocode(address):
    """ dada una dirección, devuelve dirección obtenida, latitud, longitud """

    # georreferenciar una dirección usando Google Apis (o cualquier otra), considerar las siguientes excepciones:
    #      raise SatError("La dirección no pudo ser resuelta por Google")
    #       raise SatError("Falló conexión a Google Geocode API")
    return formatted_address, latitud, longitud


def google_elevation(lat, lng):
    """ dada la latitud y longitud, devuelve elevacion en metros """

    # obtener la elevación usando Google Apis (o cualquier otra), considerar las siguientes excepciones:
    #       raise SatError("La altura no pudo ser resuelta por Google")
    #       raise SatError("Falló conexión a Google Elevation API")
    return elevation


def convert_float(name, s, min_value, max_value):
    try:
        value = float(s)
        if min_value <= value <= max_value:
            return value
        else:
            raise SatError("El parámetro '%s' debe estar en el rango [%4.0f, %4.0f]" % (name, min_value, max_value))
    except ValueError:
        raise SatError("El parámetro '%s' no es válido" % name)


def radio_elipse(s, a, b):
    """ Forma polar centrada en origen, angulo en radianes """
    return 1 / math.sqrt((math.cos(s) ** 2 / a ** 2) + (math.sin(s) ** 2 / b ** 2))


def norma_eucl(a, b):
    """ Calcula la distancia entre dos puntos n-dimensionales """
    return math.sqrt(sum([(x - y) ** 2 for x, y in zip(a, b)]))


def satellite_finder(params):
    # si la dirección viene definida, se obtiene latitud y longitud via Google API
    if params.address:
        address, lat, lng = google_geocode(params.address)

    # si no hay dirección, lat/lng son obligatorios
    elif params.lat and params.lng:
        address = None
        lat = convert_float('lat', params.lat, -90, 90)
        lng = convert_float('lng', params.lng, -180, 180)
    else:
        raise SatError("Alguno de los parámetros 'address' o 'lat/lng' tiene que estar definido")

    # si la altura no viene definida, se obtiene via Google API
    if params.alt:
        alt = convert_float('alt', params.alt, -500, 9000)
    else:
        alt = google_elevation(lat, lng)

    # obtiene la longitud del satélite (su latitud es cero)
    if params.sat:
        sat = Satellites.get(params.sat.upper(), None)
        if not sat:
            sat = convert_float('sat', params.sat, -180, 180)
    else:
        raise SatError("El parámetro 'sat' tiene que estar definido")

    # obtiene declinación magnética, en grados
    magn = geomag.declination(lat, lng, alt / Foot)

    # cálculo de coordenadas antena (x, y, z)
    lat_rad = math.radians(lat)
    r_ant = radio_elipse(lat_rad, Radio_Ecuat, Radio_Polar) + alt
    coord_ant = r_ant * math.cos(lat_rad), 0, r_ant * math.sin(lat_rad)

    # cálculo de coordenadas satélite (x, y, z)
    lng_rad = math.radians(lng - sat)
    r_sat = Radio_Ecuat + Orbita_Geo
    coord_sat = r_sat * math.cos(lng_rad), r_sat * math.sin(lng_rad), 0

    # cálculo de distancia al satélite, en km
    distance = norma_eucl(coord_ant, coord_sat) / 1000

    # cálculo de azimut y elevacion, en grados
    azimuth = 180 + math.degrees(math.atan2(math.tan(lng_rad), math.sin(lat_rad)))
    alfa = math.sqrt((r_sat * math.cos(lng_rad) - r_ant * math.cos(lat_rad)) ** 2 + r_sat ** 2 * math.sin(
        lng_rad) ** 2 + r_ant ** 2 * math.sin(lat_rad) ** 2)
    elevation = math.degrees(math.asin((r_sat * math.cos(lng_rad) * math.cos(lat_rad) - r_ant) / alfa))

    return OrderedDict([('address', address), ('lat', '%7.4f' % lat), ('lng', '%7.4f' % lng),
                        ('alt', '%5.1f' % alt), ('sat', '%5.1f' % sat), ('distance', '%5.1f' % distance),
                        ('elevation', '%5.2f' % elevation), ('azimuth_true', '%5.2f' % azimuth),
                        ('azimuth_magn', '%5.2f' % (azimuth - magn))])


@get(r'/ubicar')
def ubicar():
    """ Parámetros:
        address: dirección de la antena, tiene prioridad sobre lat/lng
        lat/lng: latitud y longitud de la antena, en grados
        alt: altura sobre el nivel de mar; con nulo resuelve vía Google, usar cero para no utilizar
        sat: longitud del satélite, en grados; también acepta 'AR1', 'AR2' y 'AMC6'
    """
    try:
        return satellite_finder(request.params)
    except Exception as e:
        return {'error': e.args[0].replace('ERROR: ', '')}


if __name__ == "__main__":
    # si funciona por favor ejecutar enviar el resultado de poner en el navegador:
    #       localhost:8080/ubicar?address=bariloche&sat=ar1
    run(host = '0.0.0.0', port = 8080)
