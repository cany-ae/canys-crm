# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as assign, remove as unassign
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


class CRMTask(Document):
	def after_insert(self):
		self._check_assignment_policy()
		self.assign_to()

	def validate(self):
		if self.is_new() or not self.assigned_to:
			return

		if self.get_doc_before_save().assigned_to != self.assigned_to:
			self._check_assignment_policy()
			self.unassign_from_previous_user(self.get_doc_before_save().assigned_to)
			self.assign_to()

		# Auto-set completed_at when status changes to Done or Canceled
		if self.has_value_changed("status"):
			if self.status in ("Done", "Canceled"):
				if not self.completed_at:
					self.completed_at = frappe.utils.now()
					self.completed_by = frappe.session.user
			else:
				# Reopened task - clear completion fields
				self.completed_at = None
				self.completed_by = None

	def _check_assignment_policy(self):
		"""Enforce role-based assignment policy before assigning."""
		if not self.assigned_to:
			return
		from crm.api.assignment_policy import can_assign_to
		can_assign_to(self.assigned_to)

	def unassign_from_previous_user(self, user):
		unassign(self.doctype, self.name, user)

	def assign_to(self):
		if self.assigned_to:
			assign({
				"assign_to": [self.assigned_to],
				"doctype": self.doctype,
				"name": self.name,
				"description": self.title or self.description,
			})

	@staticmethod
	def default_list_data():
		columns = [
			{
				'label': 'Titel',
				'type': 'Data',
				'key': 'title',
				'width': '16rem',
			},
			{
				'label': 'Status',
				'type': 'Select',
				'key': 'status',
				'width': '8rem',
			},
			{
				'label': 'Priorität',
				'type': 'Select',
				'key': 'priority',
				'width': '8rem',
			},
			{
				'label': 'Fällig',
				'type': 'Date',
				'key': 'due_date',
				'width': '8rem',
			},
			{
				'label': 'Zugewiesen an',
				'type': 'Link',
				'key': 'assigned_to',
				'width': '10rem',
			},
			{
				'label': 'Zuletzt bearbeitet',
				'type': 'Datetime',
				'key': 'modified',
				'width': '8rem',
			},
		]

		rows = [
			"name",
			"title",
			"description",
			"assigned_to",
			"due_date",
			"status",
			"priority",
			"reference_doctype",
			"reference_docname",
			"modified",
			"completed_at",
			"completed_by",
		]
		return {'columns': columns, 'rows': rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "title",
			"kanban_fields": '["description", "priority", "creation"]'
		}
