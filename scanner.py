import requests
import evdev
from evdev import InputDevice, categorize, ecodes
import subproces
import ujson

# API settings
API_BASE_URL = "https://api.speisekammer.app"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}", 'accept': 'application/json'}
DEVICE_NAME = "Datalogic Scanning, Inc. Point of Sale Handable Scanner"

# Modes
INSERT_MODE = "insert"
REMOVE_MODE = "remove"
mode = INSERT_MODE  # Default mode

# Temporary store for barcode digits
barcode_digits = []

def find_scanner_device():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        print("device name", device.name)
        if DEVICE_NAME in device.name:
            return device
    return None


def beep():
    # Play a beep sound
    subprocess.run(['aplay', '/path/to/beep/sound.wav'])


def update_stock(gtin, mode):
    url = f"{API_BASE_URL}/stock/{COMMUNITY_ID}/{STORAGE_LOCATION_ID}"

    print("try to fetch stock info for gtin", gtin)
    get_response = requests.get(f"{url}/{gtin}", headers=HEADERS)

    if mode == INSERT_MODE:
        print("INSERT")
        if get_response.status_code == 200:
            response_data = get_response.json()
            print("response", response_data)
            data = {"gtin": gtin, "attributes": [{"count": response_data['attributes'][0]['count'] + 1}]}
        else:
            data = {"gtin": gtin, "attributes": [{"count": 1}]}
        response = requests.put(url, json=data, headers=HEADERS)
        print("try put send", data)

        if response.status_code == 200:
            beep()  # Acknowledge successful scan
            print("successfully added", response.json())
        else:
            print("API request failed with status code:", response.status_code, response.text)


    elif mode == REMOVE_MODE:
        print("REMOVE")
        if get_response.status_code == 200:
            response_data = get_response.json()
            request_body = response_data
            request_body['attributes'][0]['count'] = response_data['attributes'][0]['count'] - 1

            print("try put send", request_body)

            response = requests.put(url, json=request_body, headers=HEADERS)

            if response.status_code == 200:
                beep()  # Acknowledge successful scan
                print("successfully removed item, remaining item is:", response.json())
            else:
                print("API request failed with status code:", response.status_code, response.text)
        else:
            print("item not found in stock!")
    else:
        print("Invalid mode")
        return



def main():
    device = find_scanner_device()
    if device is None:
        print(f"Scanner device {DEVICE_NAME} not found.")
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        print(f"Other devices are: {devices}")
        return
    device = InputDevice(device.path)
    print(f"Using input device: {device.name}")

    global mode
    for event in device.read_loop():
        if event.type == ecodes.EV_KEY and event.value == 1:  # KeyEvent and Down
            data = categorize(event)
            if data.scancode == 2:  # '1' key, switch to INSERT_MODE
                mode = INSERT_MODE
                print("Switched to INSERT mode")
                beep()
            elif data.scancode == 3:  # '2' key, switch to REMOVE_MODE
                mode = REMOVE_MODE
                print("Switched to REMOVE mode")
                beep()
            else:
                barcode = str(data.scancode)  # Simplified; in practice, map scancode to actual barcode number
                print(f"Scanned barcode in {mode} mode: {barcode}")
                update_stock(barcode, mode)


if __name__ == "__main__":
    main()
