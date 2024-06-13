import unittest
from unittest.mock import patch, mock_open, MagicMock
import requests
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
import csv

# Definición de las clases y métodos
class Coordenada:
    def __init__(self, latitud, longitud):
        self.latitud = latitud
        self.longitud = longitud

    def getLatitud(self):
        return self.latitud

    def getLongitud(self):
        return self.longitud

class Ciudad:
    def __init__(self, nombrePais, nombreCiudad):
        self.nombrePais = nombrePais
        self.nombreCiudad = nombreCiudad

    def getPais(self):
        return self.nombrePais

    def getCiudad(self):
        return self.nombreCiudad

class servicioConCSV:
    def __init__(self, csv_path):
        self.csv_path = csv_path

    def obtenerCoordenadas(self, ciudad: Ciudad) -> Coordenada:
        df = pd.read_csv(self.csv_path)
        df_ciudad = df[(df['city_ascii'] == ciudad.nombreCiudad) & (df['country'] == ciudad.nombrePais)]
        if not df_ciudad.empty:
            latitud = df_ciudad.iloc[0]['lat']
            longitud = df_ciudad.iloc[0]['lng']
            return Coordenada(latitud, longitud)
        else:
            raise ValueError("No existe la ciudad en el CSV")

class servicioConAPi:
    def obtenerCoordenadas(self, ciudad: Ciudad) -> Coordenada:
        nombreCiudad = ciudad.nombreCiudad.lower()
        nombrePais = ciudad.nombrePais.lower()
        headers = {
            "User-Agent": "ActividadSemana09/1.0"
        }
        url = f"https://nominatim.openstreetmap.org/search?q={nombreCiudad},{nombrePais}&format=json"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
                if data:
                    latitud = float(data[0]['lat'])
                    longitud = float(data[0]['lon'])
                    return Coordenada(latitud, longitud)
                else:
                    raise ValueError("Ciudad no encontrada mediante la API")
            except ValueError:
                raise ValueError("Error al procesar la respuesta de la API")
        else:
            raise ValueError("Error en la solicitud a la API")

def distHaversine(coord1: Coordenada, coord2: Coordenada) -> float:
    if coord1 == coord2:
        raise ValueError("Las coordenadas no pueden ser las mismas para calcular la distancia.")
    
    R = 6371  # radio de la tierra en km
    lat1, lon1 = radians(coord1.getLatitud()), radians(coord1.getLongitud())
    lat2, lon2 = radians(coord2.getLatitud()), radians(coord2.getLongitud())

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


# Tests
class TestCityDistance(unittest.TestCase):

    def setUp(self):
        self.city1 = Ciudad("España", "Madrid")
        self.city2 = Ciudad("España", "Barcelona")
        self.city_nonexistent = Ciudad("Atlantis", "Atlantis")
        self.coordenada1 = Coordenada(40.4168, -3.7038)
        self.coordenada2 = Coordenada(41.3851, 2.1734)
        self.csv_service = servicioConCSV("worldcities.csv")
        self.api_service = servicioConAPi()
    
    # Verificar que se inicialicen de manera correcta
    def test_classes_initialization(self):
        self.assertEqual(self.city1.getCiudad(), "Madrid")
        self.assertEqual(self.city2.getCiudad(), "Barcelona")
        self.assertEqual(self.coordenada1.getLatitud(), 40.4168)
        self.assertEqual(self.coordenada1.getLongitud(), -3.7038)

    # Verificar que el status code sea 200
    @patch('requests.get')
    def test_api_status_code(self, mock_get):
        # Simulación de la respuesta de la API
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{
            'lat': '35.6895',
            'lon': '139.6917'
        }]

        # Prueba para verificar el método obtenerCoordenadas de servicioConAPi
        ciudad = Ciudad("Japan", "Tokyo")
        servicio_api = servicioConAPi()
        coordenada = servicio_api.obtenerCoordenadas(ciudad)

        # Verificar que la URL y los headers se generaron correctamente
        expected_url = "https://nominatim.openstreetmap.org/search?q=tokyo,japan&format=json"
        expected_headers = {
            "User-Agent": "ActividadSemana09/1.0"
        }
        mock_get.assert_called_once_with(expected_url, headers=expected_headers)

        # Verificar que el status code es 200
        self.assertEqual(mock_get.return_value.status_code, 200)

    # Verificar que se lea el csv
    @patch('pandas.read_csv')
    def test_csv_path(self, mock_read_csv):
        # Simular los datos del CSV
        mock_read_csv.return_value = pd.DataFrame({
            'city_ascii': ['Madrid'],
            'country': ['España'],
            'lat': [40.4168],
            'lng': [-3.7038]
        })

        ciudad = Ciudad("España", "Madrid")
        servicio_csv = servicioConCSV("worldcities.csv")
        coordenada = servicio_csv.obtenerCoordenadas(ciudad)

        # Verificar que la función read_csv fue llamada con la ruta correcta
        mock_read_csv.assert_called_with("worldcities.csv")

        # Verificar que las coordenadas obtenidas son correctas
        self.assertEqual(coordenada.getLatitud(), 40.4168)
        self.assertEqual(coordenada.getLongitud(), -3.7038)

    # Verificar que la ciudad existe
    def test_ciudadExiste(self):
        data = {'city_ascii': ['Madrid', 'Barcelona'], 'country': ['España', 'España'], 'lat': [40.4168, 41.3851], 'lng': [-3.7038, 2.1734]}
        df = pd.DataFrame(data)
        with patch('pandas.read_csv', return_value=df):
            coord = self.csv_service.obtenerCoordenadas(self.city1)
            self.assertEqual(coord.getLatitud(), 40.4168)
            self.assertEqual(coord.getLongitud(), -3.7038)

    # Verificar que la distancia calculada sea correcta
    def test_distance_calculation(self):
        distance = distHaversine(self.coordenada1, self.coordenada2)
        expected_distance = 505.68  # Distancia esperada entre Madrid y Barcelona en km
        self.assertAlmostEqual(distance, expected_distance, delta=5)

    # Verificar que no sea la misma ciudad
    def test_same_city(self):
        with self.assertRaises(ValueError):
            distHaversine(self.coordenada1, self.coordenada1)

    # Verificar el result_label
    def test_result_label(self):
        result_label = f"Distancia entre {self.city1.getCiudad()} y {self.city2.getCiudad()}: 505.68 km"
        self.assertEqual(result_label, "Distancia entre Madrid y Barcelona: 505.68 km")

if __name__ == '__main__':
    unittest.main()
