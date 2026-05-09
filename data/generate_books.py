"""Generate a synthetic books catalog dataset (~600 records) for Solr indexing."""
import csv
import random
from pathlib import Path

random.seed(42)

GENRES = ["Fiction", "Mystery", "Science Fiction", "Fantasy", "Romance",
          "Thriller", "Biography", "History", "Self-Help", "Technology",
          "Philosophy", "Poetry", "Horror", "Drama", "Adventure"]

PUBLISHERS = ["Penguin Random House", "HarperCollins", "Simon & Schuster",
              "Hachette", "Macmillan", "Oxford University Press",
              "MIT Press", "O'Reilly Media", "Manning", "Pearson",
              "Wiley", "Springer", "Bloomsbury", "Vintage", "Anchor Books"]

FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer",
               "Michael", "Linda", "William", "Elizabeth", "David", "Barbara",
               "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah",
               "Charles", "Karen", "Aisha", "Hiroshi", "Priya", "Mateo",
               "Olumide", "Anya", "Kenji", "Fatima", "Diego", "Mei"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
              "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez",
              "Lopez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore",
              "Jackson", "Martin", "Lee", "Patel", "Khan", "Nguyen", "Kim",
              "Singh", "Cohen", "Tanaka", "Okafor", "Rossi", "Schmidt"]

TITLE_PARTS_A = ["The Silent", "Whispers of", "Beyond the", "Shadows of",
                 "The Last", "Echoes from", "Dreams of", "The Hidden",
                 "Voices in", "Tales of", "The Lost", "Chronicles of",
                 "The Forgotten", "Songs of", "The Ancient"]

TITLE_PARTS_B = ["Mountain", "Empire", "Garden", "Storm", "Kingdom",
                 "Forest", "River", "Star", "Ocean", "City", "Desert",
                 "Code", "Algorithm", "Mind", "Universe", "Heart",
                 "Truth", "Journey", "Legacy", "Revolution", "Network",
                 "Machine", "Quantum", "Horizon", "Frontier"]

DESCRIPTION_TEMPLATES = [
    "A gripping {genre_lower} novel that explores themes of {theme1} and {theme2} through the eyes of a young protagonist navigating a changing world.",
    "An award-winning exploration of {theme1}, blending {theme2} with sharp, contemporary prose that has captivated readers worldwide.",
    "This authoritative volume on {theme1} offers practical insights and rigorous analysis for students and practitioners alike.",
    "A sweeping tale set against the backdrop of {theme1}, where unforgettable characters confront questions of {theme2} and identity.",
    "Combining {theme1} with {theme2}, this book delivers a compelling narrative that challenges convention.",
    "A landmark study of {theme1} drawing on decades of research and firsthand experience in {theme2}.",
]

THEMES = ["love", "war", "technology", "identity", "freedom", "betrayal",
          "ambition", "family", "justice", "discovery", "memory", "loss",
          "innovation", "power", "resilience", "machine learning",
          "artificial intelligence", "data", "history", "culture", "myth",
          "society", "nature", "consciousness"]


def make_title():
    return f"{random.choice(TITLE_PARTS_A)} {random.choice(TITLE_PARTS_B)}"


def make_author():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def make_description(genre):
    tpl = random.choice(DESCRIPTION_TEMPLATES)
    return tpl.format(
        genre_lower=genre.lower(),
        theme1=random.choice(THEMES),
        theme2=random.choice(THEMES),
    )


def main():
    out = Path(__file__).parent / "books.csv"
    fields = ["id", "title", "author", "genre", "publisher", "year",
              "pages", "price", "rating", "in_stock", "description"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i in range(1, 601):
            genre = random.choice(GENRES)
            w.writerow({
                "id": f"BK{i:04d}",
                "title": make_title(),
                "author": make_author(),
                "genre": genre,
                "publisher": random.choice(PUBLISHERS),
                "year": random.randint(1955, 2025),
                "pages": random.randint(120, 850),
                "price": round(random.uniform(5.99, 59.99), 2),
                "rating": round(random.uniform(2.5, 5.0), 1),
                "in_stock": random.choice(["true", "false"]),
                "description": make_description(genre),
            })
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
