"""
Groq API Client für KI-gestützte Pferderasse-Analyse
"""

from groq import Groq
import sys
import os
import re

# Import Config
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import GROQ_API_KEY, GROQ_MODEL


class GroqClient:
    """Client für Groq API Anfragen"""

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL

    def query(self, prompt: str) -> str:
        """
        Sende Anfrage an Groq API

        Args:
            prompt: Die Anfrage/Frage an die KI

        Returns:
            str: Antwort der KI
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Fehler bei API-Anfrage: {str(e)}"


def query_horse_breed(breed_name: str, horse_name: str = "") -> dict:
    """
    Frage Informationen zu einer Pferderasse ab - für Angebots-Deckblatt

    Args:
        breed_name: Name der Pferderasse
        horse_name: Name des Pferdes (optional)

    Returns:
        dict: Informationen zur Rasse als professioneller Infotext
    """
    client = GroqClient()

    # Verwende Pferdename falls vorhanden, sonst generisch
    pferd_referenz = horse_name if horse_name else "{PFERDENAME}"

    # Prüfe ob Mischling/Mix-Rasse
    is_mix = any(keyword in breed_name.lower() for keyword in ['mix', 'mischling', 'kreuzung', '-mix'])

    prompt = f"""Du erstellst einen kurzen, emotional ansprechenden Infotext für das Deckblatt eines Angebots zur Pferdekranken- bzw. OP-Versicherung.
Der Text soll nicht nur informieren, sondern beim Pferdehalter bewusst Wertschätzung, Verantwortung und Schutzgedanken auslösen – dezent vertrieblich, ohne aufdringlich oder kitschig zu sein.

Eingaben:
- Pferderasse: {breed_name}
- Pferdename: {pferd_referenz}
- Länge: MAXIMAL 280 Zeichen (inkl. Leerzeichen), 2 KOMPLETTE Sätze
- Sprache: Deutsch (achte auf perfekte Rechtschreibung und Grammatik!)

Ziel des Textes:
Der Pferdehalter soll sich und sein Pferd wiedererkennen. Die besondere Beziehung zwischen Halter und Pferd soll subtil mitschwingen. Der Gedanke entstehen, dass ein passender Versicherungsschutz Ausdruck von Fürsorge und Verantwortung ist.

Stil:
Wertschätzend, professionell, warm, ruhig, vertrauensbildend. Leicht vertriebliche Tonalität mit Fokus auf Sicherheit, Verlässlichkeit und Vorsorge.

Inhaltliche Regeln:
- WICHTIG: Beginne den Text IMMER mit dem Pferdenamen! Nutze Formulierungen wie "{pferd_referenz} ist ein..." oder "Die Rasse {breed_name}, zu der {pferd_referenz} gehört, ..."
- Nutze 1–2 sichere, allgemein bekannte Eigenschaften der Rasse (z. B. Charakter, Temperament, Vielseitigkeit, typische Nutzung)
- Verbinde diese Eigenschaften sanft mit Themen wie Fürsorge, Verantwortung, langfristiger Begleitung und Schutz
- KEINE Wiederholungen! Vermeide es, die gleichen Eigenschaften mehrfach zu erwähnen (z.B. nicht "kraftvolle" und später "robust")
- Keine medizinischen Aussagen, keine Leistungs- oder Heilversprechen
- Keine Superlative, keine Übertreibungen, keine Garantien („beste", „perfekt", „garantiert")
- Keine erfundenen Zuchtlinien, keine Zahlen oder Jahresdaten
- Keine Aufzählungen, keine Emojis, keine Anführungszeichen
- Formuliere flüssig und elegant - jeder Satz sollte neue Informationen bringen
- PERFEKTE deutsche Rechtschreibung ist PFLICHT!

{"SONDERREGEL MISCHLINGE: Wenn die Rasse Mix/Mischling/Kreuzung enthält: Keine konkrete Herkunft nennen. Fokus auf Individualität, Vielseitigkeit und persönliche Stärken. Deutlich machen, dass gerade diese Einzigartigkeit einen durchdachten, verlässlichen Versicherungsschutz verdient." if is_mix else ""}

Format:
Gib ausschließlich den fertigen Text für die Rasse-Box aus (ohne Überschrift, ohne Erklärungen).
ABSOLUT KRITISCH:
- MAXIMAL 280 Zeichen! Das ist eine harte Grenze!
- GENAU 2 vollständige Sätze (nicht mehr, nicht weniger)!
- Jeder Satz MUSS mit einem Punkt enden!
- Perfekte deutsche Rechtschreibung und Grammatik!

Beispiel-Stil (nur als Stilreferenz, nicht kopieren):
"{pferd_referenz} ist ein Arabisches Vollblut, eine Rasse, die für ihre Eleganz und ihren feinfühligen Charakter geschätzt wird. Als treuer Begleiter verdient {pferd_referenz} einen Versicherungsschutz, der dieser besonderen Verbindung gerecht wird."
"""

    response = client.query(prompt).strip()

    # STRENGE Sicherheitsprüfung: Entferne abgeschnittene Sätze
    # 1. Prüfe ob Text mit Satzzeichen endet (., !, ?)
    if not response or response[-1] not in '.!?':
        # Finde letzten vollständigen Satz
        last_period = max(response.rfind('.'), response.rfind('!'), response.rfind('?'))
        if last_period > 0:
            response = response[:last_period + 1]
        else:
            # Kein vollständiger Satz gefunden - Fehlerfall
            response = ""

    # 2. Prüfe Zeichenlänge und kürze auf MAXIMAL 300 Zeichen (mit Puffer)
    if len(response) > 300:
        # Finde letzten vollständigen Satz unter 300 Zeichen
        # Split bei ". " um Sätze zu trennen
        sentences = []
        current_pos = 0

        for match in re.finditer(r'[.!?]\s+', response):
            sentence = response[current_pos:match.end()].strip()
            sentences.append(sentence)
            current_pos = match.end()

        # Letzter Satz (falls kein Leerzeichen nach Punkt)
        if current_pos < len(response):
            sentences.append(response[current_pos:].strip())

        # Baue Text aus vollständigen Sätzen zusammen (max 300 Zeichen)
        result = ""
        for sentence in sentences:
            test = (result + " " + sentence).strip() if result else sentence
            if len(test) <= 300:
                result = test
            else:
                break

        response = result if result and result.endswith(('.', '!', '?')) else ""

    # 3. Finale Validierung
    if not response or len(response) > 300 or response[-1] not in '.!?':
        # Fallback: Wenn immer noch ungültig, leeren String zurückgeben
        print(f"⚠️ KI-Text ungültig (Länge: {len(response)}, endet mit: '{response[-1] if response else 'N/A'}')")
        response = ""

    return {
        "breed": breed_name,
        "horse_name": horse_name,
        "info": response
    }


if __name__ == "__main__":
    # Test mit verschiedenen Rassen
    print("=" * 70)
    print("🐴 Groq API Test - Pferderassen-Infotexte")
    print("=" * 70)
    print()

    test_breeds = [
        ("Achal Tekkiner", "Golden Dream"),
        ("Hannoveraner", "Donnerhall"),
        ("Shetlandpony", "Little Star")
    ]

    for breed, name in test_breeds:
        print(f"📝 Test: {breed} (Pferdename: {name})")
        print("-" * 70)
        result = query_horse_breed(breed, name)
        print(result["info"])
        print()
        print()
