"""
Ad Promotion Web Platform - Flask Backend
Connects to MongoDB Atlas using PyMongo
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
import os
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Optional PyMongo / bson imports (falls back gracefully if not installed)
try:
    from pymongo import MongoClient, DESCENDING
    from bson.objectid import ObjectId
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    MongoClient = None
    # Lightweight ObjectId substitute for demo/no-DB mode
    class ObjectId:
        def __init__(self, oid=None):
            self._id = str(oid) if oid else uuid.uuid4().hex[:24]
        def __str__(self): return self._id
        def __repr__(self): return f"ObjectId('{self._id}')"
        def __eq__(self, other): return str(self) == str(other)
        def __hash__(self): return hash(self._id)

app = Flask(__name__)
app.secret_key = "ad_platform_secret_key_change_in_production"

# ─── MongoDB Atlas Connection ─────────────────────────────────────────────────
# Replace this URI with your MongoDB Atlas connection string in a .env file
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://laxmantejaswi9707_db_user:UQ8CMkZIv3JdQFzZ@cluster0.paep0wm.mongodb.net/"
)

try:
    if not PYMONGO_AVAILABLE:
        raise ImportError("PyMongo not installed")
    
    # Use certifi for SSL/TLS to avoid handshake errors on Windows
    import certifi
    client = MongoClient(
        MONGO_URI, 
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000
    )
    client.server_info()  # Test connection
    db = client["ad_platform"]
    ads_col = db["ads"]
    print("CONNECTED: Connected to MongoDB Atlas")
except Exception as e:
    print(f"FAILED: MongoDB connection failed: {e}")
    print("   Running with mock in-memory data for demo purposes.")
    client = None
    db = None
    ads_col = None

# ─── Mock in-memory store (fallback when MongoDB is not configured) ───────────
MOCK_ADS = []

def get_now():
    return datetime.utcnow()

def use_mock():
    return ads_col is None

# ─── Helper: filter active ads ────────────────────────────────────────────────
def active_only(ads):
    now = get_now()
    return [a for a in ads if a.get("expiry_date", now) > now]

# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    """Home page with hero, featured ads, categories, and trending ads."""
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    if use_mock():
        all_ads = list(MOCK_ADS)
    else:
        all_ads = list(ads_col.find())

    active = active_only(all_ads)

    # Featured ads: duration = 7 days, sorted by duration desc
    featured = sorted(
        [a for a in active if a.get("duration_days") == 7],
        key=lambda x: x.get("created_at", datetime.min),
        reverse=True
    )[:6]

    # Trending ads: most views
    trending = sorted(active, key=lambda x: x.get("views", 0), reverse=True)[:6]

    # Category counts
    categories = ["Education", "Apps", "Services", "Business", "Health", "Technology", "Entertainment", "Other"]
    cat_counts = {c: sum(1 for a in active if a.get("category") == c) for c in categories}

    return render_template(
        "index.html",
        featured=featured,
        trending=trending,
        categories=categories,
        cat_counts=cat_counts,
        total_ads=len(active),
        query=query,
        selected_category=category
    )


@app.route("/ads")
def ads_page():
    """View all active ads with search and filter."""
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sort_by = request.args.get("sort", "duration")

    if use_mock():
        all_ads = list(MOCK_ADS)
    else:
        all_ads = list(ads_col.find())

    active = active_only(all_ads)

    # Filter by search query
    if query:
        active = [a for a in active if query.lower() in a.get("title", "").lower()
                  or query.lower() in a.get("description", "").lower()]

    # Filter by category
    if category:
        active = [a for a in active if a.get("category") == category]

    # Sorting
    if sort_by == "views":
        active.sort(key=lambda x: x.get("views", 0), reverse=True)
    elif sort_by == "newest":
        active.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    else:  # default: duration desc, then newest
        active.sort(key=lambda x: (x.get("duration_days", 0), x.get("created_at", datetime.min)), reverse=True)

    categories = ["Education", "Apps", "Services", "Business", "Health", "Technology", "Entertainment", "Other"]

    return render_template(
        "ads.html",
        ads=active,
        categories=categories,
        query=query,
        selected_category=category,
        sort_by=sort_by,
        now=get_now()
    )


@app.route("/post_ad", methods=["GET", "POST"])
def post_ad():
    """Form to submit a new ad promotion."""
    categories = ["Education", "Apps", "Services", "Business", "Health", "Technology", "Entertainment", "Other"]

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "Other")
        external_link = request.form.get("external_link", "").strip()
        image_url = request.form.get("image_url", "").strip()
        duration_days = int(request.form.get("duration_days", 1))

        # Basic validation
        if not title or not external_link:
            flash("Title and External Link are required.", "error")
            return render_template("post_ad.html", categories=categories)

        # Ensure external link has protocol
        if external_link and not external_link.startswith(("http://", "https://")):
            external_link = "https://" + external_link

        # Handle image upload
        image_file = request.files.get("image_file")
        if image_file and image_file.filename:
            ext = os.path.splitext(image_file.filename)[1].lower()
            if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                fname = f"{uuid.uuid4().hex}{ext}"
                save_path = os.path.join(app.root_path, "static", "uploads", fname)
                image_file.save(save_path)
                image_url = f"/static/uploads/{fname}"

        # Fallback placeholder
        if not image_url:
            image_url = f"https://picsum.photos/seed/{uuid.uuid4().hex[:8]}/800/450"

        created_at = get_now()
        expiry_date = created_at + timedelta(days=duration_days)

        # Mock user session
        user_id = session.get("user_id", "guest_user")

        ad_doc = {
            "title": title,
            "description": description,
            "category": category,
            "external_link": external_link,
            "image_url": image_url,
            "duration_days": duration_days,
            "created_at": created_at,
            "expiry_date": expiry_date,
            "views": 0,
            "user_id": user_id,
        }

        if use_mock():
            ad_doc["_id"] = ObjectId()
            MOCK_ADS.append(ad_doc)
        else:
            ads_col.insert_one(ad_doc)

        flash("🎉 Your ad has been submitted successfully!", "success")
        return redirect(url_for("ads_page"))

    return render_template("post_ad.html", categories=categories)


@app.route("/dashboard")
def dashboard():
    """User dashboard showing their own ads."""
    user_id = session.get("user_id", "guest_user")

    if use_mock():
        user_ads = [a for a in MOCK_ADS if a.get("user_id") == user_id]
    else:
        user_ads = list(ads_col.find({"user_id": user_id}))

    now = get_now()
    # Add status to each ad
    for ad in user_ads:
        ad["is_active"] = ad.get("expiry_date", now) > now

    user_ads.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)

    return render_template("dashboard.html", ads=user_ads, now=now)


@app.route("/visit/<ad_id>")
def visit_ad(ad_id):
    """Increment view count and redirect to external link."""
    try:
        oid = ObjectId(ad_id)
    except Exception:
        flash("Invalid ad ID.", "error")
        return redirect(url_for("ads_page"))

    external_link = "#"

    if use_mock():
        for ad in MOCK_ADS:
            if str(ad["_id"]) == ad_id:
                ad["views"] = ad.get("views", 0) + 1
                external_link = ad.get("external_link", "#")
                break
    else:
        ad = ads_col.find_one_and_update(
            {"_id": oid},
            {"$inc": {"views": 1}},
            return_document=True
        )
        if ad:
            external_link = ad.get("external_link", "#")

    return redirect(external_link)


@app.route("/delete_ad/<ad_id>", methods=["POST"])
def delete_ad(ad_id):
    """Delete an ad (only owner can delete)."""
    user_id = session.get("user_id", "guest_user")

    if use_mock():
        global MOCK_ADS
        MOCK_ADS = [a for a in MOCK_ADS if not (str(a["_id"]) == ad_id and a.get("user_id") == user_id)]
    else:
        try:
            ads_col.delete_one({"_id": ObjectId(ad_id), "user_id": user_id})
        except Exception:
            pass

    flash("Ad deleted successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/edit_ad/<ad_id>", methods=["GET", "POST"])
def edit_ad(ad_id):
    """Edit an existing ad."""
    user_id = session.get("user_id", "guest_user")
    categories = ["Education", "Apps", "Services", "Business", "Health", "Technology", "Entertainment", "Other"]

    # Fetch ad
    ad = None
    if use_mock():
        for a in MOCK_ADS:
            if str(a["_id"]) == ad_id and a.get("user_id") == user_id:
                ad = a
                break
    else:
        try:
            ad = ads_col.find_one({"_id": ObjectId(ad_id), "user_id": user_id})
        except Exception:
            pass

    if not ad:
        flash("Ad not found or permission denied.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        updates = {
            "title": request.form.get("title", "").strip(),
            "description": request.form.get("description", "").strip(),
            "category": request.form.get("category", "Other"),
            "external_link": request.form.get("external_link", "").strip(),
            "image_url": request.form.get("image_url", ad.get("image_url", "")),
        }

        if use_mock():
            ad.update(updates)
        else:
            ads_col.update_one({"_id": ObjectId(ad_id)}, {"$set": updates})

        flash("Ad updated successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("edit_ad.html", ad=ad, categories=categories)


@app.route("/set_session")
def set_session():
    """Set a mock user session (demo purposes)."""
    if "user_id" not in session:
        session["user_id"] = f"user_{uuid.uuid4().hex[:8]}"
    return redirect(url_for("home"))


# ─── Seed demo data if empty ──────────────────────────────────────────────────
def seed_demo_data():
    """Insert demo ads for demonstration purposes."""
    demo_ads = [
        {
            "_id": ObjectId(),
            "title": "Learn Python in 30 Days",
            "description": "Join our intensive Python bootcamp designed for beginners. Hands-on projects, mentorship, and job placement support included.",
            "category": "Education",
            "external_link": "https://example.com/python-course",
            "image_url": "https://images.unsplash.com/photo-1587620962725-abab7fe55159?w=800&q=80",
            "duration_days": 7,
            "created_at": get_now() - timedelta(days=1),
            "expiry_date": get_now() + timedelta(days=6),
            "views": 248,
            "user_id": "demo_user",
        },
        {
            "_id": ObjectId(),
            "title": "TaskFlow - Project Management App",
            "description": "Streamline your team's workflow with TaskFlow. Real-time collaboration, Kanban boards, and AI-powered scheduling.",
            "category": "Apps",
            "external_link": "https://example.com/taskflow",
            "image_url": "https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=800&q=80",
            "duration_days": 7,
            "created_at": get_now() - timedelta(days=2),
            "expiry_date": get_now() + timedelta(days=5),
            "views": 189,
            "user_id": "demo_user",
        },
        {
            "_id": ObjectId(),
            "title": "Digital Marketing Agency",
            "description": "Grow your brand with data-driven marketing strategies. SEO, social media management, and paid ads that convert.",
            "category": "Services",
            "external_link": "https://example.com/marketing",
            "image_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80",
            "duration_days": 3,
            "created_at": get_now() - timedelta(hours=12),
            "expiry_date": get_now() + timedelta(days=2, hours=12),
            "views": 97,
            "user_id": "demo_user2",
        },
        {
            "_id": ObjectId(),
            "title": "HealthTrack Pro",
            "description": "Monitor your fitness journey with HealthTrack Pro. Calorie tracking, workout plans, and sleep analysis all in one app.",
            "category": "Health",
            "external_link": "https://example.com/healthtrack",
            "image_url": "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?w=800&q=80",
            "duration_days": 3,
            "created_at": get_now() - timedelta(hours=6),
            "expiry_date": get_now() + timedelta(days=2, hours=18),
            "views": 145,
            "user_id": "demo_user2",
        },
        {
            "_id": ObjectId(),
            "title": "StartupLaunch Business Consulting",
            "description": "From idea to IPO. Our team of ex-founders and investors guide you through fundraising, scaling, and strategy.",
            "category": "Business",
            "external_link": "https://example.com/startup",
            "image_url": "https://images.unsplash.com/photo-1553484771-047a44eee27b?w=800&q=80",
            "duration_days": 1,
            "created_at": get_now() - timedelta(hours=3),
            "expiry_date": get_now() + timedelta(hours=21),
            "views": 34,
            "user_id": "demo_user3",
        },
        {
            "_id": ObjectId(),
            "title": "CloudSync Storage Solutions",
            "description": "Secure, fast, and affordable cloud storage. 1TB free trial, end-to-end encryption, and cross-device sync.",
            "category": "Technology",
            "external_link": "https://example.com/cloudsync",
            "image_url": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=800&q=80",
            "duration_days": 7,
            "created_at": get_now() - timedelta(days=3),
            "expiry_date": get_now() + timedelta(days=4),
            "views": 312,
            "user_id": "demo_user3",
        },
    ]

    if use_mock():
        MOCK_ADS.extend(demo_ads)
    else:
        if ads_col.count_documents({}) == 0:
            ads_col.insert_many(demo_ads)


# ─── App entry point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Ensure session gets set for demo
    @app.before_request
    def ensure_session():
        if "user_id" not in session:
            session["user_id"] = "guest_user"

    seed_demo_data()
    print("Starting AdVance Platform on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
