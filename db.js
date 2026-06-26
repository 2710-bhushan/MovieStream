const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');
const bcrypt = require('bcryptjs');

const dbDir = path.join(__dirname, 'instance');
if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
}
const dbPath = path.join(dbDir, 'platform_v2.db');
const db = new sqlite3.Database(dbPath);

// Helper methods returning Promises
function dbRun(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function(err) {
            if (err) return reject(err);
            resolve(this); // this includes lastID and changes
        });
    });
}

function dbGet(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

function dbAll(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) return reject(err);
            resolve(rows);
        });
    });
}

// Database tables initialization schema
async function initializeSchema() {
    await dbRun(`
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            phone VARCHAR(20),
            role VARCHAR(20) DEFAULT 'user',
            otp VARCHAR(6),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS movie (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            poster_url VARCHAR(500),
            screenshots TEXT,
            trailer_url VARCHAR(500),
            description TEXT,
            director VARCHAR(100),
            cast VARCHAR(300),
            release_date VARCHAR(50),
            genre VARCHAR(100),
            language VARCHAR(100),
            tags VARCHAR(200),
            imdb_rating FLOAT DEFAULT 7.0,
            is_paid BOOLEAN DEFAULT 0,
            price FLOAT DEFAULT 0.0,
            subtitle_url VARCHAR(500),
            status VARCHAR(20) DEFAULT 'published',
            views INTEGER DEFAULT 0,
            downloads_count INTEGER DEFAULT 0,
            scheduled_release DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            link_480p VARCHAR(500),
            link_720p VARCHAR(500),
            link_1080p VARCHAR(500),
            link_4k VARCHAR(500)
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS upcoming_movie (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            poster_url VARCHAR(500),
            release_date VARCHAR(50),
            trailer_url VARCHAR(500),
            genre VARCHAR(100),
            cast VARCHAR(300),
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS web_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            poster_url VARCHAR(500),
            description TEXT,
            director VARCHAR(100),
            cast VARCHAR(300),
            release_date VARCHAR(50),
            genre VARCHAR(100),
            status VARCHAR(20) DEFAULT 'published',
            views INTEGER DEFAULT 0,
            is_paid BOOLEAN DEFAULT 0,
            price FLOAT DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS episode (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            web_series_id INTEGER NOT NULL,
            title VARCHAR(200) NOT NULL,
            season_number INTEGER DEFAULT 1,
            episode_number INTEGER DEFAULT 1,
            cover_url VARCHAR(500),
            video_url VARCHAR(500) NOT NULL,
            duration VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(web_series_id) REFERENCES web_series(id) ON DELETE CASCADE
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS album (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            artist VARCHAR(150) NOT NULL,
            cover_url VARCHAR(500),
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS song (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            album_id INTEGER,
            artist VARCHAR(150),
            cover_url VARCHAR(500),
            lyrics TEXT,
            music_video_url VARCHAR(500),
            external_streaming_links TEXT,
            song_type VARCHAR(20) DEFAULT 'free',
            price FLOAT DEFAULT 0.0,
            downloads_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            audio_128_url VARCHAR(500),
            audio_320_url VARCHAR(500),
            FOREIGN KEY(album_id) REFERENCES album(id) ON DELETE SET NULL
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS subscription_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            price FLOAT NOT NULL,
            duration_months INTEGER DEFAULT 1,
            description TEXT
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS user_subscription (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            end_date DATETIME NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE,
            FOREIGN KEY(plan_id) REFERENCES subscription_plan(id) ON DELETE CASCADE
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS payment_request (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(120) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            utr_number VARCHAR(12) NOT NULL UNIQUE,
            movie_id INTEGER,
            song_id INTEGER,
            web_series_id INTEGER,
            plan_id INTEGER,
            amount FLOAT NOT NULL,
            transaction_id VARCHAR(50) NOT NULL UNIQUE,
            status VARCHAR(20) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            verified_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(movie_id) REFERENCES movie(id),
            FOREIGN KEY(song_id) REFERENCES song(id),
            FOREIGN KEY(web_series_id) REFERENCES web_series(id),
            FOREIGN KEY(plan_id) REFERENCES subscription_plan(id)
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS advertisement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_type VARCHAR(50) NOT NULL,
            banner_url VARCHAR(500),
            target_url VARCHAR(500),
            display_duration INTEGER DEFAULT 10,
            priority INTEGER DEFAULT 0,
            ad_code TEXT,
            status VARCHAR(20) DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS promotion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            promo_type VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            subtitle VARCHAR(300),
            image_url VARCHAR(500),
            target_url VARCHAR(500),
            coupon_code VARCHAR(50),
            discount_percent FLOAT DEFAULT 0.0,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS site_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_name VARCHAR(100) DEFAULT 'StreamVibe',
            logo_url VARCHAR(500),
            favicon_url VARCHAR(500),
            footer_content TEXT DEFAULT '&copy; 2026 StreamVibe. All rights reserved.',
            terms_conditions TEXT,
            privacy_policy TEXT,
            contact_info TEXT,
            homepage_sections TEXT DEFAULT 'slider,trending,movies,music,promotions',
            navigation_menu TEXT DEFAULT 'Home|/,Movies|/movies,Music|/music,Contact|/terms#contact',
            theme_colors VARCHAR(100) DEFAULT 'dark-purple',
            seo_metadata TEXT DEFAULT 'description=Stream Premium Movies and Songs;keywords=movies,download,music,streaming,mp3',
            chatbot_settings TEXT DEFAULT 'system_prompt=You are StreamVibe AI, a helpful movie and music expert recommendation bot.;voice_enabled=true;multilingual=true',
            ai_agent_settings TEXT DEFAULT 'auto_generate=true;duplicate_detect=true;pricing_suggest=true',
            payment_qr_url VARCHAR(500) DEFAULT 'https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=upi://pay?pa=pay@streamvibe%26pn=StreamVibe',
            upi_id VARCHAR(100) DEFAULT 'pay@streamvibe',
            adsense_code TEXT DEFAULT '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8471194516724047" crossorigin="anonymous"></script>',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username VARCHAR(80),
            action VARCHAR(200) NOT NULL,
            ip_address VARCHAR(50),
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            movie_id INTEGER,
            song_id INTEGER,
            web_series_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE,
            FOREIGN KEY(movie_id) REFERENCES movie(id) ON DELETE CASCADE,
            FOREIGN KEY(song_id) REFERENCES song(id) ON DELETE CASCADE,
            FOREIGN KEY(web_series_id) REFERENCES web_series(id) ON DELETE CASCADE
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS review (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            movie_id INTEGER,
            song_id INTEGER,
            rating INTEGER DEFAULT 5,
            comment TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(movie_id) REFERENCES movie(id),
            FOREIGN KEY(song_id) REFERENCES song(id)
        )
    `);

    await dbRun(`
        CREATE TABLE IF NOT EXISTS secure_download_token (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token VARCHAR(100) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            movie_id INTEGER,
            song_id INTEGER,
            expires_at DATETIME NOT NULL,
            downloads_count INTEGER DEFAULT 0,
            max_downloads INTEGER DEFAULT 3,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(movie_id) REFERENCES movie(id),
            FOREIGN KEY(song_id) REFERENCES song(id)
        )
    `);
}

async function seedDatabase() {
    // 1. Site Settings
    const settings = await dbGet('SELECT * FROM site_settings LIMIT 1');
    if (!settings) {
        await dbRun(`
            INSERT INTO site_settings (
                site_name, logo_url, favicon_url, footer_content, terms_conditions,
                privacy_policy, contact_info, theme_colors, navigation_menu, payment_qr_url, upi_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `, [
            "StreamVibe",
            "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?auto=format&fit=crop&w=80&q=80",
            "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?auto=format&fit=crop&w=16&q=16",
            "&copy; 2026 StreamVibe Premium. Unlimited Video Streaming & Downloads.",
            "<h3>1. Terms of Use</h3><p>By using StreamVibe, you agree to comply with our downloading and streaming guidelines.</p>",
            "<h3>2. Privacy Policy</h3><p>We respect your personal details. Payment transactions are processed securely.</p>",
            "<h4>Support Center</h4><p>Email: support@streamvibe.com</p>",
            "dark-purple",
            "Home|/,Movies|/movies,Web Series|/webseries,Music Library|/music,Upcoming|/upcoming,VIP Plans|/subscriptions",
            "https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=upi://pay?pa=pay@streamvibe%26pn=StreamVibe",
            "pay@streamvibe"
        ]);
    }

    // 2. Admin account
    const adminUser = await dbGet('SELECT * FROM user WHERE username = ?', ['admin']);
    if (!adminUser) {
        const hashedPassword = await bcrypt.hash('admin123', 10);
        await dbRun(`
            INSERT INTO user (username, email, phone, role, is_active, password_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        `, ['admin', 'admin@gmail.com', '1234567890', 'super_admin', 1, hashedPassword]);
    }

    // Load dynamic seed data from seed_data.json
    const seedPath = path.join(__dirname, 'seed_data.json');
    if (fs.existsSync(seedPath)) {
        try {
            const data = JSON.parse(fs.readFileSync(seedPath, 'utf8'));

            // 3. Subscription Plans
            const plansCount = await dbGet('SELECT COUNT(*) as count FROM subscription_plan');
            if (plansCount.count === 0 && data.plans) {
                for (const p of data.plans) {
                    await dbRun(`
                        INSERT INTO subscription_plan (name, price, duration_months, description)
                        VALUES (?, ?, ?, ?)
                    `, [p.name, p.price, p.duration_months, p.description]);
                }
            }

            // 4. Promotions
            const promoCount = await dbGet('SELECT COUNT(*) as count FROM promotion');
            if (promoCount.count === 0 && data.promotions) {
                for (const pr of data.promotions) {
                    await dbRun(`
                        INSERT INTO promotion (promo_type, title, subtitle, image_url, target_url, coupon_code, discount_percent, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    `, [pr.promo_type, pr.title, pr.subtitle, pr.image_url || null, pr.target_url || null, pr.coupon_code || null, pr.discount_percent || 0.0, pr.is_active]);
                }
            }

            // 5. Movies
            const moviesCount = await dbGet('SELECT COUNT(*) as count FROM movie');
            if (moviesCount.count === 0 && data.movies) {
                for (const m of data.movies) {
                    await dbRun(`
                        INSERT INTO movie (
                            title, poster_url, screenshots, trailer_url, description, director, cast,
                            release_date, genre, language, imdb_rating, is_paid, price, status,
                            link_480p, link_720p, link_1080p, link_4k
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    `, [
                        m.title, m.poster_url, m.screenshots, m.trailer_url, m.description, m.director, m.cast,
                        m.release_date, m.genre, m.language, m.imdb_rating, m.is_paid, m.price, m.status,
                        m.link_480p, m.link_720p, m.link_1080p, m.link_4k
                    ]);
                }
            }

            // 6. Upcoming Movies
            const upcomingCount = await dbGet('SELECT COUNT(*) as count FROM upcoming_movie');
            if (upcomingCount.count === 0 && data.upcoming) {
                for (const u of data.upcoming) {
                    await dbRun(`
                        INSERT INTO upcoming_movie (title, poster_url, release_date, trailer_url, genre, cast, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    `, [u.title, u.poster_url, u.release_date, u.trailer_url, u.genre, u.cast, u.description]);
                }
            }

            // 7. Web Series
            const seriesCount = await dbGet('SELECT COUNT(*) as count FROM web_series');
            if (seriesCount.count === 0 && data.webseries) {
                for (const s of data.webseries) {
                    const result = await dbRun(`
                        INSERT INTO web_series (title, poster_url, description, director, cast, release_date, genre, status, is_paid, price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    `, [s.title, s.poster_url, s.description, s.director, s.cast, s.release_date, s.genre, s.status, s.is_paid, s.price]);
                    
                    const seriesId = result.lastID;
                    if (s.episodes) {
                        for (const ep of s.episodes) {
                            await dbRun(`
                                INSERT INTO episode (web_series_id, title, season_number, episode_number, cover_url, video_url, duration)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            `, [seriesId, ep.title, ep.season_number, ep.episode_number, ep.cover_url, ep.video_url, ep.duration]);
                        }
                    }
                }
            }

            // 8. Albums & Songs
            const albumCount = await dbGet('SELECT COUNT(*) as count FROM album');
            if (albumCount.count === 0 && data.albums) {
                for (const a of data.albums) {
                    const result = await dbRun(`
                        INSERT INTO album (title, artist, cover_url, description)
                        VALUES (?, ?, ?, ?)
                    `, [a.title, a.artist, a.cover_url, a.description]);
                    
                    const albumId = result.lastID;
                    if (a.songs) {
                        for (const s of a.songs) {
                            await dbRun(`
                                INSERT INTO song (title, album_id, artist, cover_url, lyrics, song_type, price, audio_128_url, audio_320_url)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            `, [s.title, albumId, s.artist, s.cover_url, s.lyrics, s.song_type, s.price, s.audio_128_url, s.audio_320_url]);
                        }
                    }
                }
            }
        } catch (e) {
            console.error("Error seeding dynamic database:", e);
        }
    }
}

// Recreate database from scratch
async function resetDatabase() {
    await dbRun("DROP TABLE IF EXISTS user");
    await dbRun("DROP TABLE IF EXISTS movie");
    await dbRun("DROP TABLE IF EXISTS upcoming_movie");
    await dbRun("DROP TABLE IF EXISTS web_series");
    await dbRun("DROP TABLE IF EXISTS episode");
    await dbRun("DROP TABLE IF EXISTS album");
    await dbRun("DROP TABLE IF EXISTS song");
    await dbRun("DROP TABLE IF EXISTS subscription_plan");
    await dbRun("DROP TABLE IF EXISTS user_subscription");
    await dbRun("DROP TABLE IF EXISTS payment_request");
    await dbRun("DROP TABLE IF EXISTS advertisement");
    await dbRun("DROP TABLE IF EXISTS promotion");
    await dbRun("DROP TABLE IF EXISTS site_settings");
    await dbRun("DROP TABLE IF EXISTS audit_log");
    await dbRun("DROP TABLE IF EXISTS wishlist");
    await dbRun("DROP TABLE IF EXISTS review");
    await dbRun("DROP TABLE IF EXISTS secure_download_token");

    await initializeSchema();
    await seedDatabase();
}

// Export database interface
module.exports = {
    dbRun,
    dbGet,
    dbAll,
    initializeSchema,
    seedDatabase,
    resetDatabase
};
