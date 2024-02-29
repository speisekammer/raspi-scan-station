from pynput.keyboard import Listener, Key
import requests
import os

# API settings
API_BASE_URL = "https://api.speisekammer.app"
COMMUNITY_ID = ""
STORAGE_LOCATION_ID = ""
ACCESS_TOKEN = ""
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}", 'accept': 'application/json'}

# Modes
INSERT_MODE = "insert"
REMOVE_MODE = "remove"
mode = INSERT_MODE  # Default mode

# Temporary store for barcode digits
barcode_digits = []


def beep():
    # Play a beep sound
    os.system('afplay /System/Library/Sounds/Ping.aiff')


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


def on_press(key):
    global barcode_digits
    try:
        if hasattr(key, 'char') and key.char is not None:
            # Handle numeric keys and special mode-switching codes
            if key.char.isdigit():
                barcode_digits.append(key.char)
            elif key.char == 'i':  # Switch to INSERT_MODE
                global mode
                mode = INSERT_MODE
                print("Switched to INSERT mode")
                beep()
                barcode_digits = []  # Clear digits
            elif key.char == 'r':  # Switch to REMOVE_MODE
                mode = REMOVE_MODE
                print("Switched to REMOVE mode")
                beep()
                barcode_digits = []  # Clear digits
    except AttributeError:
        pass


def on_release(key):
    if key == Key.enter:
        # Process the barcode when Enter is pressed
        barcode = ''.join(barcode_digits)
        if barcode:
            print(f"Scanned barcode in {mode} mode: {barcode}")
            update_stock(barcode, mode)
        # Reset the barcode_digits for the next scan
        barcode_digits.clear()


def main():
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    main()
