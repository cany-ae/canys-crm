import { createResource } from 'frappe-ui'
import { computed, ref } from 'vue'

// Hardcoded fallback phases - used when API is unavailable or still loading
const FALLBACK_PHASES = [
  { phase_code: '10', phase_value: '10 - Neu ohne Termin', label: 'Neu', color: 'gray', hex_color: '#6B7280', sort_order: 10, is_default: 1, role_owner: 'Setter' },
  { phase_code: '20', phase_value: '20 - Termin gebucht', label: 'Termin', color: 'blue', hex_color: '#3B82F6', sort_order: 20, is_default: 0, role_owner: 'Setter' },
  { phase_code: '30', phase_value: '30 - Reaktivierung', label: 'Reaktiv.', color: 'amber', hex_color: '#F59E0B', sort_order: 30, is_default: 0, role_owner: 'Opener' },
  { phase_code: '50', phase_value: '50 - Closer-Termin', label: 'Closer', color: 'purple', hex_color: '#8B5CF6', sort_order: 50, is_default: 0, role_owner: 'Closer' },
  { phase_code: '70', phase_value: '70 - Follow-up', label: 'Follow-up', color: 'orange', hex_color: '#F97316', sort_order: 70, is_default: 0, role_owner: 'System' },
  { phase_code: '80', phase_value: '80 - Abschluss gewonnen', label: 'Gewonnen', color: 'green', hex_color: '#10B981', sort_order: 80, is_default: 0, role_owner: 'System' },
  { phase_code: '90', phase_value: '90 - Abschluss verloren', label: 'Verloren', color: 'red', hex_color: '#EF4444', sort_order: 90, is_default: 0, role_owner: 'System' },
]

// Badge CSS class mappings per color name
const BADGE_CLASSES = {
  gray: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  blue: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  amber: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300',
  purple: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
  orange: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
  green: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  red: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
}

// Phase class mappings for larger badges (Lead detail view uses text-800 variant)
const PHASE_CLASSES = {
  gray: 'bg-gray-100 text-gray-800',
  blue: 'bg-blue-100 text-blue-800',
  amber: 'bg-amber-100 text-amber-800',
  purple: 'bg-purple-100 text-purple-800',
  orange: 'bg-orange-100 text-orange-800',
  green: 'bg-green-100 text-green-800',
  red: 'bg-red-100 text-red-800',
}

// Module-level singleton: fetched once, shared across all consumers
const phasesData = ref(null)
let fetchInitiated = false

function initFetch() {
  if (fetchInitiated) return
  fetchInitiated = true
  createResource({
    url: 'crm.fcrm.doctype.crm_lead.crm_lead.get_pipeline_phases_api',
    cache: 'Pipeline Phases',
    auto: true,
    onSuccess: (data) => {
      if (data && Array.isArray(data) && data.length > 0) {
        phasesData.value = data
      }
    },
  })
}

// The reactive phases list: API data or fallback
const phases = computed(() => {
  return phasesData.value || FALLBACK_PHASES
})

/**
 * Get the Tailwind color name for a given phase value.
 * @param {string} phaseValue - e.g. '10 - Neu ohne Termin'
 * @returns {string} - e.g. 'gray'
 */
function getPhaseColor(phaseValue) {
  const p = phases.value.find(ph => ph.phase_value === phaseValue)
  return p ? p.color : 'gray'
}

/**
 * Get the label for a given phase value.
 * @param {string} phaseValue - e.g. '10 - Neu ohne Termin'
 * @returns {string} - e.g. 'Neu'
 */
function getPhaseLabel(phaseValue) {
  const p = phases.value.find(ph => ph.phase_value === phaseValue)
  return p ? p.label : (phaseValue ? phaseValue.replace(/^\d+\s*-\s*/, '') : '')
}

/**
 * Get the hex color for a given phase value.
 * @param {string} phaseValue - e.g. '10 - Neu ohne Termin'
 * @returns {string} - e.g. '#6B7280'
 */
function getPhaseHex(phaseValue) {
  const p = phases.value.find(ph => ph.phase_value === phaseValue)
  return p ? p.hex_color : '#6B7280'
}

/**
 * Get badge CSS classes for a given phase value (sidebar/list badges).
 * @param {string} phaseValue - e.g. '10 - Neu ohne Termin'
 * @returns {string} - Tailwind classes
 */
function getPhaseBadgeClass(phaseValue) {
  const color = getPhaseColor(phaseValue)
  return BADGE_CLASSES[color] || BADGE_CLASSES.gray
}

/**
 * Get phase CSS classes for lead detail view (larger badges).
 * @param {string} phaseValue - e.g. '10 - Neu ohne Termin'
 * @returns {string} - Tailwind classes
 */
function getPhaseClass(phaseValue) {
  const color = getPhaseColor(phaseValue)
  return PHASE_CLASSES[color] || PHASE_CLASSES.gray
}

/**
 * Get badge CSS classes for a color name (used by LeadsListView).
 * @param {string} color - e.g. 'gray', 'blue'
 * @returns {string} - Tailwind classes
 */
function getListeBadgeClass(color) {
  return BADGE_CLASSES[color] || BADGE_CLASSES.gray
}

/**
 * Build the sidebar-friendly phases list with short labels and badge classes.
 * @returns {Array} - phases with value, short, hex, badgeClass
 */
const sidebarPhases = computed(() => {
  return phases.value.map(p => ({
    value: p.phase_value,
    short: p.phase_code + ' ' + p.label,
    hex: p.hex_color,
    badgeClass: BADGE_CLASSES[p.color] || BADGE_CLASSES.gray,
  }))
})

/**
 * Build the Leads.vue-friendly phases list with full labels.
 * @returns {Array} - phases with value, label, short, color, hex
 */
const leadsPagePhases = computed(() => {
  return phases.value.map(p => ({
    value: p.phase_value,
    label: p.phase_value.replace(/^\d+\s*-\s*/, ''),
    short: p.phase_code,
    color: p.color,
    hex: p.hex_color,
  }))
})

export function usePipelinePhases() {
  // Ensure fetch is initiated on first use
  initFetch()

  return {
    phases,
    sidebarPhases,
    leadsPagePhases,
    getPhaseColor,
    getPhaseLabel,
    getPhaseHex,
    getPhaseBadgeClass,
    getPhaseClass,
    getListeBadgeClass,
  }
}
