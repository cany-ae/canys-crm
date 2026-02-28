<template>
  <Dialog v-model="show" :options="{ title: dialogTitle, size: 'lg' }">
    <template #body-content>
      <div class="flex flex-col gap-4 py-2">
        <!-- Step 1: Select type and duration -->
        <div v-if="!showSlots" class="flex flex-col gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-ink-gray-7">Termin-Typ</label>
            <select
              v-model="terminTyp"
              style="font-size: 16px; padding: 12px 14px; height: 44px;"
              class="form-select w-full rounded-md border-outline-gray-2 bg-surface-gray-1 text-ink-gray-8 focus:border-outline-gray-4 focus:ring-0"
            >
              <option v-for="opt in typOptions" :key="opt" :value="opt">{{ opt }}</option>
            </select>
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-ink-gray-7">Dauer (Minuten)</label>
            <select
              v-model.number="durationMinutes"
              style="font-size: 16px; padding: 12px 14px; height: 44px;"
              class="form-select w-full rounded-md border-outline-gray-2 bg-surface-gray-1 text-ink-gray-8 focus:border-outline-gray-4 focus:ring-0"
            >
              <option :value="15">15</option>
              <option :value="30">30</option>
              <option :value="45">45</option>
              <option :value="60">60</option>
              <option :value="75">75</option>
              <option :value="90">90</option>
              <option :value="120">120</option>
            </select>
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-ink-gray-7">Notiz <span class="text-ink-gray-4">(optional)</span></label>
            <textarea
              v-model="terminNotiz"
              rows="4"
              style="font-size: 16px; padding: 12px 14px; min-height: 100px;"
              class="form-textarea w-full rounded-md border-outline-gray-2 bg-surface-gray-1 text-ink-gray-8 focus:border-outline-gray-4 focus:ring-0"
              placeholder="Optionale Notiz zum Termin..."
            ></textarea>
          </div>

          <div class="flex items-center gap-3 pt-2">
            <Button
              variant="solid"
              theme="blue"
              :loading="loadingSlots"
              @click="loadSlots"
              class="flex-1"
            >
              <template #prefix>
                <FeatherIcon name="calendar" class="h-4 w-4" />
              </template>
              Verfügbare Termine laden
            </Button>
          </div>
          <div class="text-center">
            <button
              @click="switchToManual"
              class="text-xs text-ink-gray-4 hover:text-ink-gray-6 underline"
            >
              Manuell buchen (ohne Vorschläge)
            </button>
          </div>
        </div>

        <!-- Step 2: Show slot suggestions -->
        <div v-if="showSlots" class="flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <button
              @click="showSlots = false"
              class="flex items-center gap-1 text-sm text-ink-gray-5 hover:text-ink-gray-7"
            >
              <FeatherIcon name="arrow-left" class="h-3.5 w-3.5" />
              Zurück
            </button>
            <span class="text-xs text-ink-gray-4">
              {{ terminTyp }} &middot; {{ durationMinutes }} Min.
            </span>
          </div>

          <!-- Loading state -->
          <div v-if="loadingSlots" class="flex items-center justify-center py-8">
            <div class="flex flex-col items-center gap-2">
              <div class="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
              <span class="text-sm text-ink-gray-5">Termine werden geprüft...</span>
            </div>
          </div>

          <!-- No slots available -->
          <div v-else-if="slots.length === 0" class="py-8 text-center">
            <FeatherIcon name="calendar" class="h-8 w-8 text-ink-gray-3 mx-auto mb-2" />
            <p class="text-sm text-ink-gray-5">Keine verfügbaren Termine in den nächsten 14 Tagen.</p>
            <button
              @click="switchToManual"
              class="mt-3 text-sm text-blue-600 hover:text-blue-700 underline"
            >
              Manuell buchen
            </button>
          </div>

          <!-- Slot cards -->
          <div v-else class="flex flex-col gap-2 max-h-[400px] overflow-y-auto pr-1">
            <div
              v-for="(slot, idx) in slots"
              :key="idx"
              @click="bookSlot(slot)"
              class="group cursor-pointer rounded-lg border border-outline-gray-2 bg-surface-white px-4 py-3 transition-all hover:border-blue-400 hover:bg-blue-50 hover:shadow-sm"
              :class="{ 'opacity-50 pointer-events-none': bookingInProgress }"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="flex flex-col items-center rounded bg-surface-gray-1 px-2.5 py-1 group-hover:bg-blue-100">
                    <span class="text-[10px] font-semibold uppercase text-ink-gray-4 group-hover:text-blue-600">{{ slot.weekday }}</span>
                    <span class="text-sm font-bold text-ink-gray-8 group-hover:text-blue-700">{{ formatDateShort(slot.date) }}</span>
                  </div>
                  <div class="flex flex-col">
                    <span class="text-sm font-semibold text-ink-gray-8 group-hover:text-blue-700">
                      {{ slot.start }} - {{ slot.end }}
                    </span>
                    <span class="text-xs text-ink-gray-5">
                      {{ formatDateFull(slot.date) }}
                    </span>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <span
                    v-if="slot.berater_name"
                    class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700"
                  >
                    <FeatherIcon name="user" class="h-3 w-3" />
                    {{ slot.berater_name }}
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
                    :class="availabilityClass(slot.available_count)"
                  >
                    <span class="h-1.5 w-1.5 rounded-full" :class="availabilityDotClass(slot.available_count)"></span>
                    {{ slot.available_count }} Berater frei
                  </span>
                  <FeatherIcon name="chevron-right" class="h-4 w-4 text-ink-gray-3 group-hover:text-blue-500" />
                </div>
              </div>
            </div>
          </div>

          <!-- Booking in progress -->
          <div v-if="bookingInProgress" class="flex items-center justify-center py-2">
            <div class="flex items-center gap-2 text-sm text-blue-600">
              <div class="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"></div>
              Termin wird gebucht...
            </div>
          </div>

          <div v-if="!loadingSlots && slots.length > 0" class="text-center pt-1">
            <button
              @click="switchToManual"
              class="text-xs text-ink-gray-4 hover:text-ink-gray-6 underline"
            >
              Keiner passt? Manuell buchen
            </button>
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button variant="subtle" @click="show = false">
          {{ __('Abbrechen') }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { call, Dialog, Button, FeatherIcon } from 'frappe-ui'

const props = defineProps({
  leadId: { type: String, default: '' },
})

const emit = defineEmits(['booked', 'manual', 'update:show'])

const show = defineModel('show', { type: Boolean, default: false })

const terminTyp = ref('Ersttermin')
const durationMinutes = ref(60)
const terminNotiz = ref('')
const loadingSlots = ref(false)
const showSlots = ref(false)
const slots = ref([])
const bookingInProgress = ref(false)

const typOptions = ['Ersttermin', 'Closer-Termin', 'Follow-up Termin', 'Reaktivierung', 'Spezialist']
const dialogTitle = computed(() => {
  if (showSlots.value) return 'Termin auswählen'
  return 'Termin buchen'
})
// Reset state when dialog opens
watch(show, async (newVal) => {
  if (newVal) {
    showSlots.value = false
    slots.value = []
    bookingInProgress.value = false
    loadingSlots.value = false
  }
})

function formatDateShort(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  return d.getDate() + '.' + (d.getMonth() + 1) + '.'
}

function formatDateFull(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  const days = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag']
  const months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
  return days[d.getDay()] + ', ' + d.getDate() + '. ' + months[d.getMonth()] + ' ' + d.getFullYear()
}

function availabilityClass(count) {
  if (count >= 10) return 'bg-green-100 text-green-700'
  if (count >= 5) return 'bg-emerald-100 text-emerald-700'
  if (count >= 2) return 'bg-amber-100 text-amber-700'
  return 'bg-red-100 text-red-700'
}

function availabilityDotClass(count) {
  if (count >= 10) return 'bg-green-500'
  if (count >= 5) return 'bg-emerald-500'
  if (count >= 2) return 'bg-amber-500'
  return 'bg-red-500'
}

async function loadSlots() {
  loadingSlots.value = true
  showSlots.value = true
  try {
    const result = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.get_termin_vorschlaege',
      {
        duration_minutes: durationMinutes.value,
        lead_name: props.leadId,
        termin_typ: terminTyp.value,
        berater: null,
      }
    )
    slots.value = result || []
  } catch (err) {
    console.error('Failed to load Terminvorschlaege:', err)
    slots.value = []
  } finally {
    loadingSlots.value = false
  }
}

async function bookSlot(slot) {
  if (bookingInProgress.value) return
  bookingInProgress.value = true
  try {
    const result = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.execute_lead_action',
      {
        lead_name: props.leadId,
        action: 'termin_buchen',
        data: JSON.stringify({
          termin_datum: slot.date,
          termin_typ: terminTyp.value,
          termin_zeit_von: slot.start,
          termin_zeit_bis: slot.end,
          termin_notiz: terminNotiz.value,
          termin_berater: slot.berater || '',
          from_vorschlag: true,
        }),
      }
    )
    if (result && result.success) {
      emit('booked', result)
      show.value = false
    }
  } catch (err) {
    console.error('Booking failed:', err)
    bookingInProgress.value = false
  }
}

function switchToManual() {
  show.value = false
  emit('manual', {
    termin_typ: terminTyp.value,
    termin_notiz: terminNotiz.value,
  })
}
</script>
