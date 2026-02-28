# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMAppointment(Document):
    """CRM Appointment manages termin records linked to CRM Leads.

    On every insert/update the latest appointment data is synced back
    to the lead's inline termin fields (custom_termin_datum, etc.)
    so both data models stay in sync.
    """

    def validate(self):
        self._validate_termin_datum()
        self._validate_zeit()

    def _validate_termin_datum(self):
        """Ensure termin_datum is present (already reqd, but extra safety)."""
        if not self.termin_datum:
            frappe.throw(_("Termin Datum ist erforderlich."))

    def _validate_zeit(self):
        """If both times set, ensure von < bis."""
        if self.termin_zeit_von and self.termin_zeit_bis:
            from frappe.utils import get_time
            t_von = get_time(self.termin_zeit_von)
            t_bis = get_time(self.termin_zeit_bis)
            if t_von >= t_bis:
                frappe.throw(_("Uhrzeit von muss vor Uhrzeit bis liegen."))

    def after_insert(self):
        self.sync_to_lead()

    def on_update(self):
        self.sync_to_lead()

    def sync_to_lead(self):
        """Sync the latest appointment back to the CRM Lead inline fields.

        Always writes the most recent (by termin_datum DESC) appointment
        of this lead back to the lead record, so the lead always reflects
        the current/next appointment state.

        Skips sync when flags.skip_lead_sync is set (e.g. when called from
        execute_lead_action which already manages the lead fields itself).
        Uses update_modified=False to prevent timestamp conflicts.
        """
        if not self.lead:
            return

        # Skip if caller already manages the lead (avoids TimestampMismatchError)
        if getattr(self.flags, "skip_lead_sync", False):
            return

        try:
            # Find the latest appointment for this lead (by termin_datum)
            latest = frappe.db.sql("""
                SELECT name, termin_datum, status, typ, berater, notiz
                FROM `tabCRM Appointment`
                WHERE lead = %(lead)s
                ORDER BY termin_datum DESC, creation DESC
                LIMIT 1
            """, {"lead": self.lead}, as_dict=True)

            if not latest:
                return

            apt = latest[0]

            # Update lead inline fields directly via frappe.db.set_value
            # with update_modified=False to avoid timestamp conflicts
            frappe.db.set_value("CRM Lead", self.lead, {
                "custom_termin_datum": str(apt.termin_datum) if apt.termin_datum else None,
                "custom_termin_status": apt.status or "Geplant",
                "custom_termin_typ": apt.typ or "Ersttermin",
                "custom_termin_berater": apt.berater or "",
            }, update_modified=False)

            if apt.notiz:
                frappe.db.set_value("CRM Lead", self.lead,
                    "custom_termin_notiz", apt.notiz, update_modified=False)

        except Exception:
            frappe.log_error(
                "CRM Appointment sync_to_lead failed for appointment {0}, lead {1}".format(
                    self.name, self.lead
                )
            )

    @staticmethod
    def default_list_data():
        columns = [
            {"label": "Lead", "type": "Link", "key": "lead", "width": "10rem"},
            {"label": "Lead Name", "type": "Data", "key": "lead_name", "width": "12rem"},
            {"label": "Datum", "type": "Date", "key": "termin_datum", "width": "8rem"},
            {"label": "Typ", "type": "Select", "key": "typ", "width": "8rem"},
            {"label": "Status", "type": "Select", "key": "status", "width": "8rem"},
            {"label": "Berater", "type": "Link", "key": "berater", "width": "10rem"},
            {"label": "Quelle", "type": "Select", "key": "quelle", "width": "8rem"},
        ]
        rows = [
            "name", "lead", "lead_name", "termin_datum",
            "termin_zeit_von", "termin_zeit_bis",
            "typ", "status", "berater", "quelle",
            "event_link", "notiz", "modified",
        ]
        return {"columns": columns, "rows": rows}


# ── Whitelisted API ─────────────────────────────────────────────────────

@frappe.whitelist()
def get_appointments_for_lead(lead_name):
    """Return all appointments for a given lead, newest first."""
    if not lead_name:
        return []
    if not frappe.has_permission("CRM Appointment", "read"):
        frappe.throw(_("Keine Berechtigung"), frappe.PermissionError)

    return frappe.get_all(
        "CRM Appointment",
        filters={"lead": lead_name},
        fields=[
            "name", "lead", "lead_name", "berater",
            "termin_datum", "termin_zeit_von", "termin_zeit_bis",
            "typ", "status", "quelle", "event_link", "notiz",
            "creation", "modified",
        ],
        order_by="termin_datum desc, creation desc",
    )


@frappe.whitelist()
def get_upcoming_appointments(user=None, days=7):
    """Return upcoming appointments within N days for a user (or all for admin)."""
    import datetime as dt

    if not frappe.has_permission("CRM Appointment", "read"):
        frappe.throw(_("Keine Berechtigung"), frappe.PermissionError)

    if not user:
        user = frappe.session.user

    today = frappe.utils.today()
    end_date = frappe.utils.add_days(today, int(days))

    filters = {
        "termin_datum": ["between", [today, end_date]],
        "status": ["in", ["Geplant", "Bestaetigt"]],
    }

    is_admin = "System Manager" in frappe.get_roles(user)
    if not is_admin:
        filters["berater"] = user

    return frappe.get_all(
        "CRM Appointment",
        filters=filters,
        fields=[
            "name", "lead", "lead_name", "berater",
            "termin_datum", "termin_zeit_von", "termin_zeit_bis",
            "typ", "status", "quelle", "notiz",
        ],
        order_by="termin_datum asc, termin_zeit_von asc",
    )
