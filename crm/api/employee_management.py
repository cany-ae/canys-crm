import frappe
from frappe import _

ALLOWED_PROFILES = ["Vertriebler", "Geschäftsführer"]
PROFILE_MODULE_MAP = {
    "Vertriebler": "Sales Desk Only",
    "Geschäftsführer": "Management Desk",
}
BLOCKED_ROLES = ["System Manager", "Administrator"]


def _check_gf_permission():
    """Ensure caller is Geschäftsführer or System Manager."""
    roles = frappe.get_roles(frappe.session.user)
    if frappe.session.user == "Administrator":
        return
    if "Sales Manager" not in roles:
        frappe.throw(_("Keine Berechtigung. Nur Geschäftsführer dürfen Mitarbeiter verwalten."),
                     frappe.PermissionError)


def _validate_profile(profile):
    if profile not in ALLOWED_PROFILES:
        frappe.throw(_("Ungültiges Profil. Erlaubt: {0}").format(", ".join(ALLOWED_PROFILES)))


@frappe.whitelist()
def get_employees():
    """List all managed employees (users with allowed role profiles)."""
    _check_gf_permission()

    users = frappe.get_all("User",
        filters={
            "user_type": "System User",
            "name": ["not in", ["Administrator", "Guest"]],
            "role_profile_name": ["in", ALLOWED_PROFILES + ["Sales"]]
        },
        fields=["name", "first_name", "last_name", "email", "enabled",
                "role_profile_name", "module_profile", "last_login", "creation"],
        order_by="creation desc"
    )
    return users


@frappe.whitelist()
def create_employee(first_name, last_name, email, profile):
    """Create a new user with the given profile."""
    _check_gf_permission()
    _validate_profile(profile)

    email = email.strip().lower()

    if frappe.db.exists("User", email):
        frappe.throw(_("Ein Benutzer mit dieser E-Mail existiert bereits."))

    # Validate email format
    from frappe.utils import validate_email_address
    if not validate_email_address(email):
        frappe.throw(_("Ungültige E-Mail-Adresse."))

    module_profile = PROFILE_MODULE_MAP.get(profile, "")

    user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "user_type": "System User",
        "role_profile_name": profile,
        "module_profile": module_profile,
        "send_welcome_email": 1,
        "language": "de",
    })
    user.insert(ignore_permissions=True)

    # Verify roles were populated from role profile
    user.reload()
    user_roles = [r.role for r in user.roles]
    if not user_roles or user_roles == ["All"]:
        # Force role population
        rp = frappe.get_doc("Role Profile", profile)
        user.roles = []
        for role in rp.roles:
            user.append("roles", {"role": role.role})
        user.save(ignore_permissions=True)

    # Security check: ensure no escalation
    for role in BLOCKED_ROLES:
        if role in [r.role for r in user.roles]:
            frappe.throw(_("Sicherheitsfehler: Rolle {0} darf nicht zugewiesen werden.").format(role))

    # Create Contact linked to user
    _create_contact(user)

    frappe.db.commit()

    return {
        "success": True,
        "message": _("Benutzer {0} wurde erstellt. Eine Willkommens-E-Mail wurde gesendet.").format(email),
        "user": email
    }


def _create_contact(user):
    """Create a Contact linked to the new user with custom_contact_type=Intern."""
    if frappe.db.exists("Contact", {"email_id": user.email}):
        # Link existing contact
        contact = frappe.get_doc("Contact", {"email_id": user.email})
        contact.user = user.name
        if hasattr(contact, 'custom_contact_type'):
            contact.custom_contact_type = "Intern"
        contact.save(ignore_permissions=True)
        return

    contact = frappe.get_doc({
        "doctype": "Contact",
        "first_name": user.first_name,
        "last_name": user.last_name or "",
        "user": user.name,
        "email_ids": [{"email_id": user.email, "is_primary": 1}],
    })
    if hasattr(frappe.get_meta("Contact"), "has_field") and frappe.get_meta("Contact").has_field("custom_contact_type"):
        contact.custom_contact_type = "Intern"
    contact.insert(ignore_permissions=True)


@frappe.whitelist()
def toggle_employee(email, enabled):
    """Enable or disable a user."""
    _check_gf_permission()

    if not frappe.db.exists("User", email):
        frappe.throw(_("Benutzer nicht gefunden."))

    user = frappe.get_doc("User", email)

    # Prevent disabling Administrator or self
    if user.name == "Administrator" or user.name == frappe.session.user:
        frappe.throw(_("Dieser Benutzer kann nicht deaktiviert werden."))

    # Only allow managing users with allowed profiles
    if user.role_profile_name not in ALLOWED_PROFILES + ["Sales"]:
        frappe.throw(_("Dieser Benutzer kann nicht über die Mitarbeiterverwaltung verwaltet werden."))

    user.enabled = int(enabled)
    user.save(ignore_permissions=True)
    frappe.db.commit()

    status = "aktiviert" if int(enabled) else "deaktiviert"
    return {"success": True, "message": _("Benutzer {0} wurde {1}.").format(email, status)}


@frappe.whitelist()
def reset_employee_password(email):
    """Trigger a password reset for a user."""
    _check_gf_permission()

    if not frappe.db.exists("User", email):
        frappe.throw(_("Benutzer nicht gefunden."))

    user = frappe.get_doc("User", email)
    if user.role_profile_name not in ALLOWED_PROFILES + ["Sales"]:
        frappe.throw(_("Dieser Benutzer kann nicht über die Mitarbeiterverwaltung verwaltet werden."))

    from frappe.utils import get_url, random_string
    key = random_string(32)
    user.db_set("reset_password_key", key)
    user.db_set("last_reset_password_key_generated_on", frappe.utils.now_datetime())

    url = get_url("/update-password?key=" + key)

    frappe.sendmail(
        recipients=email,
        subject=_("Passwort zurücksetzen"),
        template="password_reset",
        args={"link": url},
        header=[_("Passwort zurücksetzen"), "green"],
        now=True,
    )

    frappe.db.commit()
    return {"success": True, "message": _("Passwort-Reset E-Mail wurde an {0} gesendet.").format(email)}


@frappe.whitelist()
def update_employee_profile(email, profile):
    """Update role profile of existing user."""
    _check_gf_permission()
    _validate_profile(profile)

    if not frappe.db.exists("User", email):
        frappe.throw(_("Benutzer nicht gefunden."))

    user = frappe.get_doc("User", email)
    if user.role_profile_name not in ALLOWED_PROFILES + ["Sales"]:
        frappe.throw(_("Dieser Benutzer kann nicht über die Mitarbeiterverwaltung verwaltet werden."))

    user.role_profile_name = profile
    user.module_profile = PROFILE_MODULE_MAP.get(profile, "")
    user.save(ignore_permissions=True)

    # Security check
    for role in BLOCKED_ROLES:
        if role in [r.role for r in user.roles]:
            frappe.throw(_("Sicherheitsfehler"))

    frappe.db.commit()
    return {"success": True, "message": _("Profil von {0} auf {1} geändert.").format(email, profile)}
