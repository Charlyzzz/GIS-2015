# coding: utf-8
from bottle import get, run, request

from satelite import satellite_finder


@get('/ubicar')
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
        return 'Error: ' + e.args[0].replace('ERROR: ', '')


run(reloader = True)

if __name__ == "__main__":
    # si funciona por favor ejecutar enviar el resultado de poner en el navegador:
    #       localhost:8080/ubicar?address=bariloche&sat=ar1
    run(host = '0.0.0.0', port = 8080)
