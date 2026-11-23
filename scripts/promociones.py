"""Promociones publicadas por DIA; importes monetarios en céntimos."""

import re
from decimal import Decimal, ROUND_HALF_UP


def centimos(value):
    if value is None:
        return None
    return int((Decimal(str(value).replace(',', '.')) * 100).quantize(
        Decimal('1'), rounding=ROUND_HALF_UP))


def clasificar_promocion(description):
    """Interpreta solo patrones explícitos y conserva siempre el texto original."""
    text = description.upper()
    result = {'tipo': 'otra', 'descripcion': description,
              'descuento_porcentaje': None, 'unidades_requeridas': None,
              'unidades_pagadas': None, 'importe_centimos': None,
              'unidad_descontada': None}
    multi = re.search(r'\b(\d+)\s*[X×]\s*(\d+)\b', text)
    percent = re.search(r'(\d+(?:[.,]\d+)?)\s*%', text)
    nth = re.search(r'\b(\d+)\s*[ªºA]?\s*(?:UDS?\.?|UNIDAD)', text)
    bundle = re.search(
        r'\b(\d+)\s*UDS?\.?\s*(?:POR\s*)?(?:A\s*)?(?:S[ÓO]LO\s*)?'
        r'(\d+(?:[.,]\d+)?)\s*(?:EUROS?|EUR\b|€)', text)
    fixed = re.search(
        r'\b(?:S[ÓO]LO\s+)?A\s+(\d+(?:[.,]\d+)?)\s*(?:EUROS?|EUR\b|€)', text)
    if multi:
        bought, paid = map(int, multi.groups())
        result.update(tipo=f'{bought}x{paid}', unidades_requeridas=bought,
                      unidades_pagadas=paid)
    elif percent:
        result.update(tipo='descuento_unidad' if nth else 'descuento_porcentaje',
                      descuento_porcentaje=float(percent[1].replace(',', '.')),
                      unidad_descontada=int(nth[1]) if nth else None)
    elif bundle:
        result.update(tipo='precio_por_lote', unidades_requeridas=int(bundle[1]),
                      importe_centimos=centimos(bundle[2]))
    elif fixed:
        result.update(tipo='precio_fijo', importe_centimos=centimos(fixed[1]))
    return result


def extraer_promociones(item):
    prices = item.get('prices') or {}
    promotions = []
    for raw in item.get('promotions') or []:
        promotion = clasificar_promocion(raw.get('description') or '')
        promotion.update(codigo=raw.get('code'),
                         solo_club_dia=raw.get('only_club_dia'),
                         exclusiva_online=raw.get('exclusive_online'),
                         url=raw.get('url'))
        promotions.append(promotion)

    general = [p for p in promotions if p['solo_club_dia'] is False]
    club = [p for p in promotions if p['solo_club_dia'] is True]
    is_club = prices.get('is_club_price')
    is_promo = prices.get('is_promo_price')
    # Las ofertas por varias unidades no implican un precio individual rebajado.
    general_price = is_promo is True and is_club is False
    club_price = is_club is True

    def summary(group, key):
        values = list(dict.fromkeys(p[key] for p in group if p[key] is not None))
        return values[0] if len(values) == 1 else None

    return {
        'precio_centimos': centimos(prices.get('price')),
        'precio_anterior_centimos': centimos(prices.get('strikethrough_price')),
        'precio_referencia_centimos': centimos(prices.get('price_per_unit')),
        'unidad_precio_referencia': prices.get('measure_unit'),
        'moneda': prices.get('currency'),
        'es_promo': True if general or general_price else (
            False if is_promo is False or is_club is True else None),
        'es_promo_club_dia': True if club or club_price else is_club,
        'precio_promo_centimos': centimos(prices.get('price')) if general_price else None,
        'precio_club_centimos': centimos(prices.get('price')) if club_price else None,
        'tipo_promo': summary(general, 'tipo'),
        'descripcion_promo': ' | '.join(p['descripcion'] for p in general) or None,
        'descuento_porcentaje': summary(general, 'descuento_porcentaje'),
        'tipo_promo_club': summary(club, 'tipo'),
        'descripcion_promo_club': ' | '.join(p['descripcion'] for p in club) or None,
        'descuento_porcentaje_club': summary(club, 'descuento_porcentaje'),
        'promociones': promotions,
    }
