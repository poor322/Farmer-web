from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import csv
import io
import math
import sqlite3
import requests

def init_db():
    conn = sqlite3.connect("farmer_portal.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            survey_number TEXT,
            phone_number TEXT,
            state TEXT,
            district TEXT,
            taluk TEXT,
            hobli TEXT,
            password TEXT
        )
    ''')
    # Migrations for new columns
    columns_to_add = [
        ('password', 'TEXT'),
        ('land_area_acres', 'REAL'),
        ('land_area_guntas', 'REAL'),
        ('current_crop', 'TEXT')
    ]
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE farmers ADD COLUMN {col_name} {col_type}')
            print(f"Added '{col_name}' column to farmers table.")
        except sqlite3.OperationalError:
            pass
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alert_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE,
            farmer_name TEXT,
            crop TEXT,
            taluk TEXT,
            district TEXT,
            whatsapp_enabled INTEGER DEFAULT 1,
            sms_enabled INTEGER DEFAULT 1,
            frequency TEXT DEFAULT 'daily_7am',
            min_surge_pct REAL DEFAULT 3.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


init_db()

app = FastAPI(title="Farmer Portal API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/coconut.jpg")
async def get_coconut_image():
    if os.path.exists("static/coconut.jpg"):
        return FileResponse("static/coconut.jpg", media_type="image/jpeg")
    return {"error": "Coconut image not found"}

DATA_FILE = "mock_db.json"
CSV_FILE = "dakshina_kannada_crop_dataset.csv"
MARKET_HISTORY_FILE = "dakshina_kannada_market_history.csv"
FARMER_DETAILS_FILE = "mangaluru_farmer_details.csv"

# OpenWeatherMap API configuration
WEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE")
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# data.gov.in API configuration for APMC market prices
DATAGOV_API_KEY = os.environ.get("DATAGOV_API_KEY", "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b")
DATAGOV_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
DATAGOV_BASE_URL = f"https://api.data.gov.in/resource/{DATAGOV_RESOURCE_ID}"

# Mapping: Our district names → data.gov.in API district names
# The API uses older/different spellings for some districts
DISTRICT_API_MAP = {
    "Bagalkot": "Bagalkot",
    "Ballari": "Bellary",
    "Belagavi": "Belgaum",
    "Bengaluru Rural": "Bangalore",
    "Bengaluru Urban": "Bangalore",
    "Bidar": "Bidar",
    "Chamarajanagar": "Chamarajanagar",
    "Chikkaballapur": "Chikkaballapur",
    "Chikkamagaluru": "Chikmagalur",
    "Chitradurga": "Chitradurga",
    "Dakshina Kannada": "Dakshina Kannada",
    "Davanagere": "Davangere",
    "Dharwad": "Dharwad",
    "Gadag": "Gadag",
    "Hassan": "Hassan",
    "Haveri": "Haveri",
    "Kalaburagi": "Gulbarga",
    "Kodagu": "Kodagu",
    "Kolar": "Kolar",
    "Koppal": "Koppal",
    "Mandya": "Mandya",
    "Mysuru": "Mysore",
    "Raichur": "Raichur",
    "Ramanagara": "Ramanagara",
    "Shivamogga": "Shimoga",
    "Tumakuru": "Tumkur",
    "Udupi": "Udupi",
    "Uttara Kannada": "Uttar Kannada",
    "Vijayanagara": "Bellary",
    "Vijayapura": "Bijapur",
    "Yadgir": "Yadgir",
}

TALUK_MAP = {
    "Bagalkot": ["Bagalkot", "Badami", "Hungund", "Mudhol", "Jamkhandi", "Bilagi", "Ilkal", "Rabkavi Banhatti", "Guledgudda"],
    "Ballari": ["Ballari", "Kurugodu", "Siruguppa", "Sandur", "Kampli"],
    "Belagavi": ["Belagavi", "Athani", "Bailhongal", "Chikkodi", "Gokak", "Hukkeri", "Khanapur", "Raybag", "Ramdurg", "Saundatti", "Kittur", "Nippani", "Kagawad", "Mudalagi"],
    "Bengaluru Rural": ["Devanahalli", "Doddaballapura", "Hoskote", "Nelamangala"],
    "Bengaluru Urban": ["Bengaluru North", "Bengaluru South", "Bengaluru East", "Anekal", "Yelahanka"],
    "Bidar": ["Bidar", "Basavakalyan", "Bhalki", "Homnabad", "Aurad", "Chitgoppa", "Kamalnagar", "Hulasur"],
    "Chamarajanagar": ["Chamarajanagar", "Gundlupet", "Kollegal", "Yelandur", "Hanur"],
    "Chikkaballapur": ["Chikkaballapura", "Bagepalli", "Chintamani", "Gauribidanur", "Gudibanda", "Sidlaghatta"],
    "Chikkamagaluru": ["Chikkamagaluru", "Kadur", "Koppa", "Mudigere", "Narasimharajapura", "Sringeri", "Tarikere", "Ajjampura", "Kalasa"],
    "Chitradurga": ["Chitradurga", "Challakere", "Hiriyur", "Holalkere", "Hosadurga", "Molakalmuru"],
    "Dakshina Kannada": ["Mangaluru", "Bantwal", "Puttur", "Belthangady", "Sullia", "Moodabidri", "Kadaba"],
    "Davanagere": ["Davanagere", "Harihar", "Channagiri", "Honnali", "Jagalur", "Nyamathi"],
    "Dharwad": ["Dharwad", "Hubballi", "Hubballi City", "Kalghatgi", "Kundgol", "Navalgund", "Annigeri", "Alnavar"],
    "Gadag": ["Gadag", "Naragund", "Mundargi", "Ron", "Shirhatti", "Gajendragad", "Lakshmeshwar"],
    "Hassan": ["Hassan", "Arsikere", "Channarayapatna", "Holenarasipura", "Sakleshpur", "Alur", "Arkalgud", "Belur"],
    "Haveri": ["Haveri", "Byadgi", "Hangal", "Hirekerur", "Ranebennur", "Savanur", "Shiggaon", "Rattihalli"],
    "Kalaburagi": ["Kalaburagi", "Afzalpur", "Aland", "Chincholi", "Chitapur", "Jevargi", "Sedam", "Kamalapura", "Kalagi", "Shahabad", "Yadrami"],
    "Kodagu": ["Madikeri", "Somwarpet", "Virajpet", "Ponnampet", "Kushalnagar"],
    "Kolar": ["Kolar", "Bangarapet", "Malur", "Mulbagal", "Srinivaspur", "KGF"],
    "Koppal": ["Koppal", "Gangawati", "Kushtagi", "Yelburga", "Kanakagiri", "Karatagi", "Kukanoor"],
    "Mandya": ["Mandya", "Maddur", "Malavalli", "Srirangapatna", "Krishnarajapet", "Nagamangala", "Pandavapura"],
    "Mysuru": ["Mysuru", "Hunsur", "Krishnarajanagara", "Nanjangud", "Heggadadevanakote", "Piriyapatna", "Tirumakudalu Narasipura", "Saligrama", "Sargur"],
    "Raichur": ["Raichur", "Devadurga", "Lingsugur", "Manvi", "Sindhanur", "Sirwar", "Maski"],
    "Ramanagara": ["Ramanagara", "Channapatna", "Kanakapura", "Magadi", "Harohalli"],
    "Shivamogga": ["Shivamogga", "Bhadravati", "Hosanagara", "Shikaripura", "Soraba", "Thirthahalli", "Sagar"],
    "Tumakuru": ["Tumakuru", "Chikkanayakanahalli", "Gubbi", "Koratagere", "Kunigal", "Madhugiri", "Pavagada", "Sira", "Tiptur", "Turuvekere"],
    "Udupi": ["Udupi", "Kundapura", "Karkala", "Byndoor", "Brahmavara", "Kaup", "Hebri"],
    "Uttara Kannada": ["Karwar", "Ankola", "Kumta", "Honnavar", "Bhatkal", "Sirsi", "Siddapur", "Yellapur", "Mundgod", "Haliyal", "Joida", "Dandeli"],
    "Vijayanagara": ["Hosapete", "Harapanahalli", "Hoovina Hadagali", "Hagari Bommanahalli", "Kotturu", "Kudligi"],
    "Vijayapura": ["Vijayapura", "Indi", "Basavana Bagevadi", "Sindagi", "Muddebihal", "Talikota", "Devara Hippargi", "Chadchan", "Babaleshwar", "Kolhar", "Nidagundi", "Tikota"],
    "Yadgir": ["Yadgir", "Shahapur", "Surapura", "Gurmitkal", "Vadagera", "Hunasagi"],

    # ── Maharashtra ──
    "Pune": ["Haveli", "Mulshi", "Maval", "Baramati", "Indapur", "Daund", "Shirur", "Junnar", "Ambegaon", "Khed", "Bhor", "Velhe", "Purandar"],
    "Mumbai City": ["Mumbai City"],
    "Mumbai Suburban": ["Andheri", "Borivali", "Kurla"],
    "Nagpur": ["Nagpur Urban", "Nagpur Rural", "Kamptee", "Hingna", "Saoner", "Parseoni", "Ramtek", "Mouda", "Umred", "Bhiwapur", "Kuhi", "Katol", "Narkhed"],
    "Nashik": ["Nashik", "Igatpuri", "Sinnar", "Dindori", "Peth", "Trimbakeshwar", "Kalwan", "Deola", "Surgana", "Baglan", "Malegaon", "Nandgaon", "Chandwad", "Yeola", "Niphad"],
    "Kolhapur": ["Karveer", "Panhala", "Shahuwadi", "Hatkanangale", "Shirol", "Kagal", "Radhanagari", "Gadhinglaj", "Chandgad", "Bhudargad", "Ajara", "Bavda"],
    "Thane": ["Thane", "Kalyan", "Bhiwandi", "Shahapur", "Murbad", "Ambarnath"],
    "Aurangabad": ["Aurangabad", "Paithan", "Vaijapur", "Gangapur", "Kannad", "Khuldabad", "Phulambri", "Sillod", "Soegaon"],
    "Solapur": ["Solapur North", "Solapur South", "Barshi", "Akkalkot", "Pandharpur", "Sangola", "Mangalvedhe", "Mohol", "Malshiras", "Karmala", "Madha"],
    "Satara": ["Satara", "Karad", "Patan", "Wai", "Mahabaleshwar", "Javali", "Koregaon", "Khandala", "Phaltan", "Man", "Khatav"],
    "Sangli": ["Miraj", "Sangli", "Walwa", "Shirala", "Khanapur", "Atpadi", "Kadegaon", "Jat"],
    "Ahmednagar": ["Ahmednagar", "Rahuri", "Nevasa", "Shevgaon", "Patoda", "Shrirampur", "Kopargaon", "Sangamner", "Akole"],
    "Ratnagiri": ["Ratnagiri", "Chiplun", "Rajapur", "Khed", "Mandangad", "Guhagar", "Dapoli", "Lanja", "Sangameshwar"],

    # ── Tamil Nadu ──
    "Chennai": ["Tondiarpet", "Fort Tondiarpet", "Egmore", "Mambalam", "Mylapore", "Perambur", "Ambattur"],
    "Coimbatore": ["Coimbatore North", "Coimbatore South", "Mettupalayam", "Sulur", "Pollachi", "Valparai", "Kinathukadavu", "Madukkarai", "Anamalai"],
    "Madurai": ["Madurai North", "Madurai South", "Melur", "Thirumangalam", "Usilampatti", "Peraiyur", "Vadipatti"],
    "Salem": ["Salem", "Attur", "Mettur", "Omalur", "Gangavalli", "Yercaud", "Edappadi", "Sankagiri"],
    "Tiruchirappalli": ["Tiruchirappalli", "Srirangam", "Lalgudi", "Musiri", "Manapparai", "Thuraiyur", "Marungapuri"],
    "Thanjavur": ["Thanjavur", "Kumbakonam", "Papanasam", "Orathanadu", "Pattukkottai", "Peravurani", "Thiruvidaimarudur", "Budalur"],
    "Erode": ["Erode", "Bhavani", "Gobichettipalayam", "Sathyamangalam", "Perundurai", "Anthiyur", "Nambiyur"],
    "Tirunelveli": ["Tirunelveli", "Palayamkottai", "Ambasamudram", "Cheranmahadevi", "Nanguneri", "Radhapuram", "Sankarankovil"],
    "Vellore": ["Vellore", "Gudiyatham", "Ambur", "Katpadi", "Anaicut"],
    "Dindigul": ["Dindigul", "Palani", "Kodaikanal", "Oddanchatram", "Natham", "Vedasandur", "Nilakkottai"],
    "Nilgiris": ["Udhagamandalam", "Coonoor", "Kotagiri", "Gudalur", "Pandalur", "Kundah"],
    "Kanchipuram": ["Kanchipuram", "Uthiramerur", "Sriperumbudur", "Walajabad"],
    "Tiruppur": ["Tiruppur North", "Tiruppur South", "Dharapuram", "Kangeyam", "Udumalpet", "Palladam", "Avinashi", "Mulanur"],

    # ── Andhra Pradesh ──
    "Visakhapatnam": ["Visakhapatnam Urban", "Gajuwaka", "Bheemunipatnam", "Anakapalli", "Pendurthi"],
    "Guntur": ["Guntur", "Tenali", "Mangalagiri", "Bapatla", "Narasaraopet", "Ponnuru", "Sattenapalle"],
    "Kurnool": ["Kurnool", "Nandyal", "Adoni", "Yemmiganur", "Mantralayam", "Dhone"],
    "Krishna": ["Machilipatnam", "Vijayawada", "Gudivada", "Nuzvid", "Jaggaiahpet", "Nandigama", "Tiruvuru"],
    "East Godavari": ["Kakinada", "Rajahmundry", "Amalapuram", "Ramachandrapuram", "Peddapuram", "Tuni"],
    "Chittoor": ["Chittoor", "Tirupati", "Madanapalle", "Punganur", "Palamaner", "Pileru", "Kuppam"],
    "Anantapur": ["Anantapur", "Guntakal", "Hindupur", "Dharmavaram", "Penukonda", "Kalyandurg", "Tadpatri"],
    "Kadapa": ["Kadapa", "Proddatur", "Rajampet", "Mydukur", "Jammalamadugu", "Badvel"],
    "Nellore": ["Nellore", "Kavali", "Gudur", "Atmakur", "Udayagiri", "Sullurpeta"],

    # ── Kerala ──
    "Thiruvananthapuram": ["Thiruvananthapuram", "Nedumangad", "Neyyattinkara", "Chirayinkeezhu", "Kattakada", "Varkala"],
    "Kollam": ["Kollam", "Karunagappally", "Kottarakkara", "Punalur", "Pathanapuram", "Chadayamangalam"],
    "Ernakulam": ["Kochi", "Aluva", "Muvattupuzha", "Kothamangalam", "Kunnathunad", "Paravur"],
    "Thrissur": ["Thrissur", "Kodungallur", "Chalakudy", "Irinjalakuda", "Mukundapuram", "Thalapilly", "Chavakkad"],
    "Palakkad": ["Palakkad", "Ottapalam", "Mannarkad", "Chittur", "Alathur", "Pattambi"],
    "Kozhikode": ["Kozhikode", "Vadakara", "Koyilandy", "Quilandy", "Thamarassery"],
    "Malappuram": ["Malappuram", "Ponnani", "Tirur", "Perinthalmanna", "Nilambur", "Ernad", "Kondotty"],
    "Kannur": ["Kannur", "Thalassery", "Taliparamba", "Iritty", "Payyanur"],
    "Kasaragod": ["Kasaragod", "Manjeshwar", "Hosdurg"],
    "Wayanad": ["Kalpetta", "Mananthavady", "Sultan Bathery"],
    "Idukki": ["Thodupuzha", "Devikulam", "Udumbanchola", "Peerumade", "Idukki"],
    "Kottayam": ["Kottayam", "Changanassery", "Vaikom", "Meenachil", "Kanjirapally"],
    "Alappuzha": ["Alappuzha", "Cherthala", "Karthikappally", "Ambalapuzha", "Kuttanad", "Mavelikkara"],
    "Pathanamthitta": ["Pathanamthitta", "Adoor", "Kozhencherry", "Ranni", "Thiruvalla", "Mallappally"],

    # ── Telangana ──
    "Hyderabad": ["Hyderabad Central", "Hyderabad North", "Hyderabad South", "Hyderabad East", "Hyderabad West"],
    "Rangareddy": ["Rajendranagar", "Chevella", "Shamshabad", "Ibrahimpatnam", "Maheshwaram", "Tandur"],
    "Karimnagar": ["Karimnagar", "Huzurabad", "Jammikunta", "Choppadandi", "Manakondur"],
    "Nizamabad": ["Nizamabad", "Bodhan", "Armoor", "Banswada", "Kamareddy"],
    "Khammam": ["Khammam", "Madhira", "Yellandu", "Sathupalli", "Kothagudem"],
    "Nalgonda": ["Nalgonda", "Bhongir", "Miryalaguda", "Devarakonda", "Suryapet"],
    "Warangal Urban": ["Warangal", "Hanamkonda", "Kazipet"],
    "Mahbubnagar": ["Mahbubnagar", "Narayanpet", "Gadwal", "Wanaparthy", "Kollapur", "Nagarkurnool"],
    "Medchal-Malkajgiri": ["Medchal", "Malkajgiri", "Keesara", "Ghatkesar", "Balanagar"],

    # ── Uttar Pradesh ──
    "Lucknow": ["Lucknow", "Mohanlalganj", "Bakshi Ka Talab", "Malihabad", "Sarojininagar"],
    "Varanasi": ["Varanasi", "Pindra", "Rajatalab", "Sevapuri", "Kashi Vidyapeeth"],
    "Agra": ["Agra", "Fatehabad", "Kheragarh", "Etmadpur", "Bah", "Shamshabad"],
    "Kanpur Nagar": ["Kanpur", "Bilhaur", "Ghatampur", "Bhitargaon", "Sarsaul"],
    "Meerut": ["Meerut", "Sardhana", "Mawana", "Parikshitgarh", "Hastinapur"],
    "Gorakhpur": ["Gorakhpur", "Sahjanwan", "Khajni", "Chauri Chaura", "Campierganj", "Bansgaon"],
    "Prayagraj": ["Prayagraj", "Phulpur", "Soraon", "Handia", "Meja", "Koraon", "Bara"],
    "Jhansi": ["Jhansi", "Mauranipur", "Garautha", "Moth", "Chirgaon", "Babina"],

    # ── Rajasthan ──
    "Jaipur": ["Jaipur", "Amber", "Sanganer", "Bassi", "Chaksu", "Jamwa Ramgarh", "Kotputli", "Shahpura", "Chomu", "Phulera"],
    "Jodhpur": ["Jodhpur", "Bilara", "Phalodi", "Shergarh", "Osian", "Bhopalgarh", "Luni"],
    "Udaipur": ["Udaipur", "Vallabhnagar", "Salumber", "Kherwara", "Girwa", "Gogunda", "Mavli"],
    "Kota": ["Kota", "Ladpura", "Ramganjmandi", "Sangod", "Itawa", "Digod"],
    "Bikaner": ["Bikaner", "Nokha", "Lunkaransar", "Kolayat", "Khajuwala"],
    "Ajmer": ["Ajmer", "Beawar", "Kishangarh", "Nasirabad", "Kekri", "Sarwar"],
    "Alwar": ["Alwar", "Behror", "Tijara", "Bansur", "Laxmangarh", "Rajgarh", "Kotkasim", "Thanagazi"],

    # ── Gujarat ──
    "Ahmedabad": ["Ahmedabad City", "Daskroi", "Dholka", "Sanand", "Bavla", "Detroj", "Dhandhuka", "Viramgam", "Mandal"],
    "Surat": ["Surat City", "Choryasi", "Palsana", "Kamrej", "Olpad", "Bardoli", "Mangrol", "Mandvi"],
    "Rajkot": ["Rajkot", "Lodhika", "Kotda Sangani", "Jasdan", "Gondal", "Jetpur", "Dhoraji", "Upleta"],
    "Vadodara": ["Vadodara", "Padra", "Savli", "Dabhoi", "Karjan", "Shinor", "Waghodia"],
    "Bhavnagar": ["Bhavnagar", "Sihor", "Palitana", "Mahuva", "Gariadhar", "Ghogha", "Talaja", "Botad"],
    "Kutch": ["Bhuj", "Anjar", "Mundra", "Mandvi", "Nakhatrana", "Abdasa", "Lakhpat", "Rapar", "Bhachau", "Gandhidham"],
    "Gandhinagar": ["Gandhinagar", "Kalol", "Dehgam", "Mansa"],

    # ── Madhya Pradesh ──
    "Bhopal": ["Huzur", "Berasia", "Phanda"],
    "Indore": ["Indore", "Depalpur", "Mhow", "Sanwer"],
    "Jabalpur": ["Jabalpur", "Sihora", "Patan", "Panagar", "Shahpura", "Kundam", "Bargi"],
    "Gwalior": ["Gwalior", "Morar", "Dabra", "Bhitarwar"],
    "Ujjain": ["Ujjain", "Nagda", "Tarana", "Mahidpur", "Khachrod", "Barnagar"],
    "Sagar": ["Sagar", "Rehli", "Bina", "Khurai", "Banda", "Rahatgarh"],

    # ── Punjab ──
    "Ludhiana": ["Ludhiana East", "Ludhiana West", "Khanna", "Samrala", "Jagraon", "Raikot", "Payal"],
    "Amritsar": ["Amritsar-I", "Amritsar-II", "Ajnala", "Baba Bakala", "Majitha", "Verka"],
    "Jalandhar": ["Jalandhar-I", "Jalandhar-II", "Nakodar", "Phillaur", "Shahkot", "Adampur"],
    "Patiala": ["Patiala", "Rajpura", "Nabha", "Samana", "Patran"],
    "Bathinda": ["Bathinda", "Rampura Phul", "Talwandi Sabo", "Sangat", "Maur"],

    # ── Haryana ──
    "Gurugram": ["Gurugram", "Sohna", "Pataudi", "Farrukhnagar"],
    "Karnal": ["Karnal", "Assandh", "Indri", "Nilokheri", "Gharaunda"],
    "Ambala": ["Ambala", "Barara", "Naraingarh", "Shahzadpur"],
    "Hisar": ["Hisar", "Hansi", "Barwala", "Narnaund", "Adampur"],
    "Panipat": ["Panipat", "Samalkha", "Israna", "Madlauda"],
    "Faridabad": ["Faridabad", "Ballabhgarh", "Palwal", "Hathin"],
}

# Coordinates map for Karnataka taluks/districts to allow weather lookup and map centering without GPS.
TALUK_COORDS = {
    # Dakshina Kannada
    "Mangaluru": (12.9141, 74.8560),
    "Bantwal": (12.9000, 75.0333),
    "Puttur": (12.7667, 75.2167),
    "Belthangady": (12.9667, 75.3000),
    "Sullia": (12.5667, 75.3833),
    "Moodabidri": (13.0700, 74.9900),
    "Kadaba": (12.7833, 75.4167),
    # Udupi
    "Udupi": (13.3409, 74.7421),
    "Karkala": (13.2167, 74.9833),
    "Kundapura": (13.6244, 74.6936),
    "Byndoor": (13.8667, 74.6333),
    "Brahmavara": (13.4167, 74.7500),
    "Kaup": (13.2167, 74.7500),
    "Hebri": (13.4667, 75.0667),
    # Uttara Kannada
    "Karwar": (14.8000, 74.1300),
    "Ankola": (14.6667, 74.3000),
    "Kumta": (14.4333, 74.4167),
    "Honnavar": (14.2833, 74.4500),
    "Bhatkal": (13.9667, 74.5500),
    "Sirsi": (14.6195, 74.8441),
    "Siddapur": (14.3333, 74.8833),
    "Yellapur": (14.9667, 74.7000),
    "Mundgod": (14.9667, 75.0333),
    "Haliyal": (15.3333, 74.7667),
    "Joida": (15.1500, 74.4833),
    "Dandeli": (15.2500, 74.6167),
    # Bengaluru Urban
    "Bengaluru North": (13.0500, 77.5800),
    "Bengaluru South": (12.9000, 77.5800),
    "Bengaluru East": (12.9700, 77.6500),
    "Yelahanka": (13.1008, 77.5963),
    "Anekal": (12.7107, 77.6975),
    # Bengaluru Rural
    "Devanahalli": (13.2483, 77.7128),
    "Doddaballapura": (13.2925, 77.5428),
    "Hoskote": (13.0706, 77.7981),
    "Nelamangala": (13.0978, 77.3944),
    # Hassan
    "Hassan": (13.0050, 76.1028),
    "Sakleshpur": (12.9436, 75.7861),
    "Sakleshpura": (12.9436, 75.7861),
    # Chikkamagaluru
    "Chikkamagaluru": (13.3161, 75.7720),
    "Sringeri": (13.4214, 75.2572),
    # Kodagu
    "Madikeri": (12.4244, 75.7389),
    "Somwarpet": (12.5958, 75.8622),
    "Virajpet": (12.1994, 75.8033),
    # Shivamogga
    "Shivamogga": (13.9299, 75.5681),
    "Sagar": (14.1667, 75.0333),
    "Sagara": (14.1667, 75.0333),
    # Tumakuru
    "Tumakuru": (13.3392, 77.1140),
    # Mandya
    "Mandya": (12.5218, 76.8973),
    # Mysuru
    "Mysuru": (12.2958, 76.6394),
    # Kalaburagi
    "Kalaburagi": (17.3297, 76.8343),
    # Belagavi
    "Belagavi": (15.8497, 74.4977),
    # Davanagere
    "Davanagere": (14.4644, 75.9219),
    # Dharwad
    "Dharwad": (15.4589, 75.0078),
    # Bellary
    "Ballari": (15.1394, 76.9214),
    # Bagalkot
    "Bagalkot": (16.1817, 75.6958),
    # Bidar
    "Bidar": (17.9104, 77.5199),
    # Vijayapura
    "Vijayapura": (16.8302, 75.7100),
}

# Coordinate map for all hoblis in Uttara Kannada district to center the map precisely.
HOBLI_COORDS = {
    # Karwar taluk hoblis
    "Karwar Kasaba": (14.8000, 74.1300),
    "Asnoti": (14.8350, 74.1680),
    "Majali": (14.8780, 74.1080),
    "Shirwad": (14.7950, 74.1750),
    
    # Ankola taluk hoblis
    "Ankola Kasaba": (14.6667, 74.3000),
    "Hattikeri": (14.6850, 74.3300),
    "Poojageri": (14.6420, 74.3220),
    
    # Kumta taluk hoblis
    "Kumta Kasaba": (14.4333, 74.4167),
    "Gokarna": (14.5420, 74.3160),
    "Hiregutti": (14.5020, 74.3720),
    "Mirjan": (14.4850, 74.4180),
    
    # Honnavar taluk hoblis
    "Honnavar Kasaba": (14.2833, 74.4500),
    "Manki": (14.1850, 74.4620),
    "Gersoppa": (14.2380, 74.5850),
    "Haldipur": (14.3250, 74.4320),
    
    # Bhatkal taluk hoblis
    "Bhatkal Kasaba": (13.9667, 74.5500),
    "Shirali": (14.0150, 74.5250),
    "Murdeshwar": (14.0940, 74.4850),
    
    # Sirsi taluk hoblis
    "Sirsi Kasaba": (14.6195, 74.8441),
    "Banavasi": (14.5320, 75.0180),
    "Sampkhand": (14.6880, 74.7650),
    "Hulekal": (14.6350, 74.7320),
    
    # Siddapur taluk hoblis
    "Siddapur Kasaba": (14.3333, 74.8833),
    "Bilgi": (14.3680, 74.8080),
    "Kyadgi": (14.2650, 74.9120),
    "Harsikatta": (14.3980, 74.9250),

    # Yellapur taluk hoblis
    "Yellapur Kasaba": (14.9667, 74.7000),
    "Kirwatti": (15.0150, 74.8320),
    "Manchikere": (14.8850, 74.7620),

    # Mundgod taluk hoblis
    "Mundgod Kasaba": (14.9667, 75.0333),
    "Koppa": (14.8820, 75.0150),
    "Pala": (15.0250, 75.0580),

    # Haliyal taluk hoblis
    "Haliyal Kasaba": (15.3333, 74.7667),
    "Tergaon": (15.3950, 74.7250),
    "Mangalwad": (15.2480, 74.8150),

    # Joida taluk hoblis
    "Joida Kasaba": (15.1500, 74.4833),
    "Gund": (15.0780, 74.3250),
    "Castlerock": (15.4320, 74.3350),
    "Ulvi": (15.0120, 74.5050),

    # Dandeli taluk hoblis
    "Dandeli Kasaba": (15.2500, 74.6167),
    "Ambikanagar": (15.1780, 74.6320)
}

DISTRICT_BASELINES = {
    "Dakshina Kannada": {"soil_type": "Laterite", "ph": 5.8, "avg_temp": 28.0, "avg_humidity": 85, "avg_rainfall": 3800},
    "Udupi": {"soil_type": "Laterite", "ph": 5.9, "avg_temp": 28.5, "avg_humidity": 85, "avg_rainfall": 3700},
    "Uttara Kannada": {"soil_type": "Laterite", "ph": 5.7, "avg_temp": 27.5, "avg_humidity": 82, "avg_rainfall": 3200},
    
    "Chikkamagaluru": {"soil_type": "Red Clayey", "ph": 5.9, "avg_temp": 22.0, "avg_humidity": 75, "avg_rainfall": 2100},
    "Kodagu": {"soil_type": "Red Clayey", "ph": 5.8, "avg_temp": 21.0, "avg_humidity": 78, "avg_rainfall": 2300},
    "Hassan": {"soil_type": "Red Sandy", "ph": 6.2, "avg_temp": 24.0, "avg_humidity": 72, "avg_rainfall": 1200},
    "Shivamogga": {"soil_type": "Red Loamy", "ph": 6.1, "avg_temp": 25.5, "avg_humidity": 74, "avg_rainfall": 1800},

    "Bengaluru Rural": {"soil_type": "Red Sandy", "ph": 6.5, "avg_temp": 26.0, "avg_humidity": 62, "avg_rainfall": 820},
    "Bengaluru Urban": {"soil_type": "Red Sandy", "ph": 6.6, "avg_temp": 26.2, "avg_humidity": 60, "avg_rainfall": 800},
    "Kolar": {"soil_type": "Red Sandy", "ph": 6.8, "avg_temp": 27.0, "avg_humidity": 58, "avg_rainfall": 720},
    "Chikkaballapur": {"soil_type": "Red Sandy", "ph": 6.7, "avg_temp": 26.8, "avg_humidity": 59, "avg_rainfall": 750},
    "Tumakuru": {"soil_type": "Red Loam", "ph": 6.6, "avg_temp": 27.2, "avg_humidity": 56, "avg_rainfall": 780},
    "Ramanagara": {"soil_type": "Red Sandy", "ph": 6.4, "avg_temp": 27.5, "avg_humidity": 61, "avg_rainfall": 840},
    "Mandya": {"soil_type": "Red Sandy", "ph": 6.8, "avg_temp": 28.0, "avg_humidity": 63, "avg_rainfall": 710},
    "Mysuru": {"soil_type": "Red Loamy", "ph": 6.7, "avg_temp": 26.8, "avg_humidity": 65, "avg_rainfall": 790},
    "Chamarajanagar": {"soil_type": "Red Loamy", "ph": 6.8, "avg_temp": 27.0, "avg_humidity": 62, "avg_rainfall": 730},

    "Bagalkot": {"soil_type": "Black Clayey", "ph": 7.8, "avg_temp": 32.5, "avg_humidity": 45, "avg_rainfall": 560},
    "Ballari": {"soil_type": "Black Clayey", "ph": 7.9, "avg_temp": 33.8, "avg_humidity": 42, "avg_rainfall": 580},
    "Belagavi": {"soil_type": "Black Clayey", "ph": 7.4, "avg_temp": 27.2, "avg_humidity": 68, "avg_rainfall": 880},
    "Bidar": {"soil_type": "Black Clayey", "ph": 7.6, "avg_temp": 31.0, "avg_humidity": 50, "avg_rainfall": 820},
    "Chitradurga": {"soil_type": "Mixed Red & Black", "ph": 7.5, "avg_temp": 29.5, "avg_humidity": 52, "avg_rainfall": 590},
    "Davanagere": {"soil_type": "Mixed Red & Black", "ph": 7.4, "avg_temp": 29.8, "avg_humidity": 55, "avg_rainfall": 680},
    "Dharwad": {"soil_type": "Black Clayey", "ph": 7.6, "avg_temp": 28.5, "avg_humidity": 62, "avg_rainfall": 740},
    "Gadag": {"soil_type": "Black Clayey", "ph": 7.8, "avg_temp": 31.0, "avg_humidity": 48, "avg_rainfall": 610},
    "Haveri": {"soil_type": "Red Loamy", "ph": 6.8, "avg_temp": 29.0, "avg_humidity": 64, "avg_rainfall": 780},
    "Kalaburagi": {"soil_type": "Black Clayey", "ph": 8.0, "avg_temp": 34.0, "avg_humidity": 44, "avg_rainfall": 750},
    "Koppal": {"soil_type": "Mixed Red & Black", "ph": 7.9, "avg_temp": 32.8, "avg_humidity": 45, "avg_rainfall": 570},
    "Raichur": {"soil_type": "Black Clayey", "ph": 8.1, "avg_temp": 34.5, "avg_humidity": 43, "avg_rainfall": 610},
    "Vijayanagara": {"soil_type": "Black Clayey", "ph": 7.8, "avg_temp": 33.2, "avg_humidity": 43, "avg_rainfall": 590},
    "Vijayapura": {"soil_type": "Black Clayey", "ph": 8.2, "avg_temp": 33.5, "avg_humidity": 40, "avg_rainfall": 550},
    "Yadgir": {"soil_type": "Black Clayey", "ph": 8.0, "avg_temp": 33.8, "avg_humidity": 44, "avg_rainfall": 720},

    # ── Maharashtra ──
    "Pune": {"soil_type": "Red Laterite", "ph": 6.5, "avg_temp": 25.5, "avg_humidity": 60, "avg_rainfall": 720},
    "Mumbai City": {"soil_type": "Coastal Alluvial", "ph": 7.0, "avg_temp": 27.5, "avg_humidity": 80, "avg_rainfall": 2400},
    "Mumbai Suburban": {"soil_type": "Coastal Alluvial", "ph": 7.0, "avg_temp": 27.5, "avg_humidity": 80, "avg_rainfall": 2400},
    "Nagpur": {"soil_type": "Black Cotton", "ph": 7.8, "avg_temp": 30.5, "avg_humidity": 55, "avg_rainfall": 1100},
    "Nashik": {"soil_type": "Red Laterite", "ph": 6.8, "avg_temp": 26.0, "avg_humidity": 58, "avg_rainfall": 670},
    "Kolhapur": {"soil_type": "Laterite", "ph": 6.2, "avg_temp": 26.5, "avg_humidity": 72, "avg_rainfall": 1200},
    "Thane": {"soil_type": "Laterite", "ph": 6.5, "avg_temp": 27.0, "avg_humidity": 78, "avg_rainfall": 2500},
    "Aurangabad": {"soil_type": "Black Cotton", "ph": 7.5, "avg_temp": 29.0, "avg_humidity": 50, "avg_rainfall": 650},
    "Solapur": {"soil_type": "Black Cotton", "ph": 7.8, "avg_temp": 30.0, "avg_humidity": 45, "avg_rainfall": 550},
    "Satara": {"soil_type": "Laterite", "ph": 6.4, "avg_temp": 25.0, "avg_humidity": 65, "avg_rainfall": 900},
    "Sangli": {"soil_type": "Black Cotton", "ph": 7.5, "avg_temp": 28.0, "avg_humidity": 55, "avg_rainfall": 600},
    "Ahmednagar": {"soil_type": "Red Laterite", "ph": 6.8, "avg_temp": 27.5, "avg_humidity": 55, "avg_rainfall": 650},
    "Ratnagiri": {"soil_type": "Laterite", "ph": 5.8, "avg_temp": 27.0, "avg_humidity": 80, "avg_rainfall": 3200},

    # ── Tamil Nadu ──
    "Chennai": {"soil_type": "Coastal Alluvial", "ph": 7.2, "avg_temp": 28.5, "avg_humidity": 75, "avg_rainfall": 1400},
    "Coimbatore": {"soil_type": "Red Loamy", "ph": 6.8, "avg_temp": 27.0, "avg_humidity": 60, "avg_rainfall": 700},
    "Madurai": {"soil_type": "Black Cotton", "ph": 7.5, "avg_temp": 29.5, "avg_humidity": 65, "avg_rainfall": 850},
    "Salem": {"soil_type": "Red Sandy", "ph": 6.5, "avg_temp": 28.0, "avg_humidity": 55, "avg_rainfall": 900},
    "Thanjavur": {"soil_type": "Alluvial", "ph": 7.0, "avg_temp": 29.0, "avg_humidity": 70, "avg_rainfall": 1000},
    "Tiruchirappalli": {"soil_type": "Red Sandy", "ph": 7.0, "avg_temp": 29.0, "avg_humidity": 60, "avg_rainfall": 800},
    "Tirunelveli": {"soil_type": "Red Loamy", "ph": 6.5, "avg_temp": 28.5, "avg_humidity": 70, "avg_rainfall": 750},
    "Erode": {"soil_type": "Red Loamy", "ph": 6.8, "avg_temp": 28.0, "avg_humidity": 58, "avg_rainfall": 650},
    "Nilgiris": {"soil_type": "Laterite", "ph": 5.5, "avg_temp": 16.0, "avg_humidity": 80, "avg_rainfall": 1900},
    "Vellore": {"soil_type": "Red Sandy", "ph": 6.8, "avg_temp": 28.5, "avg_humidity": 62, "avg_rainfall": 950},
    "Dindigul": {"soil_type": "Red Loamy", "ph": 6.5, "avg_temp": 28.0, "avg_humidity": 62, "avg_rainfall": 800},
    "Tiruppur": {"soil_type": "Red Loamy", "ph": 6.8, "avg_temp": 27.5, "avg_humidity": 60, "avg_rainfall": 700},

    # ── Andhra Pradesh ──
    "Visakhapatnam": {"soil_type": "Red Sandy", "ph": 6.5, "avg_temp": 28.0, "avg_humidity": 75, "avg_rainfall": 1100},
    "Guntur": {"soil_type": "Black Cotton", "ph": 7.5, "avg_temp": 30.0, "avg_humidity": 65, "avg_rainfall": 800},
    "Kurnool": {"soil_type": "Black Cotton", "ph": 7.8, "avg_temp": 31.0, "avg_humidity": 50, "avg_rainfall": 600},
    "Krishna": {"soil_type": "Alluvial", "ph": 7.0, "avg_temp": 29.5, "avg_humidity": 70, "avg_rainfall": 1000},
    "East Godavari": {"soil_type": "Alluvial", "ph": 6.8, "avg_temp": 28.5, "avg_humidity": 75, "avg_rainfall": 1200},
    "Chittoor": {"soil_type": "Red Loamy", "ph": 6.5, "avg_temp": 27.5, "avg_humidity": 60, "avg_rainfall": 750},
    "Anantapur": {"soil_type": "Red Sandy", "ph": 7.2, "avg_temp": 30.5, "avg_humidity": 45, "avg_rainfall": 550},
    "Kadapa": {"soil_type": "Red Sandy", "ph": 7.0, "avg_temp": 30.0, "avg_humidity": 52, "avg_rainfall": 650},
    "Nellore": {"soil_type": "Sandy Loam", "ph": 6.8, "avg_temp": 29.5, "avg_humidity": 70, "avg_rainfall": 1000},

    # ── Kerala ──
    "Thiruvananthapuram": {"soil_type": "Laterite", "ph": 5.5, "avg_temp": 27.5, "avg_humidity": 80, "avg_rainfall": 1800},
    "Ernakulam": {"soil_type": "Laterite", "ph": 5.8, "avg_temp": 27.0, "avg_humidity": 78, "avg_rainfall": 3100},
    "Palakkad": {"soil_type": "Red Loamy", "ph": 6.2, "avg_temp": 28.0, "avg_humidity": 70, "avg_rainfall": 2200},
    "Kozhikode": {"soil_type": "Laterite", "ph": 5.5, "avg_temp": 27.0, "avg_humidity": 82, "avg_rainfall": 3500},
    "Wayanad": {"soil_type": "Forest Loam", "ph": 5.8, "avg_temp": 23.0, "avg_humidity": 85, "avg_rainfall": 2800},
    "Idukki": {"soil_type": "Forest Loam", "ph": 5.2, "avg_temp": 22.0, "avg_humidity": 85, "avg_rainfall": 3200},
    "Kasaragod": {"soil_type": "Laterite", "ph": 5.5, "avg_temp": 28.0, "avg_humidity": 80, "avg_rainfall": 3400},
    "Thrissur": {"soil_type": "Laterite", "ph": 5.8, "avg_temp": 27.5, "avg_humidity": 78, "avg_rainfall": 3000},
    "Malappuram": {"soil_type": "Laterite", "ph": 5.6, "avg_temp": 27.5, "avg_humidity": 80, "avg_rainfall": 3200},
    "Kollam": {"soil_type": "Laterite", "ph": 5.5, "avg_temp": 28.0, "avg_humidity": 80, "avg_rainfall": 2600},
    "Kottayam": {"soil_type": "Red Loamy", "ph": 5.5, "avg_temp": 27.0, "avg_humidity": 80, "avg_rainfall": 3000},
    "Alappuzha": {"soil_type": "Coastal Alluvial", "ph": 6.0, "avg_temp": 28.0, "avg_humidity": 80, "avg_rainfall": 2700},
    "Kannur": {"soil_type": "Laterite", "ph": 5.5, "avg_temp": 27.5, "avg_humidity": 80, "avg_rainfall": 3400},

    # ── Telangana ──
    "Hyderabad": {"soil_type": "Red Sandy", "ph": 7.0, "avg_temp": 27.5, "avg_humidity": 55, "avg_rainfall": 800},
    "Rangareddy": {"soil_type": "Red Sandy", "ph": 7.0, "avg_temp": 28.0, "avg_humidity": 55, "avg_rainfall": 750},
    "Karimnagar": {"soil_type": "Black Cotton", "ph": 7.5, "avg_temp": 29.0, "avg_humidity": 58, "avg_rainfall": 900},
    "Nizamabad": {"soil_type": "Black Cotton", "ph": 7.2, "avg_temp": 28.5, "avg_humidity": 60, "avg_rainfall": 950},
    "Khammam": {"soil_type": "Red Loamy", "ph": 6.5, "avg_temp": 28.5, "avg_humidity": 65, "avg_rainfall": 1100},
    "Nalgonda": {"soil_type": "Red Sandy", "ph": 7.0, "avg_temp": 29.5, "avg_humidity": 55, "avg_rainfall": 700},
    "Warangal Urban": {"soil_type": "Black Cotton", "ph": 7.2, "avg_temp": 28.5, "avg_humidity": 60, "avg_rainfall": 950},
    "Medchal-Malkajgiri": {"soil_type": "Red Sandy", "ph": 6.8, "avg_temp": 27.5, "avg_humidity": 58, "avg_rainfall": 850},

    # ── Uttar Pradesh ──
    "Lucknow": {"soil_type": "Alluvial", "ph": 7.5, "avg_temp": 26.0, "avg_humidity": 65, "avg_rainfall": 1000},
    "Varanasi": {"soil_type": "Alluvial", "ph": 7.2, "avg_temp": 27.0, "avg_humidity": 68, "avg_rainfall": 1050},
    "Agra": {"soil_type": "Alluvial", "ph": 7.8, "avg_temp": 26.5, "avg_humidity": 55, "avg_rainfall": 650},
    "Kanpur Nagar": {"soil_type": "Alluvial", "ph": 7.5, "avg_temp": 26.0, "avg_humidity": 60, "avg_rainfall": 800},
    "Meerut": {"soil_type": "Alluvial", "ph": 7.5, "avg_temp": 24.5, "avg_humidity": 65, "avg_rainfall": 850},
    "Gorakhpur": {"soil_type": "Alluvial", "ph": 7.0, "avg_temp": 26.5, "avg_humidity": 72, "avg_rainfall": 1300},
    "Prayagraj": {"soil_type": "Alluvial", "ph": 7.2, "avg_temp": 27.0, "avg_humidity": 68, "avg_rainfall": 1050},

    # ── Rajasthan ──
    "Jaipur": {"soil_type": "Sandy Loam", "ph": 7.8, "avg_temp": 27.0, "avg_humidity": 40, "avg_rainfall": 600},
    "Jodhpur": {"soil_type": "Desert Sandy", "ph": 8.2, "avg_temp": 28.5, "avg_humidity": 35, "avg_rainfall": 360},
    "Udaipur": {"soil_type": "Red Loamy", "ph": 7.0, "avg_temp": 25.0, "avg_humidity": 50, "avg_rainfall": 650},
    "Kota": {"soil_type": "Black Cotton", "ph": 7.5, "avg_temp": 27.0, "avg_humidity": 50, "avg_rainfall": 800},
    "Bikaner": {"soil_type": "Desert Sandy", "ph": 8.5, "avg_temp": 28.0, "avg_humidity": 30, "avg_rainfall": 250},
    "Ajmer": {"soil_type": "Sandy Loam", "ph": 7.5, "avg_temp": 26.5, "avg_humidity": 42, "avg_rainfall": 520},
    "Alwar": {"soil_type": "Sandy Loam", "ph": 7.5, "avg_temp": 26.0, "avg_humidity": 45, "avg_rainfall": 650},

    # ── Gujarat ──
    "Ahmedabad": {"soil_type": "Sandy Loam", "ph": 7.5, "avg_temp": 28.0, "avg_humidity": 55, "avg_rainfall": 750},
    "Surat": {"soil_type": "Black Cotton", "ph": 7.0, "avg_temp": 28.0, "avg_humidity": 70, "avg_rainfall": 1200},
    "Rajkot": {"soil_type": "Black Cotton", "ph": 7.5, "avg_temp": 27.5, "avg_humidity": 55, "avg_rainfall": 600},
    "Kutch": {"soil_type": "Desert Sandy", "ph": 8.0, "avg_temp": 28.5, "avg_humidity": 40, "avg_rainfall": 350},
    "Vadodara": {"soil_type": "Black Cotton", "ph": 7.2, "avg_temp": 28.0, "avg_humidity": 60, "avg_rainfall": 950},
    "Bhavnagar": {"soil_type": "Black Cotton", "ph": 7.5, "avg_temp": 27.5, "avg_humidity": 60, "avg_rainfall": 650},
    "Gandhinagar": {"soil_type": "Sandy Loam", "ph": 7.5, "avg_temp": 27.5, "avg_humidity": 55, "avg_rainfall": 780},

    # ── Madhya Pradesh ──
    "Bhopal": {"soil_type": "Black Cotton", "ph": 7.5, "avg_temp": 26.0, "avg_humidity": 58, "avg_rainfall": 1200},
    "Indore": {"soil_type": "Black Cotton", "ph": 7.8, "avg_temp": 26.5, "avg_humidity": 55, "avg_rainfall": 950},
    "Jabalpur": {"soil_type": "Black Cotton", "ph": 7.2, "avg_temp": 26.5, "avg_humidity": 60, "avg_rainfall": 1400},
    "Gwalior": {"soil_type": "Alluvial", "ph": 7.5, "avg_temp": 27.0, "avg_humidity": 50, "avg_rainfall": 800},
    "Ujjain": {"soil_type": "Black Cotton", "ph": 7.8, "avg_temp": 27.0, "avg_humidity": 52, "avg_rainfall": 900},
    "Sagar": {"soil_type": "Black Cotton", "ph": 7.5, "avg_temp": 26.5, "avg_humidity": 55, "avg_rainfall": 1100},

    # ── Punjab ──
    "Ludhiana": {"soil_type": "Alluvial", "ph": 7.5, "avg_temp": 24.5, "avg_humidity": 65, "avg_rainfall": 750},
    "Amritsar": {"soil_type": "Alluvial", "ph": 7.8, "avg_temp": 24.0, "avg_humidity": 62, "avg_rainfall": 680},
    "Jalandhar": {"soil_type": "Alluvial", "ph": 7.5, "avg_temp": 24.0, "avg_humidity": 62, "avg_rainfall": 700},
    "Patiala": {"soil_type": "Alluvial", "ph": 7.5, "avg_temp": 24.5, "avg_humidity": 60, "avg_rainfall": 700},
    "Bathinda": {"soil_type": "Sandy Loam", "ph": 8.0, "avg_temp": 25.0, "avg_humidity": 50, "avg_rainfall": 400},

    # ── Haryana ──
    "Gurugram": {"soil_type": "Sandy Loam", "ph": 7.8, "avg_temp": 25.5, "avg_humidity": 55, "avg_rainfall": 600},
    "Karnal": {"soil_type": "Alluvial", "ph": 7.5, "avg_temp": 24.5, "avg_humidity": 65, "avg_rainfall": 750},
    "Hisar": {"soil_type": "Sandy Loam", "ph": 8.0, "avg_temp": 26.0, "avg_humidity": 48, "avg_rainfall": 450},
    "Ambala": {"soil_type": "Alluvial", "ph": 7.2, "avg_temp": 24.0, "avg_humidity": 65, "avg_rainfall": 850},
    "Faridabad": {"soil_type": "Sandy Loam", "ph": 7.8, "avg_temp": 25.5, "avg_humidity": 58, "avg_rainfall": 680}
}

CROP_PROFILES = {
    "Banana": {"ph": 6.0, "temp": 28.0, "humidity": 80.0, "rainfall": 2000.0},
    "Arecanut": {"ph": 6.0, "temp": 26.0, "humidity": 80.0, "rainfall": 2500.0},
    "Pepper": {"ph": 5.8, "temp": 27.0, "humidity": 85.0, "rainfall": 2200.0},
    "Cashew": {"ph": 5.5, "temp": 30.0, "humidity": 75.0, "rainfall": 1500.0},
    "Rubber": {"ph": 5.5, "temp": 28.0, "humidity": 85.0, "rainfall": 3000.0},
    "Coconut": {"ph": 6.5, "temp": 29.0, "humidity": 80.0, "rainfall": 1800.0},
    "Rice": {"ph": 6.2, "temp": 29.0, "humidity": 85.0, "rainfall": 1500.0},
    
    "Coffee": {"ph": 5.8, "temp": 22.0, "humidity": 80.0, "rainfall": 2000.0},
    "Cardamom": {"ph": 5.5, "temp": 20.0, "humidity": 85.0, "rainfall": 2500.0},
    "Ginger": {"ph": 6.0, "temp": 25.0, "humidity": 75.0, "rainfall": 1800.0},

    "Jowar": {"ph": 7.5, "temp": 32.0, "humidity": 45.0, "rainfall": 600.0},
    "Cotton": {"ph": 7.8, "temp": 31.0, "humidity": 50.0, "rainfall": 700.0},
    "Maize": {"ph": 6.5, "temp": 28.0, "humidity": 60.0, "rainfall": 800.0},
    "Bengal Gram": {"ph": 7.2, "temp": 24.0, "humidity": 45.0, "rainfall": 500.0},
    "Red Gram": {"ph": 7.5, "temp": 30.0, "humidity": 45.0, "rainfall": 650.0},
    "Wheat": {"ph": 7.0, "temp": 22.0, "humidity": 50.0, "rainfall": 600.0},
    "Pomegranate": {"ph": 7.5, "temp": 32.0, "humidity": 40.0, "rainfall": 600.0},
    
    "Ragi": {"ph": 6.5, "temp": 27.0, "humidity": 60.0, "rainfall": 750.0},
    "Groundnut": {"ph": 6.5, "temp": 28.0, "humidity": 55.0, "rainfall": 700.0},
    "Sugarcane": {"ph": 7.0, "temp": 29.0, "humidity": 70.0, "rainfall": 1200.0},
    "Tomato": {"ph": 6.2, "temp": 26.0, "humidity": 60.0, "rainfall": 750.0},
    "Mango": {"ph": 6.5, "temp": 28.0, "humidity": 60.0, "rainfall": 900.0},
    "Onion": {"ph": 6.5, "temp": 25.0, "humidity": 65.0, "rainfall": 700.0},
    "Potato": {"ph": 5.5, "temp": 20.0, "humidity": 70.0, "rainfall": 800.0},
    "Turmeric": {"ph": 6.0, "temp": 27.0, "humidity": 80.0, "rainfall": 1500.0},
    "Chilli": {"ph": 6.5, "temp": 28.0, "humidity": 65.0, "rainfall": 900.0},
}

# Comprehensive crop species/varieties with individual prices
CROP_SPECIES = {
    "Rice": {
        "unit": "quintal",
        "botanical_genus": "Oryza sativa",
        "varieties": [
            {
                "name": "Sona Masuri",
                "scientific_species": "Oryza sativa subsp. indica",
                "price": 2800,
                "price_display": "₹2,800/quintal",
                "season": "Kharif",
                "duration_days": 120,
                "yield_per_acre": 18,
                "characteristics": "Medium slender grain, premium table rice, high demand in Karnataka & AP"
            },
            {
                "name": "IR-64",
                "scientific_species": "Oryza sativa subsp. indica",
                "price": 2200,
                "price_display": "₹2,200/quintal",
                "season": "Kharif",
                "duration_days": 115,
                "yield_per_acre": 22,
                "characteristics": "High yielding semi-dwarf variety, resistant to blast and bacterial blight"
            },
            {
                "name": "Basmati (Pusa 1121)",
                "scientific_species": "Oryza sativa subsp. indica",
                "price": 4500,
                "price_display": "₹4,500/quintal",
                "season": "Kharif",
                "duration_days": 145,
                "yield_per_acre": 14,
                "characteristics": "Extra-long grain aromatic rice with exceptional elongation after cooking"
            },
            {
                "name": "Ponni",
                "scientific_species": "Oryza sativa subsp. indica",
                "price": 2600,
                "price_display": "₹2,600/quintal",
                "season": "Kharif/Rabi",
                "duration_days": 130,
                "yield_per_acre": 16,
                "characteristics": "Popular fine grain table rice, good milling quality and pest tolerance"
            },
            {
                "name": "Jaya",
                "scientific_species": "Oryza sativa subsp. indica",
                "price": 2100,
                "price_display": "₹2,100/quintal",
                "season": "Kharif",
                "duration_days": 125,
                "yield_per_acre": 20,
                "characteristics": "Standard high yield coarse variety widely grown across coastal Karnataka"
            },
            {
                "name": "BPT 5204 (Samba Mahsuri)",
                "scientific_species": "Oryza sativa subsp. indica",
                "price": 2900,
                "price_display": "₹2,900/quintal",
                "season": "Kharif",
                "duration_days": 150,
                "yield_per_acre": 15,
                "characteristics": "Fine grain, excellent cooking quality, fetched top prices in open markets"
            },
            {
                "name": "KMP-220 (Tunga)",
                "scientific_species": "Oryza sativa subsp. indica",
                "price": 2400,
                "price_display": "₹2,400/quintal",
                "season": "Kharif",
                "duration_days": 110,
                "yield_per_acre": 19,
                "characteristics": "Bred by UAS Bengaluru, blast resistant and early maturing variety"
            },
            {
                "name": "Jyothi (PTB-10)",
                "scientific_species": "Oryza sativa subsp. indica",
                "price": 2350,
                "price_display": "₹2,350/quintal",
                "season": "Kharif/Rabi",
                "duration_days": 118,
                "yield_per_acre": 19,
                "characteristics": "Red kernelled semi-tall rice variety, popular in coastal Dakshina Kannada & Udupi"
            }
        ]
    },
    "Banana": {
        "unit": "kg",
        "botanical_genus": "Musa acuminata",
        "varieties": [
            {
                "name": "Robusta (Cavendish)",
                "scientific_species": "Musa acuminata (AAA Group)",
                "price": 35,
                "price_display": "₹35/kg",
                "season": "Year-round",
                "duration_days": 300,
                "yield_per_acre": 3000,
                "characteristics": "Commercial Cavendish clone with large heavy bunches and uniform green-to-yellow ripening"
            },
            {
                "name": "Yelakki (Elaichi)",
                "scientific_species": "Musa acuminata (AB Group)",
                "price": 60,
                "price_display": "₹60/kg",
                "season": "Year-round",
                "duration_days": 330,
                "yield_per_acre": 1800,
                "characteristics": "Small aromatic dessert banana highly relished in South India, commands premium retail price"
            },
            {
                "name": "Nendran",
                "scientific_species": "Musa balbisiana x acuminata (AAB Group)",
                "price": 45,
                "price_display": "₹45/kg",
                "season": "Year-round",
                "duration_days": 360,
                "yield_per_acre": 2200,
                "characteristics": "Famous plantain variety for banana chips and culinary processing in Kerala and coastal Karnataka"
            },
            {
                "name": "Red Banana (Chandra Bale)",
                "scientific_species": "Musa acuminata (AAA Group)",
                "price": 55,
                "price_display": "₹55/kg",
                "season": "Year-round",
                "duration_days": 330,
                "yield_per_acre": 1500,
                "characteristics": "Nutrient-rich red peel banana with sweet berry flavour and high beta-carotene content"
            },
            {
                "name": "Grand Naine (G9)",
                "scientific_species": "Musa acuminata (AAA Group)",
                "price": 30,
                "price_display": "₹30/kg",
                "season": "Year-round",
                "duration_days": 300,
                "yield_per_acre": 3500,
                "characteristics": "Tissue culture export quality variety with wind resistance and uniform cylindrical bunches"
            },
            {
                "name": "Poovan (Mysore)",
                "scientific_species": "Musa balbisiana x acuminata (AAB Group)",
                "price": 40,
                "price_display": "₹40/kg",
                "season": "Year-round",
                "duration_days": 340,
                "yield_per_acre": 2000,
                "characteristics": "Hardy perennial variety with slight sub-acid flavor, resistant to Panama wilt"
            },
            {
                "name": "Rasthali (Silk)",
                "scientific_species": "Musa acuminata x balbisiana (AAB Group)",
                "price": 50,
                "price_display": "₹50/kg",
                "season": "Year-round",
                "duration_days": 350,
                "yield_per_acre": 1600,
                "characteristics": "Traditional premium dessert table banana with thin peel and pleasant aroma"
            }
        ]
    },
    "Arecanut": {
        "unit": "quintal",
        "botanical_genus": "Areca catechu",
        "varieties": [
            {
                "name": "Mangala",
                "scientific_species": "Areca catechu var. Mangala",
                "price": 48000,
                "price_display": "₹48,000/quintal",
                "season": "Perennial",
                "duration_days": 1825,
                "yield_per_acre": 10,
                "characteristics": "Early-bearing semi-tall variety developed by CPCRI with high fruit set and tender nut yield"
            },
            {
                "name": "Sumangala",
                "scientific_species": "Areca catechu var. Sumangala",
                "price": 46000,
                "price_display": "₹46,000/quintal",
                "season": "Perennial",
                "duration_days": 1825,
                "yield_per_acre": 11,
                "characteristics": "High yielding variety with bold nuts, consistent annual yield and tolerance to heavy rainfall"
            },
            {
                "name": "Sreemangala",
                "scientific_species": "Areca catechu var. Sreemangala",
                "price": 47000,
                "price_display": "₹47,000/quintal",
                "season": "Perennial",
                "duration_days": 1825,
                "yield_per_acre": 9,
                "characteristics": "Tall vigorous selection producing large round nuts suited for Chali processing"
            },
            {
                "name": "South Kanara Local",
                "scientific_species": "Areca catechu Local Selection",
                "price": 44000,
                "price_display": "₹44,000/quintal",
                "season": "Perennial",
                "duration_days": 1825,
                "yield_per_acre": 12,
                "characteristics": "Indigenous coastal ecotype well acclimatized to laterite soils and heavy southwest monsoons"
            },
            {
                "name": "Mohitnagar",
                "scientific_species": "Areca catechu var. Mohitnagar",
                "price": 43000,
                "price_display": "₹43,000/quintal",
                "season": "Perennial",
                "duration_days": 1825,
                "yield_per_acre": 10,
                "characteristics": "Vigorous palm with compact bunch formation and uniform nut development"
            },
            {
                "name": "Thirthahalli Local",
                "scientific_species": "Areca catechu Malnad Ecotype",
                "price": 49000,
                "price_display": "₹49,000/quintal",
                "season": "Perennial",
                "duration_days": 1825,
                "yield_per_acre": 11,
                "characteristics": "Malnad region specialty producing premium red boiled nut (Rashi/Gorabaluku) prized by APMC"
            }
        ]
    },
    "Pepper": {
        "unit": "kg",
        "botanical_genus": "Piper nigrum",
        "varieties": [
            {
                "name": "Panniyur-1",
                "scientific_species": "Piper nigrum (Hybrid Uthirankotta x Cheriyakaniakkadan)",
                "price": 650,
                "price_display": "₹650/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 160,
                "characteristics": "World renowned first pepper hybrid with long spikes, bold berries and high piperine content"
            },
            {
                "name": "Karimunda",
                "scientific_species": "Piper nigrum cv. Karimunda",
                "price": 580,
                "price_display": "₹580/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 140,
                "characteristics": "Most adaptable traditional cultivar, regular bearer with high dry recovery percentage"
            },
            {
                "name": "Panniyur-5",
                "scientific_species": "Piper nigrum cv. Panniyur-5",
                "price": 640,
                "price_display": "₹640/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 170,
                "characteristics": "High shade-tolerant variety ideal for intercropping with arecanut and coffee estates"
            },
            {
                "name": "Sreekara",
                "scientific_species": "Piper nigrum cv. Sreekara",
                "price": 620,
                "price_display": "₹620/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 155,
                "characteristics": "Selection from Karimunda by IISR, suited for diverse altitudes and soils"
            },
            {
                "name": "Subhakara",
                "scientific_species": "Piper nigrum cv. Subhakara",
                "price": 610,
                "price_display": "₹610/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 150,
                "characteristics": "Consistent yielding cultivar with high oleoresin and volatile essential oil content"
            },
            {
                "name": "Panchami",
                "scientific_species": "Piper nigrum cv. Panchami",
                "price": 630,
                "price_display": "₹630/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 165,
                "characteristics": "Late maturing variety with very long spikes and high tolerance to root rot (Phytophthora)"
            }
        ]
    },
    "Cashew": {
        "unit": "kg",
        "botanical_genus": "Anacardium occidentale",
        "varieties": [
            {
                "name": "Vengurla-4",
                "scientific_species": "Anacardium occidentale cv. V-4",
                "price": 135,
                "price_display": "₹135/kg",
                "season": "Feb-May",
                "duration_days": 1460,
                "yield_per_acre": 220,
                "characteristics": "High shelling percentage (31%), export grade W-210 jumbo kernels"
            },
            {
                "name": "Vengurla-7",
                "scientific_species": "Anacardium occidentale cv. V-7",
                "price": 130,
                "price_display": "₹130/kg",
                "season": "Feb-May",
                "duration_days": 1460,
                "yield_per_acre": 240,
                "characteristics": "Profuse cluster bearing habit with high nut count per panicle and large apple"
            },
            {
                "name": "BPP-8 (Ullal-3)",
                "scientific_species": "Anacardium occidentale cv. Ullal-3",
                "price": 125,
                "price_display": "₹125/kg",
                "season": "Feb-May",
                "duration_days": 1460,
                "yield_per_acre": 200,
                "characteristics": "Popular coastal Karnataka variety bred by Ullal Research Station, excellent kernel weight"
            },
            {
                "name": "Bhaskara",
                "scientific_species": "Anacardium occidentale cv. Bhaskara",
                "price": 120,
                "price_display": "₹120/kg",
                "season": "Feb-May",
                "duration_days": 1460,
                "yield_per_acre": 210,
                "characteristics": "Mid-season variety bred by DCR Puttur with high kernel recovery and pest tolerance"
            },
            {
                "name": "Dhana",
                "scientific_species": "Anacardium occidentale cv. Dhana",
                "price": 115,
                "price_display": "₹115/kg",
                "season": "Feb-May",
                "duration_days": 1460,
                "yield_per_acre": 190,
                "characteristics": "Hybrid variety suited for high density planting and hill slope conservation"
            },
            {
                "name": "Priyanka",
                "scientific_species": "Anacardium occidentale cv. Priyanka",
                "price": 140,
                "price_display": "₹140/kg",
                "season": "Feb-May",
                "duration_days": 1460,
                "yield_per_acre": 230,
                "characteristics": "Extra bold nuts with high export kernel weight and early bearing timeline"
            }
        ]
    },
    "Rubber": {
        "unit": "kg",
        "botanical_genus": "Hevea brasiliensis",
        "varieties": [
            {
                "name": "RRII 105",
                "scientific_species": "Hevea brasiliensis clone RRII 105",
                "price": 190,
                "price_display": "₹190/kg",
                "season": "Perennial",
                "duration_days": 2190,
                "yield_per_acre": 550,
                "characteristics": "Dominant commercial clone in South India with high dry rubber content and vigorous girth"
            },
            {
                "name": "RRII 414",
                "scientific_species": "Hevea brasiliensis clone RRII 414",
                "price": 185,
                "price_display": "₹185/kg",
                "season": "Perennial",
                "duration_days": 2190,
                "yield_per_acre": 520,
                "characteristics": "High initial yield, thick virgin bark and rapid bark renewal characteristics"
            },
            {
                "name": "GT-1",
                "scientific_species": "Hevea brasiliensis clone GT-1",
                "price": 175,
                "price_display": "₹175/kg",
                "season": "Perennial",
                "duration_days": 2190,
                "yield_per_acre": 480,
                "characteristics": "Primary clone known for exceptional wind firmness and low incidence of tapping panel dryness"
            },
            {
                "name": "PB 260",
                "scientific_species": "Hevea brasiliensis clone PB 260",
                "price": 180,
                "price_display": "₹180/kg",
                "season": "Perennial",
                "duration_days": 2190,
                "yield_per_acre": 500,
                "characteristics": "Vigorous grower with straight trunk, high latex volume during early tapping years"
            },
            {
                "name": "RRIM 600",
                "scientific_species": "Hevea brasiliensis clone RRIM 600",
                "price": 182,
                "price_display": "₹182/kg",
                "season": "Perennial",
                "duration_days": 2190,
                "yield_per_acre": 510,
                "characteristics": "Proven Malaysian clone adapted to varied slopes, resistant to Oidium leaf mildew"
            }
        ]
    },
    "Coconut": {
        "unit": "piece",
        "botanical_genus": "Cocos nucifera",
        "crop_image": "/coconut.jpg",
        "varieties": [
            {
                "name": "West Coast Tall",
                "scientific_species": "Cocos nucifera var. typica",
                "price": 38,
                "price_display": "₹38/piece",
                "season": "Perennial",
                "duration_days": 1825,
                "yield_per_acre": 6500,
                "characteristics": "Premier tall variety of Karnataka coast, high copra content (68% oil) and durable timber",
                "image_url": "/coconut.jpg"
            },
            {
                "name": "Chowghat Orange Dwarf",
                "scientific_species": "Cocos nucifera var. javanica (COD)",
                "price": 42,
                "price_display": "₹42/piece",
                "season": "Perennial",
                "duration_days": 1460,
                "yield_per_acre": 5000,
                "characteristics": "Early flowering tender nut variety with sweet nutritious water and orange-colored fruit",
                "image_url": "/coconut.jpg"
            },
            {
                "name": "Tiptur Tall",
                "scientific_species": "Cocos nucifera cv. Tiptur Tall",
                "price": 36,
                "price_display": "₹36/piece",
                "season": "Perennial",
                "duration_days": 1825,
                "yield_per_acre": 7000,
                "characteristics": "Famous ball copra variety from Tumakuru district, highest commercial ball copra recovery",
                "image_url": "/coconut.jpg"
            },
            {
                "name": "Lakshadweep Micro Tall",
                "scientific_species": "Cocos nucifera cv. Laccadive Ordinary",
                "price": 40,
                "price_display": "₹40/piece",
                "season": "Perennial",
                "duration_days": 1825,
                "yield_per_acre": 5500,
                "characteristics": "Medium-sized sweet water nuts with outstanding copra quality and pest resilience",
                "image_url": "/coconut.jpg"
            },
            {
                "name": "Gangabondam (Hybrid)",
                "scientific_species": "Cocos nucifera cv. Gangabondam",
                "price": 45,
                "price_display": "₹45/piece",
                "season": "Perennial",
                "duration_days": 1460,
                "yield_per_acre": 6000,
                "characteristics": "Semi-tall high yielding green tender coconut variety widely planted for fresh water sale",
                "image_url": "/coconut.jpg"
            },
            {
                "name": "Kera Sankara (D x T)",
                "scientific_species": "Cocos nucifera Hybrid (WCT x COD)",
                "price": 44,
                "price_display": "₹44/piece",
                "season": "Perennial",
                "duration_days": 1460,
                "yield_per_acre": 7500,
                "characteristics": "High-yielding dwarf x tall hybrid yielding up to 108 nuts per palm annually",
                "image_url": "/coconut.jpg"
            }
        ]
    },
    "Coffee": {
        "unit": "kg",
        "botanical_genus": "Coffea",
        "varieties": [
            {
                "name": "Arabica (S.795)",
                "scientific_species": "Coffea arabica cv. S.795",
                "price": 320,
                "price_display": "₹320/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 8,
                "characteristics": "Most celebrated Indian Arabica cultivar with balanced body, mild acidity and mocha notes"
            },
            {
                "name": "Arabica (Cauvery / Catimor)",
                "scientific_species": "Coffea arabica cv. Cauvery",
                "price": 300,
                "price_display": "₹300/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 10,
                "characteristics": "Semi-dwarf compact variety resistant to leaf rust, suitable for close spacing"
            },
            {
                "name": "Robusta (CxR)",
                "scientific_species": "Coffea canephora x congensis",
                "price": 220,
                "price_display": "₹220/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 15,
                "characteristics": "Congensis x Robusta hybrid combining compact bush stature with superior cup aroma"
            },
            {
                "name": "Robusta (S.274)",
                "scientific_species": "Coffea canephora cv. S.274",
                "price": 210,
                "price_display": "₹210/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 14,
                "characteristics": "Heavy bearing robusta selection thriving under multi-tier shade across Kodagu and Chikmagalur"
            },
            {
                "name": "Arabica (Selection-9)",
                "scientific_species": "Coffea arabica cv. SLN 9",
                "price": 350,
                "price_display": "₹350/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 7,
                "characteristics": "Tafarikela cross noted for drought tolerance and winning 'Flavour of India - Fine Cup' awards"
            },
            {
                "name": "Kent Arabica",
                "scientific_species": "Coffea arabica cv. Kent",
                "price": 340,
                "price_display": "₹340/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 8,
                "characteristics": "Historic heritage Indian Arabica selection with exquisite floral cup profile and bright acidity"
            }
        ]
    },
    "Cardamom": {
        "unit": "kg",
        "botanical_genus": "Elettaria cardamomum",
        "varieties": [
            {
                "name": "Mysore (Green Gold)",
                "scientific_species": "Elettaria cardamomum var. major",
                "price": 1600,
                "price_display": "₹1,600/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 1.5,
                "characteristics": "Erect panicles producing bold 8mm ribbed green capsules commanding premier auction rates"
            },
            {
                "name": "Malabar",
                "scientific_species": "Elettaria cardamomum var. minor",
                "price": 1450,
                "price_display": "₹1,450/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 1.8,
                "characteristics": "Prostrate panicles with round capsules, tolerant to thrips and lower altitude humidity"
            },
            {
                "name": "Vazhukka",
                "scientific_species": "Elettaria cardamomum (Natural Cross)",
                "price": 1550,
                "price_display": "₹1,550/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 1.6,
                "characteristics": "Semi-erect panicles producing deep green oblong capsules with high essential oil content"
            },
            {
                "name": "ICRI-3 (Avinash)",
                "scientific_species": "Elettaria cardamomum cv. ICRI-3",
                "price": 1700,
                "price_display": "₹1,700/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 2.0,
                "characteristics": "Bred by Indian Cardamom Research Institute, highly tolerant to 'Katte' mosaic viral disease"
            },
            {
                "name": "Mudigere-1",
                "scientific_species": "Elettaria cardamomum cv. Mudigere-1",
                "price": 1500,
                "price_display": "₹1,500/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 1.7,
                "characteristics": "High yielding Malabar selection bred for Karnataka Western Ghats coffee understory"
            },
            {
                "name": "Njallani",
                "scientific_species": "Elettaria cardamomum cv. Njallani Green Gold",
                "price": 1800,
                "price_display": "₹1,800/kg",
                "season": "Perennial",
                "duration_days": 1095,
                "yield_per_acre": 2.2,
                "characteristics": "Farmer-developed high-yielding superstar variety producing three times average capsule count"
            }
        ]
    },
    "Ginger": {
        "unit": "kg",
        "botanical_genus": "Zingiber officinale",
        "varieties": [
            {
                "name": "Maran",
                "scientific_species": "Zingiber officinale cv. Maran",
                "price": 130,
                "price_display": "₹130/kg",
                "season": "Kharif",
                "duration_days": 240,
                "yield_per_acre": 90,
                "characteristics": "Plump aromatic rhizomes with low fiber and high volatile oil, preferred for fresh export"
            },
            {
                "name": "Varada",
                "scientific_species": "Zingiber officinale cv. Varada",
                "price": 125,
                "price_display": "₹125/kg",
                "season": "Kharif",
                "duration_days": 220,
                "yield_per_acre": 85,
                "characteristics": "High yielding variety released by IISR with bold fingers and excellent fresh ginger pungency"
            },
            {
                "name": "Himachal",
                "scientific_species": "Zingiber officinale cv. Himachal",
                "price": 120,
                "price_display": "₹120/kg",
                "season": "Kharif",
                "duration_days": 230,
                "yield_per_acre": 80,
                "characteristics": "Cold tolerant variety with high dry ginger (Sonth) conversion percentage"
            },
            {
                "name": "IISR Rejatha",
                "scientific_species": "Zingiber officinale cv. Rejatha",
                "price": 135,
                "price_display": "₹135/kg",
                "season": "Kharif",
                "duration_days": 240,
                "yield_per_acre": 95,
                "characteristics": "Exceptional dry recovery (24.7%) and high oleoresin content for commercial extraction"
            },
            {
                "name": "Suprabha",
                "scientific_species": "Zingiber officinale cv. Suprabha",
                "price": 115,
                "price_display": "₹115/kg",
                "season": "Kharif",
                "duration_days": 210,
                "yield_per_acre": 75,
                "characteristics": "Short duration variety with high tolerance to bacterial wilt and rhizome rot"
            },
            {
                "name": "Mahim",
                "scientific_species": "Zingiber officinale cv. Mahim",
                "price": 128,
                "price_display": "₹128/kg",
                "season": "Kharif",
                "duration_days": 235,
                "yield_per_acre": 88,
                "characteristics": "Large thick fibrous rhizomes with spicy flavor and long storage shelf life"
            }
        ]
    },
    "Jowar": {
        "unit": "quintal",
        "botanical_genus": "Sorghum bicolor",
        "varieties": [
            {
                "name": "M 35-1 (Maldandi)",
                "scientific_species": "Sorghum bicolor cv. Maldandi",
                "price": 3100,
                "price_display": "₹3,100/quintal",
                "season": "Rabi",
                "duration_days": 120,
                "yield_per_acre": 10,
                "characteristics": "Iconic pearly white grain Rabi sorghum, supreme roti making quality and sweet fodder"
            },
            {
                "name": "CSH-16",
                "scientific_species": "Sorghum bicolor Hybrid CSH-16",
                "price": 2900,
                "price_display": "₹2,900/quintal",
                "season": "Kharif",
                "duration_days": 105,
                "yield_per_acre": 12,
                "characteristics": "High-yielding Kharif hybrid resistant to grain mold and shoot fly"
            },
            {
                "name": "SPV-462",
                "scientific_species": "Sorghum bicolor cv. SPV-462",
                "price": 2800,
                "price_display": "₹2,800/quintal",
                "season": "Kharif",
                "duration_days": 110,
                "yield_per_acre": 11,
                "characteristics": "Dual-purpose grain and stover variety with high protein and digestible dry matter"
            },
            {
                "name": "DSV-4 (Bijapur Local)",
                "scientific_species": "Sorghum bicolor cv. DSV-4",
                "price": 3200,
                "price_display": "₹3,200/quintal",
                "season": "Rabi",
                "duration_days": 115,
                "yield_per_acre": 9,
                "characteristics": "Drought tolerant Northern Karnataka selection yielding soft palatable rotis"
            },
            {
                "name": "CSV-15",
                "scientific_species": "Sorghum bicolor cv. CSV-15",
                "price": 2750,
                "price_display": "₹2,750/quintal",
                "season": "Kharif",
                "duration_days": 100,
                "yield_per_acre": 13,
                "characteristics": "Sweet stalk sorghum variety used for both grain harvest and silage production"
            }
        ]
    },
    "Cotton": {
        "unit": "quintal",
        "botanical_genus": "Gossypium hirsutum",
        "varieties": [
            {
                "name": "Bt Cotton (Bollgard II)",
                "scientific_species": "Gossypium hirsutum (Cry1Ac + Cry2Ab)",
                "price": 6500,
                "price_display": "₹6,500/quintal",
                "season": "Kharif",
                "duration_days": 180,
                "yield_per_acre": 8,
                "characteristics": "Transgenic hybrid with dual-gene bollworm protection and high ginning outturn (36%)"
            },
            {
                "name": "DCH-32 (Hybrid)",
                "scientific_species": "Gossypium hirsutum x barbadense",
                "price": 6200,
                "price_display": "₹6,200/quintal",
                "season": "Kharif",
                "duration_days": 170,
                "yield_per_acre": 7,
                "characteristics": "Extra long staple premium cotton fetching high prices in textile spinning mills"
            },
            {
                "name": "Suraj (Bt Hybrid)",
                "scientific_species": "Gossypium hirsutum cv. Suraj",
                "price": 6400,
                "price_display": "₹6,400/quintal",
                "season": "Kharif",
                "duration_days": 175,
                "yield_per_acre": 9,
                "characteristics": "Central Institute for Cotton Research release with compact canopy and synchronous bursting"
            },
            {
                "name": "Jayadhar",
                "scientific_species": "Gossypium herbaceum cv. Jayadhar",
                "price": 5800,
                "price_display": "₹5,800/quintal",
                "season": "Kharif",
                "duration_days": 160,
                "yield_per_acre": 6,
                "characteristics": "Hardy indigenous Desi cotton thriving under rainfed black soils of Dharwad & Belagavi"
            },
            {
                "name": "NHH-44",
                "scientific_species": "Gossypium hirsutum Hybrid NHH-44",
                "price": 6100,
                "price_display": "₹6,100/quintal",
                "season": "Kharif",
                "duration_days": 165,
                "yield_per_acre": 7,
                "characteristics": "Popular rainfed hybrid variety with medium staple length and good drought resilience"
            }
        ]
    },
    "Maize": {
        "unit": "quintal",
        "botanical_genus": "Zea mays",
        "varieties": [
            {
                "name": "NAH-2049 (Hybrid)",
                "scientific_species": "Zea mays indurata Hybrid",
                "price": 2200,
                "price_display": "₹2,200/quintal",
                "season": "Kharif/Rabi",
                "duration_days": 100,
                "yield_per_acre": 24,
                "characteristics": "High yield yellow dent maize released by UAS Dharwad, uniform cobs and stay-green trait"
            },
            {
                "name": "Deccan 103",
                "scientific_species": "Zea mays indentata Hybrid",
                "price": 2050,
                "price_display": "₹2,050/quintal",
                "season": "Kharif",
                "duration_days": 95,
                "yield_per_acre": 22,
                "characteristics": "Wide ecological adaptation, excellent poultry feed quality with high starch recovery"
            },
            {
                "name": "NK 6240",
                "scientific_species": "Zea mays Hybrid NK 6240",
                "price": 2150,
                "price_display": "₹2,150/quintal",
                "season": "Kharif/Rabi",
                "duration_days": 105,
                "yield_per_acre": 25,
                "characteristics": "Heavy grain density with tight husk cover protecting against ear rot and bird damage"
            },
            {
                "name": "DHM-117",
                "scientific_species": "Zea mays Hybrid DHM-117",
                "price": 2000,
                "price_display": "₹2,000/quintal",
                "season": "Kharif",
                "duration_days": 90,
                "yield_per_acre": 20,
                "characteristics": "Early maturing hybrid suited for multi-crop rotations with pulse crops"
            },
            {
                "name": "Baby Corn (G-5414)",
                "scientific_species": "Zea mays saccharata",
                "price": 3500,
                "price_display": "₹3,500/quintal",
                "season": "Year-round",
                "duration_days": 55,
                "yield_per_acre": 8,
                "characteristics": "Short-duration specialty crop yielding tender yellow ears for hotel and fresh vegetable retail"
            }
        ]
    },
    "Bengal Gram": {
        "unit": "quintal",
        "botanical_genus": "Cicer arietinum",
        "varieties": [
            {
                "name": "JG-11",
                "scientific_species": "Cicer arietinum (Desi type)",
                "price": 5600,
                "price_display": "₹5,600/quintal",
                "season": "Rabi",
                "duration_days": 100,
                "yield_per_acre": 7,
                "characteristics": "Most popular Desi chickpea variety in Karnataka, resistant to Fusarium wilt and lodging"
            },
            {
                "name": "Annigeri-1",
                "scientific_species": "Cicer arietinum cv. A-1",
                "price": 5300,
                "price_display": "₹5,300/quintal",
                "season": "Rabi",
                "duration_days": 95,
                "yield_per_acre": 6,
                "characteristics": "Famous traditional Karnataka variety, bold yellow-brown seeds with superior besan quality"
            },
            {
                "name": "JAKI 9218",
                "scientific_species": "Cicer arietinum cv. JAKI 9218",
                "price": 5500,
                "price_display": "₹5,500/quintal",
                "season": "Rabi",
                "duration_days": 105,
                "yield_per_acre": 8,
                "characteristics": "Early maturing bold seeded desi variety with excellent drought escape mechanism"
            },
            {
                "name": "KAK-2",
                "scientific_species": "Cicer arietinum (Kabuli type)",
                "price": 5100,
                "price_display": "₹5,100/quintal",
                "season": "Rabi",
                "duration_days": 90,
                "yield_per_acre": 6,
                "characteristics": "Medium-bold kabuli chickpea with light creamy seeds and early maturity"
            },
            {
                "name": "Kabuli (L-550)",
                "scientific_species": "Cicer arietinum cv. L-550",
                "price": 7200,
                "price_display": "₹7,200/quintal",
                "season": "Rabi",
                "duration_days": 110,
                "yield_per_acre": 5,
                "characteristics": "Extra bold 100-seed weight Kabuli chana commanding high export demand and retail margins"
            }
        ]
    },
    "Red Gram": {
        "unit": "quintal",
        "botanical_genus": "Cajanus cajan",
        "varieties": [
            {
                "name": "BRG-1 (Maruti)",
                "scientific_species": "Cajanus cajan cv. BRG-1",
                "price": 7800,
                "price_display": "₹7,800/quintal",
                "season": "Kharif",
                "duration_days": 160,
                "yield_per_acre": 5,
                "characteristics": "High protein tur dal variety, resistant to sterility mosaic and Fusarium wilt diseases"
            },
            {
                "name": "TS-3R",
                "scientific_species": "Cajanus cajan cv. TS-3R",
                "price": 7500,
                "price_display": "₹7,500/quintal",
                "season": "Kharif",
                "duration_days": 150,
                "yield_per_acre": 6,
                "characteristics": "Bred in Kalaburagi pulse bowl, medium maturity with high dhal recovery percentage"
            },
            {
                "name": "GRG-811",
                "scientific_species": "Cajanus cajan cv. GRG-811",
                "price": 7600,
                "price_display": "₹7,600/quintal",
                "season": "Kharif",
                "duration_days": 155,
                "yield_per_acre": 5,
                "characteristics": "Vigorous branching red gram variety developed by UAS Raichur with bold reddish brown grains"
            },
            {
                "name": "BRG-2",
                "scientific_species": "Cajanus cajan cv. BRG-2",
                "price": 7400,
                "price_display": "₹7,400/quintal",
                "season": "Kharif",
                "duration_days": 145,
                "yield_per_acre": 6,
                "characteristics": "Shorter duration variety suitable for intercropping with groundnut, ragi and cotton"
            },
            {
                "name": "ICPL 87119 (Asha)",
                "scientific_species": "Cajanus cajan cv. Asha",
                "price": 7900,
                "price_display": "₹7,900/quintal",
                "season": "Kharif",
                "duration_days": 165,
                "yield_per_acre": 5,
                "characteristics": "Bred by ICRISAT, dual disease resistant with high pod clustering and uniform seed size"
            }
        ]
    },
    "Wheat": {
        "unit": "quintal",
        "botanical_genus": "Triticum aestivum",
        "varieties": [
            {
                "name": "HD-2967",
                "scientific_species": "Triticum aestivum cv. HD-2967",
                "price": 2400,
                "price_display": "₹2,400/quintal",
                "season": "Rabi",
                "duration_days": 135,
                "yield_per_acre": 14,
                "characteristics": "India's highest acreage bread wheat with high chapati making score and rust tolerance"
            },
            {
                "name": "PBW-343",
                "scientific_species": "Triticum aestivum cv. PBW-343",
                "price": 2300,
                "price_display": "₹2,300/quintal",
                "season": "Rabi",
                "duration_days": 130,
                "yield_per_acre": 13,
                "characteristics": "Classic semi-dwarf bread wheat with high grain weight and strong straw resistance"
            },
            {
                "name": "Lok-1 (Sharbati)",
                "scientific_species": "Triticum aestivum cv. Lok-1",
                "price": 2800,
                "price_display": "₹2,800/quintal",
                "season": "Rabi",
                "duration_days": 120,
                "yield_per_acre": 11,
                "characteristics": "Golden amber lustrous grain Sharbati wheat, sweet rotis, sells at major market premium"
            },
            {
                "name": "GW-366",
                "scientific_species": "Triticum aestivum cv. GW-366",
                "price": 2350,
                "price_display": "₹2,350/quintal",
                "season": "Rabi",
                "duration_days": 125,
                "yield_per_acre": 12,
                "characteristics": "Early maturing, heat tolerant variety well suited for peninsular India winter temperatures"
            },
            {
                "name": "DBW-187 (Karan Vandana)",
                "scientific_species": "Triticum aestivum cv. DBW-187",
                "price": 2500,
                "price_display": "₹2,500/quintal",
                "season": "Rabi",
                "duration_days": 140,
                "yield_per_acre": 15,
                "characteristics": "Bio-fortified wheat with elevated iron (43.1 ppm) and protein, high yield potential"
            }
        ]
    },
    "Pomegranate": {
        "unit": "kg",
        "botanical_genus": "Punica granatum",
        "varieties": [
            {
                "name": "Bhagwa",
                "scientific_species": "Punica granatum cv. Bhagwa (Kesar)",
                "price": 160,
                "price_display": "₹160/kg",
                "season": "Year-round",
                "duration_days": 1095,
                "yield_per_acre": 70,
                "characteristics": "King of pomegranates with saffron-colored thick rind, dark red sweet arils and soft seeds"
            },
            {
                "name": "Ganesh",
                "scientific_species": "Punica granatum cv. Ganesh",
                "price": 130,
                "price_display": "₹130/kg",
                "season": "Year-round",
                "duration_days": 1095,
                "yield_per_acre": 65,
                "characteristics": "First commercial soft-seeded selection with pinkish arils and sweet aromatic juice"
            },
            {
                "name": "Arakta",
                "scientific_species": "Punica granatum cv. Arakta",
                "price": 145,
                "price_display": "₹145/kg",
                "season": "Year-round",
                "duration_days": 1095,
                "yield_per_acre": 60,
                "characteristics": "Heavy bearer with attractive deep red fruit surface and blood-red juicy seeds"
            },
            {
                "name": "Mridula",
                "scientific_species": "Punica granatum cv. Mridula",
                "price": 135,
                "price_display": "₹135/kg",
                "season": "Year-round",
                "duration_days": 1095,
                "yield_per_acre": 55,
                "characteristics": "Enriched aril sweetness, bright crimson rind and soft edible seeds"
            },
            {
                "name": "Sinduri",
                "scientific_species": "Punica granatum cv. Sinduri",
                "price": 120,
                "price_display": "₹120/kg",
                "season": "Year-round",
                "duration_days": 1095,
                "yield_per_acre": 50,
                "characteristics": "Hardy semi-arid cultivar tolerant to sunburn and fruit cracking in dry weather"
            }
        ]
    },
    "Ragi": {
        "unit": "quintal",
        "botanical_genus": "Eleusine coracana",
        "varieties": [
            {
                "name": "GPU-28",
                "scientific_species": "Eleusine coracana cv. GPU-28",
                "price": 3600,
                "price_display": "₹3,600/quintal",
                "season": "Kharif",
                "duration_days": 110,
                "yield_per_acre": 12,
                "characteristics": "Premier finger millet variety of Karnataka with compact fist-shaped earheads and blast resistance"
            },
            {
                "name": "MR-1",
                "scientific_species": "Eleusine coracana cv. MR-1",
                "price": 3400,
                "price_display": "₹3,400/quintal",
                "season": "Kharif",
                "duration_days": 105,
                "yield_per_acre": 10,
                "characteristics": "Early maturing, high tillering variety yielding nutritious brown grains rich in calcium"
            },
            {
                "name": "GPU-67",
                "scientific_species": "Eleusine coracana cv. GPU-67",
                "price": 3500,
                "price_display": "₹3,500/quintal",
                "season": "Kharif",
                "duration_days": 115,
                "yield_per_acre": 11,
                "characteristics": "High grain and quality straw yielder with outstanding resilience to drought spells"
            },
            {
                "name": "ML-365",
                "scientific_species": "Eleusine coracana cv. ML-365",
                "price": 3300,
                "price_display": "₹3,300/quintal",
                "season": "Kharif",
                "duration_days": 100,
                "yield_per_acre": 9,
                "characteristics": "Short duration drought escape variety ideal for late sowing and dry farming zones"
            },
            {
                "name": "KMR-204",
                "scientific_species": "Eleusine coracana cv. KMR-204",
                "price": 3550,
                "price_display": "₹3,550/quintal",
                "season": "Kharif",
                "duration_days": 108,
                "yield_per_acre": 11,
                "characteristics": "Uniform flowering and maturity, high malt recovery and culinary suitability for ragi mudde"
            },
            {
                "name": "Indaf-5",
                "scientific_species": "Eleusine coracana cv. Indaf-5",
                "price": 3450,
                "price_display": "₹3,450/quintal",
                "season": "Kharif",
                "duration_days": 112,
                "yield_per_acre": 10,
                "characteristics": "Open earhead Indo-African hybrid derivative with high grain weight"
            }
        ]
    },
    "Groundnut": {
        "unit": "quintal",
        "botanical_genus": "Arachis hypogaea",
        "varieties": [
            {
                "name": "TMV-2",
                "scientific_species": "Arachis hypogaea subsp. fastigiata",
                "price": 6700,
                "price_display": "₹6,700/quintal",
                "season": "Kharif",
                "duration_days": 105,
                "yield_per_acre": 8,
                "characteristics": "Standard Spanish bunch groundnut with 49% oil content and high shelling turnout"
            },
            {
                "name": "JL-24 (Phule Pragati)",
                "scientific_species": "Arachis hypogaea cv. JL-24",
                "price": 6500,
                "price_display": "₹6,500/quintal",
                "season": "Kharif/Rabi",
                "duration_days": 100,
                "yield_per_acre": 9,
                "characteristics": "Early maturing bunch type with two-seeded bold pink pods, widely popular across Karnataka"
            },
            {
                "name": "GPBD-4",
                "scientific_species": "Arachis hypogaea cv. GPBD-4",
                "price": 6800,
                "price_display": "₹6,800/quintal",
                "season": "Kharif",
                "duration_days": 110,
                "yield_per_acre": 10,
                "characteristics": "Bred by UAS Dharwad, highly resistant to late leaf spot and rust, high oleic acid content"
            },
            {
                "name": "K-6 (Kadiri-6)",
                "scientific_species": "Arachis hypogaea cv. Kadiri-6",
                "price": 6400,
                "price_display": "₹6,400/quintal",
                "season": "Kharif",
                "duration_days": 95,
                "yield_per_acre": 7,
                "characteristics": "Drought-hardy selection tailored for light red sandy soils of Chitradurga and Kolar"
            },
            {
                "name": "TAG-24",
                "scientific_species": "Arachis hypogaea cv. TAG-24",
                "price": 6600,
                "price_display": "₹6,600/quintal",
                "season": "Kharif/Rabi",
                "duration_days": 100,
                "yield_per_acre": 8,
                "characteristics": "Semi-dwarf compact canopy variety released by BARC with high harvest index"
            }
        ]
    },
    "Sugarcane": {
        "unit": "quintal",
        "botanical_genus": "Saccharum officinarum",
        "varieties": [
            {
                "name": "Co-86032",
                "scientific_species": "Saccharum officinarum cv. Co-86032",
                "price": 325,
                "price_display": "₹325/quintal",
                "season": "Year-round",
                "duration_days": 360,
                "yield_per_acre": 400,
                "characteristics": "Superstar sugarcane variety of peninsular India with 14.5% sucrose and excellent ratoon ability"
            },
            {
                "name": "CoC-671",
                "scientific_species": "Saccharum officinarum cv. CoC-671",
                "price": 310,
                "price_display": "₹310/quintal",
                "season": "Year-round",
                "duration_days": 330,
                "yield_per_acre": 350,
                "characteristics": "Early high sugar cane producing golden jaggery with superior crystal recovery"
            },
            {
                "name": "Co-0238",
                "scientific_species": "Saccharum officinarum cv. Co-0238",
                "price": 330,
                "price_display": "₹330/quintal",
                "season": "Year-round",
                "duration_days": 345,
                "yield_per_acre": 380,
                "characteristics": "Thick heavy canes with high sugar recovery, profuse tillering and low fiber"
            },
            {
                "name": "Co-62175",
                "scientific_species": "Saccharum officinarum cv. Co-62175",
                "price": 300,
                "price_display": "₹300/quintal",
                "season": "Year-round",
                "duration_days": 340,
                "yield_per_acre": 320,
                "characteristics": "Hardy variety tolerant to drought and salinity, reliable performance under irregular irrigation"
            },
            {
                "name": "SNK-44 (Early)",
                "scientific_species": "Saccharum officinarum cv. SNK-44",
                "price": 315,
                "price_display": "₹315/quintal",
                "season": "Year-round",
                "duration_days": 300,
                "yield_per_acre": 360,
                "characteristics": "Bred for Northern Karnataka sugar belt (Belagavi, Bagalkot) with early harvest window"
            }
        ]
    },
    "Tomato": {
        "unit": "kg",
        "botanical_genus": "Solanum lycopersicum",
        "varieties": [
            {
                "name": "Arka Rakshak (Hybrid)",
                "scientific_species": "Solanum lycopersicum F1 Hybrid",
                "price": 35,
                "price_display": "₹35/kg",
                "season": "Rabi/Summer",
                "duration_days": 75,
                "yield_per_acre": 140,
                "characteristics": "Triple disease resistant hybrid (ToLCV + BW + Early Blight), deep red firm fruits with long shelf life"
            },
            {
                "name": "Pusa Ruby",
                "scientific_species": "Solanum lycopersicum cv. Pusa Ruby",
                "price": 28,
                "price_display": "₹28/kg",
                "season": "Year-round",
                "duration_days": 70,
                "yield_per_acre": 120,
                "characteristics": "Early flattish round tomato with pleasant acidity, ideal for processing and household cooking"
            },
            {
                "name": "Arka Vikas",
                "scientific_species": "Solanum lycopersicum cv. Arka Vikas",
                "price": 30,
                "price_display": "₹30/kg",
                "season": "Year-round",
                "duration_days": 72,
                "yield_per_acre": 130,
                "characteristics": "Semi-determinate variety bred by IIHR Bengaluru, adaptable to moisture stress and hot summer"
            },
            {
                "name": "NS-501 (Hybrid)",
                "scientific_species": "Solanum lycopersicum F1 NS-501",
                "price": 38,
                "price_display": "₹38/kg",
                "season": "Rabi/Summer",
                "duration_days": 80,
                "yield_per_acre": 150,
                "characteristics": "Commercial shipper hybrid with square-round firm fruits ideal for distant long transport"
            },
            {
                "name": "PKM-1",
                "scientific_species": "Solanum lycopersicum cv. PKM-1",
                "price": 25,
                "price_display": "₹25/kg",
                "season": "Year-round",
                "duration_days": 65,
                "yield_per_acre": 110,
                "characteristics": "High vitamin C variety yielding prolific clusters of smooth medium sized fruits"
            },
            {
                "name": "Shivam Hybrid",
                "scientific_species": "Solanum lycopersicum F1 Shivam",
                "price": 32,
                "price_display": "₹32/kg",
                "season": "Year-round",
                "duration_days": 75,
                "yield_per_acre": 145,
                "characteristics": "Uniform shiny fruits with high firmness and strong resistance to leaf curl virus"
            }
        ]
    },
    "Mango": {
        "unit": "kg",
        "botanical_genus": "Mangifera indica",
        "varieties": [
            {
                "name": "Alphonso (Hapus)",
                "scientific_species": "Mangifera indica cv. Alphonso",
                "price": 150,
                "price_display": "₹150/kg",
                "season": "Mar-Jun",
                "duration_days": 1825,
                "yield_per_acre": 30,
                "characteristics": "Undisputed king of mangoes with golden saffron flesh, fiberless texture and intoxicating fragrance"
            },
            {
                "name": "Badami (Karnataka Alphonso)",
                "scientific_species": "Mangifera indica cv. Badami",
                "price": 100,
                "price_display": "₹100/kg",
                "season": "Apr-Jun",
                "duration_days": 1825,
                "yield_per_acre": 40,
                "characteristics": "Karnataka's signature dessert mango, sweet creamy pulp with thin skin and rich aroma"
            },
            {
                "name": "Totapuri (Ginimoothi)",
                "scientific_species": "Mangifera indica cv. Totapuri",
                "price": 55,
                "price_display": "₹55/kg",
                "season": "Apr-Jul",
                "duration_days": 1825,
                "yield_per_acre": 60,
                "characteristics": "Parrot-beak shaped mango heavily cultivated in Kolar & Srinivaspur for commercial pulp processing"
            },
            {
                "name": "Raspuri (Sweet Rasalu)",
                "scientific_species": "Mangifera indica cv. Raspuri",
                "price": 70,
                "price_display": "May-Jul",
                "duration_days": 1825,
                "yield_per_acre": 50,
                "characteristics": "Extremely juicy aromatic local mango beloved in Old Mysuru and Bengaluru regions"
            },
            {
                "name": "Malgova",
                "scientific_species": "Mangifera indica cv. Malgova",
                "price": 85,
                "price_display": "₹85/kg",
                "season": "May-Jul",
                "duration_days": 1825,
                "yield_per_acre": 45,
                "characteristics": "Large round fruit (up to 400g) with thick sweet fiberless pulp and tiny flat stone"
            },
            {
                "name": "Neelam",
                "scientific_species": "Mangifera indica cv. Neelam",
                "price": 45,
                "price_display": "₹45/kg",
                "season": "Jun-Aug",
                "duration_days": 1825,
                "yield_per_acre": 55,
                "characteristics": "Late season variety with exceptional keeping quality and regular annual bearing"
            },
            {
                "name": "Mallika",
                "scientific_species": "Mangifera indica (Neelam x Dashehari)",
                "price": 90,
                "price_display": "₹90/kg",
                "season": "May-Jun",
                "duration_days": 1825,
                "yield_per_acre": 48,
                "characteristics": "Hybrid variety combining high TSS (sugar), uniform canary yellow flesh and disease resistance"
            }
        ]
    },
    "Onion": {
        "unit": "quintal",
        "botanical_genus": "Allium cepa",
        "varieties": [
            {
                "name": "Bellary Red",
                "scientific_species": "Allium cepa cv. Bellary Red",
                "price": 2600,
                "price_display": "₹2,600/quintal",
                "season": "Kharif/Rabi",
                "duration_days": 115,
                "yield_per_acre": 90,
                "characteristics": "Renowned Karnataka variety with flattish-round pungent red bulbs and outstanding storage life"
            },
            {
                "name": "Arka Kalyan",
                "scientific_species": "Allium cepa cv. Arka Kalyan",
                "price": 2800,
                "price_display": "₹2,800/quintal",
                "season": "Kharif",
                "duration_days": 125,
                "yield_per_acre": 110,
                "characteristics": "Bred by IIHR Bengaluru, tolerant to purple blotch disease, deep red globular flesh"
            },
            {
                "name": "Bhima Super",
                "scientific_species": "Allium cepa cv. Bhima Super",
                "price": 2900,
                "price_display": "₹2,900/quintal",
                "season": "Kharif",
                "duration_days": 110,
                "yield_per_acre": 100,
                "characteristics": "Bred by DOGR, bright red single-centered bulbs suited for early Kharif harvest"
            },
            {
                "name": "Nashik Red",
                "scientific_species": "Allium cepa cv. Nashik Red",
                "price": 2500,
                "price_display": "₹2,500/quintal",
                "season": "Rabi",
                "duration_days": 120,
                "yield_per_acre": 95,
                "characteristics": "Standard commercial red onion with tight outer scales and minimal bolting"
            },
            {
                "name": "Pusa White",
                "scientific_species": "Allium cepa cv. Pusa White Flat",
                "price": 3100,
                "price_display": "₹3,100/quintal",
                "season": "Rabi",
                "duration_days": 130,
                "yield_per_acre": 85,
                "characteristics": "White onion cultivar with high total soluble solids (14% TSS) suited for dehydration"
            }
        ]
    },
    "Potato": {
        "unit": "quintal",
        "botanical_genus": "Solanum tuberosum",
        "varieties": [
            {
                "name": "Kufri Jyoti",
                "scientific_species": "Solanum tuberosum cv. Kufri Jyoti",
                "price": 1800,
                "price_display": "₹1,800/quintal",
                "season": "Rabi",
                "duration_days": 100,
                "yield_per_acre": 85,
                "characteristics": "Widely grown table potato with oval white tubers, resistant to late blight"
            },
            {
                "name": "Kufri Pukhraj",
                "scientific_species": "Solanum tuberosum cv. Kufri Pukhraj",
                "price": 1650,
                "price_display": "₹1,650/quintal",
                "season": "Rabi",
                "duration_days": 80,
                "yield_per_acre": 110,
                "characteristics": "Early bulking variety with smooth yellow skin, high yield in short crop windows"
            },
            {
                "name": "Kufri Chandramukhi",
                "scientific_species": "Solanum tuberosum cv. Chandramukhi",
                "price": 1900,
                "price_display": "₹1,900/quintal",
                "season": "Rabi",
                "duration_days": 90,
                "yield_per_acre": 80,
                "characteristics": "Attractive oval flat white tubers with shallow eyes and superior boiling score"
            },
            {
                "name": "Kufri Chipsona-1",
                "scientific_species": "Solanum tuberosum cv. Chipsona-1",
                "price": 2100,
                "price_display": "₹2,100/quintal",
                "season": "Rabi",
                "duration_days": 105,
                "yield_per_acre": 90,
                "characteristics": "Industrial processing variety with high dry matter and low reducing sugar for chips"
            }
        ]
    },
    "Turmeric": {
        "unit": "quintal",
        "botanical_genus": "Curcuma longa",
        "varieties": [
            {
                "name": "Salem Local",
                "scientific_species": "Curcuma longa cv. Salem",
                "price": 9500,
                "price_display": "₹9,500/quintal",
                "season": "Kharif",
                "duration_days": 270,
                "yield_per_acre": 110,
                "characteristics": "High grade long bright orange-yellow mother fingers with 4.5% curcumin content"
            },
            {
                "name": "IISR Pratibha",
                "scientific_species": "Curcuma longa cv. Pratibha",
                "price": 10500,
                "price_display": "₹10,500/quintal",
                "season": "Kharif",
                "duration_days": 225,
                "yield_per_acre": 130,
                "characteristics": "High curcumin (6.25%) early variety released by IISR with golden yellow polished fingers"
            },
            {
                "name": "Pragati",
                "scientific_species": "Curcuma longa cv. Pragati",
                "price": 10200,
                "price_display": "₹10,200/quintal",
                "season": "Kharif",
                "duration_days": 210,
                "yield_per_acre": 120,
                "characteristics": "Short duration variety (7 months) with 5.0% curcumin, suited for crop rotation"
            },
            {
                "name": "Erode Local",
                "scientific_species": "Curcuma longa cv. Erode",
                "price": 9800,
                "price_display": "₹9,800/quintal",
                "season": "Kharif",
                "duration_days": 260,
                "yield_per_acre": 105,
                "characteristics": "Famous GI-tagged South Indian turmeric with dark yellow core and fragrant aroma"
            }
        ]
    },
    "Chilli": {
        "unit": "quintal",
        "botanical_genus": "Capsicum annuum",
        "varieties": [
            {
                "name": "Byadgi Kaddi",
                "scientific_species": "Capsicum annuum cv. Byadgi Kaddi",
                "price": 28000,
                "price_display": "₹28,000/quintal",
                "season": "Kharif",
                "duration_days": 150,
                "yield_per_acre": 14,
                "characteristics": "GI-tagged Karnataka specialty, extra long wrinkled deep red pods with high ASTA color (150+)"
            },
            {
                "name": "Byadgi Dabbi",
                "scientific_species": "Capsicum annuum cv. Byadgi Dabbi",
                "price": 32000,
                "price_display": "₹32,000/quintal",
                "season": "Kharif",
                "duration_days": 155,
                "yield_per_acre": 12,
                "characteristics": "Plump pouch-shaped dry chilli with intense crimson natural oleoresin color and mild pungency"
            },
            {
                "name": "Guntur Sannam (S4)",
                "scientific_species": "Capsicum annuum cv. Guntur Sannam",
                "price": 18000,
                "price_display": "₹18,000/quintal",
                "season": "Kharif/Rabi",
                "duration_days": 140,
                "yield_per_acre": 18,
                "characteristics": "India's highest volume spice chilli with fiery heat (35,000 to 40,000 SHU) and thick skin"
            },
            {
                "name": "Pusa Jwala",
                "scientific_species": "Capsicum annuum cv. Pusa Jwala",
                "price": 19500,
                "price_display": "₹19,500/quintal",
                "season": "Kharif",
                "duration_days": 130,
                "yield_per_acre": 16,
                "characteristics": "Early pungent variety with light green slender fruits turning bright red at maturity"
            }
        ]
    }
}


# Comprehensive crop species/varieties and agronomic recommendation engine
from crop_varieties_data import CROP_SPECIES, get_crop_species_info, recommend_crop_varieties


def get_district_for_taluk(taluk_name: str) -> str:
    taluk_clean = taluk_name.strip().lower()
    for district, taluks in TALUK_MAP.items():
        for t in taluks:
            if t.lower() == taluk_clean or taluk_clean in t.lower() or t.lower() in taluk_clean:
                return district
    return taluk_name  # Return taluk name itself as fallback (it may be a district)


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_soil_data_from_csv():
    """Extract average pH and soil type from the crop dataset."""
    if not os.path.exists(CSV_FILE):
        return {"ph": 6.2, "soil_type": "Laterite"}
    
    ph_values = []
    soil_types = {}
    
    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ph_values.append(float(row['pH']))
                    soil = row.get('Soil_Type', 'Laterite')
                    soil_types[soil] = soil_types.get(soil, 0) + 1
                except (ValueError, KeyError):
                    continue
    except Exception as e:
        print(f"Error reading CSV for soil data: {e}")
        return {"ph": 6.2, "soil_type": "Laterite"}
    
    avg_ph = round(sum(ph_values) / len(ph_values), 2) if ph_values else 6.2
    most_common_soil = max(soil_types, key=soil_types.get) if soil_types else "Laterite"
    
    return {"ph": avg_ph, "soil_type": most_common_soil}

def get_recommendations_from_csv(ph, temp, rainfall, humidity=None):
    """Find best matching crops based on pH, Temperature, Rainfall, and Humidity using a scoring algorithm."""
    scores = {} # Store best match score for each crop type
    target_humidity = humidity if humidity is not None else 85.0
    
    try:
        for crop, profile in CROP_PROFILES.items():
            row_ph = profile["ph"]
            row_temp = profile["temp"]
            row_hum = profile["humidity"]
            row_rainfall = profile["rainfall"]
            
            # Normalized distances (weighted)
            # pH: range 4-9 (5) | Temp: 15-40 (25) | Hum: 30-100 (70) | Rain: 500-5000 (4500)
            d_ph = (abs(row_ph - ph) / 5.0) * 0.1
            d_temp = (abs(row_temp - temp) / 25.0) * 0.3
            d_hum = (abs(row_hum - target_humidity) / 70.0) * 0.3
            d_rain = (abs(row_rainfall - rainfall) / 4500.0) * 0.3
            
            # Similarity score
            distance = (d_ph**2 + d_temp**2 + d_hum**2 + d_rain**2)**0.5
            score = 1.0 / (1.0 + distance)
            scores[crop] = score
            
    except Exception as e:
        print(f"Error in recommendation logic: {e}")
        return ["Rice", "Arecanut", "Banana"]

    if not scores:
        return ["Coconut", "Arecanut", "Pepper"]
    
    # Return Top 5 unique crops sorted by score
    recommended = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [crop for crop, score in recommended[:5]]

def get_market_history(crop, taluk=None):
    """Get 5-year market price history for a crop."""
    history = []
    if not os.path.exists(MARKET_HISTORY_FILE):
        return history
    
    try:
        with open(MARKET_HISTORY_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Crop'] == crop:
                    if taluk and row['Taluk'] != taluk:
                        continue
                    history.append({
                        "taluk": row['Taluk'],
                        "crop": row['Crop'],
                        "year": int(row['Year']),
                        "month": row['Month'],
                        "price": float(row['Price']),
                        "unit": row['Unit'],
                        "trend": row['Trend']
                    })
    except Exception as e:
        print(f"Error reading market history: {e}")
    
    return history

def get_avg_yield_for_crop(crop):
    """Get average yield per acre from farmer details dataset."""
    yields = []
    if not os.path.exists(FARMER_DETAILS_FILE):
        return None
    
    try:
        with open(FARMER_DETAILS_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Primary_Crop'] == crop:
                    acres = float(row['Total_Land_Acres'])
                    total_yield = float(row['Yield_Quantity'])
                    if acres > 0:
                        yields.append(total_yield / acres)
    except Exception as e:
        print(f"Error reading farmer details: {e}")
    
    if yields:
        return round(sum(yields) / len(yields), 1)
        
    crop_yields = {
        "Coffee": 12.0,
        "Cardamom": 1.5,
        "Ginger": 80.0,
        "Jowar": 8.0,
        "Cotton": 7.0,
        "Maize": 20.0,
        "Bengal Gram": 6.0,
        "Red Gram": 5.0,
        "Wheat": 12.0,
        "Pomegranate": 60.0,
        "Ragi": 10.0,
        "Groundnut": 8.0,
        "Sugarcane": 350.0,
        "Tomato": 120.0,
        "Mango": 40.0,
        "Rice": 15.0,
        "Banana": 180.0,
        "Arecanut": 10.0,
        "Pepper": 4.0,
        "Cashew": 6.0,
        "Rubber": 8.0,
        "Coconut": 40.0,
    }
    return crop_yields.get(crop, 10.0)

# Models
class RegistrationRequest(BaseModel):
    name: str
    survey_number: str
    phone_number: str
    state: str
    district: str
    taluk: str
    hobli: str
    password: str
    land_area_acres: float = 0.0
    land_area_guntas: float = 0.0
    current_crop: Optional[str] = "Rice"

class LoginRequest(BaseModel):
    name: str
    password: str

@app.post("/register")
async def register_farmer(reg: RegistrationRequest):
    try:
        conn = sqlite3.connect("farmer_portal.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO farmers (name, current_crop, survey_number, phone_number, state, district, taluk, hobli, password, land_area_acres, land_area_guntas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            reg.name,
            reg.current_crop or "Rice",
            reg.survey_number,
            reg.phone_number,
            reg.state,
            reg.district,
            reg.taluk,
            reg.hobli,
            reg.password,
            reg.land_area_acres,
            reg.land_area_guntas
        ))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Farmer registered successfully"}
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login_farmer(login: LoginRequest):
    try:
        conn = sqlite3.connect("farmer_portal.db")
        cursor = conn.cursor()
        
        # Check user by name or phone
        cursor.execute("SELECT id FROM farmers WHERE name = ? OR phone_number = ?", (login.name, login.name))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Farmer account not found. Please register first.")
            
        # Check password
        cursor.execute("""
            SELECT name, taluk, district, current_crop, survey_number, phone_number, land_area_acres, land_area_guntas, hobli, state
            FROM farmers 
            WHERE (name = ? OR phone_number = ?) AND password = ?
            ORDER BY id DESC LIMIT 1
        """, (login.name, login.name, login.password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            crop_val = user[3] if user[3] else "Rice"
            return {
                "status": "success",
                "user": {
                    "name": user[0],
                    "taluk": user[1],
                    "district": user[2],
                    "current_crop": crop_val,
                    "primary_crop": crop_val,
                    "survey_number": user[4],
                    "phone_number": user[5],
                    "land_area_acres": user[6],
                    "land_area_guntas": user[7],
                    "hobli": user[8] or "",
                    "state": user[9] or "Karnataka"
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Password incorrect")
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during login")

@app.get("/farmer-info/{name}")
async def get_farmer_info(name: str):
    try:
        conn = sqlite3.connect("farmer_portal.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, taluk, district, current_crop, survey_number, phone_number FROM farmers WHERE name = ? OR phone_number = ? ORDER BY id DESC LIMIT 1", (name, name))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                "name": user[0],
                "taluk": user[1],
                "district": user[2],
                "current_crop": user[3] or "Rice",
                "survey_number": user[4],
                "phone_number": user[5]
            }
        raise HTTPException(status_code=404, detail="Farmer not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Farmer Portal API is running"}

# Helper to resolve coordinates from location name (GPS format "lat,lon" or Taluk lookup)
def get_location_coordinates(location: str) -> tuple:
    try:
        parts = location.split(',')
        if len(parts) == 2:
            return float(parts[0].strip()), float(parts[1].strip())
    except ValueError:
        pass
        
    loc_clean = location.strip().title()
    # Check direct Taluk coords mapping
    if loc_clean in TALUK_COORDS:
        return TALUK_COORDS[loc_clean]
        
    # Check if this is a taluk listed in our taluk map, and match it
    for dist, taluks in TALUK_MAP.items():
        for t in taluks:
            if t.lower() in location.lower() or location.lower() in t.lower():
                if t in TALUK_COORDS:
                    return TALUK_COORDS[t]
                    
    # District fallbacks
    district_fallbacks = {
        "Dakshina Kannada": (12.9141, 74.8560),
        "Udupi": (13.3409, 74.7421),
        "Uttara Kannada": (14.8000, 74.1300),
        "Bengaluru Urban": (12.9716, 77.5946),
        "Bengaluru Rural": (13.2483, 77.7128),
        "Hassan": (13.0050, 76.1028),
        "Chikkamagaluru": (13.3161, 75.7720),
        "Kodagu": (12.4244, 75.7389),
        "Shivamogga": (13.9299, 75.5681),
        "Tumakuru": (13.3392, 77.1140),
        "Mandya": (12.5218, 76.8973),
        "Mysuru": (12.2958, 76.6394),
        "Kalaburagi": (17.3297, 76.8343),
        "Belagavi": (15.8497, 74.4977),
        "Davanagere": (14.4644, 75.9219),
        "Dharwad": (15.4589, 75.0078),
        "Ballari": (15.1394, 76.9214),
        "Bagalkot": (16.1817, 75.6958),
        "Bidar": (17.9104, 77.5199),
        "Vijayapura": (16.8302, 75.7100),
    }
    
    for d, coords in district_fallbacks.items():
        if d.lower() in location.lower() or location.lower() in d.lower():
            return coords
            
    return (12.9141, 74.8560)

# WMO Weather Codes to descriptions
WMO_WEATHER_CODES = {
    0: "Clear Sky",
    1: "Partly Cloudy",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Foggy",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    56: "Light Drizzle",
    57: "Dense Drizzle",
    61: "Light Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    66: "Light Rain",
    67: "Heavy Rain",
    71: "Slight Snowfall",
    73: "Moderate Snowfall",
    75: "Heavy Snowfall",
    77: "Snow Grains",
    80: "Light Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    85: "Slight Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Hail",
    99: "Thunderstorm with Heavy Hail"
}

@app.get("/soil-data")
async def get_soil_info(taluk: Optional[str] = None, district: Optional[str] = None):
    """Get soil pH, type, and live parameters (temperature, moisture) from Open-Meteo."""
    target_district = "Dakshina Kannada"
    location_name = "Mangaluru"
    if taluk:
        location_name = taluk
        target_district = get_district_for_taluk(taluk) or "Dakshina Kannada"
    elif district:
        location_name = district
        target_district = district
        
    lat, lon = get_location_coordinates(location_name)
    
    # Get baseline soil type and pH
    soil_type = "Laterite"
    ph = 6.2
    if target_district and target_district in DISTRICT_BASELINES:
        ph = DISTRICT_BASELINES[target_district]["ph"]
        soil_type = DISTRICT_BASELINES[target_district]["soil_type"]
    else:
        # Fallback to CSV check
        try:
            csv_data = get_soil_data_from_csv()
            if csv_data:
                ph = csv_data.get("ph", ph)
                soil_type = csv_data.get("soil_type", soil_type)
        except Exception:
            pass
            
    # Fetch live variables
    live_temp = 25.4
    live_moisture = 34.2
    
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=soil_temperature_0_to_7cm,soil_moisture_0_to_7cm&timezone=auto"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            curr = data.get("current_weather", {})
            hourly = data.get("hourly", {})
            curr_time = curr.get("time")
            idx = 0
            if curr_time and "time" in hourly:
                times = hourly["time"]
                if curr_time in times:
                    idx = times.index(curr_time)
                else:
                    idx = next((i for i, t in enumerate(times) if t.startswith(curr_time[:13])), 0)
                    
            if "soil_temperature_0_to_7cm" in hourly and len(hourly["soil_temperature_0_to_7cm"]) > idx:
                live_temp = float(hourly["soil_temperature_0_to_7cm"][idx])
            if "soil_moisture_0_to_7cm" in hourly and len(hourly["soil_moisture_0_to_7cm"]) > idx:
                val = float(hourly["soil_moisture_0_to_7cm"][idx])
                live_moisture = round(val * 100, 1) if val <= 1.0 else round(val, 1)
    except Exception as e:
        print(f"Soil parameters fetch error: {e}")
        
    return {
        "ph": ph,
        "soil_type": soil_type,
        "temperature": round(live_temp, 1),
        "moisture": round(live_moisture, 1),
        "latitude": lat,
        "longitude": lon,
        "source": "Open-Meteo Soil Variable Service"
    }

@app.get("/lookup/{survey_number:path}")
async def lookup_survey(survey_number: str):
    """Check survey details. If not in mock_db.json, dynamically simulate a Karnataka Bhoomi RTC."""
    data = load_data()
    surveys = data.get("surveys", {})
    
    s_norm = survey_number.strip().upper()
    if s_norm in surveys:
        return surveys[s_norm]
        
    # Dynamically generate realistic survey details for Karnataka
    import hashlib
    h = int(hashlib.md5(s_norm.encode()).hexdigest(), 16)
    
    districts = list(TALUK_MAP.keys())
    district = districts[h % len(districts)]
    taluks = TALUK_MAP[district]
    taluk = taluks[(h >> 2) % len(taluks)]
    
    hoblis_options = {
        "Mangaluru": ["Mangaluru A", "Mangaluru B", "Surathkal", "Gurupura", "Mulki", "Haleyangadi", "Moodabidri"],
        "Bantwal": ["Bantwal", "Panemangaluru", "Vittal", "Rayi", "Navoor"],
        "Puttur": ["Puttur", "Uppinangady", "Nelyadi", "Kadaba"],
        "Belthangady": ["Belthangady", "Venur", "Kokkada", "Dharmasthala", "Poonjalkatte"],
        "Sullia": ["Sullia", "Panja", "Bellare", "Subrahmanya"],
        "Moodabidri": ["Moodabidri Kasaba", "Belavai", "Padumarnadu", "Puttige", "Mijar"],
        "Kadaba": ["Kadaba Kasaba", "Subrahmanya", "Nelyadi"],
    }
    hoblis = hoblis_options.get(taluk, [f"{taluk} Kasaba Hobli", f"{taluk} Rural Hobli"])
    hobli = hoblis[(h >> 4) % len(hoblis)]
    
    villages = ["Keladi", "Koteshwara", "Hadinbal", "Hanubalu", "Belavai", "Ullal", "Vittal", "Kokkada", "Subrahmanya", "Kalladka"]
    village = villages[(h >> 6) % len(villages)]
    
    return {
        "state": "Karnataka",
        "district": district,
        "taluk": taluk,
        "village": village,
        "hobli": hobli,
        "land_acres": 1 + (h % 5),
        "land_guntas": h % 40,
        "owner_name": f"Farmer {s_norm}"
    }

@app.get("/weather/{location}")
async def get_weather(location: str):
    lat, lon = get_location_coordinates(location)
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relative_humidity_2m,precipitation,rain,soil_temperature_0_to_7cm,soil_moisture_0_to_7cm&daily=precipitation_sum&timezone=auto"
        response = requests.get(url, timeout=12)
        
        if response.status_code == 200:
            data = response.json()
            curr = data.get("current_weather", {})
            hourly = data.get("hourly", {})
            daily = data.get("daily", {})
            
            # Find the hourly index that matches current weather time
            curr_time = curr.get("time")
            idx = 0
            if curr_time and "time" in hourly:
                times = hourly["time"]
                if curr_time in times:
                    idx = times.index(curr_time)
                else:
                    try:
                        idx = next((i for i, t in enumerate(times) if t.startswith(curr_time[:13])), 0)
                    except StopIteration:
                        pass
            
            temp = curr.get("temperature", 28.0)
            wind_speed = curr.get("windspeed", 5.0)
            weather_code = curr.get("weathercode", 0)
            description = WMO_WEATHER_CODES.get(weather_code, "Overcast")
            
            humidity = 65
            if "relative_humidity_2m" in hourly and len(hourly["relative_humidity_2m"]) > idx:
                humidity = int(hourly["relative_humidity_2m"][idx])
                
            rain_current = 0.0
            if "precipitation" in hourly and len(hourly["precipitation"]) > idx:
                rain_current = float(hourly["precipitation"][idx])
                
            soil_temp = 25.0
            if "soil_temperature_0_to_7cm" in hourly and len(hourly["soil_temperature_0_to_7cm"]) > idx:
                soil_temp = float(hourly["soil_temperature_0_to_7cm"][idx])
                
            soil_moisture = 30.0
            if "soil_moisture_0_to_7cm" in hourly and len(hourly["soil_moisture_0_to_7cm"]) > idx:
                val = float(hourly["soil_moisture_0_to_7cm"][idx])
                if val <= 1.0:
                    soil_moisture = round(val * 100, 1)
                else:
                    soil_moisture = round(val, 1)
            
            today_rain = 0.0
            if "precipitation_sum" in daily and len(daily["precipitation_sum"]) > 0:
                today_rain = float(daily["precipitation_sum"][0])
            
            estimated_annual_rainfall = 1200
            district = get_district_for_taluk(location.split(',')[0].strip()) if ',' in location else get_district_for_taluk(location)
            if district in DISTRICT_BASELINES:
                estimated_annual_rainfall = DISTRICT_BASELINES[district]["avg_rainfall"]
            
            return {
                "temperature": round(temp, 1),
                "humidity": humidity,
                "rainfall": round(estimated_annual_rainfall),
                "rain_today": round(today_rain, 1),
                "rain_current": round(rain_current, 1),
                "soil_temp": round(soil_temp, 1),
                "soil_moisture": round(soil_moisture, 1),
                "description": description,
                "location": location.split(',')[0].strip().title() if ',' in location else location,
                "latitude": lat,
                "longitude": lon,
                "source": "Open-Meteo Weather & Soil API"
            }
        else:
            print(f"Open-Meteo API returned {response.status_code}: {response.text}")
            return generate_mock_weather_for_coords(location, lat, lon)
    except Exception as e:
        print(f"Weather fetch error: {e}")
        return generate_mock_weather_for_coords(location, lat, lon)

def generate_mock_weather_for_coords(location: str, lat: float, lon: float):
    res = generate_mock_weather(location)
    res["latitude"] = lat
    res["longitude"] = lon
    res["soil_temp"] = round(res["temperature"] - 2.5, 1)
    res["soil_moisture"] = round(30 + (res["humidity"] * 0.2), 1)
    res["rain_today"] = round(res["rain_current"] * 4.5, 1)
    res["source"] = "Simulated Live Parameters (Open-Meteo offline)"
    return res

def generate_mock_weather(location: str):
    """Generate realistic mock weather based on district/taluk baselines."""
    district = get_district_for_taluk(location)
    baseline = DISTRICT_BASELINES.get(district, {
        "ph": 6.5, "soil_type": "Red Sandy", 
        "avg_temp": 26.5, "avg_humidity": 65, "avg_rainfall": 800
    })
    
    import hashlib
    h = int(hashlib.md5(location.lower().encode()).hexdigest(), 16)
    temp_var = ((h % 5) - 2) * 0.5 # -1C to +1C
    humidity_var = ((h % 7) - 3) # -3% to +3%
    rainfall_var = ((h % 11) - 5) * 10 # -50mm to +50mm
    
    temp = baseline["avg_temp"] + temp_var
    humidity = baseline["avg_humidity"] + humidity_var
    rainfall = baseline["avg_rainfall"] + rainfall_var
    
    conditions = ["Clear Skies", "Scattered Clouds", "Mostly Cloudy", "Light Rain", "Dry & Sunny", "Humid & Cloudy", "Overcast", "Mist"]
    if rainfall > 2000:
        conditions = ["Light Rain", "Heavy Rain", "Humid & Cloudy", "Overcast"]
    elif rainfall < 700:
        conditions = ["Dry & Sunny", "Clear Skies", "Scattered Clouds"]
        
    condition = conditions[h % len(conditions)]
    
    return {
        "temperature": round(temp, 1),
        "humidity": int(humidity),
        "rainfall": round(max(100, rainfall)),
        "rain_current": 1.2 if "Rain" in condition else 0.0,
        "description": condition,
        "location": location,
        "source": "fallback"
    }

KARNATAKA_FARMER_NAMES = [
    ("Mahadeva", "Gowda", "ಮಹಾದೇವ", "ಗೌಡ"),
    ("Somanna", "Patil", "ಸೋಮಣ್ಣ", "ಪಾಟೀಲ್"),
    ("Chandrashekar", "Hegde", "ಚಂದ್ರಶೇಖರ್", "ಹೆಗಡೆ"),
    ("Eshwarappa", "Bhat", "ಈಶ್ವರಪ್ಪ", "ಭಟ್"),
    ("Parameshwar", "Naik", "ಪರಮೇಶ್ವರ", "ನಾಯ್ಕ್"),
    ("Shivakumar", "Reddy", "ಶಿವಕುಮಾರ್", "ರೆಡ್ಡಿ"),
    ("Dyamanna", "Pujari", "ದ್ಯಾಮಣ್ಣ", "ಪೂಜಾರಿ"),
    ("Mylarappa", "Shetty", "ಮೈಲಾರಪ್ಪ", "ಶೆಟ್ಟಿ"),
    ("Hanumanthappa", "Kulkarni", "ಹನುಮಂತಪ್ಪ", "ಕುಲಕರ್ಣಿ"),
    ("Thimmegowda", "Deshmukh", "ತಿಮ್ಮೇಗೌಡ", "ದೇಶಮುಖ್"),
    ("Kalleshappa", "Hiremath", "ಕಲ್ಲೇಶಪ್ಪ", "ಹಿರೇಮಠ"),
    ("Sidramappa", "Angadi", "ಸಿದ್ಧರಾಮಪ್ಪ", "ಅಂಗಡಿ"),
    ("Channabasappa", "Totada", "ಚನ್ನಬಸಪ್ಪ", "ತೋಟದ"),
    ("Narasimha", "Marathe", "ನರಸಿಂಹ", "ಮರಾಠೆ"),
    ("Govindappa", "Ballal", "ಗೋವಿಂದಪ್ಪ", "ಬಲ್ಲಾಳ್"),
    ("Lingaraju", "Alva", "ಲಿಂಗರಾಜು", "ಆಳ್ವ"),
    ("Anjinappa", "Rao", "ಅಂಜಿನಪ್ಪ", "ರಾವ್"),
    ("Bheemappa", "Kamath", "ಭೀಮಪ್ಪ", "ಕಾಮತ್"),
    ("Yellappa", "Shenoy", "ಯಲ್ಲಪ್ಪ", "ಶೆಣೈ"),
    ("Puttaswamy", "Kudva", "ಪುಟ್ಟಸ್ವಾಮಿ", "ಕುಡ್ವ"),
    ("Marigowda", "Moger", "ಮಾರಿಗೌಡ", "ಮೊಗೇರ್"),
    ("Krishnappa", "Harikanth", "ಕೃಷ್ಣಪ್ಪ", "ಹರಿಕಾಂತ್"),
    ("Lakshminarayana", "Bovi", "ಲಕ್ಷ್ಮೀನಾರಾಯಣ", "ಬೋವಿ"),
    ("Venkataramana", "Lambani", "ವೆಂಕಟರಮಣ", "ಲಂಬಾಣಿ"),
    ("Raghavendra", "Badiger", "ರಾಘವೇಂದ್ರ", "ಬಡಿಗೇರ್"),
    ("Sridhara", "Kambar", "ಶ್ರೀಧರ", "ಕಂಬಾರ"),
    ("Gopalakrishna", "Hadimani", "ಗೋಪಾಲಕೃಷ್ಣ", "ಹಡಿಮನಿ"),
    ("Ramachandra", "Barker", "ರಾಮಚಂದ್ರ", "ಬರ್ಕರ್"),
    ("Ganapathi", "Gudigar", "ಗಣಪತಿ", "ಗುಡಿಗಾರ್"),
    ("Vigneshwara", "Madivala", "ವಿಘ್ನೇಶ್ವರ", "ಮಡಿವಾಳ"),
    ("Keshava", "Kotian", "ಕೇಶವ", "ಕೋಟ್ಯಾನ್"),
    ("Subramanya", "Acharya", "ಸುಬ್ರಹ್ಮಣ್ಯ", "ಆಚಾರ್ಯ"),
    ("Nanjundappa", "Devadiga", "ನಂಜುಂಡಪ್ಪ", "ದೇವಾಡಿಗ"),
    ("Mallikarjun", "Kattimani", "ಮಲ್ಲಿಕಾರ್ಜುನ", "ಕಟ್ಟಿಮನಿ"),
    ("Gurushanthappa", "Metagudda", "ಗುರುಶಾಂತಪ್ಪ", "ಮೇಟಿಗುಡ್ಡ"),
    ("Veerabhadrappa", "Chaluvadi", "ವೀರಭದ್ರಪ್ಪ", "ಚಲುವಾದಿ"),
    ("Bhojappa", "Kuruba", "ಭೋಜಪ್ಪ", "ಕುರುಬ"),
    ("Rukmayya", "Bari", "ರುಕ್ಮಯ್ಯ", "ಬಾರಿ"),
    ("Kanthappa", "Kudroli", "ಕಾಂತಪ್ಪ", "ಕುದ್ರೋಳಿ"),
    ("Kittanna", "Uppar", "ಕಿಟ್ಟಣ್ಣ", "ಉಪ್ಪಾರ"),
    ("Kaverappa", "Bhandari", "ಕಾವೇರಪ್ಪ", "ಭಂಡಾರಿ"),
    ("Muthappa", "Nayaka", "ಮುತ್ತಪ್ಪ", "ನಾಯಕ"),
    ("Somayya", "Salimath", "ಸೋಮಯ್ಯ", "ಸಾಲಿಮಠ"),
    ("Sharada", "Acharya", "ಶಾರದಾ", "ಆಚಾರ್ಯ"),
    ("Pushpa", "Gowda", "ಪುಷ್ಪಾ", "ಗೌಡ"),
    ("Padma", "Poojary", "ಪದ್ಮಾ", "ಪೂಜಾರಿ"),
    ("Parvathi", "Kotian", "ಪಾರ್ವತಿ", "ಕೋಟ್ಯಾನ್"),
    ("Geetha", "Hegde", "ಗೀತಾ", "ಹೆಗಡೆ"),
    ("Suma", "Reddy", "ಸುಮಾ", "ರೆಡ್ಡಿ"),
    ("Girija", "Patil", "ಗಿರಿಜಾ", "ಪಾಟೀಲ್"),
    ("Renuka", "Bhat", "ರೇಣುಕಾ", "ಭಟ್")
]

@app.get("/bhoomi/land-map")
async def get_bhoomi_land_map(
    taluk: str,
    hobli: Optional[str] = None,
    survey_number: Optional[str] = None,
    user_name: Optional[str] = "You",
    user_acres: Optional[float] = 2.0,
    user_guntas: Optional[float] = 0.0,
    user_crop: Optional[str] = "Rice",
    lat: Optional[float] = None,
    lon: Optional[float] = None
):
    """Generate a realistic Bhoomi cadastral map centered on the farmer's land with unique non-repeating neighbours."""
    # Resolve center coordinates
    center_lat, center_lon = 12.9141, 74.8560
    if lat is not None and lon is not None:
        center_lat = lat
        center_lon = lon
    elif hobli and hobli in HOBLI_COORDS:
        center_lat, center_lon = HOBLI_COORDS[hobli]
    else:
        center_lat, center_lon = get_location_coordinates(taluk)
        
    # Standardize survey number
    user_survey = survey_number or "120"
    user_survey_clean = user_survey.strip().upper()
    
    # Generate a 3x3 grid of adjacent land parcels
    spacing = 0.0025
    width = 0.0021
    
    parcels = []
    
    district = get_district_for_taluk(taluk) or "Dakshina Kannada"
    coastal_districts = ["Dakshina Kannada", "Udupi", "Uttara Kannada"]
    malnad_districts = ["Chikkamagaluru", "Kodagu", "Hassan", "Shivamogga"]
    northern_districts = ["Bagalkot", "Ballari", "Belagavi", "Bidar", "Chitradurga", "Davanagere", "Dharwad", "Gadag", "Haveri", "Kalaburagi", "Koppal", "Raichur", "Vijayanagara", "Vijayapura", "Yadgir"]
    
    if district in coastal_districts:
        crops = ["Rice", "Banana", "Arecanut", "Pepper", "Cashew", "Coconut"]
    elif district in malnad_districts:
        crops = ["Coffee", "Cardamom", "Ginger", "Pepper", "Banana"]
    elif district in northern_districts:
        crops = ["Jowar", "Cotton", "Maize", "Bengal Gram", "Red Gram", "Wheat"]
    else:
        crops = ["Ragi", "Maize", "Groundnut", "Sugarcane", "Tomato", "Mango"]
        
    import hashlib
    h_base = int(hashlib.md5(f"{taluk}_{hobli or ''}_{user_survey_clean}".encode()).hexdigest(), 16)
    
    # Query real registered farmers in this taluk from DB to display as live neighbours (deduplicated)
    live_registered_neighbors = []
    try:
        conn = sqlite3.connect("farmer_portal.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, current_crop, survey_number, land_area_acres, land_area_guntas 
            FROM farmers 
            WHERE LOWER(taluk) = ? AND LOWER(name) != ? AND name != ''
            GROUP BY LOWER(name)
            ORDER BY MAX(id) DESC LIMIT 5
        """, (taluk.lower(), (user_name or "").lower().strip()))
        live_registered_neighbors = cursor.fetchall()
        conn.close()
    except Exception:
        pass
    
    neighbour_slot = 0
    used_owners = { (user_name or "").lower().strip() }
    
    for r in [-1, 0, 1]:
        for c in [-1, 0, 1]:
            is_user = (r == 0 and c == 0)
            cell_key = f"{taluk}_{hobli or ''}_{user_survey_clean}_{r}_{c}"
            h_val = int(hashlib.md5(cell_key.encode()).hexdigest(), 16)
            
            lat_c = center_lat + r * spacing
            lon_c = center_lon + c * spacing
            
            lat_min = lat_c - width / 2.0
            lat_max = lat_c + width / 2.0
            lon_min = lon_c - width / 2.0
            lon_max = lon_c + width / 2.0
            
            p_scale = 0.0003
            p_lat_min = lat_min + (((h_val & 0xFF) % 7) - 3) * (p_scale / 6.0)
            p_lat_max = lat_max + ((((h_val >> 8) & 0xFF) % 7) - 3) * (p_scale / 6.0)
            p_lon_min = lon_min + ((((h_val >> 16) & 0xFF) % 7) - 3) * (p_scale / 6.0)
            p_lon_max = lon_max + ((((h_val >> 24) & 0xFF) % 7) - 3) * (p_scale / 6.0)
            
            polygon = [
                [p_lat_min, p_lon_min],
                [p_lat_max, p_lon_min + (((h_val >> 4) & 0x03) - 1) * 0.00006],
                [p_lat_max + (((h_val >> 12) & 0x03) - 1) * 0.00006, p_lon_max],
                [p_lat_min, p_lon_max + (((h_val >> 20) & 0x03) - 1) * 0.00006]
            ]
            
            recommended_crops = []
            suggested_work = ""
            suggested_work_kn = ""
            is_empty = False
            
            if is_user:
                s_num = user_survey_clean
                owner = user_name or "You"
                owner_kn = "ನೀವು (You)"
                acres = user_acres or 2.0
                guntas = user_guntas or 0.0
                crop = user_crop or "Rice"
                l_type = "Wet" if crop in ["Rice", "Sugarcane"] else "Garden" if crop in ["Arecanut", "Coconut", "Coffee"] else "Dry"
                l_type_kn = "ತರಿ (Wet)" if l_type == "Wet" else "ಬಾಗಾಯ್ತು (Garden)" if l_type == "Garden" else "ಖುಷ್ಕಿ (Dry)"
                soil = DISTRICT_BASELINES.get(district, {}).get("soil_type", "Red Sandy")
            else:
                survey_base = 100
                try:
                    import re
                    m = re.match(r'\d+', user_survey_clean)
                    if m:
                        survey_base = int(m.group())
                except Exception:
                    pass
                    
                if r == 0:
                    s_num = f"{survey_base}/{abs(c) + 1}"
                elif c == 0:
                    s_num = f"{survey_base + r}"
                else:
                    s_num = f"{survey_base + r}/{abs(c) + 1}"
                    
                # 1 parcel out of 8 as fallow/government land, others with unique distinct farmers
                is_empty = (neighbour_slot == 5)
                
                if is_empty:
                    owner = "Government Land (Fallow)"
                    owner_kn = "ಸರ್ಕಾರಿ ಬಂಜರು ಜಮೀನು"
                    crop = "Fallow"
                    l_type = "Dry"
                    l_type_kn = "ಖುಷ್ಕಿ (Dry)"
                    soil = DISTRICT_BASELINES.get(district, {}).get("soil_type", "Laterite")
                    acres = 3.5
                    guntas = 0.0
                elif live_registered_neighbors and neighbour_slot < len(live_registered_neighbors) and live_registered_neighbors[neighbour_slot][0].lower() not in used_owners:
                    reg_row = live_registered_neighbors[neighbour_slot]
                    used_owners.add(reg_row[0].lower())
                    owner = f"{reg_row[0]} (Live Member)"
                    owner_kn = f"{reg_row[0]} (ನೋಂದಾಯಿತ ರೈತರು)"
                    crop = reg_row[1] or crops[(neighbour_slot) % len(crops)]
                    s_num = reg_row[2] or s_num
                    acres = float(reg_row[3] or 2.0)
                    guntas = float(reg_row[4] or 0.0)
                    l_type = "Wet" if crop in ["Rice", "Sugarcane"] else "Garden" if crop in ["Arecanut", "Coconut", "Coffee"] else "Dry"
                    l_type_kn = "ತರಿ (Wet)" if l_type == "Wet" else "ಬಾಗಾಯ್ತು (Garden)" if l_type == "Garden" else "ಖುಷ್ಕಿ (Dry)"
                    soil = DISTRICT_BASELINES.get(district, {}).get("soil_type", "Laterite")
                else:
                    # Pick guaranteed unique name from KARNATAKA_FARMER_NAMES
                    name_idx = (h_base + neighbour_slot * 7 + 1) % len(KARNATAKA_FARMER_NAMES)
                    while KARNATAKA_FARMER_NAMES[name_idx][0].lower() in used_owners:
                        name_idx = (name_idx + 3) % len(KARNATAKA_FARMER_NAMES)
                    fname, lname, fname_kn, lname_kn = KARNATAKA_FARMER_NAMES[name_idx]
                    used_owners.add(fname.lower())
                    owner = f"{fname} {lname}"
                    owner_kn = f"{fname_kn} {lname_kn}"
                    
                    crop = crops[(h_base + neighbour_slot) % len(crops)]
                    l_type = "Wet" if crop in ["Rice", "Sugarcane"] else "Garden" if crop in ["Arecanut", "Coconut", "Coffee"] else "Dry"
                    l_type_kn = "ತರಿ (Wet)" if l_type == "Wet" else "ಬಾಗಾಯ್ತು (Garden)" if l_type == "Garden" else "ಖುಷ್ಕಿ (Dry)"
                    soil = DISTRICT_BASELINES.get(district, {}).get("soil_type", "Laterite")
                    acres = 1 + ((h_base + neighbour_slot * 3) % 4)
                    guntas = (h_val >> 2) % 40
                neighbour_slot += 1

            # Calculate recommendations & suggested work for all parcels (user, empty, or neighbour)
            baseline = DISTRICT_BASELINES.get(district, {"soil_type": "Laterite", "ph": 6.2, "avg_temp": 28.0, "avg_humidity": 85, "avg_rainfall": 3500})
            rec_list = get_recommendations_from_csv(baseline["ph"], baseline["avg_temp"], baseline["avg_rainfall"], baseline["avg_humidity"])
            recommended_crops = rec_list[:3]  # Top 3 suggestions
            
            # Add detailed agricultural development work suggestions based on soil type
            work_suggestions = {
                "Laterite": (
                    "Soil conservation, deep plowing before monsoon, planting cashew/pepper/rubber, and application of organic compost & lime to adjust pH.",
                    "ಮಣ್ಣು ಸಂರಕ್ಷಣೆ, ಮುಂಗಾರಿಗೆ ಮುನ್ನ ಆಳವಾದ ಉಳುಮೆ, ಗೋಡಂಬಿ/ಕಾಳುಮೆಣಸು/ರಬ್ಬರ್ ನೆಡುವುದು, ಮಣ್ಣಿನ ಆಮ್ಲೀಯತೆ ಸರಿಪಡಿಸಲು ಸಾವಯವ ಗೊಬ್ಬರ ಮತ್ತು ಸುಣ್ಣದ ಬಳಕೆ."
                ),
                "Red Sandy": (
                    "Drip irrigation setup, green manuring, crop rotation with legumes to improve soil nitrogen, and mulching to prevent moisture loss.",
                    "ಹನಿ ನೀರಾವರಿ ಅಳವಡಿಕೆ, ಹಸಿರು ಎಲೆ ಗೊಬ್ಬರ ಬಳಕೆ, ಮಣ್ಣಿನ ಸಾರಜನಕ ಹೆಚ್ಚಿಸಲು ದ್ವಿದಳ ಧಾನ್ಯಗಳೊಂದಿಗೆ ಬೆಳೆ ಸರದಿ, ತೇವಾಂಶ ತಡೆಯಲು ಹೊದಿಕೆ (Mulching) ವಿಧಾನ."
                ),
                "Black Cotton": (
                    "Constructing drainage channels to prevent waterlogging, soil aeration, gypsum application, and crop rotation with cotton or gram.",
                    "ನೀರು ನಿಲ್ಲದಂತೆ ಬಸಿದುಹೋಗುವ ಚರಂಡಿ ನಿರ್ಮಾಣ, ಮಣ್ಣಿನ ವಾತಾಯನ ಕ್ರಿಯೆ, ಜಿಪ್ಸಮ್ ಬಳಕೆ, ಹತ್ತಿ ಅಥವಾ ಕಡಲೆಯೊಂದಿಗೆ ಬೆಳೆ ಸರದಿ."
                ),
                "Red Clayey": (
                    "Adding organic compost to improve soil texture, contour bunding to prevent erosion, planting fruits like banana/mango, and deep drainage.",
                    "ಮಣ್ಣಿನ ವಿನ್ಯಾಸ ಸುಧಾರಿಸಲು ಸಾವಯವ ಗೊಬ್ಬರ ಸೇರಿಸುವುದು, ಮಣ್ಣಿನ ಸವಕಳಿ ತಡೆಯಲು ಸಮಪಾತಳಿ ಬದು ನಿರ್ಮಾಣ, ಬಾಳೆ/ಮಾವಿನ ಹಣ್ಣಿನ ಗಿಡ ನೆಡುವುದು, ಬಸಿಕಾಲುವೆ ನಿರ್ಮಾಣ."
                )
            }
            work_en, work_kn = work_suggestions.get(soil, (
                "Organic composting, terracing, contour bunding to prevent soil erosion, and crop rotation.",
                "ಸಾವಯವ ಗೊಬ್ಬರ ತಯಾರಿಕೆ, ತಟ್ಟಿ ಹಂತದ ಕೃಷಿ, ಮಣ್ಣಿನ ಸವಕಳಿ ತಡೆಯಲು ಸಮಪಾತಳಿ ಬದು ನಿರ್ಮಾಣ ಮತ್ತು ಬೆಳೆ ಸರದಿ."
            ))
            suggested_work = work_en
            suggested_work_kn = work_kn
            
            crop_kn_map = {
                "Rice": "ಅಕ್ಕಿ (ಭತ್ತ)", "Banana": "ಬಾಳೆಹಣ್ಣು", "Arecanut": "ಅಡಿಕೆ", "Pepper": "ಕಾಳುಮೆಣಸು", 
                "Cashew": "ಗೋಡಂಬಿ", "Rubber": "ರಬ್ಬರ್", "Coconut": "ತೆಂಗಿನಕಾಯಿ", "Coffee": "ಕಾಫಿ", 
                "Cardamom": "ಏಲಕ್ಕಿ", "Ginger": "ಶುಂಠಿ", "Jowar": "ಜೋಳ", "Cotton": "ಹತ್ತಿ", 
                "Maize": "ಮೆಕ್ಕೆಜೋಳ", "Bengal Gram": "ಕಡಲೆ", "Red Gram": "ತೊಗರಿ", "Wheat": "ಗೋಧಿ", 
                "Pomegranate": "ದಾಳಿಂಬೆ", "Ragi": "ರಾಗಿ", "Groundnut": "ಶೇಂಗಾ", "Sugarcane": "ಕಬ್ಬು", 
                "Tomato": "ಟೊಮೆಟೊ", "Mango": "ಮಾವಿನಹಣ್ಣು", "Fallow": "ಬೀಳು ಜಮೀನು (ಖಾಲಿ)"
            }
            crop_kn = crop_kn_map.get(crop, crop)
            
            soil_kn_map = {
                "Laterite": "ಲ್ಯಾಟರೈಟ್ (ಕೆಂಪು ಜೇಡಿ ಮಣ್ಣು)", "Red Sandy": "ಕೆಂಪು ಉಸುಕು ಮಣ್ಣು", 
                "Red Loam": "ಕೆಂಪು ಲೋಮ್ ಮಣ್ಣು", "Black Cotton": "ಕಪ್ಪು ಹತ್ತಿ ಮಣ್ಣು", 
                "Mixed Red & Black": "ಕೆಂಪು ಮತ್ತು ಕಪ್ಪು ಮಿಶ್ರಿತ ಮಣ್ಣು", "Black Clayey": "ಕಪ್ಪು ಜೇಡಿ ಮಣ್ಣು",
                "Red Clayey": "ಕೆಂಪು ಜೇಡಿ ಮಣ್ಣು", "Red Loamy": "ಕೆಂಪು ಲೋಮಿ ಮಣ್ಣು"
            }
            soil_kn = soil_kn_map.get(soil, soil)
            
            parcels.append({
                "survey_number": s_num,
                "owner_name": owner,
                "owner_name_kn": owner_kn,
                "land_acres": int(acres),
                "land_guntas": int(guntas),
                "land_type": l_type,
                "land_type_kn": l_type_kn,
                "soil_type": soil,
                "soil_type_kn": soil_kn,
                "crop_grown": crop,
                "crop_grown_kn": crop_kn,
                "is_user": is_user,
                "is_empty": is_empty,
                "recommended_crops": recommended_crops,
                "suggested_work": suggested_work,
                "suggested_work_kn": suggested_work_kn,
                "polygon": polygon
            })
            
    return {
        "center": [center_lat, center_lon],
        "parcels": parcels,
        "taluk": taluk,
        "hobli": hobli or f"{taluk} Kasaba Hobli",
        "district": district
    }

@app.get("/recommendations/{taluk}")
async def get_recommendations(
    taluk: str,
    ph: Optional[float] = Query(None, description="Soil pH value"),
    temp: Optional[float] = Query(None, description="Temperature in Celsius"),
    rainfall: Optional[float] = Query(None, description="Rainfall in mm"),
    humidity: Optional[float] = Query(None, description="Humidity in %")
):
    data = load_data()
    market_prices = data.get("market_prices", [])
    
    price_map = {item["crop"]: item for item in market_prices}
    
    # Map taluk to district to retrieve localized baseline parameters
    district = get_district_for_taluk(taluk)
    baseline = DISTRICT_BASELINES.get(district, {"soil_type": "Laterite", "ph": 6.2, "avg_temp": 28.0, "avg_humidity": 85, "avg_rainfall": 3500})
    
    final_ph = ph if ph is not None else baseline["ph"]
    final_temp = temp if temp is not None else baseline["avg_temp"]
    final_rainfall = rainfall if rainfall is not None else baseline["avg_rainfall"]
    final_humidity = humidity if humidity is not None else baseline["avg_humidity"]
    soil_type = baseline["soil_type"]
    
    # Find matching crops
    crop_names = get_recommendations_from_csv(final_ph, final_temp, final_rainfall, humidity=final_humidity)
    
    enriched_recommendations = []
    for crop in crop_names:
        price_info = price_map.get(crop, {"crop": crop, "price": "Price on Request", "trend": "stable"})
        species_info = get_crop_species_info(
            crop,
            ph=final_ph,
            temp=final_temp,
            rainfall=final_rainfall,
            humidity=final_humidity,
            soil_type=soil_type,
            taluk=taluk,
            district=district
        )
        item = dict(price_info)
        if species_info:
            item["unit"] = species_info.get("unit")
            item["botanical_genus"] = species_info.get("botanical_genus")
            item["crop_image"] = species_info.get("crop_image")
            item["varieties_count"] = species_info.get("varieties_count")
            item["price_range"] = species_info.get("price_range", {}).get("display")
            item["varieties"] = species_info.get("varieties", [])
            item["top_varieties"] = species_info.get("varieties", [])[:3]
            item["best_variety"] = species_info.get("varieties", [])[0] if species_info.get("varieties") else None
        else:
            item["varieties"] = []
            item["varieties_count"] = 0
            item["price_range"] = item.get("price")
            item["top_varieties"] = []
            item["best_variety"] = None
        enriched_recommendations.append(item)
            
    return {
        "soil_data": {
            "ph": final_ph,
            "temp": final_temp,
            "rainfall": final_rainfall,
            "soil_type": soil_type,
            "taluk": taluk,
            "district": district
        },
        "recommended_crops": enriched_recommendations
    }

@app.get("/crop-varieties/{crop}")
async def get_crop_varieties(
    crop: str,
    taluk: Optional[str] = Query(None, description="Taluk name for location suitability"),
    district: Optional[str] = Query(None, description="District name"),
    ph: Optional[float] = Query(None, description="Soil pH value"),
    temp: Optional[float] = Query(None, description="Temperature in Celsius"),
    rainfall: Optional[float] = Query(None, description="Rainfall in mm"),
    humidity: Optional[float] = Query(None, description="Humidity in %"),
    soil_type: Optional[str] = Query(None, description="Soil Type"),
    season: Optional[str] = Query(None, description="Current or target season (Kharif, Rabi, Summer)")
):
    """
    Returns authentic agricultural varieties for a crop, dynamically evaluated and ranked
    based on the farmer's location, soil requirements, climate, growing season, maturity period, and expected yield.
    """
    resolved_district = district
    if taluk and not resolved_district:
        resolved_district = get_district_for_taluk(taluk)

    info = get_crop_species_info(
        crop,
        ph=ph,
        temp=temp,
        rainfall=rainfall,
        humidity=humidity,
        soil_type=soil_type,
        season=season,
        taluk=taluk,
        district=resolved_district
    )
    if not info:
        raise HTTPException(status_code=404, detail=f"Crop '{crop}' not found in catalog. Available: {list(CROP_SPECIES.keys())}")
    return info

@app.get("/crop-species")
async def get_all_crop_species(crop: Optional[str] = Query(None, description="Optional crop name to filter")):
    """Get all crop species and varieties with individual prices, duration, yield, and agronomic characteristics."""
    if crop:
        info = get_crop_species_info(crop)
        if not info:
            raise HTTPException(status_code=404, detail=f"Crop species not found for '{crop}'. Available: {list(CROP_SPECIES.keys())}")
        return info

    result = {}
    for crop_name in CROP_SPECIES:
        result[crop_name] = get_crop_species_info(crop_name)
    return {
        "total_crops": len(CROP_SPECIES),
        "crops": result
    }

@app.get("/crop-species/{crop}")
async def get_crop_species_by_name(crop: str):
    """Get varieties, botanical species, and individual pricing for a particular crop."""
    info = get_crop_species_info(crop)
    if not info:
        raise HTTPException(status_code=404, detail=f"Crop '{crop}' not found in species catalog. Available: {list(CROP_SPECIES.keys())}")
    return info

@app.get("/market-prices")
async def get_market_prices():
    data = load_data()
    return data.get("market_prices", [])

@app.get("/taluk-market-prices")
async def get_taluk_market_prices():
    """Get latest market prices for all crops across all taluks from the history CSV."""
    if not os.path.exists(MARKET_HISTORY_FILE):
        return {"taluks": [], "crops": [], "prices": {}}
    
    try:
        # Read the CSV and get the latest prices (2025, most recent month)
        all_data = {}
        taluks_set = set()
        crops_set = set()
        
        with open(MARKET_HISTORY_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                taluk = row['Taluk']
                crop = row['Crop']
                year = int(row['Year'])
                price = float(row['Price'])
                unit = row['Unit']
                trend = row['Trend']
                
                taluks_set.add(taluk)
                crops_set.add(crop)
                
                key = f"{taluk}_{crop}"
                # Keep only the latest entry (highest year, latest month)
                if key not in all_data or year > all_data[key]['year']:
                    all_data[key] = {
                        "taluk": taluk,
                        "crop": crop,
                        "price": round(price, 2),
                        "unit": unit,
                        "trend": trend,
                        "year": year
                    }
                elif year == all_data[key]['year']:
                    # Same year, update with newer month data
                    all_data[key] = {
                        "taluk": taluk,
                        "crop": crop,
                        "price": round(price, 2),
                        "unit": unit,
                        "trend": trend,
                        "year": year
                    }
        
        # Organize as taluk -> crop -> price
        prices_by_taluk = {}
        for key, data in all_data.items():
            taluk = data["taluk"]
            if taluk not in prices_by_taluk:
                prices_by_taluk[taluk] = {}
            prices_by_taluk[taluk][data["crop"]] = {
                "price": data["price"],
                "unit": data["unit"],
                "trend": data["trend"]
            }
        
        return {
            "taluks": sorted(list(taluks_set)),
            "crops": sorted(list(crops_set)),
            "prices": prices_by_taluk
        }
    except Exception as e:
        print(f"Error reading taluk market prices: {e}")
        return {"taluks": [], "crops": [], "prices": {}}


def fetch_datagov_prices(district_filter: str = None):
    """Fetch live market prices from data.gov.in API."""
    try:
        params = {
            "api-key": DATAGOV_API_KEY,
            "format": "json",
            "limit": "100",
            "filters[state]": "Karnataka",
        }
        if district_filter:
            params["filters[district]"] = district_filter

        response = requests.get(DATAGOV_BASE_URL, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            records = data.get("records", [])
            total = data.get("total", 0)

            # Group by market
            markets = {}
            commodities = set()
            for rec in records:
                market = rec.get("market", "Unknown")
                if market not in markets:
                    markets[market] = []
                commodities.add(rec.get("commodity", ""))
                markets[market].append({
                    "commodity": rec.get("commodity", ""),
                    "variety": rec.get("variety", ""),
                    "grade": rec.get("grade", ""),
                    "min_price": rec.get("min_price", 0),
                    "max_price": rec.get("max_price", 0),
                    "modal_price": rec.get("modal_price", 0),
                    "arrival_date": rec.get("arrival_date", ""),
                })

            return {
                "source": "data.gov.in",
                "total": total,
                "district": district_filter or "All Karnataka",
                "markets": markets,
                "commodities": sorted(list(commodities)),
                "records": [{
                    "market": rec.get("market", ""),
                    "commodity": rec.get("commodity", ""),
                    "variety": rec.get("variety", ""),
                    "grade": rec.get("grade", ""),
                    "min_price": rec.get("min_price", 0),
                    "max_price": rec.get("max_price", 0),
                    "modal_price": rec.get("modal_price", 0),
                    "arrival_date": rec.get("arrival_date", ""),
                } for rec in records],
            }
        else:
            print(f"data.gov.in API returned {response.status_code}")
            return None
    except Exception as e:
        print(f"data.gov.in API error: {e}")
        return None


def generate_fallback_apmc_prices(district: str) -> dict:
    from datetime import date
    import hashlib
    
    today_str = date.today().strftime("%d/%m/%Y")
    
    crops_map = {
        "Coastal": ["Rice", "Banana", "Arecanut", "Pepper", "Cashew", "Coconut"],
        "Malnad": ["Coffee", "Cardamom", "Ginger", "Pepper", "Banana", "Arecanut"],
        "Northern Dry": ["Jowar", "Cotton", "Maize", "Bengal Gram", "Red Gram", "Wheat", "Pomegranate"],
        "Southern Dry": ["Ragi", "Maize", "Groundnut", "Sugarcane", "Tomato", "Mango", "Coconut"]
    }
    
    coastal_districts = ["Dakshina Kannada", "Udupi", "Uttara Kannada"]
    malnad_districts = ["Chikkamagaluru", "Kodagu", "Hassan", "Shivamogga"]
    northern_districts = [
        "Bagalkot", "Ballari", "Belagavi", "Bidar", "Chitradurga", "Davanagere", 
        "Dharwad", "Gadag", "Haveri", "Kalaburagi", "Koppal", "Raichur", 
        "Vijayanagara", "Vijayapura", "Yadgir"
    ]
    
    zone = "Southern Dry"
    if district in coastal_districts:
        zone = "Coastal"
    elif district in malnad_districts:
        zone = "Malnad"
    elif district in northern_districts:
        zone = "Northern Dry"
        
    crops = crops_map[zone]
    
    base_modal_prices = {
        "Rice": 2300, "Banana": 40, "Arecanut": 46000, "Pepper": 600, 
        "Cashew": 120, "Rubber": 180, "Coconut": 35, "Coffee": 250, 
        "Cardamom": 1500, "Ginger": 120, "Jowar": 2900, "Cotton": 6200, 
        "Maize": 2100, "Bengal Gram": 5300, "Red Gram": 7600, "Wheat": 2300, 
        "Pomegranate": 140, "Ragi": 3400, "Groundnut": 6600, "Sugarcane": 310, 
        "Tomato": 32, "Mango": 85
    }
    
    taluks = TALUK_MAP.get(district, [district])
    records = []
    markets = {}
    
    for taluk in taluks[:3]:
        mkt_name = f"{taluk} APMC"
        markets[mkt_name] = []
        for crop in crops:
            modal = base_modal_prices.get(crop, 1500)
            h = int(hashlib.md5(f"{taluk}_{crop}".encode()).hexdigest(), 16)
            var_pct = ((h % 10) - 5) / 100.0 # -5% to +4%
            modal = int(modal * (1.0 + var_pct))
            min_p = int(modal * 0.92)
            max_p = int(modal * 1.06)
            
            rec = {
                "market": mkt_name,
                "commodity": crop,
                "variety": "Local / Common",
                "grade": "FAQ",
                "min_price": min_p,
                "max_price": max_p,
                "modal_price": modal,
                "arrival_date": today_str
            }
            records.append(rec)
            markets[mkt_name].append(rec)
            
    return {
        "source": "Simulated APMC (Fallback)",
        "total": len(records),
        "district": district,
        "markets": markets,
        "commodities": sorted(list(set(crops))),
        "records": records
    }


@app.get("/district-market-prices/{district}")
async def get_district_market_prices(district: str):
    """Get live APMC market prices for a specific district from data.gov.in with local fallbacks."""
    api_district = DISTRICT_API_MAP.get(district, district)
    result = fetch_datagov_prices(api_district)
    
    if result and result.get("records"):
        result["requested_district"] = district
        result["api_district"] = api_district
        return result
        
    fallback_res = generate_fallback_apmc_prices(district)
    fallback_res["requested_district"] = district
    fallback_res["api_district"] = api_district
    return fallback_res


@app.get("/market-prices-live")
async def get_all_live_market_prices():
    """Get all live APMC market prices across Karnataka with fallback support."""
    result = fetch_datagov_prices()
    if result and result.get("records"):
        return result
        
    return generate_fallback_apmc_prices("Dakshina Kannada")


def generate_mock_market_history(crop: str, taluk: str = None) -> list:
    history = []
    base_prices = {
        "Coffee": (240.0, "kg"),
        "Cardamom": (1350.0, "kg"),
        "Ginger": (110.0, "kg"),
        "Jowar": (2700.0, "quintal"),
        "Cotton": (5900.0, "quintal"),
        "Maize": (1850.0, "quintal"),
        "Bengal Gram": (4700.0, "quintal"),
        "Red Gram": (7100.0, "quintal"),
        "Wheat": (2250.0, "quintal"),
        "Pomegranate": (130.0, "kg"),
        "Ragi": (2900.0, "quintal"),
        "Groundnut": (6200.0, "quintal"),
        "Sugarcane": (300.0, "quintal"),
        "Tomato": (28.0, "kg"),
        "Mango": (72.0, "kg"),
    }
    
    base_price, unit = base_prices.get(crop, (1500.0, "quintal"))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    import hashlib
    h = int(hashlib.md5(crop.encode("utf-8")).hexdigest(), 16)
    
    t_name = taluk or "Karnataka APMC"
    for year in range(2020, 2025):
        year_multiplier = 1.0 + (year - 2020) * 0.05 + ((h % 5) - 2) * 0.01
        for m_idx, month in enumerate(months):
            month_factor = 1.0 + math.sin(m_idx * (math.pi / 6)) * 0.08 + ((h + m_idx) % 7 - 3) * 0.01
            price = round(base_price * year_multiplier * month_factor, 2)
            
            trend = "stable"
            if m_idx > 0:
                prev_factor = 1.0 + math.sin((m_idx - 1) * (math.pi / 6)) * 0.08 + ((h + m_idx - 1) % 7 - 3) * 0.01
                if month_factor > prev_factor + 0.01:
                    trend = "up"
                elif month_factor < prev_factor - 0.01:
                    trend = "down"
            
            history.append({
                "taluk": t_name,
                "crop": crop,
                "year": year,
                "month": month,
                "price": price,
                "unit": unit,
                "trend": trend,
                "Market_Name": f"{t_name} Market"
            })
            
    return history


@app.get("/market-history/{crop}")
async def get_crop_market_history(crop: str, taluk: Optional[str] = Query(None)):
    """Get 5-year price history for a crop, optionally filtered by taluk."""
    history = get_market_history(crop, taluk)
    if not history:
        history = generate_mock_market_history(crop, taluk)
    if not history:
        return {"crop": crop, "history": [], "summary": {}}
    
    # Calculate yearly averages
    yearly_avg = {}
    for entry in history:
        year = entry["year"]
        if year not in yearly_avg:
            yearly_avg[year] = {"total": 0, "count": 0}
        yearly_avg[year]["total"] += entry["price"]
        yearly_avg[year]["count"] += 1
    
    summary = {}
    for year, vals in yearly_avg.items():
        summary[year] = round(vals["total"] / vals["count"], 2)
    
    return {
        "crop": crop,
        "unit": history[0]["unit"] if history else "",
        "history": history[-60:],  # last 60 entries
        "yearly_averages": summary
    }

@app.get("/profit-estimate")
async def estimate_profit(
    crop: str = Query(..., description="Crop name"),
    acres: float = Query(0, description="Land area in acres"),
    guntas: float = Query(0, description="Land area in guntas"),
    survey_number: Optional[str] = Query(None, description="Survey number"),
    variety: Optional[str] = Query(None, description="Specific crop variety/species name")
):
    """Estimate profit for a crop based on land area, using historical data."""
    # Convert guntas to acres if needed (40 guntas = 1 acre)
    total_acres = acres + (guntas / 40.0)
    
    if total_acres <= 0:
        raise HTTPException(status_code=400, detail="Please provide valid land area")
    
    # Get average yield per acre from farmer dataset
    avg_yield = get_avg_yield_for_crop(crop)
    
    # Fallback yields per acre
    fallback_yields = {
        'Rice': 18, 'Arecanut': 8, 'Coconut': 6000,
        'Pepper': 150, 'Cashew': 200, 'Rubber': 500, 'Banana': 2500
    }
    yield_units = {
        'Rice': 'quintal', 'Arecanut': 'quintal', 'Coconut': 'piece',
        'Pepper': 'kg', 'Cashew': 'kg', 'Rubber': 'kg', 'Banana': 'kg'
    }
    
    yield_per_acre = avg_yield if avg_yield else fallback_yields.get(crop, 100)
    unit = yield_units.get(crop, 'kg')
    
    # Check if a specific variety was selected from CROP_SPECIES
    selected_variety = None
    species_info = get_crop_species_info(crop)
    if species_info:
        unit = species_info.get("unit", unit)
        if variety:
            for v in species_info.get("varieties", []):
                if v["name"].lower() == variety.lower() or variety.lower() in v["name"].lower():
                    selected_variety = v
                    break

    # Get current market price
    data = load_data()
    market_prices = data.get("market_prices", [])
    current_price_info = next((p for p in market_prices if p["crop"] == crop), None)
    
    # Extract numeric price
    current_price = 0
    if selected_variety:
        current_price = float(selected_variety.get("price", 0))
        yield_per_acre = selected_variety.get("yield_per_acre", yield_per_acre)
        price_display = selected_variety.get("price_display", f"₹{current_price:,.0f}/{unit}")
    elif current_price_info:
        price_str = current_price_info["price"]
        price_display = price_str
        import re
        match = re.search(r'[\d,]+', price_str)
        if match:
            current_price = float(match.group().replace(',', ''))
    else:
        price_display = f"₹{current_price:,.0f}/{unit}" if current_price else "N/A"
    
    # Calculate estimates
    estimated_yield = round(yield_per_acre * total_acres, 1)
    estimated_revenue = round(estimated_yield * current_price)
    estimated_input_cost = round(estimated_revenue * 0.40)  # ~40% input cost
    estimated_profit = estimated_revenue - estimated_input_cost
    profit_per_acre = round(estimated_profit / total_acres) if total_acres > 0 else 0
    
    # Get 5-year price trend
    history = get_market_history(crop, "Mangaluru")
    yearly_prices = {}
    for entry in history:
        year = entry["year"]
        if year not in yearly_prices:
            yearly_prices[year] = {"total": 0, "count": 0}
        yearly_prices[year]["total"] += entry["price"]
        yearly_prices[year]["count"] += 1
    
    price_trend = []
    for year in sorted(yearly_prices.keys()):
        avg = round(yearly_prices[year]["total"] / yearly_prices[year]["count"], 2)
        price_trend.append({"year": year, "avg_price": avg})
    
    return {
        "crop": crop,
        "variety": selected_variety["name"] if selected_variety else None,
        "variety_details": selected_variety,
        "available_varieties": [v["name"] for v in species_info["varieties"]] if species_info else [],
        "land_acres": round(total_acres, 2),
        "land_guntas": round(total_acres * 40),
        "survey_number": survey_number,
        "yield_per_acre": yield_per_acre,
        "yield_unit": unit,
        "estimated_total_yield": estimated_yield,
        "current_price_per_unit": current_price,
        "price_display": price_display,
        "estimated_revenue": estimated_revenue,
        "estimated_input_cost": estimated_input_cost,
        "estimated_profit": estimated_profit,
        "profit_per_acre": profit_per_acre,
        "trend": current_price_info["trend"] if current_price_info else "stable",
        "price_history_5yr": price_trend
    }

def generate_mock_neighbours(taluk: str, hobli: str = None, exclude_name: str = None) -> dict:
    import hashlib
    
    district = get_district_for_taluk(taluk)
    baseline = DISTRICT_BASELINES.get(district, {
        "ph": 6.5, "soil_type": "Red Sandy", 
        "avg_temp": 26.5, "avg_humidity": 65, "avg_rainfall": 800
    })
    
    # Retrieve crops typical to this district/zone
    coastal_districts = ["Dakshina Kannada", "Udupi", "Uttara Kannada"]
    malnad_districts = ["Chikkamagaluru", "Kodagu", "Hassan", "Shivamogga"]
    northern_districts = [
        "Bagalkot", "Ballari", "Belagavi", "Bidar", "Chitradurga", "Davanagere", 
        "Dharwad", "Gadag", "Haveri", "Kalaburagi", "Koppal", "Raichur", 
        "Vijayanagara", "Vijayapura", "Yadgir"
    ]
    
    if district in coastal_districts:
        crops = ["Rice", "Banana", "Arecanut", "Pepper", "Cashew", "Coconut"]
    elif district in malnad_districts:
        crops = ["Coffee", "Cardamom", "Ginger", "Pepper", "Banana"]
    elif district in northern_districts:
        crops = ["Jowar", "Cotton", "Maize", "Bengal Gram", "Red Gram", "Wheat"]
    else: # Southern Dry
        crops = ["Ragi", "Maize", "Groundnut", "Sugarcane", "Tomato", "Mango"]
        
    h_tal = int(hashlib.md5(taluk.encode()).hexdigest(), 16)
    
    neighbours = []
    crop_counts = {}
    total_land = 0.0
    crop_profits = {}
    crop_yields = {}
    
    target_hobli = hobli or f"{taluk} Kasaba Hobli"
    seen_names = set()
    if exclude_name:
        seen_names.add(exclude_name.lower().strip())
        
    yield_base = {
        "Coffee": 12.0, "Cardamom": 1.5, "Ginger": 80.0, "Jowar": 8.0, 
        "Cotton": 7.0, "Maize": 20.0, "Bengal Gram": 6.0, "Red Gram": 5.0, 
        "Wheat": 12.0, "Pomegranate": 60.0, "Ragi": 10.0, "Groundnut": 8.0, 
        "Sugarcane": 350.0, "Tomato": 120.0, "Mango": 40.0, "Rice": 15.0, 
        "Banana": 180.0, "Arecanut": 10.0, "Pepper": 4.0, "Cashew": 6.0, 
        "Rubber": 8.0, "Coconut": 40.0
    }
    
    profit_base = {
        "Coffee": 45000, "Cardamom": 90000, "Ginger": 60000, "Jowar": 18000,
        "Cotton": 28000, "Maize": 22000, "Bengal Gram": 25000, "Red Gram": 30000,
        "Wheat": 24000, "Pomegranate": 85000, "Ragi": 20000, "Groundnut": 24000,
        "Sugarcane": 55000, "Tomato": 40000, "Mango": 50000, "Rice": 22000,
        "Banana": 75000, "Arecanut": 120000, "Pepper": 80000, "Cashew": 35000,
        "Rubber": 50000, "Coconut": 40000
    }

    # 1. First, check live registered farmers in DB for this taluk/district
    try:
        conn = sqlite3.connect("farmer_portal.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, taluk, hobli, current_crop, land_area_acres, land_area_guntas, phone_number, survey_number
            FROM farmers
            WHERE (LOWER(taluk) = ? OR LOWER(district) = ?)
            ORDER BY id DESC LIMIT 5
        """, (taluk.lower(), district.lower() if district else ""))
        reg_rows = cursor.fetchall()
        conn.close()
        
        for r_name, r_taluk, r_hobli, r_crop, r_acres, r_guntas, r_phone, r_survey in reg_rows:
            if not r_name or r_name.lower().strip() in seen_names:
                continue
            seen_names.add(r_name.lower().strip())
            
            p_crop = r_crop if r_crop else crops[len(neighbours) % len(crops)]
            acres_num = float(r_acres or 2.0)
            guntas_num = float(r_guntas or 0.0)
            tot_ac = acres_num + (guntas_num / 40.0)
            total_land += tot_ac
            
            unit = "kg" if p_crop in ["Coffee", "Cardamom", "Ginger", "Pepper", "Cashew", "Rubber", "Tomato", "Mango", "Pomegranate"] else ("piece" if p_crop == "Coconut" else "quintal")
            y_b = yield_base.get(p_crop, 12.0)
            y_val = round(y_b * (0.90 + (len(neighbours) % 15) / 100.0), 1)
            p_b = profit_base.get(p_crop, 25000)
            prof_acre = int(p_b * (0.95 + (len(neighbours) % 15) / 100.0))
            
            crop_sp = CROP_SPECIES.get(p_crop, {})
            v_list = crop_sp.get("varieties", [])
            var_obj = v_list[len(neighbours) % len(v_list)] if v_list else {}
            
            neighbours.append({
                "farmer_id": f"LIVE-{100 + len(neighbours)}",
                "name": r_name,
                "hobli": r_hobli or target_hobli,
                "primary_crop": p_crop,
                "secondary_crop": "Banana" if p_crop in ["Arecanut", "Rubber"] else "Pulses",
                "variety": var_obj.get("name", f"{p_crop} Local Improved"),
                "variety_scientific": var_obj.get("scientific_species", ""),
                "growing_season": var_obj.get("season", "Kharif"),
                "duration_days": var_obj.get("duration_days", 120),
                "market_price": var_obj.get("price", p_b),
                "market_price_display": var_obj.get("price_display", f"₹{p_b:,}/{unit}"),
                "expected_yield": var_obj.get("expected_yield", f"{y_val} {unit}/acre"),
                "land_acres": acres_num,
                "land_guntas": guntas_num,
                "soil_type": var_obj.get("soil_type", baseline["soil_type"]),
                "soil_ph": round(baseline.get("ph", 6.5), 1),
                "latest_year": 2025,
                "latest_yield": round(y_val * tot_ac, 1),
                "yield_unit": unit,
                "yield_per_acre": y_val,
                "latest_profit": int(prof_acre * tot_ac),
                "profit_per_acre": prof_acre,
                "is_real_data": True,
                "is_registered_live": True,
                "data_source": "live_db",
                "data_source_label": "🟢 Live Registered Community Member"
            })
            crop_counts[p_crop] = crop_counts.get(p_crop, 0) + 1
            crop_profits[p_crop] = crop_profits.get(p_crop, 0) + prof_acre
            crop_yields[p_crop] = crop_yields.get(p_crop, 0) + y_val
    except Exception as e:
        print(f"Error loading live neighbours from DB: {e}")

    # 2. Fill remaining community neighbours up to 8-10 with unique names from KARNATAKA_FARMER_NAMES
    target_count = max(8, 6 + (h_tal % 4))
    name_pointer = (h_tal * 3) % len(KARNATAKA_FARMER_NAMES)
    
    while len(neighbours) < target_count:
        fname, lname, fname_kn, lname_kn = KARNATAKA_FARMER_NAMES[name_pointer % len(KARNATAKA_FARMER_NAMES)]
        full_n = f"{fname} {lname}"
        name_pointer += 1
        
        if full_n.lower() in seen_names:
            continue
        seen_names.add(full_n.lower())
        
        h_ind = int(hashlib.md5(f"{taluk}_{len(neighbours)}_{full_n}".encode()).hexdigest(), 16)
        primary = crops[len(neighbours) % len(crops)]
        secondary = crops[(len(neighbours) + 1) % len(crops)]
        
        acres = 2 + (h_ind % 7)
        guntas = (h_ind >> 2) % 40
        tot_acres = acres + guntas / 40.0
        total_land += tot_acres
        
        unit = "kg" if primary in ["Coffee", "Cardamom", "Ginger", "Pepper", "Cashew", "Rubber", "Tomato", "Mango", "Pomegranate"] else ("piece" if primary == "Coconut" else "quintal")
        y_base_val = yield_base.get(primary, 10.0)
        y_val = round(y_base_val * (0.85 + ((h_ind % 30) / 100.0)), 1)
        p_base_val = profit_base.get(primary, 25000)
        profit_per_acre = int(p_base_val * (0.90 + ((h_ind % 20) / 100.0)))
        tot_profit = int(tot_acres * profit_per_acre)
        
        crop_species_obj = CROP_SPECIES.get(primary, {})
        v_list = crop_species_obj.get("varieties", [])
        if v_list:
            selected_var = v_list[h_ind % len(v_list)]
            var_name = selected_var.get("name", f"{primary} Local")
            var_season = selected_var.get("season", "Kharif")
            var_duration = selected_var.get("duration_days", 120)
            var_price = selected_var.get("price", p_base_val)
            var_price_display = selected_var.get("price_display", f"₹{var_price:,}/{unit}")
            var_yield_exp = selected_var.get("expected_yield", f"{y_val} {unit}/acre")
            var_soil = selected_var.get("soil_type", baseline["soil_type"])
            var_sci = selected_var.get("scientific_species", "")
        else:
            var_name = f"{primary} Standard"
            var_season = "Kharif"
            var_duration = 120
            var_price = p_base_val
            var_price_display = f"₹{p_base_val:,}/{unit}"
            var_yield_exp = f"{y_val} {unit}/acre"
            var_soil = baseline["soil_type"]
            var_sci = ""
            
        soil_ph = round(baseline.get("ph", 6.5) + ((h_ind % 7) - 3) * 0.1, 1)
        
        neighbours.append({
            "farmer_id": f"F-{1000 + (h_ind % 9000)}",
            "name": full_n,
            "hobli": target_hobli,
            "primary_crop": primary,
            "secondary_crop": secondary,
            "variety": var_name,
            "variety_scientific": var_sci,
            "growing_season": var_season,
            "duration_days": var_duration,
            "market_price": var_price,
            "market_price_display": var_price_display,
            "expected_yield": var_yield_exp,
            "land_acres": acres,
            "land_guntas": guntas,
            "soil_type": var_soil or baseline["soil_type"],
            "soil_ph": soil_ph,
            "latest_year": 2025,
            "latest_yield": round(y_val * tot_acres, 1),
            "yield_unit": unit,
            "yield_per_acre": y_val,
            "latest_profit": tot_profit,
            "profit_per_acre": profit_per_acre,
            "is_real_data": False,
            "data_source": "demo",
            "data_source_label": "Local Baseline Model"
        })
        crop_counts[primary] = crop_counts.get(primary, 0) + 1
        crop_profits[primary] = crop_profits.get(primary, 0) + profit_per_acre
        crop_yields[primary] = crop_yields.get(primary, 0) + y_val

        
    crop_summary = []
    for crop, count in crop_counts.items():
        pct = round((count / len(neighbours)) * 100, 1)
        avg_prof = int(crop_profits[crop] / count)
        avg_yld = round(crop_yields[crop] / count, 1)
        unit = "kg" if crop in ["Coffee", "Cardamom", "Ginger", "Pepper", "Cashew", "Rubber", "Tomato", "Mango", "Pomegranate"] else ("piece" if crop == "Coconut" else "quintal")
        
        crop_land = sum([n["land_acres"] + n["land_guntas"]/40.0 for n in neighbours if n["primary_crop"] == crop])
        
        crop_summary.append({
            "crop": crop,
            "farmer_count": count,
            "percentage": pct,
            "total_land_acres": round(crop_land, 1),
            "avg_yield_per_acre": avg_yld,
            "avg_profit_per_acre": avg_prof,
            "yield_unit": unit
        })
        
    crop_summary = sorted(crop_summary, key=lambda x: x["percentage"], reverse=True)
    top_crop = crop_summary[0] if crop_summary else {"crop": "Ragi", "percentage": 100, "avg_profit_per_acre": 20000}
    
    insight = (
        f"🌾 Most of your neighbours ({top_crop['percentage']}%) in {taluk} grow {top_crop['crop']} "
        f"as their primary crop, earning an average profit of ₹{top_crop['avg_profit_per_acre']:,} per acre."
    )
    
    return {
        "neighbours": neighbours,
        "crop_summary": crop_summary,
        "total_farmers": len(neighbours),
        "scope": target_hobli if hobli else taluk,
        "scope_type": "hobli" if hobli else "taluk",
        "available_hoblis": [target_hobli, f"{taluk} Rural Hobli"],
        "insight": insight,
        "is_real_data": False,
        "data_badge": "Demo Data (Simulated)",
        "data_source_label": "Demonstration simulation calibrated to local agro-climatic conditions and soil profiles"
    }


def _enrich_neighbour_response(response: dict) -> dict:
    """Attach crop species/variety data to each crop in crop_summary, varieties breakdown, and top variety to each neighbour."""
    is_real = any(nb.get("is_real_data") for nb in response.get("neighbours", []))
    response["is_real_data"] = is_real
    response["data_badge"] = "Verified Farmer Records" if is_real else "Demo Data (Simulated)"
    response["data_source_label"] = (
        "Verified local farmer records from Taluk agriculture registry" 
        if is_real else 
        "Demonstration simulation calibrated to local agro-climatic conditions and soil profiles"
    )

    # Enrich crop_summary with full species info and varieties breakdown
    for cs in response.get("crop_summary", []):
        species = get_crop_species_info(cs["crop"])
        if species:
            cs["botanical_genus"] = species.get("botanical_genus", "")
            cs["varieties_count"] = species.get("varieties_count", 0)
            cs["price_range"] = species.get("price_range", {})
            cs["top_varieties"] = species.get("varieties", [])[:4]  # Top 4 varieties
            cs["all_varieties"] = species.get("varieties", [])
            var_names = [v.get("name") for v in species.get("varieties", []) if v.get("name")]
            cs["available_varieties"] = var_names
            if species.get("varieties"):
                first_v = species["varieties"][0]
                cs["primary_season"] = first_v.get("season", "Kharif")
                cs["soil_requirements"] = first_v.get("soil_type", "Loamy")
                cs["soil_ph_range"] = first_v.get("soil_ph_range", [6.0, 7.5])
        else:
            cs["botanical_genus"] = ""
            cs["varieties_count"] = 0
            cs["price_range"] = {}
            cs["top_varieties"] = []
            cs["all_varieties"] = []
            cs["available_varieties"] = []
            cs["primary_season"] = "Kharif"
            cs["soil_requirements"] = "Loamy"
            cs["soil_ph_range"] = [6.0, 7.5]

        # Calculate varieties breakdown among actual neighbours
        var_breakdown = {}
        for nb in response.get("neighbours", []):
            if nb.get("primary_crop") == cs["crop"]:
                vname = nb.get("variety") or "Standard Variety"
                if vname not in var_breakdown:
                    var_breakdown[vname] = {
                        "variety": vname,
                        "farmers_count": 0,
                        "farmer_names": [],
                        "yields": [],
                        "profits": [],
                        "market_price_display": nb.get("market_price_display", ""),
                        "growing_season": nb.get("growing_season", ""),
                        "soil_type": nb.get("soil_type", ""),
                        "soil_ph": nb.get("soil_ph", 6.5)
                    }
                var_breakdown[vname]["farmers_count"] += 1
                var_breakdown[vname]["farmer_names"].append(nb.get("name"))
                var_breakdown[vname]["yields"].append(nb.get("yield_per_acre", 0))
                var_breakdown[vname]["profits"].append(nb.get("profit_per_acre", 0))

        v_list = []
        for vname, vdata in var_breakdown.items():
            avg_y = round(sum(vdata["yields"]) / len(vdata["yields"]), 1) if vdata["yields"] else 0
            avg_p = int(sum(vdata["profits"]) / len(vdata["profits"])) if vdata["profits"] else 0
            v_list.append({
                "variety": vname,
                "farmers_count": vdata["farmers_count"],
                "farmer_names": vdata["farmer_names"][:3],
                "avg_yield": avg_y,
                "avg_profit": avg_p,
                "market_price_display": vdata["market_price_display"],
                "growing_season": vdata["growing_season"],
                "soil_type": vdata["soil_type"],
                "soil_ph": vdata["soil_ph"]
            })
        cs["varieties_breakdown"] = v_list

    # Enrich each neighbour with their crop's best-yielding variety if not set
    for nb in response.get("neighbours", []):
        species = get_crop_species_info(nb.get("primary_crop", ""))
        if species and species.get("varieties"):
            best = max(species["varieties"], key=lambda v: v.get("yield_per_acre", 0))
            if not nb.get("variety"):
                nb["variety"] = best.get("name", "")
                nb["growing_season"] = best.get("season", "Kharif")
                nb["expected_yield"] = best.get("expected_yield", "")
                nb["market_price_display"] = best.get("price_display", "")
            nb["crop_top_variety"] = best.get("name", "")
            nb["crop_top_variety_price"] = best.get("price_display", "")
            nb["crop_botanical_genus"] = species.get("botanical_genus", "")
            nb["crop_varieties_count"] = species.get("varieties_count", 0)
        else:
            nb["crop_top_variety"] = ""
            nb["crop_top_variety_price"] = ""
            nb["crop_botanical_genus"] = ""
            nb["crop_varieties_count"] = 0

    return response


@app.get("/neighbour-planting/{taluk}")
async def get_neighbour_planting(
    taluk: str,
    hobli: Optional[str] = Query(None, description="Filter by hobli for closer neighbours"),
    exclude_name: Optional[str] = Query(None, description="Exclude the logged-in farmer's name")
):
    """Get planting details of neighbouring farmers in the same taluk/hobli for comparison."""
    if not os.path.exists(FARMER_DETAILS_FILE):
        return _enrich_neighbour_response(generate_mock_neighbours(taluk, hobli, exclude_name))

    try:
        # Read all farmer records for this taluk (deduplicate by Farmer_Name)
        farmer_records = {}  # farmer_name -> list of year records
        all_rows = []

        with open(FARMER_DETAILS_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Taluk'].lower() != taluk.lower():
                    continue
                if hobli and row['Hobli'].lower() != hobli.lower():
                    continue
                if exclude_name and row['Farmer_Name'].lower().strip() == exclude_name.lower().strip():
                    continue
                all_rows.append(row)
                fname_key = row['Farmer_Name'].strip()
                if fname_key not in farmer_records:
                    farmer_records[fname_key] = []
                farmer_records[fname_key].append(row)

        if not farmer_records:
            return _enrich_neighbour_response(generate_mock_neighbours(taluk, hobli, exclude_name))

        # Build individual neighbour details (latest year per farmer)
        import hashlib
        neighbours = []
        for fname_key, records in farmer_records.items():
            latest = max(records, key=lambda r: int(r['Year']))
            fid = latest.get('Farmer_ID', 'F-000')
            acres = float(latest['Total_Land_Acres'])
            yield_qty = float(latest['Yield_Quantity'])
            yield_per_acre = round(yield_qty / acres, 1) if acres > 0 else 0
            primary = latest['Primary_Crop']
            unit = latest['Yield_Unit']
            
            # Select authentic variety for primary crop
            crop_species_obj = CROP_SPECIES.get(primary, {})
            v_list = crop_species_obj.get("varieties", [])
            h_fid = int(hashlib.md5(fid.encode()).hexdigest(), 16)
            if v_list:
                selected_var = v_list[h_fid % len(v_list)]
                var_name = selected_var.get("name", f"{primary} Local")
                var_season = selected_var.get("season", "Kharif")
                var_duration = selected_var.get("duration_days", 120)
                var_price = float(latest.get('Market_Price_Per_Unit')) if latest.get('Market_Price_Per_Unit') else selected_var.get("price", 0)
                var_price_display = f"₹{int(var_price):,}/{unit}"
                var_yield_exp = selected_var.get("expected_yield", f"{yield_per_acre} {unit}/acre")
                var_sci = selected_var.get("scientific_species", "")
            else:
                var_name = f"{primary} Local"
                var_season = "Kharif"
                var_duration = 120
                var_price = float(latest.get('Market_Price_Per_Unit', 0)) if latest.get('Market_Price_Per_Unit') else 0
                var_price_display = f"₹{int(var_price):,}/{unit}" if var_price else ""
                var_yield_exp = f"{yield_per_acre} {unit}/acre"
                var_sci = ""
                
            soil_ph = float(latest.get('pH', 6.0)) if latest.get('pH') else 6.0

            neighbours.append({
                "farmer_id": fid,
                "name": latest['Farmer_Name'],
                "hobli": latest['Hobli'],
                "primary_crop": primary,
                "secondary_crop": latest['Secondary_Crop'],
                "variety": var_name,
                "variety_scientific": var_sci,
                "growing_season": var_season,
                "duration_days": var_duration,
                "market_price": var_price,
                "market_price_display": var_price_display,
                "expected_yield": var_yield_exp,
                "land_acres": acres,
                "land_guntas": float(latest['Total_Land_Guntas']),
                "soil_type": latest.get('Soil_Type', 'Laterite'),
                "soil_ph": soil_ph,
                "latest_year": int(latest['Year']),
                "latest_yield": round(yield_qty, 1),
                "yield_unit": unit,
                "yield_per_acre": yield_per_acre,
                "latest_profit": float(latest['Profit_INR']),
                "profit_per_acre": float(latest['Profit_Per_Acre_INR']),
                "is_real_data": True,
                "data_source": "real",
                "data_source_label": "Verified Farmer (Mangaluru Taluk Records)"
            })

        # Aggregate crop summary
        crop_data = {}  # crop -> {farmers: set, total_acres, yields_per_acre, profits_per_acre}
        for fid, records in farmer_records.items():
            latest = max(records, key=lambda r: int(r['Year']))
            crop = latest['Primary_Crop']
            if crop not in crop_data:
                crop_data[crop] = {
                    "farmers": set(),
                    "total_acres": 0,
                    "yields_per_acre": [],
                    "profits_per_acre": [],
                }
            acres = float(latest['Total_Land_Acres'])
            yield_qty = float(latest['Yield_Quantity'])
            crop_data[crop]["farmers"].add(fid)
            crop_data[crop]["total_acres"] += acres
            if acres > 0:
                crop_data[crop]["yields_per_acre"].append(yield_qty / acres)
            crop_data[crop]["profits_per_acre"].append(float(latest['Profit_Per_Acre_INR']))

        total_farmers = len(farmer_records)
        crop_summary = []
        for crop, data in crop_data.items():
            count = len(data["farmers"])
            avg_yield = round(sum(data["yields_per_acre"]) / len(data["yields_per_acre"]), 1) if data["yields_per_acre"] else 0
            avg_profit = round(sum(data["profits_per_acre"]) / len(data["profits_per_acre"])) if data["profits_per_acre"] else 0
            crop_summary.append({
                "crop": crop,
                "farmer_count": count,
                "percentage": round((count / total_farmers) * 100, 1),
                "total_land_acres": round(data["total_acres"], 1),
                "avg_yield_per_acre": avg_yield,
                "avg_profit_per_acre": avg_profit,
                "yield_unit": neighbours[0]["yield_unit"] if neighbours else "unit",
            })

        # Sort by popularity
        crop_summary.sort(key=lambda x: x["farmer_count"], reverse=True)

        # Fix yield_unit per crop from actual data
        for cs in crop_summary:
            for n in neighbours:
                if n["primary_crop"] == cs["crop"]:
                    cs["yield_unit"] = n["yield_unit"]
                    break

        # Generate demand insight
        top_crop = crop_summary[0] if crop_summary else None
        least_crop = crop_summary[-1] if len(crop_summary) > 1 else None
        insight = ""
        if top_crop and least_crop:
            if top_crop["percentage"] >= 40:
                insight = (
                    f"🔍 {top_crop['percentage']}% of your neighbours grow {top_crop['crop']} — "
                    f"high local competition. Consider diversifying to {least_crop['crop']} "
                    f"(only {least_crop['percentage']}% farmers) for potentially better returns. "
                    f"Average profit for {least_crop['crop']}: ₹{least_crop['avg_profit_per_acre']:,}/acre."
                )
            else:
                insight = (
                    f"🌱 Crop diversity is good in your area! {top_crop['crop']} is the most popular "
                    f"({top_crop['percentage']}%) with avg profit of ₹{top_crop['avg_profit_per_acre']:,}/acre."
                )
        elif top_crop:
            insight = f"🌾 Most neighbours grow {top_crop['crop']} with avg profit of ₹{top_crop['avg_profit_per_acre']:,}/acre."

        # Get list of unique hoblis for the scope selector
        hoblis = sorted(list(set(n["hobli"] for n in neighbours)))

        res_payload = {
            "neighbours": neighbours,
            "crop_summary": crop_summary,
            "total_farmers": total_farmers,
            "scope": hobli or taluk,
            "scope_type": "hobli" if hobli else "taluk",
            "available_hoblis": hoblis,
            "insight": insight,
            "is_real_data": True,
            "data_badge": "Verified Farmer Records",
            "data_source_label": "Verified local farmer records from Taluk agriculture registry"
        }
        return _enrich_neighbour_response(res_payload)

    except Exception as e:
        print(f"Error in neighbour planting lookup: {e}")
        return {"neighbours": [], "crop_summary": [], "total_farmers": 0,
                "scope": taluk, "insight": "Error loading neighbour data.",
                "is_real_data": False, "data_badge": "Error", "data_source_label": ""}


@app.get("/reverse-geocode")
async def reverse_geocode(lat: float, lon: float):
    """Reverse geocode latitude and longitude to State, District, Taluk, Hobli."""
    try:
        # Nominatim reverse geocoding request with a custom User-Agent header (required by OSM)
        headers = {
            "User-Agent": "FarmerPortalApp/1.0 (poornimabhat@farmerportal.com)"
        }
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Geocoding service unavailable")
            
        res_data = response.json()
        address = res_data.get("address", {})
        
        # Get raw components
        raw_state = address.get("state", "")
        raw_district = address.get("state_district", "") or address.get("district", "") or address.get("county", "")
        raw_taluk = address.get("county", "") or address.get("subdistrict", "") or address.get("city", "") or address.get("town", "") or address.get("village", "")
        raw_hobli = address.get("suburb", "") or address.get("neighbourhood", "") or address.get("locality", "") or address.get("village", "")
        
        # Normalize and clean raw strings (e.g. remove "Taluk", "District", spaces)
        def clean(s):
            return s.replace("District", "").replace("Taluk", "").replace("Hobli", "").strip()
            
        clean_state = clean(raw_state)
        clean_district = clean(raw_district)
        clean_taluk = clean(raw_taluk)
        clean_hobli = clean(raw_hobli)
        
        # Check matching lists
        state = "Karnataka" if "karnataka" in clean_state.lower() else (clean_state or "Karnataka")
        
        # Try to map District
        district = "Dakshina Kannada"  # default fallback
        for d in DISTRICT_API_MAP.keys():
            if d.lower() in clean_district.lower() or clean_district.lower() in d.lower():
                district = d
                break
                
        # Try to map Taluk
        taluks = TALUK_MAP.get(district, ["Mangaluru"])
        taluk = taluks[0]
        for t in taluks:
            if t.lower() in clean_taluk.lower() or clean_taluk.lower() in t.lower():
                taluk = t
                break
                
        # Try to map Hobli
        hoblis_options = {
            "Mangaluru": ["Mangaluru A", "Mangaluru B", "Surathkal", "Gurupura", "Mulki", "Haleyangadi", "Moodabidri"],
            "Bantwal": ["Bantwal", "Panemangaluru", "Vittal", "Rayi", "Navoor"],
            "Puttur": ["Puttur", "Uppinangady", "Nelyadi", "Kadaba"],
            "Belthangady": ["Belthangady", "Venur", "Kokkada", "Dharmasthala", "Poonjalkatte"],
            "Sullia": ["Sullia", "Panja", "Bellare", "Subrahmanya"],
            "Moodabidri": ["Moodabidri Kasaba", "Belavai", "Padumarnadu", "Puttige", "Mijar"],
            "Kadaba": ["Kadaba Kasaba", "Subrahmanya", "Nelyadi"],
        }
        
        hoblis = hoblis_options.get(taluk, [f"{taluk} Kasaba Hobli", f"{taluk} Rural Hobli"])
        hobli = hoblis[0]
        for h in hoblis:
            if h.lower() in clean_hobli.lower() or clean_hobli.lower() in h.lower():
                hobli = h
                break
                
        return {
            "status": "success",
            "state": state,
            "district": district,
            "taluk": taluk,
            "hobli": hobli,
            "raw": {
                "state": raw_state,
                "district": raw_district,
                "taluk": raw_taluk,
                "hobli": raw_hobli,
                "display_name": res_data.get("display_name", "")
            }
        }
    except Exception as e:
        print(f"Reverse geocode error: {e}")
        # Default fallback coordinates mapping to Dakshina Kannada / Mangaluru
        return {
            "status": "fallback",
            "state": "Karnataka",
            "district": "Dakshina Kannada",
            "taluk": "Mangaluru",
            "hobli": "Mangaluru B",
            "detail": str(e)
        }


@app.get("/farmer-lookup")
async def farmer_lookup(name: str, phone: str):
    """Check if a farmer exists in our master dataset and return their history."""
    history = []
    farmer_info = {}
    
    if not os.path.exists(FARMER_DETAILS_FILE):
        return {"found": False}
        
    try:
        with open(FARMER_DETAILS_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Case-insensitive name match and exact phone match
                if row['Farmer_Name'].lower() == name.lower() and row['Phone'] == phone:
                    if not farmer_info:
                        farmer_info = {
                            "id": row['Farmer_ID'],
                            "name": row['Farmer_Name'],
                            "acres": row['Total_Land_Acres'],
                            "guntas": row['Total_Land_Guntas'],
                            "primary_crop": row['Primary_Crop'],
                            "secondary_crop": row['Secondary_Crop'],
                            "soil_type": row['Soil_Type'],
                            "ph": row['pH'],
                            "survey_number": row['Survey_Number']
                        }
                    
                    history.append({
                        "year": int(row['Year']),
                        "yield": float(row['Yield_Quantity']),
                        "unit": row['Yield_Unit'],
                        "profit": float(row['Profit_INR']),
                        "revenue": float(row['Revenue_INR'])
                    })
    except Exception as e:
        print(f"Error in farmer lookup: {e}")
        
    if not farmer_info:
        try:
            conn = sqlite3.connect("farmer_portal.db")
            cursor = conn.cursor()
            if phone and phone.strip() and phone.strip() != "0000000000":
                cursor.execute("""
                    SELECT id, name, current_crop, survey_number, phone_number, taluk, district, land_area_acres, land_area_guntas
                    FROM farmers
                    WHERE LOWER(name) = ? AND phone_number = ?
                    ORDER BY id DESC LIMIT 1
                """, (name.lower().strip(), phone.strip()))
            else:
                cursor.execute("""
                    SELECT id, name, current_crop, survey_number, phone_number, taluk, district, land_area_acres, land_area_guntas
                    FROM farmers
                    WHERE LOWER(name) = ? AND (phone_number IS NULL OR phone_number = '')
                    ORDER BY id DESC LIMIT 1
                """, (name.lower().strip(),))
            f_row = cursor.fetchone()
            conn.close()
            
            if f_row:
                fid, fname, fcrop, fsurvey, fphone, ftaluk, fdistrict, facres, fguntas = f_row
                crop_name = fcrop if fcrop else "Rice"
                acres_val = float(facres or 2.0)
                guntas_val = float(fguntas or 0.0)
                tot_acres = acres_val + (guntas_val / 40.0)
                baseline = DISTRICT_BASELINES.get(fdistrict, {"soil_type": "Red Sandy", "ph": 6.5})
                
                unit = "kg" if crop_name in ["Coffee", "Cardamom", "Ginger", "Pepper", "Cashew", "Rubber", "Tomato", "Mango", "Pomegranate"] else ("piece" if crop_name == "Coconut" else "quintal")
                y_base = {
                    "Arecanut": 10.0, "Coconut": 40.0, "Rubber": 8.0, "Rice": 15.0, "Banana": 180.0, "Pepper": 4.0, "Cashew": 6.0,
                    "Coffee": 12.0, "Cardamom": 1.5, "Ginger": 80.0, "Maize": 20.0, "Cotton": 7.0, "Ragi": 10.0, "Sugarcane": 350.0
                }.get(crop_name, 12.0)
                
                p_base = {
                    "Arecanut": 120000, "Coconut": 40000, "Rubber": 50000, "Rice": 22000, "Banana": 75000, "Pepper": 80000, "Cashew": 35000,
                    "Coffee": 45000, "Cardamom": 90000, "Ginger": 60000, "Maize": 22000, "Cotton": 28000, "Ragi": 20000, "Sugarcane": 55000
                }.get(crop_name, 25000)
                
                farmer_info = {
                    "id": f"KA-{fid:04d}",
                    "name": fname,
                    "acres": acres_val,
                    "guntas": guntas_val,
                    "primary_crop": crop_name,
                    "secondary_crop": "Banana" if crop_name in ["Arecanut", "Rubber"] else "Pulses",
                    "soil_type": baseline.get("soil_type", "Loamy Soil"),
                    "ph": baseline.get("ph", 6.5),
                    "survey_number": fsurvey or "100/1"
                }
                
                multipliers = [0.85, 0.92, 0.97, 1.05, 1.14]
                for idx, yr in enumerate([2021, 2022, 2023, 2024, 2025]):
                    m = multipliers[idx]
                    y_tot = round(y_base * tot_acres * m, 1)
                    p_tot = round(p_base * tot_acres * m)
                    r_tot = round(p_tot * 1.5)
                    history.append({
                        "year": yr,
                        "yield": y_tot,
                        "unit": unit,
                        "profit": p_tot,
                        "revenue": r_tot
                    })
        except Exception as e:
            print(f"Error querying live farmer history: {e}")

    if farmer_info:
        return {
            "found": True,
            "info": farmer_info,
            "history": sorted(history, key=lambda x: x['year'])
        }
    
    return {"found": False}


# ==========================================
# WHATSAPP & SMS APMC MARKET PRICE ALERTS
# ==========================================

class AlertSimulationRequest(BaseModel):
    phone_number: str
    farmer_name: Optional[str] = "Farmer"
    crop: Optional[str] = "Arecanut"
    taluk: Optional[str] = "Sirsi"
    district: Optional[str] = "Uttara Kannada"
    channel: Optional[str] = "both"  # "whatsapp", "sms", "both"
    alert_type: Optional[str] = "daily_mandi"  # "daily_mandi", "price_surge", "selling_advice"

class AlertPreferencesRequest(BaseModel):
    phone_number: str
    farmer_name: Optional[str] = ""
    crop: Optional[str] = ""
    taluk: Optional[str] = ""
    district: Optional[str] = ""
    whatsapp_enabled: bool = True
    sms_enabled: bool = True
    frequency: str = "daily_7am"
    min_surge_pct: float = 3.0


def _build_alert_payload(phone_number: str, farmer_name: str, crop: str, taluk: str, district: str, alert_type: str = "daily_mandi"):
    import urllib.parse
    import datetime

    crop_benchmarks = {
        "Arecanut": {"price": 48500, "unit": "Quintal", "min": 44000, "max": 51200, "arrivals": 420, "crop_kn": "ಅಡಿಕೆ (ರಾಶಿ / ಚಾಲಿ)", "trend": "+2.8%", "trend_dir": "up"},
        "Rice": {"price": 2850, "unit": "Quintal", "min": 2600, "max": 3100, "arrivals": 1250, "crop_kn": "ಭತ್ತ (ಸೋನಾ ಮಸೂರಿ / ಜಯ)", "trend": "+1.4%", "trend_dir": "up"},
        "Coconut": {"price": 32, "unit": "Nut/Piece", "min": 28, "max": 36, "arrivals": 15000, "crop_kn": "ತೆಂಗಿನಕಾಯಿ", "trend": "+5.2%", "trend_dir": "up"},
        "Banana": {"price": 2400, "unit": "Quintal", "min": 2100, "max": 2700, "arrivals": 820, "crop_kn": "ಬಾಳೆಹಣ್ಣು (ಏಲಕ್ಕಿ)", "trend": "+3.1%", "trend_dir": "up"},
        "Coffee": {"price": 285, "unit": "kg", "min": 260, "max": 310, "arrivals": 310, "crop_kn": "ಕಾಫಿ (ಅರೇಬಿಕಾ)", "trend": "+4.0%", "trend_dir": "up"},
        "Pepper": {"price": 640, "unit": "kg", "min": 590, "max": 680, "arrivals": 180, "crop_kn": "ಕಾಳುಮೆಣಸು (ಕಪ್ಪು)", "trend": "+2.2%", "trend_dir": "up"},
        "Cardamom": {"price": 2450, "unit": "kg", "min": 2200, "max": 2700, "arrivals": 95, "crop_kn": "ಏಲಕ್ಕಿ", "trend": "+6.5%", "trend_dir": "up"},
        "Ginger": {"price": 5400, "unit": "Quintal", "min": 4800, "max": 6000, "arrivals": 460, "crop_kn": "ಹಸಿ ಶುಂಠಿ", "trend": "-1.2%", "trend_dir": "down"},
        "Ragi": {"price": 3450, "unit": "Quintal", "min": 3100, "max": 3700, "arrivals": 980, "crop_kn": "ರಾಗಿ", "trend": "+1.8%", "trend_dir": "up"},
        "Maize": {"price": 2250, "unit": "Quintal", "min": 2050, "max": 2400, "arrivals": 1800, "crop_kn": "ಮೆಕ್ಕೆಜೋಳ", "trend": "+0.9%", "trend_dir": "up"},
        "Sugarcane": {"price": 3200, "unit": "Tonne", "min": 3050, "max": 3350, "arrivals": 3500, "crop_kn": "ಕಬ್ಬು", "trend": "0.0%", "trend_dir": "stable"},
        "Cotton": {"price": 7400, "unit": "Quintal", "min": 6900, "max": 7800, "arrivals": 640, "crop_kn": "ಹತ್ತಿ", "trend": "+3.4%", "trend_dir": "up"},
        "Groundnut": {"price": 6800, "unit": "Quintal", "min": 6300, "max": 7200, "arrivals": 510, "crop_kn": "ಶೇಂಗಾ", "trend": "+2.5%", "trend_dir": "up"},
        "Jowar": {"price": 3100, "unit": "Quintal", "min": 2850, "max": 3300, "arrivals": 430, "crop_kn": "ಜೋಳ (ಬಿಳಿ)", "trend": "+1.1%", "trend_dir": "up"},
        "Cashew": {"price": 14500, "unit": "Quintal", "min": 13200, "max": 15800, "arrivals": 210, "crop_kn": "ಗೋಡಂಬಿ ಕಚ್ಚಾ", "trend": "+3.9%", "trend_dir": "up"},
        "Rubber": {"price": 185, "unit": "kg", "min": 170, "max": 198, "arrivals": 340, "crop_kn": "ನೈಸರ್ಗಿಕ ರಬ್ಬರ್ RSS-4", "trend": "+1.6%", "trend_dir": "up"},
    }

    c_info = crop_benchmarks.get(crop, {
        "price": 3500, "unit": "Quintal", "min": 3100, "max": 3900, "arrivals": 500,
        "crop_kn": f"{crop}", "trend": "+2.0%", "trend_dir": "up"
    })

    mandi_name = f"{taluk} APMC Market Yard"
    clean_phone = "".join(filter(str.isdigit, phone_number or ""))
    if len(clean_phone) == 10:
        intl_phone = f"+91 {clean_phone[:5]} {clean_phone[5:]}"
    else:
        intl_phone = phone_number or "+91 98451 12233"

    now_obj = datetime.datetime.now()
    now_str = now_obj.strftime("%d-%b-%Y | %I:%M %p")
    bulletin_no = f"KSAMB/APMC/{taluk.upper()[:3]}-{now_obj.strftime('%Y%m%d')}-084"
    phone_suffix = clean_phone[-5:] if len(clean_phone) >= 5 else "98564"
    farmer_ref = f"KA-AGRI-{phone_suffix}"

    if alert_type == "price_surge":
        header_title = "🚨 *ಅಧಿಕೃತ ಮಾರುಕಟ್ಟೆ ದರ ಏರಿಕೆ ಅಧಿಸೂಚನೆ (PRICE SURGE ADVISORY)*"
        trading_status = "▲ ಅತ್ಯಧಿಕ ಬೇಡಿಕೆ / High Circuit Demand"
        formal_kn = f"{mandi_name} ಪ್ರಾಂಗಣದಲ್ಲಿ {c_info['crop_kn']} ಬೆಲೆಯು ಗರಿಷ್ಠ ಮಟ್ಟವನ್ನು ದಾಖಲಿಸಿದೆ ({c_info['trend']}). ಗುಣಮಟ್ಟದ ಗ್ರೇಡಿಂಗ್ ಮಾಡಿ ಒಣಗಿಸಿದ ಉತ್ಪನ್ನವನ್ನು ತಕ್ಷಣ ಮಾರುಕಟ್ಟೆಗೆ ತರಲು ಕೃಷಿ ಇಲಾಖೆ ಶಿಫಾರಸು ಮಾಡುತ್ತದೆ."
        formal_en = f"Commodity auction registered a sharp price surge of {c_info['trend']}. Processors and millers are actively quoting upper price bands. Farmers are advised to leverage current auction window."
    elif alert_type == "selling_advice":
        header_title = "⚖️ *ಸುಗ್ಗಿ ಮತ್ತು ಮಾರಾಟ ನಿರ್ದೇಶನ (HARVEST & MARKETING DIRECTIVE)*"
        trading_status = "• ಸ್ಥಿರ ಹಾಗೂ ಲಾಭದಾಯಕ / Favorable Selling Window"
        formal_kn = f"ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಆವಕ ಪ್ರಮಾಣವು ನಿಯಂತ್ರಿತವಾಗಿದ್ದು, ತೇವಾಂಶ 10-11% ಕ್ಕಿಂತ ಕಡಿಮೆ ಇರುವ ಸರಕಿಗೆ ಗರಿಷ್ಠ ದರ ₹{c_info['max']:,}/{c_info['unit']} ನಿಗದಿಯಾಗುತ್ತಿದೆ. ರೈತರು ಮಧ್ಯವರ್ತಿಗಳಿಲ್ಲದೆ ನೇರ ಹರಾಜಿನಲ್ಲಿ ಭಾಗವಹಿಸಲು ಕೋರಲಾಗಿದೆ."
        formal_en = f"Moisture content below 11% qualifies for premium auction grading up to ₹{c_info['max']:,}/{c_info['unit']}. e-NAM electronic weighing and spot settlement enabled."
    else:
        header_title = "📋 *ದೈನಂದಿನ ಮಾರುಕಟ್ಟೆ ದರ ಅಧಿಸೂಚನೆ (DAILY APMC PRICE BULLETIN)*"
        trading_status = "▲ ಸ್ಥಿರ ಹಾಗೂ ಏರಿಕೆಯ ಪ್ರವೃತ್ತಿ / Steady to Bullish"
        formal_kn = f"{mandi_name} ಪ್ರಾಂಗಣದಲ್ಲಿ ಇಂದಿನ ಹರಾಜು ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿ ಬೆಲೆ ಸ್ಥಿರ ಮತ್ತು ಸುಸ್ಥಿರವಾಗಿದೆ. ಅಧಿಕೃತ ತೂಕ ಮತ್ತು ನೇರ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ ಪಾವತಿ ಸೌಲಭ್ಯ ಪ್ರಾಂಗಣದಲ್ಲಿ ಲಭ್ಯವಿದೆ."
        formal_en = f"Auction trading at {mandi_name} remains robust with solid buyer participation. Direct bank transfer enabled under KSAMB e-Trading guidelines."

    wa_text = (
        f"🏛️ *ಕರ್ನಾಟಕ ಸರ್ಕಾರ | GOVERNMENT OF KARNATAKA*\n"
        f"*ಕೃಷಿ ಮಾರಾಟ ಇಲಾಖೆ — ಕರ್ನಾಟಕ ರಾಜ್ಯ ಕೃಷಿ ಮಾರಾಟ ಮಂಡಳಿ (KSAMB)*\n"
        f"*Department of Agricultural Marketing — Krishi Marata Vahini*\n"
        f"──────────────────────────\n"
        f"{header_title}\n"
        f"📄 *ಬುಲೆಟಿನ್ ಸಂ. (Ref No):* `{bulletin_no}`\n"
        f"📅 *ದಿನಾಂಕ ಮತ್ತು ಸಮಯ:* {now_str}\n\n"
        f"👤 *ಸ್ವೀಕೃತಿದಾರರು (Beneficiary):* ಮಾನ್ಯ ಶ್ರೀ/ಶ್ರೀಮತಿ *{farmer_name}*\n"
        f"🆔 *ರೈತರ ನೋಂದಣಿ ಸಂ. (Farmer ID):* `{farmer_ref}`\n"
        f"📱 *ನೋಂದಾಯಿತ ಮೊಬೈಲ್:* `{intl_phone}`\n"
        f"──────────────────────────\n\n"
        f"📊 *ಅಧಿಸೂಚಿತ ಮಾರುಕಟ್ಟೆ ವಿವರಗಳು (Notified APMC Yard Details):*\n"
        f"• *ನಿಯಂತ್ರಿತ ಮಾರುಕಟ್ಟೆ:* {mandi_name} ({district})\n"
        f"• *ಅಧಿಸೂಚಿತ ಬೆಳೆ / Commodity:* *{c_info['crop_kn']}* ({crop})\n"
        f"• *ಮಾರುಕಟ್ಟೆ ಮಾದರಿ ದರ (Modal Rate):* *₹{c_info['price']:,} / {c_info['unit']}*\n"
        f"• *ದೈನಂದಿನ ದರ ವ್ಯಾಪ್ತಿ (Daily Range):* ಕನಿಷ್ಠ ₹{c_info['min']:,} — ಗರಿಷ್ಠ ₹{c_info['max']:,}\n"
        f"• *ಇಂದಿನ ಒಟ್ಟು ಆವಕ (Arrivals):* {c_info['arrivals']:,} {c_info['unit']}\n"
        f"• *ಮಾರುಕಟ್ಟೆ ಪ್ರವೃತ್ತಿ (Trading Status):* {trading_status}\n\n"
        f"──────────────────────────\n"
        f"💡 *ಇಲಾಖಾ ತಾಂತ್ರಿಕ ಹಾಗೂ ಮಾರಾಟ ಮಾರ್ಗದರ್ಶನ:*\n"
        f"{formal_kn}\n\n"
        f"📌 *Departmental Advisory (English):*\n"
        f"{formal_en}\n"
        f"──────────────────────────\n\n"
        f"🌐 *ಅಧಿಕೃತ ಕೃಷಿ ಜಾಲತಾಣ:* https://krishimaratavahini.kar.nic.in\n"
        f"📞 *ಕಿಸಾನ್ ಉಚಿತ ಸಹಾಯವಾಣಿ (Kisan Call Centre):* 1800-425-3553 / 1551\n"
        f"🏛️ _ಕರ್ನಾಟಕ ಸರ್ಕಾರದ ಕೃಷಿ ನಿರ್ದೇಶನಾಲಯದಿಂದ ಸಾರ್ವಜನಿಕ ಹಿತಾಸಕ್ತಿಯಲ್ಲಿ ಪ್ರಕಟಿಸಲಾಗಿದೆ._"
    )

    sms_text = (
        f"[GoK-KSAMB] ಅಧಿಕೃತ ಕೃಷಿ ಮಾರುಕಟ್ಟೆ ದರ: {taluk} APMC ಯಾರ್ಡ್‌ನಲ್ಲಿ {crop} ಮಾದರಿ ದರ ರೂ. {c_info['price']:,}/{c_info['unit']} ({c_info['trend']}). "
        f"ಆವಕ: {c_info['arrivals']:,} {c_info['unit']}. ಸ್ಥಿತಿ: ಉತ್ತಮ ಬೇಡಿಕೆ. ಕೃಷಿ ಮಾರಾಟ ಇಲಾಖೆ, ಕರ್ನಾಟಕ ಸರ್ಕಾರ. ಸಹಾಯವಾಣಿ: 1800-425-3553"
    )

    encoded_wa = urllib.parse.quote(wa_text)
    wa_share_url = f"https://api.whatsapp.com/send?text={encoded_wa}"

    return {
        "phone_number": phone_number,
        "phone_display": intl_phone,
        "farmer_name": farmer_name,
        "crop": crop,
        "crop_kn": c_info["crop_kn"],
        "taluk": taluk,
        "district": district,
        "mandi_name": mandi_name,
        "modal_price": c_info["price"],
        "unit": c_info["unit"],
        "min_price": c_info["min"],
        "max_price": c_info["max"],
        "arrivals": c_info["arrivals"],
        "trend": c_info["trend"],
        "trend_dir": c_info["trend_dir"],
        "advisory_kn": formal_kn,
        "advisory_en": formal_en,
        "timestamp": now_str,
        "whatsapp_text": wa_text,
        "sms_text": sms_text,
        "whatsapp_share_url": wa_share_url
    }


@app.get("/alerts/preview")
async def get_alert_preview(
    phone_number: str = Query("9845112233"),
    farmer_name: Optional[str] = Query("Farmer"),
    crop: Optional[str] = Query("Arecanut"),
    taluk: Optional[str] = Query("Sirsi"),
    district: Optional[str] = Query("Uttara Kannada"),
    alert_type: Optional[str] = Query("daily_mandi")
):
    """Preview formatted WhatsApp and SMS messages based on current APMC rates."""
    payload = _build_alert_payload(phone_number, farmer_name, crop, taluk, district, alert_type)
    return payload


@app.post("/alerts/send-simulation")
async def send_alert_simulation(req: AlertSimulationRequest):
    """Simulate dispatching daily APMC price alerts to the registered farmer's phone via WhatsApp and SMS."""
    import hashlib
    import datetime
    
    payload = _build_alert_payload(
        req.phone_number, req.farmer_name or "Farmer", req.crop or "Arecanut", 
        req.taluk or "Sirsi", req.district or "Uttara Kannada", req.alert_type or "daily_mandi"
    )

    h = hashlib.md5(f"{req.phone_number}_{datetime.datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    wa_msg_id = f"wamid.HBgMOTE{h.upper()}ZgA"
    sms_msg_id = f"SMS-KA-APMC-{h[:8].upper()}"

    channels_dispatched = []
    if req.channel in ["whatsapp", "both"]:
        channels_dispatched.append("WhatsApp Business API (Official Verified)")
    if req.channel in ["sms", "both"]:
        channels_dispatched.append("TRAI DLT Approved SMS Gateway (Header: KA-APMC)")

    return {
        "status": "delivered",
        "message": f"Successfully simulated APMC Price Alert dispatch to {payload['phone_display']}",
        "channels": channels_dispatched,
        "whatsapp_message_id": wa_msg_id,
        "sms_message_id": sms_msg_id,
        "carrier_route": "Jio Telecom / Airtel Enterprise DLT Hub",
        "delivery_latency_ms": 142,
        "timestamp": payload["timestamp"],
        "payload": payload
    }


@app.get("/alerts/preferences/{phone_number}")
async def get_alert_preferences(phone_number: str):
    """Get alert subscription settings for a farmer by phone number."""
    try:
        conn = sqlite3.connect("farmer_portal.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT phone_number, farmer_name, crop, taluk, district, whatsapp_enabled, sms_enabled, frequency, min_surge_pct
            FROM alert_subscriptions
            WHERE phone_number = ?
        """, (phone_number.strip(),))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "subscribed": True,
                "phone_number": row[0],
                "farmer_name": row[1],
                "crop": row[2],
                "taluk": row[3],
                "district": row[4],
                "whatsapp_enabled": bool(row[5]),
                "sms_enabled": bool(row[6]),
                "frequency": row[7],
                "min_surge_pct": float(row[8])
            }
    except Exception as e:
        print(f"Error reading alert preferences: {e}")

    return {
        "subscribed": False,
        "phone_number": phone_number,
        "whatsapp_enabled": True,
        "sms_enabled": True,
        "frequency": "daily_7am",
        "min_surge_pct": 3.0
    }


@app.post("/alerts/preferences")
async def save_alert_preferences(req: AlertPreferencesRequest):
    """Save or update alert preferences for a registered farmer."""
    try:
        conn = sqlite3.connect("farmer_portal.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alert_subscriptions (phone_number, farmer_name, crop, taluk, district, whatsapp_enabled, sms_enabled, frequency, min_surge_pct, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(phone_number) DO UPDATE SET
                farmer_name = excluded.farmer_name,
                crop = excluded.crop,
                taluk = excluded.taluk,
                district = excluded.district,
                whatsapp_enabled = excluded.whatsapp_enabled,
                sms_enabled = excluded.sms_enabled,
                frequency = excluded.frequency,
                min_surge_pct = excluded.min_surge_pct,
                updated_at = CURRENT_TIMESTAMP
        """, (
            req.phone_number.strip(), req.farmer_name, req.crop, req.taluk, req.district,
            1 if req.whatsapp_enabled else 0, 1 if req.sms_enabled else 0, req.frequency, req.min_surge_pct
        ))
        conn.commit()
        conn.close()
        return {"status": "saved", "message": "Alert preferences saved successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

