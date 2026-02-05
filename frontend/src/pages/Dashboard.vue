<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Dashboard" />
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
            :iconLeft="LucideRefreshCcw"
            variant="outline"
            @click="dashboardData.reload()"
            :loading="dashboardData.loading"
          />
        </div>
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto p-5 space-y-5">
      <!-- KPI Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          :label="__('Leads gesamt')"
          :value="data?.leads?.total ?? 0"
          icon="users"
          color="blue"
        />
        <KpiCard
          :label="__('Deals gesamt')"
          :value="data?.deals?.total ?? 0"
          icon="handshake"
          color="green"
        />
        <KpiCard
          :label="__('Ø Erster Kontakt → Deal')"
          :value="formatDays(data?.deals?.avg_first_contact_to_deal)"
          icon="clock"
          color="orange"
          :subtitle="__('Ab erstem Kontaktversuch')"
        />
        <KpiCard
          :label="__('Ø Lead → Deal')"
          :value="formatDays(data?.process?.avg_lead_to_deal)"
          icon="arrow-right"
          color="purple"
          :subtitle="__('Von Lead-Eingang bis Deal')"
        />
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- Leads by Period -->
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
          <h3 class="text-base font-semibold text-ink-gray-9 mb-3">
            {{ __('Leads pro Zeitraum') }}
          </h3>
          <div class="h-64"><AxisChart
            v-if="leadsChartConfig.data.length"
            :config="leadsChartConfig"
          />
          <EmptyState v-else :message="__('Keine Daten')" /></div>
        </div>

        <!-- Deals by Period -->
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
          <h3 class="text-base font-semibold text-ink-gray-9 mb-3">
            {{ __('Deals pro Zeitraum') }}
          </h3>
          <div class="h-64"><AxisChart
            v-if="dealsChartConfig.data.length"
            :config="dealsChartConfig"
          />
          <EmptyState v-else :message="__('Keine Daten')" /></div>
        </div>

        <!-- Leads by List (Donut) -->
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
          <h3 class="text-base font-semibold text-ink-gray-9 mb-3">
            {{ __('Leads nach Liste') }}
          </h3>
          <div class="h-auto min-h-[16rem]"><ECharts
            v-if="donutEchartOptions.series[0].data.length"
            :options="donutEchartOptions"
          />
          <EmptyState v-else :message="__('Keine Daten')" /></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LucideRefreshCcw from '~icons/lucide/refresh-ccw'
import { createResource, usePageMeta, AxisChart, ECharts } from 'frappe-ui'
import { ref, computed, h, watch } from 'vue'

// frappe-ui chart components
// AxisChart imported from frappe-ui below
// DonutChart imported from frappe-ui below

const periods = [
  { label: 'Woche', value: 'week' },
  { label: 'Monat', value: 'month' },
  { label: 'Quartal', value: 'quarter' },
  { label: 'Jahr', value: 'year' },
]

const activePeriod = ref('month')

const dashboardData = createResource({
  url: 'crm.api.dashboard_custom.get_dashboard_data',
  makeParams() {
    return { period: activePeriod.value }
  },
  auto: true,
})

watch(activePeriod, () => dashboardData.reload())

const data = computed(() => dashboardData.data)

// --- Chart Configs ---

const leadsChartConfig = computed(() => ({
  data: (data.value?.leads?.by_period || []).map(r => ({ ...r, Anzahl: r.count })),
  title: '',
  colors: ['#3b82f6'],
  xAxis: { key: 'label', type: 'category', title: '' },
  yAxis: { title: '' },
  series: [{ name: 'Anzahl', type: 'bar' }],
}))

const dealsChartConfig = computed(() => ({
  data: (data.value?.deals?.by_period || []).map(r => ({ ...r, Anzahl: r.count })),
  title: '',
  colors: ['#22c55e'],
  xAxis: { key: 'label', type: 'category', title: '' },
  yAxis: { title: '' },
  series: [{ name: 'Anzahl', type: 'bar' }],
}))

const donutColors = ['#3b82f6', '#06b6d4', '#f59e0b', '#ef4444', '#8b5cf6', '#6b7280']

const donutEchartOptions = computed(() => {
  const rawData = data.value?.leads?.by_list || []
  const total = rawData.reduce((sum, r) => sum + (r.count || 0), 0)
  const seriesData = rawData.map((r) => ({ name: r.label, value: r.count }))

  return {
    animation: true,
    animationDuration: 700,
    color: donutColors,
    textStyle: { fontFamily: ['InterVar', 'sans-serif'] },
    series: [
      {
        type: 'pie',
        center: ['50%', '45%'],
        radius: ['40%', '70%'],
        data: seriesData,
        label: { show: false },
        labelLine: { show: false },
        emphasis: { scaleSize: 5 },
      },
    ],
    legend: {
      show: true,
      type: 'plain',
      bottom: 0,
      left: 'center',
      orient: 'horizontal',
      itemGap: 12,
      padding: [8, 10, 0, 10],
      formatter: function (name) {
        const item = rawData.find((r) => r.label === name)
        const pct = total > 0 && item ? ((item.count / total) * 100).toFixed(0) : 0
        return name + ' (' + pct + '%)'
      },
      textStyle: {
        padding: [0, 0, 0, -5],
        color: 'var(--ink-gray-8)',
      },
      icon: 'circle',
    },
    tooltip: {
      trigger: 'item',
      confine: true,
      formatter: function (p) {
        const pct = total > 0 ? ((p.value / total) * 100).toFixed(0) : 0
        return '<div class="flex items-center justify-between gap-5">' +
          '<div>' + p.name + '</div>' +
          '<div class="font-bold">' + p.value + ' (' + pct + '%)</div></div>'
      },
    },
  }
})

function formatDays(val) {
  if (!val || val === 0) return '–'
  return `${val} Tage`
}

usePageMeta(() => ({ title: __('Dashboard') }))

// --- KPI Card Component ---
const KpiCard = {
  props: {
    label: String,
    value: [String, Number],
    icon: String,
    color: String,
    subtitle: String,
  },
  setup(props) {
    const colorMap = {
      blue: 'bg-blue-50 text-blue-600 border-blue-100',
      green: 'bg-green-50 text-green-600 border-green-100',
      orange: 'bg-orange-50 text-orange-600 border-orange-100',
      purple: 'bg-purple-50 text-purple-600 border-purple-100',
    }
    const iconMap = {
      users: '👥',
      handshake: '🤝',
      clock: '⏱️',
      'arrow-right': '➡️',
    }
    return () =>
      h(
        'div',
        {
          class:
            'rounded-lg border border-outline-gray-2 bg-surface-white p-4 flex flex-col gap-1',
        },
        [
          h('div', { class: 'flex items-center gap-2' }, [
            h(
              'span',
              {
                class: `inline-flex items-center justify-center w-8 h-8 rounded-md text-sm ${colorMap[props.color] || ''}`,
              },
              iconMap[props.icon] || '📊',
            ),
            h(
              'span',
              { class: 'text-sm font-medium text-ink-gray-5' },
              props.label,
            ),
          ]),
          h(
            'div',
            { class: 'text-2xl font-bold text-ink-gray-9 mt-1' },
            String(props.value),
          ),
          props.subtitle
            ? h(
                'div',
                { class: 'text-xs text-ink-gray-4 mt-0.5' },
                props.subtitle,
              )
            : null,
        ],
      )
  },
}

// --- Empty State ---
const EmptyState = {
  props: { message: String },
  setup(props) {
    return () =>
      h(
        'div',
        { class: 'flex items-center justify-center h-48 text-ink-gray-4 text-sm' },
        props.message,
      )
  },
}
</script>
