<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <div class="flex items-center gap-3">
          <span class="text-lg font-semibold text-ink-gray-7">{{ __('Dashboard') }}</span>
          <div class="flex items-center gap-0.5 bg-surface-gray-1 rounded-lg p-0.5">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              class="px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
              :class="activeTab === tab.key
                ? 'bg-surface-white text-ink-gray-9 shadow-sm'
                : 'text-ink-gray-5 hover:text-ink-gray-7'"
              @click="switchTab(tab.key)"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>
      </template>
      <template #right-header>
        <!-- Übersicht header controls -->
        <div v-if="activeTab === 'uebersicht'" class="flex items-center gap-2">
          <Dropdown
            v-if="salesUsers.data?.length"
            :options="userOptions"
            placement="right"
          >
            <template #default="{ open }">
              <Button
                :label="activeUserLabel"
                :iconRight="open ? 'chevron-up' : 'chevron-down'"
                variant="outline"
                size="sm"
              >
                <template #prefix>
                  <Avatar
                    v-if="activeUser"
                    :label="activeUserLabel"
                    :image="activeUserImage"
                    size="xs"
                  />
                  <FeatherIcon v-else name="users" class="h-3.5 w-3.5" />
                </template>
              </Button>
            </template>
          </Dropdown>
          <div class="h-5 border-l border-outline-gray-2" v-if="salesUsers.data?.length" />
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
        <!-- Mein Tag header controls -->
        <div v-else-if="activeTab === 'meintag'" class="flex items-center gap-2">
          <Button
            :label="__('Aktualisieren')"
            variant="outline"
            size="sm"
            @click="meinTagData.reload()"
            :loading="meinTagData.loading"
          >
            <template #prefix>
              <FeatherIcon name="refresh-cw" class="h-3.5 w-3.5" />
            </template>
          </Button>
        </div>
        <!-- Prämien header controls -->
        <div v-else-if="activeTab === 'praemien'" class="flex items-center gap-2">
          <Dropdown :options="praemienPeriodOptions">
            <template #default="{ open }">
              <Button
                :label="praemienActivePeriodLabel"
                :iconRight="open ? 'chevron-up' : 'chevron-down'"
                variant="outline"
                size="sm"
              />
            </template>
          </Dropdown>
          <Button
            :label="__('Aktualisieren')"
            variant="outline"
            size="sm"
            @click="reloadPraemien"
            :loading="praemienLoading"
          >
            <template #prefix>
              <FeatherIcon name="refresh-cw" class="h-3.5 w-3.5" />
            </template>
          </Button>
          <Button
            v-if="isAdmin"
            :label="__('CSV Export')"
            variant="outline"
            size="sm"
            @click="exportPraemienCSV"
            :loading="praemienExporting"
          >
            <template #prefix>
              <FeatherIcon name="download" class="h-3.5 w-3.5" />
            </template>
          </Button>
        </div>
        <!-- KPI header controls -->
        <div v-else-if="activeTab === 'kpis'" class="flex items-center gap-2">
          <Dropdown :options="kpiPeriodOptions">
            <template #default="{ open }">
              <Button
                :label="kpiActivePeriodLabel"
                :iconRight="open ? 'chevron-up' : 'chevron-down'"
                variant="outline"
                size="sm"
              />
            </template>
          </Dropdown>
          <Dropdown
            v-if="isAdmin && kpiSalesUsers.length"
            :options="kpiUserOptions"
          >
            <template #default="{ open }">
              <Button
                :label="kpiActiveUserLabel"
                :iconRight="open ? 'chevron-up' : 'chevron-down'"
                variant="outline"
                size="sm"
              >
                <template #prefix>
                  <FeatherIcon name="users" class="h-3.5 w-3.5" />
                </template>
              </Button>
            </template>
          </Dropdown>
          <Button
            :label="__('Aktualisieren')"
            variant="outline"
            size="sm"
            @click="reloadKpiData"
            :loading="kpiLoading"
          >
            <template #prefix>
              <FeatherIcon name="refresh-cw" class="h-3.5 w-3.5" />
            </template>
          </Button>
        </div>
      </template>
    </LayoutHeader>

    <!-- ============================================================ -->
    <!-- TAB: UEBERSICHT (GL-Dashboard)                              -->
    <!-- ============================================================ -->
    <div v-show="activeTab === 'uebersicht'" class="flex-1 overflow-y-auto p-5 space-y-5">
      <!-- KPI Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard :label="__('Leads gesamt')" :value="data?.leads?.total ?? 0" icon="users" color="blue" />
        <KpiCard :label="__('Deals gesamt')" :value="data?.deals?.total ?? 0" icon="handshake" color="green" />
        <KpiCard :label="__('Durchschn. Erster Kontakt zu Deal')" :value="formatDays(data?.deals?.avg_first_contact_to_deal)" icon="clock" color="orange" :subtitle="__('Ab erstem Kontaktversuch')" />
        <KpiCard :label="__('Durchschn. Lead zu Deal')" :value="formatDays(data?.process?.avg_lead_to_deal)" icon="arrow-right" color="purple" :subtitle="__('Von Lead-Eingang bis Deal')" />
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 overflow-hidden">
          <h3 class="text-base font-semibold text-ink-gray-9 mb-3">{{ __('Leads pro Zeitraum') }}</h3>
          <div class="h-80 overflow-hidden">
            <AxisChart v-if="leadsChartConfig.data.length" :config="leadsChartConfig" class="w-full h-full" />
            <EmptyState v-else :message="__('Keine Daten')" />
          </div>
        </div>
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 overflow-hidden">
          <h3 class="text-base font-semibold text-ink-gray-9 mb-3">{{ __('Deals pro Zeitraum') }}</h3>
          <div class="h-80 overflow-hidden">
            <AxisChart v-if="dealsChartConfig.data.length" :config="dealsChartConfig" class="w-full h-full" />
            <EmptyState v-else :message="__('Keine Daten')" />
          </div>
        </div>
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 overflow-hidden">
          <h3 class="text-base font-semibold text-ink-gray-9 mb-3">{{ __('Leads nach Liste') }}</h3>
          <div class="h-80 overflow-hidden">
            <ECharts v-if="donutEchartOptions.series[0].data.length" :options="donutEchartOptions" class="w-full h-full" />
            <EmptyState v-else :message="__('Keine Daten')" />
          </div>
        </div>
      </div>

      <!-- Warnings -->
      <div v-if="data?.warnings" class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="rounded-lg border p-4" :class="data.warnings.overdue_count > 0 ? 'border-red-300 bg-red-50' : 'border-outline-gray-2 bg-surface-white'">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-lg text-red-500">!</span>
            <span class="text-sm font-semibold" :class="data.warnings.overdue_count > 0 ? 'text-red-700' : 'text-ink-gray-7'">{{ __('Follow-up Stau') }}</span>
          </div>
          <div class="text-2xl font-bold" :class="data.warnings.overdue_count > 0 ? 'text-red-700' : 'text-ink-gray-9'">{{ data.warnings.overdue_count }}</div>
          <div class="text-xs text-ink-gray-5 mt-1">{{ __('Leads mit überfälligem Follow-up') }}</div>
        </div>
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
          <div class="flex items-center gap-2 mb-1">
            <FeatherIcon name="clock" class="h-4 w-4 text-ink-gray-5" />
            <span class="text-sm font-semibold text-ink-gray-7">{{ __('Reaktionszeit') }}</span>
          </div>
          <div class="text-2xl font-bold text-ink-gray-9">{{ data.warnings.avg_reaction_hours }}h</div>
          <div class="text-xs text-ink-gray-5 mt-1">{{ __('Durchschnitt bis Erstkontakt') }}</div>
        </div>
        <div class="rounded-lg border p-4" :class="data.warnings.noshow_rate > 20 ? 'border-orange-300 bg-orange-50' : 'border-outline-gray-2 bg-surface-white'">
          <div class="flex items-center gap-2 mb-1">
            <FeatherIcon name="user-x" class="h-4 w-4" :class="data.warnings.noshow_rate > 20 ? 'text-orange-600' : 'text-ink-gray-5'" />
            <span class="text-sm font-semibold" :class="data.warnings.noshow_rate > 20 ? 'text-orange-700' : 'text-ink-gray-7'">{{ __('No-Show Rate') }}</span>
          </div>
          <div class="text-2xl font-bold" :class="data.warnings.noshow_rate > 20 ? 'text-orange-700' : 'text-ink-gray-9'">{{ data.warnings.noshow_rate }}%</div>
          <div class="text-xs text-ink-gray-5 mt-1">{{ data.warnings.noshow_count }} {{ __('von') }} {{ data.warnings.termin_total }} {{ __('Terminen') }}</div>
        </div>
      </div>

      <!-- Pipeline Funnel -->
      <div v-if="data?.pipeline?.length" class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
        <h3 class="text-base font-semibold text-ink-gray-9 mb-4">{{ __('Pipeline-Funnel') }}</h3>
        <div class="space-y-2">
          <div v-for="phase in data.pipeline" :key="phase.phase" class="flex items-center gap-3">
            <div class="w-28 text-xs font-medium text-ink-gray-7 text-right truncate">{{ phase.short }}</div>
            <div class="flex-1 h-7 bg-surface-gray-1 rounded-md overflow-hidden relative">
              <div class="h-full rounded-md transition-all duration-500" :style="{ width: Math.max(phase.pct, 2) + '%', backgroundColor: phase.color }"></div>
              <span class="absolute inset-0 flex items-center justify-center text-xs font-semibold" :class="phase.pct > 30 ? 'text-white' : 'text-ink-gray-7'">
                {{ phase.count }} ({{ phase.pct }}%)
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Closings Summary -->
      <div v-if="data?.closings" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="rounded-lg border border-green-200 bg-green-50 p-4">
          <h3 class="text-base font-semibold text-green-800 mb-3">{{ __('Abschlüsse gewonnen') }}</h3>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <div class="text-2xl font-bold text-green-700">{{ data.closings.won.count }}</div>
              <div class="text-xs text-green-600">{{ __('Leads') }}</div>
            </div>
            <div>
              <div class="text-2xl font-bold text-green-700">{{ formatCurrency(data.closings.won.beitrag) }}</div>
              <div class="text-xs text-green-600">{{ __('Monatsbeitrag') }}</div>
            </div>
            <div>
              <div class="text-2xl font-bold text-green-700">{{ formatCurrency(data.closings.won.provision) }}</div>
              <div class="text-xs text-green-600">{{ __('Provision') }}</div>
            </div>
          </div>
        </div>
        <div class="rounded-lg border border-red-200 bg-red-50 p-4">
          <h3 class="text-base font-semibold text-red-800 mb-3">{{ __('Abschlüsse verloren') }}</h3>
          <div class="flex items-start gap-6">
            <div>
              <div class="text-2xl font-bold text-red-700">{{ data.closings.lost.count }}</div>
              <div class="text-xs text-red-600">{{ __('Leads') }}</div>
            </div>
            <div v-if="data.closings.lost.top_reasons?.length" class="flex-1">
              <div class="text-xs font-medium text-red-700 mb-1">{{ __('Top Gruende') }}:</div>
              <div v-for="r in data.closings.lost.top_reasons" :key="r.reason" class="flex items-center justify-between text-xs text-red-600 py-0.5">
                <span>{{ r.reason }}</span>
                <span class="font-semibold">{{ r.count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Termin Stats -->
      <div v-if="data?.termin_stats?.length" class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
        <h3 class="text-base font-semibold text-ink-gray-9 mb-3">{{ __('Termin-Statistik') }}</h3>
        <div class="flex flex-wrap gap-3">
          <div v-for="ts in data.termin_stats" :key="ts.status" class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm" :class="terminStatClass(ts.status)">
            <span class="font-bold">{{ ts.count }}</span>
            <span>{{ ts.status }}</span>
          </div>
        </div>
      </div>

      <!-- Team Performance -->
      <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-semibold text-ink-gray-9">{{ __('Team Performance') }}</h3>
          <div class="flex items-center gap-2">
            <span v-if="teamData?.from_date && teamData?.to_date" class="text-xs text-ink-gray-5">
              {{ teamData.from_date }} - {{ teamData.to_date }}
            </span>
            <Button :label="__('Aktualisieren')" variant="ghost" size="sm" @click="teamPerformance.reload()" :loading="teamPerformance.loading" />
          </div>
        </div>
        <div v-if="teamPerformance.loading && !teamData" class="flex items-center justify-center h-32 text-ink-gray-4 text-sm">
          {{ __('Lade Team-Daten...') }}
        </div>
        <div v-else-if="teamUsers.length === 0" class="flex items-center justify-center h-32 text-ink-gray-4 text-sm">
          {{ __('Keine Team-Daten verfügbar') }}
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-outline-gray-2">
                <th v-for="col in teamColumns" :key="col.key"
                  class="px-3 py-2.5 text-left text-xs font-semibold text-ink-gray-5 uppercase tracking-wider cursor-pointer hover:text-ink-gray-8 select-none whitespace-nowrap"
                  :class="{ 'text-right': col.align === 'right' }"
                  @click="toggleSort(col.key)"
                >
                  <div class="flex items-center gap-1" :class="{ 'justify-end': col.align === 'right' }">
                    <span>{{ col.label }}</span>
                    <span v-if="sortKey === col.key" class="text-blue-500">{{ sortDir === 'asc' ? '\u2191' : '\u2193' }}</span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(user, idx) in sortedTeamUsers" :key="user.email"
                class="border-b border-outline-gray-1 transition-colors"
                :class="[
                  idx === 0 && user.abschluesse_gewonnen > 0 ? 'bg-amber-50/50 ring-1 ring-amber-200' : 'hover:bg-surface-gray-1',
                  activeUser === user.email ? 'bg-blue-50' : '',
                  user.followup_overdue > 3 ? 'border-l-2 border-l-red-400' : '',
                ]"
                style="cursor: pointer"
                @click="selectTeamUser(user.email)"
              >
                <td class="px-3 py-2.5 whitespace-nowrap">
                  <div class="flex items-center gap-2.5">
                    <div class="relative">
                      <Avatar :label="user.full_name" :image="user.user_image" size="sm" />
                      <div v-if="idx === 0 && user.abschluesse_gewonnen > 0"
                        class="absolute -top-1 -right-1 w-4 h-4 bg-amber-400 rounded-full flex items-center justify-center text-[8px] font-bold text-white shadow"
                        title="Top Performer">*</div>
                    </div>
                    <div>
                      <div class="font-medium text-ink-gray-9 text-sm">{{ user.full_name }}</div>
                      <div class="text-xs text-ink-gray-4 truncate max-w-[140px]">{{ user.email }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-3 py-2.5 text-right whitespace-nowrap">
                  <div class="flex flex-col items-end">
                    <span class="font-semibold text-ink-gray-8">{{ user.leads_total }}</span>
                    <span class="text-xs text-ink-gray-4">+{{ user.leads_new }} {{ __('neu') }}</span>
                  </div>
                </td>
                <td class="px-3 py-2.5 text-right whitespace-nowrap">
                  <div class="flex flex-col items-end">
                    <span class="font-semibold text-ink-gray-8">{{ user.termine_gebucht }}</span>
                    <span class="text-xs text-ink-gray-4">{{ user.termine_durchgefuehrt }} {{ __('durchgef.') }}</span>
                  </div>
                </td>
                <td class="px-3 py-2.5 text-right whitespace-nowrap">
                  <div class="flex items-center gap-2 justify-end">
                    <span class="inline-flex items-center rounded px-1.5 py-0.5 text-xs font-bold" :class="user.abschluesse_gewonnen > 0 ? 'bg-green-100 text-green-700' : 'bg-gray-50 text-ink-gray-5'">{{ user.abschluesse_gewonnen }}</span>
                    <span class="text-ink-gray-3">/</span>
                    <span class="inline-flex items-center rounded px-1.5 py-0.5 text-xs font-bold" :class="user.abschluesse_verloren > 0 ? 'bg-red-100 text-red-600' : 'bg-gray-50 text-ink-gray-5'">{{ user.abschluesse_verloren }}</span>
                  </div>
                </td>
                <td class="px-3 py-2.5 text-right whitespace-nowrap">
                  <div class="flex items-center gap-2 justify-end">
                    <div class="w-16 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div class="h-full rounded-full transition-all duration-500" :class="conversionColor(user.conversion_rate)" :style="{ width: Math.min(user.conversion_rate, 100) + '%' }"></div>
                    </div>
                    <span class="font-semibold text-sm min-w-[40px] text-right" :class="conversionTextColor(user.conversion_rate)">{{ user.conversion_rate }}%</span>
                  </div>
                </td>
                <td class="px-3 py-2.5 text-right whitespace-nowrap">
                  <span :class="user.avg_response_time > 48 ? 'text-red-600 font-semibold' : user.avg_response_time > 24 ? 'text-orange-600' : 'text-ink-gray-7'">
                    {{ user.avg_response_time > 0 ? user.avg_response_time + 'h' : '\u2013' }}
                  </span>
                </td>
                <td class="px-3 py-2.5 text-right whitespace-nowrap">
                  <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-bold"
                    :class="user.followup_overdue > 3 ? 'bg-red-100 text-red-700 animate-pulse' : user.followup_overdue > 0 ? 'bg-orange-100 text-orange-700' : 'bg-gray-50 text-ink-gray-4'">
                    {{ user.followup_overdue }}
                  </span>
                </td>
                <td class="px-3 py-2.5 text-right whitespace-nowrap">
                  <span class="text-ink-gray-7">{{ user.cross_sell_rate }}%</span>
                </td>
                <td class="px-3 py-2.5 text-right whitespace-nowrap">
                  <span class="font-semibold" :class="user.provision > 0 ? 'text-green-700' : 'text-ink-gray-5'">
                    {{ user.provision > 0 ? formatCurrency(user.provision) : '\u2013' }}
                  </span>
                </td>
              </tr>
            </tbody>
            <tfoot v-if="teamUsers.length > 1">
              <tr class="bg-surface-gray-1 font-semibold text-ink-gray-8">
                <td class="px-3 py-2.5 text-sm">{{ __('Gesamt') }} ({{ teamUsers.length }})</td>
                <td class="px-3 py-2.5 text-right">{{ teamTotals.leads_total }}</td>
                <td class="px-3 py-2.5 text-right">{{ teamTotals.termine_gebucht }}</td>
                <td class="px-3 py-2.5 text-right">
                  <span class="text-green-700">{{ teamTotals.abschluesse_gewonnen }}</span>
                  <span class="text-ink-gray-3"> / </span>
                  <span class="text-red-600">{{ teamTotals.abschluesse_verloren }}</span>
                </td>
                <td class="px-3 py-2.5 text-right">{{ teamTotals.conversion_rate }}%</td>
                <td class="px-3 py-2.5 text-right">{{ teamTotals.avg_response_time > 0 ? teamTotals.avg_response_time + 'h' : '\u2013' }}</td>
                <td class="px-3 py-2.5 text-right">
                  <span :class="teamTotals.followup_overdue > 0 ? 'text-red-600' : ''">{{ teamTotals.followup_overdue }}</span>
                </td>
                <td class="px-3 py-2.5 text-right">{{ teamTotals.cross_sell_rate }}%</td>
                <td class="px-3 py-2.5 text-right text-green-700">{{ teamTotals.provision > 0 ? formatCurrency(teamTotals.provision) : '\u2013' }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- TAB: MEIN TAG (Personal Dashboard)                           -->
    <!-- ============================================================ -->
    <div v-show="activeTab === 'meintag'" class="flex-1 overflow-y-auto p-5 space-y-5">
      <div v-if="meinTagData.loading && !mtData" class="flex items-center justify-center h-48 text-ink-gray-4 text-sm">
        {{ __('Lade Daten...') }}
      </div>
      <template v-else-if="mtData">
        <!-- Row 1: Personal KPIs -->
        <div class="grid grid-cols-2 lg:grid-cols-6 gap-3">
          <MiniKpi :label="__('Leads heute')" :value="mtData.personal_kpis.leads_today" color="blue" />
          <MiniKpi :label="__('Leads Woche')" :value="mtData.personal_kpis.leads_week" color="blue" />
          <MiniKpi :label="__('Termine heute')" :value="mtData.personal_kpis.termine_today" color="cyan" />
          <MiniKpi :label="__('Termine Woche')" :value="mtData.personal_kpis.termine_week" color="cyan" />
          <MiniKpi :label="__('Abschl. heute')" :value="mtData.personal_kpis.abschluesse_today" color="green" />
          <MiniKpi :label="__('Abschl. Woche')" :value="mtData.personal_kpis.abschluesse_week" color="green" />
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <!-- Left Column: Tasks + Overdue -->
          <div class="lg:col-span-2 space-y-5">
            <!-- Open Leads by Phase -->
            <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
              <div class="flex items-center justify-between mb-3">
                <h3 class="text-base font-semibold text-ink-gray-9">{{ __('Offene Leads') }}</h3>
                <span class="text-sm text-ink-gray-5">{{ mtData.today_tasks.total }} {{ __('gesamt') }}</span>
              </div>
              <div class="space-y-2">
                <div
                  v-for="phase in mtData.today_tasks.by_phase"
                  :key="phase.phase"
                  class="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-surface-gray-1 cursor-pointer transition-colors"
                  @click="goToPhase(phase.phase)"
                >
                  <span class="inline-block h-3 w-3 rounded-full flex-shrink-0" :style="{ backgroundColor: phase.color }"></span>
                  <span class="flex-1 text-sm text-ink-gray-8">{{ phase.short }}</span>
                  <span class="text-sm font-bold text-ink-gray-9 min-w-[32px] text-right">{{ phase.count }}</span>
                </div>
              </div>
            </div>

            <!-- Overdue Follow-ups -->
            <div v-if="mtData.overdue_followups?.length" class="rounded-lg border border-red-200 bg-red-50 p-4">
              <div class="flex items-center gap-2 mb-3">
                <FeatherIcon name="alert-circle" class="h-4 w-4 text-red-600" />
                <h3 class="text-base font-semibold text-red-800">{{ __('Überfällige Follow-ups') }} ({{ mtData.overdue_followups.length }})</h3>
              </div>
              <div class="space-y-1.5">
                <div
                  v-for="fu in mtData.overdue_followups"
                  :key="fu.name"
                  class="flex items-center gap-3 rounded-md bg-white px-3 py-2 border border-red-100 cursor-pointer hover:border-red-300 transition-colors"
                  @click="openLead(fu.name)"
                >
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-ink-gray-9 truncate">{{ fu.lead_name || fu.first_name || fu.name }}</div>
                    <div class="text-xs text-ink-gray-5">{{ fu.custom_followup_grund || fu.custom_liste }}</div>
                  </div>
                  <div class="text-xs text-red-600 font-semibold flex-shrink-0">
                    {{ formatDateShort(fu.custom_naechster_kontakt) }}
                  </div>
                  <span v-if="fu.custom_kontaktversuche > 0" class="text-[10px] text-ink-gray-4">
                    {{ fu.custom_kontaktversuche }}x
                  </span>
                </div>
              </div>
            </div>

            <!-- Today Follow-ups -->
            <div v-if="mtData.today_followups?.length" class="rounded-lg border border-blue-200 bg-blue-50 p-4">
              <div class="flex items-center gap-2 mb-3">
                <FeatherIcon name="phone-call" class="h-4 w-4 text-blue-600" />
                <h3 class="text-base font-semibold text-blue-800">{{ __('Heutige Follow-ups') }} ({{ mtData.today_followups.length }})</h3>
              </div>
              <div class="space-y-1.5">
                <div
                  v-for="fu in mtData.today_followups"
                  :key="fu.name"
                  class="flex items-center gap-3 rounded-md bg-white px-3 py-2 border border-blue-100 cursor-pointer hover:border-blue-300 transition-colors"
                  @click="openLead(fu.name)"
                >
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-ink-gray-9 truncate">{{ fu.lead_name || fu.first_name || fu.name }}</div>
                    <div class="text-xs text-ink-gray-5">{{ fu.custom_followup_grund || fu.custom_liste }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right Column: Prämien + Gamification -->
          <div class="space-y-5">
            <!-- Prämien Summary -->
            <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
              <div class="flex items-center justify-between mb-3">
                <h3 class="text-base font-semibold text-ink-gray-9">{{ __('Prämien (Quartal)') }}</h3>
                <button class="text-xs text-blue-600 hover:underline" @click="switchTab('praemien')">{{ __('Alle anzeigen') }}</button>
              </div>
              <div class="text-2xl font-bold text-green-700 mb-1">{{ formatCurrency(mtData.praemien_summary.quartal_total) }}</div>
              <div class="text-xs text-ink-gray-5 mb-3">{{ mtData.praemien_summary.quartal_count }} {{ __('Leads mit Prämie') }}</div>
              <div v-if="mtData.praemien_summary.last_praemien?.length" class="space-y-1.5">
                <div class="text-xs font-medium text-ink-gray-5 mb-1">{{ __('Letzte Prämien:') }}</div>
                <div
                  v-for="p in mtData.praemien_summary.last_praemien"
                  :key="p.name"
                  class="flex items-center justify-between text-xs py-1 border-b border-outline-gray-1 last:border-0"
                >
                  <span class="text-ink-gray-7 truncate max-w-[120px]">{{ p.lead_name || p.name }}</span>
                  <span class="font-semibold" :class="p.status === 'Ausgezahlt' ? 'text-green-600' : 'text-orange-600'">
                    {{ formatCurrency(p.betrag) }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Gamification (dezent) -->
            <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
              <h3 class="text-base font-semibold text-ink-gray-9 mb-3">{{ __('Tagesfortschritt') }}</h3>
              <!-- Progress bar -->
              <div class="mb-3">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs text-ink-gray-5">{{ mtData.gamification.actions_today }} {{ __('Aktionen heute') }}</span>
                  <span class="text-xs font-semibold text-ink-gray-7">{{ mtData.gamification.daily_points }}/{{ mtData.gamification.daily_target }} {{ __('Pkt.') }}</span>
                </div>
                <div class="h-2.5 bg-surface-gray-2 rounded-full overflow-hidden">
                  <div
                    class="h-full rounded-full transition-all duration-700"
                    :class="mtData.gamification.progress_pct >= 100 ? 'bg-green-500' : mtData.gamification.progress_pct >= 50 ? 'bg-blue-500' : 'bg-blue-300'"
                    :style="{ width: mtData.gamification.progress_pct + '%' }"
                  ></div>
                </div>
              </div>

              <!-- Streak -->
              <div class="flex items-center gap-3 mb-3 py-2 px-3 bg-surface-gray-1 rounded-lg">
                <div class="text-center">
                  <div class="text-lg font-bold text-orange-600">{{ mtData.gamification.streak_current }}</div>
                  <div class="text-[10px] text-ink-gray-5">{{ __('Streak') }}</div>
                </div>
                <div class="h-8 border-l border-outline-gray-2"></div>
                <div class="text-center">
                  <div class="text-lg font-bold text-ink-gray-7">{{ mtData.gamification.streak_best }}</div>
                  <div class="text-[10px] text-ink-gray-5">{{ __('Bester') }}</div>
                </div>
              </div>

              <!-- Recent Badges -->
              <div v-if="mtData.gamification.badges_recent?.length">
                <div class="text-xs font-medium text-ink-gray-5 mb-2">{{ __('Letzte Badges:') }}</div>
                <div class="flex gap-2">
                  <div
                    v-for="badge in mtData.gamification.badges_recent"
                    :key="badge.badge_id"
                    class="flex items-center gap-1.5 bg-amber-50 border border-amber-200 rounded-lg px-2 py-1"
                    :title="badge.badge_name"
                  >
                    <span class="text-sm">{{ badgeIconMap[badge.badge_icon] || badge.badge_icon }}</span>
                    <span class="text-[10px] font-medium text-ink-gray-7">{{ badge.badge_name }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- ============================================================ -->
    <!-- TAB: PRAEMIEN                                                -->
    <!-- ============================================================ -->
    <div v-show="activeTab === 'praemien'" class="flex-1 overflow-y-auto p-5 space-y-5">
      <!-- Summary Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 flex flex-col gap-1">
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-8 h-8 rounded-md text-sm bg-blue-50 text-blue-600 border border-blue-100">
              <FeatherIcon name="dollar-sign" class="h-4 w-4" />
            </span>
            <span class="text-sm font-medium text-ink-gray-5">{{ __('Gesamt Prämien') }}</span>
          </div>
          <div class="text-2xl font-bold text-ink-gray-9 mt-1">{{ formatCurrency(praemienSummary.total_berechnet + praemienSummary.total_ausgezahlt) }}</div>
          <div class="text-xs text-ink-gray-4 mt-0.5">{{ praemienSummary.count_berechnet + praemienSummary.count_ausgezahlt }} {{ __('Leads') }}</div>
        </div>
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 flex flex-col gap-1">
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-8 h-8 rounded-md text-sm bg-green-50 text-green-600 border border-green-100">
              <FeatherIcon name="check-circle" class="h-4 w-4" />
            </span>
            <span class="text-sm font-medium text-ink-gray-5">{{ __('Ausgezahlt') }}</span>
          </div>
          <div class="text-2xl font-bold text-green-700 mt-1">{{ formatCurrency(praemienSummary.total_ausgezahlt) }}</div>
          <div class="text-xs text-ink-gray-4 mt-0.5">{{ praemienSummary.count_ausgezahlt }} {{ __('Leads') }}</div>
        </div>
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 flex flex-col gap-1">
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-8 h-8 rounded-md text-sm bg-orange-50 text-orange-600 border border-orange-100">
              <FeatherIcon name="clock" class="h-4 w-4" />
            </span>
            <span class="text-sm font-medium text-ink-gray-5">{{ __('Ausstehend') }}</span>
          </div>
          <div class="text-2xl font-bold text-orange-700 mt-1">{{ formatCurrency(praemienSummary.total_offen) }}</div>
          <div class="text-xs text-ink-gray-4 mt-0.5">{{ praemienSummary.count_berechnet }} {{ __('offen') }}</div>
        </div>
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 flex flex-col gap-1">
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-8 h-8 rounded-md text-sm bg-purple-50 text-purple-600 border border-purple-100">
              <FeatherIcon name="users" class="h-4 w-4" />
            </span>
            <span class="text-sm font-medium text-ink-gray-5">{{ __('Anzahl Leads') }}</span>
          </div>
          <div class="text-2xl font-bold text-ink-gray-9 mt-1">{{ praemienSummary.count_berechnet + praemienSummary.count_ausgezahlt }}</div>
          <div class="text-xs text-ink-gray-4 mt-0.5">{{ __('mit Prämie') }}</div>
        </div>
      </div>

      <!-- Main Content: Table + Sidebar -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- Prämien per User Table -->
        <div class="lg:col-span-2 rounded-lg border border-outline-gray-2 bg-surface-white">
          <div class="px-4 py-3 border-b border-outline-gray-2">
            <h3 class="text-base font-semibold text-ink-gray-9">{{ __('Prämien pro Mitarbeiter') }}</h3>
          </div>
          <div v-if="praemienByUser.length === 0" class="flex items-center justify-center h-48 text-ink-gray-4 text-sm">
            {{ __('Keine Prämien im gewählten Zeitraum') }}
          </div>
          <div v-else class="divide-y divide-outline-gray-1">
            <div v-for="(userRow, idx) in praemienByUser" :key="userRow.user">
              <div
                class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-surface-gray-1 transition-colors"
                @click="togglePraemienExpand(idx)"
              >
                <FeatherIcon name="chevron-right" class="h-4 w-4 text-ink-gray-5 transition-transform duration-200 flex-shrink-0"
                  :class="{ 'rotate-90': praemienExpandedRows[idx] }" />
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-ink-gray-9 truncate">{{ userRow.full_name || userRow.user }}</div>
                  <div class="text-xs text-ink-gray-4">{{ userRow.user }}</div>
                </div>
                <div class="text-right flex-shrink-0 w-16">
                  <div class="text-xs text-ink-gray-5">{{ __('Anzahl') }}</div>
                  <div class="text-sm font-semibold text-ink-gray-9">{{ userRow.count }}</div>
                </div>
                <div class="text-right flex-shrink-0 w-24">
                  <div class="text-xs text-ink-gray-5">{{ __('Berechnet') }}</div>
                  <div class="text-sm font-semibold text-orange-600">{{ formatCurrency(userRow.berechnet) }}</div>
                </div>
                <div class="text-right flex-shrink-0 w-24">
                  <div class="text-xs text-ink-gray-5">{{ __('Ausgezahlt') }}</div>
                  <div class="text-sm font-semibold text-green-600">{{ formatCurrency(userRow.ausgezahlt) }}</div>
                </div>
                <div class="text-right flex-shrink-0 w-24">
                  <div class="text-xs text-ink-gray-5">{{ __('Gesamt') }}</div>
                  <div class="text-sm font-bold text-ink-gray-9">{{ formatCurrency(userRow.total) }}</div>
                </div>
              </div>
              <div v-if="praemienExpandedRows[idx]" class="bg-surface-gray-1 px-4 py-2">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="text-ink-gray-5 border-b border-outline-gray-2">
                      <th class="text-left py-1.5 font-medium">{{ __('Lead') }}</th>
                      <th class="text-left py-1.5 font-medium">{{ __('Typ') }}</th>
                      <th class="text-right py-1.5 font-medium">{{ __('Prämie') }}</th>
                      <th class="text-center py-1.5 font-medium">{{ __('Status') }}</th>
                      <th class="text-right py-1.5 font-medium">{{ __('Datum') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="lead in userRow.leads" :key="lead.lead"
                      class="border-b border-outline-gray-1 last:border-0 hover:bg-surface-white transition-colors cursor-pointer"
                      @click.stop="openLead(lead.lead)"
                    >
                      <td class="py-1.5 text-ink-gray-8">
                        <span class="font-medium">{{ lead.lead_name || lead.lead }}</span>
                        <span class="text-ink-gray-4 ml-1">({{ lead.lead }})</span>
                      </td>
                      <td class="py-1.5 text-ink-gray-7">{{ lead.spezialist_typ }}</td>
                      <td class="py-1.5 text-right font-semibold text-ink-gray-9">{{ formatCurrency(lead.praemie) }}</td>
                      <td class="py-1.5 text-center">
                        <span class="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold"
                          :class="praemienStatusBadgeClass(lead.status)">
                          {{ lead.status }}
                        </span>
                      </td>
                      <td class="py-1.5 text-right text-ink-gray-6">{{ formatDateShort(lead.datum) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- Sidebar: By Type -->
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white">
          <div class="px-4 py-3 border-b border-outline-gray-2">
            <h3 class="text-base font-semibold text-ink-gray-9">{{ __('Prämien pro Produkttyp') }}</h3>
          </div>
          <div v-if="praemienByTyp.length === 0" class="flex items-center justify-center h-32 text-ink-gray-4 text-sm">
            {{ __('Keine Daten') }}
          </div>
          <div v-else class="divide-y divide-outline-gray-1">
            <div v-for="typRow in praemienByTyp" :key="typRow.typ" class="px-4 py-3">
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-medium text-ink-gray-8">{{ typRow.typ }}</span>
                <span class="text-sm font-bold text-ink-gray-9">{{ formatCurrency(typRow.total) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <div class="flex-1 mr-3">
                  <div class="h-2 bg-surface-gray-2 rounded-full overflow-hidden">
                    <div class="h-full bg-blue-500 rounded-full transition-all duration-500"
                      :style="{ width: praemienTypBarWidth(typRow.total) + '%' }"></div>
                  </div>
                </div>
                <span class="text-xs text-ink-gray-5 flex-shrink-0">{{ typRow.count }} {{ __('Leads') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- TAB: KPIs                                                    -->
    <!-- ============================================================ -->
    <div v-show="activeTab === 'kpis'" class="flex-1 overflow-y-auto p-5 space-y-5">
      <!-- Loading -->
      <div v-if="kpiLoading && !kpiData" class="flex items-center justify-center h-48 text-ink-gray-4 text-sm">
        {{ __('Lade KPI-Daten...') }}
      </div>
      <template v-else-if="kpiData">
        <!-- ── KPI-Karten ──────────────────────────────────────── -->
        <div class="grid grid-cols-2 lg:grid-cols-6 gap-3">
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <div class="text-xs font-medium text-ink-gray-5 truncate">{{ __('Leads gesamt') }}</div>
            <div class="text-2xl font-bold text-ink-gray-9 mt-1">{{ kpiData.general.leads_total }}</div>
            <div class="text-[10px] text-ink-gray-4">{{ __('im Zeitraum') }}</div>
          </div>
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <div class="text-xs font-medium text-ink-gray-5 truncate">{{ __('Terminquote') }}</div>
            <div class="text-2xl font-bold mt-1" :class="kpiData.setter.terminquote >= 30 ? 'text-green-700' : kpiData.setter.terminquote >= 15 ? 'text-orange-600' : 'text-red-600'">{{ kpiData.setter.terminquote }}%</div>
            <div class="text-[10px] text-ink-gray-4">{{ __('Leads mit Termin') }}</div>
          </div>
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <div class="text-xs font-medium text-ink-gray-5 truncate">{{ __('Abschlussquote') }}</div>
            <div class="text-2xl font-bold mt-1" :class="kpiData.closer.abschlussquote >= 50 ? 'text-green-700' : kpiData.closer.abschlussquote >= 25 ? 'text-orange-600' : 'text-red-600'">{{ kpiData.closer.abschlussquote }}%</div>
            <div class="text-[10px] text-ink-gray-4">{{ __('von durchgeführten Terminen') }}</div>
          </div>
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <div class="text-xs font-medium text-ink-gray-5 truncate">{{ __('Show-Rate') }}</div>
            <div class="text-2xl font-bold mt-1" :class="kpiData.closer.show_rate >= 70 ? 'text-green-700' : kpiData.closer.show_rate >= 50 ? 'text-orange-600' : 'text-red-600'">{{ kpiData.closer.show_rate }}%</div>
            <div class="text-[10px] text-ink-gray-4">{{ __('Termine durchgeführt') }}</div>
          </div>
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <div class="text-xs font-medium text-ink-gray-5 truncate">{{ __('Reaktionszeit') }}</div>
            <div class="text-2xl font-bold mt-1" :class="kpiData.general.durchschnittliche_reaktionszeit <= 2 ? 'text-green-700' : kpiData.general.durchschnittliche_reaktionszeit <= 4 ? 'text-orange-600' : 'text-red-600'">{{ kpiData.general.durchschnittliche_reaktionszeit }}h</div>
            <div class="text-[10px] text-ink-gray-4">{{ __('Durchschnitt') }}</div>
          </div>
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <div class="text-xs font-medium text-ink-gray-5 truncate">{{ __('Offene Follow-ups') }}</div>
            <div class="text-2xl font-bold mt-1" :class="kpiData.general.offene_followups > 10 ? 'text-red-600' : kpiData.general.offene_followups > 3 ? 'text-orange-600' : 'text-green-700'">{{ kpiData.general.offene_followups }}</div>
            <div class="text-[10px] text-ink-gray-4">{{ __('überfällig') }}</div>
          </div>
        </div>

        <!-- ── Detaillierte KPIs (2-spaltig) ──────────────────── -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <!-- Generelle KPIs -->
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <h3 class="text-base font-semibold text-ink-gray-9 mb-3">{{ __('Generelle KPIs') }}</h3>
            <div class="space-y-2.5">
              <div class="flex items-center justify-between py-1.5 border-b border-outline-gray-1">
                <span class="text-sm text-ink-gray-6">{{ __('Leads erstellt') }}</span>
                <span class="text-sm font-bold text-ink-gray-9">{{ kpiData.general.leads_total }}</span>
              </div>
              <div class="flex items-center justify-between py-1.5 border-b border-outline-gray-1">
                <span class="text-sm text-ink-gray-6">{{ __('Davon neu (Phase 10)') }}</span>
                <span class="text-sm font-bold text-ink-gray-9">{{ kpiData.general.leads_neu }}</span>
              </div>
              <div class="flex items-center justify-between py-1.5 border-b border-outline-gray-1">
                <span class="text-sm text-ink-gray-6">{{ __('Leads mit Termin') }}</span>
                <span class="text-sm font-bold text-ink-gray-9">{{ kpiData.general.leads_mit_termin }}</span>
              </div>
              <div class="flex items-center justify-between py-1.5 border-b border-outline-gray-1">
                <span class="text-sm text-ink-gray-6">{{ __('Gewonnen') }}</span>
                <span class="text-sm font-bold text-green-700">{{ kpiData.general.abschluesse_gewonnen }}</span>
              </div>
              <div class="flex items-center justify-between py-1.5 border-b border-outline-gray-1">
                <span class="text-sm text-ink-gray-6">{{ __('Verloren') }}</span>
                <span class="text-sm font-bold text-red-600">{{ kpiData.general.abschluesse_verloren }}</span>
              </div>
              <div class="flex items-center justify-between py-1.5 border-b border-outline-gray-1">
                <span class="text-sm text-ink-gray-6">{{ __('Conversion Rate') }}</span>
                <span class="text-sm font-bold" :class="kpiData.general.conversion_rate >= 50 ? 'text-green-700' : 'text-orange-600'">{{ kpiData.general.conversion_rate }}%</span>
              </div>
              <div class="flex items-center justify-between py-1.5">
                <span class="text-sm text-ink-gray-6">{{ __('Follow-up Disziplin') }}</span>
                <span class="text-sm font-bold" :class="kpiData.general.follow_up_disziplin >= 80 ? 'text-green-700' : 'text-orange-600'">{{ kpiData.general.follow_up_disziplin }}%</span>
              </div>
            </div>
          </div>

          <!-- Setter-KPIs -->
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <h3 class="text-base font-semibold text-ink-gray-9 mb-3">{{ __('Setter-KPIs') }}</h3>
            <div class="space-y-2.5">
              <div class="flex items-center justify-between py-1.5 border-b border-outline-gray-1">
                <span class="text-sm text-ink-gray-6">{{ __('Terminquote') }}</span>
                <span class="text-sm font-bold" :class="kpiData.setter.terminquote >= 30 ? 'text-green-700' : 'text-orange-600'">{{ kpiData.setter.terminquote }}%</span>
              </div>
              <div class="flex items-center justify-between py-1.5">
                <span class="text-sm text-ink-gray-6">{{ __('Ø Kontaktversuche') }}</span>
                <span class="text-sm font-bold text-ink-gray-9">{{ kpiData.setter.kontaktversuche_avg }}</span>
              </div>
            </div>
            <!-- Visual: Terminquote gauge -->
            <div class="mt-4 pt-3 border-t border-outline-gray-1">
              <div class="text-xs text-ink-gray-5 mb-2">{{ __('Terminquote-Fortschritt') }}</div>
              <div class="h-4 bg-surface-gray-2 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-700"
                  :class="kpiData.setter.terminquote >= 30 ? 'bg-green-500' : kpiData.setter.terminquote >= 15 ? 'bg-yellow-400' : 'bg-red-400'"
                  :style="{ width: Math.min(kpiData.setter.terminquote, 100) + '%' }">
                </div>
              </div>
              <div class="flex justify-between text-[10px] text-ink-gray-4 mt-1">
                <span>0%</span>
                <span>{{ __('Ziel: 30%') }}</span>
                <span>100%</span>
              </div>
            </div>

            <h3 class="text-base font-semibold text-ink-gray-9 mb-3 mt-6">{{ __('Closer-KPIs') }}</h3>
            <div class="space-y-2.5">
              <div class="flex items-center justify-between py-1.5 border-b border-outline-gray-1">
                <span class="text-sm text-ink-gray-6">{{ __('Show-Rate') }}</span>
                <span class="text-sm font-bold" :class="kpiData.closer.show_rate >= 70 ? 'text-green-700' : 'text-orange-600'">{{ kpiData.closer.show_rate }}%</span>
              </div>
              <div class="flex items-center justify-between py-1.5 border-b border-outline-gray-1">
                <span class="text-sm text-ink-gray-6">{{ __('Abschlussquote') }}</span>
                <span class="text-sm font-bold" :class="kpiData.closer.abschlussquote >= 50 ? 'text-green-700' : 'text-orange-600'">{{ kpiData.closer.abschlussquote }}%</span>
              </div>
              <div class="flex items-center justify-between py-1.5 border-b border-outline-gray-1">
                <span class="text-sm text-ink-gray-6">{{ __('Cross-Selling Quote') }}</span>
                <span class="text-sm font-bold text-ink-gray-9">{{ kpiData.closer.cross_selling_quote }}%</span>
              </div>
              <div class="flex items-center justify-between py-1.5">
                <span class="text-sm text-ink-gray-6">{{ __('Qualifizierte Weiterleitungen') }}</span>
                <span class="text-sm font-bold text-ink-gray-9">{{ kpiData.closer.weiterleitungen }}</span>
              </div>
            </div>
          </div>

          <!-- Funnel -->
          <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
            <h3 class="text-base font-semibold text-ink-gray-9 mb-3">{{ __('Pipeline-Funnel') }}</h3>
            <div v-if="funnelData" class="space-y-2">
              <div v-for="phase in funnelData.phases" :key="phase.phase" class="flex items-center gap-2">
                <div class="w-20 text-[11px] font-medium text-ink-gray-6 text-right truncate">{{ phase.phase }}</div>
                <div class="flex-1 h-6 bg-surface-gray-1 rounded overflow-hidden relative">
                  <div class="h-full rounded transition-all duration-500" :style="{ width: Math.max(phase.percentage, 2) + '%', backgroundColor: phase.color }"></div>
                  <span class="absolute inset-0 flex items-center justify-center text-[10px] font-bold" :class="phase.percentage > 30 ? 'text-white' : 'text-ink-gray-7'">
                    {{ phase.count }} ({{ phase.percentage }}%)
                  </span>
                </div>
              </div>
              <!-- Conversion arrows -->
              <div class="mt-4 pt-3 border-t border-outline-gray-1 grid grid-cols-3 gap-2 text-center">
                <div class="rounded-lg bg-blue-50 border border-blue-100 p-2">
                  <div class="text-[10px] text-ink-gray-5">{{ __('Neu → Termin') }}</div>
                  <div class="text-lg font-bold text-blue-700">{{ funnelData.conversion_10_to_20 }}%</div>
                </div>
                <div class="rounded-lg bg-purple-50 border border-purple-100 p-2">
                  <div class="text-[10px] text-ink-gray-5">{{ __('Termin → Gewonnen') }}</div>
                  <div class="text-lg font-bold text-purple-700">{{ funnelData.conversion_20_to_80 }}%</div>
                </div>
                <div class="rounded-lg bg-green-50 border border-green-100 p-2">
                  <div class="text-[10px] text-ink-gray-5">{{ __('Gesamt-Conversion') }}</div>
                  <div class="text-lg font-bold text-green-700">{{ funnelData.overall_conversion }}%</div>
                </div>
              </div>
              <div class="text-xs text-ink-gray-4 text-center mt-1">{{ funnelData.total_leads }} {{ __('Leads gesamt') }}</div>
            </div>
            <div v-else class="flex items-center justify-center h-32 text-ink-gray-4 text-sm">
              {{ __('Keine Funnel-Daten') }}
            </div>
          </div>
        </div>

        <!-- ── Team-Tabelle (nur Admin/GF) ────────────────────── -->
        <div v-if="isAdmin && teamOverviewData" class="rounded-lg border border-outline-gray-2 bg-surface-white p-4">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-base font-semibold text-ink-gray-9">{{ __('Team-Übersicht') }}</h3>
            <span v-if="teamOverviewData.from_date" class="text-xs text-ink-gray-5">
              {{ teamOverviewData.from_date }} – {{ teamOverviewData.to_date }}
            </span>
          </div>
          <div v-if="teamOverviewData.users?.length === 0" class="text-sm text-ink-gray-4 text-center py-8">
            {{ __('Keine Team-Daten verfügbar') }}
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-outline-gray-2">
                  <th class="px-3 py-2.5 text-left text-xs font-semibold text-ink-gray-5 uppercase tracking-wider">{{ __('Mitarbeiter') }}</th>
                  <th class="px-3 py-2.5 text-right text-xs font-semibold text-ink-gray-5 uppercase tracking-wider">{{ __('Leads') }}</th>
                  <th class="px-3 py-2.5 text-right text-xs font-semibold text-ink-gray-5 uppercase tracking-wider">{{ __('Neu') }}</th>
                  <th class="px-3 py-2.5 text-right text-xs font-semibold text-ink-gray-5 uppercase tracking-wider">{{ __('Gewonnen') }}</th>
                  <th class="px-3 py-2.5 text-right text-xs font-semibold text-ink-gray-5 uppercase tracking-wider">{{ __('Verloren') }}</th>
                  <th class="px-3 py-2.5 text-right text-xs font-semibold text-ink-gray-5 uppercase tracking-wider">{{ __('Quote') }}</th>
                  <th class="px-3 py-2.5 text-right text-xs font-semibold text-ink-gray-5 uppercase tracking-wider">{{ __('Reaktion') }}</th>
                  <th class="px-3 py-2.5 text-right text-xs font-semibold text-ink-gray-5 uppercase tracking-wider">{{ __('Show-Rate') }}</th>
                  <th class="px-3 py-2.5 text-right text-xs font-semibold text-ink-gray-5 uppercase tracking-wider">{{ __('Overdue') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in teamOverviewData.users" :key="u.user"
                  class="border-b border-outline-gray-1 hover:bg-surface-gray-1 transition-colors"
                  :class="u.offene_followups > 5 ? 'border-l-2 border-l-red-400' : ''"
                >
                  <td class="px-3 py-2.5 whitespace-nowrap">
                    <div class="flex items-center gap-2">
                      <Avatar :label="u.full_name" :image="u.user_image" size="xs" />
                      <span class="text-sm font-medium text-ink-gray-9">{{ u.full_name }}</span>
                    </div>
                  </td>
                  <td class="px-3 py-2.5 text-right text-ink-gray-9 font-semibold">{{ u.leads_total }}</td>
                  <td class="px-3 py-2.5 text-right text-ink-gray-7">{{ u.leads_neu }}</td>
                  <td class="px-3 py-2.5 text-right text-green-700 font-semibold">{{ u.leads_gewonnen }}</td>
                  <td class="px-3 py-2.5 text-right text-red-600">{{ u.leads_verloren }}</td>
                  <td class="px-3 py-2.5 text-right">
                    <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold"
                      :class="u.abschlussquote >= 60 ? 'bg-green-100 text-green-700' : u.abschlussquote >= 30 ? 'bg-yellow-100 text-yellow-700' : u.abschlussquote > 0 ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500'">
                      {{ u.abschlussquote }}%
                    </span>
                  </td>
                  <td class="px-3 py-2.5 text-right">
                    <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold"
                      :class="kpiReaktionColor(u.avg_reaktionszeit_h)">
                      {{ u.avg_reaktionszeit_h > 0 ? u.avg_reaktionszeit_h + 'h' : '–' }}
                    </span>
                  </td>
                  <td class="px-3 py-2.5 text-right">
                    <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold"
                      :class="u.show_rate >= 70 ? 'bg-green-100 text-green-700' : u.show_rate >= 50 ? 'bg-yellow-100 text-yellow-700' : u.show_rate > 0 ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500'">
                      {{ u.show_rate > 0 ? u.show_rate + '%' : '–' }}
                    </span>
                  </td>
                  <td class="px-3 py-2.5 text-right">
                    <span v-if="u.offene_followups > 0" class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-bold"
                      :class="u.offene_followups > 5 ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'">
                      {{ u.offene_followups }}
                    </span>
                    <span v-else class="text-xs text-ink-gray-4">–</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ── Warnungen (nur Admin/GF) ───────────────────────── -->
        <div v-if="isAdmin && teamOverviewData?.warnings?.length" class="rounded-lg border border-red-200 bg-red-50 p-4">
          <div class="flex items-center gap-2 mb-3">
            <FeatherIcon name="alert-triangle" class="h-5 w-5 text-red-600" />
            <h3 class="text-base font-semibold text-red-800">{{ __('Frühwarnungen') }} ({{ teamOverviewData.warnings.length }})</h3>
          </div>
          <div class="space-y-2">
            <div v-for="(warning, idx) in teamOverviewData.warnings" :key="idx"
              class="flex items-center gap-3 rounded-md bg-white px-3 py-2.5 border"
              :class="warning.severity === 'danger' ? 'border-red-200' : warning.severity === 'warning' ? 'border-orange-200' : 'border-blue-200'"
            >
              <FeatherIcon :name="warning.icon || 'alert-circle'" class="h-4 w-4 flex-shrink-0"
                :class="warning.severity === 'danger' ? 'text-red-600' : warning.severity === 'warning' ? 'text-orange-500' : 'text-blue-500'" />
              <span class="text-sm flex-1"
                :class="warning.severity === 'danger' ? 'text-red-800 font-semibold' : warning.severity === 'warning' ? 'text-orange-800' : 'text-blue-800'">
                {{ warning.message }}
              </span>
              <span class="text-[10px] uppercase font-bold rounded-full px-2 py-0.5 flex-shrink-0"
                :class="warning.severity === 'danger' ? 'bg-red-100 text-red-700' : warning.severity === 'warning' ? 'bg-orange-100 text-orange-700' : 'bg-blue-100 text-blue-700'">
                {{ warning.severity === 'danger' ? 'Kritisch' : warning.severity === 'warning' ? 'Warnung' : 'Info' }}
              </span>
            </div>
          </div>
        </div>
      </template>
      <!-- No data state -->
      <div v-else class="flex items-center justify-center h-48 text-ink-gray-4 text-sm">
        {{ __('Keine KPI-Daten verfügbar') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import LucideRefreshCcw from '~icons/lucide/refresh-ccw'
import {
  createResource,
  usePageMeta,
  AxisChart,
  ECharts,
  Dropdown,
  Avatar,
  FeatherIcon,
  call,
} from 'frappe-ui'
import { ref, reactive, computed, h, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// ─── Tab Management ──────────────────────────────────────────────────
const tabs = [
  { key: 'uebersicht', label: 'Übersicht' },
  { key: 'meintag', label: 'Mein Tag' },
  { key: 'praemien', label: 'Prämien' },
  { key: 'kpis', label: 'KPIs' },
]

const activeTab = ref('uebersicht')

// Restore tab from query param
onMounted(() => {
  const tabParam = route.query.tab
  if (tabParam && tabs.some(t => t.key === tabParam)) {
    activeTab.value = tabParam
  }
})

function switchTab(key) {
  activeTab.value = key
  router.replace({ query: { ...route.query, tab: key } })
  // Lazy load data when switching to a tab for the first time
  if (key === 'meintag' && !mtData.value) {
    meinTagData.reload()
  }
  if (key === 'praemien' && praemienByUser.value.length === 0) {
    fetchPraemienData()
  }
  if (key === 'kpis' && !kpiData.value) {
    reloadKpiData()
  }
}

// ─── Badge Icon Map ──────────────────────────────────────────────────
const badgeIconMap = {
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

// ═════════════════════════════════════════════════════════════════════
// UEBERSICHT TAB - GL Dashboard
// ═════════════════════════════════════════════════════════════════════

const periods = [
  { label: 'Woche', value: 'week' },
  { label: 'Monat', value: 'month' },
  { label: 'Quartal', value: 'quarter' },
  { label: 'Jahr', value: 'year' },
]

const activePeriod = ref('month')
const activeUser = ref('')

const salesUsers = createResource({
  url: 'crm.api.dashboard_custom.get_sales_users',
  auto: true,
})

const userOptions = computed(() => {
  const users = salesUsers.data || []
  const options = [
    { label: __('Alle'), icon: 'users', onClick: () => { activeUser.value = '' } },
  ]
  users.forEach((u) => {
    options.push({
      label: u.full_name || u.email,
      onClick: () => { activeUser.value = u.email },
    })
  })
  return options
})

const activeUserLabel = computed(() => {
  if (!activeUser.value) return __('Alle')
  const u = (salesUsers.data || []).find((u) => u.email === activeUser.value)
  return u?.full_name || activeUser.value
})

const activeUserImage = computed(() => {
  if (!activeUser.value) return null
  const u = (salesUsers.data || []).find((u) => u.email === activeUser.value)
  return u?.user_image || null
})

const dashboardData = createResource({
  url: 'crm.api.dashboard_custom.get_dashboard_data',
  makeParams() {
    return { period: activePeriod.value, user: activeUser.value }
  },
  auto: true,
})

watch([activePeriod, activeUser], () => {
  dashboardData.reload()
  teamPerformance.reload()
})

const data = computed(() => dashboardData.data)

// Team Performance
const teamPerformance = createResource({
  url: 'crm.api.dashboard_custom.get_team_performance',
  makeParams() {
    return { period: activePeriod.value, user: '' }
  },
  auto: true,
})

const teamData = computed(() => teamPerformance.data)
const teamUsers = computed(() => teamData.value?.users || [])

const sortKey = ref('abschluesse_gewonnen')
const sortDir = ref('desc')

const teamColumns = [
  { key: 'full_name', label: 'Mitarbeiter', align: 'left' },
  { key: 'leads_total', label: 'Leads', align: 'right' },
  { key: 'termine_gebucht', label: 'Termine', align: 'right' },
  { key: 'abschluesse_gewonnen', label: 'Gew./Verl.', align: 'right' },
  { key: 'conversion_rate', label: 'Conv. %', align: 'right' },
  { key: 'avg_response_time', label: 'Reaktion', align: 'right' },
  { key: 'followup_overdue', label: 'Overdue', align: 'right' },
  { key: 'cross_sell_rate', label: 'X-Sell %', align: 'right' },
  { key: 'provision', label: 'Provision', align: 'right' },
]

function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'desc'
  }
}

const sortedTeamUsers = computed(() => {
  const users = [...teamUsers.value]
  const key = sortKey.value
  const dir = sortDir.value === 'asc' ? 1 : -1
  users.sort((a, b) => {
    const aVal = typeof a[key] === 'string' ? a[key].toLowerCase() : (a[key] || 0)
    const bVal = typeof b[key] === 'string' ? b[key].toLowerCase() : (b[key] || 0)
    if (aVal < bVal) return -1 * dir
    if (aVal > bVal) return 1 * dir
    return 0
  })
  return users
})

const teamTotals = computed(() => {
  const users = teamUsers.value
  if (!users.length) return {}
  const sum = (key) => users.reduce((s, u) => s + (u[key] || 0), 0)
  const totalGewonnen = sum('abschluesse_gewonnen')
  const totalVerloren = sum('abschluesse_verloren')
  const totalClosed = totalGewonnen + totalVerloren
  const avgResp = users.filter(u => u.avg_response_time > 0)
  const avgRespTime = avgResp.length > 0
    ? Math.round(avgResp.reduce((s, u) => s + u.avg_response_time, 0) / avgResp.length * 10) / 10
    : 0
  const csUsers = users.filter(u => u.cross_sell_rate > 0)
  const avgCs = csUsers.length > 0
    ? Math.round(csUsers.reduce((s, u) => s + u.cross_sell_rate, 0) / csUsers.length * 10) / 10
    : 0
  return {
    leads_total: sum('leads_total'),
    termine_gebucht: sum('termine_gebucht'),
    abschluesse_gewonnen: totalGewonnen,
    abschluesse_verloren: totalVerloren,
    conversion_rate: totalClosed > 0 ? Math.round(totalGewonnen / totalClosed * 1000) / 10 : 0,
    avg_response_time: avgRespTime,
    followup_overdue: sum('followup_overdue'),
    cross_sell_rate: avgCs,
    provision: sum('provision'),
  }
})

function selectTeamUser(email) {
  activeUser.value = activeUser.value === email ? '' : email
}

function conversionColor(rate) {
  if (rate >= 60) return 'bg-green-500'
  if (rate >= 30) return 'bg-yellow-400'
  if (rate > 0) return 'bg-red-400'
  return 'bg-gray-200'
}

function conversionTextColor(rate) {
  if (rate >= 60) return 'text-green-700'
  if (rate >= 30) return 'text-yellow-700'
  if (rate > 0) return 'text-red-600'
  return 'text-ink-gray-5'
}

// Charts
const leadsChartConfig = computed(() => ({
  data: (data.value?.leads?.by_period || []).map((r) => ({ ...r, Anzahl: r.count })),
  title: '',
  colors: ['#3b82f6'],
  xAxis: { key: 'label', type: 'category', title: '' },
  yAxis: { title: '' },
  series: [{ name: 'Anzahl', type: 'bar' }],
}))

const dealsChartConfig = computed(() => ({
  data: (data.value?.deals?.by_period || []).map((r) => ({ ...r, Anzahl: r.count })),
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
    grid: { containLabel: true },
    series: [{
      type: 'pie',
      center: ['50%', '42%'],
      radius: ['30%', '58%'],
      data: seriesData,
      label: { show: false },
      labelLine: { show: false },
      emphasis: { scaleSize: 5 },
    }],
    legend: {
      show: true,
      type: 'scroll',
      bottom: 0,
      left: 'center',
      orient: 'horizontal',
      itemGap: 8,
      padding: [2, 4, 2, 4],
      itemWidth: 8,
      itemHeight: 8,
      formatter: function (name) {
        const item = rawData.find((r) => r.label === name)
        const pct = total > 0 && item ? ((item.count / total) * 100).toFixed(0) : 0
        return name + ' (' + pct + '%)'
      },
      textStyle: { fontSize: 10, color: 'var(--ink-gray-8)' },
      icon: 'circle',
    },
    tooltip: {
      trigger: 'item', confine: true,
      formatter: function (p) {
        const pct = total > 0 ? ((p.value / total) * 100).toFixed(0) : 0
        return '<div class="flex items-center justify-between gap-5"><div>' + p.name + '</div><div class="font-bold">' + p.value + ' (' + pct + '%)</div></div>'
      },
    },
  }
})

function terminStatClass(status) {
  const map = {
    'Geplant': 'bg-blue-100 text-blue-700',
    'Bestaetigt': 'bg-green-100 text-green-700',
    'Durchgeführt': 'bg-green-50 text-green-800',
    'No-Show': 'bg-red-100 text-red-700',
    'Abgesagt': 'bg-gray-100 text-gray-600',
    'Verschoben': 'bg-amber-100 text-amber-700',
  }
  return map[status] || 'bg-gray-50 text-gray-600'
}

// ═════════════════════════════════════════════════════════════════════
// MEIN TAG TAB - Personal Dashboard
// ═════════════════════════════════════════════════════════════════════

const meinTagData = createResource({
  url: 'crm.api.dashboard_custom.get_mein_tag_data',
  auto: true,
})

const mtData = computed(() => meinTagData.data)

function goToPhase(phase) {
  router.push({ name: 'Leads', query: { phase } })
}

function openLead(leadId) {
  router.push({ name: 'Lead', params: { leadId } })
}

// ═════════════════════════════════════════════════════════════════════
// PRAEMIEN TAB
// ═════════════════════════════════════════════════════════════════════

const praemienPeriods = [
  { label: 'Diesen Monat', value: 'month' },
  { label: 'Dieses Quartal', value: 'quarter' },
  { label: 'Dieses Jahr', value: 'year' },
  { label: 'Alle', value: 'all' },
]

const praemienActivePeriod = ref('month')
const praemienLoading = ref(false)
const praemienExporting = ref(false)
const praemienSummary = ref({
  total_berechnet: 0, total_ausgezahlt: 0, total_offen: 0,
  count_berechnet: 0, count_ausgezahlt: 0,
})
const praemienByUser = ref([])
const praemienByTyp = ref([])
const praemienExpandedRows = reactive({})

const isAdmin = computed(() => {
  const roles = window.frappe?.boot?.user?.roles || []
  return roles.includes('System Manager') || roles.includes('Administrator')
})

const praemienActivePeriodLabel = computed(() => {
  const p = praemienPeriods.find((p) => p.value === praemienActivePeriod.value)
  return p ? __(p.label) : __('Diesen Monat')
})

const praemienPeriodOptions = computed(() =>
  praemienPeriods.map((p) => ({
    label: __(p.label),
    onClick: () => {
      praemienActivePeriod.value = p.value
      fetchPraemienData()
    },
  }))
)

async function fetchPraemienData() {
  praemienLoading.value = true
  try {
    const result = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.get_praemien_uebersicht',
      { period: praemienActivePeriod.value }
    )
    if (result) {
      praemienSummary.value = result.summary || praemienSummary.value
      praemienByUser.value = result.by_user || []
      praemienByTyp.value = result.by_typ || []
    }
  } catch (e) {
    console.error('Error fetching Praemien data:', e)
  } finally {
    praemienLoading.value = false
  }
}

function reloadPraemien() {
  Object.keys(praemienExpandedRows).forEach((k) => delete praemienExpandedRows[k])
  fetchPraemienData()
}

function togglePraemienExpand(idx) {
  if (praemienExpandedRows[idx]) {
    delete praemienExpandedRows[idx]
  } else {
    praemienExpandedRows[idx] = true
  }
}

function exportPraemienCSV() {
  praemienExporting.value = true
  try {
    const url = `/api/method/crm.fcrm.doctype.crm_lead.crm_lead.export_praemien_csv?period=${praemienActivePeriod.value}`
    window.open(url, '_blank')
  } catch (e) {
    console.error('Export error:', e)
  } finally {
    praemienExporting.value = false
  }
}

function praemienStatusBadgeClass(status) {
  switch (status) {
    case 'Ausgezahlt': return 'bg-green-100 text-green-700'
    case 'Berechnet': return 'bg-orange-100 text-orange-700'
    case 'Offen': return 'bg-gray-100 text-gray-600'
    default: return 'bg-gray-100 text-gray-600'
  }
}

const maxPraemienTypTotal = computed(() => {
  if (praemienByTyp.value.length === 0) return 1
  return Math.max(...praemienByTyp.value.map((t) => t.total), 1)
})

function praemienTypBarWidth(total) {
  return Math.max((total / maxPraemienTypTotal.value) * 100, 2)
}

// Auto-load praemien data when switching to praemien tab
onMounted(() => {
  if (activeTab.value === 'praemien') {
    fetchPraemienData()
  }
})



// ═════════════════════════════════════════════════════════════════════
// KPI TAB
// ═════════════════════════════════════════════════════════════════════

const kpiPeriods = [
  { label: 'Diese Woche', value: 'week' },
  { label: 'Diesen Monat', value: 'month' },
  { label: 'Dieses Quartal', value: 'quarter' },
  { label: 'Dieses Jahr', value: 'year' },
]

const kpiActivePeriod = ref('month')
const kpiActiveUser = ref('')
const kpiLoading = ref(false)
const kpiData = ref(null)
const funnelData = ref(null)
const teamOverviewData = ref(null)

const kpiActivePeriodLabel = computed(() => {
  const p = kpiPeriods.find((p) => p.value === kpiActivePeriod.value)
  return p ? __(p.label) : __('Diesen Monat')
})

const kpiPeriodOptions = computed(() =>
  kpiPeriods.map((p) => ({
    label: __(p.label),
    onClick: () => {
      kpiActivePeriod.value = p.value
      reloadKpiData()
    },
  }))
)

const kpiSalesUsers = computed(() => salesUsers.data || [])

const kpiActiveUserLabel = computed(() => {
  if (!kpiActiveUser.value) return __('Alle Mitarbeiter')
  const u = kpiSalesUsers.value.find((u) => u.email === kpiActiveUser.value)
  return u?.full_name || kpiActiveUser.value
})

const kpiUserOptions = computed(() => {
  const users = kpiSalesUsers.value
  const options = [
    { label: __('Alle Mitarbeiter'), onClick: () => { kpiActiveUser.value = ''; reloadKpiData() } },
  ]
  users.forEach((u) => {
    options.push({
      label: u.full_name || u.email,
      onClick: () => { kpiActiveUser.value = u.email; reloadKpiData() },
    })
  })
  return options
})

async function reloadKpiData() {
  kpiLoading.value = true
  try {
    const [kpiResult, funnelResult, teamResult] = await Promise.all([
      call('crm.api.dashboard_custom.get_kpi_dashboard', {
        user: kpiActiveUser.value,
        period: kpiActivePeriod.value,
      }),
      call('crm.api.dashboard_custom.get_funnel_data', {
        period: kpiActivePeriod.value,
      }),
      isAdmin.value
        ? call('crm.api.dashboard_custom.get_team_overview', {
            period: kpiActivePeriod.value,
          })
        : Promise.resolve(null),
    ])
    kpiData.value = kpiResult
    funnelData.value = funnelResult
    teamOverviewData.value = teamResult
  } catch (e) {
    console.error('KPI load error:', e)
  } finally {
    kpiLoading.value = false
  }
}

function kpiReaktionColor(hours) {
  if (hours <= 0) return 'bg-gray-100 text-gray-500'
  if (hours <= 2) return 'bg-green-100 text-green-700'
  if (hours <= 4) return 'bg-yellow-100 text-yellow-700'
  return 'bg-red-100 text-red-700'
}

// ═════════════════════════════════════════════════════════════════════
// SHARED UTILITIES
// ═════════════════════════════════════════════════════════════════════

function formatDays(val) {
  if (!val || val === 0) return '\u2013'
  return `${val} Tage`
}

function formatCurrency(val) {
  if (!val || val === 0) return '0,00 \u20AC'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(val)
}

function formatDateShort(dateStr) {
  if (!dateStr) return '\u2013'
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
  } catch {
    return dateStr
  }
}

usePageMeta(() => ({ title: __('Dashboard') }))

// ─── Sub-Components ──────────────────────────────────────────────────

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
    const iconMap = { users: '\u{1F465}', handshake: '\u{1F91D}', clock: '\u{23F1}\u{FE0F}', 'arrow-right': '\u{27A1}\u{FE0F}' }
    return () =>
      h('div', { class: 'rounded-lg border border-outline-gray-2 bg-surface-white p-4 flex flex-col gap-1' }, [
        h('div', { class: 'flex items-center gap-2' }, [
          h('span', { class: `inline-flex items-center justify-center w-8 h-8 rounded-md text-sm ${colorMap[props.color] || ''}` }, iconMap[props.icon] || '\u{1F4CA}'),
          h('span', { class: 'text-sm font-medium text-ink-gray-5' }, props.label),
        ]),
        h('div', { class: 'text-2xl font-bold text-ink-gray-9 mt-1' }, String(props.value)),
        props.subtitle ? h('div', { class: 'text-xs text-ink-gray-4 mt-0.5' }, props.subtitle) : null,
      ])
  },
}

const MiniKpi = {
  props: {
    label: String,
    value: [String, Number],
    color: { type: String, default: 'blue' },
  },
  setup(props) {
    const colorMap = {
      blue: 'border-blue-100 bg-blue-50',
      cyan: 'border-cyan-100 bg-cyan-50',
      green: 'border-green-100 bg-green-50',
      orange: 'border-orange-100 bg-orange-50',
    }
    const textMap = {
      blue: 'text-blue-700',
      cyan: 'text-cyan-700',
      green: 'text-green-700',
      orange: 'text-orange-700',
    }
    return () =>
      h('div', { class: `rounded-lg border p-3 ${colorMap[props.color] || colorMap.blue}` }, [
        h('div', { class: 'text-xs font-medium text-ink-gray-5 truncate' }, props.label),
        h('div', { class: `text-2xl font-bold mt-0.5 ${textMap[props.color] || textMap.blue}` }, String(props.value ?? 0)),
      ])
  },
}

const EmptyState = {
  props: { message: String },
  setup(props) {
    return () => h('div', { class: 'flex items-center justify-center h-48 text-ink-gray-4 text-sm' }, props.message)
  },
}
</script>
