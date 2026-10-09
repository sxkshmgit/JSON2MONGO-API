# JSON2Mongo

A FastAPI service that fetches data from [JSONPlaceholder](https://jsonplaceholder.typicode.com/) and imports users, posts, and comments into MongoDB Atlas while preserving relationships between the documents.

## Overview

The project imports data in this order:

```text
Users → Posts → Comments
```

The import order matters because relationships are resolved through MongoDB's generated `_id` values.

- JSONPlaceholder user `id` is stored as `users.source_id`.
- A post's JSONPlaceholder `userId` is stored as `posts.source_user_id`, while `posts.user_id` stores the corresponding MongoDB `users._id`.
- JSONPlaceholder post `id` is stored as `posts.source_id`.
- A comment's JSONPlaceholder `postId` is stored as `comments.source_post_id`, while `comments.post_id` stores the corresponding MongoDB `posts._id`.
- JSONPlaceholder source IDs never replace MongoDB's `_id`.

Unique indexes on `source_id` prevent the same source record from being imported more than once.

## Tech Stack

- Python
- FastAPI
- HTTPX
- PyMongo
- MongoDB Atlas
- JSONPlaceholder
- Uvicorn
- python-dotenv

## Project Structure

```text
JSON2MONGO-API/
├── main.py
├── database.py
├── mongo_collections.py
├── jsonplaceholder_client.py
├── users_import.py
├── posts_import.py
├── comments_import.py
├── requirements.txt
├── .gitignore
└── .env
```

### File Responsibilities

| File | Responsibility |
|---|---|
| `main.py` | Creates the FastAPI application and registers import routers. |
| `database.py` | Loads the MongoDB connection string and creates the MongoDB client/database connection. |
| `mongo_collections.py` | Defines collection handles and unique `source_id` indexes. |
| `jsonplaceholder_client.py` | Fetches users, posts, and comments from JSONPlaceholder. |
| `users_import.py` | Imports users into MongoDB and prevents duplicate source records. |
| `posts_import.py` | Imports posts and resolves each post to a MongoDB user `_id`. |
| `comments_import.py` | Imports comments and resolves each comment to a MongoDB post `_id`. |

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/sxkshmgit/JSON2MONGO-API.git
cd JSON2MONGO-API
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MongoDB Atlas

Create a `.env` file in the project root:

```env
MONGODB_URI=your_mongodb_atlas_connection_string
```

The application uses the `json2mongo` database.

Do not commit `.env` or your MongoDB credentials to Git.

### 5. Start the API

```bash
python -m uvicorn main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

All import endpoints use the `/import` prefix.

### Import users

```http
POST /import/users
```

Fetches users from JSONPlaceholder and inserts them into the MongoDB `users` collection.

Example response:

```json
{
  "fetched": 10,
  "inserted": 10,
  "skipped": 0,
  "failed": 0
}
```

### Import posts

```http
POST /import/posts
```

Posts require users to already exist in MongoDB.

For each post, the application:

1. Reads the JSONPlaceholder `userId`.
2. Finds the user using `users.source_id`.
3. Stores that user's MongoDB `_id` in `posts.user_id`.
4. Keeps the original source relationship in `posts.source_user_id`.

Example response:

```json
{
  "fetched": 100,
  "inserted": 100,
  "skipped": 0,
  "failed": 0
}
```

### Import comments

```http
POST /import/comments
```

Comments require posts to already exist in MongoDB.

For each comment, the application:

1. Reads the JSONPlaceholder `postId`.
2. Finds the post using `posts.source_id`.
3. Stores that post's MongoDB `_id` in `comments.post_id`.
4. Keeps the original source relationship in `comments.source_post_id`.

Example response:

```json
{
  "fetched": 500,
  "inserted": 500,
  "skipped": 0,
  "failed": 0
}
```

## Import Behavior

Each import response contains:

| Field | Meaning |
|---|---|
| `fetched` | Number of records received from JSONPlaceholder. |
| `inserted` | Number of new records successfully inserted into MongoDB. |
| `skipped` | Number of records already present and therefore not inserted again. |
| `failed` | Number of records that could not be imported because required data was missing or the write failed. |

Running the same import endpoint again does not create duplicate source records.

For example, a second users import returns:

```json
{
  "fetched": 10,
  "inserted": 0,
  "skipped": 10,
  "failed": 0
}
```

## Import Order Protection

The API enforces the required relationship order:

- Posts cannot be imported before users exist.
- Comments cannot be imported before posts exist.

When a required parent collection is empty, the corresponding endpoint returns HTTP `409 Conflict`.

## Relationship Example

A post can be represented as:

```text
posts
├── source_id: 1
├── source_user_id: 1
└── user_id: ObjectId("...")

          │
          ▼

users
├── source_id: 1
└── _id: ObjectId("...")
```

The important relationship is:

```text
posts.user_id == users._id
```

For comments:

```text
comments
├── source_id: 1
├── source_post_id: 1
└── post_id: ObjectId("...")

             │
             ▼

posts
├── source_id: 1
└── _id: ObjectId("...")
```

The important relationship is:

```text
comments.post_id == posts._id
```

This keeps MongoDB's native identifiers as the primary document identifiers while retaining the original JSONPlaceholder IDs for source lookup and duplicate prevention.

## Error Handling

The API handles:

- JSONPlaceholder HTTP errors.
- Network/request failures when calling JSONPlaceholder.
- Missing parent records required for relationships.
- Duplicate source records.
- MongoDB write errors.
- MongoDB connection/database errors.

External API failures are reported as HTTP `502 Bad Gateway`, missing import prerequisites use HTTP `409 Conflict`, and MongoDB failures use HTTP `500 Internal Server Error`.

## Typical Usage

Run the endpoints in this sequence:

```text
POST /import/users
        ↓
POST /import/posts
        ↓
POST /import/comments
```

After importing, the MongoDB collections are:

```text
json2mongo
├── users
├── posts
└── comments
```

