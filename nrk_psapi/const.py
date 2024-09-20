"""NRK Podcast API constants."""

import logging

LOGGER = logging.getLogger(__name__)
PSAPI_BASE_URL = "https://psapi.nrk.no"
NRK_RADIO_BASE_URL = "https://radio.nrk.no/podkast"

DISK_CACHE_SIZE_LIMIT = 5 * 1024 * 1024 * 1024  # 5GB
DISK_CACHE_DURATION = 60 * 60  # 1 hour
