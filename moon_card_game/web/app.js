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

const TAG_LABELS = {
  route: "경로",
  street: "거리",
  negotiation: "교섭",
  public: "공공",
  shrine: "사당",
  support: "지원",
  covert: "잠입",
  repair: "수리",
  fixer: "해결",
  survival: "생존",
  escort: "호위",
  combat: "전투",
  medical: "치료",
  evidence: "증거",
  permit: "허가",
};

const state = {
  payload: null,
  selectedEventIndex: null,
  stagedCardInstanceId: null,
  draggingCardInstanceId: null,
  selectedCardInstanceId: null,
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
    throw new Error(`요청에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

function visualForCategory(category) {
  return CATEGORY_VISUALS[category] ?? { accent: "#1f4f7d", glyph: "달" };
}

function displayTag(tag) {
  return TAG_LABELS[tag] ?? tag;
}

function eventNeedsSpecificInfo(event) {
  return Boolean(event?.requiredCardIds?.length);
}

function cardMatchesEvent(card, event) {
  if (!event || card.category === "equipment") {
    return false;
  }
  const hasRequiredTag =
    event.requiredTags.length === 0 ||
    card.tags.some((tag) => event.requiredTags.includes(tag));
  const hasRequiredCard =
    !eventNeedsSpecificInfo(event) || event.requiredCardIds.includes(card.cardId);
  return hasRequiredTag && hasRequiredCard;
}

function cardPowerText(card) {
  if (card.category === "equipment") {
    return `보정 +${card.power}`;
  }
  if (card.equipmentBonus > 0) {
    return `대응 ${card.power} (+장비 ${card.equipmentBonus})`;
  }
  return `대응 ${card.power}`;
}

function cardDurabilityText(card) {
  if (card.category === "equipment") {
    return card.equippedToName ? `장착 ${card.equippedToName}` : "장비 보관";
  }
  return `내구 ${card.durability}/${card.maxDurability}`;
}

function cardAttachmentSummary(card) {
  if (card.category === "equipment") {
    return card.equippedToName ? `장착 대상: ${card.equippedToName}` : "장착 대상 없음";
  }
  if (card.attachedEquipmentNames.length > 0) {
    return `장착 장비: ${card.attachedEquipmentNames.join(", ")}`;
  }
  return "";
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

function selectedCard() {
  if (!state.selectedCardInstanceId) {
    return null;
  }
  return findCard(state.selectedCardInstanceId);
}

function handIndexForCard(instanceId) {
  if (!state.payload) {
    return -1;
  }
  return state.payload.hand.findIndex((card) => card.instanceId === instanceId);
}

function stagedCard() {
  if (!state.stagedCardInstanceId) {
    return null;
  }
  return findCard(state.stagedCardInstanceId);
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

  const filterEvent = selectedEvent();
  const staged = stagedCard();
  if (!filterEvent || !staged || !cardMatchesEvent(staged, filterEvent)) {
    state.stagedCardInstanceId = null;
  }

  const chosenCard = selectedCard();
  if (!chosenCard || (filterEvent && !cardMatchesEvent(chosenCard, filterEvent))) {
    state.selectedCardInstanceId = null;
  }
}

function cardsForRail() {
  const payload = state.payload;
  const filterEvent = selectedEvent();
  const cards = filterEvent
    ? payload.collection.filter((card) => cardMatchesEvent(card, filterEvent))
    : [...payload.collection];

  cards.sort((left, right) => {
    if (left.isInHand !== right.isInHand) {
      return left.isInHand ? -1 : 1;
    }
    if (left.isUsable !== right.isUsable) {
      return left.isUsable ? -1 : 1;
    }
    const categoryComparison = left.displayCategory.localeCompare(right.displayCategory);
    if (categoryComparison !== 0) {
      return categoryComparison;
    }
    const nameComparison = left.name.localeCompare(right.name);
    if (nameComparison !== 0) {
      return nameComparison;
    }
    return left.instanceId.localeCompare(right.instanceId);
  });

  return cards;
}

function canCommitDraggedCard(filterEvent, card) {
  if (!state.payload || !filterEvent || !card) {
    return false;
  }
  return (
    !state.payload.isOver &&
    filterEvent.isCurrent &&
    card.isUsable &&
    card.isInHand &&
    handIndexForCard(card.instanceId) >= 0
  );
}

function canQuickPlay(card) {
  if (!state.payload || !card) {
    return false;
  }
  const filterEvent = selectedEvent();
  return (
    !state.payload.isOver &&
    card.category !== "equipment" &&
    card.isUsable &&
    card.isInHand &&
    handIndexForCard(card.instanceId) >= 0 &&
    (!filterEvent || filterEvent.isCurrent)
  );
}

function cardStateBadge(card, filterEvent) {
  if (!card.isUsable) {
    return { label: "소모됨", className: "state-worn" };
  }
  if (card.category === "equipment") {
    return {
      label: card.equippedToName ? "장착됨" : "장비",
      className: "state-preview",
    };
  }
  if (filterEvent && !filterEvent.isCurrent) {
    return { label: "미리보기", className: "state-preview" };
  }
  if (card.isInHand) {
    return { label: "손패", className: "state-ready" };
  }
  return { label: "보관", className: "state-reserve" };
}

function renderStatus() {
  const payload = state.payload;
  refs.statusStrip.innerHTML = "";
  const items = [
    ["안정도", payload.stability],
    ["사건", payload.events.length],
    ["손패", payload.hand.length],
  ];
  for (const [label, value] of items) {
    const chip = document.createElement("div");
    chip.className = "status-chip";
    chip.innerHTML = `<strong>${escapeHtml(label)}</strong> ${escapeHtml(value)}`;
    refs.statusStrip.append(chip);
  }
}

function renderMenu() {
  refs.gearShell.classList.toggle("open", state.isMenuOpen);
  refs.gearDrawer.setAttribute("aria-hidden", String(!state.isMenuOpen));
  refs.menuToggle.setAttribute("aria-expanded", String(state.isMenuOpen));
}

function createRoutePath(events) {
  if (events.length === 0) {
    return "";
  }
  const points = events.map((_, index) => EVENT_POSITIONS[index % EVENT_POSITIONS.length]);
  let path = `M ${points[0].x} ${points[0].y}`;
  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1];
    const current = points[index];
    const controlX = (previous.x + current.x) / 2;
    const controlY = (previous.y + current.y) / 2 + (index % 2 === 0 ? 7 : -7);
    path += `Q ${controlX} ${controlY} ${current.x} ${current.y} `;
  }
  return path;
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

  const panX = (50 - position.x) * 0.58;
  const panY = (46 - position.y) * 0.58;
  refs.mapSurface.classList.add("event-focused");
  refs.mapSurface.style.setProperty("--camera-pan-x", `${panX}%`);
  refs.mapSurface.style.setProperty("--camera-pan-y", `${panY}%`);
  refs.mapSurface.style.setProperty("--camera-scale", "1.22");
  refs.focusGlow.style.left = `${position.x}%`;
  refs.focusGlow.style.top = `${position.y}%`;
}

function renderMap() {
  const payload = state.payload;
  refs.routeLayer.innerHTML = "";
  refs.eventMap.innerHTML = "";

  if (payload.events.length === 0) {
    refs.eventMap.innerHTML = `<div class="empty-card">지금 지도에 남은 사건이 없습니다.</div>`;
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
    if (index === state.selectedEventIndex) {
      node.classList.add("selected");
    }
    node.style.left = `${position.x}%`;
    node.style.top = `${position.y}%`;
    node.innerHTML = `
      <span class="event-node-index">${index + 1}</span>
      <strong class="event-node-title">${escapeHtml(event.title)}</strong>
    `;
    node.addEventListener("click", () => {
      const isSameSelection = state.selectedEventIndex === index;
      state.selectedEventIndex = isSameSelection ? null : index;
      state.stagedCardInstanceId = null;
      state.selectedCardInstanceId = null;
      render();
    });
    refs.eventMap.append(node);
  });

  renderMapFocus();
}

function dropZoneContent(card, filterEvent) {
  if (!card) {
    return `
      <div class="drop-zone-placeholder" aria-hidden="true"></div>
    `;
  }

  const badge = cardStateBadge(card, filterEvent);
  return `
    <div class="drop-card">
      <div class="drop-card-header">
        <div>
          <p class="eyebrow">${escapeHtml(card.displayCategory)}</p>
          <h4 class="drop-card-title">${escapeHtml(card.name)}</h4>
        </div>
        <span class="card-badge ${badge.className}">${escapeHtml(badge.label)}</span>
      </div>
      <p class="drop-card-copy">${escapeHtml(card.description)}</p>
      <div class="stat-row">
        <span class="stat-chip">${escapeHtml(cardPowerText(card))}</span>
        <span class="stat-chip">${escapeHtml(cardDurabilityText(card))}</span>
      </div>
      ${
        cardAttachmentSummary(card)
          ? `<p class="drop-card-copy">${escapeHtml(cardAttachmentSummary(card))}</p>`
          : ""
      }
      <div class="tag-grid">
        ${card.tags.map((tag) => `<span class="card-tag">${escapeHtml(displayTag(tag))}</span>`).join("")}
      </div>
    </div>
  `;
}

function renderDetailPanel() {
  const payload = state.payload;
  const filterEvent = selectedEvent();
  const current = activeEvent();
  const event = filterEvent ?? current;

  if (!event) {
    refs.detailPanel.innerHTML = `
      <div class="detail-stack">
        <p class="eyebrow">월광 기록</p>
        <h3>고요한 거리</h3>
        <p class="detail-copy">지금은 지도에 남은 사건이 없습니다. 새 게임을 시작하거나 저장을 불러오세요.</p>
      </div>
    `;
    return;
  }

  const matchingCards = payload.collection.filter((card) => cardMatchesEvent(card, event));
  const staged = stagedCard();
  const canCommit = canCommitDraggedCard(filterEvent, staged);

  if (!filterEvent) {
    refs.detailPanel.innerHTML = `
      <div class="detail-stack">
        <div>
          <p class="eyebrow">월광 기록</p>
          <h3>${escapeHtml(event.title)}</h3>
        </div>
        <p class="detail-copy">${escapeHtml(event.description)}</p>
        <div class="detail-meta">
          <span class="detail-stat">투입 가능 카드 ${matchingCards.length}</span>
          <span class="detail-stat">보상 ${escapeHtml(event.rewardNames.join(", ") || "미확인")}</span>
        </div>
        <div>
          <p class="eyebrow">필수 태그</p>
          <div class="tag-group">
            ${event.requiredTags.map((tag) => `<span class="tag-pill">${escapeHtml(displayTag(tag))}</span>`).join("")}
          </div>
        </div>
        ${
          event.requiredCardNames.length > 0
            ? `
              <div>
                <p class="eyebrow">전용 정보</p>
                <div class="tag-group">
                  ${event.requiredCardNames.map((name) => `<span class="tag-pill">${escapeHtml(name)}</span>`).join("")}
                </div>
              </div>
            `
            : ""
        }
      </div>
    `;
    return;
  }

  refs.detailPanel.innerHTML = `
    <div class="detail-stack">
      <div>
        <p class="eyebrow">${filterEvent.isCurrent ? "사건 집중" : "미래 사건 집중"}</p>
        <h3>${escapeHtml(filterEvent.title)}</h3>
      </div>
      <p class="detail-copy">${escapeHtml(filterEvent.description)}</p>
      <div class="detail-meta">
        <span class="detail-stat">투입 가능 카드 ${matchingCards.length}</span>
        <span class="detail-stat">${filterEvent.isCurrent ? "진행 중" : "미리보기"}</span>
      </div>
      <div>
        <p class="eyebrow">필수 태그</p>
        <div class="tag-group">
          ${filterEvent.requiredTags.map((tag) => `<span class="tag-pill">${escapeHtml(displayTag(tag))}</span>`).join("")}
        </div>
      </div>
      <div>
        <p class="eyebrow">보너스 태그</p>
        <div class="tag-group">
          ${
            filterEvent.bonusTags.length > 0
              ? filterEvent.bonusTags
                  .map((tag) => `<span class="tag-pill bonus">${escapeHtml(displayTag(tag))}</span>`)
                  .join("")
              : '<span class="detail-copy">추가 보너스는 없습니다.</span>'
          }
        </div>
      </div>
      ${
        filterEvent.requiredCardNames.length > 0
          ? `
            <div>
              <p class="eyebrow">전용 정보</p>
              <div class="tag-group">
                ${filterEvent.requiredCardNames
                  .map((name) => `<span class="tag-pill">${escapeHtml(name)}</span>`)
                  .join("")}
              </div>
            </div>
          `
          : ""
      }
      <div class="drop-lab">
        <div class="drop-zone${staged ? " has-card" : ""}" data-drop-zone>
          ${dropZoneContent(staged, filterEvent)}
        </div>
      <div class="drop-actions">
          <button class="play-button" type="button" data-commit-card ${canCommit ? "" : "disabled"}>
            ${
              canCommit
                ? "올린 카드 사용"
                : filterEvent.isCurrent
                  ? "손패 카드 필요"
                  : "미리보기 전용"
            }
          </button>
          <button class="chrome-button" type="button" data-clear-slot ${staged ? "" : "disabled"}>
            비우기
          </button>
          ${
            filterEvent.isCurrent && !payload.isOver
              ? '<button class="chrome-button danger" type="button" data-skip-event>넘기기</button>'
              : ""
          }
        </div>
      </div>
      <div>
        <p class="eyebrow">획득 가능 카드</p>
        <div class="tag-group">
          ${
            filterEvent.rewardNames.length > 0
              ? filterEvent.rewardNames
                  .map((name) => `<span class="tag-pill">${escapeHtml(name)}</span>`)
                  .join("")
              : '<span class="detail-copy">알려진 보상이 없습니다.</span>'
          }
        </div>
      </div>
    </div>
  `;

  const dropZone = refs.detailPanel.querySelector("[data-drop-zone]");
  const commitButton = refs.detailPanel.querySelector("[data-commit-card]");
  const clearButton = refs.detailPanel.querySelector("[data-clear-slot]");
  const skipButton = refs.detailPanel.querySelector("[data-skip-event]");

  if (dropZone) {
    dropZone.addEventListener("dragenter", (eventObject) => {
      eventObject.preventDefault();
      dropZone.classList.add("is-over");
    });
    dropZone.addEventListener("dragover", (eventObject) => {
      eventObject.preventDefault();
      dropZone.classList.add("is-over");
    });
    dropZone.addEventListener("dragleave", () => {
      dropZone.classList.remove("is-over");
    });
    dropZone.addEventListener("drop", (eventObject) => {
      eventObject.preventDefault();
      dropZone.classList.remove("is-over");
      const droppedId =
        state.draggingCardInstanceId ||
        eventObject.dataTransfer?.getData("text/plain") ||
        "";
      const droppedCard = findCard(droppedId);
      if (droppedCard && cardMatchesEvent(droppedCard, filterEvent)) {
        state.stagedCardInstanceId = droppedId;
        render();
      }
    });
  }

  if (commitButton) {
    commitButton.addEventListener("click", async () => {
      const card = stagedCard();
      const handIndex = card ? handIndexForCard(card.instanceId) : -1;
      if (handIndex >= 0 && canCommitDraggedCard(filterEvent, card)) {
        await postAction("/api/play", { handIndex });
      }
    });
  }

  if (clearButton) {
    clearButton.addEventListener("click", () => {
      state.stagedCardInstanceId = null;
      render();
    });
  }

  if (skipButton) {
    skipButton.addEventListener("click", async () => {
      await postAction("/api/skip");
    });
  }
}

function renderMessage() {
  const payload = state.payload;
  refs.messageBanner.textContent = payload.message;
  refs.messageBanner.className = "message-banner";
  if (payload.isWon) {
    refs.messageBanner.classList.add("win");
  } else if (payload.isLost) {
    refs.messageBanner.classList.add("loss");
  }
}

function renderCards() {
  const payload = state.payload;
  const filterEvent = selectedEvent();
  const cards = cardsForRail();
  refs.cardRail.innerHTML = "";

  if (cards.length === 0) {
    refs.cardRail.innerHTML = `
      <div class="empty-card">
        맞는 카드가 없습니다.
      </div>
    `;
    return;
  }

  cards.forEach((card) => {
    const visual = visualForCategory(card.category);
    const badge = cardStateBadge(card, filterEvent);
    const wrapper = document.createElement("article");
    const canDrag = Boolean(filterEvent) && cardMatchesEvent(card, filterEvent);
    const isSelected = state.selectedCardInstanceId === card.instanceId;

    wrapper.classList.add("card");
    if (!card.isInHand || (filterEvent && !filterEvent.isCurrent) || !card.isUsable) {
      wrapper.classList.add("unavailable");
    }
    if (canDrag) {
      wrapper.classList.add("draggable");
      wrapper.draggable = true;
    }
    if (state.stagedCardInstanceId === card.instanceId) {
      wrapper.classList.add("staged");
    }
    if (isSelected) {
      wrapper.classList.add("selected-card");
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
        <span class="card-mini-meta">${escapeHtml(cardPowerText(card))}</span>
        <span class="card-mini-meta">${
          card.category === "equipment"
            ? escapeHtml(card.equippedToName ? `장착: ${card.equippedToName}` : "장비")
            : escapeHtml(card.isInHand ? "손패" : "보관")
        }</span>
      </div>
    `;

    wrapper.addEventListener("click", () => {
      state.selectedCardInstanceId =
        state.selectedCardInstanceId === card.instanceId ? null : card.instanceId;
      render();
    });

    wrapper.addEventListener("keydown", (eventObject) => {
      if (eventObject.key === "Enter" || eventObject.key === " ") {
        eventObject.preventDefault();
        state.selectedCardInstanceId =
          state.selectedCardInstanceId === card.instanceId ? null : card.instanceId;
        render();
      }
    });
    wrapper.tabIndex = 0;

    if (canDrag) {
      wrapper.addEventListener("dragstart", (eventObject) => {
        state.draggingCardInstanceId = card.instanceId;
        wrapper.classList.add("dragging");
        eventObject.dataTransfer?.setData("text/plain", card.instanceId);
        if (eventObject.dataTransfer) {
          eventObject.dataTransfer.effectAllowed = "move";
        }
      });
      wrapper.addEventListener("dragend", () => {
        state.draggingCardInstanceId = null;
        wrapper.classList.remove("dragging");
      });
    }

    refs.cardRail.append(wrapper);
  });
}

function renderCardInspector() {
  const card = selectedCard();
  if (!card) {
    refs.cardInspector.className = "card-inspector";
    refs.cardInspector.setAttribute("aria-hidden", "true");
    refs.cardInspector.innerHTML = "";
    return;
  }

  const filterEvent = selectedEvent();
  const visual = visualForCategory(card.category);
  const canStage = Boolean(filterEvent) && cardMatchesEvent(card, filterEvent);
  const canPlay = canQuickPlay(card);
  const isStaged = state.stagedCardInstanceId === card.instanceId;
  const badge = cardStateBadge(card, filterEvent);
  const stageLabel = filterEvent
    ? filterEvent.isCurrent
      ? "사건 슬롯에 올리기"
      : "슬롯에서 미리보기"
    : "먼저 사건 선택";

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
            <p class="eyebrow">${escapeHtml(card.displayCategory)}</p>
            <h3>${escapeHtml(card.name)}</h3>
          </div>
          <button class="inspector-close" type="button" data-close-inspector>x</button>
        </div>
        <div class="detail-meta">
          <span class="detail-stat">${escapeHtml(badge.label)}</span>
          <span class="detail-stat">${escapeHtml(cardPowerText(card))}</span>
          <span class="detail-stat">${escapeHtml(cardDurabilityText(card))}</span>
        </div>
        <p class="detail-copy">${escapeHtml(card.description)}</p>
        ${
          cardAttachmentSummary(card)
            ? `<p class="detail-copy">${escapeHtml(cardAttachmentSummary(card))}</p>`
            : ""
        }
        <div class="tag-group">
          ${card.tags.map((tag) => `<span class="tag-pill">${escapeHtml(displayTag(tag))}</span>`).join("")}
        </div>
        <div class="inspector-actions">
          <button class="chrome-button" type="button" data-stage-card ${canStage ? "" : "disabled"}>
            ${escapeHtml(stageLabel)}
          </button>
          <button class="play-button" type="button" data-play-card ${canPlay ? "" : "disabled"}>
            ${canPlay ? "바로 사용" : "바로 사용 불가"}
          </button>
          <button class="chrome-button" type="button" data-close-inspector>
            ${isStaged ? "닫기 (올림)" : "닫기"}
          </button>
        </div>
      </div>
    </div>
  `;

  refs.cardInspector.addEventListener(
    "click",
    (eventObject) => {
      if (eventObject.target === refs.cardInspector) {
        state.selectedCardInstanceId = null;
        render();
      }
    },
    { once: true },
  );

  refs.cardInspector
    .querySelectorAll("[data-close-inspector]")
    .forEach((button) =>
      button.addEventListener("click", () => {
        state.selectedCardInstanceId = null;
        render();
      }),
    );

  const stageButton = refs.cardInspector.querySelector("[data-stage-card]");
  if (stageButton) {
    stageButton.addEventListener("click", () => {
      if (canStage) {
        state.stagedCardInstanceId = card.instanceId;
        render();
      }
    });
  }

  const playButton = refs.cardInspector.querySelector("[data-play-card]");
  if (playButton) {
    playButton.addEventListener("click", async () => {
      const handIndex = handIndexForCard(card.instanceId);
      if (handIndex >= 0 && canQuickPlay(card)) {
        await postAction("/api/play", { handIndex });
      }
    });
  }
}

function renderControls() {
  renderMenu();
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
  state.stagedCardInstanceId = null;
  state.draggingCardInstanceId = null;
  state.selectedCardInstanceId = null;
  state.isMenuOpen = false;
  render();
}

function bindControls() {
  refs.menuToggle.addEventListener("click", (eventObject) => {
    eventObject.stopPropagation();
    state.isMenuOpen = !state.isMenuOpen;
    renderMenu();
  });

  refs.gearDrawer.addEventListener("click", (eventObject) => {
    eventObject.stopPropagation();
  });

  for (const button of refs.menuActions) {
    button.addEventListener("click", async () => {
      const action = button.dataset.menuAction;
      if (action === "save") {
        await postAction("/api/save");
      } else if (action === "load") {
        await postAction("/api/load");
      } else if (action === "forfeit") {
        if (window.confirm("현재 진행을 포기할까요? 이 선택은 즉시 패배로 처리됩니다.")) {
          await postAction("/api/forfeit");
        }
      }
    });
  }

  document.addEventListener("click", (eventObject) => {
    if (state.isMenuOpen && !refs.gearShell.contains(eventObject.target)) {
      state.isMenuOpen = false;
      renderMenu();
    }
  });

  document.addEventListener("keydown", (eventObject) => {
    if (eventObject.key === "Escape") {
      let changed = false;
      if (state.isMenuOpen) {
        state.isMenuOpen = false;
        changed = true;
      }
      if (state.selectedCardInstanceId !== null) {
        state.selectedCardInstanceId = null;
        changed = true;
      }
      if (changed) {
        render();
      }
    }
  });
}

async function boot() {
  bindControls();
  try {
    await loadState();
  } catch (error) {
    refs.messageBanner.textContent = `로컬 게임 서버에 연결하지 못했습니다: ${error.message}`;
    refs.messageBanner.className = "message-banner loss";
  }
}

boot();
