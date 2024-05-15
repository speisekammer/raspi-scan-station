import requests
import evdev
from evdev import InputDevice, categorize, ecodes
import ujson

try:
    config = ujson.load(open("config.json"))
    print("Successfully loaded config.json")
except FileNotFoundError:
    print("""
config.json not found. Please generate a file named config.json with your credentials:

{
    "token": "your_access_token",
    "communityId": "your_community_id",
    "storageLocationId": "your_storage_location_id"
}
""")
    exit(1)

# API settings
API_BASE_URL = "https://api.speisekammer.app"
HEADERS = {"Authorization": f"Bearer {config['token']}", "accept": "application/json"}
COMMUNITY_ID = config["communityId"]
STORAGE_LOCATION_ID = config["storageLocationId"]
target_device_names = [
    "Scanner",
    "Scanning",
    "Barcode",
    "BARCODE",
    # Add parts of the device name here, if your barcode scanner is not recognized
]

# Modes
INSERT_MODE = "insert"
REMOVE_MODE = "remove"
mode = INSERT_MODE  # Default mode

REMOVE_CODE = "02000060"  # last digit 0 = remove
INSERT_CODE = "02000091"  # last digit 1 = insert


def find_scanner_device():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        print("device name", device.name)
        if any(
            target_device_name in device.name
            for target_device_name in target_device_names
        ):
            return device
    return None


def update_stock(gtin, update_mode):
    url = f"{API_BASE_URL}/stock/{COMMUNITY_ID}/{STORAGE_LOCATION_ID}"

    print("try to fetch stock info for gtin", gtin)
    get_response = requests.get(f"{url}/{gtin}", headers=HEADERS)

    if update_mode == INSERT_MODE:
        print("INSERT")
        if get_response.status_code == 200:
            response_data = get_response.json()
            print("response", response_data)
            data = {
                "gtin": gtin,
                "attributes": [{"count": response_data["attributes"][0]["count"] + 1}],
            }
        else:
            data = {"gtin": gtin, "attributes": [{"count": 1}]}
        response = requests.put(url, json=data, headers=HEADERS)
        print("try put send", data)

        if response.status_code == 200:
            # TODO Acknowledge successful add using a beep
            print("successfully added", response.json())
        else:
            print(
                "API request failed with status code:",
                response.status_code,
                response.text,
            )

    elif update_mode == REMOVE_MODE:
        print("REMOVE")
        if get_response.status_code == 200:
            response_data = get_response.json()
            request_body = response_data
            request_body["attributes"][0]["count"] = (
                response_data["attributes"][0]["count"] - 1
            )

            print("try put send", request_body)

            response = requests.put(url, json=request_body, headers=HEADERS)

            if response.status_code == 200:
                # TODO Acknowledge successful delete using a beep
                print("successfully removed item, remaining item is:", response.json())
            else:
                print(
                    "API request failed with status code:",
                    response.status_code,
                    response.text,
                )
        else:
            print("item not found in stock!")
    else:
        print("Invalid mode")
        return


def generate_keycode_map():
    return {
        ecodes.KEY_1: "1",
        ecodes.KEY_2: "2",
        ecodes.KEY_3: "3",
        ecodes.KEY_4: "4",
        ecodes.KEY_5: "5",
        ecodes.KEY_6: "6",
        ecodes.KEY_7: "7",
        ecodes.KEY_8: "8",
        ecodes.KEY_9: "9",
        ecodes.KEY_0: "0",
    }


def main():
    keycode_map = generate_keycode_map()
    device = find_scanner_device()
    if device is None:
        print(
            """No USB scanner device found. Please connect a scanner and try again.
            If it does not work, type 'lsusb' to find the device name.
            Then add the name to the target_device_names list in the script."""
        )
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        print(f"Other devices are: {devices}")
        return
    device = InputDevice(device.path)
    print(f"Using input device: {device.name}")
    print("Waiting for next scan...")

    global mode
    scanned_code = ""
    for event in device.read_loop():
        if event.type == ecodes.EV_KEY and event.value == 1:  # KeyEvent and Down
            data = categorize(event)

            if data.scancode in keycode_map:
                scanned_code = scanned_code + keycode_map[data.scancode]
            elif data.scancode == ecodes.KEY_ENTER:
                if scanned_code == INSERT_CODE:
                    mode = INSERT_MODE
                    print("Switched to INSERT mode")
                elif scanned_code == REMOVE_CODE:
                    print("Switched to REMOVE mode")
                    mode = REMOVE_MODE
                else:
                    print(f"Scanned barcode in {mode} mode: {scanned_code}")
                    update_stock(scanned_code, mode)

                scanned_code = ""
            else:
                print(f"Ignoring unrecognized character: {data.scancode}")


if __name__ == "__main__":
    main()
