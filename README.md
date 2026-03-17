# AdVance – Ad Promotion Web Platform

A full-stack Flask + MongoDB Atlas ad promotion platform.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your MongoDB Atlas URI
Create a `.env` file in the root directory and add your connection string:
```bash
MONGO_URI="mongodb+srv://<username>:<password>@cluster0.mongodb.net/"
```
Or set it as an environment variable:
```bash
export MONGO_URI="mongodb+srv://..."
```
> **Note:** Without a valid URI the app runs with demo in-memory data so you can preview the UI immediately.

### 3. Run the app
```bash
python app.py
```
Visit http://localhost:5000

---

## Project Structure
```
ad_platform/
├── app.py                   # Flask app + all routes
├── requirements.txt
├── static/
│   ├── css/style.css        # Full responsive stylesheet
│   ├── js/main.js           # Timers, animations, nav
│   └── uploads/             # Local image uploads
└── templates/
    ├── base.html            # Navbar, footer, flash messages
    ├── index.html           # Home page
    ├── ads.html             # Browse all ads
    ├── post_ad.html         # Post ad form
    ├── dashboard.html       # User dashboard
    ├── edit_ad.html         # Edit ad form
    └── _ad_card.html        # Reusable ad card partial
```

## Routes
| Route              | Method    | Description                          |
|--------------------|-----------|--------------------------------------|
| `/`                | GET       | Home with hero, featured, trending   |
| `/ads`             | GET       | Browse all active ads                |
| `/post_ad`         | GET/POST  | Submit new ad                        |
| `/dashboard`       | GET       | User's ad management dashboard       |
| `/visit/<ad_id>`   | GET       | Increment views + redirect           |
| `/edit_ad/<id>`    | GET/POST  | Edit an existing ad                  |
| `/delete_ad/<id>`  | POST      | Delete an ad                         |

## Features
- ⭐ Featured ads (7-day) get special highlighted cards
- 🔥 Trending ads sorted by view count
- ⏳ Live countdown timers on each ad card
- 🔍 Search by keyword + filter by category
- 📊 Dashboard with view stats and status
- 🖼️ Image upload OR URL support
- 📱 Fully responsive mobile design
- 🎨 Dark theme with animated gradient UI
