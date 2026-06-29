#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json
import gzip
import shutil
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta, datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

## OBTENER LISTA DE CANALES

arregloCanales = []

with open('json_Zapopan_Julio_03_2025.json', encoding="latin-1") as f:
    json_data = json.load(f)
    Informacion = json_data['chs']
    for Canales in Informacion:
        try:
            ChImg = "https://www.izzigo.tv/images/" + Canales['loc'][0]['img']['dir'] + "/LOGO/m/0"
        except KeyError:
            ChImg = "https://www.izzigo.tv/webclient/img/channel_no_logo.svg"

        arregloCanales.append([
            int(Canales['ord']),
            Canales['loc'][0]['nam'],
            Canales['sid'],
            "izzitv",
            ChImg,
        ])

arregloCanales.sort()

def gzip_file(input_file, output_file):
    print(f"Starting compression of '{input_file}'...")
    if not os.path.exists(input_file):
        print(f"Error: The file '{input_file}' does not exist.")
        return
    with open(input_file, 'rb') as f_in:
        with gzip.open(output_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print(f"Compression complete! Gzipped file created: '{output_file}'")
    print(f"Original size: {os.path.getsize(input_file)} bytes")
    print(f"Gzipped size: {os.path.getsize(output_file)} bytes")
    print("Compression ratio: {:.2f}%".format(
        (1 - os.path.getsize(output_file) / os.path.getsize(input_file)) * 100
    ))

def estrellas_rate(estrellas):
    if estrellas == 0:
        return "☆☆☆☆☆"
    elif estrellas == 1:
        return "★☆☆☆☆"
    elif estrellas == 2:
        return "★★☆☆☆"
    elif estrellas == 3:
        return "★★★☆☆"
    elif estrellas == 4:
        return "★★★★☆"
    elif estrellas == 5:
        return "★★★★★"
    return "☆☆☆☆☆"

def formato_fecha_xmltv(iso_z, fallback):
    try:
        datetimeObj = datetime.strptime(iso_z, "%Y-%m-%dT%H:%M:%SZ")
        return datetimeObj.strftime("%Y%m%d%H%M%S") + " +0000"
    except (TypeError, ValueError, KeyError):
        return fallback

def evento_a_programa(Evento):
    try:
        CanalID = Evento['sid']
    except KeyError:
        CanalID = 0

    TituloProgramaTv = ""
    try:
        isLive = Evento.get('liv', Evento.get('rep'))
        if isLive is False:
            TituloProgramaTv = "🔴 ᵛᶦᵛᵒ "
    except KeyError:
        TituloProgramaTv = ""

    try:
        isNew = Evento['new']
        if isNew:
            TituloProgramaTv = TituloProgramaTv + "[ESTRENO] "
    except KeyError:
        pass

    try:
        TituloProgramaTv = TituloProgramaTv + Evento['con']['oti']
    except KeyError:
        TituloProgramaTv = "No disponible"

    try:
        TemporadaProgramaTv = 'Temporada: ' + str(Evento['con']['sea']) + ' | '
    except KeyError:
        TemporadaProgramaTv = ""

    try:
        EpisodioProgramaTv = 'Episodio: ' + str(Evento['con']['scn']) + ' | '
    except KeyError:
        EpisodioProgramaTv = ""

    try:
        SubTituloProgramaTv = Evento['con']['loc'][0]['cti']
    except KeyError:
        SubTituloProgramaTv = ""

    try:
        ImagenProgramaTv = Evento['con']['loc'][0]['img']['dir']
    except KeyError:
        ImagenProgramaTv = ""

    RepeticionProgramaTv = ""

    try:
        DescripcionProgramaTv = Evento['con']['loc'][0]['syn']
    except KeyError:
        DescripcionProgramaTv = "Sin descripción"

    try:
        TestCategoriaProgramaTv = Evento['con']['categories']
        if TestCategoriaProgramaTv:
            CategoriaProgramaTv = TestCategoriaProgramaTv[-1]
        else:
            CategoriaProgramaTv = "izzi.tv"
    except KeyError:
        CategoriaProgramaTv = "izzi.tv"

    try:
        ParentalProgramaTv = Evento['con']['par']
    except KeyError:
        ParentalProgramaTv = 0

    try:
        EstrellasProgramaTv = Evento['con']['str']
        EstrellasRate = estrellas_rate(EstrellasProgramaTv)
    except KeyError:
        EstrellasProgramaTv = 0
        EstrellasRate = "☆☆☆☆☆"

    try:
        FechaProgramaTV = Evento['con']['oda']
    except KeyError:
        FechaProgramaTV = 2021

    PaisProgramaTv = "MEX"

    ComienzoProgramaTv = formato_fecha_xmltv(Evento.get('sta'), "00000000000000 +0000")
    TerminacionProgramaTv = formato_fecha_xmltv(Evento.get('end'), "20210301223000 +0000")

    if "Sport" in CategoriaProgramaTv and SubTituloProgramaTv:
        if "🔴 ᵛᶦᵛᵒ" in TituloProgramaTv:
            TituloProgramaTv = TituloProgramaTv.replace("🔴 ᵛᶦᵛᵒ ", "")
            SubTituloProgramaTv = "🔴 ᵛᶦᵛᵒ " + SubTituloProgramaTv
        TemporadaProgramaTv = TituloProgramaTv + ' | ' + TemporadaProgramaTv
        TempSubTitulo = SubTituloProgramaTv
        SubTituloProgramaTv = TituloProgramaTv
        TituloProgramaTv = TempSubTitulo

    ExtraDescripcion = (
        str(TemporadaProgramaTv) + str(EpisodioProgramaTv) + str(RepeticionProgramaTv)
        + str(CategoriaProgramaTv) + ' | ' + str(FechaProgramaTV) + ' | '
        + str(PaisProgramaTv) + ' | +' + str(ParentalProgramaTv) + ' | ' + str(EstrellasRate) + '\n'
    )

    programa = {
        "channel": "IzzI." + str(CanalID),
        "start": ComienzoProgramaTv,
        "stop": TerminacionProgramaTv,
        "title": {"lang": "es", "value": TituloProgramaTv},
        "desc": {"lang": "es", "value": ExtraDescripcion + DescripcionProgramaTv},
        "date": str(FechaProgramaTV),
        "country": PaisProgramaTv,
        "category": {"lang": "es", "value": CategoriaProgramaTv},
        "rating": {"system": "MEX", "value": str(ParentalProgramaTv) + "+"},
        "star_rating": {"value": str(EstrellasProgramaTv) + "/5"},
        "icon": "https://www.izzigo.tv/images/" + ImagenProgramaTv + "/SNAPSHOT/m/0",
        "image": {
            "type": "backdrop",
            "size": "3",
            "orient": "L",
            "system": "tvdb",
            "url": "https://www.izzigo.tv/images/" + ImagenProgramaTv + "/SNAPSHOT/l/0",
        },
    }

    if SubTituloProgramaTv:
        programa["sub_title"] = {"lang": "es", "value": SubTituloProgramaTv}

    return programa

## GENERAR EPG

headers = {
    'accept': 'application/json',
    'accept-charset': 'utf-8',
    'accept-encoding': 'gzip',
    'connection': 'Keep-Alive',
    'host': 'www.izzigo.tv',
    'iris-app-name': 'izzigo',
    'iris-app-version': '(9010303)',
    'iris-device-class': 'TABLET',
    'iris-device-type': 'TABLET/ANDROID',
    'iris-hw-device-id': '318e96d1e40b0638f251d87922287e63b2c05fcdd765a8a6b6c039cf8a01ba8f',
    'user-agent': 'Android-Retrofit2',
}

StartDate = date.today() - timedelta(days=7)
print(">> Start date:", StartDate)
EndDate = date.today() + timedelta(days=7)
print(">> End date  :", EndDate)

file_contents = []

def download_file(epg_url, NombreDeCanal, IdDeCanal):
    inicio = time.time()
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    s.mount('https://www.izzigo.tv', HTTPAdapter(max_retries=retries))
    response = s.get(epg_url, headers=headers, verify=False)
    try:
        jsonresponce = json.loads(response.text)
        file_contents.append([IdDeCanal, NombreDeCanal, jsonresponce])
    except Exception:
        print("Falla al tratar de obetener informacion del canal: " + NombreDeCanal + " ID: " + IdDeCanal + " Url: " + epg_url)
    fin = time.time()
    print("RespCode: " + str(response.status_code) + " Canal: " + NombreDeCanal + " - ID: " + IdDeCanal + " Tiempo: " + str(fin - inicio))
    return response.status_code

start = time.time()
print(">> Comienza descarga de programacion de canales...")
with ThreadPoolExecutor(max_workers=100) as executor:
    for Channel in arregloCanales:
        IdDeCanal = Channel[2]
        NombreDeCanal = Channel[1]
        epg_url = (
            'https://www.izzigo.tv/managetv/tvinfo/events/schedule?controlvn=1688543700129&end='
            + str(EndDate) + 'T00%3A00%3A00Z&language=SPA&serviceId=' + IdDeCanal
            + '&start=' + str(StartDate) + 'T00%3A00%3A00Z&view=cd-events-grid-view'
        )
        executor.submit(download_file, epg_url, NombreDeCanal, IdDeCanal)

print('>> Time taken to download shows: ' + str(time.time() - start))

inicioTodo = time.time()

epg_json = {
    "generator_info_name": "pythonmxepg",
    "generator_info_url": "https://github.com/",
    "channels": [],
    "programmes": [],
}

print(">> Generando headers (canales)...")
for Channel in arregloCanales:
    NombreDeCanal = Channel[1]
    IdDeCanal = Channel[2]
    LogoDeCanal = Channel[4]
    epg_json["channels"].append({
        "id": "IzzI." + IdDeCanal,
        "display_name": NombreDeCanal,
        "icon": LogoDeCanal,
    })

print(">> Generando programas...")
print(f"| {'ID':<7} | {'Canal':<35} | {'Programas':<10} |")
CanalesSinProgramas = ""

for Channel in file_contents:
    IdDeCanal = Channel[0]
    NombreDeCanal = Channel[1]
    ContenidoDeCanal = Channel[2]
    NumeroDeProgramasGenerados = 0

    try:
        jsonresponce = ContenidoDeCanal
    except Exception:
        print("Falla al tratar de obetener informacion del canal: " + NombreDeCanal + " ID: " + IdDeCanal)
        continue

    try:
        EventosEnCanal = jsonresponce['evs']
    except KeyError:
        EventosEnCanal = []

    for Evento in EventosEnCanal:
        epg_json["programmes"].append(evento_a_programa(Evento))
        NumeroDeProgramasGenerados += 1

    print(f"| {IdDeCanal:<7} | {NombreDeCanal:<35} | {NumeroDeProgramasGenerados:<5} |")
    if NumeroDeProgramasGenerados == 0:
        CanalesSinProgramas += "Sin programas -> Canal: " + NombreDeCanal + " - ID: " + IdDeCanal + " - Programas: " + str(NumeroDeProgramasGenerados) + "\n"

finalTodo = time.time()
print("\n>> Time taken to build JSON: " + str(finalTodo - inicioTodo) + "\n")
print(CanalesSinProgramas)

filename = "myCablepg.json"
print(">> Escribiendo archivo JSON...")
with open(filename, 'w', encoding="utf-8") as myfile:
    json.dump(epg_json, myfile, ensure_ascii=False, indent=2)

output_gz = "myCablepg.json.gz"
gzip_file(filename, output_gz)

print(">> Listo:", filename, "y", output_gz)
