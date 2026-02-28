"""
CRM Activity Tracking API
--------------------------
Provides endpoints for managing contact activities (CRM Tasks with activity metadata).
Used by the CRM frontend for follow-up tracking, contact logging, and overdue management.
"""
import frappe
from frappe import _
from frappe.utils import now, today, getdate, date_diff, add_days


@frappe.whitelist()
def get_activities_for_lead(lead_name, status=None, activity_type=None, limit=50):
    """Get all activity tasks for a specific lead.

    Args:
        lead_name: CRM Lead name (e.g. CRM-LEAD-2025-00001)
        status: Optional filter by custom_followup_status (Offen/Erledigt/Ueberfaellig)
        activity_type: Optional filter by custom_activity_type
        limit: Max results (default 50)

    Returns:
        List of CRM Task dicts with activity fields
    """
    if not frappe.db.exists("CRM Lead", lead_name):
        frappe.throw(_("Lead {0} nicht gefunden").format(lead_name), frappe.DoesNotExistError)

    filters = {
        "reference_doctype": "CRM Lead",
        "reference_docname": lead_name,
    }
    if status:
        filters["custom_followup_status"] = status
    if activity_type:
        filters["custom_activity_type"] = activity_type

    tasks = frappe.get_all("CRM Task",
        filters=filters,
        fields=[
            "name", "title", "description", "status", "priority",
            "assigned_to", "due_date", "creation", "modified",
            "custom_activity_type", "custom_contact_result",
            "custom_followup_status", "custom_duration_minutes",
            "custom_next_action", "custom_auto_created", "custom_lead_liste",
            "completed_at", "completed_by",
        ],
        order_by="creation desc",
        limit_page_length=int(limit),
    )

    # Enrich with user info
    for task in tasks:
        if task.assigned_to:
            user_info = frappe.db.get_value("User", task.assigned_to,
                ["full_name", "user_image"], as_dict=True)
            task["assigned_to_name"] = user_info.full_name if user_info else ""
            task["assigned_to_image"] = user_info.user_image if user_info else ""

        # Compute overdue flag
        if task.due_date and task.status not in ("Done", "Canceled"):
            task["is_overdue"] = getdate(task.due_date) < getdate(today())
        else:
            task["is_overdue"] = False

    return tasks


@frappe.whitelist()
def get_overdue_activities(user=None, limit=100):
    """Get all overdue activity tasks for a user.

    Args:
        user: User email (defaults to current user)
        limit: Max results (default 100)

    Returns:
        List of overdue CRM Task dicts with lead info
    """
    user = user or frappe.session.user

    tasks = frappe.db.sql("""
        SELECT
            t.name, t.title, t.description, t.status, t.priority,
            t.assigned_to, t.due_date, t.creation, t.modified,
            t.reference_docname AS lead_name,
            t.custom_activity_type, t.custom_contact_result,
            t.custom_followup_status, t.custom_duration_minutes,
            t.custom_next_action, t.custom_auto_created, t.custom_lead_liste,
            l.lead_name AS lead_display_name,
            l.custom_liste AS lead_current_phase,
            l.lead_owner AS lead_owner,
            l.mobile_no AS lead_mobile,
            u.full_name AS assigned_to_name
        FROM `tabCRM Task` t
        LEFT JOIN `tabCRM Lead` l ON t.reference_docname = l.name
            AND t.reference_doctype = 'CRM Lead'
        LEFT JOIN tabUser u ON t.assigned_to = u.name
        WHERE t.assigned_to = %(user)s
          AND t.status NOT IN ('Done', 'Canceled')
          AND t.due_date IS NOT NULL
          AND t.due_date < %(now)s
        ORDER BY t.due_date ASC
        LIMIT %(limit)s
    """, {"user": user, "now": now(), "limit": int(limit)}, as_dict=True)

    for task in tasks:
        task["is_overdue"] = True
        if task.due_date:
            task["days_overdue"] = date_diff(today(), task.due_date)

    return tasks


@frappe.whitelist()
def create_activity(lead_name, activity_type, title=None, description=None,
                    contact_result=None, duration_minutes=None, next_action=None,
                    due_date=None, assigned_to=None, priority="Medium"):
    """Create a new activity task for a lead.

    This is the main entry point for logging contact actions from the frontend.

    Args:
        lead_name: CRM Lead name
        activity_type: Anruf/WhatsApp/E-Mail/SMS/Besuch/Follow-up/Sonstiges
        title: Optional title (auto-generated if empty)
        description: Optional description/notes
        contact_result: Erreicht/Nicht erreicht/Mailbox/etc.
        duration_minutes: Duration of the contact in minutes
        next_action: Next planned action text
        due_date: Due date for follow-up tasks
        assigned_to: User to assign (defaults to current user)
        priority: Low/Medium/High (default Medium)

    Returns:
        Created CRM Task dict
    """
    if not frappe.db.exists("CRM Lead", lead_name):
        frappe.throw(_("Lead {0} nicht gefunden").format(lead_name), frappe.DoesNotExistError)

    valid_types = ["Anruf", "WhatsApp", "E-Mail", "SMS", "Besuch", "Follow-up", "Sonstiges"]
    if activity_type not in valid_types:
        frappe.throw(_("Ungueltiger Aktivitaetstyp: {0}").format(activity_type))

    # Auto-generate title if not provided
    if not title:
        lead_display = frappe.db.get_value("CRM Lead", lead_name, "lead_name") or lead_name
        title = f"{activity_type}: {lead_display}"

    assigned_to = assigned_to or frappe.session.user
    lead_liste = frappe.db.get_value("CRM Lead", lead_name, "custom_liste") or ""

    task = frappe.new_doc("CRM Task")
    task.title = title
    task.description = description or ""
    task.assigned_to = assigned_to
    task.priority = priority
    task.status = "Todo"
    task.reference_doctype = "CRM Lead"
    task.reference_docname = lead_name
    task.custom_activity_type = activity_type
    task.custom_contact_result = contact_result or ""
    task.custom_followup_status = "Offen"
    task.custom_duration_minutes = int(duration_minutes) if duration_minutes else 0
    task.custom_next_action = next_action or ""
    task.custom_auto_created = 0
    task.custom_lead_liste = lead_liste

    if due_date:
        task.due_date = due_date

    task.insert(ignore_permissions=True)
    frappe.db.commit()

    # Update lead contact tracking fields
    _update_lead_contact_tracking(lead_name, activity_type, contact_result)

    return task.as_dict()


@frappe.whitelist()
def complete_activity(task_name, contact_result=None, duration_minutes=None, next_action=None):
    """Mark an activity task as completed.

    Args:
        task_name: CRM Task name
        contact_result: Final contact result
        duration_minutes: Duration of the contact
        next_action: What to do next

    Returns:
        Updated CRM Task dict
    """
    if not frappe.db.exists("CRM Task", task_name):
        frappe.throw(_("Aufgabe {0} nicht gefunden").format(task_name), frappe.DoesNotExistError)

    task = frappe.get_doc("CRM Task", task_name)
    task.status = "Done"
    task.completed_at = now()
    task.completed_by = frappe.session.user
    task.custom_followup_status = "Erledigt"

    if contact_result:
        task.custom_contact_result = contact_result
    if duration_minutes:
        task.custom_duration_minutes = int(duration_minutes)
    if next_action:
        task.custom_next_action = next_action

    task.save(ignore_permissions=True)
    frappe.db.commit()

    # Update lead contact tracking
    if task.reference_doctype == "CRM Lead" and task.reference_docname:
        _update_lead_contact_tracking(
            task.reference_docname,
            task.custom_activity_type,
            contact_result
        )

    return task.as_dict()


@frappe.whitelist()
def get_activity_summary(lead_name):
    """Get activity summary/statistics for a lead.

    Args:
        lead_name: CRM Lead name

    Returns:
        Dict with activity counts by type and status
    """
    if not frappe.db.exists("CRM Lead", lead_name):
        frappe.throw(_("Lead {0} nicht gefunden").format(lead_name), frappe.DoesNotExistError)

    # Counts by activity type
    by_type = frappe.db.sql("""
        SELECT custom_activity_type AS activity_type, COUNT(*) AS count
        FROM `tabCRM Task`
        WHERE reference_doctype = 'CRM Lead'
          AND reference_docname = %(lead_name)s
          AND custom_activity_type IS NOT NULL
          AND custom_activity_type != ''
        GROUP BY custom_activity_type
        ORDER BY count DESC
    """, {"lead_name": lead_name}, as_dict=True)

    # Counts by followup status
    by_status = frappe.db.sql("""
        SELECT custom_followup_status AS followup_status, COUNT(*) AS count
        FROM `tabCRM Task`
        WHERE reference_doctype = 'CRM Lead'
          AND reference_docname = %(lead_name)s
          AND custom_followup_status IS NOT NULL
          AND custom_followup_status != ''
        GROUP BY custom_followup_status
    """, {"lead_name": lead_name}, as_dict=True)

    # Total contact duration
    total_duration = frappe.db.sql("""
        SELECT COALESCE(SUM(custom_duration_minutes), 0) AS total_minutes
        FROM `tabCRM Task`
        WHERE reference_doctype = 'CRM Lead'
          AND reference_docname = %(lead_name)s
          AND custom_duration_minutes > 0
    """, {"lead_name": lead_name}, as_dict=True)

    # Last activity date
    last_activity = frappe.db.sql("""
        SELECT MAX(creation) AS last_activity_date
        FROM `tabCRM Task`
        WHERE reference_doctype = 'CRM Lead'
          AND reference_docname = %(lead_name)s
    """, {"lead_name": lead_name}, as_dict=True)

    return {
        "by_type": by_type,
        "by_status": by_status,
        "total_contact_minutes": total_duration[0].total_minutes if total_duration else 0,
        "last_activity_date": last_activity[0].last_activity_date if last_activity else None,
        "total_activities": sum(t.get("count", 0) for t in by_type),
    }


def _update_lead_contact_tracking(lead_name, activity_type, contact_result=None):
    """Update lead contact tracking fields after an activity.

    Updates custom_letzter_kontakt, custom_letzte_kontaktart, custom_kontaktversuche.
    """
    try:
        lead = frappe.get_doc("CRM Lead", lead_name)

        # Map activity type to contact art
        kontaktart_map = {
            "Anruf": "Anruf",
            "WhatsApp": "WhatsApp",
            "E-Mail": "E-Mail",
            "SMS": "SMS",
            "Besuch": "Besuch",
        }
        kontaktart = kontaktart_map.get(activity_type, "")

        updates = {}
        if kontaktart:
            updates["custom_letzte_kontaktart"] = kontaktart
        updates["custom_letzter_kontakt"] = frappe.utils.now()

        # Increment contact attempts
        current_attempts = lead.custom_kontaktversuche or 0
        updates["custom_kontaktversuche"] = current_attempts + 1

        for field, value in updates.items():
            frappe.db.set_value("CRM Lead", lead_name, field, value, update_modified=False)

        frappe.db.commit()
    except Exception:
        frappe.log_error(f"Failed to update lead contact tracking for {lead_name}")
