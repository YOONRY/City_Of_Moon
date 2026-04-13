const EVENT_POSITIONS = [
  { x: 16, y: 66 },
  { x: 29, y: 38 },
  { x: 42, y: 56 },
  { x: 56, y: 29 },
  { x: 70, y: 51 },
  { x: 84, y: 24 },
  { x: 88, y: 70 },
  { x: 62, y: 76 },
];

const CATEGORY_VISUALS = {
  person: { accent: "#3d78a5", glyph: "인" },
  info: { accent: "#b3944e", glyph: "정" },
  equipment: { accent: "#4b6f88", glyph: "장" },
};

const CATEGORY_LABELS = {
  person: "인물",
  info: "정보",
  equipment: "장비",
};

const SLOT_LABELS = {
  weapon: "무기",
  armor: "방어구",
  accessory: "악세사리",
};

const TAG_LABELS = {
  route: "경로",
  street: "거리",
  negotiation: "교섭",
  public: "공공",
  shrine: "사원",
  support: "지원",
  covert: "은밀",
  repair: "수리",
  fixer: "해결",
  survival: "생존",
  escort: "호위",
  combat: "전투",
  medical: "의료",
  evidence: "증거",
  permit: "허가",
};

const STAT_LABELS = {
  strength: "근력",
  agility: "민첩",
  intelligence: "지능",
  charm: "매력",
};

const state = {
  payload: null,
  selectedEventIndex: null,
  stagedPrimaryId: null,
  stagedSupportId: null,
  selectedCardId: null,
  draggingCardId: null,
  isMenuOpen: false,
};

const refs = {
  mapSurface: document.getElementById("mapSurface"),
  focusGlow: document.getElementById("focusGlow"),
  statusStrip: document.getElementById("statusStrip"),
  messageBanner: document.getElementById("messageBanner"),
  eventMap: document.getElementById("eventMap"),
  routeLayer: document.getElementById("routeLayer"),
  detailPanel: document.getElementById("detailPanel"),
  cardRail: document.getElementById("cardRail"),
  cardInspector: document.getElementById("cardInspector"),
  gearShell: document.getElementById("gearShell"),
  gearDrawer: document.getElementById("gearDrawer"),
  menuToggle: document.getElementById("menuToggle"),
  menuActions: Array.from(document.querySelectorAll("[data-menu-action]")),
  endDayButton: document.getElementById("endDayButton"),
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function fetchJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`요청 실패: ${response.status}`);
  }
  return response.json();
}

function activeEvent() {
  if (!state.payload || state.payload.events.length === 0) {
    return null;
  }
  return state.payload.events.find((event) => event.isCurrent) ?? state.payload.events[0];
}

function selectedEvent() {
  if (
    !state.payload ||
    state.selectedEventIndex === null ||
    state.selectedEventIndex < 0 ||
    state.selectedEventIndex >= state.payload.events.length
  ) {
    return null;
  }
  return state.payload.events[state.selectedEventIndex];
}

function currentOrSelectedEvent() {
  return selectedEvent() ?? activeEvent();
}

function selectedEventPosition() {
  if (state.selectedEventIndex === null) {
    return null;
  }
  return EVENT_POSITIONS[state.selectedEventIndex % EVENT_POSITIONS.length];
}

function findCard(instanceId) {
  if (!state.payload) {
    return null;
  }
  return state.payload.collection.find((card) => card.instanceId === instanceId) ?? null;
}

function handIndexForCard(instanceId) {
  if (!state.payload) {
    return -1;
  }
  return state.payload.hand.findIndex((card) => card.instanceId === instanceId);
}

function isPerson(card) {
  return card?.category === "person";
}

function isGeneralInfo(card) {
  return card?.category === "info" && card?.infoKind === "general";
}

function isExclusiveInfo(card) {
  return card?.category === "info" && card?.infoKind === "exclusive";
}

function displayStat(statName) {
  return STAT_LABELS[statName] ?? statName;
}

function displayTag(tag) {
  return TAG_LABELS[tag] ?? tag;
}

function displayCategory(card) {
  if (!card) {
    return "";
  }
  const base = CATEGORY_LABELS[card.category] ?? card.category;
  if (card.category === "equipment" && card.equipmentSlot) {
    return `${base} / ${SLOT_LABELS[card.equipmentSlot] ?? card.equipmentSlot}`;
  }
  return base;
}

function statSummary(stats) {
  return ["strength", "agility", "intelligence", "charm"]
    .map((stat) => `${displayStat(stat)} ${stats[stat] ?? 0}`)
    .join(" · ");
}

function eventCheckValue(card, event) {
  if (!card || !event) {
    return 0;
  }
  return event.checkStats.reduce((total, stat) => total + (card.stats?.[stat] ?? 0), 0);
}

function matchesPrimaryRole(card, event) {
  return Boolean(card && event && isPerson(card) && eventCheckValue(card, event) > 0);
}

function matchesSupportRole(card, event) {
  return Boolean(card && event && isGeneralInfo(card) && eventCheckValue(card, event) > 0);
}

function canStagePrimary(card, event) {
  return matchesPrimaryRole(card, event) && card.isUsable;
}

function canStageSupport(card, event) {
  return matchesSupportRole(card, event) && card.isUsable;
}

function cardMatchesEvent(card, event) {
  return matchesPrimaryRole(card, event) || matchesSupportRole(card, event);
}

function currentBusyLabel(card) {
  if (!card.isCommitted) {
    return "";
  }
  return `${card.busyTurnsRemaining}턴`;
}

function cardStateBadge(card, filterEvent) {
  if (card.isCommitted) {
    return { label: currentBusyLabel(card), className: "state-worn" };
  }
  if (card.category === "equipment") {
    return {
      label: card.equippedToName ? "장착됨" : "장비",
      className: "state-preview",
    };
  }
  if (isExclusiveInfo(card)) {
    return { label: "전용 정보", className: "state-preview" };
  }
  if (isGeneralInfo(card)) {
    return { label: "범용 정보", className: "state-preview" };
  }
  if (filterEvent && !filterEvent.isCurrent) {
    return { label: "미리보기", className: "state-preview" };
  }
  return { label: "사용 가능", className: "state-ready" };
}

function cardSecondaryText(card) {
  if (card.category === "equipment") {
    const slot = SLOT_LABELS[card.equipmentSlot] ?? "장비";
    return card.equippedToName ? `${slot} · ${card.equippedToName}` : slot;
  }
  if (card.isCommitted) {
    return `${card.busyTurnsRemaining}턴 남음`;
  }
  return "사용 가능";
}

function eventCheckText(card, event) {
  return `판정 ${eventCheckValue(card, event)} / ${event.difficulty}`;
}

function normalizeState() {
  if (!state.payload) {
    return;
  }

  if (
    state.selectedEventIndex !== null &&
    state.selectedEventIndex >= state.payload.events.length
  ) {
    state.selectedEventIndex = null;
  }

  const event = selectedEvent();
  const stagedPrimary = findCard(state.stagedPrimaryId);
  const stagedSupport = findCard(state.stagedSupportId);

  if (!event || !stagedPrimary || !matchesPrimaryRole(stagedPrimary, event)) {
    state.stagedPrimaryId = null;
  }
  if (!event || !stagedSupport || !matchesSupportRole(stagedSupport, event)) {
    state.stagedSupportId = null;
  }
  if (state.stagedPrimaryId && state.stagedPrimaryId === state.stagedSupportId) {
    state.stagedSupportId = null;
  }
  if (state.selectedCardId && !findCard(state.selectedCardId)) {
    state.selectedCardId = null;
  }
}

function cardsForRail() {
  const event = selectedEvent();
  const cards = event
    ? state.payload.collection.filter((card) => cardMatchesEvent(card, event))
    : [...state.payload.collection];

  cards.sort((left, right) => {
    if (left.category === "equipment" && right.category !== "equipment") {
      return 1;
    }
    if (left.category !== "equipment" && right.category === "equipment") {
      return -1;
    }
    if (left.isUsable !== right.isUsable) {
      return left.isUsable ? -1 : 1;
    }
    return left.name.localeCompare(right.name) || left.instanceId.localeCompare(right.instanceId);
  });

  return cards;
}

function createRoutePath(events) {
  if (events.length === 0) {
    return "";
  }
  const points = events.map((_, index) => EVENT_POSITIONS[index % EVENT_POSITIONS.length]);
  let path = `M ${points[0].x} ${points[0].y}`;
  for (let index = 1; index < points.length; index += 1) {
    const prev = points[index - 1];
    const curr = points[index];
    const cx = (prev.x + curr.x) / 2;
    const cy = (prev.y + curr.y) / 2 + (index % 2 === 0 ? 7 : -7);
    path += ` Q ${cx} ${cy} ${curr.x} ${curr.y}`;
  }
  return path;
}

function renderStatus() {
  refs.statusStrip.innerHTML = "";
  const payload = state.payload;
  const items = [
    ["날짜", payload.day],
    ["돈", `${payload.money} 크라운`],
    ["세금", `${payload.daysUntilTax}일 후`],
    ["가용 인원", payload.readyPeople],
  ];

  items.forEach(([label, value]) => {
    const chip = document.createElement("div");
    chip.className = "status-chip";
    chip.innerHTML = `<strong>${escapeHtml(label)}</strong> ${escapeHtml(value)}`;
    refs.statusStrip.append(chip);
  });
}

function renderMapFocus() {
  const position = selectedEventPosition();
  if (!position) {
    refs.mapSurface.classList.remove("event-focused");
    refs.mapSurface.style.setProperty("--camera-pan-x", "0%");
    refs.mapSurface.style.setProperty("--camera-pan-y", "0%");
    refs.mapSurface.style.setProperty("--camera-scale", "1");
    refs.focusGlow.style.left = "50%";
    refs.focusGlow.style.top = "50%";
    return;
  }

  refs.mapSurface.classList.add("event-focused");
  refs.mapSurface.style.setProperty("--camera-pan-x", `${(50 - position.x) * 0.58}%`);
  refs.mapSurface.style.setProperty("--camera-pan-y", `${(46 - position.y) * 0.58}%`);
  refs.mapSurface.style.setProperty("--camera-scale", "1.22");
  refs.focusGlow.style.left = `${position.x}%`;
  refs.focusGlow.style.top = `${position.y}%`;
}

function renderMap() {
  refs.eventMap.innerHTML = "";
  refs.routeLayer.innerHTML = "";
  const payload = state.payload;

  if (payload.events.length === 0) {
    refs.eventMap.innerHTML = '<div class="empty-card">현재 배치된 이벤트가 없습니다.</div>';
    renderMapFocus();
    return;
  }

  const route = document.createElementNS("http://www.w3.org/2000/svg", "path");
  route.setAttribute("d", createRoutePath(payload.events));
  refs.routeLayer.append(route);

  payload.events.forEach((event, index) => {
    const position = EVENT_POSITIONS[index % EVENT_POSITIONS.length];
    const node = document.createElement("button");
    node.type = "button";
    node.className = "event-node";
    if (event.isCurrent) {
      node.classList.add("current");
    }
    if (state.selectedEventIndex === index) {
      node.classList.add("selected");
    }
    node.style.left = `${position.x}%`;
    node.style.top = `${position.y}%`;
    node.innerHTML = `
      <span class="event-node-index">${index + 1}</span>
      <strong class="event-node-title">${escapeHtml(event.title)}</strong>
    `;
    node.addEventListener("click", () => {
      state.selectedEventIndex = state.selectedEventIndex === index ? null : index;
      state.stagedPrimaryId = null;
      state.stagedSupportId = null;
      render();
    });
    refs.eventMap.append(node);
  });

  renderMapFocus();
}

function equipmentListMarkup(card) {
  if (!card.attachedEquipment || card.attachedEquipment.length === 0) {
    return '<p class="detail-copy">장착한 장비가 없습니다.</p>';
  }
  return `
    <div class="tag-group">
      ${card.attachedEquipment
        .map(
          (item) =>
            `<span class="tag-pill">${escapeHtml(
              `${SLOT_LABELS[item.slot] ?? item.slot} · ${item.name}`,
            )}</span>`,
        )
        .join("")}
    </div>
  `;
}

function renderDetailPanel() {
  const event = currentOrSelectedEvent();
  if (!event) {
    refs.detailPanel.innerHTML = `
      <div class="detail-stack">
        <p class="eyebrow">상황판</p>
        <h3>진행 중인 이벤트가 없습니다</h3>
        <p class="detail-copy">턴 종료로 다음 날을 넘기거나, 술집에서 새 소문을 열어보세요.</p>
      </div>
    `;
    return;
  }

  const filterEvent = selectedEvent();
  const matchingCards = state.payload.collection.filter((card) => cardMatchesEvent(card, event));
  const stagedPrimary = findCard(state.stagedPrimaryId);
  const stagedSupport = findCard(state.stagedSupportId);
  const canCommit =
    Boolean(filterEvent && filterEvent.isCurrent && stagedPrimary && stagedPrimary.isUsable) &&
    (!stagedSupport || stagedSupport.isUsable) &&
    handIndexForCard(stagedPrimary?.instanceId) >= 0 &&
    (!stagedSupport || handIndexForCard(stagedSupport.instanceId) >= 0);

  refs.detailPanel.innerHTML = `
    <div class="detail-stack">
      <div>
        <p class="eyebrow">${filterEvent ? "선택한 이벤트" : "현재 이벤트"}</p>
        <h3>${escapeHtml(event.title)}</h3>
      </div>
      <p class="detail-copy">${escapeHtml(event.description)}</p>
      <div class="detail-meta">
        <span class="detail-stat">체크 ${escapeHtml(event.checkStats.map(displayStat).join(", "))}</span>
        <span class="detail-stat">난도 ${escapeHtml(event.difficulty)}</span>
        <span class="detail-stat">소요 ${escapeHtml(event.timeCost)}턴</span>
        <span class="detail-stat">보수 ${escapeHtml(event.payout)} 크라운</span>
      </div>
      ${
        event.requiredCardNames.length > 0
          ? `
            <div>
              <p class="eyebrow">전용 정보</p>
              <div class="tag-group">
                ${event.requiredCardNames
                  .map((name) => `<span class="tag-pill">${escapeHtml(name)}</span>`)
                  .join("")}
              </div>
            </div>
          `
          : ""
      }
      <div>
        <p class="eyebrow">배치 가능한 카드</p>
        <div class="detail-meta">
          <span class="detail-stat">${escapeHtml(matchingCards.length)}장</span>
        </div>
      </div>
      ${
        filterEvent
          ? `
            <div class="drop-lab">
              <p class="eyebrow">인물 슬롯</p>
              <div class="drop-zone${stagedPrimary ? " has-card" : ""}" data-drop-zone="primary">
                ${dropZoneMarkup(stagedPrimary, event)}
              </div>
              <p class="eyebrow">범용 정보 슬롯</p>
              <div class="drop-zone${stagedSupport ? " has-card" : ""}" data-drop-zone="support">
                ${dropZoneMarkup(stagedSupport, event)}
              </div>
              <div class="drop-actions">
                <button class="play-button" type="button" data-commit-card ${canCommit ? "" : "disabled"}>배치 카드 사용</button>
                <button class="chrome-button" type="button" data-clear-primary ${stagedPrimary ? "" : "disabled"}>인물 비우기</button>
                <button class="chrome-button" type="button" data-clear-support ${stagedSupport ? "" : "disabled"}>정보 비우기</button>
                ${
                  filterEvent.isCurrent && !state.payload.isOver
                    ? '<button class="chrome-button danger" type="button" data-skip-event>넘기기</button>'
                    : ""
                }
              </div>
            </div>
          `
          : `
            <div>
              <p class="eyebrow">필요 태그</p>
              <div class="tag-group">
                ${event.requiredTags.map((tag) => `<span class="tag-pill">${escapeHtml(displayTag(tag))}</span>`).join("")}
              </div>
            </div>
          `
      }
    </div>
  `;

  bindDetailPanelActions(filterEvent, event);
}

function dropZoneMarkup(card, event) {
  if (!card) {
    return '<div class="drop-zone-placeholder" aria-hidden="true"></div>';
  }
  const badge = cardStateBadge(card, event);
  return `
    <div class="drop-card">
      <div class="drop-card-header">
        <div>
          <p class="eyebrow">${escapeHtml(displayCategory(card))}</p>
          <h4 class="drop-card-title">${escapeHtml(card.name)}</h4>
        </div>
        <span class="card-badge ${badge.className}">${escapeHtml(badge.label)}</span>
      </div>
      <p class="drop-card-copy">${escapeHtml(card.description)}</p>
      <div class="stat-row">
        <span class="stat-chip">${escapeHtml(statSummary(card.stats))}</span>
        <span class="stat-chip">${escapeHtml(cardSecondaryText(card))}</span>
      </div>
      <div class="stat-row">
        <span class="stat-chip">${escapeHtml(eventCheckText(card, event))}</span>
      </div>
    </div>
  `;
}

function bindDetailPanelActions(filterEvent, event) {
  const primaryZone = refs.detailPanel.querySelector('[data-drop-zone="primary"]');
  const supportZone = refs.detailPanel.querySelector('[data-drop-zone="support"]');
  const commitButton = refs.detailPanel.querySelector("[data-commit-card]");
  const clearPrimaryButton = refs.detailPanel.querySelector("[data-clear-primary]");
  const clearSupportButton = refs.detailPanel.querySelector("[data-clear-support]");
  const skipButton = refs.detailPanel.querySelector("[data-skip-event]");

  if (primaryZone) {
    bindDropZone(primaryZone, (card) => matchesPrimaryRole(card, event), (card) => {
      state.stagedPrimaryId = card.instanceId;
      if (state.stagedSupportId === card.instanceId) {
        state.stagedSupportId = null;
      }
      render();
    });
  }

  if (supportZone) {
    bindDropZone(supportZone, (card) => matchesSupportRole(card, event), (card) => {
      state.stagedSupportId = card.instanceId;
      if (state.stagedPrimaryId === card.instanceId) {
        state.stagedPrimaryId = null;
      }
      render();
    });
  }

  if (commitButton) {
    commitButton.addEventListener("click", async () => {
      const primaryIndex = handIndexForCard(state.stagedPrimaryId);
      const supportIndex = state.stagedSupportId ? handIndexForCard(state.stagedSupportId) : -1;
      if (primaryIndex >= 0 && filterEvent?.isCurrent) {
        await postAction("/api/play", {
          handIndex: primaryIndex,
          supportHandIndex: supportIndex >= 0 ? supportIndex : null,
        });
      }
    });
  }

  clearPrimaryButton?.addEventListener("click", () => {
    state.stagedPrimaryId = null;
    render();
  });

  clearSupportButton?.addEventListener("click", () => {
    state.stagedSupportId = null;
    render();
  });

  skipButton?.addEventListener("click", async () => {
    await postAction("/api/skip");
  });
}

function bindDropZone(element, matcher, onDropCard) {
  element.addEventListener("dragenter", (event) => {
    event.preventDefault();
    element.classList.add("is-over");
  });
  element.addEventListener("dragover", (event) => {
    event.preventDefault();
    element.classList.add("is-over");
  });
  element.addEventListener("dragleave", () => {
    element.classList.remove("is-over");
  });
  element.addEventListener("drop", (event) => {
    event.preventDefault();
    element.classList.remove("is-over");
    const droppedId =
      state.draggingCardId ||
      event.dataTransfer?.getData("text/plain") ||
      "";
    const card = findCard(droppedId);
    if (card && matcher(card)) {
      onDropCard(card);
    }
  });
}

function renderMessage() {
  refs.messageBanner.textContent = state.payload.message;
  refs.messageBanner.className = "message-banner";
  if (state.payload.isWon) {
    refs.messageBanner.classList.add("win");
  } else if (state.payload.isLost) {
    refs.messageBanner.classList.add("loss");
  }
}

function renderCards() {
  const cards = cardsForRail();
  const event = selectedEvent();
  refs.cardRail.innerHTML = "";

  if (cards.length === 0) {
    refs.cardRail.innerHTML = '<div class="empty-card">표시할 카드가 없습니다.</div>';
    return;
  }

  cards.forEach((card) => {
    const badge = cardStateBadge(card, event);
    const visual = CATEGORY_VISUALS[card.category] ?? CATEGORY_VISUALS.person;
    const wrapper = document.createElement("article");
    wrapper.className = "card";
    if (!card.isUsable || (event && !event.isCurrent)) {
      wrapper.classList.add("unavailable");
    }
    if (state.selectedCardId === card.instanceId) {
      wrapper.classList.add("selected-card");
    }
    if (state.stagedPrimaryId === card.instanceId || state.stagedSupportId === card.instanceId) {
      wrapper.classList.add("staged");
    }

    const canDrag =
      Boolean(event) &&
      event.isCurrent &&
      cardMatchesEvent(card, event) &&
      card.isUsable;
    if (canDrag) {
      wrapper.classList.add("draggable");
      wrapper.draggable = true;
    }

    wrapper.style.setProperty("--card-accent", visual.accent);
    wrapper.innerHTML = `
      <div class="card-compact-top">
        <h3 class="card-compact-title">${escapeHtml(card.name)}</h3>
      </div>
      <div class="card-art">
        <span class="card-art-glyph">${escapeHtml(visual.glyph)}</span>
        <span class="card-art-badge">${escapeHtml(badge.label)}</span>
      </div>
      <div class="card-mini-row">
        <span class="card-mini-meta">${escapeHtml(event ? eventCheckText(card, event) : statSummary(card.stats))}</span>
        <span class="card-mini-meta">${escapeHtml(cardSecondaryText(card))}</span>
      </div>
    `;

    wrapper.addEventListener("click", () => {
      state.selectedCardId = state.selectedCardId === card.instanceId ? null : card.instanceId;
      render();
    });

    wrapper.tabIndex = 0;
    wrapper.addEventListener("keydown", (eventObject) => {
      if (eventObject.key === "Enter" || eventObject.key === " ") {
        eventObject.preventDefault();
        state.selectedCardId = state.selectedCardId === card.instanceId ? null : card.instanceId;
        render();
      }
    });

    if (canDrag) {
      wrapper.addEventListener("dragstart", (eventObject) => {
        state.draggingCardId = card.instanceId;
        wrapper.classList.add("dragging");
        eventObject.dataTransfer?.setData("text/plain", card.instanceId);
      });
      wrapper.addEventListener("dragend", () => {
        state.draggingCardId = null;
        wrapper.classList.remove("dragging");
      });
    }

    refs.cardRail.append(wrapper);
  });
}

function renderCardInspector() {
  const card = findCard(state.selectedCardId);
  if (!card) {
    refs.cardInspector.className = "card-inspector";
    refs.cardInspector.setAttribute("aria-hidden", "true");
    refs.cardInspector.innerHTML = "";
    return;
  }

  const event = selectedEvent();
  const visual = CATEGORY_VISUALS[card.category] ?? CATEGORY_VISUALS.person;
  const badge = cardStateBadge(card, event);
  const canStageAsPrimary = Boolean(event?.isCurrent && canStagePrimary(card, event));
  const canStageAsSupport = Boolean(event?.isCurrent && canStageSupport(card, event));
  const canPlayNow = canStageAsPrimary && handIndexForCard(card.instanceId) >= 0;

  refs.cardInspector.className = "card-inspector open";
  refs.cardInspector.setAttribute("aria-hidden", "false");
  refs.cardInspector.innerHTML = `
    <div class="inspector-panel">
      <div class="inspector-hero" style="--inspector-accent: ${visual.accent};">
        <span class="inspector-glyph">${escapeHtml(visual.glyph)}</span>
      </div>
      <div class="inspector-content">
        <div class="inspector-head">
          <div>
            <p class="eyebrow">${escapeHtml(displayCategory(card))}</p>
            <h3>${escapeHtml(card.name)}</h3>
          </div>
          <button class="inspector-close" type="button" data-close-inspector>x</button>
        </div>
        <div class="detail-meta">
          <span class="detail-stat">${escapeHtml(badge.label)}</span>
          <span class="detail-stat">${escapeHtml(statSummary(card.stats))}</span>
          <span class="detail-stat">${escapeHtml(cardSecondaryText(card))}</span>
        </div>
        <p class="detail-copy">${escapeHtml(card.description)}</p>
        ${
          isPerson(card)
            ? `
              <div>
                <p class="eyebrow">장착 장비</p>
                ${equipmentListMarkup(card)}
              </div>
            `
            : ""
        }
        ${
          card.category === "equipment" && card.equippedToName
            ? `<p class="detail-copy">장착 대상: ${escapeHtml(card.equippedToName)}</p>`
            : ""
        }
        <div class="tag-group">
          ${card.tags.map((tag) => `<span class="tag-pill">${escapeHtml(displayTag(tag))}</span>`).join("")}
        </div>
        <div class="inspector-actions">
          <button class="chrome-button" type="button" data-stage-primary ${canStageAsPrimary ? "" : "disabled"}>인물 슬롯에 올리기</button>
          <button class="chrome-button" type="button" data-stage-support ${canStageAsSupport ? "" : "disabled"}>정보 슬롯에 올리기</button>
          <button class="play-button" type="button" data-play-card ${canPlayNow ? "" : "disabled"}>바로 사용</button>
          <button class="chrome-button" type="button" data-close-inspector>닫기</button>
        </div>
      </div>
    </div>
  `;

  refs.cardInspector.querySelectorAll("[data-close-inspector]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedCardId = null;
      render();
    });
  });

  refs.cardInspector.querySelector("[data-stage-primary]")?.addEventListener("click", () => {
    state.stagedPrimaryId = card.instanceId;
    if (state.stagedSupportId === card.instanceId) {
      state.stagedSupportId = null;
    }
    render();
  });

  refs.cardInspector.querySelector("[data-stage-support]")?.addEventListener("click", () => {
    state.stagedSupportId = card.instanceId;
    if (state.stagedPrimaryId === card.instanceId) {
      state.stagedPrimaryId = null;
    }
    render();
  });

  refs.cardInspector.querySelector("[data-play-card]")?.addEventListener("click", async () => {
    const handIndex = handIndexForCard(card.instanceId);
    if (handIndex >= 0) {
      await postAction("/api/play", { handIndex });
    }
  });
}

function renderMenu() {
  refs.gearShell.classList.toggle("open", state.isMenuOpen);
  refs.gearDrawer.setAttribute("aria-hidden", String(!state.isMenuOpen));
  refs.menuToggle.setAttribute("aria-expanded", String(state.isMenuOpen));
}

function renderControls() {
  renderMenu();
  if (refs.endDayButton) {
    refs.endDayButton.disabled = state.payload.isOver;
  }
}

function render() {
  if (!state.payload) {
    return;
  }
  normalizeState();
  renderStatus();
  renderMap();
  renderDetailPanel();
  renderMessage();
  renderCards();
  renderCardInspector();
  renderControls();
}

async function loadState() {
  state.payload = await fetchJson("/api/state");
  render();
}

async function postAction(path, payload = {}) {
  state.payload = await fetchJson(path, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.selectedEventIndex = null;
  state.stagedPrimaryId = null;
  state.stagedSupportId = null;
  state.selectedCardId = null;
  state.draggingCardId = null;
  state.isMenuOpen = false;
  render();
}

function bindControls() {
  refs.menuToggle.addEventListener("click", (event) => {
    event.stopPropagation();
    state.isMenuOpen = !state.isMenuOpen;
    renderMenu();
  });

  refs.gearDrawer.addEventListener("click", (event) => {
    event.stopPropagation();
  });

  refs.endDayButton?.addEventListener("click", async () => {
    await postAction("/api/end-day");
  });

  refs.menuActions.forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.menuAction;
      if (action === "save") {
        await postAction("/api/save");
      } else if (action === "load") {
        await postAction("/api/load");
      } else if (action === "forfeit") {
        if (window.confirm("현재 진행을 포기할까요?")) {
          await postAction("/api/forfeit");
        }
      }
    });
  });

  document.addEventListener("click", (event) => {
    if (state.isMenuOpen && !refs.gearShell.contains(event.target)) {
      state.isMenuOpen = false;
      renderMenu();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      state.isMenuOpen = false;
      state.selectedCardId = null;
      render();
    }
  });
}

async function boot() {
  bindControls();
  try {
    await loadState();
  } catch (error) {
    refs.messageBanner.textContent = `로컬 서버 연결 실패: ${error.message}`;
    refs.messageBanner.className = "message-banner loss";
  }
}

boot();
