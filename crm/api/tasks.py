import frappe
from frappe import _


@frappe.whitelist()
def get_tasks(view="open", quick_filter="", user_filter=""):
	"""
	Task inbox API with role-based filtering and smart sorting.

	view: open | completed | all
	quick_filter: overdue | today | this_week | no_date | (empty)
	user_filter: email of user to filter by (manager only)
	"""
	roles = frappe.get_roles(frappe.session.user)
	is_manager = "Sales Manager" in roles or "System Manager" in roles

	conditions = []
	params = {}

	# Role-based filtering
	if not is_manager:
		# Sales users see only their own tasks
		conditions.append("t.assigned_to = %(current_user)s")
		params["current_user"] = frappe.session.user
	elif user_filter:
		conditions.append("t.assigned_to = %(user_filter)s")
		params["user_filter"] = user_filter

	# View filtering
	if view == "open":
		conditions.append("t.status NOT IN ('Done', 'Canceled')")
	elif view == "completed":
		conditions.append("t.status IN ('Done', 'Canceled')")

	# Quick filters
	today = frappe.utils.today()
	if quick_filter == "overdue":
		conditions.append("t.due_date < %(today)s")
		conditions.append("t.status NOT IN ('Done', 'Canceled')")
		params["today"] = today
	elif quick_filter == "today":
		conditions.append("DATE(t.due_date) = %(today)s")
		params["today"] = today
	elif quick_filter == "this_week":
		week_end = frappe.utils.add_days(today, 7)
		conditions.append("DATE(t.due_date) BETWEEN %(today)s AND %(week_end)s")
		params["today"] = today
		params["week_end"] = week_end
	elif quick_filter == "no_date":
		conditions.append("(t.due_date IS NULL OR t.due_date = '')")

	where = " AND ".join(conditions) if conditions else "1=1"

	# Sorting
	if view == "completed":
		order_by = "t.completed_at DESC, t.modified DESC"
	else:
		# Open view: overdue first, then today, then upcoming, then no date
		order_by = """
			CASE
				WHEN t.due_date IS NOT NULL AND DATE(t.due_date) < CURDATE() THEN 0
				WHEN t.due_date IS NOT NULL AND DATE(t.due_date) = CURDATE() THEN 1
				WHEN t.due_date IS NOT NULL AND DATE(t.due_date) > CURDATE() THEN 2
				ELSE 3
			END ASC,
			t.due_date ASC,
			priority_order ASC,
			t.modified DESC
		"""

	tasks = frappe.db.sql(f"""
		SELECT
			t.name, t.title, t.description, t.status, t.priority,
			t.assigned_to, t.due_date, t.reference_doctype, t.reference_docname,
			t.completed_at, t.completed_by, t.creation, t.modified,
			CASE t.priority
				WHEN 'High' THEN 0
				WHEN 'Medium' THEN 1
				ELSE 2
			END AS priority_order,
			u.full_name AS assigned_to_name,
			u.user_image AS assigned_to_image
		FROM `tabCRM Task` t
		LEFT JOIN tabUser u ON t.assigned_to = u.name
		WHERE {where}
		ORDER BY {order_by}
		LIMIT 200
	""", params, as_dict=True)

	# Add computed fields
	today_date = frappe.utils.getdate(today)
	for task in tasks:
		if task.due_date:
			due = frappe.utils.getdate(task.due_date)
			task["is_overdue"] = due < today_date and task["status"] not in ("Done", "Canceled")
			task["is_today"] = due == today_date
		else:
			task["is_overdue"] = False
			task["is_today"] = False

	# Counts for tabs
	count_conds = []
	if not is_manager:
		count_conds.append(f"assigned_to = '{frappe.db.escape(frappe.session.user)}'")
	elif user_filter:
		count_conds.append(f"assigned_to = '{frappe.db.escape(user_filter)}'")

	count_where = " AND ".join(count_conds) if count_conds else "1=1"

	counts = frappe.db.sql(f"""
		SELECT
			SUM(status NOT IN ('Done', 'Canceled')) AS open_count,
			SUM(status IN ('Done', 'Canceled')) AS completed_count,
			COUNT(*) AS total_count,
			SUM(due_date IS NOT NULL AND DATE(due_date) < CURDATE() AND status NOT IN ('Done', 'Canceled')) AS overdue_count
		FROM `tabCRM Task`
		WHERE {count_where}
	""", as_dict=True)[0]

	return {
		"tasks": tasks,
		"counts": {
			"open": int(counts.open_count or 0),
			"completed": int(counts.completed_count or 0),
			"total": int(counts.total_count or 0),
			"overdue": int(counts.overdue_count or 0),
		},
		"is_manager": is_manager,
	}


@frappe.whitelist()
def get_task_users():
	"""
	Returns list of actual sales employees (Vertriebler).
	Uses Mitarbeiterverwaltung sales_team assignment and lead/deal ownership
	to identify real sales users instead of all users with the Sales User role.
	Manager only.
	"""
	roles = frappe.get_roles(frappe.session.user)
	is_manager = "Sales Manager" in roles or "System Manager" in roles
	if not is_manager:
		return []

	return frappe.db.sql("""
		SELECT DISTINCT u.name AS email, u.full_name, u.user_image
		FROM tabUser u
		WHERE u.enabled = 1
			AND u.name NOT IN ('Administrator', 'Guest')
			AND (
				(u.sales_team IS NOT NULL AND u.sales_team != '')
				OR EXISTS (SELECT 1 FROM `tabCRM Lead` l WHERE l.lead_owner = u.name)
				OR EXISTS (SELECT 1 FROM `tabCRM Deal` d WHERE d.deal_owner = u.name)
			)
		ORDER BY u.full_name
	""", as_dict=True)
