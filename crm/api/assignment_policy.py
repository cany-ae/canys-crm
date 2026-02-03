import frappe
from frappe import _

# Role profiles recognized by the assignment policy.
# Only profiles managed by Mitarbeiterverwaltung app.
SALES_AGENT_PROFILES = ("Vertriebler",)
TEAM_LEAD_PROFILES = ("Teamleiter",)
EXECUTIVE_PROFILES = ("Geschäftsführer",)
ALL_CRM_PROFILES = SALES_AGENT_PROFILES + TEAM_LEAD_PROFILES + EXECUTIVE_PROFILES


def _normalize_profile(profile):
    """Map profile name to a canonical level for policy decisions."""
    if profile in SALES_AGENT_PROFILES:
        return "agent"
    elif profile in TEAM_LEAD_PROFILES:
        return "teamlead"
    elif profile in EXECUTIVE_PROFILES:
        return "executive"
    return None


def get_user_role_profile(user=None):
    """Get the role profile name for a user."""
    if not user:
        user = frappe.session.user
    return frappe.db.get_value("User", user, "role_profile_name")


def get_user_sales_team(user=None):
    """Get the sales team (MV Sales Team) for a user."""
    if not user:
        user = frappe.session.user
    return frappe.db.get_value("User", user, "sales_team")


def _is_system_manager(user=None):
    """Check if user has System Manager role."""
    if not user:
        user = frappe.session.user
    return "System Manager" in frappe.get_roles(user)


@frappe.whitelist()
def can_assign_to(target_user):
    """Check if current user can assign tasks to target_user.

    Returns True if allowed, throws frappe.PermissionError otherwise.

    Rules:
    - System Manager / Administrator: unrestricted
    - Vertriebler/Sales (agent): can only assign to self
    - Teamleiter (teamlead): can assign to agents in own MV Sales Team + self
    - Geschäftsführer (executive): can assign to any agent or teamlead + self
    """
    actor = frappe.session.user

    if actor == "Administrator" or _is_system_manager(actor):
        return True

    actor_profile = get_user_role_profile(actor)
    actor_level = _normalize_profile(actor_profile)

    if not actor_level:
        frappe.throw(
            _("Kein gültiges Role Profile zugewiesen. Bitte Admin kontaktieren."),
            frappe.PermissionError,
        )

    # Everyone can assign to self
    if target_user == actor:
        return True

    target_profile = get_user_role_profile(target_user)
    target_level = _normalize_profile(target_profile)

    if actor_level == "agent":
        frappe.throw(
            _("Vertriebler dürfen Aufgaben nur an sich selbst zuweisen."),
            frappe.PermissionError,
        )

    elif actor_level == "teamlead":
        if target_level != "agent":
            frappe.throw(
                _("Teamleiter dürfen Aufgaben nur an Vertriebler im eigenen Team zuweisen."),
                frappe.PermissionError,
            )

        actor_team = get_user_sales_team(actor)
        if not actor_team:
            frappe.throw(
                _("Teamleiter hat kein Sales Team zugewiesen. Bitte Admin kontaktieren."),
                frappe.ValidationError,
            )

        target_team = get_user_sales_team(target_user)
        if target_team != actor_team:
            frappe.throw(
                _("Zuweisung nur an Vertriebler im eigenen Team ({0}) erlaubt.").format(actor_team),
                frappe.PermissionError,
            )
        return True

    elif actor_level == "executive":
        if target_level not in ("agent", "teamlead", "executive"):
            frappe.throw(
                _("Zuweisung nur an Mitarbeiter der Mitarbeiterverwaltung erlaubt."),
                frappe.PermissionError,
            )
        return True

    frappe.throw(
        _("Keine Berechtigung für Aufgabenzuweisung."),
        frappe.PermissionError,
    )


@frappe.whitelist()
def get_assignable_users():
    """Return list of users the current user can assign tasks to.

    Returns:
        list[dict]: Each dict has name, full_name, role_profile_name, sales_team
    """
    actor = frappe.session.user
    base_filters = {"enabled": 1, "user_type": "System User"}
    fields = ["name", "full_name", "role_profile_name", "sales_team"]

    if actor == "Administrator" or _is_system_manager(actor):
        return frappe.get_all(
            "User",
            filters={
                **base_filters,
                "role_profile_name": ["in", list(ALL_CRM_PROFILES)],
            },
            fields=fields,
            order_by="full_name asc",
        )

    actor_profile = get_user_role_profile(actor)
    actor_level = _normalize_profile(actor_profile)

    if not actor_level:
        return []

    def _self_entry():
        doc = frappe.db.get_value("User", actor, ["full_name", "sales_team"], as_dict=True)
        return {
            "name": actor,
            "full_name": doc.full_name or actor,
            "role_profile_name": actor_profile,
            "sales_team": doc.sales_team or "",
        }

    if actor_level == "agent":
        return [_self_entry()]

    elif actor_level == "teamlead":
        actor_team = get_user_sales_team(actor)
        result = [_self_entry()]
        if actor_team:
            team_members = frappe.get_all(
                "User",
                filters={
                    **base_filters,
                    "role_profile_name": ["in", list(SALES_AGENT_PROFILES)],
                    "sales_team": actor_team,
                },
                fields=fields,
                order_by="full_name asc",
            )
            # Add team members, skip self if already present
            for m in team_members:
                if m["name"] != actor:
                    result.append(m)
        return result

    elif actor_level == "executive":
        result = [_self_entry()]
        subordinates = frappe.get_all(
            "User",
            filters={
                **base_filters,
                "role_profile_name": ["in", list(ALL_CRM_PROFILES)],
            },
            fields=fields,
            order_by="full_name asc",
        )
        for u in subordinates:
            if u["name"] != actor:
                result.append(u)
        return result

    return []


def validate_assignment(doc, method=None):
    """Hook: validate assignment on ToDo save.

    Called via doc_events on ToDo validate.
    Enforces the role-based assignment policy for CRM documents.
    """
    if not doc.allocated_to:
        return

    actor = frappe.session.user

    # Skip for Administrator and System Manager
    if actor == "Administrator" or _is_system_manager(actor):
        return

    # Only enforce for CRM-related assignments
    if doc.reference_type not in ("CRM Lead", "CRM Deal", "CRM Task"):
        return

    actor_profile = get_user_role_profile(actor)
    if not _normalize_profile(actor_profile):
        return

    can_assign_to(doc.allocated_to)
