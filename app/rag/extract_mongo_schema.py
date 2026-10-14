from pprint import pprint
from pymongo import MongoClient
import os
import json 
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# get file path
SCHEMA_PATH = Path(r'C:\Users\Akhil\Downloads\ciq-ai\app\rag\knowledge_base\db_schema.json')
FIELD_DESCRIPTION_PATH = Path(r'C:\Users\Akhil\Downloads\ciq-ai\app\rag\knowledge_base\field-descriptions.json')
DATABASE_DIR = SCHEMA_PATH.parent
OUTPUT_PATH = DATABASE_DIR / "output.json"

# connect mongodb
client = MongoClient(os.getenv("MONGO_OPERATOR_URI"))
operator_db = client["priva_db"]

# load files from path
def load_json_file():
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)
    
def load_field_descriptions():
    with open(FIELD_DESCRIPTION_PATH, "r") as f:
        return json.load(f)
    
# write file to specified path 
def write_json_file(data):
    with open(OUTPUT_PATH, 'w') as file:
        json.dump(data, file, indent=2)

db_schema  = load_json_file()
field_descriptions = load_field_descriptions()   

def clean_dict(d: dict):
    """Remove keys with None/empty values."""
    return {k: v for k, v in d.items() if v not in (None, "", [], {}, ())}

def normalize_collection_name(schema_name: str) -> str:
    camel = schema_name[0].lower() + schema_name[1:]
    if camel.endswith("s"):
        return camel
    elif camel.endswith("y"):
        if camel == "paymentGateway":
            return "paymentGateways"
        return camel[:-1] + "ies"
    else:
        return camel + "s"


# Converts array → { field: description }
def build_description_map(description_json, collection_name):
    """
    Extracts {field, description} pairs from any nested structure
    inside description_json[collection_name].
    Supports:
      - flat arrays
      - nested objects
      - deeply nested arrays/dicts
    """
    description_map = {}
    def extract(node):
        if isinstance(node, dict):
            # ✅ If this object contains a field-description pair
            if "field" in node and "description" in node:
                description_map[node["field"]] = node["description"]

            # ✅ Traverse deeper
            for value in node.values():
                extract(value)

        elif isinstance(node, list):
            for item in node:
                extract(item)

        # Other types ignored
        return

    # Get the root array for the collection (may contain nested layers)
    root = description_json.get(collection_name, [])

    extract(root)

    return description_map


# Lookup
def get_field_description(field_name, description_map):
    return description_map.get(field_name)

# parsing raw definitions from schema
def parse_definitions(schema_json):
    definitions = schema_json.get("definitions", {})
    parsed = {}

    for key_name, block in definitions.items():
        collection_name = normalize_collection_name(block.get("title", key_name))

        # ✅ build description lookup
        description_map = build_description_map(field_descriptions, collection_name)

        properties = block.get("properties", {})
        required = list(set(block.get("required", [])))
        indexes = block.get("indexes", [])

        field_map = {}
        relationships = []
        index_list = []
        index_field_options = {}

        # ✅ Parse indexes (fixed)
        for idx in indexes:
            if isinstance(idx, list) and len(idx) == 2:
                field_spec = idx[0]    
                options = idx[1]

                index_list.append({"fields": field_spec, "options": options})

                for field_name, direction in field_spec.items():
                    index_field_options.setdefault(field_name, {})
                    index_field_options[field_name]["indexed"] = True

                    for opt_key, opt_val in options.items():
                        index_field_options[field_name][opt_key] = opt_val

        # ✅ Parse fields (fixed)
        for field_name, field_meta in properties.items():
            field_info = {
                "required": field_name in required,
                "enum": field_meta.get("enum"),
                "format": field_meta.get("format"),
                "pattern": field_meta.get("pattern"),
                "description": get_field_description(field_name, description_map)
            }

            field_info = clean_dict(field_info)

            if field_name in index_field_options:
                field_info.update(index_field_options[field_name])

            # ✅ Relationship (x-ref)
            if "x-ref" in field_meta:
                ref_target = field_meta["x-ref"]

                relationships.append({
                    "from_collection": collection_name,
                    "from_field": field_name,
                    "to_collection": normalize_collection_name(ref_target),
                    "to_field": "_id",
                    "relationship_type": "x-ref",
                })

                field_info["ref"] = normalize_collection_name(ref_target)

            field_map[field_name] = field_info

        # ✅ Deduplicate relationships
        unique_relationships = []
        seen_rel = set()
        for rel in relationships:
            sig = (rel["from_collection"], rel["from_field"], rel["to_collection"])
            if sig not in seen_rel:
                seen_rel.add(sig)
                unique_relationships.append(rel)

        parsed[collection_name] = {
            "collection": collection_name,
            "fields": field_map,
            "required": required,
            "indexes": index_list,
            "relationships": unique_relationships,
        }

    return parsed


result = parse_definitions(db_schema)

write_json_file({
    "players": result["players"],
    "countries": result["countries"],
    "transactions":  result["transactions"],
    "paymentGateways": result["paymentGateways"],
    'playerCategorizations': result["playerCategorizations"],
    "providers": result["providers"],
    "tournaments": result["tournaments"],
    "games": result["games"],
    "categories": result["categories"],
    "communications": result["communications"],
    "emailCredentials": result["emailCredentials"],
    "emailTemplates": result["emailTemplates"]
})

print('file saved to target path')