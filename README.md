# Raspberry PI Scan Station for Speisekammer.App

Tested with:
- Raspberry PI 3B
- Raspbian PI OS (Debian Bullseye)

Right now just supports one specific USB scanner, needs more work to be more generic.

Perform the following steps to get it running:
- Create an SD Card with "Raspberry PI Imager", choosing Raspberry PI OS. I chose the lite image without a desktop.
  <img width="687" alt="Bildschirmfoto 2024-02-29 um 12 51 39" src="https://github.com/speisekammer/raspi-scan-station/assets/468039/f7fc02e7-53fd-4268-81d9-88aebf2a8ad0">
- Connect to your PI using SSH or a monitor and keyboard
- Download this repo to you Raspberry PI: `git clone https://github.com/speisekammer/raspi-scan-station`
- `cd raspi-scan-station`
- `pip install evdev requests ujson`
- Get a Speisekammer.App API key from here: https://app.speisekammer.app/developer
- Create a config file named `config.json` with your account data:
```
{
  "token": "your_api_key",
  "communityId": "your_community_id",
  "storageLocationId": "your_storage_location_id"
}
```
- Print a sheet with the "INSERT" and "REMOVE" barcodes, located in `doc/Speisekammer.App Scan Station.pdf`
- Run the scanner script: `python scanner.py`