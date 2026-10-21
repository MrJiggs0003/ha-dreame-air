"""Constants for the Dreame Air integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "dreame_air"
MANUFACTURER = "Dreame"

CONF_REGION = "region"
CONF_DID = "did"
CONF_MODEL = "model"
CONF_HOST = "host"
CONF_MAC = "mac"
CONF_OFF_BEHAVIOR = "off_behavior"
CONF_SCAN_INTERVAL = "scan_interval"

REGIONS = ["us", "eu", "sg", "ru", "kr", "cn"]
DEFAULT_REGION = "us"

OFF_SOFT = "soft"
OFF_REAL = "real"
DEFAULT_OFF_BEHAVIOR = OFF_SOFT

DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 15
MAX_SCAN_INTERVAL = 300

# Properties are read in small batches: large get_properties calls time out.
READ_BATCH_SIZE = 8

# A property missing from this many polls in a row is shown as unavailable.
MAX_MISSED_POLLS = 2

# The cloud lags a few seconds behind writes; refresh after this delay.
POST_WRITE_REFRESH = timedelta(seconds=10)

# Filter replacement is flagged at or below these values.
FILTER_LIFE_THRESHOLD = 10
FILTER_DAYS_THRESHOLD = 14
