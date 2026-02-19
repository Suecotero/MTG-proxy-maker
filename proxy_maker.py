import os
import time
import requests
from PIL import Image

DECK_FILE = "deck.txt"
IMAGE_FOLDER = "card_images"
OUTPUT_PDF = "printable_proxies.pdf"

SCRYFALL_API = "https://api.scryfall.com/cards/named"

# ----- PRINT SETTINGS (A4 @ 300 DPI) -----

PAGE_WIDTH = 2480
PAGE_HEIGHT = 3508

CARD_WIDTH = 744
CARD_HEIGHT = 1039

COLUMNS = 3
ROWS = 3

H_MARGIN = (PAGE_WIDTH - COLUMNS * CARD_WIDTH) // 2
V_MARGIN = (PAGE_HEIGHT - ROWS * CARD_HEIGHT) // 2

session = requests.Session()


# ----- DOWNLOAD IMAGES -----

def clean_filename(name):
    return "".join(c for c in name if c.isalnum() or c in " -_").rstrip()


def get_card_data(card_name):
    params = {"fuzzy": card_name}
    r = session.get(SCRYFALL_API, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def save_image(url, filename):
    path = os.path.join(IMAGE_FOLDER, filename)

    r = session.get(url, timeout=20)
    r.raise_for_status()

    with open(path, "wb") as f:
        f.write(r.content)

    print(f"Saved {filename}")


def download_card(card_name):
    data = get_card_data(card_name)

    if "card_faces" in data:
        for i, face in enumerate(data["card_faces"]):
            if "image_uris" in face:
                url = face["image_uris"]["png"]
                name = f"{clean_filename(card_name)}_face{i+1}.png"
                save_image(url, name)
    else:
        url = data["image_uris"]["png"]
        name = f"{clean_filename(card_name)}.png"
        save_image(url, name)


def download_all_cards():
    os.makedirs(IMAGE_FOLDER, exist_ok=True)

    with open(DECK_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("//"):
                continue

            qty, name = line.split(" ", 1)

            for _ in range(int(qty)):
                download_card(name)
                time.sleep(0.1)


# ----- CREATE PDF -----

def load_images():
    imgs = []

    for file in sorted(os.listdir(IMAGE_FOLDER)):
        if file.lower().endswith(".png"):
            path = os.path.join(IMAGE_FOLDER, file)
            img = Image.open(path).convert("RGB")
            img = img.resize((CARD_WIDTH, CARD_HEIGHT))
            imgs.append(img)

    return imgs


def make_pages(images):
    pages = []

    for i in range(0, len(images), COLUMNS * ROWS):
        page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")

        subset = images[i:i + COLUMNS * ROWS]

        for idx, img in enumerate(subset):
            row = idx // COLUMNS
            col = idx % COLUMNS

            x = H_MARGIN + col * CARD_WIDTH
            y = V_MARGIN + row * CARD_HEIGHT

            page.paste(img, (x, y))

        pages.append(page)

    return pages


def create_pdf():
    images = load_images()

    if not images:
        print("No images found.")
        return

    pages = make_pages(images)

    pages[0].save(
        OUTPUT_PDF,
        save_all=True,
        append_images=pages[1:]
    )

    print(f"\nPDF created: {OUTPUT_PDF}")


# ----- MAIN -----

def main():
    print("Downloading card images...")
    download_all_cards()

    print("\nCreating printable PDF...")
    create_pdf()

    print("\nDone!")


if __name__ == "__main__":
    main()
