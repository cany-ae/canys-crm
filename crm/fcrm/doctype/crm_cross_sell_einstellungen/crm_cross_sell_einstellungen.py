# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMCrossSellEinstellungen(Document):
	pass


def get_cross_sell_for_leadtyp(leadtyp):
	"""Return (prio1, prio2, prio3) for a given Leadtyp from settings.

	Reads from CRM Cross Sell Einstellungen doctype.
	Returns None if no rules found for the Leadtyp.
	"""
	if not leadtyp:
		return None

	try:
		settings = frappe.get_single("CRM Cross Sell Einstellungen")
	except Exception:
		return None

	if not settings.regeln:
		return None

	# Build lookup: {prio_number: thema} for active rules of this leadtyp
	prio_map = {}
	for regel in settings.regeln:
		if regel.leadtyp == leadtyp and regel.aktiv:
			prio_map[str(regel.prioritaet)] = regel.thema

	if not prio_map:
		return None

	prio1 = prio_map.get("1", "")
	prio2 = prio_map.get("2", "")
	prio3 = prio_map.get("3", "")

	return (prio1, prio2, prio3)
