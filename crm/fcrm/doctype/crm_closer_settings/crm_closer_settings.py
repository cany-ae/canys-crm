# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


SKILL_LEVEL_WEIGHT = {
    "Experte": 3,
    "Fortgeschritten": 2,
    "Basis": 1,
}


class CRMCloserSettings(Document):
    def validate(self):
        """Validate closer skills configuration."""
        seen = set()
        for skill in self.closer_skills:
            key = (skill.user, skill.leadtyp)
            if key in seen:
                frappe.throw(
                    f"Doppelter Eintrag: {skill.user} hat bereits einen Skill fuer {skill.leadtyp}. "
                    "Bitte nur einen Eintrag pro User+Leadtyp."
                )
            seen.add(key)

    def on_update(self):
        """Clear cached routing data when settings change."""
        frappe.cache().delete_key("crm_closer_skills")
        frappe.cache().delete_key("crm_closer_settings")


def get_closer_settings():
    """Return closer settings (cached)."""
    cached = frappe.cache().get_value("crm_closer_settings")
    if cached:
        return cached

    try:
        settings = frappe.get_single("CRM Closer Settings")
        result = {
            "routing_mode": settings.routing_mode or "Skill-basiert",
            "max_open_leads_per_closer": settings.max_open_leads_per_closer or 20,
            "fallback_to_roundrobin": settings.fallback_to_roundrobin,
        }
        frappe.cache().set_value("crm_closer_settings", result, expires_in_sec=120)
        return result
    except Exception:
        return {
            "routing_mode": "Round-Robin",
            "max_open_leads_per_closer": 20,
            "fallback_to_roundrobin": 1,
        }


def get_closer_skills():
    """Return all active closer skills (cached).

    Returns:
        list of dicts: [{user, leadtyp, skill_level, weight}]
    """
    cached = frappe.cache().get_value("crm_closer_skills")
    if cached:
        return cached

    skills = []
    try:
        settings = frappe.get_single("CRM Closer Settings")
        for s in settings.closer_skills:
            if s.active:
                skills.append({
                    "user": s.user,
                    "leadtyp": s.leadtyp,
                    "skill_level": s.skill_level,
                    "weight": SKILL_LEVEL_WEIGHT.get(s.skill_level, 0),
                })
    except Exception:
        pass

    frappe.cache().set_value("crm_closer_skills", skills, expires_in_sec=120)
    return skills


def get_open_lead_counts():
    """Return dict of {user: open_lead_count} for all closers.

    Open leads = custom_liste NOT IN (80, 90), where user is lead_owner or assigned.
    """
    counts = {}

    # Count leads where user is lead_owner
    owner_counts = frappe.db.sql("""
        SELECT lead_owner, COUNT(*) as cnt
        FROM `tabCRM Lead`
        WHERE lead_owner IS NOT NULL
          AND lead_owner != ''
          AND custom_liste NOT IN ('80 - Abschluss gewonnen', '90 - Abschluss verloren')
        GROUP BY lead_owner
    """, as_dict=True)

    for row in owner_counts:
        counts[row.lead_owner] = row.cnt

    return counts


def intelligent_assign_closer(lead_name, leadtyp=None):
    """Assign a Closer to the lead using intelligent routing.

    Routing modes:
    1. Skill-basiert: Match leadtyp skills, prefer higher skill level, then lowest capacity
    2. Round-Robin: Simple rotation among all active CRM Vertrieb users
    3. Kapazitaet: Pick the closer with fewest open leads (no skill preference)

    Args:
        lead_name: CRM Lead name
        leadtyp: Optional leadtyp override (otherwise read from lead)

    Returns:
        str: Assigned user email, or None if no assignment possible
    """
    settings = get_closer_settings()
    routing_mode = settings["routing_mode"]
    max_leads = settings["max_open_leads_per_closer"]
    fallback = settings["fallback_to_roundrobin"]

    # Get leadtyp from lead if not provided
    if not leadtyp:
        leadtyp = frappe.db.get_value("CRM Lead", lead_name, "custom_leadtyp")

    assigned_user = None

    if routing_mode == "Skill-basiert" and leadtyp:
        assigned_user = _skill_based_routing(leadtyp, max_leads)
        if not assigned_user and fallback:
            assigned_user = _round_robin_routing(max_leads)

    elif routing_mode == "Kapazitaet":
        assigned_user = _capacity_routing(max_leads)
        if not assigned_user and fallback:
            assigned_user = _round_robin_routing(max_leads=0)

    else:
        # Round-Robin or fallback
        assigned_user = _round_robin_routing(max_leads)

    if assigned_user:
        _apply_closer_assignment(lead_name, assigned_user)

    return assigned_user


def _skill_based_routing(leadtyp, max_leads):
    """Find best closer based on skill match and capacity.

    Priority: skill_level (Experte > Fortgeschritten > Basis),
    then fewest open leads among same skill level.
    """
    skills = get_closer_skills()
    open_counts = get_open_lead_counts()

    # Filter skills matching this leadtyp
    matching = [s for s in skills if s["leadtyp"] == leadtyp]
    if not matching:
        return None

    # Check user is still active
    active_users = set()
    for s in matching:
        if frappe.db.get_value("User", s["user"], "enabled"):
            active_users.add(s["user"])

    matching = [s for s in matching if s["user"] in active_users]
    if not matching:
        return None

    # Apply capacity filter
    if max_leads > 0:
        matching = [s for s in matching if open_counts.get(s["user"], 0) < max_leads]
        if not matching:
            return None

    # Sort by skill_level DESC (weight), then open leads ASC
    matching.sort(
        key=lambda s: (-s["weight"], open_counts.get(s["user"], 0))
    )

    return matching[0]["user"]


def _capacity_routing(max_leads):
    """Assign to the closer with fewest open leads (no skill check)."""
    from crm.fcrm.doctype.crm_lead.crm_lead import get_active_sales_users

    users = get_active_sales_users()
    if not users:
        return None

    open_counts = get_open_lead_counts()

    candidates = []
    for u in users:
        count = open_counts.get(u.name, 0)
        if max_leads > 0 and count >= max_leads:
            continue
        candidates.append((u.name, count))

    if not candidates:
        return None

    # Sort by fewest open leads
    candidates.sort(key=lambda x: x[1])
    return candidates[0][0]


def _round_robin_routing(max_leads=0):
    """Simple round-robin among active CRM Vertrieb users, with optional capacity check."""
    from crm.fcrm.doctype.crm_lead.crm_lead import get_active_sales_users

    users = get_active_sales_users()
    if not users:
        return None

    user_list = [u.name for u in users]

    # Apply capacity filter if needed
    if max_leads > 0:
        open_counts = get_open_lead_counts()
        user_list = [u for u in user_list if open_counts.get(u, 0) < max_leads]
        if not user_list:
            return None

    # Get last assigned index from cache
    cache_key = "crm_closer_round_robin_index"
    last_index = frappe.cache.get_value(cache_key) or 0

    next_index = (last_index + 1) % len(user_list)
    assigned_user = user_list[next_index]

    frappe.cache.set_value(cache_key, next_index)

    return assigned_user


def _apply_closer_assignment(lead_name, user):
    """Apply the closer assignment to a lead (set termin_berater + comment)."""
    frappe.db.set_value("CRM Lead", lead_name, "custom_termin_berater", user, update_modified=False)

    full_name = frappe.db.get_value("User", user, "full_name") or user

    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "CRM Lead",
        "reference_name": lead_name,
        "content": "CLOSER-ROUTING: {0} ({1}) automatisch zugewiesen".format(full_name, user),
    }).insert(ignore_permissions=True)
