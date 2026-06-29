# TODO – GCode Translator

Strukturierte Sammlung der Optimierungspunkte aus dem Code-Review (Stand 2026-06-29).
Die Punkte sind **unabhängig voneinander** angelegt und können in **beliebiger Reihenfolge**
abgearbeitet werden. Jeder Punkt hat eine ID (z. B. `LIB-1`), damit wir in Commits/PRs
darauf verweisen können.

> **Erledigt am 2026-06-29:** `LIB-1` + `ARCH-1` (gemeinsam umgesetzt). Verifiziert: das
> aggregierte Ergebnis-Dict ist byte-identisch zur Vorversion (Demo + echte Beispieldatei),
> `output.txt` bleibt inhaltsgleich (nur überflüssige Leerzeilen entfernt), Bibliotheksmodus
> ist seiteneffektfrei und stumm auf stdout.

---

## Kontext: Was das Programm aktuell kann

Der **GCode Translator** ist ein Python-Tool (als Paket `gcode-translator` installierbar, CLI + API),
das 3D-Drucker-G-Code lesbar macht:

1. **Übersetzung** – jede G-/M-Code-Zeile wird über ein Mapping (`G1 → "Linear Move"`) in
   Klartext plus Parameter aufgelöst (`GCode_Translator.py`).
2. **Mapping-Beschaffung** mit 3-stufigem Fallback (`GCode_Mapping.py`):
   lokale JSON (1) → Paket-Ressource (2) → Live-Scraping der Marlin-Doku via Selenium/BeautifulSoup (3).
   Standardmäßig offline (`url="local"`).
3. **Formatunterstützung**: `.gcode` (Text), `.bgcode` (Prusa-Binär, via mitgeliefertem
   C++-Binary `bgcode`, **nur Linux**), `.gx` (Flashforge).
4. **Thumbnails extrahieren**: base64-Vorschaubilder → `preview.png`, bzw. Binär-BMP aus `.gx`.
5. **Aggregation**: alle Codes werden in ein Dict gesammelt, dedupliziert/gelistet
   (`helper.add_to_dict_smart`), sortiert und in G-/M-/Sonstige-Gruppen aufgeteilt
   (`sort_and_filter_dict`) – gedacht für die Weiterverarbeitung in `chemotion-converter-app`.
6. **Ausgabe**: zeilenweise Klartext nach `output.txt`.

Die Pipeline funktioniert. Die Hauptschwächen liegen in **Bibliothekstauglichkeit,
Robustheit und Code-Hygiene**.

---

## Priorisierte Übersicht

| ID    | Prio      | Maßnahme                                                              | Aufwand | Status |
|-------|-----------|----------------------------------------------------------------------|---------|--------|
| LIB-1 | 🔴 Hoch   | `use()` Rückgabewert + konfigurierbare/optionale Output-Pfade; `print` → `logging` | mittel  | ✅ erledigt |
| ARCH-1| 🔴 Hoch   | String-Roundtrip durch Dataclass ersetzen                            | mittel  | ✅ erledigt |
| LIB-2 | 🟠 Mittel | Vorschaubild als `bytes` in `GCodeLine` führen + optional aus `use()` zurückgeben | mittel  | ✅ erledigt |
| BUG-8 | 🟠 Mittel | `.gx`-Bildextraktion an `preview_path` koppeln (Silent-Modus-Leak)  | klein   | ✅ erledigt |
| BUG-4 | 🟠 Mittel | `.gx`-Bildextraktion: BMP-Header auswerten statt fixer Offsets       | klein   | ✅ erledigt |
| TEST-1| 🟠 Mittel | pytest-Suite mit `exFiles/`                                          | mittel  |
| BUG-1 | 🟠 Mittel | Toten `resources/`-Pfad fixen                                       | klein   |
| BUG-2 | 🟠 Mittel | `subprocess` mit `check=True` + Existenzprüfung der Ausgabedatei     | klein   |
| HYG-1 | 🟢 Niedrig| Repo aufräumen (`.gitignore`, Artefakte entfernen)                  | klein   |
| SCRP-1| 🟢 Niedrig| Selenium → optionales Extra; `time.sleep` → `WebDriverWait`         | klein   |

> Empfehlung für maximale Wirkung: **LIB-1 + ARCH-1 zusammen** (saubere Bibliotheks-API mit
> strukturierter Rückgabe) – das macht das Tool für die Chemotion-Integration deutlich solider.

---

## 1. Bibliothekstauglichkeit

### LIB-1 — `use()` API-tauglich machen 🔴 ✅ ERLEDIGT (2026-06-29)
**Datei:** `gcode_translator/GCode_Translator.py`

Das Tool soll laut README in `chemotion-converter-app` eingebunden werden – dafür war `use()`
schlecht geeignet. Umgesetzt:

- [x] **Rückgabewert ergänzt.** `use()` gibt jetzt die `[g_dict, m_dict, other_dict]`-Liste zurück.
- [x] **Output-Pfade konfigurierbar / optional.** Neue Parameter `output_txt_path` und
      `preview_path`. Über einen `_UNSET`-Sentinel gilt: CLI-Modus schreibt wie bisher
      `output.txt`/`preview.png`, Bibliotheksmodus schreibt **standardmäßig keine Dateien**.
- [x] **`print()` + Emojis → `logging`.** `GCode_Translator.py`, `GCode_Mapping.py` und
      `Binary_GCode_Translator.py` nutzen jetzt modulweite Logger (`logging.getLogger(__name__)`).
      Bibliotheksmodus bleibt stumm; die CLI konfiguriert Logging in `main()`.
- [x] **`sys.exit(...)` aus der Logik entfernt.** Im Bibliotheksmodus werden jetzt Exceptions
      geworfen (`FileNotFoundError`, `ValueError`, `RuntimeError`); `sys.exit` nur noch im
      CLI-Pfad (`cli_mode`).

**Akzeptanzkriterium erfüllt:** `result = use("datei.gcode")` liefert die Dict-Liste zurück,
schreibt ohne explizite Pfadangabe keine Dateien und gibt nichts auf stdout aus (verifiziert).

**Hinweis:** Der Console-Script-Entry-Point wurde von `…:use` auf `…:main` umgestellt
(`pyproject.toml` + `entry_points.txt`).

---

### LIB-2 — Vorschaubild ohne Datei-Umweg bereitstellen 🟠 ✅ ERLEDIGT (2026-06-29)
**Datei:** `gcode_translator/GCode_Translator.py`, `gcode_translator/Binary_GCode_Translator.py`

Bisher ließ sich das Vorschaubild nur als Datei (`preview.png`) gewinnen; ein Konsument wie
`chemotion-converter-app` hatte keinen In-Memory-Zugriff. Umgesetzt:

- [x] **`GCodeLine.preview: bytes | None`** ergänzt. Bei `; thumbnail end` dekodiert
      `explain_gcode_line` den gesammelten base64-Block und legt die Roh-`bytes` in der
      zurückgegebenen `GCodeLine` ab (statt sie nur in eine Datei zu schreiben).
- [x] **Extraktion vom Datei-Schreiben entkoppelt.** Steuergröße ist jetzt
      `preview_picture_needed` (= „Aufrufer will das Bild"); geschrieben wird nur, wenn ein
      `preview_path` gesetzt ist. `transform_preview_picture()` gibt die `bytes` zurück und
      schreibt nur optional. Der Parameter `preview_pic_as_file` entfällt.
- [x] **`use(..., return_preview=True)`** gibt ein Tupel `(dict_list, previews)` zurück, wobei
      `previews` eine Liste aller extrahierten Bild-`bytes` ist (mehrere Thumbnails möglich).
      Default `return_preview=False` → unveränderte Rückgabe (rückwärtskompatibel).

**Akzeptanzkriterium:** `dicts, imgs = use("datei.gcode", return_preview=True)` liefert die
Bilddaten als `bytes`, ohne dass eine Datei entsteht (verifiziert).

---

## 2. Architektur

### ARCH-1 — String-Roundtrip durch Dataclass ersetzen 🔴 ✅ ERLEDIGT (2026-06-29)
**Datei:** `gcode_translator/GCode_Translator.py`

`explain_gcode_line` baute einen String `"G1: ... | Parameter: ..."`, den `translated_line_to_dict`
danach mit `split("|")`, `split(";")` wieder zerlegte. Fragil und doppelte Arbeit. Umgesetzt:

- [x] `explain_gcode_line` gibt jetzt ein `@dataclass GCodeLine`-Objekt zurück
      (`cmd`, `explanation`, `params`, `inline_comment`, `is_comment`, `text`) mit den
      Properties `dict_key`/`dict_value` für die Aggregation.
- [x] String-Formatierung (`text`) wird nur noch für die Datei-Ausgabe erzeugt.
- [x] `translated_line_to_dict` und `clean_str_from_dict` **entfernt**; ersetzt durch die
      strukturbasierte `add_line_to_dict(gline)`. Kein `Parameter:`-Nachputzen mehr.

**Verifiziert:** aggregiertes Dict byte-identisch zur Vorversion (Demo + echte Datei).
Gemeinsam mit LIB-1 umgesetzt.

---

## 3. Bugs & fragile Stellen

### BUG-1 — Toter Lookup-Pfad für lokale Mapping-JSON 🟠
**Datei:** `gcode_translator/GCode_Mapping.py:47`

`local_json_map_path = Path(os.getcwd()) / "resources" / ...` trifft fast nie, weil die Datei real
unter `gcode_translator/marlin_mapping.json` (kein `resources/`-Ordner) liegt. Getestet: es wird
immer der Paket-Fallback genommen.

- [ ] Entweder `resources/`-Ordner einführen und Datei dorthin verschieben, **oder** diesen Pfad
      korrigieren/entfernen und den Paket-Resource-Lookup als primären Weg dokumentieren.

### BUG-2 — `binary_gcode_to_gcode` ohne Fehlerprüfung 🟠
**Datei:** `gcode_translator/Binary_GCode_Translator.py` (`binary_gcode_to_gcode`)

- [ ] `subprocess.run(...)` mit `check=True` aufrufen (bei Fehlschlag wird aktuell trotzdem ein
      `.gcode`-Pfad zurückgegeben, der evtl. nicht existiert).
- [ ] Existenz der erzeugten `.gcode`-Datei vor dem Rückgeben prüfen.
- [ ] `chmod` nicht bei jedem Aufruf neu setzen (einmalig genügt).

### BUG-3 — `.gx` wird als UTF-8-Text gelesen 🟠
**Datei:** `gcode_translator/GCode_Translator.py:207`

`.gx` ist ein Binärformat, wird aber zeilenweise als UTF-8-Text gelesen. Nur `errors="replace"`
verhindert den Crash – sinnvoller Output entsteht kaum.

- [ ] `.gx`-Verarbeitung überdenken: Header/Binärblock korrekt parsen statt als Text einzulesen,
      oder klar dokumentieren, was unterstützt wird.

### BUG-4 — Magic Numbers in `.gx`-Bildextraktion 🟠 ✅ ERLEDIGT (2026-06-29)
**Datei:** `gcode_translator/Binary_GCode_Translator.py` (`extract_binary_picture_from_gx`)

`extract_binary_picture_from_gx(skip=58, count=14454)` passte exakt auf *eine* Beispieldatei und
generalisierte nicht — bei einer Text-`.gx` (z. B. `modern_Flashforge_Ninetales.gx`) wurden blind
14454 Müll-Bytes „extrahiert". Umgesetzt:

- [x] Neuer Helfer `_locate_embedded_bmp(header)` sucht die `BM`-Signatur und **validiert den
      BMP-Datei-Header** (reserved-Feld == 0, `54 <= pixel_offset < size`), sodass ein zufälliges
      `BM` in der Nutzlast nicht fehlinterpretiert wird.
- [x] Offset **und** Größe werden aus dem BMP-Header gelesen (`size` = uint32 LE @ +2), nicht mehr
      hartkodiert → funktioniert für beliebige Thumbnail-Auflösungen.
- [x] Es wird nur der Header-Bereich (`_HEADER_SCAN_BYTES = 4096`) plus das BMP selbst gelesen,
      nicht die ganze (ggf. viele MB große) Datei.
- [x] Gibt `None` zurück, wenn kein BMP vorhanden ist (Text-`.gx`) → keine Müll-Datei/-bytes.
- [x] `skip`/`count` bleiben als optionale Override-Parameter erhalten (Default `None` = Auto-Erkennung).

**Verifiziert:** Auto-Erkennung ist byte-identisch zur alten fixen Extraktion *und* zur
mitgelieferten Referenz-`.bmp`; Text-`.gx` liefert sauber `None`.

### BUG-5 — Fragile Kommentar-Blacklist 🟢
**Datei:** `gcode_translator/GCode_Translator.py:52` (`is_valid_comment`)

Substring-Matching: `"layer"` matcht z. B. auch „multilayer", `"type:"` matcht jedes Vorkommen.

- [ ] Wort-/Präfix-genaues Matching statt `in`-Substring-Prüfung.

### BUG-6 — Stille Trunkierung von Kommentaren 🟢
**Datei:** `gcode_translator/GCode_Translator.py:55`

`line_to_translate[1:200]` schneidet Kommentare bei 200 Zeichen ab (Magic Number).

- [ ] Konstante mit sprechendem Namen, oder Trunkierung entfernen/begründen.

### BUG-7 — Ungenutzte ABC-Abstraktion 🟢
**Datei:** `gcode_translator/GCode_Mapping.py`

`abstractmethod` wird importiert, aber nie verwendet; `fetch_gcode_mapping` ist in der Basisklasse
nur `pass`. `init_mapping` instanziiert erst `GCodeMapping()`, prüft `gcode_type`, verwirft die
Instanz und baut dann `MarlinGcodeScraper` – umständlich; die Enum-Prüfung ist effektiv tot
(immer `GENERIC`).

- [ ] Entweder `@abstractmethod` korrekt verwenden, oder die Basisklasse vereinfachen und die
      tote `gcode_type`-Prüfung in `init_mapping` entfernen.

### BUG-8 — `.gx`-Bildextraktion ignorierte den Silent-Modus 🟠 ✅ ERLEDIGT (2026-06-29)
**Datei:** `gcode_translator/GCode_Translator.py`, `gcode_translator/Binary_GCode_Translator.py`

`use()` rief für `.gx`-Dateien **immer** `extract_binary_picture_from_gx(file, "preview_gx.bmp")`
auf und schrieb so eine BMP-Datei ins Arbeitsverzeichnis – auch im Bibliotheksmodus, was dem
LIB-1-Versprechen „ohne Pfadangabe keine Dateien" widersprach. Umgesetzt:

- [x] `extract_binary_picture_from_gx(input_path, output_path=None, ...)` schreibt nur noch, wenn
      `output_path` gesetzt ist, und **gibt die `bytes` zurück** (rückwärtskompatibel für Aufrufer,
      die einen Pfad übergeben).
- [x] In `use()` wird das `.gx`-Bild nur extrahiert, wenn der Aufrufer es will (`want_preview =
      return_preview or preview_path is not None`); die BMP-Datei entsteht nur bei gesetztem
      `preview_path`. Die `bytes` fließen in die `previews`-Liste von `return_preview` ein.

**Verifiziert:** `.gx` im reinen Silent-Modus erzeugt keine `preview_gx.bmp` mehr.

---

## 4. Tests

### TEST-1 — pytest-Suite mit `exFiles/` aufbauen 🟠
Es gibt einen `exFiles/`-Ordner mit vielen Beispielen, aber **keine Tests**. Angesichts der vielen
fragilen String-Parser ist das der größte Qualitätsgewinn.

- [ ] `pytest` als Dev-Abhängigkeit aufnehmen.
- [ ] Tests für: Mapping-Lookup, Kommentar-Erkennung (`is_valid_comment`), Thumbnail-Decode,
      Dict-Aggregation (`add_to_dict_smart`, `sort_and_filter_dict`).
- [ ] Beispieldateien aus `exFiles/` als Fixtures nutzen.

---

## 5. Scraping

### SCRP-1 — Selenium robuster & optional machen 🟢
**Datei:** `gcode_translator/GCode_Mapping.py`

- [ ] `time.sleep(3)` durch `WebDriverWait` auf ein konkretes Element ersetzen (zuverlässiger).
- [ ] Selenium + Chrome als Pflicht-Abhängigkeit nur fürs gelegentliche Mapping-Update ist
      schwergewichtig. Erwägung: einfacher `requests`-Abruf, oder Selenium in ein optionales Extra
      (`pip install gcode-translator[scrape]`) auslagern, da der Normalbetrieb offline läuft.

---

## 6. Repo-Hygiene

### HYG-1 — Artefakte aus dem Repo entfernen 🟢
Im Working Tree liegen Dateien, die nicht versioniert gehören:

- `build/`
- `gcode_translator.egg-info/`
- `.idea/`
- `GCode_Translator.zip`
- `output.txt`
- `preview.png`
- `.gitignore.bak`
- `__pycache__/`
- `.bak`-Dateien in `exFiles/`

Aufgaben:

- [ ] `.gitignore` entsprechend ergänzen.
- [ ] Diese Dateien aus dem Git-Index entfernen (`git rm --cached ...`).
