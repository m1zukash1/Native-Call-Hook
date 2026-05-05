Sveiki, mano vardas Elvinas Žukauskas, mano darbo vadovas yra docentas daktaras Saulius Valentinavičius ir mano pristatoma tema yra Android vietinių funkcijų perėmimas šifruotoms bibliotekoms.

## Problema

Android platformoje vietines bibliotekas galima uzkrauti per Java sluoksni arba tiesiogiai per vietini sluoksni. Problema kyla tuomet, kai viena vietine biblioteka bando uzkrauti kita vietine biblioteka, visiskai apeidama Java sluoksni.

Toks principas yra ypac daznas irankiuose, leidzianciuose tureti viena aplikacijos implementacija ir ja eksportuoti i kelias platformas, pavyzdziui, Flutter ar .NET MAUI.

## Aktualumas

Nėra viešai prieinamo įrankio, implementacijos ar net paprasčiausių šaltinių kurie užsimintų apie tokios apsaugos implementaciją.

Android ekosistemoje dažnai pasitaiko aplikacijų, kurios naudoja įrankius ir sprendimus, paremtus vietinių bibliotekų užkrovimo principu. Pavyzdžiui, 2024 metų duomenimis, iš visų Google Play aplikacijų Flutteris sudarė 11%.

Dirbu kaip programinės įrangos inžinierius būtent prie Android apsaugos produkto ir esame gavę tiesioginių užklausų iš klientų, kurie naudoja Flutter ir .NET MAUI būtent tokių vietinių bibliotekų apsaugai.

## Uždaviniai

Išanalizuoti vietinių bibliotekų užkrovimo mechanizmus.
Ištirti ir įvertinti technikas metodų perėmimui.
Sukurti konceptualią sistemos veikimą įrodančią architektūrą.
Implementuoti ir ištestuoti šią architektūrą.

## Vietiniu biblioteku uzkrovimo analize

Analizeje isnagrinejau kaip Android platformoje veikia vietiniu biblioteku uzkrovimas. Platformoje vietines bibliotekas galima uzkrauti is java sluoksnio per `System.loadLibrary()`. Arba is vietinio sluoksnio per `dlopen()`. Abejais atvejais siu vietiniu biblioteku iskvietimo seka susikerta bionic dynamic linkerio vidinei funkcijoj `__loder_dlopen`. Butent si funkcija ir yra peremimo taikinys.

## Metodu peremimo analize

Isanalizavau pagrindinius pasirinkimus Android platformoje.

Java lygio metodu peremimas per Java reflection veikia tik java sluoksnyje ir nepagauna vietiniu iskvietimu.

Inline hookingas, toki scenariju padengia, taciau jis yra nestabilus, jis tiesiogiai keicia aplikacijos instrukcijas ir stipriai priklauso nuo irenginio architekturos.

PLT metodu peremimas nekeicia aplikacijos instrukciju, o keicia pacio dinaminio linkerio valdomus funkciju adresus. Prie to pacio jis leidzia perimti visus processo iskvietimmus ir puikiai tinka dlopen metodu seimai. Butet PLT metodu perimimas ir buvo pasiriktas siam darbui.


## Sistemos architekturos specifikacija

Visa sistemos architektura galime skelti i keturias dalis.

Pirma dalis yra aplikacijos kompiliavimo metu taikoma apsauga vietinei bilbiotekai. Integruotas python skriptas uzsifruoja norima vietinia biblioteka. Sifruota biblioteka yra atgal supakuojama i jau sukompiliuota aplikacija.

Antrame lygmenyje yra apsasugota android aplikacija. Jos veikimo metu inicializuojama vietine apsaugos biblioteka, kuri registruoja PLT metodu peremima ir susieja ji su paskutiniame lygmenyje esancia proxy funkcija.

Treciame lygmenyje gyvena Android platforma, Android runtime virtuali masina ir bionic dinamyc linkeris. Visos vietines bibliotekos uzkrovimo funkcijos pereina per si sluoksni.

Paskutiniame sluoksnyje gyvena proxy funkcija. Visi vietiniu biblioteku krovimo metodai pereina per dinamini linkeri, o aplikacijos pradzioje inicializuotas PLT metodu peremejas nukreipia visas vietiniu biblioteku krovimo funkcijas i sia proxy funkcija.

Proxy funkcija tikrina norima uzkrauti vietinia biblioteka su vidiniu registru sarasu kuriame yra nurodytos visos uzsifruotos bibliotekos aplikacijos viduje. Jei biblioteka nera tame registre, tos bibliotekos uzkrovimas yra nukreipiamas i orginalia dlopen implementacija. Kitu atveju toliau veikia proxy funkcija, kuri tikrina ar ta biblioteka aplikacijos viduje egzistuoja, tada visa uzsifruota biblioteka yra nuskaitoma tiesiogiai i atminti, atmintyje desifruojama ir is atminties tiesiogiai uzkraunama i aplikacijos procecsa.

## Implementacija

### Vietines bibliotekos sifravimas

Aplikacijos kompiliavimo metu CMake įrankyje yra integruotas papildomas post-build žingsnis kuris kviečia python skriptą. Jis šifruoja pasirinktas bibliotekas su nurodytu raktu. Šifravimo mechanizmas specialiai yra pasirinktas labai paprastas, iteruojames per biblioteką baitas po baito ir ant esamo baito turinio atliekam XOR operaciją su nurodytu raktu. Toks primityvus mechanizmas pasirinktas specialiai, nes šis darbas orientuojasi į vidinių sistemų funkcijų perėmimą, dešifravimo logiką, o ne šifravimo stiprumą. Taigi, sukompiliuotos aplikacijos viduje lieka tik užšifruota bibliotekos versija.

### PLT metodu peremimas

Aplikacijos veikimo metu egzistuoja papildoma vietinė biblioteka kurios viduje gyvena PLT metodų perėmimo logika. Ši biblioteka yra pats pirmas dalykas kuris užsikrauna aplikacijos veikimo metu. Logika inicializuojama per `__attribute__((constructor))` funkciją. Tokiu būdu kompiliuotos bibliotekos inicializacijos logika yra patalpinta į ELF `.init_array` segmentą. Dinaminis linkeris šį segmentą įvygdo iškarto kai biblioteka yra užkraunama, dar prieš visas Java sluoksnyje esančias android lifecycle funkcijas.

Pirmas zingsnis inicializacijos logikoje tai yra prisikabinti prie `__loader_dlopen` funkcijos ir ja nukreipti i savo dedikuota proxy funkcija. Tai yra igyvendinta su trecios salies pagalbine biblioteka `ByteHook`. Nukreipimo logika veikia per Post linkage table ir global offset table lenteliu modifikavima. Tai reiskia kad nera keiciama pati `__loader_dlopen` funkcijos implementacija ar perrasomas jos masininis kodas, o modifikuojama tu biblioteku importo lentele, kurios kviecia sia funkcija. Kai betkokia vietine biblioteka bando kviesti `__loader_dlopen`, jos PLT irasas per GOT lentele yra nukreipiamas ne i orginalia funkcija, o i mano proxy funkcija.

### Proxy funkcijos veikimas

Proxy funkcija gauna tuos pacius argumentus kaip ir originali funkcija. Peremimo logikos metu yra tikrinama kokia biblioteka yra bandoma uzkrauti ir ar ji egzistuoja vidiniame registre kur yra nurodytos visos uzsifruotos bibliotekos. Jei biblioteka neegzistuoja registre ji yra perduodama originaliai linkerio funkcijai.

Kitu atveju, pirmas zingsis yra uzsikrauti visa uzsifruota biblioteka tiesiai i atminti. Sifruota biblioteka yra nuskaitoma tiesiai i vektoriu baitas po baito. Tada yra iteruojamasi per kiekviena baita kuris yra uzkrautas i atminti ir ant jo atliekama XOR operacija su nurodytu raktu, tai desifruoja pasirinkta biblioteka. Tada yra patikrinami pirmi keturi ELF magiski baitai. Jie nusako ar biblioteka grizo atgal i originalu ELF tipa, ar desifravimo logikoje neatsirado klaidos.

Tada yra sukuriamas anoniminis atminties failo deskriptorius. Deskriptoriaus dydis yra nustatomas i musu desifruotos bibliotekos, kuri siuo metu gyvena atmintyje, bufferio dydi ir tada pati desifruota biblioteka yra irasoma i deskriptoriu. Tada bionic dynamic linkeriui per `android_dlopen_ext()` su `ANDROID_DLEXT_USE_LIBRARY_FD` flag'u nurodome uzkrauti ELF segmentus tiesiogiai is sio atminties deskriptoriaus i aplikacijos procesa. Toliau linkeris dirba standartiskai, atlieka reikalingas relokacijas, uzkrana priklausomybes, ivygdo konstruktorius ir grazina standartini handle. Taigi, biblioteka tiesiai is atminties yra uzkraunama i aplikacijos procesa. Desifruota biblioteka niekad nera laikoma tiesiogiai diske.

## Testavimas

Implementacija buvo patikrinta septyniuose testuose su realiu Google Pixel 9 irenginiu ir Android 16. Testai patvirtino svarbiausius dalykus:

Uzsifruota biblioteka irenginio diske yra saugoma kaip nevalidi ir nenuskaitoma ELF biblioteka

Antra, Uzsifruota vietine biblioteka yra desifruojama aplikacijos vykdimo metu ir yra uzkraunama i aplikacijos procesa.

Neteisingas desifravimo raktas yra atmetamas, nesugriaunant aplikacijos veikimo ciklo.

## Išvados

Isanalizavus vietiniu biblioteku uzkrovimo mechanizmus buvo nustatyta jog __loader_dlopen yra logiskiausias peremimo taskas apimantis tiek Java tiek vietini sluoksni.

Isanalizavimus metodu peremimo mechanizmus, nustatyta jog logiskiausia yra PLT peremimo technika.

Sukurta architektura irode kad sistema gali veikti ir atrodo logiskai ant popieriaus.

O implementacija irode kad tokia architektura imanoma igyvedinti fiziskai. Testai irode, jog veikimo mechanizmas yra svarus ir sklandus. 