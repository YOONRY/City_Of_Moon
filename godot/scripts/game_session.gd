extends RefCounted
class_name GameSession

const SAVE_PATH := "user://city_of_moon_save.json"
const CATEGORY_ORDER := {
	"person": 0,
	"info": 1,
	"equipment": 2,
}
const EVENT_KIND_ORDER := {
	"incident": 0,
	"daily": 1,
	"special": 2,
}
const STAT_FIELDS := ["strength", "agility", "intelligence", "charm"]

var content: Dictionary = {}
var rules: Dictionary = {}
var card_defs: Dictionary = {}
var event_templates: Dictionary = {}
var rng := RandomNumberGenerator.new()
var state: Dictionary = {}
var last_message := ""


func setup(payload: Dictionary) -> void:
	content = payload.duplicate(true)
	rules = content.get("rules", {})
	card_defs.clear()
	for card in content.get("cards", []):
		card_defs[str(card.get("id", ""))] = card
	event_templates.clear()
	for event_template in content.get("eventTemplates", []):
		event_templates[str(event_template.get("templateId", event_template.get("id", "")))] = event_template
	rng.seed = 20260413
	new_run()


func has_save() -> bool:
	return FileAccess.file_exists(SAVE_PATH)


func save_to_disk() -> bool:
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file == null:
		last_message = "저장 파일을 열 수 없습니다."
		return false
	file.store_string(
		JSON.stringify(
			{
				"state": state,
				"rngState": str(rng.state),
			},
			"\t"
		)
	)
	last_message = "현재 런을 저장했습니다."
	return true


func load_from_disk() -> bool:
	if not has_save():
		last_message = "불러올 저장 파일이 없습니다."
		return false
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		last_message = "저장 파일을 읽을 수 없습니다."
		return false
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		last_message = "저장 파일 형식이 올바르지 않습니다."
		return false
	state = _normalize_state(parsed.get("state", {}))
	rng.state = int(str(parsed.get("rngState", "0")))
	_normalize_equipment_assignments()
	_sort_events_in_place(state.get("events", []))
	last_message = "저장된 런을 불러왔습니다."
	return true


func new_run() -> void:
	state = _normalize_state(content.get("previewState", {}))
	_normalize_equipment_assignments()
	_sort_events_in_place(state.get("events", []))
	last_message = "새 런을 시작했습니다."


func get_message() -> String:
	return last_message


func get_view_state() -> Dictionary:
	var collection := _serialize_collection()
	var hand_ids := _build_hand_order()
	return {
		"day": int(state.get("day", 1)),
		"money": int(state.get("money", 0)),
		"stability": int(state.get("stability", 0)),
		"weeklyTaxAmount": int(rules.get("weeklyTaxAmount", 0)),
		"daysUntilTax": days_until_tax(),
		"completedEvents": int(state.get("completedEvents", 0)),
		"uniqueCards": _unique_cards_owned(),
		"totalInstances": collection.size(),
		"readyPeople": _ready_person_count(),
		"tavernVisitsToday": int(state.get("tavernVisitsToday", 0)),
		"canVisitTavern": _can_visit_tavern(),
		"isWon": is_won(),
		"isLost": is_lost(),
		"hasSave": has_save(),
		"message": last_message,
		"handOrder": hand_ids,
		"collection": collection,
		"events": _serialize_events(),
	}


func play_current_event(primary_instance_id: String, support_instance_id: String = "") -> bool:
	var event := _current_event()
	if event.is_empty():
		last_message = "해결할 의뢰가 없습니다."
		return false

	var primary_instance := _instance_by_id(primary_instance_id)
	if primary_instance.is_empty():
		last_message = "주역 인물을 먼저 지정하세요."
		return false
	var primary_card := _card_def(str(primary_instance.get("cardId", "")))
	if str(primary_card.get("category", "")) != "person":
		last_message = "주역 슬롯에는 인물 카드만 둘 수 있습니다."
		return false
	if not _is_available(primary_instance):
		last_message = "선택한 인물은 아직 다른 임무 중입니다."
		return false

	var support_instance: Dictionary = {}
	var support_card: Dictionary = {}
	if support_instance_id != "":
		support_instance = _instance_by_id(support_instance_id)
		support_card = _card_def(str(support_instance.get("cardId", "")))
		if str(support_card.get("category", "")) != "info" or str(support_card.get("infoKind", "")) != "general":
			last_message = "지원 슬롯에는 범용 정보만 둘 수 있습니다."
			return false
		if not _is_available(support_instance):
			last_message = "선택한 정보 카드는 아직 임무 중입니다."
			return false
		if support_instance_id == primary_instance_id:
			last_message = "같은 카드를 두 슬롯에 동시에 둘 수 없습니다."
			return false

	if int(event.get("infoSlots", 0)) > 0 and support_instance_id == "":
		last_message = "이 의뢰는 범용 정보 지원이 필요합니다."
		return false
	if int(event.get("infoSlots", 0)) == 0:
		support_instance_id = ""

	var has_required_info := _owns_required_info(event)
	var score := _event_check_total(primary_instance_id, event, support_instance_id)
	var success := has_required_info and score >= int(event.get("difficulty", 0))
	var stability_delta := int(event.get("successDelta", 0)) if success else int(event.get("failureDelta", 0))
	state["stability"] = int(state.get("stability", 0)) + stability_delta
	state["completedEvents"] = int(state.get("completedEvents", 0)) + 1

	_reserve_card_for_days(primary_instance_id, int(event.get("timeCost", 1)))
	_reserve_attached_equipment(primary_instance_id, int(event.get("timeCost", 1)))
	if support_instance_id != "":
		_reserve_card_for_days(support_instance_id, int(event.get("timeCost", 1)))

	var events: Array = state.get("events", [])
	if not events.is_empty():
		events.remove_at(0)

	var reward_text := ""
	if success:
		var payout := int(event.get("payout", 0))
		state["money"] = int(state.get("money", 0)) + payout
		if event.get("rewardCardIds", []).size() > 0:
			var reward_card_id := str(event.get("rewardCardIds", [])[0])
			var reward_instance := _add_card_to_collection(reward_card_id)
			reward_text = " 보상 카드 %s 획득." % str(reward_instance.get("name", reward_card_id))
	else:
		if str(event.get("kind", "")) == "special":
			state["specialChainFailed"] = true

	if success and str(event.get("kind", "")) == "special":
		state["specialChainProgress"] = max(
			int(state.get("specialChainProgress", 0)),
			int(event.get("chainStep", 0))
		)

	_sort_events_in_place(events)
	last_message = _build_resolution_message(event, primary_instance, primary_card, support_instance, support_card, success, score, reward_text)
	return success


func skip_current_event() -> void:
	var events: Array = state.get("events", [])
	if events.is_empty():
		last_message = "넘길 의뢰가 없습니다."
		return
	var event: Dictionary = events[0]
	events.remove_at(0)
	if str(event.get("kind", "")) == "special":
		events.append(event)
		_sort_events_in_place(events)
		last_message = "특수 의뢰를 보류하고 뒤로 미뤘습니다."
	else:
		last_message = "의뢰를 일단 넘겼습니다."


func visit_tavern() -> bool:
	if not _can_visit_tavern():
		if int(state.get("tavernVisitsToday", 0)) >= 1:
			last_message = "오늘은 이미 술집 정보를 캤습니다."
		else:
			last_message = "술집 정보를 캐려면 크라운이 더 필요합니다."
		return false
	var templates := _incident_templates("tavern")
	if templates.is_empty():
		last_message = "지금은 술집에서 건질 만한 소문이 없습니다."
		return false
	state["money"] = int(state.get("money", 0)) - int(rules.get("tavernVisitCost", 2))
	state["tavernVisitsToday"] = 1
	var template: Dictionary = templates[_pick_random_index(templates.size())]
	var events: Array = state.get("events", [])
	events.append(_build_offer(template))
	_sort_events_in_place(events)
	last_message = "술집에서 새 돌발 사건을 건져냈습니다."
	return true


func end_day() -> void:
	state["day"] = int(state.get("day", 1)) + 1
	state["tavernVisitsToday"] = 0
	_pay_weekly_tax()
	_refresh_day_board()
	last_message = "턴을 종료하고 다음 날로 넘어갔습니다."


func is_won() -> bool:
	return (
		_special_templates().size() > 0
		and int(state.get("specialChainProgress", 0)) >= _special_templates().size()
		and not bool(state.get("specialChainFailed", false))
	)


func is_lost() -> bool:
	return int(state.get("stability", 0)) <= 0


func days_until_tax() -> int:
	return _next_tax_day() - int(state.get("day", 1))


func _normalize_state(raw_state: Dictionary) -> Dictionary:
	var normalized_collection: Array = []
	for card_entry in raw_state.get("collection", []):
		normalized_collection.append(
			{
				"instanceId": str(card_entry.get("instanceId", "")),
				"cardId": str(card_entry.get("cardId", "")),
				"powerBonus": int(card_entry.get("powerBonus", 0)),
				"busyUntilDay": int(card_entry.get("busyUntilDay", 0)),
				"equippedToInstanceId": str(card_entry.get("equippedToInstanceId", "")),
			}
		)
	return {
		"day": int(raw_state.get("day", 1)),
		"money": int(raw_state.get("money", 0)),
		"stability": int(raw_state.get("stability", 0)),
		"completedEvents": int(raw_state.get("completedEvents", 0)),
		"specialChainProgress": int(raw_state.get("specialChainProgress", 0)),
		"specialChainFailed": bool(raw_state.get("specialChainFailed", false)),
		"offerSequence": int(raw_state.get("offerSequence", 0)),
		"tavernVisitsToday": int(raw_state.get("tavernVisitsToday", 0)),
		"collection": normalized_collection,
		"events": raw_state.get("events", []).duplicate(true),
	}


func _serialize_events() -> Array:
	var serialized: Array = []
	var events: Array = state.get("events", [])
	for index in range(events.size()):
		var event: Dictionary = events[index].duplicate(true)
		event["isCurrent"] = index == 0
		serialized.append(event)
	return serialized


func _serialize_collection() -> Array:
	var collection := _sorted_collection_instances()
	var hand_ids := _build_hand_order()
	var hand_lookup: Dictionary = {}
	for instance_id in hand_ids:
		hand_lookup[instance_id] = true

	var serialized: Array = []
	for instance_data in collection:
		var card := _card_def(str(instance_data.get("cardId", "")))
		var attached_equipment := []
		var attached_names: Array = []
		if str(card.get("category", "")) == "person":
			for equipment_instance in _equipment_for(str(instance_data.get("instanceId", ""))):
				var equipment_card := _card_def(str(equipment_instance.get("cardId", "")))
				attached_names.append(str(equipment_card.get("name", "")))
				attached_equipment.append(
					{
						"instanceId": str(equipment_instance.get("instanceId", "")),
						"cardId": str(equipment_instance.get("cardId", "")),
						"name": str(equipment_card.get("name", "")),
						"slot": str(equipment_card.get("equipmentSlot", "")),
						"stats": _base_stats(equipment_card),
					}
				)
		var busy_turns_remaining: int = max(int(instance_data.get("busyUntilDay", 0)) - int(state.get("day", 1)) + 1, 0)
		var equipped_to_name := ""
		if str(card.get("category", "")) == "equipment" and str(instance_data.get("equippedToInstanceId", "")) != "":
			var target := _instance_by_id(str(instance_data.get("equippedToInstanceId", "")))
			var target_card := _card_def(str(target.get("cardId", "")))
			equipped_to_name = str(target_card.get("name", ""))
		serialized.append(
			{
				"instanceId": str(instance_data.get("instanceId", "")),
				"cardId": str(instance_data.get("cardId", "")),
				"name": str(card.get("name", "")),
				"category": str(card.get("category", "")),
				"equipmentSlot": str(card.get("equipmentSlot", "")),
				"infoKind": str(card.get("infoKind", "")),
				"rarity": str(card.get("rarity", "")),
				"tags": card.get("tags", []).duplicate(true),
				"description": str(card.get("description", "")),
				"powerBonus": int(instance_data.get("powerBonus", 0)),
				"baseStats": _base_stats(card),
				"stats": _effective_stats(instance_data),
				"isUsable": _is_available(instance_data),
				"isCommitted": int(instance_data.get("busyUntilDay", 0)) >= int(state.get("day", 1)),
				"busyUntilDay": int(instance_data.get("busyUntilDay", 0)),
				"busyTurnsRemaining": busy_turns_remaining,
				"isInHand": hand_lookup.has(str(instance_data.get("instanceId", ""))),
				"equippedToInstanceId": str(instance_data.get("equippedToInstanceId", "")),
				"equippedToName": equipped_to_name,
				"attachedEquipmentNames": attached_names,
				"attachedEquipment": attached_equipment,
				"equipmentBonus": _equipment_bonus_for(str(instance_data.get("instanceId", ""))),
			}
		)
	return serialized


func _base_stats(card: Dictionary) -> Dictionary:
	var stats: Dictionary = {}
	for stat_name in STAT_FIELDS:
		stats[stat_name] = int(card.get("stats", {}).get(stat_name, 0))
	return stats


func _effective_stats(instance_data: Dictionary) -> Dictionary:
	var card := _card_def(str(instance_data.get("cardId", "")))
	var totals := _base_stats(card)
	if str(card.get("category", "")) == "person":
		var equipment_bonus := _equipment_bonus_for(str(instance_data.get("instanceId", "")))
		for stat_name in STAT_FIELDS:
			totals[stat_name] = int(totals.get(stat_name, 0)) + int(equipment_bonus.get(stat_name, 0))
	return totals


func _equipment_bonus_for(person_instance_id: String) -> Dictionary:
	var totals := {}
	for stat_name in STAT_FIELDS:
		totals[stat_name] = 0
	for equipment_instance in _equipment_for(person_instance_id):
		if not _is_available(equipment_instance):
			continue
		var equipment_card := _card_def(str(equipment_instance.get("cardId", "")))
		for stat_name in STAT_FIELDS:
			totals[stat_name] = int(totals.get(stat_name, 0)) + int(equipment_card.get("stats", {}).get(stat_name, 0))
	return totals


func _equipment_for(person_instance_id: String) -> Array:
	var equipment: Array = []
	for instance_data in state.get("collection", []):
		var card := _card_def(str(instance_data.get("cardId", "")))
		if str(card.get("category", "")) == "equipment" and str(instance_data.get("equippedToInstanceId", "")) == person_instance_id:
			equipment.append(instance_data)
	_sort_collection_in_place(equipment)
	return equipment


func _instance_by_id(instance_id: String) -> Dictionary:
	for instance_data in state.get("collection", []):
		if str(instance_data.get("instanceId", "")) == instance_id:
			return instance_data
	return {}


func _card_def(card_id: String) -> Dictionary:
	return card_defs.get(card_id, {})


func _is_available(instance_data: Dictionary) -> bool:
	return int(instance_data.get("busyUntilDay", 0)) < int(state.get("day", 1))


func _ready_person_count() -> int:
	var count := 0
	for instance_data in state.get("collection", []):
		var card := _card_def(str(instance_data.get("cardId", "")))
		if str(card.get("category", "")) == "person" and _is_available(instance_data):
			count += 1
	return count


func _build_hand_order() -> Array:
	var ids: Array = []
	for instance_data in _sorted_collection_instances():
		var card := _card_def(str(instance_data.get("cardId", "")))
		if str(card.get("category", "")) != "equipment":
			ids.append(str(instance_data.get("instanceId", "")))
	return ids


func _sorted_collection_instances() -> Array:
	var copied: Array = state.get("collection", []).duplicate(true)
	_sort_collection_in_place(copied)
	return copied


func _sort_collection_in_place(items: Array) -> void:
	for i in range(items.size()):
		for j in range(i + 1, items.size()):
			if _collection_less(items[j], items[i]):
				var temp = items[i]
				items[i] = items[j]
				items[j] = temp


func _collection_less(a: Dictionary, b: Dictionary) -> bool:
	var card_a := _card_def(str(a.get("cardId", "")))
	var card_b := _card_def(str(b.get("cardId", "")))
	var category_a := int(CATEGORY_ORDER.get(str(card_a.get("category", "")), 99))
	var category_b := int(CATEGORY_ORDER.get(str(card_b.get("category", "")), 99))
	if category_a != category_b:
		return category_a < category_b
	var name_a := str(card_a.get("name", ""))
	var name_b := str(card_b.get("name", ""))
	if name_a != name_b:
		return name_a < name_b
	return str(a.get("instanceId", "")) < str(b.get("instanceId", ""))


func _sort_events_in_place(items: Array) -> void:
	for i in range(items.size()):
		for j in range(i + 1, items.size()):
			if _event_less(items[j], items[i]):
				var temp = items[i]
				items[i] = items[j]
				items[j] = temp


func _event_less(a: Dictionary, b: Dictionary) -> bool:
	var deadline_a := int(a.get("deadlineDay", int(state.get("day", 1))))
	var deadline_b := int(b.get("deadlineDay", int(state.get("day", 1))))
	if deadline_a != deadline_b:
		return deadline_a < deadline_b
	var kind_a := int(EVENT_KIND_ORDER.get(str(a.get("kind", "")), 99))
	var kind_b := int(EVENT_KIND_ORDER.get(str(b.get("kind", "")), 99))
	if kind_a != kind_b:
		return kind_a < kind_b
	var title_a := str(a.get("title", ""))
	var title_b := str(b.get("title", ""))
	if title_a != title_b:
		return title_a < title_b
	return str(a.get("offerId", "")) < str(b.get("offerId", ""))


func _current_event() -> Dictionary:
	var events: Array = state.get("events", [])
	if events.is_empty():
		return {}
	return events[0]


func _event_check_total(primary_instance_id: String, event: Dictionary, support_instance_id: String = "") -> int:
	var total := 0
	var primary_instance := _instance_by_id(primary_instance_id)
	var primary_stats := _effective_stats(primary_instance)
	for stat_name in event.get("checkStats", []):
		total += int(primary_stats.get(str(stat_name), 0))
	total += max(int(primary_instance.get("powerBonus", 0)), 0)
	if support_instance_id != "":
		var support_instance := _instance_by_id(support_instance_id)
		var support_stats := _effective_stats(support_instance)
		for stat_name in event.get("checkStats", []):
			total += int(support_stats.get(str(stat_name), 0))
		total += max(int(support_instance.get("powerBonus", 0)), 0)
	return total


func _owns_required_info(event: Dictionary) -> bool:
	var owned_ids: Dictionary = {}
	for instance_data in state.get("collection", []):
		owned_ids[str(instance_data.get("cardId", ""))] = true
	for card_id in event.get("requiredCardIds", []):
		if not owned_ids.has(str(card_id)):
			return false
	return true


func _build_resolution_message(
	event: Dictionary,
	primary_instance: Dictionary,
	primary_card: Dictionary,
	support_instance: Dictionary,
	support_card: Dictionary,
	success: bool,
	score: int,
	reward_text: String
) -> String:
	var primary_name := str(primary_card.get("name", "인물"))
	if success:
		var base_text := str(event.get("successText", "의뢰를 해결했습니다."))
		if not support_instance.is_empty():
			base_text = "%s (주역 %s + 지원 %s)" % [
				base_text,
				primary_name,
				str(support_card.get("name", "정보")),
			]
		return "%s 최종 수치 %d.%s" % [base_text, score, reward_text]
	if not _owns_required_info(event):
		var required_names := ", ".join(event.get("requiredCardNames", []))
		return "전용 정보 [%s]가 없어 의뢰를 진행하지 못했습니다." % required_names
	return "%s 최종 수치 %d." % [str(event.get("failureText", "의뢰 해결에 실패했습니다.")), score]


func _reserve_card_for_days(instance_id: String, days: int) -> void:
	var instance_data := _instance_by_id(instance_id)
	if instance_data.is_empty():
		return
	var commitment: int = max(days, 1)
	instance_data["busyUntilDay"] = max(
		int(instance_data.get("busyUntilDay", 0)),
		int(state.get("day", 1)) + commitment - 1
	)


func _reserve_attached_equipment(person_instance_id: String, days: int) -> void:
	for equipment_instance in _equipment_for(person_instance_id):
		_reserve_card_for_days(str(equipment_instance.get("instanceId", "")), days)


func _add_card_to_collection(card_id: String) -> Dictionary:
	var card := _card_def(card_id)
	var instance_data := {
		"instanceId": _next_instance_id(card_id),
		"cardId": card_id,
		"powerBonus": 0,
		"busyUntilDay": 0,
		"equippedToInstanceId": "",
	}
	var collection: Array = state.get("collection", [])
	collection.append(instance_data)
	if str(card.get("category", "")) == "equipment":
		_attach_equipment(str(instance_data.get("instanceId", "")))
	return {
		"instanceId": str(instance_data.get("instanceId", "")),
		"name": str(card.get("name", card_id)),
	}


func _next_instance_id(card_id: String) -> String:
	var index := 1
	var used: Dictionary = {}
	for instance_data in state.get("collection", []):
		used[str(instance_data.get("instanceId", ""))] = true
	while true:
		var candidate := "%s_instance_%d" % [card_id, index]
		if not used.has(candidate):
			return candidate
		index += 1
	return ""


func _attach_equipment(equipment_instance_id: String, target_instance_id: String = "") -> void:
	var equipment_instance := _instance_by_id(equipment_instance_id)
	if equipment_instance.is_empty():
		return
	var equipment_card := _card_def(str(equipment_instance.get("cardId", "")))
	if str(equipment_card.get("category", "")) != "equipment":
		return
	var slot_name := str(equipment_card.get("equipmentSlot", ""))
	var resolved_target := target_instance_id
	if resolved_target == "":
		resolved_target = _default_equipment_target_for_slot(slot_name)
	if resolved_target == "":
		equipment_instance["equippedToInstanceId"] = ""
		return
	var occupying := _equipped_item_for_slot(resolved_target, slot_name)
	if not occupying.is_empty() and str(occupying.get("instanceId", "")) != equipment_instance_id:
		occupying["equippedToInstanceId"] = ""
	equipment_instance["equippedToInstanceId"] = resolved_target


func _equipped_item_for_slot(person_instance_id: String, slot_name: String) -> Dictionary:
	for equipment_instance in _equipment_for(person_instance_id):
		var equipment_card := _card_def(str(equipment_instance.get("cardId", "")))
		if str(equipment_card.get("equipmentSlot", "")) == slot_name:
			return equipment_instance
	return {}


func _default_equipment_target_for_slot(slot_name: String) -> String:
	for instance_data in _sorted_collection_instances():
		var card := _card_def(str(instance_data.get("cardId", "")))
		if str(card.get("category", "")) != "person":
			continue
		if _equipped_item_for_slot(str(instance_data.get("instanceId", "")), slot_name).is_empty():
			return str(instance_data.get("instanceId", ""))
	return ""


func _normalize_equipment_assignments() -> void:
	var valid_people: Dictionary = {}
	for instance_data in state.get("collection", []):
		var card := _card_def(str(instance_data.get("cardId", "")))
		if str(card.get("category", "")) == "person":
			valid_people[str(instance_data.get("instanceId", ""))] = true
	var occupied: Dictionary = {}
	for instance_data in _sorted_collection_instances():
		var card := _card_def(str(instance_data.get("cardId", "")))
		if str(card.get("category", "")) != "equipment":
			continue
		var target := str(instance_data.get("equippedToInstanceId", ""))
		var slot_key := "%s::%s" % [target, str(card.get("equipmentSlot", ""))]
		if target != "" and valid_people.has(target) and not occupied.has(slot_key):
			occupied[slot_key] = true
			continue
		_attach_equipment(str(instance_data.get("instanceId", "")))


func _next_tax_day() -> int:
	var day := int(state.get("day", 1))
	var current_week := int((day - 1) / 7)
	return (current_week + 1) * 7 + 1


func _pay_weekly_tax() -> void:
	var day := int(state.get("day", 1))
	if day <= 1 or (day - 1) % 7 != 0:
		return
	var weekly_tax := int(rules.get("weeklyTaxAmount", 0))
	if int(state.get("money", 0)) >= weekly_tax:
		state["money"] = int(state.get("money", 0)) - weekly_tax
		return
	state["money"] = 0
	state["stability"] = int(state.get("stability", 0)) - int(rules.get("weeklyTaxStabilityPenalty", 2))


func _refresh_day_board() -> void:
	_expire_outdated_offers()
	if is_won() or is_lost():
		return
	_generate_daily_offers()
	_maybe_add_random_incident()
	_ensure_special_offer()
	_sort_events_in_place(state.get("events", []))


func _generate_daily_offers() -> void:
	var events: Array = state.get("events", [])
	for event in events:
		if str(event.get("kind", "")) == "daily":
			return
	var templates := _daily_templates()
	if templates.is_empty():
		return
	var sample_size: int = min(2, templates.size())
	var selected := _pick_unique_templates(templates, sample_size)
	for template in selected:
		events.append(_build_offer(template))


func _maybe_add_random_incident() -> void:
	var events: Array = state.get("events", [])
	for event in events:
		if str(event.get("kind", "")) == "incident" and str(event.get("source", "")) != "tavern":
			return
	if rng.randf() > float(rules.get("incidentChance", 0.35)):
		return
	var templates := _incident_templates("street")
	if templates.is_empty():
		return
	events.append(_build_offer(templates[_pick_random_index(templates.size())]))


func _ensure_special_offer() -> void:
	if bool(state.get("specialChainFailed", false)):
		return
	for event in state.get("events", []):
		if str(event.get("kind", "")) == "special":
			return
	var chain := _special_templates()
	if int(state.get("specialChainProgress", 0)) >= chain.size():
		return
	if chain.is_empty():
		return
	var events: Array = state.get("events", [])
	events.append(_build_offer(chain[int(state.get("specialChainProgress", 0))]))


func _expire_outdated_offers() -> void:
	var remaining: Array = []
	for event in state.get("events", []):
		var kind := str(event.get("kind", ""))
		var expired := false
		if kind == "daily" or kind == "incident":
			expired = int(event.get("introducedDay", 0)) < int(state.get("day", 1)) or int(event.get("deadlineDay", 0)) < int(state.get("day", 1))
		elif kind == "special":
			expired = int(event.get("deadlineDay", 0)) < int(state.get("day", 1))
		if not expired:
			remaining.append(event)
		elif kind == "special":
			state["specialChainFailed"] = true
	state["events"] = remaining


func _build_offer(template: Dictionary, introduced_day: int = -1) -> Dictionary:
	var start_day := introduced_day if introduced_day > 0 else int(state.get("day", 1))
	var offer := template.duplicate(true)
	offer["offerId"] = _next_offer_id(str(template.get("templateId", template.get("id", ""))))
	offer["introducedDay"] = start_day
	offer["deadlineDay"] = start_day + max(int(template.get("deadlineDays", 1)), 1) - 1
	return offer


func _next_offer_id(template_id: String) -> String:
	state["offerSequence"] = int(state.get("offerSequence", 0)) + 1
	return "%s__d%d_n%d" % [template_id, int(state.get("day", 1)), int(state.get("offerSequence", 0))]


func _daily_templates() -> Array:
	var templates: Array = []
	for template in event_templates.values():
		if str(template.get("kind", "")) == "daily":
			templates.append(template)
	return templates


func _incident_templates(source: String) -> Array:
	var templates: Array = []
	for template in event_templates.values():
		if str(template.get("kind", "")) == "incident" and str(template.get("source", "")) == source:
			templates.append(template)
	return templates


func _special_templates() -> Array:
	var templates: Array = []
	for template in event_templates.values():
		if str(template.get("kind", "")) == "special":
			templates.append(template)
	for i in range(templates.size()):
		for j in range(i + 1, templates.size()):
			if _special_less(templates[j], templates[i]):
				var temp = templates[i]
				templates[i] = templates[j]
				templates[j] = temp
	return templates


func _special_less(a: Dictionary, b: Dictionary) -> bool:
	var storyline_a := str(a.get("storylineId", ""))
	var storyline_b := str(b.get("storylineId", ""))
	if storyline_a != storyline_b:
		return storyline_a < storyline_b
	var step_a := int(a.get("chainStep", 0))
	var step_b := int(b.get("chainStep", 0))
	if step_a != step_b:
		return step_a < step_b
	return str(a.get("templateId", a.get("id", ""))) < str(b.get("templateId", b.get("id", "")))


func _pick_unique_templates(templates: Array, count: int) -> Array:
	var pool := templates.duplicate(true)
	var picked: Array = []
	for _index in range(min(count, pool.size())):
		var chosen_index := _pick_random_index(pool.size())
		picked.append(pool[chosen_index])
		pool.remove_at(chosen_index)
	return picked


func _pick_random_index(size: int) -> int:
	if size <= 1:
		return 0
	return int(rng.randi_range(0, size - 1))


func _can_visit_tavern() -> bool:
	return int(state.get("tavernVisitsToday", 0)) < 1 and int(state.get("money", 0)) >= int(rules.get("tavernVisitCost", 2))


func _unique_cards_owned() -> int:
	var unique_ids: Dictionary = {}
	for instance_data in state.get("collection", []):
		unique_ids[str(instance_data.get("cardId", ""))] = true
	return unique_ids.size()
