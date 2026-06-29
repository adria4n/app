#!/usr/bin/env python
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta, datetime
from html import escape
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import urllib3
import gzip
import shutil
import os

import time
inicio = time.time()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

##OBTENER LISTA DE CANALES

arrayCategoria = []
arregloCanales = []
  
with open('json_Zapopan_Julio_03_2025.json',encoding="latin-1") as f:
    json_data = json.load(f)
    Informacion = json_data['chs']
    for Canales in Informacion: 
        try:
            ChImg = "https://www.izzigo.tv/images/"+ Canales['loc'][0]['img']['dir'] +"/LOGO/m/0"
        except KeyError:
            ChImg = "https://www.izzigo.tv/webclient/img/channel_no_logo.svg"

        arregloCanales.append([int(Canales['ord']), Canales['loc'][0]['nam'], Canales['sid'], "izzitv", ChImg],)                   
    #print(arrayCategoria)
    #print(arregloCanales)
    arregloCanales.sort()
    ##for i in arregloCanales: 
    ##    print(i)

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

##GENERAR EPG

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
#StartDate = date.today() - timedelta(days=1)
print(">> Start date:", StartDate)
EndDate = date.today() + timedelta(days=7)
print(">> End date  :", EndDate)

file_contents = []

def download_file(epg_url,NombreDeCanal,IdDeCanal):
    #html = requests.get(url, stream=True)
    inicio = time.time()
    #link example https://www.izzigo.tv/managetv/tvinfo/events/schedule?controlvn=1614989100045&end=2021-03-08T00%3A00%3A00Z&language=SPA&serviceId=15688&start=2021-03-05T12%3A00%3A00Z&view=cd-events-grid-view
    #epg_url = 'https://www.izzigo.tv/managetv/tvinfo/events/schedule?controlvn=1614989100045&end=' + str(EndDate) + 'T00%3A00%3A00Z&language=SPA&serviceId=' + IdDeCanal + '&start=' + str(StartDate) + 'T00%3A00%3A00Z&view=cd-events-grid-view'
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    s.mount('https://www.izzigo.tv', HTTPAdapter(max_retries=retries))
    #s.mount('https://www.izzigo.tv', HTTPAdapter(max_retries=10))
    #print (epg_url) #debug
    response = s.get(epg_url, headers=headers, verify=False)
    #print (response) #debug
    try:
        jsonresponce = json.loads(response.text)
        file_contents.append([IdDeCanal,NombreDeCanal,jsonresponce])
    except:
        print("Falla al tratar de obetener informacion del canal: " + NombreDeCanal +" ID: " + IdDeCanal + " Url: " + epg_url)

    fin = time.time()
    print( "RespCode: " + str(response.status_code) + " Canal: " + NombreDeCanal + " - ID: " + IdDeCanal + " Tiempo: " + str(fin-inicio) )
    return response.status_code

start = time.time()
print(">> Comienza descarga de programacion de canales...")
processes = []
with ThreadPoolExecutor(max_workers=100) as executor:
    for Channel in arregloCanales:
        NumeroDeCanal=Channel[0]
        NombreDeCanal=Channel[1]
        IdDeCanal=Channel[2]
        GrupoDeCanal=Channel[3]
        LogoDeCanal=Channel[4]

        NumeroDeProgramasGenerados = 0
        
        #inicio = time.time()
        #link example https://www.izzigo.tv/managetv/tvinfo/events/schedule?controlvn=1688543700129&end=2023-07-01T12%3A00%3A00Z&language=SPA&serviceId=87311&start=2023-07-01T00%3A00%3A00Z&view=cd-events-grid-view
        epg_url = 'https://www.izzigo.tv/managetv/tvinfo/events/schedule?controlvn=1688543700129&end=' + str(EndDate) + 'T00%3A00%3A00Z&language=SPA&serviceId=' + IdDeCanal + '&start=' + str(StartDate) + 'T00%3A00%3A00Z&view=cd-events-grid-view'

        #response = requests.get(epg_url, headers=headers, timeout=20)
        processes.append(executor.submit(download_file, epg_url,NombreDeCanal,IdDeCanal ))

#for task in as_completed(processes):
    #print(task.result())


print(f'>> Time taken to download shows: {time.time() - start}')

#print(file_contents[0])

#time.sleep(60)

inicioTodo = time.time()

filename = "myCablepg.xml"
myfile = open(filename, 'w', encoding="utf-8")
print(">> Escribiendo archivo...")
myfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
myfile.write('<tv generator-info-name="pythonmxepg" generator-info-url="https://github.com/">\n')

#RespCode: 200 Canal: Boomerang - ID: 55719 - Programas: 310 Tiempo: 1.922248363494873 - 45.43744659423828
#Generar headers de canales (nombre/EPG ID/ICONO)
print(">> Generando headers...")
CanalesHeaders = ""
ProgramasDelCanal = ""
for Channel in arregloCanales:
    NumeroDeCanal=Channel[0]
    NombreDeCanal=Channel[1]
    IdDeCanal=Channel[2]
    GrupoDeCanal=Channel[3]
    LogoDeCanal=Channel[4]

    ###print("Canal: " + NombreDeCanal + "     ID: " + IdDeCanal)
    #myfile.write('<channel id="IzzI.' + IdDeCanal + '">\n')
    #myfile.write('<display-name>' + escape(NombreDeCanal) + '</display-name>\n')
    #myfile.write('</channel>\n')

    myfile.write('<channel id="IzzI.' + IdDeCanal + '">\n')
    myfile.write('<display-name>' + escape(NombreDeCanal) + '</display-name>\n')
    myfile.write('<icon src="' + escape(LogoDeCanal) + '"/>\n')
    myfile.write('</channel>\n')

print(">> Generando programas...")
print(f"| {'ID':<7} | {'Canal':<35} | {'Programas':<10} |")
CanalesSinProgramas = ""
for Channel in file_contents:
    #NumeroDeCanal=Channel[0]
    #NombreDeCanal=Channel[1]
    #IdDeCanal=Channel[2]
    #GrupoDeCanal=Channel[3]
    #LogoDeCanal=Channel[4]

    IdDeCanal=Channel[0]
    NombreDeCanal=Channel[1]
    ContenidoDeCanal=Channel[2]

    NumeroDeProgramasGenerados = 0
    
    #inicio = time.time()
    #link example https://www.izzigo.tv/managetv/tvinfo/events/schedule?controlvn=1614989100045&end=2021-03-08T00%3A00%3A00Z&language=SPA&serviceId=15688&start=2021-03-05T12%3A00%3A00Z&view=cd-events-grid-view
    #epg_url = 'https://www.izzigo.tv/managetv/tvinfo/events/schedule?controlvn=1614989100045&end=' + str(EndDate) + 'T00%3A00%3A00Z&language=SPA&serviceId=' + IdDeCanal + '&start=' + str(StartDate) + 'T00%3A00%3A00Z&view=cd-events-grid-view'

    #response = requests.get(epg_url, headers=headers, timeout=20)
    #fin = time.time()
    inicioEventos = time.time()
    try:
        #jsonresponce = json.loads(ContenidoDeCanal)
        jsonresponce = ContenidoDeCanal
    except:
        print("Falla al tratar de obetener informacion del canal: " + NombreDeCanal +" ID: " + IdDeCanal)
        #print(jsonresponce)
        #print(ContenidoDeCanal)
        #time.wait(60)
    ####print(response.status_code)
    try:
        # Extract the events from the JSON response
        EventosEnCanal = jsonresponce['evs']
    except KeyError:
        # If there are no events, set an empty list
        EventosEnCanal = []
    ##myfile.write('<channel id="izzi.41677">\n')
    ##myfile.write('<display-name>Star Channel</display-name>\n')
    ##myfile.write('</channel>\n')
    for Evento in EventosEnCanal:
        #print(jsonresponce['evs'][0]['con']['oti'])
        #if(Evento['con']['typ'] == "EPISODE"):
        try:
            CanalID = Evento['sid']
        except KeyError:
            CanalID = 0
        try:
            isLive = Evento['rep'] # was isLive = Evento['liv']
            if not (isLive):
                TituloProgramaTv = "🔴 ᵛᶦᵛᵒ " #ᴸᴵⱽᴱ ᵛᶦᵛᵒ ᴸᶦᵛᵉ
            else:
                TituloProgramaTv = "" #No es en vivo
        except KeyError:
            #Do nothing
            TituloProgramaTv = ""
        try:
            isNew = Evento['new']
            if(isNew):
                TituloProgramaTv = TituloProgramaTv + "[ESTRENO] "
            else:
                TituloProgramaTv = TituloProgramaTv #No es en nuevo
        except KeyError:
            #Do nothing
            TituloProgramaTv = TituloProgramaTv
        try:
            TituloProgramaTv = TituloProgramaTv + Evento['con']['oti']
        except KeyError:
            TituloProgramaTv = "No disponible"
        try:
            TemporadaProgramaTv = 'Temporada: ' + str(Evento['con']['sea']) + ' | '
        except KeyError:
            #Do nothing
            TemporadaProgramaTv = ""
        try:
            EpisodioProgramaTv = 'Episodio: ' + str(Evento['con']['scn']) + ' | '
        except KeyError:
            #Do nothing
            EpisodioProgramaTv = ""
        try:
            SubTituloProgramaTv = Evento['con']['loc'][0]['cti']
        except KeyError:
            #Do nothing
            SubTituloProgramaTv = ""

        try:
            ImagenProgramaTv = Evento['con']['loc'][0]['img']['dir']
        except KeyError:
            #Do nothing
            ImagenProgramaTv = ""

        try:
            isRepeat = Evento['rep']
            if(isRepeat):
                #RepeticionProgramaTv = "[Retransmisión] | "
                RepeticionProgramaTv = "" #No necesario
            else:
                RepeticionProgramaTv = "" #No es repedition
        except KeyError:
            #Do nothing
            RepeticionProgramaTv = ""

        try:
            DescripcionProgramaTv = Evento['con']['loc'][0]['syn']
        except KeyError:
            #Do nothing
            DescripcionProgramaTv = "Sin descripción"

        try:
            TestCategoriaProgramaTv = Evento['con']['categories']
            if TestCategoriaProgramaTv:
                CategoriaProgramaTv=TestCategoriaProgramaTv[-1]
            else:
                CategoriaProgramaTv = "izzi.tv"
        except KeyError:
            #Do nothing
            CategoriaProgramaTv = "izzi.tv"

        try:
            ParentalProgramaTv = Evento['con']['par']
        except KeyError:
            #Do nothing
            ParentalProgramaTv = 0

        try:
            EstrellasProgramaTv = Evento['con']['str']
            if EstrellasProgramaTv == 0:
                EstrellasRate = "☆☆☆☆☆"
            elif EstrellasProgramaTv == 1:
                EstrellasRate = "★☆☆☆☆"
            elif EstrellasProgramaTv == 2:
                EstrellasRate = "★★☆☆☆"
            elif EstrellasProgramaTv == 3:
                EstrellasRate = "★★★☆☆"
            elif EstrellasProgramaTv == 4:
                EstrellasRate = "★★★★☆"
            elif EstrellasProgramaTv == 5:
                EstrellasRate = "★★★★★"
            else:
                EstrellasRate = "☆☆☆☆☆"
            EstrellasRate
        except KeyError:
            #Do nothing
            EstrellasProgramaTv = 0
            EstrellasRate = "☆☆☆☆☆"

        try:
            FechaProgramaTV = Evento['con']['oda']
        except KeyError:
            #Do nothing
            FechaProgramaTV = 2021

        #try:
        #    PaisProgramaTv = Evento['con']['cou'][0]
        #except KeyError:
        #    #Do nothing
        PaisProgramaTv = "MEX"

        try:
            ComienzoProgramaTv = Evento['sta'] #2021-03-05T12:01:00Z -> 20210305120100 +0000
            datetimeObj = datetime.strptime(ComienzoProgramaTv, "%Y-%m-%dT%H:%M:%SZ")
            ##print(datetimeObj) #DEBUG
            ##print(datetimeObj.strftime("%Y%m%d%H%M%S%z")) #DEBUG
            ComienzoProgramaTv = datetimeObj.strftime("%Y%m%d%H%M%S%z")
        except KeyError:
            #Do nothing
            ComienzoProgramaTv = "00000000000000 +0000" #Revisar

        try:
            TerminacionProgramaTv = Evento['end'] #2021-03-05T11:40:00Z
            datetimeObj = datetime.strptime(TerminacionProgramaTv, "%Y-%m-%dT%H:%M:%SZ")
            TerminacionProgramaTv = datetimeObj.strftime("%Y%m%d%H%M%S%z")
        except KeyError:
            #Do nothing
            TerminacionProgramaTv = "20210301223000 +0000" #Revisar

        #MEJORAR DESCRIPCION PARA DEPORTES PONIENDO EL PARTIDO/JUEGO EN EL TILUTO Y LA COMPETICION EN EL SUBTITULO
        if "Sport" in CategoriaProgramaTv and SubTituloProgramaTv:
            if "🔴 ᵛᶦᵛᵒ" in TituloProgramaTv:
                TituloProgramaTv = TituloProgramaTv.replace("🔴 ᵛᶦᵛᵒ ","")
                SubTituloProgramaTv = "🔴 ᵛᶦᵛᵒ " + SubTituloProgramaTv
            TemporadaProgramaTv = TituloProgramaTv + ' | '+ TemporadaProgramaTv
            TempSubTitulo = SubTituloProgramaTv
            SubTituloProgramaTv = TituloProgramaTv
            TituloProgramaTv = TempSubTitulo
            #SubTituloProgramaTv = ""
        
        myfile.write('<programme channel="IzzI.'+ str(CanalID)+ '" start="'+ ComienzoProgramaTv+ ' +0000" stop="'+ TerminacionProgramaTv+ ' +0000">\n')
        #ProgramasDelCanal.join(['<programme start="'+ ComienzoProgramaTv+ '" stop="'+ TerminacionProgramaTv+ '" channel="IzzI.'+ str(CanalID)+ '">\n'])
        #print(ProgramasDelCanal)
        myfile.write('<title lang="es">' + escape(TituloProgramaTv) + '</title>\n')
        if SubTituloProgramaTv:
           myfile.write('<sub-title lang="es">' + escape(SubTituloProgramaTv) + '</sub-title>\n')
        #ExtraDescripcion = ""
        ExtraDescripcion= str(TemporadaProgramaTv) + str(EpisodioProgramaTv) + str(RepeticionProgramaTv) + str(CategoriaProgramaTv)  + ' | '+ str(FechaProgramaTV) + ' | '+ str(PaisProgramaTv) + ' | +' +  str(ParentalProgramaTv) + ' | '+ str(EstrellasRate) + '\n'
        if "Movie" in CategoriaProgramaTv or "Film" in CategoriaProgramaTv:
            myfile.write('<icon src="https://www.izzigo.tv/images/'+ ImagenProgramaTv +'/SNAPSHOT/m/0"/>\n') #POSTER PELICULA /POSTER/m/0
        else:
            myfile.write('<icon src="https://www.izzigo.tv/images/'+ ImagenProgramaTv +'/SNAPSHOT/m/0"/>\n') #SNAPSHOT PROGRAMA
        myfile.write('<image type="backdrop" size="3" orient="L" system="tvdb">https://www.izzigo.tv/images/'+ ImagenProgramaTv +'/SNAPSHOT/l/0</image>\n')
        myfile.write('<desc lang="es">' + escape(ExtraDescripcion) + escape(DescripcionProgramaTv) + '</desc>\n')
        myfile.write('<date>' + str(FechaProgramaTV) + '</date>\n')
        myfile.write('<country>' + str(PaisProgramaTv) + '</country>\n')
        myfile.write('<category lang="es">' + str(CategoriaProgramaTv) + '</category>\n')
        myfile.write('<rating system="MEX"><value>' + str(ParentalProgramaTv) + '+</value></rating>\n')
        myfile.write('<star-rating><value>' + str(EstrellasProgramaTv) + '/5</value></star-rating>\n')
        myfile.write('</programme>\n')
        
        #print(ProgramasDelCanal)
        ##myfile.write('<programme start="' + ComienzoProgramaTv + '" stop="' + TerminacionProgramaTv + '" channel="IzzI.' + str(CanalID) + '">\n')
        ##myfile.write('<title lang="es" >' + escape(TituloProgramaTv) + '</title>\n')
        ##if SubTituloProgramaTv:
        ##    myfile.write('<sub-title lang="es">' + escape(SubTituloProgramaTv) + '</sub-title>\n')
        ##ExtraDescripcion = TemporadaProgramaTv + EpisodioProgramaTv + RepeticionProgramaTv + CategoriaProgramaTv  + ' | '+ FechaProgramaTV + ' | '+ PaisProgramaTv + ' | +' +  str(ParentalProgramaTv) + ' | '+ str(EstrellasRate) + '\n'
        ##myfile.write('<icon src="https://www.izzigo.tv/images/'+ ImagenProgramaTv +'/BACKGROUND/m/0"/>\n') #FANART PROGRAMA
        ##myfile.write('<desc lang="es">' + escape(ExtraDescripcion) + escape(DescripcionProgramaTv) + '</desc>\n')
        ##myfile.write('<date>' + FechaProgramaTV + '</date>\n')
        ##myfile.write('<country>' + PaisProgramaTv + '</country>\n')
        ##myfile.write('<category lang="es">' + CategoriaProgramaTv + '</category>\n')
        ##myfile.write('<rating system="RTC"><value>' + str(ParentalProgramaTv) + '+</value></rating>\n')
        ##myfile.write('<star-rating><value>' + str(EstrellasProgramaTv) + '/5</value></star-rating>\n')
        ##myfile.write('</programme>\n')
        #print(TituloProgramaTv + ": " + SubTituloProgramaTv)
        NumeroDeProgramasGenerados=NumeroDeProgramasGenerados+1
    #ESCRIBIR PROGRAMAS AL ARCHIVO
    #if NumeroDeProgramasGenerados > 0:
    #    myfile.write(ProgramasDelCanal)
    finalEventos = time.time()
    #print(datetimeObj)
    #print(f"| {'Canal':<20} | {'ID':<10} | {'Programas':<10} | {'Tiempo':<10} |")
    #print(f"|{'-'*22}|{'-'*12}|{'-'*12}|{'-'*12}|")
    print(f"| {IdDeCanal:<7} | {NombreDeCanal:<35} | {NumeroDeProgramasGenerados:<5} |")
    if NumeroDeProgramasGenerados==0:
        CanalesSinProgramas = CanalesSinProgramas + "Sin programas -> Canal: " + NombreDeCanal + " - ID: " + IdDeCanal + " - Programas: " + str(NumeroDeProgramasGenerados) + "\n"

finalTodo = time.time()
print("\n")
print(">>Time taken to write xml: " + str(finalTodo-inicioTodo))
print("\n")
print(CanalesSinProgramas)
#print("\n")


#myfile.write(CanalesHeaders)
#myfile.write(ProgramasDelCanal)
myfile.write('</tv>\n')
# Close the file
myfile.close()

input_file = filename  # Replace with your input file
output_file = 'myCablepg.xml.gz'  # Output file name
gzip_file(input_file, output_file)

        #print(Evento['con']['oti']+": S"+ str(Evento['con']['sea']) + "E"+str(Evento['con']['scn']) +" "+ Evento['con']['loc'][0]['cti'])
    #else:
        #print(Evento['con']['oti'])
#print(jsonresponce['videos'][0]['licenses'][0]['url'])
#print(jsonresponce['videos'][0]['licenses'][0]['system'])

##<?xml version="1.0" encoding="UTF-8"?>
##<tv generator-info-name="m3u4u" generator-info-url="https://m3u4u.com/">
##<channel id="AandE.mx">
##<display-name>A&amp;E</display-name>
##</channel>
##<programme start="20210301223000 +0000" stop="20210301230000 +0000" channel="Azteca7.mx">
##<title lang="es" >Los Simpson</title>
##<desc lang="es">La comedia de dibujos animados se centra en una familia que vive en la ciudad de Springfield. La cabeza de la familia Simpson es Homero, quien no es un hombre de familia típico, obrero de una planta nuclear, él hace lo mejor para poder liderar a su familia, pero frecuentemente se da cuenta que son ellos los que lo mandan. La familia se compone de la matriarca amorosa, Marge de cabello azul, el hijo agitador Bart, la hija aplicada Lisa y la bebé Maggie.</desc>
##</programme>
##</tv>



'''
https://www.izzigo.tv/webclient/libs_b2d862cadeb05f305bf110ae22a5cc57.js


##### LIVE CHANNELS PROGRAM CONTENT PARAMETERS

function(t, e, n) {
    var r = n(0)
      , i = n(12)
      , a = r.partialRight(i.credits, "nam")
      , o = n(155)
      , s = n(74)
      , l = n(73)
      , u = n(45)
      , c = n(3);
    function d(t) {
        if (this.index = t.idx,
        this.id = t.cid,
        this.type = t.typ,
        this.isOriginalVersion = t.ori,
        this.duration = t.dur,
        this.originalTitle = t.oti,
        this.year = t.oda,
        this.languages = t.lan,
        this.parentalRating = t.par,
        this.genreIds = t.gid,
        this.seriesId = t.srd,
        this.seasonId = t.sed,
        this.higestKnownSeason = t.sem,
        this.seriesIdContainer = t.sic,
        this.rating = t.str,
        this.containerIds = t.ctn,
        this.isNew = t.new,
        this.isLastChance = t.las,
        this.isRecommended = t.rec,
        this.linearCount = t.lin,
        this.onDemandCount = t.onn,
        this.packageCount = t.pkn,
        this.trickplayDisabled = t.tkpDis,
        this.isAdult = t.adult,
        t.interaction && t.interaction.select && t.interaction.select.type && (this.interactionSelectType = t.interaction.select.type),
        this.countries = t.cou || [],
        this.previewUrls = u.map(t.pres || []),
        this.hasSeasonNumber = !!t.sea,
        this.hasSeasonNumber && (this.seasonNumber = parseInt(t.sea, 10)),
        this.hasEpisodeNumber = !!t.scn,
        this.hasEpisodeNumber && (this.episodeNumber = parseInt(t.scn, 10)),
        this.actors = a(t.act),
        this.directors = a(t.dir),
        this.writers = a(t.wrt),
        this.presenters = a(t.prs),
        this.creators = a(t.cre),
        this.musicians = a(t.mus),
        this.producers = a(t.prc),
        this.cinematographers = a(t.pho),
        this.hasCredits = this.actors.length > 0 || this.directors.length > 0 || this.writers.length > 0,
        "EPISODE" === this.type) {
            var e = i.text(t.loc, "cti") || [];
            this.episodeTitle = e.length ? e[0] : void 0
        }
        var n = i.text(t.loc, "syn") || [];
        this.description = n.length ? n[0] : void 0,
        this.images = i.images(t);
        var c = i.text(t.loc, "tit");
        if (this.title = c.length ? c[0] : this.originalTitle,
        t.lik && (this.likeThis = r.map(t.lik, (function(t) {
            return new d(t)
        }
        ))),
        t.chi && (this.children = r.map(t.chi, (function(t) {
            return new d(t)
        }
        ))),
        this.packages = s.map(t.pkg),
        this.isContent = !0,
        this.isSerie = "SERIES" === this.type,
        this.isSeason = "SEASON" === this.type,
        this.isEpisode = "EPISODE" === this.type,
        this.isSerie && (this.isBroadcastSerie = !0,
        this.isVODSerie = !!this.seriesIdContainer,
        t.dty && r.isArray(t.dty) && (this.isBroadcastSerie = -1 !== t.dty.indexOf("BROADCAST"),
        this.isVODSerie = -1 !== t.dty.indexOf("VOD"),
        this.isCatchUpSerie = -1 !== t.dty.indexOf("CATCHUP"),
        this.isRecordingSerie = -1 !== t.dty.indexOf("RECORDING"))),
        t.srs && (this.seriesServices = l.map(t.srs)),
        t.del) {
            this.numberOfDeliveries = t.del.length;
            var h = this
              , f = r.map(o.map(t.del), (function(t) {
                if (!t.isBroadcast || t.channel)
                    return t.content = h,
                    t
            }
            ));
            this.recordings = r.filter(f, {
                isRecording: !0
            }) || [],
            this.deliveries = r.filter(f, {
                isRecording: !1
            }) || []
        }
    }


##### LIVE CHANNELS PROGRAM PARAMETERS


function(t, e, n) {
    var r = n(0)
      , i = n(11)
      , a = n(41).cache
      , o = n(73)
      , s = n(264)
      , l = n(45)
      , u = n(50)
      , c = n(3)
      , d = n(72);
    e.map = c((function(t) {
        if (t.rid)
            return u.map(t);
        this.eventId = t.eid,
        this.serviceId = t.sid,
        this.isLive = t.liv,
        this.isRepeat = t.rep,
        this.videoStreams = t.vid,
        this.onDemandId = t.oid,
        this.isNew = t.new,
        this.price = t.pri,
        this.rentalPeriod = t.ren,
        this.events = t.evt,
        this.isCopyProtected = t.cpy,
        this.isHd = t.hd,
        this.is3d = t.is3d,
        this.privateDescriptors = t.prd,
        this.audioFormats = t.aud || [],
        this.audioLanguages = (t.aua || []).concat(t.aul || []),
        this.subtitleLanguages = (t.sua || []).concat(t.stl || []),
        t.cas && (this.catchUpStart = i.parseDate(t.cas)),
        t.cae && (this.catchUpEnd = i.parseDate(t.cae)),
        t.schsta ? (this.availabilityStart = t.sta && i.parseDate(t.sta),
        this.start = i.parseDate(t.schsta)) : this.start = t.sta && i.parseDate(t.sta),
        t.schend ? (this.availabilityEnd = t.end && i.parseDate(t.end),
        this.end = i.parseDate(t.schend).toDate()) : this.end = t.end && i.parseDate(t.end),
        t.vissta && (this.visibleStart = i.parseDate(t.vissta)),
        t.visend && (this.visibleEnd = i.parseDate(t.visend)),
        this.urls = l.map(t.urls) || [],
        this.startOverUrls = l.map(t.sov) || [],
        this.catchUpUrls = l.map(t.cup) || [],
        this.serviceId && (this.channel = a[this.serviceId]);
        var e = o.map(t.pro);
        this.onDemandPackages = s.map(t.opk),
        this.isRecording = !1,
        this.isVod = !!this.onDemandId,
        this.isBroadcast = !!this.eventId,
        this.isCatchUp = !!this.catchUpStart && !!this.catchUpEnd,
        this.isPpv = !!r.find(e, {
            isPPV: !0
        }),
        this.hasStartOver = !!t.soa,
        t.appReference && (this.appReference = t.appReference,
        t.appDetails && t.appDetails.load && (this.appDetailsLoad = d.map(t.appDetails.load)));
        var n = this;
        this.products = r.map(e, (function(t) {
            return t.delivery = n,
            t
        }
        ))
    }
    ))
}

##### ON DEMAND

, function(t, e, n) {
    var r = n(0)
      , i = n(11)
      , a = n(45)
      , o = n(155)
      , s = n(73)
      , l = n(39)
      , u = n(3);
    e.map = u((function(t) {
        this.onDemandId = t.oid,
        this.videoStreams = t.vid,
        this.isCopyProtected = t.cpy,
        this.isHd = t.hd,
        this.price = t.pri,
        this.privateDescriptors = t.prd,
        this.vodPackageIds = t.opk,
        this.audioFormats = t.aud || [],
        this.audioLanguages = (t.aua || []).concat(t.aul || []),
        this.subtitleLanguages = (t.sua || []).concat(t.stl || []),
        this.urls = a.map(t.urls) || [],
        this.previewUrls = a.map(t.pres) || [],
        this.products = s.map(t.pro),
        this.content = l.map(t.con),
        t.sta && (this.start = i.parseDate(t.sta)),
        t.end && (this.end = i.parseDate(t.end)),
        t.vissta && (this.visibleStart = i.parseDate(t.vissta)),
        t.visend && (this.visibleEnd = i.parseDate(t.visend)),
        this.isRecording = !1,
        this.isVod = !0,
        this.isBroadcast = !1,
        this.isCatchUp = !1;
        var e = this;
        this.broadcastDeliveries = r.map(o.map(t.evt), (function(t) {
            return t.content = e.content,
            t
        }
        )),
        this.content && !this.content.deliveries && (this.content.deliveries = [this])
    }
    ))
}
'''
