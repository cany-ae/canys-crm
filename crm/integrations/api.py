import frappe
from frappe.query_builder import Order
from pypika.functions import Replace

from crm.utils import are_same_phone_number, parse_phone_number


@frappe.whitelist()
def is_call_integration_enabled():
	twilio_enabled = frappe.db.get_single_value("CRM Twilio Settings", "enabled")
	exotel_enabled = frappe.db.get_single_value("CRM Exotel Settings", "enabled")

	return {
		"twilio_enabled": twilio_enabled,
		"exotel_enabled": exotel_enabled,
		"default_calling_medium": get_user_default_calling_medium(),
	}


def get_user_default_calling_medium():
	if not frappe.db.exists("CRM Telephony Agent", frappe.session.user):
		return None

	default_medium = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "default_medium")

	if not default_medium:
		return None

	return default_medium


@frappe.whitelist()
def set_default_calling_medium(medium):
	if not frappe.db.exists("CRM Telephony Agent", frappe.session.user):
		frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": frappe.session.user,
				"default_medium": medium,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("CRM Telephony Agent", frappe.session.user, "default_medium", medium)

	return get_user_default_calling_medium()


@frappe.whitelist()
def add_note_to_call_log(call_sid, note):
	"""Add/Update note to call log based on call sid."""
	_note = None
	if not note.get("name"):
		_note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": note.get("title", "Call Note"),
				"content": note.get("content"),
			}
		).insert(ignore_permissions=True)
	else:
		_note = frappe.set_value("FCRM Note", note.get("name"), "content", note.get("content"))

	call_log = frappe.get_cached_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("FCRM Note", _note.name)
	call_log.save(ignore_permissions=True)

	return _note


@frappe.whitelist()
def add_task_to_call_log(call_sid, task):
	"""Add/Update task to call log based on call sid."""
	_task = None
	if not task.get("name"):
		_task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": task.get("title"),
				"description": task.get("description"),
				"assigned_to": task.get("assigned_to"),
				"due_date": task.get("due_date"),
				"status": task.get("status"),
				"priority": task.get("priority"),
			}
		).insert(ignore_permissions=True)
	else:
		_task = frappe.get_doc("CRM Task", task.get("name"))
		_task.update(
			{
				"title": task.get("title"),
				"description": task.get("description"),
				"assigned_to": task.get("assigned_to"),
				"due_date": task.get("due_date"),
				"status": task.get("status"),
				"priority": task.get("priority"),
			}
		)
		_task.save(ignore_permissions=True)

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("CRM Task", _task.name)
	call_log.save(ignore_permissions=True)

	return _task

frappe.whitelist()
def get_contact_lead_or_deal_from_number(number):
	"""Get contact, lead or deal from the given number."""
	contact = get_contact_by_phone_number(number)
	if contact.get("name"):
		doctype = "Contact"
		docname = contact.get("name")
		if contact.get("lead"):
			doctype = "CRM Lead"
			docname = contact.get("lead")
		elif contact.get("deal"):
			doctype = "CRM Deal"
			docname = contact.get("deal")
		return docname, doctype
	return None, None

@frappe.whitelist()
def get_contact_by_phone_number(phone_number):
	"""Get contact by phone number."""
	number = parse_phone_number(phone_number)

	if number.get("is_valid"):
		return get_contact(number.get("national_number"), number.get("country"))
	else:
		return get_contact(phone_number, number.get("country"), exact_match=True)


def get_contact(phone_number, country="IN", exact_match=False):
	if not phone_number:
		return {"mobile_no": phone_number}

	cleaned_number = (
		phone_number.strip()
		.replace(" ", "")
		.replace("-", "")
		.replace("(", "")
		.replace(")", "")
		.replace("+", "")
	)

	# Check if the number is associated with a contact
	Contact = frappe.qb.DocType("Contact")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(Contact.mobile_no, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(Contact)
		.select(Contact.name, Contact.full_name, Contact.image, Contact.mobile_no)
		.where(normalized_phone.like(f"%{cleaned_number}%"))
		.orderby("modified", order=Order.desc)
	)
	contacts = query.run(as_dict=True)

	if len(contacts):
		# Check if the contact is associated with a deal
		for contact in contacts:
			if frappe.db.exists("CRM Contacts", {"contact": contact.name, "is_primary": 1}):
				deal = frappe.db.get_value(
					"CRM Contacts", {"contact": contact.name, "is_primary": 1}, "parent"
				)
				if are_same_phone_number(contact.mobile_no, phone_number, country, validate=not exact_match):
					contact["deal"] = deal
					return contact

	# Else, Check if the number is associated with a lead
	Lead = frappe.qb.DocType("CRM Lead")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(Lead.mobile_no, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(Lead)
		.select(Lead.name, Lead.lead_name, Lead.image, Lead.mobile_no)
		.where(Lead.converted == 0)
		.where(normalized_phone.like(f"%{cleaned_number}%"))
		.orderby("modified", order=Order.desc)
	)
	leads = query.run(as_dict=True)

	if len(leads):
		for lead in leads:
			if are_same_phone_number(lead.mobile_no, phone_number, country, validate=not exact_match):
				lead["lead"] = lead.name
				lead["full_name"] = lead.lead_name
				return lead

	if len(contacts) and are_same_phone_number(
		contacts[0].mobile_no, phone_number, country, validate=not exact_match
	):
		return contacts[0]

	return {"mobile_no": phone_number}


@frappe.whitelist()
def lookup_by_phone(phone_number):
	"""Lookup Lead (priority) or Contact by phone number.
	Returns: {type: "lead"|"contact"|"unknown", name, full_name, image, mobile_no}
	Lead priority: open leads (converted=0), prefer assigned to current user.
	"""
	if not phone_number:
		return {"type": "unknown", "mobile_no": phone_number}

	number = parse_phone_number(phone_number)
	if number.get("is_valid"):
		cleaned = number.get("national_number")
		country = number.get("country")
		exact = False
	else:
		cleaned = phone_number
		country = number.get("country") or "DE"
		exact = True

	# Normalize: strip spaces, dashes, parentheses, +
	cleaned_number = (
		str(cleaned).strip()
		.replace(" ", "")
		.replace("-", "")
		.replace("(", "")
		.replace(")", "")
		.replace("+", "")
	)

	# Also try DE variants: +49xxx <-> 0xxx
	alt_numbers = [cleaned_number]
	if cleaned_number.startswith("49"):
		alt_numbers.append("0" + cleaned_number[2:])
	elif cleaned_number.startswith("0"):
		alt_numbers.append("49" + cleaned_number[1:])

	current_user = frappe.session.user

	# --- STEP 1: Search Leads (priority) ---
	Lead = frappe.qb.DocType("CRM Lead")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(Lead.mobile_no, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	# Build OR condition for all number variants
	from pypika import Criterion
	phone_conditions = Criterion.any([normalized_phone.like(f"%{n}%") for n in alt_numbers])

	query = (
		frappe.qb.from_(Lead)
		.select(Lead.name, Lead.lead_name, Lead.image, Lead.mobile_no, Lead._assign)
		.where(Lead.converted == 0)
		.where(phone_conditions)
		.orderby("modified", order=Order.desc)
	)
	leads = query.run(as_dict=True)

	if leads:
		# Prefer lead assigned to current user
		my_lead = None
		any_lead = None
		for lead in leads:
			assign = lead.get("_assign") or ""
			if current_user in assign:
				my_lead = lead
				break
			elif not any_lead:
				any_lead = lead

		chosen = my_lead or any_lead
		if chosen:
			return {
				"type": "lead",
				"name": chosen.name,
				"full_name": chosen.lead_name,
				"image": chosen.image,
				"mobile_no": chosen.mobile_no,
			}

	# --- STEP 2: Search Contacts (fallback) ---
	Contact = frappe.qb.DocType("Contact")
	normalized_phone_c = Replace(
		Replace(Replace(Replace(Replace(Contact.mobile_no, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)
	phone_conditions_c = Criterion.any([normalized_phone_c.like(f"%{n}%") for n in alt_numbers])

	query = (
		frappe.qb.from_(Contact)
		.select(Contact.name, Contact.full_name, Contact.image, Contact.mobile_no)
		.where(phone_conditions_c)
		.orderby("modified", order=Order.desc)
	)
	contacts = query.run(as_dict=True)

	if contacts:
		for c in contacts:
			if True:  # LIKE query with alt_numbers handles matching
				# Check if contact has a deal
				deal = None
				if frappe.db.exists("CRM Contacts", {"contact": c.name, "is_primary": 1}):
					deal = frappe.db.get_value(
						"CRM Contacts", {"contact": c.name, "is_primary": 1}, "parent"
					)
				return {
					"type": "contact",
					"name": c.name,
					"full_name": c.full_name,
					"image": c.image,
					"mobile_no": c.mobile_no,
					"deal": deal,
				}

	return {"type": "unknown", "mobile_no": phone_number}
