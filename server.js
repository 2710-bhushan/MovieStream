require('dotenv').config();
const express = require('express');
const session = require('express-session');
const nunjucks = require('nunjucks');
const path = require('path');
const fs = require('fs');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const fileUpload = require('express-fileupload');
const db = require('./db');

const app = express();
const PORT = process.env.PORT || 5000;

// Setup Middlewares
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(fileUpload({ createParentPath: true }));

// Setup Session
app.use(session({
    secret: process.env.SECRET_KEY || 'antigravity_secret_key_129847391',
    resave: false,
    saveUninitialized: true,
    cookie: { maxAge: 24 * 60 * 60 * 1000 } // 24 hours
}));

// Setup Static assets routing
app.use('/static', express.static(path.join(__dirname, 'static')));
app.use('/staticcss', express.static(path.join(__dirname, 'staticcss')));
app.use('/svg', express.static(path.join(__dirname, 'svg')));

// Setup Nunjucks Templating
const env = nunjucks.configure('templates', {
    autoescape: true,
    express: app,
    noCache: true
});

// Custom Nunjucks Filters & Globals
env.addGlobal('url_for', (endpoint, kwargs = {}) => {
    if (endpoint === 'static') {
        return '/' + kwargs.filename;
    }
    const routes = {
        'index': '/',
        'movies': '/movies',
        'music': '/music',
        'webseries': '/webseries',
        'upcoming': '/upcoming',
        'subscriptions': '/subscriptions',
        'profile': '/profile',
        'auth_page': '/auth',
        'terms': '/terms',
        'dev_setup': '/dev/setup',
        'admin_dashboard': '/admin/dashboard',
        'logout': '/auth/logout'
    };
    if (routes[endpoint]) {
        return routes[endpoint];
    }
    if (endpoint === 'movie_detail') {
        return `/movie/${kwargs.movie_id}`;
    }
    if (endpoint === 'webseries_detail') {
        return `/webseries/${kwargs.series_id}`;
    }
    if (endpoint === 'checkout') {
        return `/checkout/${kwargs.item_type}/${kwargs.item_id}`;
    }
    return '#';
});

// Helper functions for template views
env.addFilter('default', (val, defVal) => {
    return val !== undefined && val !== null && val !== '' ? val : defVal;
});

env.addFilter('slice_limit', (arr, limit) => {
    return arr ? arr.slice(0, limit) : [];
});

// Context Processor Middleware to inject global data
app.use(async (req, res, next) => {
    // Setup flash messages
    req.session.flashMessages = req.session.flashMessages || [];
    res.locals.get_flashed_messages = (options = {}) => {
        if (req.session.flashMessages.length === 0) {
            return null;
        }
        const msgs = req.session.flashMessages.map(m => [m.category, m.message]);
        req.session.flashMessages = [];
        return msgs;
    };
    req.flash = (message, category = 'info') => {
        req.session.flashMessages.push({ message, category });
    };

    try {
        const settings = await db.dbGet('SELECT * FROM site_settings LIMIT 1') || {};
        const ads = await db.dbAll("SELECT * FROM advertisement WHERE status = 'active' ORDER BY priority DESC");
        
        const nav_links = [];
        if (settings.navigation_menu) {
            settings.navigation_menu.split(',').forEach(item => {
                if (item.includes('|')) {
                    const parts = item.split('|');
                    nav_links.push({ title: parts[0].trim(), url: parts[1].trim() });
                }
            });
        }
        
        const seo = {};
        if (settings.seo_metadata) {
            settings.seo_metadata.split(';').forEach(tag => {
                if (tag.includes('=')) {
                    const parts = tag.split('=');
                    seo[parts[0].trim()] = parts[1].trim();
                }
            });
        }
        
        const banner_promos = await db.dbAll("SELECT * FROM promotion WHERE promo_type = 'homepage_banner' AND is_active = 1");
        const flash_sales = await db.dbAll("SELECT * FROM promotion WHERE promo_type = 'flash_sale' AND is_active = 1");
        
        let current_user = null;
        let user_subscribed = false;
        if (req.session.user_id) {
            current_user = await db.dbGet('SELECT * FROM user WHERE id = ?', [req.session.user_id]);
            if (current_user) {
                const sub = await db.dbGet('SELECT * FROM user_subscription WHERE user_id = ? AND is_active = 1 LIMIT 1', [current_user.id]);
                if (sub) {
                    const now = new Date();
                    const endDate = new Date(sub.end_date);
                    if (endDate > now) {
                        user_subscribed = true;
                    } else {
                        await db.dbRun('UPDATE user_subscription SET is_active = 0 WHERE id = ?', [sub.id]);
                    }
                }
            }
        }
        
        res.locals.settings = settings;
        res.locals.ads = ads;
        res.locals.nav_links = nav_links;
        res.locals.theme = settings.theme_colors || 'dark-purple';
        res.locals.seo = seo;
        res.locals.banner_promos = banner_promos;
        res.locals.flash_sales = flash_sales;
        res.locals.current_user = current_user;
        res.locals.user_subscribed = user_subscribed;
        res.locals.session = req.session;
    } catch (err) {
        console.error("Global context load error:", err);
    }
    next();
});

// Middleware Helpers
const loginRequired = (req, res, next) => {
    if (!req.session.user_id) {
        req.flash('Please log in to access this page.', 'warning');
        req.session.next_url = req.path;
        return res.redirect('/auth');
    }
    next();
};

const roleRequired = (...roles) => {
    return async (req, res, next) => {
        if (!req.session.user_id) {
            req.flash('Please log in.', 'warning');
            return res.redirect('/auth');
        }
        const user = await db.dbGet('SELECT * FROM user WHERE id = ?', [req.session.user_id]);
        if (!user || !roles.includes(user.role)) {
            req.flash('Access denied. Insufficient permissions.', 'danger');
            return res.redirect('/');
        }
        req.user = user;
        next();
    };
};

async function addAuditLog(userId, action, details = "", req = null) {
    try {
        let username = "Anonymous";
        if (userId) {
            const user = await db.dbGet('SELECT username FROM user WHERE id = ?', [userId]);
            if (user) username = user.username;
        }
        const ip = req ? (req.headers['x-forwarded-for'] || req.socket.remoteAddress) : '127.0.0.1';
        await db.dbRun(`
            INSERT INTO audit_log (user_id, username, action, ip_address, details)
            VALUES (?, ?, ?, ?, ?)
        `, [userId, username, action, ip, details]);
    } catch (e) {
        console.error("Error logging audit:", e);
    }
}

// Mail Dispatcher emulated with nodemailer and file logger
const sendMockEmail = async (toEmail, subject, templateName, context) => {
    console.log(`\n[EMAIL DISPATCHER] To: ${toEmail} | Subject: ${subject}`);
    
    const smtpHost = process.env.EMAIL_HOST || 'smtp.gmail.com';
    const smtpPort = parseInt(process.env.EMAIL_PORT || '587');
    const smtpUser = process.env.EMAIL_HOST_USER || 'bhushan.272006@gmail.com';
    const smtpPass = process.env.EMAIL_HOST_PASSWORD || 'gpkh pcco zwmw dyxp';
    const fromEmail = process.env.DEFAULT_FROM_EMAIL || 'ServiceHub <bhushan.272006@gmail.com>';

    let htmlBody = '';
    try {
        htmlBody = nunjucks.render(`emails/${templateName}.html`, context);
    } catch (err) {
        console.error(`[EMAIL ERROR] Failed to render template ${templateName}:`, err);
    }

    try {
        const transporter = require('nodemailer').createTransport({
            host: smtpHost,
            port: smtpPort,
            secure: smtpPort === 465,
            auth: {
                user: smtpUser,
                pass: smtpPass
            }
        });

        await transporter.sendMail({
            from: fromEmail,
            to: toEmail,
            subject: subject,
            html: htmlBody
        });
        console.log("[EMAIL DISPATCHER] Success! Email sent successfully via SMTP.");
    } catch (e) {
        console.error(`[EMAIL ERROR] Failed to send SMTP: ${e.message}. Saving copy locally.`);
    }

    // Save copy locally for review
    try {
        const emailLogDir = path.join(__dirname, '.gemini_email_logs');
        fs.mkdirSync(emailLogDir, { recursive: true });
        const safeSubject = subject.replace(/[^a-zA-Z0-9]/g, '_');
        const filename = `${new Date().toISOString().replace(/[:.]/g, '-')}_${safeSubject}.html`;
        fs.writeFileSync(path.join(emailLogDir, filename), htmlBody, 'utf-8');
    } catch (ex) {
        console.error(`[EMAIL ERROR] Failed saving file backup:`, ex);
    }
};

const handleFileUpload = (req, fieldName, defaultUrl) => {
    if (req.files && req.files[fieldName]) {
        const file = req.files[fieldName];
        const ext = path.extname(file.name);
        const safeName = file.name.replace(/[^a-zA-Z0-9]/g, '_');
        const uniqueName = `${Math.random().toString(36).substring(2, 10)}_${safeName}${ext}`;
        const uploadPath = path.join(__dirname, 'static', 'uploads', uniqueName);
        
        fs.mkdirSync(path.dirname(uploadPath), { recursive: true });
        file.mv(uploadPath);
        return `/static/uploads/${uniqueName}`;
    }
    return defaultUrl;
};

// ==========================================
// FRONTEND ROUTES
// ==========================================

// Homepage
app.get('/', async (req, res) => {
    try {
        const featured = await db.dbAll("SELECT * FROM movie WHERE status = 'featured'");
        const trending = await db.dbAll("SELECT * FROM movie WHERE status = 'trending'");
        const movies_free = await db.dbAll("SELECT * FROM movie WHERE is_paid = 0 AND status = 'published' LIMIT 6");
        const movies_paid = await db.dbAll("SELECT * FROM movie WHERE is_paid = 1 AND status = 'published' LIMIT 6");
        const albums = await db.dbAll("SELECT * FROM album LIMIT 4");
        const songs_free = await db.dbAll("SELECT * FROM song WHERE song_type = 'free' LIMIT 5");
        const web_series = await db.dbAll("SELECT * FROM web_series WHERE status = 'published' LIMIT 4");
        const upcoming = await db.dbAll("SELECT * FROM upcoming_movie ORDER BY release_date ASC LIMIT 4");
        const plans = await db.dbAll("SELECT * FROM subscription_plan");
        const promo_banners = await db.dbAll("SELECT * FROM promotion WHERE promo_type = 'homepage_banner' AND is_active = 1");
        const flash_sales = await db.dbAll("SELECT * FROM promotion WHERE promo_type = 'flash_sale' AND is_active = 1");
        const adsense_top = await db.dbGet("SELECT * FROM advertisement WHERE ad_type = 'google_adsense' AND status = 'active' LIMIT 1");

        res.render('home.html', {
            featured,
            trending,
            movies_free,
            movies_paid,
            albums,
            songs_free,
            web_series,
            upcoming,
            plans,
            promo_banners,
            flash_sales,
            adsense_top
        });
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// All Movies
app.get('/movies', async (req, res) => {
    try {
        const queryParam = req.query.q || '';
        const genreParam = req.query.genre || '';
        const langParam = req.query.language || '';
        const priceParam = req.query.price || '';

        let sql = "SELECT * FROM movie WHERE status = 'published'";
        const params = [];

        if (queryParam) {
            sql += " AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)";
            const p = `%${queryParam}%`;
            params.push(p, p, p);
        }
        if (genreParam) {
            sql += " AND genre LIKE ?";
            params.push(`%${genreParam}%`);
        }
        if (langParam) {
            sql += " AND language LIKE ?";
            params.push(`%${langParam}%`);
        }
        if (priceParam === 'free') {
            sql += " AND is_paid = 0";
        } else if (priceParam === 'paid') {
            sql += " AND is_paid = 1";
        }

        const movies = await db.dbAll(sql, params);
        res.render('movies.html', { movies, q: queryParam, genre: genreParam, language: langParam, price: priceParam });
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// Movie Details
app.get('/movie/:id', async (req, res) => {
    try {
        const movie = await db.dbGet("SELECT * FROM movie WHERE id = ?", [req.params.id]);
        if (!movie) return res.status(404).send("Movie Not Found");

        // Increment views
        await db.dbRun("UPDATE movie SET views = views + 1 WHERE id = ?", [movie.id]);

        // Get reviews
        const reviews = await db.dbAll(`
            SELECT r.*, u.username 
            FROM review r
            JOIN user u ON r.user_id = u.id
            WHERE r.movie_id = ?
            ORDER BY r.created_at DESC
        `, [movie.id]);

        // Related movies
        const related = await db.dbAll("SELECT * FROM movie WHERE id != ? AND genre LIKE ? LIMIT 4", [movie.id, `%${movie.genre.split(',')[0]}%`]);

        res.render('movie_detail.html', { movie, reviews, related });
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// All Web Series
app.get('/webseries', async (req, res) => {
    try {
        const series = await db.dbAll("SELECT * FROM web_series WHERE status = 'published'");
        res.render('webseries.html', { series });
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// Web Series Details
app.get('/webseries/:id', async (req, res) => {
    try {
        const series = await db.dbGet("SELECT * FROM web_series WHERE id = ?", [req.params.id]);
        if (!series) return res.status(404).send("Web Series Not Found");

        // Increment views
        await db.dbRun("UPDATE web_series SET views = views + 1 WHERE id = ?", [series.id]);

        const episodes = await db.dbAll("SELECT * FROM episode WHERE web_series_id = ? ORDER BY season_number ASC, episode_number ASC", [series.id]);

        res.render('webseries_detail.html', { series, episodes });
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// Watch Episode
app.get('/webseries/episode/:id', loginRequired, async (req, res) => {
    try {
        const episode = await db.dbGet("SELECT * FROM episode WHERE id = ?", [req.params.id]);
        if (!episode) return res.status(404).send("Episode Not Found");

        const series = await db.dbGet("SELECT * FROM web_series WHERE id = ?", [episode.web_series_id]);

        // Check if premium/paid and if user has access
        let isAuthorized = true;
        if (series.is_paid) {
            isAuthorized = false;
            if (res.locals.user_subscribed) {
                isAuthorized = true;
            } else {
                const purchase = await db.dbGet("SELECT * FROM payment_request WHERE user_id = ? AND web_series_id = ? AND status = 'verified'", [req.session.user_id, series.id]);
                if (purchase) isAuthorized = true;
            }
        }

        if (!isAuthorized) {
            req.flash("Access Denied. Please purchase this web series or get a membership subscription to watch this episode.", "danger");
            return res.redirect(`/checkout/webseries/${series.id}`);
        }

        res.render('episode_watch.html', { episode, series });
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// Upcoming Releases
app.get('/upcoming', async (req, res) => {
    try {
        const upcoming = await db.dbAll("SELECT * FROM upcoming_movie ORDER BY release_date ASC");
        res.render('upcoming.html', { upcoming });
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// Music Library
app.get('/music', async (req, res) => {
    try {
        const queryParam = req.query.q || '';
        let songsSql = "SELECT s.*, a.title as album_title FROM song s LEFT JOIN album a ON s.album_id = a.id";
        const params = [];
        if (queryParam) {
            songsSql += " WHERE s.title LIKE ? OR s.artist LIKE ? OR s.lyrics LIKE ?";
            const p = `%${queryParam}%`;
            params.push(p, p, p);
        }
        const songs = await db.dbAll(songsSql, params);
        const albums = await db.dbAll("SELECT * FROM album");
        res.render('music.html', { songs, albums, q: queryParam });
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// Subscriptions VIP plans
app.get('/subscriptions', async (req, res) => {
    try {
        const plans = await db.dbAll("SELECT * FROM subscription_plan");
        res.render('subscriptions.html', { plans });
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// Checkout screen
app.get('/checkout/:item_type/:item_id', loginRequired, async (req, res) => {
    try {
        const { item_type, item_id } = req.params;
        let item = null;
        if (item_type === 'movie') {
            item = await db.dbGet("SELECT * FROM movie WHERE id = ?", [item_id]);
        } else if (item_type === 'song') {
            item = await db.dbGet("SELECT * FROM song WHERE id = ?", [item_id]);
        } else if (item_type === 'webseries') {
            item = await db.dbGet("SELECT * FROM web_series WHERE id = ?", [item_id]);
        } else if (item_type === 'plan') {
            item = await db.dbGet("SELECT * FROM subscription_plan WHERE id = ?", [item_id]);
        }

        if (!item) return res.status(404).send("Item Not Found");

        const settings = res.locals.settings;
        res.render('purchase.html', { item, item_type, item_id, settings });
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// Process Purchase Checkout Form Submission
app.post('/checkout/:item_type/:item_id', loginRequired, async (req, res) => {
    try {
        const { item_type, item_id } = req.params;
        const { name, email, phone, utr_number, amount } = req.body;

        if (!name || !email || !phone || !utr_number) {
            req.flash("All fields are required.", "danger");
            return res.redirect(req.originalUrl);
        }

        if (utr_number.length !== 12 || isNaN(utr_number)) {
            req.flash("UTR Number must be exactly 12 digits.", "danger");
            return res.redirect(req.originalUrl);
        }

        const transactionId = `TXN-${Math.random().toString(36).substring(2, 10).toUpperCase()}`;

        // Verify duplicate UTR
        const checkUtr = await db.dbGet("SELECT * FROM payment_request WHERE utr_number = ?", [utr_number]);
        if (checkUtr) {
            req.flash("This UTR number has already been submitted for verification.", "warning");
            return res.redirect(req.originalUrl);
        }

        let movie_id = null, song_id = null, web_series_id = null, plan_id = null;
        if (item_type === 'movie') movie_id = item_id;
        else if (item_type === 'song') song_id = item_id;
        else if (item_type === 'webseries') web_series_id = item_id;
        else if (item_type === 'plan') plan_id = item_id;

        await db.dbRun(`
            INSERT INTO payment_request (
                user_id, name, email, phone, utr_number, amount, transaction_id, status,
                movie_id, song_id, web_series_id, plan_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `, [
            req.session.user_id, name, email, phone, utr_number, parseFloat(amount),
            transactionId, 'pending', movie_id, song_id, web_series_id, plan_id
        ]);

        await addAuditLog(req.session.user_id, "PURCHASE_REQUEST", `Submitted UTR ${utr_number} for verification`, req);

        // Send Purchase Confirmation Mock email
        await sendMockEmail(email, "Payment Request Submitted - StreamVibe", "purchase_received", {
            name,
            utr_number,
            amount,
            transaction_id: transactionId
        });

        req.flash("Payment request submitted successfully! Pending verification by Admin.", "success");
        return res.redirect('/profile');
    } catch (err) {
        console.error(err);
        req.flash("An error occurred during submission. Please try again.", "danger");
        res.redirect(req.originalUrl);
    }
});

// Download landing request page
app.get('/download/request/:item_type/:item_id', loginRequired, async (req, res) => {
    try {
        const { item_type, item_id } = req.params;
        const user = await db.dbGet("SELECT * FROM user WHERE id = ?", [req.session.user_id]);

        let movie = null, song = null;
        let isAuthorized = false;

        if (item_type === 'movie') {
            movie = await db.dbGet("SELECT * FROM movie WHERE id = ?", [item_id]);
            if (!movie) return res.status(404).send("Movie Not Found");
            if (!movie.is_paid || res.locals.user_subscribed) {
                isAuthorized = true;
            } else {
                const purchase = await db.dbGet("SELECT * FROM payment_request WHERE user_id = ? AND movie_id = ? AND status = 'verified'", [user.id, movie.id]);
                if (purchase) isAuthorized = true;
            }
        } else {
            song = await db.dbGet("SELECT * FROM song WHERE id = ?", [item_id]);
            if (!song) return res.status(404).send("Song Not Found");
            if (song.song_type === 'free' || res.locals.user_subscribed) {
                isAuthorized = true;
            } else {
                const purchase = await db.dbGet("SELECT * FROM payment_request WHERE user_id = ? AND song_id = ? AND status = 'verified'", [user.id, song.id]);
                if (purchase) isAuthorized = true;
            }
        }

        if (!isAuthorized) {
            req.flash("Access Denied. Please purchase this item or get a membership subscription.", "danger");
            return res.redirect(`/checkout/${item_type}/${item_id}`);
        }

        const tokenStr = `DL-${Math.random().toString(36).substring(2, 15).toUpperCase()}`;
        const expires = new Date();
        expires.setHours(expires.getHours() + 24); // Expires in 24 hours

        await db.dbRun(`
            INSERT INTO secure_download_token (token, user_id, movie_id, song_id, expires_at, max_downloads)
            VALUES (?, ?, ?, ?, ?, ?)
        `, [
            tokenStr, user.id,
            movie ? movie.id : null,
            song ? song.id : null,
            expires.toISOString().replace('T', ' ').substring(0, 19), 3
        ]);

        return res.redirect(`/download/link/${tokenStr}?quality=${req.query.quality || ''}`);
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// Download Link execution
app.get('/download/link/:token', async (req, res) => {
    try {
        const dl_token = await db.dbGet("SELECT * FROM secure_download_token WHERE token = ?", [req.params.token]);
        if (!dl_token) return res.status(404).send("Invalid download link.");

        const now = new Date();
        const expiresAt = new Date(dl_token.expires_at);
        if (expiresAt < now) {
            return res.status(410).send("This download link has expired (24h limit reached).");
        }
        if (dl_token.downloads_count >= dl_token.max_downloads) {
            return res.status(403).send("Link download limit exceeded.");
        }

        await db.dbRun("UPDATE secure_download_token SET downloads_count = downloads_count + 1 WHERE id = ?", [dl_token.id]);

        let title = '';
        let file_url = '';
        const quality = req.query.quality || '';

        if (dl_token.movie_id) {
            const movie = await db.dbGet("SELECT * FROM movie WHERE id = ?", [dl_token.movie_id]);
            await db.dbRun("UPDATE movie SET downloads_count = downloads_count + 1 WHERE id = ?", [movie.id]);
            title = movie.title;

            if (quality === '480p') {
                file_url = movie.link_480p || movie.link_720p || movie.link_1080p || movie.link_4k || "https://www.w3schools.com/html/mov_bbb.mp4";
            } else if (quality === '720p') {
                file_url = movie.link_720p || movie.link_1080p || movie.link_4k || movie.link_480p || "https://www.w3schools.com/html/mov_bbb.mp4";
            } else if (quality === '1080p') {
                file_url = movie.link_1080p || movie.link_720p || movie.link_4k || movie.link_480p || "https://www.w3schools.com/html/mov_bbb.mp4";
            } else if (quality === '4k') {
                file_url = movie.link_4k || movie.link_1080p || movie.link_720p || movie.link_480p || "https://www.w3schools.com/html/mov_bbb.mp4";
            } else {
                file_url = movie.link_1080p || movie.link_720p || movie.link_480p || movie.link_4k || "https://www.w3schools.com/html/mov_bbb.mp4";
            }
            if (quality) title = `${title} [${quality.toUpperCase()}]`;
        } else {
            const song = await db.dbGet("SELECT * FROM song WHERE id = ?", [dl_token.song_id]);
            await db.dbRun("UPDATE song SET downloads_count = downloads_count + 1 WHERE id = ?", [song.id]);
            title = song.title;
            file_url = song.audio_320_url || song.audio_128_url || "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3";
        }

        await addAuditLog(dl_token.user_id, "DOWNLOAD_EXECUTED", `Downloaded ${title}`, req);
        
        res.render('download_landing.html', { file_url, title, dl_token });
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// Profile page
app.get('/profile', loginRequired, async (req, res) => {
    try {
        const user = await db.dbGet("SELECT * FROM user WHERE id = ?", [req.session.user_id]);
        
        const payments = await db.dbAll(`
            SELECT p.*, 
                   m.title as movie_title, 
                   s.title as song_title, 
                   w.title as series_title,
                   sp.name as plan_name
            FROM payment_request p
            LEFT JOIN movie m ON p.movie_id = m.id
            LEFT JOIN song s ON p.song_id = s.id
            LEFT JOIN web_series w ON p.web_series_id = w.id
            LEFT JOIN subscription_plan sp ON p.plan_id = sp.id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC
        `, [user.id]);

        const wishlist = await db.dbAll(`
            SELECT w.id as wishlist_id, 
                   m.title as movie_title, m.poster_url as movie_poster, m.id as movie_id,
                   s.title as song_title, s.cover_url as song_cover, s.id as song_id,
                   ws.title as series_title, ws.poster_url as series_poster, ws.id as series_id
            FROM wishlist w
            LEFT JOIN movie m ON w.movie_id = m.id
            LEFT JOIN song s ON w.song_id = s.id
            LEFT JOIN web_series ws ON w.web_series_id = ws.id
            WHERE w.user_id = ?
            ORDER BY w.created_at DESC
        `, [user.id]);

        res.render('profile.html', { user, payments, wishlist });
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// Wishlist toggle endpoint
app.post('/wishlist/toggle/:item_type/:item_id', loginRequired, async (req, res) => {
    try {
        const { item_type, item_id } = req.params;
        const userId = req.session.user_id;

        let sql = "SELECT * FROM wishlist WHERE user_id = ?";
        let params = [userId];

        if (item_type === 'movie') {
            sql += " AND movie_id = ?";
            params.push(item_id);
        } else if (item_type === 'song') {
            sql += " AND song_id = ?";
            params.push(item_id);
        } else if (item_type === 'webseries') {
            sql += " AND web_series_id = ?";
            params.push(item_id);
        }

        const existing = await db.dbGet(sql, params);
        if (existing) {
            await db.dbRun("DELETE FROM wishlist WHERE id = ?", [existing.id]);
            return res.json({ status: 'removed' });
        } else {
            await db.dbRun(`
                INSERT INTO wishlist (user_id, movie_id, song_id, web_series_id)
                VALUES (?, ?, ?, ?)
            `, [
                userId,
                item_type === 'movie' ? item_id : null,
                item_type === 'song' ? item_id : null,
                item_type === 'webseries' ? item_id : null
            ]);
            return res.json({ status: 'added' });
        }
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Server Error' });
    }
});

// Add review
app.post('/review/add/:movie_id', loginRequired, async (req, res) => {
    try {
        const { rating, comment } = req.body;
        await db.dbRun(`
            INSERT INTO review (user_id, movie_id, rating, comment)
            VALUES (?, ?, ?, ?)
        `, [req.session.user_id, req.params.movie_id, parseInt(rating || 5), comment || '']);

        req.flash("Review submitted!", "success");
        res.redirect(`/movie/${req.params.movie_id}`);
    } catch (err) {
        console.error(err);
        res.status(500).send("Internal Server Error");
    }
});

// Terms & Privacy Page
app.get('/terms', (req, res) => {
    res.render('terms.html');
});

// ==========================================
// AI & AGENT API ENDPOINTS
// ==========================================

// AI Scraper Helper
async function scrapeUnsplash(query) {
    try {
        const headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        };
        const encoded = encodeURIComponent(query);
        const r = await fetch(`https://unsplash.com/s/photos/${encoded}`, { headers, signal: AbortSignal.timeout(5000) });
        if (r.ok) {
            const html = await r.text();
            const regex = /https:\/\/images\.unsplash\.com\/photo-[a-zA-Z0-9\-]+/g;
            const matches = html.match(regex);
            if (matches && matches.length > 0) {
                return `${matches[0]}?auto=format&fit=crop&w=400&q=80`;
            }
        }
    } catch (e) {
        console.error("Scraper error:", e);
    }
    return null;
}

// AI Metadata Fetch endpoint
app.post('/api/metadata/fetch', roleRequired('admin', 'super_admin'), async (req, res) => {
    const title = (req.body.title || '').trim();
    const itemType = req.body.type || 'movie';

    if (!title) return res.status(400).json({ error: 'Title is required' });

    const query = title.toLowerCase();
    let poster = '';
    let desc = '';
    let cast = '';
    let director = '';
    let genre = '';
    let rating = 7.0;

    if (query.includes('dhamaal')) {
        poster = "https://upload.wikimedia.org/wikipedia/en/a/a2/Dhamaal_film_poster.jpg";
        desc = "Four lazy, good-for-nothing friends find out about a hidden treasure in Goa from a dying thief. They embark on a race to find the treasure before a determined police inspector.";
        cast = "Sanjay Dutt, Arshad Warsi, Riteish Deshmukh, Javed Jaffrey";
        director = "Indra Kumar";
        genre = "Comedy, Adventure";
        rating = 7.4;
    } else if (query.includes('gadar') || query.includes('deol')) {
        poster = "https://upload.wikimedia.org/wikipedia/en/6/65/Gadar_2_film_poster.jpg";
        desc = "During the Indo-Pakistani War of 1971, Tara Singh returns to Pakistan to rescue his son, Charanjeet, who has been imprisoned and tortured by the Pakistani army.";
        cast = "Sunny Deol, Ameesha Patel, Utkarsh Sharma";
        director = "Anil Sharma";
        genre = "Action, Drama";
        rating = 6.2;
    } else if (query.includes('kalki')) {
        poster = "https://upload.wikimedia.org/wikipedia/en/4/4c/Kalki_2898_AD_poster.jpg";
        desc = "A modern avatar of Vishnu, a Hindu god, is believed to have descended to Earth to protect humanity from evil forces in a futuristic dystopian world.";
        cast = "Prabhas, Amitabh Bachchan, Kamal Haasan, Deepika Padukone";
        director = "Nag Ashwin";
        genre = "Sci-Fi, Action";
        rating = 7.2;
    } else if (query.includes('pushpa')) {
        poster = "https://upload.wikimedia.org/wikipedia/en/5/5f/Pushpa_2-_The_Rule.jpg";
        desc = "The clash continues between Pushpa Raj and SP Bhanwar Singh Shekhawat in this high-octane action thriller sequel.";
        cast = "Allu Arjun, Rashmika Mandanna, Fahadh Faasil";
        director = "Sukumar";
        genre = "Action, Thriller";
        rating = 7.8;
    } else {
        poster = await scrapeUnsplash(title);
        if (!poster) {
            const fallbacks = {
                comedy: "https://images.unsplash.com/photo-1514306191717-452ec28c7814?auto=format&fit=crop&w=400&q=80",
                action: "https://images.unsplash.com/photo-1595769816263-9b910be24d5f?auto=format&fit=crop&w=400&q=80",
                indian: "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=400&q=80",
                default: "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=400&q=80"
            };
            if (query.includes('comedy')) poster = fallbacks.comedy;
            else if (query.includes('action')) poster = fallbacks.action;
            else if (query.includes('india') || query.includes('indian')) poster = fallbacks.indian;
            else poster = fallbacks.default;
        }

        const genres = ['Action', 'Thriller', 'Sci-Fi', 'Drama', 'Comedy', 'Horror', 'Adventure'];
        genre = `${genres[Math.floor(Math.random() * genres.length)]}, ${genres[Math.floor(Math.random() * genres.length)]}`;
        
        rating = parseFloat((Math.random() * 2.5 + 6.5).toFixed(1));
        if (itemType === 'web_series') {
            desc = `Dive into '${title}', an outstanding new web series season. Experience premium acting and award-winning suspenseful episodes.`;
            cast = "A.I. Model Ensemble Cast";
            director = "A.I. Series Director";
        } else {
            desc = `Stream and download the official release of '${title}', a stunning new movie production. Featuring highly acclaimed sequences and award-winning cinematography.`;
            cast = "A.I. Star Actor, Supporting AI Model";
            director = "A.I. Agent Director";
        }
    }

    res.json({
        description: desc,
        director,
        cast,
        genre,
        imdb_rating: rating,
        poster_url: poster,
        screenshots: 'https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=600&q=80'
    });
});

// AI Chatbot endpoint
app.post('/api/ai/chat', async (req, res) => {
    const message = (req.body.message || '').trim();
    if (!message) {
        return res.json({ response: "I didn't catch that. Could you ask me about movies, genres, or songs?" });
    }

    let responseText = '';
    const priceMatch = message.match(/(?:under|below|less than)\s*(?:rs\.?|inr|₹)?\s*(\d+)/i);
    const priceLimit = priceMatch ? parseFloat(priceMatch[1]) : null;

    const genreKeywords = ['action', 'comedy', 'drama', 'romance', 'romantic', 'adventure', 'sci-fi', 'horror', 'thriller'];
    const foundGenres = genreKeywords.filter(g => message.toLowerCase().includes(g));

    const isMusic = message.toLowerCase().includes('song') || message.toLowerCase().includes('music');

    if (isMusic) {
        let songs = await db.dbAll("SELECT * FROM song");
        if (priceLimit !== null) {
            songs = songs.filter(s => (s.song_type === 'paid' && s.price <= priceLimit) || s.song_type === 'free');
        }
        if (songs.length > 0) {
            const list = songs.slice(0, 5).map(s => `'${s.title}' by ${s.artist || 'Various Artists'}`).join(', ');
            responseText = `I recommend these tracks matching your criteria: ${list}.`;
        } else {
            responseText = "Check out our latest Cybernetic Waves album!";
        }
    } else {
        let sql = "SELECT * FROM movie WHERE status = 'published'";
        const params = [];
        if (foundGenres.length > 0) {
            sql += " AND genre LIKE ?";
            params.push(`%${foundGenres[0]}%`);
        }
        let movies = await db.dbAll(sql, params);
        if (priceLimit !== null) {
            movies = movies.filter(m => (m.is_paid && m.price <= priceLimit) || !m.is_paid);
        }
        if (movies.length > 0) {
            const list = movies.slice(0, 4).map(m => `🎥 **${m.title}** - Rating: ⭐${m.imdb_rating} | ${!m.is_paid ? 'Free' : `₹${m.price}`}`).join('\n');
            responseText = `Based on your query, here is what I recommend:\n\n${list}`;
        } else {
            responseText = "I couldn't find matches in our current database. Try asking: 'Show Action movies under ₹100'.";
        }
    }

    res.json({
        response: responseText,
        voice_response: responseText.replace(/🎥/g, '').replace(/⭐/g, 'rating')
    });
});

// AI Agent check duplicate
app.post('/api/ai/agent/check-duplicate', roleRequired('admin', 'super_admin'), async (req, res) => {
    const title = (req.body.title || '').trim();
    if (!title) return res.status(400).json({ error: 'Title is required' });

    const movie = await db.dbGet("SELECT * FROM movie WHERE title LIKE ?", [`%${title}%`]);
    const series = await db.dbGet("SELECT * FROM web_series WHERE title LIKE ?", [`%${title}%`]);

    if (movie || series) {
        return res.json({
            duplicate: true,
            message: `Warning: Content matching '${title}' was found in the database. Continuing might result in a duplicate entry.`
        });
    }
    res.json({ duplicate: false });
});

// AI Agent generate suggestion
app.post('/api/ai/agent/generate', roleRequired('admin', 'super_admin'), (req, res) => {
    const title = (req.body.title || '').trim();
    if (!title) return res.status(400).json({ error: 'Title is required' });

    const genres = ['Action', 'Thriller', 'Sci-Fi', 'Drama', 'Comedy', 'Horror', 'Adventure'];
    const assigned = `${genres[Math.floor(Math.random() * genres.length)]}, ${genres[Math.floor(Math.random() * genres.length)]}`;

    res.json({
        description: `Experience the high-octane thrill of '${title}', a masterfully crafted cinematic journey. Breathtaking visuals, an amazing cast, and immersive sound design make this release a new standard in modern storytelling.`,
        seo_tags: `${title.toLowerCase().replace(/ /g, ', ')}, blockbuster, premium movie, download, streaming`,
        suggested_price: 149,
        suggested_type: 'Blockbuster'
    });
});

// ==========================================
// AUTHENTICATION ROUTES
// ==========================================

app.get('/auth', (req, res) => {
    res.render('auth.html');
});

app.post('/auth/register', async (req, res) => {
    const { username, email, password, phone } = req.body;
    if (!username || !email || !password) {
        req.flash('All fields are required.', 'danger');
        return res.redirect('/auth');
    }

    try {
        const existUser = await db.dbGet("SELECT * FROM user WHERE username = ? OR email = ?", [username, email]);
        if (existUser) {
            req.flash('Username or Email already registered.', 'warning');
            return res.redirect('/auth');
        }

        const otp = Math.floor(100000 + Math.random() * 900000).toString();
        const hash = await bcrypt.hash(password, 10);

        // Store registration info temporarily in session
        req.session.pendingReg = {
            username,
            email,
            phone,
            password_hash: hash,
            otp
        };

        // Send OTP via SMTP
        await sendMockEmail(email, "Verify Your OTP - StreamVibe", "otp_verification", {
            username,
            otp
        });

        req.flash("An OTP has been sent to your email. Please verify to complete registration.", "success");
        return res.render('loginlist.html', { email }); // Render the OTP verification page
    } catch (e) {
        console.error(e);
        req.flash("An error occurred. Please try again.", "danger");
        res.redirect('/auth');
    }
});

app.post('/auth/verify-otp', async (req, res) => {
    const { otp } = req.body;
    const pending = req.session.pendingReg;

    if (!pending) {
        req.flash("Session expired. Please register again.", "danger");
        return res.redirect('/auth');
    }

    if (otp !== pending.otp) {
        req.flash("Invalid OTP code. Please try again.", "danger");
        return res.render('loginlist.html', { email: pending.email });
    }

    try {
        await db.dbRun(`
            INSERT INTO user (username, email, password_hash, phone, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        `, [pending.username, pending.email, pending.password_hash, pending.phone || '', 'user', 1]);

        const newUser = await db.dbGet("SELECT * FROM user WHERE username = ?", [pending.username]);
        
        // Remove pending credentials
        delete req.session.pendingReg;

        // Welcome Email
        await sendMockEmail(newUser.email, "Welcome to StreamVibe Premium!", "welcome", {
            username: newUser.username
        });

        req.session.user_id = newUser.id;
        req.session.role = newUser.role;
        req.session.username = newUser.username;

        await addAuditLog(newUser.id, "USER_REGISTERED", "Registered and verified via OTP", req);

        req.flash("Account verified successfully! Welcome to StreamVibe.", "success");
        return res.redirect('/');
    } catch (err) {
        console.error(err);
        req.flash("Verification failed.", "danger");
        res.redirect('/auth');
    }
});

app.post('/auth/login', async (req, res) => {
    const { email, password } = req.body;
    if (!email || !password) {
        req.flash("Please enter both email/username and password.", "warning");
        return res.redirect('/auth');
    }

    try {
        const user = await db.dbGet("SELECT * FROM user WHERE email = ? OR username = ?", [email, email]);
        if (!user || !(await bcrypt.compare(password, user.password_hash))) {
            req.flash("Invalid credentials.", "danger");
            return res.redirect('/auth');
        }

        if (!user.is_active) {
            req.flash("This account is suspended.", "danger");
            return res.redirect('/auth');
        }

        req.session.user_id = user.id;
        req.session.role = user.role;
        req.session.username = user.username;

        await addAuditLog(user.id, "USER_LOGGED_IN", "Logged in successfully", req);

        req.flash(`Welcome back, ${user.username}!`, "success");
        
        const nextUrl = req.session.next_url || '/';
        delete req.session.next_url;
        res.redirect(nextUrl);
    } catch (err) {
        console.error(err);
        req.flash("Login failed.", "danger");
        res.redirect('/auth');
    }
});

app.get('/auth/logout', (req, res) => {
    if (req.session.user_id) {
        addAuditLog(req.session.user_id, "USER_LOGGED_OUT", "Logged out successfully", req);
    }
    req.session.destroy(() => {
        res.redirect('/');
    });
});

// ==========================================
// ADMIN ACTIONS & CRUD ENDPOINTS
// ==========================================

// Admin Dashboard page
app.get('/admin/dashboard', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const userCount = (await db.dbGet("SELECT COUNT(*) as count FROM user")).count;
        const movieCount = (await db.dbGet("SELECT COUNT(*) as count FROM movie")).count;
        const songCount = (await db.dbGet("SELECT COUNT(*) as count FROM song")).count;
        const upcomingCount = (await db.dbGet("SELECT COUNT(*) as count FROM upcoming_movie")).count;
        const webseriesCount = (await db.dbGet("SELECT COUNT(*) as count FROM web_series")).count;

        const rawRevenue = await db.dbGet("SELECT SUM(amount) as total FROM payment_request WHERE status = 'verified'");
        const total_revenue = rawRevenue ? (rawRevenue.total || 0.0) : 0.0;

        const payments = await db.dbAll("SELECT * FROM payment_request ORDER BY created_at DESC");
        const movies = await db.dbAll("SELECT * FROM movie ORDER BY created_at DESC");
        const songs = await db.dbAll("SELECT * FROM song ORDER BY created_at DESC");
        const albums = await db.dbAll("SELECT * FROM album");
        const upcoming = await db.dbAll("SELECT * FROM upcoming_movie");
        const webseries = await db.dbAll("SELECT * FROM web_series");
        const plans = await db.dbAll("SELECT * FROM subscription_plan");
        const logs = await db.dbAll("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 50");
        const ads = await db.dbAll("SELECT * FROM advertisement");
        const promotions = await db.dbAll("SELECT * FROM promotion");

        res.render('admin.html', {
            user_count: userCount,
            movie_count: movieCount,
            song_count: songCount,
            upcoming_count: upcomingCount,
            webseries_count: webseriesCount,
            total_revenue,
            payments,
            movies,
            songs,
            albums,
            upcoming,
            webseries,
            plans,
            logs,
            ads,
            promotions
        });
    } catch (err) {
        console.error(err);
        res.status(500).send("Admin load error");
    }
});

// Admin Analytics API
app.get('/api/admin/analytics', roleRequired('admin', 'super_admin'), async (req, res) => {
    const scale = req.query.scale || 'monthly';
    let labels, revenue_data, downloads_data, purchase_conversions;

    if (scale === 'daily') {
        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
        revenue_data = [450, 990, 840, 1200, 1900, 2400, 3100];
        downloads_data = [80, 120, 110, 150, 210, 310, 390];
        purchase_conversions = [3.5, 4.0, 3.8, 4.5, 5.2, 6.0, 6.5];
    } else {
        labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        revenue_data = [12000, 14500, 16000, 15000, 19500, 22000, 24500, 21000, 23000, 28000, 32000, 45000];
        downloads_data = [1200, 1400, 1650, 1550, 1900, 2100, 2300, 2050, 2200, 2700, 3100, 4200];
        purchase_conversions = [4.2, 4.5, 4.8, 4.3, 5.0, 5.2, 5.5, 5.1, 5.3, 5.8, 6.0, 7.2];
    }

    const actualRevenue = (await db.dbGet("SELECT SUM(amount) as sum FROM payment_request WHERE status='verified'")).sum || 0;
    const actualDownloads = (await db.dbGet("SELECT SUM(downloads_count) as sum FROM movie")).sum || 0;

    res.json({
        labels, revenue: revenue_data, downloads: downloads_data, conversions: purchase_conversions,
        totals: {
            revenue: actualRevenue,
            downloads: actualDownloads
        }
    });
});

// Movie CRUD
app.post('/admin/movie/add', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const posterUrl = handleFileUpload(req, 'poster_file', req.body.poster_url || '');
        const screenshotsUrl = handleFileUpload(req, 'screenshot_file', req.body.screenshots || '');

        await db.dbRun(`
            INSERT INTO movie (
                title, poster_url, screenshots, trailer_url, description, director, cast,
                release_date, genre, language, imdb_rating, is_paid, price, subtitle_url,
                status, link_480p, link_720p, link_1080p, link_4k
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `, [
            req.body.title, posterUrl, screenshotsUrl, req.body.trailer_url, req.body.description,
            req.body.director, req.body.cast, req.body.release_date, req.body.genre, req.body.language,
            parseFloat(req.body.imdb_rating || 7.0), req.body.is_paid === 'true' ? 1 : 0,
            parseFloat(req.body.price || 0.0), req.body.subtitle_url, req.body.status || 'published',
            req.body.link_480p, req.body.link_720p, req.body.link_1080p, req.body.link_4k
        ]);

        await addAuditLog(req.session.user_id, "MOVIE_ADDED", `Added movie: ${req.body.title}`, req);
        req.flash("Movie added successfully!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        req.flash("Failed to add movie.", "danger");
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/movie/edit/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const posterUrl = handleFileUpload(req, 'poster_file', req.body.poster_url || '');
        const screenshotsUrl = handleFileUpload(req, 'screenshot_file', req.body.screenshots || '');

        await db.dbRun(`
            UPDATE movie SET 
                title=?, poster_url=?, screenshots=?, trailer_url=?, description=?, director=?, cast=?,
                release_date=?, genre=?, language=?, imdb_rating=?, is_paid=?, price=?, subtitle_url=?,
                status=?, link_480p=?, link_720p=?, link_1080p=?, link_4k=?
            WHERE id=?
        `, [
            req.body.title, posterUrl, screenshotsUrl, req.body.trailer_url, req.body.description,
            req.body.director, req.body.cast, req.body.release_date, req.body.genre, req.body.language,
            parseFloat(req.body.imdb_rating || 7.0), req.body.is_paid === 'true' ? 1 : 0,
            parseFloat(req.body.price || 0.0), req.body.subtitle_url, req.body.status || 'published',
            req.body.link_480p, req.body.link_720p, req.body.link_1080p, req.body.link_4k,
            req.params.id
        ]);

        await addAuditLog(req.session.user_id, "MOVIE_EDITED", `Edited movie: ${req.body.title}`, req);
        req.flash("Movie updated successfully!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        req.flash("Failed to edit movie.", "danger");
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/movie/delete/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const movie = await db.dbGet("SELECT title FROM movie WHERE id = ?", [req.params.id]);
        await db.dbRun("DELETE FROM movie WHERE id = ?", [req.params.id]);
        await addAuditLog(req.session.user_id, "MOVIE_DELETED", `Deleted movie: ${movie ? movie.title : req.params.id}`, req);
        req.flash("Movie deleted.", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

// Web Series CRUD
app.post('/admin/webseries/add', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const posterUrl = handleFileUpload(req, 'poster_file', req.body.poster_url || '');
        await db.dbRun(`
            INSERT INTO web_series (title, poster_url, description, director, cast, release_date, genre, status, is_paid, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `, [
            req.body.title, posterUrl, req.body.description, req.body.director, req.body.cast,
            req.body.release_date, req.body.genre, req.body.status || 'published',
            req.body.is_paid === 'true' ? 1 : 0, parseFloat(req.body.price || 0.0)
        ]);

        await addAuditLog(req.session.user_id, "WEBSERIES_ADDED", `Added Web Series: ${req.body.title}`, req);
        req.flash("Web Series added successfully!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/webseries/edit/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const posterUrl = handleFileUpload(req, 'poster_file', req.body.poster_url || '');
        await db.dbRun(`
            UPDATE web_series SET 
                title=?, poster_url=?, description=?, director=?, cast=?, release_date=?, genre=?, status=?, is_paid=?, price=?
            WHERE id=?
        `, [
            req.body.title, posterUrl, req.body.description, req.body.director, req.body.cast,
            req.body.release_date, req.body.genre, req.body.status || 'published',
            req.body.is_paid === 'true' ? 1 : 0, parseFloat(req.body.price || 0.0),
            req.params.id
        ]);

        await addAuditLog(req.session.user_id, "WEBSERIES_EDITED", `Edited Web Series: ${req.body.title}`, req);
        req.flash("Web Series updated successfully!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/webseries/delete/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const ws = await db.dbGet("SELECT title FROM web_series WHERE id = ?", [req.params.id]);
        await db.dbRun("DELETE FROM web_series WHERE id = ?", [req.params.id]);
        await addAuditLog(req.session.user_id, "WEBSERIES_DELETED", `Deleted series: ${ws ? ws.title : req.params.id}`, req);
        req.flash("Web Series deleted.", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

// Episode CRUD
app.post('/admin/episode/add', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const coverUrl = handleFileUpload(req, 'cover_file', req.body.cover_url || '');
        await db.dbRun(`
            INSERT INTO episode (web_series_id, title, season_number, episode_number, cover_url, video_url, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        `, [
            parseInt(req.body.web_series_id), req.body.title, parseInt(req.body.season_number || 1),
            parseInt(req.body.episode_number || 1), coverUrl, req.body.video_url, req.body.duration || ''
        ]);

        req.flash("Episode added!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/episode/edit/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const coverUrl = handleFileUpload(req, 'cover_file', req.body.cover_url || '');
        await db.dbRun(`
            UPDATE episode SET 
                web_series_id=?, title=?, season_number=?, episode_number=?, cover_url=?, video_url=?, duration=?
            WHERE id=?
        `, [
            parseInt(req.body.web_series_id), req.body.title, parseInt(req.body.season_number || 1),
            parseInt(req.body.episode_number || 1), coverUrl, req.body.video_url, req.body.duration || '',
            req.params.id
        ]);

        req.flash("Episode updated successfully!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/episode/delete/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        await db.dbRun("DELETE FROM episode WHERE id = ?", [req.params.id]);
        req.flash("Episode deleted.", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

// Upcoming CRUD
app.post('/admin/upcoming/add', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const posterUrl = handleFileUpload(req, 'poster_file', req.body.poster_url || '');
        await db.dbRun(`
            INSERT INTO upcoming_movie (title, poster_url, release_date, trailer_url, genre, cast, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        `, [
            req.body.title, posterUrl, req.body.release_date, req.body.trailer_url,
            req.body.genre, req.body.cast, req.body.description
        ]);

        req.flash("Upcoming content added!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/upcoming/edit/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const posterUrl = handleFileUpload(req, 'poster_file', req.body.poster_url || '');
        await db.dbRun(`
            UPDATE upcoming_movie SET 
                title=?, poster_url=?, release_date=?, trailer_url=?, genre=?, cast=?, description=?
            WHERE id=?
        `, [
            req.body.title, posterUrl, req.body.release_date, req.body.trailer_url,
            req.body.genre, req.body.cast, req.body.description, req.params.id
        ]);

        req.flash("Upcoming content updated!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/upcoming/delete/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        await db.dbRun("DELETE FROM upcoming_movie WHERE id = ?", [req.params.id]);
        req.flash("Upcoming movie deleted.", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

// Album CRUD
app.post('/admin/album/add', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const coverUrl = handleFileUpload(req, 'cover_file', req.body.cover_url || '');
        await db.dbRun(`
            INSERT INTO album (title, artist, cover_url, description)
            VALUES (?, ?, ?, ?)
        `, [req.body.title, req.body.artist, coverUrl, req.body.description]);

        req.flash("Music Album added!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/album/edit/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const coverUrl = handleFileUpload(req, 'cover_file', req.body.cover_url || '');
        await db.dbRun(`
            UPDATE album SET title=?, artist=?, cover_url=?, description=? WHERE id=?
        `, [req.body.title, req.body.artist, coverUrl, req.body.description, req.params.id]);

        req.flash("Album updated successfully!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/album/delete/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        await db.dbRun("DELETE FROM album WHERE id = ?", [req.params.id]);
        req.flash("Album deleted.", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

// Song CRUD
app.post('/admin/song/add', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const coverUrl = handleFileUpload(req, 'cover_file', req.body.cover_url || '');
        const audio128Url = handleFileUpload(req, 'audio_128_file', req.body.audio_128_url || '');
        const audio320Url = handleFileUpload(req, 'audio_320_file', req.body.audio_320_url || '');

        await db.dbRun(`
            INSERT INTO song (
                title, album_id, artist, cover_url, lyrics, music_video_url,
                external_streaming_links, song_type, price, audio_128_url, audio_320_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `, [
            req.body.title, req.body.album_id ? parseInt(req.body.album_id) : null, req.body.artist,
            coverUrl, req.body.lyrics, req.body.music_video_url, req.body.external_streaming_links,
            req.body.song_type || 'free', parseFloat(req.body.price || 0.0), audio128Url, audio320Url
        ]);

        req.flash("Song track added successfully!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/song/edit/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const coverUrl = handleFileUpload(req, 'cover_file', req.body.cover_url || '');
        const audio128Url = handleFileUpload(req, 'audio_128_file', req.body.audio_128_url || '');
        const audio320Url = handleFileUpload(req, 'audio_320_file', req.body.audio_320_url || '');

        await db.dbRun(`
            UPDATE song SET 
                title=?, album_id=?, artist=?, cover_url=?, lyrics=?, music_video_url=?,
                external_streaming_links=?, song_type=?, price=?, audio_128_url=?, audio_320_url=?
            WHERE id=?
        `, [
            req.body.title, req.body.album_id ? parseInt(req.body.album_id) : null, req.body.artist,
            coverUrl, req.body.lyrics, req.body.music_video_url, req.body.external_streaming_links,
            req.body.song_type || 'free', parseFloat(req.body.price || 0.0), audio128Url, audio320Url,
            req.params.id
        ]);

        req.flash("Song updated successfully!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/song/delete/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        await db.dbRun("DELETE FROM song WHERE id = ?", [req.params.id]);
        req.flash("Song track deleted.", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

// VIP Plan CRUD
app.post('/admin/plan/add', roleRequired('super_admin'), async (req, res) => {
    try {
        await db.dbRun(`
            INSERT INTO subscription_plan (name, price, duration_months, description)
            VALUES (?, ?, ?, ?)
        `, [req.body.name, parseFloat(req.body.price || 99.0), parseInt(req.body.duration_months || 1), req.body.description]);

        req.flash("Subscription Plan added!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/plan/edit/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        await db.dbRun(`
            UPDATE subscription_plan SET name=?, price=?, duration_months=?, description=? WHERE id=?
        `, [req.body.name, parseFloat(req.body.price || 99.0), parseInt(req.body.duration_months || 1), req.body.description, req.params.id]);

        await addAuditLog(req.session.user_id, "PLAN_EDITED", `Edited plan: ${req.body.name}`, req);
        req.flash(`Subscription Plan '${req.body.name}' updated successfully!`, "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/plan/delete/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        await db.dbRun("DELETE FROM subscription_plan WHERE id = ?", [req.params.id]);
        req.flash("Subscription Plan deleted.", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

// Verify Payments
app.post('/admin/payment/verify/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    const status = req.body.status; // verified or rejected
    
    try {
        const payment = await db.dbGet("SELECT * FROM payment_request WHERE id = ?", [req.params.id]);
        if (!payment) return res.status(404).send("Payment Request Not Found");

        const verifiedAt = new Date().toISOString().replace('T', ' ').substring(0, 19);

        await db.dbRun(`
            UPDATE payment_request 
            SET status = ?, verified_at = ? 
            WHERE id = ?
        `, [status, verifiedAt, payment.id]);

        const user = await db.dbGet("SELECT * FROM user WHERE id = ?", [payment.user_id]);

        if (status === 'verified') {
            // Apply Plan Subscription
            if (payment.plan_id) {
                const plan = await db.dbGet("SELECT * FROM subscription_plan WHERE id = ?", [payment.plan_id]);
                const startDate = new Date();
                const endDate = new Date();
                endDate.setMonth(endDate.getMonth() + plan.duration_months);

                await db.dbRun(`
                    INSERT INTO user_subscription (user_id, plan_id, start_date, end_date, is_active)
                    VALUES (?, ?, ?, ?, 1)
                `, [
                    payment.user_id, plan.id,
                    startDate.toISOString().replace('T', ' ').substring(0, 19),
                    endDate.toISOString().replace('T', ' ').substring(0, 19)
                ]);
            }

            // Send verification approved email
            await sendMockEmail(payment.email, "Payment Verified & Approved - StreamVibe", "payment_approved", {
                name: payment.name,
                utr_number: payment.utr_number,
                amount: payment.amount,
                transaction_id: payment.transaction_id
            });

            await addAuditLog(req.session.user_id, "PAYMENT_VERIFIED", `Approved payment request: UTR ${payment.utr_number} for user ${user.username}`, req);
            req.flash("Payment Request has been Verified & Approved!", "success");
        } else {
            // Send rejected email
            await sendMockEmail(payment.email, "Payment Rejected - StreamVibe", "payment_rejected", {
                name: payment.name,
                utr_number: payment.utr_number,
                amount: payment.amount,
                transaction_id: payment.transaction_id
            });

            await addAuditLog(req.session.user_id, "PAYMENT_REJECTED", `Rejected payment request: UTR ${payment.utr_number} for user ${user.username}`, req);
            req.flash("Payment Request has been Rejected.", "warning");
        }

        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

// Update Settings
app.post('/admin/settings/update', roleRequired('super_admin'), async (req, res) => {
    try {
        const logoUrl = handleFileUpload(req, 'logo_file', req.body.logo_url || '');
        const faviconUrl = handleFileUpload(req, 'favicon_file', req.body.favicon_url || '');
        const qrUrl = handleFileUpload(req, 'qr_file', req.body.payment_qr_url || '');

        const existing = await db.dbGet("SELECT id FROM site_settings LIMIT 1");
        if (existing) {
            await db.dbRun(`
                UPDATE site_settings SET 
                    site_name=?, footer_content=?, terms_conditions=?, privacy_policy=?, contact_info=?,
                    homepage_sections=?, navigation_menu=?, theme_colors=?, seo_metadata=?,
                    chatbot_settings=?, ai_agent_settings=?, upi_id=?, adsense_code=?,
                    logo_url=?, favicon_url=?, payment_qr_url=?
                WHERE id=?
            `, [
                req.body.site_name, req.body.footer_content, req.body.terms_conditions, req.body.privacy_policy,
                req.body.contact_info, req.body.homepage_sections, req.body.navigation_menu, req.body.theme_colors,
                req.body.seo_metadata, req.body.chatbot_settings, req.body.ai_agent_settings, req.body.upi_id,
                req.body.adsense_code, logoUrl, faviconUrl, qrUrl, existing.id
            ]);
        } else {
            await db.dbRun(`
                INSERT INTO site_settings (
                    site_name, footer_content, terms_conditions, privacy_policy, contact_info,
                    homepage_sections, navigation_menu, theme_colors, seo_metadata,
                    chatbot_settings, ai_agent_settings, upi_id, adsense_code,
                    logo_url, favicon_url, payment_qr_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            `, [
                req.body.site_name, req.body.footer_content, req.body.terms_conditions, req.body.privacy_policy,
                req.body.contact_info, req.body.homepage_sections, req.body.navigation_menu, req.body.theme_colors,
                req.body.seo_metadata, req.body.chatbot_settings, req.body.ai_agent_settings, req.body.upi_id,
                req.body.adsense_code, logoUrl, faviconUrl, qrUrl
            ]);
        }

        await addAuditLog(req.session.user_id, "SETTINGS_UPDATED", "Updated global site settings", req);
        req.flash("Site settings updated successfully!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

// Ads Actions
app.post('/admin/ads/manage', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const bannerUrl = handleFileUpload(req, 'banner_file', req.body.banner_url || '');
        await db.dbRun(`
            INSERT INTO advertisement (ad_type, banner_url, target_url, display_duration, priority, ad_code, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        `, [
            req.body.ad_type, bannerUrl, req.body.target_url, parseInt(req.body.display_duration || 10),
            parseInt(req.body.priority || 0), req.body.ad_code || '', req.body.status || 'active'
        ]);

        req.flash("Ad unit saved!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/ads/delete/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        await db.dbRun("DELETE FROM advertisement WHERE id = ?", [req.params.id]);
        req.flash("Ad unit deleted.", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

// Promotions Actions
app.post('/admin/promotions/manage', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        const imageUrl = handleFileUpload(req, 'image_file', req.body.image_url || '');
        await db.dbRun(`
            INSERT INTO promotion (promo_type, title, subtitle, image_url, target_url, coupon_code, discount_percent, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `, [
            req.body.promo_type, req.body.title, req.body.subtitle, imageUrl, req.body.target_url,
            req.body.coupon_code || '', parseFloat(req.body.discount_percent || 0.0),
            req.body.is_active === 'true' ? 1 : 0
        ]);

        req.flash("Promotion campaign saved!", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

app.post('/admin/promotions/delete/:id', roleRequired('admin', 'super_admin'), async (req, res) => {
    try {
        await db.dbRun("DELETE FROM promotion WHERE id = ?", [req.params.id]);
        req.flash("Promotion deleted.", "success");
        res.redirect('/admin/dashboard');
    } catch (err) {
        console.error(err);
        res.redirect('/admin/dashboard');
    }
});

// ==========================================
// SEED AND DEVELOPMENT PATHS
// ==========================================

app.get('/dev/setup', async (req, res) => {
    try {
        await db.resetDatabase();
        res.send("Database reset and seeded successfully with proper Bollywood cover photos, subscription plans, web series, and FLAC music tracks!");
    } catch (err) {
        console.error(err);
        res.status(500).send("Database Setup Failed: " + err.message);
    }
});

// Start Server
db.initializeSchema().then(() => {
    db.seedDatabase().then(() => {
        app.listen(PORT, () => {
            console.log(`[SERVER] Express Server is running on port ${PORT}`);
            console.log(`[URL] Live at http://localhost:${PORT}`);
        });
    });
});
