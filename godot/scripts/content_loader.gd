extends RefCounted
class_name ContentLoader

const DEFAULT_CONTENT_PATH := "res://data/content.json"


func load_content(path: String = DEFAULT_CONTENT_PATH) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_warning("Could not open content file: %s" % path)
		return {}

	var parsed := JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("Content file did not parse into a Dictionary: %s" % path)
		return {}

	return parsed
