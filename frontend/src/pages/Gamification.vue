<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Gamification" />
      </template>
      <template #right-header>
        <div class="flex items-center gap-2">
          <Button
            v-for="p in periods"
            :key="p.value"
            :label="p.label"
            :variant="activePeriod === p.value ? 'solid' : 'outline'"
            size="sm"
            @click="activePeriod = p.value"
          />
          <Button
            :label="__('Aktualisieren')"
            variant="outline"
            size="sm"
            @click="refreshAll()"
            :loading="userStats.loading || leaderboard.loading"
          />
        </div>
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto p-5 space-y-5">
      <!-- Personal Stats Header -->
      <div v-if="stats" class="rounded-xl border border-outline-gray-2 bg-gradient-to-r from-blue-50 to-purple-50 p-5">
        <div class="flex items-center gap-4 mb-4">
          <Avatar
            :label="stats.full_name"
            :image="stats.user_image"
            size="xl"
          />
          <div>
            <h2 class="text-xl font-bold text-ink-gray-9">{{ stats.full_name }}</h2>
            <div class="flex items-center gap-3 mt-1">
              <span v-if="stats.weekly_rank > 0" class="text-sm text-ink-gray-6">
                Platz {{ stats.weekly_rank }} von {{ stats.weekly_total_users }} diese Woche
              </span>
              <span v-else class="text-sm text-ink-gray-5">
                Noch keine Wochenwertung
              </span>
            </div>
          </div>
          <!-- Streak Display -->
          <div class="ml-auto flex items-center gap-2 bg-white rounded-lg px-4 py-3 shadow-sm border border-orange-200">
            <span class="text-3xl">{{ streakIcon }}</span>
            <div>
              <div class="text-2xl font-bold text-orange-600">{{ stats.streak?.current || 0 }}</div>
              <div class="text-xs text-ink-gray-5">{{ __('Tage-Streak') }}</div>
            </div>
            <div class="ml-3 pl-3 border-l border-orange-200">
              <div class="text-sm font-semibold text-ink-gray-7">{{ stats.streak?.best || 0 }}</div>
              <div class="text-xs text-ink-gray-5">{{ __('Bester') }}</div>
            </div>
          </div>
        </div>

        <!-- Points Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div class="bg-white rounded-lg p-3 shadow-sm border border-blue-100">
            <div class="text-xs font-medium text-ink-gray-5 uppercase tracking-wide">{{ __('Heute') }}</div>
            <div class="text-2xl font-bold text-blue-600 mt-1">{{ stats.daily?.points || 0 }}</div>
            <div class="text-xs text-ink-gray-4 mt-0.5">{{ __('Punkte') }}</div>
          </div>
          <div class="bg-white rounded-lg p-3 shadow-sm border border-cyan-100">
            <div class="text-xs font-medium text-ink-gray-5 uppercase tracking-wide">{{ __('Diese Woche') }}</div>
            <div class="text-2xl font-bold text-cyan-600 mt-1">{{ stats.weekly?.points || 0 }}</div>
            <div class="text-xs text-ink-gray-4 mt-0.5">{{ __('Punkte') }}</div>
          </div>
          <div class="bg-white rounded-lg p-3 shadow-sm border border-purple-100">
            <div class="text-xs font-medium text-ink-gray-5 uppercase tracking-wide">{{ __('Dieser Monat') }}</div>
            <div class="text-2xl font-bold text-purple-600 mt-1">{{ stats.monthly?.points || 0 }}</div>
            <div class="text-xs text-ink-gray-4 mt-0.5">{{ __('Punkte') }}</div>
          </div>
          <div class="bg-white rounded-lg p-3 shadow-sm border border-green-100">
            <div class="text-xs font-medium text-ink-gray-5 uppercase tracking-wide">{{ __('Gesamt') }}</div>
            <div class="text-2xl font-bold text-green-600 mt-1">{{ stats.total?.points || 0 }}</div>
            <div class="text-xs text-ink-gray-4 mt-0.5">{{ __('Punkte') }}</div>
          </div>
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <!-- Left: Activity Breakdown -->
        <div class="lg:col-span-1 space-y-5">
          <!-- Today's Activity -->
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <h3 class="text-base font-semibold text-ink-gray-9 mb-3">{{ __('Aktivitaeten heute') }}</h3>
            <div class="space-y-2">
              <ActivityRow
                :label="__('Leads erstellt')"
                :count="stats?.daily?.lead_created_count || 0"
                :points="5"
                color="blue"
              />
              <ActivityRow
                :label="__('Termine gebucht')"
                :count="stats?.daily?.termin_booked_count || 0"
                :points="10"
                color="cyan"
              />
              <ActivityRow
                :label="__('Follow-ups')"
                :count="stats?.daily?.followup_count || 0"
                :points="3"
                color="amber"
              />
              <ActivityRow
                :label="__('Abschlüsse')"
                :count="stats?.daily?.abschluss_count || 0"
                :points="50"
                color="green"
              />
            </div>
          </div>

          <!-- Total Stats -->
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <h3 class="text-base font-semibold text-ink-gray-9 mb-3">{{ __('Gesamt-Statistik') }}</h3>
            <div class="space-y-2">
              <StatRow :label="__('Leads erstellt')" :value="stats?.total?.lead_created_count || 0" />
              <StatRow :label="__('Termine gebucht')" :value="stats?.total?.termin_booked_count || 0" />
              <StatRow :label="__('Follow-ups')" :value="stats?.total?.followup_count || 0" />
              <StatRow :label="__('Abschlüsse gewonnen')" :value="stats?.total?.abschluss_count || 0" />
              <StatRow :label="__('Abschlüsse verloren')" :value="stats?.total?.verloren_count || 0" />
              <StatRow :label="__('Spezialist qualifiziert')" :value="stats?.total?.spezialist_count || 0" />
              <StatRow :label="__('Cross-Sell')" :value="stats?.total?.cross_sell_count || 0" />
            </div>
          </div>

          <!-- Badges -->
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <h3 class="text-base font-semibold text-ink-gray-9 mb-3">
              {{ __('Badges') }}
              <span class="text-sm font-normal text-ink-gray-4">({{ earnedBadges.length }}/{{ allBadgeCount }})</span>
            </h3>
            <div class="grid grid-cols-3 gap-2">
              <div
                v-for="badge in displayBadges"
                :key="badge.id"
                class="flex flex-col items-center gap-1 rounded-lg p-2 text-center transition-all"
                :class="badge.earned
                  ? 'bg-amber-50 border border-amber-200 shadow-sm'
                  : 'bg-gray-50 border border-gray-200 opacity-40'"
                :title="badge.description"
              >
                <span class="text-2xl">{{ badge.icon }}</span>
                <span class="text-[10px] font-medium leading-tight" :class="badge.earned ? 'text-ink-gray-8' : 'text-ink-gray-4'">
                  {{ badge.name }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Leaderboard -->
        <div class="lg:col-span-2">
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-base font-semibold text-ink-gray-9">{{ __('Leaderboard') }}</h3>
              <div class="flex items-center gap-1">
                <Button
                  v-for="lp in leaderboardPeriods"
                  :key="lp.value"
                  :label="lp.label"
                  :variant="leaderboardPeriod === lp.value ? 'solid' : 'ghost'"
                  size="sm"
                  @click="leaderboardPeriod = lp.value"
                />
              </div>
            </div>

            <div v-if="leaderboard.loading && !leaders.length" class="flex items-center justify-center h-48 text-ink-gray-4 text-sm">
              {{ __('Lade Leaderboard...') }}
            </div>

            <div v-else-if="!leaders.length" class="flex items-center justify-center h-48 text-ink-gray-4 text-sm">
              {{ __('Noch keine Daten für diesen Zeitraum') }}
            </div>

            <div v-else class="space-y-2">
              <div
                v-for="(leader, idx) in leaders"
                :key="leader.user"
                class="flex items-center gap-3 rounded-lg px-3 py-2.5 transition-all"
                :class="leaderRowClass(idx, leader.user)"
              >
                <!-- Rank -->
                <div class="w-8 flex-shrink-0 text-center">
                  <span v-if="idx === 0" class="text-2xl">&#127942;</span>
                  <span v-else-if="idx === 1" class="text-2xl">&#129352;</span>
                  <span v-else-if="idx === 2" class="text-2xl">&#129353;</span>
                  <span v-else class="text-lg font-bold text-ink-gray-4">#{{ idx + 1 }}</span>
                </div>

                <!-- Avatar + Name -->
                <Avatar
                  :label="leader.full_name || leader.user"
                  :image="leader.user_image"
                  size="md"
                />
                <div class="flex-1 min-w-0">
                  <div class="font-semibold text-ink-gray-9 truncate">{{ leader.full_name || leader.user }}</div>
                  <div class="flex items-center gap-2 text-xs text-ink-gray-5">
                    <span v-if="leader.abschluss_count">{{ leader.abschluss_count }} Abschl.</span>
                    <span v-if="leader.termin_booked_count">{{ leader.termin_booked_count }} Termine</span>
                    <span v-if="leader.lead_created_count">{{ leader.lead_created_count }} Leads</span>
                  </div>
                </div>

                <!-- Points -->
                <div class="text-right flex-shrink-0">
                  <div class="text-xl font-bold" :class="idx === 0 ? 'text-amber-600' : idx === 1 ? 'text-gray-500' : idx === 2 ? 'text-orange-700' : 'text-ink-gray-7'">
                    {{ leader.points }}
                  </div>
                  <div class="text-xs text-ink-gray-4">{{ __('Punkte') }}</div>
                </div>

                <!-- Streak indicator -->
                <div v-if="leader.current_streak > 0" class="flex-shrink-0 flex items-center gap-0.5 bg-orange-100 text-orange-700 rounded-full px-2 py-0.5 text-xs font-bold">
                  <span>&#128293;</span>{{ leader.current_streak }}
                </div>
              </div>
            </div>
          </div>

          <!-- Points Configuration Reference -->
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 mt-5">
            <h3 class="text-base font-semibold text-ink-gray-9 mb-3">{{ __('Punkte-System') }}</h3>
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <div v-for="pc in pointsConfig" :key="pc.action" class="flex items-center gap-2 rounded-lg bg-gray-50 px-3 py-2">
                <span class="text-lg">{{ pc.icon }}</span>
                <div class="flex-1">
                  <div class="text-xs font-medium text-ink-gray-7">{{ pc.label }}</div>
                  <div class="text-sm font-bold" :class="pc.color">+{{ pc.points }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { createResource, usePageMeta, Avatar } from 'frappe-ui'
import { ref, computed, watch, h } from 'vue'

const periods = [
  { label: 'Woche', value: 'weekly' },
  { label: 'Monat', value: 'monthly' },
  { label: 'Gesamt', value: 'total' },
]

const leaderboardPeriods = [
  { label: 'Heute', value: 'daily' },
  { label: 'Woche', value: 'weekly' },
  { label: 'Monat', value: 'monthly' },
  { label: 'Gesamt', value: 'total' },
]

const activePeriod = ref('weekly')
const leaderboardPeriod = ref('weekly')

// --- User Stats ---
const userStats = createResource({
  url: 'crm.api.gamification.get_user_gamification_stats',
  auto: true,
})

const stats = computed(() => userStats.data)

// --- Leaderboard ---
const leaderboard = createResource({
  url: 'crm.api.gamification.get_gamification_leaderboard',
  makeParams() {
    return { period: leaderboardPeriod.value }
  },
  auto: true,
})

watch(leaderboardPeriod, () => {
  leaderboard.reload()
})

const leaders = computed(() => leaderboard.data || [])

function refreshAll() {
  userStats.reload()
  leaderboard.reload()
}

// --- Streak Icon ---
const streakIcon = computed(() => {
  const s = stats.value?.streak?.current || 0
  if (s >= 20) return '\u{1F30B}'  // volcano
  if (s >= 10) return '\u{1F525}'  // fire
  if (s >= 5) return '\u{1F4AA}'   // flexed biceps
  if (s >= 1) return '\u{1F4A5}'   // collision
  return '\u{2744}\u{FE0F}'        // snowflake (no streak)
})

// --- Badge Display ---
const BADGE_ICON_MAP = {
  trophy: '\u{1F3C6}',
  star: '\u{2B50}',
  crown: '\u{1F451}',
  flame: '\u{1F525}',
  fire: '\u{1F4A5}',
  volcano: '\u{1F30B}',
  zap: '\u{26A1}',
  lightning: '\u{1F329}\u{FE0F}',
  calendar: '\u{1F4C5}',
  calendar_star: '\u{1F4C6}',
  users: '\u{1F465}',
  link: '\u{1F517}',
  medal: '\u{1F3C5}',
}

const ALL_BADGES = [
  { id: 'first_close', name: 'Erster Abschluss', icon: '\u{1F3C6}', description: 'Ersten Abschluss erzielt' },
  { id: 'close_10', name: '10 Abschlüsse', icon: '\u{2B50}', description: '10 Abschlüsse erzielt' },
  { id: 'close_50', name: '50 Abschlüsse', icon: '\u{1F451}', description: '50 Abschlüsse erzielt' },
  { id: 'streak_5', name: '5-Tage-Streak', icon: '\u{1F525}', description: '5 Arbeitstage in Folge aktiv' },
  { id: 'streak_10', name: '10-Tage-Streak', icon: '\u{1F4A5}', description: '10 Arbeitstage in Folge aktiv' },
  { id: 'streak_20', name: '20-Tage-Streak', icon: '\u{1F30B}', description: '20 Arbeitstage in Folge aktiv' },
  { id: 'points_100_day', name: '100 Pkt/Tag', icon: '\u{26A1}', description: '100+ Punkte an einem Tag' },
  { id: 'points_500_day', name: '500 Pkt/Tag', icon: '\u{1F329}\u{FE0F}', description: '500+ Punkte an einem Tag' },
  { id: 'termin_10', name: '10 Termine', icon: '\u{1F4C5}', description: '10 Termine gebucht' },
  { id: 'termin_50', name: '50 Termine', icon: '\u{1F4C6}', description: '50 Termine gebucht' },
  { id: 'leads_50', name: '50 Leads', icon: '\u{1F465}', description: '50 Leads erstellt' },
  { id: 'cross_sell_10', name: 'Cross-Sell Profi', icon: '\u{1F517}', description: '10 Cross-Sell Empfehlungen' },
  { id: 'weekly_top', name: 'Top der Woche', icon: '\u{1F3C5}', description: 'Hoechste Punktzahl der Woche' },
]

const allBadgeCount = ALL_BADGES.length

const earnedBadges = computed(() => {
  return (stats.value?.badges || []).map(b => b.badge_id)
})

const displayBadges = computed(() => {
  const earned = new Set(earnedBadges.value)
  return ALL_BADGES.map(b => ({
    ...b,
    earned: earned.has(b.id),
  }))
})

// --- Leaderboard styling ---
function leaderRowClass(idx, user) {
  const isMe = user === stats.value?.user
  if (idx === 0) return 'bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200'
  if (idx === 1) return 'bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-200'
  if (idx === 2) return 'bg-gradient-to-r from-orange-50 to-amber-50 border border-orange-200'
  if (isMe) return 'bg-blue-50 border border-blue-200'
  return 'bg-surface-white hover:bg-surface-gray-1'
}

// --- Points Config Display ---
const pointsConfig = [
  { action: 'lead_created', label: 'Lead erstellt', points: 5, icon: '\u{1F465}', color: 'text-blue-600' },
  { action: 'termin_booked', label: 'Termin gebucht', points: 10, icon: '\u{1F4C5}', color: 'text-cyan-600' },
  { action: 'followup_set', label: 'Follow-up', points: 3, icon: '\u{1F4DE}', color: 'text-amber-600' },
  { action: 'abschluss_gewonnen', label: 'Abschluss gew.', points: 50, icon: '\u{2705}', color: 'text-green-600' },
  { action: 'abschluss_verloren', label: 'Abschluss verl.', points: 5, icon: '\u{274C}', color: 'text-red-600' },
  { action: 'spezialist_qual', label: 'Spezialist qual.', points: 20, icon: '\u{1F9D1}\u{200D}\u{1F4BC}', color: 'text-purple-600' },
  { action: 'cross_sell', label: 'Cross-Sell', points: 5, icon: '\u{1F517}', color: 'text-indigo-600' },
]

// --- Sub-components ---
const ActivityRow = {
  props: {
    label: String,
    count: Number,
    points: Number,
    color: { type: String, default: 'blue' },
  },
  setup(props) {
    const colorMap = {
      blue: 'bg-blue-100 text-blue-700',
      cyan: 'bg-cyan-100 text-cyan-700',
      amber: 'bg-amber-100 text-amber-700',
      green: 'bg-green-100 text-green-700',
    }
    return () =>
      h('div', { class: 'flex items-center justify-between py-1.5' }, [
        h('span', { class: 'text-sm text-ink-gray-7' }, props.label),
        h('div', { class: 'flex items-center gap-2' }, [
          h('span', {
            class: `inline-flex items-center rounded-full px-2 py-0.5 text-xs font-bold ${colorMap[props.color] || colorMap.blue}`
          }, String(props.count)),
          h('span', { class: 'text-xs text-ink-gray-4' },
            `(+${props.count * props.points})`
          ),
        ]),
      ])
  },
}

const StatRow = {
  props: {
    label: String,
    value: Number,
  },
  setup(props) {
    return () =>
      h('div', { class: 'flex items-center justify-between py-1' }, [
        h('span', { class: 'text-sm text-ink-gray-6' }, props.label),
        h('span', { class: 'text-sm font-semibold text-ink-gray-8' }, String(props.value)),
      ])
  },
}

usePageMeta(() => ({ title: __('Gamification') }))
</script>
