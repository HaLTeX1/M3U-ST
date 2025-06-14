import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import requests
import time
import re


def test_stream_url(url, timeout=10):
    try:
        if not (url.startswith("http://") or url.startswith("https://")):
            return False, "Érvénytelen URL"
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    return True, "Működik"
        return False, "Nincs adatfogadás"
    except Exception as e:
        return False, str(e)


def load_m3u_channels(source, is_url=False):
    try:
        if is_url:
            content = requests.get(source, timeout=10).text
        else:
            with open(source, "r", encoding="utf-8") as f:
                content = f.read()
    except Exception as e:
        messagebox.showerror("Hiba", f"Nem sikerült betölteni az M3U forrást: {e}")
        return []

    lines = content.splitlines()
    channels = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            name = re.split(r"#EXTINF:-1.*?,", line)[-1].strip()
            logo = re.search(r'tvg-logo="([^"]+)"', line)
            group = re.search(r'group-title="([^"]+)"', line)
            lang = re.search(r'tvg-language="([^"]+)"', line)
            country = re.search(r'tvg-country="([^"]+)"', line)
            if i + 1 < len(lines):
                url = lines[i + 1].strip()
                channels.append({
                    "name": name,
                    "url": url,
                    "logo": logo.group(1) if logo else "",
                    "group": group.group(1) if group else "",
                    "language": lang.group(1) if lang else "",
                    "country": country.group(1) if country else ""
                })
                i += 1
        i += 1
    return channels


class M3UTesterApp:
    def __init__(self, master):
        self.master = master
        self.master.title("M3U Tesztelő")

        self.m3u_source = None
        self.is_source_url = False
        self.channels_to_test = []
        self.working_channels = []

        menu = tk.Menu(master)
        tools = tk.Menu(menu, tearoff=0)
        tools.add_command(label="Csatornalista böngészése", command=self.browse_channels)
        tools.add_command(label="M3U fájlok egyesítése", command=self.merge_m3u_files)
        menu.add_cascade(label="Eszközök", menu=tools)
        master.config(menu=menu)

        url_frame = tk.LabelFrame(master, text="M3U URL")
        url_frame.pack(fill="x", padx=10, pady=5)
        self.url_entry = tk.Entry(url_frame, width=80)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        tk.Button(url_frame, text="Betöltés URL-ről", command=self.load_from_url).pack(side="right", padx=5)

        file_frame = tk.LabelFrame(master, text="Helyi M3U fájl")
        file_frame.pack(fill="x", padx=10, pady=5)
        self.file_label = tk.Label(file_frame, text="Nincs kiválasztott fájl")
        self.file_label.pack(side="left", padx=5)
        tk.Button(file_frame, text="Tallózás", command=self.load_from_file).pack(side="right", padx=5)

        self.btn_test = tk.Button(master, text="Teszt indítása", command=self.start_test, state="disabled")
        self.btn_test.pack(pady=5)
        self.btn_save = tk.Button(master, text="Működő csatornák mentése", command=self.save_working, state="disabled")
        self.btn_save.pack(pady=5)

        result_frame = tk.LabelFrame(master, text="Eredmények")
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.txt_working = scrolledtext.ScrolledText(result_frame, bg="#e6ffe6", height=12, state="disabled")
        self.txt_working.pack(side="left", expand=True, fill="both", padx=5, pady=5)
        self.txt_failed = scrolledtext.ScrolledText(result_frame, bg="#ffe6e6", height=12, state="disabled")
        self.txt_failed.pack(side="right", expand=True, fill="both", padx=5, pady=5)

    def load_from_url(self):
        self.m3u_source = self.url_entry.get()
        self.is_source_url = True
        self.file_label.config(text="URL kiválasztva")
        self.btn_test.config(state="normal")

    def load_from_file(self):
        path = filedialog.askopenfilename(filetypes=[("M3U", "*.m3u")])
        if path:
            self.m3u_source = path
            self.is_source_url = False
            self.file_label.config(text=path)
            self.btn_test.config(state="normal")

    def start_test(self):
        self.channels_to_test = load_m3u_channels(self.m3u_source, self.is_source_url)
        self.working_channels = []
        self.txt_working.config(state="normal")
        self.txt_failed.config(state="normal")
        self.txt_working.delete("1.0", "end")
        self.txt_failed.delete("1.0", "end")
        threading.Thread(target=self._run_test).start()

    def _run_test(self):
        for ch in self.channels_to_test:
            ok, msg = test_stream_url(ch["url"])
            target = self.txt_working if ok else self.txt_failed
            target.config(state="normal")
            target.insert("end", f"{ch['name']} - {msg}\n")
            target.see("end")
            target.config(state="disabled")
            if ok:
                self.working_channels.append(ch)
        self.btn_save.config(state="normal")

    def save_working(self):
        if not self.working_channels:
            return
        path = filedialog.asksaveasfilename(defaultextension=".m3u")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                for ch in self.working_channels:
                    ext = f'#EXTINF:-1 tvg-name="{ch["name"]}"'
                    if ch["logo"]: ext += f' tvg-logo="{ch["logo"]}"'
                    if ch["group"]: ext += f' group-title="{ch["group"]}"'
                    if ch["language"]: ext += f' tvg-language="{ch["language"]}"'
                    if ch["country"]: ext += f' tvg-country="{ch["country"]}"'
                    ext += f',{ch["name"]}\n{ch["url"]}\n'
                    f.write(ext)
            messagebox.showinfo("Mentve", f"Mentés kész: {path}")

    def merge_m3u_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("M3U", "*.m3u")])
        if not paths:
            return
        all_channels = []
        seen_urls = set()
        for path in paths:
            chans = load_m3u_channels(path)
            for ch in chans:
                if ch["url"] not in seen_urls:
                    seen_urls.add(ch["url"])
                    all_channels.append(ch)
        self.working_channels = all_channels
        self.save_working()

    def browse_channels(self):
        path = filedialog.askopenfilename(filetypes=[("M3U", "*.m3u")])
        if not path:
            return
        chans = load_m3u_channels(path)
        win = tk.Toplevel(self.master)
        win.title("Csatornalista")

        filters = tk.Frame(win)
        filters.pack(fill="x")
        entries = {}
        for i, field in enumerate(["name", "group", "language", "country"]):
            tk.Label(filters, text=field.capitalize()).grid(row=0, column=2*i)
            var = tk.StringVar()
            entries[field] = var
            tk.Entry(filters, textvariable=var, width=12).grid(row=0, column=2*i+1)

        cols = ("Név", "Kategória", "Nyelv", "Ország", "Logó")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        tree.pack(fill="both", expand=True)

        def apply():
            tree.delete(*tree.get_children())
            for ch in chans:
                if all(entries[k].get().lower() in ch.get(k, '').lower() for k in entries):
                    tree.insert("", "end", values=(ch["name"], ch["group"], ch["language"], ch["country"], ch["logo"]))

        tk.Button(filters, text="Szűrés", command=apply).grid(row=0, column=8)
        apply()


def main():
    root = tk.Tk()
    app = M3UTesterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
