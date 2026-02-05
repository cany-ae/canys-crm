import frappe
import json
import re


COLUMN_MAP = {
    "vorname": "first_name",
    "nachname": "last_name",
    "e-mail": "email",
    "e mail": "email",
    "email": "email",
    "mobilfunknummer": "mobile_no",
    "telefon": "mobile_no",
    "mobil": "mobile_no",
    "organisation": "organization",
    "firma": "organization",
    "unternehmen": "organization",
    "status": "status",
    "liste": "custom_liste",
    "first_name": "first_name",
    "first name": "first_name",
    "last_name": "last_name",
    "last name": "last_name",
    "mobile_no": "mobile_no",
    "mobile": "mobile_no",
    "phone": "mobile_no",
    "organization": "organization",
    "company": "organization",
    "custom_liste": "custom_liste",
}

VALID_FIELDS = {
    "first_name", "last_name", "email", "mobile_no",
    "organization", "status", "custom_liste",
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_header(header):
    return header.strip().lower().replace("_", " ").replace("-", " ").strip()


def _map_columns(headers):
    mapping = {}
    for i, h in enumerate(headers):
        norm = _normalize_header(h)
        if norm in COLUMN_MAP:
            mapping[i] = COLUMN_MAP[norm]
        elif norm.replace(" ", "_") in COLUMN_MAP:
            mapping[i] = COLUMN_MAP[norm.replace(" ", "_")]
        elif norm.replace(" ", "_") in VALID_FIELDS:
            mapping[i] = norm.replace(" ", "_")
    return mapping


def _get_vertriebler():
    """Get all active users with Role Profile Vertriebler."""
    users = frappe.get_all(
        "User",
        filters={"role_profile_name": "Vertriebler", "enabled": 1},
        fields=["name", "full_name"],
        order_by="name asc",
    )
    return users


@frappe.whitelist()
def get_valid_statuses():
    meta = frappe.get_meta("CRM Lead")
    status_field = meta.get_field("status")
    if not status_field:
        return []
    if status_field.fieldtype == "Link" and status_field.options:
        return frappe.get_all(status_field.options, pluck="name", order_by="creation")
    elif status_field.fieldtype == "Select" and status_field.options:
        opts = status_field.options
        return [s.strip() for s in opts.split(chr(10)) if s.strip()]
    return []


@frappe.whitelist()
def get_vertriebler_list():
    """Return list of Vertriebler for frontend display."""
    return _get_vertriebler()


@frappe.whitelist()
def import_leads(rows, headers):
    frappe.only_for(["System Manager", "Sales Manager"])

    if isinstance(rows, str):
        rows = json.loads(rows)
    if isinstance(headers, str):
        headers = json.loads(headers)

    valid_statuses = get_valid_statuses()
    default_status = valid_statuses[0] if valid_statuses else "New"

    col_mapping = _map_columns(headers)

    if not col_mapping:
        frappe.throw("Keine Spalten konnten zugeordnet werden. Bitte Spaltenkoepfe pruefen.")

    has_first_name = any(v == "first_name" for v in col_mapping.values())
    if not has_first_name:
        frappe.throw("Pflichtfeld Vorname / first_name fehlt in den Spaltenkoepfen.")

    # Get Vertriebler for round-robin assignment
    vertriebler = _get_vertriebler()

    results = {
        "success": 0,
        "failed": 0,
        "errors": [],
        "created": [],
        "distribution": {},
    }

    # Initialize distribution counter
    for v in vertriebler:
        results["distribution"][v["full_name"]] = 0

    assign_index = 0

    for idx, row in enumerate(rows):
        row_num = idx + 2
        try:
            doc_data = {"doctype": "CRM Lead"}

            for col_idx, fieldname in col_mapping.items():
                ci = int(col_idx)
                if ci < len(row):
                    value = str(row[ci]).strip() if row[ci] is not None else ""
                    if value:
                        doc_data[fieldname] = value

            if not doc_data.get("first_name"):
                results["errors"].append({"row": row_num, "error": "Vorname fehlt"})
                results["failed"] += 1
                continue

            if doc_data.get("email") and not EMAIL_RE.match(doc_data["email"]):
                results["errors"].append({"row": row_num, "error": "Ungueltige E-Mail: " + doc_data["email"]})
                results["failed"] += 1
                continue

            if doc_data.get("status"):
                if doc_data["status"] not in valid_statuses:
                    results["errors"].append({
                        "row": row_num,
                        "error": "Ungueltiger Status: " + doc_data["status"] + ". Gueltig: " + ", ".join(valid_statuses),
                    })
                    results["failed"] += 1
                    continue
            else:
                doc_data["status"] = default_status

            # Assign to Vertriebler (round-robin) - set lead_owner BEFORE insert
            if vertriebler:
                assigned_user = vertriebler[assign_index % len(vertriebler)]
                doc_data["lead_owner"] = assigned_user["name"]
            else:
                doc_data["lead_owner"] = frappe.session.user

            lead = frappe.get_doc(doc_data)
            lead.insert(ignore_permissions=True)

            # Track distribution (lead_owner already assigns the Vertriebler)
            if vertriebler:
                results["distribution"][assigned_user["full_name"]] = results["distribution"].get(assigned_user["full_name"], 0) + 1
                assign_index += 1

            results["success"] += 1
            results["created"].append(lead.name)

        except Exception as e:
            results["errors"].append({"row": row_num, "error": str(e)})
            results["failed"] += 1

    frappe.db.commit()
    return results
