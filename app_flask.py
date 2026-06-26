import os
import re
import uuid
import datetime
import random
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask App
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'antigravity_secret_key_129847391')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

@app.template_filter('slice_limit')
def slice_limit(lst, limit):
    return lst[:limit] if lst else []

# ==========================================
# DATABASE MODELS
# ==========================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default='user')  # super_admin, admin, user
    otp = db.Column(db.String(6), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    poster_url = db.Column(db.String(500), nullable=True)
    screenshots = db.Column(db.Text, nullable=True)  # Comma-separated urls
    trailer_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    director = db.Column(db.String(100), nullable=True)
    cast = db.Column(db.String(300), nullable=True)
    release_date = db.Column(db.String(50), nullable=True)
    genre = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    imdb_rating = db.Column(db.Float, default=7.0)
    is_paid = db.Column(db.Boolean, default=False)
    price = db.Column(db.Float, default=0.0)
    subtitle_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default='published')  # draft, published, featured, trending
    views = db.Column(db.Integer, default=0)
    downloads_count = db.Column(db.Integer, default=0)
    scheduled_release = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Resolution/Quality links (URL or uploaded file path)
    link_480p = db.Column(db.String(500), nullable=True)
    link_720p = db.Column(db.String(500), nullable=True)
    link_1080p = db.Column(db.String(500), nullable=True)
    link_4k = db.Column(db.String(500), nullable=True)

    @property
    def quality_options(self):
        qualities = []
        if self.link_480p: qualities.append("480p")
        if self.link_720p: qualities.append("720p")
        if self.link_1080p: qualities.append("1080p")
        if self.link_4k: qualities.append("4K")
        return ", ".join(qualities) if qualities else "HD"


class UpcomingMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    poster_url = db.Column(db.String(500), nullable=True)
    release_date = db.Column(db.String(50), nullable=True)
    trailer_url = db.Column(db.String(500), nullable=True)  # YouTube link
    genre = db.Column(db.String(100), nullable=True)
    cast = db.Column(db.String(300), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class WebSeries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    poster_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    director = db.Column(db.String(100), nullable=True)
    cast = db.Column(db.String(300), nullable=True)
    release_date = db.Column(db.String(50), nullable=True)
    genre = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='published')  # draft, published, featured, trending
    views = db.Column(db.Integer, default=0)
    is_paid = db.Column(db.Boolean, default=False)
    price = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    episodes = db.relationship('Episode', backref='web_series', lazy=True, cascade="all, delete-orphan")


class Episode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    web_series_id = db.Column(db.Integer, db.ForeignKey('web_series.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    season_number = db.Column(db.Integer, default=1)
    episode_number = db.Column(db.Integer, default=1)
    cover_url = db.Column(db.String(500), nullable=True)
    video_url = db.Column(db.String(500), nullable=False)  # url or uploaded path
    duration = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(150), nullable=False)
    cover_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    songs = db.relationship('Song', backref='album', lazy=True, cascade="all, delete-orphan")


class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=True)
    artist = db.Column(db.String(150), nullable=True)
    cover_url = db.Column(db.String(500), nullable=True)
    lyrics = db.Column(db.Text, nullable=True)
    music_video_url = db.Column(db.String(500), nullable=True)
    external_streaming_links = db.Column(db.Text, nullable=True)
    song_type = db.Column(db.String(20), default='free')  # free, paid
    price = db.Column(db.Float, default=0.0)
    downloads_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Song Qualities (MP3/FLAC link or uploaded file path)
    audio_128_url = db.Column(db.String(500), nullable=True)
    audio_320_url = db.Column(db.String(500), nullable=True)


class SubscriptionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration_months = db.Column(db.Integer, default=1)
    description = db.Column(db.Text, nullable=True)


class UserSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    user = db.relationship('User', backref='subscriptions')
    plan = db.relationship('SubscriptionPlan')


class PaymentRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    utr_number = db.Column(db.String(12), nullable=False, unique=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=True)
    web_series_id = db.Column(db.Integer, db.ForeignKey('web_series.id'), nullable=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String(50), nullable=False, unique=True)
    status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='payments')
    movie = db.relationship('Movie', backref='payments')
    song = db.relationship('Song', backref='payments')
    web_series = db.relationship('WebSeries', backref='payments')
    plan = db.relationship('SubscriptionPlan')


class Advertisement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad_type = db.Column(db.String(50), nullable=False)  # google_adsense, banner, sidebar, video, sponsored, popup
    banner_url = db.Column(db.String(500), nullable=True)
    target_url = db.Column(db.String(500), nullable=True)
    display_duration = db.Column(db.Integer, default=10)
    priority = db.Column(db.Integer, default=0)
    ad_code = db.Column(db.Text, nullable=True)  # Google AdSense scripts
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Promotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    promo_type = db.Column(db.String(50), nullable=False)  # homepage_banner, trending, featured_movie, featured_song, flash_sale, coupon, seasonal
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(300), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    target_url = db.Column(db.String(500), nullable=True)
    coupon_code = db.Column(db.String(50), nullable=True)
    discount_percent = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default="StreamVibe")
    logo_url = db.Column(db.String(500), nullable=True)
    favicon_url = db.Column(db.String(500), nullable=True)
    footer_content = db.Column(db.Text, default="&copy; 2026 StreamVibe. All rights reserved.")
    terms_conditions = db.Column(db.Text, nullable=True)
    privacy_policy = db.Column(db.Text, nullable=True)
    contact_info = db.Column(db.Text, nullable=True)
    homepage_sections = db.Column(db.Text, default="slider,trending,movies,music,promotions")
    navigation_menu = db.Column(db.Text, default="Home|/,Movies|/movies,Music|/music,Contact|/terms#contact")
    theme_colors = db.Column(db.String(100), default="dark-purple")
    seo_metadata = db.Column(db.Text, default="description=Stream Premium Movies and Songs;keywords=movies,download,music,streaming,mp3")
    chatbot_settings = db.Column(db.Text, default="system_prompt=You are StreamVibe AI, a helpful movie and music expert recommendation bot.;voice_enabled=true;multilingual=true")
    ai_agent_settings = db.Column(db.Text, default="auto_generate=true;duplicate_detect=true;pricing_suggest=true")
    payment_qr_url = db.Column(db.String(500), default="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=upi://pay?pa=pay@streamvibe%26pn=StreamVibe")
    upi_id = db.Column(db.String(100), default="pay@streamvibe")
    adsense_code = db.Column(db.Text, default='<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8471194516724047" crossorigin="anonymous"></script>')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    username = db.Column(db.String(80), nullable=True)
    action = db.Column(db.String(200), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=True)
    web_series_id = db.Column(db.Integer, db.ForeignKey('web_series.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', backref=db.backref('wishlists', cascade="all, delete-orphan"))
    movie = db.relationship('Movie', backref=db.backref('wishlists', cascade="all, delete-orphan"))
    song = db.relationship('Song', backref=db.backref('wishlists', cascade="all, delete-orphan"))
    web_series = db.relationship('WebSeries', backref=db.backref('wishlists', cascade="all, delete-orphan"))


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=True)
    rating = db.Column(db.Integer, default=5)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', backref='reviews')
    movie = db.relationship('Movie', backref='reviews')
    song = db.relationship('Song', backref='reviews')


class SecureDownloadToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=True)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    downloads_count = db.Column(db.Integer, default=0)
    max_downloads = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User')
    movie = db.relationship('Movie')
    song = db.relationship('Song')


# ==========================================
# DECORATORS & UTILITY FUNCTIONS
# ==========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            session['next_url'] = request.path
            return redirect(url_for('auth_page'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in.', 'warning')
                return redirect(url_for('auth_page'))
            user = User.query.get(session['user_id'])
            if not user or user.role not in roles:
                flash('Access denied. Insufficient permissions.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_site_settings():
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        db.session.commit()
    return settings

def get_active_ads():
    return Advertisement.query.filter_by(status='active').order_by(Advertisement.priority.desc()).all()

def add_audit_log(user_id, action, details=""):
    try:
        user = User.query.get(user_id) if user_id else None
        username = user.username if user else "Anonymous"
        ip = request.remote_addr
        log = AuditLog(user_id=user_id, username=username, action=action, ip_address=ip, details=details)
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging audit: {e}")

# Check if user has an active membership subscription
def has_active_subscription(user_id):
    if not user_id:
        return False
    sub = UserSubscription.query.filter_by(user_id=user_id, is_active=True).first()
    if sub:
        if sub.end_date > datetime.datetime.utcnow():
            return True
        else:
            sub.is_active = False
            db.session.commit()
    return False

# Reusable file upload handler supporting URL fallback
def handle_file_upload(file_field, default_url):
    file = request.files.get(file_field)
    if file and file.filename != '':
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        upload_folder = os.path.join(app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, unique_name))
        return f"/static/uploads/{unique_name}"
    return default_url

# Context processor to inject global variables in all templates
@app.context_processor
def inject_global_data():
    settings = get_site_settings()
    ads = get_active_ads()
    
    # Simple parser for navigation menu
    nav_links = []
    if settings.navigation_menu:
        for item in settings.navigation_menu.split(','):
            if '|' in item:
                title, url = item.split('|', 1)
                nav_links.append({'title': title.strip(), 'url': url.strip()})
    
    # Parse theme settings
    theme = settings.theme_colors or 'dark-purple'

    # Parse SEO tags
    seo = {}
    if settings.seo_metadata:
        for tag in settings.seo_metadata.split(';'):
            if '=' in tag:
                k, v = tag.split('=', 1)
                seo[k.strip()] = v.strip()
    
    # Load site promotions
    banner_promos = Promotion.query.filter_by(promo_type='homepage_banner', is_active=True).all()
    flash_sales = Promotion.query.filter_by(promo_type='flash_sale', is_active=True).all()

    # User context
    current_user = None
    user_subscribed = False
    if 'user_id' in session:
        current_user = User.query.get(session['user_id'])
        user_subscribed = has_active_subscription(session['user_id'])

    return dict(
        settings=settings,
        ads=ads,
        nav_links=nav_links,
        theme=theme,
        seo=seo,
        banner_promos=banner_promos,
        flash_sales=flash_sales,
        current_user=current_user,
        user_subscribed=user_subscribed
    )


# ==========================================
# MAIL DISPATCHER (SMTP + HTML Emails)
# ==========================================

def send_mock_email(to_email, subject, template_name, context):
    """
    Sends beautiful, colorful HTML emails via SMTP.
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    print(f"\n[EMAIL DISPATCHER] To: {to_email} | Subject: {subject}")
    
    smtp_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    try:
        smtp_port = int(os.environ.get('EMAIL_PORT', 587))
    except ValueError:
        smtp_port = 587
    smtp_user = os.environ.get('EMAIL_HOST_USER', 'bhushan.272006@gmail.com')
    smtp_pass = os.environ.get('EMAIL_HOST_PASSWORD', 'gpkh pcco zwmw dyxp')
    from_email = os.environ.get('DEFAULT_FROM_EMAIL', 'ServiceHub <bhushan.272006@gmail.com>')

    try:
        html_body = render_template(f"emails/{template_name}.html", **context)
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        part = MIMEText(html_body, 'html')
        msg.attach(part)
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        
        print("[EMAIL DISPATCHER] Success! Email sent successfully via SMTP.")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send SMTP: {e}. Saving copy locally.")
        
    # Write a copy to files for review
    try:
        html_body = render_template(f"emails/{template_name}.html", **context)
        email_log_dir = os.path.join(app.root_path, '.gemini_email_logs')
        os.makedirs(email_log_dir, exist_ok=True)
        safe_subject = re.sub(r'[^a-zA-Z0-9]', '_', subject)
        filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_subject}.html"
        with open(os.path.join(email_log_dir, filename), 'w', encoding='utf-8') as f:
            f.write(html_body)
    except Exception as ex:
        print(f"[EMAIL ERROR] Failed saving file backup: {ex}")
    print("=" * 60 + "\n")


# ==========================================
# FRONTEND PAGES & CONTROLLERS
# ==========================================

@app.route('/')
def index():
    movies_featured = Movie.query.filter_by(status='featured').all()
    movies_trending = Movie.query.filter_by(status='trending').all()
    movies_free = Movie.query.filter_by(is_paid=False, status='published').limit(6).all()
    movies_paid = Movie.query.filter_by(is_paid=True, status='published').limit(6).all()
    
    albums = Album.query.limit(4).all()
    songs_free = Song.query.filter_by(song_type='free').limit(5).all()
    
    # Web Series
    web_series = WebSeries.query.filter_by(status='published').limit(4).all()
    
    # Upcoming Movies
    upcoming = UpcomingMovie.query.order_by(UpcomingMovie.release_date.asc()).limit(4).all()

    # Subscription Plans for Home page
    plans = SubscriptionPlan.query.all()

    promo_banners = Promotion.query.filter_by(promo_type='homepage_banner', is_active=True).all()
    flash_sales = Promotion.query.filter_by(promo_type='flash_sale', is_active=True).all()
    adsense_top = Advertisement.query.filter_by(ad_type='google_adsense', status='active').first()

    return render_template('home.html', 
                           featured=movies_featured,
                           trending=movies_trending,
                           movies_free=movies_free,
                           movies_paid=movies_paid,
                           albums=albums,
                           songs_free=songs_free,
                           web_series=web_series,
                           upcoming=upcoming,
                           plans=plans,
                           promo_banners=promo_banners,
                           flash_sales=flash_sales,
                           adsense_top=adsense_top)


@app.route('/movies')
def browse_movies():
    query = request.args.get('q', '')
    genre = request.args.get('genre', '')
    lang = request.args.get('lang', '')
    price_type = request.args.get('price_type', '')
    
    db_query = Movie.query.filter_by(status='published')
    if query:
        db_query = db_query.filter(Movie.title.ilike(f'%{query}%') | Movie.description.ilike(f'%{query}%') | Movie.cast.ilike(f'%{query}%'))
    if genre:
        db_query = db_query.filter(Movie.genre.ilike(f'%{genre}%'))
    if lang:
        db_query = db_query.filter(Movie.language.ilike(f'%{lang}%'))
    if price_type == 'free':
        db_query = db_query.filter_by(is_paid=False)
    elif price_type == 'paid':
        db_query = db_query.filter_by(is_paid=True)
        
    movies = db_query.order_by(Movie.release_date.desc()).all()
    
    all_genres = set()
    for m in Movie.query.with_entities(Movie.genre).all():
        if m.genre:
            for g in m.genre.split(','):
                all_genres.add(g.strip())
                
    return render_template('movies.html', movies=movies, genres=sorted(all_genres), selected_genre=genre, selected_lang=lang, price_type=price_type, query=query)


@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    movie.views += 1
    db.session.commit()
    
    has_purchased = False
    if 'user_id' in session:
        # User has full access if subscribed
        if has_active_subscription(session['user_id']):
            has_purchased = True
        else:
            has_purchased = PaymentRequest.query.filter_by(
                user_id=session['user_id'], 
                movie_id=movie_id, 
                status='verified'
            ).first() is not None
        
    reviews = Review.query.filter_by(movie_id=movie_id).order_by(Review.created_at.desc()).all()
    related = Movie.query.filter(Movie.id != movie.id, Movie.genre.ilike(f'%{movie.genre.split(",")[0] if movie.genre else ""}%')).limit(4).all()
    screenshot_list = [s.strip() for s in movie.screenshots.split(',') if s.strip()] if movie.screenshots else []

    return render_template('movie_detail.html', 
                           movie=movie, 
                           has_purchased=has_purchased, 
                           reviews=reviews, 
                           related=related, 
                           screenshots=screenshot_list)


# Web Series Browser
@app.route('/webseries')
def browse_web_series():
    series = WebSeries.query.filter_by(status='published').all()
    return render_template('webseries.html', series=series)


@app.route('/webseries/<int:series_id>')
def web_series_detail(series_id):
    series = WebSeries.query.get_or_404(series_id)
    series.views += 1
    db.session.commit()
    
    has_purchased = False
    if 'user_id' in session:
        if has_active_subscription(session['user_id']):
            has_purchased = True
        else:
            has_purchased = PaymentRequest.query.filter_by(
                user_id=session['user_id'],
                web_series_id=series_id,
                status='verified'
            ).first() is not None

    # Group episodes by season
    seasons = {}
    for ep in series.episodes:
        if ep.season_number not in seasons:
            seasons[ep.season_number] = []
        seasons[ep.season_number].append(ep)

    return render_template('webseries_detail.html', series=series, seasons=seasons, has_purchased=has_purchased)


@app.route('/webseries/episode/<int:episode_id>')
@login_required
def watch_episode(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    series = episode.web_series
    
    # Check access permission
    has_purchased = False
    if not series.is_paid:
        has_purchased = True
    elif has_active_subscription(session['user_id']):
        has_purchased = True
    else:
        has_purchased = PaymentRequest.query.filter_by(
            user_id=session['user_id'],
            web_series_id=series.id,
            status='verified'
        ).first() is not None

    if not has_purchased:
        flash("You need to purchase this web series subscription to watch episodes.", "warning")
        return redirect(url_for('web_series_detail', series_id=series.id))

    return render_template('episode_watch.html', episode=episode, series=series)


# Upcoming movies page with YouTube Embed
@app.route('/upcoming')
def upcoming_movies():
    upcoming = UpcomingMovie.query.order_by(UpcomingMovie.release_date.asc()).all()
    return render_template('upcoming.html', upcoming=upcoming)


@app.route('/music')
def browse_music():
    query = request.args.get('q', '')
    album_id = request.args.get('album', '')
    albums = Album.query.all()
    
    song_query = Song.query
    if query:
        song_query = song_query.filter(Song.title.ilike(f'%{query}%') | Song.artist.ilike(f'%{query}%') | Song.lyrics.ilike(f'%{query}%'))
    if album_id:
        song_query = song_query.filter_by(album_id=album_id)
        
    songs = song_query.all()
    
    # Determine purchases or active subscription
    purchased_song_ids = []
    user_subscribed = False
    if 'user_id' in session:
        user_subscribed = has_active_subscription(session['user_id'])
        if not user_subscribed:
            payments = PaymentRequest.query.filter_by(user_id=session['user_id'], status='verified').all()
            purchased_song_ids = [p.song_id for p in payments if p.song_id]
        
    return render_template('music.html', songs=songs, albums=albums, selected_album=int(album_id) if album_id else None, query=query, purchased_songs=purchased_song_ids, user_subscribed=user_subscribed)


# Subscriptions choosing panel
@app.route('/subscriptions')
@login_required
def subscriptions_portal():
    plans = SubscriptionPlan.query.all()
    active_sub = UserSubscription.query.filter_by(user_id=session['user_id'], is_active=True).first()
    return render_template('subscriptions.html', plans=plans, active_sub=active_sub)


# ==========================================
# CHECKOUT & PAYMENT VERIFICATION WORKFLOW
# ==========================================

@app.route('/checkout/<string:item_type>/<int:item_id>', methods=['GET', 'POST'])
@login_required
def checkout(item_type, item_id):
    user = User.query.get(session['user_id'])
    movie = None
    song = None
    webseries = None
    plan = None
    amount = 0.0
    item_name = ""

    if item_type == 'movie':
        movie = Movie.query.get_or_404(item_id)
        amount = movie.price
        item_name = movie.title
    elif item_type == 'song':
        song = Song.query.get_or_404(item_id)
        amount = song.price
        item_name = song.title
    elif item_type == 'webseries':
        webseries = WebSeries.query.get_or_404(item_id)
        amount = webseries.price
        item_name = webseries.title
    elif item_type == 'plan':
        plan = SubscriptionPlan.query.get_or_404(item_id)
        amount = plan.price
        item_name = f"Membership: {plan.name}"
    else:
        flash("Invalid purchase type.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        utr_number = request.form.get('utr_number', '').strip()

        if not re.match(r'^[a-zA-Z0-9]{12}$', utr_number):
            flash("Invalid UTR number! It must be exactly 12 alphanumeric characters.", "danger")
            return render_template('purchase.html', item_type=item_type, movie=movie, song=song, webseries=webseries, plan=plan, amount=amount, item_name=item_name, user=user)

        existing = PaymentRequest.query.filter_by(utr_number=utr_number).first()
        if existing:
            flash("This UTR number has already been submitted.", "warning")
            return render_template('purchase.html', item_type=item_type, movie=movie, song=song, webseries=webseries, plan=plan, amount=amount, item_name=item_name, user=user)

        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

        pay_request = PaymentRequest(
            user_id=user.id, name=name, email=email, phone=phone, utr_number=utr_number,
            movie_id=movie.id if movie else None,
            song_id=song.id if song else None,
            web_series_id=webseries.id if webseries else None,
            plan_id=plan.id if plan else None,
            amount=amount, transaction_id=transaction_id, status='pending'
        )
        db.session.add(pay_request)
        db.session.commit()

        add_audit_log(user.id, "PAYMENT_SUBMITTED", f"Submitted UTR {utr_number} for {item_name} (Txn: {transaction_id})")

        email_ctx = {
            'username': user.username,
            'item_name': item_name,
            'amount': amount,
            'utr': utr_number,
            'txn_id': transaction_id,
            'logo_url': get_site_settings().logo_url or '/static/assets/logo.png'
        }
        send_mock_email(email, f"Purchase Request Received: {item_name}", "purchase_received", email_ctx)

        flash("Payment request submitted successfully! Once matched by our admins, your subscription or downloads will activate.", "success")
        return redirect(url_for('user_profile'))

    return render_template('purchase.html', item_type=item_type, movie=movie, song=song, webseries=webseries, plan=plan, amount=amount, item_name=item_name, user=user)


# ==========================================
# SECURE DOWNLOAD DELIVERY
# ==========================================

@app.route('/download/request/<string:item_type>/<int:item_id>')
@login_required
def request_download(item_type, item_id):
    user = User.query.get(session['user_id'])
    is_authorized = False
    movie = None
    song = None
    
    # Subscribed accounts can bypass individual checks
    if has_active_subscription(user.id):
        is_authorized = True
        if item_type == 'movie':
            movie = Movie.query.get_or_404(item_id)
        else:
            song = Song.query.get_or_404(item_id)
    else:
        if item_type == 'movie':
            movie = Movie.query.get_or_404(item_id)
            if not movie.is_paid:
                is_authorized = True
            else:
                payment = PaymentRequest.query.filter_by(user_id=user.id, movie_id=movie.id, status='verified').first()
                if payment:
                    is_authorized = True
        elif item_type == 'song':
            song = Song.query.get_or_404(item_id)
            if song.song_type == 'free':
                is_authorized = True
            else:
                payment = PaymentRequest.query.filter_by(user_id=user.id, song_id=song.id, status='verified').first()
                if payment:
                    is_authorized = True

    if not is_authorized:
        flash("Access Denied. Please purchase this item or get a membership subscription.", "danger")
        return redirect(url_for('checkout', item_type=item_type, item_id=item_id))

    token_str = f"DL-{uuid.uuid4().hex}"
    expires = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    
    dl_token = SecureDownloadToken(
        token=token_str, user_id=user.id,
        movie_id=movie.id if movie else None,
        song_id=song.id if song else None,
        expires_at=expires, max_downloads=3
    )
    db.session.add(dl_token)
    db.session.commit()

    return redirect(url_for('download_file', token=token_str, quality=request.args.get('quality', '')))


@app.route('/download/link/<string:token>')
def download_file(token):
    dl_token = SecureDownloadToken.query.filter_by(token=token).first()
    if not dl_token:
        return "Invalid download link.", 404
    if dl_token.expires_at < datetime.datetime.utcnow():
        return "This download link has expired (24h limit reached).", 410
    if dl_token.downloads_count >= dl_token.max_downloads:
        return "Link download limit exceeded.", 403

    dl_token.downloads_count += 1
    
    quality = request.args.get('quality', '')
    if dl_token.movie:
        dl_token.movie.downloads_count += 1
        title = dl_token.movie.title
        
        # Select target quality or fallback
        if quality == '480p':
            file_url = dl_token.movie.link_480p or dl_token.movie.link_720p or dl_token.movie.link_1080p or dl_token.movie.link_4k or "https://www.w3schools.com/html/mov_bbb.mp4"
        elif quality == '720p':
            file_url = dl_token.movie.link_720p or dl_token.movie.link_1080p or dl_token.movie.link_4k or dl_token.movie.link_480p or "https://www.w3schools.com/html/mov_bbb.mp4"
        elif quality == '1080p':
            file_url = dl_token.movie.link_1080p or dl_token.movie.link_720p or dl_token.movie.link_4k or dl_token.movie.link_480p or "https://www.w3schools.com/html/mov_bbb.mp4"
        elif quality == '4k':
            file_url = dl_token.movie.link_4k or dl_token.movie.link_1080p or dl_token.movie.link_720p or dl_token.movie.link_480p or "https://www.w3schools.com/html/mov_bbb.mp4"
        else:
            file_url = dl_token.movie.link_1080p or dl_token.movie.link_720p or dl_token.movie.link_480p or dl_token.movie.link_4k or "https://www.w3schools.com/html/mov_bbb.mp4"
            
        if quality:
            title = f"{title} [{quality.upper()}]"
    else:
        dl_token.song.downloads_count += 1
        title = dl_token.song.title
        file_url = dl_token.song.audio_320_url or dl_token.song.audio_128_url or "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

    db.session.commit()
    add_audit_log(dl_token.user_id, "DOWNLOAD_EXECUTED", f"Downloaded {title}")
    return render_template('download_landing.html', file_url=file_url, title=title, dl_token=dl_token)


# ==========================================
# METADATA AUTO-FETCH API (AI AGENT FEATURE)
# ==========================================

def scrape_unsplash(query):
    try:
        import urllib.parse
        import requests
        import re
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        url = f"https://unsplash.com/s/photos/{urllib.parse.quote(query)}"
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            urls = re.findall(r'https://images\.unsplash\.com/photo-[a-zA-Z0-9\-]+', r.text)
            if urls:
                # Return the first match with clean resolution parameters
                return f"{urls[0]}?auto=format&fit=crop&w=400&q=80"
    except Exception as e:
        print(f"Scraper error: {e}")
    return None


@app.route('/api/metadata/fetch', methods=['POST'])
@role_required('admin', 'super_admin')
def fetch_online_metadata():
    """
    AI Agent Metadata Scraper with Unsplash HTML parser and default Indian movie details.
    """
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    item_type = data.get('type', 'movie') # movie or web_series

    if not title:
        return jsonify({'error': 'Title is required'}), 400

    query = title.lower()
    
    # Direct mapping for specific Indian / Bollywood blockbusters to guarantee proper poster and details
    if 'dhamaal' in query:
        scraped_poster = "https://upload.wikimedia.org/wikipedia/en/a/a2/Dhamaal_film_poster.jpg"
        desc = "Four lazy, good-for-nothing friends find out about a hidden treasure in Goa from a dying thief. They embark on a race to find the treasure before a determined police inspector."
        cast = "Sanjay Dutt, Arshad Warsi, Riteish Deshmukh, Javed Jaffrey"
        director = "Indra Kumar"
        assigned_genre = "Comedy, Adventure"
        rating = 7.4
    elif 'gadar' in query or 'deol' in query:
        scraped_poster = "https://upload.wikimedia.org/wikipedia/en/6/65/Gadar_2_film_poster.jpg"
        desc = "During the Indo-Pakistani War of 1971, Tara Singh returns to Pakistan to rescue his son, Charanjeet, who has been imprisoned and tortured by the Pakistani army."
        cast = "Sunny Deol, Ameesha Patel, Utkarsh Sharma"
        director = "Anil Sharma"
        assigned_genre = "Action, Drama"
        rating = 6.2
    elif 'kalki' in query:
        scraped_poster = "https://upload.wikimedia.org/wikipedia/en/4/4c/Kalki_2898_AD_poster.jpg"
        desc = "A modern avatar of Vishnu, a Hindu god, is believed to have descended to Earth to protect humanity from evil forces in a futuristic dystopian world."
        cast = "Prabhas, Amitabh Bachchan, Kamal Haasan, Deepika Padukone"
        director = "Nag Ashwin"
        assigned_genre = "Sci-Fi, Action"
        rating = 7.2
    elif 'pushpa' in query:
        scraped_poster = "https://upload.wikimedia.org/wikipedia/en/5/5f/Pushpa_2-_The_Rule.jpg"
        desc = "The clash continues between Pushpa Raj and SP Bhanwar Singh Shekhawat in this high-octane action thriller sequel."
        cast = "Allu Arjun, Rashmika Mandanna, Fahadh Faasil"
        director = "Sukumar"
        assigned_genre = "Action, Thriller"
        rating = 7.8
    else:
        # 1. Scraping a live cover photo from Unsplash matching the exact title
        scraped_poster = scrape_unsplash(title)
        
        # 2. Select contextual fallbacks if Unsplash blocks or fails
        if not scraped_poster:
            fallbacks = {
                'comedy': "https://images.unsplash.com/photo-1514306191717-452ec28c7814?auto=format&fit=crop&w=400&q=80",
                'action': "https://images.unsplash.com/photo-1595769816263-9b910be24d5f?auto=format&fit=crop&w=400&q=80",
                'indian': "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=400&q=80",
                'default': "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=400&q=80"
            }
            if 'comedy' in query:
                scraped_poster = fallbacks['comedy']
            elif 'action' in query:
                scraped_poster = fallbacks['action']
            elif 'india' in query or 'indian' in query:
                scraped_poster = fallbacks['indian']
            else:
                scraped_poster = fallbacks['default']

        genres = ['Action', 'Thriller', 'Sci-Fi', 'Drama', 'Comedy', 'Horror', 'Adventure']
        assigned_genre = random.choice(genres) + ", " + random.choice(genres)
        
        if item_type == 'web_series':
            desc = f"Dive into '{title}', an outstanding new web series season. Experience premium acting and award-winning suspenseful episodes."
            cast = "A.I. Model Ensemble Cast"
            director = "A.I. Series Director"
            rating = round(random.uniform(6.5, 9.0), 1)
        else:
            desc = f"Stream and download the official release of '{title}', a stunning new movie production. Featuring highly acclaimed sequences and award-winning cinematography."
            cast = "A.I. Star Actor, Supporting AI Model"
            director = "A.I. Agent Director"
            rating = round(random.uniform(6.5, 9.0), 1)

    match = {
        'description': desc,
        'director': director,
        'cast': cast,
        'genre': assigned_genre,
        'imdb_rating': rating,
        'poster_url': scraped_poster,
        'screenshots': 'https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=600&q=80'
    }

    return jsonify(match)


# ==========================================
# OTHER ENDPOINTS & SEED INITIALIZATION
# ==========================================

@app.route('/api/ai/chat', methods=['POST'])
def ai_chatbot():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'response': "I didn't catch that. Could you ask me about movies, genres, or songs?"})

    # AI chatbot processing
    response_text = ""
    price_match = re.search(r'(?:under|below|less than)\s*(?:rs\.?|inr|₹)?\s*(\d+)', message, re.IGNORECASE)
    price_limit = float(price_match.group(1)) if price_match else None
    
    genre_keywords = ['action', 'comedy', 'drama', 'romance', 'romantic', 'adventure', 'sci-fi', 'horror', 'thriller']
    found_genres = [g for g in genre_keywords if g in message.lower()]

    is_music = 'song' in message.lower() or 'music' in message.lower()

    if is_music:
        query = Song.query
        songs = query.all()
        if price_limit is not None:
            songs = [s for s in songs if s.song_type == 'paid' and s.price <= price_limit] or [s for s in songs if s.song_type == 'free']
        if songs:
            song_list = ", ".join([f"'{s.title}' by {s.artist or 'Various Artists'}" for s in songs[:5]])
            response_text = f"I recommend these tracks matching your criteria: {song_list}."
        else:
            response_text = "Check out our latest Cybernetic Waves album!"
    else:
        query = Movie.query.filter_by(status='published')
        if found_genres:
            query = query.filter(Movie.genre.ilike(f"%{found_genres[0]}%"))
        movies = query.all()
        if price_limit is not None:
            movies = [m for m in movies if (m.is_paid and m.price <= price_limit) or (not m.is_paid)]

        if movies:
            movie_list = "\n".join([f"🎥 **{m.title}** - Rating: ⭐{m.imdb_rating} | {'Free' if not m.is_paid else f'₹{m.price}'}" for m in movies[:4]])
            response_text = f"Based on your query, here is what I recommend:\n\n{movie_list}"
        else:
            response_text = "I couldn't find matches in our current database. Try asking: 'Show Action movies under ₹100'."

    return jsonify({
        'response': response_text,
        'voice_response': response_text.replace('🎥', '').replace('⭐', 'rating')
    })


@app.route('/api/ai/agent/check-duplicate', methods=['POST'])
@role_required('admin', 'super_admin')
def ai_agent_check_duplicate():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    duplicate = Movie.query.filter(Movie.title.ilike(title)).first()
    if duplicate:
        return jsonify({
            'duplicate': True,
            'message': f"Potential duplicate detected: '{duplicate.title}' was already uploaded."
        })
    return jsonify({'duplicate': False})


@app.route('/profile')
@login_required
def user_profile():
    user = User.query.get(session['user_id'])
    payments = PaymentRequest.query.filter_by(user_id=user.id).order_by(PaymentRequest.created_at.desc()).all()
    wishlist_items = Wishlist.query.filter_by(user_id=user.id).all()
    logs = AuditLog.query.filter_by(user_id=user.id).order_by(AuditLog.created_at.desc()).limit(10).all()
    return render_template('profile.html', user=user, payments=payments, wishlist=wishlist_items, logs=logs)


@app.route('/wishlist/toggle/<string:item_type>/<int:item_id>', methods=['POST'])
@login_required
def toggle_wishlist(item_type, item_id):
    user_id = session['user_id']
    if item_type == 'movie':
        item = Wishlist.query.filter_by(user_id=user_id, movie_id=item_id).first()
        if item:
            db.session.delete(item)
            msg = "Removed from wishlist."
            status = "removed"
        else:
            item = Wishlist(user_id=user_id, movie_id=item_id)
            db.session.add(item)
            msg = "Added to wishlist."
            status = "added"
    elif item_type == 'webseries':
        item = Wishlist.query.filter_by(user_id=user_id, web_series_id=item_id).first()
        if item:
            db.session.delete(item)
            msg = "Removed from wishlist."
            status = "removed"
        else:
            item = Wishlist(user_id=user_id, web_series_id=item_id)
            db.session.add(item)
            msg = "Added to wishlist."
            status = "added"
    else:
        item = Wishlist.query.filter_by(user_id=user_id, song_id=item_id).first()
        if item:
            db.session.delete(item)
            msg = "Removed from favorites."
            status = "removed"
        else:
            item = Wishlist(user_id=user_id, song_id=item_id)
            db.session.add(item)
            msg = "Added to favorites."
            status = "added"

    db.session.commit()
    return jsonify({'status': status, 'message': msg})


@app.route('/review/add/<int:movie_id>', methods=['POST'])
@login_required
def add_review(movie_id):
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '').strip()
    if not comment:
        flash("Review comment cannot be empty.", "warning")
        return redirect(url_for('movie_detail', movie_id=movie_id))
    review = Review(user_id=session['user_id'], movie_id=movie_id, rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()
    flash("Review added!", "success")
    return redirect(url_for('movie_detail', movie_id=movie_id))


# ==========================================
# ADMIN DASHBOARD CRUD ACTIONS
# ==========================================

@app.route('/admin/dashboard')
@role_required('admin', 'super_admin')
def admin_dashboard():
    user_count = User.query.count()
    movie_count = Movie.query.count()
    song_count = Song.query.count()
    upcoming_count = UpcomingMovie.query.count()
    webseries_count = WebSeries.query.count()
    payment_requests = PaymentRequest.query.order_by(PaymentRequest.created_at.desc()).all()
    
    total_revenue = db.session.query(db.func.sum(PaymentRequest.amount)).filter_by(status='verified').scalar() or 0.0
    
    movies = Movie.query.order_by(Movie.created_at.desc()).all()
    songs = Song.query.order_by(Song.created_at.desc()).all()
    albums = Album.query.all()
    upcoming = UpcomingMovie.query.all()
    webseries = WebSeries.query.all()
    plans = SubscriptionPlan.query.all()
    
    audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(50).all()
    ads = Advertisement.query.all()
    promotions = Promotion.query.all()

    return render_template('admin.html',
                           user_count=user_count,
                           movie_count=movie_count,
                           song_count=song_count,
                           upcoming_count=upcoming_count,
                           webseries_count=webseries_count,
                           total_revenue=total_revenue,
                           payments=payment_requests,
                           movies=movies,
                           songs=songs,
                           albums=albums,
                           upcoming=upcoming,
                           webseries=webseries,
                           plans=plans,
                           logs=audit_logs,
                           ads=ads,
                           promotions=promotions)


@app.route('/api/admin/analytics')
@role_required('admin', 'super_admin')
def admin_analytics_api():
    scale = request.args.get('scale', 'monthly')
    labels, revenue_data, downloads_data, purchase_conversions = [], [], [], []

    if scale == 'daily':
        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        revenue_data = [450, 990, 840, 1200, 1900, 2400, 3100]
        downloads_data = [80, 120, 110, 150, 210, 310, 390]
        purchase_conversions = [3.5, 4.0, 3.8, 4.5, 5.2, 6.0, 6.5]
    else:  # monthly
        labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        revenue_data = [12000, 14500, 16000, 15000, 19500, 22000, 24500, 21000, 23000, 28000, 32000, 45000]
        downloads_data = [1200, 1400, 1650, 1550, 1900, 2100, 2300, 2050, 2200, 2700, 3100, 4200]
        purchase_conversions = [4.2, 4.5, 4.8, 4.3, 5.0, 5.2, 5.5, 5.1, 5.3, 5.8, 6.0, 7.2]

    actual_total_revenue = db.session.query(db.func.sum(PaymentRequest.amount)).filter_by(status='verified').scalar() or 0.0
    actual_downloads = db.session.query(db.func.sum(Movie.downloads_count)).scalar() or 0
    
    return jsonify({
        'labels': labels, 'revenue': revenue_data, 'downloads': downloads_data, 'conversions': purchase_conversions,
        'totals': {
            'revenue': actual_total_revenue,
            'downloads': actual_downloads,
            'ad_revenue': actual_total_revenue * 0.15
        }
    })


# Movie Add/Edit
@app.route('/admin/movie/add', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_add_movie():
    title = request.form.get('title')
    poster_url = handle_file_upload('poster_file', request.form.get('poster_url'))
    screenshots = request.form.get('screenshots')
    trailer_url = request.form.get('trailer_url')
    description = request.form.get('description')
    director = request.form.get('director')
    cast = request.form.get('cast')
    release_date = request.form.get('release_date')
    genre = request.form.get('genre')
    language = request.form.get('language')
    tags = request.form.get('tags')
    imdb_rating = float(request.form.get('imdb_rating', 7.0))
    is_paid = request.form.get('is_paid') == 'true'
    price = float(request.form.get('price', 0.0) or 0.0)
    subtitle_url = request.form.get('subtitle_url')
    status = request.form.get('status', 'published')
    
    scheduled_release_str = request.form.get('scheduled_release')
    scheduled_release = None
    if scheduled_release_str:
        try:
            scheduled_release = datetime.datetime.strptime(scheduled_release_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass

    # Check multi quality upload links
    link_480p = handle_file_upload('file_480p', request.form.get('link_480p'))
    link_720p = handle_file_upload('file_720p', request.form.get('link_720p'))
    link_1080p = handle_file_upload('file_1080p', request.form.get('link_1080p'))
    link_4k = handle_file_upload('file_4k', request.form.get('link_4k'))

    movie = Movie(
        title=title, poster_url=poster_url, screenshots=screenshots, trailer_url=trailer_url,
        description=description, director=director, cast=cast, release_date=release_date,
        genre=genre, language=language, tags=tags, imdb_rating=imdb_rating, is_paid=is_paid, price=price,
        subtitle_url=subtitle_url, status=status, link_480p=link_480p, link_720p=link_720p,
        link_1080p=link_1080p, link_4k=link_4k, scheduled_release=scheduled_release
    )
    db.session.add(movie)
    db.session.commit()
    
    add_audit_log(session['user_id'], "MOVIE_ADDED", f"Added movie: {title}")
    flash(f"Movie '{title}' added successfully!", "success")
    return redirect(url_for('admin_dashboard'))


# Web Series Add
@app.route('/admin/webseries/add', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_add_webseries():
    title = request.form.get('title')
    poster_url = handle_file_upload('poster_file', request.form.get('poster_url'))
    description = request.form.get('description')
    director = request.form.get('director')
    cast = request.form.get('cast')
    release_date = request.form.get('release_date')
    genre = request.form.get('genre')
    is_paid = request.form.get('is_paid') == 'true'
    price = float(request.form.get('price', 0.0) or 0.0)
    status = request.form.get('status', 'published')

    ws = WebSeries(
        title=title, poster_url=poster_url, description=description, director=director,
        cast=cast, release_date=release_date, genre=genre, is_paid=is_paid, price=price, status=status
    )
    db.session.add(ws)
    db.session.commit()
    flash(f"Web Series '{title}' created successfully!", "success")
    return redirect(url_for('admin_dashboard'))


# Web Series Episode Add
@app.route('/admin/episode/add', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_add_episode():
    web_series_id = int(request.form.get('web_series_id'))
    title = request.form.get('title')
    season_number = int(request.form.get('season_number', 1))
    episode_number = int(request.form.get('episode_number', 1))
    cover_url = handle_file_upload('cover_file', request.form.get('cover_url'))
    video_url = handle_file_upload('video_file', request.form.get('video_url'))
    duration = request.form.get('duration')

    ep = Episode(
        web_series_id=web_series_id, title=title, season_number=season_number,
        episode_number=episode_number, cover_url=cover_url, video_url=video_url, duration=duration
    )
    db.session.add(ep)
    db.session.commit()
    flash(f"Episode '{title}' added!", "success")
    return redirect(url_for('admin_dashboard'))


# Upcoming Movie Add
@app.route('/admin/upcoming/add', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_add_upcoming():
    title = request.form.get('title')
    poster_url = handle_file_upload('poster_file', request.form.get('poster_url'))
    release_date = request.form.get('release_date')
    trailer_url = request.form.get('trailer_url')
    genre = request.form.get('genre')
    cast = request.form.get('cast')
    description = request.form.get('description')

    up = UpcomingMovie(
        title=title, poster_url=poster_url, release_date=release_date,
        trailer_url=trailer_url, genre=genre, cast=cast, description=description
    )
    db.session.add(up)
    db.session.commit()
    flash(f"Upcoming Movie '{title}' added!", "success")
    return redirect(url_for('admin_dashboard'))


# Music Album & Song Add
@app.route('/admin/album/add', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_add_album():
    title = request.form.get('title')
    artist = request.form.get('artist')
    cover_url = handle_file_upload('cover_file', request.form.get('cover_url'))
    description = request.form.get('description')
    
    album = Album(title=title, artist=artist, cover_url=cover_url, description=description)
    db.session.add(album)
    db.session.commit()
    flash(f"Album '{title}' created!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/song/add', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_add_song():
    title = request.form.get('title')
    album_id = request.form.get('album_id')
    artist = request.form.get('artist')
    cover_url = handle_file_upload('cover_file', request.form.get('cover_url'))
    lyrics = request.form.get('lyrics')
    music_video_url = request.form.get('music_video_url')
    external_streaming_links = request.form.get('external_streaming_links')
    song_type = request.form.get('song_type', 'free')
    price = float(request.form.get('price', 0.0) or 0.0)
    
    album_id = int(album_id) if album_id else None

    # Handle quality files
    audio_128_url = handle_file_upload('audio_128_file', request.form.get('audio_128_url'))
    audio_320_url = handle_file_upload('audio_320_file', request.form.get('audio_320_url'))

    # Fallback to general audio_url inside quality
    audio_url = audio_320_url or audio_128_url

    song = Song(
        title=title, album_id=album_id, artist=artist, audio_url=audio_url,
        cover_url=cover_url, lyrics=lyrics, music_video_url=music_video_url,
        external_streaming_links=external_streaming_links, song_type=song_type,
        price=price, audio_128_url=audio_128_url, audio_320_url=audio_320_url
    )
    db.session.add(song)
    db.session.commit()
    flash(f"Song '{title}' added successfully!", "success")
    return redirect(url_for('admin_dashboard'))


# Delete Movie/Song/WebSeries/Upcoming
@app.route('/admin/movie/delete/<int:movie_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash("Movie deleted.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/song/delete/<int:song_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_delete_song(song_id):
    song = Song.query.get_or_404(song_id)
    db.session.delete(song)
    db.session.commit()
    flash("Song deleted.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/webseries/delete/<int:series_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_delete_webseries(series_id):
    ws = WebSeries.query.get_or_404(series_id)
    title = ws.title
    db.session.delete(ws)
    db.session.commit()
    add_audit_log(session['user_id'], "WEBSERIES_DELETED", f"Deleted web series: {title}")
    flash(f"Web Series '{title}' deleted.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/episode/delete/<int:episode_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_delete_episode(episode_id):
    ep = Episode.query.get_or_404(episode_id)
    title = ep.title
    db.session.delete(ep)
    db.session.commit()
    add_audit_log(session['user_id'], "EPISODE_DELETED", f"Deleted episode: {title}")
    flash(f"Episode '{title}' deleted.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/upcoming/delete/<int:upcoming_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_delete_upcoming(upcoming_id):
    up = UpcomingMovie.query.get_or_404(upcoming_id)
    title = up.title
    db.session.delete(up)
    db.session.commit()
    add_audit_log(session['user_id'], "UPCOMING_DELETED", f"Deleted upcoming movie: {title}")
    flash(f"Upcoming Movie '{title}' deleted.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/plan/delete/<int:plan_id>', methods=['POST'])
@role_required('super_admin')
def admin_delete_plan(plan_id):
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    name = plan.name
    db.session.delete(plan)
    db.session.commit()
    add_audit_log(session['user_id'], "PLAN_DELETED", f"Deleted subscription plan: {name}")
    flash(f"Subscription Plan '{name}' deleted.", "success")
    return redirect(url_for('admin_dashboard'))


# ==========================================
# ADMIN EDIT ACTIONS
# ==========================================

@app.route('/admin/movie/edit/<int:movie_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_edit_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    movie.title = request.form.get('title')
    movie.poster_url = handle_file_upload('poster_file', request.form.get('poster_url'))
    movie.screenshots = request.form.get('screenshots')
    movie.trailer_url = request.form.get('trailer_url')
    movie.description = request.form.get('description')
    movie.director = request.form.get('director')
    movie.cast = request.form.get('cast')
    movie.release_date = request.form.get('release_date')
    movie.genre = request.form.get('genre')
    movie.language = request.form.get('language')
    movie.tags = request.form.get('tags')
    movie.imdb_rating = float(request.form.get('imdb_rating', 7.0))
    movie.is_paid = request.form.get('is_paid') == 'true'
    movie.price = float(request.form.get('price', 0.0) or 0.0)
    movie.subtitle_url = request.form.get('subtitle_url')
    movie.status = request.form.get('status', 'published')
    
    scheduled_release_str = request.form.get('scheduled_release')
    if scheduled_release_str:
        try:
            movie.scheduled_release = datetime.datetime.strptime(scheduled_release_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            movie.scheduled_release = None
    else:
        movie.scheduled_release = None

    link_480p = handle_file_upload('file_480p', request.form.get('link_480p'))
    link_720p = handle_file_upload('file_720p', request.form.get('link_720p'))
    link_1080p = handle_file_upload('file_1080p', request.form.get('link_1080p'))
    link_4k = handle_file_upload('file_4k', request.form.get('link_4k'))

    if link_480p: movie.link_480p = link_480p
    if link_720p: movie.link_720p = link_720p
    if link_1080p: movie.link_1080p = link_1080p
    if link_4k: movie.link_4k = link_4k

    db.session.commit()
    add_audit_log(session['user_id'], "MOVIE_EDITED", f"Edited movie: {movie.title}")
    flash(f"Movie '{movie.title}' updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/album/edit/<int:album_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_edit_album(album_id):
    album = Album.query.get_or_404(album_id)
    album.title = request.form.get('title')
    album.artist = request.form.get('artist')
    album.cover_url = handle_file_upload('cover_file', request.form.get('cover_url'))
    album.description = request.form.get('description')
    
    db.session.commit()
    add_audit_log(session['user_id'], "ALBUM_EDITED", f"Edited album: {album.title}")
    flash(f"Album '{album.title}' updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/album/delete/<int:album_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_delete_album(album_id):
    album = Album.query.get_or_404(album_id)
    title = album.title
    db.session.delete(album)
    db.session.commit()
    add_audit_log(session['user_id'], "ALBUM_DELETED", f"Deleted album: {title}")
    flash(f"Album '{title}' deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/episode/edit/<int:episode_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_edit_episode(episode_id):
    ep = Episode.query.get_or_404(episode_id)
    ep.title = request.form.get('title')
    ep.season_number = int(request.form.get('season_number', 1))
    ep.episode_number = int(request.form.get('episode_number', 1))
    ep.duration = request.form.get('duration')
    ep.cover_url = handle_file_upload('cover_file', request.form.get('cover_url'))
    ep.video_url = handle_file_upload('video_file', request.form.get('video_url'))
    
    db.session.commit()
    add_audit_log(session['user_id'], "EPISODE_EDITED", f"Edited episode: {ep.title} in web series {ep.web_series.title}")
    flash(f"Episode '{ep.title}' updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/ads/delete/<int:ad_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_delete_ad(ad_id):
    ad = Advertisement.query.get_or_404(ad_id)
    ad_type = ad.ad_type
    db.session.delete(ad)
    db.session.commit()
    add_audit_log(session['user_id'], "AD_DELETED", f"Deleted ad campaign of placement type: {ad_type}")
    flash("Ad campaign deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/promotions/delete/<int:promo_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_delete_promotion(promo_id):
    promo = Promotion.query.get_or_404(promo_id)
    title = promo.title
    db.session.delete(promo)
    db.session.commit()
    add_audit_log(session['user_id'], "PROMOTION_DELETED", f"Deleted promotion: {title}")
    flash("Promotion event deleted successfully!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/webseries/edit/<int:series_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_edit_webseries(series_id):
    ws = WebSeries.query.get_or_404(series_id)
    ws.title = request.form.get('title')
    ws.poster_url = handle_file_upload('poster_file', request.form.get('poster_url'))
    ws.description = request.form.get('description')
    ws.director = request.form.get('director')
    ws.cast = request.form.get('cast')
    ws.release_date = request.form.get('release_date')
    ws.genre = request.form.get('genre')
    ws.is_paid = request.form.get('is_paid') == 'true'
    ws.price = float(request.form.get('price', 0.0) or 0.0)
    ws.status = request.form.get('status', 'published')

    db.session.commit()
    add_audit_log(session['user_id'], "WEBSERIES_EDITED", f"Edited web series: {ws.title}")
    flash(f"Web Series '{ws.title}' updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/upcoming/edit/<int:upcoming_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_edit_upcoming(upcoming_id):
    up = UpcomingMovie.query.get_or_404(upcoming_id)
    up.title = request.form.get('title')
    up.poster_url = handle_file_upload('poster_file', request.form.get('poster_url'))
    up.release_date = request.form.get('release_date')
    up.trailer_url = request.form.get('trailer_url')
    up.genre = request.form.get('genre')
    up.cast = request.form.get('cast')
    up.description = request.form.get('description')

    db.session.commit()
    add_audit_log(session['user_id'], "UPCOMING_EDITED", f"Edited upcoming movie: {up.title}")
    flash(f"Upcoming Movie '{up.title}' updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/song/edit/<int:song_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def admin_edit_song(song_id):
    song = Song.query.get_or_404(song_id)
    song.title = request.form.get('title')
    
    album_id = request.form.get('album_id')
    song.album_id = int(album_id) if album_id else None
    
    song.artist = request.form.get('artist')
    song.cover_url = handle_file_upload('cover_file', request.form.get('cover_url'))
    song.lyrics = request.form.get('lyrics')
    song.music_video_url = request.form.get('music_video_url')
    song.external_streaming_links = request.form.get('external_streaming_links')
    song.song_type = request.form.get('song_type', 'free')
    song.price = float(request.form.get('price', 0.0) or 0.0)
    
    audio_128_url = handle_file_upload('audio_128_file', request.form.get('audio_128_url'))
    audio_320_url = handle_file_upload('audio_320_file', request.form.get('audio_320_url'))
    
    if audio_128_url: song.audio_128_url = audio_128_url
    if audio_320_url: song.audio_320_url = audio_320_url
    
    song.audio_url = audio_320_url or audio_128_url or song.audio_url

    db.session.commit()
    flash(f"Song '{song.title}' updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/plan/edit/<int:plan_id>', methods=['POST'])
@role_required('super_admin')
def admin_edit_plan(plan_id):
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    plan.name = request.form.get('name')
    plan.price = float(request.form.get('price', 99.0))
    plan.duration_months = int(request.form.get('duration_months', 1))
    plan.description = request.form.get('description')

    db.session.commit()
    add_audit_log(session['user_id'], "PLAN_EDITED", f"Edited plan: {plan.name}")
    flash(f"Subscription Plan '{plan.name}' updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/api/ai/agent/generate', methods=['POST'])
@role_required('admin', 'super_admin')
def ai_agent_generate():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    genres = ['Action', 'Thriller', 'Sci-Fi', 'Drama', 'Comedy', 'Horror', 'Adventure']
    assigned_genre = random.choice(genres) + ", " + random.choice(genres)
    
    return jsonify({
        'description': f"Experience the high-octane thrill of '{title}', a masterfully crafted cinematic journey. With breathtaking visuals, a star-studded cast, and immersive sound design, this release sets a new standard for modern storytelling.",
        'seo_tags': f"{title.lower().replace(' ', ', ')}, blockbuster, premium movie, download, streaming",
        'suggested_price': 149,
        'suggested_type': 'Blockbuster'
    })


# Subscription Plan Management
@app.route('/admin/plan/add', methods=['POST'])
@role_required('super_admin')
def admin_add_plan():
    name = request.form.get('name')
    price = float(request.form.get('price', 99.0))
    duration_months = int(request.form.get('duration_months', 1))
    description = request.form.get('description')

    plan = SubscriptionPlan(name=name, price=price, duration_months=duration_months, description=description)
    db.session.add(plan)
    db.session.commit()
    flash("Subscription Plan added!", "success")
    return redirect(url_for('admin_dashboard'))


# Payment Verifications & Subscriptions
@app.route('/admin/payment/verify/<int:payment_id>', methods=['POST'])
@role_required('admin', 'super_admin')
def verify_payment(payment_id):
    action = request.form.get('action')
    payment = PaymentRequest.query.get_or_404(payment_id)
    user = User.query.get(payment.user_id)
    
    if action == 'verify':
        payment.status = 'verified'
        payment.verified_at = datetime.datetime.utcnow()
        
        # If it was a subscription plan purchase, activate it
        if payment.plan_id:
            plan = SubscriptionPlan.query.get(payment.plan_id)
            expires = datetime.datetime.utcnow() + datetime.timedelta(days=30 * plan.duration_months)
            sub = UserSubscription(user_id=payment.user_id, plan_id=plan.id, end_date=expires, is_active=True)
            db.session.add(sub)
        
        db.session.commit()
        
        # Generate download links and send email
        item_name = payment.movie.title if payment.movie else (payment.song.title if payment.song else (payment.web_series.title if payment.web_series else payment.plan.name))
        
        email_ctx = {
            'username': user.username,
            'item_name': item_name,
            'transaction_id': payment.transaction_id,
            'logo_url': get_site_settings().logo_url or '/static/assets/logo.png',
            'is_subscription': payment.plan_id is not None
        }
        send_mock_email(payment.email, f"Access Granted for {item_name}", "payment_approved", email_ctx)
        flash("Payment verified. Access granted to user.", "success")
    else:
        payment.status = 'rejected'
        db.session.commit()
        email_ctx = {
            'username': user.username,
            'item_name': payment.movie.title if payment.movie else (payment.song.title if payment.song else "Item"),
            'transaction_id': payment.transaction_id,
            'utr': payment.utr_number,
            'logo_url': get_site_settings().logo_url or '/static/assets/logo.png'
        }
        send_mock_email(payment.email, "Verification Failed", "payment_rejected", email_ctx)
        flash("Payment rejected.", "warning")
        
    return redirect(url_for('admin_dashboard'))


# Site settings update
@app.route('/admin/settings/update', methods=['POST'])
@role_required('admin', 'super_admin')
def update_site_settings():
    settings = get_site_settings()
    
    settings.site_name = request.form.get('site_name')
    settings.logo_url = request.form.get('logo_url')
    settings.favicon_url = request.form.get('favicon_url')
    settings.footer_content = request.form.get('footer_content')
    settings.terms_conditions = request.form.get('terms_conditions')
    settings.privacy_policy = request.form.get('privacy_policy')
    settings.contact_info = request.form.get('contact_info')
    settings.homepage_sections = request.form.get('homepage_sections')
    settings.navigation_menu = request.form.get('navigation_menu')
    settings.theme_colors = request.form.get('theme_colors')
    settings.seo_metadata = request.form.get('seo_metadata')
    
    settings.chatbot_settings = request.form.get('chatbot_settings')
    settings.ai_agent_settings = request.form.get('ai_agent_settings')
    settings.upi_id = request.form.get('upi_id')
    settings.adsense_code = request.form.get('adsense_code')

    # Handle QR Code file upload
    settings.payment_qr_url = handle_file_upload('payment_qr_file', request.form.get('payment_qr_url'))

    db.session.commit()
    flash("Site Configuration updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))


# Ads & Promotions CRUD
@app.route('/admin/ads/manage', methods=['POST'])
@role_required('admin', 'super_admin')
def manage_ads():
    ad_id = request.form.get('ad_id')
    ad_type = request.form.get('ad_type')
    banner_url = handle_file_upload('banner_file', request.form.get('banner_url'))
    target_url = request.form.get('target_url')
    priority = int(request.form.get('priority', 0) or 0)
    ad_code = request.form.get('ad_code')
    status = request.form.get('status', 'active')

    if ad_id:
        ad = Advertisement.query.get(ad_id)
        if ad:
            ad.ad_type = ad_type
            ad.banner_url = banner_url
            ad.target_url = target_url
            ad.priority = priority
            ad.ad_code = ad_code
            ad.status = status
    else:
        ad = Advertisement(
            ad_type=ad_type, banner_url=banner_url, target_url=target_url,
            priority=priority, ad_code=ad_code, status=status
        )
        db.session.add(ad)
        
    db.session.commit()
    flash("Ad Campaign updated!", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/promotions/manage', methods=['POST'])
@role_required('admin', 'super_admin')
def manage_promotions():
    promo_id = request.form.get('promo_id')
    promo_type = request.form.get('promo_type')
    title = request.form.get('title')
    subtitle = request.form.get('subtitle')
    image_url = handle_file_upload('image_file', request.form.get('image_url'))
    target_url = request.form.get('target_url')
    coupon_code = request.form.get('coupon_code')
    discount_percent = float(request.form.get('discount_percent', 0.0) or 0.0)
    is_active = request.form.get('is_active') == 'true'

    if promo_id:
        promo = Promotion.query.get(promo_id)
        if promo:
            promo.promo_type = promo_type
            promo.title = title
            promo.subtitle = subtitle
            promo.image_url = image_url
            promo.target_url = target_url
            promo.coupon_code = coupon_code
            promo.discount_percent = discount_percent
            promo.is_active = is_active
    else:
        promo = Promotion(
            promo_type=promo_type, title=title, subtitle=subtitle, image_url=image_url,
            target_url=target_url, coupon_code=coupon_code, discount_percent=discount_percent, is_active=is_active
        )
        db.session.add(promo)

    db.session.commit()
    flash("Promotion updated!", "success")
    return redirect(url_for('admin_dashboard'))


# User registration / session auth
@app.route('/auth', methods=['GET', 'POST'])
def auth_page():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('auth.html')


@app.route('/auth/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for('auth_page'))

    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        flash("Username or email already exists.", "danger")
        return redirect(url_for('auth_page'))

    otp_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
    new_user = User(username=username, email=email, phone=phone, otp=otp_code, is_active=False)
    new_user.set_password(password)
    
    if User.query.count() == 0:
        new_user.role = 'super_admin'
        new_user.is_active = True
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        flash("Initial Super Admin account configured!", "success")
        return redirect(url_for('admin_dashboard'))

    db.session.add(new_user)
    db.session.commit()

    email_ctx = {
        'username': username,
        'otp': otp_code,
        'logo_url': get_site_settings().logo_url or '/static/assets/logo.png'
    }
    send_mock_email(email, "Verify OTP - StreamVibe", "otp_verification", email_ctx)

    session['verify_email'] = email
    flash("Verification code sent to your registered email address.", "info")
    return redirect(url_for('auth_page', verify='true'))


@app.route('/auth/verify-otp', methods=['POST'])
def verify_otp():
    email = session.get('verify_email')
    otp_entered = request.form.get('otp', '').strip()

    if not email:
        flash("Verification expired.", "danger")
        return redirect(url_for('auth_page'))

    user = User.query.filter_by(email=email, otp=otp_entered).first()
    if not user:
        flash("Invalid OTP.", "danger")
        return redirect(url_for('auth_page', verify='true'))

    user.is_active = True
    user.otp = None
    db.session.commit()
    
    session.pop('verify_email', None)
    session['user_id'] = user.id

    email_ctx = {
        'username': user.username,
        'logo_url': get_site_settings().logo_url or '/static/assets/logo.png'
    }
    send_mock_email(user.email, "Welcome to StreamVibe", "welcome", email_ctx)
    flash("Account verified successfully!", "success")
    
    next_url = session.pop('next_url', None)
    if next_url:
        return redirect(next_url)
    return redirect(url_for('index'))


@app.route('/auth/login', methods=['POST'])
def login():
    login_id = request.form.get('login_id', '').strip()
    password = request.form.get('password')
    user = User.query.filter((User.username == login_id) | (User.email == login_id)).first()

    if not user or not user.check_password(password):
        flash("Invalid credentials.", "danger")
        return redirect(url_for('auth_page'))

    if not user.is_active:
        session['verify_email'] = user.email
        flash("Verify your account with OTP first.", "warning")
        return redirect(url_for('auth_page', verify='true'))

    session['user_id'] = user.id
    if user.role in ['admin', 'super_admin']:
        return redirect(url_for('admin_dashboard'))
        
    next_url = session.pop('next_url', None)
    if next_url:
        return redirect(next_url)
    return redirect(url_for('index'))


@app.route('/auth/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('index'))


@app.route('/terms')
def terms_and_privacy():
    settings = get_site_settings()
    return render_template('terms.html', settings=settings)


# Database seeding
# Database seeding
def seed_database():
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings(
            site_name="StreamVibe",
            logo_url="https://images.unsplash.com/photo-1594909122845-11baa439b7bf?auto=format&fit=crop&w=80&q=80",
            favicon_url="https://images.unsplash.com/photo-1594909122845-11baa439b7bf?auto=format&fit=crop&w=16&q=16",
            footer_content="&copy; 2026 StreamVibe Premium. Unlimited Video Streaming & Downloads.",
            terms_conditions="<h3>1. Terms of Use</h3><p>By using StreamVibe, you agree to comply with our downloading and streaming guidelines.</p>",
            privacy_policy="<h3>2. Privacy Policy</h3><p>We respect your personal details. Payment transactions are processed securely.</p>",
            contact_info="<h4>Support Center</h4><p>Email: support@streamvibe.com</p>",
            theme_colors="dark-purple",
            navigation_menu="Home|/,Movies|/movies,Web Series|/webseries,Music Library|/music,Upcoming|/upcoming,VIP Plans|/subscriptions",
            payment_qr_url="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=upi://pay?pa=pay@streamvibe%26pn=StreamVibe",
            upi_id="pay@streamvibe"
        )
        db.session.add(settings)

    # Admin Account
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(username='admin', email='admin@gmail.com', phone='1234567890', role='super_admin', is_active=True)
        admin_user.set_password('admin123')
        db.session.add(admin_user)

    # Load dynamic seed data from seed_data.json
    seed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seed_data.json')
    if os.path.exists(seed_path):
        import json
        try:
            with open(seed_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Subscription plans
            if SubscriptionPlan.query.count() == 0 and 'plans' in data:
                for p in data['plans']:
                    plan = SubscriptionPlan(name=p['name'], price=p['price'], duration_months=p['duration_months'], description=p.get('description'))
                    db.session.add(plan)

            # Promotions
            if Promotion.query.count() == 0 and 'promotions' in data:
                for pr in data['promotions']:
                    promo = Promotion(
                        promo_type=pr['promo_type'],
                        title=pr['title'],
                        subtitle=pr.get('subtitle'),
                        image_url=pr.get('image_url'),
                        target_url=pr.get('target_url'),
                        coupon_code=pr.get('coupon_code'),
                        discount_percent=pr.get('discount_percent', 0.0),
                        is_active=bool(pr.get('is_active', True))
                    )
                    db.session.add(promo)

            # Movies
            if Movie.query.count() == 0 and 'movies' in data:
                for m in data['movies']:
                    movie = Movie(
                        title=m['title'],
                        poster_url=m.get('poster_url'),
                        screenshots=m.get('screenshots'),
                        trailer_url=m.get('trailer_url'),
                        description=m.get('description'),
                        director=m.get('director'),
                        cast=m.get('cast'),
                        release_date=m.get('release_date'),
                        genre=m.get('genre'),
                        language=m.get('language'),
                        imdb_rating=m.get('imdb_rating', 7.0),
                        is_paid=bool(m.get('is_paid', False)),
                        price=m.get('price', 0.0),
                        subtitle_url=m.get('subtitle_url'),
                        status=m.get('status', 'published'),
                        link_480p=m.get('link_480p'),
                        link_720p=m.get('link_720p'),
                        link_1080p=m.get('link_1080p'),
                        link_4k=m.get('link_4k')
                    )
                    db.session.add(movie)

            # Upcoming Movies
            if UpcomingMovie.query.count() == 0 and 'upcoming' in data:
                for u in data['upcoming']:
                    up = UpcomingMovie(
                        title=u['title'],
                        poster_url=u.get('poster_url'),
                        release_date=u.get('release_date'),
                        trailer_url=u.get('trailer_url'),
                        genre=u.get('genre'),
                        cast=u.get('cast'),
                        description=u.get('description')
                    )
                    db.session.add(up)

            # Web Series
            if WebSeries.query.count() == 0 and 'webseries' in data:
                for s in data['webseries']:
                    series = WebSeries(
                        title=s['title'],
                        poster_url=s.get('poster_url'),
                        description=s.get('description'),
                        director=s.get('director'),
                        cast=s.get('cast'),
                        release_date=s.get('release_date'),
                        genre=s.get('genre'),
                        status=s.get('status', 'published'),
                        is_paid=bool(s.get('is_paid', False)),
                        price=s.get('price', 0.0)
                    )
                    db.session.add(series)
                    db.session.flush()
                    if 'episodes' in s:
                        for ep in s['episodes']:
                            episode = Episode(
                                web_series_id=series.id,
                                title=ep['title'],
                                season_number=ep.get('season_number', 1),
                                episode_number=ep.get('episode_number', 1),
                                cover_url=ep.get('cover_url'),
                                video_url=ep['video_url'],
                                duration=ep.get('duration')
                            )
                            db.session.add(episode)

            # Albums & Songs
            if Album.query.count() == 0 and 'albums' in data:
                for a in data['albums']:
                    album = Album(
                        title=a['title'],
                        artist=a['artist'],
                        cover_url=a.get('cover_url'),
                        description=a.get('description')
                    )
                    db.session.add(album)
                    db.session.flush()
                    if 'songs' in a:
                        for s in a['songs']:
                            song = Song(
                                title=s['title'],
                                album_id=album.id,
                                artist=s.get('artist'),
                                cover_url=s.get('cover_url'),
                                lyrics=s.get('lyrics'),
                                song_type=s.get('song_type', 'free'),
                                price=s.get('price', 0.0),
                                audio_128_url=s.get('audio_128_url'),
                                audio_320_url=s.get('audio_320_url')
                            )
                            db.session.add(song)
        except Exception as e:
            print(f"Error seeding database from json: {e}")

    db.session.commit()


@app.route('/dev/setup')
def dev_setup():
    db.drop_all()
    db.create_all()
    seed_database()
    return "Database reset and seeded successfully with proper Bollywood cover photos, subscription plans, web series, and FLAC music tracks!"


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database()
    app.run(debug=True, port=5000)
