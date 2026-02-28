# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign
from frappe.model.document import Document
from frappe.utils import has_gravatar, validate_email_address

from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import (
	add_status_change_log,
)
from crm.fcrm.doctype.crm_referral.crm_referral import get_premium_amount



# Pipeline transitions loaded from CRM Pipeline Settings (configurable)
# Fallback to hardcoded values if settings not yet created
def _get_allowed_transitions():
    try:
        from crm.fcrm.doctype.crm_pipeline_settings.crm_pipeline_settings import get_allowed_transitions
        return get_allowed_transitions()
    except Exception:
        return {
            "10 - Neu ohne Termin": ["20 - Termin gebucht", "50 - Closer-Termin", "90 - Abschluss verloren"],
            "20 - Termin gebucht": ["30 - Reaktivierung", "50 - Closer-Termin", "70 - Follow-up", "80 - Abschluss gewonnen", "90 - Abschluss verloren"],
            "30 - Reaktivierung": ["20 - Termin gebucht", "50 - Closer-Termin", "70 - Follow-up", "90 - Abschluss verloren"],
            "50 - Closer-Termin": ["70 - Follow-up", "80 - Abschluss gewonnen", "90 - Abschluss verloren"],
            "70 - Follow-up": ["20 - Termin gebucht", "30 - Reaktivierung", "50 - Closer-Termin", "80 - Abschluss gewonnen", "90 - Abschluss verloren"],
            "80 - Abschluss gewonnen": [],
            "90 - Abschluss verloren": ["30 - Reaktivierung"],
        }


# ── Cross-Sell Matrix ──────────────────────────────────────────────────────
# Cross-Sell-Regeln werden jetzt aus dem Doctype "CRM Cross Sell Einstellungen"
# gelesen. Konfiguration unter: /app/crm-cross-sell-einstellungen
from crm.fcrm.doctype.crm_cross_sell_einstellungen.crm_cross_sell_einstellungen import get_cross_sell_for_leadtyp


# Gamification points
def _try_award_points(user, action_type, lead_name=None):
    """Gamification: Punkte vergeben (Masterplanung 9.8).
    Nur 4 Aktionen: erstkontakt, followup_puenktlich, termin_erschienen, weiterleitung_qualifiziert."""
    try:
        if action_type == 'erstkontakt':
            from crm.api.gamification import award_erstkontakt
            award_erstkontakt(user, lead_name)
        elif action_type == 'followup_puenktlich':
            from crm.api.gamification import award_followup_puenktlich
            award_followup_puenktlich(user, lead_name)
        elif action_type == 'termin_erschienen':
            from crm.api.gamification import award_termin_erschienen
            award_termin_erschienen(user, lead_name)
        elif action_type == 'weiterleitung_qualifiziert':
            from crm.api.gamification import award_weiterleitung_qualifiziert
            award_weiterleitung_qualifiziert(user, lead_name)
    except Exception:
        pass

class CRMLead(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from crm.fcrm.doctype.crm_products.crm_products import CRMProducts
		from crm.fcrm.doctype.crm_rolling_response_time.crm_rolling_response_time import CRMRollingResponseTime
		from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import CRMStatusChangeLog
		from frappe.types import DF

		annual_revenue: DF.Currency
		communication_status: DF.Link | None
		converted: DF.Check
		email: DF.Data | None
		facebook_form_id: DF.Data | None
		facebook_lead_id: DF.Data | None
		first_name: DF.Data
		first_responded_on: DF.Datetime | None
		first_response_time: DF.Duration | None
		gender: DF.Link | None
		image: DF.AttachImage | None
		industry: DF.Link | None
		job_title: DF.Data | None
		last_name: DF.Data | None
		last_responded_on: DF.Datetime | None
		last_response_time: DF.Duration | None
		lead_name: DF.Data | None
		lead_owner: DF.Link | None
		middle_name: DF.Data | None
		mobile_no: DF.Data | None
		naming_series: DF.Literal["CRM-LEAD-.YYYY.-"]
		net_total: DF.Currency
		no_of_employees: DF.Literal["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]
		organization: DF.Data | None
		phone: DF.Data | None
		products: DF.Table[CRMProducts]
		response_by: DF.Datetime | None
		rolling_responses: DF.Table[CRMRollingResponseTime]
		salutation: DF.Link | None
		sla: DF.Link | None
		sla_creation: DF.Datetime | None
		sla_status: DF.Literal["", "First Response Due", "Rolling Response Due", "Failed", "Fulfilled"]
		source: DF.Link | None
		status: DF.Link
		status_change_log: DF.Table[CRMStatusChangeLog]
		territory: DF.Link | None
		total: DF.Currency
		website: DF.Data | None
	# end: auto-generated types

	def before_validate(self):
		if not self.status:
			self.status = "Nicht kontaktiert"
		self.set_sla()

	def validate(self):
		self.set_full_name()
		self.set_lead_name()
		self.set_title()
		self.validate_email()
		if not self.is_new() and self.has_value_changed("lead_owner") and self.lead_owner:
			self._check_assignment_policy(self.lead_owner)
			self.share_with_agent(self.lead_owner)
			self.assign_agent(self.lead_owner)
		if self.has_value_changed("status"):
			old_doc = self.get_doc_before_save()
			self._old_status = old_doc.status if old_doc else None
			add_status_change_log(self)
		# Auto-trigger phase transitions based on field changes
		if not self.is_new():
			self.apply_phase_triggers()
		# Auto-refresh cross-sell when Leadtyp changes
		if not self.is_new() and self.has_value_changed("custom_leadtyp"):
			self.refresh_cross_sell_for_leadtyp()
		if not self.is_new() and self.has_value_changed("custom_liste"):
			self.validate_liste_transition()

	def after_insert(self):
		# Set default phase if not already set
		if not self.custom_liste:
			self.db_set("custom_liste", "10 - Neu ohne Termin")
			frappe.get_doc({
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "CRM Lead",
				"reference_name": self.name,
				"content": "LISTENWECHSEL: \u2014 -> 10 - Neu ohne Termin (automatisch bei Erstellung)",
			}).insert(ignore_permissions=True)
		# Auto-populate cross-sell suggestions based on Leadtyp
		self.auto_populate_cross_sell()
		if self.custom_cross_sell_prio1_produkt:
			self.db_set("custom_cross_sell_prio1_produkt", self.custom_cross_sell_prio1_produkt)
			self.db_set("custom_cross_sell_prio2_produkt", self.custom_cross_sell_prio2_produkt)
			self.db_set("custom_cross_sell_prio3_produkt", self.custom_cross_sell_prio3_produkt)
		# Auto-assign lead via round-robin (before manual owner check)
		auto_assign_lead(self.name)
		# Reload to pick up lead_owner set by auto_assign_lead
		self.reload()
		if self.lead_owner:
			self._check_assignment_policy(self.lead_owner)
			self.assign_agent(self.lead_owner)
		self._create_initial_status_update()
		# Gamification: award points for lead creation
		# Gamification: Erstkontakt-Punkte werden bei erster Aktion vergeben, nicht bei Erstellung
		self.auto_link_contact()

	def auto_link_contact(self):
		"""Automatisch Kontakt erstellen oder verknuepfen beim Lead-Erstellen.
		Matching: 1) Email, 2) Mobilnummer, 3) kein Auto-Kontakt.
		Sets both Dynamic Link (Contact->Lead) and custom_contact (Lead->Contact)."""
		if not self.email and not self.mobile_no and not self.phone:
			return

		try:
			# Pruefen ob bereits ein Kontakt verknuepft ist (via Dynamic Link)
			existing_link = frappe.db.get_value("Dynamic Link", {
				"link_doctype": "CRM Lead",
				"link_name": self.name,
				"parenttype": "Contact",
			}, "parent")
			if existing_link:
				# Dynamic Link exists, ensure custom_contact is set too
				if not self.custom_contact:
					self.db_set("custom_contact", existing_link)
				return

			# Bestehenden Kontakt suchen (Email > Phone > Mobile)
			existing_contact = self.contact_exists(throw=False)

			if existing_contact:
				# Pruefen ob Kontakt intern ist - dann nicht verknuepfen, neuen erstellen
				contact_type = frappe.db.get_value('Contact', existing_contact, 'custom_contact_type')
				if contact_type == 'Intern':
					# Interner Kontakt: neuen Kunden-Kontakt erstellen statt verknuepfen
					contact_name = self.create_contact(existing_contact=False, throw=False)
					if contact_name:
						self._link_contact_to_lead(contact_name)
				else:
					# Bestehenden Kunden-Kontakt mit Lead verknuepfen
					self._link_contact_to_lead(existing_contact)
			else:
				# Neuen Kontakt erstellen
				contact_name = self.create_contact(existing_contact=False, throw=False)
				if contact_name:
					self._link_contact_to_lead(contact_name)
		except Exception:
			# Fehler beim Auto-Kontakt soll Lead-Erstellung nicht blockieren
			frappe.log_error("Auto-Kontakt Erstellung fehlgeschlagen für Lead: {0}".format(self.name))

	def _link_contact_to_lead(self, contact_name):
		"""Dynamic Link zwischen Contact und CRM Lead erstellen + custom_contact setzen."""
		contact = frappe.get_doc("Contact", contact_name)
		# Pruefen ob Link bereits existiert
		link_exists = False
		for link in contact.links:
			if link.link_doctype == "CRM Lead" and link.link_name == self.name:
				link_exists = True
				break
		if not link_exists:
			contact.append("links", {
				"link_doctype": "CRM Lead",
				"link_name": self.name,
			})
			contact.flags.ignore_permissions = True
			contact.save()
		# Set reverse link on Lead
		self.db_set("custom_contact", contact_name)

	def _create_initial_status_update(self):
		"""Erstelle initialen Status-Update-Eintrag für neue Leads."""
		if not self.status:
			return
		# Pruefen ob bereits eine Version mit status-Aenderung existiert
		existing = frappe.db.exists("Version", {
			"ref_doctype": "CRM Lead",
			"docname": self.name,
		})
		if existing:
			return
		import json
		# Frappe Version erstellen, die als status_change erkannt wird
		version = frappe.new_doc("Version")
		version.ref_doctype = "CRM Lead"
		version.docname = self.name
		version.data = json.dumps({
			"changed": [["status", "\u2014", self.status]]
		})
		version.insert(ignore_permissions=True)
		# Timeline-Comment für die Aktivitäten-Ansicht
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": "CRM Lead",
			"reference_name": self.name,
			"content": "\U0001f6a6 STATUS UPDATE: \u2014 \u2192 {0}".format(self.status),
		}).insert(ignore_permissions=True)

	def on_update(self):
		self.add_status_timeline_comment()
		self.add_liste_change_comment()

	def validate_liste_transition(self):
		"""Enforce allowed phase transitions for custom_liste field.
		System Managers can override all transitions.
		Skip validation for auto-triggered transitions (flagged)."""
		if getattr(self, '_skip_liste_validation', False):
			return

		old_doc = self.get_doc_before_save()
		if not old_doc:
			return

		old_liste = old_doc.custom_liste
		new_liste = self.custom_liste

		if old_liste == new_liste:
			return

		# System Managers (admins) can do any transition
		if "System Manager" in frappe.get_roles():
			return

		allowed = _get_allowed_transitions().get(old_liste, [])
		if new_liste not in allowed:
			frappe.throw(
				_("Listenwechsel von '{0}' nach '{1}' ist nicht erlaubt.").format(
					old_liste, new_liste
				),
				frappe.ValidationError,
			)


	def auto_populate_cross_sell(self):
		"""Auto-populate cross-sell suggestions based on Leadtyp.
		Reads rules from CRM Cross Sell Einstellungen doctype."""
		if not self.custom_leadtyp:
			return
		matrix = get_cross_sell_for_leadtyp(self.custom_leadtyp)
		if not matrix:
			return
		prio1, prio2, prio3 = matrix
		if not self.custom_cross_sell_prio1_produkt:
			self.custom_cross_sell_prio1_produkt = prio1
		if not self.custom_cross_sell_prio2_produkt:
			self.custom_cross_sell_prio2_produkt = prio2
		if not self.custom_cross_sell_prio3_produkt:
			self.custom_cross_sell_prio3_produkt = prio3


	def refresh_cross_sell_for_leadtyp(self):
		"""Force-refresh cross-sell suggestions when Leadtyp changes.
		Reads rules from CRM Cross Sell Einstellungen doctype."""
		if not self.custom_leadtyp:
			self.custom_cross_sell_prio1_produkt = ""
			self.custom_cross_sell_prio2_produkt = ""
			self.custom_cross_sell_prio3_produkt = ""
			return
		matrix = get_cross_sell_for_leadtyp(self.custom_leadtyp)
		if not matrix:
			self.custom_cross_sell_prio1_produkt = ""
			self.custom_cross_sell_prio2_produkt = ""
			self.custom_cross_sell_prio3_produkt = ""
			return
		prio1, prio2, prio3 = matrix
		self.custom_cross_sell_prio1_produkt = prio1
		self.custom_cross_sell_prio2_produkt = prio2
		self.custom_cross_sell_prio3_produkt = prio3

	def apply_phase_triggers(self):
		"""Automatically set custom_liste based on field changes.
		Called in validate() for existing docs, and after_insert for new ones.
		Uses _skip_liste_validation flag to bypass transition checks for auto-triggers."""
		if self.is_new():
			return

		old_doc = self.get_doc_before_save()
		if not old_doc:
			return

		current_phase = self.custom_liste or ""

		# Abschluss verloren: verloren_grund was just set
		if (self.custom_abschluss_verloren_grund
				and not old_doc.custom_abschluss_verloren_grund
				and current_phase != "90 - Abschluss verloren"):
			self.custom_liste = "90 - Abschluss verloren"
			self._skip_liste_validation = True
			return

		# Abschluss gewonnen: abschluss_datum was just set (and no verloren_grund)
		if (self.custom_abschluss_datum
				and not old_doc.custom_abschluss_datum
				and not self.custom_abschluss_verloren_grund
				and current_phase != "80 - Abschluss gewonnen"):
			self.custom_liste = "80 - Abschluss gewonnen"
			self._skip_liste_validation = True
			return

		# Termin gebucht: termin_datum was just set or changed
		if (self.custom_termin_datum
				and self.custom_termin_datum != old_doc.custom_termin_datum):
			# Closer-Termin if termin_typ is "Closer"
			if self.custom_termin_typ == "Closer-Termin" and current_phase != "50 - Closer-Termin":
				self.custom_liste = "50 - Closer-Termin"
				self._skip_liste_validation = True
				return
			# Regular termin -> Phase 20
			elif self.custom_termin_typ != "Closer-Termin" and current_phase not in [
				"20 - Termin gebucht", "50 - Closer-Termin",
				"80 - Abschluss gewonnen", "90 - Abschluss verloren"]:
				self.custom_liste = "20 - Termin gebucht"
				self._skip_liste_validation = True
				return

		# Termin-Status change: No-Show or Abgesagt triggers phase change
		if (self.custom_termin_status
				and self.custom_termin_status != old_doc.custom_termin_status):
			if self.custom_termin_status == "No-Show" and current_phase in [
				"20 - Termin gebucht", "50 - Closer-Termin"]:
				self.custom_liste = "70 - Follow-up"
				self._skip_liste_validation = True
				return
			if self.custom_termin_status == "Abgesagt":
				if current_phase == "50 - Closer-Termin":
					self.custom_liste = "70 - Follow-up"
					self._skip_liste_validation = True
					return
				elif current_phase == "20 - Termin gebucht":
					self.custom_liste = "10 - Neu ohne Termin"
					self._skip_liste_validation = True
					return
			if self.custom_termin_status == "Durchgeführt" and current_phase in [
				"20 - Termin gebucht", "50 - Closer-Termin"]:
				self.custom_liste = "70 - Follow-up"
				self._skip_liste_validation = True
				return

		# Follow-up: naechster_kontakt was just set and we're past initial phase
		if (self.custom_naechster_kontakt
				and self.custom_naechster_kontakt != old_doc.custom_naechster_kontakt
				and current_phase in [
					"20 - Termin gebucht", "30 - Reaktivierung",
					"50 - Closer-Termin"]):
			self.custom_liste = "70 - Follow-up"
			self._skip_liste_validation = True
			return

	def add_liste_change_comment(self):
		"""Add audit trail comment when custom_liste changes."""
		old_doc = self.get_doc_before_save()
		if not old_doc:
			return

		old_liste = old_doc.custom_liste
		new_liste = self.custom_liste

		if old_liste and old_liste != new_liste:
			frappe.get_doc({
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "CRM Lead",
				"reference_name": self.name,
				"content": "LISTENWECHSEL: {0} -> {1}".format(old_liste, new_liste),
			}).insert(ignore_permissions=True)

	def add_status_timeline_comment(self):
		old_status = getattr(self, "_old_status", None)
		if old_status and old_status != self.status:
			frappe.get_doc({
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "CRM Lead",
				"reference_name": self.name,
				"content": "🚦 STATUS UPDATE: {0} → {1}".format(old_status, self.status),
			}).insert(ignore_permissions=True)

	def before_save(self):
		self.apply_sla()

	def set_full_name(self):
		if self.first_name:
			self.lead_name = " ".join(
				filter(
					None,
					[
						self.salutation,
						self.first_name,
						self.middle_name,
						self.last_name,
					],
				)
			)

	def set_lead_name(self):
		if not self.lead_name:
			# Check for leads being created through data import
			if not self.organization and not self.email and not self.flags.ignore_mandatory:
				frappe.throw(_("A Lead requires either a person's name or an organization's name"))
			elif self.organization:
				self.lead_name = self.organization
			elif self.email:
				self.lead_name = self.email.split("@")[0]
			else:
				self.lead_name = "Unnamed Lead"

	def set_title(self):
		self.title = self.organization or self.lead_name

	def validate_email(self):
		if self.email:
			if not self.flags.ignore_email_validation:
				validate_email_address(self.email, throw=True)

			if self.email == self.lead_owner:
				frappe.throw(_("Lead Owner cannot be same as the Lead Email Address"))

			if self.is_new() or not self.image:
				self.image = has_gravatar(self.email)

	def _check_assignment_policy(self, target_user):
		"""Enforce role-based assignment policy."""
		if not target_user:
			return
		from crm.api.assignment_policy import can_assign_to
		can_assign_to(target_user)

	def assign_agent(self, agent):
		if not agent:
			return

		assignees = self.get_assigned_users()
		if assignees:
			for assignee in assignees:
				if agent == assignee:
					# the agent is already set as an assignee
					return

		assign({"assign_to": [agent], "doctype": "CRM Lead", "name": self.name})

	def share_with_agent(self, agent):
		if not agent:
			return

		docshares = frappe.get_all(
			"DocShare",
			filters={"share_name": self.name, "share_doctype": self.doctype},
			fields=["name", "user"],
		)

		shared_with = [d.user for d in docshares] + [agent]

		for user in shared_with:
			if user == agent and not frappe.db.exists(
				"DocShare",
				{"user": agent, "share_name": self.name, "share_doctype": self.doctype},
			):
				frappe.share.add_docshare(
					self.doctype,
					self.name,
					agent,
					write=1,
					flags={"ignore_share_permission": True},
				)
			elif user != agent:
				frappe.share.remove(self.doctype, self.name, user)

	def create_contact(self, existing_contact=None, throw=True):
		if not self.lead_name:
			self.set_full_name()
			self.set_lead_name()

		existing_contact = existing_contact or self.contact_exists(throw)
		if existing_contact:
			self.update_lead_contact(existing_contact)
			return existing_contact

		contact = frappe.new_doc("Contact")
		contact.update(
			{
				"first_name": self.first_name or self.lead_name,
				"last_name": self.last_name,
				"salutation": self.salutation,
				"gender": self.gender,
				"designation": self.job_title,
				"company_name": self.organization,
				"image": self.image or "",
			}
		)

		if self.email:
			contact.append("email_ids", {"email_id": self.email, "is_primary": 1})

		if self.phone:
			contact.append("phone_nos", {"phone": self.phone, "is_primary_phone": 1})

		if self.mobile_no:
			contact.append("phone_nos", {"phone": self.mobile_no, "is_primary_mobile_no": 1})

		contact.insert(ignore_permissions=True)
		# Aus Lead erstellte Kontakte sind immer Kunden
		frappe.db.set_value('Contact', contact.name, 'custom_contact_type', 'Kunde')
		contact.reload()  # load changes by hooks on contact

		return contact.name

	def create_organization(self, existing_organization=None):
		if not self.organization and not existing_organization:
			return

		existing_organization = existing_organization or frappe.db.exists(
			"CRM Organization", {"organization_name": self.organization}
		)
		if existing_organization:
			self.db_set("organization", existing_organization)
			return existing_organization

		organization = frappe.new_doc("CRM Organization")
		organization.update(
			{
				"organization_name": self.organization,
				"website": self.website,
				"territory": self.territory,
				"industry": self.industry,
				"annual_revenue": self.annual_revenue,
			}
		)
		organization.insert(ignore_permissions=True)
		return organization.name

	def update_lead_contact(self, contact):
		contact = frappe.get_cached_doc("Contact", contact)
		frappe.db.set_value(
			"CRM Lead",
			self.name,
			{
				"salutation": contact.salutation,
				"first_name": contact.first_name,
				"last_name": contact.last_name,
				"email": contact.email_id,
				"mobile_no": contact.mobile_no,
			},
		)

	def contact_exists(self, throw=True):
		email_exist = frappe.db.exists("Contact Email", {"email_id": self.email})
		phone_exist = frappe.db.exists("Contact Phone", {"phone": self.phone})
		mobile_exist = frappe.db.exists("Contact Phone", {"phone": self.mobile_no})

		doctype = "Contact Email" if email_exist else "Contact Phone"
		name = email_exist or phone_exist or mobile_exist

		if name:
			text = "Email" if email_exist else "Phone" if phone_exist else "Mobile No"
			data = self.email if email_exist else self.phone if phone_exist else self.mobile_no

			value = "{0}: {1}".format(text, data)

			contact = frappe.db.get_value(doctype, name, "parent")

			if throw:
				frappe.throw(
					_("Contact already exists with {0}").format(value),
					title=_("Contact Already Exists"),
				)
			return contact

		return False

	def create_deal(self, contact, organization, deal=None):
		new_deal = frappe.new_doc("CRM Deal")

		lead_deal_map = {
			"lead_owner": "deal_owner",
		}

		restricted_fieldtypes = [
			"Tab Break",
			"Section Break",
			"Column Break",
			"HTML",
			"Button",
			"Attach",
		]
		restricted_map_fields = [
			"name",
			"naming_series",
			"creation",
			"owner",
			"modified",
			"modified_by",
			"idx",
			"docstatus",
			"status",
			"email",
			"mobile_no",
			"phone",
			"sla",
			"sla_status",
			"response_by",
			"first_response_time",
			"first_responded_on",
			"communication_status",
			"sla_creation",
			"status_change_log",
		]

		for field in self.meta.fields:
			if field.fieldtype in restricted_fieldtypes:
				continue
			if field.fieldname in restricted_map_fields:
				continue

			fieldname = field.fieldname
			if field.fieldname in lead_deal_map:
				fieldname = lead_deal_map[field.fieldname]

			if hasattr(new_deal, fieldname):
				if fieldname == "organization":
					new_deal.update({fieldname: organization})
				else:
					new_deal.update({fieldname: self.get(field.fieldname)})

		new_deal.update(
			{
				"lead": self.name,
				"contacts": [{"contact": contact}],
			}
		)

		if self.first_responded_on:
			new_deal.update(
				{
					"sla_creation": self.sla_creation,
					"response_by": self.response_by,
					"sla_status": self.sla_status,
					"communication_status": self.communication_status,
					"first_response_time": self.first_response_time,
					"first_responded_on": self.first_responded_on,
				}
			)

		if deal:
			new_deal.update(deal)

		new_deal.insert(ignore_permissions=True)
		return new_deal.name

	def set_sla(self):
		"""
		Find an SLA to apply to the lead.
		"""
		if self.sla:
			return

		sla = get_sla(self)
		if not sla:
			self.first_responded_on = None
			self.first_response_time = None
			return
		self.sla = sla.name

	def apply_sla(self):
		"""
		Apply SLA if set.
		"""
		if not self.sla:
			return
		sla = frappe.get_last_doc("CRM Service Level Agreement", {"name": self.sla})
		if sla:
			sla.apply(self)

	def convert_to_deal(self, deal=None):
		return convert_to_deal(lead=self.name, doc=self, deal=deal)

	@staticmethod
	def get_non_filterable_fields():
		return ["converted"]

	@staticmethod
	def default_list_data():
		columns = [
			{"label": "Name", "type": "Data", "key": "lead_name", "width": "14rem"},
			{"label": "Leadtyp", "type": "Select", "key": "custom_leadtyp", "width": "10rem"},
			{"label": "Mobilfunknummer", "type": "Data", "key": "mobile_no", "width": "11rem"},
			{"label": "Zugewiesen zu", "type": "Link", "key": "_assign", "width": "10rem"},
			{"label": "Status", "type": "Select", "key": "status", "width": "12rem"},
			{"label": "Liste", "type": "Select", "key": "custom_liste", "width": "9rem"},
		]
		rows = [
			"name", "lead_name", "email", "mobile_no", "modified",
			"custom_liste", "status", "organization", "lead_owner", "first_name",
			"sla_status", "response_by", "first_response_time",
			"first_responded_on", "_assign", "image",
			"custom_leadtyp", "custom_leadquelle", "custom_lead_potenzial",
			"custom_naechster_kontakt", "custom_termin_datum", "custom_termin_status",
			"custom_zustaendige_rolle",
		]
		return {"columns": columns, "rows": rows}

@frappe.whitelist()
def convert_to_deal(lead, doc=None, deal=None, existing_contact=None, existing_organization=None):
	if not (doc and doc.flags.get("ignore_permissions")) and not frappe.has_permission(
		"CRM Lead", "write", lead
	):
		frappe.throw(_("Not allowed to convert Lead to Deal"), frappe.PermissionError)

	lead = frappe.get_cached_doc("CRM Lead", lead)
	if frappe.db.exists("CRM Lead Status", "Qualified"):
		lead.db_set("status", "Qualified")
	lead.db_set("converted", 1)
	if lead.sla and frappe.db.exists("CRM Communication Status", "Replied"):
		lead.db_set("communication_status", "Replied")
	contact = lead.create_contact(existing_contact, False)
	organization = lead.create_organization(existing_organization)
	_deal = lead.create_deal(contact, organization, deal)
	return _deal


@frappe.whitelist()
def update_lead_status(lead_name, new_status, note=None):
	"""Update lead status and optionally add a comment note."""
	if not frappe.has_permission("CRM Lead", "write", lead_name):
		frappe.throw(_("Keine Berechtigung"), frappe.PermissionError)

	lead = frappe.get_doc("CRM Lead", lead_name)
	old_status = lead.status
	lead.status = new_status
	lead.save(ignore_permissions=True)

	# Add note as comment if provided
	if note and note.strip():
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Comment",
			"reference_doctype": "CRM Lead",
			"reference_name": lead_name,
			"content": _("Status geaendert von {0} nach {1}: {2}").format(old_status, new_status, note),
		}).insert(ignore_permissions=True)

	frappe.db.commit()
	return {"status": "success", "old_status": old_status, "new_status": new_status}



def _update_latest_appointment_status(lead_name, new_status):
    """Update the status of the most recent CRM Appointment for a lead.

    Finds the latest appointment (by termin_datum DESC) and sets its status.
    Silently fails if no appointment exists or CRM Appointment doctype
    is not yet available.
    """
    try:
        if not frappe.db.table_exists("CRM Appointment"):
            return
        latest = frappe.db.sql("""
            SELECT name FROM `tabCRM Appointment`
            WHERE lead = %(lead)s
            ORDER BY termin_datum DESC, creation DESC
            LIMIT 1
        """, {"lead": lead_name}, as_dict=True)
        if latest:
            frappe.db.set_value("CRM Appointment", latest[0].name, "status", new_status)
    except Exception:
        frappe.log_error("Failed to update CRM Appointment status for lead {0}".format(lead_name))


def _create_appointment_from_action(lead_name, data, action_context):
    """Create a CRM Appointment record AND a linked Frappe Event when a termin action occurs.

    Args:
        lead_name: CRM Lead name
        data: action data dict
        action_context: dict with keys that override defaults
            (termin_datum, termin_typ, berater, status, quelle, notiz)
    """
    try:
        apt = frappe.new_doc("CRM Appointment")
        apt.lead = lead_name
        apt.berater = action_context.get("berater") or data.get("termin_berater") or frappe.session.user
        apt.termin_datum = action_context.get("termin_datum") or data.get("termin_datum") or frappe.utils.today()
        apt.typ = action_context.get("termin_typ") or data.get("termin_typ") or "Ersttermin"
        apt.status = action_context.get("status") or "Geplant"
        apt.quelle = action_context.get("quelle") or "Schnellaktion"
        if action_context.get("notiz") or data.get("termin_notiz"):
            apt.notiz = action_context.get("notiz") or data.get("termin_notiz")
        # Set time fields if provided (validate format to prevent garbage microsecond values)
        import re as _re_apt
        def _valid_time(t):
            if not t:
                return None
            t_str = str(t)
            if _re_apt.match(r"^\d{1,2}:\d{2}(:\d{2})?$", t_str):
                return t_str
            return None

        zeit_von = _valid_time(action_context.get("termin_zeit_von")) or _valid_time(data.get("termin_zeit_von"))
        zeit_bis = _valid_time(action_context.get("termin_zeit_bis")) or _valid_time(data.get("termin_zeit_bis"))
        if zeit_von:
            apt.termin_zeit_von = zeit_von
        if zeit_bis:
            apt.termin_zeit_bis = zeit_bis
        apt.flags.ignore_permissions = True
        apt.flags.skip_lead_sync = True  # Caller manages lead fields
        apt.insert(ignore_permissions=True)

        # ── Also create a Frappe Event linked to this CRM Lead ──────────
        event_name = _create_event_for_appointment(lead_name, apt, action_context, data)
        if event_name:
            # Link the Event back to the CRM Appointment
            frappe.db.set_value("CRM Appointment", apt.name, "event_link", event_name, update_modified=False)

        return apt.name
    except Exception:
        frappe.log_error("Failed to create CRM Appointment for lead {0}".format(lead_name))
        return None


def _create_event_for_appointment(lead_name, appointment, action_context, data):
    """Create a Frappe Event document linked to a CRM Lead for the given appointment.

    Sets frappe.flags.skip_event_to_lead_sync to prevent the sync_event_to_lead
    hook from creating a duplicate CRM Appointment or redundantly updating the lead.

    Args:
        lead_name: CRM Lead name (e.g. CRM-LEAD-2026-00039)
        appointment: The already-inserted CRM Appointment doc
        action_context: dict with termin details
        data: original action data dict
    Returns:
        Event name (str) on success, None on failure
    """
    try:
        from datetime import datetime, timedelta
        from frappe.utils import get_time

        termin_datum = str(appointment.termin_datum)
        zeit_von = appointment.termin_zeit_von
        zeit_bis = appointment.termin_zeit_bis

        # Build starts_on datetime
        if zeit_von:
            t_von = get_time(zeit_von)
            starts_on = datetime.strptime(termin_datum, "%Y-%m-%d").replace(
                hour=t_von.hour, minute=t_von.minute, second=t_von.second
            )
        else:
            # No time provided: default to 09:00
            starts_on = datetime.strptime(termin_datum, "%Y-%m-%d").replace(hour=9, minute=0)

        # Build ends_on datetime
        if zeit_bis:
            t_bis = get_time(zeit_bis)
            ends_on = datetime.strptime(termin_datum, "%Y-%m-%d").replace(
                hour=t_bis.hour, minute=t_bis.minute, second=t_bis.second
            )
        else:
            # Default: starts_on + 1 hour
            ends_on = starts_on + timedelta(hours=1)

        # Build descriptive subject
        lead_display = lead_name
        try:
            lead_display = frappe.db.get_value("CRM Lead", lead_name, "lead_name") or lead_name
        except Exception:
            pass
        termin_typ = appointment.typ or "Termin"
        subject = "{0} - {1}".format(termin_typ, lead_display)

        # Build description
        berater = appointment.berater or frappe.session.user
        desc_parts = []
        desc_parts.append("Lead: {0}".format(lead_name))
        desc_parts.append("Berater: {0}".format(berater))
        desc_parts.append("Typ: {0}".format(termin_typ))
        desc_parts.append("Quelle: {0}".format(appointment.quelle or ""))
        if appointment.notiz:
            desc_parts.append("Notiz: {0}".format(appointment.notiz))
        description = "<br>".join(desc_parts)

        # Set flag to prevent sync_event_to_lead from firing for this Event
        frappe.flags.skip_event_to_lead_sync = True
        try:
            event = frappe.new_doc("Event")
            event.subject = subject
            event.starts_on = starts_on
            event.ends_on = ends_on
            event.event_type = "Private"
            event.status = "Open"
            event.reference_doctype = "CRM Lead"
            event.reference_docname = lead_name
            event.description = description

            # Add Berater as Event Participant (if valid user)
            if berater and frappe.db.exists("User", berater):
                event.append("event_participants", {
                    "reference_doctype": "User",
                    "reference_docname": berater,
                    "email": berater,
                })

            event.flags.ignore_permissions = True
            event.insert(ignore_permissions=True)
            return event.name
        finally:
            # Always clear the flag so subsequent Event operations are not affected
            frappe.flags.skip_event_to_lead_sync = False

    except Exception as e:
        frappe.log_error(
            title="Event creation from CRM Appointment failed",
            message="Lead: {0}, Appointment: {1}, Error: {2}".format(
                lead_name, appointment.name if appointment else "N/A", str(e)[:200]
            )
        )
        return None


@frappe.whitelist()
def execute_lead_action(lead_name, action, data=None):
	"""Execute a one-click action on a lead.
	Actions: termin_buchen, followup_setzen, abschluss_gewonnen,
	         abschluss_verloren, an_spezialist_weiterleiten
	Returns: dict with success status and next_lead info."""
	import json
	if isinstance(data, str):
		data = json.loads(data)
	data = data or {}

	if not frappe.has_permission("CRM Lead", "write", lead_name):
		frappe.throw(_("Keine Berechtigung"), frappe.PermissionError)

	lead = frappe.get_doc("CRM Lead", lead_name)
	# Merke altes Follow-up-Datum fuer Gamification
	lead._old_naechster_kontakt = lead.custom_naechster_kontakt
	old_liste = lead.custom_liste or ""
	now = frappe.utils.now_datetime()
	today = frappe.utils.today()
	comment_parts = []
	deferred_appointment = None
	deferred_points = None
	deferred_relationship = False

	if action == "termin_buchen":
		lead.custom_termin_datum = data.get("termin_datum") or today
		termin_typ = data.get("termin_typ", "Ersttermin")
		# Map frontend labels to actual field options
		termin_typ_map = {"Closer": "Closer-Termin", "Beratung": "Follow-up Termin", "Nachtermin": "Follow-up Termin"}
		lead.custom_termin_typ = termin_typ_map.get(termin_typ, termin_typ)
		lead.custom_termin_status = "Geplant"
		# Time slot support (from Terminvorschlaege)
		termin_zeit_von = data.get("termin_zeit_von", "")
		termin_zeit_bis = data.get("termin_zeit_bis", "")
		from_vorschlag = data.get("from_vorschlag", False)
		# Store time on lead for list display
		if termin_zeit_von:
			# Validate and normalize time format (HH:MM or HH:MM:SS)
			import re as _re_time
			if _re_time.match(r"^\d{1,2}:\d{2}(:\d{2})?$", str(termin_zeit_von)):
				lead.custom_termin_zeit_von = termin_zeit_von
			else:
				lead.custom_termin_zeit_von = None
		else:
			lead.custom_termin_zeit_von = None
		# Store lead email for appointment (for reminders)
		termin_email = data.get("termin_email", "")
		# Intelligent Closer routing: use provided berater, or auto-assign
		termin_berater = data.get("termin_berater")
		if from_vorschlag and termin_zeit_von:
			# Re-check availability for this specific slot (race-condition protection)
			# If user explicitly chose a berater, validate that specific person
			chosen_berater = termin_berater if termin_berater else None
			termin_berater = _pick_available_berater(
				lead.custom_termin_datum, termin_zeit_von, termin_zeit_bis,
				lead_name=lead_name, leadtyp=lead.custom_leadtyp,
				specific_berater=chosen_berater
			)
			if not termin_berater:
				if chosen_berater:
					frappe.throw(_("Der gewählte Berater ist zu diesem Zeitpunkt leider nicht mehr verfügbar. Bitte wählen Sie einen anderen Termin oder Berater."))
				else:
					frappe.throw(_("Dieser Termin-Slot ist leider nicht mehr verfügbar. Bitte wählen Sie einen anderen."))
		if not termin_berater:
			try:
				from crm.fcrm.doctype.crm_closer_settings.crm_closer_settings import intelligent_assign_closer
				termin_berater = intelligent_assign_closer(lead_name, leadtyp=lead.custom_leadtyp)
			except Exception:
				pass
		lead.custom_termin_berater = termin_berater or frappe.session.user
		if data.get("termin_notiz"):
			lead.custom_termin_notiz = data["termin_notiz"]
		lead.custom_letzter_kontakt = now
		lead.custom_letzte_kontaktart = "Termin"
		# Status update
		lead.status = "Termin vereinbart"
		time_info = ""
		if termin_zeit_von:
			time_info = " {0}-{1}".format(termin_zeit_von, termin_zeit_bis or "")
		comment_parts.append("Termin gebucht: {0}{1} ({2})".format(
			lead.custom_termin_datum, time_info, lead.custom_termin_typ))
		# Defer appointment creation until after lead.save() to prevent TimestampMismatchError
		deferred_appointment = {
			"termin_datum": lead.custom_termin_datum,
			"termin_typ": lead.custom_termin_typ,
			"berater": lead.custom_termin_berater,
			"status": "Geplant",
			"quelle": "Vorschlag" if from_vorschlag else "Schnellaktion",
			"notiz": data.get("termin_notiz"),
			"termin_zeit_von": termin_zeit_von if termin_zeit_von and _re_time.match(r"^\d{1,2}:\d{2}(:\d{2})?$", str(termin_zeit_von)) else None,
			"termin_zeit_bis": termin_zeit_bis if termin_zeit_bis and _re_time.match(r"^\d{1,2}:\d{2}(:\d{2})?$", str(termin_zeit_bis)) else None,
			"termin_email": termin_email,
		}
		# Gamification: Follow-up puenktlich erledigt ODER Erstkontakt-Reaktionszeit
		if lead._old_naechster_kontakt:
			deferred_points = "followup_puenktlich"
		else:
			deferred_points = "erstkontakt"

	elif action == "followup_setzen":
		lead.custom_naechster_kontakt = data.get("naechster_kontakt")
		lead.custom_followup_grund = data.get("followup_grund", "Rückruf vereinbart")
		if data.get("followup_notiz"):
			lead.custom_followup_notiz = data["followup_notiz"]
		lead.custom_kontaktversuche = (lead.custom_kontaktversuche or 0) + 1
		lead.custom_letzter_kontakt = now
		lead.custom_letzte_kontaktart = data.get("kontaktart", "Anruf")
		# Status update
		lead.status = "Rückruf geplant"
		comment_parts.append("Follow-up gesetzt: {0} ({1})".format(
			lead.custom_naechster_kontakt, lead.custom_followup_grund))
		# Gamification: Wenn ein altes Follow-up pünktlich erledigt wurde, Punkte vergeben
		if lead._old_naechster_kontakt:
			deferred_points = "followup_puenktlich"

	elif action == "abschluss_gewonnen":
		lead.custom_abschluss_datum = data.get("abschluss_datum") or today
		lead.custom_abschluss_produkt = data.get("abschluss_produkt", "")
		lead.custom_abschluss_beitrag = data.get("abschluss_beitrag") or 0
		lead.custom_abschluss_provision = data.get("abschluss_provision") or 0
		if data.get("abschluss_notiz"):
			lead.custom_abschluss_notiz = data["abschluss_notiz"]
		lead.custom_letzter_kontakt = now
		comment_parts.append("Abschluss gewonnen: {0} (Beitrag: {1})".format(
			lead.custom_abschluss_produkt, lead.custom_abschluss_beitrag))
		# Gamification: Abschluss wird ueber Badges belohnt, nicht ueber Punkte
		deferred_relationship = True

	elif action == "abschluss_verloren":
		lead.custom_abschluss_verloren_grund = data.get("verloren_grund", "Kein Interesse")
		lead.custom_abschluss_datum = data.get("abschluss_datum") or today
		if data.get("abschluss_notiz"):
			lead.custom_abschluss_notiz = data["abschluss_notiz"]
		lead.custom_letzter_kontakt = now
		# Status update
		lead.status = "Kein Interesse"
		comment_parts.append("Abschluss verloren: {0}".format(
			lead.custom_abschluss_verloren_grund))
		# Gamification: Kein Punkteabzug fuer verlorene Abschluesse

	elif action == "an_spezialist_weiterleiten":
		lead.custom_an_spezialist_weitergeleitet = 1
		lead.custom_spezialist_typ = data.get("spezialist_typ", "KV Mensch")
		lead.custom_spezialist_user = data.get("spezialist_user", "")
		lead.custom_spezialist_status = "Offen"
		comment_parts.append("An Spezialist weitergeleitet: {0} ({1})".format(
			lead.custom_spezialist_typ, lead.custom_spezialist_user or "noch nicht zugewiesen"))
		# Create CRM Referral record (with Cross-Sell context if provided)
		try:
			cross_sell_prio = data.get("cross_sell_prio", "")
			cross_sell_produkt = data.get("cross_sell_produkt", "")
			created_from = "Cross-Sell" if cross_sell_prio else "Spezialist-Weiterleitung"
			referral = frappe.get_doc({
				"doctype": "CRM Referral",
				"origin_lead": lead_name,
				"referrer_user": frappe.session.user,
				"target_specialist": data.get("spezialist_user", ""),
				"target_topic": data.get("spezialist_typ", "KV Mensch"),
				"referral_status": "Erstellt",
				"created_from": created_from,
				"cross_sell_prio": str(cross_sell_prio) if cross_sell_prio else "",
				"cross_sell_produkt": cross_sell_produkt,
				"notiz": data.get("notiz", ""),
			})
			referral.flags.ignore_permissions = True
			referral.insert(ignore_permissions=True)
			# Update cross-sell status on lead if this was a cross-sell referral
			if cross_sell_prio:
				prio_field = f"custom_cross_sell_prio{cross_sell_prio}_status"
				if hasattr(lead, prio_field):
					setattr(lead, prio_field, "Weiterleitung erstellt")
			if cross_sell_prio:
				pass  # Gamification: Cross-Sell Punkte bei Qualifizierung, nicht bei Weiterleitung
		except Exception as e:
			frappe.log_error(f"CRM Referral creation failed: {e}", "CRM Referral Error")
		# Notify the specialist about the new lead referral
		spezialist_user = data.get("spezialist_user", "")
		if spezialist_user:
			_create_crm_notification(
				from_user=frappe.session.user,
				to_user=spezialist_user,
				notification_type="Task",
				message=f"Neuer Lead zur Qualifizierung: {lead.lead_name or lead_name} ({lead.custom_spezialist_typ})",
				reference_doctype="CRM Lead",
				reference_name=lead_name,
			)

	elif action == "termin_bestaetigen":
		lead.custom_termin_status = "Bestätigt"
		lead.custom_letzter_kontakt = now
		lead.custom_letzte_kontaktart = "Anruf"
		comment_parts.append("Termin bestätigt für {0}".format(lead.custom_termin_datum))
		# Update latest CRM Appointment status
		_update_latest_appointment_status(lead_name, "Bestätigt")

	elif action == "termin_durchgefuehrt":
		lead.custom_termin_status = "Durchgeführt"
		lead.custom_letzter_kontakt = now
		lead.custom_letzte_kontaktart = "Termin"
		# After appointment completed, move to follow-up for post-appointment actions
		if lead.custom_liste in ["20 - Termin gebucht", "50 - Closer-Termin"]:
			lead.custom_liste = "70 - Follow-up"
			lead._skip_liste_validation = True
		comment_parts.append("Termin durchgeführt am {0}".format(lead.custom_termin_datum))
		# Update latest CRM Appointment status
		_update_latest_appointment_status(lead_name, "Durchgeführt")
		deferred_points = "termin_erschienen"  # Punkte fuer durchgefuehrten Termin

	elif action == "termin_noshow":
		lead.custom_termin_status = "No-Show"
		lead.custom_letzter_kontakt = now
		lead.custom_kontaktversuche = (lead.custom_kontaktversuche or 0) + 1
		# No-Show: set follow-up for next day automatically
		from frappe.utils import add_days
		lead.custom_naechster_kontakt = add_days(today, 1)
		lead.custom_followup_grund = "Nachfass nach Termin"
		# Move to follow-up phase
		if lead.custom_liste in ["20 - Termin gebucht", "50 - Closer-Termin"]:
			lead.custom_liste = "70 - Follow-up"
			lead._skip_liste_validation = True
		lead.status = "Kontaktiert aber nicht erreicht"
		comment_parts.append("No-Show: Termin am {0} nicht wahrgenommen".format(lead.custom_termin_datum))
		# Update latest CRM Appointment status
		_update_latest_appointment_status(lead_name, "No-Show")


	elif action == "termin_absagen":
		lead.custom_termin_status = "Abgesagt"
		lead.custom_letzter_kontakt = now
		absage_grund = data.get("absage_grund", "Vom Kunden abgesagt")
		if data.get("termin_notiz"):
			lead.custom_termin_notiz = data["termin_notiz"]
		# Cancellation: move back depending on context
		if lead.custom_liste == "50 - Closer-Termin":
			lead.custom_liste = "70 - Follow-up"
			lead._skip_liste_validation = True
		elif lead.custom_liste == "20 - Termin gebucht":
			lead.custom_liste = "10 - Neu ohne Termin"
			lead._skip_liste_validation = True
		lead.status = "Kontaktiert"
		comment_parts.append("Termin abgesagt: {0}".format(absage_grund))
		# Update latest CRM Appointment status
		_update_latest_appointment_status(lead_name, "Abgesagt")

	elif action == "termin_verschieben":
		lead.custom_termin_status = "Verschoben"
		neues_datum = data.get("neues_datum")
		if neues_datum:
			lead.custom_termin_datum = neues_datum
			lead.custom_termin_status = "Geplant"
			# Update time on lead if provided
			neue_zeit_von = data.get("termin_zeit_von", "")
			lead.custom_termin_zeit_von = neue_zeit_von or None
		lead.custom_letzter_kontakt = now
		if data.get("termin_notiz"):
			lead.custom_termin_notiz = data["termin_notiz"]
		lead.status = "Termin vereinbart"
		comment_parts.append("Termin verschoben{0}".format(
			" auf {0}".format(neues_datum) if neues_datum else ""))
		# Update latest appointment: mark as Verschoben and create new if rescheduled
		_update_latest_appointment_status(lead_name, "Verschoben")
		if neues_datum:
			deferred_appointment = {
				"termin_datum": neues_datum,
				"termin_typ": lead.custom_termin_typ,
				"berater": lead.custom_termin_berater,
				"status": "Geplant",
				"quelle": "Schnellaktion",
				"notiz": data.get("termin_notiz"),
			}

	elif action == "spezialist_qualifiziert":
		lead.custom_spezialist_status = "Qualifiziert"
		lead.custom_letzter_kontakt = now
		# Set premium based on specialist type + mitarbeiter_kategorie (from CRM Prämien Einstellungen)
		if not lead.custom_veredelungspraemie:
			ueberleiter = lead.custom_spezialist_user or frappe.session.user
			lead.custom_veredelungspraemie = get_premium_amount(
				lead.custom_spezialist_typ or "Sonstiges",
				user=ueberleiter
			)
		lead.custom_praemie_status = "Berechnet"
		qualif_notiz = data.get("qualif_notiz", "")
		comment_parts.append("Spezialist: Lead qualifiziert ({0}){1}".format(
			lead.custom_spezialist_typ,
			" - {0}".format(qualif_notiz) if qualif_notiz else ""))
		# Update existing CRM Referral
		try:
			referrals = frappe.get_all("CRM Referral",
				filters={"origin_lead": lead_name, "referral_status": ["in", ["Erstellt", "Kontaktiert"]]},
				order_by="creation desc", limit=1)
			if referrals:
				ref = frappe.get_doc("CRM Referral", referrals[0].name)
				ref.referral_status = "Qualifiziert"
				ref.qualified_date = frappe.utils.today()
				ref.qualified_by = frappe.session.user
				if qualif_notiz:
					ref.notiz = (ref.notiz or "") + ("\n" if ref.notiz else "") + qualif_notiz
				ref.flags.ignore_permissions = True
				ref.save(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(f"CRM Referral update (qualifiziert) failed: {e}", "CRM Referral Error")
		deferred_points = "weiterleitung_qualifiziert"

	elif action == "spezialist_nicht_qualifiziert":
		lead.custom_spezialist_status = "Nicht qualifiziert"
		lead.custom_letzter_kontakt = now
		lead.custom_veredelungspraemie = 0
		lead.custom_praemie_status = ""
		grund = data.get("nicht_qualif_grund", "Nicht spezifiziert")
		comment_parts.append("Spezialist: Lead nicht qualifiziert ({0}) - Grund: {1}".format(
			lead.custom_spezialist_typ, grund))
		# Update existing CRM Referral
		try:
			referrals = frappe.get_all("CRM Referral",
				filters={"origin_lead": lead_name, "referral_status": ["in", ["Erstellt", "Kontaktiert"]]},
				order_by="creation desc", limit=1)
			if referrals:
				ref = frappe.get_doc("CRM Referral", referrals[0].name)
				ref.referral_status = "Nicht qualifiziert"
				ref.premium_amount = 0
				ref.premium_status = "Offen"
				ref.notiz = (ref.notiz or "") + ("\n" if ref.notiz else "") + "Nicht qualifiziert: " + grund
				ref.flags.ignore_permissions = True
				ref.save(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(f"CRM Referral update (nicht qualifiziert) failed: {e}", "CRM Referral Error")

	elif action == "reaktivieren":
		# Reset abschluss fields for re-activation
		lead.custom_abschluss_verloren_grund = ""
		lead.custom_abschluss_datum = None
		lead.custom_liste = "30 - Reaktivierung"
		lead._skip_liste_validation = True
		lead.status = "Nicht kontaktiert"
		comment_parts.append("Lead reaktiviert")

	else:
		frappe.throw(_("Unbekannte Aktion: {0}").format(action))

	lead.save(ignore_permissions=True)

	# Execute deferred actions (after save to prevent TimestampMismatchError)
	if deferred_appointment:
		_create_appointment_from_action(lead_name, data, deferred_appointment)
	if deferred_points:
		_try_award_points(frappe.session.user, deferred_points, lead_name=lead_name)
	if deferred_relationship:
		_create_relationship_on_close(lead)

	# Add audit comment
	if comment_parts:
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": "CRM Lead",
			"reference_name": lead_name,
			"content": "AKTION: " + "; ".join(comment_parts),
		}).insert(ignore_permissions=True)

	frappe.db.commit()

	return {
		"success": True,
		"action": action,
		"old_liste": old_liste,
		"new_phase": lead.custom_liste,
		"new_status": lead.status,
		"phase_changed": old_liste != (lead.custom_liste or ""),
	}




@frappe.whitelist()
def create_todo_for_lead(lead_name, description, due_date=None, due_time=None, priority="Medium"):
	"""Create a ToDo (Aufgabe) linked to a CRM Lead.
	Args:
		lead_name: CRM Lead name
		description: Task description text
		due_date: Due date (YYYY-MM-DD), defaults to tomorrow
		due_time: Due time (HH:MM), defaults to 09:00
		priority: Low/Medium/High, defaults to Medium
	Returns: dict with success status and todo name
	"""
	if not frappe.has_permission("CRM Lead", "read", lead_name):
		frappe.throw(_("Keine Berechtigung"), frappe.PermissionError)

	if not description or not description.strip():
		frappe.throw(_("Aufgabenbeschreibung darf nicht leer sein"))

	from frappe.utils import add_days, today as get_today

	if not due_date:
		due_date = add_days(get_today(), 1)

	# Build rich description with time info
	full_description = description.strip()
	if due_time:
		full_description += " (Fällig um {0})".format(due_time)

	todo = frappe.get_doc({
		"doctype": "ToDo",
		"description": full_description,
		"reference_type": "CRM Lead",
		"reference_name": lead_name,
		"allocated_to": frappe.session.user,
		"date": due_date,
		"status": "Open",
		"priority": priority if priority in ["Low", "Medium", "High"] else "Medium",
	})
	todo.insert(ignore_permissions=True)

	# Add audit comment on the lead
	frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Info",
		"reference_doctype": "CRM Lead",
		"reference_name": lead_name,
		"content": "AUFGABE ERSTELLT: {0} (Fällig: {1}{2})".format(
			description.strip(),
			due_date,
			" um {0}".format(due_time) if due_time else ""
		),
	}).insert(ignore_permissions=True)

	frappe.db.commit()

	return {
		"success": True,
		"todo_name": todo.name,
		"description": full_description,
		"due_date": due_date,
	}


@frappe.whitelist()
def get_vertriebler_list():
    """Return list of active Vertriebler (ohne Geschaeftsfuehrer) for Berater dropdown."""
    users = frappe.get_all(
        "User",
        filters={
            "user_type": "System User",
            "name": ["not in", ["Administrator", "Guest", "landing-page@api.local"]],
            "role_profile_name": "Vertriebler",
            "enabled": 1,
        },
        fields=["name as email", "full_name"],
        order_by="full_name asc",
    )
    return [{"email": u.email, "full_name": u.full_name or u.email} for u in users]

@frappe.whitelist()
def get_next_lead(current_lead, current_phase=None, assigned_to=None):
	"""Get the next lead to work on after current lead's phase changed.

	Cascading priority:
	1. Same liste, assigned to current user (via _assign or lead_owner)
	2. Same liste, any lead
	3. Next liste in priority order (10, 20, 30, 50, 70) - assigned first, then any
	4. None (all done)

	Returns dict with next_lead, remaining count, same_liste flag, and all_done flag.
	"""
	if not assigned_to:
		assigned_to = frappe.session.user

	user_pattern = "%{}%".format(assigned_to)

	# Active lists in work priority order (skip 80/90 = closed)
	active_lists = [
		"10 - Neu ohne Termin",
		"20 - Termin gebucht",
		"30 - Reaktivierung",
		"50 - Closer-Termin",
		"70 - Follow-up",
	]

	def _find_lead_in_liste(liste, only_assigned=False):
		"""Find the next lead in a specific liste.
		If only_assigned=True, only returns leads assigned/owned by user."""
		if only_assigned:
			leads = frappe.db.sql("""
				SELECT name FROM `tabCRM Lead`
				WHERE custom_liste = %(liste)s
				  AND name != %(current)s
				  AND converted = 0
				  AND (_assign LIKE %(pattern)s OR lead_owner = %(user)s)
				ORDER BY modified ASC
				LIMIT 1
			""", {
				"liste": liste,
				"current": current_lead,
				"pattern": user_pattern,
				"user": assigned_to,
			}, as_dict=True)
		else:
			leads = frappe.db.sql("""
				SELECT name FROM `tabCRM Lead`
				WHERE custom_liste = %(liste)s
				  AND name != %(current)s
				  AND converted = 0
				ORDER BY modified ASC
				LIMIT 1
			""", {
				"liste": liste,
				"current": current_lead,
			}, as_dict=True)
		return leads[0].name if leads else None

	def _count_in_liste(liste, only_assigned=False):
		"""Count remaining leads in a liste (excluding current)."""
		if only_assigned:
			result = frappe.db.sql("""
				SELECT COUNT(*) as cnt FROM `tabCRM Lead`
				WHERE custom_liste = %(liste)s
				  AND name != %(current)s
				  AND converted = 0
				  AND (_assign LIKE %(pattern)s OR lead_owner = %(user)s)
			""", {
				"liste": liste,
				"current": current_lead,
				"pattern": user_pattern,
				"user": assigned_to,
			}, as_dict=True)
		else:
			result = frappe.db.sql("""
				SELECT COUNT(*) as cnt FROM `tabCRM Lead`
				WHERE custom_liste = %(liste)s
				  AND name != %(current)s
				  AND converted = 0
			""", {
				"liste": liste,
				"current": current_lead,
			}, as_dict=True)
		return result[0].cnt if result else 0

	# --- Priority 1: Same liste, assigned to me ---
	if current_phase:
		next_lead = _find_lead_in_liste(current_phase, only_assigned=True)
		if next_lead:
			remaining = _count_in_liste(current_phase, only_assigned=True)
			return {
				"next_lead": next_lead,
				"remaining": remaining,
				"same_liste": True,
				"liste": current_phase,
				"all_done": False,
			}

		# --- Priority 2: Same liste, any lead ---
		next_lead = _find_lead_in_liste(current_phase, only_assigned=False)
		if next_lead:
			remaining = _count_in_liste(current_phase, only_assigned=False)
			return {
				"next_lead": next_lead,
				"remaining": remaining,
				"same_liste": True,
				"liste": current_phase,
				"all_done": False,
			}

	# --- Priority 3: Next liste in order (assigned first, then any) ---
	# Determine starting position in list order
	start_idx = 0
	if current_phase:
		for i, lst in enumerate(active_lists):
			if lst == current_phase:
				start_idx = i
				break

	for offset in range(len(active_lists)):
		idx = (start_idx + offset) % len(active_lists)
		liste = active_lists[idx]
		if liste == current_phase:
			continue  # Already checked above

		# Try assigned first
		next_lead = _find_lead_in_liste(liste, only_assigned=True)
		if next_lead:
			remaining = _count_in_liste(liste, only_assigned=True)
			return {
				"next_lead": next_lead,
				"remaining": remaining,
				"same_liste": False,
				"liste": liste,
				"all_done": False,
			}

		# Try any lead
		next_lead = _find_lead_in_liste(liste, only_assigned=False)
		if next_lead:
			remaining = _count_in_liste(liste, only_assigned=False)
			return {
				"next_lead": next_lead,
				"remaining": remaining,
				"same_liste": False,
				"liste": liste,
				"all_done": False,
			}

	# --- Priority 4: All done ---
	return {
		"next_lead": None,
		"remaining": 0,
		"same_liste": False,
		"liste": None,
		"all_done": True,
	}


@frappe.whitelist()
def get_lead_queue_counts(user=None):
	"""Return lead counts per pipeline phase for sidebar queue badges.

	System Manager: counts ALL leads across all phases.
	Regular users: counts only leads assigned to them (_assign) or owned by them.

	Returns a dict with phase counts, total, and overdue_followups.
	"""
	if not user:
		user = frappe.session.user

	is_admin = "System Manager" in frappe.get_roles(user)

	phases = [
		"10 - Neu ohne Termin",
		"20 - Termin gebucht",
		"30 - Reaktivierung",
		"50 - Closer-Termin",
		"70 - Follow-up",
		"80 - Abschluss gewonnen",
		"90 - Abschluss verloren",
	]

	result = {phase: 0 for phase in phases}
	result["total"] = 0
	result["overdue_followups"] = 0

	if is_admin:
		# Admin sees all leads
		phase_counts = frappe.db.sql("""
			SELECT custom_liste, COUNT(*) as cnt
			FROM `tabCRM Lead`
			WHERE custom_liste IS NOT NULL
			  AND custom_liste != ''
			  AND converted = 0
			GROUP BY custom_liste
		""", as_dict=True)
	else:
		# Regular user: leads assigned via _assign or owned
		user_pattern = "%{}%".format(user)
		phase_counts = frappe.db.sql("""
			SELECT custom_liste, COUNT(*) as cnt
			FROM `tabCRM Lead`
			WHERE custom_liste IS NOT NULL
			  AND custom_liste != ''
			  AND converted = 0
			  AND (_assign LIKE %(pattern)s OR lead_owner = %(user)s)
			GROUP BY custom_liste
		""", {"pattern": user_pattern, "user": user}, as_dict=True)

	for row in phase_counts:
		if row.custom_liste in result:
			result[row.custom_liste] = row.cnt

	result["total"] = sum(result[p] for p in phases)

	# Overdue follow-ups
	if is_admin:
		overdue = frappe.db.sql("""
			SELECT COUNT(*) as cnt
			FROM `tabCRM Lead`
			WHERE custom_naechster_kontakt < CURDATE()
			  AND custom_naechster_kontakt IS NOT NULL
			  AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
			  AND converted = 0
		""", as_dict=True)
	else:
		user_pattern = "%{}%".format(user)
		overdue = frappe.db.sql("""
			SELECT COUNT(*) as cnt
			FROM `tabCRM Lead`
			WHERE custom_naechster_kontakt < CURDATE()
			  AND custom_naechster_kontakt IS NOT NULL
			  AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
			  AND converted = 0
			  AND (_assign LIKE %(pattern)s OR lead_owner = %(user)s)
		""", {"pattern": user_pattern, "user": user}, as_dict=True)

	result["overdue_followups"] = overdue[0].cnt if overdue else 0

	return result

@frappe.whitelist()
def process_overdue_followups():
	"""Scheduled job: Process overdue follow-ups.

	Runs hourly. For leads where custom_naechster_kontakt < today:
	1. Creates a notification for the assigned user / lead_owner
	2. Creates a CRM Task (activity) with type 'Follow-up' and status 'Offen'
	3. Only sends one notification per lead per day (idempotent)
	4. Only creates one auto-task per lead per overdue period (idempotent)

	Only processes leads NOT in closed phases (80, 90).
	"""
	today = frappe.utils.today()

	overdue_leads = frappe.db.sql("""
		SELECT l.name, l.lead_name, l.lead_owner, l.custom_naechster_kontakt,
		       l.custom_liste, l.custom_followup_grund, l.custom_kontaktversuche
		FROM `tabCRM Lead` l
		WHERE l.custom_naechster_kontakt < %(today)s
		  AND l.custom_naechster_kontakt IS NOT NULL
		  AND l.custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
	""", {"today": today}, as_dict=True)

	tasks_created = 0
	notifications_sent = 0

	for lead in overdue_leads:
		# Find the responsible user (assigned or owner)
		assigned_users = frappe.db.sql("""
			SELECT allocated_to FROM `tabToDo`
			WHERE reference_type = 'CRM Lead'
			  AND reference_name = %(name)s
			  AND status != 'Cancelled'
			ORDER BY modified DESC LIMIT 1
		""", {"name": lead.name}, as_dict=True)

		notify_user = assigned_users[0].allocated_to if assigned_users else lead.lead_owner
		if not notify_user:
			continue

		# Calculate days overdue
		from frappe.utils import date_diff
		days_overdue = date_diff(today, lead.custom_naechster_kontakt)

		# Auto-create CRM Task for overdue follow-up (one per lead, idempotent)
		existing_task = frappe.db.exists("CRM Task", {
			"reference_doctype": "CRM Lead",
			"reference_docname": lead.name,
			"custom_activity_type": "Follow-up",
			"custom_auto_created": 1,
			"status": ["not in", ["Done", "Canceled"]],
		})

		if not existing_task:
			grund = lead.custom_followup_grund or "Überfälliger Follow-up"
			task = frappe.new_doc("CRM Task")
			task.title = f"Follow-up: {lead.lead_name or lead.name}"
			task.description = (
				f"Automatisch erstellte Follow-up-Aufgabe.\n"
				f"Grund: {grund}\n"
				f"Fällig seit: {lead.custom_naechster_kontakt} ({days_overdue} Tage überfällig)\n"
				f"Kontaktversuche: {lead.custom_kontaktversuche or 0}"
			)
			task.assigned_to = notify_user
			task.due_date = lead.custom_naechster_kontakt
			task.priority = "High" if days_overdue > 3 else "Medium"
			task.status = "Todo"
			task.reference_doctype = "CRM Lead"
			task.reference_docname = lead.name
			task.custom_activity_type = "Follow-up"
			task.custom_followup_status = "Überfällig"
			task.custom_auto_created = 1
			task.custom_lead_liste = lead.custom_liste or ""
			task.insert(ignore_permissions=True)
			tasks_created += 1

		# Only send notification once per day per lead (check if already sent today)
		existing = frappe.db.exists("Notification Log", {
			"for_user": notify_user,
			"document_type": "CRM Lead",
			"document_name": lead.name,
			"creation": [">=", today]
		})

		if not existing:
			# Create notification
			fu_subject = f"Follow-up überfällig: {lead.lead_name or lead.name} ({days_overdue} Tage)"
			fu_body = f"Der Follow-up-Termin für Lead {lead.lead_name or lead.name} war am {lead.custom_naechster_kontakt}. Bitte zeitnah kontaktieren."
			notification = frappe.new_doc("Notification Log")
			notification.for_user = notify_user
			notification.type = "Alert"
			notification.document_type = "CRM Lead"
			notification.document_name = lead.name
			notification.subject = fu_subject
			notification.email_content = fu_body
			notification.insert(ignore_permissions=True)

			# Also create CRM Notification for the CRM frontend bell icon
			_create_crm_notification(
				from_user="Administrator",
				to_user=notify_user,
				notification_type="Task",
				message=f"<b>{fu_subject}</b><br>{fu_body}",
				reference_doctype="CRM Lead",
				reference_name=lead.name,
			)
			notifications_sent += 1

	frappe.db.commit()
	return f"Processed {len(overdue_leads)} overdue leads: {tasks_created} tasks created, {notifications_sent} notifications sent"


@frappe.whitelist()
def get_active_sales_users():
	"""Gibt aktive Vertriebler aus der Mitarbeiterverwaltung zurück (role_profile_name = 'Vertriebler').

	Nur User die in der Mitarbeiterverwaltung als 'Vertriebler' angelegt wurden, werden für
	die automatische Lead-Zuweisung (Round-Robin, Skill-basiert, Kapazität) berücksichtigt.
	Andere User mit CRM-Rollen (Sales, Geschäftsführer, etc.) werden NICHT zugewiesen.
	"""
	users = frappe.db.sql("""
		SELECT u.name, u.full_name
		FROM `tabUser` u
		WHERE u.role_profile_name = 'Vertriebler'
		  AND u.enabled = 1
		  AND u.name NOT IN ('Administrator', 'Guest')
		ORDER BY u.full_name
	""", as_dict=True)
	return users



def _create_relationship_on_close(lead):
    """Create or update a CRM Relationship when a lead is closed as won.
    Sets the current user as primary advisor for the lead's contact email."""
    if not lead.email:
        return

    try:
        existing = frappe.get_all(
            "CRM Relationship",
            filters={"contact_email": lead.email, "status": "Aktiv"},
            fields=["name"],
            limit=1,
        )

        if not existing:
            rel = frappe.new_doc("CRM Relationship")
            rel.contact_email = lead.email
            rel.contact_name = lead.lead_name or "{0} {1}".format(
                lead.first_name or "", lead.last_name or ""
            ).strip()
            rel.primary_advisor = frappe.session.user
            rel.origin_lead = lead.name
            rel.lead_typ = lead.custom_leadtyp or ""
            rel.start_date = frappe.utils.today()
            rel.status = "Aktiv"
            rel.insert(ignore_permissions=True)
            frappe.get_doc({
                "doctype": "Comment",
                "comment_type": "Info",
                "reference_doctype": "CRM Lead",
                "reference_name": lead.name,
                "content": "Primaerberater-Beziehung erstellt: {0}".format(
                    frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
                ),
            }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error("CRM Relationship Erstellung fehlgeschlagen für Lead: {0}".format(lead.name))



def auto_assign_lead(lead_name):
	"""Assign a new lead using intelligent routing (skill-based, capacity, or round-robin).

	Uses CRM Closer Settings for routing configuration.
	Falls back to simple round-robin if settings are not configured.
	Skips if lead already has a lead_owner set (e.g., from import with specific assignment).
	"""
	lead = frappe.get_doc("CRM Lead", lead_name)

	# Skip if already assigned
	if lead.lead_owner and lead.lead_owner not in ('', 'Administrator'):
		return

	# Try intelligent routing first
	assigned_user = None
	try:
		from crm.fcrm.doctype.crm_closer_settings.crm_closer_settings import intelligent_assign_closer
		assigned_user = intelligent_assign_closer(lead_name, leadtyp=lead.custom_leadtyp)
	except Exception:
		# Fallback to simple round-robin if intelligent routing fails
		pass

	if not assigned_user:
		# Simple round-robin fallback
		users = get_active_sales_users()
		if not users:
			return

		user_list = [u.name for u in users]
		cache_key = "crm_lead_round_robin_index"
		last_index = frappe.cache.get_value(cache_key) or 0
		next_index = (last_index + 1) % len(user_list)
		assigned_user = user_list[next_index]
		frappe.cache.set_value(cache_key, next_index)

	# Set lead_owner
	frappe.db.set_value("CRM Lead", lead_name, "lead_owner", assigned_user)

	# Create ToDo assignment
	from frappe.desk.form.assign_to import add as assign_to
	assign_to({
		"doctype": "CRM Lead",
		"name": lead_name,
		"assign_to": [assigned_user],
		"description": "Neuer Lead automatisch zugewiesen"
	})

	frappe.msgprint(
		"Lead automatisch zugewiesen an {0}".format(
			frappe.db.get_value('User', assigned_user, 'full_name') or assigned_user
		),
		alert=True
	)



# ---------------------------------------------------------------------------
# Prämien-Konto / Export System
# ---------------------------------------------------------------------------

def _get_praemien_period_filter(period):
	"""Return SQL date condition for the given period, applied to custom_abschluss_datum or modified."""
	import frappe.utils
	today = frappe.utils.today()
	year = frappe.utils.getdate(today).year
	month = frappe.utils.getdate(today).month
	quarter_start_month = ((month - 1) // 3) * 3 + 1

	if period == "month":
		start = f"{year}-{month:02d}-01"
		return f" AND (l.custom_abschluss_datum >= '{start}' OR (l.custom_abschluss_datum IS NULL AND l.modified >= '{start}'))"
	elif period == "quarter":
		start = f"{year}-{quarter_start_month:02d}-01"
		return f" AND (l.custom_abschluss_datum >= '{start}' OR (l.custom_abschluss_datum IS NULL AND l.modified >= '{start}'))"
	elif period == "year":
		start = f"{year}-01-01"
		return f" AND (l.custom_abschluss_datum >= '{start}' OR (l.custom_abschluss_datum IS NULL AND l.modified >= '{start}'))"
	else:
		# "all" or unknown => no filter
		return ""


@frappe.whitelist()
def get_praemien_uebersicht(user=None, period="month"):
	"""Return a structured overview of all premiums (Veredelungspraemien).

	Args:
		user: Optional user email to filter by. Non-admins can only see their own data.
		period: "month" | "quarter" | "year" | "all"

	Returns:
		dict with keys: summary, by_user, by_typ
	"""
	import json

	is_admin = "System Manager" in frappe.get_roles()

	# Non-admins can only see their own premiums
	if not is_admin:
		user = frappe.session.user

	period_filter = _get_praemien_period_filter(period)

	user_filter = ""
	if user:
		user_filter = f" AND l.custom_spezialist_user = {frappe.db.escape(user)}"

	# Fetch all leads with premiums
	query = f"""
		SELECT
			l.name AS lead_id,
			l.lead_name,
			l.custom_spezialist_user,
			l.custom_spezialist_typ,
			l.custom_veredelungspraemie,
			l.custom_praemie_status,
			COALESCE(l.custom_abschluss_datum, DATE(l.modified)) AS datum
		FROM `tabCRM Lead` l
		WHERE l.custom_veredelungspraemie > 0
		{user_filter}
		{period_filter}
		ORDER BY datum DESC
	"""
	rows = frappe.db.sql(query, as_dict=True)

	# Build summary
	total_berechnet = 0.0
	total_ausgezahlt = 0.0
	count_berechnet = 0
	count_ausgezahlt = 0

	for r in rows:
		amount = float(r.custom_veredelungspraemie or 0)
		status = r.custom_praemie_status or "Offen"
		if status == "Berechnet":
			total_berechnet += amount
			count_berechnet += 1
		elif status == "Ausgezahlt":
			total_ausgezahlt += amount
			count_ausgezahlt += 1
		else:
			# Offen counts as berechnet (pending)
			total_berechnet += amount
			count_berechnet += 1

	summary = {
		"total_berechnet": total_berechnet,
		"total_ausgezahlt": total_ausgezahlt,
		"total_offen": total_berechnet - total_ausgezahlt,
		"count_berechnet": count_berechnet,
		"count_ausgezahlt": count_ausgezahlt,
	}

	# Group by user
	user_map = {}
	for r in rows:
		uid = r.custom_spezialist_user or "Unbekannt"
		if uid not in user_map:
			full_name = ""
			if uid and uid != "Unbekannt":
				full_name = frappe.db.get_value("User", uid, "full_name") or uid
			user_map[uid] = {
				"user": uid,
				"full_name": full_name,
				"total": 0.0,
				"berechnet": 0.0,
				"ausgezahlt": 0.0,
				"count": 0,
				"leads": [],
			}
		amount = float(r.custom_veredelungspraemie or 0)
		status = r.custom_praemie_status or "Offen"
		user_map[uid]["total"] += amount
		user_map[uid]["count"] += 1
		if status == "Ausgezahlt":
			user_map[uid]["ausgezahlt"] += amount
		else:
			user_map[uid]["berechnet"] += amount
		user_map[uid]["leads"].append({
			"lead": r.lead_id,
			"lead_name": r.lead_name or "",
			"spezialist_typ": r.custom_spezialist_typ or "",
			"praemie": amount,
			"status": status,
			"datum": str(r.datum) if r.datum else "",
		})

	by_user = sorted(user_map.values(), key=lambda x: x["total"], reverse=True)

	# Group by typ
	typ_map = {}
	for r in rows:
		typ = r.custom_spezialist_typ or "Sonstiges"
		if typ not in typ_map:
			typ_map[typ] = {"typ": typ, "total": 0.0, "count": 0}
		typ_map[typ]["total"] += float(r.custom_veredelungspraemie or 0)
		typ_map[typ]["count"] += 1

	by_typ = sorted(typ_map.values(), key=lambda x: x["total"], reverse=True)

	return {
		"summary": summary,
		"by_user": by_user,
		"by_typ": by_typ,
	}


@frappe.whitelist()
def export_praemien_csv(period="month"):
	"""Export premiums as CSV file (semicolon-separated, German-style).

	Only accessible to System Manager role.
	Columns: Datum, Lead-ID, Lead-Name, Spezialist, Spezialist-Typ, Prämie EUR, Status
	"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Keine Berechtigung für Prämien-Export", frappe.PermissionError)

	import csv
	import io

	period_filter = _get_praemien_period_filter(period)

	query = f"""
		SELECT
			COALESCE(l.custom_abschluss_datum, DATE(l.modified)) AS datum,
			l.name AS lead_id,
			l.lead_name,
			l.custom_spezialist_user,
			l.custom_spezialist_typ,
			l.custom_veredelungspraemie,
			l.custom_praemie_status
		FROM `tabCRM Lead` l
		WHERE l.custom_veredelungspraemie > 0
		{period_filter}
		ORDER BY datum DESC
	"""
	rows = frappe.db.sql(query, as_dict=True)

	# Resolve user full names (cache to avoid repeated lookups)
	user_names = {}
	for r in rows:
		u = r.custom_spezialist_user
		if u and u not in user_names:
			user_names[u] = frappe.db.get_value("User", u, "full_name") or u

	output = io.StringIO()
	writer = csv.writer(output, delimiter=";")
	writer.writerow(["Datum", "Lead-ID", "Lead-Name", "Spezialist", "Spezialist-Typ", "Prämie EUR", "Status"])

	for r in rows:
		writer.writerow([
			str(r.datum) if r.datum else "",
			r.lead_id,
			r.lead_name or "",
			user_names.get(r.custom_spezialist_user, r.custom_spezialist_user or ""),
			r.custom_spezialist_typ or "",
			f"{float(r.custom_veredelungspraemie or 0):.2f}",
			r.custom_praemie_status or "Offen",
		])

	frappe.response["filename"] = f"praemien_export_{period}_{frappe.utils.today()}.csv"
	frappe.response["filecontent"] = output.getvalue()
	frappe.response["type"] = "download"

@frappe.whitelist()
def process_termin_reminders():
	"""Scheduled job (every 15 min): Send termin reminders.

	For leads with upcoming appointments (custom_termin_datum):
	- 24h reminder: termin between 23h and 25h from now
	- 1h reminder:  termin between 30min and 90min from now

	Creates Notification Log entries for the assigned user AND
	the termin_berater. Idempotent: skips if notification for
	the same lead+type combination already exists today.
	"""
	from frappe.utils import now_datetime, get_datetime
	import math

	now = now_datetime()
	today_str = now.strftime("%Y-%m-%d")

	# Find leads with active appointments not in closed phases
	leads = frappe.db.sql("""
		SELECT l.name, l.lead_name, l.lead_owner,
		       l.custom_termin_datum, l.custom_termin_typ,
		       l.custom_termin_status, l.custom_termin_berater,
		       l.custom_liste
		FROM `tabCRM Lead` l
		WHERE l.custom_termin_datum IS NOT NULL
		  AND l.custom_termin_status IN ('Geplant', 'Bestätigt')
		  AND l.custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
		  AND l.custom_termin_datum >= %(now)s
	""", {"now": now}, as_dict=True)

	reminders_sent = 0

	for lead in leads:
		try:
			termin_dt = get_datetime(lead.custom_termin_datum)
			hours_until = (termin_dt - now).total_seconds() / 3600.0

			reminder_type = None
			subject = ""
			body = ""

			# 24h reminder: between 23h and 25h away
			if 23.0 <= hours_until <= 25.0:
				reminder_type = "24h"
				termin_date_str = termin_dt.strftime("%d.%m.%Y um %H:%M")
				subject = f"Termin-Erinnerung (24h): {lead.lead_name or lead.name} am {termin_date_str}"
				body = (
					f"Morgen steht ein Termin an für {lead.lead_name or lead.name}.\n"
					f"Datum: {termin_date_str}\n"
					f"Typ: {lead.custom_termin_typ or 'k.A.'}\n"
					f"Status: {lead.custom_termin_status}"
				)

			# 1h reminder: between 30min and 90min away
			elif 0.5 <= hours_until <= 1.5:
				reminder_type = "1h"
				termin_time_str = termin_dt.strftime("%H:%M")
				minutes_until = int(math.ceil(hours_until * 60))
				subject = f"Termin in {minutes_until} Minuten: {lead.lead_name or lead.name} um {termin_time_str}"
				body = (
					f"In {minutes_until} Minuten beginnt der Termin mit {lead.lead_name or lead.name}.\n"
					f"Uhrzeit: {termin_time_str}\n"
					f"Typ: {lead.custom_termin_typ or 'k.A.'}\n"
					f"Status: {lead.custom_termin_status}"
				)

			if not reminder_type:
				continue

			# Collect users to notify: assigned user + termin_berater
			users_to_notify = set()

			# Find assigned user
			assigned_users = frappe.db.sql("""
				SELECT allocated_to FROM `tabToDo`
				WHERE reference_type = 'CRM Lead'
				  AND reference_name = %(name)s
				  AND status != 'Cancelled'
				ORDER BY modified DESC LIMIT 1
			""", {"name": lead.name}, as_dict=True)

			if assigned_users:
				users_to_notify.add(assigned_users[0].allocated_to)
			elif lead.lead_owner:
				users_to_notify.add(lead.lead_owner)

			if lead.custom_termin_berater:
				users_to_notify.add(lead.custom_termin_berater)

			# Send notification to each user (idempotent per lead+type+user+day)
			for user in users_to_notify:
				if not user:
					continue

				# Build a unique subject prefix for idempotency check
				check_prefix = f"Termin-Erinnerung ({reminder_type})" if reminder_type == "24h" else f"Termin in"

				existing = frappe.db.sql("""
					SELECT name FROM `tabNotification Log`
					WHERE for_user = %(user)s
					  AND document_type = 'CRM Lead'
					  AND document_name = %(lead)s
					  AND subject LIKE %(prefix)s
					  AND creation >= %(today)s
					LIMIT 1
				""", {
					"user": user,
					"lead": lead.name,
					"prefix": f"{check_prefix}%",
					"today": today_str,
				}, as_dict=True)

				if existing:
					continue

				notification = frappe.new_doc("Notification Log")
				notification.for_user = user
				notification.type = "Alert"
				notification.document_type = "CRM Lead"
				notification.document_name = lead.name
				notification.subject = subject
				notification.email_content = body
				notification.insert(ignore_permissions=True)

				# Also create CRM Notification for the CRM frontend bell icon
				_create_crm_notification(
					from_user="Administrator",
					to_user=user,
					notification_type="Task",
					message=f"<b>{subject}</b><br>{body}",
					reference_doctype="CRM Lead",
					reference_name=lead.name,
				)
				reminders_sent += 1

		except Exception as e:
			frappe.log_error(
				title=f"Termin Reminder Error: {lead.name}",
				message=str(e)
			)

	frappe.db.commit()
	return f"Processed {len(leads)} leads, sent {reminders_sent} reminders"


@frappe.whitelist()
def get_upcoming_termine(hours=24):
	"""Return upcoming appointments for the current user.

	Filters to leads where the current user is either the assigned user
	(lead_owner) or the termin_berater.

	Args:
		hours: Look-ahead window in hours (default 24)

	Returns:
		list of dicts with lead_name, lead_display, termin_datum,
		termin_typ, termin_status, termin_berater, hours_until, is_urgent
	"""
	from frappe.utils import now_datetime, get_datetime, cint
	import math

	hours = cint(hours) or 24
	now = now_datetime()
	from datetime import timedelta
	cutoff = now + timedelta(hours=hours)
	current_user = frappe.session.user

	leads = frappe.db.sql("""
		SELECT l.name AS lead_name, l.lead_name AS lead_display,
		       l.custom_termin_datum AS termin_datum,
		       l.custom_termin_typ AS termin_typ,
		       l.custom_termin_status AS termin_status,
		       l.custom_termin_berater AS termin_berater,
		       l.lead_owner
		FROM `tabCRM Lead` l
		WHERE l.custom_termin_datum IS NOT NULL
		  AND l.custom_termin_datum >= %(now)s
		  AND l.custom_termin_datum <= %(cutoff)s
		  AND l.custom_termin_status IN ('Geplant', 'Bestätigt')
		  AND l.custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
		  AND (l.lead_owner = %(user)s OR l.custom_termin_berater = %(user)s)
		ORDER BY l.custom_termin_datum ASC
	""", {
		"now": now,
		"cutoff": cutoff,
		"user": current_user,
	}, as_dict=True)

	result = []
	for lead in leads:
		try:
			termin_dt = get_datetime(lead.termin_datum)
			hours_until = (termin_dt - now).total_seconds() / 3600.0
			result.append({
				"lead_name": lead.lead_name,
				"lead_display": lead.lead_display or lead.lead_name,
				"termin_datum": str(lead.termin_datum),
				"termin_typ": lead.termin_typ or "",
				"termin_status": lead.termin_status or "",
				"termin_berater": lead.termin_berater or "",
				"hours_until": round(hours_until, 1),
				"is_urgent": hours_until < 2.0,
			})
		except Exception:
			continue

	return result


@frappe.whitelist()
def get_specialist_queue_counts(user=None):
	"""Return specialist lead counts for sidebar specialist queue badges.

	For System Manager: counts all specialist-referred leads.
	For regular users: counts only leads where the user is the assigned specialist.

	Returns a dict with status counts and my_specialist_leads.
	"""
	if not user:
		user = frappe.session.user

	result = {
		"total": 0,
		"offen": 0,
		"in_bearbeitung": 0,
		"qualifiziert": 0,
		"nicht_qualifiziert": 0,
		"my_specialist_leads": 0,
	}

	status_map = {
		"Offen": "offen",
		"In Bearbeitung": "in_bearbeitung",
		"Qualifiziert": "qualifiziert",
		"Nicht qualifiziert": "nicht_qualifiziert",
	}

	# All CRM users see all specialist-referred leads (global overview)
	status_counts = frappe.db.sql("""
		SELECT IFNULL(custom_spezialist_status, 'Offen') as status, COUNT(*) as cnt
		FROM `tabCRM Lead`
		WHERE custom_an_spezialist_weitergeleitet = 1
		GROUP BY IFNULL(custom_spezialist_status, 'Offen')
	""", as_dict=True)

	for row in status_counts:
		key = status_map.get(row.status)
		if key:
			result[key] = row.cnt

	result["total"] = sum(result[k] for k in ["offen", "in_bearbeitung", "qualifiziert", "nicht_qualifiziert"])

	# my_specialist_leads: leads where current user is the assigned specialist
	my_count = frappe.db.sql("""
		SELECT COUNT(*) as cnt
		FROM `tabCRM Lead`
		WHERE custom_an_spezialist_weitergeleitet = 1
		  AND custom_spezialist_user = %(user)s
		  AND IFNULL(custom_spezialist_status, 'Offen') IN ('Offen', 'In Bearbeitung')
	""", {"user": user}, as_dict=True)
	result["my_specialist_leads"] = my_count[0].cnt if my_count else 0

	return result


@frappe.whitelist()
def get_pipeline_phases_api():
	"""Return pipeline phase configuration for frontend use.

	Used by sidebar and other frontend components to dynamically
	render phase labels, colors, and ordering from settings.
	"""
	try:
		from crm.fcrm.doctype.crm_pipeline_settings.crm_pipeline_settings import get_pipeline_phases
		return get_pipeline_phases()
	except Exception:
		return [
			{"phase_code": "10", "phase_value": "10 - Neu ohne Termin", "label": "Neu", "color": "gray", "hex_color": "#6B7280", "sort_order": 10},
			{"phase_code": "20", "phase_value": "20 - Termin gebucht", "label": "Termin", "color": "blue", "hex_color": "#3B82F6", "sort_order": 20},
			{"phase_code": "30", "phase_value": "30 - Reaktivierung", "label": "Reaktiv.", "color": "amber", "hex_color": "#F59E0B", "sort_order": 30},
			{"phase_code": "50", "phase_value": "50 - Closer-Termin", "label": "Closer", "color": "purple", "hex_color": "#8B5CF6", "sort_order": 50},
			{"phase_code": "70", "phase_value": "70 - Follow-up", "label": "Follow-up", "color": "orange", "hex_color": "#F97316", "sort_order": 70},
			{"phase_code": "80", "phase_value": "80 - Abschluss gewonnen", "label": "Gewonnen", "color": "green", "hex_color": "#10B981", "sort_order": 80},
			{"phase_code": "90", "phase_value": "90 - Abschluss verloren", "label": "Verloren", "color": "red", "hex_color": "#EF4444", "sort_order": 90},
		]


# ---------------------------------------------------------------------------
# Fruehwarnsystem - Automatic Push Alerts
# ---------------------------------------------------------------------------

def _get_lead_responsible_user(lead_name, lead_owner=None):
    """Get the primary responsible user for a lead (assigned or owner)."""
    assigned = frappe.db.sql("""
        SELECT allocated_to FROM `tabToDo`
        WHERE reference_type = 'CRM Lead'
          AND reference_name = %(name)s
          AND status != 'Cancelled'
        ORDER BY modified DESC LIMIT 1
    """, {"name": lead_name}, as_dict=True)
    if assigned and assigned[0].allocated_to:
        return assigned[0].allocated_to
    return lead_owner


def _get_system_managers():
    """Return list of active System Manager user emails (excluding Admin/Guest)."""
    managers = frappe.db.sql("""
        SELECT DISTINCT u.name
        FROM `tabUser` u
        INNER JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE hr.role = 'System Manager'
          AND u.enabled = 1
          AND u.name NOT IN ('Administrator', 'Guest')
    """, as_dict=True)
    return [m.name for m in managers]


def _warning_already_sent_today(for_user, document_name, subject_prefix):
    """Check if a warning with the given subject prefix was already sent today."""
    today = frappe.utils.today()
    existing = frappe.db.sql("""
        SELECT name FROM `tabNotification Log`
        WHERE for_user = %(user)s
          AND document_name = %(doc)s
          AND subject LIKE %(prefix)s
          AND creation >= %(today)s
        LIMIT 1
    """, {
        "user": for_user,
        "doc": document_name,
        "prefix": f"{subject_prefix}%",
        "today": today,
    }, as_dict=True)
    return bool(existing)


def _warning_cache_check(cache_key, ttl_seconds=14400):
    """Check if a warning was recently sent using cache. Returns True if already sent.
    TTL default: 4 hours (14400 seconds)."""
    val = frappe.cache.hget("crm_warning_sent", cache_key)
    if val:
        return True
    frappe.cache.hset("crm_warning_sent", cache_key, "1")
    # Set expiry on the hash key
    try:
        frappe.cache.expire("crm_warning_sent", ttl_seconds)
    except Exception:
        pass  # expire not always available on all cache backends
    return False


def _create_crm_notification(from_user, to_user, notification_type, message, reference_doctype=None, reference_name=None):
    """Create a CRM Notification visible in the CRM frontend bell icon.

    This bridges Frappe's Notification Log to the CRM frontend notification panel.
    The CRM frontend only displays CRM Notification docs, not Notification Log entries.
    """
    try:
        doc = frappe.get_doc({
            "doctype": "CRM Notification",
            "from_user": from_user or "Administrator",
            "to_user": to_user,
            "type": notification_type,
            "message": message,
            "notification_text": message,
            "notification_type_doctype": reference_doctype or "",
            "notification_type_doc": reference_name or "",
            "reference_doctype": reference_doctype or "",
            "reference_name": reference_name or "",
            "read": 0,
        })
        doc.insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"CRM Notification Error: {e}")


def _send_warning_notification(for_user, document_name, subject, body):
    """Create a Notification Log entry, CRM Notification, and publish realtime event."""
    notification = frappe.new_doc("Notification Log")
    notification.for_user = for_user
    notification.type = "Alert"
    notification.document_type = "CRM Lead"
    notification.document_name = document_name
    notification.subject = subject
    notification.email_content = body
    notification.insert(ignore_permissions=True)

    # Also create CRM Notification for the CRM frontend bell icon
    _create_crm_notification(
        from_user="Administrator",
        to_user=for_user,
        notification_type="Task",
        message=f"<b>{subject}</b><br>{body}",
        reference_doctype="CRM Lead",
        reference_name=document_name if not document_name.startswith(("noshow-", "fu-stau-", "capacity-")) else None,
    )

    # Push realtime notification for bell icon update
    frappe.publish_realtime(
        event="notification",
        message={"type": "Alert", "subject": subject},
        user=for_user,
    )


@frappe.whitelist()
def process_crm_warnings():
    """Scheduled job (every 30 min): CRM Frühwarnsystem.

    Checks 3 warning conditions and sends Frappe + CRM notifications:
    A. Follow-up überfällig (per lead owner) - once/lead/day
    C. No-Show Warnung (per admin) - once/day/user
    D. Follow-up Stau (per admin) - once/day/user
    """
    from frappe.utils import now_datetime, date_diff, time_diff_in_hours
    import json

    now = now_datetime()
    today = frappe.utils.today()
    warnings_sent = 0
    admin_users = _get_system_managers()

    # ── A. Follow-up überfällig (per Lead Owner) ───────────────────────
    try:
        overdue_leads = frappe.db.sql("""
            SELECT l.name, l.lead_name, l.lead_owner, l.custom_naechster_kontakt,
                   l.custom_liste, l._assign
            FROM `tabCRM Lead` l
            WHERE l.custom_naechster_kontakt < %(today)s
              AND l.custom_naechster_kontakt IS NOT NULL
              AND l.custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
        """, {"today": today}, as_dict=True)

        for lead in overdue_leads:
            notify_user = _get_lead_responsible_user(lead.name, lead.lead_owner)
            if not notify_user:
                continue

            days_overdue = date_diff(today, str(lead.custom_naechster_kontakt))
            subject_prefix = "WARNUNG: Follow-up überfällig"

            if not _warning_already_sent_today(notify_user, lead.name, subject_prefix):
                subject = f"{subject_prefix}: {lead.lead_name or lead.name} ({days_overdue} Tage)"
                body = (
                    f"Lead <b>{lead.lead_name or lead.name}</b> hat ein überfälliges Follow-up "
                    f"seit <b>{days_overdue} Tagen</b> (fällig: {lead.custom_naechster_kontakt}).<br>"
                    f"Aktuelle Phase: {lead.custom_liste}<br>"
                    f"Bitte zeitnah kontaktieren."
                )
                _send_warning_notification(notify_user, lead.name, subject, body)
                warnings_sent += 1
    except Exception as e:
        frappe.log_error(title="CRM Warning Error: Follow-up Overdue", message=str(e))

    # ── C. No-Show Warnung (per Admin/GF) ─────────────────────────────────
    try:
        if admin_users:
            # Calculate No-Show rate per user in last 7 days
            # A lead counts as having an appointment if custom_termin_status is set
            from frappe.utils import add_days
            seven_days_ago = add_days(today, -7)

            appointment_stats = frappe.db.sql("""
                SELECT
                    COALESCE(l.custom_termin_berater, l.lead_owner) AS berater,
                    COUNT(*) AS total_termine,
                    SUM(CASE WHEN l.custom_termin_status = 'No-Show' THEN 1 ELSE 0 END) AS noshow_count
                FROM `tabCRM Lead` l
                WHERE l.custom_termin_status IS NOT NULL
                  AND l.custom_termin_status != ''
                  AND l.modified >= %(since)s
                GROUP BY COALESCE(l.custom_termin_berater, l.lead_owner)
                HAVING total_termine >= 3
            """, {"since": seven_days_ago}, as_dict=True)

            for stat in appointment_stats:
                if not stat.berater or stat.total_termine < 3:
                    continue

                noshow_rate = (stat.noshow_count / stat.total_termine) * 100
                if noshow_rate < 30:
                    continue

                berater_name = frappe.db.get_value("User", stat.berater, "full_name") or stat.berater
                subject_prefix = f"WARNUNG: Hohe No-Show-Rate"
                # Use a pseudo document_name for dedup (user-based, not lead-based)
                dedup_key = f"noshow-{stat.berater}"

                for admin in admin_users:
                    if not _warning_already_sent_today(admin, dedup_key, subject_prefix):
                        subject = f"{subject_prefix}: {berater_name} ({noshow_rate:.0f}%)"
                        body = (
                            f"<b>Achtung:</b> {berater_name} ({stat.berater}) hat eine "
                            f"No-Show-Rate von <b>{noshow_rate:.0f}%</b> in den letzten 7 Tagen.<br>"
                            f"Termine gesamt: {stat.total_termine}<br>"
                            f"Davon No-Show: {stat.noshow_count}"
                        )
                        _send_warning_notification(admin, dedup_key, subject, body)
                        warnings_sent += 1
    except Exception as e:
        frappe.log_error(title="CRM Warning Error: No-Show Rate", message=str(e))

    # ── D. Follow-up Stau (per Admin/GF) ─────────────────────────────────
    try:
        if admin_users:
            # Count overdue follow-ups per user (> 10 triggers warning)
            stau_stats = frappe.db.sql("""
                SELECT
                    COALESCE(l.lead_owner, 'Unbekannt') AS owner,
                    COUNT(*) AS overdue_count
                FROM `tabCRM Lead` l
                WHERE l.custom_naechster_kontakt < %(today)s
                  AND l.custom_naechster_kontakt IS NOT NULL
                  AND l.custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
                GROUP BY COALESCE(l.lead_owner, 'Unbekannt')
                HAVING overdue_count > 10
            """, {"today": today}, as_dict=True)

            for stat in stau_stats:
                if not stat.owner or stat.owner == 'Unbekannt':
                    continue

                owner_name = frappe.db.get_value("User", stat.owner, "full_name") or stat.owner
                subject_prefix = "WARNUNG: Follow-up Stau"
                dedup_key = f"fu-stau-{stat.owner}"

                for admin in admin_users:
                    if not _warning_already_sent_today(admin, dedup_key, subject_prefix):
                        subject = f"{subject_prefix}: {owner_name} ({stat.overdue_count} überfällig)"
                        body = (
                            f"<b>Achtung:</b> {owner_name} ({stat.owner}) hat "
                            f"<b>{stat.overdue_count} überfällige Follow-ups</b>.<br>"
                            f"Das deutet auf einen Engpass oder Arbeitsrueckstand hin.<br>"
                            f"Bitte pruefen und ggf. Leads umverteilen."
                        )
                        _send_warning_notification(admin, dedup_key, subject, body)
                        warnings_sent += 1
    except Exception as e:
        frappe.log_error(title="CRM Warning Error: Follow-up Stau", message=str(e))

    frappe.db.commit()
    return f"CRM Warnings: {warnings_sent} warnings sent"


@frappe.whitelist()
def get_closer_routing_info(lead_name=None, leadtyp=None):
	"""Return routing info for a lead, showing which closer would be assigned.

	Useful for frontend to preview routing before termin_buchen.
	Also returns capacity info for each closer.

	Args:
		lead_name: Optional CRM Lead name
		leadtyp: Optional leadtyp to check (overrides lead's leadtyp)

	Returns:
		dict with: routing_mode, recommended_closer, closer_capacities
	"""
	try:
		from crm.fcrm.doctype.crm_closer_settings.crm_closer_settings import (
			get_closer_settings,
			get_closer_skills,
			get_open_lead_counts,
		)
	except ImportError:
		return {"routing_mode": "Round-Robin", "recommended_closer": None, "closer_capacities": []}

	settings = get_closer_settings()

	# Get leadtyp
	if not leadtyp and lead_name:
		leadtyp = frappe.db.get_value("CRM Lead", lead_name, "custom_leadtyp")

	# Get open lead counts
	open_counts = get_open_lead_counts()
	max_leads = settings["max_open_leads_per_closer"]

	# Get matching skills for this leadtyp
	skills = get_closer_skills()
	matching_skills = [s for s in skills if s["leadtyp"] == leadtyp] if leadtyp else []

	# Build capacity info
	closer_capacities = []
	for skill in matching_skills:
		user = skill["user"]
		count = open_counts.get(user, 0)
		at_capacity = max_leads > 0 and count >= max_leads
		closer_capacities.append({
			"user": user,
			"full_name": frappe.db.get_value("User", user, "full_name") or user,
			"skill_level": skill["skill_level"],
			"open_leads": count,
			"max_leads": max_leads,
			"at_capacity": at_capacity,
		})

	# Sort: highest skill first, then fewest leads
	closer_capacities.sort(key=lambda x: (
		-{"Experte": 3, "Fortgeschritten": 2, "Basis": 1}.get(x["skill_level"], 0),
		x["open_leads"]
	))

	recommended = None
	for c in closer_capacities:
		if not c["at_capacity"]:
			recommended = c["user"]
			break

	return {
		"routing_mode": settings["routing_mode"],
		"leadtyp": leadtyp,
		"recommended_closer": recommended,
		"max_open_leads": max_leads,
		"fallback_to_roundrobin": settings["fallback_to_roundrobin"],
		"closer_capacities": closer_capacities,
	}

# ── Event -> CRM Lead Sync ──────────────────────────────────────────────
def sync_event_to_lead(doc, method):
	"""Hook called when an Event is created or updated.
	If the Event is linked to a CRM Lead, enqueue async lead update.
	MUST NOT block the Event save transaction.
	"""
	if doc.reference_doctype != "CRM Lead" or not doc.reference_docname:
		return

	# Skip if Event was created from _create_appointment_from_action
	# to prevent duplicate CRM Appointment creation and redundant lead updates
	if getattr(frappe.flags, "skip_event_to_lead_sync", False):
		return
	
	# Run the actual sync asynchronously so it doesn't block Event creation
	frappe.enqueue(
		_sync_event_to_lead_async,
		queue="short",
		lead_name=doc.reference_docname,
		event_subject=doc.subject or "",
		event_starts_on=str(doc.starts_on) if doc.starts_on else "",
		event_status=doc.status or "Open",
		event_owner=doc.owner or "",
		event_participants=[p.email for p in (doc.event_participants or []) if p.email],
		now=True,  # execute immediately if worker available
	)


def _sync_event_to_lead_async(lead_name, event_subject, event_starts_on, event_status, event_owner, event_participants=None):
	"""Async worker: sync Event data to CRM Lead termin fields + phase trigger."""
	try:
		lead = frappe.get_doc("CRM Lead", lead_name)
		
		# Cancelled event -> mark termin as cancelled
		if event_status == "Cancelled":
			if lead.custom_termin_status in ("Geplant", "Bestätigt"):
				lead.custom_termin_status = "Abgesagt"
				lead.add_comment("Info", "Veranstaltung abgesagt: {0}".format(event_subject))
				lead.save(ignore_permissions=True)
				frappe.db.commit()
			return
		
		# Closed event -> mark termin as completed
		if event_status == "Closed":
			if lead.custom_termin_status in ("Geplant", "Bestätigt"):
				lead.custom_termin_status = "Durchgeführt"
				lead.add_comment("Info", "Veranstaltung durchgeführt: {0}".format(event_subject))
				lead.save(ignore_permissions=True)
				frappe.db.commit()
			return
		
		# Open event -> sync termin fields
		if not event_starts_on:
			return
		
		event_date = frappe.utils.get_datetime(event_starts_on)
		
		# Determine termin typ from subject
		# Valid options: Ersttermin, Closer-Termin, Follow-up Termin, Reaktivierung, Spezialist
		termin_typ = "Ersttermin"
		subject_lower = event_subject.lower()
		if "closer" in subject_lower or "abschluss" in subject_lower:
			termin_typ = "Closer-Termin"
		elif "follow" in subject_lower or "nachfass" in subject_lower:
			termin_typ = "Follow-up Termin"
		elif "reaktiv" in subject_lower:
			termin_typ = "Reaktivierung"
		elif "spezial" in subject_lower or "veredelung" in subject_lower:
			termin_typ = "Spezialist"
		
		# Determine berater from participants or event owner
		# Only use valid Frappe Users as berater (skip lead/contact emails)
		termin_berater = event_owner
		if event_participants:
			for email in event_participants:
				if email != event_owner and frappe.db.exists("User", email):
					termin_berater = email
					break
		
		# Validate berater is a valid User
		if not frappe.db.exists("User", termin_berater):
			termin_berater = event_owner if frappe.db.exists("User", event_owner) else "Administrator"
		
		# Update lead termin fields
		lead.custom_termin_datum = event_date
		lead.custom_termin_typ = termin_typ
		lead.custom_termin_status = "Geplant"
		# Store event time on lead for list display
		if hasattr(event_date, 'strftime') and event_date.hour != 0:
			lead.custom_termin_zeit_von = event_date.strftime("%H:%M:%S")
		else:
			lead.custom_termin_zeit_von = None
		lead.custom_termin_berater = termin_berater
		lead.custom_letzter_kontakt = frappe.utils.now_datetime()
		lead.custom_letzte_kontaktart = "Termin"
		
		# Status update
		if lead.status in ("Nicht kontaktiert", "Kontaktiert", "Kontaktiert aber nicht erreicht"):
			lead.status = "Termin vereinbart"
		
		lead.add_comment("Info", "Termin via Veranstaltung: {0} am {1} (Berater: {2})".format(
			event_subject, event_date.strftime("%d.%m.%Y %H:%M"), termin_berater))
		
		# Save triggers validate() -> apply_phase_triggers() for automatic phase change
		lead.save(ignore_permissions=True)
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(title="CRM Event Sync", message=str(e)[:130])


# --- Event-Termin Integration ---

@frappe.whitelist()
def on_event_created_for_lead(lead_name, event_date=None, event_time=None, event_name=None):
	"""Called after an Event is created/linked to a CRM Lead.
	Triggers the same list-change logic as termin_buchen.
	Also creates a CRM Appointment record for tracking."""
	lead = frappe.get_doc("CRM Lead", lead_name)

	today = str(frappe.utils.today())

	termin_datum = event_date or today
	lead.custom_termin_datum = termin_datum
	lead.custom_termin_status = "Geplant"
	# Store event time on lead for list display
	lead.custom_termin_zeit_von = event_time or None

	# Determine termin type based on current phase
	current_phase = lead.custom_liste or ""
	if "50" in current_phase or "Closer" in current_phase:
		termin_typ = "Closer-Termin"
	else:
		termin_typ = "Ersttermin"

	lead.custom_termin_typ = termin_typ
	lead.custom_termin_berater = frappe.session.user

	if event_name:
		lead.custom_termin_notiz = "Event: {0}".format(event_name)

	comment_parts = []
	comment_parts.append("Termin erstellt via Veranstaltung: {0} ({1})".format(
		lead.custom_termin_datum, termin_typ))

	lead.add_comment("Info", "<br>".join(comment_parts))
	lead.save(ignore_permissions=True)
	frappe.db.commit()

	# --- Create CRM Appointment record ---
	try:
		# Try to find the Event document linked to this lead (most recent)
		event_doc_name = None
		try:
			event_doc_name = frappe.db.get_value(
				"Event",
				filters={
					"event_type": ["in", ["Public", "Private"]],
				},
				fieldname="name",
				order_by="creation desc",
			)
			# More precise: look for Event Participants linking to this lead
			linked_event = frappe.db.sql("""
				SELECT ep.parent
				FROM `tabEvent Participants` ep
				WHERE ep.reference_doctype = 'CRM Lead'
				  AND ep.reference_docname = %(lead)s
				ORDER BY ep.creation DESC
				LIMIT 1
			""", {"lead": lead_name}, as_dict=True)
			if linked_event:
				event_doc_name = linked_event[0].parent
		except Exception:
			pass

		appointment = frappe.new_doc("CRM Appointment")
		appointment.lead = lead_name
		appointment.lead_name = lead.lead_name or ""
		appointment.termin_datum = termin_datum
		if event_time:
			appointment.termin_zeit_von = event_time
			# Set end time = start + 1 hour to satisfy validation
			try:
				from datetime import datetime, timedelta
				from frappe.utils import get_time
				t_von = get_time(event_time)
				dt_von = datetime.combine(datetime.today(), t_von)
				dt_bis = dt_von + timedelta(hours=1)
				appointment.termin_zeit_bis = str(dt_bis.time())
			except Exception:
				pass
		else:
			# No time provided: explicitly clear to prevent Frappe auto-fill
			appointment.termin_zeit_von = ""
			appointment.termin_zeit_bis = ""
		appointment.typ = termin_typ
		appointment.status = "Geplant"
		appointment.berater = frappe.session.user
		appointment.quelle = "Event"
		if event_doc_name:
			appointment.event_link = event_doc_name
		if event_name:
			appointment.notiz = event_name

		# Skip sync back to lead since we already set the lead fields above
		appointment.flags.skip_lead_sync = True
		appointment.insert(ignore_permissions=True)
		frappe.db.commit()

	except Exception as e:
		frappe.log_error(
			title="CRM Appointment creation from Event failed",
			message="Lead: {0}, Error: {1}".format(lead_name, str(e)[:200])
		)

	return {
		"success": True,
		"new_phase": lead.custom_liste,
		"message": "Listenwechsel durchgeführt"
	}


@frappe.whitelist()
def get_leads_for_contact(email):
	"""Get all open CRM Leads for a given contact email address."""
	if not email:
		return []

	leads = frappe.get_all("CRM Lead",
		filters={
			"email": email,
			"custom_liste": ["not in", ["80 - Abschluss gewonnen", "90 - Abschluss verloren"]]
		},
		fields=["name", "lead_name", "first_name", "last_name", "custom_liste",
			"custom_leadtyp", "custom_produktlinie", "email", "organization",
			"mobile_no", "creation"],
		order_by="creation desc"
	)
	return leads

def rate_setter_quality(lead_name, bewertung, kommentar=None):
    """Rate the setter quality for a lead after closer appointment.

    Called from the frontend when a closer evaluates the setter work
    after completing an appointment (Termin durchgeführt).

    Args:
        lead_name: CRM Lead name
        bewertung: Rating string like "4 - Gut"
        kommentar: Optional comment text

    Returns:
        dict with success status and rating
    """
    if not lead_name or not bewertung:
        frappe.throw("lead_name und bewertung sind Pflichtfelder")

    valid_ratings = [
        "1 - Schlecht", "2 - Mangelhaft", "3 - Akzeptabel",
        "4 - Gut", "5 - Sehr gut"
    ]
    if bewertung not in valid_ratings:
        frappe.throw(f"Ungueltige Bewertung: {bewertung}. Erlaubt: {valid_ratings}")

    lead = frappe.get_doc("CRM Lead", lead_name)
    lead.custom_setter_bewertung = bewertung
    lead.custom_setter_bewertung_kommentar = kommentar or ""
    lead.custom_setter_bewertung_user = frappe.session.user
    lead.custom_setter_bewertung_datum = frappe.utils.now()
    lead.save(ignore_permissions=True)
    frappe.db.commit()

    # Add audit comment
    user_fullname = frappe.utils.get_fullname(frappe.session.user)
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "CRM Lead",
        "reference_name": lead_name,
        "content": f"Setter-Bewertung durch {user_fullname}: {bewertung}"
                   + (f" - {kommentar}" if kommentar else "")
    }).insert(ignore_permissions=True)
    frappe.db.commit()

    return {"success": True, "bewertung": bewertung}


# ── No-Show Notification Helper ──────────────────────────────────────────
@frappe.whitelist()
def update_cross_sell_with_reason(lead_name, prio, status, grund=None):
    """Update cross-sell status with optional reason for 'bewusst nicht angesprochen'.

    Args:
        lead_name: CRM Lead name
        prio: Priority level (1, 2, or 3)
        status: New status value
        grund: Optional reason when status is 'Bewusst nicht angesprochen'
    """
    prio = int(prio)
    if prio not in (1, 2, 3):
        frappe.throw("Ungueltige Prioritaet: muss 1, 2 oder 3 sein")

    valid_statuses = ["", "Nicht angesprochen", "Angesprochen", "Bewusst nicht angesprochen", "Weiterleitung erstellt"]
    if status not in valid_statuses:
        frappe.throw(f"Ungueltiger Status: {status}")

    if not frappe.db.exists("CRM Lead", lead_name):
        frappe.throw("Lead nicht gefunden")

    lead = frappe.get_doc("CRM Lead", lead_name)

    status_field = f"custom_cross_sell_prio{prio}_status"
    grund_field = f"custom_cross_sell_prio{prio}_nicht_grund"

    lead.set(status_field, status)

    if status == "Bewusst nicht angesprochen" and grund:
        lead.set(grund_field, grund)
    elif status != "Bewusst nicht angesprochen":
        # Clear reason if status changed away from "bewusst nicht angesprochen"
        lead.set(grund_field, "")

    lead.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "prio": prio,
        "status": status,
        "grund": grund if status == "Bewusst nicht angesprochen" else None,
    }


# ──────────────────────────────────────────────────────────────────────
# Firma-Berater Zuordnung API
# ──────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_firma_berater(firma_name=None, firma_url=None, leadtyp=None):
    """Look up the assigned advisor for a company.

    Args:
        firma_name: Exact company name to match
        firma_url: URL pattern to search for (partial match)
        leadtyp: Lead type to filter by (matches exact type or 'Beides')

    Returns:
        dict with berater and firma_name, or None if no match found
    """
    filters = {"aktiv": 1}
    if firma_name:
        filters["firma_name"] = firma_name
    if firma_url:
        filters["firma_url"] = ["like", "%{0}%".format(firma_url)]
    if leadtyp:
        filters["leadtyp"] = ["in", [leadtyp, "Beides"]]

    mapping = frappe.get_all(
        "CRM Firma Berater",
        filters=filters,
        fields=["berater", "firma_name", "firma_url", "leadtyp"],
        limit=1,
    )
    if mapping:
        return mapping[0]
    return None


@frappe.whitelist()
def get_all_firma_berater():
    """Return all active Firma-Berater mappings for frontend display."""
    return frappe.get_all(
        "CRM Firma Berater",
        filters={"aktiv": 1},
        fields=["name", "firma_name", "firma_url", "berater", "leadtyp"],
        order_by="firma_name asc",
    )


def _pick_available_berater(termin_datum, zeit_von, zeit_bis, lead_name=None, leadtyp=None, specific_berater=None):
    """Re-check availability for a specific slot and pick the best available berater.

    Used when booking from a Terminvorschlag to prevent race conditions.
    Returns: user email of available berater, or None if none available.
    """
    from datetime import timedelta as td, datetime

    def time_to_min(t):
        if not t:
            return 0
        if isinstance(t, str) and ":" in t:
            parts = t.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        if isinstance(t, td):
            return int(t.total_seconds() / 60)
        return 0

    slot_start = time_to_min(zeit_von)
    slot_end = time_to_min(zeit_bis)
    if slot_end <= slot_start:
        slot_end = slot_start + 60

    vertriebler_data = frappe.get_all(
        "User",
        filters={
            "user_type": "System User",
            "name": ["not in", ["Administrator", "Guest", "landing-page@api.local"]],
            "role_profile_name": "Vertriebler",
            "enabled": 1,
        },
        fields=["name"],
    )
    active_users = [u.name for u in vertriebler_data]

    if not active_users:
        return None

    # Check appointments on that date
    appointments = frappe.get_all(
        "CRM Appointment",
        filters={
            "termin_datum": str(termin_datum),
            "status": ["in", ["Geplant", "Bestätigt"]],
        },
        fields=["berater", "termin_zeit_von", "termin_zeit_bis"],
    )

    busy_users = set()
    for apt in appointments:
        berater = apt.get("berater")
        if berater not in active_users:
            continue
        apt_start = time_to_min(apt.get("termin_zeit_von"))
        apt_end = time_to_min(apt.get("termin_zeit_bis"))
        if apt_end <= apt_start:
            apt_end = apt_start + 60
        if slot_start < apt_end and slot_end > apt_start:
            busy_users.add(berater)

    # Check events on that date
    events = frappe.get_all(
        "Event",
        filters=[
            ["starts_on", ">=", str(termin_datum) + " 00:00:00"],
            ["starts_on", "<=", str(termin_datum) + " 23:59:59"],
            ["status", "not in", ["Cancelled"]],
        ],
        fields=["owner", "starts_on", "ends_on"],
    )

    for ev in events:
        owner = ev.get("owner")
        if owner not in active_users:
            continue
        starts_on = ev.get("starts_on")
        ends_on = ev.get("ends_on")
        if isinstance(starts_on, str):
            starts_on = datetime.strptime(starts_on, "%Y-%m-%d %H:%M:%S")
        if isinstance(starts_on, datetime):
            ev_start = starts_on.hour * 60 + starts_on.minute
        else:
            continue
        if ends_on:
            if isinstance(ends_on, str):
                ends_on = datetime.strptime(ends_on, "%Y-%m-%d %H:%M:%S")
            if isinstance(ends_on, datetime):
                ev_end = ends_on.hour * 60 + ends_on.minute
            else:
                ev_end = ev_start + 60
        else:
            ev_end = ev_start + 60
        if slot_start < ev_end and slot_end > ev_start:
            busy_users.add(owner)

    free_users = [u for u in active_users if u not in busy_users]

    # If a specific berater was requested, check only that user
    if specific_berater:
        if specific_berater in free_users:
            return specific_berater
        return None

    if not free_users:
        return None

    # Pick user with fewest open leads
    best_user = None
    min_leads = 99999
    for user in free_users:
        count = frappe.db.count("CRM Lead", filters={
            "lead_owner": user,
            "custom_liste": ["not in", ["80 - Abschluss gewonnen", "90 - Abschluss verloren"]],
        })
        if count < min_leads:
            min_leads = count
            best_user = user
    return best_user


@frappe.whitelist()
def get_termin_vorschlaege(duration_minutes=60, lead_name=None, termin_typ="Ersttermin", berater=None):
    """Return 5-10 anonymous time slot suggestions based on real user availability.

    Checks CRM Appointments and Events for all active CRM Vertrieb users
    over the next 14 business days. Returns slots where at least 1 user is free.
    """
    from datetime import datetime, timedelta, date, time as dt_time
    import json

    duration_minutes = int(duration_minutes or 60)
    duration_minutes = max(15, min(240, duration_minutes))
    duration = timedelta(minutes=duration_minutes)

    # Cache key
    cache_key = "termin_vorschlaege_{0}_{1}".format(duration_minutes, berater or "all")
    cached = frappe.cache().get_value(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    # 1. Get all active Vertriebler (via role_profile, not role - to get only real sales staff)
    vertriebler_data = frappe.get_all(
        "User",
        filters={
            "user_type": "System User",
            "name": ["not in", ["Administrator", "Guest", "landing-page@api.local"]],
            "role_profile_name": "Vertriebler",
            "enabled": 1,
        },
        fields=["name"],
    )
    active_users = [u.name for u in vertriebler_data]

    # If specific berater requested, validate and filter
    berater_full_name = None
    if berater:
        if berater not in active_users:
            return []
        berater_full_name = frappe.db.get_value("User", berater, "full_name") or berater
        active_users = [berater]

    if not active_users:
        return []

    # 2. Next 14 business days (Mon-Fri), starting tomorrow
    today = date.today()
    business_days = []
    check_date = today + timedelta(days=1)
    while len(business_days) < 14:
        if check_date.weekday() < 5:
            business_days.append(check_date)
        check_date += timedelta(days=1)

    first_day = business_days[0]
    last_day = business_days[-1]

    # 3. Load ALL appointments in date range (single query)
    appointments = frappe.get_all(
        "CRM Appointment",
        filters={
            "termin_datum": ["between", [str(first_day), str(last_day)]],
            "status": ["in", ["Geplant", "Bestätigt"]],
        },
        fields=["berater", "termin_datum", "termin_zeit_von", "termin_zeit_bis"],
    )

    # Build per-user busy intervals
    user_busy = {u: [] for u in active_users}
    for apt in appointments:
        berater = apt.get("berater")
        if berater not in user_busy:
            continue
        apt_date = apt.get("termin_datum")
        if isinstance(apt_date, datetime):
            apt_date = apt_date.date()
        zeit_von = apt.get("termin_zeit_von")
        zeit_bis = apt.get("termin_zeit_bis")

        if zeit_von and zeit_bis:
            if isinstance(zeit_von, timedelta):
                start_min = int(zeit_von.total_seconds() / 60)
            else:
                start_min = 9 * 60
            if isinstance(zeit_bis, timedelta):
                end_min = int(zeit_bis.total_seconds() / 60)
            else:
                end_min = start_min + 60
        else:
            start_min = 9 * 60
            end_min = 10 * 60

        user_busy[berater].append((apt_date, start_min, end_min))

    # 4. Load Events in date range
    events_data = frappe.get_all(
        "Event",
        filters=[
            ["starts_on", ">=", str(first_day) + " 00:00:00"],
            ["starts_on", "<=", str(last_day) + " 23:59:59"],
        ],
        fields=["owner", "starts_on", "ends_on"],
    )

    for ev in events_data:
        owner = ev.get("owner")
        if owner not in user_busy:
            continue
        starts_on = ev.get("starts_on")
        ends_on = ev.get("ends_on")
        if not starts_on:
            continue

        if isinstance(starts_on, str):
            starts_on = datetime.strptime(starts_on, "%Y-%m-%d %H:%M:%S")

        if isinstance(starts_on, datetime):
            ev_date = starts_on.date()
            start_min = starts_on.hour * 60 + starts_on.minute
        else:
            continue

        if ends_on:
            if isinstance(ends_on, str):
                ends_on = datetime.strptime(ends_on, "%Y-%m-%d %H:%M:%S")
            if isinstance(ends_on, datetime):
                end_min = ends_on.hour * 60 + ends_on.minute
            else:
                end_min = start_min + 60
        else:
            end_min = start_min + 60

        user_busy[owner].append((ev_date, start_min, end_min))

    # 5. Generate slots: 08:00-20:00
    WEEKDAY_NAMES = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    WORK_START = 8 * 60
    WORK_END = 20 * 60

    all_slots = []
    for day in business_days:
        slot_start = WORK_START
        while slot_start + duration_minutes <= WORK_END:
            slot_end = slot_start + duration_minutes
            available_count = 0
            for user in active_users:
                busy_intervals = user_busy.get(user, [])
                is_busy = False
                for (busy_date, busy_start, busy_end) in busy_intervals:
                    if busy_date == day:
                        if slot_start < busy_end and slot_end > busy_start:
                            is_busy = True
                            break
                if not is_busy:
                    available_count += 1

            if available_count > 0:
                # Score for ranking
                days_away = (day - today).days
                date_score = max(0, 15 - days_away) * 10
                if 9 * 60 <= slot_start < 12 * 60:
                    time_score = 30
                elif 14 * 60 <= slot_start < 17 * 60:
                    time_score = 25
                elif 8 * 60 <= slot_start < 9 * 60:
                    time_score = 15
                elif 17 * 60 <= slot_start < 19 * 60:
                    time_score = 10
                else:
                    time_score = 5
                avail_score = min(available_count, 22) * 3
                score = date_score + time_score + avail_score

                slot_data = {
                    "date": str(day),
                    "weekday": WEEKDAY_NAMES[day.weekday()],
                    "start": "{0:02d}:{1:02d}".format(slot_start // 60, slot_start % 60),
                    "end": "{0:02d}:{1:02d}".format(slot_end // 60, slot_end % 60),
                    "available_count": available_count,
                    "_score": score,
                }
                if berater and berater_full_name:
                    slot_data["berater"] = berater
                    slot_data["berater_name"] = berater_full_name
                all_slots.append(slot_data)
            slot_start += duration_minutes

    # 6. Sort by score and return top 10
    all_slots.sort(key=lambda s: s["_score"], reverse=True)
    result = []
    for s in all_slots[:10]:
        del s["_score"]
        result.append(s)

    # Re-sort by date/time for display
    result.sort(key=lambda s: (s["date"], s["start"]))

    # Cache for 5 minutes
    try:
        frappe.cache().set_value(cache_key, json.dumps(result), expires_in_sec=300)
    except Exception:
        pass

    return result




@frappe.whitelist()
def get_angebot_email_vorlage(lead_name):
    """Return the Angebot email template with placeholders resolved."""
    import re as _re

    lead = frappe.get_doc("CRM Lead", lead_name)

    try:
        settings = frappe.get_single("CRM Angebot Vorlage")
        betreff = settings.email_betreff or "Ihr persönliches Angebot"
        inhalt = settings.email_inhalt or ""
    except Exception:
        betreff = "Ihr persönliches Angebot – {lead_name}"
        inhalt = "<p>Sehr geehrte/r {lead_name},</p><p>anbei finden Sie Ihr persönliches Angebot.</p><p>Mit freundlichen Grüßen<br>{mitarbeiter_name}</p>"

    mitarbeiter = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user

    lead_display = lead.lead_name or ((lead.first_name or "") + " " + (lead.last_name or "")).strip()

    replacements = {
        "{lead_name}": lead_display,
        "{mitarbeiter_name}": mitarbeiter,
        "{leadtyp}": lead.custom_leadtyp or "",
        "{firma}": lead.organization or "",
    }

    for key, val in replacements.items():
        betreff = betreff.replace(key, val.strip())
        inhalt = inhalt.replace(key, val.strip())

    # Strip HTML tags for plain text version
    inhalt_plain = _re.sub(r'<br\s*/?>', '\n', inhalt)
    inhalt_plain = _re.sub(r'</p>\s*<p>', '\n\n', inhalt_plain)
    inhalt_plain = _re.sub(r'<[^>]+>', '', inhalt_plain)
    inhalt_plain = inhalt_plain.strip()

    return {
        "betreff": betreff.strip(),
        "inhalt_html": inhalt,
        "inhalt_plain": inhalt_plain,
        "empfaenger": lead.email or "",
    }

@frappe.whitelist()
def get_lead_preview(lead_name):
    """Return key fields for a lead hover popup. Fast single-read."""
    import json as _json

    if not lead_name:
        return {}

    cache_key = "lead_preview_{0}".format(lead_name)
    cached = frappe.cache().get_value(cache_key)
    if cached:
        try:
            return _json.loads(cached)
        except Exception:
            pass

    fields = [
        "name", "first_name", "last_name", "lead_name", "email", "mobile_no", "phone",
        "status", "custom_liste", "custom_leadtyp", "custom_leadquelle",
        "custom_lead_potenzial", "lead_owner", "custom_naechster_kontakt",
        "custom_letzte_kontaktart", "custom_letzter_kontakt",
        "custom_tierart", "custom_tiername", "organization",
        "custom_zustaendige_rolle", "custom_kontaktversuche",
        "custom_erreichbarkeit", "custom_followup_grund",
        "custom_termin_datum", "custom_termin_zeit_von", "custom_termin_status",
        "custom_termin_typ", "custom_termin_berater",
        "custom_cross_sell_prio1_produkt", "custom_cross_sell_prio1_status",
        "custom_cross_sell_prio2_produkt", "custom_cross_sell_prio2_status",
        "custom_cross_sell_prio3_produkt", "custom_cross_sell_prio3_status",
    ]
    lead_data = frappe.db.get_value("CRM Lead", lead_name, fields, as_dict=True)
    if not lead_data:
        return {}

    owner_name = ""
    if lead_data.get("lead_owner"):
        owner_name = frappe.db.get_value("User", lead_data["lead_owner"], "full_name") or lead_data["lead_owner"]

    # Resolve Berater full name from lead field
    termin_berater_name = ""
    berater_email = lead_data.get("custom_termin_berater") or ""
    if berater_email:
        termin_berater_name = frappe.db.get_value("User", berater_email, "full_name") or berater_email

    phase_label = lead_data.get("custom_liste") or ""

    result = {
        "name": lead_data.get("name"),
        "lead_name": lead_data.get("lead_name") or "{0} {1}".format(
            lead_data.get("first_name") or "", lead_data.get("last_name") or ""
        ).strip(),
        "email": lead_data.get("email") or "",
        "mobile_no": lead_data.get("mobile_no") or "",
        "phone": lead_data.get("phone") or "",
        "status": lead_data.get("status") or "",
        "custom_liste": phase_label,
        "custom_leadtyp": lead_data.get("custom_leadtyp") or "",
        "custom_leadquelle": lead_data.get("custom_leadquelle") or "",
        "lead_potenzial": lead_data.get("custom_lead_potenzial") or "",
        "owner_name": owner_name,
        "lead_owner": lead_data.get("lead_owner") or "",
        "naechster_kontakt": str(lead_data.get("custom_naechster_kontakt") or ""),
        "letzte_kontaktart": lead_data.get("custom_letzte_kontaktart") or "",
        "letzter_kontakt": str(lead_data.get("custom_letzter_kontakt") or ""),
        "tierart": lead_data.get("custom_tierart") or "",
        "tiername": lead_data.get("custom_tiername") or "",
        "organization": lead_data.get("organization") or "",
        "zustaendige_rolle": lead_data.get("custom_zustaendige_rolle") or "",
        "kontaktversuche": lead_data.get("custom_kontaktversuche") or 0,
        "erreichbarkeit": lead_data.get("custom_erreichbarkeit") or "",
        "followup_grund": lead_data.get("custom_followup_grund") or "",
        "termin_datum": str(lead_data.get("custom_termin_datum") or ""),
        "termin_zeit_von": str(lead_data.get("custom_termin_zeit_von") or ""),
        "termin_typ": lead_data.get("custom_termin_typ") or "",
        "termin_status": lead_data.get("custom_termin_status") or "",
        "termin_berater": termin_berater_name,
        "cross_sell_prio1_produkt": lead_data.get("custom_cross_sell_prio1_produkt") or "",
        "cross_sell_prio1_status": lead_data.get("custom_cross_sell_prio1_status") or "",
        "cross_sell_prio2_produkt": lead_data.get("custom_cross_sell_prio2_produkt") or "",
        "cross_sell_prio2_status": lead_data.get("custom_cross_sell_prio2_status") or "",
        "cross_sell_prio3_produkt": lead_data.get("custom_cross_sell_prio3_produkt") or "",
        "cross_sell_prio3_status": lead_data.get("custom_cross_sell_prio3_status") or "",
    }

    try:
        frappe.cache().set_value(cache_key, _json.dumps(result, default=str), expires_in_sec=30)
    except Exception:
        pass

    return result


@frappe.whitelist(allow_guest=True)
def create_lead_from_webhook(**kwargs):
    """Webhook-Endpoint fuer Landing Pages.
    Empfaengt beliebiges JSON, mappt Felder dynamisch, erstellt Lead in Liste 10.

    Auth: X-API-Key Header oder Authorization: token key:secret
    """
    import json as _json

    # --- Authentication ---
    api_key_header = frappe.request.headers.get("X-API-Key", "")
    auth_header = frappe.request.headers.get("Authorization", "")

    authenticated = False

    # Method 1: X-API-Key: key:secret
    if api_key_header and ":" in api_key_header:
        key, secret = api_key_header.split(":", 1)
        authenticated = _validate_api_key(key, secret)

    # Method 2: Authorization: token key:secret
    if not authenticated and auth_header.startswith("token "):
        token = auth_header[6:]
        if ":" in token:
            key, secret = token.split(":", 1)
            authenticated = _validate_api_key(key, secret)

    # Method 3: Logged-in user with CRM Vertrieb role
    if not authenticated and frappe.session.user != "Guest":
        roles = frappe.get_roles(frappe.session.user)
        if "CRM Vertrieb" in roles or "System Manager" in roles:
            authenticated = True

    if not authenticated:
        frappe.throw("Nicht autorisiert. API-Key fehlt oder ungueltig.", frappe.AuthenticationError)

    # --- Parse request data ---
    data = {}
    if frappe.request.data:
        try:
            data = _json.loads(frappe.request.data)
        except Exception:
            pass
    # Also accept form-data / query params
    data.update(kwargs)

    if not data:
        frappe.throw("Keine Daten empfangen.")

    # Log incoming payload for debugging (always, so failed requests can be replayed)
    try:
        frappe.get_doc({
            "doctype": "Error Log",
            "method": "create_lead_from_webhook:payload",
            "error": _json.dumps(data, indent=2, ensure_ascii=False, default=str)[:10000]
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        pass

    # --- Feld-Mapping: Masterplanung S.23-43 + allgemeine Felder ---
    FIELD_MAP = {
        # === STANDARD (alle Leadtypen) ===
        "vorname": "first_name",
        "first_name": "first_name",
        "anrede": "salutation",
        "salutation": "salutation",
        "nachname": "last_name",
        "last_name": "last_name",
        "name": "_full_name",
        "full_name": "_full_name",
        "telefon": "mobile_no",
        "phone": "mobile_no",
        "mobile": "mobile_no",
        "mobile_no": "mobile_no",
        "handy": "mobile_no",
        "nummer": "mobile_no",
        "telefonnummer": "mobile_no",
        "mobilnummer": "mobile_no",
        "tel": "mobile_no",
        "email": "email",
        "e-mail": "email",
        "email_address": "email",
        "mail": "email",
        "firma": "organization",
        "company": "organization",
        "organization": "organization",
        "unternehmen": "organization",
        # Erreichbarkeit (alle LPs haben das)
        "erreichbarkeit": "custom_erreichbarkeit",
        "am besten telefonisch erreichbar": "custom_erreichbarkeit",
        "erreichbar": "custom_erreichbarkeit",
        "custom erreichbarkeit": "custom_erreichbarkeit",
        "custom_erreichbarkeit": "custom_erreichbarkeit",
        "custom erreichbartkeit": "custom_erreichbarkeit",

        # === LEADTYP / PRODUKT ===
        "produkt": "custom_leadtyp",
        "product": "custom_leadtyp",
        "leadtyp": "custom_leadtyp",
        "lead_type": "custom_leadtyp",
        "typ": "custom_leadtyp",
        "bereich": "custom_leadtyp",
        "versicherung": "custom_leadtyp",
        "produktlinie": "custom_produktlinie",
        "product_line": "custom_produktlinie",

        # === QUELLE / TRACKING ===
        "quelle": "custom_leadquelle",
        "source": "custom_leadquelle",
        "lead_source": "custom_leadquelle",
        "herkunft": "custom_herkunft_typ",
        "herkunft_typ": "custom_herkunft_typ",
        "utm_source": "custom_utm_source",
        "utm_medium": "custom_utm_medium",
        "utm_campaign": "custom_utm_campaign",
        "kampagne": "custom_kampagne",
        "url": "custom_quell_url",
        "quell_url": "custom_quell_url",
        "page_url": "custom_quell_url",
        "landing_page": "custom_quell_url",
        "geraet": "custom_geraet",
        "device": "custom_geraet",
        "agent": "custom_geraet",

        # === DSGVO ===
        "dsgvo": "custom_dsgvo_zugestimmt",
        "dsgvo_zugestimmt": "custom_dsgvo_zugestimmt",
        "zugestimmt": "custom_dsgvo_zugestimmt",
        "consent": "custom_dsgvo_zugestimmt",
        "privacy": "custom_dsgvo_zugestimmt",
        "datenschutzerklaerung": "custom_dsgvo_zugestimmt",
        "datenschutzerklärung": "custom_dsgvo_zugestimmt",
        "einwilligungserklaerung": "custom_dsgvo_zugestimmt",
        "einwilligungserklärung": "custom_dsgvo_zugestimmt",
        "dsgvo_whatsapp": "custom_dsgvo_whatsapp",
        "dsgvo_sms": "custom_dsgvo_sms",
        "dsgvo_email": "custom_dsgvo_email",
        "dsgvo_telefon": "custom_dsgvo_telefon",

        # === TIER (Pferd/Hund/Katze) – Masterplanung S.23-26 ===
        "tierart": "custom_tierart",
        "name des pferdes": "custom_tiername",
        "name des hundes": "custom_tiername",
        "name des hunds": "custom_tiername",
        "name der katze": "custom_tiername",
        "tiername": "custom_tiername",
        "pet_name": "custom_tiername",
        "alter des pferdes": "custom_tieralter",
        "alter des hundes": "custom_tieralter",
        "alter des hunds": "custom_tieralter",
        "alter der katze": "custom_tieralter",
        "tieralter": "custom_tieralter",
        "pet_age": "custom_tieralter",
        "hunderasse": "custom_tierrasse",
        "katzenrasse": "custom_tierrasse",
        "tierrasse": "custom_tierrasse",
        "rasse": "custom_tierrasse",
        "breed": "custom_tierrasse",
        "gechipt": "custom_chip_nummer",
        "chip_nummer": "custom_chip_nummer",
        "chipnummer": "custom_chip_nummer",
        "vorerkrankungen": "custom_vorerkrankungen",
        "aktuell_versichert": "custom_aktuell_versichert",
        "aktuelle_versicherung": "custom_aktuelle_versicherung",

        # === OLDTIMER – Masterplanung S.27-28 ===
        "hersteller": "custom_ot_hersteller",
        "herrsteller": "custom_ot_hersteller",
        "modell": "custom_ot_modell",
        "leistung": "custom_ot_leistung_kw",
        "leistung (kw)": "custom_ot_leistung_kw",
        "leistung_kw": "custom_ot_leistung_kw",
        "kw": "custom_ot_leistung_kw",
        "marktwert": "custom_wert_gutachten",
        "marktwert (€)": "custom_wert_gutachten",
        "wert": "custom_wert_gutachten",
        "baujahr": "custom_baujahr",
        "kennzeichen": "custom_kennzeichen",
        "alltagsfahrzeug": "custom_ot_alltagsfahrzeug",
        "alltagsfahrzeug vorhanden": "custom_ot_alltagsfahrzeug",
        "alltagsfahrzeug_vorhanden": "custom_ot_alltagsfahrzeug",
        "fahrzeugtyp": "custom_fahrzeugtyp",

        # === GELDANLAGE / VALLUE – Masterplanung S.29-30 ===
        "anlagebetrag": "custom_anlagesumme",
        "anlagesumme": "custom_anlagesumme",
        "gewünschter anlagebetrag": "custom_anlagesumme",
        "ihr gewünschter anlagebetrag": "custom_anlagesumme",
        "anlagekonzept": "custom_vallue_anlagekonzept",
        "gewünschtes anlagekonzept": "custom_vallue_anlagekonzept",
        "konzept": "custom_vallue_anlagekonzept",
        "art der anlage": "custom_vallue_anlageart",
        "anlageart": "custom_vallue_anlageart",

        # === KINDERPOLICE – Masterplanung S.30-31 ===
        "gewünschter monatlicher beitrag": "custom_kp_monatsbeitrag",
        "monatlicher beitrag": "custom_kp_monatsbeitrag",
        "gewünschte monatlicher beitrag": "custom_kp_monatsbeitrag",
        "monatsbeitrag": "custom_kp_monatsbeitrag",
        "beitrag": "custom_kp_monatsbeitrag",
        "geburtsdatum kind": "custom_kp_geburtsdatum_kind",
        "geburtsdatum des kindes": "custom_kp_geburtsdatum_kind",
        "geburtsdatum_kind": "custom_kp_geburtsdatum_kind",
        "name kind": "custom_kp_name_kind",
        "name des kindes": "custom_kp_name_kind",
        "name_kind": "custom_kp_name_kind",

        # === MANAGERPROTECT – Masterplanung S.32-33 ===
        "position": "custom_mp_position",
        "position im unternehmen": "custom_mp_position",
        "branche": "custom_mp_branche",
        "branche des unternehmens": "custom_mp_branche",
        "gewünschte absicherung": "custom_mp_gewuenschte_absicherung",
        "gewuenschte absicherung": "custom_mp_gewuenschte_absicherung",
        "mp_firma": "custom_mp_firma",

        # === JURATAX – Masterplanung S.34-35 ===
        "aktuelle rechtsform": "custom_jt_rechtsform",
        "rechtsform": "custom_jt_rechtsform",
        "anzahl berufsträger": "custom_jt_berufstraeger",
        "anzahl der berufsträger": "custom_jt_berufstraeger",
        "berufstraeger": "custom_jt_berufstraeger",
        "anzahl mitarbeiter": "custom_jt_mitarbeiter",
        "anzahl der mitarbeiter": "custom_jt_mitarbeiter",
        "mitarbeiter": "custom_jt_mitarbeiter",
        "jt_branche": "custom_jt_branche",

        # === LOL (Loss of Licence) – Masterplanung S.36-38 ===
        "beruf": "custom_lol_beruf",
        "kapitän": "custom_lol_beruf",
        "co-pilot": "custom_lol_beruf",
        "arbeitgeber": "custom_lol_arbeitgeber",
        "airline": "custom_lol_arbeitgeber",
        "gewünschte monatliche lol-rente": "custom_lol_gewuenschte_rente",
        "gewünschte lol-rente": "custom_lol_gewuenschte_rente",
        "lol_rente": "custom_lol_gewuenschte_rente",
        "lol-rente": "custom_lol_gewuenschte_rente",
        "bestehende monatliche lol-rente": "custom_lol_bestehende_rente",
        "bestehende lol-rente": "custom_lol_bestehende_rente",
        "endalter": "custom_lol_endalter",
        "geburtsdatum": "custom_geburtsdatum",

        # === PILOTNOW – Masterplanung S.39 ===
        "gewünschte bausteine": "custom_pn_bausteine",
        "bausteine": "custom_pn_bausteine",
        "pn_bausteine": "custom_pn_bausteine",

        # === BU (meine-1750) – Masterplanung S.40 ===
        "bu_beruf": "custom_bu_beruf",
        "bu_geburtsdatum": "custom_bu_geburtsdatum",
        "monatliches brutto-einkommen": "custom_bu_einkommen",
        "brutto-einkommen": "custom_bu_einkommen",
        "bruttoeinkommen": "custom_bu_einkommen",
        "bu_einkommen": "custom_bu_einkommen",
        "steuerklasse": "custom_bu_steuerklasse",
        "bu_steuerklasse": "custom_bu_steuerklasse",
        "kinder lohnsteuerkarte": "custom_bu_kinder",
        "kinder": "custom_bu_kinder",
        "bu_kinder": "custom_bu_kinder",
        "kirchensteuer": "custom_bu_kirchensteuer",
        "bu_kirchensteuer": "custom_bu_kirchensteuer",
        "privat krankenversichert": "custom_bu_pkv",
        "pkv": "custom_bu_pkv",
        "bu_pkv": "custom_bu_pkv",
        "gewünschte monatliche rente bei berufsunfähigkeitsrente": "custom_bu_gewuenschte_rente",
        "gewünschte rente": "custom_bu_gewuenschte_rente",
        "rente": "custom_bu_gewuenschte_rente",
        "bu_rente": "custom_bu_gewuenschte_rente",

        # === bAV (vorsorge-anfrage) – Masterplanung S.41-43 ===
        "bav_firma": "custom_bav_firma",
        "bav_einkommen": "custom_bav_einkommen",
        "bav_steuerklasse": "custom_bav_steuerklasse",
        "bav_kinder": "custom_bav_kinder",
        "bav_kirchensteuer": "custom_bav_kirchensteuer",
        "bav_pkv": "custom_bav_pkv",
        "eintrittsdatum": "custom_bav_eintrittsdatum",
        "bav_eintrittsdatum": "custom_bav_eintrittsdatum",
        "vorsorgekonzept": "custom_bav_vorsorgekonzept",
        "gewuenschtes vorsorgekonzept": "custom_bav_vorsorgekonzept",
        "bav_vorsorgekonzept": "custom_bav_vorsorgekonzept",
        # bAV LP-spezifische Felder
        "monatliches_brutto_einkommen": "custom_bav_einkommen",
        "steuerklasse": "custom_bav_steuerklasse",
        "kinder_lohnsteuerkarte": "custom_bav_kinder",
        "kirchensteuer": "custom_bav_kirchensteuer",
        "privat_krankenversichert": "custom_bav_pkv",
        "variante_basis": "custom_bav_variante_basis",
        "variante_komfort": "custom_bav_variante_komfort",
        "variante_premium": "custom_bav_variante_premium",
        "variante_individuell": "custom_bav_variante_individuell",
        "bu_rente_1750": "custom_bav_bu_rente_1750",
        "bu_rente_individuell": "custom_bav_bu_rente_individuell",
        "service_ruhestandsberatung": "custom_bav_service_ruhestand",
        "service_vorsorge_check": "custom_bav_service_vorsorge",
        # === Allgemeine Adressfelder ===
        "strasse": "custom_strasse",
        "plz_ort": "custom_plz_ort",
        "adresse": "_adresse",

        # === Allgemein / KV Mensch ===
        "einkommen": "custom_einkommen_brutto",
        "versicherungsstatus": "custom_versicherungsstatus",
        "vorerkrankungen_mensch": "custom_vorerkrankungen_mensch",
        "kv_typ": "custom_kv_typ",

        # === Notizen ===
        "notiz": "custom_followup_notiz",
        "bemerkung": "custom_followup_notiz",
        "nachricht": "custom_followup_notiz",
        "message": "custom_followup_notiz",
        "kommentar": "custom_followup_notiz",
    }

    # --- Map fields ---
    lead_data = {}
    extra_data = {}

    # Normalize keys: lowercase, strip whitespace
    normalized_data = {}
    for key, value in data.items():
        normalized_data[key.lower().strip()] = value
    data = normalized_data

    for key, value in data.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        k = key.lower().strip()
        # Try mapping with original key first, then without custom_ prefix
        mapped = FIELD_MAP.get(k)
        if not mapped and k.startswith("custom_"):
            mapped = FIELD_MAP.get(k[7:])  # strip "custom_" prefix
        if not mapped and k.startswith("custom_"):
            # Direct field name on CRM Lead (e.g. custom_dsgvo_zugestimmt)
            if hasattr(frappe.get_meta("CRM Lead"), "has_field") and frappe.get_meta("CRM Lead").has_field(k):
                mapped = k
        if mapped:
            lead_data[mapped] = value
        else:
            extra_data[key] = value

    # Context-aware routing: some fields depend on Leadtyp
    leadtyp = (lead_data.get("custom_leadtyp") or "").lower()

    # "beruf" conflicts: LOL uses custom_lol_beruf, BU uses custom_bu_beruf, general uses custom_beruf
    if "custom_lol_beruf" in lead_data and leadtyp and "bu" in leadtyp:
        lead_data["custom_bu_beruf"] = lead_data.pop("custom_lol_beruf")
    elif "custom_lol_beruf" in lead_data and leadtyp and ("lol" not in leadtyp and "pilot" not in leadtyp):
        lead_data["custom_beruf"] = lead_data.pop("custom_lol_beruf")

    # "arbeitgeber" conflicts: LOL uses custom_lol_arbeitgeber, bAV uses custom_bav_firma
    if "custom_lol_arbeitgeber" in lead_data and leadtyp and "bav" in leadtyp:
        lead_data["custom_bav_firma"] = lead_data.pop("custom_lol_arbeitgeber")
    elif "custom_lol_arbeitgeber" in lead_data and leadtyp and ("lol" not in leadtyp and "pilot" not in leadtyp):
        lead_data["custom_arbeitgeber"] = lead_data.pop("custom_lol_arbeitgeber")

    # "branche" conflicts: MP uses custom_mp_branche, JT uses custom_jt_branche
    if "custom_mp_branche" in lead_data and leadtyp and "jura" in leadtyp:
        lead_data["custom_jt_branche"] = lead_data.pop("custom_mp_branche")

    # "geburtsdatum" general: route to BU if BU leadtyp
    if "custom_geburtsdatum" in lead_data and leadtyp and "bu" in leadtyp:
        lead_data["custom_bu_geburtsdatum"] = lead_data.get("custom_geburtsdatum", "")

    # "einkommen" route to BU/bAV specific fields
    if "custom_bu_einkommen" in lead_data and leadtyp and "bav" in leadtyp:
        lead_data["custom_bav_einkommen"] = lead_data.pop("custom_bu_einkommen")
    if "custom_bu_steuerklasse" in lead_data and leadtyp and "bav" in leadtyp:
        lead_data["custom_bav_steuerklasse"] = lead_data.pop("custom_bu_steuerklasse")
    if "custom_bu_kinder" in lead_data and leadtyp and "bav" in leadtyp:
        lead_data["custom_bav_kinder"] = lead_data.pop("custom_bu_kinder")
    if "custom_bu_kirchensteuer" in lead_data and leadtyp and "bav" in leadtyp:
        lead_data["custom_bav_kirchensteuer"] = lead_data.pop("custom_bu_kirchensteuer")
    if "custom_bu_pkv" in lead_data and leadtyp and "bav" in leadtyp:
        lead_data["custom_bav_pkv"] = lead_data.pop("custom_bu_pkv")


    # --- Normalize Select field values (short form -> full form) ---
    # Landing pages send short values, CRM expects full option labels


    # Normalize Alltagsfahrzeug (Ja/Nein -> 1/0 for Check field, or keep string)
    if "custom_ot_alltagsfahrzeug" in lead_data:
        raw = str(lead_data["custom_ot_alltagsfahrzeug"]).strip().lower()
        if raw in ("ja", "yes", "1", "true"):
            lead_data["custom_ot_alltagsfahrzeug"] = "Ja"
        elif raw in ("nein", "no", "0", "false"):
            lead_data["custom_ot_alltagsfahrzeug"] = "Nein"

    # Normalize all Ja/Nein Select fields (lowercase -> capitalized)
    JA_NEIN_FIELDS = [
        "custom_bu_kirchensteuer", "custom_bu_pkv",
        "custom_bav_kirchensteuer", "custom_bav_pkv",
    ]
    for jn_field in JA_NEIN_FIELDS:
        if jn_field in lead_data:
            raw = str(lead_data[jn_field]).strip().lower()
            if raw in ("ja", "yes", "1", "true"):
                lead_data[jn_field] = "Ja"
            elif raw in ("nein", "no", "0", "false"):
                lead_data[jn_field] = "Nein"

    # Normalize custom_leadquelle values (LP sends various spellings)
    if "custom_leadquelle" in lead_data:
        LEADQUELLE_MAP = {
            "landingpage": "Landing Page",
            "landing page": "Landing Page",
            "landing-page": "Landing Page",
            "lp": "Landing Page",
            "facebook": "Facebook",
            "instagram": "Instagram",
            "google ads": "Google Ads",
            "google": "Google Ads",
            "googleads": "Google Ads",
            "empfehlung": "Empfehlung",
            "referral": "Empfehlung",
            "bestandskunde": "Bestandskunde",
            "manuell": "Manuell",
            "manual": "Manuell",
            "telefon": "Telefon",
            "phone": "Telefon",
            "messe": "Messe",
            "partner": "Partner",
            "sonstiges": "Sonstiges",
            "other": "Sonstiges",
        }
        raw_quelle = str(lead_data["custom_leadquelle"]).strip().lower()
        if raw_quelle in LEADQUELLE_MAP:
            lead_data["custom_leadquelle"] = LEADQUELLE_MAP[raw_quelle]

    # Normalize custom_leadtyp (LP sends various spellings)
    if "custom_leadtyp" in lead_data:
        LEADTYP_MAP = {
            "pferdeversicherung": "Pferd",
            "pferd": "Pferd",
            "hundeversicherung": "Hund",
            "hund": "Hund",
            "katzenversicherung": "Katze",
            "katze": "Katze",
            "tierkrankenversicherung": "Pferd",
            "oldtimer": "Oldtimer",
            "oldtimerversicherung": "Oldtimer",
            "geldanlage": "Geldanlage / Vallue",
            "geldanlage / vallue": "Geldanlage / Vallue",
            "vallue": "Geldanlage / Vallue",
            "kinderpolice": "Kinderpolice",
            "managerprotect": "ManagerProtect",
            "manager protect": "ManagerProtect",
            "d&o": "ManagerProtect",
            "juratax": "JuraTax",
            "jura tax": "JuraTax",
            "lol": "LOL (Loss of Licence)",
            "lol (loss of licence)": "LOL (Loss of Licence)",
            "loss of licence": "LOL (Loss of Licence)",
            "bu": "BU (meine-1750)",
            "bu (meine-1750)": "BU (meine-1750)",
            "berufsunfähigkeit": "BU (meine-1750)",
            "berufsunfaehigkeit": "BU (meine-1750)",
            "meine-1750": "BU (meine-1750)",
            "bav": "bAV",
            "betriebliche altersversorgung": "bAV",
            "betriebliche altersvorsorge": "bAV",
            "pilotnow": "PilotNow",
            "pilot now": "PilotNow",
            "kv mensch voll": "KV Mensch Voll",
            "kv voll": "KV Mensch Voll",
            "krankenversicherung voll": "KV Mensch Voll",
            "kv mensch zusatz": "KV Mensch Zusatz",
            "kv zusatz": "KV Mensch Zusatz",
            "krankenversicherung zusatz": "KV Mensch Zusatz",
            "sonstiges": "Sonstiges",
        }
        raw_typ = str(lead_data["custom_leadtyp"]).strip().lower()
        if raw_typ in LEADTYP_MAP:
            lead_data["custom_leadtyp"] = LEADTYP_MAP[raw_typ]

    # Normalize custom_herkunft_typ
    if "custom_herkunft_typ" in lead_data:
        HERKUNFT_MAP = {
            "organisch": "Organisch",
            "organic": "Organisch",
            "google": "Google Ads",
            "google ads": "Google Ads",
            "facebook": "Facebook Ads",
            "facebook ads": "Facebook Ads",
            "instagram": "Instagram Ads",
            "instagram ads": "Instagram Ads",
            "bezahlte kampagne": "Bezahlte Kampagne",
            "kampagne": "Bezahlte Kampagne",
            "empfehlung": "Empfehlung",
            "referral": "Empfehlung",
            "bestandskunde": "Bestandskunde",
        }
        raw_herkunft = str(lead_data["custom_herkunft_typ"]).strip().lower()
        if raw_herkunft in HERKUNFT_MAP:
            lead_data["custom_herkunft_typ"] = HERKUNFT_MAP[raw_herkunft]

    # Handle _full_name (split into first/last if not separately provided)
    if "_full_name" in lead_data:
        full = str(lead_data.pop("_full_name")).strip()
        if "first_name" not in lead_data:
            parts = full.split(" ", 1)
            lead_data["first_name"] = parts[0]
            if len(parts) > 1 and "last_name" not in lead_data:
                lead_data["last_name"] = parts[1]

    # --- Validation ---
    if not lead_data.get("first_name") and not lead_data.get("last_name"):
        frappe.throw("Mindestens Vorname oder Nachname muss angegeben werden.")

    if not lead_data.get("mobile_no") and not lead_data.get("email") and not lead_data.get("phone"):
        frappe.throw("Mindestens Telefon oder E-Mail muss angegeben werden.")

    # --- Duplicate check by external LP-ID (if provided) ---
    duplicate_lead = None
    lp_id = data.get("lp_id") or data.get("submission_id") or data.get("form_id") or data.get("anfrage_id") or ""
    if lp_id:
        existing = frappe.get_all(
            "CRM Lead",
            filters={"custom_quell_url": ["like", "%lp_id=" + str(lp_id)]},
            fields=["name"],
            limit=1,
        )
        if existing:
            duplicate_lead = existing[0].name
        # Also store lp_id in quell_url for future dedup
        if not lead_data.get("custom_quell_url"):
            lead_data["custom_quell_url"] = "lp_id=" + str(lp_id)
        elif "lp_id=" not in str(lead_data.get("custom_quell_url", "")):
            lead_data["custom_quell_url"] = str(lead_data["custom_quell_url"]) + "?lp_id=" + str(lp_id)

    if duplicate_lead:
        # Update existing lead with new data, don't create duplicate
        lead = frappe.get_doc("CRM Lead", duplicate_lead)
        for field, value in lead_data.items():
            if field in ("first_name", "last_name", "email", "mobile_no", "phone"):
                continue  # Don't overwrite identity fields
            if hasattr(lead, field) and value:
                setattr(lead, field, value)
        if extra_data:
            old_extra = {}
            if lead.custom_followup_notiz and lead.custom_followup_notiz.startswith("{"):
                try:
                    old_extra = _json.loads(lead.custom_followup_notiz)
                except Exception:
                    pass
            lead.add_comment("Info", "LP-Update: Duplikat erkannt, Daten aktualisiert. Neue Felder: {0}".format(
                ", ".join(extra_data.keys())
            ))
        lead.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "lead_name": lead.name,
            "duplicate": True,
            "message": "Lead existiert bereits und wurde aktualisiert.",
        }

    # --- Create new lead ---
    lead = frappe.new_doc("CRM Lead")

    # Set mapped fields
    for field, value in lead_data.items():
        if hasattr(lead, field):
            # Boolean handling
            if field == "custom_dsgvo_zugestimmt":
                value = 1 if value in (True, 1, "1", "true", "yes", "ja") else 0
            setattr(lead, field, value)

    # Ensure lead_name is set (CRM Lead requires name or organization or email)
    if not lead.lead_name:
        name_parts = [lead.first_name or "", lead.last_name or ""]
        lead.lead_name = " ".join(p for p in name_parts if p).strip() or lead.email or "LP Lead"

    # Always set Liste 10 and defaults
    lead.custom_liste = "10 - Neu ohne Termin"
    lead.status = "Nicht kontaktiert"
    lead.custom_zustaendige_rolle = "CRM Vertrieb"

    if not lead.custom_leadquelle:
        lead.custom_leadquelle = "Landing Page"
    if not lead.custom_herkunft_typ:
        lead.custom_herkunft_typ = "Organisch"

    # DSGVO timestamp
    if lead.custom_dsgvo_zugestimmt:
        lead.custom_dsgvo_timestamp = frappe.utils.now_datetime()

    # Auto-set tierart from leadtyp for Tier-Leads
    if lead.custom_leadtyp in ("Hund", "Katze", "Pferd") and not lead.custom_tierart:
        lead.custom_tierart = lead.custom_leadtyp

    # Copy organization to type-specific firma field
    if lead.custom_leadtyp == "ManagerProtect" and lead.organization and not lead.custom_mp_firma:
        lead.custom_mp_firma = lead.organization
    if lead.custom_leadtyp == "bAV" and lead.organization and not lead.custom_bav_firma:
        lead.custom_bav_firma = lead.organization

    # Skip validations for webhook leads
    lead.flags.ignore_email_validation = True
    lead.flags.ignore_assignment_policy = True
    lead.flags.ignore_validate = True
    lead.flags.ignore_mandatory = True

    # Sanitize all email-type fields to prevent Frappe's _validate_data_fields from throwing
    import re as _re
    _email_re = _re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    for df in lead.meta.fields:
        if df.options == "Email" or df.fieldtype == "Data" and df.options == "Email":
            val = getattr(lead, df.fieldname, None)
            if val and not _email_re.match(str(val).strip()):
                setattr(lead, df.fieldname, None)

    # Sanitize Date fields: convert DD.MM.YYYY -> YYYY-MM-DD
    _date_de_re = _re.compile(r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$')
    for df in lead.meta.fields:
        if df.fieldtype in ("Date", "Datetime"):
            val = getattr(lead, df.fieldname, None)
            if val and isinstance(val, str):
                val = val.strip()
                m = _date_de_re.match(val)
                if m:
                    day, month, year = m.groups()
                    try:
                        setattr(lead, df.fieldname, "{}-{}-{}".format(year, month.zfill(2), day.zfill(2)))
                    except Exception:
                        setattr(lead, df.fieldname, None)
                elif not _re.match(r'^\d{4}-\d{2}-\d{2}', val):
                    # Not ISO format either - clear it
                    setattr(lead, df.fieldname, None)

    # Sanitize Select fields: clear invalid values instead of letting Frappe reject
    for df in lead.meta.fields:
        if df.fieldtype == "Select" and df.options:
            val = getattr(lead, df.fieldname, None)
            if val:
                valid_options = [o.strip() for o in df.options.split(chr(10)) if o.strip()]
                if str(val).strip() not in valid_options:
                    setattr(lead, df.fieldname, None)

    # Save as Administrator to avoid permission issues
    original_user = frappe.session.user
    frappe.set_user("Administrator")
    try:
        lead.save(ignore_permissions=True)
        frappe.db.commit()
    finally:
        frappe.set_user(original_user)

    # Auto-create custom fields for unknown LP fields
    if extra_data:
        auto_created = []
        for field_key, field_value in extra_data.items():
            if field_key in ("cmd",):
                continue  # Skip Frappe internal params
            created_fieldname = _auto_create_lp_field(field_key, field_value)
            if created_fieldname:
                # Set the value on the lead
                frappe.db.set_value("CRM Lead", lead.name, created_fieldname, str(field_value), update_modified=False)
                auto_created.append("{0} -> {1}".format(field_key, created_fieldname))
            else:
                # Field already existed or was just created in a previous call
                existing_fn = "custom_lp_" + _sanitize_fieldname(field_key)
                try:
                    frappe.db.set_value("CRM Lead", lead.name, existing_fn, str(field_value), update_modified=False)
                except Exception:
                    pass

        if auto_created:
            frappe.get_doc({
                "doctype": "Comment",
                "comment_type": "Info",
                "reference_doctype": "CRM Lead",
                "reference_name": lead.name,
                "content": "Neue LP-Felder automatisch angelegt: {0}".format(", ".join(auto_created)),
            }).insert(ignore_permissions=True)

            # Notify admins about new fields
            _notify_admins_new_lp_fields(auto_created)

        frappe.db.commit()

    # Gamification: Erstkontakt-Punkte werden bei erster Aktion vergeben, nicht bei Erstellung

    return {
        "success": True,
        "lead_name": lead.name,
        "duplicate": False,
        "message": "Lead erfolgreich erstellt.",
        "unmapped_fields": list(extra_data.keys()) if extra_data else [],
    }


def _validate_api_key(api_key, api_secret):
    """Validate API key:secret pair against User records."""
    try:
        user = frappe.db.get_value("User", {"api_key": api_key, "enabled": 1}, "name")
        if not user:
            return False
        stored_secret = frappe.utils.password.get_decrypted_password("User", user, "api_secret")
        if stored_secret == api_secret:
            frappe.set_user(user)
            return True
        return False
    except Exception:
        return False


def _sanitize_fieldname(name):
    """Convert arbitrary field name to valid Frappe fieldname."""
    import re
    clean = name.lower().strip()
    clean = re.sub(r'[^a-z0-9_]', '_', clean)
    clean = re.sub(r'_+', '_', clean).strip('_')
    if len(clean) < 2:
        clean = "field_" + clean
    return clean[:40]


def _auto_create_lp_field(field_key, field_value):
    """Auto-create a Custom Field on CRM Lead for an unknown LP field.
    Returns the fieldname if created, None if already exists.
    """
    sanitized = _sanitize_fieldname(field_key)
    fieldname = "custom_lp_" + sanitized

    if frappe.db.exists("Custom Field", {"dt": "CRM Lead", "fieldname": fieldname}):
        return None

    # Use Text/mediumtext for LP fields to avoid MariaDB row size limit (65535 bytes)
    # varchar fields count toward row size; Text (mediumtext) does not
    fieldtype = "Text"
    if isinstance(field_value, bool):
        fieldtype = "Check"
    elif isinstance(field_value, int):
        fieldtype = "Int"
    elif isinstance(field_value, float):
        fieldtype = "Float"

    label = field_key.replace("_", " ").replace("-", " ").title()
    label = "LP: " + label

    if not frappe.db.exists("Custom Field", {"dt": "CRM Lead", "fieldname": "custom_lp_section"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "CRM Lead",
            "fieldname": "custom_lp_section",
            "fieldtype": "Section Break",
            "label": "Landing Page Felder",
            "insert_after": "custom_followup_notiz",
            "collapsible": 1,
        }).insert(ignore_permissions=True)

    try:
        cf = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "CRM Lead",
            "fieldname": fieldname,
            "fieldtype": fieldtype,
            "label": label,
            "insert_after": "custom_lp_section",
            "description": "Automatisch von Landing Page erstellt",
        })
        cf.insert(ignore_permissions=True)
        frappe.clear_cache(doctype="CRM Lead")
        return fieldname
    except Exception as e:
        frappe.log_error("LP Auto-Field Creation Error: {0} - {1}".format(field_key, str(e)))
        return None


def _notify_admins_new_lp_fields(created_fields):
    """Send notification to System Managers about auto-created LP fields."""
    try:
        admins = frappe.get_all(
            "Has Role",
            filters={"role": "System Manager", "parenttype": "User"},
            fields=["parent"],
        )
        for admin in admins:
            if admin.parent in ("Administrator", "Guest"):
                continue
            if not frappe.db.get_value("User", admin.parent, "enabled"):
                continue
            frappe.get_doc({
                "doctype": "Notification Log",
                "for_user": admin.parent,
                "type": "Alert",
                "document_type": "CRM Lead",
                "subject": "Neue Landing Page Felder automatisch angelegt",
                "email_content": "Folgende Felder wurden automatisch erstellt:\n{0}\n\nBitte pruefen und ggf. umbenennen.".format(
                    "\n".join("- " + f for f in created_fields)
                ),
            }).insert(ignore_permissions=True)
            break
    except Exception:
        pass


@frappe.whitelist()
def get_primary_advisor(lead_name):
    """Return the primary advisor for a lead if an active CRM Relationship exists."""
    if not lead_name:
        return None

    rels = frappe.get_all(
        'CRM Relationship',
        filters={'origin_lead': lead_name, 'status': 'Aktiv'},
        fields=['name', 'primary_advisor', 'start_date', 'contact_name', 'lead_typ'],
        limit=1,
    )

    if not rels:
        return None

    advisor = rels[0]
    user_info = frappe.db.get_value(
        'User', advisor.primary_advisor, ['full_name', 'user_image'], as_dict=True
    )

    return {
        'name': advisor.name,
        'advisor': advisor.primary_advisor,
        'full_name': user_info.full_name if user_info else advisor.primary_advisor,
        'image': user_info.user_image if user_info else None,
        'since': str(advisor.start_date) if advisor.start_date else None,
        'contact_name': advisor.contact_name,
        'lead_typ': advisor.lead_typ,
    }