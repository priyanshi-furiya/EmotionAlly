from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import re
import pyodbc
import sqlite3
import openai
import time
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Set up SQLite database
conn = sqlite3.connect("chatbot.db", check_same_thread=False)
c = conn.cursor()

# Create messages table if it doesn't exist
c.execute(
    """CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, role TEXT, content TEXT, user TEXT)"""
)
conn.commit()


# Function to insert new messages into the database
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email)


def insert_message(role, content, user):
    if role not in ["user", "assistant"]:
        print(f"Invalid role: {role}")
        return
    c.execute(
        "INSERT INTO messages (role, content, user) VALUES (?, ?, ?)",
        (role, content, user),
    )
    conn.commit()


# Function to retrieve top messages from the database
def retrieve_top_messages(user, limit=5):
    c.execute(
        "SELECT role, content FROM messages WHERE user = ? ORDER BY id DESC LIMIT ?",
        (user, limit),
    )
    rows = c.fetchall()
    messages = [{"role": row[0], "content": row[1]} for row in rows]
    messages.reverse()  # Reverse to get correct order for conversation
    return messages


def get_db_connection():
    server = " "
    database = "test"
    username = "priyanshi"
    password = " "
    driver = "{ODBC Driver 18 for SQL Server}"

    connection = pyodbc.connect(
        "DRIVER="
        + driver
        + ";SERVER=tcp:"
        + server
        + ";PORT=1433;DATABASE="
        + database
        + ";UID="
        + username
        + ";PWD="
        + password
        + ";Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return connection


# Set up OpenAI credentials
endpoint = " "
api_key = " "
deployment_name = "emotionally"

openai.api_type = "azure"
openai.api_base = endpoint
openai.api_version = "2024-02-01"
openai.api_key = api_key


# Function to generate embeddings
def generate_embeddings(text):
    response = openai.Embedding.create(input=[text], engine="emotion-embedding")
    return response["data"][0]["embedding"]


# Function to add embeddings to DataFrame
def add_embeddings_to_df(df, text_column):
    df["embedding"] = df[text_column].apply(generate_embeddings)
    return df


# Load or generate embeddings for the CSV
def load_or_generate_embeddings(csv_file, embeddings_file):
    if os.path.exists(embeddings_file):
        df = pd.read_csv(embeddings_file)
        df["embedding"] = (
            df["embedding"].apply(eval).apply(lambda x: list(map(float, x)))
        )
    else:
        df = pd.read_csv(csv_file)
        df = add_embeddings_to_df(df, "text_scraped")
        df.to_csv(embeddings_file, index=False)
    return df


# Load or generate embeddings for both CSVs
df1 = load_or_generate_embeddings(
    "nhs_data_validated copy.csv", "nhs_data_with_embeddings.csv"
)
df2 = load_or_generate_embeddings(
    "mind_data_validated copy.csv", "mind_data_with_embeddings.csv"
)
df3 = load_or_generate_embeddings(
    "Mental_Health_FAQs.csv", "mental_health_faqs_with_embeddings.csv"
)


# Mental health keywords
mental_health_keywords = [
    "anxiety",
    "depression",
    "stress",
    "therapy",
    "counseling",
    "mental health",
    "psychologist",
    "psychiatrist",
    "panic",
    "disorder",
    "emotional",
    "wellbeing",
    "mental illness",
    "mental disorder",
    "ptsd",
    "trauma",
]


# Function to check if a query is mental health related
def is_mental_health_query(query):
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in mental_health_keywords)


@app.route("/get", methods=["GET"])
def get_response():
    user_input = request.args.get("msg")
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    user = session.get("user", "guest")
    insert_message("user", user_input, user)

    if is_mental_health_query(user_input):
        try:
            # Generate an embedding for the user input
            query_embedding = generate_embeddings(user_input)

            # Compute cosine similarity between the query embedding and each embedding in both CSVs
            df1["similarity"] = df1["embedding"].apply(
                lambda x: cosine_similarity([query_embedding], [x])[0][0]
            )
            df2["similarity"] = df2["embedding"].apply(
                lambda x: cosine_similarity([query_embedding], [x])[0][0]
            )
            df3["similarity"] = df3["embedding"].apply(
                lambda x: cosine_similarity([query_embedding], [x])[0][0]
            )

            # Find the row with the highest similarity score in both CSVs
            most_relevant_entry_df1 = df1.loc[df1["similarity"].idxmax()]
            most_relevant_entry_df2 = df2.loc[df2["similarity"].idxmax()]
            most_relevant_entry_df3 = df3.loc[df3["similarity"].idxmax()]

            # Compare the highest similarity scores from both DataFrames
            if (
                most_relevant_entry_df1["similarity"]
                > most_relevant_entry_df2["similarity"]
                and most_relevant_entry_df1["similarity"]
                > most_relevant_entry_df3["similarity"]
            ):
                most_relevant_entry = most_relevant_entry_df1
            elif (
                most_relevant_entry_df2["similarity"]
                > most_relevant_entry_df1["similarity"]
                and most_relevant_entry_df2["similarity"]
                > most_relevant_entry_df3["similarity"]
            ):
                most_relevant_entry = most_relevant_entry_df2
            else:
                most_relevant_entry = most_relevant_entry_df3
            text = most_relevant_entry["text_scraped"]
            print(f"Most relevant entry: {text}")  # Debug print

            # Summarize the most relevant entry using GPT-3.5 turbo
            response = openai.ChatCompletion.create(
                engine="emotionally",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a compassionate mental health assistant, act like it and respond accordingly",
                    },
                    {
                        "role": "user",
                        "content": f"Please summarize the following text to make it coherent and concise:\n\n{text}",
                    },
                ],
                max_tokens=200,  # You can adjust the max tokens as needed
            )
            assistant_response = response["choices"][0]["message"]["content"].strip()
            insert_message("assistant", assistant_response, user)
            return jsonify({"response": assistant_response})
        except openai.error.RateLimitError as e:
            if (
                "Requests to the ChatCompletions_Create Operation under Azure OpenAI API version 2024-02-01 have exceeded token rate limit"
                in str(e)
            ):
                time.sleep(48)
                return get_response()
            else:
                return jsonify({"error": str(e)}), 500
        except openai.error.InvalidRequestError as e:
            print(f"OpenAI API error: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        try:
            # Handle general conversational queries
            # messages = retrieve_top_messages(user)
            messages = [
                {
                    "role": "system",
                    "content": "You are a compassionate mental health assistant, act like it and respond accordingly",
                },
                {"role": "user", "content": user_input},
            ]
            print(f"Retrieved messages: {messages}")  # Debug print

            response = openai.ChatCompletion.create(
                engine=deployment_name,
                messages=messages,
                max_tokens=150,
            )
            assistant_response = response.choices[0].message["content"].strip()
            insert_message("assistant", assistant_response, user)
            return jsonify({"response": assistant_response})
        except openai.error.RateLimitError as e:
            if (
                "Requests to the ChatCompletions_Create Operation under Azure OpenAI API version 2024-02-01 have exceeded token rate limit"
                in str(e)
            ):
                time.sleep(48)
                return get_response()
            else:
                return jsonify({"error": str(e)}), 500
        except openai.error.InvalidRequestError as e:
            print(f"OpenAI API error: {e}")
            return jsonify({"error": str(e)}), 500


@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Connect to the Azure SQL database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists in the database
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password)
        )
        user = cursor.fetchone
        if user:
            session["user"] = username
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password. Please try again."

    return render_template("login.html", error=error)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        age = request.form["age"]
        gender = request.form["gender"]
        password = request.form["password"]

        # Connect to the Azure SQL database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' and xtype='U')
            CREATE TABLE users (
                id INT IDENTITY(1,1) PRIMARY KEY,
                username NVARCHAR(50) NOT NULL,
                email NVARCHAR(50) NOT NULL,
                age INT NOT NULL,
                gender NVARCHAR(10) NOT NULL,
                password NVARCHAR(50) NOT NULL
            );
        """
        )

        cursor.execute("SELECT COUNT(*) FROM users WHERE username=?", (username,))
        if cursor.fetchone()[0] > 0:
            error = "Username already exists. Please choose a different one."

        elif not is_valid_email(email):
            error = "Invalid email format. Please enter a valid email address."

        cursor.execute("SELECT COUNT(*) FROM users WHERE email=?", (email,))
        if cursor.fetchone()[0] > 0:
            error = "Email already exists. Please use a different one."

        if error is None:
            cursor.execute(
                "INSERT INTO users (username, email, age, gender, password) VALUES (?, ?, ?, ?, ?)",
                (username, email, age, gender, password),
            )
            conn.commit()
            conn.close()

            return redirect(url_for("login"))

    return render_template("signup.html", error=error)


@app.route("/index")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(port=8000, debug=True)
