# Lokale AI-Modelle

Die AI-Modelle werden aus Datenschutz-, Größen- und Reproduzierbarkeitsgründen nicht in das GitHub-Repository hochgeladen.

Lokaler Modellpfad für den bisherigen Ollama-Modellbestand:

```text
C:\Einrichtung\05_AI\models
```

Aktuell verwendete Modelltags werden in den Test- und Qualifikationsreports dokumentiert. Das Repository enthält nur Skripte, Konfigurationsexamples, Testdefinitionen und Reports; Modellblobs, Binaries, Caches und lokale Laufzeitdaten bleiben lokal.

## Bonsai 2 — separater experimenteller Server

Bonsai 2 wird separat und **nicht über Ollama** unter folgendem Pfad installiert:

```text
C:\Einrichtung\05_AI\bonsai
```

Der aktuell getestete Server stellt eine OpenAI-kompatible API unter `http://127.0.0.1:8080/v1` bereit. Die lokal erfolgreich verwendete Modell-ID lautet `bonsai2-gguf/27B`; vor Verwendung soll sie über `/v1/models` geprüft werden.

- Server-/Modellqualifikation: [Bonsai Provider Specification](../07_Keystone/BONSAI_PROVIDER.md)
- Keystone-Architektur: [ARCHITECTURE.md](../07_Keystone/ARCHITECTURE.md)

Bonsai ist derzeit ein experimenteller Kandidat, noch kein in Keystone implementierter Provider. Kein automatischer Download, Autostart oder Cloud-Fallback wird durch diese Dokumentation aktiviert. Ollama und bestehende Modellordner bleiben unverändert.
