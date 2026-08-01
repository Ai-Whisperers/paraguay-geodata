#!/usr/bin/env python3
"""py_city_to_depto.py — Minimal reference table for the most common cities
in the Paraguay property listings corpus.  Used by tools/merge_fresh_sources
to fill in state_province before the canonicalizer runs.

Each entry: city name → canonical depto.  Cities not in this table get
state_province=None (which the canonicalizer flags as 'unknown_depto').
"""
from __future__ import annotations

CITY_TO_DEPTO: dict[str, str] = {
    # Asunción (Capital District)
    "Asunción": "Asunción",
    # Central
    "Luque": "Central", "San Lorenzo": "Central", "Capiatá": "Central",
    "Lambaré": "Central", "Fernando de la Mora": "Central",
    "Mariano Roque Alonso": "Central", "Limpio": "Central", "Ñemby": "Central",
    "San Antonio": "Central", "Itauguá": "Central", "Areguá": "Central",
    "Ypané": "Central", "Villa Elisa": "Central", "Guarambaré": "Central",
    "Itá": "Central", "J. Augusto Saldívar": "Central", "Ypacaraí": "Central",
    "Villeta": "Central",
    # Cordillera
    "Caacupé": "Cordillera", "San Bernardino": "Cordillera", "Piribebuy": "Cordillera",
    "Eusebio Ayala": "Cordillera", "Tobatí": "Cordillera", "Atyrá": "Cordillera",
    "Altos": "Cordillera", "Arroyos y Esteros": "Cordillera",
    # Alto Paraná
    "Ciudad del Este": "Alto Paraná", "Presidente Franco": "Alto Paraná",
    "Hernandarias": "Alto Paraná", "Minga Guazú": "Alto Paraná",
    "Santa Rita": "Alto Paraná", "Itaipulandia": "Alto Paraná",
    # Itapúa
    "Encarnación": "Itapúa", "Hohenau": "Itapúa", "Obligado": "Itapúa",
    "Bella Vista": "Itapúa", "Cambyretá": "Itapúa", "Capitán Miranda": "Itapúa",
    "Coronel Bogado": "Itapúa", "San Juan del Paraná": "Itapúa",
    # Misiones
    "San Ignacio": "Misiones", "San Juan Bautista": "Misiones", "Ayolas": "Misiones",
    "Santa María": "Misiones", "San Miguel": "Misiones",
    # Paraguarí
    "Paraguarí": "Paraguarí", "Carapeguá": "Paraguarí", "Yaguarón": "Paraguarí",
    "Pirayú": "Paraguarí", "Acahay": "Paraguarí",
    # Caaguazú
    "Coronel Oviedo": "Caaguazú", "Caaguazú": "Caaguazú", "Juan Eulogio Estigarribia": "Caaguazú",
    "Repatriación": "Caaguazú",
    # Caazapá
    "Caazapá": "Caazapá", "San Juan Nepomuceno": "Caazapá", "Yuty": "Caazapá",
    # Guairá
    "Villarrica": "Guairá", "Iturbe": "Guairá", "Borja": "Guairá",
    "Mbocayaty": "Guairá",
    # San Pedro
    "San Pedro de Ycuamandiyú": "San Pedro", "Santa Rosa del Aguaray": "San Pedro",
    "Chore": "San Pedro", "Lima": "San Pedro", "San Estanislao": "San Pedro",
    # Concepción
    "Concepción": "Concepción", "Horqueta": "Concepción", "Yby Yaú": "Concepción",
    "Loreto": "Concepción",
    # Amambay
    "Pedro Juan Caballero": "Amambay", "Capitán Bado": "Amambay",
    # Canindeyú
    "Saltos del Guairá": "Canindeyú", "Curuguaty": "Canindeyú",
    "La Paloma": "Canindeyú", "Villa Ygatimí": "Canindeyú",
    # Ñeembucú
    "Pilar": "Ñeembucú", "Alberdi": "Ñeembucú", "Humaitá": "Ñeembucú",
    # Presidente Hayes
    "Villa Hayes": "Presidente Hayes", "Pozo Colorado": "Presidente Hayes",
    "Benjamin Aceval": "Presidente Hayes", "Nanawa": "Presidente Hayes",
    # Boquerón
    "Filadelfia": "Boquerón", "Loma Plata": "Boquerón", "Mariscal Estigarribia": "Boquerón",
    # Alto Paraguay
    "Fuerte Olimpo": "Alto Paraguay", "Bahía Negra": "Alto Paraguay",
    "Carmelo Peralta": "Alto Paraguay",
}


def depto_for_city(city: str | None) -> str | None:
    if not city:
        return None
    return CITY_TO_DEPTO.get(city.strip())