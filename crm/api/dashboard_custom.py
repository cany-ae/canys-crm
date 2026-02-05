import frappe
from frappe import _


@frappe.whitelist()
def get_dashboard_data(period="month", user=""):
	"""
	Aggregated dashboard data for Leads and Deals.
	period: week | month | quarter | year
	Returns: { leads: {...}, deals: {...}, process: {...} }
	"""
	roles = frappe.get_roles(frappe.session.user)
	is_sales_manager = "Sales Manager" in roles or "System Manager" in roles
	is_sales_user = "Sales User" in roles and not is_sales_manager

	if is_sales_user:
		user = frappe.session.user

	lead_conds = ""
	deal_conds = ""
	params = {}

	if user:
		lead_conds = " AND lead_owner = %(user)s"
		deal_conds = " AND deal_owner = %(user)s"
		params["user"] = user

	# --- LEADS ---
	leads_total = _get_leads_total(lead_conds, params)
	leads_by_period = _get_leads_by_period(period, lead_conds, params)
	leads_by_list = _get_leads_by_list(lead_conds, params)

	# --- DEALS ---
	deals_total = _get_deals_total(deal_conds, params)
	deals_by_period = _get_deals_by_period(period, deal_conds, params)
	avg_time_to_close = _get_avg_time_to_close(deal_conds, params)

	# --- PROCESS ---
	avg_lead_to_deal = _get_avg_lead_to_deal(deal_conds, params)

	return {
		"leads": {
			"total": leads_total,
			"by_period": leads_by_period,
			"by_list": leads_by_list,
		},
		"deals": {
			"total": deals_total,
			"by_period": deals_by_period,
			"avg_time_to_close": avg_time_to_close,
		},
		"process": {
			"avg_lead_to_deal": avg_lead_to_deal,
		},
	}


def _get_leads_total(conds, params):
	"""Total number of leads."""
	result = frappe.db.sql(
		f"SELECT COUNT(*) as cnt FROM `tabCRM Lead` WHERE 1=1 {conds}",
		params,
		as_dict=True,
	)
	return result[0].cnt if result else 0


def _get_leads_by_period(period, conds, params):
	"""
	Leads grouped by time period.
	Returns: [{ label: '2026-W05', count: 12 }, ...]
	"""
	group_expr, label_expr = _period_sql(period, "creation")

	result = frappe.db.sql(
		f"""
		SELECT {label_expr} AS label, COUNT(*) AS count
		FROM `tabCRM Lead`
		WHERE 1=1 {conds}
		GROUP BY {group_expr}
		ORDER BY {group_expr}
		""",
		params,
		as_dict=True,
	)
	return result or []


def _get_leads_by_list(conds, params):
	"""
	Leads grouped by custom_liste (Liste A-E).
	Returns: [{ label: 'Liste A', count: 5 }, ...]
	"""
	result = frappe.db.sql(
		f"""
		SELECT IFNULL(NULLIF(custom_liste, ''), 'Ohne Liste') AS label, COUNT(*) AS count
		FROM `tabCRM Lead`
		WHERE 1=1 {conds}
		GROUP BY label
		ORDER BY count DESC
		""",
		params,
		as_dict=True,
	)
	return result or []


def _get_deals_total(conds, params):
	"""Total number of deals."""
	result = frappe.db.sql(
		f"SELECT COUNT(*) as cnt FROM `tabCRM Deal` WHERE 1=1 {conds}",
		params,
		as_dict=True,
	)
	return result[0].cnt if result else 0


def _get_deals_by_period(period, conds, params):
	"""
	Deals grouped by time period.
	Returns: [{ label: '2026-W05', count: 3 }, ...]
	"""
	group_expr, label_expr = _period_sql(period, "creation")

	result = frappe.db.sql(
		f"""
		SELECT {label_expr} AS label, COUNT(*) AS count
		FROM `tabCRM Deal`
		WHERE 1=1 {conds}
		GROUP BY {group_expr}
		ORDER BY {group_expr}
		""",
		params,
		as_dict=True,
	)
	return result or []


def _get_avg_time_to_close(conds, params):
	"""
	Average days from deal creation to closed_date for won deals.
	"""
	result = frappe.db.sql(
		f"""
		SELECT AVG(DATEDIFF(d.closed_date, d.creation)) AS avg_days
		FROM `tabCRM Deal` d
		JOIN `tabCRM Deal Status` s ON d.status = s.name
		WHERE s.type = 'Won'
			AND d.closed_date IS NOT NULL
			{conds}
		""",
		params,
		as_dict=True,
	)
	val = result[0].avg_days if result and result[0].avg_days else 0
	return round(float(val), 1)


def _get_avg_lead_to_deal(conds, params):
	"""
	Average days from lead creation to first deal creation.
	Only considers deals that have a linked lead.
	"""
	result = frappe.db.sql(
		f"""
		SELECT AVG(DATEDIFF(d.creation, l.creation)) AS avg_days
		FROM `tabCRM Deal` d
		JOIN `tabCRM Lead` l ON d.lead = l.name
		WHERE d.lead IS NOT NULL AND d.lead != ''
			{conds}
		""",
		params,
		as_dict=True,
	)
	val = result[0].avg_days if result and result[0].avg_days else 0
	return round(float(val), 1)


def _period_sql(period, date_field):
	"""
	Returns (group_expression, label_expression) for SQL GROUP BY.
	"""
	if period == "week":
		# ISO week: 2026-W05
		group_expr = f"YEARWEEK({date_field}, 1)"
		label_expr = f"CONCAT(YEAR({date_field}), '-W', LPAD(WEEK({date_field}, 1), 2, '0'))"
	elif period == "quarter":
		group_expr = f"CONCAT(YEAR({date_field}), '-Q', QUARTER({date_field}))"
		label_expr = group_expr
	elif period == "year":
		group_expr = f"YEAR({date_field})"
		label_expr = f"CAST(YEAR({date_field}) AS CHAR)"
	else:  # month (default)
		group_expr = f"DATE_FORMAT({date_field}, '%%Y-%%m')"
		label_expr = group_expr

	return group_expr, label_expr
