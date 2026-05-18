"""
Seed script — inserts all 150 music news sources into Supabase.
Run: python seed/sources.py
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SOURCES = [
    # ─────────────────────────────────────────
    # ENGLISH (en)
    # ─────────────────────────────────────────
    {"name": "Pitchfork",          "url": "https://pitchfork.com",               "rss_url": "https://pitchfork.com/rss/news/",                         "language": "en", "primary_genres": ["indie","alternative","rock"]},
    {"name": "Stereogum",          "url": "https://www.stereogum.com",            "rss_url": "https://www.stereogum.com/feed/",                          "language": "en", "primary_genres": ["indie","rock","alternative"]},
    {"name": "NME",                "url": "https://www.nme.com",                  "rss_url": "https://www.nme.com/feed",                                 "language": "en", "primary_genres": ["rock","pop","indie"]},
    {"name": "Consequence",        "url": "https://consequence.net",              "rss_url": "https://consequence.net/feed/",                            "language": "en", "primary_genres": ["rock","indie","metal","electronic"]},
    {"name": "The Quietus",        "url": "https://thequietus.com",               "rss_url": "https://thequietus.com/feed",                              "language": "en", "primary_genres": ["experimental","metal","indie","electronic"]},
    {"name": "Resident Advisor",   "url": "https://ra.co",                        "rss_url": "https://ra.co/xml/news.xml",                               "language": "en", "primary_genres": ["electronic","techno"]},
    {"name": "FACT Magazine",      "url": "https://www.factmag.com",              "rss_url": "https://www.factmag.com/feed/",                            "language": "en", "primary_genres": ["electronic","underground","hip-hop"]},
    {"name": "DJ Mag",             "url": "https://djmag.com",                    "rss_url": "https://djmag.com/rss.xml",                                "language": "en", "primary_genres": ["electronic","techno"]},
    {"name": "Louder Sound",       "url": "https://www.loudersound.com",          "rss_url": "https://www.loudersound.com/rss",                          "language": "en", "primary_genres": ["metal","rock"]},
    {"name": "Kerrang!",           "url": "https://www.kerrang.com",              "rss_url": "https://www.kerrang.com/rss",                              "language": "en", "primary_genres": ["metal","rock"]},
    {"name": "Metal Injection",    "url": "https://metalinjection.net",           "rss_url": "https://metalinjection.net/feed",                         "language": "en", "primary_genres": ["metal"]},
    {"name": "Blabbermouth",       "url": "https://www.blabbermouth.net",         "rss_url": "https://www.blabbermouth.net/news/feed/",                  "language": "en", "primary_genres": ["metal","rock"]},
    {"name": "Bandcamp Daily",     "url": "https://daily.bandcamp.com",           "rss_url": "https://daily.bandcamp.com/feed",                         "language": "en", "primary_genres": ["underground","indie","experimental"]},
    {"name": "The Wire",           "url": "https://www.thewire.co.uk",            "rss_url": "https://www.thewire.co.uk/rss",                           "language": "en", "primary_genres": ["experimental","jazz","electronic"]},
    {"name": "Jazz Times",         "url": "https://jazztimes.com",                "rss_url": "https://jazztimes.com/feed/",                             "language": "en", "primary_genres": ["jazz"]},
    {"name": "All About Jazz",     "url": "https://www.allaboutjazz.com",         "rss_url": "https://www.allaboutjazz.com/rss.php",                    "language": "en", "primary_genres": ["jazz"]},
    {"name": "Under the Radar",    "url": "https://www.undertheradarmag.com",     "rss_url": "https://www.undertheradarmag.com/news/rss",               "language": "en", "primary_genres": ["indie","alternative"]},
    {"name": "The Line of Best Fit","url": "https://www.thelineofbestfit.com",    "rss_url": "https://www.thelineofbestfit.com/rss/news",               "language": "en", "primary_genres": ["indie","alternative"]},
    {"name": "Exclaim!",           "url": "https://exclaim.ca",                   "rss_url": "https://exclaim.ca/rss",                                  "language": "en", "primary_genres": ["indie","alternative","metal"]},
    {"name": "Spin",               "url": "https://www.spin.com",                 "rss_url": "https://www.spin.com/feed/",                              "language": "en", "primary_genres": ["rock","indie","pop"]},
    {"name": "Paste Magazine",     "url": "https://www.pastemagazine.com",        "rss_url": "https://www.pastemagazine.com/rss/",                      "language": "en", "primary_genres": ["indie","folk","rock"]},
    {"name": "Clash Music",        "url": "https://www.clashmusic.com",           "rss_url": "https://www.clashmusic.com/rss",                          "language": "en", "primary_genres": ["indie","electronic","hip-hop"]},
    {"name": "PopMatters",         "url": "https://www.popmatters.com",           "rss_url": "https://www.popmatters.com/feed/",                        "language": "en", "primary_genres": ["indie","rock","electronic","jazz"]},
    {"name": "No Ripcord",         "url": "https://www.noripcord.com",            "rss_url": "https://www.noripcord.com/rss.xml",                       "language": "en", "primary_genres": ["indie","alternative"]},
    {"name": "Treble",             "url": "https://www.treblemag.com",            "rss_url": "https://www.treblemag.com/feed/",                         "language": "en", "primary_genres": ["indie","rock","experimental"]},

    # ─────────────────────────────────────────
    # ROMANIAN (ro)
    # ─────────────────────────────────────────
    {"name": "Metalhead.ro",       "url": "https://www.metalhead.ro",             "rss_url": "https://www.metalhead.ro/feed/",                          "language": "ro", "primary_genres": ["metal"]},
    {"name": "Scena9",             "url": "https://www.scena9.ro",                "rss_url": "https://www.scena9.ro/feed",                              "language": "ro", "primary_genres": ["indie","alternative","experimental"]},
    {"name": "Observator Cultural","url": "https://www.observatorcultural.ro",    "rss_url": "https://www.observatorcultural.ro/rss",                   "language": "ro", "primary_genres": ["jazz","classical","folk"]},
    {"name": "RFI România",        "url": "https://www.rfi.ro/muzica",            "rss_url": "https://www.rfi.ro/rss",                                  "language": "ro", "primary_genres": ["pop","rock","world"]},
    {"name": "Guerrilla",          "url": "https://www.guerrilla.ro",             "rss_url": "https://www.guerrilla.ro/rss/",                           "language": "ro", "primary_genres": ["rock","alternative","indie"]},
    {"name": "Muzici și Faze",     "url": "https://www.muzicisifaze.ro",          "rss_url": None,                                                       "language": "ro", "primary_genres": ["metal","underground"]},
    {"name": "ProFM Blog",         "url": "https://www.profm.ro/stiri",           "rss_url": "https://www.profm.ro/rss",                                "language": "ro", "primary_genres": ["pop","electronic","hip-hop"]},
    {"name": "Rock FM România",    "url": "https://www.rockfm.ro",               "rss_url": "https://www.rockfm.ro/rss",                               "language": "ro", "primary_genres": ["rock","metal"]},
    {"name": "HipHop.ro",          "url": "https://www.hiphop.ro",               "rss_url": "https://www.hiphop.ro/feed",                              "language": "ro", "primary_genres": ["hip-hop"]},
    {"name": "DoR",                "url": "https://www.dor.ro/tag/muzica",        "rss_url": "https://www.dor.ro/feed/",                                "language": "ro", "primary_genres": ["indie","folk","jazz"]},
    {"name": "Digi24 Cultură",     "url": "https://www.digi24.ro/cultura",        "rss_url": "https://www.digi24.ro/rss/cultura",                       "language": "ro", "primary_genres": ["pop","rock","classical"]},
    {"name": "Adevărul Cultură",   "url": "https://adevarul.ro/cultura/muzica",   "rss_url": "https://adevarul.ro/rss",                                 "language": "ro", "primary_genres": ["pop","rock","classical"]},
    {"name": "Libertatea Cultură", "url": "https://www.libertatea.ro/entertainment","rss_url": "https://www.libertatea.ro/rss",                         "language": "ro", "primary_genres": ["pop","rock","hip-hop"]},
    {"name": "Gandul Cultură",     "url": "https://www.gandul.ro/cultura",        "rss_url": "https://www.gandul.ro/rss/cultura",                       "language": "ro", "primary_genres": ["pop","classical","folk"]},
    {"name": "Artgasm",            "url": "https://www.artgasm.ro",               "rss_url": "https://www.artgasm.ro/feed",                             "language": "ro", "primary_genres": ["indie","electronic","alternative"]},
    {"name": "LaPunkt",            "url": "https://www.lapunkt.ro",               "rss_url": "https://www.lapunkt.ro/feed",                             "language": "ro", "primary_genres": ["jazz","world","experimental"]},
    {"name": "Vibe.ro",            "url": "https://www.vibe.ro",                  "rss_url": "https://www.vibe.ro/feed",                                "language": "ro", "primary_genres": ["pop","r&b","hip-hop"]},
    {"name": "The ARK",            "url": "https://theark.ro",                    "rss_url": None,                                                       "language": "ro", "primary_genres": ["indie","alternative"]},
    {"name": "Recorder",           "url": "https://recorder.ro",                  "rss_url": "https://recorder.ro/feed/",                               "language": "ro", "primary_genres": ["folk","rock","indie"]},
    {"name": "Cinetic",            "url": "https://cinetic.ro",                   "rss_url": None,                                                       "language": "ro", "primary_genres": ["electronic","underground","experimental"]},
    {"name": "Untold News",        "url": "https://untold.com/ro/news",           "rss_url": None,                                                       "language": "ro", "primary_genres": ["electronic","techno"]},
    {"name": "Electric Castle Blog","url": "https://electriccastle.ro/blog",      "rss_url": None,                                                       "language": "ro", "primary_genres": ["electronic","indie"]},
    {"name": "Music.ro",           "url": "https://www.music.ro",                 "rss_url": "https://www.music.ro/rss.xml",                            "language": "ro", "primary_genres": ["pop","rock","indie"]},
    {"name": "Modernism.ro",       "url": "https://modernism.ro",                 "rss_url": "https://modernism.ro/feed/",                              "language": "ro", "primary_genres": ["electronic","experimental"]},
    {"name": "Zeppelin",           "url": "https://www.zeppelin.ro",              "rss_url": "https://www.zeppelin.ro/feed",                            "language": "ro", "primary_genres": ["rock","alternative","punk"]},

    # ─────────────────────────────────────────
    # FRENCH (fr)
    # ─────────────────────────────────────────
    {"name": "Les Inrockuptibles", "url": "https://www.lesinrocks.com",           "rss_url": "https://www.lesinrocks.com/feed/",                        "language": "fr", "primary_genres": ["indie","alternative","pop"]},
    {"name": "Télérama Musique",   "url": "https://www.telerama.fr/musique",      "rss_url": "https://www.telerama.fr/rss/musique.xml",                 "language": "fr", "primary_genres": ["jazz","classical","rock","indie"]},
    {"name": "Rolling Stone FR",   "url": "https://www.rollingstone.fr",          "rss_url": "https://www.rollingstone.fr/feed/",                       "language": "fr", "primary_genres": ["rock","pop","indie"]},
    {"name": "Tsugi",              "url": "https://www.tsugi.fr",                 "rss_url": "https://www.tsugi.fr/feed/",                              "language": "fr", "primary_genres": ["electronic","techno"]},
    {"name": "Trax Magazine",      "url": "https://www.traxmag.com",              "rss_url": "https://www.traxmag.com/feed/",                           "language": "fr", "primary_genres": ["electronic","techno"]},
    {"name": "Gonzaï",             "url": "https://gonzai.com",                   "rss_url": "https://gonzai.com/feed/",                                "language": "fr", "primary_genres": ["indie","underground","alternative"]},
    {"name": "Metallian",          "url": "https://www.metallian.com",            "rss_url": "https://www.metallian.com/rss.php",                       "language": "fr", "primary_genres": ["metal"]},
    {"name": "Hard Force",         "url": "https://www.hard-force.com",           "rss_url": "https://www.hard-force.com/feed/",                        "language": "fr", "primary_genres": ["metal","rock"]},
    {"name": "Jazz Magazine",      "url": "https://www.jazzmagazine.com",         "rss_url": "https://www.jazzmagazine.com/feed/",                      "language": "fr", "primary_genres": ["jazz"]},
    {"name": "Improjazz",          "url": "https://www.improjazz.net",            "rss_url": None,                                                       "language": "fr", "primary_genres": ["jazz","experimental"]},
    {"name": "Mouvement",          "url": "https://www.mouvement.net",            "rss_url": "https://www.mouvement.net/rss",                           "language": "fr", "primary_genres": ["experimental","electronic"]},
    {"name": "Chronicart",         "url": "https://www.chronicart.com",           "rss_url": "https://www.chronicart.com/feed/",                        "language": "fr", "primary_genres": ["rock","indie","metal","electronic"]},
    {"name": "Magic!",             "url": "https://www.magic.fr",                 "rss_url": "https://www.magic.fr/rss",                                "language": "fr", "primary_genres": ["rock","classic-rock"]},
    {"name": "IndieMag",           "url": "https://www.indiemag.fr",              "rss_url": "https://www.indiemag.fr/feed/",                           "language": "fr", "primary_genres": ["indie"]},
    {"name": "Sourdoreille",       "url": "https://www.sourdoreille.net",         "rss_url": "https://www.sourdoreille.net/feed/",                      "language": "fr", "primary_genres": ["indie","world","folk"]},
    {"name": "Obskure",            "url": "https://www.obskure.com",              "rss_url": None,                                                       "language": "fr", "primary_genres": ["underground","experimental","electronic"]},
    {"name": "DBD Magazine",       "url": "https://www.dbdmag.fr",               "rss_url": "https://www.dbdmag.fr/feed/",                             "language": "fr", "primary_genres": ["metal"]},
    {"name": "Radio Nova",         "url": "https://www.nova.fr/musique",          "rss_url": "https://www.nova.fr/feed/",                               "language": "fr", "primary_genres": ["world","electronic","hip-hop"]},
    {"name": "Brain Magazine",     "url": "https://www.brain-magazine.fr",        "rss_url": "https://www.brain-magazine.fr/feed/",                     "language": "fr", "primary_genres": ["hip-hop","electronic","indie"]},
    {"name": "Longueur d'Ondes",   "url": "https://www.longueurdondes.com",       "rss_url": "https://www.longueurdondes.com/feed",                     "language": "fr", "primary_genres": ["world","folk","jazz"]},
    {"name": "Le Son du Rock",     "url": "https://www.leson-durock.com",         "rss_url": "https://www.leson-durock.com/feed/",                      "language": "fr", "primary_genres": ["rock","indie"]},
    {"name": "Charts in France",   "url": "https://www.chartsinfrance.net",       "rss_url": "https://www.chartsinfrance.net/rss/news.xml",             "language": "fr", "primary_genres": ["pop"]},
    {"name": "Libération Next",    "url": "https://www.liberation.fr/culture",    "rss_url": "https://www.liberation.fr/arc/outboundfeeds/rss/",        "language": "fr", "primary_genres": ["indie","pop","jazz"]},
    {"name": "Le Monde Culture",   "url": "https://www.lemonde.fr/culture",       "rss_url": "https://www.lemonde.fr/culture/rss_full.xml",             "language": "fr", "primary_genres": ["classical","jazz","pop"]},
    {"name": "Néosphère",          "url": "https://www.neosphere.com",            "rss_url": None,                                                       "language": "fr", "primary_genres": ["electronic","experimental"]},

    # ─────────────────────────────────────────
    # GERMAN (de)
    # ─────────────────────────────────────────
    {"name": "Laut.de",            "url": "https://www.laut.de",                  "rss_url": "https://www.laut.de/rss/news",                            "language": "de", "primary_genres": ["rock","indie","pop","metal"]},
    {"name": "Musikexpress",       "url": "https://www.musikexpress.de",          "rss_url": "https://www.musikexpress.de/feed/",                       "language": "de", "primary_genres": ["pop","rock","indie"]},
    {"name": "Rolling Stone DE",   "url": "https://www.rollingstone.de",          "rss_url": "https://www.rollingstone.de/feed/",                       "language": "de", "primary_genres": ["rock","pop","indie"]},
    {"name": "Metal Hammer DE",    "url": "https://www.metal-hammer.de",          "rss_url": "https://www.metal-hammer.de/feed/",                       "language": "de", "primary_genres": ["metal"]},
    {"name": "Rock Hard",          "url": "https://www.rock-hard.de",             "rss_url": "https://www.rock-hard.de/rss",                            "language": "de", "primary_genres": ["metal","rock"]},
    {"name": "Intro",              "url": "https://www.intro.de",                 "rss_url": "https://www.intro.de/feed/",                              "language": "de", "primary_genres": ["indie","alternative","electronic"]},
    {"name": "Visions",            "url": "https://www.visions.de",               "rss_url": "https://www.visions.de/rss",                              "language": "de", "primary_genres": ["indie","alternative","metal"]},
    {"name": "Jazzthing",          "url": "https://jazzthing.de",                 "rss_url": "https://jazzthing.de/feed/",                              "language": "de", "primary_genres": ["jazz"]},
    {"name": "Jazzzeitung",        "url": "https://www.jazzzeitung.de",           "rss_url": "https://www.jazzzeitung.de/feed/",                        "language": "de", "primary_genres": ["jazz"]},
    {"name": "Slam Magazine",      "url": "https://www.slam.de",                  "rss_url": "https://www.slam.de/feed/",                               "language": "de", "primary_genres": ["hip-hop","electronic"]},
    {"name": "Juice",              "url": "https://www.juice.de",                 "rss_url": "https://www.juice.de/feed/",                              "language": "de", "primary_genres": ["hip-hop"]},
    {"name": "Ox Fanzine",         "url": "https://www.ox-fanzine.de",            "rss_url": "https://www.ox-fanzine.de/rss.php",                       "language": "de", "primary_genres": ["punk","hardcore","underground"]},
    {"name": "Eclipsed",           "url": "https://www.eclipsed.de",              "rss_url": "https://www.eclipsed.de/rss",                             "language": "de", "primary_genres": ["rock","experimental","electronic"]},
    {"name": "Diffus Magazine",    "url": "https://www.diffus.de",               "rss_url": None,                                                       "language": "de", "primary_genres": ["electronic","indie"]},
    {"name": "NBHAP",              "url": "https://nbhap.com",                    "rss_url": "https://nbhap.com/feed/",                                 "language": "de", "primary_genres": ["electronic","indie","pop"]},
    {"name": "Plattentests",       "url": "https://www.plattentests.de",          "rss_url": "https://www.plattentests.de/rss.xml",                     "language": "de", "primary_genres": ["rock","indie","metal","electronic"]},
    {"name": "Musikreviews",       "url": "https://www.musikreviews.de",          "rss_url": "https://www.musikreviews.de/feed/",                       "language": "de", "primary_genres": ["rock","indie","metal"]},
    {"name": "Folk World",         "url": "https://www.folk-world.eu",            "rss_url": "https://www.folk-world.eu/rss.xml",                       "language": "de", "primary_genres": ["folk","world"]},
    {"name": "Terrorverlag",       "url": "https://www.terrorverlag.de",          "rss_url": None,                                                       "language": "de", "primary_genres": ["metal","punk","hardcore"]},
    {"name": "Byte.fm Blog",       "url": "https://www.byte.fm/blog",             "rss_url": "https://www.byte.fm/blog/feed/",                          "language": "de", "primary_genres": ["electronic","indie","jazz"]},
    {"name": "Unter Schafen",      "url": "https://www.unterschafen.com",         "rss_url": "https://www.unterschafen.com/feed/",                      "language": "de", "primary_genres": ["indie","alternative"]},
    {"name": "taz Musik",          "url": "https://taz.de/Musik",                 "rss_url": "https://taz.de/!p4608/rss.xml",                           "language": "de", "primary_genres": ["indie","electronic","jazz"]},
    {"name": "Subculture Magazin", "url": "https://www.subculture-magazin.de",    "rss_url": None,                                                       "language": "de", "primary_genres": ["underground","electronic","punk"]},
    {"name": "Ox Blog",            "url": "https://www.ox-fanzine.de/blog",       "rss_url": "https://www.ox-fanzine.de/blog/feed",                     "language": "de", "primary_genres": ["punk","hardcore"]},
    {"name": "Gitarre & Bass",     "url": "https://www.gitarrebass.de",           "rss_url": "https://www.gitarrebass.de/feed/",                        "language": "de", "primary_genres": ["rock","metal"]},

    # ─────────────────────────────────────────
    # ITALIAN (it)
    # ─────────────────────────────────────────
    {"name": "Sentireascoltare",   "url": "https://www.sentireascoltare.com",     "rss_url": "https://www.sentireascoltare.com/feed/",                  "language": "it", "primary_genres": ["indie","alternative","experimental"]},
    {"name": "Rumore Magazine",    "url": "https://www.rumoremag.com",            "rss_url": "https://www.rumoremag.com/feed/",                         "language": "it", "primary_genres": ["indie","alternative","rock"]},
    {"name": "Ondarock",           "url": "https://www.ondarock.it",              "rss_url": "https://www.ondarock.it/rss.xml",                         "language": "it", "primary_genres": ["rock","alternative","experimental"]},
    {"name": "Kalporz",            "url": "https://kalporz.com",                  "rss_url": "https://kalporz.com/feed/",                               "language": "it", "primary_genres": ["indie","alternative"]},
    {"name": "Rolling Stone IT",   "url": "https://www.rollingstone.it",          "rss_url": "https://www.rollingstone.it/feed/",                       "language": "it", "primary_genres": ["rock","pop","indie"]},
    {"name": "All Music Italia",   "url": "https://www.allmusicitalia.it",        "rss_url": "https://www.allmusicitalia.it/feed",                      "language": "it", "primary_genres": ["pop","rock","indie"]},
    {"name": "Soundwall",          "url": "https://www.soundwall.it",             "rss_url": "https://www.soundwall.it/feed/",                          "language": "it", "primary_genres": ["electronic","techno"]},
    {"name": "Jazzit",             "url": "https://www.jazzit.it",               "rss_url": "https://www.jazzit.it/feed/",                             "language": "it", "primary_genres": ["jazz"]},
    {"name": "Musica Jazz",        "url": "https://www.musicajazz.it",            "rss_url": "https://www.musicajazz.it/feed/",                         "language": "it", "primary_genres": ["jazz"]},
    {"name": "Blow Up",            "url": "https://www.blowupmagazine.it",        "rss_url": None,                                                       "language": "it", "primary_genres": ["electronic","experimental","underground"]},
    {"name": "Metal.it",           "url": "https://www.metal.it",                 "rss_url": "https://www.metal.it/rss.xml",                            "language": "it", "primary_genres": ["metal"]},
    {"name": "Necromance IT",      "url": "https://www.necromance.it",            "rss_url": "https://www.necromance.it/feed/",                         "language": "it", "primary_genres": ["metal","punk"]},
    {"name": "Il Mucchio",         "url": "https://www.mucchio.it",               "rss_url": "https://www.mucchio.it/feed/",                            "language": "it", "primary_genres": ["rock","indie","alternative"]},
    {"name": "Rockit",             "url": "https://www.rockit.it",               "rss_url": "https://www.rockit.it/rss",                               "language": "it", "primary_genres": ["indie","rock"]},
    {"name": "Indie for Bunnies",  "url": "https://www.indieforbunnies.com",      "rss_url": "https://www.indieforbunnies.com/feed/",                   "language": "it", "primary_genres": ["indie"]},
    {"name": "Bad Taste Musica",   "url": "https://www.badtaste.it/musica",       "rss_url": "https://www.badtaste.it/rss/musica",                      "language": "it", "primary_genres": ["rock","metal","indie","electronic"]},
    {"name": "Seenoise",           "url": "https://www.seenoise.it",              "rss_url": "https://www.seenoise.it/feed/",                           "language": "it", "primary_genres": ["indie","alternative"]},
    {"name": "XL Repubblica",      "url": "https://xl.repubblica.it",             "rss_url": "https://xl.repubblica.it/rss",                            "language": "it", "primary_genres": ["indie","electronic","alternative"]},
    {"name": "Wired IT Musica",    "url": "https://www.wired.it/play/musica",     "rss_url": "https://www.wired.it/rss",                                "language": "it", "primary_genres": ["electronic","pop","indie"]},
    {"name": "Classic Rock IT",    "url": "https://www.classicrockmag.it",        "rss_url": None,                                                       "language": "it", "primary_genres": ["rock"]},
    {"name": "Loud and Proud IT",  "url": "https://www.loudandproud.it",          "rss_url": "https://www.loudandproud.it/feed/",                       "language": "it", "primary_genres": ["metal","rock"]},
    {"name": "Hit Week",           "url": "https://www.hitweek.it",               "rss_url": "https://www.hitweek.it/rss",                              "language": "it", "primary_genres": ["pop","rock","indie"]},
    {"name": "Stordisco",          "url": "https://www.stordisco.com",            "rss_url": "https://www.stordisco.com/feed/",                         "language": "it", "primary_genres": ["electronic","techno"]},
    {"name": "Mucchio Extra",      "url": "https://www.mucchio.it/extra",         "rss_url": None,                                                       "language": "it", "primary_genres": ["underground","experimental"]},
    {"name": "Onda Rock Notizie",  "url": "https://www.ondarock.it/notizie",      "rss_url": "https://www.ondarock.it/notizie.rss",                     "language": "it", "primary_genres": ["rock","indie","metal"]},

    # ─────────────────────────────────────────
    # SPANISH (es)
    # ─────────────────────────────────────────
    {"name": "Mondosonoro",        "url": "https://www.mondosonoro.com",          "rss_url": "https://www.mondosonoro.com/feed/",                       "language": "es", "primary_genres": ["indie","alternative","rock"]},
    {"name": "Rolling Stone ES",   "url": "https://www.rollingstone.es",          "rss_url": "https://www.rollingstone.es/feed/",                       "language": "es", "primary_genres": ["rock","pop","indie"]},
    {"name": "Rockdelux",          "url": "https://www.rockdelux.com",            "rss_url": "https://www.rockdelux.com/rss/",                          "language": "es", "primary_genres": ["rock","indie","alternative"]},
    {"name": "Playground",         "url": "https://www.playgroundmag.net",        "rss_url": "https://www.playgroundmag.net/feed/",                     "language": "es", "primary_genres": ["electronic","hip-hop","indie"]},
    {"name": "Jenesaispop",        "url": "https://jenesaispop.com",              "rss_url": "https://jenesaispop.com/feed/",                           "language": "es", "primary_genres": ["pop","indie"]},
    {"name": "Go! Mag",            "url": "https://www.go-mag.com",               "rss_url": "https://www.go-mag.com/feed/",                            "language": "es", "primary_genres": ["electronic","techno","indie"]},
    {"name": "Rock Zone",          "url": "https://rockzone.es",                  "rss_url": "https://rockzone.es/feed/",                               "language": "es", "primary_genres": ["rock","metal"]},
    {"name": "Muzikalia",          "url": "https://www.muzikalia.com",            "rss_url": "https://www.muzikalia.com/feed/",                         "language": "es", "primary_genres": ["rock","indie","electronic","jazz"]},
    {"name": "Tomajazz",           "url": "https://www.tomajazz.com",             "rss_url": "https://www.tomajazz.com/feed/",                          "language": "es", "primary_genres": ["jazz"]},
    {"name": "Cuadernos de Jazz",  "url": "https://www.cuadernosdejazz.com",      "rss_url": "https://www.cuadernosdejazz.com/feed/",                   "language": "es", "primary_genres": ["jazz"]},
    {"name": "Metal Hammer ES",    "url": "https://www.metal-hammer.es",          "rss_url": "https://www.metal-hammer.es/feed/",                       "language": "es", "primary_genres": ["metal"]},
    {"name": "Necromance ES",      "url": "https://www.necromance.es",            "rss_url": "https://www.necromance.es/feed/",                         "language": "es", "primary_genres": ["metal"]},
    {"name": "La Fonoteca",        "url": "https://www.lafonoteca.net",           "rss_url": "https://www.lafonoteca.net/feed/",                        "language": "es", "primary_genres": ["rock","indie","electronic"]},
    {"name": "Face B",             "url": "https://faceb.es",                     "rss_url": "https://faceb.es/feed/",                                  "language": "es", "primary_genres": ["electronic","techno"]},
    {"name": "Ruta 66",            "url": "https://www.ruta66.es",               "rss_url": "https://www.ruta66.es/feed/",                             "language": "es", "primary_genres": ["rock","blues","folk"]},
    {"name": "Slowkiss Magazine",  "url": "https://www.slowkiss.es",              "rss_url": "https://www.slowkiss.es/feed/",                           "language": "es", "primary_genres": ["indie","dream-pop","shoegaze"]},
    {"name": "Indie Rocks!",       "url": "https://www.indiericksmagazine.com",   "rss_url": "https://www.indiericksmagazine.com/feed/",                "language": "es", "primary_genres": ["indie"]},
    {"name": "Zona de Obras",      "url": "https://www.zonadeobras.com",          "rss_url": "https://www.zonadeobras.com/feed/",                       "language": "es", "primary_genres": ["electronic","indie"]},
    {"name": "El Diario Música",   "url": "https://www.eldiario.es/cultura/musica","rss_url": "https://www.eldiario.es/rss/",                           "language": "es", "primary_genres": ["indie","pop","folk"]},
    {"name": "El País Música",     "url": "https://elpais.com/cultura/musica",    "rss_url": "https://feeds.elpais.com/mrss-v2/pages/ep/site/elpais.com/section/cultura/portada",  "language": "es", "primary_genres": ["pop","rock","classical","jazz"]},
    {"name": "Hipersónica",        "url": "https://hipersonica.com",              "rss_url": "https://hipersonica.com/feed/",                           "language": "es", "primary_genres": ["electronic","experimental"]},
    {"name": "Conexión Rock",      "url": "https://www.conexionrock.com",         "rss_url": "https://www.conexionrock.com/feed/",                      "language": "es", "primary_genres": ["rock","metal"]},
    {"name": "Radio 3 Blog",       "url": "https://www.rtve.es/radio/radio3",     "rss_url": "https://api2.rtve.es/rss/temas_radio3.xml",               "language": "es", "primary_genres": ["indie","world","jazz","experimental"]},
    {"name": "Hipersonica ES",     "url": "https://www.hipersonica.com",          "rss_url": "https://www.hipersonica.com/feed",                        "language": "es", "primary_genres": ["electronic","techno","experimental"]},
    {"name": "Cultura Inquieta Música","url": "https://culturainquieta.com/musica","rss_url": "https://culturainquieta.com/feed/",                     "language": "es", "primary_genres": ["indie","folk","world","jazz"]},
]


def seed_sources():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    client = create_client(url, key)

    print(f"Seeding {len(SOURCES)} sources...")
    inserted = 0
    skipped = 0
    errors = 0

    for source in SOURCES:
        try:
            result = (
                client.table("sources")
                .upsert(source, on_conflict="url")
                .execute()
            )
            inserted += 1
            print(f"  ✓  [{source['language'].upper()}] {source['name']}")
        except Exception as e:
            errors += 1
            print(f"  ✗  [{source['language'].upper()}] {source['name']} — {e}")

    print(f"\nDone. inserted/updated={inserted}  errors={errors}")


if __name__ == "__main__":
    seed_sources()
