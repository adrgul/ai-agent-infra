1.házi openai api hívás megvalósítása.

Távlati cél:
A kiválasztott megvalósítandó projektem a meeting-asszisztens.
Jelen házival egy API hívást kell prezentálnom. Kiindulásként (INIT_PROMPT.md) a vector_embedding projektet használtam, azt szabtam testre, de csak közepes sikerrel. Vannak benne hibák, nem sikerült mindent kigyepálni, de szorít az idő a beadás miatt.

A meeting asszisztens első feladata:
Az összegzés és kivonatolás funkció demonstrálása. 

Tesztelésem egyelőre sekélyes volt, ez alapján az összegzés igen furcsa eredményt mutatott, nem a teljes szöveget összegezte, hanem csak az elejét. Nem ezt a célt kívántam elérni.
A névkivonatolás, listásan sem teljesen tökéletes, ámde nem hiányos, bővebb listát (halmazt) eredményezett, mint az elvárt.


Teszteset1
Bemenet1:
Kelemen elment bevásárolni és a boltból 
egy milli tejjel jött haza. Kelemen elfelejtett Túró Rudit venni. Ettől én nagyon szomoroú lettem, és visszaküldtem őt a tekintetemmel. Bátor az ablakban ül és a terasz felé kémlel. Holnap karácsony, Jézuska csomagol. Ha ez egy meeting jegyzőkönyv lenne, rém szomorú lennék, hogy 12.23-án este 21.50kor még mindig ezt csinálom, de valahogy el kell érni a karakterszámot. A lakógyűlésen megvitatásra került a Közönséges Képviselő és a Többi Jómadár részvételével a szavazás az érintett témában. Nem nagyon volt konszenzus. A jegyzőkönyvet nem vezették. Az elnök nem írta alá. Amit nem vezettek. Zsiráf Zsófi ellenben jelen volt és már ngyon tele a 


Kimenet1 (extrakt, a fölös, nem releváns válaszokat kihagyva):

Summary (<=20 words):
Kelemen elment bevásárolni és a boltból egy milli tejjel jött haza. Kelemen elfelejtett Túró Rudit venni. Ettől én nagyon szomoroú

Names found:
- Kelemen
- Túró Rudit
- Ettől
- Bátor
- Holnap
- Jézuska
- Ha
- A
- Közönséges Képviselő
- Többi Jómadár
- Nem
- Az
- Amit
- Zsiráf Zsófi

Teszteset2
Bemenetként egy koherensebb szöveget adok meg:
Egy napsütéses szombat reggel Pitypang felébredt, nyújtózott egy nagyot és kiugrott az ágyból. Mikor mindennapi tornájával végzett, arra gondolt, vajon járt-e már itt a Postás. Felhúzta pulóverét és kiment a postaládához. Volt is benne egy levél, csupa arany tintával írva:
Kedves Pitypang!
Szombat délután szívesen látlak egy csésze teára és egy szelet tortára. Nem kell kiöltöznöd!
Szeretettel ölel,
Zsiráf Zsófi.
Pitypang nagyon megörült: nohát! hiszen ez ma van, még szerencse, hogy úgyis borbélyhoz készültem. Sietve elmosogatta és eltörölgette a reggeli edényt, gyorsan beágyazott és már futott is a borbélyhoz.
Kenguru Kázmér már várta. Kázmér előbb … aztán alaposan besamponozta a sörényét. 

Kimenet:

Enter a prompt (or 'exit' to quit): Egy napsütéses szombat reggel Pitypang felébredt, nyújtózott egy nagyot és kiugrott az ágyból. Mikor mindennapi tornájával végzett, arra gondolt, vajon járt-e már itt a Postás. Felhúzta pulóverét és kiment a postaládához. Volt is benne egy levél, csupa arany tintával írva:Kedves Pitypang!Szombat délután szívesen látlak egy csésze teára és egy szelet tortára. Nem kell kiöltöznöd!Szeretettel ölel,Zsiráf Zsófi.Pitypang nagyon megörült: nohát! hiszen ez ma van, még szerencse, hogy úgyis borbélyhoz készültem. Sietve elmosogatta és eltörölgette a reggeli edényt, gyorsan beágyazott és már futott is a borbélyhoz.Kenguru Kázmér már várta. Kázmér előbb … aztán alaposan besamponozta a sörényét. 

Summary (<=20 words):
Egy napsütéses szombat reggel Pitypang felébredt, nyújtózott egy nagyot és kiugrott az ágyból. Mikor mindennapi tornájával végzett, arra gondolt, vajon 

Names found:
- Egy
- Pitypang
- Mikor
- Postás Felhúzta
- Volt
- Pitypang!Szombat
- Nem
- Zsófi.Pitypang
- Sietve
- Kázmér

Teszt2 konklúzió: Központozás-érzékeny

Teszt3 
Be (központozás javítva):
Egy napsütéses szombat reggel Pitypang felébredt, nyújtózott egy nagyot és kiugrott az ágyból. Mikor mindennapi tornájával végzett, arra gondolt, vajon járt-e már itt a Postás. Felhúzta pulóverét és kiment a postaládához. Volt is benne egy levél, csupa arany tintával írva: Kedves Pitypang! Szombat délután szívesen látlak egy csésze teára és egy szelet tortára. Nem kell kiöltöznöd! Szeretettel ölel, Zsiráf Zsófi. Pitypang nagyon megörült: nohát! hiszen ez ma van, még szerencse, hogy úgyis borbélyhoz készültem. Sietve elmosogatta és eltörölgette a reggeli edényt, gyorsan beágyazott és már futott is a borbélyhoz. Kenguru Kázmér már várta. Kázmér előbb megnyírta aztán alaposan besamponozta a sörényét. 
Ki: Summary (<=20 words):
Egy napsütéses szombat reggel Pitypang felébredt, nyújtózott egy nagyot és kiugrott az ágyból. Mikor mindennapi tornájával végzett, arra gondolt, vajon 

Names found:
- Egy
- Pitypang
- Mikor
- Postás Felhúzta
- Volt
- Kedves Pitypang! Szombat
- Nem
- Szeretettel
- Zsiráf Zsófi Pitypang
- Sietve
- Kenguru Kázmér
- Kázmér

Konklúzió: sem a summary sem a névlistázás nem megfelelő válasz. prompt finomhangolandó későbbi felhasználásra.

TODO:
eliminálni a fölösleges kódrészeket (embedding, vectorstore), ehhez módosítani az init-promptot, áttekinteni a hivatkozásokat.

Tesztelhetőség:
1) A pro1 mappában .env file helyezendő el, OPENAI_API_KEY=<sajátkulcsbeheylettesítendő> tartalommal.
2) navigáljunk az app almappába
3) python -m main.py
De jelenleg indentationError-t dob. Beadás előtt nem tudom már megfixálni, több kört is futva, javítást kérve a copilottól, ugyanott tartok. Pardon.
Tóth.
