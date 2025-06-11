def test_stream_url(url, timeout=10):
    """
    Teszteli egy adott stream URL működőképességét.
    Visszaadja True-t, ha működik, False-t különben.
    """
    try:
        # HEAD kérés küldése a gyors ellenőrzéshez, hogy elérhető-e a forrás
        # de a valós stream ellenőrzéshez GET szükséges, mert a HEAD nem mindig elegendő.
        # Itt egyszerűsítünk, GET-tel próbálunk adatot olvasni.
        start_time = time.time()
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status() # HTTP hibák ellenőrzése (pl. 404, 500)

            # Próbálunk egy kis adatot olvasni a streamből
            # Ez biztosítja, hogy nem csak a fejléc jött vissza, hanem a stream is elindult.
            chunk_size = 1024 # Olvassunk 1KB-ot
            data_received = False
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    data_received = True
                    break # Elég volt 1 KB adat a teszthez

            if not data_received:
                return False, "Nincs adatfogadás a streamről"

            end_time = time.time()
            if (end_time - start_time) > timeout:
                return False, "Teszt időtúllépés"

            return True, "Működik"

    except requests.exceptions.Timeout:
        return False, f"Időtúllépés ({timeout} másodperc)"
    except requests.exceptions.ConnectionError:
        return False, "Kapcsolódási hiba"
    except requests.exceptions.RequestException as e:
        return False, f"Hiba: {e}"
    except Exception as e:
        return False, f"Ismeretlen hiba: {e}"

# Példa használat:
# stream_url = "http://example.com/live.m3u8"
# is_working, message = test_stream_url(stream_url, timeout=10)
# if is_working:
#     print(f"A stream ({stream_url}) működik: {message}")
# else:
#     print(f"A stream ({stream_url}) NEM működik: {message}")

