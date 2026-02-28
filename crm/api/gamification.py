"""Gamification API for CRM.

Punkte-System basierend auf Masterplanung Kapitel 9.8:
- Schneller Erstkontakt (Reaktionszeit < 1h/4h/24h)
- Saubere Follow-ups (puenktlich erledigt)
- Hohe Show-Rate (Termine durchgefuehrt)
- Qualifizierte Weiterleitungen (Spezialist qualifiziert)

Badges:
- Abschluss-Champion (1/10/50)
- Fleiss-Champion (Viele Aktionen/Tag)
- 5 Tage ohne ueberfaellige Leads
- Top Show-Rate im Monat
- Cross-Selling sauber umgesetzt
"""

import frappe
from frappe import _
from frappe.utils import today, now_datetime, getdate, add_days, get_datetime, date_diff


# == Points Configuration (NUR Masterplanung-Aktionen) ================
POINTS_CONFIG = {
    # Schneller Erstkontakt: abgestuft nach Reaktionszeit
    "erstkontakt_blitz": 15,    # < 1 Stunde
    "erstkontakt_schnell": 10,  # < 4 Stunden
    "erstkontakt_ok": 5,        # < 24 Stunden
    # Saubere Follow-ups
    "followup_puenktlich": 8,   # Follow-up am/vor Faelligkeitstag erledigt
    # Hohe Show-Rate
    "termin_erschienen": 12,    # Termin durchgefuehrt (Kunde da)
    # Qualifizierte Weiterleitungen
    "weiterleitung_qualifiziert": 20,  # Spezialist hat Lead qualifiziert
}

# Maps action_type to the counter field on CRM Gamification Score
ACTION_COUNTER_MAP = {
    "erstkontakt_blitz": "erstkontakt_count",
    "erstkontakt_schnell": "erstkontakt_count",
    "erstkontakt_ok": "erstkontakt_count",
    "followup_puenktlich": "followup_count",
    "termin_erschienen": "showrate_count",
    "weiterleitung_qualifiziert": "weiterleitung_count",
}

# == Badge Definitions (Masterplanung 9.8) ============================
BADGE_DEFINITIONS = {
    # Abschluss-Champion
    "abschluss_champion_1": {
        "name": "Erster Abschluss",
        "icon": "trophy",
        "description": "Ersten Abschluss erzielt",
    },
    "abschluss_champion_10": {
        "name": "Abschluss-Champion Silber",
        "icon": "star",
        "description": "10 Abschl\u00fcsse erzielt",
    },
    "abschluss_champion_50": {
        "name": "Abschluss-Champion Gold",
        "icon": "crown",
        "description": "50 Abschl\u00fcsse erzielt",
    },
    # Fleiss-Champion
    "fleiss_champion": {
        "name": "Flei\u00df-Champion",
        "icon": "zap",
        "description": "10+ Aktionen an einem Tag",
    },
    "fleiss_champion_pro": {
        "name": "Flei\u00df-Champion Pro",
        "icon": "lightning",
        "description": "20+ Aktionen an einem Tag",
    },
    # 5 Tage ohne ueberfaellige Leads
    "keine_ueberfaelligen_5": {
        "name": "5 Tage ohne \u00fcberf\u00e4llige Leads",
        "icon": "flame",
        "description": "5 Arbeitstage in Folge keine \u00fcberf\u00e4lligen Follow-ups",
    },
    "keine_ueberfaelligen_10": {
        "name": "10 Tage ohne \u00fcberf\u00e4llige Leads",
        "icon": "fire",
        "description": "10 Arbeitstage in Folge keine \u00fcberf\u00e4lligen Follow-ups",
    },
    # Top Show-Rate im Monat
    "top_showrate_monat": {
        "name": "Top Show-Rate im Monat",
        "icon": "medal",
        "description": "Beste Show-Rate im aktuellen Monat (mind. 5 Termine)",
    },
    # Cross-Selling sauber umgesetzt
    "cross_sell_sauber_5": {
        "name": "Cross-Selling Profi",
        "icon": "link",
        "description": "5 qualifizierte Cross-Sell Weiterleitungen",
    },
    "cross_sell_sauber_20": {
        "name": "Cross-Selling Champion",
        "icon": "target",
        "description": "20 qualifizierte Cross-Sell Weiterleitungen",
    },
    # Streaks
    "streak_5": {
        "name": "5-Tage-Streak",
        "icon": "flame",
        "description": "5 Arbeitstage in Folge aktiv",
    },
    "streak_10": {
        "name": "10-Tage-Streak",
        "icon": "fire",
        "description": "10 Arbeitstage in Folge aktiv",
    },
    "streak_20": {
        "name": "20-Tage-Streak",
        "icon": "volcano",
        "description": "20 Arbeitstage in Folge aktiv",
    },
    # Weekly top
    "weekly_top": {
        "name": "Top-Performer der Woche",
        "icon": "medal",
        "description": "H\u00f6chste Punktzahl in einer Woche",
    },
}


def _get_week_str(dt=None):
    d = getdate(dt or today())
    return f"{d.year}-W{d.isocalendar()[1]:02d}"


def _get_month_str(dt=None):
    d = getdate(dt or today())
    return f"{d.year}-{d.month:02d}"


def _get_or_create_score(user, score_type, period):
    name = frappe.db.exists("CRM Gamification Score", {
        "user": user,
        "score_type": score_type,
        "period": period,
    })
    if name:
        return frappe.get_doc("CRM Gamification Score", name)

    doc = frappe.new_doc("CRM Gamification Score")
    doc.user = user
    doc.score_type = score_type
    doc.period = period
    doc.points = 0
    doc.insert(ignore_permissions=True)
    return doc


def _update_streak(user, daily_score):
    yesterday = add_days(today(), -1)
    yesterday_date = getdate(yesterday)

    if yesterday_date.weekday() == 5:
        yesterday = add_days(yesterday, -1)
    elif yesterday_date.weekday() == 6:
        yesterday = add_days(yesterday, -2)

    yesterday_str = str(getdate(yesterday))

    yesterday_score = frappe.db.get_value(
        "CRM Gamification Score",
        {"user": user, "score_type": "daily_points", "period": yesterday_str},
        ["points", "current_streak", "best_streak"],
        as_dict=True,
    )

    if yesterday_score and yesterday_score.points > 0:
        daily_score.current_streak = (yesterday_score.current_streak or 0) + 1
    else:
        daily_score.current_streak = 1

    if daily_score.current_streak > (daily_score.best_streak or 0):
        daily_score.best_streak = daily_score.current_streak

    total_score = _get_or_create_score(user, "total_points", "ALL")
    if daily_score.best_streak > (total_score.best_streak or 0):
        total_score.best_streak = daily_score.best_streak
        total_score.save(ignore_permissions=True)


# == Core Award Function ==============================================

def award_gamification_points(user, action_type):
    if not user or user in ("Administrator", "Guest"):
        return {"points": 0}

    points = POINTS_CONFIG.get(action_type, 0)
    if points == 0:
        return {"points": 0}

    counter_field = ACTION_COUNTER_MAP.get(action_type)
    today_str = str(getdate(today()))
    week_str = _get_week_str()
    month_str = _get_month_str()

    for score_type, period in [
        ("daily_points", today_str),
        ("weekly_points", week_str),
        ("monthly_points", month_str),
        ("total_points", "ALL"),
    ]:
        score = _get_or_create_score(user, score_type, period)
        score.points = (score.points or 0) + points
        if counter_field:
            current = getattr(score, counter_field, 0) or 0
            setattr(score, counter_field, current + 1)

        if score_type == "daily_points":
            _update_streak(user, score)

        score.save(ignore_permissions=True)

    try:
        check_and_award_badges(user)
    except Exception:
        frappe.log_error("Badge check failed for user: {}".format(user))

    frappe.db.commit()

    return {
        "points": points,
        "action_type": action_type,
        "user": user,
    }


# == Smart Award Functions (mit Kontext-Pruefung) ======================

def award_erstkontakt(user, lead_name):
    """Pruefe Reaktionszeit und vergebe abgestufte Punkte.
    Wird aufgerufen bei der ERSTEN Aktion auf einem Lead."""
    if not user or user in ("Administrator", "Guest"):
        return

    try:
        lead_data = frappe.db.get_value(
            "CRM Lead", lead_name,
            ["creation", "custom_kontaktversuche"],
            as_dict=True,
        )
        if not lead_data:
            return

        # Nur beim ERSTEN Kontaktversuch Punkte vergeben
        kontaktversuche = lead_data.custom_kontaktversuche or 0
        if kontaktversuche > 1:
            return

        creation = get_datetime(lead_data.creation)
        jetzt = now_datetime()
        diff_hours = (jetzt - creation).total_seconds() / 3600

        if diff_hours < 1:
            award_gamification_points(user, "erstkontakt_blitz")
        elif diff_hours < 4:
            award_gamification_points(user, "erstkontakt_schnell")
        elif diff_hours < 24:
            award_gamification_points(user, "erstkontakt_ok")
    except Exception:
        frappe.log_error(f"Erstkontakt-Punkte Fehler fuer {lead_name}", "Gamification Error")


def award_followup_puenktlich(user, lead_name):
    """Pruefe ob Follow-up puenktlich erledigt wurde.
    Puenktlich = Aktion am oder vor dem Faelligkeitstag (+1 Tag Toleranz)."""
    if not user or user in ("Administrator", "Guest"):
        return

    try:
        lead_data = frappe.db.get_value(
            "CRM Lead", lead_name,
            ["custom_naechster_kontakt"],
            as_dict=True,
        )
        if not lead_data or not lead_data.custom_naechster_kontakt:
            return

        faellig = getdate(lead_data.custom_naechster_kontakt)
        heute = getdate(today())

        # Puenktlich = heute <= Faelligkeitstag + 1 Tag Toleranz
        if date_diff(faellig, heute) >= -1:
            award_gamification_points(user, "followup_puenktlich")
    except Exception:
        frappe.log_error(f"Follow-up-Punkte Fehler fuer {lead_name}", "Gamification Error")


def award_termin_erschienen(user, lead_name):
    """Punkte wenn Termin durchgefuehrt (Kunde erschienen)."""
    if not user or user in ("Administrator", "Guest"):
        return
    award_gamification_points(user, "termin_erschienen")


def award_weiterleitung_qualifiziert(user, lead_name):
    """Punkte wenn Spezialist einen Lead qualifiziert."""
    if not user or user in ("Administrator", "Guest"):
        return
    award_gamification_points(user, "weiterleitung_qualifiziert")


# == Badge Logic ======================================================

def _has_badge(user, badge_id):
    return frappe.db.exists("CRM Badge", {
        "user": user,
        "badge_id": badge_id,
    })


def _award_badge(user, badge_id):
    if _has_badge(user, badge_id):
        return False

    definition = BADGE_DEFINITIONS.get(badge_id)
    if not definition:
        return False

    badge = frappe.new_doc("CRM Badge")
    badge.user = user
    badge.badge_id = badge_id
    badge.badge_name = definition["name"]
    badge.badge_icon = definition.get("icon", "star")
    badge.badge_description = definition.get("description", "")
    badge.awarded_at = now_datetime()
    badge.insert(ignore_permissions=True)
    return True


def check_and_award_badges(user):
    """Check all badge criteria and award any earned badges."""
    if not user or user in ("Administrator", "Guest"):
        return

    total = frappe.db.get_value(
        "CRM Gamification Score",
        {"user": user, "score_type": "total_points", "period": "ALL"},
        ["points", "best_streak", "showrate_count", "weiterleitung_count",
         "erstkontakt_count", "followup_count"],
        as_dict=True,
    )
    if not total:
        return

    best_streak = total.best_streak or 0

    # -- Abschluss-Champion: basierend auf tatsaechlichen Abschluessen --
    abschluesse = frappe.db.count("CRM Lead", filters={
        "custom_liste": "80 - Abschluss gewonnen",
        "lead_owner": user,
    }) or 0

    if abschluesse >= 1:
        _award_badge(user, "abschluss_champion_1")
    if abschluesse >= 10:
        _award_badge(user, "abschluss_champion_10")
    if abschluesse >= 50:
        _award_badge(user, "abschluss_champion_50")

    # -- Fleiss-Champion: Viele Aktionen an einem Tag --
    today_str = str(getdate(today()))
    daily = frappe.db.get_value(
        "CRM Gamification Score",
        {"user": user, "score_type": "daily_points", "period": today_str},
        ["erstkontakt_count", "followup_count", "showrate_count", "weiterleitung_count"],
        as_dict=True,
    )
    if daily:
        actions_today = (
            (daily.erstkontakt_count or 0) +
            (daily.followup_count or 0) +
            (daily.showrate_count or 0) +
            (daily.weiterleitung_count or 0)
        )
        if actions_today >= 10:
            _award_badge(user, "fleiss_champion")
        if actions_today >= 20:
            _award_badge(user, "fleiss_champion_pro")

    # -- 5/10 Tage ohne ueberfaellige Leads --
    overdue_count = frappe.db.count("CRM Lead", filters={
        "lead_owner": user,
        "custom_naechster_kontakt": ["<", today()],
        "custom_liste": ["not in", ["80 - Abschluss gewonnen", "90 - Abschluss verloren"]],
    }) or 0

    if overdue_count == 0 and best_streak >= 5:
        _award_badge(user, "keine_ueberfaelligen_5")
    if overdue_count == 0 and best_streak >= 10:
        _award_badge(user, "keine_ueberfaelligen_10")

    # -- Streak badges --
    if best_streak >= 5:
        _award_badge(user, "streak_5")
    if best_streak >= 10:
        _award_badge(user, "streak_10")
    if best_streak >= 20:
        _award_badge(user, "streak_20")

    # -- Cross-Selling sauber umgesetzt --
    cross_sell_qualified = frappe.db.count("CRM Referral", filters={
        "referrer_user": user,
        "created_from": "Cross-Sell",
        "referral_status": "Qualifiziert",
    }) or 0

    if cross_sell_qualified >= 5:
        _award_badge(user, "cross_sell_sauber_5")
    if cross_sell_qualified >= 20:
        _award_badge(user, "cross_sell_sauber_20")


@frappe.whitelist()
def check_monthly_showrate_badge():
    """Scheduled monthly: Award Top Show-Rate badge."""
    month_str = _get_month_str()

    top = frappe.db.sql("""
        SELECT user, showrate_count
        FROM `tabCRM Gamification Score`
        WHERE score_type = 'monthly_points'
          AND period = %(period)s
          AND COALESCE(showrate_count, 0) >= 5
        ORDER BY showrate_count DESC
        LIMIT 1
    """, {"period": month_str}, as_dict=True)

    if top:
        _award_badge(top[0].user, "top_showrate_monat")
        return {"user": top[0].user, "showrate_count": top[0].showrate_count}

    return {"user": None}


# == Whitelist API Endpoints ==========================================

@frappe.whitelist()
def get_gamification_leaderboard(period="weekly"):
    score_type_map = {
        "daily": "daily_points",
        "weekly": "weekly_points",
        "monthly": "monthly_points",
        "total": "total_points",
    }
    score_type = score_type_map.get(period, "weekly_points")

    if period == "daily":
        period_str = str(getdate(today()))
    elif period == "weekly":
        period_str = _get_week_str()
    elif period == "monthly":
        period_str = _get_month_str()
    else:
        period_str = "ALL"

    scores = frappe.db.sql("""
        SELECT
            gs.user,
            gs.points,
            gs.current_streak,
            gs.best_streak,
            gs.erstkontakt_count,
            gs.followup_count,
            gs.showrate_count,
            gs.weiterleitung_count,
            u.full_name,
            u.user_image
        FROM `tabCRM Gamification Score` gs
        LEFT JOIN `tabUser` u ON u.name = gs.user
        WHERE gs.score_type = %(score_type)s
          AND gs.period = %(period)s
          AND gs.points > 0
        ORDER BY gs.points DESC
        LIMIT 10
    """, {
        "score_type": score_type,
        "period": period_str,
    }, as_dict=True)

    for idx, score in enumerate(scores):
        score["rank"] = idx + 1

    return scores


@frappe.whitelist()
def get_user_gamification_stats(user=None):
    if not user:
        user = frappe.session.user

    today_str = str(getdate(today()))
    week_str = _get_week_str()
    month_str = _get_month_str()

    def _get_points(score_type, period):
        result = frappe.db.get_value(
            "CRM Gamification Score",
            {"user": user, "score_type": score_type, "period": period},
            ["points", "current_streak", "best_streak",
             "erstkontakt_count", "followup_count",
             "showrate_count", "weiterleitung_count"],
            as_dict=True,
        )
        return result or {
            "points": 0, "current_streak": 0, "best_streak": 0,
            "erstkontakt_count": 0, "followup_count": 0,
            "showrate_count": 0, "weiterleitung_count": 0,
        }

    daily = _get_points("daily_points", today_str)
    weekly = _get_points("weekly_points", week_str)
    monthly = _get_points("monthly_points", month_str)
    total = _get_points("total_points", "ALL")

    badges = frappe.get_all(
        "CRM Badge",
        filters={"user": user},
        fields=["badge_id", "badge_name", "badge_icon", "badge_description", "awarded_at"],
        order_by="awarded_at desc",
    )

    weekly_rank = 0
    weekly_leaders = frappe.db.sql("""
        SELECT user, points
        FROM `tabCRM Gamification Score`
        WHERE score_type = 'weekly_points' AND period = %(period)s AND points > 0
        ORDER BY points DESC
    """, {"period": week_str}, as_dict=True)

    for idx, leader in enumerate(weekly_leaders):
        if leader.user == user:
            weekly_rank = idx + 1
            break

    user_info = frappe.db.get_value("User", user, ["full_name", "user_image"], as_dict=True) or {}

    def _fmt(data):
        return {
            "points": data.get("points", 0) or 0,
            "erstkontakt_count": data.get("erstkontakt_count", 0) or 0,
            "followup_count": data.get("followup_count", 0) or 0,
            "showrate_count": data.get("showrate_count", 0) or 0,
            "weiterleitung_count": data.get("weiterleitung_count", 0) or 0,
        }

    return {
        "user": user,
        "full_name": user_info.get("full_name", user),
        "user_image": user_info.get("user_image"),
        "daily": _fmt(daily),
        "weekly": _fmt(weekly),
        "monthly": _fmt(monthly),
        "total": _fmt(total),
        "streak": {
            "current": daily.get("current_streak", 0) or 0,
            "best": total.get("best_streak", 0) or 0,
        },
        "badges": badges,
        "weekly_rank": weekly_rank,
        "weekly_total_users": len(weekly_leaders),
    }


@frappe.whitelist()
def award_weekly_top_performer():
    """Scheduled weekly: Award Top-Performer der Woche badge."""
    last_week_date = getdate(add_days(today(), -7))
    last_week_str = f"{last_week_date.year}-W{last_week_date.isocalendar()[1]:02d}"

    top_user = frappe.db.sql("""
        SELECT user, points
        FROM `tabCRM Gamification Score`
        WHERE score_type = 'weekly_points'
          AND period = %(period)s
          AND points > 0
        ORDER BY points DESC
        LIMIT 1
    """, {"period": last_week_str}, as_dict=True)

    if top_user:
        _award_badge(top_user[0].user, "weekly_top")
        return {"user": top_user[0].user, "points": top_user[0].points}

    return {"user": None}
