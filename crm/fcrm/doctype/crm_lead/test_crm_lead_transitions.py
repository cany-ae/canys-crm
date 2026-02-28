# -*- coding: utf-8 -*-
# Unit tests for CRM Lead phase transition logic
# Tests: Phase transitions, permissions, trigger-based actions, execute_lead_action

import frappe
from frappe.tests.utils import FrappeTestCase
import json


# Phase constants (match custom_liste Select options)
PHASE_10 = "10 - Neu ohne Termin"
PHASE_20 = "20 - Termin gebucht"
PHASE_30 = "30 - Reaktivierung"
PHASE_50 = "50 - Closer-Termin"
PHASE_70 = "70 - Follow-up"
PHASE_80 = "80 - Abschluss gewonnen"
PHASE_90 = "90 - Abschluss verloren"


def _make_test_lead(phase=None, first_name=None, **kwargs):
    """Create a minimal CRM Lead for testing. Returns the doc."""
    import random
    import string
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    lead = frappe.new_doc("CRM Lead")
    lead.first_name = first_name or f"Test-{suffix}"
    lead.last_name = "Transition"
    lead.status = "Nicht kontaktiert"
    # Set any custom fields from kwargs
    for k, v in kwargs.items():
        if hasattr(lead, k):
            setattr(lead, k, v)
    lead.flags.ignore_permissions = True
    lead.flags.ignore_mandatory = True
    lead.insert(ignore_permissions=True)
    # Force-set phase if requested (bypass after_insert default)
    if phase and phase != PHASE_10:
        frappe.db.set_value("CRM Lead", lead.name, "custom_liste", phase, update_modified=False)
        lead.reload()
    elif not phase:
        # after_insert already sets PHASE_10
        lead.reload()
    return lead


class TestPhaseTransitions(FrappeTestCase):
    """Test the ALLOWED_TRANSITIONS enforcement in validate_liste_transition."""

    def setUp(self):
        """Create a fresh test lead for each test."""
        self.lead = _make_test_lead()
        # Ensure we are running as System Manager for setup
        frappe.set_user("Administrator")

    def tearDown(self):
        """Clean up test lead."""
        frappe.set_user("Administrator")
        if hasattr(self, "lead") and self.lead and frappe.db.exists("CRM Lead", self.lead.name):
            frappe.delete_doc("CRM Lead", self.lead.name, force=True, ignore_permissions=True)

    # ── New lead defaults ─────────────────────────────────────────────────

    def test_new_lead_gets_phase_10(self):
        """A new lead must automatically be assigned to Liste 10."""
        lead = _make_test_lead()
        self.assertEqual(lead.custom_liste, PHASE_10)
        frappe.delete_doc("CRM Lead", lead.name, force=True, ignore_permissions=True)

    def test_new_lead_gets_default_status(self):
        """A new lead must get status 'Nicht kontaktiert' by default."""
        lead = _make_test_lead()
        self.assertEqual(lead.status, "Nicht kontaktiert")
        frappe.delete_doc("CRM Lead", lead.name, force=True, ignore_permissions=True)

    # ── Valid transitions (System Manager can always transition) ──────────

    def test_valid_transition_10_to_20(self):
        """Phase 10 -> 20 (Termin gebucht) is allowed."""
        self.lead.custom_liste = PHASE_20
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_20)

    def test_valid_transition_10_to_50(self):
        """Phase 10 -> 50 (Closer-Termin) is allowed."""
        self.lead.custom_liste = PHASE_50
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_50)

    def test_valid_transition_10_to_90(self):
        """Phase 10 -> 90 (Abschluss verloren) is allowed."""
        self.lead.custom_liste = PHASE_90
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_90)

    def test_valid_transition_20_to_50(self):
        """Phase 20 -> 50 (Closer-Termin) is allowed."""
        self.lead = _make_test_lead(phase=PHASE_20)
        self.lead.custom_liste = PHASE_50
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_50)

    def test_valid_transition_20_to_70(self):
        """Phase 20 -> 70 (Follow-up) is allowed."""
        self.lead = _make_test_lead(phase=PHASE_20)
        self.lead.custom_liste = PHASE_70
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_70)

    def test_valid_transition_20_to_80(self):
        """Phase 20 -> 80 (Abschluss gewonnen) is allowed."""
        self.lead = _make_test_lead(phase=PHASE_20)
        self.lead.custom_liste = PHASE_80
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_80)

    def test_valid_transition_20_to_90(self):
        """Phase 20 -> 90 (Abschluss verloren) is allowed."""
        self.lead = _make_test_lead(phase=PHASE_20)
        self.lead.custom_liste = PHASE_90
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_90)

    def test_valid_transition_50_to_70(self):
        """Phase 50 -> 70 (Follow-up) is allowed."""
        self.lead = _make_test_lead(phase=PHASE_50)
        self.lead.custom_liste = PHASE_70
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_70)

    def test_valid_transition_50_to_80(self):
        """Phase 50 -> 80 (Closer wins) is allowed."""
        self.lead = _make_test_lead(phase=PHASE_50)
        self.lead.custom_liste = PHASE_80
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_80)

    def test_valid_transition_50_to_90(self):
        """Phase 50 -> 90 (Closer loses) is allowed."""
        self.lead = _make_test_lead(phase=PHASE_50)
        self.lead.custom_liste = PHASE_90
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_90)

    def test_valid_transition_90_to_30(self):
        """Phase 90 -> 30 (Reactivation from lost) is allowed."""
        self.lead = _make_test_lead(phase=PHASE_90)
        self.lead.custom_liste = PHASE_30
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_30)

    def test_valid_transition_70_to_80(self):
        """Phase 70 -> 80 (Follow-up to won) is allowed."""
        self.lead = _make_test_lead(phase=PHASE_70)
        self.lead.custom_liste = PHASE_80
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_80)

    def test_valid_transition_70_to_50(self):
        """Phase 70 -> 50 (Follow-up to Closer-Termin) is allowed."""
        self.lead = _make_test_lead(phase=PHASE_70)
        self.lead.custom_liste = PHASE_50
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_50)

    def test_valid_transition_30_to_20(self):
        """Phase 30 -> 20 (Reactivation to Termin) is allowed."""
        self.lead = _make_test_lead(phase=PHASE_30)
        self.lead.custom_liste = PHASE_20
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_20)

    def test_valid_transition_30_to_50(self):
        """Phase 30 -> 50 (Reactivation to Closer) is allowed."""
        self.lead = _make_test_lead(phase=PHASE_30)
        self.lead.custom_liste = PHASE_50
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_50)

    # ── Terminal phase: 80 has no outgoing transitions ────────────────────

    def test_phase_80_is_terminal(self):
        """Phase 80 (won) is terminal - no transitions allowed for non-admin.
        Admin can still override, so we test that the transitions dict is empty."""
        from crm.fcrm.doctype.crm_lead.crm_lead import _get_allowed_transitions
        transitions = _get_allowed_transitions()
        self.assertEqual(transitions.get(PHASE_80, []), [],
                         "Phase 80 should have no allowed transitions (terminal)")

    def test_phase_90_only_to_30(self):
        """Phase 90 (lost) can only transition to 30 (Reactivation)."""
        from crm.fcrm.doctype.crm_lead.crm_lead import _get_allowed_transitions
        transitions = _get_allowed_transitions()
        self.assertEqual(transitions.get(PHASE_90, []), [PHASE_30],
                         "Phase 90 should only allow transition to 30")


class TestPermissions(FrappeTestCase):
    """Test that phase change permissions are enforced correctly.
    - System Manager (GF/Admin) CAN manually change phase
    - Sales User without System Manager CANNOT do invalid transitions
    """

    def setUp(self):
        frappe.set_user("Administrator")
        self.lead = _make_test_lead()
        # Find or create a test user with Sales User role (for write perm) but NO System Manager
        self.test_user = self._get_or_create_test_user()

    def tearDown(self):
        frappe.set_user("Administrator")
        if hasattr(self, "lead") and self.lead and frappe.db.exists("CRM Lead", self.lead.name):
            frappe.delete_doc("CRM Lead", self.lead.name, force=True, ignore_permissions=True)

    def _get_or_create_test_user(self):
        """Get or create a test user with Sales User + CRM Vertrieb roles (no System Manager)."""
        test_email = "test-vertrieb-unit@test.local"
        if not frappe.db.exists("User", test_email):
            user = frappe.get_doc({
                "doctype": "User",
                "email": test_email,
                "first_name": "Test",
                "last_name": "Vertrieb",
                "user_type": "System User",
                "send_welcome_email": 0,
                "roles": [
                    {"role": "Sales User"},
                    {"role": "CRM Vertrieb"},
                ],
            })
            user.flags.ignore_permissions = True
            user.insert(ignore_permissions=True)
        else:
            # Ensure Sales User role is present
            user = frappe.get_doc("User", test_email)
            roles = [r.role for r in user.roles]
            changed = False
            if "Sales User" not in roles:
                user.append("roles", {"role": "Sales User"})
                changed = True
            if "CRM Vertrieb" not in roles:
                user.append("roles", {"role": "CRM Vertrieb"})
                changed = True
            if changed:
                user.flags.ignore_permissions = True
                user.save(ignore_permissions=True)
        return test_email

    def test_admin_can_change_phase_freely(self):
        """System Manager (Administrator) can manually change phase."""
        frappe.set_user("Administrator")
        self.lead.custom_liste = PHASE_50
        # Should not raise
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_50)

    def test_admin_can_do_invalid_transition(self):
        """System Manager can even do 'invalid' transitions (admin override)."""
        frappe.set_user("Administrator")
        # 10 -> 80 is normally not allowed, but admin can override
        self.lead.custom_liste = PHASE_80
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_80)

    def test_vertrieb_blocked_on_invalid_transition(self):
        """Sales User (non-admin) is blocked from invalid manual phase changes.
        10 -> 80 is not in ALLOWED_TRANSITIONS, so it should raise ValidationError."""
        # Share doc with test user so they have write access
        frappe.share.add_docshare(
            "CRM Lead", self.lead.name, self.test_user, write=1,
            flags={"ignore_share_permission": True}
        )
        frappe.set_user(self.test_user)
        lead = frappe.get_doc("CRM Lead", self.lead.name)
        lead.custom_liste = PHASE_80
        with self.assertRaises(frappe.ValidationError):
            lead.save()

    def test_vertrieb_blocked_10_to_70(self):
        """Sales User (non-admin) cannot go 10 -> 70 (not in allowed transitions)."""
        frappe.share.add_docshare(
            "CRM Lead", self.lead.name, self.test_user, write=1,
            flags={"ignore_share_permission": True}
        )
        frappe.set_user(self.test_user)
        lead = frappe.get_doc("CRM Lead", self.lead.name)
        lead.custom_liste = PHASE_70
        with self.assertRaises(frappe.ValidationError):
            lead.save()

    def test_vertrieb_allowed_valid_transition(self):
        """Sales User (non-admin) can do valid transition 10 -> 20."""
        frappe.share.add_docshare(
            "CRM Lead", self.lead.name, self.test_user, write=1,
            flags={"ignore_share_permission": True}
        )
        frappe.set_user(self.test_user)
        lead = frappe.get_doc("CRM Lead", self.lead.name)
        lead.custom_liste = PHASE_20
        lead.save()
        self.assertEqual(lead.custom_liste, PHASE_20)

    def test_vertrieb_blocked_on_terminal_escape(self):
        """Sales User cannot transition out of Phase 80 (won is terminal)."""
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_liste", PHASE_80, update_modified=False)
        frappe.share.add_docshare(
            "CRM Lead", self.lead.name, self.test_user, write=1,
            flags={"ignore_share_permission": True}
        )
        frappe.set_user(self.test_user)
        lead = frappe.get_doc("CRM Lead", self.lead.name)
        lead.custom_liste = PHASE_10
        with self.assertRaises(frappe.ValidationError):
            lead.save()


class TestApplyPhaseTriggers(FrappeTestCase):
    """Test the apply_phase_triggers method which auto-sets custom_liste
    based on field changes (termin_datum, termin_status, abschluss, etc.)."""

    def setUp(self):
        frappe.set_user("Administrator")
        self.lead = _make_test_lead()

    def tearDown(self):
        frappe.set_user("Administrator")
        if hasattr(self, "lead") and self.lead and frappe.db.exists("CRM Lead", self.lead.name):
            frappe.delete_doc("CRM Lead", self.lead.name, force=True, ignore_permissions=True)

    def test_verloren_grund_triggers_phase_90(self):
        """Setting custom_abschluss_verloren_grund triggers move to Phase 90."""
        self.lead.custom_abschluss_verloren_grund = "Kein Interesse"
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_90)

    def test_abschluss_datum_triggers_phase_80(self):
        """Setting custom_abschluss_datum (without verloren_grund) triggers Phase 80."""
        self.lead.custom_abschluss_datum = frappe.utils.today()
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_80)

    def test_termin_datum_triggers_phase_20(self):
        """Setting custom_termin_datum (non-Closer) triggers move to Phase 20."""
        self.lead.custom_termin_datum = frappe.utils.today()
        self.lead.custom_termin_typ = "Ersttermin"
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_20)

    def test_termin_datum_closer_triggers_phase_50(self):
        """Setting custom_termin_datum with Closer-Termin type triggers Phase 50."""
        self.lead.custom_termin_datum = frappe.utils.today()
        self.lead.custom_termin_typ = "Closer-Termin"
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_50)

    def test_termin_noshow_triggers_phase_70(self):
        """Setting termin_status to No-Show from Phase 20 triggers Phase 70."""
        # First move to Phase 20 with a termin
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_liste", PHASE_20, update_modified=False)
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_termin_datum", frappe.utils.today(), update_modified=False)
        self.lead.reload()
        # Now simulate No-Show
        self.lead.custom_termin_status = "No-Show"
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_70)

    def test_termin_noshow_from_50_triggers_phase_70(self):
        """Setting termin_status to No-Show from Phase 50 triggers Phase 70."""
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_liste", PHASE_50, update_modified=False)
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_termin_datum", frappe.utils.today(), update_modified=False)
        self.lead.reload()
        self.lead.custom_termin_status = "No-Show"
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_70)

    def test_termin_abgesagt_from_50_triggers_phase_70(self):
        """Cancelling termin from Phase 50 triggers Phase 70 (Follow-up)."""
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_liste", PHASE_50, update_modified=False)
        self.lead.reload()
        self.lead.custom_termin_status = "Abgesagt"
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_70)

    def test_termin_abgesagt_from_20_triggers_phase_10(self):
        """Cancelling termin from Phase 20 triggers Phase 10 (back to start)."""
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_liste", PHASE_20, update_modified=False)
        self.lead.reload()
        self.lead.custom_termin_status = "Abgesagt"
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_10)

    def test_termin_durchgefuehrt_from_20_triggers_phase_70(self):
        """Completing termin from Phase 20 triggers Phase 70."""
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_liste", PHASE_20, update_modified=False)
        self.lead.reload()
        self.lead.custom_termin_status = u"Durchgef\u00fchrt"
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_70)

    def test_termin_durchgefuehrt_from_50_triggers_phase_70(self):
        """Completing termin from Phase 50 triggers Phase 70."""
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_liste", PHASE_50, update_modified=False)
        self.lead.reload()
        self.lead.custom_termin_status = u"Durchgef\u00fchrt"
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_70)

    def test_followup_from_phase_20_triggers_phase_70(self):
        """Setting naechster_kontakt from Phase 20 triggers Phase 70."""
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_liste", PHASE_20, update_modified=False)
        self.lead.reload()
        from frappe.utils import add_days
        self.lead.custom_naechster_kontakt = add_days(frappe.utils.today(), 3)
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_70)

    def test_followup_from_phase_50_triggers_phase_70(self):
        """Setting naechster_kontakt from Phase 50 triggers Phase 70."""
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_liste", PHASE_50, update_modified=False)
        self.lead.reload()
        from frappe.utils import add_days
        self.lead.custom_naechster_kontakt = add_days(frappe.utils.today(), 3)
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_70)

    def test_verloren_grund_takes_priority_over_termin(self):
        """If both verloren_grund and termin_datum are set, verloren takes priority."""
        self.lead.custom_abschluss_verloren_grund = "Kein Interesse"
        self.lead.custom_termin_datum = frappe.utils.today()
        self.lead.custom_termin_typ = "Ersttermin"
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_90,
                         "verloren_grund should take priority over termin_datum")

    def test_no_trigger_when_already_in_target_phase(self):
        """If lead is already in Phase 90, setting verloren_grund should not re-trigger."""
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_liste", PHASE_90, update_modified=False)
        frappe.db.set_value("CRM Lead", self.lead.name, "custom_abschluss_verloren_grund", "Kein Interesse", update_modified=False)
        self.lead.reload()
        # Now change something else - verloren_grund already set, should not re-trigger
        self.lead.custom_followup_notiz = "Test note"
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_90)

    def test_followup_from_phase_10_does_not_trigger(self):
        """Setting naechster_kontakt from Phase 10 should NOT trigger Phase 70.
        apply_phase_triggers only triggers from 20/30/50."""
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_10)
        from frappe.utils import add_days
        self.lead.custom_naechster_kontakt = add_days(frappe.utils.today(), 3)
        self.lead.save(ignore_permissions=True)
        self.assertEqual(self.lead.custom_liste, PHASE_10,
                         "Follow-up from Phase 10 should not auto-trigger Phase 70")


class TestExecuteLeadAction(FrappeTestCase):
    """Test the execute_lead_action whitelisted API function."""

    def setUp(self):
        frappe.set_user("Administrator")
        self.lead = _make_test_lead()

    def tearDown(self):
        frappe.set_user("Administrator")
        if hasattr(self, "lead") and self.lead and frappe.db.exists("CRM Lead", self.lead.name):
            frappe.delete_doc("CRM Lead", self.lead.name, force=True, ignore_permissions=True)

    def test_action_abschluss_gewonnen(self):
        """Action 'abschluss_gewonnen' should move lead to Phase 80."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        result = execute_lead_action(self.lead.name, "abschluss_gewonnen", {
            "abschluss_datum": frappe.utils.today(),
            "abschluss_produkt": "Tierkranken Hund",
            "abschluss_beitrag": 50,
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("new_phase"), PHASE_80)

    def test_action_abschluss_verloren(self):
        """Action 'abschluss_verloren' should move lead to Phase 90."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        result = execute_lead_action(self.lead.name, "abschluss_verloren", {
            "verloren_grund": "Kein Interesse",
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("new_phase"), PHASE_90)

    def test_action_abschluss_verloren_sets_status(self):
        """Action 'abschluss_verloren' should set status to 'Kein Interesse'."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        result = execute_lead_action(self.lead.name, "abschluss_verloren", {
            "verloren_grund": "Preis zu hoch",
        })
        self.assertEqual(result.get("new_status"), "Kein Interesse")

    def test_action_termin_buchen_default(self):
        """Action 'termin_buchen' with default type should move to Phase 20."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        result = execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Ersttermin",
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("new_phase"), PHASE_20)

    def test_action_termin_buchen_closer(self):
        """Action 'termin_buchen' with Closer type should move to Phase 50."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        result = execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Closer",
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("new_phase"), PHASE_50)

    def test_action_termin_buchen_sets_status(self):
        """Action 'termin_buchen' should set status to 'Termin vereinbart'."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        result = execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Ersttermin",
        })
        self.assertEqual(result.get("new_status"), "Termin vereinbart")

    def test_action_followup_setzen(self):
        """Action 'followup_setzen' should set next contact date and grund."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        from frappe.utils import add_days, getdate
        target_date = add_days(frappe.utils.today(), 3)
        result = execute_lead_action(self.lead.name, "followup_setzen", {
            "naechster_kontakt": target_date,
            "followup_grund": u"R\u00fcckruf vereinbart",
        })
        self.assertTrue(result.get("success"))
        # Verify follow-up date was set (compare as date objects to avoid datetime mismatch)
        lead = frappe.get_doc("CRM Lead", self.lead.name)
        self.assertEqual(getdate(lead.custom_naechster_kontakt), getdate(target_date))
        self.assertEqual(lead.custom_followup_grund, u"R\u00fcckruf vereinbart")
        self.assertEqual(lead.status, u"R\u00fcckruf geplant")

    def test_action_followup_increments_kontaktversuche(self):
        """Each followup_setzen should increment custom_kontaktversuche."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        from frappe.utils import add_days
        initial = frappe.db.get_value("CRM Lead", self.lead.name, "custom_kontaktversuche") or 0
        execute_lead_action(self.lead.name, "followup_setzen", {
            "naechster_kontakt": add_days(frappe.utils.today(), 1),
        })
        after_one = frappe.db.get_value("CRM Lead", self.lead.name, "custom_kontaktversuche") or 0
        self.assertEqual(after_one, initial + 1)

    def test_action_termin_noshow(self):
        """Action 'termin_noshow' should move from Phase 20 to 70."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        # First book a termin
        execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Ersttermin",
        })
        # Verify in Phase 20
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_20)
        # Now no-show
        result = execute_lead_action(self.lead.name, "termin_noshow")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("new_phase"), PHASE_70)

    def test_action_termin_noshow_sets_followup(self):
        """After no-show, a follow-up should be auto-set for next day."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        from frappe.utils import add_days, getdate
        execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Ersttermin",
        })
        execute_lead_action(self.lead.name, "termin_noshow")
        lead = frappe.get_doc("CRM Lead", self.lead.name)
        expected = add_days(frappe.utils.today(), 1)
        self.assertEqual(getdate(lead.custom_naechster_kontakt), getdate(expected))

    def test_action_termin_absagen_from_50(self):
        """Action 'termin_absagen' from Phase 50 should move to Phase 70."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        # Book Closer termin
        execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Closer",
        })
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_50)
        # Cancel
        result = execute_lead_action(self.lead.name, "termin_absagen", {
            "absage_grund": "Vom Kunden abgesagt",
        })
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("new_phase"), PHASE_70)

    def test_action_termin_absagen_from_20(self):
        """Action 'termin_absagen' from Phase 20 should move back to Phase 10."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Ersttermin",
        })
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_20)
        result = execute_lead_action(self.lead.name, "termin_absagen", {})
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("new_phase"), PHASE_10)

    def test_action_termin_durchgefuehrt(self):
        """Action 'termin_durchgefuehrt' from Phase 20 should move to Phase 70."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Ersttermin",
        })
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_20)
        result = execute_lead_action(self.lead.name, "termin_durchgefuehrt")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("new_phase"), PHASE_70)

    def test_action_termin_bestaetigen(self):
        """Action 'termin_bestaetigen' should set termin_status to Bestaetigt."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Ersttermin",
        })
        result = execute_lead_action(self.lead.name, "termin_bestaetigen")
        self.assertTrue(result.get("success"))
        lead = frappe.get_doc("CRM Lead", self.lead.name)
        self.assertEqual(lead.custom_termin_status, u"Best\u00e4tigt")

    def test_action_reaktivieren_from_90(self):
        """Action 'reaktivieren' should move from Phase 90 to Phase 30."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        # First lose the lead
        execute_lead_action(self.lead.name, "abschluss_verloren", {
            "verloren_grund": "Kein Interesse",
        })
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_90)
        # Reactivate
        result = execute_lead_action(self.lead.name, "reaktivieren")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("new_phase"), PHASE_30)

    def test_action_reaktivieren_resets_verloren_fields(self):
        """Reactivation should clear abschluss_verloren_grund and abschluss_datum."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        execute_lead_action(self.lead.name, "abschluss_verloren", {
            "verloren_grund": "Kein Interesse",
        })
        execute_lead_action(self.lead.name, "reaktivieren")
        lead = frappe.get_doc("CRM Lead", self.lead.name)
        self.assertFalse(lead.custom_abschluss_verloren_grund)
        self.assertFalse(lead.custom_abschluss_datum)
        self.assertEqual(lead.status, "Nicht kontaktiert")

    def test_action_unknown_raises_error(self):
        """An unknown action should raise an error."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        with self.assertRaises(Exception):
            execute_lead_action(self.lead.name, "non_existent_action")

    def test_action_returns_phase_changed_flag(self):
        """The result should correctly report whether the phase changed."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        result = execute_lead_action(self.lead.name, "abschluss_gewonnen", {
            "abschluss_datum": frappe.utils.today(),
        })
        self.assertTrue(result.get("phase_changed"))
        self.assertEqual(result.get("old_liste"), PHASE_10)
        self.assertEqual(result.get("new_phase"), PHASE_80)

    def test_action_abschluss_gewonnen_sets_fields(self):
        """Action 'abschluss_gewonnen' should set product, beitrag, provision."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        execute_lead_action(self.lead.name, "abschluss_gewonnen", {
            "abschluss_datum": frappe.utils.today(),
            "abschluss_produkt": "Tierkranken Hund",
            "abschluss_beitrag": 75,
            "abschluss_provision": 150,
        })
        lead = frappe.get_doc("CRM Lead", self.lead.name)
        self.assertEqual(lead.custom_abschluss_produkt, "Tierkranken Hund")
        self.assertEqual(float(lead.custom_abschluss_beitrag or 0), 75.0)
        self.assertEqual(float(lead.custom_abschluss_provision or 0), 150.0)


class TestTransitionsDataIntegrity(FrappeTestCase):
    """Test that the transitions configuration is complete and consistent."""

    def test_all_phases_present_in_transitions(self):
        """Every defined phase must have an entry in ALLOWED_TRANSITIONS."""
        from crm.fcrm.doctype.crm_lead.crm_lead import _get_allowed_transitions
        transitions = _get_allowed_transitions()
        expected_phases = [PHASE_10, PHASE_20, PHASE_30, PHASE_50, PHASE_70, PHASE_80, PHASE_90]
        for phase in expected_phases:
            self.assertIn(phase, transitions,
                          f"Phase '{phase}' missing from ALLOWED_TRANSITIONS")

    def test_transition_targets_are_valid_phases(self):
        """Every target in ALLOWED_TRANSITIONS must itself be a valid phase."""
        from crm.fcrm.doctype.crm_lead.crm_lead import _get_allowed_transitions
        transitions = _get_allowed_transitions()
        all_phases = set(transitions.keys())
        for source, targets in transitions.items():
            for target in targets:
                self.assertIn(target, all_phases,
                              f"Transition target '{target}' from '{source}' is not a valid phase")

    def test_no_self_transitions(self):
        """No phase should list itself as an allowed transition target."""
        from crm.fcrm.doctype.crm_lead.crm_lead import _get_allowed_transitions
        transitions = _get_allowed_transitions()
        for source, targets in transitions.items():
            self.assertNotIn(source, targets,
                             f"Phase '{source}' has a self-transition (should not)")

    def test_phase_80_has_no_outgoing(self):
        """Phase 80 (won) must be terminal - no outgoing transitions."""
        from crm.fcrm.doctype.crm_lead.crm_lead import _get_allowed_transitions
        transitions = _get_allowed_transitions()
        self.assertEqual(len(transitions.get(PHASE_80, [])), 0,
                         "Phase 80 should be terminal with 0 outgoing transitions")

    def test_phase_10_has_limited_outgoing(self):
        """Phase 10 can only go to 20, 50, or 90 (not 30, 70, 80)."""
        from crm.fcrm.doctype.crm_lead.crm_lead import _get_allowed_transitions
        transitions = _get_allowed_transitions()
        allowed = transitions.get(PHASE_10, [])
        self.assertIn(PHASE_20, allowed)
        self.assertIn(PHASE_50, allowed)
        self.assertIn(PHASE_90, allowed)
        self.assertNotIn(PHASE_30, allowed, "Phase 10 should not transition to 30")
        self.assertNotIn(PHASE_70, allowed, "Phase 10 should not transition to 70")
        self.assertNotIn(PHASE_80, allowed, "Phase 10 should not transition to 80")

    def test_seven_phases_total(self):
        """There should be exactly 7 pipeline phases."""
        from crm.fcrm.doctype.crm_lead.crm_lead import _get_allowed_transitions
        transitions = _get_allowed_transitions()
        self.assertEqual(len(transitions), 7, "Expected exactly 7 pipeline phases")


class TestAuditTrail(FrappeTestCase):
    """Test that phase changes create proper audit trail comments."""

    def setUp(self):
        frappe.set_user("Administrator")
        self.lead = _make_test_lead()

    def tearDown(self):
        frappe.set_user("Administrator")
        if hasattr(self, "lead") and self.lead and frappe.db.exists("CRM Lead", self.lead.name):
            frappe.delete_doc("CRM Lead", self.lead.name, force=True, ignore_permissions=True)

    def test_initial_status_comment_created(self):
        """New lead should have a STATUS UPDATE comment from initial creation.
        Note: The LISTENWECHSEL comment for Phase 10 is skipped because
        custom_liste has a Custom Field default value pre-set before after_insert."""
        comments = frappe.get_all("Comment", filters={
            "reference_doctype": "CRM Lead",
            "reference_name": self.lead.name,
            "comment_type": "Info",
            "content": ["like", "%STATUS UPDATE%Nicht kontaktiert%"],
        })
        self.assertTrue(len(comments) > 0,
                        "Expected STATUS UPDATE comment for initial status assignment")

    def test_new_lead_phase_is_set_by_default(self):
        """New lead phase is set by Custom Field default (not after_insert code path).
        Verifies the default mechanism works correctly."""
        lead = _make_test_lead()
        self.assertEqual(lead.custom_liste, PHASE_10)
        # The Custom Field default pre-sets the value, so after_insert
        # condition 'if not self.custom_liste' is False
        frappe.delete_doc("CRM Lead", lead.name, force=True, ignore_permissions=True)

    def test_phase_change_comment_created(self):
        """Changing phase should create a LISTENWECHSEL audit comment."""
        self.lead.custom_liste = PHASE_90
        self.lead.save(ignore_permissions=True)
        comments = frappe.get_all("Comment", filters={
            "reference_doctype": "CRM Lead",
            "reference_name": self.lead.name,
            "comment_type": "Info",
            "content": ["like", "%LISTENWECHSEL%90 - Abschluss verloren%"],
        })
        self.assertTrue(len(comments) > 0,
                        "Expected LISTENWECHSEL comment for phase change to 90")

    def test_action_creates_audit_comment(self):
        """execute_lead_action should create an AKTION audit comment."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        execute_lead_action(self.lead.name, "abschluss_verloren", {
            "verloren_grund": "Kein Interesse",
        })
        comments = frappe.get_all("Comment", filters={
            "reference_doctype": "CRM Lead",
            "reference_name": self.lead.name,
            "comment_type": "Info",
            "content": ["like", "%AKTION%Abschluss verloren%"],
        })
        self.assertTrue(len(comments) > 0,
                        "Expected AKTION comment for abschluss_verloren action")


class TestLeadAlwaysInOnePhase(FrappeTestCase):
    """Test the invariant: a lead is always in exactly one phase."""

    def setUp(self):
        frappe.set_user("Administrator")
        self.lead = _make_test_lead()

    def tearDown(self):
        frappe.set_user("Administrator")
        if hasattr(self, "lead") and self.lead and frappe.db.exists("CRM Lead", self.lead.name):
            frappe.delete_doc("CRM Lead", self.lead.name, force=True, ignore_permissions=True)

    def test_lead_has_phase_after_creation(self):
        """After creation, lead must have a phase value set."""
        self.assertIsNotNone(self.lead.custom_liste)
        self.assertNotEqual(self.lead.custom_liste, "")

    def test_lead_phase_is_valid_after_actions(self):
        """After a sequence of actions, lead must still be in a valid phase."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action, _get_allowed_transitions
        valid_phases = set(_get_allowed_transitions().keys())

        # Run through a realistic lifecycle
        actions = [
            ("termin_buchen", {"termin_datum": frappe.utils.today(), "termin_typ": "Ersttermin"}),
            ("termin_durchgefuehrt", {}),
            ("followup_setzen", {"naechster_kontakt": frappe.utils.add_days(frappe.utils.today(), 3)}),
            ("abschluss_gewonnen", {"abschluss_datum": frappe.utils.today(), "abschluss_beitrag": 100}),
        ]
        for action, data in actions:
            execute_lead_action(self.lead.name, action, data)
            self.lead.reload()
            self.assertIn(self.lead.custom_liste, valid_phases,
                          f"After action '{action}', lead is in invalid phase: {self.lead.custom_liste}")

    def test_full_lifecycle_10_20_70_80(self):
        """Test complete lifecycle: 10 -> 20 -> 70 -> 80."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        # 10 -> 20
        execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Ersttermin",
        })
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_20)
        # 20 -> 70 (termin completed)
        execute_lead_action(self.lead.name, "termin_durchgefuehrt")
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_70)
        # 70 -> 80 (won)
        execute_lead_action(self.lead.name, "abschluss_gewonnen", {
            "abschluss_datum": frappe.utils.today(),
            "abschluss_beitrag": 200,
        })
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_80)

    def test_full_lifecycle_10_50_90_30(self):
        """Test lifecycle with loss and reactivation: 10 -> 50 -> 90 -> 30."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        # 10 -> 50
        execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Closer",
        })
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_50)
        # 50 -> 90
        execute_lead_action(self.lead.name, "abschluss_verloren", {
            "verloren_grund": "Preis zu hoch",
        })
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_90)
        # 90 -> 30
        execute_lead_action(self.lead.name, "reaktivieren")
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_30)

    def test_full_lifecycle_10_20_noshow_70_50_80(self):
        """Complex lifecycle: 10 -> 20 -> No-Show -> 70 -> 50 -> 80."""
        from crm.fcrm.doctype.crm_lead.crm_lead import execute_lead_action
        # 10 -> 20
        execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Ersttermin",
        })
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_20)
        # 20 -> 70 (no-show)
        execute_lead_action(self.lead.name, "termin_noshow")
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_70)
        # 70 -> 50 (rebook as Closer)
        execute_lead_action(self.lead.name, "termin_buchen", {
            "termin_datum": frappe.utils.today(),
            "termin_typ": "Closer",
        })
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_50)
        # 50 -> 80 (won)
        execute_lead_action(self.lead.name, "abschluss_gewonnen", {
            "abschluss_datum": frappe.utils.today(),
            "abschluss_beitrag": 300,
        })
        self.lead.reload()
        self.assertEqual(self.lead.custom_liste, PHASE_80)
