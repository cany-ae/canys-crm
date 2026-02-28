# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document


class CRMPipelineSettings(Document):
	def validate(self):
		"""Ensure only one phase is marked as default."""
		default_count = sum(1 for p in self.phases if p.is_default)
		if default_count > 1:
			frappe.throw("Nur eine Phase darf als Standard markiert sein.")
		if default_count == 0 and self.phases:
			frappe.throw("Mindestens eine Phase muss als Standard markiert sein.")

		# Validate JSON in allowed_transitions
		for phase in self.phases:
			if phase.allowed_transitions:
				try:
					parsed = json.loads(phase.allowed_transitions)
					if not isinstance(parsed, list):
						frappe.throw(f"Erlaubte Übergänge für {phase.phase_value} muss ein JSON-Array sein.")
				except json.JSONDecodeError:
					frappe.throw(f"Ungültiges JSON in 'Erlaubte Übergänge' für Phase {phase.phase_value}")

	def on_update(self):
		"""Clear cached transitions when settings change."""
		frappe.cache().delete_key("crm_pipeline_transitions")
		frappe.cache().delete_key("crm_pipeline_phases")
		frappe.cache().delete_key("crm_pipeline_default_phase")


def get_allowed_transitions():
	"""Return allowed transitions dict from settings (cached).

	Returns:
		dict: {phase_value: [allowed_target_values]}
	"""
	cached = frappe.cache().get_value("crm_pipeline_transitions")
	if cached:
		return cached

	transitions = {}
	try:
		settings = frappe.get_single("CRM Pipeline Settings")
		for phase in settings.phases:
			if phase.allowed_transitions:
				transitions[phase.phase_value] = json.loads(phase.allowed_transitions)
			else:
				transitions[phase.phase_value] = []
	except Exception:
		# Fallback to hardcoded if settings not yet created
		transitions = {
			"10 - Neu ohne Termin": ["20 - Termin gebucht", "50 - Closer-Termin", "90 - Abschluss verloren"],
			"20 - Termin gebucht": ["30 - Reaktivierung", "50 - Closer-Termin", "70 - Follow-up", "80 - Abschluss gewonnen", "90 - Abschluss verloren"],
			"30 - Reaktivierung": ["20 - Termin gebucht", "50 - Closer-Termin", "70 - Follow-up", "90 - Abschluss verloren"],
			"50 - Closer-Termin": ["70 - Follow-up", "80 - Abschluss gewonnen", "90 - Abschluss verloren"],
			"70 - Follow-up": ["20 - Termin gebucht", "30 - Reaktivierung", "50 - Closer-Termin", "80 - Abschluss gewonnen", "90 - Abschluss verloren"],
			"80 - Abschluss gewonnen": [],
			"90 - Abschluss verloren": ["30 - Reaktivierung"],
		}

	frappe.cache().set_value("crm_pipeline_transitions", transitions, expires_in_sec=300)
	return transitions


def get_pipeline_phases():
	"""Return ordered list of pipeline phases from settings (cached).

	Returns:
		list of dicts: [{phase_value, label, color, hex_color, sort_order, ...}]
	"""
	cached = frappe.cache().get_value("crm_pipeline_phases")
	if cached:
		return cached

	phases = []
	try:
		settings = frappe.get_single("CRM Pipeline Settings")
		for p in sorted(settings.phases, key=lambda x: x.sort_order or 0):
			phases.append({
				"phase_code": p.phase_code,
				"phase_value": p.phase_value,
				"label": p.label,
				"color": p.color,
				"hex_color": p.hex_color,
				"sort_order": p.sort_order,
				"is_default": p.is_default,
				"role_owner": p.role_owner,
			})
	except Exception:
		phases = [
			{"phase_code": "10", "phase_value": "10 - Neu ohne Termin", "label": "Neu", "color": "gray", "hex_color": "#6B7280", "sort_order": 10, "is_default": 1, "role_owner": "Setter"},
			{"phase_code": "20", "phase_value": "20 - Termin gebucht", "label": "Termin", "color": "blue", "hex_color": "#3B82F6", "sort_order": 20, "is_default": 0, "role_owner": "Setter"},
			{"phase_code": "30", "phase_value": "30 - Reaktivierung", "label": "Reaktiv.", "color": "amber", "hex_color": "#F59E0B", "sort_order": 30, "is_default": 0, "role_owner": "Opener"},
			{"phase_code": "50", "phase_value": "50 - Closer-Termin", "label": "Closer", "color": "purple", "hex_color": "#8B5CF6", "sort_order": 50, "is_default": 0, "role_owner": "Closer"},
			{"phase_code": "70", "phase_value": "70 - Follow-up", "label": "Follow-up", "color": "orange", "hex_color": "#F97316", "sort_order": 70, "is_default": 0, "role_owner": "System"},
			{"phase_code": "80", "phase_value": "80 - Abschluss gewonnen", "label": "Gewonnen", "color": "green", "hex_color": "#10B981", "sort_order": 80, "is_default": 0, "role_owner": "System"},
			{"phase_code": "90", "phase_value": "90 - Abschluss verloren", "label": "Verloren", "color": "red", "hex_color": "#EF4444", "sort_order": 90, "is_default": 0, "role_owner": "System"},
		]

	frappe.cache().set_value("crm_pipeline_phases", phases, expires_in_sec=300)
	return phases


def get_default_phase():
	"""Return the default phase value for new leads."""
	cached = frappe.cache().get_value("crm_pipeline_default_phase")
	if cached:
		return cached

	try:
		settings = frappe.get_single("CRM Pipeline Settings")
		for p in settings.phases:
			if p.is_default:
				frappe.cache().set_value("crm_pipeline_default_phase", p.phase_value, expires_in_sec=300)
				return p.phase_value
	except Exception:
		pass

	return "10 - Neu ohne Termin"
