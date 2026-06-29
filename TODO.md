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
| FEAT-1| 🟠 Mittel | `; key = value` / `; key: value`-Metadaten in `other_dict` aufnehmen | mittel  | ✅ erledigt |
| BUG-5 | 🟠 Mittel | Blacklist: sinnvolle `=`-Settings nicht mehr fälschlich verwerfen    | klein   | ✅ erledigt |
| FEAT-2| 🟠 Mittel | Hochfrequente Befehle nicht als Riesen-Liste sammeln (Dedup/Zählung) | mittel  | offen |
| BUG-9 | 🟠 Mittel | Inline-Kommentar vom Befehls-Token trennen; Special/Unknown-Semantik | klein   | ✅ erledigt |
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

### FEAT-1 — Slicer-Metadaten (`key = value` / `key: value`) in `other_dict` 🟠 ✅ ERLEDIGT (2026-06-29)
**Datei:** `gcode_translator/GCode_Translator.py`

Deklarative Metadaten wie `; temperature = 220`, `; filament_type = PLA` oder `; nozzle_diameter = 0.4`
landeten bisher gar nicht im Ergebnis-Dict (sie sind keine G/M-Befehle) — gerade Werte ohne
Befehlsäquivalent gingen für den Converter komplett verloren. Umgesetzt:

- [x] `GCodeLine` um `meta_key`/`meta_value` (+ Property `is_metadata`) erweitert.
- [x] Innerhalb des „sinnvoller Kommentar"-Zweigs erkennt `explain_gcode_line` über
      `_META_PAIR_RE` Paare der Form `; key = value` **oder** `; key: value`.
- [x] **Abgrenzung gegen Rauschen:** Wert muss nicht-leer sein (`; design parameters:` bleibt
      Kommentar); die bestehende Blacklist fängt Per-Layer-Marker (`;LAYER:`, `;HEIGHT:`,
      `; end of layer_num:` …) ab; Single-Letter-Keys (`;Z:0.2`, `; T = 5`) werden über
      `_META_MIN_KEY_LEN = 2` ausgeschlossen (G-Code-Achsen-Marker, kein Setting).
- [x] Paare werden in `meta_dict` gesammelt und in `sort_and_filter_dict` **immer** in
      `other_dict` einsortiert (unabhängig vom Anfangsbuchstaben des Keys).

**Verifiziert:** PrusaSlicer-Config wird vollständig erfasst (297 Einträge inkl.
`temperature`, `bed_temperature`, `filament_type`, `nozzle_diameter`); `g_dict`/`m_dict` bleiben
byte-identisch zur Vorversion; `;Z:`-Per-Layer-Marker landen **nicht** im Dict.

**Nachtrag:** Die ursprünglich hier vermerkte Einschränkung (Settings mit Teilwort `layer` gingen
verloren) wurde mit **BUG-5** behoben — `=`-Settings umgehen jetzt die Blacklist.

---

### FEAT-2 — Hochfrequente Befehle nicht als Riesen-Liste sammeln 🟠
**Datei:** `gcode_translator/GCode_Translator.py` (`add_line_to_dict`), `gcode_translator/helper.py`
(`add_to_dict_smart`)

`add_to_dict_smart` sammelt **jedes** Vorkommen eines Befehls als Listenelement (Duplikate erlaubt).
Bei hochfrequenten Befehlen ohne G/M-Mapping (z. B. Klipper-Makros wie `SET_VELOCITY_LIMIT`,
`EXCLUDE_OBJECT_START/END`) entstehen so riesige Listen — in der Datei
`4color_necroDragon_PLA_0.2_3h39m58s.gcode` z. B. **59 825** Elemente unter einem einzigen
`other_dict`-Key. Das bläht Rückgabe/`output.txt` auf und ist für den Converter kaum nutzbar.

Hinweis: Betrifft genauso die regulären Bewegungsbefehle (`G1: Linear Move` hatte dort ~579 000
Parameter-Einträge) — das ist dasselbe Aggregationsmuster.

Mögliche Ansätze (zu entscheiden):
- [ ] Werte pro Key **deduplizieren** (Menge statt Liste), optional mit Häufigkeitszähler
      (`{value: count}`).
- [ ] Obergrenze pro Key (Top-N) mit explizitem `log()`-Hinweis auf Trunkierung (kein stilles Kürzen).
- [ ] Für reine Bewegungsbefehle (`G0/G1/G2/G3`) ggf. nur Aggregat (Anzahl, Achsen-Wertebereiche)
      statt aller Parameter.
- [ ] Verhalten konfigurierbar machen (Default abwärtskompatibel?).

**Kontext:** Aufgekommen beim necroDragon-Test im Rahmen von BUG-5; rein vorbestehendes
Aggregationsverhalten, unabhängig von [[FEAT-1]]/BUG-5.

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

### BUG-9 — Inline-Kommentar am Befehl + Special/Unknown-Semantik 🟠 ✅ ERLEDIGT (2026-06-29)
**Datei:** `gcode_translator/GCode_Translator.py` (`explain_gcode_line`, `GCodeLine.dict_key/dict_value`)

`M84; disable motors` (Semikolon **ohne** Leerzeichen am Befehl) erzeugte das Token `M84;`, das
kein Mapping trifft → kaputter/uneinheitlicher Key (`M84;: Unknown command`), während
`M84 ; disable motors` einen anderen Key ergab. Umgesetzt:

- [x] Inline-Kommentar wird per `partition(";")` **vor** dem Tokenisieren abgetrennt → `cmd` ist
      immer sauber (`M84`), unabhängig vom Leerzeichen-Stil.
- [x] `explanation` ist jetzt `None`, wenn kein Mapping-Treffer existiert (statt des Sentinels
      `"Unknown command"`/`"Unknown mapping"`) — klare Unterscheidung.
- [x] **Neue Schlüssel-Semantik** (wie vom Nutzer vorgegeben):
      - Mapping-Treffer → `"<cmd>: <Beschreibung>"`, Value = Parameter.
      - Kein Mapping, **aber** Erklärung (inline-Kommentar) → Key `"<cmd>: Special command"`,
        **Value = die Erklärung** (z. B. `M84: Special command` → `disable motors`).
      - Kein Mapping **und** keine Erklärung → Key `"<cmd>: Unknown command"`, Value = Parameter.
- [x] Die `output.txt`-Zeile behält die Erklärung lesbar inline
      (`M84: Special command - disable motors | Parameter: True`).

**Verifiziert (necroDragon):** `M84: Special command` = `disable motors`; `T0/T1/T2: Special command`
(mit „change extruder"), `T3: Unknown command` (ohne); `SET_VELOCITY_LIMIT`/`EXCLUDE_OBJECT_*:
Unknown command`; `g_dict` (bekannte Befehle) byte-identisch zur Vorversion.

**Edge-Case:** Bei einem Special command mit *zusätzlichen* echten Parametern (`M998 S1 ; custom`)
wird die Erklärung als Value priorisiert (`custom`); die Parameter bleiben in `output.txt` sichtbar.

### BUG-5 — Fragile Kommentar-Blacklist 🟠 ✅ ERLEDIGT (2026-06-29)
**Datei:** `gcode_translator/GCode_Translator.py` (`explain_gcode_line`)

Die Substring-Blacklist (`"layer"`) verwarf auch sinnvolle Settings mit Teilwort `layer`
(z. B. `layer_height`, `first_layer_temperature` — in einer realen Datei **56 Stück**).

**Erkenntnis aus den Beispieldateien:** Echte Slicer-Settings nutzen `=`; das Per-Layer-Rauschen
(`;LAYER:5`, `;HEIGHT:0.2`, `; end of layer_num: …` — bis zu 362×/Datei) nutzt `:` oder gar keinen
Separator. Reines Umstellen der Blacklist auf Wortgrenzen würde `layer_num` **nicht** von
`layer_height` trennen. Daher gewählter, robusterer Ansatz:

- [x] **`=`-Paare umgehen die Blacklist** (`_META_EQ_RE`) — zuverlässige Settings werden immer als
      Metadaten erfasst, auch mit Teilwort `layer`.
- [x] **`:`-Paare unterliegen weiter der (unveränderten) Blacklist** (`_META_COLON_RE`) — dort lebt
      das Per-Layer-Rauschen; Leerzeichen im Key bleiben erlaubt, sodass `; Filament used: 1.2m`
      durchkommt, `; end of layer_num: …` aber von „layer" geblockt wird.

**Verifiziert (necroDragon):** `other_dict` 491 → 576; **70** `layer`-Settings jetzt erfasst
(`layer_height=0.2`, `first_layer_temperature=230`, `total_layers=328`, `first_layer_bed_temperature=55` …);
**kein** `;LAYER:`/`;HEIGHT:`/`end of layer_num`/`AFTER_LAYER_CHANGE` im Dict; `g_dict`/`m_dict`
unverändert (einzige Abweichung zur HEAD-Version: ein vorher durch den String-Roundtrip-Bug
zerstörter `M84;`-Key ist jetzt sauber — eine ARCH-1-Bereinigung).

**Hinweis:** `is_valid_comment` selbst nutzt weiterhin Substring-Matching; das ist jetzt aber nur
noch für `:`-Zeilen relevant (gewollt, da dort das Rauschen sitzt).

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
