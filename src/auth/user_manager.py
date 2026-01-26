"""
User-Management für Vertriebler
Verwaltet Vertriebler-Daten in JSON-Datei
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import shutil
from datetime import datetime, timedelta


class UserManager:
    """Verwaltet Vertriebler und ihre Templates"""

    def __init__(self, data_file: str = None):
        """
        Initialisiere User Manager

        Args:
            data_file: Pfad zur JSON-Datei (Standard: data/users.json)
        """
        if data_file is None:
            data_file = Path(__file__).parent.parent.parent / "data" / "users.json"

        self.data_file = Path(data_file)
        self.templates_dir = Path(__file__).parent.parent.parent / "templates"

        # Erstelle Verzeichnisse falls nicht vorhanden
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialisiere Daten
        self._init_data()

    def _init_data(self):
        """Initialisiere JSON-Datei falls nicht vorhanden"""
        if not self.data_file.exists():
            initial_data = {
                "users": []
            }
            self._save_data(initial_data)

    def _load_data(self) -> Dict:
        """Lade Daten aus JSON-Datei"""
        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_data(self, data: Dict):
        """Speichere Daten in JSON-Datei"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_user(self, vorname: str, nachname: str, template_path: str = None) -> Dict:
        """
        Erstelle neuen Vertriebler

        Args:
            vorname: Vorname
            nachname: Nachname
            template_path: Pfad zum Template (Teil1.pdf)

        Returns:
            Dictionary mit User-Daten

        Raises:
            ValueError: Wenn User bereits existiert
        """
        # Login generieren (VornameNachname ohne Leerzeichen)
        login = f"{vorname}{nachname}".replace(" ", "")

        # Prüfe ob User bereits existiert
        if self.get_user_by_login(login):
            raise ValueError(f"Vertriebler mit Login '{login}' existiert bereits")

        # Erstelle User-Ordner
        user_folder = self.templates_dir / login.lower()
        user_folder.mkdir(parents=True, exist_ok=True)

        # Kopiere Template falls vorhanden
        template_file = None
        if template_path and Path(template_path).exists():
            template_file = user_folder / "vorlage.pdf"
            shutil.copy(template_path, template_file)
            template_file = str(template_file.relative_to(self.templates_dir.parent))

        # User-Daten
        user = {
            "id": self._get_next_id(),
            "vorname": vorname.strip(),
            "nachname": nachname.strip(),
            "login": login,
            "template": template_file,
            "active": True,
            "last_login": None
        }

        # Speichere
        data = self._load_data()
        data["users"].append(user)
        self._save_data(data)

        return user

    def update_user(self, user_id: int, vorname: str = None, nachname: str = None,
                    template_path: str = None, active: bool = None) -> Dict:
        """
        Aktualisiere Vertriebler

        Args:
            user_id: User-ID
            vorname: Neuer Vorname (optional)
            nachname: Neuer Nachname (optional)
            template_path: Neuer Template-Pfad (optional)
            active: Aktiv-Status (optional)

        Returns:
            Aktualisierte User-Daten

        Raises:
            ValueError: Wenn User nicht gefunden
        """
        data = self._load_data()
        user = None
        user_index = None

        for i, u in enumerate(data["users"]):
            if u["id"] == user_id:
                user = u
                user_index = i
                break

        if not user:
            raise ValueError(f"Vertriebler mit ID {user_id} nicht gefunden")

        old_login = user["login"]

        # Aktualisiere Felder
        if vorname:
            user["vorname"] = vorname.strip()
        if nachname:
            user["nachname"] = nachname.strip()
        if active is not None:
            user["active"] = active

        # Neuer Login bei Name-Änderung
        new_login = f"{user['vorname']}{user['nachname']}".replace(" ", "")
        if new_login != old_login:
            # Prüfe ob neuer Login bereits existiert
            if self.get_user_by_login(new_login):
                raise ValueError(f"Vertriebler mit Login '{new_login}' existiert bereits")

            # Benenne Ordner um
            old_folder = self.templates_dir / old_login.lower()
            new_folder = self.templates_dir / new_login.lower()
            if old_folder.exists():
                old_folder.rename(new_folder)

            user["login"] = new_login

        # Aktualisiere Template
        if template_path:
            user_folder = self.templates_dir / user["login"].lower()
            user_folder.mkdir(parents=True, exist_ok=True)

            template_file = user_folder / "vorlage.pdf"
            shutil.copy(template_path, template_file)
            user["template"] = str(template_file.relative_to(self.templates_dir.parent))

        # Speichere
        data["users"][user_index] = user
        self._save_data(data)

        return user

    def delete_user(self, user_id: int):
        """
        Lösche Vertriebler

        Args:
            user_id: User-ID

        Raises:
            ValueError: Wenn User nicht gefunden
        """
        data = self._load_data()
        user = None
        user_index = None

        for i, u in enumerate(data["users"]):
            if u["id"] == user_id:
                user = u
                user_index = i
                break

        if not user:
            raise ValueError(f"Vertriebler mit ID {user_id} nicht gefunden")

        # Lösche Ordner
        user_folder = self.templates_dir / user["login"].lower()
        if user_folder.exists():
            shutil.rmtree(user_folder)

        # Lösche aus Daten
        data["users"].pop(user_index)
        self._save_data(data)

    def get_user_by_login(self, login: str) -> Optional[Dict]:
        """
        Hole User anhand Login

        Args:
            login: Login-Name

        Returns:
            User-Daten oder None
        """
        data = self._load_data()
        for user in data["users"]:
            if user["login"].lower() == login.lower():
                return user
        return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Hole User anhand ID

        Args:
            user_id: User-ID

        Returns:
            User-Daten oder None
        """
        data = self._load_data()
        for user in data["users"]:
            if user["id"] == user_id:
                return user
        return None

    def get_all_users(self) -> List[Dict]:
        """
        Hole alle Vertriebler

        Returns:
            Liste aller Vertriebler
        """
        data = self._load_data()
        return data["users"]

    def get_active_users(self) -> List[Dict]:
        """
        Hole alle aktiven Vertriebler

        Returns:
            Liste der aktiven Vertriebler
        """
        data = self._load_data()
        return [u for u in data["users"] if u.get("active", True)]

    def authenticate(self, login: str) -> Optional[Dict]:
        """
        Authentifiziere User

        Args:
            login: Login-Name

        Returns:
            User-Daten bei Erfolg, None bei Fehler
        """
        # Admin-Login
        if login.lower() == "admin":
            return {
                "id": -1,
                "vorname": "Admin",
                "nachname": "",
                "login": "Admin",
                "role": "admin",
                "active": True
            }

        # Vertriebler-Login
        user = self.get_user_by_login(login)
        if user and user.get("active", True):
            # Aktualisiere last_login
            self.update_last_login(user["id"])
            # Hole aktualisierten User
            user = self.get_user_by_id(user["id"])
            user["role"] = "user"
            return user

        return None

    def update_last_login(self, user_id: int):
        """
        Aktualisiere letzten Login-Zeitpunkt

        Args:
            user_id: User-ID
        """
        data = self._load_data()

        for user in data["users"]:
            if user["id"] == user_id:
                user["last_login"] = datetime.now().isoformat()
                break

        self._save_data(data)

    def is_user_active(self, user: Dict) -> bool:
        """
        Prüfe ob User in den letzten 30 Tagen aktiv war

        Args:
            user: User-Daten

        Returns:
            True wenn aktiv (letzter Login < 30 Tage), sonst False
        """
        last_login_str = user.get("last_login")

        if not last_login_str:
            return False

        try:
            last_login = datetime.fromisoformat(last_login_str)
            days_ago = (datetime.now() - last_login).days
            return days_ago <= 30
        except (ValueError, TypeError):
            return False

    def get_active_user_count(self) -> int:
        """
        Hole Anzahl aktiver Vertriebler (letzter Login < 30 Tage)

        Returns:
            Anzahl aktiver Vertriebler
        """
        users = self.get_all_users()
        return sum(1 for user in users if self.is_user_active(user))

    def get_inactive_user_count(self) -> int:
        """
        Hole Anzahl inaktiver Vertriebler (letzter Login > 30 Tage oder nie eingeloggt)

        Returns:
            Anzahl inaktiver Vertriebler
        """
        users = self.get_all_users()
        return sum(1 for user in users if not self.is_user_active(user))

    def get_user_template_path(self, user_id: int) -> Optional[Path]:
        """
        Hole Template-Pfad für User

        Args:
            user_id: User-ID

        Returns:
            Absoluter Pfad zum Template oder None
        """
        user = self.get_user_by_id(user_id)
        if not user or not user.get("template"):
            return None

        template_path = self.templates_dir.parent / user["template"]
        if template_path.exists():
            return template_path

        return None

    def _get_next_id(self) -> int:
        """Hole nächste verfügbare ID"""
        data = self._load_data()
        if not data["users"]:
            return 1
        return max(u["id"] for u in data["users"]) + 1
