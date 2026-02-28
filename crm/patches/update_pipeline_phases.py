import frappe


def execute():
    """Update custom_liste field from Liste A-E to numeric pipeline phases 10-90."""

    # New phase options
    new_options = "\n".join([
        "10 - Neu ohne Termin",
        "20 - Termin gebucht",
        "30 - Reaktivierung",
        "50 - Closer-Termin",
        "70 - Follow-up",
        "80 - Abschluss gewonnen",
        "90 - Abschluss verloren",
    ])

    # Update the Custom Field options
    custom_field = frappe.get_doc("Custom Field", {"fieldname": "custom_liste", "dt": "CRM Lead"})
    custom_field.options = new_options
    custom_field.default = "10 - Neu ohne Termin"
    custom_field.save(ignore_permissions=True)

    # Migration mapping: existing leads
    migration_map = {
        "Liste A": "10 - Neu ohne Termin",
        "Liste B": "20 - Termin gebucht",
        "Liste C": "30 - Reaktivierung",
        "Liste D": "70 - Follow-up",
        "Liste E": "90 - Abschluss verloren",
    }

    for old_val, new_val in migration_map.items():
        frappe.db.sql(
            "UPDATE `tabCRM Lead` SET custom_liste = %s WHERE custom_liste = %s",
            (new_val, old_val),
        )

    # Handle empty/null values
    frappe.db.sql(
        "UPDATE `tabCRM Lead` SET custom_liste = %s WHERE custom_liste IS NULL OR custom_liste = ''",
        "10 - Neu ohne Termin",
    )

    frappe.db.commit()
    print("Pipeline phases updated successfully!")
