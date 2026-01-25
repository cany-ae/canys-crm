"""
Hilfs-Script zum Erstellen aller 7 Vertriebler-Templates
"""

from pathlib import Path
from pptx_manager.generator import PPTXGenerator


def create_all_templates():
    """Erstelle Templates für alle 7 Vertriebler"""
    template_dir = Path(__file__).parent.parent.parent / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)

    print("Erstelle Vertriebler-Templates...")
    print(f"Zielverzeichnis: {template_dir}\n")

    for i in range(1, 8):
        vertriebler_name = f"Vertriebler {i}"
        generator = PPTXGenerator(vertriebler_name)

        template_path = generator.create_template(vertriebler_name)
        print(f"✓ {vertriebler_name}: {Path(template_path).name}")

    print(f"\n✓ Alle Templates erstellt in: {template_dir}")


if __name__ == "__main__":
    create_all_templates()
