# Copyright (c) 2026, R&P CRM and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


# Premium amounts are exclusively configured in "CRM Praemien Einstellungen".
# No legacy fallback – if no active rule matches, premium is 0.

# Status mapping: CRM Referral status -> CRM Lead custom_spezialist_status
REFERRAL_TO_LEAD_STATUS = {
	"Erstellt": "Offen",
	"Kontaktiert": "In Bearbeitung",
	"Qualifiziert": "Qualifiziert",
	"Nicht qualifiziert": "Nicht qualifiziert",
	"Ausgezahlt": "Qualifiziert",
}


def get_premium_amount(product_type, user=None):
	"""Get premium amount from CRM Praemien Einstellungen.

	Looks up the first active rule matching the product_type AND
	the mitarbeiter_kategorie of the given user.
	Returns 0 if no active rule is found (no legacy fallback).

	Args:
		product_type: Product / insurance line (e.g. "KV Mensch Voll")
		user: Optional user email. Used to determine mitarbeiter_kategorie.

	Returns:
		Premium amount as float, or 0 if no active rule matches.
	"""
	kategorie = "Neue Mitarbeiter"
	if user:
		kategorie = frappe.db.get_value("User", user, "custom_mitarbeiter_kategorie") or "Neue Mitarbeiter"

	try:
		settings = frappe.get_single("CRM Praemien Einstellungen")
		for regel in settings.praemien_regeln:
			if regel.aktiv and regel.produkt == product_type and regel.mitarbeiter_kategorie == kategorie:
				return float(regel.praemie_betrag or 0)
	except Exception:
		pass

	return 0


class CRMReferral(Document):
	def validate(self):
		self._validate_origin_lead()
		self._handle_qualification()
		self._auto_set_qualified_fields()

	def _validate_origin_lead(self):
		"""Ensure origin_lead exists."""
		if self.origin_lead and not frappe.db.exists("CRM Lead", self.origin_lead):
			frappe.throw(
				_("Lead {0} existiert nicht.").format(self.origin_lead),
				frappe.DoesNotExistError,
			)

	def _handle_qualification(self):
		"""Auto-calculate premium when status changes to Qualifiziert."""
		if self.referral_status == "Qualifiziert" and not self.premium_amount:
			self.calculate_premium()

	def _auto_set_qualified_fields(self):
		"""Set qualified_date and qualified_by when status becomes Qualifiziert."""
		if self.referral_status in ("Qualifiziert", "Ausgezahlt"):
			if not self.qualified_date:
				self.qualified_date = frappe.utils.today()
			if not self.qualified_by:
				self.qualified_by = frappe.session.user

	def calculate_premium(self):
		"""Calculate premium based on target_topic and referrer's mitarbeiter_kategorie."""
		self.premium_amount = get_premium_amount(self.target_topic, user=self.referrer_user)
		self.premium_status = "Berechnet"

	def on_update(self):
		self.sync_to_lead()

	def on_trash(self):
		"""When referral is deleted, check if there are other referrals for this lead."""
		if self.origin_lead:
			other_referrals = frappe.get_all(
				"CRM Referral",
				filters={
					"origin_lead": self.origin_lead,
					"name": ["!=", self.name],
				},
				limit=1,
			)
			if not other_referrals:
				# No more referrals - reset specialist fields on lead
				try:
					frappe.db.set_value(
						"CRM Lead",
						self.origin_lead,
						{
							"custom_spezialist_status": "",
							"custom_spezialist_user": "",
							"custom_veredelungspraemie": 0,
							"custom_praemie_status": "",
						},
						update_modified=False,
					)
				except Exception:
					pass

	def sync_to_lead(self):
		"""Sync referral status back to the CRM Lead custom fields.
		Uses frappe.db.set_value to bypass full lead validation
		(leads may have legacy data that fails select validation)."""
		if not self.origin_lead:
			return

		if not frappe.db.exists("CRM Lead", self.origin_lead):
			return

		update_dict = {
			"custom_spezialist_status": REFERRAL_TO_LEAD_STATUS.get(self.referral_status, "Offen"),
			"custom_praemie_status": self.premium_status or "Offen",
		}

		if self.target_specialist:
			update_dict["custom_spezialist_user"] = self.target_specialist

		if self.premium_amount:
			update_dict["custom_veredelungspraemie"] = self.premium_amount

		frappe.db.set_value("CRM Lead", self.origin_lead, update_dict, update_modified=False)


@frappe.whitelist()
def get_referrals_for_lead(lead_name):
	"""Get all CRM Referral records for a given lead."""
	if not lead_name:
		return []

	if not frappe.has_permission("CRM Lead", "read", lead_name):
		frappe.throw(_("Keine Berechtigung"), frappe.PermissionError)

	return frappe.get_all(
		"CRM Referral",
		filters={"origin_lead": lead_name},
		fields=[
			"name",
			"origin_lead",
			"lead_name_display",
			"referrer_user",
			"target_specialist",
			"target_topic",
			"referral_status",
			"premium_amount",
			"premium_status",
			"created_from",
			"cross_sell_prio",
			"cross_sell_produkt",
			"notiz",
			"qualified_date",
			"qualified_by",
			"creation",
			"modified",
			"owner",
		],
		order_by="creation desc",
	)


@frappe.whitelist()
def create_referral_from_lead(lead_name, data=None):
	"""Create a CRM Referral from a lead action (API endpoint for frontend)."""
	import json

	if isinstance(data, str):
		data = json.loads(data)
	data = data or {}

	if not frappe.has_permission("CRM Lead", "write", lead_name):
		frappe.throw(_("Keine Berechtigung"), frappe.PermissionError)

	referral = frappe.get_doc({
		"doctype": "CRM Referral",
		"origin_lead": lead_name,
		"referrer_user": frappe.session.user,
		"target_specialist": data.get("spezialist_user", ""),
		"target_topic": data.get("spezialist_typ", ""),
		"referral_status": "Erstellt",
		"created_from": data.get("created_from", "Spezialist-Weiterleitung"),
		"cross_sell_prio": data.get("cross_sell_prio", ""),
		"cross_sell_produkt": data.get("cross_sell_produkt", ""),
		"notiz": data.get("notiz", ""),
	})
	referral.insert(ignore_permissions=True)

	return referral.as_dict()
