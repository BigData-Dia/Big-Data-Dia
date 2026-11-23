import importlib.util
import json
import unittest
from pathlib import Path

from promociones import clasificar_promocion, extraer_promociones


class PromocionesTest(unittest.TestCase):
    def test_condiciones(self):
        self.assertEqual(clasificar_promocion('2X1 EN LECHE')['tipo'], '2x1')
        p = clasificar_promocion('2ª UD AL 50% EN GALLETAS')
        self.assertEqual((p['tipo'], p['unidad_descontada']), ('descuento_unidad', 2))
        self.assertEqual(clasificar_promocion('20% DTO')['descuento_porcentaje'], 20)
        self.assertEqual(clasificar_promocion('SOLO A 0,99 EUROS')['importe_centimos'], 99)
        p = clasificar_promocion('2 UDS. POR SÓLO 4 EUR')
        self.assertEqual((p['tipo'], p['importe_centimos']), ('precio_por_lote', 400))

    def test_club_multicompra_no_inventa_precio(self):
        p = extraer_promociones({'prices': {'price': 4.99, 'is_club_price': False,
                                           'is_promo_price': False},
            'promotions': [{'description': '3X2 EN TURRONES', 'only_club_dia': True}]})
        self.assertTrue(p['es_promo_club_dia'])
        self.assertEqual(p['tipo_promo_club'], '3x2')
        self.assertIsNone(p['precio_club_centimos'])

    def test_precio_club_y_ausencias(self):
        p = extraer_promociones({'prices': {'price': 0.99, 'is_club_price': True,
                                           'is_promo_price': True}})
        self.assertEqual(p['precio_club_centimos'], 99)
        self.assertIsNone(p['precio_promo_centimos'])
        self.assertIsNone(extraer_promociones({})['es_promo_club_dia'])


if __name__ == '__main__':
    unittest.main()
