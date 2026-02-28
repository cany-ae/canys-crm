# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMRelationship(Document):
    def validate(self):
        """Ensure only one active relationship per contact email.
        If a new active relationship is created, deactivate existing ones."""
        if self.status == "Aktiv":
            existing = frappe.get_all(
                "CRM Relationship",
                filters={
                    "contact_email": self.contact_email,
                    "status": "Aktiv",
                    "name": ["!=", self.name],
                },
                fields=["name"],
            )
            if existing:
                for old in existing:
                    frappe.db.set_value(
                        "CRM Relationship", old.name, "status", "Inaktiv"
                    )
                frappe.msgprint(
                    _("{0} bestehende Beziehung(en) auf Inaktiv gesetzt.").format(
                        len(existing)
                    )
                )

    def before_insert(self):
        """Set contact_name from User full_name if not provided."""
        if not self.contact_name and self.contact_email:
            # Try to find contact name from CRM Lead
            lead_name = frappe.db.get_value(
                "CRM Lead",
                {"email": self.contact_email},
                "lead_name",
            )
            if lead_name:
                self.contact_name = lead_name


@frappe.whitelist()
def get_relationship_for_email(email):
    """Return the active primary advisor relationship for an email address.

    Used in Lead detail view to show primary advisor info.
    """
    if not email:
        return {}

    rel = frappe.get_all(
        "CRM Relationship",
        filters={"contact_email": email, "status": "Aktiv"},
        fields=["name", "contact_email", "contact_name", "primary_advisor",
                "start_date", "status", "origin_lead", "lead_typ", "notiz"],
        limit=1,
    )

    if not rel:
        return {}

    result = rel[0]

    # Enrich with advisor full name
    advisor_name = frappe.db.get_value("User", result.primary_advisor, "full_name")
    result["advisor_full_name"] = advisor_name or result.primary_advisor

    return result


@frappe.whitelist()
def get_relationships_for_advisor(user=None):
    """Return all active relationships for an advisor.

    Used for advisor overview / dashboard.
    """
    user = user or frappe.session.user

    relationships = frappe.get_all(
        "CRM Relationship",
        filters={"primary_advisor": user, "status": "Aktiv"},
        fields=["name", "contact_email", "contact_name", "primary_advisor",
                "start_date", "status", "origin_lead", "lead_typ", "notiz"],
        order_by="start_date desc",
    )

    return relationships
