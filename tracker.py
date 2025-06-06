# ------------------------- Student Tracker Program -------------------------
# This program helps track student records for different academic streams.
# It calculates grades, ranks, and provides filtering options for analysis.
# Uses Pandas for CSV handling and NumPy for calculations.

import pandas as pd
import numpy as np
import os

# ------------------------- CONFIGURATION -------------------------
STREAM_SUBJECTS = {
    "1": ("Maths + CS", ["Maths", "Physics", "Chemistry", "English", "Computer Science"]),
    "2": ("Maths + Biology", ["Maths", "Physics", "Chemistry", "English", "Biology"]),
    "3": ("Commerce", ["Accountancy", "Economics", "Business Studies", "English", "Mathematics"]),
    "4": ("Humanities", ["History", "Geography", "Political Science", "English", "Sociology"])
}

CSV_FILES = {
    "1": "maths_cs.csv",
    "2": "maths_bio.csv",
    "3": "commerce.csv",
    "4": "humanities.csv"
}

GRADE_SCALE = {
    (90, 100): "A+",
    (80, 89): "A",
    (70, 79): "B",
    (60, 69): "C",
    (50, 59): "D",
    (35, 49): "E",
    (0, 34): "F"
}

# ------------------------- Student Manager Class -------------------------
class StudentManager:
    def __init__(self, stream_code):
        self.stream_code = stream_code
        self.stream_name, self.subjects = STREAM_SUBJECTS[stream_code]
        self.filename = CSV_FILES[stream_code]
        self.data = self.load_data()

    def load_data(self):
        expected_columns = ["Roll No", "Name"] + self.subjects + ["Total", "Average", "Percentage", "Rank", "Grade"]
        if os.path.exists(self.filename):
            df = pd.read_csv(self.filename)
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = 0
        else:
            df = pd.DataFrame(columns=expected_columns)
        return df

    def save_data(self):
        self.data.to_csv(self.filename, index=False)

    def calculate_grades(self, row):
        marks_array = np.array([row[sub] for sub in self.subjects])
        total = np.sum(marks_array)
        average = np.mean(marks_array)
        percentage = (total / (len(self.subjects) * 100)) * 100
        grade = next(v for k, v in GRADE_SCALE.items() if k[0] <= average <= k[1])
        return pd.Series([total, average, percentage, grade])

    def update_ranks(self):
        if not self.data.empty:
            self.data['Rank'] = self.data['Total'].rank(ascending=False, method='min').astype(int)
            self.data.sort_values(by="Rank", inplace=True)

    def add_student(self):
        try:
            print(f"\nAdding student to stream: {self.stream_name}")
            roll = int(input("Enter Roll No (integer): "))
            if roll in self.data['Roll No'].values:
                print(f"❌ Roll No {roll} already exists in {self.stream_name}. Duplicate entries not allowed.")
                return
            name = input("Enter Student Name: ").strip()
            if not name:
                print("❌ Name cannot be empty!")
                return
            marks = {}
            for subject in self.subjects:
                while True:
                    try:
                        score = int(input(f"Enter marks for {subject} (0-100): "))
                        if 0 <= score <= 100:
                            marks[subject] = score
                            break
                        else:
                            print("❌ Invalid marks! Must be between 0-100.")
                    except ValueError:
                        print("❌ Please enter a valid integer!")
            grade_info = self.calculate_grades(marks)
            new_row = {"Roll No": roll, "Name": name, **marks}
            new_row["Total"], new_row["Average"], new_row["Percentage"], new_row["Grade"] = grade_info.values
            self.data = pd.concat([self.data, pd.DataFrame([new_row])], ignore_index=True)
            self.update_ranks()
            self.save_data()
            print("✅ Student added successfully!")
        except Exception as e:
            print(f"❌ Error adding student: {e}")

    def show_all_students(self, sort_by_rank=True):
        if self.data.empty:
            print(f"⚠️ No student data found in {self.stream_name}.")
            return
        df = self.data.sort_values(by="Rank" if sort_by_rank else "Roll No")
        print(f"\nStudents in {self.stream_name}:")
        print(df.to_string(index=False))

    def show_subject_toppers(self):
        if self.data.empty:
            print(f"⚠️ No data to analyze in {self.stream_name}.")
            return
        print(f"\n🏆 Subject-wise toppers in {self.stream_name}:")
        for subject in self.subjects:
            max_mark = self.data[subject].max()
            toppers = self.data[self.data[subject] == max_mark]
            print(f"\nSubject: {subject} | Top Score: {max_mark}")
            print(toppers[["Roll No", "Name", subject, "Grade"]].to_string(index=False))

    # ----------- New methods for patch ------------

    def update_student_field(self):
        if self.data.empty:
            print("⚠️ No student data to update.")
            return
        try:
            roll = int(input("Enter Roll No of student to update: "))
        except ValueError:
            print("❌ Invalid Roll No! Must be an integer.")
            return
        if roll not in self.data['Roll No'].values:
            print(f"❌ No student found with Roll No {roll}.")
            return

        fields = ["Name"] + self.subjects
        print("\nFields you can update:")
        for i, field in enumerate(fields, start=1):
            print(f"{i}. {field}")

        try:
            choice = int(input("Select field number to update: "))
            if choice < 1 or choice > len(fields):
                print("❌ Invalid choice.")
                return
        except ValueError:
            print("❌ Please enter a valid number.")
            return

        field_to_update = fields[choice - 1]

        if field_to_update == "Name":
            new_value = input("Enter new Name: ").strip()
            if not new_value:
                print("❌ Name cannot be empty.")
                return
        else:
            try:
                new_value = int(input(f"Enter new marks for {field_to_update} (0-100): "))
                if not (0 <= new_value <= 100):
                    print("❌ Marks must be between 0 and 100.")
                    return
            except ValueError:
                print("❌ Invalid input! Marks must be an integer.")
                return

        self.data.loc[self.data['Roll No'] == roll, field_to_update] = new_value

        if field_to_update in self.subjects:
            def recalc(row):
                marks = [row[sub] for sub in self.subjects]
                total = sum(marks)
                average = total / len(self.subjects)
                percentage = (total / (len(self.subjects) * 100)) * 100
                grade = next(v for k, v in GRADE_SCALE.items() if k[0] <= average <= k[1])
                return pd.Series([total, average, percentage, grade])

            updated_row = self.data.loc[self.data['Roll No'] == roll].apply(recalc, axis=1)
            self.data.loc[self.data['Roll No'] == roll, ['Total', 'Average', 'Percentage', 'Grade']] = updated_row.values

        self.update_ranks()
        self.save_data()
        print(f"✅ {field_to_update} updated successfully for Roll No {roll}.")

    def delete_student(self):
        if self.data.empty:
            print("⚠️ No student data to delete.")
            return
        try:
            roll = int(input("Enter Roll No of student to delete: "))
        except ValueError:
            print("❌ Invalid Roll No! Must be an integer.")
            return
        if roll not in self.data['Roll No'].values:
            print(f"❌ No student found with Roll No {roll}.")
            return

        confirm = input(f"Are you sure you want to delete student with Roll No {roll}? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Deletion cancelled.")
            return

        self.data = self.data[self.data['Roll No'] != roll]
        self.update_ranks()
        self.save_data()
        print(f"✅ Student with Roll No {roll} deleted successfully.")

    def modify_student(self):
        if self.data.empty:
            print("⚠️ No student data to modify.")
            return
        try:
            roll = int(input("Enter Roll No of student to modify: "))
        except ValueError:
            print("❌ Invalid Roll No! Must be an integer.")
            return
        if roll not in self.data['Roll No'].values:
            print(f"❌ No student found with Roll No {roll}.")
            return

        print(f"Modifying student with Roll No {roll}. Leave blank to keep current value.")

        current_row = self.data.loc[self.data['Roll No'] == roll].iloc[0]

        new_name = input(f"Enter new Name [{current_row['Name']}]: ").strip()
        if not new_name:
            new_name = current_row['Name']

        new_marks = {}
        for subject in self.subjects:
            while True:
                val = input(f"Enter marks for {subject} [{current_row[subject]}]: ").strip()
                if val == '':
                    new_marks[subject] = current_row[subject]
                    break
                try:
                    score = int(val)
                    if 0 <= score <= 100:
                        new_marks[subject] = score
                        break
                    else:
                        print("❌ Marks must be between 0 and 100.")
                except ValueError:
                    print("❌ Please enter a valid integer or leave blank.")

        self.data.loc[self.data['Roll No'] == roll, 'Name'] = new_name
        for subject, mark in new_marks.items():
            self.data.loc[self.data['Roll No'] == roll, subject] = mark

        def recalc(row):
            marks = [row[sub] for sub in self.subjects]
            total = sum(marks)
            average = total / len(self.subjects)
            percentage = (total / (len(self.subjects) * 100)) * 100
            grade = next(v for k, v in GRADE_SCALE.items() if k[0] <= average <= k[1])
            return pd.Series([total, average, percentage, grade])

        updated_row = self.data.loc[self.data['Roll No'] == roll].apply(recalc, axis=1)
        self.data.loc[self.data['Roll No'] == roll, ['Total', 'Average', 'Percentage', 'Grade']] = updated_row.values

        self.update_ranks()
        self.save_data()
        print(f"✅ Student with Roll No {roll} modified successfully.")

# ------------------------- Main Menu -------------------------
def main():
    print("\n✅ Welcome to Student Tracker!")
    managers = {}

    while True:
        print("\n--- MAIN MENU ---")
        print("1. Add Student")
        print("2. Show All Students")
        print("3. Show Subject-wise Toppers")
        print("4. Update Student Field")
        print("5. Modify Student Details")
        print("6. Delete Student")
        print("7. Exit")

        choice = input("Enter choice: ").strip()

        if choice == '7':
            print("👋 Goodbye! Thanks for using Student Tracker.")
            break

        if choice not in {'1', '2', '3', '4', '5', '6'}:
            print("❌ Invalid choice. Please enter a number between 1 and 7.")
            continue

        print("\nSelect Academic Stream:")
        for code, (stream_name, _) in STREAM_SUBJECTS.items():
            print(f"{code}. {stream_name}")
        stream_choice = input("Enter stream number (1-4): ").strip()

        if stream_choice not in STREAM_SUBJECTS:
            print("❌ Invalid stream choice. Please try again.")
            continue

        if stream_choice not in managers:
            managers[stream_choice] = StudentManager(stream_code=stream_choice)
        manager = managers[stream_choice]

        if choice == '1':
            manager.add_student()
        elif choice == '2':
            sort_pref = input("Sort by (R)ank or (Ro)ll No? [Default: Rank]: ").strip().lower()
            sort_by_rank = True if sort_pref in ['', 'r', 'rank'] else False
            manager.show_all_students(sort_by_rank=sort_by_rank)
        elif choice == '3':
            manager.show_subject_toppers()
        elif choice == '4':
            manager.update_student_field()
        elif choice == '5':
            manager.modify_student()
        elif choice == '6':
            manager.delete_student()

if __name__ == "__main__":
    main()
