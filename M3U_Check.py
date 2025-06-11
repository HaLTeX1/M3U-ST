# 2025.06.11
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import m3u8
import requests
import time
import re


def test_stream_url(url, timeout=10):
    """
    Teszteli egy adott stream URL működőképességét.
    Visszaadja True-t, ha működik, False-t különben.
    """
    try:
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



def _fetch_m3u_content(source, is_url=False):
    """
    Lekéri az M3U tartalmát string formájában, URL-ről vagy helyi fájlól.
    Segéd függvény a load_m3u_channels számára.
    """
    try:
        if is_url:
            response = requests.get(source, timeout=10)
            response.raise_for_status()
            return response.text
        else:
            with open(source, 'r', encoding='utf-8') as f:
                return f.read()
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Hiba",
                             f"Hiba az M3U URL letöltésekor: {e}\nKérjük, ellenőrizze az URL-t és az internetkapcsolatot.")
        return None
    except Exception as e:
        messagebox.showerror("Hiba", f"Hiba a helyi M3U fájl olvasásakor: {e}")
        return None


def _parse_m3u_content_manually(m3u_content):
    """
    Manuálisan parszolja az M3U tartalmat.
    Ez a fallback, ha az m3u8 könyvtár nem boldogul vele.
    Kinyeri a csatorna nevét, URL-jét, tvg-logo, group-title és tvg-language, tvg-country attribútumokat.
    """
    channels = []
    lines = m3u_content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            channel_name = "Ismeretlen csatorna"
            channel_logo = ""
            channel_group = ""
            channel_language = ""
            channel_country = ""

            if ',' in line:
                channel_name = line.split(',', 1)[1].strip()

            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            if logo_match:
                channel_logo = logo_match.group(1)

            group_match = re.search(r'group-title="([^"]+)"', line)
            if group_match:
                channel_group = group_match.group(1)

            language_match = re.search(r'tvg-language="([^"]+)"', line)
            if language_match:
                channel_language = language_match.group(1)

            country_match = re.search(r'tvg-country="([^"]+)"', line)
            if country_match:
                channel_country = country_match.group(1)

            if i + 1 < len(lines):
                url_line = lines[i + 1].strip()
                if url_line and not url_line.startswith("#"):
                    channels.append({
                        "name": channel_name,
                        "url": url_line,
                        "logo": channel_logo,
                        "group": channel_group,
                        "language": channel_language,
                        "country": channel_country
                    })
                    i += 1
            i += 1
        else:
            i += 1

    if not channels:
        messagebox.showwarning("Manuális parszolási hiba",
                               "A manuális parszolás sem talált csatornákat az M3U fájlban. Lehet, hogy sérült vagy ismeretlen formátumú.")
    return channels


def load_m3u_channels(source, is_url=False):
    """
    Betölti az M3U fájlt (helyi vagy URL-ről) és kinyeri a csatornák neveit és URL-jeit.
    Két módszert próbál meg: először az m3u8 könyvtárral, majd manuális parszolással.
    """
    m3u_content = _fetch_m3u_content(source, is_url)
    if m3u_content is None:
        return []

    channels = []

    # 1. Próbálkozás az m3u8 könyvtárral (ideális esetben ez működik)
    try:
        playlist = m3u8.parse(m3u_content)
        for segment in playlist.segments:
            logo = segment.extinf.get('tvg-logo', '') if segment.extinf else ''
            group = segment.extinf.get('group-title', '') if segment.extinf else ''
            language = segment.extinf.get('tvg-language', '') if segment.extinf else ''
            country = segment.extinf.get('tvg-country', '') if segment.extinf else ''

            if segment.title and segment.uri:
                channels.append({
                    "name": segment.title,
                    "url": segment.uri,
                    "logo": logo,
                    "group": group,
                    "language": language,
                    "country": country
                })

        return channels
    except Exception as e:
        error_message = str(e)
        messagebox.showwarning("Parszolási hiba",
                               f"Az 'm3u8' könyvtár hibába ütközött az M3U fájl/URL feldolgozásakor: {error_message}\n"
                               "Valószínűleg a fájl formátuma szokatlan, vagy a könyvtárverzióval van gond.\n"
                               "Megpróbálom manuálisan kinyerni a csatornákat, ami lassabb lehet...")

        # 2. Visszaváltás a manuális parszolásra
        return _parse_m3u_content_manually(m3u_content)


def test_stream_url(url, timeout=10):
    """
    Teszteli egy adott stream URL működőképességét.
    Visszaadja egy tuple-t: (True/False, üzenet).
    """
    try:
        # ELLENŐRZÉS: Hiányzik-e az 'http://' vagy 'https://' előtag
        if not (url.startswith("http://") or url.startswith("https://")):
            return False, "Érvénytelen URL: Hiányzik az 'http://' vagy 'https://' előtag."

        start_time = time.time()
        with requests.get(url, stream=True, timeout=timeout, allow_redirects=True) as r:
            r.raise_for_status()  # HTTP hibák ellenőrzése (pl. 404, 500)

            chunk_size = 1024
            data_received = False
            # Megpróbálunk egy kis adatot olvasni, hogy meggyőződjünk a stream működéséről
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    data_received = True
                    break

            if not data_received:
                return False, "Nincs adatfogadás a streamről (üres válasz)."

            return True, "Működik"

    except requests.exceptions.MissingSchema:
        # Bár az elején már ellenőrizzük, ez is elkapja, ha valahol máshol hibás URL kerülne ide.
        return False, "Érvénytelen URL: Hiányzik az 'http://' vagy 'https://' előtag (MissingSchema)."
    except requests.exceptions.Timeout:
        return False, f"Időtúllépés ({timeout} mp). A stream nem válaszolt időben."
    except requests.exceptions.ConnectionError:
        return False, "Kapcsolódási hiba. Lehet, hogy az URL hibás, vagy nincs internetkapcsolat."
    except requests.exceptions.HTTPError as e:
        # Pontosabb HTTP hibaüzenet (pl. 404 Not Found, 403 Forbidden)
        return False, f"HTTP hiba: {e.response.status_code} {e.response.reason}."
    except requests.exceptions.RequestException as e:
        # Minden más Requests hibát elkapunk
        return False, f"Általános HTTP kérés hiba: {e}."
    except Exception as e:
        # Minden egyéb, nem várt hibát elkapunk
        return False, f"Ismeretlen hiba a stream tesztelésekor: {e}."


# --- GUI rész ---

class M3UTesterApp:
    def __init__(self, master):
        self.master = master
        master.title("M3U Stream Tesztelő")

        self.m3u_source = None
        self.is_source_url = False
        self.channels_to_test = []
        self.working_channels = []

        # URL beviteli rész
        self.url_frame = tk.LabelFrame(master, text="M3U URL betöltése")
        self.url_frame.pack(padx=10, pady=5, fill="x")

        self.url_entry = tk.Entry(self.url_frame, width=70)
        self.url_entry.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill="x")
        self.url_entry.insert(0, "https://iptv-org.github.io/iptv/countries/hu.m3u")

        self.btn_load_url = tk.Button(self.url_frame, text="Betöltés URL-ről", command=self.load_m3u_from_url)
        self.btn_load_url.pack(side=tk.RIGHT, padx=5, pady=5)

        # Helyi fájl kiválasztás része
        self.file_frame = tk.LabelFrame(master, text="Helyi M3U fájl kiválasztása")
        self.file_frame.pack(padx=10, pady=5, fill="x")

        self.label_file = tk.Label(self.file_frame, text="Nincs kiválasztott helyi fájl.")
        self.label_file.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill="x")

        self.btn_browse = tk.Button(self.file_frame, text="Fájl kiválasztása", command=self.browse_m3u_file)
        self.btn_browse.pack(side=tk.RIGHT, padx=5, pady=5)

        # Tesztelés indítása gomb
        self.btn_start_test = tk.Button(master, text="Tesztelés indítása", command=self.start_test, state=tk.DISABLED)
        self.btn_start_test.pack(pady=10)

        # Működő csatornák mentése gomb
        self.btn_save_working = tk.Button(master, text="Működő csatornák mentése", command=self.save_working_channels,
                                          state=tk.DISABLED)
        self.btn_save_working.pack(pady=5)

        # Eredményeket megjelenítő keret és szövegdobozok
        self.results_frame = tk.LabelFrame(master, text="Teszt eredmények")
        self.results_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.working_streams_text = scrolledtext.ScrolledText(self.results_frame, width=60, height=15,
                                                              state=tk.DISABLED, bg="#e6ffe6")
        self.working_streams_text.pack(side=tk.LEFT, padx=5, pady=5, fill="both", expand=True)
        self.working_streams_text.insert(tk.END, "Működő streamek:\n")

        self.non_working_streams_text = scrolledtext.ScrolledText(self.results_frame, width=60, height=15,
                                                                  state=tk.DISABLED, bg="#ffe6e6")
        self.non_working_streams_text.pack(side=tk.RIGHT, padx=5, pady=5, fill="both", expand=True)
        self.non_working_streams_text.insert(tk.END, "Nem működő streamek:\n")

        self.status_label = tk.Label(master, text="Készen áll a tesztelésre.", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def load_m3u_from_url(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showwarning("Figyelem", "Kérlek, adj meg egy URL-t!")
            return

        self.m3u_source = url
        self.is_source_url = True
        self.label_file.config(text="M3U URL betöltve.")
        self.btn_start_test.config(state=tk.NORMAL)
        self.btn_save_working.config(state=tk.DISABLED)
        self.clear_results()
        self.status_label.config(text="M3U URL betöltve. Készen áll a tesztelésre.")
        self.working_channels = []

    def browse_m3u_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("M3U Files", "*.m3u"), ("All Files", "*.*")]
        )
        if filepath:
            self.m3u_source = filepath
            self.is_source_url = False
            self.label_file.config(text=f"Kiválasztott fájl: {self.m3u_source.split('/')[-1]}")
            self.btn_start_test.config(state=tk.NORMAL)
            self.btn_save_working.config(state=tk.DISABLED)
            self.clear_results()
            self.status_label.config(text="M3U fájl betöltve. Készen áll a tesztelésre.")
            self.working_channels = []

    def clear_results(self):
        self.working_streams_text.config(state=tk.NORMAL)
        self.working_streams_text.delete(1.0, tk.END)
        self.working_streams_text.insert(tk.END, "Működő streamek:\n")
        self.working_streams_text.config(state=tk.DISABLED)

        self.non_working_streams_text.config(state=tk.NORMAL)
        self.non_working_streams_text.delete(1.0, tk.END)
        self.non_working_streams_text.insert(tk.END, "Nem működő streamek:\n")
        self.non_working_streams_text.config(state=tk.DISABLED)

    def start_test(self):
        if not self.m3u_source:
            messagebox.showwarning("Figyelem", "Kérlek, válassz ki egy M3U fájlt vagy adj meg egy URL-t először!")
            return

        self.clear_results()
        self.working_channels = []
        self.btn_start_test.config(state=tk.DISABLED)
        self.btn_browse.config(state=tk.DISABLED)
        self.btn_load_url.config(state=tk.DISABLED)
        self.btn_save_working.config(state=tk.DISABLED)
        self.status_label.config(text="Tesztelés folyamatban...")

        test_thread = threading.Thread(target=self._run_test_in_thread)
        test_thread.start()

    def _run_test_in_thread(self):
        self.channels_to_test = load_m3u_channels(self.m3u_source, self.is_source_url)
        if not self.channels_to_test:
            messagebox.showerror("Hiba", "Nem sikerült csatornákat kinyerni a forrásból.")
            self.btn_start_test.config(state=tk.NORMAL)
            self.btn_browse.config(state=tk.NORMAL)
            self.btn_load_url.config(state=tk.NORMAL)
            self.status_label.config(text="Hiba történt. Készen áll a tesztelésre.")
            return

        total_channels = len(self.channels_to_test)
        tested_count = 0

        for channel in self.channels_to_test:
            tested_count += 1
            channel_name = channel['name']
            channel_url = channel['url']

            self.status_label.config(text=f"Tesztelés: {channel_name} ({tested_count}/{total_channels})")
            self.master.update_idletasks()

            is_working, message = test_stream_url(channel_url, timeout=10)

            if is_working:
                self.update_results_text(self.working_streams_text, f"{channel_name} ({channel_url}) - Működik\n",
                                         "green")
                self.working_channels.append({
                    "name": channel_name,
                    "url": channel_url,
                    "logo": channel.get("logo", ""),
                    "group": channel.get("group", ""),
                    "language": channel.get("language", ""),
                    "country": channel.get("country", "")
                })
            else:
                self.update_results_text(self.non_working_streams_text,
                                         f"{channel_name} ({channel_url}) - NEM MŰKÖDIK ({message})\n", "red")

        self.status_label.config(text="Tesztelés befejeződött.")
        self.btn_start_test.config(state=tk.NORMAL)
        self.btn_browse.config(state=tk.NORMAL)
        self.btn_load_url.config(state=tk.NORMAL)
        self.btn_save_working.config(state=tk.NORMAL)
        messagebox.showinfo("Tesztelés befejeződött", "Minden stream tesztelve lett!")

    def update_results_text(self, text_widget, content, tag=None):
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, content)
        if tag:
            pass
        text_widget.see(tk.END)
        text_widget.config(state=tk.DISABLED)

    def save_working_channels(self):
        if not self.working_channels:
            messagebox.showinfo("Információ", "Nincsenek működő csatornák a mentéshez.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".m3u",
            filetypes=[("M3U Files", "*.m3u"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("#EXTM3U\n")
                    for channel in self.working_channels:
                        extinf_line = f'#EXTINF:-1 tvg-id="{channel["name"]}" tvg-name="{channel["name"]}"'

                        if "logo" in channel and channel["logo"]:
                            extinf_line += f' tvg-logo="{channel["logo"]}"'

                        if "group" in channel and channel["group"]:
                            extinf_line += f' group-title="{channel["group"]}"'

                        if "language" in channel and channel["language"]:
                            extinf_line += f' tvg-language="{channel["language"]}"'

                        if "country" in channel and channel["country"]:
                            extinf_line += f' tvg-country="{channel["country"]}"'

                        extinf_line += f',{channel["name"]}\n'
                        f.write(extinf_line)
                        f.write(f"{channel['url']}\n")

                messagebox.showinfo("Siker", f"Működő csatornák elmentve: {filepath}")
            except Exception as e:
                messagebox.showerror("Hiba", f"Nem sikerült menteni a fájlt: {e}")


def main():
    root = tk.Tk()
    app = M3UTesterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()