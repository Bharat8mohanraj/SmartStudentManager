# ~~~~~~~~~~~~~~~~~~~~~~ Student Record Manager ~~~~~~~~~~~~~~~~~~~~~~
# Keeps track of student grades across multiple academic streams.
# Uses pandas for table handling and numpy for some basic math.
# I’m using matplotlib just for some fun visuals (nothing too fancy).

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from datetime import datetime

# -------------------- Stream Config --------------------
STREAMS = {
    "1": ("Maths + CS", ["Maths", "Physics", "Chemistry", "English", "Computer Science"]),
    "2": ("Maths + Bio", ["Maths", "Physics", "Chemistry", "English", "Biology"]),
    "3": ("Commerce", ["Accountancy", "Economics", "Business Studies", "English", "Mathematics"]),
    "4": ("Humanities", ["History", "Geography", "Political Science", "English", "Sociology"])
}

DATA_FILES = {
    "1": "maths_cs.csv",
    "2": "maths_bio.csv",
    "3": "commerce.csv",
    "4": "humanities.csv"
}

GRADE_MAP = {
    (90, 100): "A+",
    (80, 89): "A",
    (70, 79): "B",
    (60, 69): "C",
    (50, 59): "D",
    (35, 49): "E",
    (0, 34): "F"
}

CHANGELOG = "changelog.txt"

# -------------------- Student Tracker Class --------------------
class StudentTracker:
    def __init__(self, code):
        self.stream_code = code
        self.stream_name, self.subjects = STREAMS[code]
        self.csv_file = DATA_FILES[code]
        self.data = self._load_or_initialize()

    def _log(self, action, roll_no):
        with open(CHANGELOG, "a") as log:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"[{timestamp}] {action} - Roll: {roll_no} in {self.stream_name}\n")

    def _load_or_initialize(self):
        expected_cols = ["Roll No", "Name"] + self.subjects + ["Total", "Average", "Percentage", "Rank", "Grade"]
        if os.path.exists(self.csv_file):
            df = pd.read_csv(self.csv_file)
            # Not all files may have the latest columns — fill them in
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = 0
        else:
            df = pd.DataFrame(columns=expected_cols)
        return df

    def _save(self):
        self.data.to_csv(self.csv_file, index=False)

    def _compute_grades(self, row):
        scores = np.array([row[sub] for sub in self.subjects])
        total = scores.sum()
        avg = scores.mean()
        percent = (total / (len(self.subjects) * 100)) * 100
        for rng, grade in GRADE_MAP.items():
            if rng[0] <= avg <= rng[1]:
                return pd.Series([total, avg, percent, grade])
        return pd.Series([total, avg, percent, "NA"])  # fallback (shouldn’t happen)

    def _refresh_ranks(self):
        if self.data.empty:
            return
        self.data["Rank"] = self.data["Total"].rank(ascending=False, method="min").astype(int)
        self.data.sort_values("Rank", inplace=True)

    def add_new_student(self):
        try:
            print(f"\n📝 Add Student - {self.stream_name}")
            roll_no = int(input("Enter Roll No (number): "))
            if roll_no in self.data["Roll No"].values:
                print(f"⚠️ Roll No {roll_no} already exists!")
                return

            name = input("Name: ").strip()
            if not name:
                print("⚠️ Name cannot be empty.")
                return

            marks = {}
            for subject in self.subjects:
                while True:
                    try:
                        score = int(input(f"{subject}: "))
                        if 0 <= score <= 100:
                            marks[subject] = score
                            break
                        else:
                            print("Enter marks between 0 and 100.")
                    except ValueError:
                        print("Please enter a valid number.")

            grade_data = self._compute_grades(marks)
            new_row = {"Roll No": roll_no, "Name": name, **marks}
            new_row.update(dict(zip(["Total", "Average", "Percentage", "Grade"], grade_data)))

            self.data = pd.concat([self.data, pd.DataFrame([new_row])], ignore_index=True)
            self._refresh_ranks()
            self._save()
            self._log("Added", roll_no)
            print("✅ Student added.")
        except Exception as err:
            print(f"Unexpected error occurred: {err}")

    def show_all(self, by_rank=True):
        if self.data.empty:
            print("📭 No data yet.")
            return
        df = self.data.sort_values("Rank" if by_rank else "Roll No")
        print(f"\n📋 Students in {self.stream_name}")
        print(df.to_string(index=False))

    def show_toppers(self):
        if self.data.empty:
            print("📭 No data available.")
            return
        print(f"\n🎯 Toppers in {self.stream_name}")
        for subject in self.subjects:
            top_score = self.data[subject].max()
            toppers = self.data[self.data[subject] == top_score]
            print(f"\n🏅 {subject} - Top Score: {top_score}")
            print(toppers[["Roll No", "Name", subject, "Grade"]].to_string(index=False))

    def update_student_info(self):
        if self.data.empty:
            print("⚠️ Nothing to update.")
            return

        try:
            roll_no = int(input("Roll No to update: "))
        except ValueError:
            print("Invalid input.")
            return

        if roll_no not in self.data["Roll No"].values:
            print("Roll number not found.")
            return

        fields = ["Name"] + self.subjects
        print("\nWhich field to update?")
        for idx, field in enumerate(fields, start=1):
            print(f"{idx}. {field}")

        try:
            selected = int(input("Choice: "))
            if not (1 <= selected <= len(fields)):
                print("Invalid selection.")
                return
        except ValueError:
            print("Please enter a valid option.")
            return

        field = fields[selected - 1]
        if field == "Name":
            value = input("New name: ").strip()
            if not value:
                print("Name cannot be empty.")
                return
        else:
            try:
                value = int(input(f"New marks for {field}: "))
                if not (0 <= value <= 100):
                    print("Marks must be 0-100.")
                    return
            except ValueError:
                print("Marks must be a number.")
                return

        self.data.loc[self.data["Roll No"] == roll_no, field] = value

        if field in self.subjects:
            student_row = self.data.loc[self.data["Roll No"] == roll_no]
            updated_scores = self._compute_grades(student_row.iloc[0])
            self.data.loc[self.data["Roll No"] == roll_no, ["Total", "Average", "Percentage", "Grade"]] = updated_scores.values

        self._refresh_ranks()
        self._save()
        self._log("Updated Field", roll_no)
        print("✅ Field updated.")

    def delete_student(self):
        if self.data.empty:
            print("⚠️ No records to delete.")
            return

        try:
            roll_no = int(input("Roll No to delete: "))
        except ValueError:
            print("Invalid number.")
            return

        if roll_no not in self.data["Roll No"].values:
            print("Roll not found.")
            return

        confirm = input("Are you sure? (y/n): ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return

        self.data = self.data[self.data["Roll No"] != roll_no]
        self._refresh_ranks()
        self._save()
        self._log("Deleted", roll_no)
        print("✅ Student deleted.")

    def show_charts(self):
        if self.data.empty:
            print("📭 No data to visualize.")
            return

        print("\n📈 Generating charts...")

        avg_scores = self.data[self.subjects].mean()

        plt.figure(figsize=(9, 5))
        avg_scores.plot(kind="bar", color="cornflowerblue")
        plt.title(f"Avg Marks per Subject - {self.stream_name}")
        plt.ylabel("Marks")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        grade_counts = self.data["Grade"].value_counts().sort_index()
        plt.figure(figsize=(6, 6))
        plt.pie(grade_counts, labels=grade_counts.index, autopct='%1.1f%%', startangle=140)
        plt.title("Grade Distribution")
        plt.tight_layout()
        plt.show()

        plt.figure(figsize=(7, 5))
        plt.scatter(self.data["Rank"], self.data["Percentage"], c="green")
        plt.title("Rank vs Percentage")
        plt.xlabel("Rank")
        plt.ylabel("Percentage")
        plt.grid(True)
        plt.tight_layout()
        plt.show()


# -------------------- Program Entry Point --------------------
def main():
    print("\n📚 Welcome to the Student Tracker System!")
    managers = {}

    while True:
        print("\n----- MENU -----")
        print("1. Add Student")
        print("2. Show All Students")
        print("3. View Subject Toppers")
        print("4. Update Student Info")
        print("5. Delete Student")
        print("6. Charts & Visuals")
        print("7. Exit")

        opt = input("Pick an option: ").strip()

        if opt == "7":
            print("👋 Goodbye!")
            break

        if opt not in {"1", "2", "3", "4", "5", "6"}:
            print("❗ Try again with a valid option.")
            continue

        print("\nChoose Stream:")
        for k, (label, _) in STREAMS.items():
            print(f"{k}. {label}")

        stream_opt = input("Stream #: ").strip()
        if stream_opt not in STREAMS:
            print("Invalid stream.")
            continue

        if stream_opt not in managers:
            managers[stream_opt] = StudentTracker(stream_opt)
        manager = managers[stream_opt]

        if opt == "1":
            manager.add_new_student()
        elif opt == "2":
            by = input("Sort by (r)ank or (n)umber? [default: r]: ").strip().lower()
            manager.show_all(by_rank=(by in {"", "r", "rank"}))
        elif opt == "3":
            manager.show_toppers()
        elif opt == "4":
            manager.update_student_info()
        elif opt == "5":
            manager.delete_student()
        elif opt == "6":
            manager.show_charts()

if __name__ == "__main__":
    main()
