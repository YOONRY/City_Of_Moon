extends Control

const ContentLoaderRef = preload("res://scripts/content_loader.gd")
const SessionRef = preload("res://scripts/game_session.gd")
const EVENT_POSITIONS := [
	Vector2(0.15, 0.70),
	Vector2(0.31, 0.36),
	Vector2(0.45, 0.58),
	Vector2(0.58, 0.27),
	Vector2(0.73, 0.49),
	Vector2(0.86, 0.24),
]
const GOLD := Color("d8b86d")
const GOLD_SOFT := Color("f1dfaa")
const NAVY_PANEL := Color("10233c")
const NAVY_PANEL_ALT := Color("0c1b2f")
const NAVY_DEEP := Color("081423")
const INK := Color("f3ead0")
const MUTED := Color("c8d3df")
const CATEGORY_LABELS := {
	"person": "인물",
	"info": "정보",
	"equipment": "장비",
}
const INFO_KIND_LABELS := {
	"general": "범용 정보",
	"exclusive": "전용 정보",
}
const EQUIPMENT_SLOT_LABELS := {
	"weapon": "무기",
	"armor": "방어구",
	"accessory": "악세사리",
}
const EVENT_KIND_LABELS := {
	"daily": "일일 의뢰",
	"incident": "돌발 사건",
	"special": "특수 의뢰",
}
const SOURCE_LABELS := {
	"board": "게시판",
	"street": "거리",
	"story": "연쇄 의뢰",
	"tavern": "술집",
}
const STAT_LABELS := {
	"strength": "근력",
	"agility": "민첩",
	"intelligence": "지능",
	"charm": "매력",
}
const CATEGORY_ACCENTS := {
	"person": Color("4e8cc3"),
	"info": Color("d8b86d"),
	"equipment": Color("6c88a8"),
}

@onready var top_bar: PanelContainer = $RootMargin/Frame/TopBar
@onready var title_label: Label = $RootMargin/Frame/TopBar/TopMargin/TopRow/TitleBlock/TitleLabel
@onready var subtitle_label: Label = $RootMargin/Frame/TopBar/TopMargin/TopRow/TitleBlock/SubtitleLabel
@onready var status_label: Label = $RootMargin/Frame/TopBar/TopMargin/TopRow/StatusLabel
@onready var new_button: Button = $RootMargin/Frame/TopBar/TopMargin/TopRow/SessionButtons/NewButton
@onready var load_button: Button = $RootMargin/Frame/TopBar/TopMargin/TopRow/SessionButtons/LoadButton
@onready var save_button: Button = $RootMargin/Frame/TopBar/TopMargin/TopRow/SessionButtons/SaveButton
@onready var refresh_button: Button = $RootMargin/Frame/TopBar/TopMargin/TopRow/SessionButtons/RefreshButton
@onready var map_panel: PanelContainer = $RootMargin/Frame/Body/MapPanel
@onready var map_header: Label = $RootMargin/Frame/Body/MapPanel/MapMargin/MapStack/MapHeader
@onready var map_subheader: Label = $RootMargin/Frame/Body/MapPanel/MapMargin/MapStack/MapSubheader
@onready var map_canvas: Control = $RootMargin/Frame/Body/MapPanel/MapMargin/MapStack/MapCanvas
@onready var detail_panel: PanelContainer = $RootMargin/Frame/Body/DetailPanel
@onready var detail_eyebrow: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/DetailEyebrow
@onready var detail_title: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/DetailTitle
@onready var detail_description: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/DetailDescription
@onready var detail_check: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/DetailCheck
@onready var detail_requirement: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/DetailRequirement
@onready var detail_reward: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/DetailReward
@onready var tag_flow: FlowContainer = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/TagFlow
@onready var slot_flow: FlowContainer = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/SlotFlow
@onready var selection_eyebrow: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/SelectionEyebrow
@onready var primary_slot_label: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/PrimarySlotLabel
@onready var support_slot_label: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/SupportSlotLabel
@onready var assign_primary_button: Button = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/AssignButtons/AssignPrimaryButton
@onready var assign_support_button: Button = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/AssignButtons/AssignSupportButton
@onready var clear_slots_button: Button = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/AssignButtons/ClearSlotsButton
@onready var commit_button: Button = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/ActionButtons/CommitButton
@onready var skip_button: Button = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/ActionButtons/SkipButton
@onready var tavern_button: Button = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/ActionButtons/TavernButton
@onready var end_day_button: Button = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/ActionButtons/EndDayButton
@onready var session_message: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/SessionMessage
@onready var inspector_eyebrow: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/InspectorEyebrow
@onready var inspector_title: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/InspectorTitle
@onready var inspector_meta: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/InspectorMeta
@onready var inspector_stats: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/InspectorStats
@onready var inspector_description: Label = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/InspectorDescription
@onready var equipment_flow: FlowContainer = $RootMargin/Frame/Body/DetailPanel/DetailMargin/DetailStack/EquipmentFlow
@onready var rail_panel: PanelContainer = $RootMargin/Frame/RailPanel
@onready var rail_header: Label = $RootMargin/Frame/RailPanel/RailMargin/RailStack/RailHeader
@onready var card_rail: HBoxContainer = $RootMargin/Frame/RailPanel/RailMargin/RailStack/RailScroll/CardRail

var content: Dictionary = {}
var session = null
var view_state: Dictionary = {}
var selected_event_index := -1
var selected_card_instance_id := ""
var selected_primary_instance_id := ""
var selected_support_instance_id := ""
var collection_lookup: Dictionary = {}


func _ready() -> void:
	_apply_theme()
	session = SessionRef.new()
	new_button.pressed.connect(_start_new_run)
	load_button.pressed.connect(_load_run)
	save_button.pressed.connect(_save_run)
	refresh_button.pressed.connect(_reload_export)
	assign_primary_button.pressed.connect(_assign_primary)
	assign_support_button.pressed.connect(_assign_support)
	clear_slots_button.pressed.connect(_clear_slots)
	commit_button.pressed.connect(_commit_event)
	skip_button.pressed.connect(_skip_event)
	tavern_button.pressed.connect(_visit_tavern)
	end_day_button.pressed.connect(_end_day)
	map_canvas.resized.connect(_render_map)
	_reload_export()


func _reload_export() -> void:
	content = ContentLoaderRef.new().load_content()
	session.setup(content)
	_reset_selection(true)
	_refresh_view()


func _refresh_view() -> void:
	view_state = session.get_view_state()
	_rebuild_collection_lookup()
	if _events().is_empty():
		selected_event_index = -1
	else:
		selected_event_index = clamp(selected_event_index, 0, _events().size() - 1)
		if selected_event_index < 0:
			selected_event_index = 0
	if _collection().is_empty():
		selected_card_instance_id = ""
	elif not collection_lookup.has(selected_card_instance_id):
		selected_card_instance_id = str(_collection()[0].get("instanceId", ""))
	if selected_primary_instance_id != "" and not collection_lookup.has(selected_primary_instance_id):
		selected_primary_instance_id = ""
	if selected_support_instance_id != "" and not collection_lookup.has(selected_support_instance_id):
		selected_support_instance_id = ""
	_render()


func _render() -> void:
	status_label.text = "D%d  |  자금 %d  |  안정도 %d  |  세금 %d일 남음  |  의뢰 %d개  |  카드 %d장" % [
		int(view_state.get("day", 1)),
		int(view_state.get("money", 0)),
		int(view_state.get("stability", 0)),
		int(view_state.get("daysUntilTax", 0)),
		_events().size(),
		_collection().size(),
	]
	session_message.text = str(view_state.get("message", ""))
	load_button.disabled = not bool(view_state.get("hasSave", false))
	tavern_button.disabled = not bool(view_state.get("canVisitTavern", false))
	_render_map()
	_render_detail()
	_render_cards()
	_render_inspector()


func _events() -> Array:
	return view_state.get("events", [])


func _collection() -> Array:
	return view_state.get("collection", [])


func _selected_event() -> Dictionary:
	var events := _events()
	if selected_event_index < 0 or selected_event_index >= events.size():
		return {}
	return events[selected_event_index]


func _selected_card() -> Dictionary:
	if selected_card_instance_id == "":
		return {}
	return collection_lookup.get(selected_card_instance_id, {})


func _selected_primary() -> Dictionary:
	if selected_primary_instance_id == "":
		return {}
	return collection_lookup.get(selected_primary_instance_id, {})


func _selected_support() -> Dictionary:
	if selected_support_instance_id == "":
		return {}
	return collection_lookup.get(selected_support_instance_id, {})


func _rebuild_collection_lookup() -> void:
	collection_lookup.clear()
	for card_entry in _collection():
		collection_lookup[str(card_entry.get("instanceId", ""))] = card_entry


func _render_map() -> void:
	_clear_children(map_canvas)
	var events := _events()
	if events.is_empty():
		var empty_label := Label.new()
		empty_label.text = "현재 열린 의뢰가 없습니다."
		empty_label.position = Vector2(24, 24)
		empty_label.add_theme_color_override("font_color", INK)
		map_canvas.add_child(empty_label)
		return
	var canvas_size := map_canvas.size
	if canvas_size.x <= 0.0 or canvas_size.y <= 0.0:
		return

	for index in range(events.size()):
		var event: Dictionary = events[index]
		var event_button := Button.new()
		var title := str(event.get("title", "의뢰"))
		if bool(event.get("isCurrent", false)):
			title = "현재 · %s" % title
		event_button.text = title
		event_button.custom_minimum_size = Vector2(190, 62)
		event_button.focus_mode = Control.FOCUS_NONE
		var position: Vector2 = EVENT_POSITIONS[index % EVENT_POSITIONS.size()]
		event_button.position = Vector2(
			canvas_size.x * position.x - 95.0,
			canvas_size.y * position.y - 31.0
		)
		_style_event_button(event_button, index == selected_event_index, bool(event.get("isCurrent", false)))
		event_button.pressed.connect(_select_event.bind(index))
		map_canvas.add_child(event_button)


func _render_detail() -> void:
	var event := _selected_event()
	if event.is_empty():
		detail_title.text = "의뢰 없음"
		detail_description.text = "집중할 의뢰가 아직 없습니다."
		detail_check.text = ""
		detail_requirement.text = ""
		detail_reward.text = ""
		primary_slot_label.text = "주역: 비어 있음"
		support_slot_label.text = "지원: 비어 있음"
		commit_button.disabled = true
		skip_button.disabled = true
		assign_primary_button.disabled = true
		assign_support_button.disabled = true
		clear_slots_button.disabled = true
		_clear_children(tag_flow)
		_clear_children(slot_flow)
		return

	detail_title.text = str(event.get("title", "의뢰"))
	detail_description.text = str(event.get("description", ""))
	detail_check.text = "판정: %s  |  목표치 %d" % [
		_format_check_stats(event.get("checkStats", [])),
		int(event.get("difficulty", 0)),
	]
	var requirement_parts: Array[String] = []
	var required_cards: Array = event.get("requiredCardNames", [])
	if not required_cards.is_empty():
		requirement_parts.append("전용 정보: %s" % ", ".join(_stringify_array(required_cards)))
	var required_tags: Array = event.get("requiredTags", [])
	if not required_tags.is_empty():
		requirement_parts.append("요구 태그: %s" % ", ".join(_stringify_array(required_tags)))
	detail_requirement.text = " / ".join(requirement_parts) if not requirement_parts.is_empty() else "특수 요구 조건 없음"

	var reward_parts: Array[String] = []
	var payout := int(event.get("payout", 0))
	if payout > 0:
		reward_parts.append("%d 크라운" % payout)
	var reward_names: Array = event.get("rewardNames", [])
	if not reward_names.is_empty():
		reward_parts.append(", ".join(_stringify_array(reward_names)))
	detail_reward.text = "보상: %s" % " / ".join(reward_parts) if not reward_parts.is_empty() else "보상: 없음"

	_clear_children(tag_flow)
	for required_tag in event.get("requiredTags", []):
		tag_flow.add_child(_build_chip("#%s" % str(required_tag), Color("7ea6d8"), false))
	for bonus_tag in event.get("bonusTags", []):
		tag_flow.add_child(_build_chip("+%s" % str(bonus_tag), GOLD, true))
	for required_name in event.get("requiredCardNames", []):
		tag_flow.add_child(_build_chip(str(required_name), Color("b795d8"), false))

	_clear_children(slot_flow)
	slot_flow.add_child(_build_chip(EVENT_KIND_LABELS.get(str(event.get("kind", "")), str(event.get("kind", ""))), GOLD, true))
	slot_flow.add_child(_build_chip(SOURCE_LABELS.get(str(event.get("source", "")), str(event.get("source", ""))), Color("5d88b8"), false))
	slot_flow.add_child(_build_chip("인물 %d칸" % int(event.get("personSlots", 1)), Color("4e8cc3"), true))
	slot_flow.add_child(_build_chip("범용 정보 %d칸" % int(event.get("infoSlots", 0)), Color("7aa7a8"), false))
	slot_flow.add_child(_build_chip("소요 %d일" % int(event.get("timeCost", 1)), Color("d39b61"), false))
	slot_flow.add_child(_build_chip("마감 D%d" % int(event.get("deadlineDay", 0)), Color("be7f74"), false))

	primary_slot_label.text = "주역: %s" % _slot_name(_selected_primary(), "비어 있음")
	support_slot_label.text = "지원: %s" % _slot_name(_selected_support(), "비어 있음")

	assign_primary_button.disabled = not _can_assign_selected_as_primary()
	assign_support_button.disabled = not _can_assign_selected_as_support()
	clear_slots_button.disabled = selected_primary_instance_id == "" and selected_support_instance_id == ""
	skip_button.disabled = not bool(event.get("isCurrent", false))
	commit_button.disabled = not _can_commit_current_event()


func _render_cards() -> void:
	_clear_children(card_rail)
	var cards := _collection()
	rail_header.text = "보유 카드 %d장" % cards.size()
	if cards.is_empty():
		var empty_label := Label.new()
		empty_label.text = "보유 카드가 없습니다."
		empty_label.add_theme_color_override("font_color", INK)
		card_rail.add_child(empty_label)
		return
	for card_entry in cards:
		card_rail.add_child(_build_card_tile(card_entry))


func _render_inspector() -> void:
	var card := _selected_card()
	if card.is_empty():
		inspector_title.text = "선택된 카드 없음"
		inspector_meta.text = "하단 카드 중 하나를 눌러 상세를 확인하세요."
		inspector_stats.text = ""
		inspector_description.text = ""
		_clear_children(equipment_flow)
		return

	inspector_title.text = str(card.get("name", "카드"))
	var meta_parts: Array[String] = [_card_type_text(card)]
	if bool(card.get("isCommitted", false)):
		meta_parts.append("임무 중 %d턴" % int(card.get("busyTurnsRemaining", 0)))
	elif bool(card.get("isUsable", false)):
		meta_parts.append("배치 가능")
	if str(card.get("instanceId", "")) == selected_primary_instance_id:
		meta_parts.append("주역 슬롯")
	if str(card.get("instanceId", "")) == selected_support_instance_id:
		meta_parts.append("지원 슬롯")
	if str(card.get("category", "")) == "equipment" and str(card.get("equippedToName", "")) != "":
		meta_parts.append("장착 대상 %s" % str(card.get("equippedToName", "")))
	inspector_meta.text = " | ".join(meta_parts)
	inspector_stats.text = _format_card_stats(card)
	inspector_description.text = str(card.get("description", ""))

	_clear_children(equipment_flow)
	var category := str(card.get("category", ""))
	if category == "person":
		var attached_by_slot: Dictionary = {}
		for equipment_entry in card.get("attachedEquipment", []):
			attached_by_slot[str(equipment_entry.get("slot", ""))] = equipment_entry
		for slot_name in ["weapon", "armor", "accessory"]:
			var slot_label: String = str(EQUIPMENT_SLOT_LABELS.get(slot_name, slot_name))
			if attached_by_slot.has(slot_name):
				var equipment_entry: Dictionary = attached_by_slot[slot_name]
				equipment_flow.add_child(_build_chip("%s: %s" % [slot_label, str(equipment_entry.get("name", ""))], Color("7ea6d8"), true))
			else:
				equipment_flow.add_child(_build_chip("%s: 비어 있음" % slot_label, Color("5b6d82"), false))
		var equipment_bonus: Dictionary = card.get("equipmentBonus", {})
		if _sum_stats(equipment_bonus) > 0:
			equipment_flow.add_child(_build_chip("장비 보정 %s" % _format_stats_from_dict(equipment_bonus), GOLD, true))
	elif category == "equipment":
		var slot_name := str(card.get("equipmentSlot", ""))
		equipment_flow.add_child(_build_chip("슬롯: %s" % EQUIPMENT_SLOT_LABELS.get(slot_name, slot_name), Color("7ea6d8"), true))
		if str(card.get("equippedToName", "")) != "":
			equipment_flow.add_child(_build_chip("착용자: %s" % str(card.get("equippedToName", "")), GOLD, true))
	else:
		var info_kind := str(card.get("infoKind", ""))
		if info_kind != "":
			equipment_flow.add_child(_build_chip(INFO_KIND_LABELS.get(info_kind, info_kind), Color("8c7bc0"), true))
	for tag_name in card.get("tags", []):
		equipment_flow.add_child(_build_chip("#%s" % str(tag_name), Color("6c88a8"), false))


func _build_card_tile(card_entry: Dictionary) -> Control:
	var button := Button.new()
	button.text = ""
	button.custom_minimum_size = Vector2(220, 196)
	button.focus_mode = Control.FOCUS_NONE
	var accent := _accent_for_card(card_entry)
	var is_selected := str(card_entry.get("instanceId", "")) == selected_card_instance_id
	var background := NAVY_PANEL_ALT if not bool(card_entry.get("isCommitted", false)) else NAVY_DEEP
	button.add_theme_stylebox_override("normal", _card_style(background, accent, is_selected))
	button.add_theme_stylebox_override("hover", _card_style(background.lightened(0.08), accent.lightened(0.12), true))
	button.add_theme_stylebox_override("pressed", _card_style(background.lightened(0.12), GOLD_SOFT, true))
	button.pressed.connect(_select_card.bind(str(card_entry.get("instanceId", ""))))

	var margin := MarginContainer.new()
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_theme_constant_override("margin_left", 14)
	margin.add_theme_constant_override("margin_top", 14)
	margin.add_theme_constant_override("margin_right", 14)
	margin.add_theme_constant_override("margin_bottom", 14)
	button.add_child(margin)

	var stack := VBoxContainer.new()
	stack.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stack.add_theme_constant_override("separation", 7)
	margin.add_child(stack)

	var name_label := Label.new()
	name_label.text = str(card_entry.get("name", "카드"))
	name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	name_label.add_theme_color_override("font_color", INK)
	name_label.add_theme_font_size_override("font_size", 18)
	stack.add_child(name_label)

	var type_label := Label.new()
	type_label.text = _card_type_text(card_entry)
	type_label.add_theme_color_override("font_color", GOLD_SOFT)
	stack.add_child(type_label)

	var status_line := _card_status_text(card_entry)
	if status_line != "":
		var status_label_local := Label.new()
		status_label_local.text = status_line
		status_label_local.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		status_label_local.add_theme_color_override("font_color", Color("d7a07a") if bool(card_entry.get("isCommitted", false)) else MUTED)
		stack.add_child(status_label_local)

	var stats_label := Label.new()
	stats_label.text = _format_card_stats(card_entry)
	stats_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stats_label.add_theme_color_override("font_color", INK)
	stack.add_child(stats_label)

	var desc_label := Label.new()
	desc_label.text = _card_footer_text(card_entry)
	desc_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desc_label.add_theme_color_override("font_color", MUTED)
	stack.add_child(desc_label)

	return button


func _select_event(index: int) -> void:
	selected_event_index = index
	_render()


func _select_card(instance_id: String) -> void:
	selected_card_instance_id = instance_id
	_render()


func _assign_primary() -> void:
	if _can_assign_selected_as_primary():
		selected_primary_instance_id = selected_card_instance_id
		if selected_support_instance_id == selected_primary_instance_id:
			selected_support_instance_id = ""
		_render()


func _assign_support() -> void:
	if _can_assign_selected_as_support():
		selected_support_instance_id = selected_card_instance_id
		if selected_primary_instance_id == selected_support_instance_id:
			selected_primary_instance_id = ""
		_render()


func _clear_slots() -> void:
	selected_primary_instance_id = ""
	selected_support_instance_id = ""
	_render()


func _commit_event() -> void:
	if not _can_commit_current_event():
		return
	session.play_current_event(selected_primary_instance_id, selected_support_instance_id)
	_reset_selection(false)
	_refresh_view()


func _skip_event() -> void:
	session.skip_current_event()
	_reset_selection(false)
	_refresh_view()


func _visit_tavern() -> void:
	session.visit_tavern()
	_refresh_view()


func _end_day() -> void:
	session.end_day()
	_reset_selection(false)
	_refresh_view()


func _save_run() -> void:
	session.save_to_disk()
	_refresh_view()


func _load_run() -> void:
	if session.load_from_disk():
		_reset_selection(true)
	_refresh_view()


func _start_new_run() -> void:
	session.new_run()
	_reset_selection(true)
	_refresh_view()


func _reset_selection(reset_card: bool) -> void:
	selected_primary_instance_id = ""
	selected_support_instance_id = ""
	selected_event_index = 0
	if reset_card:
		selected_card_instance_id = ""


func _can_assign_selected_as_primary() -> bool:
	var event := _selected_event()
	var card := _selected_card()
	if event.is_empty() or card.is_empty():
		return false
	if not bool(event.get("isCurrent", false)):
		return false
	return str(card.get("category", "")) == "person" and bool(card.get("isUsable", false))


func _can_assign_selected_as_support() -> bool:
	var event := _selected_event()
	var card := _selected_card()
	if event.is_empty() or card.is_empty():
		return false
	if not bool(event.get("isCurrent", false)):
		return false
	if int(event.get("infoSlots", 0)) <= 0:
		return false
	return (
		str(card.get("category", "")) == "info"
		and str(card.get("infoKind", "")) == "general"
		and bool(card.get("isUsable", false))
	)


func _can_commit_current_event() -> bool:
	var event := _selected_event()
	if event.is_empty() or not bool(event.get("isCurrent", false)):
		return false
	if selected_primary_instance_id == "":
		return false
	if int(event.get("infoSlots", 0)) > 0 and selected_support_instance_id == "":
		return false
	return true


func _slot_name(card: Dictionary, empty_text: String) -> String:
	if card.is_empty():
		return empty_text
	return str(card.get("name", empty_text))


func _card_type_text(card: Dictionary) -> String:
	var category := str(card.get("category", ""))
	var label: String = str(CATEGORY_LABELS.get(category, category))
	if category == "info":
		var info_kind := str(card.get("infoKind", ""))
		if INFO_KIND_LABELS.has(info_kind):
			return "%s / %s" % [label, INFO_KIND_LABELS[info_kind]]
	if category == "equipment":
		var slot_name := str(card.get("equipmentSlot", ""))
		if slot_name != "":
			return "%s / %s" % [label, EQUIPMENT_SLOT_LABELS.get(slot_name, slot_name)]
	return label


func _card_status_text(card: Dictionary) -> String:
	if str(card.get("instanceId", "")) == selected_primary_instance_id:
		return "주역 슬롯에 지정됨"
	if str(card.get("instanceId", "")) == selected_support_instance_id:
		return "지원 슬롯에 지정됨"
	if bool(card.get("isCommitted", false)):
		return "임무 중 · %d턴 남음" % int(card.get("busyTurnsRemaining", 0))
	if str(card.get("category", "")) == "equipment" and str(card.get("equippedToName", "")) != "":
		return "장착: %s" % str(card.get("equippedToName", ""))
	var attached_names: Array = card.get("attachedEquipmentNames", [])
	if not attached_names.is_empty():
		return "장착 중: %s" % ", ".join(_stringify_array(attached_names))
	if bool(card.get("isInHand", false)):
		return "즉시 투입 가능"
	return ""


func _card_footer_text(card: Dictionary) -> String:
	var tags: Array = card.get("tags", [])
	if not tags.is_empty():
		return ", ".join(_stringify_array(tags))
	return str(card.get("description", ""))


func _format_card_stats(card: Dictionary) -> String:
	var stats: Dictionary = card.get("stats", {})
	var stat_parts: Array[String] = []
	for stat_name in ["strength", "agility", "intelligence", "charm"]:
		stat_parts.append("%s %d" % [STAT_LABELS.get(stat_name, stat_name), int(stats.get(stat_name, 0))])
	var power_bonus := int(card.get("powerBonus", 0))
	if power_bonus > 0:
		stat_parts.append("숙련 +%d" % power_bonus)
	return " | ".join(stat_parts)


func _format_check_stats(check_stats: Array) -> String:
	var names: Array[String] = []
	for stat_name in check_stats:
		names.append(STAT_LABELS.get(str(stat_name), str(stat_name)))
	return ", ".join(names)


func _format_stats_from_dict(stats: Dictionary) -> String:
	var stat_parts: Array[String] = []
	for stat_name in ["strength", "agility", "intelligence", "charm"]:
		var value := int(stats.get(stat_name, 0))
		if value > 0:
			stat_parts.append("%s +%d" % [STAT_LABELS.get(stat_name, stat_name), value])
	if stat_parts.is_empty():
		return "없음"
	return ", ".join(stat_parts)


func _sum_stats(stats: Dictionary) -> int:
	var total := 0
	for stat_name in ["strength", "agility", "intelligence", "charm"]:
		total += int(stats.get(stat_name, 0))
	return total


func _build_chip(text: String, border_color: Color, emphasize: bool) -> Control:
	var chip_panel := PanelContainer.new()
	chip_panel.add_theme_stylebox_override("panel", _chip_style(border_color))
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 10)
	margin.add_theme_constant_override("margin_top", 6)
	margin.add_theme_constant_override("margin_right", 10)
	margin.add_theme_constant_override("margin_bottom", 6)
	chip_panel.add_child(margin)
	var label := Label.new()
	label.text = text
	label.add_theme_color_override("font_color", INK if emphasize else GOLD_SOFT)
	label.add_theme_font_size_override("font_size", 14)
	margin.add_child(label)
	return chip_panel


func _apply_theme() -> void:
	title_label.add_theme_color_override("font_color", GOLD_SOFT)
	title_label.add_theme_font_size_override("font_size", 28)
	subtitle_label.add_theme_color_override("font_color", MUTED)
	status_label.add_theme_color_override("font_color", GOLD_SOFT)
	map_header.add_theme_color_override("font_color", GOLD_SOFT)
	map_header.add_theme_font_size_override("font_size", 24)
	map_subheader.add_theme_color_override("font_color", MUTED)
	detail_eyebrow.add_theme_color_override("font_color", GOLD_SOFT)
	detail_title.add_theme_color_override("font_color", INK)
	detail_title.add_theme_font_size_override("font_size", 24)
	detail_description.add_theme_color_override("font_color", MUTED)
	detail_check.add_theme_color_override("font_color", GOLD_SOFT)
	detail_requirement.add_theme_color_override("font_color", MUTED)
	detail_reward.add_theme_color_override("font_color", MUTED)
	selection_eyebrow.add_theme_color_override("font_color", GOLD_SOFT)
	primary_slot_label.add_theme_color_override("font_color", INK)
	support_slot_label.add_theme_color_override("font_color", INK)
	session_message.add_theme_color_override("font_color", GOLD_SOFT)
	inspector_eyebrow.add_theme_color_override("font_color", GOLD_SOFT)
	inspector_title.add_theme_color_override("font_color", INK)
	inspector_title.add_theme_font_size_override("font_size", 22)
	inspector_meta.add_theme_color_override("font_color", GOLD_SOFT)
	inspector_stats.add_theme_color_override("font_color", INK)
	inspector_description.add_theme_color_override("font_color", MUTED)
	rail_header.add_theme_color_override("font_color", GOLD_SOFT)
	rail_header.add_theme_font_size_override("font_size", 22)
	top_bar.add_theme_stylebox_override("panel", _panel_style(NAVY_PANEL, GOLD))
	map_panel.add_theme_stylebox_override("panel", _panel_style(NAVY_PANEL, GOLD))
	detail_panel.add_theme_stylebox_override("panel", _panel_style(NAVY_PANEL, GOLD))
	rail_panel.add_theme_stylebox_override("panel", _panel_style(NAVY_PANEL, GOLD))
	for button in [new_button, load_button, save_button, refresh_button, assign_primary_button, assign_support_button, clear_slots_button, commit_button, skip_button, tavern_button, end_day_button]:
		button.add_theme_color_override("font_color", INK)
		button.add_theme_stylebox_override("normal", _button_style(NAVY_PANEL_ALT))
		button.add_theme_stylebox_override("hover", _button_style(Color("18365b")))
		button.add_theme_stylebox_override("pressed", _button_style(Color("254871")))
		button.add_theme_stylebox_override("disabled", _button_style(Color("0b1624")))


func _style_event_button(button: Button, is_selected: bool, is_current: bool) -> void:
	var background := NAVY_PANEL_ALT
	if is_current:
		background = Color("1d3c60")
	if is_selected:
		background = Color("315d8f")
	button.add_theme_color_override("font_color", INK)
	button.add_theme_color_override("font_hover_color", INK)
	button.add_theme_stylebox_override("normal", _button_style(background))
	button.add_theme_stylebox_override("hover", _button_style(Color("3d6b9f")))
	button.add_theme_stylebox_override("pressed", _button_style(Color("4d7bb1")))


func _panel_style(background: Color, border: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = background
	style.border_color = border
	style.set_border_width_all(2)
	style.set_corner_radius_all(16)
	return style


func _button_style(background: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = background
	style.border_color = GOLD
	style.set_border_width_all(2)
	style.set_corner_radius_all(14)
	style.content_margin_left = 10
	style.content_margin_right = 10
	style.content_margin_top = 8
	style.content_margin_bottom = 8
	return style


func _card_style(background: Color, border: Color, is_selected: bool) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = background
	style.border_color = GOLD_SOFT if is_selected else border
	style.set_border_width_all(3 if is_selected else 2)
	style.set_corner_radius_all(14)
	style.content_margin_left = 6
	style.content_margin_right = 6
	style.content_margin_top = 6
	style.content_margin_bottom = 6
	return style


func _chip_style(border_color: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	var fill := border_color
	fill.a = 0.12
	style.bg_color = fill
	style.border_color = border_color
	style.set_border_width_all(1)
	style.set_corner_radius_all(10)
	return style


func _accent_for_card(card: Dictionary) -> Color:
	return CATEGORY_ACCENTS.get(str(card.get("category", "")), GOLD)


func _stringify_array(items: Array) -> Array[String]:
	var values: Array[String] = []
	for item in items:
		values.append(str(item))
	return values


func _clear_children(node: Node) -> void:
	for child in node.get_children():
		child.queue_free()
