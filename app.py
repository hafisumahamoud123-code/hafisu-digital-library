import streamlit as st
import pandas as pd
import json
import bcrypt
import re
import requests
import random
import time
from pathlib import Path

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="📚 Hafisu's Digital Library",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ORANGE THEME CSS ==========
st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=yes">
    <style>
        .stApp {
            background: linear-gradient(135deg, #ff7e05 0%, #ffb347 100%);
        }
        .main .block-container {
            background: rgba(0,0,0,0.05);
            backdrop-filter: blur(0px);
            border-radius: 30px;
            padding: 2rem 1.5rem !important;
            max-width: 1200px !important;
            margin: 1rem auto !important;
        }
        .book-card {
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .book-card:hover {
            transform: translateY(-3px);
        }
        .stButton > button {
            background: linear-gradient(90deg, #ff7e05, #ff9f2e);
            color: white;
            border: none;
            border-radius: 30px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            width: 100%;
        }
        .stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        h1, h2, h3 {
            color: white !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #4a2a00, #1f1400);
        }
        section[data-testid="stSidebar"] * {
            color: #ffe0b3;
        }
        .footer {
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(255,255,255,0.3);
            color: rgba(255,255,255,0.9);
            font-size: 0.8rem;
        }
        .creator-badge {
            text-align: center;
            font-size: 1rem;
            font-weight: bold;
            color: #fff3c9;
            margin-bottom: 1rem;
        }
    </style>
    <div class="creator-badge">✨ Created by <strong>Hafisu Mahamoud</strong> – University of Ghana, BSc Agriculture ✨</div>
""", unsafe_allow_html=True)

# ========== USER MANAGEMENT ==========
USER_FILE = Path("users.json")

def load_users():
    if USER_FILE.exists():
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(pw, hashed):
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def register_user(username, name, email, password):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    users[username] = {
        "name": name,
        "email": email,
        "password": hash_password(password),
        "favorites": [],
        "reading_progress": {},
        "challenge": {"goal": 0, "completed": 0}
    }
    save_users(users)
    return True, "Registration successful! Please log in."

def login_user(username, password):
    users = load_users()
    if username not in users:
        return False, "User not found.", None
    if verify_password(password, users[username]["password"]):
        return True, "Login successful", users[username]
    return False, "Wrong password.", None

# ========== SESSION STATE ==========
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'selected_book' not in st.session_state:
    st.session_state.selected_book = None

# ========== API FUNCTIONS ==========
@st.cache_data(ttl=3600)
def search_books(query, subject=None, limit=40):
    url = f"https://gutendex.com/books?search={query}&limit={limit}"
    if subject and subject != "All":
        url += f"&topic={subject.lower().replace(' ', '-')}"
    try:
        response = requests.get(url)
        data = response.json()
        books = data.get("results", [])
        results = []
        for book in books:
            authors = ", ".join([a["name"] for a in book.get("authors", [])]) if book.get("authors") else "Unknown"
            formats = book.get("formats", {})
            cover = formats.get("image/jpeg", "")
            text_link = formats.get("text/plain; charset=utf-8") or formats.get("text/html") or ""
            if not text_link:
                continue
            results.append({
                "id": book["id"],
                "title": book["title"],
                "authors": authors,
                "cover": cover,
                "text_link": text_link,
                "subjects": ", ".join(book.get("subjects", [])[:3])
            })
        return results
    except:
        return []

@st.cache_data(ttl=7200)
def get_random_books(limit=12):
    url = f"https://gutendex.com/books?sort=popular&limit={limit}"
    try:
        response = requests.get(url)
        data = response.json()
        books = data.get("results", [])
        results = []
        for book in books:
            authors = ", ".join([a["name"] for a in book.get("authors", [])]) if book.get("authors") else "Unknown"
            formats = book.get("formats", {})
            cover = formats.get("image/jpeg", "")
            text_link = formats.get("text/plain; charset=utf-8") or formats.get("text/html") or ""
            if not text_link:
                continue
            results.append({
                "id": book["id"],
                "title": book["title"],
                "authors": authors,
                "cover": cover,
                "text_link": text_link,
                "subjects": ", ".join(book.get("subjects", [])[:3])
            })
        return results
    except:
        return []

# ========== LOGIN / REGISTRATION ==========
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>📚 Hafisu's Digital Library</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        with st.form("login_form"):
            login_user_input = st.text_input("Username", key="login_username")
            login_pass = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login")
            if submitted:
                ok, msg, user_data = login_user(login_user_input, login_pass)
                if ok:
                    st.session_state.logged_in = True
                    st.session_state.user_name = user_data["name"]
                    st.session_state.user_data = user_data
                    st.rerun()
                else:
                    st.error(msg)
    
    with tab2:
        with st.form("register_form"):
            new_user = st.text_input("Username", key="reg_username")
            new_name = st.text_input("Full name", key="reg_name")
            new_email = st.text_input("Email", key="reg_email")
            new_pass = st.text_input("Password", type="password", key="reg_password")
            confirm_pass = st.text_input("Confirm password", type="password", key="reg_confirm")
            submitted_reg = st.form_submit_button("Register")
            if submitted_reg:
                if not all([new_user, new_name, new_email, new_pass]):
                    st.error("All fields required.")
                elif new_pass != confirm_pass:
                    st.error("Passwords don't match.")
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                    st.error("Invalid email.")
                else:
                    ok, msg = register_user(new_user, new_name, new_email, new_pass)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

# ========== MAIN LIBRARY ==========
else:
    st.sidebar.image("https://img.icons8.com/fluency/96/books.png", width=80)
    st.sidebar.title("📚 Digital Library")
    st.sidebar.write(f"Welcome, **{st.session_state.user_name}**")
    
    menu = st.sidebar.radio("Navigation", ["🔍 Search Books", "⭐ My Favorites", "📖 Reading Progress", "🎯 Reading Challenge", "🎲 Random Discovery"])
    
    if st.sidebar.button("🚪 Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_data = None
        st.rerun()
    
    st.markdown("<h1 style='text-align: center;'>📖 Your Digital Library</h1>", unsafe_allow_html=True)
    
    # ===== SEARCH BOOKS =====
    if menu == "🔍 Search Books":
        col1, col2 = st.columns([3,1])
        with col1:
            query = st.text_input("🔍 Search by title, author, or keyword", placeholder="e.g., agriculture, science, computer", key="search_query")
        with col2:
            subjects = ["All", "Science", "Technology", "Mathematics", "Economics", "Geography", "Political Science", "Computers", "Agriculture", "Biology", "Chemistry", "Physics"]
            subject_filter = st.selectbox("📂 Subject", subjects, key="subject_filter")
        
        if query:
            if st.button("Search", key="search_btn"):
                with st.spinner("Searching thousands of free books..."):
                    results = search_books(query, subject_filter if subject_filter != "All" else None, limit=40)
                    st.session_state.search_results = results
                    st.session_state.selected_book = None
        
        if st.session_state.search_results:
            st.subheader(f"📚 Found {len(st.session_state.search_results)} books")
            for book in st.session_state.search_results:
                with st.container():
                    colA, colB, colC = st.columns([1, 4, 1])
                    with colA:
                        if book["cover"]:
                            st.image(book["cover"], width=80)
                        else:
                            st.markdown("📖")
                    with colB:
                        st.markdown(f"**{book['title']}**  \n*{book['authors']}*  \n_{book['subjects']}_")
                    with colC:
                        if st.button("Read Now", key=f"read_{book['id']}"):
                            st.session_state.selected_book = book
                        if st.button("⭐ Favorite", key=f"fav_{book['id']}"):
                            if book['id'] not in st.session_state.user_data['favorites']:
                                st.session_state.user_data['favorites'].append(book['id'])
                                users = load_users()
                                users[st.session_state.user_name]['favorites'] = st.session_state.user_data['favorites']
                                save_users(users)
                                st.success("Added to favorites!")
                    st.markdown("<hr>", unsafe_allow_html=True)
            
            if st.session_state.selected_book:
                st.markdown(f"### Now Reading: {st.session_state.selected_book['title']}")
                st.components.v1.html(f'<iframe src="{st.session_state.selected_book["text_link"]}" width="100%" height="600" style="border:none;"></iframe>', height=620, scrolling=True)
    
    # ===== MY FAVORITES =====
    elif menu == "⭐ My Favorites":
        fav_ids = st.session_state.user_data.get('favorites', [])
        if not fav_ids:
            st.info("You haven't added any favorites yet. Search for books and click the ⭐ button.")
        else:
            # fetch details from API
            all_books = []
            for fid in fav_ids:
                results = search_books(f"id={fid}", limit=1)
                if results:
                    all_books.extend(results)
            for book in all_books:
                colA, colB, colC = st.columns([1,4,1])
                with colA:
                    if book.get("cover"):
                        st.image(book["cover"], width=80)
                with colB:
                    st.markdown(f"**{book['title']}**  \n*{book['authors']}*")
                with colC:
                    if st.button("Read", key=f"fav_read_{book['id']}"):
                        st.session_state.selected_book = book
                st.markdown("<hr>", unsafe_allow_html=True)
    
    # ===== READING PROGRESS =====
    elif menu == "📖 Reading Progress":
        progress = st.session_state.user_data.get('reading_progress', {})
        if not progress:
            st.info("Track your reading progress by marking pages or chapters.")
        else:
            for book_id, pct in progress.items():
                st.write(f"Book ID {book_id}: {pct}% complete")
        book_id_input = st.text_input("Book ID (from search result)")
        percent = st.slider("Percentage completed", 0, 100, 0)
        if st.button("Update Progress"):
            if book_id_input:
                st.session_state.user_data['reading_progress'][book_id_input] = percent
                users = load_users()
                users[st.session_state.user_name]['reading_progress'] = st.session_state.user_data['reading_progress']
                save_users(users)
                st.success("Progress saved!")
    
    # ===== READING CHALLENGE =====
    elif menu == "🎯 Reading Challenge":
        challenge = st.session_state.user_data.get('challenge', {"goal": 0, "completed": 0})
        goal = st.number_input("Set your reading goal (number of books this month)", min_value=0, max_value=100, value=challenge["goal"])
        if st.button("Set Goal"):
            challenge["goal"] = goal
            st.session_state.user_data['challenge'] = challenge
            users = load_users()
            users[st.session_state.user_name]['challenge'] = challenge
            save_users(users)
            st.success("Goal updated!")
        completed = st.number_input("Books completed so far", min_value=0, max_value=challenge["goal"], value=challenge["completed"])
        if st.button("Update Completed"):
            challenge["completed"] = completed
            st.session_state.user_data['challenge'] = challenge
            users = load_users()
            users[st.session_state.user_name]['challenge'] = challenge
            save_users(users)
            st.success("Progress updated!")
        if challenge["goal"] > 0:
            st.progress(challenge["completed"] / challenge["goal"])
            st.write(f"{challenge['completed']} / {challenge['goal']} books")
            if challenge["completed"] >= challenge["goal"]:
                st.balloons()
                st.success("🎉 Congratulations! You've achieved your reading challenge!")
    
    # ===== RANDOM DISCOVERY =====
    elif menu == "🎲 Random Discovery":
        if st.button("🎲 Surprise Me with a Random Book"):
            with st.spinner("Finding a random book for you..."):
                books = get_random_books(limit=20)
                if books:
                    book = random.choice(books)
                    st.session_state.selected_book = book
                    st.markdown(f"### 📖 {book['title']}")
                    st.markdown(f"*by {book['authors']}*")
                    st.markdown(f"**Topics:** {book['subjects']}")
                    if book["cover"]:
                        st.image(book["cover"], width=150)
                    if st.button("Read This Book"):
                        st.session_state.selected_book = book
                else:
                    st.warning("Could not fetch random books. Try again later.")
        if st.session_state.selected_book and "selected_book" in locals():
            st.components.v1.html(f'<iframe src="{st.session_state.selected_book["text_link"]}" width="100%" height="600"></iframe>', height=620, scrolling=True)
    
    # Footer
    st.markdown("---")
    st.markdown("<div class='footer'>📢 Hafisu Mahamoud – University of Ghana, BSc Agriculture – Free Digital Library for All Students</div>", unsafe_allow_html=True)