import frappe
from frappe import _


def validate(doc, method):
	frappe.log_error(title="Contact Validate Debug", message="Contact: {} | custom_contact_type: {} | modified_by: {}".format(doc.name, doc.custom_contact_type, doc.modified_by))  # DEBUG_LOG
	update_deals_email_mobile_no(doc)


def update_deals_email_mobile_no(doc):
	linked_deals = frappe.get_all(
		"CRM Contacts",
		filters={"contact": doc.name, "is_primary": 1},
		fields=["parent"],
	)

	for linked_deal in linked_deals:
		deal = frappe.db.get_values("CRM Deal", linked_deal.parent, ["email", "mobile_no"], as_dict=True)[0]
		if deal.email != doc.email_id or deal.mobile_no != doc.mobile_no:
			frappe.db.set_value(
				"CRM Deal",
				linked_deal.parent,
				{
					"email": doc.email_id,
					"mobile_no": doc.mobile_no,
				},
			)


@frappe.whitelist()
def get_linked_deals(contact):
	"""Get linked deals for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	deal_names = frappe.get_all(
		"CRM Contacts",
		filters={"contact": contact, "parenttype": "CRM Deal"},
		fields=["parent"],
		distinct=True,
	)

	# get deals data
	deals = []
	for d in deal_names:
		deal = frappe.get_cached_doc(
			"CRM Deal",
			d.parent,
			fields=[
				"name",
				"organization",
				"currency",
				"annual_revenue",
				"status",
				"email",
				"mobile_no",
				"deal_owner",
				"modified",
			],
		)
		deals.append(deal.as_dict())

	return deals


@frappe.whitelist()
def create_new(contact, field, value):
	"""Create new email or phone for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	contact = frappe.get_cached_doc("Contact", contact)

	if field == "email":
		email = {"email_id": value, "is_primary": 1 if len(contact.email_ids) == 0 else 0}
		contact.append("email_ids", email)
	elif field in ("mobile_no", "phone"):
		mobile_no = {"phone": value, "is_primary_mobile_no": 1 if len(contact.phone_nos) == 0 else 0}
		contact.append("phone_nos", mobile_no)
	else:
		frappe.throw("Invalid field")

	contact.save()
	return True


@frappe.whitelist()
def set_as_primary(contact, field, value):
	"""Set email or phone as primary for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw("Not permitted", frappe.PermissionError)

	contact = frappe.get_doc("Contact", contact)

	if field == "email":
		for email in contact.email_ids:
			if email.email_id == value:
				email.is_primary = 1
			else:
				email.is_primary = 0
	elif field in ("mobile_no", "phone"):
		name = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
		for phone in contact.phone_nos:
			if phone.phone == value:
				phone.set(name, 1)
			else:
				phone.set(name, 0)
	else:
		frappe.throw("Invalid field")

	contact.save()
	return True


@frappe.whitelist()
def search_emails(txt: str):
	doctype = "Contact"
	meta = frappe.get_meta(doctype)
	filters = [["Contact", "email_id", "is", "set"]]

	if meta.get("fields", {"fieldname": "enabled", "fieldtype": "Check"}):
		filters.append([doctype, "enabled", "=", 1])
	if meta.get("fields", {"fieldname": "disabled", "fieldtype": "Check"}):
		filters.append([doctype, "disabled", "!=", 1])

	or_filters = []
	search_fields = ["full_name", "email_id", "name"]
	if txt:
		for f in search_fields:
			or_filters.append([doctype, f.strip(), "like", f"%{txt}%"])

	results = frappe.get_list(
		doctype,
		filters=filters,
		fields=search_fields,
		or_filters=or_filters,
		limit_start=0,
		limit_page_length=20,
		order_by="email_id, full_name, name",
		ignore_permissions=False,
		as_list=True,
		strict=False,
	)

	return results


@frappe.whitelist()
def get_contact_history(contact):
	"""Get aggregated contact history across all linked Leads and Deals.

	Returns leads, deals, and a summary with counts, status breakdowns,
	total revenue, first lead date, and last activity date.
	"""
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	# 1. Find all linked Leads via Dynamic Link
	lead_links = frappe.get_all(
		"Dynamic Link",
		filters={
			"parenttype": "Contact",
			"parent": contact,
			"link_doctype": "CRM Lead",
		},
		fields=["link_name"],
	)

	leads = []
	for link in lead_links:
		try:
			lead = frappe.get_cached_doc("CRM Lead", link.link_name)
			leads.append({
				"name": lead.name,
				"status": lead.status,
				"lead_name": lead.lead_name,
				"email": lead.email,
				"mobile_no": lead.mobile_no,
				"custom_liste": lead.custom_liste,
				"custom_leadtyp": lead.custom_leadtyp,
				"custom_produktlinie": lead.custom_produktlinie,
				"lead_owner": lead.lead_owner,
				"creation": lead.creation,
				"modified": lead.modified,
			})
		except frappe.DoesNotExistError:
			continue

	# 2. Find all linked Deals via CRM Contacts child table
	deal_links = frappe.get_all(
		"CRM Contacts",
		filters={
			"contact": contact,
			"parenttype": "CRM Deal",
		},
		fields=["parent"],
		distinct=True,
	)

	deals = []
	for d in deal_links:
		try:
			deal = frappe.get_cached_doc("CRM Deal", d.parent)
			deals.append({
				"name": deal.name,
				"status": deal.status,
				"organization": deal.organization,
				"annual_revenue": deal.annual_revenue or 0,
				"lead": deal.lead,
				"creation": deal.creation,
				"modified": deal.modified,
			})
		except frappe.DoesNotExistError:
			continue

	# 3. Build aggregation summary
	leads_by_status = {}
	for lead in leads:
		s = lead.get("status") or "Unknown"
		leads_by_status[s] = leads_by_status.get(s, 0) + 1

	deals_by_status = {}
	deals_total_revenue = 0.0
	for deal in deals:
		s = deal.get("status") or "Unknown"
		deals_by_status[s] = deals_by_status.get(s, 0) + 1
		deals_total_revenue += float(deal.get("annual_revenue") or 0)

	# Determine first_lead_date and last_activity_date
	all_creation_dates = [l["creation"] for l in leads if l.get("creation")]
	all_modified_dates = (
		[l["modified"] for l in leads if l.get("modified")]
		+ [d["modified"] for d in deals if d.get("modified")]
	)

	first_lead_date = min(all_creation_dates) if all_creation_dates else None
	last_activity_date = max(all_modified_dates) if all_modified_dates else None

	return {
		"leads": leads,
		"deals": deals,
		"summary": {
			"leads_total": len(leads),
			"leads_by_status": leads_by_status,
			"deals_total": len(deals),
			"deals_by_status": deals_by_status,
			"deals_total_revenue": deals_total_revenue,
			"first_lead_date": first_lead_date,
			"last_activity_date": last_activity_date,
		},
	}


@frappe.whitelist()
def get_leads_for_contact(contact):
	"""Get all CRM Leads linked to a Contact.
	Uses custom_contact field (direct link) with Dynamic Link fallback."""
	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	# Primary: Query via custom_contact field (fast, indexed)
	leads_via_field = frappe.get_all("CRM Lead",
		filters={"custom_contact": contact},
		fields=[
			"name", "lead_name", "first_name", "last_name",
			"email", "mobile_no", "status",
			"custom_liste", "custom_leadtyp", "custom_produktlinie",
			"lead_owner", "creation", "modified",
		],
		order_by="creation desc")

	# Fallback: Also check Dynamic Links for leads not yet migrated
	lead_names_from_field = {l.name for l in leads_via_field}

	dl_links = frappe.get_all("Dynamic Link",
		filters={
			"parenttype": "Contact",
			"parent": contact,
			"link_doctype": "CRM Lead",
		},
		fields=["link_name"])

	# Find leads only in Dynamic Links but not in custom_contact
	missing_names = [dl.link_name for dl in dl_links if dl.link_name not in lead_names_from_field]
	if missing_names:
		extra_leads = frappe.get_all("CRM Lead",
			filters={"name": ["in", missing_names]},
			fields=[
				"name", "lead_name", "first_name", "last_name",
				"email", "mobile_no", "status",
				"custom_liste", "custom_leadtyp", "custom_produktlinie",
				"lead_owner", "creation", "modified",
			],
			order_by="creation desc")
		leads_via_field.extend(extra_leads)

	return leads_via_field
