import tkinter as tk
from tkinter import ttk
import threading
import requests
from PIL import Image, ImageTk
import io
import random

from ELO_Voting import (
    load_list,
    load_data,
    save_data,
    select_pair,
    update_elo
)

IMG_SIZE = (320, 320)


# ---------------- HTTP Session ---------------- #
session = requests.Session()

# ---------------- Sprite Loader (FAST) ---------------- #
def load_sprite(name, size=IMG_SIZE):
    url = (
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
        f"sprites/pokemon/other/official-artwork/{name}.png"
    )

    img_data = session.get(url, timeout=5).content
    img = Image.open(io.BytesIO(img_data))
    img = img.resize(size, Image.LANCZOS)

    return ImageTk.PhotoImage(img)

# ---------------- GUI App ---------------- #
class EloApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pokémon ELO Voting")

        self.items = load_data(load_list())
        self.PLACEHOLDER_IMG = ImageTk.PhotoImage(Image.new("RGBA", IMG_SIZE, (0,0,0,0)))

        self.a = None
        self.b = None
        self.a_image = self.PLACEHOLDER_IMG
        self.b_image = self.PLACEHOLDER_IMG

        self.build_ui()
        self.refresh_ranking()
        self.next_pair()

    # ---------------- UI ---------------- #
    def build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        # ===== Voting Panel =====
        vote_frame = ttk.Frame(main)
        vote_frame.pack(side="left", fill="y", padx=10)

        ttk.Label(vote_frame, text="Vote", font=("Arial", 16)).pack(pady=5)

        self.a_button = ttk.Button(
            vote_frame,
            command=lambda: self.vote("a"),
            image=self.a_image,
            compound="top",
            width=20
        )
        self.a_button.pack(pady=10)

        ttk.Label(vote_frame, text="vs", font=("Arial", 12)).pack()

        self.b_button = ttk.Button(
            vote_frame,
            command=lambda: self.vote("b"),
            image=self.b_image,
            compound="top",
            width=20
        )
        self.b_button.pack(pady=10)

        ttk.Button(
            vote_frame,
            text="Skip",
            command=self.next_pair
        ).pack(pady=15)

        # ===== Ranking Panel (Table) =====
        rank_frame = ttk.Frame(main)
        rank_frame.pack(side="right", fill="both", expand=True)

        ttk.Label(rank_frame, text="Ranking", font=("Arial", 16)).pack()

        columns = ("rank", "name", "rating")
        self.rank_table = ttk.Treeview(
            rank_frame,
            columns=columns,
            show="headings"
        )

        self.rank_table.heading("rank", text="#")
        self.rank_table.heading("name", text="Name")
        self.rank_table.heading("rating", text="Rating")

        self.rank_table.column("rank", width=50, anchor="e")
        self.rank_table.column("name", width=120, anchor="center")
        self.rank_table.column("rating", width=60, anchor="e")

        self.rank_table.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            rank_frame,
            orient="vertical",
            command=self.rank_table.yview
        )
        scrollbar.pack(side="right", fill="y")

        self.rank_table.config(yscrollcommand=scrollbar.set)

    # ---------------- Voting ---------------- #
    def vote(self, which):
        if which == "a":
            update_elo(self.items, self.a, self.b, self.a)
        else:
            update_elo(self.items, self.a, self.b, self.b)

        save_data(self.items)
        self.refresh_ranking()
        r = random.random()
        if r < 0.33: self.next_pair(self.a) 
        elif r < 0.66: self.next_pair(self.b)
        else:
            ar = self.items[self.a]["rounds"]
            br = self.items[self.b]["rounds"]
            if ar < br: self.next_pair(self.a)
            else: self.next_pair(self.b)

    # ---------------- Pair Handling ---------------- #
    def next_pair(self, init=None):
        a, b = select_pair(self.items, init)
        ar = self.items[a]["rating"]
        br = self.items[b]["rating"]
        if br > ar:
            self.a, self.b = b, a
            ar, br = br, ar
        else:
            self.a, self.b = a, b

        # Show names immediately and use placeholder for images
        text = f"{self.a} ({ar:.1f})"
        self.a_button.config(text=text, image=self.PLACEHOLDER_IMG)
        text = f"{self.b} ({br:.1f})"
        self.b_button.config(text=text, image=self.PLACEHOLDER_IMG)

        # Load sprites in parallel
        threading.Thread(
            target=self.load_sprites_async,
            args=(self.a, self.b),
            daemon=True
        ).start()

    def load_sprites_async(self, a, b):
        results = {}

        def worker(name):
            try:
                index = list(self.items.keys()).index(name)+1
                results[name] = load_sprite(index)
            except Exception:
                results[name] = None

        t1 = threading.Thread(target=worker, args=(a,))
        t2 = threading.Thread(target=worker, args=(b,))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.root.after(
            0,
            lambda: self.update_images(a, b, results.get(a), results.get(b))
        )

    def update_images(self, a, b, a_img, b_img):
        # Prevent race condition if user already voted
        if a != self.a or b != self.b:
            return

        if a_img:
            self.a_image = a_img
            self.a_button.config(image=self.a_image)
        if b_img:
            self.b_image = b_img
            self.b_button.config(image=self.b_image)

    # ---------------- Ranking ---------------- #
    def refresh_ranking(self):
        for row in self.rank_table.get_children():
            self.rank_table.delete(row)

        ranked = sorted(
            self.items.items(),
            key=lambda x: x[1]["rating"],
            reverse=True
        )

        for i, (name, data) in enumerate(ranked, start=1):
            self.rank_table.insert(
                "",
                "end",
                values=(
                    i,
                    name.title(),
                    f"{data['rating']:.1f}"
                )
            )

# ---------------- Main ---------------- #
if __name__ == "__main__":
    root = tk.Tk()
    app = EloApp(root)
    root.mainloop()
