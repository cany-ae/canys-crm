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
	avg_first_contact_to_deal = _get_avg_first_contact_to_deal(deal_conds, params)

	# --- PROCESS ---
	avg_lead_to_deal = _get_avg_lead_to_deal(deal_conds, params)

	# --- PIPELINE FUNNEL ---
	pipeline_funnel = _get_pipeline_funnel(lead_conds, params)

	# --- CLOSINGS ---
	closings = _get_closings_summary(lead_conds, params)

	# --- WARNINGS ---
	warnings = _get_warnings(lead_conds, params)

	# --- TERMIN STATS ---
	termin_stats = _get_termin_stats(lead_conds, params)

	return {
		"leads": {
			"total": leads_total,
			"by_period": leads_by_period,
			"by_list": leads_by_list,
		},
		"deals": {
			"total": deals_total,
			"by_period": deals_by_period,
			"avg_first_contact_to_deal": avg_first_contact_to_deal,
		},
		"process": {
			"avg_lead_to_deal": avg_lead_to_deal,
		},
		"pipeline": pipeline_funnel,
		"closings": closings,
		"warnings": warnings,
		"termin_stats": termin_stats,
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


def _get_avg_first_contact_to_deal(conds, params):
	"""
	Average days from first contact attempt (first status change away from
	'Nicht kontaktiert') to deal creation.
	"""
	result = frappe.db.sql(
		f"""
		SELECT AVG(DATEDIFF(d.creation, fc.first_contact_date)) AS avg_days
		FROM `tabCRM Deal` d
		JOIN `tabCRM Lead` l ON d.lead = l.name
		JOIN (
			SELECT parent, MIN(to_date) AS first_contact_date
			FROM `tabCRM Status Change Log`
			WHERE parenttype = 'CRM Lead'
				AND `from` IN ('Nicht kontaktiert', 'New')
				AND `to` NOT IN ('Nicht kontaktiert', 'New')
			GROUP BY parent
		) fc ON fc.parent = l.name
		WHERE d.lead IS NOT NULL AND d.lead != ''
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


def _get_pipeline_funnel(conds, params):
	"""Pipeline funnel: leads per phase with color coding.
	Returns: [{ phase: '10 - Neu ohne Termin', count: 5, color: '#6B7280', short: '10 Neu' }, ...]
	"""
	phase_config = [
		{"phase": "10 - Neu ohne Termin", "color": "#6B7280", "short": "10 Neu"},
		{"phase": "20 - Termin gebucht", "color": "#3B82F6", "short": "20 Termin"},
		{"phase": "30 - Reaktivierung", "color": "#F59E0B", "short": "30 Reaktiv."},
		{"phase": "50 - Closer-Termin", "color": "#8B5CF6", "short": "50 Closer"},
		{"phase": "70 - Follow-up", "color": "#F97316", "short": "70 Follow-up"},
		{"phase": "80 - Abschluss gewonnen", "color": "#10B981", "short": "80 Gewonnen"},
		{"phase": "90 - Abschluss verloren", "color": "#EF4444", "short": "90 Verloren"},
	]

	result = frappe.db.sql(
		f"""
		SELECT custom_liste, COUNT(*) AS count
		FROM `tabCRM Lead`
		WHERE custom_liste IS NOT NULL AND custom_liste != ''
			{conds}
		GROUP BY custom_liste
		""",
		params,
		as_dict=True,
	)

	count_map = {r.custom_liste: r["count"] for r in result}
	total = sum(count_map.values()) or 1

	funnel = []
	for pc in phase_config:
		cnt = count_map.get(pc["phase"], 0)
		funnel.append({
			"phase": pc["phase"],
			"short": pc["short"],
			"count": cnt,
			"color": pc["color"],
			"pct": round(cnt / total * 100, 1),
		})

	return funnel


def _get_closings_summary(conds, params):
	"""Summary of won and lost leads with revenue.
	Returns: { won: {count, beitrag, provision}, lost: {count, top_reasons: [...]} }
	"""
	won = frappe.db.sql(
		f"""
		SELECT COUNT(*) AS count,
			   IFNULL(SUM(custom_abschluss_beitrag), 0) AS beitrag,
			   IFNULL(SUM(custom_abschluss_provision), 0) AS provision
		FROM `tabCRM Lead`
		WHERE custom_liste = '80 - Abschluss gewonnen'
			{conds}
		""",
		params,
		as_dict=True,
	)

	lost = frappe.db.sql(
		f"""
		SELECT COUNT(*) AS count
		FROM `tabCRM Lead`
		WHERE custom_liste = '90 - Abschluss verloren'
			{conds}
		""",
		params,
		as_dict=True,
	)

	lost_reasons = frappe.db.sql(
		f"""
		SELECT IFNULL(NULLIF(custom_abschluss_verloren_grund, ''), 'Nicht angegeben') AS reason,
			   COUNT(*) AS count
		FROM `tabCRM Lead`
		WHERE custom_liste = '90 - Abschluss verloren'
			AND custom_abschluss_verloren_grund IS NOT NULL
			{conds}
		GROUP BY reason
		ORDER BY count DESC
		LIMIT 5
		""",
		params,
		as_dict=True,
	)

	return {
		"won": {
			"count": won[0]["count"] if won else 0,
			"beitrag": float(won[0].beitrag) if won else 0,
			"provision": float(won[0].provision) if won else 0,
		},
		"lost": {
			"count": lost[0]["count"] if lost else 0,
			"top_reasons": [{"reason": r.reason, "count": r["count"]} for r in lost_reasons],
		},
	}


def _get_warnings(conds, params):
	"""Dashboard warnings: overdue follow-ups, avg reaction time, no-show rate.
	Returns: { overdue_count, avg_reaction_hours, noshow_rate, noshow_count, termin_total }
	"""
	today = frappe.utils.today()

	# Overdue follow-ups
	overdue = frappe.db.sql(
		f"""
		SELECT COUNT(*) AS cnt
		FROM `tabCRM Lead`
		WHERE custom_naechster_kontakt < %(today)s
			AND custom_naechster_kontakt IS NOT NULL
			AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
			{conds}
		""",
		{**params, "today": today},
		as_dict=True,
	)
	overdue_count = overdue[0].cnt if overdue else 0

	# Average reaction time (hours from lead creation to first status change)
	avg_reaction = frappe.db.sql(
		f"""
		SELECT AVG(TIMESTAMPDIFF(HOUR, l.creation, sc.first_change)) AS avg_hours
		FROM `tabCRM Lead` l
		JOIN (
			SELECT parent, MIN(to_date) AS first_change
			FROM `tabCRM Status Change Log`
			WHERE parenttype = 'CRM Lead'
				AND `from` IN ('Nicht kontaktiert', 'New')
			GROUP BY parent
		) sc ON sc.parent = l.name
		WHERE 1=1 {conds}
		""",
		params,
		as_dict=True,
	)
	avg_reaction_hours = round(float(avg_reaction[0].avg_hours or 0), 1) if avg_reaction else 0

	# No-show rate (termin_status = No-Show vs total appointments)
	noshow = frappe.db.sql(
		f"""
		SELECT
			SUM(CASE WHEN custom_termin_status = 'No-Show' THEN 1 ELSE 0 END) AS noshow_count,
			SUM(CASE WHEN custom_termin_datum IS NOT NULL THEN 1 ELSE 0 END) AS termin_total
		FROM `tabCRM Lead`
		WHERE custom_termin_datum IS NOT NULL
			{conds}
		""",
		params,
		as_dict=True,
	)
	noshow_count = int(noshow[0].noshow_count or 0) if noshow else 0
	termin_total = int(noshow[0].termin_total or 0) if noshow else 0
	noshow_rate = round(noshow_count / termin_total * 100, 1) if termin_total > 0 else 0

	return {
		"overdue_count": overdue_count,
		"avg_reaction_hours": avg_reaction_hours,
		"noshow_rate": noshow_rate,
		"noshow_count": noshow_count,
		"termin_total": termin_total,
	}


def _get_termin_stats(conds, params):
	"""Appointment status distribution.
	Returns: [{ status: 'Geplant', count: 5 }, ...]
	"""
	result = frappe.db.sql(
		f"""
		SELECT IFNULL(NULLIF(custom_termin_status, ''), 'Kein Status') AS status,
			   COUNT(*) AS count
		FROM `tabCRM Lead`
		WHERE custom_termin_datum IS NOT NULL
			{conds}
		GROUP BY status
		ORDER BY count DESC
		""",
		params,
		as_dict=True,
	)
	return [{"status": r.status, "count": r["count"]} for r in result]


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


@frappe.whitelist()
def get_sales_users():
	"""
	Returns list of users who own leads or deals.
	Only available for Sales Manager / System Manager.
	"""
	roles = frappe.get_roles(frappe.session.user)
	is_manager = "Sales Manager" in roles or "System Manager" in roles

	if not is_manager:
		return []

	users = frappe.db.sql("""
		SELECT DISTINCT u.name AS email, u.full_name
		FROM tabUser u
		WHERE u.enabled = 1
			AND u.name != 'Administrator'
			AND u.name != 'Guest'
			AND (
				EXISTS (SELECT 1 FROM `tabCRM Lead` l WHERE l.lead_owner = u.name)
				OR EXISTS (SELECT 1 FROM `tabCRM Deal` d WHERE d.deal_owner = u.name)
			)
		ORDER BY u.full_name
	""", as_dict=True)
	return users


@frappe.whitelist()
def get_team_performance(period="month", user=""):
	"""
	Team performance metrics per user.
	period: week | month | quarter | year
	user: optional email to filter to a single user
	Returns: { users: [...], period: str }
	"""
	roles = frappe.get_roles(frappe.session.user)
	is_manager = "Sales Manager" in roles or "System Manager" in roles

	if not is_manager:
		frappe.throw(_("Nur fuer Sales Manager / System Manager verfuegbar"), frappe.PermissionError)

	from_date, to_date = _get_period_dates(period)

	users = _get_team_users(user)

	results = []
	for u in users:
		metrics = _calc_user_metrics(u["email"], from_date, to_date)
		metrics["email"] = u["email"]
		metrics["full_name"] = u["full_name"] or u["email"]
		metrics["user_image"] = u.get("user_image") or None
		results.append(metrics)

	results.sort(key=lambda x: (-x["abschluesse_gewonnen"], -x["leads_total"]))

	return {
		"users": results,
		"period": period,
		"from_date": str(from_date),
		"to_date": str(to_date),
	}


def _get_period_dates(period):
	"""Calculate from_date and to_date based on period string."""
	import datetime
	today = frappe.utils.today()
	today_dt = frappe.utils.getdate(today)

	if period == "week":
		from_date = today_dt - datetime.timedelta(days=today_dt.weekday())
		to_date = from_date + datetime.timedelta(days=6)
	elif period == "quarter":
		quarter = (today_dt.month - 1) // 3
		from_date = datetime.date(today_dt.year, quarter * 3 + 1, 1)
		if quarter == 3:
			to_date = datetime.date(today_dt.year, 12, 31)
		else:
			to_date = datetime.date(today_dt.year, (quarter + 1) * 3 + 1, 1) - datetime.timedelta(days=1)
	elif period == "year":
		from_date = datetime.date(today_dt.year, 1, 1)
		to_date = datetime.date(today_dt.year, 12, 31)
	else:
		from_date = frappe.utils.get_first_day(today)
		to_date = frappe.utils.get_last_day(today)

	return str(from_date), str(to_date)


def _get_team_users(user_filter=""):
	"""Get list of users who own leads."""
	if user_filter:
		u = frappe.db.get_value("User", user_filter, ["name as email", "full_name", "user_image"], as_dict=True)
		return [u] if u else []

	users = frappe.db.sql("""
		SELECT DISTINCT u.name AS email, u.full_name, u.user_image
		FROM tabUser u
		WHERE u.enabled = 1
			AND u.name != 'Administrator'
			AND u.name != 'Guest'
			AND (
				EXISTS (SELECT 1 FROM `tabCRM Lead` l WHERE l.lead_owner = u.name)
				OR EXISTS (SELECT 1 FROM `tabCRM Deal` d WHERE d.deal_owner = u.name)
			)
		ORDER BY u.full_name
	""", as_dict=True)
	return users


def _calc_user_metrics(email, from_date, to_date):
	"""Calculate all metrics for a single user within date range."""
	params = {"user": email, "from_date": from_date, "to_date": to_date}
	today = frappe.utils.today()

	leads_total = frappe.db.sql(
		"SELECT COUNT(*) AS cnt FROM `tabCRM Lead` WHERE lead_owner = %(user)s",
		params, as_dict=True
	)[0].cnt or 0

	leads_new = frappe.db.sql(
		"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
		WHERE lead_owner = %(user)s
			AND DATE(creation) BETWEEN %(from_date)s AND %(to_date)s""",
		params, as_dict=True
	)[0].cnt or 0

	termine_gebucht = frappe.db.sql(
		"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
		WHERE lead_owner = %(user)s
			AND custom_termin_datum BETWEEN %(from_date)s AND %(to_date)s""",
		params, as_dict=True
	)[0].cnt or 0

	termine_durchgefuehrt = frappe.db.sql(
		"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
		WHERE lead_owner = %(user)s
			AND custom_termin_status = 'Durchgefuehrt'
			AND custom_termin_datum BETWEEN %(from_date)s AND %(to_date)s""",
		params, as_dict=True
	)[0].cnt or 0

	abschluesse_gewonnen = frappe.db.sql(
		"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
		WHERE lead_owner = %(user)s
			AND custom_liste = '80 - Abschluss gewonnen'
			AND custom_abschluss_datum BETWEEN %(from_date)s AND %(to_date)s""",
		params, as_dict=True
	)[0].cnt or 0

	abschluesse_verloren = frappe.db.sql(
		"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
		WHERE lead_owner = %(user)s
			AND custom_liste = '90 - Abschluss verloren'
			AND custom_abschluss_datum BETWEEN %(from_date)s AND %(to_date)s""",
		params, as_dict=True
	)[0].cnt or 0

	total_closed = abschluesse_gewonnen + abschluesse_verloren
	conversion_rate = round(abschluesse_gewonnen / total_closed * 100, 1) if total_closed > 0 else 0

	avg_resp = frappe.db.sql(
		"""SELECT AVG(TIMESTAMPDIFF(HOUR, l.creation, sc.first_change)) AS avg_hours
		FROM `tabCRM Lead` l
		JOIN (
			SELECT parent, MIN(to_date) AS first_change
			FROM `tabCRM Status Change Log`
			WHERE parenttype = 'CRM Lead'
				AND `from` IN ('Nicht kontaktiert', 'New')
				AND `to` NOT IN ('Nicht kontaktiert', 'New')
			GROUP BY parent
		) sc ON sc.parent = l.name
		WHERE l.lead_owner = %(user)s
			AND DATE(l.creation) BETWEEN %(from_date)s AND %(to_date)s""",
		params, as_dict=True
	)
	avg_response_time = round(float(avg_resp[0].avg_hours or 0), 1) if avg_resp and avg_resp[0].avg_hours else 0

	followup_overdue = frappe.db.sql(
		"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
		WHERE lead_owner = %(user)s
			AND custom_naechster_kontakt < %(today)s
			AND custom_naechster_kontakt IS NOT NULL
			AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')""",
		{**params, "today": today}, as_dict=True
	)[0].cnt or 0

	cross_sell_total = frappe.db.sql(
		"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
		WHERE lead_owner = %(user)s
			AND custom_cross_sell_prio1_produkt IS NOT NULL
			AND custom_cross_sell_prio1_produkt != ''""",
		params, as_dict=True
	)[0].cnt or 0

	cross_sell_done = frappe.db.sql(
		"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
		WHERE lead_owner = %(user)s
			AND custom_cross_sell_prio1_status = 'Angesprochen'
			AND custom_cross_sell_prio1_produkt IS NOT NULL
			AND custom_cross_sell_prio1_produkt != ''""",
		params, as_dict=True
	)[0].cnt or 0

	cross_sell_rate = round(cross_sell_done / cross_sell_total * 100, 1) if cross_sell_total > 0 else 0

	revenue = frappe.db.sql(
		"""SELECT
			IFNULL(SUM(custom_abschluss_beitrag), 0) AS beitrag,
			IFNULL(SUM(custom_abschluss_provision), 0) AS provision
		FROM `tabCRM Lead`
		WHERE lead_owner = %(user)s
			AND custom_liste = '80 - Abschluss gewonnen'
			AND custom_abschluss_datum BETWEEN %(from_date)s AND %(to_date)s""",
		params, as_dict=True
	)
	beitrag = float(revenue[0].beitrag) if revenue else 0
	provision = float(revenue[0].provision) if revenue else 0

	return {
		"leads_total": leads_total,
		"leads_new": leads_new,
		"termine_gebucht": termine_gebucht,
		"termine_durchgefuehrt": termine_durchgefuehrt,
		"abschluesse_gewonnen": abschluesse_gewonnen,
		"abschluesse_verloren": abschluesse_verloren,
		"conversion_rate": conversion_rate,
		"avg_response_time": avg_response_time,
		"followup_overdue": followup_overdue,
		"cross_sell_rate": cross_sell_rate,
		"beitrag": beitrag,
		"provision": provision,
	}


@frappe.whitelist()
def get_mein_tag_data():
    """
    Personal dashboard data for the current user.
    Returns: {
        today_tasks: { by_phase: [...], total: int },
        personal_kpis: { leads_today, leads_week, termine_today, abschluesse_week },
        overdue_followups: [...],
        praemien_summary: { quartal_total, last_praemien: [...] },
        gamification: { daily_points, daily_target, streak, badges_recent: [...] }
    }
    """
    import datetime

    user = frappe.session.user
    today_str = frappe.utils.today()
    today_dt = frappe.utils.getdate(today_str)

    # Week boundaries (Monday to Sunday)
    week_start = today_dt - datetime.timedelta(days=today_dt.weekday())
    week_end = week_start + datetime.timedelta(days=6)

    # Quarter boundaries
    quarter = (today_dt.month - 1) // 3
    quarter_start = datetime.date(today_dt.year, quarter * 3 + 1, 1)
    if quarter == 3:
        quarter_end = datetime.date(today_dt.year, 12, 31)
    else:
        quarter_end = datetime.date(today_dt.year, (quarter + 1) * 3 + 1, 1) - datetime.timedelta(days=1)

    # --- Today's Tasks: Leads by Phase ---
    phase_config = [
        {"phase": "10 - Neu ohne Termin", "color": "#6B7280", "short": "10 Neu"},
        {"phase": "20 - Termin gebucht", "color": "#3B82F6", "short": "20 Termin"},
        {"phase": "30 - Reaktivierung", "color": "#F59E0B", "short": "30 Reaktiv."},
        {"phase": "50 - Closer-Termin", "color": "#8B5CF6", "short": "50 Closer"},
        {"phase": "70 - Follow-up", "color": "#F97316", "short": "70 Follow-up"},
    ]

    by_phase = frappe.db.sql("""
        SELECT custom_liste AS phase, COUNT(*) AS count
        FROM `tabCRM Lead`
        WHERE lead_owner = %(user)s
          AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
          AND custom_liste IS NOT NULL AND custom_liste != ''
        GROUP BY custom_liste
        ORDER BY custom_liste
    """, {"user": user}, as_dict=True)

    phase_map = {r.phase: r["count"] for r in by_phase}
    today_tasks = []
    total_open = 0
    for pc in phase_config:
        cnt = phase_map.get(pc["phase"], 0)
        total_open += cnt
        today_tasks.append({
            "phase": pc["phase"],
            "short": pc["short"],
            "color": pc["color"],
            "count": cnt,
        })

    # --- Personal KPIs ---
    leads_today = frappe.db.sql(
        """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE lead_owner = %(user)s AND DATE(creation) = %(today)s""",
        {"user": user, "today": today_str}, as_dict=True
    )[0].cnt or 0

    leads_week = frappe.db.sql(
        """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE lead_owner = %(user)s
          AND DATE(creation) BETWEEN %(start)s AND %(end)s""",
        {"user": user, "start": str(week_start), "end": str(week_end)}, as_dict=True
    )[0].cnt or 0

    termine_today = frappe.db.sql(
        """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE lead_owner = %(user)s
          AND custom_termin_datum = %(today)s""",
        {"user": user, "today": today_str}, as_dict=True
    )[0].cnt or 0

    termine_week = frappe.db.sql(
        """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE lead_owner = %(user)s
          AND custom_termin_datum BETWEEN %(start)s AND %(end)s""",
        {"user": user, "start": str(week_start), "end": str(week_end)}, as_dict=True
    )[0].cnt or 0

    abschluesse_week = frappe.db.sql(
        """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE lead_owner = %(user)s
          AND custom_liste = '80 - Abschluss gewonnen'
          AND custom_abschluss_datum BETWEEN %(start)s AND %(end)s""",
        {"user": user, "start": str(week_start), "end": str(week_end)}, as_dict=True
    )[0].cnt or 0

    abschluesse_today = frappe.db.sql(
        """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE lead_owner = %(user)s
          AND custom_liste = '80 - Abschluss gewonnen'
          AND custom_abschluss_datum = %(today)s""",
        {"user": user, "today": today_str}, as_dict=True
    )[0].cnt or 0

    # --- Overdue Follow-ups ---
    overdue_followups = frappe.db.sql(
        """SELECT name, lead_name, first_name, custom_liste, custom_naechster_kontakt,
                  custom_followup_grund, custom_kontaktversuche
        FROM `tabCRM Lead`
        WHERE lead_owner = %(user)s
          AND custom_naechster_kontakt < %(today)s
          AND custom_naechster_kontakt IS NOT NULL
          AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
        ORDER BY custom_naechster_kontakt ASC
        LIMIT 20""",
        {"user": user, "today": today_str}, as_dict=True
    )

    # --- Upcoming Follow-ups (today) ---
    today_followups = frappe.db.sql(
        """SELECT name, lead_name, first_name, custom_liste, custom_naechster_kontakt,
                  custom_followup_grund
        FROM `tabCRM Lead`
        WHERE lead_owner = %(user)s
          AND custom_naechster_kontakt = %(today)s
          AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
        ORDER BY custom_naechster_kontakt ASC
        LIMIT 10""",
        {"user": user, "today": today_str}, as_dict=True
    )

    # --- Praemien Summary (this quarter) ---
    praemien_quartal = frappe.db.sql(
        """SELECT IFNULL(SUM(custom_veredelungspraemie), 0) AS total,
                  COUNT(*) AS count
        FROM `tabCRM Lead`
        WHERE lead_owner = %(user)s
          AND custom_veredelungspraemie > 0
          AND custom_praemie_status IN ('Berechnet', 'Ausgezahlt')
          AND custom_abschluss_datum BETWEEN %(q_start)s AND %(q_end)s
        """,
        {"user": user, "q_start": str(quarter_start), "q_end": str(quarter_end)},
        as_dict=True,
    )

    last_praemien = frappe.db.sql(
        """SELECT name, lead_name, custom_veredelungspraemie AS betrag,
                  custom_praemie_status AS status,
                  custom_spezialist_typ AS typ,
                  custom_abschluss_datum AS datum
        FROM `tabCRM Lead`
        WHERE lead_owner = %(user)s
          AND custom_veredelungspraemie > 0
          AND custom_praemie_status IN ('Berechnet', 'Ausgezahlt')
        ORDER BY datum DESC
        LIMIT 5""",
        {"user": user}, as_dict=True,
    )

    # --- Gamification (light) ---
    gamification_data = {}
    try:
        today_period = str(frappe.utils.getdate(today_str))
        daily_score = frappe.db.get_value(
            "CRM Gamification Score",
            {"user": user, "score_type": "daily_points", "period": today_period},
            ["points", "current_streak", "erstkontakt_count", "followup_count",
             "showrate_count", "weiterleitung_count"],
            as_dict=True,
        )

        total_score = frappe.db.get_value(
            "CRM Gamification Score",
            {"user": user, "score_type": "total_points", "period": "ALL"},
            ["best_streak"],
            as_dict=True,
        )

        recent_badges = frappe.get_all(
            "CRM Badge",
            filters={"user": user},
            fields=["badge_id", "badge_name", "badge_icon", "awarded_at"],
            order_by="awarded_at desc",
            limit=3,
        )

        daily_points = (daily_score.points if daily_score else 0) or 0
        # Calculate a rough daily target: 5 leads created = 25 pts, 2 termine = 20 pts, 
        # 3 followups = 9 pts, small chance of close = ~5 pts => ~60 pts as target
        daily_target = 50

        # Actions completed today for progress
        actions_today = 0
        if daily_score:
            actions_today = (
                (daily_score.erstkontakt_count or 0) +
                (daily_score.followup_count or 0) +
                (daily_score.showrate_count or 0) +
                (daily_score.weiterleitung_count or 0)
            )

        gamification_data = {
            "daily_points": daily_points,
            "daily_target": daily_target,
            "progress_pct": min(round(daily_points / daily_target * 100), 100) if daily_target > 0 else 0,
            "actions_today": actions_today,
            "streak_current": (daily_score.current_streak if daily_score else 0) or 0,
            "streak_best": (total_score.best_streak if total_score else 0) or 0,
            "badges_recent": recent_badges,
        }
    except Exception:
        gamification_data = {
            "daily_points": 0,
            "daily_target": 60,
            "progress_pct": 0,
            "actions_today": 0,
            "streak_current": 0,
            "streak_best": 0,
            "badges_recent": [],
        }

    return {
        "today_tasks": {
            "by_phase": today_tasks,
            "total": total_open,
        },
        "personal_kpis": {
            "leads_today": leads_today,
            "leads_week": leads_week,
            "termine_today": termine_today,
            "termine_week": termine_week,
            "abschluesse_today": abschluesse_today,
            "abschluesse_week": abschluesse_week,
        },
        "overdue_followups": overdue_followups,
        "today_followups": today_followups,
        "praemien_summary": {
            "quartal_total": float(praemien_quartal[0].total) if praemien_quartal else 0,
            "quartal_count": int(praemien_quartal[0]["count"]) if praemien_quartal else 0,
            "last_praemien": last_praemien,
        },
        "gamification": gamification_data,
    }


# ═══════════════════════════════════════════════════════════════════════
# KPI-SYSTEM: Erweiterte KPI-Berechnungen fuer GL-Dashboard
# ═══════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_kpi_dashboard(user="", period="month"):
    """
    Berechnet umfassende KPIs fuer einen User oder alle User.
    Setzt sich zusammen aus:
      - Generelle KPIs (Leads, Termine, Abschluesse, Conversion)
      - Setter-KPIs (Terminquote, Kontaktversuche)
      - Closer-KPIs (Show-Rate, Abschlussquote, Cross-Selling)
    """
    import datetime

    roles = frappe.get_roles(frappe.session.user)
    is_manager = "Sales Manager" in roles or "System Manager" in roles

    # Non-managers only see their own data
    if not is_manager:
        user = frappe.session.user

    from_date, to_date = _get_period_dates(period)
    params = {"from_date": from_date, "to_date": to_date}
    user_cond = ""
    if user:
        user_cond = " AND lead_owner = %(user)s"
        params["user"] = user

    today = frappe.utils.today()

    # ── Generelle KPIs ─────────────────────────────────────────────
    leads_total = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE DATE(creation) BETWEEN %(from_date)s AND %(to_date)s {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    leads_neu = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE custom_liste = '10 - Neu ohne Termin'
          AND DATE(creation) BETWEEN %(from_date)s AND %(to_date)s {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    leads_mit_termin = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE custom_liste IN ('20 - Termin gebucht', '50 - Closer-Termin')
          AND custom_termin_datum BETWEEN %(from_date)s AND %(to_date)s {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    abschluesse_gewonnen = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE custom_liste = '80 - Abschluss gewonnen'
          AND custom_abschluss_datum BETWEEN %(from_date)s AND %(to_date)s {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    abschluesse_verloren = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE custom_liste = '90 - Abschluss verloren'
          AND custom_abschluss_datum BETWEEN %(from_date)s AND %(to_date)s {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    total_closed = abschluesse_gewonnen + abschluesse_verloren
    conversion_rate = round(abschluesse_gewonnen / total_closed * 100, 1) if total_closed > 0 else 0.0

    # Durchschnittliche Reaktionszeit (Stunden): creation -> erster Status-Wechsel
    avg_resp = frappe.db.sql(
        f"""SELECT AVG(TIMESTAMPDIFF(HOUR, l.creation, sc.first_change)) AS avg_hours
        FROM `tabCRM Lead` l
        JOIN (
            SELECT parent, MIN(to_date) AS first_change
            FROM `tabCRM Status Change Log`
            WHERE parenttype = 'CRM Lead'
              AND `from` IN ('Nicht kontaktiert', 'New')
              AND `to` NOT IN ('Nicht kontaktiert', 'New')
            GROUP BY parent
        ) sc ON sc.parent = l.name
        WHERE DATE(l.creation) BETWEEN %(from_date)s AND %(to_date)s {user_cond}""",
        params, as_dict=True
    )
    durchschnittliche_reaktionszeit = round(float(avg_resp[0].avg_hours or 0), 1) if avg_resp and avg_resp[0].avg_hours else 0.0

    # Follow-up Disziplin: % der Follow-ups die puenktlich bearbeitet wurden
    # "puenktlich" = naechster_kontakt lag in der Vergangenheit UND Lead wurde danach aktualisiert
    followup_total_period = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE custom_naechster_kontakt BETWEEN %(from_date)s AND %(to_date)s
          AND custom_naechster_kontakt IS NOT NULL
          AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
          {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    followup_on_time = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE custom_naechster_kontakt BETWEEN %(from_date)s AND %(to_date)s
          AND custom_naechster_kontakt IS NOT NULL
          AND custom_letzter_kontakt IS NOT NULL
          AND custom_letzter_kontakt >= custom_naechster_kontakt
          AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
          {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    follow_up_disziplin = round(followup_on_time / followup_total_period * 100, 1) if followup_total_period > 0 else 0.0

    # Offene (ueberfaellige) Follow-ups
    offene_followups = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE custom_naechster_kontakt < %(today)s
          AND custom_naechster_kontakt IS NOT NULL
          AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
          {user_cond}""",
        {**params, "today": today}, as_dict=True
    )[0].cnt or 0

    # ── Setter-KPIs ────────────────────────────────────────────────
    # Terminquote: % der Leads die einen Termin bekommen haben
    leads_created_period = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE DATE(creation) BETWEEN %(from_date)s AND %(to_date)s {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    leads_with_termin = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE DATE(creation) BETWEEN %(from_date)s AND %(to_date)s
          AND custom_termin_datum IS NOT NULL {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    terminquote = round(leads_with_termin / leads_created_period * 100, 1) if leads_created_period > 0 else 0.0

    # Durchschnittliche Kontaktversuche
    avg_kontakt = frappe.db.sql(
        f"""SELECT AVG(IFNULL(custom_kontaktversuche, 0)) AS avg_val FROM `tabCRM Lead`
        WHERE DATE(creation) BETWEEN %(from_date)s AND %(to_date)s
          AND custom_kontaktversuche > 0 {user_cond}""",
        params, as_dict=True
    )
    kontaktversuche_avg = round(float(avg_kontakt[0].avg_val or 0), 1) if avg_kontakt and avg_kontakt[0].avg_val else 0.0

    # ── Closer-KPIs ───────────────────────────────────────────────
    # Show-Rate: % Termine "Durchgefuehrt" vs total
    termine_total = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE custom_termin_datum BETWEEN %(from_date)s AND %(to_date)s
          AND custom_termin_datum IS NOT NULL {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    termine_durchgefuehrt = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE custom_termin_datum BETWEEN %(from_date)s AND %(to_date)s
          AND custom_termin_status = 'Durchgeführt' {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    show_rate = round(termine_durchgefuehrt / termine_total * 100, 1) if termine_total > 0 else 0.0

    # Abschlussquote: gewonnen / durchgefuehrte Termine
    abschlussquote = round(abschluesse_gewonnen / termine_durchgefuehrt * 100, 1) if termine_durchgefuehrt > 0 else 0.0

    # Cross-Selling Quote: % der Leads mit mindestens 1 Cross-Sell "Angesprochen"
    cross_sell_total = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE custom_cross_sell_prio1_produkt IS NOT NULL
          AND custom_cross_sell_prio1_produkt != ''
          AND DATE(creation) BETWEEN %(from_date)s AND %(to_date)s {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    cross_sell_done = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE custom_cross_sell_prio1_status = 'Angesprochen'
          AND custom_cross_sell_prio1_produkt IS NOT NULL
          AND custom_cross_sell_prio1_produkt != ''
          AND DATE(creation) BETWEEN %(from_date)s AND %(to_date)s {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    cross_selling_quote = round(cross_sell_done / cross_sell_total * 100, 1) if cross_sell_total > 0 else 0.0

    # Weiterleitungen (qualifizierte Referrals)
    try:
        weiterleitungen = frappe.db.sql(
            f"""SELECT COUNT(*) AS cnt FROM `tabCRM Referral`
            WHERE custom_referral_status = 'Qualifiziert'
              AND DATE(creation) BETWEEN %(from_date)s AND %(to_date)s
              {"AND referrer_user = %(user)s" if user else ""}""",
            params, as_dict=True
        )[0].cnt or 0
    except Exception:
        weiterleitungen = 0

    return {
        "general": {
            "leads_total": leads_total,
            "leads_neu": leads_neu,
            "leads_mit_termin": leads_mit_termin,
            "abschluesse_gewonnen": abschluesse_gewonnen,
            "abschluesse_verloren": abschluesse_verloren,
            "conversion_rate": conversion_rate,
            "durchschnittliche_reaktionszeit": durchschnittliche_reaktionszeit,
            "follow_up_disziplin": follow_up_disziplin,
            "offene_followups": offene_followups,
        },
        "setter": {
            "terminquote": terminquote,
            "kontaktversuche_avg": kontaktversuche_avg,
        },
        "closer": {
            "show_rate": show_rate,
            "abschlussquote": abschlussquote,
            "cross_selling_quote": cross_selling_quote,
            "weiterleitungen": weiterleitungen,
        },
        "period": period,
        "from_date": from_date,
        "to_date": to_date,
        "user": user or "Alle",
    }


@frappe.whitelist()
def get_funnel_data(period="month"):
    """
    Gibt Funnel-Daten fuer die Pipeline-Phasen zurueck.
    Zeigt die Verteilung aller Leads ueber die Phasen und Conversion-Raten.
    """
    from_date, to_date = _get_period_dates(period)

    roles = frappe.get_roles(frappe.session.user)
    is_manager = "Sales Manager" in roles or "System Manager" in roles

    user_cond = ""
    params = {"from_date": from_date, "to_date": to_date}
    if not is_manager:
        user_cond = " AND lead_owner = %(user)s"
        params["user"] = frappe.session.user

    # Gesamtzahl der Leads im Zeitraum (nach Erstelldatum)
    total_leads = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE DATE(creation) BETWEEN %(from_date)s AND %(to_date)s {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    # Alle Leads die jemals in einer Phase waren (aktueller Stand)
    total_all = frappe.db.sql(
        f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
        WHERE 1=1 {user_cond}""",
        params, as_dict=True
    )[0].cnt or 0

    phase_config = [
        {"phase": "10 - Neu ohne Termin", "label": "10 - Neu", "color": "#6B7280"},
        {"phase": "20 - Termin gebucht", "label": "20 - Termin", "color": "#3B82F6"},
        {"phase": "30 - Reaktivierung", "label": "30 - Reaktiv.", "color": "#F59E0B"},
        {"phase": "50 - Closer-Termin", "label": "50 - Closer", "color": "#8B5CF6"},
        {"phase": "70 - Follow-up", "label": "70 - Follow-up", "color": "#F97316"},
        {"phase": "80 - Abschluss gewonnen", "label": "80 - Gewonnen", "color": "#10B981"},
        {"phase": "90 - Abschluss verloren", "label": "90 - Verloren", "color": "#EF4444"},
    ]

    phases = []
    phase_counts = {}
    for pc in phase_config:
        cnt = frappe.db.sql(
            f"""SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
            WHERE custom_liste = %(phase)s {user_cond}""",
            {**params, "phase": pc["phase"]}, as_dict=True
        )[0].cnt or 0
        pct = round(cnt / total_all * 100, 1) if total_all > 0 else 0.0
        phases.append({
            "phase": pc["label"],
            "full_phase": pc["phase"],
            "count": cnt,
            "percentage": pct,
            "color": pc["color"],
        })
        phase_counts[pc["phase"]] = cnt

    # Conversion-Raten
    c10 = phase_counts.get("10 - Neu ohne Termin", 0)
    c20 = phase_counts.get("20 - Termin gebucht", 0)
    c50 = phase_counts.get("50 - Closer-Termin", 0)
    c80 = phase_counts.get("80 - Abschluss gewonnen", 0)
    c90 = phase_counts.get("90 - Abschluss verloren", 0)

    conversion_10_to_20 = round((c20 + c50) / total_all * 100, 1) if total_all > 0 else 0.0
    conversion_20_to_80 = round(c80 / (c20 + c50) * 100, 1) if (c20 + c50) > 0 else 0.0
    overall_conversion = round(c80 / total_all * 100, 1) if total_all > 0 else 0.0

    return {
        "phases": phases,
        "conversion_10_to_20": conversion_10_to_20,
        "conversion_20_to_80": conversion_20_to_80,
        "overall_conversion": overall_conversion,
        "total_leads": total_all,
        "leads_im_zeitraum": total_leads,
        "period": period,
    }


@frappe.whitelist()
def get_team_overview(period="month"):
    """
    Gibt Team-Performance mit Warnungen zurueck (nur fuer System Manager / GF).
    Enthaelt pro User: Leads, Abschluesse, Quoten, Reaktionszeit.
    Plus: Fruehwarnsystem mit Warnungen.
    """
    roles = frappe.get_roles(frappe.session.user)
    is_manager = "Sales Manager" in roles or "System Manager" in roles

    if not is_manager:
        frappe.throw(_("Nur fuer System Manager / Sales Manager verfuegbar"), frappe.PermissionError)

    from_date, to_date = _get_period_dates(period)
    today = frappe.utils.today()

    users = _get_team_users()
    results = []
    total_overdue = 0

    for u in users:
        email = u["email"]
        params = {"user": email, "from_date": from_date, "to_date": to_date, "today": today}

        leads_total = frappe.db.sql(
            """SELECT COUNT(*) AS cnt FROM `tabCRM Lead` WHERE lead_owner = %(user)s""",
            params, as_dict=True
        )[0].cnt or 0

        leads_new_period = frappe.db.sql(
            """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
            WHERE lead_owner = %(user)s AND DATE(creation) BETWEEN %(from_date)s AND %(to_date)s""",
            params, as_dict=True
        )[0].cnt or 0

        leads_gewonnen = frappe.db.sql(
            """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
            WHERE lead_owner = %(user)s
              AND custom_liste = '80 - Abschluss gewonnen'
              AND custom_abschluss_datum BETWEEN %(from_date)s AND %(to_date)s""",
            params, as_dict=True
        )[0].cnt or 0

        leads_verloren = frappe.db.sql(
            """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
            WHERE lead_owner = %(user)s
              AND custom_liste = '90 - Abschluss verloren'
              AND custom_abschluss_datum BETWEEN %(from_date)s AND %(to_date)s""",
            params, as_dict=True
        )[0].cnt or 0

        offene_leads = frappe.db.sql(
            """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
            WHERE lead_owner = %(user)s
              AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')""",
            params, as_dict=True
        )[0].cnt or 0

        offene_followups_user = frappe.db.sql(
            """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
            WHERE lead_owner = %(user)s
              AND custom_naechster_kontakt < %(today)s
              AND custom_naechster_kontakt IS NOT NULL
              AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')""",
            params, as_dict=True
        )[0].cnt or 0

        total_overdue += offene_followups_user

        total_closed = leads_gewonnen + leads_verloren
        abschlussquote_user = round(leads_gewonnen / total_closed * 100, 1) if total_closed > 0 else 0.0

        # Reaktionszeit fuer diesen User
        avg_resp_user = frappe.db.sql(
            """SELECT AVG(TIMESTAMPDIFF(HOUR, l.creation, sc.first_change)) AS avg_hours
            FROM `tabCRM Lead` l
            JOIN (
                SELECT parent, MIN(to_date) AS first_change
                FROM `tabCRM Status Change Log`
                WHERE parenttype = 'CRM Lead'
                  AND `from` IN ('Nicht kontaktiert', 'New')
                  AND `to` NOT IN ('Nicht kontaktiert', 'New')
                GROUP BY parent
            ) sc ON sc.parent = l.name
            WHERE l.lead_owner = %(user)s
              AND DATE(l.creation) BETWEEN %(from_date)s AND %(to_date)s""",
            params, as_dict=True
        )
        avg_reaktionszeit_h = round(float(avg_resp_user[0].avg_hours or 0), 1) if avg_resp_user and avg_resp_user[0].avg_hours else 0.0

        # Terminquote
        termin_total_user = frappe.db.sql(
            """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
            WHERE lead_owner = %(user)s
              AND custom_termin_datum BETWEEN %(from_date)s AND %(to_date)s""",
            params, as_dict=True
        )[0].cnt or 0

        termin_done_user = frappe.db.sql(
            """SELECT COUNT(*) AS cnt FROM `tabCRM Lead`
            WHERE lead_owner = %(user)s
              AND custom_termin_status = 'Durchgeführt'
              AND custom_termin_datum BETWEEN %(from_date)s AND %(to_date)s""",
            params, as_dict=True
        )[0].cnt or 0

        show_rate_user = round(termin_done_user / termin_total_user * 100, 1) if termin_total_user > 0 else 0.0

        results.append({
            "user": email,
            "full_name": u["full_name"] or email,
            "user_image": u.get("user_image") or None,
            "leads_total": leads_total,
            "leads_neu": leads_new_period,
            "leads_gewonnen": leads_gewonnen,
            "leads_verloren": leads_verloren,
            "offene_leads": offene_leads,
            "offene_followups": offene_followups_user,
            "abschlussquote": abschlussquote_user,
            "avg_reaktionszeit_h": avg_reaktionszeit_h,
            "termine_total": termin_total_user,
            "termine_durchgefuehrt": termin_done_user,
            "show_rate": show_rate_user,
        })

    # Sortierung: meiste Abschluesse zuerst
    results.sort(key=lambda x: (-x["leads_gewonnen"], -x["leads_total"]))

    # ── Warnungen (Fruehwarnsystem) ────────────────────────────────
    warnings = []

    # 1) Gesamte ueberfaellige Follow-ups
    if total_overdue > 5:
        warnings.append({
            "type": "followup_stau",
            "message": f"{total_overdue} Follow-ups überfällig",
            "severity": "danger" if total_overdue > 15 else "warning",
            "icon": "alert-circle",
        })

    # 2) Durchschnittliche Reaktionszeit Team
    avg_resp_all = frappe.db.sql(
        """SELECT AVG(TIMESTAMPDIFF(HOUR, l.creation, sc.first_change)) AS avg_hours
        FROM `tabCRM Lead` l
        JOIN (
            SELECT parent, MIN(to_date) AS first_change
            FROM `tabCRM Status Change Log`
            WHERE parenttype = 'CRM Lead'
              AND `from` IN ('Nicht kontaktiert', 'New')
              AND `to` NOT IN ('Nicht kontaktiert', 'New')
            GROUP BY parent
        ) sc ON sc.parent = l.name
        WHERE DATE(l.creation) BETWEEN %(from_date)s AND %(to_date)s""",
        {"from_date": from_date, "to_date": to_date}, as_dict=True
    )
    team_avg_resp = round(float(avg_resp_all[0].avg_hours or 0), 1) if avg_resp_all and avg_resp_all[0].avg_hours else 0.0

    if team_avg_resp > 4:
        warnings.append({
            "type": "reaktionszeit",
            "message": f"Durchschnittliche Reaktionszeit {team_avg_resp}h (Ziel: < 4h)",
            "severity": "danger" if team_avg_resp > 8 else "warning",
            "icon": "clock",
        })
    elif team_avg_resp > 2:
        warnings.append({
            "type": "reaktionszeit",
            "message": f"Reaktionszeit {team_avg_resp}h - Achtung",
            "severity": "info",
            "icon": "clock",
        })

    # 3) Show-Rate Einbruch
    global_termine = frappe.db.sql(
        """SELECT
            SUM(CASE WHEN custom_termin_status = 'Durchgeführt' THEN 1 ELSE 0 END) AS done,
            COUNT(*) AS total
        FROM `tabCRM Lead`
        WHERE custom_termin_datum BETWEEN %(from_date)s AND %(to_date)s
          AND custom_termin_datum IS NOT NULL""",
        {"from_date": from_date, "to_date": to_date}, as_dict=True
    )
    if global_termine and global_termine[0].total and global_termine[0].total > 0:
        global_show_rate = round(int(global_termine[0].done or 0) / int(global_termine[0].total) * 100, 1)
        if global_show_rate < 60:
            warnings.append({
                "type": "show_rate",
                "message": f"Show-Rate nur {global_show_rate}% (Ziel: > 70%)",
                "severity": "danger" if global_show_rate < 40 else "warning",
                "icon": "user-x",
            })

    # 4) User mit vielen ueberfaelligen Follow-ups
    for u in results:
        if u["offene_followups"] > 5:
            warnings.append({
                "type": "user_followup",
                "message": f"{u['full_name']}: {u['offene_followups']} überfällige Follow-ups",
                "severity": "warning",
                "icon": "alert-triangle",
            })

    # 5) User mit langer Reaktionszeit
    for u in results:
        if u["avg_reaktionszeit_h"] > 8:
            warnings.append({
                "type": "user_reaktionszeit",
                "message": f"{u['full_name']}: Reaktionszeit {u['avg_reaktionszeit_h']}h",
                "severity": "danger",
                "icon": "clock",
            })

    return {
        "users": results,
        "warnings": warnings,
        "period": period,
        "from_date": from_date,
        "to_date": to_date,
        "team_avg_reaktionszeit": team_avg_resp,
        "total_overdue_followups": total_overdue,
    }
