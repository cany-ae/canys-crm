"""
Setup script for CRM Vertrieb role and all custom fields on CRM Lead.
Run on server with: bench --site eco.canys.de execute crm.setup_role_and_fields.run
Or manually via bench console.
"""
import frappe


def create_role():
    """Create the overarching CRM Vertrieb role."""
    role_name = "CRM Vertrieb"
    if not frappe.db.exists("Role", role_name):
        role = frappe.get_doc({
            "doctype": "Role",
            "role_name": role_name,
            "desk_access": 1,
            "is_custom": 1,
            "restrict_to_domain": "",
        })
        role.insert(ignore_permissions=True)
        print(f"Role '{role_name}' created.")
    else:
        print(f"Role '{role_name}' already exists.")

    # Grant permissions on CRM Lead for this role
    perms_to_set = [
        {"doctype": "CRM Lead", "role": role_name, "permlevel": 0,
         "read": 1, "write": 1, "create": 1, "delete": 0, "submit": 0,
         "cancel": 0, "amend": 0, "report": 1, "export": 1, "import": 1,
         "share": 1, "print": 1, "email": 1},
    ]

    for perm in perms_to_set:
        existing = frappe.db.exists("Custom DocPerm", {
            "parent": perm["doctype"],
            "role": perm["role"],
            "permlevel": perm["permlevel"],
        })
        if not existing:
            cdp = frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": perm["doctype"],
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": perm["role"],
                "permlevel": perm["permlevel"],
                "read": perm.get("read", 0),
                "write": perm.get("write", 0),
                "create": perm.get("create", 0),
                "delete": perm.get("delete", 0),
                "submit": perm.get("submit", 0),
                "cancel": perm.get("cancel", 0),
                "amend": perm.get("amend", 0),
                "report": perm.get("report", 0),
                "export": perm.get("export", 0),
                "set_user_permissions": 0,
                "share": perm.get("share", 0),
                "print": perm.get("print", 0),
                "email": perm.get("email", 0),
                "if_owner": 0,
            })
            cdp.insert(ignore_permissions=True)
            print(f"Permission for '{perm['role']}' on '{perm['doctype']}' created.")
        else:
            print(f"Permission for '{perm['role']}' on '{perm['doctype']}' already exists.")


def create_custom_fields():
    """Create all custom fields on CRM Lead."""
    # Get max idx of existing custom fields for ordering
    max_idx = frappe.db.sql(
        "SELECT MAX(idx) FROM `tabCustom Field` WHERE dt='CRM Lead'"
    )
    start_idx = (max_idx[0][0] or 0) + 1

    fields = []
    idx = start_idx

    # =====================================================
    # SECTION: Steuerungsfelder (Core Pipeline Fields)
    # =====================================================
    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_steuerung_section",
        "fieldtype": "Section Break",
        "label": "Steuerung & Klassifizierung",
        "insert_after": "custom_liste",
        "idx": idx,
        "collapsible": 0,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_leadtyp",
        "fieldtype": "Select",
        "label": "Leadtyp",
        "insert_after": "custom_steuerung_section",
        "idx": idx,
        "options": "\nPferd\nHund\nKatze\nOldtimer\nGeldanlage / Vallue\nKinderpolice\nManagerProtect\nJuraTax\nLOL (Loss of Licence)\nBU (meine-1750)\nbAV\nPilotNow\nKV Mensch Voll\nKV Mensch Zusatz\nSonstiges",
        "reqd": 0,
        "in_list_view": 1,
        "in_standard_filter": 1,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_leadquelle",
        "fieldtype": "Select",
        "label": "Leadquelle",
        "insert_after": "custom_leadtyp",
        "idx": idx,
        "options": "\nFacebook\nInstagram\nGoogle Ads\nLanding Page\nEmpfehlung\nBestandskunde\nManuell\nTelefon\nMesse\nPartner\nSonstiges",
        "reqd": 0,
        "in_standard_filter": 1,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_produktlinie",
        "fieldtype": "Select",
        "label": "Produktlinie",
        "insert_after": "custom_leadquelle",
        "idx": idx,
        "options": "\nKV Tier\nKV Mensch\nSach / Oldtimer\nFinanz / Anlage\nbAV\nSonstiges",
        "reqd": 0,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_col_break_steuerung",
        "fieldtype": "Column Break",
        "insert_after": "custom_produktlinie",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_lead_potenzial",
        "fieldtype": "Select",
        "label": "Potenzial",
        "insert_after": "custom_col_break_steuerung",
        "idx": idx,
        "options": "\nHoch\nMittel\nNiedrig",
        "reqd": 0,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_zustaendige_rolle",
        "fieldtype": "Select",
        "label": "Zustaendige Rolle",
        "insert_after": "custom_lead_potenzial",
        "idx": idx,
        "options": "\nCRM Vertrieb\nSetter\nOpener\nCloser\nSpezialist\nTeamlead\nGF/Admin",
        "reqd": 0,
        "default": "CRM Vertrieb",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_herkunft_typ",
        "fieldtype": "Select",
        "label": "Herkunft",
        "insert_after": "custom_zustaendige_rolle",
        "idx": idx,
        "options": "\nNeukunde\nBestandskunde\nEmpfehlung",
        "reqd": 0,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_erreichbarkeit",
        "fieldtype": "Select",
        "label": "Erreichbarkeit",
        "insert_after": "custom_herkunft_typ",
        "idx": idx,
        "options": "\nMorgens (8-12)\nMittags (12-15)\nAbends (15-20)\nFlexibel\nNur Wochenende",
        "reqd": 0,
    })
    idx += 1

    # =====================================================
    # SECTION: Follow-up & Kontakt
    # =====================================================
    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_followup_section",
        "fieldtype": "Section Break",
        "label": "Follow-up & Kontakt",
        "insert_after": "custom_erreichbarkeit",
        "idx": idx,
        "collapsible": 0,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_naechster_kontakt",
        "fieldtype": "Datetime",
        "label": "Naechster Kontakt",
        "insert_after": "custom_followup_section",
        "idx": idx,
        "reqd": 0,
        "description": "Wann soll der Lead als naechstes kontaktiert werden?",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_followup_grund",
        "fieldtype": "Select",
        "label": "Follow-up Grund",
        "insert_after": "custom_naechster_kontakt",
        "idx": idx,
        "options": "\nErstkontakt\nRueckruf vereinbart\nTerminerinnerung\nNachfass nach Termin\nReaktivierung\nCross-Selling\nDokumente ausstehend\nSonstiges",
        "reqd": 0,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_kontaktversuche",
        "fieldtype": "Int",
        "label": "Kontaktversuche",
        "insert_after": "custom_followup_grund",
        "idx": idx,
        "default": "0",
        "description": "Anzahl bisheriger Kontaktversuche",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_col_break_followup",
        "fieldtype": "Column Break",
        "insert_after": "custom_kontaktversuche",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_letzter_kontakt",
        "fieldtype": "Datetime",
        "label": "Letzter Kontakt",
        "insert_after": "custom_col_break_followup",
        "idx": idx,
        "read_only": 1,
        "description": "Wird automatisch aktualisiert",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_letzte_kontaktart",
        "fieldtype": "Select",
        "label": "Letzte Kontaktart",
        "insert_after": "custom_letzter_kontakt",
        "idx": idx,
        "options": "\nAnruf\nWhatsApp\nSMS\nE-Mail\nTermin\nSonstiges",
        "read_only": 1,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_followup_notiz",
        "fieldtype": "Small Text",
        "label": "Follow-up Notiz",
        "insert_after": "custom_letzte_kontaktart",
        "idx": idx,
    })
    idx += 1

    # =====================================================
    # SECTION: DSGVO & Einwilligungen
    # =====================================================
    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_dsgvo_section",
        "fieldtype": "Section Break",
        "label": "DSGVO & Einwilligungen",
        "insert_after": "custom_followup_notiz",
        "idx": idx,
        "collapsible": 1,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_dsgvo_zugestimmt",
        "fieldtype": "Check",
        "label": "DSGVO Einwilligung erteilt",
        "insert_after": "custom_dsgvo_section",
        "idx": idx,
        "default": "0",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_dsgvo_timestamp",
        "fieldtype": "Datetime",
        "label": "DSGVO Zeitstempel",
        "insert_after": "custom_dsgvo_zugestimmt",
        "idx": idx,
        "read_only": 1,
        "depends_on": "eval:doc.custom_dsgvo_zugestimmt",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_dsgvo_whatsapp",
        "fieldtype": "Check",
        "label": "WhatsApp Opt-in",
        "insert_after": "custom_dsgvo_timestamp",
        "idx": idx,
        "default": "0",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_col_break_dsgvo",
        "fieldtype": "Column Break",
        "insert_after": "custom_dsgvo_whatsapp",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_dsgvo_sms",
        "fieldtype": "Check",
        "label": "SMS Opt-in",
        "insert_after": "custom_col_break_dsgvo",
        "idx": idx,
        "default": "0",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_dsgvo_email",
        "fieldtype": "Check",
        "label": "E-Mail Opt-in",
        "insert_after": "custom_dsgvo_sms",
        "idx": idx,
        "default": "0",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_dsgvo_telefon",
        "fieldtype": "Check",
        "label": "Telefon Opt-in",
        "insert_after": "custom_dsgvo_email",
        "idx": idx,
        "default": "0",
    })
    idx += 1

    # =====================================================
    # SECTION: Herkunft / Tracking
    # =====================================================
    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_tracking_section",
        "fieldtype": "Section Break",
        "label": "Herkunft & Tracking",
        "insert_after": "custom_dsgvo_telefon",
        "idx": idx,
        "collapsible": 1,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_quell_url",
        "fieldtype": "Data",
        "label": "Quell-URL",
        "insert_after": "custom_tracking_section",
        "idx": idx,
        "read_only": 1,
        "description": "Landing Page URL des Leads",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_geraet",
        "fieldtype": "Data",
        "label": "Geraet",
        "insert_after": "custom_quell_url",
        "idx": idx,
        "read_only": 1,
        "description": "Geraet des Leads (z.B. iPhone, Android)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_kampagne",
        "fieldtype": "Data",
        "label": "Kampagne",
        "insert_after": "custom_geraet",
        "idx": idx,
        "description": "Kampagnenname (Facebook, Google etc.)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_col_break_tracking",
        "fieldtype": "Column Break",
        "insert_after": "custom_kampagne",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_utm_source",
        "fieldtype": "Data",
        "label": "UTM Source",
        "insert_after": "custom_col_break_tracking",
        "idx": idx,
        "read_only": 1,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_utm_medium",
        "fieldtype": "Data",
        "label": "UTM Medium",
        "insert_after": "custom_utm_source",
        "idx": idx,
        "read_only": 1,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_utm_campaign",
        "fieldtype": "Data",
        "label": "UTM Campaign",
        "insert_after": "custom_utm_medium",
        "idx": idx,
        "read_only": 1,
    })
    idx += 1

    # =====================================================
    # SECTION: Tier-Versicherung (Pferd/Hund/Katze)
    # =====================================================
    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_tier_section",
        "fieldtype": "Section Break",
        "label": "Tierversicherung",
        "insert_after": "custom_utm_campaign",
        "idx": idx,
        "collapsible": 1,
        "depends_on": "eval:['Pferd','Hund','Katze'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_tierart",
        "fieldtype": "Select",
        "label": "Tierart",
        "insert_after": "custom_tier_section",
        "idx": idx,
        "options": "\nPferd\nHund\nKatze",
        "depends_on": "eval:['Pferd','Hund','Katze'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_tiername",
        "fieldtype": "Data",
        "label": "Tiername",
        "insert_after": "custom_tierart",
        "idx": idx,
        "depends_on": "eval:['Pferd','Hund','Katze'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_tierrasse",
        "fieldtype": "Data",
        "label": "Tierrasse",
        "insert_after": "custom_tiername",
        "idx": idx,
        "depends_on": "eval:['Pferd','Hund','Katze'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_tieralter",
        "fieldtype": "Int",
        "label": "Tieralter (Jahre)",
        "insert_after": "custom_tierrasse",
        "idx": idx,
        "depends_on": "eval:['Pferd','Hund','Katze'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_col_break_tier",
        "fieldtype": "Column Break",
        "insert_after": "custom_tieralter",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_chip_nummer",
        "fieldtype": "Data",
        "label": "Chipnummer",
        "insert_after": "custom_col_break_tier",
        "idx": idx,
        "depends_on": "eval:['Pferd','Hund','Katze'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_vorerkrankungen",
        "fieldtype": "Small Text",
        "label": "Vorerkrankungen",
        "insert_after": "custom_chip_nummer",
        "idx": idx,
        "depends_on": "eval:['Pferd','Hund','Katze'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_aktuell_versichert",
        "fieldtype": "Check",
        "label": "Aktuell versichert?",
        "insert_after": "custom_vorerkrankungen",
        "idx": idx,
        "default": "0",
        "depends_on": "eval:['Pferd','Hund','Katze'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_aktuelle_versicherung",
        "fieldtype": "Data",
        "label": "Aktuelle Versicherung",
        "insert_after": "custom_aktuell_versichert",
        "idx": idx,
        "depends_on": "eval:doc.custom_aktuell_versichert",
    })
    idx += 1

    # =====================================================
    # SECTION: Oldtimer/KFZ
    # =====================================================
    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_oldtimer_section",
        "fieldtype": "Section Break",
        "label": "Oldtimer / KFZ",
        "insert_after": "custom_aktuelle_versicherung",
        "idx": idx,
        "collapsible": 1,
        "depends_on": "eval:doc.custom_leadtyp=='Oldtimer'",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_fahrzeugtyp",
        "fieldtype": "Data",
        "label": "Fahrzeugtyp / Modell",
        "insert_after": "custom_oldtimer_section",
        "idx": idx,
        "depends_on": "eval:doc.custom_leadtyp=='Oldtimer'",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_baujahr",
        "fieldtype": "Int",
        "label": "Baujahr",
        "insert_after": "custom_fahrzeugtyp",
        "idx": idx,
        "depends_on": "eval:doc.custom_leadtyp=='Oldtimer'",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_kennzeichen",
        "fieldtype": "Data",
        "label": "Kennzeichen",
        "insert_after": "custom_baujahr",
        "idx": idx,
        "depends_on": "eval:doc.custom_leadtyp=='Oldtimer'",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_col_break_oldtimer",
        "fieldtype": "Column Break",
        "insert_after": "custom_kennzeichen",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_wert_gutachten",
        "fieldtype": "Currency",
        "label": "Wert lt. Gutachten",
        "insert_after": "custom_col_break_oldtimer",
        "idx": idx,
        "depends_on": "eval:doc.custom_leadtyp=='Oldtimer'",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_km_begrenzung",
        "fieldtype": "Data",
        "label": "KM-Begrenzung",
        "insert_after": "custom_wert_gutachten",
        "idx": idx,
        "depends_on": "eval:doc.custom_leadtyp=='Oldtimer'",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_oldtimer_zustand",
        "fieldtype": "Select",
        "label": "Zustand",
        "insert_after": "custom_km_begrenzung",
        "idx": idx,
        "options": "\nNote 1 (Concours)\nNote 2 (Gut)\nNote 3 (Gebrauchszustand)\nNote 4 (Aufbauobjekt)",
        "depends_on": "eval:doc.custom_leadtyp=='Oldtimer'",
    })
    idx += 1

    # =====================================================
    # SECTION: KV Mensch (Krankenversicherung)
    # =====================================================
    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_kv_mensch_section",
        "fieldtype": "Section Break",
        "label": "KV Mensch",
        "insert_after": "custom_oldtimer_zustand",
        "idx": idx,
        "collapsible": 1,
        "depends_on": "eval:['KV Mensch Voll','KV Mensch Zusatz'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_kv_typ",
        "fieldtype": "Select",
        "label": "KV Typ",
        "insert_after": "custom_kv_mensch_section",
        "idx": idx,
        "options": "\nKV Voll\nKV Zusatz",
        "depends_on": "eval:['KV Mensch Voll','KV Mensch Zusatz'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_beruf",
        "fieldtype": "Data",
        "label": "Beruf",
        "insert_after": "custom_kv_typ",
        "idx": idx,
        "depends_on": "eval:['KV Mensch Voll','KV Mensch Zusatz'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_geburtsdatum",
        "fieldtype": "Date",
        "label": "Geburtsdatum",
        "insert_after": "custom_beruf",
        "idx": idx,
        "depends_on": "eval:['KV Mensch Voll','KV Mensch Zusatz','BU (meine-1750)','bAV'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_col_break_kv",
        "fieldtype": "Column Break",
        "insert_after": "custom_geburtsdatum",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_einkommen_brutto",
        "fieldtype": "Currency",
        "label": "Bruttoeinkommen (Jahres)",
        "insert_after": "custom_col_break_kv",
        "idx": idx,
        "depends_on": "eval:['KV Mensch Voll','KV Mensch Zusatz','BU (meine-1750)'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_versicherungsstatus",
        "fieldtype": "Select",
        "label": "Versicherungsstatus",
        "insert_after": "custom_einkommen_brutto",
        "idx": idx,
        "options": "\nGKV\nPKV\nBeihilfe\nFreiwillig GKV\nFamilienversichert",
        "depends_on": "eval:['KV Mensch Voll','KV Mensch Zusatz'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_vorerkrankungen_mensch",
        "fieldtype": "Small Text",
        "label": "Vorerkrankungen",
        "insert_after": "custom_versicherungsstatus",
        "idx": idx,
        "depends_on": "eval:['KV Mensch Voll','KV Mensch Zusatz','BU (meine-1750)'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    # =====================================================
    # SECTION: Finanzprodukte (BU, bAV, Geldanlage etc.)
    # =====================================================
    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_finanz_section",
        "fieldtype": "Section Break",
        "label": "Finanzprodukte",
        "insert_after": "custom_vorerkrankungen_mensch",
        "idx": idx,
        "collapsible": 1,
        "depends_on": "eval:['Geldanlage / Vallue','Kinderpolice','ManagerProtect','JuraTax','LOL (Loss of Licence)','BU (meine-1750)','bAV','PilotNow'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_gewuenschte_absicherung",
        "fieldtype": "Data",
        "label": "Gewuenschte Absicherung",
        "insert_after": "custom_finanz_section",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_anlagesumme",
        "fieldtype": "Currency",
        "label": "Anlagesumme / Beitrag",
        "insert_after": "custom_gewuenschte_absicherung",
        "idx": idx,
        "depends_on": "eval:['Geldanlage / Vallue','Kinderpolice','bAV'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_col_break_finanz",
        "fieldtype": "Column Break",
        "insert_after": "custom_anlagesumme",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_arbeitgeber",
        "fieldtype": "Data",
        "label": "Arbeitgeber",
        "insert_after": "custom_col_break_finanz",
        "idx": idx,
        "depends_on": "eval:['bAV','BU (meine-1750)'].includes(doc.custom_leadtyp)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_finanz_notiz",
        "fieldtype": "Small Text",
        "label": "Notiz zum Finanzprodukt",
        "insert_after": "custom_arbeitgeber",
        "idx": idx,
    })
    idx += 1

    # =====================================================
    # SECTION: Termin
    # =====================================================
    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_termin_section",
        "fieldtype": "Section Break",
        "label": "Termin",
        "insert_after": "custom_finanz_notiz",
        "idx": idx,
        "collapsible": 0,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_termin_datum",
        "fieldtype": "Datetime",
        "label": "Termindatum",
        "insert_after": "custom_termin_section",
        "idx": idx,
        "description": "Naechster geplanter Termin",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_termin_typ",
        "fieldtype": "Select",
        "label": "Termintyp",
        "insert_after": "custom_termin_datum",
        "idx": idx,
        "options": "\nErsttermin\nCloser-Termin\nFollow-up Termin\nReaktivierung\nSpezialist",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_col_break_termin",
        "fieldtype": "Column Break",
        "insert_after": "custom_termin_typ",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_termin_status",
        "fieldtype": "Select",
        "label": "Terminstatus",
        "insert_after": "custom_col_break_termin",
        "idx": idx,
        "options": "\nGeplant\nBestaetigt\nDurchgefuehrt\nNo-Show\nAbgesagt\nVerschoben",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_termin_berater",
        "fieldtype": "Link",
        "label": "Berater (Closer)",
        "insert_after": "custom_termin_status",
        "idx": idx,
        "options": "User",
        "description": "Zugeordneter Berater fuer den Termin",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_termin_notiz",
        "fieldtype": "Small Text",
        "label": "Terminnotiz",
        "insert_after": "custom_termin_berater",
        "idx": idx,
    })
    idx += 1

    # =====================================================
    # SECTION: Abschluss
    # =====================================================
    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_abschluss_section",
        "fieldtype": "Section Break",
        "label": "Abschluss",
        "insert_after": "custom_termin_notiz",
        "idx": idx,
        "collapsible": 1,
        "depends_on": "eval:['80 - Abschluss gewonnen','90 - Abschluss verloren'].includes(doc.custom_liste)",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_abschluss_datum",
        "fieldtype": "Date",
        "label": "Abschlussdatum",
        "insert_after": "custom_abschluss_section",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_abschluss_produkt",
        "fieldtype": "Data",
        "label": "Abschlussprodukt",
        "insert_after": "custom_abschluss_datum",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_abschluss_beitrag",
        "fieldtype": "Currency",
        "label": "Monatsbeitrag",
        "insert_after": "custom_abschluss_produkt",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_col_break_abschluss",
        "fieldtype": "Column Break",
        "insert_after": "custom_abschluss_beitrag",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_abschluss_provision",
        "fieldtype": "Currency",
        "label": "Provision",
        "insert_after": "custom_col_break_abschluss",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_abschluss_verloren_grund",
        "fieldtype": "Select",
        "label": "Grund (Verloren)",
        "insert_after": "custom_abschluss_provision",
        "idx": idx,
        "options": "\nKein Interesse\nPreis zu hoch\nAnderem Anbieter zugesagt\nNicht erreicht\nFalsche Zielgruppe\nSonstiges",
        "depends_on": "eval:doc.custom_liste=='90 - Abschluss verloren'",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_abschluss_notiz",
        "fieldtype": "Small Text",
        "label": "Abschlussnotiz",
        "insert_after": "custom_abschluss_verloren_grund",
        "idx": idx,
    })
    idx += 1

    # =====================================================
    # SECTION: Cross-Selling
    # =====================================================
    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_cross_sell_section",
        "fieldtype": "Section Break",
        "label": "Cross-Selling",
        "insert_after": "custom_abschluss_notiz",
        "idx": idx,
        "collapsible": 1,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_cross_sell_prio1_produkt",
        "fieldtype": "Data",
        "label": "Prio-1 Produkt",
        "insert_after": "custom_cross_sell_section",
        "idx": idx,
        "read_only": 1,
        "description": "Wird automatisch basierend auf Leadtyp gesetzt",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_cross_sell_prio1_status",
        "fieldtype": "Select",
        "label": "Prio-1 Status",
        "insert_after": "custom_cross_sell_prio1_produkt",
        "idx": idx,
        "options": "\nNicht angesprochen\nAngesprochen\nBewusst nicht angesprochen\nWeiterleitung erstellt",
        "description": "Closer MUSS Prio-1 bestaetigen",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_cross_sell_prio2_produkt",
        "fieldtype": "Data",
        "label": "Prio-2 Produkt",
        "insert_after": "custom_cross_sell_prio1_status",
        "idx": idx,
        "read_only": 1,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_col_break_cross_sell",
        "fieldtype": "Column Break",
        "insert_after": "custom_cross_sell_prio2_produkt",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_cross_sell_prio3_produkt",
        "fieldtype": "Data",
        "label": "Prio-3 Produkt",
        "insert_after": "custom_col_break_cross_sell",
        "idx": idx,
        "read_only": 1,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_cross_sell_notiz",
        "fieldtype": "Small Text",
        "label": "Cross-Sell Notiz",
        "insert_after": "custom_cross_sell_prio3_produkt",
        "idx": idx,
    })
    idx += 1

    # =====================================================
    # SECTION: Spezialist / Veredlung
    # =====================================================
    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_spezialist_section",
        "fieldtype": "Section Break",
        "label": "Spezialist & Veredlung",
        "insert_after": "custom_cross_sell_notiz",
        "idx": idx,
        "collapsible": 1,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_an_spezialist_weitergeleitet",
        "fieldtype": "Check",
        "label": "An Spezialist weitergeleitet",
        "insert_after": "custom_spezialist_section",
        "idx": idx,
        "default": "0",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_spezialist_typ",
        "fieldtype": "Select",
        "label": "Spezialist-Typ",
        "insert_after": "custom_an_spezialist_weitergeleitet",
        "idx": idx,
        "options": "\nKV Mensch\nbAV\nFinanz\nSach\nSonstiges",
        "depends_on": "eval:doc.custom_an_spezialist_weitergeleitet",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_spezialist_user",
        "fieldtype": "Link",
        "label": "Spezialist",
        "insert_after": "custom_spezialist_typ",
        "idx": idx,
        "options": "User",
        "depends_on": "eval:doc.custom_an_spezialist_weitergeleitet",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_col_break_spezialist",
        "fieldtype": "Column Break",
        "insert_after": "custom_spezialist_user",
        "idx": idx,
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_spezialist_status",
        "fieldtype": "Select",
        "label": "Spezialist-Status",
        "insert_after": "custom_col_break_spezialist",
        "idx": idx,
        "options": "\nOffen\nIn Bearbeitung\nQualifiziert\nNicht qualifiziert",
        "depends_on": "eval:doc.custom_an_spezialist_weitergeleitet",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_veredelungspraemie",
        "fieldtype": "Currency",
        "label": "Veredelungspraemie",
        "insert_after": "custom_spezialist_status",
        "idx": idx,
        "read_only": 1,
        "depends_on": "eval:doc.custom_an_spezialist_weitergeleitet",
        "description": "Automatisch berechnet bei Qualifizierung",
    })
    idx += 1

    fields.append({
        "dt": "CRM Lead",
        "fieldname": "custom_praemie_status",
        "fieldtype": "Select",
        "label": "Praemien-Status",
        "insert_after": "custom_veredelungspraemie",
        "idx": idx,
        "options": "\nOffen\nBerechnet\nAusgezahlt",
        "depends_on": "eval:doc.custom_an_spezialist_weitergeleitet",
    })
    idx += 1

    # =====================================================
    # Insert all fields
    # =====================================================
    created_count = 0
    skipped_count = 0

    for field_data in fields:
        fieldname = field_data.get("fieldname")
        if not fieldname:
            continue

        # Check if field already exists
        existing = frappe.db.exists("Custom Field", {
            "dt": "CRM Lead",
            "fieldname": fieldname,
        })

        if existing:
            skipped_count += 1
            continue

        # Build the Custom Field name
        field_data["name"] = f"CRM Lead-{fieldname}"

        try:
            cf = frappe.get_doc({"doctype": "Custom Field", **field_data})
            cf.insert(ignore_permissions=True)
            created_count += 1
        except Exception as e:
            print(f"ERROR creating {fieldname}: {e}")

    print(f"Custom Fields: {created_count} created, {skipped_count} skipped (already exist)")


def run():
    """Main entry point."""
    print("=" * 60)
    print("CRM Setup: Role + Custom Fields")
    print("=" * 60)

    create_role()
    create_custom_fields()

    frappe.db.commit()
    print("\nAll done! Clear cache with: bench --site eco.canys.de clear-cache")


if __name__ == "__main__":
    run()
