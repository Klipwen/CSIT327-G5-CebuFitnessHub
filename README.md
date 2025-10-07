# 🏋️‍♂️ Cebu Fitness Hub

A web-based **Gym Session & Membership Management System** designed to streamline attendance tracking, member management, and real-time gym occupancy monitoring for **Cebu Fitness Hub**.

---

## 📘 Project Overview

This project introduces a web-based system that allows staff to check members in and out by scanning their gym IDs, enabling **real-time visibility** of gym occupancy.
Members can also request account freezing and access attendance reports.

The platform leverages **Django** and **Supabase** to provide a secure, efficient, and scalable solution to replace manual, paper-based operations.

---

## 🎯 Project Purpose / Business Justification

To digitize Cebu Fitness Hub’s membership and attendance operations, improving accuracy, efficiency, and customer satisfaction through an integrated online management system.

---

## 🎯 Objectives

### **Primary Objective**

To develop a Gym Session & Membership Management System that streamlines attendance tracking and membership services at Cebu Fitness Hub.

### **Specific Objectives (SMART Framework)**

**Specific:**

1. Implement a web-based system for manual check-in/out and membership account freezing requests.

**Measurable:**

1. Achieve **95% accuracy** in real-time gym occupancy tracking and report generation.

**Achievable:**

1. Utilize existing web technologies and the project team’s expertise to deliver the system by **November 2025**.

**Relevant:**

1. Address the gym’s current inefficiencies in attendance monitoring and member convenience, enhancing operational effectiveness.

**Time-Bounded:**

1. Complete system development, testing, and deployment within the current semester — by **November 2025**.

---

## 🧠 Tech Stack

| Component         | Technology Used         |
| ----------------- | ----------------------- |
| Backend Framework | Django                  |
| Database          | Supabase                |
| Frontend          | HTML / CSS / JavaScript |
| Version Control   | Git & GitHub            |
| IDE               | Visual Studio Code      |

---

## ⚙️ Setup & Run Instructions (Windows)

### **1. Install Python**

* Download: [Python 3.13+](https://www.python.org/downloads/)
* During setup, ensure:

  * ✅ Add Python to PATH
  * ✅ Install launcher for all users
* Verify installation:

  ```bash
  python --version
  ```

---

### **2. Install Git**

* Download: [Git for Windows](https://git-scm.com/download/win)
* Verify installation:

  ```bash
  git --version
  ```

---

### **3. Clone the Repository**

```bash
git clone https://github.com/Klipwen/CSIT327-G5-CebuFitnessHub.git
cd CSIT327-G5-CebuFitnessHub
```

---

### **4. Open in VS Code**

```bash
code .
```

---

### **5. Set Up Virtual Environment (venv)**

```bash
python -m venv venv
```

**Activate:**

* **Command Prompt**

  ```bash
  venv\Scripts\activate.bat
  ```
* **PowerShell**

  ```bash
  .\venv\Scripts\Activate.ps1
  ```

---

### **6. Install Dependencies**

```bash
pip install django
```

---

### **7. Run the Django App**

```bash
python manage.py runserver
```

Visit:
👉 [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

### **8. (Optional) Connect Supabase Database**

Create a `.env` file in your project root directory and add:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@aws-0-<project-ref>.pooler.supabase.com:5432/postgres?sslmode=require
```

Apply migrations:

```bash
python manage.py migrate
```

Run the server to test connection:

```bash
python manage.py runserver
```

---

## 🧑‍💻 Team Members

### **Developers**

| Name               | Role      | CIT-U Email                                                   |
| ------------------ | --------- | ------------------------------------------------------------- |
| Elvin O. Lagamo Jr.| Lead Developer | [elvin.lagamo@cit.edu](mailto:elvin.lagamo@cit.edu)           |
| Gee Caliph A. Juen | Developer | [geecaliph.juen@cit.edu](mailto:geecaliph.juen@cit.edu)       |
| Zyrrah Kaye Lacida | Developer | [zyrrahkaye.lacida@cit.edu](mailto:zyrrahkaye.lacida@cit.edu) |

### **Project Management Team**

| Name                    | Role             | CIT-U Email                                                       |
| ----------------------- | ---------------- | ----------------------------------------------------------------- |
| Jhey Mars P. Malingin   | Product Owner    | [jheymars.malingin@cit.edu](mailto:jheymars.malingin@cit.edu)     |
| Kobe Vincent L. Marikit | Product Owner    | [kobevincent.marikit@cit.edu](mailto:kobevincent.marikit@cit.edu) |
| Simon Jay D. Lugatiman  | Scrum Master     | [simonjay.lugatiman@cit.edu](mailto:simonjay.lugatiman@cit.edu)   |
| John Kheinzy A. Mandawe | Business Analyst | [johnkheinzy.mandawe@cit.edu](mailto:johnkheinzy.mandawe@cit.edu) |

---

## 🌐 Deployed Link

*(Coming soon...)*
