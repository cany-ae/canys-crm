# -*- coding: utf-8 -*-
# Copyright (c) 2026, R&P CRM. All rights reserved.
# Landingpage Webhook API for external lead intake.
#
# Endpoint: POST /api/method/crm.api.lead_webhook.create_lead
# Health:   GET  /api/method/crm.api.lead_webhook.health
#
# Authentication: X-API-Key header must match the value of
#   crm_webhook_api_key in site_config.json.

import frappe
from frappe import _
from datetime import datetime


# --- Valid lead types (must match custom_leadtyp Select options) ---
VALID_LEADTYPEN = [
    "Pferd", "Hund", "Katze", "Oldtimer", "Geldanlage / Vallue",
    "Kinderpolice", "ManagerProtect", "JuraTax", "LOL (Loss of Licence)",
    "BU (meine-1750)", "bAV", "PilotNow", "KV Mensch Voll",
    "KV Mensch Zusatz", "Sonstiges",
]

# --- Field mapping per lead type (which extra fields to accept) ---
LEADTYPE_FIELDS = {
    "Pferd": [
        "custom_tierart", "custom_tiername", "custom_tierrasse",
        "custom_tieralter", "custom_chip_nummer", "custom_vorerkrankungen",
        "custom_aktuell_versichert", "custom_aktuelle_versicherung",
    ],
    "Hund": [
        "custom_tierart", "custom_tiername", "custom_tierrasse",
        "custom_tieralter", "custom_chip_nummer", "custom_vorerkrankungen",
        "custom_aktuell_versichert", "custom_aktuelle_versicherung",
    ],
    "Katze": [
        "custom_tierart", "custom_tiername", "custom_tierrasse",
        "custom_tieralter", "custom_chip_nummer", "custom_vorerkrankungen",
        "custom_aktuell_versichert", "custom_aktuelle_versicherung",
    ],
    "Oldtimer": [
        "custom_fahrzeugtyp", "custom_baujahr", "custom_kennzeichen",
        "custom_wert_gutachten", "custom_km_begrenzung", "custom_oldtimer_zustand",
    ],
    "KV Mensch Voll": [
        "custom_kv_typ", "custom_beruf", "custom_geburtsdatum",
        "custom_einkommen_brutto", "custom_versicherungsstatus",
        "custom_vorerkrankungen_mensch",
    ],
    "KV Mensch Zusatz": [
        "custom_kv_typ", "custom_beruf", "custom_geburtsdatum",
        "custom_einkommen_brutto", "custom_versicherungsstatus",
        "custom_vorerkrankungen_mensch",
    ],
    "Geldanlage / Vallue": [
        "custom_gewuenschte_absicherung", "custom_anlagesumme",
        "custom_arbeitgeber", "custom_finanz_notiz",
    ],
    "bAV": [
        "custom_gewuenschte_absicherung", "custom_arbeitgeber",
        "custom_finanz_notiz",
    ],
    "BU (meine-1750)": [
        "custom_beruf", "custom_geburtsdatum", "custom_einkommen_brutto",
    ],
    "Kinderpolice": [
        "custom_geburtsdatum",
    ],
}

# --- Common fields accepted for all lead types ---
COMMON_FIELDS = [
    # Core contact
    "first_name", "last_name", "email", "mobile_no", "phone",
    "organization",
    # Steuerung
    "custom_leadtyp", "custom_leadquelle", "custom_produktlinie",
    "custom_lead_potenzial", "custom_erreichbarkeit",
    # Tracking / Herkunft
    "custom_quell_url", "custom_geraet", "custom_kampagne",
    "custom_utm_source", "custom_utm_medium", "custom_utm_campaign",
    "custom_herkunft_typ",
    # DSGVO
    "custom_dsgvo_zugestimmt", "custom_dsgvo_whatsapp", "custom_dsgvo_sms",
    "custom_dsgvo_email", "custom_dsgvo_telefon",
    # Termin (optional - if landing page books appointment directly)
    "custom_termin_datum", "custom_termin_typ",
]

# --- Sanitization: only these fields may ever be written ---
ALL_ALLOWED_FIELDS = set(COMMON_FIELDS)
for _fields in LEADTYPE_FIELDS.values():
    ALL_ALLOWED_FIELDS.update(_fields)


def _authenticate():
    """Validate X-API-Key header against configured key."""
    api_key = frappe.request.headers.get("X-API-Key", "").strip()

    configured_key = frappe.conf.get("crm_webhook_api_key", "")

    if not configured_key:
        frappe.throw(
            _("Webhook API key not configured. "
              "Set crm_webhook_api_key in site_config.json."),
            frappe.AuthenticationError,
        )

    if not api_key:
        frappe.throw(
            _("Missing X-API-Key header."),
            frappe.AuthenticationError,
        )

    if api_key != configured_key:
        frappe.throw(_("Invalid API key."), frappe.AuthenticationError)


def _sanitize_string(value, max_length=500):
    """Strip and truncate a string value to prevent abuse."""
    if not isinstance(value, str):
        return value
    return value.strip()[:max_length]




def _check_duplicate_smart(data, leadtyp):
    """Smart duplicate detection for webhook lead creation.

    Returns a response dict if an active duplicate exists (caller should return it).
    Returns None if no blocking duplicate found (caller should proceed with creation).
    """
    CLOSED_PHASES = ("80 - Abschluss gewonnen", "90 - Abschluss verloren")

    # Find existing leads by email or mobile_no
    existing_leads = []

    if data.get("email"):
        leads_by_email = frappe.get_all(
            "CRM Lead",
            filters={"email": data["email"]},
            fields=["name", "custom_leadtyp", "custom_liste", "lead_name"],
        )
        existing_leads.extend(leads_by_email)

    if data.get("mobile_no"):
        leads_by_mobile = frappe.get_all(
            "CRM Lead",
            filters={"mobile_no": data["mobile_no"]},
            fields=["name", "custom_leadtyp", "custom_liste", "lead_name"],
        )
        # Deduplicate (a lead could match on both email and mobile)
        seen_names = {l["name"] for l in existing_leads}
        for lead in leads_by_mobile:
            if lead["name"] not in seen_names:
                existing_leads.append(lead)

    if not existing_leads:
        return None  # No duplicates at all, proceed with creation

    # Check for same-leadtyp duplicates that are still open
    for lead in existing_leads:
        same_type = (lead.get("custom_leadtyp") or "") == leadtyp
        is_closed = (lead.get("custom_liste") or "") in CLOSED_PHASES

        if same_type and not is_closed:
            # Active lead with same type exists => block creation, return existing
            return {
                "success": False,
                "duplicate": True,
                "lead_name": lead["name"],
                "message": _(
                    "Aktiver Lead mit gleichen Kontaktdaten und Leadtyp '{0}' "
                    "existiert bereits: {1}"
                ).format(leadtyp, lead["name"]),
            }

    # All same-type leads are closed, or leads have different types => allow creation
    return None


def _lookup_firma_berater(data, leadtyp):
    """Look up a company-advisor mapping for bAV/BU leads.

    Checks CRM Firma Berater doctype for a matching record based on:
    1. firma_url pattern in the quell_url
    2. Or explicit firma_name if provided

    Returns the advisor user email or None.
    """
    if leadtyp not in ("bAV", "BU (meine-1750)"):
        return None

    try:
        if not frappe.db.table_exists("CRM Firma Berater"):
            return None
    except Exception:
        return None

    quell_url = (data.get("custom_quell_url") or "").lower()

    # Try to match by URL pattern
    if quell_url:
        mappings = frappe.get_all(
            "CRM Firma Berater",
            filters={
                "aktiv": 1,
                "leadtyp": ["in", [leadtyp, "Beides"]],
            },
            fields=["berater", "firma_name", "firma_url"],
        )
        for m in mappings:
            url_pattern = (m.get("firma_url") or "").lower().strip()
            if url_pattern and url_pattern in quell_url:
                return m["berater"]

    # Try to match by organization/firma_name
    org = (data.get("organization") or "").strip()
    if org:
        match = frappe.get_all(
            "CRM Firma Berater",
            filters={
                "aktiv": 1,
                "firma_name": org,
                "leadtyp": ["in", [leadtyp, "Beides"]],
            },
            fields=["berater"],
            limit=1,
        )
        if match:
            return match[0]["berater"]

    return None

@frappe.whitelist(allow_guest=True, methods=["POST"])
def create_lead(**kwargs):
    """
    REST API endpoint for landing page lead intake.

    POST /api/method/crm.api.lead_webhook.create_lead

    Headers:
        X-API-Key: <configured API key from site_config.json>
        Content-Type: application/json

    Body (JSON):
        {
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": "max@example.com",
            "mobile_no": "+491234567890",
            "custom_leadtyp": "Pferd",
            "custom_leadquelle": "Landing Page",
            "custom_tierart": "Pferd",
            "custom_tiername": "Blitz",
            "custom_dsgvo_zugestimmt": 1,
            "custom_utm_source": "google",
            "custom_utm_medium": "cpc",
            "custom_quell_url": "https://example.com/pferd-versicherung"
        }

    Returns:
        {
            "success": true,
            "lead_name": "CRM-LEAD-00042",
            "liste": "10 - Neu ohne Termin",
            "message": "Lead erfolgreich erstellt"
        }
    """
    # --- Authentication ---
    _authenticate()

    # Run as Administrator after successful API key validation
    frappe.set_user('Administrator')

    # --- Parse input ---
    data = frappe._dict(kwargs)

    # --- Validate required fields ---
    if not data.get("first_name"):
        frappe.throw(_("first_name is required."), frappe.ValidationError)

    if not data.get("email") and not data.get("mobile_no"):
        frappe.throw(
            _("Either email or mobile_no is required."),
            frappe.ValidationError,
        )

    # --- Validate leadtyp ---
    leadtyp = data.get("custom_leadtyp", "Sonstiges")
    if leadtyp not in VALID_LEADTYPEN:
        frappe.throw(
            _("Invalid leadtyp: {0}. Valid options: {1}").format(
                leadtyp, ", ".join(VALID_LEADTYPEN)
            ),
            frappe.ValidationError,
        )

    # --- Smart duplicate/repeat handling ---
    # Rules:
    #   same contact + same leadtyp + open (not 80/90) => return existing (no duplicate)
    #   same contact + same leadtyp + closed (80/90) => create new (re-engagement)
    #   same contact + different leadtyp => create new (different product interest)
    dup_result = _check_duplicate_smart(data, leadtyp)
    if dup_result:
        return dup_result

    # --- Build lead document ---
    lead_data = {
        "doctype": "CRM Lead",
        "custom_liste": "10 - Neu ohne Termin",
        "status": "Nicht kontaktiert",
        "custom_leadquelle": data.get("custom_leadquelle", "Landing Page"),
        "custom_herkunft_typ": data.get("custom_herkunft_typ", "Neukunde"),
    }

    # Map common fields (sanitized)
    for field in COMMON_FIELDS:
        val = data.get(field)
        if val not in (None, ""):
            lead_data[field] = _sanitize_string(val)

    # Map leadtype-specific fields (sanitized)
    extra_fields = LEADTYPE_FIELDS.get(leadtyp, [])
    for field in extra_fields:
        val = data.get(field)
        if val not in (None, ""):
            lead_data[field] = _sanitize_string(val)

    # Auto-set tierart for animal leads if not explicitly provided
    if leadtyp in ("Pferd", "Hund", "Katze") and not lead_data.get("custom_tierart"):
        lead_data["custom_tierart"] = leadtyp

    # Ensure leadtyp is always set
    lead_data["custom_leadtyp"] = leadtyp

    # DSGVO: record consent timestamp
    if data.get("custom_dsgvo_zugestimmt"):
        lead_data["custom_dsgvo_timestamp"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    # If an appointment date is provided, set phase to 20 instead of 10
    if data.get("custom_termin_datum"):
        lead_data["custom_liste"] = "20 - Termin gebucht"
        lead_data["custom_termin_status"] = "Geplant"
        lead_data["status"] = "Termin vereinbart"

    # --- Create Lead ---
    try:
        lead = frappe.get_doc(lead_data)
        lead.flags.ignore_permissions = True
        lead.insert()

        # Firma-Berater mapping: for bAV/BU leads, check if a company-specific
        # advisor is configured and override the assignment
        firma_berater = _lookup_firma_berater(data, leadtyp)
        if firma_berater:
            frappe.db.set_value("CRM Lead", lead.name, "lead_owner", firma_berater)
            from frappe.desk.form.assign_to import add as assign_to
            try:
                assign_to({
                    "doctype": "CRM Lead",
                    "name": lead.name,
                    "assign_to": [firma_berater],
                    "description": "Automatisch zugewiesen via Firma-Berater-Zuordnung",
                })
            except Exception:
                pass  # assignment failure should not block lead creation
            frappe.logger("webhook").info(
                "Lead {0} assigned to {1} via Firma-Berater mapping".format(
                    lead.name, firma_berater
                )
            )
        else:
            # Auto-assign via round-robin (best-effort, failure must not
            # prevent lead creation)
            try:
                from crm.fcrm.doctype.crm_lead.crm_lead import auto_assign_lead
                auto_assign_lead(lead.name)
            except Exception as assign_err:
                frappe.log_error(
                    title="Webhook Lead Auto-Assign Warning",
                    message="Lead {0} created but auto-assign failed: {1}".format(
                        lead.name, str(assign_err)
                    ),
                )

        frappe.db.commit()

        frappe.logger("webhook").info(
            "Lead created via webhook: {0} (type={1}, source={2})".format(
                lead.name, leadtyp, lead_data.get("custom_leadquelle")
            )
        )

        return {
            "success": True,
            "lead_name": lead.name,
            "liste": lead.custom_liste,
            "message": _("Lead erfolgreich erstellt."),
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(
            title="Webhook Lead Creation Error",
            message="Payload: {0}\n\nError: {1}".format(
                str(data)[:2000], frappe.get_traceback()
            ),
        )
        return {
            "success": False,
            "message": _("Lead creation failed: {0}").format(str(e)),
        }


@frappe.whitelist(allow_guest=True, methods=["GET"])
def health():
    """
    Simple health check endpoint for monitoring.

    GET /api/method/crm.api.lead_webhook.health

    Returns:
        {"status": "ok", "timestamp": "2026-02-07T12:00:00"}
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }
