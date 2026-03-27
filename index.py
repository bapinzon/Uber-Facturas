import os
import sys
import calendar
import threading
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import customtkinter as ctk
from tkinter import filedialog, messagebox


class UberInvoiceDownloader:

    graphqlUrl = "https://riders.uber.com/graphql"

    queryActivities = (
        "query Activities($cityID: Int, $endTimeMs: Float, $includePast: Boolean = true, "
        "$includeUpcoming: Boolean = true, $limit: Int = 5, $nextPageToken: String, "
        "$orderTypes: [RVWebCommonActivityOrderType!] = [RIDES, TRAVEL], "
        "$profileType: RVWebCommonActivityProfileType = PERSONAL, $startTimeMs: Float) {\n"
        "  activities(cityID: $cityID) {\n    cityID\n    past(\n      endTimeMs: $endTimeMs\n"
        "      limit: $limit\n      nextPageToken: $nextPageToken\n      orderTypes: $orderTypes\n"
        "      profileType: $profileType\n      startTimeMs: $startTimeMs\n    ) @include(if: $includePast) {\n"
        "      activities {\n        ...RVWebCommonActivityFragment\n        __typename\n      }\n"
        "      nextPageToken\n      __typename\n    }\n    upcoming @include(if: $includeUpcoming) {\n"
        "      activities {\n        ...RVWebCommonActivityFragment\n        __typename\n      }\n"
        "      __typename\n    }\n    __typename\n  }\n}\n\n"
        "fragment RVWebCommonActivityFragment on RVWebCommonActivity {\n"
        "  buttons {\n    isDefault\n    startEnhancerIcon\n    text\n    url\n    __typename\n  }\n"
        "  cardURL\n  description\n  imageURL {\n    light\n    dark\n    __typename\n  }\n"
        "  subtitle\n  title\n  uuid\n  __typename\n}\n"
    )

    queryInvoice = (
        "query GetInvoiceFiles($tripUUID: ID!) {\n"
        "  invoiceFiles(tripUUID: $tripUUID) {\n    archiveURL\n    files {\n"
        "      downloadURL\n      __typename\n    }\n    __typename\n  }\n}\n"
    )

    mesesEs = {
        "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
        "julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12,
    }

    def __init__(self, cookies, rutaCarpeta, hilos=5, logFn=None):
        self.cookies      = cookies
        self.rutaCarpeta  = rutaCarpeta
        self.hilos        = hilos
        self.log          = logFn or print
        self._lock        = threading.Lock()
        self._threadLocal = threading.local()

    @property
    def session(self):
        if not hasattr(self._threadLocal, "session"):
            s = requests.Session()
            s.headers.update(self._headers())
            self._threadLocal.session = s
        return self._threadLocal.session

    def _headers(self):
        return {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "es-419,es;q=0.5",
            "content-type": "application/json",
            "cookie": self.cookies,
            "origin": "https://riders.uber.com",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/146.0.0.0 Safari/537.36"
            ),
            "x-csrf-token": "x",
            "x-uber-rv-session-type": "desktop_session",
        }

    def _mesTimestamps(self, año, mes):
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Mexico_City")
        except ImportError:
            import pytz
            tz = pytz.timezone("America/Mexico_City")
        ultimoDia = calendar.monthrange(año, mes)[1]
        inicio    = datetime(año, mes, 1, 0, 0, 0, tzinfo=tz)
        fin       = datetime(año, mes, ultimoDia, 23, 59, 59, 999000, tzinfo=tz)
        return int(inicio.timestamp() * 1000), int(fin.timestamp() * 1000)

    def _mesNumero(self, nombre):
        n = self.mesesEs.get(nombre.lower().strip())
        if not n:
            raise ValueError(f"Mes no reconocido: '{nombre}'")
        return n

    def _nombreBase(self, url):
        archivo     = os.path.basename(urlparse(url).path)
        nombre, ext = os.path.splitext(archivo)
        return nombre.split("_")[0], ext

    def _graphql(self, payload, referer="https://riders.uber.com/trips"):
        self.session.headers.update({"referer": referer})
        r = self.session.post(self.graphqlUrl, json=payload, timeout=15)
        r.raise_for_status()
        return r.json()

    def _viajes(self, año, mes):
        startMs, endMs = self._mesTimestamps(año, mes)
        self.log(f"Consultando viajes  {año}-{mes:02d}")
        data = self._graphql({
            "operationName": "Activities",
            "variables": {
                "includePast": True, "includeUpcoming": False,
                "limit": 1000, "orderTypes": ["RIDES", "TRAVEL"],
                "profileType": "PERSONAL",
                "startTimeMs": startMs, "endTimeMs": endMs,
            },
            "query": self.queryActivities,
        })
        uuids = [
            a["uuid"]
            for a in data["data"]["activities"]["past"]["activities"]
            if a.get("uuid")
        ]
        self.log(f"Viajes encontrados: {len(uuids)}\n")
        return uuids

    def _archivosViaje(self, tripUuid):
        data = self._graphql(
            {
                "operationName": "GetInvoiceFiles",
                "variables": {"tripUUID": tripUuid},
                "query": self.queryInvoice,
            },
            referer=f"https://riders.uber.com/trips/{tripUuid}",
        )
        return data["data"]["invoiceFiles"]["files"]

    def _guardar(self, url, carpeta, nombreBase):
        _, ext = self._nombreBase(url)
        ruta   = os.path.join(carpeta, f"{nombreBase}{ext}")
        if os.path.exists(ruta):
            self.log(f"  Existe: {os.path.basename(ruta)}")
            return
        r = self.session.get(url, timeout=30)
        r.raise_for_status()
        with open(ruta, "wb") as f:
            f.write(r.content)
        self.log(f"  Guardado: {os.path.basename(ruta)}")

    def descargarMes(self, mes, año=None):
        if año is None:
            año = datetime.now().year
        if isinstance(mes, str):
            mes = self._mesNumero(mes)

        base    = os.path.dirname(os.path.abspath(sys.argv[0]))
        carpeta = os.path.join(base, self.rutaCarpeta, f"{año}-{mes:02d}")
        os.makedirs(carpeta, exist_ok=True)
        self.log(f"Destino: {carpeta}\n")

        uuids = self._viajes(año, mes)
        total = len(uuids)

        def procesar(args):
            idx, uuid = args
            with self._lock:
                self.log(f"[{idx}/{total}] {uuid}")
            try:
                archivos = self._archivosViaje(uuid)
                if not archivos:
                    with self._lock:
                        self.log("  Sin facturas")
                    return
                nombre, _ = self._nombreBase(archivos[0]["downloadURL"])
                for a in archivos:
                    self._guardar(a["downloadURL"], carpeta, nombre)
            except Exception as e:
                with self._lock:
                    self.log(f"  Error: {e}")

        with ThreadPoolExecutor(max_workers=self.hilos) as ex:
            for f in as_completed({ex.submit(procesar, (i, u)): u for i, u in enumerate(uuids, 1)}):
                f.result()

        self.log(f"\nCompletado — {carpeta}")


def resourcePath(file):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, file)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

C = {
    "bg":      "#0a0a0a",
    "topbar":  "#111111",
    "panel":   "#0f0f0f",
    "input":   "#141414",
    "border":  "#1f1f1f",
    "fg":      "#e0e0e0",
    "dim":     "#555555",
    "green":   "#4caf50",
    "gbg":     "#0d1f12",
    "gborder": "#1e4d28",
    "log":     "#6fcf97",
}

MESES = [
    "Enero","Febrero","Marzo","Abril","Mayo","Junio",
    "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre",
]


class App(ctk.CTk):

    def __init__(self):
        super().__init__(fg_color=C["bg"])
        self.title("Uber Facturas")
        self.resizable(False, False)
        try:
            self.iconbitmap(resourcePath("icono.ico"))
        except Exception:
            pass
        self._build()

    def _label(self, parent, text, size=9, fg=None, **grid):
        ctk.CTkLabel(
            parent, text=text,
            font=("Segoe UI", size),
            text_color=fg or C["dim"],
            fg_color="transparent",
        ).grid(**grid)

    def _build(self):
        topbar = ctk.CTkFrame(self, fg_color=C["topbar"], corner_radius=0, height=52)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)

        ctk.CTkLabel(
            topbar, text="UBER FACTURAS",
            font=("Segoe UI", 13, "bold"),
            text_color=C["fg"],
        ).place(x=18, rely=0.5, anchor="w")

        ctk.CTkLabel(
            topbar, text="DEV: Cody Prime",
            font=("Segoe UI", 8),
            text_color=C["dim"],
        ).place(x=158, rely=0.5, anchor="w")

        ctk.CTkFrame(self, fg_color=C["border"], height=1, corner_radius=0).grid(row=1, column=0, sticky="ew")

        body = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        body.grid(row=2, column=0, sticky="nsew", padx=20, pady=16)

        self._label(body, "COOKIES", size=8, row=0, column=0, columnspan=3, sticky="w", padx=0, pady=(0,5))
        self.txtCookies = ctk.CTkTextbox(
            body, width=480, height=90,
            font=("Consolas", 8),
            fg_color=C["input"],
            text_color=C["log"],
            border_color=C["border"],
            border_width=1,
            corner_radius=8,
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color="#2a2a2a",
        )
        self.txtCookies.grid(row=1, column=0, columnspan=3, pady=(0,14))

        fields = ctk.CTkFrame(body, fg_color="transparent")
        fields.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0,14))
        fields.columnconfigure(1, weight=1)

        labelKw = dict(size=8, fg=C["dim"])
        entryKw = dict(
            fg_color=C["input"],
            text_color=C["fg"],
            border_color=C["border"],
            border_width=1,
            corner_radius=8,
            font=("Segoe UI", 10),
        )

        rows = [("MES", 0), ("AÑO", 1), ("HILOS", 2), ("CARPETA", 3)]
        for txt, r in rows:
            self._label(fields, txt, **labelKw, row=r, column=0, sticky="w", padx=(0,12), pady=5)

        self.cmbMes = ctk.CTkOptionMenu(
            fields,
            values=MESES,
            width=140,
            fg_color=C["input"],
            text_color=C["fg"],
            button_color=C["border"],
            button_hover_color="#2a2a2a",
            dropdown_fg_color="#161616",
            dropdown_text_color=C["fg"],
            dropdown_hover_color="#1e1e1e",
            corner_radius=8,
            font=("Segoe UI", 10),
        )
        self.cmbMes.set(MESES[datetime.now().month - 1])
        self.cmbMes.grid(row=0, column=1, sticky="w", pady=5)

        self.entAño = ctk.CTkEntry(fields, width=100, **entryKw)
        self.entAño.insert(0, str(datetime.now().year))
        self.entAño.grid(row=1, column=1, sticky="w", pady=5)

        self.entHilos = ctk.CTkEntry(fields, width=100, **entryKw)
        self.entHilos.insert(0, "5")
        self.entHilos.grid(row=2, column=1, sticky="w", pady=5)

        carpetaRow = ctk.CTkFrame(fields, fg_color="transparent")
        carpetaRow.grid(row=3, column=1, sticky="w", pady=5)

        self.entCarpeta = ctk.CTkEntry(carpetaRow, width=310, **entryKw)
        self.entCarpeta.insert(0, "facturas")
        self.entCarpeta.pack(side="left")

        ctk.CTkButton(
            carpetaRow, text="...", width=36,
            fg_color=C["input"],
            text_color=C["dim"],
            hover_color="#1a1a1a",
            border_color=C["border"],
            border_width=1,
            corner_radius=8,
            font=("Segoe UI", 10),
            command=self._elegirCarpeta,
        ).pack(side="left", padx=(6,0))

        ctk.CTkFrame(body, fg_color=C["border"], height=1, corner_radius=0).grid(
            row=3, column=0, columnspan=3, sticky="ew", pady=(0,14)
        )

        self.btn = ctk.CTkButton(
            body,
            text="DESCARGAR FACTURAS",
            font=("Segoe UI", 11, "bold"),
            fg_color=C["gbg"],
            text_color=C["green"],
            hover_color="#102716",
            border_color=C["gborder"],
            border_width=1,
            corner_radius=8,
            height=40,
            command=self._iniciar,
        )
        self.btn.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0,14))

        self._label(body, "LOG", size=8, row=5, column=0, columnspan=3, sticky="w", padx=0, pady=(0,5))
        self.txtLog = ctk.CTkTextbox(
            body, width=480, height=180,
            font=("Consolas", 8),
            fg_color=C["input"],
            text_color=C["log"],
            border_color=C["border"],
            border_width=1,
            corner_radius=8,
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color="#2a2a2a",
            state="disabled",
        )
        self.txtLog.grid(row=6, column=0, columnspan=3)

        ctk.CTkFrame(self, fg_color=C["border"], height=1, corner_radius=0).grid(row=3, column=0, sticky="ew")

        footer = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0, height=32)
        footer.grid(row=4, column=0, sticky="ew")
        footer.grid_propagate(False)
        ctk.CTkLabel(footer, text="riders.uber.com",                font=("Segoe UI", 8), text_color="#222", fg_color="transparent").place(x=18,  rely=0.5, anchor="w")
        ctk.CTkLabel(footer, text="Solo para uso con Uber Facturas", font=("Segoe UI", 8), text_color="#222", fg_color="transparent").place(relx=1, x=-18, rely=0.5, anchor="e")

    def _elegirCarpeta(self):
        ruta = filedialog.askdirectory()
        if ruta:
            self.entCarpeta.delete(0, "end")
            self.entCarpeta.insert(0, ruta)

    def _writeLog(self, msg):
        self.txtLog.configure(state="normal")
        self.txtLog.insert("end", msg + "\n")
        self.txtLog.see("end")
        self.txtLog.configure(state="disabled")

    def _log(self, msg):
        self.after(0, self._writeLog, msg)

    def _iniciar(self):
        cookies = self.txtCookies.get("1.0", "end").strip()
        mes     = self.cmbMes.get()
        carpeta = self.entCarpeta.get().strip() or "facturas"

        try:
            año   = int(self.entAño.get())
            hilos = int(self.entHilos.get())
        except ValueError:
            messagebox.showerror("Error", "Año e Hilos deben ser numeros enteros.")
            return

        if not cookies:
            messagebox.showerror("Error", "Pega las cookies de Uber.")
            return

        self.btn.configure(state="disabled", text="Descargando...")
        self.txtLog.configure(state="normal")
        self.txtLog.delete("1.0", "end")
        self.txtLog.configure(state="disabled")

        def run():
            try:
                UberInvoiceDownloader(
                    cookies=cookies,
                    rutaCarpeta=carpeta,
                    hilos=hilos,
                    logFn=self._log,
                ).descargarMes(mes, año)
            except Exception as e:
                self._log(f"Error: {e}")
            finally:
                self.after(0, lambda: self.btn.configure(state="normal", text="DESCARGAR FACTURAS"))

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    App().mainloop()