# FastAPI Project: The AI Interviewer Café

Welcome! Here’s a beginner-friendly, story-style walkthrough of your FastAPI project, using real-life analogies to make each part clear.

---

## Imagine: The AI Interviewer Café

Picture a busy café where job interviews happen. There’s a front desk, a manager, interview rooms, and a record-keeping system. Your FastAPI project is like the software running this café, making sure everything runs smoothly.

---

## 1. The Front Door: `main.py`

Think of `main.py` as the main entrance to the café. When someone walks in (a request comes in), this is where they’re greeted and directed.

- **FastAPI App:** The café itself, ready to serve.
- **Routers:** Like different counters for different services (sign-up, interviews, file uploads, performance tracking).
- **CORS:** The security guard, deciding who can enter from outside.
- **Database Tables:** The café’s filing cabinets, set up when the café opens.

**How it works:**  
When the café opens (`main.py` runs), it sets up all the counters (routers) and makes sure the filing cabinets (database tables) are ready.

---

## 2. The Staff: Routers (`auth.py`, `interview.py`, `jd_resume.py`, `performance.py`)

Each router is like a specialized staff member at a counter, handling specific tasks.

### a. `auth.py` – The Receptionist

Handles new visitors (sign-up) and returning guests (login).

- **Sign Up:** Checks if a username is unique, then adds the user to the system.
- **Login:** Verifies credentials and lets the user in.

### b. `interview.py` – The Interview Manager

Manages the interview process.

- **Start Interview:** Assigns a new interview session to a user.
- **Answer Questions:** Lets users answer questions, upload recordings, and update their answers.
- **Status Updates:** Tracks the progress of each question.

### c. `jd_resume.py` – The Document Clerk

Handles uploading and managing Job Descriptions (JD) and Resumes.

- **Upload:** Stores files in the right place.
- **Preview/Delete:** Lets users see or remove their documents.

### d. `performance.py` – The Performance Analyst

Keeps track of how users performed in interviews.

- **Summary:** Gives an overview of all interviews.
- **Details:** Shows detailed results for a specific interview.

---

## 3. The Filing Cabinets: Database Models (`models.py`)

These are the blueprints for how information is stored.

- **User:** Like a folder for each café guest, with their name, password, type, and documents.
- **Interview:** A folder for each interview session, linked to a user.
- **QuestionAnswer:** A record for each question in an interview, with answers, recordings, AI feedback, and scores.

---

## 4. The Forms: Schemas (`schemas.py`)

Schemas are like the forms guests fill out at the counter.

- **UserCreate, UserLogin:** Forms for signing up and logging in.
- **InterviewCreate:** Form to start a new interview.
- **QuestionAnswerCreate/Update:** Forms for answering or updating a question.
- **QuestionAnswerOut, InterviewSummary, InterviewDetails:** Forms for sending info back to the guest.

---

## 5. The Database Connection: `database.py`

This is the café’s connection to its filing cabinets. It sets up and manages the link to the database, so staff can read/write records.

---

## 6. The Rulebook: `config.py`

Holds the café’s rules (settings), like where the database is located. Uses environment variables for flexibility.

---

## 7. The Logbook: `logger.py`

Keeps a log of important events, errors, and actions for troubleshooting.

---

## How a Visit Flows

1. **A guest arrives** (`main.py` receives a request).
2. **Receptionist greets them** (`auth.py` handles sign-up/login).
3. **They start an interview** (`interview.py` assigns questions).
4. **They answer questions, upload recordings** (handled by `interview.py`).
5. **They upload their resume/JD** (`jd_resume.py`).
6. **After the interview, they check their performance** (`performance.py`).
7. **All actions are logged and stored** (via `models.py`, `schemas.py`, `database.py`, `logger.py`).

---

## Key Analogies

| Concept        | Analogy                     |
|----------------|----------------------------|
| FastAPI App    | The café building           |
| Routers        | Specialized staff/counters  |
| Models         | Filing cabinet folders      |
| Schemas        | Forms for input/output      |
| Database       | The actual filing cabinets  |
| Config         | The café’s rulebook         |
| Logger         | The logbook for all events  |

---

## Summary Table

| File            | Real-life Role         | Purpose                                      |
|-----------------|-----------------------|----------------------------------------------|
| main.py         | Front Door            | Entry point, sets up everything              |
| auth.py         | Receptionist          | Handles sign-up and login                    |
| interview.py    | Interview Manager     | Manages interviews and answers               |
| jd_resume.py    | Document Clerk        | Handles JD/Resume uploads                    |
| performance.py  | Performance Analyst   | Tracks and reports interview results         |
| models.py       | Filing Cabinet Folders| Defines how data is stored                   |
| schemas.py      | Forms                 | Validates and structures data in/out         |
| database.py     | Filing Cabinet Access | Connects to the database                     |
| config.py       | Rulebook              | Stores configuration                         |
| logger.py       | Logbook               | Logs events and errors                       |

---

## Final Words

With this story, you can see how each part of your FastAPI project works together, just like a well-run café. Each file and class has a clear role, and together they create a smooth experience for users and developers alike.

If you want to dive deeper into any part, just ask!