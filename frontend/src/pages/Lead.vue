<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template v-if="!errorTitle" #right-header>
      <CustomActions
        v-if="document._actions?.length"
        :actions="document._actions"
      />
      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />
      <AssignTo v-model="assignees.data" doctype="CRM Lead" :docname="leadId" />
      <Button
        :label="__('In Deal umwandeln')"
        variant="solid"
        theme="green"
        size="md"
        @click="showConvertToDealModal = true"
      >
        <template #prefix>
          <FeatherIcon name="arrow-right-circle" class="h-4 w-4" />
        </template>
      </Button>
    </template>
  </LayoutHeader>
  <div v-if="doc.name" class="flex h-full overflow-hidden">
    <Tabs
      v-model="tabIndex"
      :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-0 [&_[role='tablist']]:px-5 [&_[role='tablist']]:gap-7.5 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow"
    >
      <template #tab-panel>
        <Activities
          ref="activities"
          doctype="CRM Lead"
          :docname="leadId"
          :tabs="tabs"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          @beforeSave="saveChanges"
          @afterSave="reloadAssignees"
        />
      </template>
    </Tabs>
    <Resizer class="flex flex-col border-l overflow-y-auto" side="right">
      <div
        class="flex h-[45px] cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
        @click="copyToClipboard(leadId)"
      >
        {{ __(leadId) }}
      </div>
      <FileUploader
        @success="(file) => updateField('image', file.file_url)"
        :validateFile="validateIsImageFile"
      >
        <template #default="{ openFileSelector, error }">
          <div class="flex items-center justify-start gap-5 border-b p-5">
            <div class="group relative size-12">
              <Avatar
                size="3xl"
                class="size-12"
                :label="title"
                :image="doc.image"
              />
              <component
                :is="doc.image ? Dropdown : 'div'"
                v-bind="
                  doc.image
                    ? {
                        options: [
                          {
                            icon: 'upload',
                            label: doc.image
                              ? __('Change image')
                              : __('Upload image'),
                            onClick: openFileSelector,
                          },
                          {
                            icon: 'trash-2',
                            label: __('Remove image'),
                            onClick: () => updateField('image', ''),
                          },
                        ],
                      }
                    : { onClick: openFileSelector }
                "
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="z-1 absolute bottom-0.5 left-0 right-0.5 flex h-9 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-3 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                  style="
                    -webkit-clip-path: inset(12px 0 0 0);
                    clip-path: inset(12px 0 0 0);
                  "
                >
                  <CameraIcon class="size-4 cursor-pointer text-white" />
                </div>
              </component>
            </div>
            <div class="flex flex-col gap-2.5 truncate">
              <Tooltip :text="doc.lead_name || __('Set first name')">
                <div class="truncate text-2xl font-medium text-ink-gray-9">
                  {{ title }}
                </div>
              </Tooltip>
              <Tooltip
                v-if="primaryAdvisor"
                :text="primaryAdvisor.since ? __('Primärberater seit') + ' ' + formatRelationshipDate(primaryAdvisor.since) : __('Primärberater')"
              >
                <div class="inline-flex items-center gap-1.5 rounded-full bg-green-100 border border-green-300 px-2.5 py-0.5">
                  <FeatherIcon name="shield" class="h-3.5 w-3.5 text-green-700" />
                  <span class="text-xs font-semibold text-green-800 truncate max-w-[140px]">{{ primaryAdvisor.full_name }}</span>
                </div>
              </Tooltip>
              <div class="flex gap-1.5">
                <Button
                  v-if="callEnabled"
                  :tooltip="__('Make a call')"
                  :icon="PhoneIcon"
                  @click="
                    () => {
                      if (doc.mobile_no) {
                        makeCall(doc.mobile_no)
                                          } else {
                        toast.error(__('No phone number set'))
                      }
                    }
                  "
                />

                <Button
                  :tooltip="__('Send an email')"
                  :icon="Email2Icon"
                  @click="
                    doc.email ? openEmailBoxWithPrompt() : toast.error(__('No email set'))
                  "
                />
                <Button
                  :tooltip="__('Go to website')"
                  :icon="LinkIcon"
                  @click="
                    doc.website
                      ? openWebsite(doc.website)
                      : toast.error(__('No website set'))
                  "
                />

                <Button
                  :tooltip="__('Attach a file')"
                  :icon="AttachmentIcon"
                  @click="showFilesUploader = true"
                />

                <Button
                  v-if="canDelete"
                  :tooltip="__('Delete')"
                  variant="subtle"
                  theme="red"
                  icon="trash-2"
                  @click="deleteLead"
                />
              </div>
              <ErrorMessage :message="__(error)" />
            </div>
          </div>
        </template>
      </FileUploader>
      <!-- Pipeline Phase (Liste) Badge -->
      <div class="sticky top-0 z-10 border-b bg-surface-white px-5 py-3">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5">Pipeline-Phase</span>
        </div>
        <div class="flex items-center gap-2 mb-2">
          <span
            class="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold w-full"
            :class="listePhaseClass"
          >
            <span class="inline-block h-3 w-3 rounded-full flex-shrink-0" :style="{ backgroundColor: listePhaseHex }"></span>
            {{ doc.custom_liste || 'Keine Phase' }}
          </span>
        </div>
        <div class="flex flex-col gap-1 text-xs text-ink-gray-5">
          <div class="flex items-center gap-1.5" v-if="lastStatusChange">
            <FeatherIcon name="clock" class="h-3 w-3" />
            <span>{{ __('Letzte Änderung') }}: {{ lastStatusChange }}</span>
          </div>
          <div class="flex items-center gap-1.5" v-if="lastActivity">
            <FeatherIcon name="activity" class="h-3 w-3" />
            <span>{{ __('Letzte Aktivität') }}: {{ lastActivity }}</span>
          </div>
        </div>
      </div>
      <!-- Primaerberater-Beziehung -->
      <div v-if="primaryAdvisor" class="border-b bg-surface-white px-5 py-3">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5">Primärberater</span>
        </div>
        <div class="flex items-center gap-2 rounded-lg bg-green-50 border border-green-200 px-3 py-2">
          <FeatherIcon name="shield" class="h-4 w-4 text-green-600 flex-shrink-0" />
          <div class="flex flex-col min-w-0">
            <span class="text-sm font-semibold text-green-800 truncate">{{ primaryAdvisor.full_name }}</span>
            <span class="text-xs text-green-600">seit {{ formatRelationshipDate(primaryAdvisor.since) }}</span>
          </div>
        </div>
        <div v-if="primaryAdvisor.lead_typ" class="mt-1.5 text-xs text-ink-gray-5">
          <span>Abschluss-Typ: {{ primaryAdvisor.lead_typ }}</span>
        </div>
      </div>
            <!-- Termin-Info (wenn vorhanden) -->
      <div v-if="doc.custom_termin_datum" class="border-b bg-surface-white px-5 py-3">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5">Termin</span>
        </div>
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center gap-2 text-sm">
            <FeatherIcon name="calendar" class="h-4 w-4 text-ink-gray-5" />
            <span class="font-medium">{{ formatTerminDatum(doc.custom_termin_datum) }}</span>
          </div>
          <div v-if="formatTerminZeit(doc.custom_termin_zeit_von)" class="flex items-center gap-2 text-sm">
            <FeatherIcon name="clock" class="h-4 w-4 text-ink-gray-5" />
            <span class="font-medium">{{ formatTerminZeit(doc.custom_termin_zeit_von) }} Uhr</span>
          </div>
          <div class="flex items-center gap-2">
            <span
              class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold"
              :class="terminStatusClass"
            >
              <FeatherIcon :name="terminStatusIcon" class="h-3 w-3" />
              {{ doc.custom_termin_status || 'Geplant' }}
            </span>
            <span v-if="doc.custom_termin_typ" class="text-xs text-ink-gray-5">{{ doc.custom_termin_typ }}</span>
          </div>
          <div v-if="doc.custom_termin_berater" class="flex items-center gap-2 text-xs text-ink-gray-5">
            <FeatherIcon name="user" class="h-3 w-3" />
            <span>{{ getBeraterDisplayName(doc.custom_termin_berater) }}</span>
          </div>
        </div>
      </div>
      <!-- Cross-Selling Box -->
      <div v-if="showCrossSelling" class="border-b bg-surface-white px-5 py-3">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5">Cross-Selling</span>
        </div>
        <div class="flex flex-col gap-2">
          <!-- Prio 1 (mandatory) -->
          <div v-if="doc.custom_cross_sell_prio1_produkt" class="rounded-lg border border-green-200 bg-green-50 p-2.5">
            <div class="flex items-center justify-between mb-1.5">
              <div class="flex items-center gap-1.5">
                <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-green-600 text-white text-xs font-bold">1</span>
                <span class="text-sm font-semibold text-green-800">{{ doc.custom_cross_sell_prio1_produkt }}</span>
              </div>
              <span class="text-xs font-medium" :class="getCrossSellStatusClass(1)">{{ getCrossSellStatusLabel(1) }}
              <span v-if="doc.custom_cross_sell_prio1_nicht_grund && doc.custom_cross_sell_prio1_status === 'Bewusst nicht angesprochen'" class="text-xs text-gray-500 block mt-0.5">{{ doc.custom_cross_sell_prio1_nicht_grund }}</span></span>
            </div>
            <!-- Referral info (wenn weitergeleitet) -->
            <div v-if="getCrossSellReferral(1)" class="mb-1.5 rounded bg-blue-50 border border-blue-100 px-2 py-1.5">
              <div class="flex items-center gap-1.5 text-xs">
                <FeatherIcon name="external-link" class="h-3 w-3 text-blue-500 flex-shrink-0" />
                <span class="text-blue-700 font-medium">Weitergeleitet am {{ formatReferralDate(getCrossSellReferral(1).creation) }}</span>
              </div>
              <div v-if="getCrossSellReferral(1).target_specialist" class="flex items-center gap-1.5 text-xs mt-0.5 ml-4.5">
                <span class="text-blue-600">Spezialist: {{ getCrossSellReferral(1).target_specialist }}</span>
              </div>
              <div class="flex items-center gap-1.5 text-xs mt-0.5 ml-4.5">
                <span class="inline-flex items-center rounded-full px-1.5 py-0.5 text-xs font-semibold"
                  :class="getReferralStatusClass(getCrossSellReferral(1).referral_status)">
                  {{ getCrossSellReferral(1).referral_status }}
                </span>
              </div>
            </div>
            <div class="flex gap-1.5 mt-1">
              <button
                v-if="!doc.custom_cross_sell_prio1_status || doc.custom_cross_sell_prio1_status === 'Nicht angesprochen'"
                class="flex-1 text-xs font-medium rounded px-2 py-1 bg-green-600 text-white hover:bg-green-700 transition-colors"
                @click="updateField('custom_cross_sell_prio1_status', 'Angesprochen')"
              >
                Angesprochen
              </button>
              <button
                v-if="!doc.custom_cross_sell_prio1_status || doc.custom_cross_sell_prio1_status === 'Nicht angesprochen'"
                class="flex-1 text-xs font-medium rounded px-2 py-1 bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors"
                @click="openBewusstNichtDialog(1)"
              >
                Bewusst nicht
              </button>
              <button
                v-if="doc.custom_cross_sell_prio1_status === 'Angesprochen' && !getCrossSellReferral(1)"
                class="flex-1 text-xs font-medium rounded px-2 py-1 bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                @click="openCrossSellWeiterleitung(1, doc.custom_cross_sell_prio1_produkt)"
              >
                Weiterleiten
              </button>
            </div>
          </div>
          <!-- Prio 2 -->
          <div v-if="doc.custom_cross_sell_prio2_produkt" class="rounded-lg border border-amber-200 bg-amber-50 p-2.5">
            <div class="flex items-center justify-between mb-1.5">
              <div class="flex items-center gap-1.5">
                <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-500 text-white text-xs font-bold">2</span>
                <span class="text-sm font-medium text-amber-800">{{ doc.custom_cross_sell_prio2_produkt }}</span>
              </div>
              <span class="text-xs font-medium" :class="getCrossSellStatusClass(2)">{{ getCrossSellStatusLabel(2) }}
              <span v-if="doc.custom_cross_sell_prio2_nicht_grund && doc.custom_cross_sell_prio2_status === 'Bewusst nicht angesprochen'" class="text-xs text-gray-500 block mt-0.5">{{ doc.custom_cross_sell_prio2_nicht_grund }}</span></span>
            </div>
            <!-- Referral info (wenn weitergeleitet) -->
            <div v-if="getCrossSellReferral(2)" class="mb-1.5 rounded bg-blue-50 border border-blue-100 px-2 py-1.5">
              <div class="flex items-center gap-1.5 text-xs">
                <FeatherIcon name="external-link" class="h-3 w-3 text-blue-500 flex-shrink-0" />
                <span class="text-blue-700 font-medium">Weitergeleitet am {{ formatReferralDate(getCrossSellReferral(2).creation) }}</span>
              </div>
              <div v-if="getCrossSellReferral(2).target_specialist" class="flex items-center gap-1.5 text-xs mt-0.5 ml-4.5">
                <span class="text-blue-600">Spezialist: {{ getCrossSellReferral(2).target_specialist }}</span>
              </div>
              <div class="flex items-center gap-1.5 text-xs mt-0.5 ml-4.5">
                <span class="inline-flex items-center rounded-full px-1.5 py-0.5 text-xs font-semibold"
                  :class="getReferralStatusClass(getCrossSellReferral(2).referral_status)">
                  {{ getCrossSellReferral(2).referral_status }}
                </span>
              </div>
            </div>
            <div class="flex gap-1.5 mt-1">
              <button
                v-if="!doc.custom_cross_sell_prio2_status || doc.custom_cross_sell_prio2_status === 'Nicht angesprochen'"
                class="flex-1 text-xs font-medium rounded px-2 py-1 bg-amber-500 text-white hover:bg-amber-600 transition-colors"
                @click="updateField('custom_cross_sell_prio2_status', 'Angesprochen')"
              >
                Angesprochen
              </button>
              <button
                v-if="!doc.custom_cross_sell_prio2_status || doc.custom_cross_sell_prio2_status === 'Nicht angesprochen'"
                class="flex-1 text-xs font-medium rounded px-2 py-1 bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors"
                @click="openBewusstNichtDialog(2)"
              >
                Bewusst nicht
              </button>
              <button
                v-if="doc.custom_cross_sell_prio2_status === 'Angesprochen' && !getCrossSellReferral(2)"
                class="flex-1 text-xs font-medium rounded px-2 py-1 bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                @click="openCrossSellWeiterleitung(2, doc.custom_cross_sell_prio2_produkt)"
              >
                Weiterleiten
              </button>
            </div>
          </div>
          <!-- Prio 3 -->
          <div v-if="doc.custom_cross_sell_prio3_produkt" class="rounded-lg border border-gray-200 bg-gray-50 p-2.5">
            <div class="flex items-center justify-between mb-1.5">
              <div class="flex items-center gap-1.5">
                <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-gray-400 text-white text-xs font-bold">3</span>
                <span class="text-sm font-medium text-gray-700">{{ doc.custom_cross_sell_prio3_produkt }}</span>
              </div>
              <span class="text-xs font-medium" :class="getCrossSellStatusClass(3)">{{ getCrossSellStatusLabel(3) }}
              <span v-if="doc.custom_cross_sell_prio3_nicht_grund && doc.custom_cross_sell_prio3_status === 'Bewusst nicht angesprochen'" class="text-xs text-gray-500 block mt-0.5">{{ doc.custom_cross_sell_prio3_nicht_grund }}</span></span>
            </div>
            <!-- Referral info (wenn weitergeleitet) -->
            <div v-if="getCrossSellReferral(3)" class="mb-1.5 rounded bg-blue-50 border border-blue-100 px-2 py-1.5">
              <div class="flex items-center gap-1.5 text-xs">
                <FeatherIcon name="external-link" class="h-3 w-3 text-blue-500 flex-shrink-0" />
                <span class="text-blue-700 font-medium">Weitergeleitet am {{ formatReferralDate(getCrossSellReferral(3).creation) }}</span>
              </div>
              <div v-if="getCrossSellReferral(3).target_specialist" class="flex items-center gap-1.5 text-xs mt-0.5 ml-4.5">
                <span class="text-blue-600">Spezialist: {{ getCrossSellReferral(3).target_specialist }}</span>
              </div>
              <div class="flex items-center gap-1.5 text-xs mt-0.5 ml-4.5">
                <span class="inline-flex items-center rounded-full px-1.5 py-0.5 text-xs font-semibold"
                  :class="getReferralStatusClass(getCrossSellReferral(3).referral_status)">
                  {{ getCrossSellReferral(3).referral_status }}
                </span>
              </div>
            </div>
            <div class="flex gap-1.5 mt-1">
              <button
                v-if="!doc.custom_cross_sell_prio3_status || doc.custom_cross_sell_prio3_status === 'Nicht angesprochen'"
                class="flex-1 text-xs font-medium rounded px-2 py-1 bg-gray-500 text-white hover:bg-gray-600 transition-colors"
                @click="updateField('custom_cross_sell_prio3_status', 'Angesprochen')"
              >
                Angesprochen
              </button>
              <button
                v-if="!doc.custom_cross_sell_prio3_status || doc.custom_cross_sell_prio3_status === 'Nicht angesprochen'"
                class="flex-1 text-xs font-medium rounded px-2 py-1 bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors"
                @click="openBewusstNichtDialog(3)"
              >
                Bewusst nicht
              </button>
              <button
                v-if="doc.custom_cross_sell_prio3_status === 'Angesprochen' && !getCrossSellReferral(3)"
                class="flex-1 text-xs font-medium rounded px-2 py-1 bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                @click="openCrossSellWeiterleitung(3, doc.custom_cross_sell_prio3_produkt)"
              >
                Weiterleiten
              </button>
            </div>
          </div>
          <!-- Cross-Sell Notiz -->
          <div v-if="doc.custom_cross_sell_notiz" class="text-xs text-ink-gray-5 mt-1">
            {{ doc.custom_cross_sell_notiz }}
          </div>
        </div>
      </div>
      <!-- Spezialist-Info (wenn weitergeleitet) -->
      <div v-if="doc.custom_an_spezialist_weitergeleitet" class="border-b bg-surface-white px-5 py-3">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5">Spezialist</span>
        </div>
        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 text-sm">
              <FeatherIcon name="user-check" class="h-4 w-4 text-blue-500" />
              <span class="font-medium">{{ doc.custom_spezialist_typ }}</span>
            </div>
            <span
              class="text-xs font-semibold px-2 py-0.5 rounded-full"
              :class="spezialistStatusClass"
            >
              {{ doc.custom_spezialist_status || 'Offen' }}
            </span>
          </div>
          <div v-if="doc.custom_spezialist_user" class="flex items-center gap-2 text-xs text-ink-gray-5">
            <FeatherIcon name="at-sign" class="h-3 w-3" />
            <span>{{ doc.custom_spezialist_user }}</span>
          </div>
          <!-- Premium info (after qualification) -->
          <div v-if="doc.custom_veredelungspraemie && doc.custom_praemie_status" class="flex items-center justify-between text-xs mt-1 rounded bg-green-50 px-2 py-1">
            <span class="text-green-700 font-medium">Prämie: {{ formatPraemie(doc.custom_veredelungspraemie) }}</span>
            <span class="text-green-600">{{ doc.custom_praemie_status }}</span>
          </div>
          <!-- Qualification buttons (only for open/in-progress status) -->
          <div v-if="!doc.custom_spezialist_status || doc.custom_spezialist_status === 'Offen' || doc.custom_spezialist_status === 'In Bearbeitung'" class="flex gap-2 mt-1">
            <button
              v-if="doc.custom_spezialist_status !== 'In Bearbeitung'"
              class="flex-1 text-xs font-medium rounded px-2 py-1.5 bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors"
              @click="updateField('custom_spezialist_status', 'In Bearbeitung')"
            >
              In Bearbeitung
            </button>
            <button
              class="flex-1 text-xs font-medium rounded px-2 py-1.5 bg-green-600 text-white hover:bg-green-700 transition-colors"
              @click="showActionDialog('spezialist_qualifiziert')"
            >
              Qualifiziert
            </button>
            <button
              class="flex-1 text-xs font-medium rounded px-2 py-1.5 bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
              @click="showActionDialog('spezialist_nicht_qualifiziert')"
            >
              Nicht qualifiziert
            </button>
          </div>
        </div>
      </div>
      <!-- Aktionsleiste (One-Click Actions) -->
      <div class="border-b bg-surface-white px-5 py-3">
        <div class="flex items-center gap-2 mb-3">
          <span class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5">Schnellaktionen</span>
        </div>

        <!-- Gruppe: Kontakt -->
        <template v-if="(!isClosedPhase && doc.mobile_no)">
          <div class="mb-1 text-xs font-medium text-ink-gray-4 uppercase tracking-wide">Kontakt</div>
          <div class="flex flex-wrap gap-2 mb-3">
            <Button
              v-if="!isClosedPhase && doc.mobile_no"
              size="sm"
              variant="subtle"
              theme="green"
              @click="handleCall"
            >
              <template #prefix>
                <FeatherIcon name="phone" class="h-3.5 w-3.5" />
              </template>
              {{ __('Anrufen') }}
            </Button>
            <Button
              v-if="!isClosedPhase && doc.mobile_no"
              size="sm"
              variant="subtle"
              theme="green"
              @click="openWhatsApp"
            >
              <template #prefix>
                <FeatherIcon name="message-circle" class="h-3.5 w-3.5" />
              </template>
              {{ __('WhatsApp') }}
            </Button>
          </div>
        </template>

        <!-- Trennlinie -->
        <div v-if="(!isClosedPhase && doc.mobile_no) && !isClosedPhase" class="border-t border-outline-gray-1 mb-3"></div>

        <!-- Gruppe: Terminierung -->
        <template v-if="!isClosedPhase || hasAppointment">
          <div class="mb-1 text-xs font-medium text-ink-gray-4 uppercase tracking-wide">Terminierung</div>
          <div class="flex flex-wrap gap-2 mb-3">
            <Button
              v-if="!isClosedPhase"
              size="sm"
              variant="subtle"
              theme="blue"
              @click="openTerminVorschlaege()"
            >
              <template #prefix>
                <FeatherIcon name="calendar" class="h-3.5 w-3.5" />
              </template>
              {{ __('Termin buchen') }}
            </Button>
            <Button
              v-if="hasAppointment && doc.custom_termin_status === 'Geplant'"
              size="sm"
              variant="subtle"
              theme="blue"
              @click="executeAction('termin_bestaetigen', {})"
            >
              <template #prefix>
                <FeatherIcon name="check" class="h-3.5 w-3.5" />
              </template>
              {{ __('Bestätigen') }}
            </Button>
            <Button
              v-if="hasAppointment && ['Geplant', 'Bestätigt'].includes(doc.custom_termin_status)"
              size="sm"
              variant="subtle"
              theme="green"
              @click="executeAction('termin_durchgefuehrt', {})"
            >
              <template #prefix>
                <FeatherIcon name="check-circle" class="h-3.5 w-3.5" />
              </template>
              {{ __('Durchgeführt') }}
            </Button>
            <Button
              v-if="hasAppointment && ['Geplant', 'Bestätigt'].includes(doc.custom_termin_status)"
              size="sm"
              variant="subtle"
              theme="red"
              @click="executeAction('termin_noshow', {})"
            >
              <template #prefix>
                <FeatherIcon name="user-x" class="h-3.5 w-3.5" />
              </template>
              {{ __('No-Show') }}
            </Button>
            <Button
              v-if="hasAppointment && !['Abgesagt', 'Durchgeführt'].includes(doc.custom_termin_status)"
              size="sm"
              variant="subtle"
              theme="orange"
              @click="showActionDialog('termin_absagen')"
            >
              <template #prefix>
                <FeatherIcon name="x" class="h-3.5 w-3.5" />
              </template>
              {{ __('Absagen') }}
            </Button>
            <Button
              v-if="hasAppointment && !['Durchgeführt', 'Abgesagt'].includes(doc.custom_termin_status)"
              size="sm"
              variant="subtle"
              theme="purple"
              @click="showActionDialog('termin_verschieben')"
            >
              <template #prefix>
                <FeatherIcon name="calendar" class="h-3.5 w-3.5" />
              </template>
              {{ __('Verschieben') }}
            </Button>
            <Button
              v-if="doc.custom_termin_status === 'Durchgeführt' && !doc.custom_setter_bewertung"
              size="sm"
              variant="subtle"
              theme="purple"
              @click="openBewertungDialog()"
            >
              <template #prefix>
                <FeatherIcon name="star" class="h-3.5 w-3.5" />
              </template>
              {{ __('Setter bewerten') }}
            </Button>
          </div>
        </template>

        <!-- Trennlinie -->
        <div v-if="!isClosedPhase" class="border-t border-outline-gray-1 mb-3"></div>

        <!-- Gruppe: Nachfassen -->
        <template v-if="!isClosedPhase">
          <div class="mb-1 text-xs font-medium text-ink-gray-4 uppercase tracking-wide">Nachfassen</div>
          <div class="flex flex-wrap gap-2 mb-3">
            <Button
              v-if="!isClosedPhase"
              size="sm"
              variant="subtle"
              theme="orange"
              @click="showActionDialog('followup_setzen')"
            >
              <template #prefix>
                <FeatherIcon name="clock" class="h-3.5 w-3.5" />
              </template>
              {{ __('Follow-up setzen') }}
            </Button>
            <Button
              v-if="!isClosedPhase"
              size="sm"
              variant="subtle"
              theme="blue"
              @click="activities?.showNoteWithTimer()"
            >
              <template #prefix>
                <FeatherIcon name="bell" class="h-3.5 w-3.5" />
              </template>
              {{ __('Erinnerung') }}
            </Button>

          </div>
        </template>

        <!-- Gruppe: Reaktivierung (nur bei Liste 90) -->
        <template v-if="doc.custom_liste === '90 - Abschluss verloren'">
          <div class="border-t border-outline-gray-1 mb-3"></div>
          <div class="mb-1 text-xs font-medium text-ink-gray-4 uppercase tracking-wide">Reaktivierung</div>
          <div class="flex flex-wrap gap-2 mb-3">
            <Button
              size="sm"
              variant="subtle"
              theme="blue"
              @click="executeAction('reaktivieren', {})"
            >
              <template #prefix>
                <FeatherIcon name="refresh-cw" class="h-3.5 w-3.5" />
              </template>
              {{ __('Reaktivieren') }}
            </Button>
          </div>
        </template>

        <!-- Trennlinie -->
        <div v-if="!isClosedPhase && canSeeAbschluss" class="border-t border-outline-gray-1 mb-3"></div>

        <!-- Gruppe: Abschluss -->
        <template v-if="!isClosedPhase && canSeeAbschluss">
          <div class="mb-1 text-xs font-medium text-ink-gray-4 uppercase tracking-wide">Abschluss</div>
          <div class="flex flex-wrap gap-2 mb-3">
            <Button
              v-if="!isClosedPhase && canSeeAbschluss"
              size="sm"
              variant="subtle"
              theme="green"
              @click="showActionDialog('abschluss_gewonnen')"
            >
              <template #prefix>
                <FeatherIcon name="check-circle" class="h-3.5 w-3.5" />
              </template>
              {{ __('Abschluss gewonnen') }}
            </Button>
            <Button
              v-if="!isClosedPhase && canSeeAbschluss"
              size="sm"
              variant="subtle"
              theme="red"
              @click="showActionDialog('abschluss_verloren')"
            >
              <template #prefix>
                <FeatherIcon name="x-circle" class="h-3.5 w-3.5" />
              </template>
              {{ __('Abschluss verloren') }}
            </Button>
          </div>
        </template>

        <!-- Trennlinie -->
        <div v-if="!isClosedPhase && canSeeSalesActions" class="border-t border-outline-gray-1 mb-3"></div>

        <!-- Gruppe: Weiterleitung -->
        <template v-if="!isClosedPhase && canSeeSalesActions">
          <div class="mb-1 text-xs font-medium text-ink-gray-4 uppercase tracking-wide">Weiterleitung</div>
          <div class="flex flex-wrap gap-2">
            <Button
              v-if="!isClosedPhase && canSeeSalesActions"
              size="sm"
              variant="subtle"
              @click="showActionDialog('an_spezialist_weiterleiten')"
            >
              <template #prefix>
                <FeatherIcon name="arrow-right" class="h-3.5 w-3.5" />
              </template>
              {{ __('An Spezialist weiterleiten') }}
            </Button>
          </div>
        </template>

      </div>
      <SLASection
        v-if="doc.sla_status"
        v-model="doc"
        @updateField="updateField"
      />
      <div
        v-if="sections.data"
        class="flex flex-col"
      >
        <SidePanelLayout
          :sections="sections.data"
          doctype="CRM Lead"
          :docname="leadId"
          @reload="sections.reload"
          @afterFieldChange="reloadAssignees"
        />
      </div>
    </Resizer>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <ConvertToDealModal
    v-if="showConvertToDealModal"
    v-model="showConvertToDealModal"
    :lead="doc"
  />
  <FilesUploader
    v-model="showFilesUploader"
    doctype="CRM Lead"
    :docname="leadId"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Lead'"
    :docname="leadId"
    name="Leads"
  />
  <TerminVorschlaegeDialog
    v-model:show="showTerminVorschlaegeDialog"
    :lead-id="props.leadId"
    @booked="onTerminBooked"
    @manual="onTerminManual"
  />
  <LeadActionDialog
    v-model:show="showActionDialogVisible"
    :action="currentAction"
    :crossSellData="currentCrossSellData"
    :leadId="props.leadId"
    @submit="handleActionSubmit"
    @switchToVorschlaege="onSwitchToVorschlaege"
  />

  <!-- Cross-Sell Bewusst-nicht Grund Dialog -->
  <Dialog v-model="showBewusstNichtDialog" :options="{ title: 'Grund angeben', size: 'sm' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <p class="text-sm text-ink-gray-5">Warum wurde das Cross-Selling-Produkt bewusst nicht angesprochen?</p>
        <textarea
          v-model="bewusstNichtGrund"
          class="w-full rounded border border-outline-gray-2 p-2 text-sm focus:border-blue-500 focus:outline-none"
          rows="3"
          placeholder="z.B. Kunde hat bereits Versicherung, kein Bedarf, etc."
        ></textarea>
        <div class="flex justify-end gap-2">
          <Button variant="subtle" @click="showBewusstNichtDialog = false">Abbrechen</Button>
          <Button variant="solid" theme="blue" @click="submitBewusstNicht">Speichern</Button>
        </div>
      </div>
    </template>
  </Dialog>

  <!-- Setter-Bewertung Dialog -->
  <Dialog v-model="showBewertungDialogVisible" :options="{ title: 'Setter-Qualität bewerten', size: 'sm' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <p class="text-sm text-ink-gray-5">Wie war die Qualität des Setter-Termins?</p>
        <div class="flex gap-2 justify-center py-2">
          <button
            v-for="option in bewertungOptions"
            :key="option.value"
            class="flex flex-col items-center gap-1 rounded-lg border-2 px-3 py-2 transition-colors cursor-pointer"
            :class="bewertungScore === option.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'"
            @click="bewertungScore = option.value"
          >
            <span class="text-lg">{{ option.emoji }}</span>
            <span class="text-xs font-medium" :class="bewertungScore === option.value ? 'text-blue-700' : 'text-gray-600'">{{ option.short }}</span>
          </button>
        </div>
        <textarea
          v-model="bewertungKommentar"
          class="w-full rounded border border-outline-gray-2 p-2 text-sm focus:border-blue-500 focus:outline-none"
          rows="2"
          placeholder="Optionaler Kommentar..."
        ></textarea>
        <div class="flex justify-end gap-2">
          <Button variant="subtle" @click="showBewertungDialogVisible = false">Abbrechen</Button>
          <Button variant="solid" theme="blue" :disabled="!bewertungScore" @click="submitBewertung">Bewertung speichern</Button>
        </div>
      </div>
    </template>
  </Dialog>

</template>
<script setup>
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import ConvertToDealModal from '@/components/Modals/ConvertToDealModal.vue'
import LeadActionDialog from '@/components/LeadActionDialog.vue'
import TerminVorschlaegeDialog from '@/components/TerminVorschlaegeDialog.vue'
import {
  openWebsite,
  setupCustomizations,
  copyToClipboard,
  validateIsImageFile,
  timeAgo,
} from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { whatsappEnabled, callEnabled } from '@/composables/settings'
import { showEventModal, activeEvent, lockedParticipantEmails } from '@/composables/event'
import {
  createResource,
  FileUploader,
  Dialog,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
  FeatherIcon,
} from 'frappe-ui'
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const { brand } = getSettings()
const { $dialog, $socket, makeCall } = globalStore()
const { doctypeMeta } = getMeta('CRM Lead')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  leadId: {
    type: String,
    required: true,
  },
})

const reload = ref(false)
const activities = ref(null)
const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)
const showConvertToDealModal = ref(false)
const showFilesUploader = ref(false)

const { triggerOnChange, assignees, permissions, document, scripts, error } =
  useDocument('CRM Lead', props.leadId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const doc = computed(() => document.doc || {})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? 'Document not found'
        : 'Fehler aufgetreten',
    )
    errorMessage.value = __(err.messages?.[0] || 'An error occurred')
  } else {
    errorTitle.value = ''
    errorMessage.value = ''
  }
})

watch(
  () => document.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField,
        createToast: toast.create,
        deleteDoc: deleteLead,
        call,
      })
      document._actions = s.actions || []
      document._statuses = s.statuses || []
    }
  },
  { once: true },
)

const breadcrumbs = computed(() => {
  let items = [{ label: __('Leads'), route: { name: 'Leads' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Lead')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Leads',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Lead', params: { leadId: props.leadId } },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta['CRM Lead']?.title_field || 'name'
  return doc.value?.[t] || props.leadId
})





// Pipeline Phase (Liste) color mapping
const listePhaseConfig = {
  '10 - Neu ohne Termin': { color: 'gray', hex: '#6B7280' },
  '20 - Termin gebucht': { color: 'blue', hex: '#3B82F6' },
  '30 - Reaktivierung': { color: 'amber', hex: '#F59E0B' },
  '50 - Closer-Termin': { color: 'purple', hex: '#8B5CF6' },
  '70 - Follow-up': { color: 'orange', hex: '#F97316' },
  '80 - Abschluss gewonnen': { color: 'green', hex: '#10B981' },
  '90 - Abschluss verloren': { color: 'red', hex: '#EF4444' },
}

const listePhaseClassMap = {
  gray: 'bg-gray-100 text-gray-800',
  blue: 'bg-blue-100 text-blue-800',
  amber: 'bg-amber-100 text-amber-800',
  purple: 'bg-purple-100 text-purple-800',
  orange: 'bg-orange-100 text-orange-800',
  green: 'bg-green-100 text-green-800',
  red: 'bg-red-100 text-red-800',
}

const listePhaseClass = computed(() => {
  const phase = listePhaseConfig[doc.value.custom_liste]
  if (!phase) return listePhaseClassMap.gray
  return listePhaseClassMap[phase.color] || listePhaseClassMap.gray
})

const listePhaseHex = computed(() => {
  const phase = listePhaseConfig[doc.value.custom_liste]
  return phase ? phase.hex : '#6B7280'
})

const lastStatusChange = computed(() => {
  if (!activities.value?.all_activities?.data?.versions) return null
  const statusChanges = activities.value.all_activities.data.versions.filter(
    a => a.activity_type === 'status_change'
  )
  if (statusChanges.length) {
    const last = statusChanges[statusChanges.length - 1]
    return timeAgo(last.creation)
  }
  return null
})

const lastActivity = computed(() => {
  if (!activities.value?.all_activities?.data?.versions) return null
  const versions = activities.value.all_activities.data.versions
  if (versions.length) {
    const last = versions[versions.length - 1]
    if (last.activity_type === 'communication') return 'E-Mail'
    if (last.activity_type === 'comment') return 'Kommentar'
    if (last.activity_type === 'status_change') return 'Status Update'
    if (last.activity_type === 'incoming_call' || last.activity_type === 'outgoing_call') return 'Anruf'
    return timeAgo(last.creation)
  }
  return null
})

usePageMeta(() => {
  return { title: title.value, icon: brand.favicon }
})

const tabs = computed(() => {
  return [
    {
      name: 'Activity',
      label: __('Alle Aktivitäten'),
      icon: ActivityIcon,
    },
    {
      name: 'StatusUpdates',
      label: __('Status Updates'),
      icon: ActivityIcon,
    },
    {
      name: 'Calls',
      label: __('Anrufe'),
      icon: PhoneIcon,
    },
    {
      name: 'Emails',
      label: __('E-Mails'),
      icon: EmailIcon,
    },
    {
      name: 'Attachments',
      label: __('Anhänge'),
      icon: AttachmentIcon,
    },
    {
      name: 'Events',
      label: __('Veranstaltungen'),
      icon: EventIcon,
    },
    {
      name: 'Notes',
      label: __('Notizen'),
      icon: NoteIcon,
    },
    {
      name: 'InvoiceTool',
      label: __('Angebotstool'),
      icon: DetailsIcon,
    },
    {
      name: 'Data',
      label: __('Daten'),
      icon: DetailsIcon,
    },
  ]
})

const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastLeadTab', 'activity')

// Reset to Activity tab when navigating to a different lead (no URL hash)
watch(() => props.leadId, () => {
  if (!route.hash) {
    tabIndex.value = 0
  }
})

// Primaerberater relationship resource - sucht nach origin_lead
const primaerberaterResource = createResource({
  url: 'crm.fcrm.doctype.crm_lead.crm_lead.get_primary_advisor',
  cache: ['primaryAdvisor', props.leadId],
  params: { lead_name: props.leadId },
  auto: true,
})

const primaerberater = computed(() => {
  return primaerberaterResource.data || {}
})

const primaryAdvisor = computed(() => {
  return primaerberaterResource.data || null
})

function formatRelationshipDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Lead'],
  params: { doctype: 'CRM Lead' },
  auto: true,
})

function updateField(name, value) {
  value = Array.isArray(name) ? '' : value
  let oldValues = Array.isArray(name) ? {} : doc.value[name]

  if (Array.isArray(name)) {
    name.forEach((field) => (doc.value[field] = value))
  } else {
    doc.value[name] = value
  }

  document.save.submit(null, {
    onSuccess: () => (reload.value = true),
    onError: (err) => {
      if (Array.isArray(name)) {
        name.forEach((field) => (doc.value[field] = oldValues[field]))
      } else {
        doc.value[name] = oldValues
      }
      toast.error(err.messages?.[0] || __('Error updating field'))
    },
  })
}

function deleteLead() {
  showDeleteLinkedDocModal.value = true
}

function openEmailBox() {
  let currentTab = tabs.value[tabIndex.value]
  if (!['Emails', 'Comments', 'Activities'].includes(currentTab.name)) {
    activities.value.changeTabTo('emails')
  }
  nextTick(() => (activities.value.emailBox.show = true))
}

function openEmailBoxWithPrompt() {
  openEmailBox()
  // Watch for email reload (indicates email was sent)
  const unwatch = watch(
    () => reload.value,
    (newVal) => {
      if (newVal) {
        unwatch()
      }
    },
  )
  // Auto-cleanup after 5 minutes
  setTimeout(() => unwatch(), 300000)
}

function saveChanges(data) {
  document.save.submit(null, {
    onSuccess: () => reloadAssignees(data),
  })
}

function reloadAssignees(data) {
  if (data?.hasOwnProperty('lead_owner')) {
    assignees.reload()
  }
}

// Status Update Prompt - nach Anruf, E-Mail, Task, Event
const termin_reminder_shown = ref(false)

onMounted(() => {
  // Listen for call events
  $socket.on('crm_call_completed', (data) => {
    if (data.reference_name === props.leadId) {
    }
  })
})

// Termin proximity warning: toast when lead has termin within 2 hours
watch(
  () => doc.value?.custom_termin_datum,
  (terminDatum) => {
    if (!terminDatum || termin_reminder_shown.value) return
    const terminDate = new Date(terminDatum)
    const now = new Date()
    const diffMs = terminDate - now
    const diffMin = Math.round(diffMs / 60000)
    // Only warn if termin is in the future and within 2 hours (120 min)
    if (diffMin > 0 && diffMin <= 120) {
      const terminStatus = doc.value?.custom_termin_status
      if (terminStatus === 'Geplant' || terminStatus === 'Bestätigt') {
        const terminTyp = doc.value?.custom_termin_typ || 'Termin'
        toast.warning(__('Termin in {0} Minuten: {1}', [diffMin, terminTyp]))
        termin_reminder_shown.value = true
      }
    }
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  $socket.off('crm_call_completed')
})

// Reload lead data when EventModal closes (e.g. after Termin buchen)
watch(showEventModal, (newVal, oldVal) => {
  if (!newVal && oldVal) {
    // Modal just closed - reload lead data to reflect phase/status changes
    nextTick(() => {
      document.reload()
      activities.value?.all_activities?.reload()
    })
  }
})

// Trigger status prompt after email send
const originalOpenEmailBox = openEmailBox
watch(
  () => reload.value,
  (newVal) => {
    if (newVal) {
      // Check if latest activity was an email send or call
      // The reload trigger fires after saves including email sends
    }
  },
)


// --- Rollenbasierte Sichtsteuerung ---
const userRoles = computed(() => {
  return window.frappe?.boot?.user?.roles || []
})

const isAdmin = computed(() => {
  return userRoles.value.includes('System Manager') || userRoles.value.includes('Administrator')
})

const isAssignedSpecialist = computed(() => {
  if (!doc.value.custom_an_spezialist_weitergeleitet) return false
  const currentUser = window.frappe?.session?.user || ''
  return doc.value.custom_spezialist_user === currentUser
})

const canSeeAbschluss = computed(() => {
  if (isAdmin.value) return true
  if (isAssignedSpecialist.value) return false
  return true
})

const canSeeSalesActions = computed(() => {
  if (isAdmin.value) return true
  if (isAssignedSpecialist.value) return false
  return true
})

// --- Aktionsleiste (One-Click Actions) ---
const isClosedPhase = computed(() => {
  return ['80 - Abschluss gewonnen', '90 - Abschluss verloren'].includes(doc.value.custom_liste)
})

const hasAppointment = computed(() => {
  return doc.value.custom_termin_datum && ['20 - Termin gebucht', '50 - Closer-Termin'].includes(doc.value.custom_liste)
})

const showCrossSelling = computed(() => {
  if (isClosedPhase.value) return false
  return doc.value.custom_cross_sell_prio1_produkt || doc.value.custom_cross_sell_prio2_produkt || doc.value.custom_cross_sell_prio3_produkt
})

// Cross-Sell Referral data
const leadReferrals = ref([])
const currentCrossSellData = ref(null)

const referralsResource = createResource({
  url: 'crm.fcrm.doctype.crm_referral.crm_referral.get_referrals_for_lead',
  params: { lead_name: props.leadId },
  auto: true,
  onSuccess(data) {
    leadReferrals.value = data || []
  },
})

// Reload referrals when doc reloads
watch(() => reload.value, (val) => {
  if (val) {
    referralsResource.reload()
  }
})

function getCrossSellReferral(prio) {
  return leadReferrals.value.find(
    r => r.created_from === 'Cross-Sell' && String(r.cross_sell_prio) === String(prio)
  )
}

function getCrossSellStatusLabel(prio) {
  const ref = getCrossSellReferral(prio)
  if (ref) return 'Weitergeleitet'
  const statusField = `custom_cross_sell_prio${prio}_status`
  return doc.value[statusField] || 'Nicht angesprochen'
}

function getCrossSellStatusClass(prio) {
  const ref = getCrossSellReferral(prio)
  if (ref) return 'text-blue-600'
  const statusField = `custom_cross_sell_prio${prio}_status`
  const status = doc.value[statusField]
  const map = {
    'Angesprochen': 'text-green-700',
    'Bewusst nicht angesprochen': 'text-gray-500',
    'Weiterleitung erstellt': 'text-blue-600',
    'Nicht angesprochen': 'text-orange-600',
  }
  return map[status] || 'text-orange-600'
}

function getReferralStatusClass(status) {
  const map = {
    'Erstellt': 'bg-blue-100 text-blue-700',
    'Kontaktiert': 'bg-amber-100 text-amber-700',
    'Qualifiziert': 'bg-green-100 text-green-700',
    'Nicht qualifiziert': 'bg-red-100 text-red-700',
    'Ausgezahlt': 'bg-green-100 text-green-800',
  }
  return map[status] || 'bg-gray-100 text-gray-600'
}

function formatReferralDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function openCrossSellWeiterleitung(prio, produkt) {
  currentCrossSellData.value = {
    cross_sell_prio: prio,
    cross_sell_produkt: produkt,
  }
  showActionDialog('an_spezialist_weiterleiten')
}

// Spezialist display helpers
const spezialistStatusClass = computed(() => {
  const map = {
    'Offen': 'bg-blue-100 text-blue-700',
    'In Bearbeitung': 'bg-amber-100 text-amber-700',
    'Qualifiziert': 'bg-green-100 text-green-700',
    'Nicht qualifiziert': 'bg-red-100 text-red-700',
  }
  return map[doc.value.custom_spezialist_status] || 'bg-gray-100 text-gray-600'
})

function formatPraemie(val) {
  if (!val) return '-'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(val)
}

const showActionDialogVisible = ref(false)
const showTerminVorschlaegeDialog = ref(false)
const currentAction = ref('')

// Termin display helpers
const terminStatusStyles = {
  'Geplant': { class: 'bg-blue-100 text-blue-700', icon: 'clock' },
  'Bestätigt': { class: 'bg-green-100 text-green-700', icon: 'check' },
  'Durchgeführt': { class: 'bg-green-100 text-green-800', icon: 'check-circle' },
  'No-Show': { class: 'bg-red-100 text-red-700', icon: 'user-x' },
  'Abgesagt': { class: 'bg-gray-100 text-gray-600', icon: 'x-circle' },
  'Verschoben': { class: 'bg-amber-100 text-amber-700', icon: 'clock' },
}

const terminStatusClass = computed(() => {
  const s = terminStatusStyles[doc.value.custom_termin_status]
  return s ? s.class : terminStatusStyles['Geplant'].class
})

const terminStatusIcon = computed(() => {
  const s = terminStatusStyles[doc.value.custom_termin_status]
  return s ? s.icon : 'clock'
})

function formatTerminDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatTerminDatum(dateStr) {
  if (!dateStr) return ''
  // Handle both datetime (2026-03-05 00:00:00) and date (2026-03-05) formats
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatTerminZeit(timeVal) {
  if (!timeVal) return ''
  const str = String(timeVal)
  // Match HH:MM or HH:MM:SS format (reject microsecond garbage like 21:11:46.096246)
  const match = str.match(/^(\d{1,2}):(\d{2})(?::(?:\d{2}))?$/)
  if (match) {
    return match[1].padStart(2, '0') + ':' + match[2]
  }
  // Handle timedelta-style values (seconds) - skip these
  return ''
}

function getBeraterDisplayName(beraterEmail) {
  if (!beraterEmail) return ''
  // Try to show full name instead of email
  // For now, show a cleaned up version
  const parts = beraterEmail.split('@')
  if (parts.length === 2) {
    // Convert 'vorname.nachname@domain' to 'Vorname Nachname'
    const nameParts = parts[0].split(/[._-]/)
    if (nameParts.length >= 2) {
      return nameParts.map(p => p.charAt(0).toUpperCase() + p.slice(1)).join(' ')
    }
  }
  return beraterEmail
}

function handleCall() {
  if (doc.value.mobile_no) {
    if (callEnabled.value) {
      makeCall(doc.value.mobile_no)
    } else {
      window.open('tel:' + doc.value.mobile_no)
    }
  } else {
    toast.error(__('Keine Telefonnummer hinterlegt'))
  }
}

function openWhatsApp() {
  if (!doc.value.mobile_no) {
    toast.error(__('Keine Telefonnummer hinterlegt'))
    return
  }
  // DSGVO check - WhatsApp opt-in required
  if (!doc.value.custom_dsgvo_whatsapp) {
    toast.warning(__('DSGVO: WhatsApp-Opt-in nicht erteilt. Bitte zuerst Einwilligung einholen.'))
    return
  }
  // Clean phone number (remove spaces, dashes, leading 0, add country code)
  let phone = doc.value.mobile_no.replace(/[\s\-()]/g, '')
  if (phone.startsWith('0')) {
    phone = '+49' + phone.substring(1)
  }
  if (!phone.startsWith('+')) {
    phone = '+49' + phone
  }
  // Open WhatsApp Web
  window.open('https://wa.me/' + phone.replace('+', ''), '_blank')
}

async function openTerminEventModal() {
  // Open the EventModal with the lead's contact as locked participant.
  // Uses custom_contact Link field first, falls back to email lookup.
  const eventData = {}

  if (props.leadId) {
    try {
      const data = await call('frappe.client.get_value', {
        doctype: 'CRM Lead',
        filters: { name: props.leadId },
        fieldname: ['email', 'first_name', 'last_name', 'custom_contact'],
      })
      let contactName = null
      let contactEmail = null

      // Strategy 1: Use the linked custom_contact field directly
      if (data?.custom_contact) {
        try {
          const linked = await call('frappe.client.get_value', {
            doctype: 'Contact',
            filters: { name: data.custom_contact },
            fieldname: ['name', 'email_id'],
          })
          if (linked?.name) {
            contactName = linked.name
            contactEmail = linked.email_id || data?.email
          }
        } catch (e) { /* fallback below */ }
      }

      // Strategy 2: Fallback - find Contact by lead email
      if (!contactName && data?.email) {
        try {
          const found = await call('frappe.client.get_value', {
            doctype: 'Contact',
            filters: { email_id: data.email },
            fieldname: ['name'],
          })
          if (found?.name) {
            contactName = found.name
            contactEmail = data.email
          }
        } catch (e) { /* no contact found */ }
      }

      if (contactName && contactEmail) {
        eventData.event_participants = [
          {
            email: contactEmail,
            reference_doctype: 'Contact',
            reference_docname: contactName,
          },
        ]
        lockedParticipantEmails.value = [contactEmail]
      } else {
        lockedParticipantEmails.value = []
      }
    } catch (err) {
      lockedParticipantEmails.value = []
    }
  } else {
    lockedParticipantEmails.value = []
  }

  // Set reference so EventModal knows this event belongs to this lead
  eventData.reference_doctype = 'CRM Lead'
  eventData.reference_docname = props.leadId

  showEventModal.value = true
  activeEvent.value = eventData
}


function openTerminVorschlaege() {
  showTerminVorschlaegeDialog.value = true
}

// Listen for 'open-termin-vorschlaege' event from EventArea.vue
function handleTerminVorschlaegeEvent() {
  showTerminVorschlaegeDialog.value = true
}
onMounted(() => {
  window.addEventListener('open-termin-vorschlaege', handleTerminVorschlaegeEvent)
})
onBeforeUnmount(() => {
  window.removeEventListener('open-termin-vorschlaege', handleTerminVorschlaegeEvent)
})



async function onTerminBooked(result) {
  toast.success(__('Termin erfolgreich gebucht!'))
  reload.value = true
  // The result comes from execute_lead_action and contains old_liste and phase_changed
  if (result && result.phase_changed) {
    await navigateToNextLead(result.old_liste)
  }
}

function onSwitchToVorschlaege() {
  showActionDialogVisible.value = false
  showTerminVorschlaegeDialog.value = true
}

function onTerminManual(prefill) {
  // Open the classic action dialog with prefilled data
  currentAction.value = 'termin_buchen'
  showActionDialogVisible.value = true
}

function showActionDialog(action) {
  // Reset cross-sell data unless it was set by openCrossSellWeiterleitung
  if (action !== 'an_spezialist_weiterleiten' || !currentCrossSellData.value) {
    currentCrossSellData.value = null
  }
  currentAction.value = action
  showActionDialogVisible.value = true
}

async function handleActionSubmit(action, data) {
  await executeAction(action, data)
  // Reset cross-sell data after submission
  currentCrossSellData.value = null
  // Reload referrals to show updated status
  referralsResource.reload()
}

async function executeAction(action, data) {
  try {
    const result = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.execute_lead_action',
      {
        lead_name: props.leadId,
        action: action,
        data: JSON.stringify(data),
      }
    )

    if (result.success) {
      // Build user-friendly action label
      const actionLabels = {
        termin_buchen: 'Termin gebucht',
        followup_setzen: 'Follow-up gesetzt',
        abschluss_gewonnen: 'Abschluss gewonnen',
        abschluss_verloren: 'Abschluss verloren',
        an_spezialist_weiterleiten: 'An Spezialist weitergeleitet',
        termin_bestaetigen: 'Termin bestätigt',
        termin_durchgefuehrt: 'Termin durchgeführt',
        termin_noshow: 'No-Show markiert',
        termin_absagen: 'Termin abgesagt',
        termin_verschieben: 'Termin verschoben',
        reaktivieren: 'Lead reaktiviert',
        spezialist_qualifiziert: 'Spezialist qualifiziert',
        spezialist_nicht_qualifiziert: 'Spezialist nicht qualifiziert',
      }
      toast.success(actionLabels[action] || action)

      // Reload current doc to show updates
      reload.value = true

      // Only auto-navigate if the phase actually changed
      if (result.phase_changed) {
        // Use the OLD liste (the queue we were working from) to find next lead
        await navigateToNextLead(result.old_liste)
      }
    }
  } catch (err) {
    toast.error(err.messages?.[0] || __('Fehler bei Aktion'))
  }
}

// --- Shared auto-navigate helper ---
// Extract list number for display (e.g. "10 - Neu ohne Termin" -> "10")
function getListeShort(liste) {
  if (!liste) return ''
  const match = liste.match(/^(\d+)/)
  return match ? match[1] : liste
}

async function navigateToNextLead(originListe) {
  try {
    const nextResult = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.get_next_lead',
      {
        current_lead: props.leadId,
        current_phase: originListe || null,
      }
    )

    if (nextResult.all_done) {
      toast.success(__('Alle Leads abgearbeitet!'))
      return
    }

    if (nextResult.next_lead) {
      if (nextResult.same_liste) {
        toast.info(
          __('Weiter in Liste {0} ({1} verbleibend)', [
            getListeShort(nextResult.liste),
            nextResult.remaining,
          ])
        )
      } else {
        toast.info(
          __('Wechsel zu Liste {0} ({1} verbleibend)', [
            getListeShort(nextResult.liste),
            nextResult.remaining,
          ])
        )
      }
      // Small delay so user sees success + info messages
      setTimeout(() => {
        router.push({
          name: 'Lead',
          params: { leadId: nextResult.next_lead },
        })
      }, 1200)
    }
  } catch (e) {
    // Navigation failed - stay on current lead silently
  }
}


// Cross-Sell "Bewusst nicht" reason dialog
const showBewusstNichtDialog = ref(false)
const bewusstNichtPrio = ref(null)
const bewusstNichtGrund = ref('')


function openBewusstNichtDialog(prio) {
  bewusstNichtPrio.value = prio
  bewusstNichtGrund.value = ''
  showBewusstNichtDialog.value = true
}

async function submitBewusstNicht() {
  try {
    await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.update_cross_sell_with_reason',
      {
        lead_name: props.leadId,
        prio: bewusstNichtPrio.value,
        status: 'Bewusst nicht angesprochen',
        grund: bewusstNichtGrund.value || null,
      }
    )
    toast.success(__('Cross-Sell Status aktualisiert'))
    showBewusstNichtDialog.value = false
    reload.value = true
  } catch (err) {
    toast.error(err.messages?.[0] || __('Fehler beim Speichern'))
  }
}

// Setter-Bewertung dialog
const showBewertungDialogVisible = ref(false)
const bewertungScore = ref('')
const bewertungKommentar = ref('')

const bewertungOptions = [
  { value: '1 - Schlecht', emoji: '\u{1F61E}', short: '1' },
  { value: '2 - Ausreichend', emoji: '\u{1F610}', short: '2' },
  { value: '3 - Befriedigend', emoji: '\u{1F642}', short: '3' },
  { value: '4 - Gut', emoji: '\u{1F60A}', short: '4' },
  { value: '5 - Sehr gut', emoji: '\u{1F929}', short: '5' },
]

function openBewertungDialog() {
  bewertungScore.value = ''
  bewertungKommentar.value = ''
  showBewertungDialogVisible.value = true
}

async function submitBewertung() {
  if (!bewertungScore.value) {
    toast.warning(__('Bitte eine Bewertung auswählen'))
    return
  }
  try {
    await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.rate_setter_quality',
      {
        lead_name: props.leadId,
        bewertung: bewertungScore.value,
        kommentar: bewertungKommentar.value || null,
      }
    )
    toast.success(__('Setter-Bewertung gespeichert'))
    showBewertungDialogVisible.value = false
    reload.value = true
  } catch (err) {
    toast.error(err.messages?.[0] || __('Fehler beim Speichern'))
  }
}

defineExpose({})
</script>
