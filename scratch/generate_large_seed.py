import json
import os
import random

def generate_data():
    # 1. Exact restoration of the original database elements
    original_movies = [
        {
            "title": "Dhamaal",
            "poster_url": "https://upload.wikimedia.org/wikipedia/en/a/a2/Dhamaal_film_poster.jpg",
            "screenshots": "https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=600&q=80",
            "trailer_url": "https://www.youtube.com/embed/S2jN1F8r2tE",
            "description": "Four lazy, good-for-nothing friends find out about a hidden treasure in Goa from a dying thief. They embark on a race to find the treasure before a determined police inspector.",
            "director": "Indra Kumar",
            "cast": "Sanjay Dutt, Arshad Warsi, Riteish Deshmukh, Javed Jaffrey",
            "release_date": "2007-09-07",
            "genre": "Comedy, Adventure",
            "language": "Hindi",
            "imdb_rating": 7.4,
            "is_paid": 0,
            "price": 0.0,
            "status": "published",
            "link_480p": "https://www.w3schools.com/html/mov_bbb.mp4",
            "link_720p": "https://www.w3schools.com/html/mov_bbb.mp4",
            "link_1080p": "https://www.w3schools.com/html/mov_bbb.mp4",
            "link_4k": "https://www.w3schools.com/html/mov_bbb.mp4"
        },
        {
            "title": "Gadar 2",
            "poster_url": "https://upload.wikimedia.org/wikipedia/en/6/65/Gadar_2_film_poster.jpg",
            "screenshots": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=600&q=80",
            "trailer_url": "https://www.youtube.com/embed/vhwspPvJAOc",
            "description": "During the Indo-Pakistani War of 1971, Tara Singh returns to Pakistan to rescue his son, Charanjeet, who has been imprisoned and tortured by the Pakistani army.",
            "director": "Anil Sharma",
            "cast": "Sunny Deol, Ameesha Patel, Utkarsh Sharma",
            "release_date": "2023-08-11",
            "genre": "Action, Drama",
            "language": "Hindi",
            "imdb_rating": 6.2,
            "is_paid": 1,
            "price": 99.0,
            "status": "trending",
            "link_480p": "https://www.w3schools.com/html/mov_bbb.mp4",
            "link_720p": "https://www.w3schools.com/html/mov_bbb.mp4",
            "link_1080p": "https://www.w3schools.com/html/mov_bbb.mp4",
            "link_4k": "https://www.w3schools.com/html/mov_bbb.mp4"
        }
    ]

    original_upcoming = [
        {
            "title": "Kalki 2898 AD",
            "poster_url": "https://upload.wikimedia.org/wikipedia/en/4/4c/Kalki_2898_AD_poster.jpg",
            "release_date": "2026-08-01",
            "trailer_url": "https://www.youtube.com/embed/kQDd1AhGI90",
            "genre": "Sci-Fi, Action",
            "cast": "Prabhas, Amitabh Bachchan, Kamal Haasan, Deepika Padukone",
            "description": "A modern avatar of Vishnu, a Hindu god, is believed to have descended to Earth to protect humanity from evil forces in a futuristic dystopian world."
        },
        {
            "title": "Pushpa 2: The Rule",
            "poster_url": "https://upload.wikimedia.org/wikipedia/en/5/5f/Pushpa_2-_The_Rule.jpg",
            "release_date": "2026-12-05",
            "trailer_url": "https://www.youtube.com/embed/1kVPz_T-1t0",
            "genre": "Action, Thriller",
            "cast": "Allu Arjun, Rashmika Mandanna, Fahadh Faasil",
            "description": "The clash continues between Pushpa Raj and SP Bhanwar Singh Shekhawat in this high-octane action thriller sequel."
        }
    ]

    original_webseries = [
        {
            "title": "Stranger Things",
            "poster_url": "https://upload.wikimedia.org/wikipedia/en/7/7a/Stranger_Things_season_4_poster.jpg",
            "description": "When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces and one strange little girl.",
            "director": "The Duffer Brothers",
            "cast": "Millie Bobby Brown, Finn Wolfhard, Winona Ryder",
            "release_date": "2016-07-15",
            "genre": "Sci-Fi, Horror, Drama",
            "status": "published",
            "is_paid": 1,
            "price": 199.0,
            "episodes": [
                {
                    "title": "Chapter One: The Vanishing of Will Byers",
                    "season_number": 1,
                    "episode_number": 1,
                    "cover_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=400&q=80",
                    "video_url": "https://www.w3schools.com/html/mov_bbb.mp4",
                    "duration": "48m"
                },
                {
                    "title": "Chapter Two: The Weirdo on Maple Street",
                    "season_number": 1,
                    "episode_number": 2,
                    "cover_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=400&q=80",
                    "video_url": "https://www.w3schools.com/html/mov_bbb.mp4",
                    "duration": "55m"
                }
            ]
        }
    ]

    original_albums = [
        {
            "title": "Bollywood Golden Beats",
            "artist": "Various Artists",
            "cover_url": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=400&q=80",
            "description": "Premium compilation of popular Bollywood hits.",
            "songs": [
                {
                    "title": "Tum Hi Ho",
                    "artist": "Arijit Singh",
                    "cover_url": "https://images.unsplash.com/photo-1487180142328-0c4e37023af5?auto=format&fit=crop&w=400&q=80",
                    "lyrics": "[00:00] Hum tere bin ab reh nahi sakte...\n[00:15] Kyunki tum hi ho, ab tum hi ho...",
                    "song_type": "free",
                    "price": 0.0,
                    "audio_128_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                    "audio_320_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"
                },
                {
                    "title": "Chaleya",
                    "artist": "Anirudh Ravichander",
                    "cover_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=400&q=80",
                    "lyrics": "[00:00] Ishq mein dil bana hai...\n[00:20] Chaleya teri aur, chaleya...",
                    "song_type": "paid",
                    "price": 19.0,
                    "audio_128_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
                    "audio_320_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"
                }
            ]
        }
    ]

    # Lookups for official posters from Wikipedia
    official_posters = {
        "Animal": "https://upload.wikimedia.org/wikipedia/en/9/90/Animal_%282023_film%29_poster.jpg",
        "Barfi!": "https://upload.wikimedia.org/wikipedia/en/2/2e/Barfi%21_poster.jpg",
        "Chennai Express": "https://upload.wikimedia.org/wikipedia/en/1/1b/Chennai_Express_poster.jpg",
        "Dangal": "https://upload.wikimedia.org/wikipedia/en/9/99/Dangal_Poster.jpg",
        "Edge of Tomorrow": "https://upload.wikimedia.org/wikipedia/en/f/f9/Edge_of_Tomorrow_poster.jpg",
        "Fighter": "https://upload.wikimedia.org/wikipedia/en/d/df/Fighter_film_poster.jpg",
        "Gully Boy": "https://upload.wikimedia.org/wikipedia/en/0/07/Gully_Boy_poster.jpg",
        "Hera Pheri": "https://upload.wikimedia.org/wikipedia/en/a/a3/Hera_Pheri_2000_Poster.jpg",
        "Inception": "https://upload.wikimedia.org/wikipedia/en/2/2e/Inception_%282010%29_theatrical_poster.jpg",
        "Jawan": "https://upload.wikimedia.org/wikipedia/en/3/39/Jawan_film_poster.jpg",
        "K.G.F: Chapter 1": "https://upload.wikimedia.org/wikipedia/en/d/d0/K.G.F_Chapter_1_poster.jpg",
        "Lagaan": "https://upload.wikimedia.org/wikipedia/en/b/b6/Lagaan_poster.jpg",
        "M.S. Dhoni: The Untold Story": "https://upload.wikimedia.org/wikipedia/en/3/33/M.S._Dhoni_-_The_Untold_Story_poster.jpg",
        "Newton": "https://upload.wikimedia.org/wikipedia/en/d/db/Newton_film_poster.jpg",
        "OMG: Oh My God!": "https://upload.wikimedia.org/wikipedia/en/e/eb/Oh_My_God_poster.jpg",
        "PK": "https://upload.wikimedia.org/wikipedia/en/c/c3/PK_poster.jpg",
        "Queen": "https://upload.wikimedia.org/wikipedia/en/4/45/Queen_2014_poster.jpg",
        "RRR": "https://upload.wikimedia.org/wikipedia/en/d/d7/RRR_Poster.jpg",
        "Sholay": "https://upload.wikimedia.org/wikipedia/en/5/52/Sholay-poster.jpg",
        "Tiger Zinda Hai": "https://upload.wikimedia.org/wikipedia/en/2/29/Tiger_Zinda_Hai_poster.jpg",
        "Uri: The Surgical Strike": "https://upload.wikimedia.org/wikipedia/en/3/3b/URI_-_New_Poster.jpg",
        "Vikram": "https://upload.wikimedia.org/wikipedia/en/9/93/Vikram_2022_poster.jpg",
        "War": "https://upload.wikimedia.org/wikipedia/en/6/6f/War_official_poster.jpg",
        "X-Men: Days of Future Past": "https://upload.wikimedia.org/wikipedia/en/0/0c/X-Men_Days_of_Future_Past_poster.jpg",
        "Yeh Jawaani Hai Deewani": "https://upload.wikimedia.org/wikipedia/en/1/15/Yeh_Jawaani_Hai_Deewani_poster.jpg",
        "Zindagi Na Milegi Dobara": "https://upload.wikimedia.org/wikipedia/en/3/3d/Zindagi_Na_Milegi_Dobara_poster.jpg",
        "3 Idiots": "https://upload.wikimedia.org/wikipedia/en/d/df/3_idiots_poster.jpg",
        "Sairat": "https://upload.wikimedia.org/wikipedia/en/5/59/Sairat_poster.jpg",
        "Natsamrat": "https://upload.wikimedia.org/wikipedia/en/7/77/Natsamrat_%28film%29_poster.jpg",
        "Katyar Kaljat Ghusali": "https://upload.wikimedia.org/wikipedia/en/f/f6/Katyar_Kaljat_Ghusali_poster.jpeg",
        "Lay Bhaari": "https://upload.wikimedia.org/wikipedia/en/8/89/Lay_Bhaari_poster.jpg",
        "Timepass": "https://upload.wikimedia.org/wikipedia/en/6/6c/Timepass_marathi_movie_poster.jpeg",
        "Oppenheimer": "https://upload.wikimedia.org/wikipedia/en/4/4a/Oppenheimer_%28film%29.jpg",
        "Barbie": "https://upload.wikimedia.org/wikipedia/en/0/0b/Barbie_2023_poster.jpg",
        "Titanic": "https://upload.wikimedia.org/wikipedia/en/1/1a/Official_poster_for_the_movie_Titanic.png",
        "Avatar": "https://upload.wikimedia.org/wikipedia/en/d/d6/Avatar_%282009_film%29_poster.jpg",
        "Avatar: The Way of Water": "https://upload.wikimedia.org/wikipedia/en/5/54/Avatar_The_Way_of_Water_poster.jpg",
        "Avengers: Endgame": "https://upload.wikimedia.org/wikipedia/en/0/0d/Avengers_Endgame_poster.jpg",
        "Iron Man": "https://upload.wikimedia.org/wikipedia/en/0/0c/Iron_Man_poster.jpg",
        "The Matrix": "https://upload.wikimedia.org/wikipedia/en/c/c1/The_Matrix_Poster.jpg",
        "Harry Potter": "https://upload.wikimedia.org/wikipedia/en/7/7a/Harry_Potter_and_the_Philosopher%27s_Stone_poster.jpg",
        "Dune": "https://upload.wikimedia.org/wikipedia/en/8/8e/Dune_%282021_film%29_poster.jpg",
        "Joker": "https://upload.wikimedia.org/wikipedia/en/e/e1/Joker_%282019_film%29_poster.jpg.png"
    }

    # Lookups for official posters of popular web series
    official_series_posters = {
        "Peaky Blinders": "https://upload.wikimedia.org/wikipedia/en/4/42/Peaky_Blinders_title_card.jpg",
        "Scam 1992": "https://upload.wikimedia.org/wikipedia/en/9/9f/Scam_1992_poster.png",
        "Game of Thrones": "https://upload.wikimedia.org/wikipedia/en/d/d8/Game_of_Thrones_title_card.jpg",
        "Panchayat": "https://upload.wikimedia.org/wikipedia/en/0/06/Panchayat_logo.jpg",
        "Chernobyl": "https://upload.wikimedia.org/wikipedia/en/a/a7/Chernobyl_2019_Miniseries.jpg",
        "Breaking Bad": "https://upload.wikimedia.org/wikipedia/en/7/7a/Breaking_Bad_title_card.png",
        "Rocket Boys": "https://upload.wikimedia.org/wikipedia/en/a/ad/Rocket_Boys_SonyLIV_poster.jpg",
        "Dark": "https://upload.wikimedia.org/wikipedia/en/d/da/DarkNetflixPosterv1.png",
        "Narcos": "https://upload.wikimedia.org/wikipedia/en/1/17/Narcos_poster.jpg",
        "House of the Dragon": "https://upload.wikimedia.org/wikipedia/en/d/db/House_of_the_Dragon_title_card.jpg",
        "Special OPS": "https://upload.wikimedia.org/wikipedia/en/6/67/Special_Ops_poster.jpg",
        "The Bear": "https://upload.wikimedia.org/wikipedia/en/a/a8/The_Bear_TV_series_poster.jpg",
        "The Mandalorian": "https://upload.wikimedia.org/wikipedia/en/6/6c/The_Mandalorian_logo.svg",
        "Ozark": "https://upload.wikimedia.org/wikipedia/en/a/ad/Ozark_title_card.png",
        "The Office": "https://upload.wikimedia.org/wikipedia/en/8/80/The_Office_singles.jpg",
        "Guns & Gulaabs": "https://upload.wikimedia.org/wikipedia/en/f/f6/Guns_%26_Gulaabs_poster.jpg",
        "Asur": "https://upload.wikimedia.org/wikipedia/en/f/fe/Asur_voot.jpg",
        "The Boys": "https://upload.wikimedia.org/wikipedia/en/6/6f/The_Boys_season_4_poster.jpg",
        "The Railway Men": "https://upload.wikimedia.org/wikipedia/en/d/df/The_Railway_Men_poster.jpg",
        "Delhi Crime": "https://upload.wikimedia.org/wikipedia/en/7/7a/Delhi_Crime_poster.jpg",
        "Succession": "https://upload.wikimedia.org/wikipedia/en/7/7d/Succession_title_card.jpg",
        "Fleabag": "https://upload.wikimedia.org/wikipedia/en/d/dd/Fleabag_poster.jpg",
        "The Last of Us": "https://upload.wikimedia.org/wikipedia/en/4/4b/The_Last_of_Us_TV_series_title_card.png",
        "Black Mirror": "https://upload.wikimedia.org/wikipedia/en/c/c5/Black_mirror_logo.png",
        "Wednesday": "https://upload.wikimedia.org/wikipedia/en/7/78/Wednesday_Netflix_series_poster.png",
        "Aspirants": "https://upload.wikimedia.org/wikipedia/en/7/76/TVF_Aspirants_poster.jpg",
        "Brooklyn Nine-Nine": "https://upload.wikimedia.org/wikipedia/en/b/b3/Brooklyn_Nine-Nine_S8_Poster.jpg",
        "Made in Heaven": "https://upload.wikimedia.org/wikipedia/en/a/a9/Made_In_Heaven_poster.jpg",
        "Stranger Things": "https://upload.wikimedia.org/wikipedia/en/7/7a/Stranger_Things_season_4_poster.jpg",
        "Aarya": "https://upload.wikimedia.org/wikipedia/en/b/b0/Aarya_Hotstar_poster.jpg",
        "Sherlock": "https://upload.wikimedia.org/wikipedia/en/4/4d/Sherlock_title_card.jpg",
        "The Crown": "https://upload.wikimedia.org/wikipedia/en/a/a8/The_Crown_season_5_poster.jpg",
        "Loki": "https://upload.wikimedia.org/wikipedia/en/b/b3/Loki_season_2_poster.jpg",
        "Kota Factory": "https://upload.wikimedia.org/wikipedia/en/d/d8/Kota_Factory_poster.jpg",
        "Sacred Games": "https://upload.wikimedia.org/wikipedia/en/7/72/Sacred_Games_title.jpg",
        "Samantar": "https://upload.wikimedia.org/wikipedia/en/2/23/Samantar_poster.jpg",
        "Farzi": "https://upload.wikimedia.org/wikipedia/en/1/1a/Farzi_poster.jpg",
        "Mirzapur": "https://upload.wikimedia.org/wikipedia/en/3/3c/Mirzapur_poster.jpg",
        "Friends": "https://upload.wikimedia.org/wikipedia/en/d/d6/Friends_season_one_cast.jpg",
        "The Family Man": "https://upload.wikimedia.org/wikipedia/en/1/10/The_Family_Man_poster.jpeg",
        "Raanbaazaar": "https://upload.wikimedia.org/wikipedia/en/e/ed/RaanBaazaar_poster.jpg",
        "Swarajya Rakshak Sambhaji": "https://upload.wikimedia.org/wikipedia/en/b/be/Swarajyarakshak_Sambhaji.jpg",
        "Raja Shivchatrapati": "https://upload.wikimedia.org/wikipedia/en/2/29/Raja_Shivchatrapati_Logo.jpg"
    }

    # Lookups for official covers of popular music albums
    official_album_covers = {
        "Kabir Singh": "https://upload.wikimedia.org/wikipedia/en/d/dc/Kabir_Singh.jpg",
        "Aashiqui 2": "https://upload.wikimedia.org/wikipedia/en/f/f3/Aashiqui_2_remake.jpg",
        "Rockstar": "https://upload.wikimedia.org/wikipedia/en/b/b8/Rockstar_%28soundtrack%29.jpg",
        "Yeh Jawaani Hai Deewani": "https://upload.wikimedia.org/wikipedia/en/f/f8/Yeh_Jawaani_Hai_Deewani_soundtrack.jpg",
        "Ae Dil Hai Mushkil": "https://upload.wikimedia.org/wikipedia/en/3/3d/Ae_Dil_Hai_Mushkil_soundtrack.jpg",
        "Shershaah": "https://upload.wikimedia.org/wikipedia/en/d/db/Shershaah_soundtrack_cover.jpg",
        "Jawan": "https://upload.wikimedia.org/wikipedia/en/1/19/Jawan_soundtrack_cover.jpg",
        "Animal": "https://upload.wikimedia.org/wikipedia/en/b/b1/Animal_soundtrack_cover.jpg",
        "Sairat Album": "https://upload.wikimedia.org/wikipedia/en/8/8c/Sairat_soundtrack.jpg",
        "Dunki": "https://upload.wikimedia.org/wikipedia/en/a/a2/Dunki_soundtrack.jpg",
        "Pathaan": "https://upload.wikimedia.org/wikipedia/en/2/2a/Pathaan_soundtrack.jpg",
        "Gadar 2": "https://upload.wikimedia.org/wikipedia/en/7/75/Gadar_2_soundtrack_cover.jpg",
        "RRR": "https://upload.wikimedia.org/wikipedia/en/0/0a/RRR_soundtrack.jpg",
        "Dil Se": "https://upload.wikimedia.org/wikipedia/en/8/82/Dil_Se_soundtrack_cover.jpeg"
    }

    # Unsplash poster IDs pool for padding
    unsplash_ids = [
        "photo-1489599849927-2ee91cede3ba", "photo-1594909122845-11baa439b7bf", "photo-1478760329108-5c3ed9d495a0",
        "photo-1536440136628-849c177e76a1", "photo-1542204172-e7052809f852", "photo-1485846234645-a62644f84728",
        "photo-1517604931442-7e0c8ed2963c", "photo-1574375927938-d5a98e8edd86", "photo-1509198397868-475647b2a1e5",
        "photo-1595769816263-9b910be24d5f", "photo-1535016120720-40c646be5580", "photo-1440404653325-ab127d49abc1",
        "photo-1585647347483-22b66260dfff", "photo-1515634928627-2a4e0dae3ddf", "photo-1478720568477-151d9b21cdb2",
        "photo-1524995997946-a1c2e315a42f", "photo-1533928298208-27ff66555d8d", "photo-1505682631047-4031d90268ec"
    ]

    # 1. GENERATE MOVIES (100)
    hindi_pool = [
        "Animal", "Dhamaal", "Gadar 2", "3 Idiots", "Lagaan", "Dilwale Dulhania Le Jayenge", "Bajrangi Bhaijaan",
        "Kabir Singh", "Jawan", "Pathaan", "Hera Pheri", "PK", "Munna Bhai M.B.B.S.", "Queen", "Barfi!",
        "Chennai Express", "Gully Boy", "Raazi", "Andhadhun", "Drishyam", "Uri: The Surgical Strike", "Chhichhore",
        "Tanhaji", "Fighter", "Stree", "Shershaah", "Rocky Aur Rani Kii Prem Kahaani", "Brahmastra", "Dunki",
        "Tiger 3", "Bhool Bhulaiyaa 2", "Drishyam 2", "Kantara", "Gangubai Kathiawadi", "Super 30"
    ]
    marathi_pool = [
        "Sairat", "Natsamrat", "Katyar Kaljat Ghusali", "Lay Bhaari", "Timepass", "Duniyadari", "Court",
        "Harishchandrachi Factory", "Killa", "Fandry", "Faster Fene", "Muramba", "Elizabeth Ekadashi", "Ventilator",
        "Naal", "Anandi Gopal", "Jhimma", "Pawankhind", "Sher Shivraj", "Subhedar", "Dharmaveer", "Mulshi Pattern"
    ]
    english_pool = [
        "Inception", "Interstellar", "The Dark Knight", "Titanic", "Avatar", "Avatar: The Way of Water",
        "Avengers: Endgame", "Iron Man", "Gladiator", "The Matrix", "Pulp Fiction", "Forrest Gump", "The Godfather",
        "Jurassic Park", "Star Wars: A New Hope", "The Lion King", "Toy Story", "Finding Nemo", "Up", "Inside Out",
        "Coco", "Spider-Man: Into the Spider-Verse", "Dune", "Oppenheimer", "Barbie", "Mad Max: Fury Road",
        "The Lord of the Rings", "Harry Potter", "Pirates of the Caribbean", "Joker", "Deadpool", "Logan"
    ]

    movies_set = []
    # Add original movies first
    for m in original_movies:
        movies_set.append(m)

    pool = []
    for m in hindi_pool:
        if m not in ["Dhamaal", "Gadar 2"]: pool.append((m, "Hindi"))
    for m in marathi_pool: pool.append((m, "Marathi"))
    for m in english_pool: pool.append((m, "English"))
    
    random.shuffle(pool)
    while len(movies_set) < 100 and pool:
        title, lang = pool.pop(0)
        is_paid = random.choice([0, 1])
        price = 99.0 if is_paid else 0.0
        status = random.choice(["published", "featured", "trending"])
        
        if title in official_posters:
            poster = official_posters[title]
        else:
            img_id = unsplash_ids[len(movies_set) % len(unsplash_ids)]
            poster = f"https://images.unsplash.com/{img_id}?auto=format&fit=crop&w=400&q=80"
            
        movies_set.append({
            "title": title,
            "poster_url": poster,
            "screenshots": "https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=600&q=80",
            "trailer_url": "https://www.youtube.com/embed/YoHD9XEInc0",
            "description": f"Watch '{title}', a premium {lang} movie with outstanding visual effects and story.",
            "director": f"Director {len(movies_set)+1}",
            "cast": f"Lead Stars {len(movies_set)+1}",
            "release_date": f"202{random.randint(0,5)}-10-12",
            "genre": "Drama, Action",
            "language": lang,
            "imdb_rating": round(random.uniform(6.5, 9.0), 1),
            "is_paid": is_paid,
            "price": price,
            "status": status,
            "link_480p": "https://www.w3schools.com/html/mov_bbb.mp4",
            "link_720p": "https://www.w3schools.com/html/mov_bbb.mp4",
            "link_1080p": "https://www.w3schools.com/html/mov_bbb.mp4",
            "link_4k": "https://www.w3schools.com/html/mov_bbb.mp4"
        })

    while len(movies_set) < 100:
        idx = len(movies_set)
        movies_set.append({
            "title": f"Blockbuster Movie Vol. {idx}",
            "poster_url": f"https://images.unsplash.com/{unsplash_ids[idx % len(unsplash_ids)]}?auto=format&fit=crop&w=400&q=80",
            "screenshots": "https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=600&q=80",
            "trailer_url": "https://www.youtube.com/embed/YoHD9XEInc0",
            "description": "Premium blockbusters collection movie.",
            "director": "Various",
            "cast": "Ensemble Cast",
            "release_date": "2024-01-01",
            "genre": "Drama",
            "language": "Hindi",
            "imdb_rating": 7.0,
            "is_paid": 0,
            "price": 0.0,
            "status": "published",
            "link_480p": "https://www.w3schools.com/html/mov_bbb.mp4"
        })

    # 2. GENERATE WEB SERIES (100)
    series_hindi_pool = [
        "Scam 1992", "Panchayat", "Sacred Games", "Mirzapur", "The Family Man", "Kota Factory", "Criminal Justice", 
        "Special OPS", "Bandish Bandits", "Aarya", "Asur", "Jubilee", "Farzi", "Guns & Gulaabs", "The Railway Men", 
        "Delhi Crime", "Aspirants", "Yeh Meri Family", "Kala Pani", "Breathe", "Hostages", "Inside Edge", "Taaza Khabar", 
        "Scoop", "Pataal Lok", "Human", "Leila", "Selection Day", "Bard of Blood", "She", "Dahaad"
    ]
    series_marathi_pool = [
        "Samantar", "Raanbaazaar", "Pet Puraan", "Date With Saie", "Once a Year", "Gondya Ala Re", "Pandu", 
        "Shantit Kranti", "Tu Tevha Tashi", "Mazya Navryachi Bayko", "Swarajya Rakshak Sambhaji", "Raja Shivchatrapati", 
        "Chala Hawa Yeu Lya", "Ani Kay Hava"
    ]
    series_english_pool = [
        "Peaky Blinders", "Game of Thrones", "Chernobyl", "Breaking Bad", "Dark", "Narcos", "House of the Dragon", 
        "The Bear", "The Mandalorian", "Ozark", "The Office", "Beef", "Ted Lasso", "Mindhunter", "The Boys", 
        "Succession", "Fleabag", "The Last of Us", "Black Mirror", "Wednesday", "Brooklyn Nine-Nine", 
        "How I Met Your Mother", "Sherlock", "The Crown", "Loki", "Severance", "Modern Family", "The Big Bang Theory", 
        "Better Call Saul", "WandaVision", "Friends"
    ]

    series_set = []
    # Add original webseries first
    for ws in original_webseries:
        series_set.append(ws)

    series_pool = []
    for s in series_hindi_pool:
        if s != "Stranger Things": series_pool.append((s, "Hindi"))
    for s in series_marathi_pool:
        series_pool.append((s, "Marathi"))
    for s in series_english_pool:
        if s != "Stranger Things": series_pool.append((s, "English"))

    random.shuffle(series_pool)

    while len(series_set) < 100:
        if series_pool:
            title, lang = series_pool.pop(0)
        else:
            # Generate sequels
            base_series = random.choice(series_set)
            base_title = base_series["title"]
            if "Season" in base_title:
                parts = base_title.split(" Season ")
                try:
                    next_season = int(parts[-1]) + 1
                    title = " Season ".join(parts[:-1]) + f" Season {next_season}"
                except:
                    title = f"{base_title} Season 2"
            else:
                title = f"{base_title} Season 2"
                
            # Avoid duplicate titles
            existing_titles = [x["title"] for x in series_set]
            while title in existing_titles:
                title = title + " Season 3"
                if len(title) > 80:
                    title = f"New Hits Series Vol {random.randint(1, 1000)}"
            lang = "English"
            if base_title in series_hindi_pool:
                lang = "Hindi"
            elif base_title in series_marathi_pool:
                lang = "Marathi"

        clean_title = title.split(" Season ")[0]
        if clean_title in official_series_posters:
            poster = official_series_posters[clean_title]
        else:
            img_id = unsplash_ids[len(series_set) % len(unsplash_ids)]
            poster = f"https://images.unsplash.com/{img_id}?auto=format&fit=crop&w=400&q=80"

        episodes = []
        num_episodes = random.randint(2, 4)
        for ep_idx in range(1, num_episodes + 1):
            episodes.append({
                "title": f"Chapter {ep_idx}: The Story of {title}",
                "season_number": 1,
                "episode_number": ep_idx,
                "cover_url": f"https://images.unsplash.com/{unsplash_ids[(len(series_set) + ep_idx) % len(unsplash_ids)]}?auto=format&fit=crop&w=400&q=80",
                "video_url": "https://www.w3schools.com/html/mov_bbb.mp4",
                "duration": f"{random.randint(40, 60)}m"
            })

        is_paid = random.choice([0, 1])
        price = 199.0 if is_paid else 0.0

        series_set.append({
            "title": title,
            "poster_url": poster,
            "description": f"Dive into '{title}', an outstanding new {lang} web series. Experience premium acting and award-winning episodes.",
            "director": f"Series Director {len(series_set)+1}",
            "cast": f"Ensemble Cast {len(series_set)+1}",
            "release_date": f"202{random.randint(0,5)}-08-15",
            "genre": random.choice(["Drama, Mystery", "Thriller, Romance", "Sci-Fi, Action", "Comedy, Drama"]),
            "status": "published",
            "is_paid": is_paid,
            "price": price,
            "episodes": episodes
        })

    # 3. GENERATE ALBUMS & SONGS (100)
    albums_hindi_pool = [
        "Kabira Hits", "Bollywood Party Beats", "Amit Trivedi Hits", "Badshah Club", "Retro Bollywood", 
        "Sachin-Jigar Vibe", "Rahman Classics", "Javed-Mohsin Hits", "Dil Se", "Lofi Bollywood", 
        "Kishore-Lata Duets", "Pritam Hits", "RD Burman Mix", "Shreya Ghoshal Hits", "Atif Aslam Hits", 
        "Arijit Melodies", "Kabir Singh", "Aashiqui 2", "Rockstar", "Ae Dil Hai Mushkil", "Shershaah", 
        "Jawan", "Animal", "Dunki", "Pathaan", "Gadar 2", "RRR", "Diljit Dosanjh Vibe", "Sufi Beats"
    ]
    albums_marathi_pool = [
        "Marathi Sensation", "Ajay Atul Live", "Katyar Kaljat Songs", "Duniyadari Tracks", 
        "Lata Mangeshkar Devotional", "Ajay-Atul Beats", "Marathi Romantic Hits", "Sairat Album"
    ]
    albums_english_pool = [
        "Taylor Swift Classics", "Ed Sheeran Favourites", "Coldplay Anthem", "English Pop Hits"
    ]

    albums_set = []
    # Add original albums first
    for alb in original_albums:
        albums_set.append(alb)

    albums_pool = []
    for a in albums_hindi_pool:
        if a != "Bollywood Golden Beats": albums_pool.append((a, "Hindi", "Various Artists"))
    for a in albums_marathi_pool:
        albums_pool.append((a, "Marathi", "Various Artists"))
    for a in albums_english_pool:
        if a != "Bollywood Golden Beats": albums_pool.append((a, "English", "Various Artists"))

    random.shuffle(albums_pool)

    while len(albums_set) < 100:
        if albums_pool:
            title, lang, artist = albums_pool.pop(0)
        else:
            base_album = random.choice(albums_set)
            base_title = base_album["title"]
            if "Vol." in base_title:
                parts = base_title.split(" Vol. ")
                try:
                    next_vol = int(parts[-1]) + 1
                    title = " Vol. ".join(parts[:-1]) + f" Vol. {next_vol}"
                except:
                    title = f"{base_title} Vol. 2"
            else:
                title = f"{base_title} Vol. {random.randint(2, 5)}"
                
            existing_titles = [x["title"] for x in albums_set]
            while title in existing_titles:
                title = title + f" Vol. {random.randint(6, 100)}"
                if len(title) > 80:
                    title = f"Top Melodies Album Vol {random.randint(1, 1000)}"
            lang = "Hindi"
            artist = base_album["artist"]

        clean_title = title.split(" Vol.")[0]
        if clean_title in official_album_covers:
            cover = official_album_covers[clean_title]
        else:
            img_id = unsplash_ids[len(albums_set) % len(unsplash_ids)]
            cover = f"https://images.unsplash.com/{img_id}?auto=format&fit=crop&w=400&q=80"

        songs = []
        num_songs = random.randint(2, 4)
        for song_idx in range(1, num_songs + 1):
            is_paid = random.choice([0, 1])
            price = 19.0 if is_paid else 0.0
            song_type = "paid" if is_paid else "free"
            songs.append({
                "title": f"Track {song_idx}: Soulful Beats of {title}",
                "artist": artist if artist != "Various Artists" else f"Popular Artist {song_idx}",
                "cover_url": f"https://images.unsplash.com/{unsplash_ids[(len(albums_set) + song_idx) % len(unsplash_ids)]}?auto=format&fit=crop&w=400&q=80",
                "lyrics": f"[00:00] Beautiful music starts...\n[00:20] Singing the themes of {title}...",
                "song_type": song_type,
                "price": price,
                "audio_128_url": f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{random.randint(1, 10)}.mp3",
                "audio_320_url": f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{random.randint(11, 16)}.mp3"
            })

        albums_set.append({
            "title": title,
            "artist": artist,
            "cover_url": cover,
            "description": f"Masterpiece composition album '{title}' featuring popular music tracks and premium vocals.",
            "songs": songs
        })

    plans = [
        {
            "name": "StreamVibe Mobile",
            "price": 149.0,
            "duration_months": 12,
            "description": "Watch on 1 Mobile Screen. Ad-supported, HD (720p) video quality."
        },
        {
            "name": "StreamVibe Super",
            "price": 499.0,
            "duration_months": 12,
            "description": "Watch on 2 Screens (TV, Web, Mobile). Ad-supported, Full HD (1080p) video quality."
        },
        {
            "name": "StreamVibe Premium",
            "price": 1499.0,
            "duration_months": 12,
            "description": "Watch on 4 Screens. Ad-free streaming and downloading. Up to 4K Ultra HD video + Dolby Atmos."
        }
    ]

    promotions = [
        {
            "promo_type": "homepage_banner",
            "title": "Welcome to StreamVibe Premium",
            "subtitle": "Unlimited Streaming of 100+ Movies, 100+ Web Series and 100+ Albums.",
            "image_url": "https://images.unsplash.com/photo-1540747737956-37872404a821?auto=format&fit=crop&w=1200&q=80",
            "target_url": "/movies",
            "is_active": 1
        },
        {
            "promo_type": "flash_sale",
            "title": "StreamVibe VIP Festive Sale",
            "subtitle": "Get flat 50% discount on all premium movie tickets and web series passes.",
            "coupon_code": "SVVIP50",
            "discount_percent": 50.0,
            "is_active": 1
        }
    ]

    # Save to seed_data.json
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'seed_data.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "plans": plans,
            "promotions": promotions,
            "movies": movies_set,
            "upcoming": original_upcoming,
            "webseries": series_set,
            "albums": albums_set
        }, f, indent=2)

    print(f"[SUCCESS] Generated seed_data.json at {output_path}!")
    print(f"Stats: {len(movies_set)} Movies | {len(series_set)} Web Series | {len(albums_set)} Albums")

if __name__ == '__main__':
    generate_data()
