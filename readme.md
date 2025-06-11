# M3U Stream Tester (M3U-ST)

A szoftver célja, hogy legyen mód tesztelni egy már meglévő M3U vagy M3U8 formátumú fájlt. A program ellenőrzi, hogy az időtúllépés előtt érkezik-e válasz a stream kiszolgálójától és hogy a streamből van-e letölthető adat. 

## Szükséges Modulok

- [Tkinter](https://docs.python.org/3/library/tkinter.html)
- [Threading](https://docs.python.org/3/library/threading.html)
- [m3u8](https://pypi.org/project/m3u8/)
- [Requests](https://pypi.org/project/requests/)
- [Time](https://docs.python.org/3/library/time.html)
- [RE](https://docs.python.org/3/library/re.html)

## Tesztelési logika

A program a **test_stream_url** funkcióban ellenőrzi az adott stream elérhetőségét. Amennyiben nem elérhető egy stream úgy false értékkel tér vissza. A stream működésére vonatkozó adatokat egy **GET** HTTP kérés segítségével kérdezzük le. *(Itt van lehetőség HEAD lekérdezést is alkalmazni, viszont ezt nem minden kiszolgáló támogatja)*
Alapesetben 1 KB (1024 B) adatot nyerünk ki a streamből amely a legtöbb esetben elegendő a működőképesség megállapítására. Szükség esetén ez a **chunk_size** változóval módosítható

## Adatok feldolgozása
Az M3U és M3U8 állományok betöltésére van lehetőség fájlból és HTTP/HTTPS URL segítségével. Amennyiben M3U állománnyal dolgozunk úgy szükséges a fájlból a különböző streamek adatait kinyernünk.
Az állományokól az alábbi adatokat nyeri ki a program:
- channel_name - Csatorna neve
- url_line - Stream URL
- channel_logo - LOGO
- channel_group - Kategória
- channel_language - A csatorna eredeti nyelve
- channel_country - Ország

Ezek az adatok hasznosak lehetnek a streaming szoftvernek való átadásnál (Például: Plex, Jellyfin, Emby)

A GUI segítségével ellenőrizhetjük, hogy mely streamek elérhetőek és melyek nem. 

## Új állomány összeállítása
A tesztelés végeztével elérhetővé válik a **"Működő csatornák mentése"** gomb amellyel van lehetőségünk rá hogy a tesztelt és működő streameket becsomagoljuk egy M3U állományba amelyet így könnyebben tudunk használni egy streaming szoftverben. Szükség esetén **.txt** állományba is van lehetőség menteni a listát.

## Inspiráció, ötletgazda
- [iptv-org - iptv ](https://github.com/iptv-org/iptv)

