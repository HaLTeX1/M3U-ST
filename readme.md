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
