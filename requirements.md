
# 🧠 Project: AI Interviewer

## 🧰 Tech Stack

- **Database**: PostgreSQL
- **Backend**: Python, FastAPI, Uvicorn
- **Frontend**: Node.js with NPM

---

## ✅ Strict Development Guidelines

- Keep code **clean and readable**
- **Do not complicate** logic unnecessarily
- Use **functions** wherever needed
- Implement **configurable logging** with log levels
- Use **Python Models** (e.g., SQLAlchemy) for DB objects
- Use **Pydantic** for request/response validation
- Focus on **appealing yet simple UI**
- Keep the code **easily reconfigurable** through central config files
  - Include values like `DB_CONNECTION_STRING`, `OPENAI_ENDPOINT`, `MODEL_NAME`, etc.
- Max 2 files for **backend** and **frontend** configuration respectively

---

## 🎯 Product Requirements

### 🔐 Authentication

1. Add **Signup/Login** functionality
2. Ask for:
   - Username
   - Password
   - User Type (`ADMIN` or `CANDIDATE`)

---

### 🧑‍💼 Candidate Dashboard (Post Login)

#### 📚 Left Navigation Tabs (Top to Bottom with Icons):

---

#### A. Interview

- **Start New Interview**:
  - User may take **multiple attempts**
  - Allow naming the interview via a **friendly textbox**
  - Generate a unique **Interview ID** and save metadata in DB
  - Enable **"Create Interview"** only after **JD** and **Resume** are uploaded

- **Interview Page Flow**:
  1. Dedicated interview page after clicking "Start Interview"
  2. **Backend**:
     - Trigger FastAPI endpoint to insert **3 new questions** into `QuestionAnswers` table
     - Schema:
       ```
       USER_ID,
       INTERVIEW_ID,
       QUESTION_ID,
       QUESTION_TEXT,
       STATUS ("NEW", "ATTEMPTED"),
       ANSWER_TEXT,
       CAMERA_RECORDING_PATH,
       SCREEN_RECORDING_PATH,
       AUDIO_RECORDING_PATH,
       COMBINED_RECORDING_PATH,
       AI_ANSWER,
       AI_REMARK,
       CANDIDATE_SCORE,
       CANDIDATE_GRADE
       ```
     - Initially keep fields `null` where applicable
     - Allow fetching **more questions** using the same endpoint

  3. **Frontend**:
     - Icon-based representation of **AI Voice**
     - Bottom nav bar to show question list with highlight on current question
     - Show **"more pending questions"** indicator
     - On interview start:
       - Request permission to start **audio**, **camera**, and **screen** recordings
       - If not granted, show error and halt
       - Convert question text to **temporary audio file** and allow play/pause/seek
       - User listens, then **answers verbally while on camera**
       - Upload these recordings:
         - Store in folder: `uploads/{candidate_user_id}/{interview_id}/`
         - File naming pattern: `USERID-INTERVIEWID-QUESTIONID`
       - Update DB with paths and set `STATUS = "ATTEMPTED"`
       - Use "Next" button to fetch and display more questions via FastAPI until exhausted
     - When no more questions remain:
       - Show **Congratulations** message
       - Inform user their **report is being prepared**
       - Show button to go back to **Performance tab**
       - Stop all media streams

---

---
issue fixed. You did an absolutely good work. However their are few enhancements.

After starting intrview, 
- it should ask for permissions once. Recording should not stop for each question. 
- No need to take permission for each answer, interview recording should continue until end of interview.
- When Click on next question, should mean the answer to that current question needs to be processed. this includes uploading the recoding with appropriate name. updating in the DB and moving to the next question.
- Play the question automatically , we dont have to wait for user to click to play it.
---

#### B. Job Descriptions & Resumes

- Allow upload of **max 1 JD** and **1 Resume**
- Allow user to:
  - **Preview**
  - **Delete** previously uploaded files

---

#### C. Performance

- List all **completed interviews** by the current user:
  - Show: Name, Timestamp, Grade (from DB via FastAPI)
- View More:
  - Show list of all questions, answers, and AI feedback
  - Play back **combined recording** for each question

---

#### D. Support

- Show **Support Email**

---

#### E. Logout

- End session and return to login page

---

## 🐳 Docker Setup

This project must be fully containerized using Docker.

### 🔧 Structure

- `Dockerfile.backend` → for FastAPI backend
- `Dockerfile.frontend` → for Node/React frontend
- `docker-compose.yml` → to run backend, frontend, and PostgreSQL services together
- `.env` file → for storing shared configs (like DB credentials, OpenAI keys)

## To start the backend app manualy 
### (venv) PS C:\Learning Lab\GenAI\interviewer\backend> uvicorn app.main:app --host 0.0.0.0 --port 8000

## .\venv\Scripts\activate
## cd ../..
## uvicorn worker.app.main:app --host 0.0.0.0 --port 8001 --reload

### 🎯 Goals

- Independent containers for frontend and backend
- Configurable ports:
  - `8000` for backend
  - `3000` for frontend
- PostgreSQL with persistent volume
- Run everything using one command:
  ```bash
  docker-compose up --build


