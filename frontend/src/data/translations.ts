// Translations for Farmer Portal (English & Kannada)

export type Language = 'en' | 'kn';

export const cropTranslations: Record<string, { en: string; kn: string; emoji: string }> = {
    'Rice': { en: 'Rice (Paddy)', kn: 'ಅಕ್ಕಿ (ಭತ್ತ)', emoji: '🌾' },
    'Banana': { en: 'Banana', kn: 'ಬಾಳೆಹಣ್ಣು', emoji: '🍌' },
    'Arecanut': { en: 'Arecanut (Betel Nut)', kn: 'ಅಡಿಕೆ', emoji: '🌴' },
    'Pepper': { en: 'Black Pepper', kn: 'ಕಾಳುಮೆಣಸು', emoji: '🌶️' },
    'Cashew': { en: 'Cashew Nut', kn: 'ಗೋಡಂಬಿ', emoji: '🥜' },
    'Rubber': { en: 'Rubber', kn: 'ರಬ್ಬರ್', emoji: '🌳' },
    'Coconut': { en: 'Coconut', kn: 'ತೆಂಗಿನಕಾಯಿ', emoji: '🥥' },
    'Wheat': { en: 'Wheat', kn: 'ಗೋಧಿ', emoji: '🌾' },
    'Sugarcane': { en: 'Sugarcane', kn: 'ಕಬ್ಬು', emoji: '🎋' },
    'Cotton': { en: 'Cotton', kn: 'ಹತ್ತಿ', emoji: '☁️' },
    'Coffee': { en: 'Coffee', kn: 'ಕಾಫಿ', emoji: '☕' },
    'Cardamom': { en: 'Cardamom', kn: 'ಏಲಕ್ಕಿ', emoji: '🌱' },
    'Ginger': { en: 'Ginger', kn: 'ಶುಂಠಿ', emoji: '🥔' },
    'Jowar': { en: 'Jowar (Sorghum)', kn: 'ಜೋಳ', emoji: '🌾' },
    'Maize': { en: 'Maize (Corn)', kn: 'ಮೆಕ್ಕೆಜೋಳ', emoji: '🌽' },
    'Bengal Gram': { en: 'Bengal Gram (Chana)', kn: 'ಕಡಲೆ', emoji: '🥜' },
    'Red Gram': { en: 'Red Gram (Tur Dal)', kn: 'ತೊಗರಿ', emoji: '🫘' },
    'Pomegranate': { en: 'Pomegranate', kn: 'ದಾಳಿಂಬೆ', emoji: '🍎' },
    'Ragi': { en: 'Ragi (Finger Millet)', kn: 'ರಾಗಿ', emoji: '🌾' },
    'Groundnut': { en: 'Groundnut (Peanut)', kn: 'ಶೇಂಗಾ (ನೆಲಗಡಲೆ)', emoji: '🥜' },
    'Tomato': { en: 'Tomato', kn: 'ಟೊಮೆಟೊ', emoji: '🍅' },
    'Mango': { en: 'Mango', kn: 'ಮಾವಿನಹಣ್ಣು', emoji: '🥭' },
    'Onion': { en: 'Onion', kn: 'ಈರುಳ್ಳಿ', emoji: '🧅' },
    'Potato': { en: 'Potato', kn: 'ಆಲೂಗಡ್ಡೆ', emoji: '🥔' },
    'Turmeric': { en: 'Turmeric', kn: 'ಅರಿಶಿನ', emoji: '🌿' },
    'Chilli': { en: 'Chilli', kn: 'ಮೆಣಸಿನಕಾಯಿ', emoji: '🌶️' }
};

export const soilTranslations: Record<string, { en: string; kn: string }> = {
    'Laterite': { en: 'Laterite Soil', kn: 'ಲ್ಯಾಟರೈಟ್ (ಕೆಂಪು ಜೇಡಿ ಮಣ್ಣು)' },
    'Red Sandy': { en: 'Red Sandy Soil', kn: 'ಕೆಂಪು ಉಸುಕು ಮಣ್ಣು' },
    'Red Loam': { en: 'Red Loamy Soil', kn: 'ಕೆಂಪು ಲೋಮ್ ಮಣ್ಣು' },
    'Black Cotton': { en: 'Black Cotton Soil', kn: 'ಕಪ್ಪು ಹತ್ತಿ ಮಣ್ಣು' },
    'Dark Hilly': { en: 'Dark Hilly Soil', kn: 'ಮಲೆನಾಡು ಗಿರಿಕಂದರದ ಕಪ್ಪು ಮಣ್ಣು' },
    'Deep Black': { en: 'Deep Black Soil', kn: 'ಆಳವಾದ ಕಪ್ಪು ಮಣ್ಣು' },
    'Alluvial': { en: 'Alluvial Soil', kn: 'ಎರಡುಪಟ್ಟು ಫಲವತ್ತಾದ ಹೂಳಿನ ಮಣ್ಣು' }
};

export const weatherTranslations: Record<string, { en: string; kn: string }> = {
    'clear sky': { en: 'Clear Sky', kn: 'ನಿರ್ಮಲ ಆಕಾಶ' },
    'few clouds': { en: 'Few Clouds', kn: 'ಸ್ವಲ್ಪ ಮೋಡ ಕವಿದ ಆಕಾಶ' },
    'scattered clouds': { en: 'Scattered Clouds', kn: 'ಚದುರಿದ ಮೋಡಗಳು' },
    'broken clouds': { en: 'Broken Clouds', kn: 'ದಟ್ಟ ಮೋಡಗಳು' },
    'overcast clouds': { en: 'Overcast Clouds', kn: 'ಮೋಡ ಮುಸುಕಿದ ವಾತಾವರಣ' },
    'shower rain': { en: 'Shower Rain', kn: 'ಸಣ್ಣ ಮಳೆ' },
    'rain': { en: 'Rainy', kn: 'ಮಳೆಯ ವಾತಾವರಣ' },
    'thunderstorm': { en: 'Thunderstorm', kn: 'ಸಿಡಿಲು ಸಹಿತ ಮಳೆ' },
    'light rain': { en: 'Light Rain', kn: 'ಹಗುರ ಮಳೆ' },
    'moderate rain': { en: 'Moderate Rain', kn: 'ಸಾಧಾರಣ ಮಳೆ' },
    'heavy rain': { en: 'Heavy Rain', kn: 'ಭಾರೀ ಮಳೆ' },
    'partly cloudy': { en: 'Partly Cloudy', kn: 'ಸ್ವಲ್ಪ ಮೋಡ ಕವಿದ ಆಕಾಶ' },
    'mostly cloudy': { en: 'Mostly Cloudy', kn: 'ಮೋಡ ಕವಿದ ಆಕಾಶ' },
    'foggy': { en: 'Foggy', kn: 'ಮಂಜು ಮುಸುಕಿದ ವಾತಾವರಣ' },
    'light drizzle': { en: 'Light Drizzle', kn: 'ತುಂತುರು ಮಳೆ' },
    'moderate drizzle': { en: 'Moderate Drizzle', kn: 'ಸಾಧಾರಣ ತುಂತುರು ಮಳೆ' },
    'dense drizzle': { en: 'Dense Drizzle', kn: 'ದಟ್ಟ ತುಂತುರು ಮಳೆ' },
    'light rain showers': { en: 'Light Rain Showers', kn: 'ಹಗುರ ಮಳೆ ಹನಿಗಳು' },
    'moderate rain showers': { en: 'Moderate Rain Showers', kn: 'ಸಾಧಾರಣ ಮಳೆ ಹನಿಗಳು' },
    'violent rain showers': { en: 'Violent Rain Showers', kn: 'ಭಾರೀ ಮಳೆ ಸುರಿಮಳೆ' },
    'thunderstorm with hail': { en: 'Thunderstorm with Hail', kn: 'ಆಲಿಕಲ್ಲು ಸಹಿತ ಸಿಡಿಲು ಮಳೆ' },
    'thunderstorm with heavy hail': { en: 'Thunderstorm with Heavy Hail', kn: 'ಭಾರೀ ಆಲಿಕಲ್ಲು ಸಹಿತ ಸಿಡಿಲು ಮಳೆ' },
    'overcast': { en: 'Overcast', kn: 'ಮೋಡ ಮುಸುಕಿದ ವಾತಾವರಣ' },
    'mist': { en: 'Mist', kn: 'ಮಂಜು' }
};

export const uiTranslations: Record<string, { en: string; kn: string }> = {
    // Header & Brand
    portalTitle: { en: 'Raitha Mitra — Karnataka Agricultural Portal', kn: 'ರೈತ ಮಿತ್ರ — ಕರ್ನಾಟಕ ಕೃಷಿ ಮಾಹಿತಿ ಪೋರ್ಟಲ್' },
    portalSubtitle: { en: 'Department of Agriculture & Agricultural Marketing (KSDA & KSAMB)', kn: 'ಕೃಷಿ ಇಲಾಖೆ ಮತ್ತು ಕರ್ನಾಟಕ ರಾಜ್ಯ ಕೃಷಿ ಮಾರಾಟ ಮಂಡಳಿ (ಕರ್ನಾಟಕ ಸರ್ಕಾರ)' },
    welcomeUser: { en: 'Welcome,', kn: 'ಸ್ವಾಗತ,' },
    surveyNo: { en: 'Survey No:', kn: 'ಸರ್ವೇ ಸಂಖ್ಯೆ:' },
    phoneNo: { en: 'Phone:', kn: 'ಮೊಬೈಲ್:' },
    currentCrop: { en: 'Current Crop:', kn: 'ಪ್ರಸ್ತುತ ಬೆಳೆ:' },
    registeredLand: { en: 'Registered Land:', kn: 'ನೋಂದಾಯಿತ ಜಮೀನು:' },
    acres: { en: 'Acres', kn: 'ಎಕರೆ' },
    guntas: { en: 'Guntas', kn: 'ಗುಂಟೆ' },
    useGPS: { en: 'Use GPS Location', kn: 'ಜಿಪಿಎಸ್ ಸ್ಥಳ ಬಳಸಿ' },
    tracking: { en: 'Tracking...', kn: 'ಹುಡುಕಲಾಗುತ್ತಿದೆ...' },
    logout: { en: 'Logout', kn: 'ನಿರ್ಗಮನ (Logout)' },
    
    // Auth Tabs & Titles
    login: { en: 'Login', kn: 'ಲಾಗಿನ್' },
    register: { en: 'Register', kn: 'ನೋಂದಣಿ' },
    welcomeBack: { en: 'Welcome Back', kn: 'ಮರಳಿ ಸ್ವಾಗತ' },
    loginSubtitle: { en: 'Enter your credentials to access your verified farm dashboard', kn: 'ದೃಢೀಕರಿಸಿದ ಕೃಷಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗಾಗಿ ಲಾಗಿನ್ ಆಗಿ' },
    fullName: { en: 'Full Name', kn: 'ಪೂರ್ಣ ಹೆಸರು' },
    enterFullName: { en: 'Enter your full name', kn: 'ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರು ನಮೂದಿಸಿ' },
    password: { en: 'Password', kn: 'ಪಾಸ್‌ವರ್ಡ್' },
    loggingIn: { en: 'Logging in...', kn: 'ಲಾಗಿನ್ ಆಗುತ್ತಿದೆ...' },
    loginBtn: { en: 'Login to Dashboard', kn: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಲಾಗಿನ್ ಆಗಿ' },
    
    // Registration Form
    joinCommunity: { en: 'Karnataka State Farmers Portal Registration', kn: 'ಕರ್ನಾಟಕ ರಾಜ್ಯ ರೈತರ ಅಧಿಕೃತ ನೋಂದಣಿ' },
    registerSubtitle: { en: 'Scientific crop suitability, certified cultivars & real-time APMC market intelligence', kn: 'ವೈಜ್ಞಾನಿಕ ಬೆಳೆ ಶಿಫಾರಸು, ಪ್ರಮಾಣೀಕೃತ ತಳಿಗಳು ಮತ್ತು ನೈಜ ಸಮಯದ ಮಾರುಕಟ್ಟೆ ಮಾಹಿತಿ' },
    surveyNumber: { en: 'Survey Number', kn: 'ಸರ್ವೇ ಸಂಖ್ಯೆ' },
    currentCropGrown: { en: 'Currently Grown Crop', kn: 'ಪ್ರಸ್ತುತ ಬೆಳೆಯುತ್ತಿರುವ ಬೆಳೆ' },
    selectCurrentCrop: { en: 'Select your current crop', kn: 'ಪ್ರಸ್ತುತ ಬೆಳೆಯುತ್ತಿರುವ ಬೆಳೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ' },
    phoneNumber: { en: 'Phone Number', kn: 'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ' },
    autoDetectGPS: { en: 'Auto-Detect Location (GPS)', kn: 'ಜಿಪಿಎಸ್ ಮೂಲಕ ಸ್ವಯಂಚಾಲಿತ ಸ್ಥಳ ಪತ್ತೆ' },
    detectingLoc: { en: 'Detecting location...', kn: 'ಸ್ಥಳ ಪತ್ತೆಮಾಡಲಾಗುತ್ತಿದೆ...' },
    state: { en: 'State', kn: 'ರಾಜ್ಯ' },
    district: { en: 'District', kn: 'ಜಿಲ್ಲೆ' },
    taluk: { en: 'Taluk', kn: 'ತಾಲೂಕು' },
    hobli: { en: 'Hobli', kn: 'ಹೋಬಳಿ' },
    selectDistrict: { en: 'Select District', kn: 'ಜಿಲ್ಲೆಯನ್ನು ಆಯ್ಕೆ ಮಾಡಿ' },
    selectTaluk: { en: 'Select Taluk', kn: 'ತಾಲೂಕನ್ನು ಆಯ್ಕೆ ಮಾಡಿ' },
    selectHobli: { en: 'Select Hobli', kn: 'ಹೋಬಳಿಯನ್ನು ಆಯ್ಕೆ ಮಾಡಿ' },
    setPassword: { en: 'Set Password', kn: 'ಪಾಸ್‌ವರ್ಡ್ ಹೊಂದಿಸಿ' },
    landAcres: { en: 'Land Area (Acres)', kn: 'ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ (ಎಕರೆ)' },
    landGuntas: { en: 'Land Area (Guntas)', kn: 'ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ (ಗುಂಟೆ)' },
    registering: { en: 'Registering...', kn: 'ನೋಂದಾಯಿಸಲಾಗುತ್ತಿದೆ...' },
    registerBtn: { en: 'Register & Continue', kn: 'ನೋಂದಾಯಿಸಿ ಮತ್ತು ಮುಂದುವರಿಯಿರಿ' },

    // Tabs
    tabCropRec: { en: '🌾 Crop Recommendation', kn: '🌾 ಬೆಳೆ ಶಿಫಾರಸು' },
    tabMarketPrices: { en: '💰 Market Rates', kn: '💰 ಮಾರುಕಟ್ಟೆ ದರಗಳು' },
    tabNeighbours: { en: '🏘️ Neighbours', kn: '🏘️ ನೆರೆಹೊರೆಯವರು' },
    tabFarmAnalysis: { en: '📊 My Farm Analysis', kn: '📊 ನನ್ನ ಹೊಲದ ವಿಶ್ಲೇಷಣೆ' },
    tabAlerts: { en: '📲 APMC Market Alerts', kn: '📲 ಮಾರುಕಟ್ಟೆ ಎಚ್ಚರಿಕೆಗಳು (WhatsApp & SMS)' },
    marketAlertsBtn: { en: 'Daily Price Alerts', kn: 'ದೈನಂದಿನ ದರ ಎಚ್ಚರಿಕೆ' },

    currentlyGrowing: { en: '🌿 Currently Growing on Your Land', kn: '🌿 ನಿಮ್ಮ ಜಮೀನಿನಲ್ಲಿ ಪ್ರಸ್ತುತ ಬೆಳೆಯುತ್ತಿರುವ ಬೆಳೆ' },
    noCropsGrowing: { en: 'No crops are currently growing on your land', kn: 'ನಿಮ್ಮ ಜಮೀನಿನಲ್ಲಿ ಪ್ರಸ್ತುತ ಯಾವುದೇ ಬೆಳೆ ಬೆಳೆಯುತ್ತಿಲ್ಲ' },
    activeCrop: { en: 'Active Crop', kn: 'ಪ್ರಸ್ತುತ ಬೆಳೆ' },
    aiRecommended: { en: '🌾 Agronomic Crop Recommendations', kn: '🌾 ಕೃಷಿ ಇಲಾಖೆ ಶಿಫಾರಸು ಮಾಡಿದ ಬೆಳೆಗಳು' },
    cropRecTitle: { en: '🌱 Scientific Crop Advisory for Your Land', kn: '🌱 ನಿಮ್ಮ ಜಮೀನಿಗೆ ಸೂಕ್ತವಾದ ವೈಜ್ಞಾನಿಕ ಬೆಳೆ ಶಿಫಾರಸು' },
    liveWeather: { en: '🌤️ Live Weather & Climate', kn: '🌤️ ಪ್ರಸ್ತುತ ಹವಾಮಾನ ಮಾಹಿತಿ' },
    refresh: { en: 'Refresh', kn: 'ನವೀಕರಿಸಿ' },
    temperature: { en: 'Temperature', kn: 'ತಾಪಮಾನ' },
    humidity: { en: 'Humidity', kn: 'ತೇವಾಂಶ' },
    rainfall: { en: 'Est. Rainfall', kn: 'ಅಂದಾಜು ಮಳೆ' },
    condition: { en: 'Condition', kn: 'ವಾತಾವರಣ' },
    soilDataTitle: { en: '🏔️ Soil Data — Karnataka Land Dataset', kn: '🏔️ ಮಣ್ಣಿನ ಗುಣಲಕ್ಷಣಗಳು — ಕರ್ನಾಟಕ ಜಮೀನು ಮಾಹಿತಿ' },
    soilType: { en: 'Soil Type', kn: 'ಮಣ್ಣಿನ ಪ್ರಕಾರ' },
    avgPH: { en: 'Average pH', kn: 'ಸರಾಸರಿ ಪಿಹೆಚ್ (pH)' },
    analyzing: { en: 'Analyzing soil & climate...', kn: 'ಮಣ್ಣು ಮತ್ತು ಹವಾಮಾನ ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...' },
    getCropRecBtn: { en: '🔍 Get Crop Recommendations for My Land', kn: '🔍 ನನ್ನ ಜಮೀನಿಗೆ ಬೆಳೆ ಶಿಫಾರಸು ಪಡೆಯಿರಿ' },
    recommendedCropsTitle: { en: '🌾 Recommended Crops for Your Region & Land', kn: '🌾 ನಿಮ್ಮ ಪ್ರಾಂತ್ಯ ಮತ್ತು ಜಮೀನಿಗೆ ಅತ್ಯುತ್ತಮ ಬೆಳೆಗಳು' },
    backBtn: { en: '← Back', kn: '← ಹಿಂತಿರುಗಿ' },
    checkMarket: { en: 'Check Market', kn: 'ಮಾರುಕಟ್ಟೆ ನೋಡಿ' },
    trendRising: { en: '↑ Rising', kn: '↑ ಏರಿಕೆಯಲ್ಲಿದೆ' },
    trendFalling: { en: '↓ Falling', kn: '↓ ಇಳಿಕೆಯಲ್ಲಿದೆ' },
    trendStable: { en: '• Stable', kn: '• ಸ್ಥಿರವಾಗಿದೆ' },

    // Market Rates Section
    marketRatesTitle: { en: '📊 Karnataka APMC Market Rates', kn: '📊 ಕರ್ನಾಟಕ ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆ ದರಗಳು' },
    marketRatesDesc: { en: 'View live APMC market prices from data.gov.in for Karnataka districts', kn: 'ಕರ್ನಾಟಕದ ಪ್ರತಿಯೊಂದು ಜಿಲ್ಲೆಯ ದಿನನಿತ್ಯದ ಮಾರುಕಟ್ಟೆ ದರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ' },
    selectKarnatakaDistrict: { en: '📍 Select Karnataka District', kn: '📍 ಕರ್ನಾಟಕದ ಜಿಲ್ಲೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ' },
    allKarnataka: { en: 'All Karnataka', kn: 'ಎಲ್ಲಾ ಕರ್ನಾಟಕ' },
    yourDistrict: { en: '📍 Your District', kn: '📍 ನಿಮ್ಮ ಜಿಲ್ಲೆ' },
    liveAPMCTable: { en: '🏪 Live APMC Prices', kn: '🏪 ನೇರ ಮಾರುಕಟ್ಟೆ ದರಗಳು' },
    apmcMarket: { en: 'Market (APMC)', kn: 'ಮಾರುಕಟ್ಟೆ (APMC)' },
    commodity: { en: 'Commodity', kn: 'ಬೆಳೆ / ಪದಾರ್ಥ' },
    variety: { en: 'Variety', kn: 'ತಳಿ' },
    minPrice: { en: 'Min Price', kn: 'ಕನಿಷ್ಠ ದರ' },
    maxPrice: { en: 'Max Price', kn: 'ಗರಿಷ್ಠ ದರ' },
    modalPrice: { en: 'Modal Price', kn: 'ಸರಾಸರಿ ದರ' },
    date: { en: 'Date', kn: 'ದಿನಾಂಕ' },
    fetchingLiveMarket: { en: 'Fetching live market prices...', kn: 'ನೇರ ಮಾರುಕಟ್ಟೆ ದರಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ...' },
    selectCropDetailed: { en: '🔍 Select a Crop for Profit Prediction', kn: '🔍 ಲಾಭದ ಅಂದಾಜಿಗಾಗಿ ಬೆಳೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ' },
    getMarketRateBtn: { en: '💰 Get Market Rate Prediction', kn: '💰 ಮಾರುಕಟ್ಟೆ ದರ ಅಂದಾಜು ಪಡೆಯಿರಿ' },
    goodTimeToSell: { en: '✅ Good time to sell! Market price is trending upward.', kn: '✅ ಮಾರಾಟ ಮಾಡಲು ಸೂಕ್ತ ಸಮಯ! ಮಾರುಕಟ್ಟೆ ದರ ಹೆಚ್ಚಾಗುತ್ತಿದೆ.' },
    considerHolding: { en: '⚠️ Consider holding. Market price is declining.', kn: '⚠️ ಕಾಯುವುದು ಉತ್ತಮ. ಮಾರುಕಟ್ಟೆ ದರ ಇಳಿಕೆಯಾಗುತ್ತಿದೆ.' },
    marketStable: { en: 'ℹ️ Market is stable. You can sell at your convenience.', kn: 'ℹ️ ಮಾರುಕಟ್ಟೆ ಸ್ಥಿರವಾಗಿದೆ. ನಿಮ್ಮ ಅನುಕೂಲಕ್ಕೆ ತಕ್ಕಂತೆ ಮಾರಾಟ ಮಾಡಬಹುದು.' },
    
    // Profit Calculator & Land Estimator
    profitCalcTitle: { en: '📐 Land Profit Estimator', kn: '📐 ಜಮೀನಿನ ಲಾಭದ ಲೆಕ್ಕಾಚಾರ' },
    profitCalcDesc: { en: 'Enter your Survey Number and Land Details to estimate yield & net profit', kn: 'ಇಳುವರಿ ಮತ್ತು ನಿವ್ವಳ ಲಾಭದ ಅಂದಾಜಿಗಾಗಿ ನಿಮ್ಮ ಸರ್ವೇ ಸಂಖ್ಯೆ ಮತ್ತು ಜಮೀನಿನ ವಿವರಗಳನ್ನು ನಮೂದಿಸಿ' },
    enterSurveyNumber: { en: 'Enter Survey Number (e.g. 123/A)', kn: 'ಸರ್ವೇ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ (ಉದಾ: 123/ಎ)' },
    calculateProfitBtn: { en: '📊 Calculate Estimated Profit', kn: '📊 ಅಂದಾಜು ಲಾಭವನ್ನು ಲೆಕ್ಕಹಾಕಿ' },
    calculating: { en: 'Calculating...', kn: 'ಲೆಕ್ಕಾಚಾರ ಮಾಡಲಾಗುತ್ತಿದೆ...' },
    estYield: { en: 'Est. Total Yield', kn: 'ಅಂದಾಜು ಒಟ್ಟು ಇಳುವರಿ' },
    estRevenue: { en: 'Est. Total Revenue', kn: 'ಅಂದಾಜು ಒಟ್ಟು ಆದಾಯ' },
    estInputCost: { en: 'Est. Input Cost', kn: 'ಅಂದಾಜು ವೆಚ್ಚ (~40%)' },
    estNetProfit: { en: 'Est. Net Profit', kn: 'ಅಂದಾಜು ನಿವ್ವಳ ಲಾಭ' },
    fiveYearPriceTrend: { en: '📈 5-Year Price History', kn: '📈 5 ವರ್ಷಗಳ ದರ ಇತಿಹಾಸ' },
    perAcre: { en: 'per acre', kn: 'ಎಕರೆಗೆ' },

    // Neighbours Section
    neighboursTitle: { en: '🏘️ Neighbours Planting Details in Your Area', kn: '🏘️ ನಿಮ್ಮ ಭಾಗದ ನೆರೆಹೊರೆಯ ರೈತರ ಬೆಳೆ ವಿವರಗಳು' },
    neighboursDesc: { en: 'Compare what nearby farmers in your Taluk/Hobli are growing to prevent oversupply', kn: 'ಅತಿಯಾದ ಪೂರೈಕೆ ತಪ್ಪಿಸಲು ನಿಮ್ಮ ತಾಲೂಕು/ಹೋಬಳಿಯ ರೈತರು ಬೆಳೆಯುತ್ತಿರುವ ಬೆಳೆಗಳನ್ನು ನೋಡಿ' },
    sameTaluk: { en: '📍 Same Taluk', kn: '📍 ಅದೇ ತಾಲೂಕು' },
    sameHobli: { en: '🏡 Same Hobli', kn: '🏡 ಅದೇ ಹೋಬಳಿ' },
    cropDemandDist: { en: '🌾 Crop Distribution & Competition', kn: '🌾 ಬೆಳೆಗಳ ಹಂಚಿಕೆ ಮತ್ತು ಸ್ಪರ್ಧೆ' },
    farmers: { en: 'farmers', kn: 'ರೈತರು' },
    yieldAcre: { en: 'Yield/Acre', kn: 'ಇಳುವರಿ/ಎಕರೆ' },
    profitAcre: { en: 'Profit/Acre', kn: 'ಲಾಭ/ಎಕರೆ' },
    individualNeighbours: { en: '👥 Individual Neighbour Details', kn: '👥 ಪ್ರತ್ಯೇಕ ನೆರೆಹೊರೆಯ ರೈತರ ವಿವರಗಳು' },
    neighbourDetailsSub: { en: 'Latest year planting and performance data from nearby farmers', kn: 'ಸಮೀಪದ ರೈತರ ಇತ್ತೀಚಿನ ಕೃಷಿ ಇಳುವರಿ ಮತ್ತು ಲಾಭದ ಮಾಹಿತಿ' },
    compareWithRecommendations: { en: 'Compare with Your Recommended Varieties', kn: 'ನಿಮ್ಮ ಶಿಫಾರಸು ಮಾಡಿದ ತಳಿಗಳೊಂದಿಗೆ ಹೋಲಿಕೆ' },
    compareRecommendationsSub: { en: 'Compare varieties recommended for your soil and climate with what neighbouring farmers achieved', kn: 'ನಿಮ್ಮ ಮಣ್ಣು ಮತ್ತು ಹವಾಮಾನಕ್ಕೆ ಶಿಫಾರಸು ಮಾಡಲಾದ ಬೆಳೆ ತಳಿಗಳನ್ನು ಸಮೀಪದ ರೈತರ ಸಾಧನೆಯೊಂದಿಗೆ ಹೋಲಿಕೆ ಮಾಡಿ' },
    recommendedForYou: { en: 'Recommended for You', kn: 'ನಿಮಗೆ ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ' },
    varietiesPlanted: { en: 'Varieties Planted', kn: 'ಬೆಳೆದ ತಳಿಗಳು' },
    neighbourYield: { en: 'Neighbour Avg Yield', kn: 'ನೆರೆಹೊರೆಯವರ ಸರಾಸರಿ ಇಳುವರಿ' },
    marketPrice: { en: 'Market Price', kn: 'ಮಾರುಕಟ್ಟೆ ಬೆಲೆ' },
    soilConditions: { en: 'Soil Conditions', kn: 'ಮಣ್ಣಿನ ಸ್ಥಿತಿ' },
    verifiedFarmerData: { en: 'Verified Local Farmer Records', kn: 'ದೃಢೀಕರಿಸಲ್ಪಟ್ಟ ಸ್ಥಳೀಯ ರೈತರ ದಾಖಲೆ' },
    demoSimulationData: { en: 'Demo Data (Agro-Climatic Baseline)', kn: 'ಡೆಮೊ ಮಾಹಿತಿ (ಕೃಷಿ ಹವಾಮಾನ ಮಾದರಿ)' },
    viewInNeighbours: { en: 'Compare in Neighbours Tab', kn: 'ನೆರೆಹೊರೆಯವರ ಪುಟದಲ್ಲಿ ಹೋಲಿಸಿ' },
    exploreVarieties: { en: 'Explore Varieties', kn: 'ತಳಿಗಳನ್ನು ನೋಡಿ' },
    farmersGrowing: { en: 'farmers growing this', kn: 'ರೈತರು ಬೆಳೆಯುತ್ತಿದ್ದಾರೆ' },
    recommendedVariety: { en: 'Recommended Variety', kn: 'ಶಿಫಾರಸು ಮಾಡಿದ ತಳಿ' },
    adoptionLevel: { en: 'Adoption Level', kn: 'ಬೆಳೆಯುತ್ತಿರುವ ಪ್ರಮಾಣ' },
    nicheOpportunity: { en: 'High Opportunity (Low local competition)', kn: 'ಉತ್ತಮ ಅವಕಾಶ (ಕಡಿಮೆ ಸ್ಥಳೀಯ ಸ್ಪರ್ಧೆ)' },
    highCompetition: { en: 'High Competition (Commonly grown)', kn: 'ಹೆಚ್ಚು ಬೆಳೆಯುತ್ತಿರುವ ಬೆಳೆ (ಹೆಚ್ಚು ಸ್ಪರ್ಧೆ)' },
    balancedAdoption: { en: 'Balanced Local Demand', kn: 'ಸಮತೋಲಿತ ಸ್ಥಳೀಯ ಬೇಡಿಕೆ' },

    // My Farm History
    farmHistoryTitle: { en: '📊 My Farm Performance History', kn: '📊 ನನ್ನ ಹೊಲದ ಸಾಪ್ತಾಹಿಕ/ವಾರ್ಷಿಕ ಪ್ರಗತಿ' },
    farmerID: { en: 'Farmer ID:', kn: 'ರೈತ ಐಡಿ:' },
    primaryCrop: { en: 'Primary Crop', kn: 'ಮುಖ್ಯ ಬೆಳೆ' },
    annualYieldTrend: { en: '📈 Annual Yield Trend', kn: '📈 ವಾರ್ಷಿಕ ಇಳುವರಿ ಪ್ರವೃತ್ತಿ' },
    annualProfitTrend: { en: '💰 Annual Net Profit Trend', kn: '💰 ವಾರ್ಷಿಕ ನಿವ್ವಳ ಲಾಭ' },
    performanceNote: { en: '🌟 Performance Note:', kn: '🌟 ಪ್ರಗತಿಯ ವಿವರಣೆ:' },

    // Weather/Soil Details
    soilMoisture: { en: 'Soil Moisture', kn: 'ಮಣ್ಣಿನ ತೇವಾಂಶ' },
    soilTemp: { en: 'Soil Temp', kn: 'ಮಣ್ಣಿನ ತಾಪಮಾನ' },
    rainToday: { en: 'Rain Today', kn: 'ಇಂದಿನ ಮಳೆ' },
    rainCurrent: { en: 'Current Rain', kn: 'ಪ್ರಸ್ತುತ ಮಳೆ' },
    rainAnnual: { en: 'Avg. Annual Rainfall', kn: 'ಸರಾಸರಿ ವಾರ್ಷಿಕ ಮಳೆ' },

    // Bhoomi Map
    bhoomiMapTitle: { en: '🗺️ Bhoomi RTC Land Boundary Map', kn: '🗺️ ಭೂಮಿ ಆರ್.ಟಿ.ಸಿ ಜಮೀನು ನಕ್ಷೆ' },
    bhoomiMapDesc: { en: 'Interactive cadastral map from Karnataka Bhoomi Portal showing survey boundaries of your farm and neighboring plots.', kn: 'ಕರ್ನಾಟಕ ಭೂಮಿ ಪೋರ್ಟಲ್‌ನಿಂದ ನಿಮ್ಮ ಮತ್ತು ನೆರೆಹೊರೆಯ ಜಮೀನಿನ ಗಡಿ ಮತ್ತು ಆರ್.ಟಿ.ಸಿ ವಿವರಗಳನ್ನು ತೋರಿಸುವ ಸಂವಾದಾತ್ಮಕ ನಕ್ಷೆ.' },
    bhoomiRtcTitle: { en: 'BHOOMI LAND RTC RECORD', kn: 'ಭೂಮಿ ಜಮೀನು ಆರ್.ಟಿ.ಸಿ ದಾಖಲೆ' },
    bhoomiGovt: { en: 'Government of Karnataka', kn: 'ಕರ್ನಾಟಕ ಸರ್ಕಾರ' },
    ownerNameLabel: { en: 'Land Owner Name', kn: 'ಭೂಮಾಲೀಕರ ಹೆಸರು' },
    landClassLabel: { en: 'Land Classification', kn: 'ಜಮೀನು ವರ್ಗೀಕರಣ' },
    cropGrownLabel: { en: 'Active Crop Grown', kn: 'ಬೆಳೆಸಿದ ಬೆಳೆ' },
    soilTypeLabel: { en: 'Soil Type', kn: 'ಮಣ್ಣಿನ ಪ್ರಕಾರ' },
    areaLabel: { en: 'Land Extent', kn: 'ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ' },
    userLandHighlight: { en: 'Your Land (Center)', kn: 'ನಿಮ್ಮ ಜಮೀನು (ಕೇಂದ್ರ)' },
    clickLandParcel: { en: '💡 Click on any land parcel to view its official Bhoomi RTC land record.', kn: '💡 ಅಧಿಕೃತ ಭೂಮಿ ಆರ್.ಟಿ.ಸಿ ದಾಖಲೆಯನ್ನು ನೋಡಲು ಯಾವುದೇ ಜಮೀನಿನ ಮೇಲೆ ಕ್ಲಿಕ್ ಮಾಡಿ.' },
    villageLabel: { en: 'Village', kn: 'ಗ್ರಾಮ' },
    surveyNoLabel: { en: 'Survey No', kn: 'ಸರ್ವೇ ಸಂಖ್ಯೆ' },
    hissaNoLabel: { en: 'Hissa/Partition No', kn: 'ಹಿಸ್ಸಾ ಸಂಖ್ಯೆ' },
    fallowStatus: { en: 'Uncultivated / Fallow Land', kn: 'ಖಾಲಿ / ಬೀಳು ಜಮೀನು' },
    statusLabel: { en: 'Land Status', kn: 'ಸ್ಥಿತಿ' },
    recommendedCropsLabel: { en: 'Suggested Crops', kn: 'ಸೂಚಿಸಲಾದ ಬೆಳೆಗಳು' },
    suggestedWorkLabel: { en: 'Suggested Work', kn: 'ಸೂಚಿಸಲಾದ ಕೆಲಸಗಳು' },
    fallowLegend: { en: 'Fallow / Empty Land', kn: 'ಬೀಳು ಜಮೀನು' },

    // Crop Species & Varieties
    cropSpeciesTitle: { en: 'Recommended Varieties', kn: 'ಶಿಫಾರಸು ಮಾಡಿದ ತಳಿಗಳು' },
    cropSpeciesSubtitle: { en: 'Authentic cultivars adapted to local soil, climate, and rainfall conditions.', kn: 'ಸ್ಥಳೀಯ ಮಣ್ಣು, ಹವಾಮಾನ ಮತ್ತು ಮಳೆಯ ಪರಿಸ್ಥಿತಿಗಳಿಗೆ ಹೊಂದಿಕೊಳ್ಳುವ ಅಧಿಕೃತ ತಳಿಗಳು.' },
    viewSpecies: { en: 'View Varieties', kn: 'ತಳಿಗಳನ್ನು ನೋಡಿ' },
    hideSpecies: { en: 'Hide Varieties', kn: 'ತಳಿಗಳನ್ನು ಮರೆಮಾಡಿ' },
    varietyCultivar: { en: 'Variety', kn: 'ತಳಿ' },
    scientificName: { en: 'Botanical Name', kn: 'ಸಸ್ಯಶಾಸ್ತ್ರೀಯ ಹೆಸರು' },
    pricePerUnit: { en: 'Market Rate', kn: 'ಮಾರುಕಟ್ಟೆ ದರ' },
    duration: { en: 'Duration', kn: 'ಬೆಳೆಯುವ ಅವಧಿ' },
    days: { en: 'days', kn: 'ದಿನಗಳು' },
    expectedYield: { en: 'Expected Yield', kn: 'ನಿರೀಕ್ಷಿತ ಇಳುವರಿ' },
    season: { en: 'Season', kn: 'ಋತುಮಾನ' },
    characteristics: { en: 'Agronomic Notes', kn: 'ಕೃಷಿ ಮಾಹಿತಿ' },
    selectVarietyForProfit: { en: 'Use in Profit Estimator', kn: 'ಲಾಭದ ಅಂದಾಜಿನಲ್ಲಿ ಬಳಸಿ' },
    varietySelectorLabel: { en: 'Select Crop Variety', kn: 'ಬೆಳೆ ತಳಿಯನ್ನು ಆಯ್ಕೆಮಾಡಿ' },
    defaultVarietyOption: { en: 'Standard Regional Variety', kn: 'ಸಾಮಾನ್ಯ ಪ್ರಾದೇಶಿಕ ತಳಿ' },
    varietyDetailsBadge: { en: 'Selected Variety', kn: 'ಆಯ್ಕೆಮಾಡಿದ ತಳಿ' },
    priceRangeLabel: { en: 'Rate Range', kn: 'ದರ ಶ್ರೇಣಿ' },
    varietiesAvailable: { en: 'verified varieties', kn: 'ದೃಢೀಕರಿಸಿದ ತಳಿಗಳು' },
    soilRequirements: { en: 'Soil Type & pH', kn: 'ಮಣ್ಣಿನ ಪ್ರಕಾರ ಮತ್ತು ಪಿ.ಎಚ್' },
    climateRequirements: { en: 'Temperature & Rainfall', kn: 'ತಾಪಮಾನ ಮತ್ತು ಮಳೆ' },
    growingSeason: { en: 'Recommended Season', kn: 'ಸೂಕ್ತ ಋತುಮಾನ' },
    maturityPeriod: { en: 'Days to Maturity', kn: 'ಕಟಾವಿಗೆ ಬೇಕಾಗುವ ದಿನಗಳು' },
    expectedYieldLabel: { en: 'Expected Yield', kn: 'ನಿರೀಕ್ಷಿತ ಇಳುವರಿ' },
    suitabilityMatch: { en: 'Condition Match', kn: 'ಹೊಂದಾಣಿಕೆ ಪ್ರಮಾಣ' },
    highlyRecommended: { en: 'Recommended Cultivar', kn: 'ಶಿಫಾರಸು ಮಾಡಿದ ತಳಿ' },
    suitableBadge: { en: 'Suitable', kn: 'ಸೂಕ್ತವಾಗಿದೆ' },
    moderateBadge: { en: 'Moderate', kn: 'ಮಧ್ಯಮ' },
    bestForYourLand: { en: 'Top Recommended Variety', kn: 'ಅತ್ಯಂತ ಸೂಕ್ತವಾದ ತಳಿ' },
    topVarietiesLabel: { en: 'Recommended Cultivars', kn: 'ಶಿಫಾರಸು ಮಾಡಿದ ತಳಿಗಳು' },
    exploreVarietiesBtn: { en: 'All Varieties', kn: 'ಎಲ್ಲಾ ತಳಿಗಳು' },
    filterAllSeason: { en: 'All Seasons', kn: 'ಎಲ್ಲಾ ಋತುಗಳು' },
    filterKharif: { en: 'Kharif', kn: 'ಖಾರೀಫ್' },
    filterRabi: { en: 'Rabi', kn: 'ರಬಿ' },
    filterSummer: { en: 'Summer', kn: 'ಬೇಸಿಗೆ' },
    sortByMatch: { en: 'Best Match', kn: 'ಉತ್ತಮ ಹೊಂದಾಣಿಕೆ' },
    sortByYield: { en: 'Highest Yield', kn: 'ಗರಿಷ್ಠ ಇಳುವರಿ' },
    sortByPrice: { en: 'Market Rate', kn: 'ಮಾರುಕಟ್ಟೆ ದರ' },
    sortByDuration: { en: 'Maturity (Shortest)', kn: 'ಕಡಿಮೆ ಅವಧಿ' },
    closeModal: { en: 'Close', kn: 'ಮುಚ್ಚಿ' },
    bestRegionsLabel: { en: 'Adapted Districts', kn: 'ಹೊಂದಿಕೊಳ್ಳುವ ಜಿಲ್ಲೆಗಳು' },
    matchReasonsLabel: { en: 'Agronomic Fit', kn: 'ಕೃಷಿ ಸೂಕ್ತತೆ' },
    modalTitle: { en: 'Crop Varieties & Cultivars', kn: 'ಬೆಳೆ ತಳಿಗಳು ಮತ್ತು ಪ್ರಭೇದಗಳು' },

    // WhatsApp & SMS Alerts Section
    alertsHeroTitle: { en: 'Daily APMC Mandi Price Alerts via WhatsApp & SMS', kn: 'ವಾಟ್ಸಾಪ್ ಮತ್ತು ಎಸ್‌ಎಂಎಸ್ ಮೂಲಕ ದಿನನಿತ್ಯದ ಎಪಿಎಂಸಿ ದರ ಎಚ್ಚರಿಕೆ' },
    alertsHeroDesc: { en: 'Receive authentic live modal rates, price surge spikes, and harvest marketing advice directly sent to your registered mobile number.', kn: 'ನಿಮ್ಮ ನೋಂದಾಯಿತ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಗೆ ಪ್ರತಿದಿನ ಬೆಳಿಗ್ಗೆ ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆ ದರಗಳು, ಬೆಲೆ ಏರಿಕೆ ಮಾಹಿತಿ ಮತ್ತು ಮಾರಾಟ ಸಲಹೆಗಳನ್ನು ನೇರವಾಗಿ ಪಡೆಯಿರಿ.' },
    registeredMobile: { en: 'Registered Phone Number', kn: 'ನೋಂದಾಯಿತ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ' },
    currentlyTrackingCrop: { en: 'Monitored Crop', kn: 'ಮೇಲ್ವಿಚಾರಣೆ ಮಾಡಲಾಗುತ್ತಿರುವ ಬೆಳೆ' },
    mandiCenter: { en: 'Primary APMC Yard', kn: 'ಮುಖ್ಯ ಎಪಿಎಂಸಿ ಮಾರುಕಟ್ಟೆ' },
    channelPreferences: { en: 'Notification Channels', kn: 'ಮಾಹಿತಿ ಸ್ವೀಕರಿಸುವ ಮಾಧ್ಯಮ' },
    whatsappChannel: { en: 'WhatsApp Daily Bulletin (7:00 AM)', kn: 'ವಾಟ್ಸಾಪ್ ದೈನಂದಿನ ವರದಿ (ಬೆಳಿಗ್ಗೆ ೭:೦೦)' },
    smsChannel: { en: 'High Price Surge Alerts via SMS', kn: 'ತ್ವರಿತ ಬೆಲೆ ಏರಿಕೆ SMS ಎಚ್ಚರಿಕೆ' },
    sendTestAlert: { en: '🚀 Send Test Alert to Phone', kn: '🚀 ಪರೀಕ್ಷಾರ್ಥ ಎಚ್ಚರಿಕೆಯನ್ನು ಕಳುಹಿಸಿ' },
    sendingAlert: { en: 'Transmitting via Telecom Gateway...', kn: 'ಟೆಲಿಕಾಂ ಗೇಟ್‌ವೇ ಮೂಲಕ ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ...' },
    shareToWhatsapp: { en: 'Open in WhatsApp', kn: 'ವಾಟ್ಸಾಪ್‌ನಲ್ಲಿ ತೆರೆಯಿರಿ' },
    copyAlertText: { en: 'Copy Message', kn: 'ಸಂದೇಶ ನಕಲಿಸಿ' },
    copied: { en: 'Copied to Clipboard!', kn: 'ನಕಲಿಸಲಾಗಿದೆ!' },
    deliverySimulatedSuccess: { en: 'Alert Dispatched Successfully! Delivered via Official Carrier Hub', kn: 'ಎಚ್ಚರಿಕೆಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಕಳುಹಿಸಲಾಗಿದೆ! ಟೆಲಿಕಾಂ ಗೇಟ್‌ವೇ ಮೂಲಕ ತಲುಪಿದೆ' },
    frequencyDaily: { en: 'Daily Morning (7:00 AM)', kn: 'ಪ್ರತಿದಿನ ಬೆಳಿಗ್ಗೆ (೭:೦೦)' },
    frequencySurge: { en: 'Price Surge Spike Only (+3%)', kn: 'ಬೆಲೆ ಏರಿಕೆಯಾದಾಗ ಮಾತ್ರ (+೩%)' },
    frequencyWeekly: { en: 'Weekly Market Digest', kn: 'ವಾರಕ್ಕೊಮ್ಮೆ ಸಾರಾಂಶ' },
    alertTypeDaily: { en: 'Daily Mandi Opening Rate', kn: 'ದೈನಂದಿನ ಮಾರುಕಟ್ಟೆ ಆರಂಭಿಕ ದರ' },
    alertTypeSurge: { en: 'High Price Surge Spike Alert', kn: 'ಗರಿಷ್ಠ ಬೆಲೆ ಏರಿಕೆ ಎಚ್ಚರಿಕೆ' },
    alertTypeSelling: { en: 'Harvest Window Selling Advisory', kn: 'ಸುಗ್ಗಿ ಮಾರಾಟದ ಸೂಕ್ತ ಸಮಯ ಸಲಹೆ' },
    savePreferences: { en: 'Save Notification Preferences', kn: 'ಮಾಹಿತಿ ಆಯ್ಕೆಗಳನ್ನು ಉಳಿಸಿ' },
    preferencesSaved: { en: 'Preferences Saved Successfully!', kn: 'ಆಯ್ಕೆಗಳನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಉಳಿಸಲಾಗಿದೆ!' },
    liveSimulatedBadge: { en: 'Official APMC Gateway Simulation', kn: 'ಅಧಿಕೃತ ಎಪಿಎಂಸಿ ಗೇಟ್‌ವೇ ಸಿಮ್ಯುಲೇಶನ್' }
};

export const getCropName = (crop: string, lang: Language): string => {
    const item = cropTranslations[crop];
    if (!item) return crop;
    return lang === 'kn' ? item.kn : item.en;
};

export const getSoilName = (soil: string, lang: Language): string => {
    const item = soilTranslations[soil];
    if (!item) return soil;
    return lang === 'kn' ? item.kn : item.en;
};

export const getWeatherDesc = (desc: string, lang: Language): string => {
    const key = desc.toLowerCase();
    const item = weatherTranslations[key];
    if (!item) return desc;
    return lang === 'kn' ? item.kn : item.en;
};

export const t = (key: string, lang: Language): string => {
    const item = uiTranslations[key];
    if (!item) return key;
    return lang === 'kn' ? item.kn : item.en;
};
