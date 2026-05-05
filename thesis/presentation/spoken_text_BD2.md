Sveiki, mano vardas Elvinas Žukauskas, mano darbo vadovas yra docentas daktaras Saulius Valentinavičius ir mano pristatoma tema yra Android vietinių funkcijų perėmimas šifruotoms bibliotekoms.

## Problema ir aktualumas

Android platformoje vietines bibliotekas galima užkrauti per Java sluoksnį arba tiesiogiai per vietinį sluoksnį. Problema kyla tuomet, kai viena vietinė biblioteka bando užkrauti kitą vietinę biblioteką, visiškai apeidama Java sluoksnį. Toks principas yra ypač dažnas įrankiuose, leidžiančiuose turėti vieną aplikacijos implementaciją ir ją eksportuoti į kelias platformas, pavyzdžiui, Flutter ar .NET MAUI. 2024 metų duomenimis, Flutter sudaro 11% visų Google Play aplikacijų.

Problema yra aktuali — nėra viešai prieinamo įrankio, implementacijos ar net paprasčiausių šaltinių, kurie užsimintų apie tokios apsaugos implementaciją. Pats dirbu kaip programinės įrangos inžinierius prie Android apsaugos produkto ir esame gavę tiesioginių užklausų iš klientų, naudojančių Flutter ir .NET MAUI, būtent šiai problemai spręsti.

## Uždaviniai

Darbo uždaviniai buvo išanalizuoti vietinių bibliotekų užkrovimo mechanizmus, ištirti ir įvertinti perėmimo technikas, sukurti konceptualią architektūrą ir ją implementuoti bei ištestuoti.

## Analizė

Analizėje išnagrinėjome, kaip Android platformoje veikia vietinių bibliotekų užkrovimas. ELF formato bibliotekos užkraunamos per bionic dinaminį susiejiklį, kuris apdoroja priklausomybes, atlieka relokacijas ir vykdo inicializacijos konstruktorius. Tiek Java sluoksnio `System.loadLibrary()`, tiek vietinio sluoksnio `dlopen()` iškvietimai galiausiai praeina per vieną vidinį simbolį — `__loader_dlopen`. Tai tapo mūsų perėmimo taikiniu.

Išnagrinėjome ir esamas perėmimo technikas — Java lygmens kabliais, tokiais kaip Xposed ar LSPosed, galima stebėti tik valdomąjį sluoksnį ir jie tiesiog nemato `dlopen()` iškvietimų iš vietinio kodo. Vietinio lygmens technikos, ypač PLT ir GOT paremtas perėmimas, suteikia reikiamą aprėptį. Kaip praktinę priemonę pasirinkome ByteHook biblioteką, kuri leidžia įdiegti PLT kablius visame procese be root prieigos.

## Specifikacija

Sistemai suformulavo keturis funkcinius ir keturis saugumo reikalavimus. Pagrindiniai funkciniai reikalavimai: kablys turi būti įdiegtas prieš bet kurią vietinę biblioteką, perėmimas turi veikti ir vietinio-į-vietinį scenarijuje, o neapsaugotų bibliotekų užkrovimas turi vykti be jokio papildomo apkrovimo. Saugumo pusėje — apsaugota biblioteka neturi egzistuoti diske kaip galiojantis ELF failas, iššifravimas turi vykti tik proceso atmintyje, o neteisingas raktas turi būti atmestas nesugriaujant aplikacijos.

## Implementacija

Sistema veikia dviem etapais. Pirmas — kompiliavimo metu. Python skriptas XOR šifruoja pasirinktą biblioteką raktu `0x69`, todėl pirmi keturi baitai iš ELF magijos `7f 45 4c 46` tampa `16 2c 25 2f` — tokio failo bionic linker tiesiog atsisako krauti. Šis skriptas vykdomas automatiškai kaip CMake post-build žingsnis, tad APK pakete jau yra tik užšifruota versija.

Antras etapas — vykdymo metu. `libnativecallhook.so` turi ELF konstruktoriaus funkciją, kuri vykdoma iš karto, kai tik biblioteka užkraunama — anksčiau nei `JNI_OnLoad` ir anksčiau nei bet koks kitas `dlopen()` iškvietimas. Šiame konstruktoriuje per ByteHook įdiegiamas PLT kablys ant `__loader_dlopen` simbolio visame procese.

Kai perėmimo kablys suveikia, tikrinama registro lentelė — ar prašoma biblioteka yra apsaugota. Jei ne, iškvietimas perduodamas originaliam susiejikliui be pakeitimų. Jei taip — failas nuskaitomas iš disko, XOR iššifruojamas į atmintį, patikrinama ELF magija, ir tada per `memfd_create` sukuriamas anoniminis atminties deskriptorius. Iššifruota biblioteka įrašoma į jį ir užkraunama per `android_dlopen_ext()` su `ANDROID_DLEXT_USE_LIBRARY_FD` vėliavėle — tekstas diske niekada nepasirodo.

Teisingas užkrovimo eiliškumas užtikrinamas Java pusėje — `NativeCallHook.initialize()` kviečiamas statiniame bloke prieš bet kurią kitą biblioteką.

## Testavimas

Visi septyni testai praėjo realiame Google Pixel 9 įrenginyje su Android 16. Patvirtinome, kad apsaugota biblioteka diske yra negaliojantis ELF, kablys įdiegiamas prieš bet kurį užkrovimą, vietinio-į-vietinį scenarijus veikia skaidriai, ir neteisingas raktas atmetamas nesugriaujant aplikacijos.

## Išvados

Darbe sukurta ir ištestuota konceptuali sistema, kuri leidžia apsaugoti vietines Android bibliotekas nuo tiesioginio užkrovimo net ir vietinio-į-vietinį scenarijuje. Sistema veikia be root prieigos, nereikalauja paketo struktūros pakeitimų ir užtikrina, kad iššifruotas turinys niekada nepasiekia disko. Ateityje verta papildyti stipresne kriptografija, konfigūruojamu bibliotekų sąrašu ir platesniais suderinamumo testais.