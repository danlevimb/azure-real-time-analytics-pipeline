from copy import deepcopy
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = Path("simulator") / "configs"

SOURCE_CONFIG = CONFIG_DIR / "fleet005_live_dashboard.yaml"
TARGET_CONFIG = CONFIG_DIR / "fleet060_loada_cloud.yaml"

RUN_NAME = "fleet060_load_cloud_001"
RUN_ID = "RUN-FLEET060-LOADA-CLOUD-001"

FLEET_SIZE = 60

with SOURCE_CONFIG.open("r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Conservamos los 5 perfiles originales como templates.
templates = deepcopy(config["fleet"]["members"])

members = []

# Grid de 10 columnas x 6 filas alrededor del punto base.
cols = 10
lat_step = 0.0004
lon_step = 0.0004

for i in range(FLEET_SIZE):
    template = deepcopy(templates[i % len(templates)])

    drone_number = i + 1

    row = i // cols
    col = i % cols

    # Centrado aproximadamente alrededor de 0.
    latitude_offset = (row - 2.5) * lat_step
    longitude_offset = (col - 4.5) * lon_step

    template["drone_id"] = f"DRN-{drone_number:03d}"
    template["mission_id"] = f"MSN-{drone_number:03d}"
    template["latitude_offset"] = round(latitude_offset, 6)
    template["longitude_offset"] = round(longitude_offset, 6)

    members.append(template)

config["fleet"]["members"] = members

config["simulation"]["run_name"] = RUN_NAME
config["simulation_context"]["simulator_run_id"] = RUN_ID

with TARGET_CONFIG.open("w", encoding="utf-8") as f:
    yaml.safe_dump(
        config,
        f,
        sort_keys=False,
        allow_unicode=True,
    )

print(f"Created: {TARGET_CONFIG}")
print(f"Run ID: {RUN_ID}")
print(f"Fleet members: {len(members)}")
print(f"First drone: {members[0]['drone_id']}")
print(f"Last drone: {members[-1]['drone_id']}")