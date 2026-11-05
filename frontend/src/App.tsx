import React, { useState, useEffect } from 'react';
import './App.css';
import 'leaflet/dist/leaflet.css';
import { MapContainer, TileLayer, Polygon, Popup, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import {
    indiaStates,
    getDistrictsForState,
    getTaluksForDistrict,
    getHoblisForTaluk
} from './data/locations';
import { type Language, getCropName, t, getSoilName, getWeatherDesc } from './data/translations';

// Fix Leaflet default icon issues in React
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});
interface CropPrice {
    crop: string;
    price: string;
    trend: 'up' | 'down' | 'stable';
}

interface WeatherData {
    temperature: number;
    humidity: number;
    rainfall: number;
    rain_today?: number;
    rain_current: number;
    description: string;
    location: string;
    source: string;
}

interface SoilData {
    ph: number;
    soil_type: string;
    temperature?: number;
    moisture?: number;
}

interface CropVariety {
    name: string;
    scientific_species?: string;
    price: number;
    price_display?: string;
    season: string;
    duration_days: number;
    maturity_period?: string;
    yield_per_acre: number;
    expected_yield?: string;
    characteristics?: string;
    soil_type?: string;
    soil_ph_range?: [number, number];
    min_temp?: number;
    max_temp?: number;
    rainfall_range?: [number, number];
    climate?: string;
    growing_months?: string;
    best_regions?: string[];
    image_url?: string;
    suitability_score?: number;
    suitability_level?: string;
    suitability_color?: string;
    suitability_badge?: string;
    match_highlights?: string[];
}

interface CropSpeciesData {
    crop: string;
    unit: string;
    botanical_genus?: string;
    crop_image?: string;
    varieties_count: number;
    price_range?: { min: number; max: number; unit: string; display: string };
    varieties: CropVariety[];
}

interface ProfitEstimate {
    crop: string;
    variety?: string | null;
    variety_details?: CropVariety | null;
    available_varieties?: string[];
    land_acres: number;
    land_guntas: number;
    survey_number: string;
    yield_per_acre: number;
    yield_unit: string;
    estimated_total_yield: number;
    current_price_per_unit: number;
    price_display: string;
    estimated_revenue: number;
    estimated_input_cost: number;
    estimated_profit: number;
    profit_per_acre: number;
    trend: string;
    price_history_5yr: { year: number; avg_price: number }[];
}

function App() {
    const [isRegistered, setIsRegistered] = useState(false);
    const [lang, setLang] = useState<Language>('en');

    // Form States
    const [name, setName] = useState('');
    const [currentCrop, setCurrentCrop] = useState('Rice');
    const [surveyNumber, setSurveyNumber] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [stateLoc, setStateLoc] = useState('Karnataka');
    const [district, setDistrict] = useState('Uttara Kannada');
    const [taluk, setTaluk] = useState('Karwar');
    const [hobli, setHobli] = useState('Karwar Kasaba');
    const [landAcres, setLandAcres] = useState('');
    const [landGuntas, setLandGuntas] = useState('');

    const [taluksList, setTaluksList] = useState<string[]>(getTaluksForDistrict('Uttara Kannada'));
    const [hoblisList, setHoblisList] = useState<string[]>(getHoblisForTaluk('Karwar'));
    const [loadingRegister, setLoadingRegister] = useState(false);

    // Auth States
    const [isLoginMode, setIsLoginMode] = useState(true);
    const [loginName, setLoginName] = useState('');
    const [loginPassword, setLoginPassword] = useState('');
    const [regPassword, setRegPassword] = useState('');
    const [loadingLogin, setLoadingLogin] = useState(false);

    // Dashboard States
    const [registeredUser, setRegisteredUser] = useState<{
        name: string,
        taluk: string,
        district: string,
        state?: string,
        hobli?: string,
        current_crop?: string,
        primary_crop?: string,
        survey_number: string,
        phone_number?: string,
        land_area_acres?: number,
        land_area_guntas?: number
    } | null>(null);
    const [recommendations, setRecommendations] = useState<any>(null);
    const [marketPrices, setMarketPrices] = useState<CropPrice[]>([]);

    // Weather & Soil States
    const [weatherData, setWeatherData] = useState<WeatherData | null>(null);
    const [soilData, setSoilData] = useState<SoilData | null>(null);
    const [loadingWeather, setLoadingWeather] = useState(false);

    // Crop Recommendation States
    const [showCropResults, setShowCropResults] = useState(false);
    const [loadingCropRec, setLoadingCropRec] = useState(false);

    // Market Rate States
    const [selectedCrop, setSelectedCrop] = useState('');
    const [selectedMarketResult, setSelectedMarketResult] = useState<CropPrice | null>(null);
    const [showMarketResult, setShowMarketResult] = useState(false);
    const [loadingMarket, setLoadingMarket] = useState(false);

    // Profit Calculator States
    const [showProfitCalc, setShowProfitCalc] = useState(false);
    const [profitEstimate, setProfitEstimate] = useState<ProfitEstimate | null>(null);
    const [loadingProfit, setLoadingProfit] = useState(false);
    const [calcSurveyNumber, setCalcSurveyNumber] = useState('');
    const [calcAcres, setCalcAcres] = useState('');
    const [calcGuntas, setCalcGuntas] = useState('');

    // Crop Species & Varieties States
    const [selectedVariety, setSelectedVariety] = useState<string>('');
    const [expandedSpeciesCrop, setExpandedSpeciesCrop] = useState<string | null>(null);
    const [speciesDataMap, setSpeciesDataMap] = useState<Record<string, CropSpeciesData>>({});
    const [loadingSpeciesCrop, setLoadingSpeciesCrop] = useState<string | null>(null);

    // Variety Showcase Modal States
    const [varietyModalCrop, setVarietyModalCrop] = useState<string | null>(null);
    const [varietyModalData, setVarietyModalData] = useState<CropSpeciesData | null>(null);
    const [loadingVarietyModal, setLoadingVarietyModal] = useState<boolean>(false);
    const [varietyFilterSeason, setVarietyFilterSeason] = useState<string>('all');
    const [varietySortBy, setVarietySortBy] = useState<string>('match');
    const [varietySearchQuery, setVarietySearchQuery] = useState<string>('');

    const openVarietyModal = async (cropName: string) => {
        if (!cropName) return;
        setVarietyModalCrop(cropName);
        setVarietyFilterSeason('all');
        setVarietySortBy('match');
        setVarietySearchQuery('');
        setLoadingVarietyModal(true);

        const currentTaluk = registeredUser?.taluk || 'Mangaluru';
        const currentDistrict = registeredUser?.district || '';
        const currentPh = soilData?.ph || recommendations?.soil_data?.ph || 6.0;
        const currentTemp = weatherData?.temperature || recommendations?.soil_data?.temp || 28.0;
        const currentRain = weatherData?.rainfall || recommendations?.soil_data?.rainfall || 2000;
        const currentSoil = soilData?.soil_type || recommendations?.soil_data?.soil_type || '';

        try {
            const params = new URLSearchParams();
            if (currentTaluk) params.append('taluk', currentTaluk);
            if (currentDistrict) params.append('district', currentDistrict);
            if (currentPh) params.append('ph', String(currentPh));
            if (currentTemp) params.append('temp', String(currentTemp));
            if (currentRain) params.append('rainfall', String(currentRain));
            if (currentSoil) params.append('soil_type', currentSoil);

            const res = await fetch(`http://localhost:8000/crop-varieties/${encodeURIComponent(cropName)}?${params.toString()}`);
            if (res.ok) {
                const data: CropSpeciesData = await res.json();
                setVarietyModalData(data);
                setSpeciesDataMap(prev => ({ ...prev, [cropName]: data }));
            }
        } catch (e) {
            console.error("Error fetching varieties for modal", e);
        } finally {
            setLoadingVarietyModal(false);
        }
    };

    const fetchCropSpecies = async (cropName: string) => {
        if (!cropName) return null;
        if (speciesDataMap[cropName]) return speciesDataMap[cropName];
        setLoadingSpeciesCrop(cropName);
        try {
            const currentTaluk = registeredUser?.taluk || 'Mangaluru';
            const currentPh = soilData?.ph || recommendations?.soil_data?.ph || '';
            const currentTemp = weatherData?.temperature || recommendations?.soil_data?.temp || '';
            const currentRain = weatherData?.rainfall || recommendations?.soil_data?.rainfall || '';
            const currentSoil = soilData?.soil_type || recommendations?.soil_data?.soil_type || '';

            const params = new URLSearchParams();
            if (currentTaluk) params.append('taluk', currentTaluk);
            if (currentPh) params.append('ph', String(currentPh));
            if (currentTemp) params.append('temp', String(currentTemp));
            if (currentRain) params.append('rainfall', String(currentRain));
            if (currentSoil) params.append('soil_type', currentSoil);

            const res = await fetch(`http://localhost:8000/crop-varieties/${encodeURIComponent(cropName)}?${params.toString()}`);
            if (res.ok) {
                const data: CropSpeciesData = await res.json();
                setSpeciesDataMap(prev => ({ ...prev, [cropName]: data }));
                return data;
            }
        } catch (err) {
            console.error("Error fetching crop species", err);
        } finally {
            setLoadingSpeciesCrop(null);
        }
        return null;
    };

    // Live Market Prices State (data.gov.in)
    interface LiveMarketRecord {
        market: string;
        commodity: string;
        variety: string;
        grade: string;
        min_price: number;
        max_price: number;
        modal_price: number;
        arrival_date: string;
    }
    interface LiveMarketData {
        source: string;
        total: number;
        district: string;
        requested_district?: string;
        markets: Record<string, LiveMarketRecord[]>;
        commodities: string[];
        records: LiveMarketRecord[];
        message?: string;
    }
    const [liveMarketData, setLiveMarketData] = useState<LiveMarketData | null>(null);
    const [loadingLiveMarket, setLoadingLiveMarket] = useState(false);
    const [selectedDistrict, setSelectedDistrict] = useState('');

    // Farmer History States
    const [farmerHistory, setFarmerHistory] = useState<{ info: any, history: any[] } | null>(null);

    // Neighbour Planting States
    interface VarietyBreakdown {
        variety: string;
        farmers_count: number;
        farmer_names: string[];
        avg_yield: number;
        avg_profit: number;
        market_price_display: string;
        growing_season: string;
        soil_type: string;
        soil_ph?: number;
    }
    interface NeighbourFarmer {
        farmer_id: string;
        name: string;
        hobli: string;
        primary_crop: string;
        secondary_crop: string;
        variety?: string;
        variety_scientific?: string;
        growing_season?: string;
        duration_days?: number;
        market_price?: number;
        market_price_display?: string;
        expected_yield?: string;
        land_acres: number;
        land_guntas: number;
        soil_type: string;
        soil_ph?: number;
        latest_year: number;
        latest_yield: number;
        yield_unit: string;
        yield_per_acre: number;
        latest_profit: number;
        profit_per_acre: number;
        is_real_data?: boolean;
        data_source?: string;
        data_source_label?: string;
    }
    interface CropSummary {
        crop: string;
        farmer_count: number;
        percentage: number;
        total_land_acres: number;
        avg_yield_per_acre: number;
        avg_profit_per_acre: number;
        yield_unit: string;
        botanical_genus?: string;
        varieties_count?: number;
        price_range?: { min: number; max: number; unit: string; display: string };
        top_varieties?: CropVariety[];
        all_varieties?: CropVariety[];
        available_varieties?: string[];
        primary_season?: string;
        soil_requirements?: string;
        soil_ph_range?: [number, number];
        varieties_breakdown?: VarietyBreakdown[];
    }
    interface NeighbourData {
        neighbours: NeighbourFarmer[];
        crop_summary: CropSummary[];
        total_farmers: number;
        scope: string;
        scope_type: string;
        available_hoblis: string[];
        insight: string;
        is_real_data?: boolean;
        data_badge?: string;
        data_source_label?: string;
    }
    const [neighbourData, setNeighbourData] = useState<NeighbourData | null>(null);
    const [loadingNeighbours, setLoadingNeighbours] = useState(false);
    const [neighbourScope, setNeighbourScope] = useState<'taluk' | 'hobli'>('taluk');
    const [selectedNeighbourHobli, setSelectedNeighbourHobli] = useState('');
    const [selectedCropFilter, setSelectedCropFilter] = useState<string | null>(null);

    const [detectingLocation, setDetectingLocation] = useState(false);
    const [gpsActive, setGpsActive] = useState(false);
    const [gpsCoords, setGpsCoords] = useState<{lat: number, lon: number} | null>(null);

    interface BhoomiParcel {
        survey_number: string;
        owner_name: string;
        owner_name_kn: string;
        land_acres: number;
        land_guntas: number;
        land_type: string;
        land_type_kn: string;
        soil_type: string;
        soil_type_kn: string;
        crop_grown: string;
        crop_grown_kn: string;
        is_user: boolean;
        is_empty?: boolean;
        recommended_crops?: string[];
        suggested_work?: string;
        suggested_work_kn?: string;
        polygon: [number, number][];
    }

    interface BhoomiMapData {
        center: [number, number];
        parcels: BhoomiParcel[];
        taluk: string;
        hobli: string;
        district: string;
    }

    const [bhoomiMapData, setBhoomiMapData] = useState<BhoomiMapData | null>(null);
    const [loadingBhoomiMap, setLoadingBhoomiMap] = useState(false);

    // Auto-fit bounds controller for Bhoomi Map
    function MapController({ parcels, center }: { parcels: BhoomiParcel[]; center: [number, number] }) {
        const map = useMap();
        useEffect(() => {
            if (parcels && parcels.length > 0) {
                const allPoints: [number, number][] = [];
                parcels.forEach(p => {
                    if (p.polygon) {
                        p.polygon.forEach(pt => allPoints.push(pt));
                    }
                });
                if (allPoints.length > 0) {
                    const bounds = L.latLngBounds(allPoints);
                    map.fitBounds(bounds, { padding: [45, 45], maxZoom: 18 });
                }
            } else if (center) {
                map.setView(center, 16);
            }
        }, [parcels, center, map]);
        return null;
    }

    const [activeTab, setActiveTab] = useState<'recommendation' | 'prices' | 'neighbours' | 'history' | 'alerts'>('recommendation');
    const [showPassword, setShowPassword] = useState(false);
    const [showLoginPassword, setShowLoginPassword] = useState(false);

    // APMC WhatsApp & SMS Alerts State
    const [alertPreview, setAlertPreview] = useState<{
        phone_number: string;
        phone_display: string;
        farmer_name: string;
        crop: string;
        crop_kn: string;
        taluk: string;
        district: string;
        mandi_name: string;
        modal_price: number;
        unit: string;
        min_price: number;
        max_price: number;
        arrivals: number;
        trend: string;
        trend_dir: string;
        advisory_kn: string;
        advisory_en: string;
        timestamp: string;
        whatsapp_text: string;
        sms_text: string;
        whatsapp_share_url: string;
    } | null>(null);
    const [alertType, setAlertType] = useState<'daily_mandi' | 'price_surge' | 'selling_advice'>('daily_mandi');
    const [channelWhatsApp, setChannelWhatsApp] = useState<boolean>(true);
    const [channelSMS, setChannelSMS] = useState<boolean>(true);
    const [alertFrequency, setAlertFrequency] = useState<string>('daily_7am');
    const [sendingAlert, setSendingAlert] = useState<boolean>(false);
    const [alertDispatchResult, setAlertDispatchResult] = useState<{
        status: string;
        message: string;
        sms_id?: string;
        wa_id?: string;
        carrier?: string;
        time?: string;
    } | null>(null);
    const [alertCopied, setAlertCopied] = useState<boolean>(false);


    const availableCrops = ['Rice', 'Banana', 'Arecanut', 'Pepper', 'Cashew', 'Rubber', 'Coconut', 'Coffee', 'Cardamom', 'Ginger', 'Jowar', 'Cotton', 'Maize', 'Bengal Gram', 'Red Gram', 'Wheat', 'Pomegranate', 'Ragi', 'Groundnut', 'Sugarcane', 'Tomato', 'Mango', 'Onion', 'Potato', 'Turmeric', 'Chilli'];

    // Cascading logic
    useEffect(() => {
        setDistrict('');
        setTaluk('');
        setHobli('');
    }, [stateLoc]);

    useEffect(() => {
        if (district) {
            const list = getTaluksForDistrict(district);
            setTaluksList(list);
            // When updating district, we only clear taluk IF it's not actually valid for the new district.
            // This allows the auto-fill logic to set both simultaneously without conflict.
            if (taluk && !list.includes(taluk)) {
                setTaluk('');
            }
        } else {
            setTaluksList([]);
        }
    }, [district]);

    useEffect(() => {
        if (taluk) {
            const list = getHoblisForTaluk(taluk);
            setHoblisList(list);
            // Only clear hobli if it's not valid for the new taluk
            if (hobli && !list.includes(hobli)) {
                setHobli('');
            }
        } else {
            setHoblisList([]);
        }
    }, [taluk]);

    const fetchWeather = async (location: string) => {
        setLoadingWeather(true);
        try {
            let locQuery = location;
            // If GPS is active and we are loading the dashboard farmer location, pass coordinates
            if (gpsCoords && location === (registeredUser?.taluk || '')) {
                locQuery = `${gpsCoords.lat},${gpsCoords.lon}`;
            }
            const res = await fetch(`http://localhost:8000/weather/${encodeURIComponent(locQuery)}`);
            if (res.ok) {
                const data = await res.json();
                setWeatherData(data);
            }
        } catch (e) {
            console.error("Weather fetch failed", e);
        } finally {
            setLoadingWeather(false);
        }
    };

    const fetchSoilData = async (talukName?: string, districtName?: string) => {
        try {
            const query = new URLSearchParams();
            if (talukName) query.append("taluk", talukName);
            if (districtName) query.append("district", districtName);
            const res = await fetch(`http://localhost:8000/soil-data?${query.toString()}`);
            if (res.ok) setSoilData(await res.json());
        } catch (e) {
            console.error("Soil data fetch failed", e);
        }
    };

    const fetchMarketPrices = async () => {
        try {
            const res = await fetch('http://localhost:8000/market-prices');
            if (res.ok) setMarketPrices(await res.json());
        } catch (e) {
            console.error("Failed to fetch market prices", e);
        }
    };

    const fetchLiveMarketPrices = async (district: string) => {
        setLoadingLiveMarket(true);
        try {
            const url = district
                ? `http://localhost:8000/district-market-prices/${encodeURIComponent(district)}`
                : 'http://localhost:8000/market-prices-live';
            const res = await fetch(url);
            if (res.ok) setLiveMarketData(await res.json());
        } catch (e) {
            console.error("Failed to fetch live market prices", e);
        } finally {
            setLoadingLiveMarket(false);
        }
    };

    const fetchFarmerHistory = async (name: string, phone: string) => {
        try {
            const res = await fetch(`http://localhost:8000/farmer-lookup?name=${encodeURIComponent(name)}&phone=${encodeURIComponent(phone)}`);
            if (res.ok) {
                const data = await res.json();
                if (data.found) {
                    setFarmerHistory(data);
                    if (data.info?.survey_number) {
                        setCalcSurveyNumber(data.info.survey_number);
                    }
                    return data;
                } else {
                    setFarmerHistory(null);
                }
            }
        } catch (e) {
            console.error("Farmer history lookup failed", e);
        }
        return null;
    };

    const fetchBhoomiMapData = async (userTaluk: string, userHobli?: string, userCropOverride?: string) => {
        setLoadingBhoomiMap(true);
        try {
            const params = new URLSearchParams({
                taluk: userTaluk,
                user_name: registeredUser?.name || 'You',
                user_acres: (registeredUser?.land_area_acres ?? 2).toString(),
                user_guntas: (registeredUser?.land_area_guntas ?? 0).toString(),
                user_crop: userCropOverride || farmerHistory?.info?.primary_crop || registeredUser?.primary_crop || 'Rice',
                survey_number: calcSurveyNumber || registeredUser?.survey_number || farmerHistory?.info?.survey_number || '120'
            });
            if (userHobli) params.set('hobli', userHobli);
            if (gpsCoords) {
                params.set('lat', gpsCoords.lat.toString());
                params.set('lon', gpsCoords.lon.toString());
            }
            const res = await fetch(`http://localhost:8000/bhoomi/land-map?${params.toString()}`);
            if (res.ok) {
                const data = await res.json();
                setBhoomiMapData(data);
            }
        } catch (e) {
            console.error("Bhoomi map data fetch failed", e);
        } finally {
            setLoadingBhoomiMap(false);
        }
    };

    const fetchNeighbourData = async (userTaluk: string, hobli?: string, excludeName?: string, userCropOverride?: string) => {
        setLoadingNeighbours(true);
        try {
            let url = `http://localhost:8000/neighbour-planting/${encodeURIComponent(userTaluk)}`;
            const params = new URLSearchParams();
            if (hobli) params.set('hobli', hobli);
            if (excludeName) params.set('exclude_name', excludeName);
            if (params.toString()) url += `?${params.toString()}`;
            const res = await fetch(url);
            if (res.ok) {
                const data = await res.json();
                setNeighbourData(data);
                if (data.available_hoblis && data.available_hoblis.length > 0 && !selectedNeighbourHobli) {
                    setSelectedNeighbourHobli(data.available_hoblis[0]);
                }
            }
            // Sync Bhoomi map data
            await fetchBhoomiMapData(userTaluk, hobli, userCropOverride);
        } catch (e) {
            console.error("Neighbour data fetch failed", e);
        } finally {
            setLoadingNeighbours(false);
        }
    };

    const handleGPSDetect = (isDashboard: boolean = false) => {
        if (!navigator.geolocation) {
            alert("Geolocation is not supported by your browser");
            return;
        }

        setDetectingLocation(true);
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                setGpsCoords({ lat, lon });

                try {
                    const res = await fetch(`http://localhost:8000/reverse-geocode?lat=${lat}&lon=${lon}`);
                    if (res.ok) {
                        const data = await res.json();
                        if (data.status === "success" || data.status === "fallback") {
                            if (isDashboard) {
                                // Dynamically update active dashboard locations
                                setRegisteredUser(prev => prev ? {
                                    ...prev,
                                    district: data.district,
                                    taluk: data.taluk
                                } : null);
                                setGpsActive(true);

                                // Refetch location-specific dashboard elements
                                fetchWeather(data.taluk || data.district);
                                fetchSoilData(data.taluk, data.district);
                                setSelectedDistrict(data.district);
                                fetchLiveMarketPrices(data.district);
                                fetchNeighbourData(data.taluk, undefined, registeredUser?.name, farmerHistory?.info?.primary_crop);
                                alert(`📍 Location updated to ${data.taluk}, ${data.district} via GPS! Dashboard prediction updated.`);
                            } else {
                                // Auto-fill Registration Form
                                setStateLoc(data.state);
                                
                                // Manually load cascades to bypass select lifecycle lags
                                const taluks = getTaluksForDistrict(data.district);
                                setTaluksList(taluks);
                                const hoblis = getHoblisForTaluk(data.taluk);
                                setHoblisList(hoblis);
                                
                                setDistrict(data.district);
                                setTaluk(data.taluk);
                                setHobli(data.hobli);
                                alert(`📍 GPS auto-detected: ${data.hobli}, ${data.taluk}, ${data.district}, ${data.state}`);
                            }
                        } else {
                            alert("Failed to resolve address components from GPS coordinates.");
                        }
                    } else {
                        alert("Geocoding server error. Using dropdown selections.");
                    }
                } catch (err) {
                    console.error("GPS Reverse geocoding failed", err);
                    alert("Error communicating with geocoding API.");
                } finally {
                    setDetectingLocation(false);
                }
            },
            (error) => {
                setDetectingLocation(false);
                console.error("Geolocation error", error);
                let msg = "Failed to retrieve GPS location.";
                if (error.code === error.PERMISSION_DENIED) {
                    msg = "Location permission denied. Please allow location access in your browser settings.";
                }
                alert(msg);
            },
            { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
        );
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoadingRegister(true);
        try {
            const payload = {
                name, current_crop: currentCrop, survey_number: surveyNumber, phone_number: phoneNumber,
                state: stateLoc, district: district || 'N/A',
                taluk: taluk || 'N/A', hobli: hobli || 'N/A',
                password: regPassword,
                land_area_acres: parseFloat(landAcres) || 0,
                land_area_guntas: parseFloat(landGuntas) || 0
            };
            const response = await fetch('http://localhost:8000/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (response.ok) {
                alert("🌾 Registration successful! Welcome to the Farmer Community. Please login with your name or mobile.");
                setIsLoginMode(true);
                setLoginName(name);
                setRegPassword('');
            } else {
                alert("Registration failed. Please check your inputs.");
            }
        } catch (e) {
            console.error("Registration error", e);
            alert("Error connecting to server.");
        } finally {
            setLoadingRegister(false);
        }
    };

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoadingLogin(true);
        try {
            const response = await fetch('http://localhost:8000/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: loginName, password: loginPassword })
            });

            if (response.ok) {
                const data = await response.json();
                const user = data.user;
                setRegisteredUser(user);
                setIsRegistered(true);
                if (user.survey_number) {
                    setCalcSurveyNumber(user.survey_number);
                }

                // Fetch necessary data for dashboard
                fetchWeather(user.taluk || user.district || 'Mangalore');
                fetchSoilData(user.taluk, user.district);
                fetchMarketPrices();
                setSelectedDistrict(user.district || '');
                fetchLiveMarketPrices(user.district || '');
                const historyData = await fetchFarmerHistory(user.name, user.phone_number || '');
                const userCrop = historyData?.info?.primary_crop || 'Rice';
                fetchNeighbourData(user.taluk || 'Mangaluru', undefined, user.name, userCrop);
            } else {
                const err = await response.json();
                if (response.status === 404) {
                    alert("❌ Name not found. Please register first or check your spelling.");
                } else if (response.status === 401) {
                    alert("❌ Password incorrect. Please try again.");
                } else {
                    alert(err.detail || "Login failed. Please try again later.");
                }
            }
        } catch (e) {
            console.error("Login error", e);
            alert("Error connecting to server.");
        } finally {
            setLoadingLogin(false);
        }
    };

    const handleLogout = () => {
        setIsRegistered(false);
        setRegisteredUser(null);
        setLoginName('');
        setLoginPassword('');
    };

    // Synthesize notification audio chime using Web Audio API
    const playNotificationSound = () => {
        try {
            const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
            if (!AudioContextClass) return;
            const ctx = new AudioContextClass();
            const now = ctx.currentTime;
            
            // First chime tone
            const osc1 = ctx.createOscillator();
            const gain1 = ctx.createGain();
            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(587.33, now); // D5
            gain1.gain.setValueAtTime(0.18, now);
            gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
            osc1.connect(gain1);
            gain1.connect(ctx.destination);
            osc1.start(now);
            osc1.stop(now + 0.28);

            // Second higher tone
            const osc2 = ctx.createOscillator();
            const gain2 = ctx.createGain();
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(880, now + 0.12); // A5
            gain2.gain.setValueAtTime(0.20, now + 0.12);
            gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.48);
            osc2.connect(gain2);
            gain2.connect(ctx.destination);
            osc2.start(now + 0.12);
            osc2.stop(now + 0.48);
        } catch {
            // AudioContext may be restricted by browser until user gesture
        }
    };

    const fetchAlertPreview = async (selectedType = alertType) => {
        if (!registeredUser) return;
        try {
            const phone = registeredUser.phone_number || '9845112233';
            const crop = registeredUser.current_crop || registeredUser.primary_crop || 'Arecanut';
            const talukName = registeredUser.taluk || 'Sirsi';
            const distName = registeredUser.district || 'Uttara Kannada';
            const name = registeredUser.name || 'Farmer';

            const res = await fetch(`http://localhost:8000/alerts/preview?phone_number=${encodeURIComponent(phone)}&farmer_name=${encodeURIComponent(name)}&crop=${encodeURIComponent(crop)}&taluk=${encodeURIComponent(talukName)}&district=${encodeURIComponent(distName)}&alert_type=${selectedType}`);
            if (res.ok) {
                const data = await res.json();
                setAlertPreview(data);
            }
        } catch (err) {
            console.error('Error fetching alert preview:', err);
        }
    };

    const handleSendSimulation = async () => {
        if (!registeredUser) return;
        setSendingAlert(true);
        setAlertDispatchResult(null);

        const channel = (channelWhatsApp && channelSMS) ? 'both' : channelWhatsApp ? 'whatsapp' : 'sms';
        const phone = registeredUser.phone_number || '9845112233';
        const crop = registeredUser.current_crop || registeredUser.primary_crop || 'Arecanut';

        try {
            const res = await fetch('http://localhost:8000/alerts/send-simulation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    phone_number: phone,
                    farmer_name: registeredUser.name || 'Farmer',
                    crop: crop,
                    taluk: registeredUser.taluk || 'Sirsi',
                    district: registeredUser.district || 'Uttara Kannada',
                    channel: channel,
                    alert_type: alertType
                })
            });

            if (res.ok) {
                const data = await res.json();
                playNotificationSound();
                setAlertDispatchResult({
                    status: 'success',
                    message: data.message,
                    sms_id: data.sms_message_id,
                    wa_id: data.whatsapp_message_id,
                    carrier: data.carrier_route,
                    time: data.timestamp
                });
            }
        } catch (err) {
            console.error('Simulation error:', err);
        } finally {
            setSendingAlert(false);
        }
    };

    const handleCopyAlert = (text: string) => {
        navigator.clipboard.writeText(text);
        setAlertCopied(true);
        setTimeout(() => setAlertCopied(false), 2500);
    };

    const handleCropRecommendation = async () => {
        setLoadingCropRec(true);
        setShowCropResults(false);
        try {
            const userTaluk = registeredUser?.taluk || 'Unknown';
            const ph = soilData?.ph || 6.2;
            const temp = weatherData?.temperature || 28;
            const rainfall = weatherData?.rainfall || 3500;
            const humidity = weatherData?.humidity || 85;

            const res = await fetch(
                `http://localhost:8000/recommendations/${encodeURIComponent(userTaluk)}?ph=${ph}&temp=${temp}&rainfall=${rainfall}&humidity=${humidity}`
            );
            if (res.ok) {
                const data = await res.json();
                data.soil_data.humidity = weatherData?.humidity;
                data.soil_data.weather_description = weatherData?.description;
                data.soil_data.weather_source = weatherData?.source;
                setRecommendations(data);
                setShowCropResults(true);
            }
        } catch (e) {
            alert("Could not connect to the server.");
        } finally {
            setLoadingCropRec(false);
        }
    };

    const handleMarketPrediction = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoadingMarket(true);
        setShowMarketResult(false);
        try {
            const res = await fetch('http://localhost:8000/market-prices');
            if (res.ok) {
                const prices: CropPrice[] = await res.json();
                setMarketPrices(prices);
                const found = prices.find(p => p.crop === selectedCrop);
                setSelectedMarketResult(found || { crop: selectedCrop, price: 'N/A', trend: 'stable' });
                setShowMarketResult(true);
                // Also fetch all species/varieties and pricing for this particular crop
                if (selectedCrop) {
                    fetchCropSpecies(selectedCrop);
                }
            }
        } catch (e) {
            alert("Could not connect to the server.");
        } finally {
            setLoadingMarket(false);
        }
    };

    const handleProfitEstimate = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoadingProfit(true);
        try {
            const acresVal = calcAcres || (registeredUser?.land_area_acres ?? 0).toString();
            const guntasVal = calcGuntas || (registeredUser?.land_area_guntas ?? 0).toString();
            const surveyVal = calcSurveyNumber || '';
            const cropVal = selectedMarketResult?.crop || selectedCrop || 'Rice';
            const params = new URLSearchParams({
                crop: cropVal,
                acres: acresVal,
                guntas: guntasVal,
                survey_number: surveyVal,
                ...(selectedVariety ? { variety: selectedVariety } : {})
            });
            const res = await fetch(`http://localhost:8000/profit-estimate?${params}`);
            if (res.ok) {
                setProfitEstimate(await res.json());
                setShowProfitCalc(true);
            }
        } catch (e) {
            alert("Could not connect to the server.");
        } finally {
            setLoadingProfit(false);
        }
    };

    const resetCropResults = () => {
        setShowCropResults(false);
        setRecommendations(null);
        setExpandedSpeciesCrop(null);
    };

    const resetMarketForm = () => {
        setShowMarketResult(false);
        setShowProfitCalc(false);
        setSelectedCrop('');
        setSelectedVariety('');
        setSelectedMarketResult(null);
        setProfitEstimate(null);
    };

    const cropEmojis: Record<string, string> = {
        'Rice': '🌾', 'Banana': '🍌', 'Arecanut': '🌴',
        'Pepper': '🌶️', 'Cashew': '🥜', 'Rubber': '🌳',
        'Coconut': '🥥', 'Wheat': '🌾', 'Sugarcane': '🎋',
        'Cotton': '☁️', 'Coffee': '☕', 'Cardamom': '🌱',
        'Ginger': '🥔', 'Jowar': '🌾', 'Maize': '🌽',
        'Bengal Gram': '🥜', 'Red Gram': '🫘', 'Pomegranate': '🍎',
        'Ragi': '🌾', 'Groundnut': '🥜', 'Tomato': '🍅',
        'Mango': '🥭', 'Onion': '🧅', 'Potato': '🥔',
        'Turmeric': '🌿', 'Chilli': '🌶️'
    };

    const resolveCropImage = (cropName?: string, varietyImg?: string, cropImg?: string) => {
        const cLower = (cropName || '').toLowerCase();
        const vLower = (varietyImg || '').toLowerCase();
        const crLower = (cropImg || '').toLowerCase();
        const coconutKeywords = ['coconut', 'west coast tall', 'chowghat', 'tiptur tall', 'lakshadweep', 'gangabondam', 'kera sankara'];
        if (coconutKeywords.some(k => cLower.includes(k) || vLower.includes(k) || crLower.includes(k))) {
            return '/coconut.jpg';
        }
        return varietyImg || cropImg || 'https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=700&q=80';
    };

    if (!isRegistered) {
        return (
            <div className="registration-container">
                <header className="reg-header">
                    <div className="reg-brand-mark" style={{ fontSize: '2.5rem', marginBottom: '0.4rem' }}>🌱</div>
                    <div style={{ display: 'flex', justifyContent: 'center', margin: '0.65rem 0' }}>
                        <div className="lang-switcher">
                            <button className={lang === 'en' ? 'active' : ''} onClick={() => setLang('en')}>🇬🇧 English</button>
                            <button className={lang === 'kn' ? 'active' : ''} onClick={() => setLang('kn')}>🇮🇳 ಕನ್ನಡ</button>
                        </div>
                    </div>
                    <h1 className="reg-portal-title">{t('portalTitle', lang)}</h1>
                    <p className="reg-tagline">{t('portalSubtitle', lang)}</p>
                </header>

                <div className="registration-card glass">
                    <div className="auth-toggle">
                        <button
                            className={isLoginMode ? 'active' : ''}
                            onClick={() => setIsLoginMode(true)}
                        >
                            🔑 {t('login', lang)}
                        </button>
                        <button
                            className={!isLoginMode ? 'active' : ''}
                            onClick={() => setIsLoginMode(false)}
                        >
                            📝 {t('register', lang)}
                        </button>
                    </div>

                    {isLoginMode ? (
                        <div className="login-section">
                            <h2>{t('welcomeBack', lang)}</h2>
                            <p className="auth-subtitle">{t('loginSubtitle', lang)}</p>
                            <form onSubmit={handleLogin} className="input-form">
                                <div className="form-group">
                                    <label>{t('fullName', lang)}</label>
                                    <input
                                        type="text"
                                        placeholder={t('enterFullName', lang)}
                                        value={loginName}
                                        onChange={(e) => setLoginName(e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="form-group">
                                    <label>{t('password', lang)}</label>
                                    <div className="password-input-wrapper">
                                        <input
                                            type={showLoginPassword ? "text" : "password"}
                                            placeholder="••••••••"
                                            value={loginPassword}
                                            onChange={(e) => setLoginPassword(e.target.value)}
                                            required
                                        />
                                        <button
                                            type="button"
                                            className="toggle-password"
                                            onClick={() => setShowLoginPassword(!showLoginPassword)}
                                        >
                                            {showLoginPassword ? '👁️' : '👁️‍🗨️'}
                                        </button>
                                    </div>
                                </div>
                                <button type="submit" className="submit-btn" disabled={loadingLogin}>
                                    {loadingLogin ? <><span className="spinner"></span> {t('loggingIn', lang)}</> : `🔓 ${t('loginBtn', lang)}`}
                                </button>
                            </form>
                        </div>
                    ) : (
                        <div className="registration-section">
                            <h2>{t('joinCommunity', lang)}</h2>
                            <p className="auth-subtitle">{t('registerSubtitle', lang)}</p>
                            <form onSubmit={handleRegister} className="input-form">
                                <div className="form-group">
                                    <label>{t('fullName', lang)}</label>
                                    <input type="text" placeholder={t('enterFullName', lang)} value={name} onChange={(e) => setName(e.target.value)} required />
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>📱 {t('phoneNumber', lang)}</label>
                                        <input 
                                            type="tel" 
                                            placeholder={lang === 'kn' ? '10 ಅಂಕಿಯ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ' : '10-digit mobile number'} 
                                            value={phoneNumber} 
                                            onChange={(e) => setPhoneNumber(e.target.value.replace(/\D/g, '').slice(0, 10))} 
                                            required 
                                            pattern="\d{10}" 
                                            title="Please enter a valid 10-digit mobile number" 
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>🌱 {t('currentCropGrown', lang)}</label>
                                        <select value={currentCrop} onChange={(e) => setCurrentCrop(e.target.value)} required>
                                            <option value="Rice">🌾 {lang === 'kn' ? 'ಭತ್ತ / ಅಕ್ಕಿ (Rice)' : 'Rice (Paddy)'}</option>
                                            <option value="Arecanut">🌴 {lang === 'kn' ? 'ಅಡಿಕೆ (Arecanut)' : 'Arecanut'}</option>
                                            <option value="Coconut">🥥 {lang === 'kn' ? 'ತೆಂಗು (Coconut)' : 'Coconut'}</option>
                                            <option value="Banana">🍌 {lang === 'kn' ? 'ಬಾಳೆ (Banana)' : 'Banana'}</option>
                                            <option value="Pepper">🌿 {lang === 'kn' ? 'ಕಾಳುಮೆಣಸು (Black Pepper)' : 'Black Pepper'}</option>
                                            <option value="Coffee">☕ {lang === 'kn' ? 'ಕಾಫಿ (Coffee)' : 'Coffee'}</option>
                                            <option value="Cardamom">🌱 {lang === 'kn' ? 'ಏಲಕ್ಕಿ (Cardamom)' : 'Cardamom'}</option>
                                            <option value="Cashew">🥜 {lang === 'kn' ? 'ಗೋಡಂಬಿ (Cashew)' : 'Cashew'}</option>
                                            <option value="Rubber">🌳 {lang === 'kn' ? 'ರಬ್ಬರ್ (Rubber)' : 'Rubber'}</option>
                                            <option value="Sugarcane">🎋 {lang === 'kn' ? 'ಕಬ್ಬು (Sugarcane)' : 'Sugarcane'}</option>
                                            <option value="Maize">🌽 {lang === 'kn' ? 'ಮೆಕ್ಕೆಜೋಳ (Maize)' : 'Maize'}</option>
                                            <option value="Ragi">🌾 {lang === 'kn' ? 'ರಾಗಿ (Finger Millet)' : 'Ragi'}</option>
                                            <option value="Cotton">☁️ {lang === 'kn' ? 'ಹತ್ತಿ (Cotton)' : 'Cotton'}</option>
                                            <option value="Ginger">🫚 {lang === 'kn' ? 'ಶುಂಠಿ (Ginger)' : 'Ginger'}</option>
                                            <option value="Tomato">🍅 {lang === 'kn' ? 'ಟೊಮೆಟೊ (Tomato)' : 'Tomato'}</option>
                                            <option value="Groundnut">🥜 {lang === 'kn' ? 'ಶೇಂಗಾ (Groundnut)' : 'Groundnut'}</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>{t('state', lang)}</label>
                                        <select value={stateLoc} onChange={(e) => setStateLoc(e.target.value)} required>
                                            <option value="">{lang === 'kn' ? 'ರಾಜ್ಯ ಆಯ್ಕೆಮಾಡಿ' : 'Select State'}</option>
                                            {indiaStates.map(s => <option key={s} value={s}>{s}</option>)}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>{t('district', lang)}</label>
                                        <select value={district} onChange={(e) => setDistrict(e.target.value)} required disabled={!stateLoc}>
                                            <option value="">{t('selectDistrict', lang)}</option>
                                            {getDistrictsForState(stateLoc).map(d => <option key={d} value={d}>{d}</option>)}
                                        </select>
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>{t('taluk', lang)}</label>
                                        <select value={taluk} onChange={(e) => setTaluk(e.target.value)} required disabled={!district}>
                                            <option value="">{t('selectTaluk', lang)}</option>
                                            {taluksList.map(tk => <option key={tk} value={tk}>{tk}</option>)}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>{t('hobli', lang)}</label>
                                        <select value={hobli} onChange={(e) => setHobli(e.target.value)} required disabled={!taluk}>
                                            <option value="">{t('selectHobli', lang)}</option>
                                            {hoblisList.map(h => <option key={h} value={h}>{h}</option>)}
                                        </select>
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>{t('surveyNumber', lang)}</label>
                                        <input
                                            type="text"
                                            placeholder={lang === 'kn' ? 'ಉದಾ: 123/ಎ' : 'e.g. 123/A'}
                                            value={surveyNumber}
                                            onChange={(e) => setSurveyNumber(e.target.value)}
                                            required
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>{t('setPassword', lang)}</label>
                                        <div className="password-input-wrapper">
                                            <input
                                                type={showPassword ? "text" : "password"}
                                                placeholder={lang === 'kn' ? 'ಬಲವಾದ ಪಾಸ್‌ವರ್ಡ್ ಆಯ್ಕೆಮಾಡಿ' : 'Choose a strong password'}
                                                value={regPassword}
                                                onChange={(e) => setRegPassword(e.target.value)}
                                                required
                                            />
                                            <button
                                                type="button"
                                                className="toggle-password"
                                                onClick={() => setShowPassword(!showPassword)}
                                            >
                                                {showPassword ? '👁️' : '👁️‍🗨️'}
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label>{t('landAcres', lang)}</label>
                                        <input type="number" step="0.1" placeholder={lang === 'kn' ? 'ಉದಾ: 5.5' : 'e.g. 5.5'} value={landAcres} onChange={(e) => setLandAcres(e.target.value)} required />
                                    </div>
                                    <div className="form-group">
                                        <label>{t('landGuntas', lang)}</label>
                                        <input type="number" step="1" placeholder={lang === 'kn' ? 'ಉದಾ: 100' : 'e.g. 100'} value={landGuntas} onChange={(e) => setLandGuntas(e.target.value)} required />
                                    </div>
                                </div>

                                <button type="submit" className="submit-btn" disabled={loadingRegister}>
                                    {loadingRegister ? <><span className="spinner"></span> {t('registering', lang)}</> : `🌾 ${t('registerBtn', lang)}`}
                                </button>
                            </form>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <div className="gov-header-brand">
                    <span className="dashboard-brand-icon" style={{ fontSize: '1.8rem', lineHeight: 1, marginRight: '0.25rem' }}>🌱</span>
                    <div className="gov-brand-titles">
                        <h2 className="gov-portal-main-title">ರೈತ ಮಿತ್ರ — Raitha Mitra</h2>
                        <span className="gov-dept-sub">Integrated Agricultural Advisory & Market Intelligence</span>
                    </div>
                </div>
                <div className="user-info">
                    <h2>{t('welcomeUser', lang)} {registeredUser?.name || 'Farmer'}</h2>
                    <p>
                        📍 {registeredUser?.taluk}, {registeredUser?.district}
                        {registeredUser?.phone_number && (
                            <span> • 📱 {registeredUser.phone_number}</span>
                        )}
                        {(registeredUser?.current_crop || registeredUser?.primary_crop) && (
                            <span className="current-crop-badge">🌱 {t('currentCrop', lang)} <strong>{getCropName(registeredUser.current_crop || registeredUser.primary_crop || '', lang)}</strong></span>
                        )}
                        {gpsActive && <span className="gps-active-badge">📍 GPS Live {gpsCoords ? `(${gpsCoords.lat.toFixed(4)}, ${gpsCoords.lon.toFixed(4)})` : ''}</span>}
                        <button className="alerts-shortcut-pill" onClick={() => {
                            setActiveTab('alerts');
                            fetchAlertPreview(alertType);
                        }}>
                            <span className="live-pulse-dot"></span> 📲 {t('marketAlertsBtn', lang)}
                        </button>
                    </p>
                    {registeredUser?.land_area_acres && (
                        <p className="user-land-info">📐 {t('registeredLand', lang)} {registeredUser.land_area_acres} {t('acres', lang)}, {registeredUser.land_area_guntas} {t('guntas', lang)}</p>
                    )}
                    {weatherData && (
                        <div className="weather-pill-bar">
                            <div className="weather-pill-item">
                                <span>🌤️</span>
                                <span>{getWeatherDesc(weatherData.description, lang)}</span>
                            </div>
                            <div className="weather-pill-item">
                                <span>🌡️</span>
                                <span>{t('temperature', lang)}:</span>
                                <span className="weather-pill-val">{weatherData.temperature}°C</span>
                            </div>
                            <div className="weather-pill-item">
                                <span>💧</span>
                                <span>{t('humidity', lang)}:</span>
                                <span className="weather-pill-val">{weatherData.humidity}%</span>
                            </div>
                            {soilData && (
                                <div className="weather-pill-item">
                                    <span>💦</span>
                                    <span>{t('soilMoisture', lang)}:</span>
                                    <span className="weather-pill-val">{soilData.moisture}% VWC</span>
                                </div>
                            )}
                        </div>
                    )}
                </div>
                <div className="user-profile">
                    <div className="lang-switcher">
                        <button className={lang === 'en' ? 'active' : ''} onClick={() => setLang('en')}>EN</button>
                        <button className={lang === 'kn' ? 'active' : ''} onClick={() => setLang('kn')}>ಕನ್ನಡ</button>
                    </div>
                    <button
                        className="gps-update-btn"
                        onClick={() => handleGPSDetect(true)}
                        disabled={detectingLocation}
                    >
                        {detectingLocation ? `⏳ ${t('tracking', lang)}` : `📍 ${t('useGPS', lang)}`}
                    </button>
                    <span className="user-badge">{registeredUser?.name}</span>
                    <button onClick={handleLogout} className="logout-btn">{t('logout', lang)}</button>
                </div>
            </header>

            <div className="tabs">
                <button className={activeTab === 'recommendation' ? 'active' : ''} onClick={() => setActiveTab('recommendation')}>
                    {t('tabCropRec', lang)}
                </button>
                <button className={activeTab === 'prices' ? 'active' : ''} onClick={() => setActiveTab('prices')}>
                    {t('tabMarketPrices', lang)}
                </button>
                <button className={activeTab === 'neighbours' ? 'active' : ''} onClick={() => setActiveTab('neighbours')}>
                    {t('tabNeighbours', lang)}
                </button>
                <button className={activeTab === 'history' ? 'active' : ''} onClick={() => {
                    setActiveTab('history');
                    if (!farmerHistory && registeredUser) {
                        fetchFarmerHistory(registeredUser.name, registeredUser.phone_number || '');
                    }
                }}>
                    {t('tabFarmAnalysis', lang)}
                </button>
                <button className={activeTab === 'alerts' ? 'active' : ''} onClick={() => {
                    setActiveTab('alerts');
                    fetchAlertPreview(alertType);
                }}>
                    {t('tabAlerts', lang)}
                </button>
            </div>


            <main className="dashboard-content">
                {/* ===== CROP RECOMMENDATION ===== */}
                {activeTab === 'recommendation' && (
                    <div className="section-card">
                        {!showCropResults ? (
                            <>
                                <h3>{t('cropRecTitle', lang)}</h3>

                                {/* Currently Growing Crop Section */}
                                <div className="current-crop-section" style={{
                                    background: 'linear-gradient(135deg, rgba(167, 139, 250, 0.08), rgba(6, 182, 212, 0.06))',
                                    border: '1px solid rgba(167, 139, 250, 0.15)',
                                    borderRadius: 'var(--radius-lg)',
                                    padding: '1.25rem 1.5rem',
                                    marginBottom: '1rem',
                                    animation: 'fadeIn 0.5s ease-out'
                                }}>
                                    <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 700, color: 'var(--text-dark)', marginBottom: '0.75rem' }}>
                                        {t('currentlyGrowing', lang)}
                                    </h4>
                                    {farmerHistory?.info?.primary_crop ? (
                                        <div style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '1rem',
                                            padding: '1rem 1.25rem',
                                            background: 'rgba(52, 211, 153, 0.08)',
                                            border: '1.5px solid rgba(52, 211, 153, 0.20)',
                                            borderRadius: 'var(--radius-md)',
                                        }}>
                                            <span style={{ fontSize: '2.5rem' }}>{cropEmojis[farmerHistory.info.primary_crop] || '🌿'}</span>
                                            <div>
                                                <span style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' as const, letterSpacing: '0.05em' }}>
                                                    {t('activeCrop', lang)}
                                                </span>
                                                <p style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--success)', margin: 0 }}>
                                                    {getCropName(farmerHistory.info.primary_crop, lang)}
                                                </p>
                                                {farmerHistory.info.secondary_crop && farmerHistory.info.secondary_crop !== 'None' && (
                                                    <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                                                        + {getCropName(farmerHistory.info.secondary_crop, lang)}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        <div style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.75rem',
                                            padding: '1rem 1.25rem',
                                            background: 'rgba(248, 113, 113, 0.06)',
                                            border: '1.5px dashed rgba(248, 113, 113, 0.20)',
                                            borderRadius: 'var(--radius-md)',
                                        }}>
                                            <span style={{ fontSize: '2rem' }}>🚫</span>
                                            <div>
                                                <p style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--danger)', margin: 0 }}>
                                                    {t('noCropsGrowing', lang)}
                                                </p>
                                                <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                                                    {lang === 'kn' ? 'ಕೆಳಗೆ ಅಧಿಕೃತ ಕೃಷಿ ಇಲಾಖೆ ಶಿಫಾರಸುಗಳನ್ನು ಪಡೆಯಿರಿ' : 'View scientific agronomic advisory below to find the best crop for your land'}
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                                <div className="weather-card">
                                    <div className="weather-header">
                                        <h4>{t('liveWeather', lang)} — {weatherData?.location || registeredUser?.taluk}</h4>
                                        {weatherData && (weatherData.source.includes('Open-Meteo') || weatherData.source === 'OpenWeatherMap API') && <span className="live-badge">● LIVE (Open-Meteo)</span>}
                                        {weatherData?.source === 'fallback' && <span className="fallback-badge">{lang === 'kn' ? 'ಪ್ರಾದೇಶಿಕ ಡೀಫಾಲ್ಟ್' : 'Regional Defaults'}</span>}
                                        <button className="refresh-weather-btn" onClick={() => fetchWeather(registeredUser?.taluk || 'Mangalore')} disabled={loadingWeather}>
                                            {loadingWeather ? '⏳' : '🔄'} {t('refresh', lang)}
                                        </button>
                                    </div>
                                    {loadingWeather ? (
                                        <div className="weather-loading"><span className="spinner"></span> {lang === 'kn' ? 'ಹವಾಮಾನ ಮತ್ತು ಮಣ್ಣಿನ ಮಾಹಿತಿ ಪಡೆಯಲಾಗುತ್ತಿದೆ...' : 'Fetching climate & soil parameters...'}</div>
                                    ) : weatherData ? (
                                        <div className="weather-grid-detailed">
                                            <div className="parameter-card">
                                                <div className="parameter-icon">🌡️</div>
                                                <div className="parameter-info">
                                                    <span className="parameter-label">{t('temperature', lang)}</span>
                                                    <span className="parameter-value">{weatherData.temperature}°C</span>
                                                    <span className="parameter-source">{weatherData.source}</span>
                                                </div>
                                            </div>
                                            <div className="parameter-card">
                                                <div className="parameter-icon">💧</div>
                                                <div className="parameter-info">
                                                    <span className="parameter-label">{t('humidity', lang)}</span>
                                                    <span className="parameter-value">{weatherData.humidity}%</span>
                                                    <span className="parameter-source">{weatherData.source}</span>
                                                </div>
                                            </div>
                                            <div className="parameter-card">
                                                <div className="parameter-icon">🌧️</div>
                                                <div className="parameter-info">
                                                    <span className="parameter-label">{t('rainAnnual', lang)}</span>
                                                    <span className="parameter-value">{weatherData.rainfall} mm</span>
                                                    <span className="parameter-source">{lang === 'kn' ? 'ವಾರ್ಷಿಕ ಸರಾಸರಿ' : 'Annual Average'}</span>
                                                </div>
                                            </div>
                                            {weatherData.rain_today !== undefined && (
                                                <div className="parameter-card">
                                                    <div className="parameter-icon">☔</div>
                                                    <div className="parameter-info">
                                                        <span className="parameter-label">{t('rainToday', lang)}</span>
                                                        <span className="parameter-value">{weatherData.rain_today} mm</span>
                                                        <span className="parameter-source">Forecast</span>
                                                    </div>
                                                </div>
                                            )}
                                            {weatherData.rain_current !== undefined && (
                                                <div className="parameter-card">
                                                    <div className="parameter-icon">🌦️</div>
                                                    <div className="parameter-info">
                                                        <span className="parameter-label">{t('rainCurrent', lang)}</span>
                                                        <span className="parameter-value">{weatherData.rain_current} mm/h</span>
                                                        <span className="parameter-source">Live hour</span>
                                                    </div>
                                                </div>
                                            )}
                                            {soilData && (
                                                <>
                                                    <div className="parameter-card">
                                                        <div className="parameter-icon">🧪</div>
                                                        <div className="parameter-info">
                                                            <span className="parameter-label">{t('avgPH', lang)}</span>
                                                            <span className="parameter-value">{soilData.ph} pH</span>
                                                            <span className="parameter-source">RTC Record</span>
                                                        </div>
                                                    </div>
                                                    <div className="parameter-card">
                                                        <div className="parameter-icon">🏔️</div>
                                                        <div className="parameter-info">
                                                            <span className="parameter-label">{t('soilType', lang)}</span>
                                                            <span className="parameter-value" style={{ fontSize: '0.9rem' }}>
                                                                {getSoilName(soilData.soil_type, lang)}
                                                            </span>
                                                            <span className="parameter-source">RTC Record</span>
                                                        </div>
                                                    </div>
                                                </>
                                            )}
                                            {soilData?.temperature !== undefined && (
                                                <div className="parameter-card">
                                                    <div className="parameter-icon">🌡️</div>
                                                    <div className="parameter-info">
                                                        <span className="parameter-label">{t('soilTemp', lang)}</span>
                                                        <span className="parameter-value">{soilData.temperature}°C</span>
                                                        <span className="parameter-source">Open-Meteo 0-7cm</span>
                                                    </div>
                                                </div>
                                            )}
                                            {soilData?.moisture !== undefined && (
                                                <div className="parameter-card">
                                                    <div className="parameter-icon">💦</div>
                                                    <div className="parameter-info">
                                                        <span className="parameter-label">{t('soilMoisture', lang)}</span>
                                                        <span className="parameter-value">{soilData.moisture}%</span>
                                                        <span className="parameter-source">Open-Meteo Volumetric</span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ) : null}
                                </div>

                                {/* Soil Card */}
                                <div className="soil-card" style={{ display: 'none' }}>
                                    <h4>{t('soilDataTitle', lang)}</h4>
                                    <div className="soil-details">
                                        <div className="soil-item">
                                            <span className="soil-label">{t('soilType', lang)}</span>
                                            <span className="soil-value">{getSoilName(soilData?.soil_type || 'Laterite', lang)}</span>
                                        </div>
                                        <div className="soil-item">
                                            <span className="soil-label">{t('avgPH', lang)}</span>
                                            <span className="soil-value">{soilData?.ph || '6.2'}</span>
                                        </div>
                                    </div>
                                </div>

                                <button onClick={handleCropRecommendation} className="submit-btn" disabled={loadingCropRec || loadingWeather}>
                                    {loadingCropRec ? <><span className="spinner"></span> {t('analyzing', lang)}</> : t('getCropRecBtn', lang)}
                                </button>
                            </>
                        ) : (
                            <>
                                <div className="result-header">
                                    <h3>{t('recommendedCropsTitle', lang)}</h3>
                                    <button className="back-btn" onClick={resetCropResults}>{t('backBtn', lang)}</button>
                                </div>
                                <div className="soil-info">
                                    <div className="info-chip">🧪 pH: {recommendations?.soil_data?.ph}</div>
                                    <div className="info-chip">🌡️ Temp: {recommendations?.soil_data?.temp}°C</div>
                                    <div className="info-chip">🌧️ Rainfall: {recommendations?.soil_data?.rainfall}mm</div>
                                    <div className="info-chip">🏔️ {recommendations?.soil_data?.soil_type}</div>
                                    {recommendations?.soil_data?.humidity && <div className="info-chip">💧 Humidity: {recommendations?.soil_data?.humidity}%</div>}
                                </div>
                                {recommendations?.soil_data?.weather_source === 'OpenWeatherMap API' && (
                                    <p className="weather-source-note">📡 Weather data sourced live from OpenWeatherMap for {weatherData?.location}</p>
                                )}
                                <div className="crop-grid">
                                    {recommendations?.recommended_crops.map((item: any, index: number) => {
                                        const cropName = typeof item === 'string' ? item : item.crop;
                                        const cropPrice = typeof item === 'string' ? 'Check Market' : (item.price_range || item.price);
                                        const trend = typeof item === 'string' ? 'stable' : item.trend;
                                        const varietiesList = item.varieties || [];
                                        const isExpanded = expandedSpeciesCrop === cropName;

                                        return (
                                            <div key={cropName} className={`crop-card ${isExpanded ? 'crop-card-expanded' : ''}`} style={{ animationDelay: `${index * 0.1}s` }}>
                                                {/* Top Row: Crop Icon, Title, Genus & Status Trend */}
                                                <div className="crop-card-top-row">
                                                    <div className="crop-card-identity">
                                                        <div className="crop-avatar-box">
                                                            <span className="crop-icon">{cropEmojis[cropName] || '🌿'}</span>
                                                        </div>
                                                        <div className="crop-title-block">
                                                            <h4 className="crop-name-heading">{getCropName(cropName, lang)}</h4>
                                                            {item.botanical_genus && (
                                                                <span className="crop-genus-tag">{item.botanical_genus}</span>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <div className={`crop-trend-pill ${trend}`}>
                                                        {trend === 'up' ? `▲ ${t('trendRising', lang)}` : trend === 'down' ? `▼ ${t('trendFalling', lang)}` : `● ${t('trendStable', lang)}`}
                                                    </div>
                                                </div>

                                                {/* Market Price & Land Fit Metric Card */}
                                                <div className="crop-metrics-strip">
                                                    <div className="crop-metric-cell">
                                                        <span className="metric-cell-label">Mandi Modal Rate</span>
                                                        <span className="metric-cell-value price-green">{cropPrice === 'Check Market' ? t('checkMarket', lang) : cropPrice}</span>
                                                    </div>
                                                    {item.best_variety && (
                                                        <div className="crop-metric-cell align-right">
                                                            <span className="metric-cell-label">{t('suitabilityMatch', lang)}</span>
                                                            <span className="metric-cell-badge">{item.best_variety.suitability_score}% Match</span>
                                                        </div>
                                                    )}
                                                </div>
                                                
                                                {/* Professional Cultivar Showcase Box */}
                                                {item.best_variety && (
                                                    <div className="crop-cultivar-spotlight" onClick={() => openVarietyModal(cropName)} title="Click to view full agronomic profile">
                                                        <div className="cultivar-lead-row">
                                                            <div className="cultivar-meta">
                                                                <span className="cultivar-eyebrow">⭐ {t('bestForYourLand', lang)}</span>
                                                                <span className="cultivar-primary-name">{item.best_variety.name}</span>
                                                            </div>
                                                            <span className="cultivar-view-link">Specs →</span>
                                                        </div>

                                                        {/* Clean Alternative Cultivar Badges (No duplicate best_variety) */}
                                                        {(() => {
                                                            const altList = (item.top_varieties || [])
                                                                .filter((tv: CropVariety) => tv.name !== item.best_variety?.name)
                                                                .slice(0, 3);
                                                            if (altList.length === 0) return null;
                                                            return (
                                                                <div className="cultivar-alternatives-row">
                                                                    <span className="cultivar-alt-label">Also suited:</span>
                                                                    <div className="cultivar-alt-chips">
                                                                        {altList.map((tv: CropVariety) => (
                                                                            <span key={tv.name} className="cultivar-clean-tag">
                                                                                {tv.name}
                                                                            </span>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            );
                                                        })()}
                                                    </div>
                                                )}
                                                
                                                {/* Local Taluk Neighbourhood Benchmark */}
                                                {(() => {
                                                    const nbMatch = neighbourData?.crop_summary?.find(cs => cs.crop.toLowerCase() === cropName.toLowerCase());
                                                    return (
                                                        <div 
                                                            className={`crop-neighbour-bar ${nbMatch ? 'has-farmers' : 'opportunity'}`}
                                                            onClick={() => {
                                                                if (nbMatch) setSelectedCropFilter(cropName);
                                                                setActiveTab('neighbours');
                                                            }}
                                                            title={nbMatch ? "Compare with local farmers in your taluk" : "Untapped local opportunity in your taluk"}
                                                        >
                                                            <span className="cnb-icon">{nbMatch ? '🏘️' : '✨'}</span>
                                                            <span className="cnb-text">
                                                                {nbMatch ? (
                                                                    <>{nbMatch.farmer_count} {t('farmersGrowing', lang)} • Avg {nbMatch.avg_yield_per_acre} {nbMatch.yield_unit}/ac</>
                                                                ) : (
                                                                    <>{t('nicheOpportunity', lang)}</>
                                                                )}
                                                            </span>
                                                            <span className="cnb-action">Compare →</span>
                                                        </div>
                                                    );
                                                })()}

                                                {/* Clean Modern CTA Button Row */}
                                                {varietiesList.length > 0 && (
                                                    <div className="crop-action-group">
                                                        <button
                                                            type="button"
                                                            className="crop-primary-action-btn"
                                                            onClick={() => openVarietyModal(cropName)}
                                                        >
                                                            🌾 {t('exploreVarietiesBtn', lang)} ({varietiesList.length})
                                                        </button>
                                                        <button 
                                                            type="button" 
                                                            className={`crop-quick-drawer-toggle ${isExpanded ? 'active' : ''}`}
                                                            onClick={() => setExpandedSpeciesCrop(isExpanded ? null : cropName)}
                                                            title={isExpanded ? t('hideSpecies', lang) : t('viewSpecies', lang)}
                                                        >
                                                            {isExpanded ? '▲ Hide' : '▼ Quick View'}
                                                        </button>
                                                    </div>
                                                )}

                                                {/* Expandable Species & Varieties Drawer */}
                                                {isExpanded && varietiesList.length > 0 && (
                                                    <div className="card-species-drawer">
                                                        <div className="drawer-header-row">
                                                            <div>
                                                                <h6>{t('cropSpeciesTitle', lang)}</h6>
                                                                <span className="drawer-crop-subtitle">{varietiesList.length} verified cultivars for this zone</span>
                                                            </div>
                                                            <button
                                                                type="button"
                                                                className="drawer-showcase-btn"
                                                                onClick={() => openVarietyModal(cropName)}
                                                            >
                                                                {t('exploreVarietiesBtn', lang)}
                                                            </button>
                                                        </div>
                                                        <div className="drawer-species-list">
                                                            {varietiesList.map((v: CropVariety) => (
                                                                <div key={v.name} className="drawer-variety-card">
                                                                    {/* Variety Image Thumbnail & Header */}
                                                                    <div className="drawer-variety-top">
                                                                        <div className="drawer-thumb-wrap">
                                                                            <img
                                                                                src={resolveCropImage(cropName, v.image_url, item.crop_image)}
                                                                                alt={v.name}
                                                                                className="drawer-variety-img"
                                                                                onError={(e: any) => {
                                                                                    e.target.onerror = null;
                                                                                    e.target.src = resolveCropImage(cropName, v.image_url, item.crop_image);
                                                                                }}
                                                                            />
                                                                        </div>
                                                                        <div className="drawer-variety-info-head">
                                                                            <div className="drawer-name-row">
                                                                                <strong className="drawer-var-name">{v.name}</strong>
                                                                                <span className="drawer-var-price">{v.price_display || `₹${v.price}/${item.unit || 'q'}`}</span>
                                                                            </div>
                                                                            {v.scientific_species && (
                                                                                <span className="drawer-sci-species">{v.scientific_species}</span>
                                                                            )}
                                                                            {v.suitability_score !== undefined && (
                                                                                <div className="drawer-suitability-line">
                                                                                    <span className="suitability-chip">
                                                                                        {v.suitability_score}% match
                                                                                    </span>
                                                                                    <div className="suitability-progress-track">
                                                                                        <div className="suitability-progress-bar" style={{ width: `${v.suitability_score}%` }}></div>
                                                                                    </div>
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                    </div>

                                                                    {/* Match highlights */}
                                                                    {v.match_highlights && v.match_highlights.length > 0 && (
                                                                        <div className="drawer-match-reasons">
                                                                            {v.match_highlights.slice(0, 3).map((r, rIdx) => (
                                                                                <span key={rIdx} className="drawer-reason-chip">{r}</span>
                                                                            ))}
                                                                        </div>
                                                                    )}

                                                                    {/* Agronomic Specifications Grid */}
                                                                    <div className="drawer-specs-grid">
                                                                        <div className="drawer-spec-cell">
                                                                            <span className="cell-label">Soil & pH:</span>
                                                                            <span className="cell-value">{v.soil_type || 'Loamy'} {v.soil_ph_range ? `(pH ${v.soil_ph_range[0]}-${v.soil_ph_range[1]})` : ''}</span>
                                                                        </div>
                                                                        <div className="drawer-spec-cell">
                                                                            <span className="cell-label">Climate:</span>
                                                                            <span className="cell-value">{v.min_temp}°C - {v.max_temp}°C | {v.rainfall_range?.[0]}-{v.rainfall_range?.[1]}mm</span>
                                                                        </div>
                                                                        <div className="drawer-spec-cell">
                                                                            <span className="cell-label">Season:</span>
                                                                            <span className="cell-value">{v.growing_months || v.season}</span>
                                                                        </div>
                                                                        <div className="drawer-spec-cell">
                                                                            <span className="cell-label">Maturity:</span>
                                                                            <span className="cell-value">{v.maturity_period || `${v.duration_days} days`}</span>
                                                                        </div>
                                                                        <div className="drawer-spec-cell">
                                                                            <span className="cell-label">Yield:</span>
                                                                            <span className="cell-value highlight-cell">{v.expected_yield || `${v.yield_per_acre} ${item.unit || 'q'}/acre`}</span>
                                                                        </div>
                                                                    </div>

                                                                    {v.characteristics && (
                                                                        <p className="drawer-var-desc">{v.characteristics}</p>
                                                                    )}

                                                                    <div className="drawer-card-actions">
                                                                        <button
                                                                            type="button"
                                                                            className="drawer-calc-action-btn"
                                                                            onClick={() => {
                                                                                setSelectedCrop(cropName);
                                                                                setSelectedVariety(v.name);
                                                                                setActiveTab('prices');
                                                                                setShowMarketResult(true);
                                                                                setSelectedMarketResult({ crop: cropName, price: v.price_display || `₹${v.price}`, trend: 'stable' });
                                                                                fetchCropSpecies(cropName);
                                                                                setTimeout(() => {
                                                                                    const el = document.getElementById('profit-estimator-box');
                                                                                    if (el) el.scrollIntoView({ behavior: 'smooth' });
                                                                                }, 200);
                                                                            }}
                                                                        >
                                                                            {t('selectVarietyForProfit', lang)}
                                                                        </button>
                                                                        <button
                                                                            type="button"
                                                                            className="drawer-detail-action-btn"
                                                                            onClick={() => openVarietyModal(cropName)}
                                                                        >
                                                                            {t('exploreVarietiesBtn', lang)}
                                                                        </button>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* ===== MARKET RATE PREDICTION ===== */}
                {activeTab === 'prices' && (
                    <div className="section-card">
                        {!showMarketResult ? (
                            <>
                                <h3>📊 Market Rate Prediction</h3>
                                <p className="section-description">View live APMC market prices from data.gov.in for any Karnataka district. Select your district to see today's commodity prices.</p>

                                {/* District Selector */}
                                <div className="district-selector">
                                    <label htmlFor="district-select">📍 Select District</label>
                                    <div className="district-select-row">
                                        <select
                                            id="district-select"
                                            value={selectedDistrict}
                                            onChange={(e) => {
                                                setSelectedDistrict(e.target.value);
                                                fetchLiveMarketPrices(e.target.value);
                                            }}
                                        >
                                            <option value="">All Karnataka</option>
                                            {getDistrictsForState(registeredUser?.state || 'Karnataka').map(d => (
                                                <option key={d} value={d}>{d}</option>
                                            ))}
                                        </select>
                                        {selectedDistrict === registeredUser?.district && (
                                            <span className="your-district-badge">📍 Your District</span>
                                        )}
                                    </div>
                                </div>

                                {/* Live Market Prices Table */}
                                {loadingLiveMarket && (
                                    <div className="weather-loading"><span className="spinner"></span> Fetching live market prices...</div>
                                )}

                                {!loadingLiveMarket && liveMarketData && liveMarketData.records.length > 0 && (
                                    <div className="live-market-section">
                                        <div className="live-market-header">
                                            <h4>🏪 Live APMC Market Prices — {liveMarketData.requested_district || 'All Karnataka'}</h4>
                                            <div className="live-market-meta">
                                                <span className="live-badge">● LIVE</span>
                                                <span className="data-source-badge">Source: data.gov.in</span>
                                                <span className="record-count">{liveMarketData.total} commodities</span>
                                            </div>
                                        </div>
                                        <div className="live-table-wrapper">
                                            <table className="live-market-table">
                                                <thead>
                                                    <tr>
                                                        <th>Market (APMC)</th>
                                                        <th>Commodity</th>
                                                        <th>Variety</th>
                                                        <th className="price-th">Min Price</th>
                                                        <th className="price-th">Max Price</th>
                                                        <th className="price-th modal-th">Modal Price</th>
                                                        <th>Date</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {liveMarketData.records.map((rec, idx) => (
                                                        <tr key={`${rec.market}-${rec.commodity}-${idx}`} className="live-row">
                                                            <td className="market-name-cell">{rec.market}</td>
                                                            <td className="commodity-cell">{rec.commodity}</td>
                                                            <td className="variety-cell">{rec.variety}</td>
                                                            <td className="price-cell min">₹{Number(rec.min_price).toLocaleString('en-IN')}</td>
                                                            <td className="price-cell max">₹{Number(rec.max_price).toLocaleString('en-IN')}</td>
                                                            <td className="price-cell modal">₹{Number(rec.modal_price).toLocaleString('en-IN')}</td>
                                                            <td className="date-cell">{rec.arrival_date}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}

                                {!loadingLiveMarket && liveMarketData && liveMarketData.records.length === 0 && (
                                    <div className="no-data-card">
                                        <span className="no-data-icon">📭</span>
                                        <h4>No Market Data Available Today</h4>
                                        <p>No APMC price data was reported for <strong>{selectedDistrict || 'Karnataka'}</strong> today. Try selecting a different district or check back tomorrow.</p>
                                    </div>
                                )}

                                {/* Crop Selection */}
                                <h4 className="select-crop-title">🔍 Select a Crop for Detailed Prediction</h4>
                                <form onSubmit={handleMarketPrediction} className="input-form">
                                    <div className="crop-select-grid">
                                        {availableCrops.map(crop => (
                                            <div key={crop} className={`crop-select-card ${selectedCrop === crop ? 'selected' : ''}`} onClick={() => setSelectedCrop(crop)}>
                                                <span className="crop-select-icon">{cropEmojis[crop] || '🌿'}</span>
                                                <span className="crop-select-name">{getCropName(crop, lang)}</span>
                                                {selectedCrop === crop && <span className="check-mark">✓</span>}
                                            </div>
                                        ))}
                                    </div>
                                    <button type="submit" className="submit-btn" disabled={!selectedCrop || loadingMarket}>
                                        {loadingMarket ? <><span className="spinner"></span> Fetching...</> : t('getMarketRateBtn', lang)}
                                    </button>
                                </form>
                            </>
                        ) : (
                            <>
                                <div className="result-header">
                                    <h3>💰 Market Rate Prediction</h3>
                                    <button className="back-btn" onClick={resetMarketForm}>← Select Another Crop</button>
                                </div>

                                {selectedMarketResult && (
                                    <div className="market-result-card">
                                        <div className="market-result-main">
                                            <div className="market-crop-name">
                                                <span className="market-crop-emoji">{cropEmojis[selectedMarketResult.crop] || '🌿'}</span>
                                                <h2>{selectedMarketResult.crop}</h2>
                                            </div>
                                            <div className="market-price-display">
                                                <span className="market-price-label">Current Market Rate</span>
                                                <span className="market-price-value">{selectedMarketResult.price}</span>
                                                <span className={`market-trend ${selectedMarketResult.trend}`}>
                                                    {selectedMarketResult.trend === 'up' ? '📈 Price Trending Up'
                                                        : selectedMarketResult.trend === 'down' ? '📉 Price Trending Down'
                                                            : '📊 Price Stable'}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="market-advice">
                                            {selectedMarketResult.trend === 'up' && (
                                                <p className="advice-text up">✅ <strong>Good time to sell!</strong> The market price for {selectedMarketResult.crop} is trending upward.</p>
                                            )}
                                            {selectedMarketResult.trend === 'down' && (
                                                <p className="advice-text down">⚠️ <strong>Consider holding.</strong> The market price for {selectedMarketResult.crop} is declining.</p>
                                            )}
                                            {selectedMarketResult.trend === 'stable' && (
                                                <p className="advice-text stable">ℹ️ <strong>Market is stable.</strong> You can sell at your convenience.</p>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Species & Varieties Live Catalog for Selected Crop */}
                                {selectedMarketResult && (
                                    <div className="crop-species-section" id="crop-species-catalog">
                                        <div className="species-section-header">
                                            <div>
                                                <h4>{getCropName(selectedMarketResult.crop, lang)} — {t('cropSpeciesTitle', lang)}</h4>
                                                <p className="species-section-subtitle">
                                                    {speciesDataMap[selectedMarketResult.crop]?.botanical_genus && (
                                                        <span><strong>Botanical Genus:</strong> <em>{speciesDataMap[selectedMarketResult.crop]?.botanical_genus}</em> • </span>
                                                    )}
                                                    <span>{speciesDataMap[selectedMarketResult.crop]?.varieties_count || 0} {t('varietiesAvailable', lang)}</span>
                                                    {speciesDataMap[selectedMarketResult.crop]?.price_range && (
                                                        <span> • {t('priceRangeLabel', lang)}: <strong className="range-highlight">{speciesDataMap[selectedMarketResult.crop]?.price_range?.display}</strong></span>
                                                    )}
                                                </p>
                                            </div>
                                        </div>

                                        {loadingSpeciesCrop === selectedMarketResult.crop ? (
                                            <div className="weather-loading"><span className="spinner"></span> Loading species varieties & prices...</div>
                                        ) : (
                                            <div className="species-grid">
                                                {(speciesDataMap[selectedMarketResult.crop]?.varieties || []).map((v, vIdx) => {
                                                    const isSelectedVar = selectedVariety === v.name;
                                                    return (
                                                        <div key={v.name} className={`species-card ${isSelectedVar ? 'selected-species-card' : ''}`}>
                                                            {/* Variety Photo */}
                                                            <div className="species-card-img-wrap">
                                                                <img
                                                                    src={resolveCropImage(selectedMarketResult.crop, v.image_url, speciesDataMap[selectedMarketResult.crop]?.crop_image)}
                                                                    alt={v.name}
                                                                    className="species-thumb-img"
                                                                    onError={(e: any) => {
                                                                        e.target.onerror = null;
                                                                        e.target.src = resolveCropImage(selectedMarketResult.crop, v.image_url, speciesDataMap[selectedMarketResult.crop]?.crop_image);
                                                                    }}
                                                                />
                                                                {v.suitability_score !== undefined && (
                                                                    <span className="species-card-match-pill">
                                                                        {v.suitability_score}% match
                                                                    </span>
                                                                )}
                                                            </div>

                                                            <div className="species-card-top">
                                                                <div className="species-name-group">
                                                                    <span className="species-index-pill">#{vIdx + 1}</span>
                                                                    <h5 className="species-title">{v.name}</h5>
                                                                </div>
                                                                <span className="species-price-badge">
                                                                    {v.price_display || `₹${v.price.toLocaleString('en-IN')}/${speciesDataMap[selectedMarketResult.crop]?.unit || 'quintal'}`}
                                                                </span>
                                                            </div>

                                                            {v.scientific_species && (
                                                                <span className="species-scientific-name">{v.scientific_species}</span>
                                                            )}

                                                            {/* Agronomic Quick Specs */}
                                                            <div className="species-agri-specs">
                                                                <div className="spec-mini-tag"><strong>Soil:</strong> {v.soil_type ? v.soil_type.split(',')[0] : 'Alluvial/Loam'} {v.soil_ph_range ? `(pH ${v.soil_ph_range[0]}-${v.soil_ph_range[1]})` : ''}</div>
                                                                <div className="spec-mini-tag"><strong>Climate:</strong> {v.min_temp}°C - {v.max_temp}°C | {v.rainfall_range?.[0]}-{v.rainfall_range?.[1]}mm</div>
                                                                <div className="spec-mini-tag"><strong>Maturity:</strong> {v.maturity_period || `${v.duration_days} days`}</div>
                                                                <div className="spec-mini-tag"><strong>Yield:</strong> {v.expected_yield || `${v.yield_per_acre} ${speciesDataMap[selectedMarketResult.crop]?.unit || 'q'}/acre`}</div>
                                                            </div>

                                                            {v.characteristics && (
                                                                <p className="species-characteristics">{v.characteristics}</p>
                                                            )}

                                                            <div className="species-card-actions-row">
                                                                <button 
                                                                    type="button" 
                                                                    className={`select-variety-btn ${isSelectedVar ? 'active-variety-btn' : ''}`}
                                                                    onClick={() => {
                                                                        setSelectedVariety(isSelectedVar ? '' : v.name);
                                                                        const formEl = document.getElementById('profit-estimator-box');
                                                                        if (formEl) formEl.scrollIntoView({ behavior: 'smooth' });
                                                                    }}
                                                                >
                                                                    {isSelectedVar ? 'Selected' : t('selectVarietyForProfit', lang)}
                                                                </button>
                                                                <button
                                                                    type="button"
                                                                    className="species-guide-btn"
                                                                    onClick={() => openVarietyModal(selectedMarketResult.crop)}
                                                                >
                                                                    {t('exploreVarietiesBtn', lang)}
                                                                </button>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Profit Calculator */}
                                <div className="profit-calculator" id="profit-estimator-box">
                                    <h4>📐 Profit Estimator — Enter Your Land Details</h4>
                                    <p className="profit-desc">Enter your land area to estimate crop yield, input costs, and net profit based on selected species and market rates.</p>
                                    <form onSubmit={handleProfitEstimate} className="profit-form">
                                        <div className="form-group">
                                            <label>Survey Number</label>
                                            <input type="text" value={calcSurveyNumber} onChange={(e) => setCalcSurveyNumber(e.target.value)} placeholder={registeredUser?.survey_number || 'e.g. 120/3'} className="form-input" />
                                        </div>

                                        {/* Variety / Species Selector */}
                                        <div className="form-group">
                                            <label>{t('varietySelectorLabel', lang)}</label>
                                            <select
                                                value={selectedVariety}
                                                onChange={(e) => setSelectedVariety(e.target.value)}
                                                className="form-input variety-dropdown"
                                            >
                                                <option value="">-- {t('defaultVarietyOption', lang)} ({selectedMarketResult?.crop || selectedCrop}) --</option>
                                                {(speciesDataMap[selectedMarketResult?.crop || selectedCrop]?.varieties || []).map((v) => (
                                                    <option key={v.name} value={v.name}>
                                                        {v.name} — {v.price_display || `₹${v.price}/${speciesDataMap[selectedMarketResult?.crop || selectedCrop]?.unit}`} ({v.duration_days} days, {v.yield_per_acre} {speciesDataMap[selectedMarketResult?.crop || selectedCrop]?.unit}/acre)
                                                    </option>
                                                ))}
                                            </select>
                                            {selectedVariety && (
                                                <div className="variety-selection-notice">
                                                    🎯 Profit estimate will use specific cultivar rate: <strong>{selectedVariety}</strong>
                                                </div>
                                            )}
                                        </div>

                                        <div className="form-row">
                                            <div className="form-group">
                                                <label>Acres</label>
                                                <input type="number" value={calcAcres} onChange={(e) => setCalcAcres(e.target.value)} placeholder={String(registeredUser?.land_area_acres ?? 0)} className="form-input" />
                                            </div>
                                            <div className="form-group">
                                                <label>Guntas</label>
                                                <input type="number" value={calcGuntas} onChange={(e) => setCalcGuntas(e.target.value)} placeholder={String(registeredUser?.land_area_guntas ?? 0)} className="form-input" />
                                            </div>
                                        </div>
                                        <button type="submit" className="profit-btn" disabled={loadingProfit}>
                                            {loadingProfit ? <><span className="spinner"></span> Calculating...</> : '📊 Calculate Estimated Profit'}
                                        </button>
                                    </form>
                                </div>

                                {/* Profit Results */}
                                {showProfitCalc && profitEstimate && (
                                    <div className="profit-result">
                                        <h4>💹 Profit Estimation — {profitEstimate.crop}</h4>

                                        {profitEstimate.variety && (
                                            <div className="variety-result-banner">
                                                <div className="variety-banner-left">
                                                    <span className="variety-banner-icon">🌱</span>
                                                    <div>
                                                        <span className="variety-banner-tag">{t('varietyDetailsBadge', lang)}:</span>
                                                        <h5 className="variety-banner-title">{profitEstimate.variety}</h5>
                                                        {profitEstimate.variety_details?.scientific_species && (
                                                            <span className="variety-banner-sci">{profitEstimate.variety_details.scientific_species}</span>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="variety-banner-right">
                                                    <span className="variety-banner-price-tag">{profitEstimate.price_display}</span>
                                                    <span className="variety-banner-sub">Yield: {profitEstimate.yield_per_acre} {profitEstimate.yield_unit}/acre</span>
                                                </div>
                                            </div>
                                        )}
                                        <div className="profit-grid">
                                            <div className="profit-card yield">
                                                <span className="profit-card-icon">📦</span>
                                                <span className="profit-card-label">Est. Yield</span>
                                                <span className="profit-card-value">{profitEstimate.estimated_total_yield} {profitEstimate.yield_unit}</span>
                                                <span className="profit-card-sub">{profitEstimate.yield_per_acre}/{profitEstimate.yield_unit} per acre</span>
                                            </div>
                                            <div className="profit-card revenue">
                                                <span className="profit-card-icon">💰</span>
                                                <span className="profit-card-label">Est. Revenue</span>
                                                <span className="profit-card-value">₹{profitEstimate.estimated_revenue.toLocaleString('en-IN')}</span>
                                                <span className="profit-card-sub">@ {profitEstimate.price_display}</span>
                                            </div>
                                            <div className="profit-card cost">
                                                <span className="profit-card-icon">📋</span>
                                                <span className="profit-card-label">Est. Input Cost</span>
                                                <span className="profit-card-value">₹{profitEstimate.estimated_input_cost.toLocaleString('en-IN')}</span>
                                                <span className="profit-card-sub">~40% of revenue</span>
                                            </div>
                                            <div className="profit-card profit">
                                                <span className="profit-card-icon">✨</span>
                                                <span className="profit-card-label">Est. Net Profit</span>
                                                <span className="profit-card-value highlight">₹{profitEstimate.estimated_profit.toLocaleString('en-IN')}</span>
                                                <span className="profit-card-sub">₹{profitEstimate.profit_per_acre.toLocaleString('en-IN')}/acre</span>
                                            </div>
                                        </div>

                                        {/* 5-Year Price Trend */}
                                        {profitEstimate.price_history_5yr.length > 0 && (
                                            <div className="price-history">
                                                <h4>📈 5-Year Price History — {profitEstimate.crop}</h4>
                                                <div className="history-bars">
                                                    {profitEstimate.price_history_5yr.map((entry, idx) => {
                                                        const maxPrice = Math.max(...profitEstimate.price_history_5yr.map(e => e.avg_price));
                                                        const heightPct = (entry.avg_price / maxPrice) * 100;
                                                        return (
                                                            <div key={entry.year} className="history-bar-group" style={{ animationDelay: `${idx * 0.1}s` }}>
                                                                <div className="history-bar-wrapper">
                                                                    <div className="history-bar" style={{ height: `${heightPct}%` }}></div>
                                                                </div>
                                                                <span className="history-price">₹{Math.round(entry.avg_price).toLocaleString('en-IN')}</span>
                                                                <span className="history-year">{entry.year}</span>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* All Market Rates */}
                                <div className="other-prices-section">
                                    <h4>📋 All Market Rates</h4>
                                    <div className="price-list">
                                        {marketPrices.map((item: any) => (
                                            <div key={item.crop} className={`price-item ${item.crop === selectedMarketResult?.crop ? 'highlighted' : ''}`}>
                                                <span className="crop-name">{item.crop}</span>
                                                <div className="price-value">
                                                    {item.price}
                                                    <span className={`trend ${item.trend}`}>
                                                        {item.trend === 'up' ? '↑' : item.trend === 'down' ? '↓' : '•'}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* ===== NEIGHBOURS PLANTING DETAILS ===== */}
                {activeTab === 'neighbours' && (
                    <div className="section-card neighbours-section">
                        <div className="neighbours-header">
                            <div>
                                <h3>🏘️ Neighbours Planting Details</h3>
                                <p className="section-description">Compare what your neighbouring farmers are planting, their crop yields, and profitability to make smarter decisions.</p>
                            </div>
                            <div className="scope-toggle">
                                <button
                                    className={neighbourScope === 'taluk' ? 'active' : ''}
                                    onClick={() => {
                                        setNeighbourScope('taluk');
                                        setSelectedCropFilter(null);
                                        fetchNeighbourData(registeredUser?.taluk || 'Mangaluru', undefined, registeredUser?.name, farmerHistory?.info?.primary_crop);
                                    }}
                                >
                                    📍 Same Taluk
                                </button>
                                <button
                                    className={neighbourScope === 'hobli' ? 'active' : ''}
                                    onClick={() => {
                                        setNeighbourScope('hobli');
                                        setSelectedCropFilter(null);
                                        if (selectedNeighbourHobli) {
                                            fetchNeighbourData(registeredUser?.taluk || 'Mangaluru', selectedNeighbourHobli, registeredUser?.name, farmerHistory?.info?.primary_crop);
                                        }
                                    }}
                                >
                                    🏡 Same Hobli
                                </button>
                            </div>
                        </div>

                        {/* Hobli selector when in hobli scope */}
                        {neighbourScope === 'hobli' && neighbourData?.available_hoblis && (
                            <div className="hobli-selector">
                                <label>Select Hobli:</label>
                                <div className="hobli-chips">
                                    {neighbourData.available_hoblis.map(h => (
                                        <button
                                            key={h}
                                            className={`hobli-chip ${selectedNeighbourHobli === h ? 'active' : ''}`}
                                            onClick={() => {
                                                setSelectedNeighbourHobli(h);
                                                setSelectedCropFilter(null);
                                                fetchNeighbourData(registeredUser?.taluk || 'Mangaluru', h, registeredUser?.name, farmerHistory?.info?.primary_crop);
                                            }}
                                        >
                                            {h}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {loadingNeighbours && (
                             <div className="weather-loading"><span className="spinner"></span> Loading neighbour data...</div>
                         )}
                        {!loadingNeighbours && neighbourData && neighbourData.total_farmers > 0 && (
                            <div className="neighbours-layout">
                                {/* Left Column: Sidebar Crop Filter */}
                                <aside className="neighbours-sidebar">
                                    <h4 className="sidebar-title">
                                        <span>🔍</span> {lang === 'kn' ? 'ಬೆಳೆ ಶೋಧಕ' : 'Crop Switcher'}
                                    </h4>
                                    <div className="crop-filter-list">
                                        <button 
                                            className={`crop-filter-btn ${selectedCropFilter === null ? 'active' : ''}`}
                                            onClick={() => setSelectedCropFilter(null)}
                                        >
                                            <span>🌍 {lang === 'kn' ? 'ಎಲ್ಲಾ ಬೆಳೆಗಳು' : 'All Crops'}</span>
                                            <span className="crop-filter-count">{neighbourData.total_farmers}</span>
                                        </button>
                                        {neighbourData.crop_summary.map(cs => (
                                            <button
                                                key={cs.crop}
                                                className={`crop-filter-btn ${selectedCropFilter === cs.crop ? 'active' : ''}`}
                                                onClick={() => setSelectedCropFilter(cs.crop)}
                                            >
                                                <span>{cropEmojis[cs.crop] || '🌿'} {getCropName(cs.crop, lang)}</span>
                                                <span className="crop-filter-count">{cs.farmer_count}</span>
                                            </button>
                                        ))}
                                    </div>
                                </aside>

                                {/* Right Column: Map & Analytics */}
                                <div className="neighbours-main-content" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', width: '100%' }}>
                                    {/* Unified Executive Summary Strip */}
                                    <div className="neighbour-summary-bar">
                                        <div className="nsb-left">
                                            <span className="nsb-stat-badge">
                                                📊 <strong>{neighbourData.total_farmers}</strong> Farmers in <strong>{neighbourData.scope}</strong>
                                            </span>
                                            {neighbourData.insight && (
                                                <span className="nsb-insight-chip">
                                                    🌾 {neighbourData.insight}
                                                </span>
                                            )}
                                        </div>
                                        <div className="nsb-right">
                                            {neighbourData.is_real_data ? (
                                                <span className="data-source-pill real" title={neighbourData.data_source_label || 'Verified farmer survey records'}>
                                                    ✓ {t('verifiedFarmerData', lang)}
                                                </span>
                                            ) : (
                                                <span className="data-source-pill demo" title={neighbourData.data_source_label || 'Simulated agro-climatic baseline'}>
                                                    ℹ️ {t('demoSimulationData', lang)}
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Clean Crop Adoption & Recommendation Benchmark */}
                                    {recommendations?.recommended_crops && recommendations.recommended_crops.length > 0 && (
                                        <div className="neighbour-rec-comparison-box">
                                            <div className="nrc-header">
                                                <div>
                                                    <h4>📋 {t('compareWithRecommendations', lang)}</h4>
                                                    <p className="nrc-sub">{t('compareRecommendationsSub', lang)}</p>
                                                </div>
                                            </div>
                                            <div className="nrc-grid">
                                                {recommendations.recommended_crops.slice(0, 4).map((rc: any) => {
                                                    const cropName = typeof rc === 'string' ? rc : rc.crop;
                                                    const bestVar = rc.best_variety || (rc.varieties && rc.varieties[0]);
                                                    const nbCrop = neighbourData.crop_summary.find(cs => cs.crop.toLowerCase() === cropName.toLowerCase());
                                                    const isSelectedCrop = selectedCropFilter === cropName;

                                                    return (
                                                        <div key={cropName} className={`nrc-card ${isSelectedCrop ? 'active-filter' : ''}`}>
                                                            <div className="nrc-card-top">
                                                                <div className="nrc-title-wrap">
                                                                    <span className="nrc-icon">{cropEmojis[cropName] || '🌿'}</span>
                                                                    <div>
                                                                        <strong className="nrc-crop-name">{getCropName(cropName, lang)}</strong>
                                                                        {bestVar && (
                                                                            <span className="nrc-best-var">
                                                                                Top Variety: <strong>{bestVar.name}</strong>
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                                <span className={`nrc-status-pill ${nbCrop ? (nbCrop.percentage >= 40 ? 'high' : 'balanced') : 'opportunity'}`}>
                                                                    {nbCrop ? `${nbCrop.farmer_count} Growing (${nbCrop.percentage.toFixed(0)}%)` : 'Untapped Opportunity'}
                                                                </span>
                                                            </div>

                                                            {/* Streamlined Metrics Grid (No Unnecessary Text Clutter) */}
                                                            <div className="nrc-clean-metrics">
                                                                {nbCrop ? (
                                                                    <div className="nrc-data-row">
                                                                        <div className="nrc-data-point">
                                                                            <span className="ndp-label">Avg Yield</span>
                                                                            <span className="ndp-val">{nbCrop.avg_yield_per_acre} {nbCrop.yield_unit}/ac</span>
                                                                        </div>
                                                                        <div className="nrc-data-point">
                                                                            <span className="ndp-label">Avg Profit</span>
                                                                            <span className="ndp-val highlight">₹{nbCrop.avg_profit_per_acre.toLocaleString('en-IN')}/ac</span>
                                                                        </div>
                                                                        <div className="nrc-data-point">
                                                                            <span className="ndp-label">Total Land</span>
                                                                            <span className="ndp-val">{nbCrop.total_land_acres} acres</span>
                                                                        </div>
                                                                    </div>
                                                                ) : (
                                                                    <div className="nrc-opportunity-row">
                                                                        <span className="opp-tag">✨ High Potential</span>
                                                                        <span className="opp-desc">0 local farmers currently planting in {neighbourData.scope}</span>
                                                                    </div>
                                                                )}
                                                            </div>

                                                            <div className="nrc-card-actions">
                                                                {nbCrop ? (
                                                                    <button
                                                                        type="button"
                                                                        className={`nrc-action-btn ${isSelectedCrop ? 'active' : ''}`}
                                                                        onClick={() => setSelectedCropFilter(isSelectedCrop ? null : cropName)}
                                                                    >
                                                                        {isSelectedCrop ? '✓ Filtering List' : `Filter ${nbCrop.farmer_count} Farmers →`}
                                                                    </button>
                                                                ) : (
                                                                    <button
                                                                        type="button"
                                                                        className="nrc-action-btn secondary"
                                                                        onClick={() => openVarietyModal(cropName)}
                                                                    >
                                                                        View Cultivar Details →
                                                                    </button>
                                                                )}
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    )}

                                {/* Bhoomi RTC Land Boundary Map */}
                                <div className="bhoomi-map-section">
                                    <div className="bhoomi-map-card">
                                        <div className="bhoomi-map-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                                            <div className="bhoomi-map-title-block">
                                                <h4>{t('bhoomiMapTitle', lang)}</h4>
                                                <p>{t('bhoomiMapDesc', lang)}</p>
                                            </div>
                                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                                <input
                                                    type="text"
                                                    value={calcSurveyNumber}
                                                    onChange={(e) => setCalcSurveyNumber(e.target.value)}
                                                    placeholder={lang === 'kn' ? 'ಸರ್ವೆ ಸಂಖ್ಯೆ' : 'Survey No.'}
                                                    style={{
                                                        padding: '0.45rem 0.75rem',
                                                        border: '1.5px solid rgba(167, 139, 250, 0.18)',
                                                        borderRadius: 'var(--radius-sm)',
                                                        background: 'rgba(20, 16, 40, 0.7)',
                                                        color: 'var(--text-dark)',
                                                        fontSize: '0.88rem',
                                                        width: '140px'
                                                    }}
                                                />
                                                <button
                                                    onClick={() => fetchBhoomiMapData(registeredUser?.taluk || 'Mangaluru', selectedNeighbourHobli || undefined)}
                                                    className="refresh-weather-btn"
                                                    style={{ padding: '0.45rem 0.85rem' }}
                                                >
                                                    🔍 {lang === 'kn' ? 'ನಕ್ಷೆ ನೋಡಿ' : 'Map Land'}
                                                </button>
                                            </div>
                                        </div>

                                        <div className="bhoomi-map-hint">
                                            <span>💡</span>
                                            <span>{t('clickLandParcel', lang)}</span>
                                        </div>

                                        {loadingBhoomiMap ? (
                                            <div className="weather-loading"><span className="spinner"></span> Loading cadastral map...</div>
                                        ) : bhoomiMapData ? (
                                            <>
                                                <div className="bhoomi-map-container">
                                                    <MapContainer
                                                        center={bhoomiMapData.center}
                                                        zoom={16}
                                                        style={{ height: '100%', width: '100%' }}
                                                        scrollWheelZoom={true}
                                                    >
                                                        <MapController parcels={bhoomiMapData.parcels} center={bhoomiMapData.center} />
                                                        <TileLayer
                                                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                                        />
                                                        {bhoomiMapData.parcels.map((p) => {
                                                            const isMatched = !selectedCropFilter || 
                                                                p.crop_grown === selectedCropFilter || 
                                                                (p.is_empty && selectedCropFilter === 'Fallow');
                                                            return (
                                                                <Polygon
                                                                    key={p.survey_number}
                                                                    positions={p.polygon}
                                                                    pathOptions={{
                                                                        color: p.is_user ? '#fbbf24' : (p.is_empty ? '#94a3b8' : '#22c55e'),
                                                                        fillColor: p.is_user 
                                                                            ? '#10b981' 
                                                                            : p.is_empty ? '#334155'
                                                                            : p.crop_grown === 'Rice' ? '#34d399'
                                                                            : p.crop_grown === 'Arecanut' ? '#fbbf24'
                                                                            : p.crop_grown === 'Coconut' ? '#a855f7'
                                                                            : p.crop_grown === 'Banana' ? '#f43f5e'
                                                                            : p.crop_grown === 'Coffee' ? '#b45309'
                                                                            : '#3b82f6',
                                                                        fillOpacity: isMatched ? (p.is_user ? 0.55 : p.is_empty ? 0.35 : 0.45) : 0.15,
                                                                        opacity: isMatched ? 1.0 : 0.45,
                                                                        weight: p.is_user ? 3.5 : 2.2,
                                                                        dashArray: p.is_user ? '4, 4' : p.is_empty ? '4, 4' : ''
                                                                    }}
                                                                >
                                                                <Tooltip 
                                                                    direction="center" 
                                                                    offset={[0, 0]} 
                                                                    opacity={isMatched ? 0.95 : 0.45} 
                                                                    permanent
                                                                    className={`bhoomi-cadastral-label ${p.is_user ? 'user-land' : ''}`}
                                                                >
                                                                    <span>{p.is_user ? `⭐ Sy. ${p.survey_number} (You)` : `Sy. ${p.survey_number}`}</span>
                                                                </Tooltip>
                                                                <Popup>
                                                                    <div className="bhoomi-rtc-popup">
                                                                        <div className="bhoomi-rtc-header">
                                                                            <h5>{t('bhoomiRtcTitle', lang)}</h5>
                                                                            <span>{t('bhoomiGovt', lang)}</span>
                                                                        </div>
                                                                        <div className="bhoomi-rtc-watermark">BHOOMI</div>
                                                                        <table className="bhoomi-rtc-table">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td className="bhoomi-rtc-label">{t('districtLabel', lang)}</td>
                                                                                    <td className="bhoomi-rtc-val">{bhoomiMapData.district}</td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td className="bhoomi-rtc-label">{t('talukLabel', lang)}</td>
                                                                                    <td className="bhoomi-rtc-val">{bhoomiMapData.taluk}</td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td className="bhoomi-rtc-label">{t('hobliLabel', lang)}</td>
                                                                                    <td className="bhoomi-rtc-val">{bhoomiMapData.hobli}</td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td className="bhoomi-rtc-label">{t('surveyNoLabel', lang)}</td>
                                                                                    <td className="bhoomi-rtc-val">{p.survey_number.split('/')[0]}</td>
                                                                                </tr>
                                                                                {p.survey_number.includes('/') && (
                                                                                    <tr>
                                                                                        <td className="bhoomi-rtc-label">{t('hissaNoLabel', lang)}</td>
                                                                                        <td className="bhoomi-rtc-val">{p.survey_number.split('/')[1]}</td>
                                                                                    </tr>
                                                                                )}
                                                                                <tr>
                                                                                    <td className="bhoomi-rtc-label">{t('ownerNameLabel', lang)}</td>
                                                                                    <td className="bhoomi-rtc-val bhoomi-rtc-highlight-val">
                                                                                        {lang === 'kn' ? p.owner_name_kn : p.owner_name}
                                                                                    </td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td className="bhoomi-rtc-label">{t('areaLabel', lang)}</td>
                                                                                    <td className="bhoomi-rtc-val">
                                                                                        {p.land_acres} {t('acres', lang)} {p.land_guntas} {t('guntas', lang)}
                                                                                    </td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td className="bhoomi-rtc-label">{t('landClassLabel', lang)}</td>
                                                                                    <td className="bhoomi-rtc-val">
                                                                                        {lang === 'kn' ? p.land_type_kn : p.land_type}
                                                                                    </td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td className="bhoomi-rtc-label">{t('soilTypeLabel', lang)}</td>
                                                                                    <td className="bhoomi-rtc-val">
                                                                                        {lang === 'kn' ? p.soil_type_kn : p.soil_type}
                                                                                    </td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td className="bhoomi-rtc-label">
                                                                                        {p.is_empty ? t('statusLabel', lang) : t('cropGrownLabel', lang)}
                                                                                    </td>
                                                                                    <td className="bhoomi-rtc-val bhoomi-rtc-highlight-val" style={p.is_empty ? { color: '#fb7185', fontWeight: 'bold' } : {}}>
                                                                                        {p.is_empty ? `⚠️ ${t('fallowStatus', lang)}` : `${cropEmojis[p.crop_grown] || '🌿'} ${getCropName(p.crop_grown, lang)}`}
                                                                                    </td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td className="bhoomi-rtc-label" style={{ color: '#34d399', fontWeight: 'bold' }}>
                                                                                        {t('recommendedCropsLabel', lang)}
                                                                                    </td>
                                                                                    <td className="bhoomi-rtc-val" style={{ color: '#34d399', fontWeight: 'bold' }}>
                                                                                        {p.recommended_crops?.map(crop => `${cropEmojis[crop] || '🌿'} ${getCropName(crop, lang)}`).join(', ') || 'N/A'}
                                                                                    </td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td className="bhoomi-rtc-label" style={{ color: '#a78bfa', fontWeight: 'bold' }}>
                                                                                        {t('suggestedWorkLabel', lang)}
                                                                                    </td>
                                                                                    <td className="bhoomi-rtc-val" style={{ fontSize: '0.85rem', fontStyle: 'italic', lineHeight: '1.2', color: '#d4d0e8' }}>
                                                                                        {lang === 'kn' ? p.suggested_work_kn : p.suggested_work}
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                        {p.is_user && (
                                                                            <span className="bhoomi-rtc-user-badge">{t('userLandHighlight', lang)}</span>
                                                                        )}
                                                                    </div>
                                                                </Popup>
                                                            </Polygon>
                                                            );
                                                        })}
                                                    </MapContainer>
                                                </div>

                                                <div className="bhoomi-map-legend">
                                                    <div className="legend-item">
                                                        <div className="legend-color" style={{ backgroundColor: '#34d399', border: '2px dashed #10b981' }}></div>
                                                        <span>{t('userLandHighlight', lang)}</span>
                                                    </div>
                                                    <div className="legend-item">
                                                        <div className="legend-color" style={{ backgroundColor: '#f1f5f9', border: '1px dashed #94a3b8' }}></div>
                                                        <span>{t('fallowLegend', lang)}</span>
                                                    </div>
                                                    <div className="legend-item">
                                                        <div className="legend-color" style={{ backgroundColor: '#198754' }}></div>
                                                        <span>{getCropName('Rice', lang)}</span>
                                                    </div>
                                                    <div className="legend-item">
                                                        <div className="legend-color" style={{ backgroundColor: '#fbbf24' }}></div>
                                                        <span>{getCropName('Arecanut', lang)}</span>
                                                    </div>
                                                    <div className="legend-item">
                                                        <div className="legend-color" style={{ backgroundColor: '#a855f7' }}></div>
                                                        <span>{getCropName('Coconut', lang)}</span>
                                                    </div>
                                                    <div className="legend-item">
                                                        <div className="legend-color" style={{ backgroundColor: '#f43f5e' }}></div>
                                                        <span>{getCropName('Banana', lang)}</span>
                                                    </div>
                                                    <div className="legend-item">
                                                        <div className="legend-color" style={{ backgroundColor: '#3b82f6' }}></div>
                                                        <span>{lang === 'kn' ? 'ಇತರ ಬೆಳೆಗಳು' : 'Other Crops'}</span>
                                                    </div>
                                                </div>
                                            </>
                                        ) : (
                                            <div className="weather-loading">No map data available. Please check location parameters.</div>
                                        )}
                                    </div>
                                </div>

                                {/* Crop Popularity Chart with Multi-Variety Insights */}
                                <div className="crop-popularity-section">
                                    <div className="section-title-row">
                                        <h4>🌾 {t('cropDemandDist', lang)}</h4>
                                        <span className="section-note">{neighbourData.crop_summary.length} crops cultivated locally</span>
                                    </div>
                                    <p className="chart-subtitle">What your neighbours are growing — higher bars mean more local market supply</p>
                                    <div className="popularity-bars">
                                        {neighbourData.crop_summary.map((cs, idx) => {
                                            const isRec = recommendations?.recommended_crops?.some(
                                                (rc: any) => (typeof rc === 'string' ? rc : rc.crop).toLowerCase() === cs.crop.toLowerCase()
                                            );

                                            return (
                                                <div key={cs.crop} className="popularity-bar-row" style={{ animationDelay: `${idx * 0.1}s` }}>
                                                    <div className="pop-crop-info">
                                                        <div className="pop-crop-name-block">
                                                            <span className="pop-crop-emoji">{cropEmojis[cs.crop] || '🌿'}</span>
                                                            <span className="pop-crop-name">{getCropName(cs.crop, lang)}</span>
                                                            {isRec && (
                                                                <span className="pop-rec-star">⭐ {t('recommendedForYou', lang)}</span>
                                                            )}
                                                        </div>
                                                        <span className="pop-farmer-count">{cs.farmer_count} {t('farmers', lang)} ({cs.total_land_acres} acres)</span>
                                                    </div>
                                                    
                                                    <div className="pop-bar-track">
                                                        <div
                                                            className="pop-bar-fill"
                                                            style={{ width: `${cs.percentage}%`, animationDelay: `${idx * 0.15}s` }}
                                                        >
                                                            <span className="pop-bar-label">{cs.percentage}%</span>
                                                        </div>
                                                    </div>

                                                    {/* Cultivars & Varieties Breakdown */}
                                                    <div className="pop-varieties-strip">
                                                        <span className="pop-var-label">{t('varietiesPlanted', lang)}:</span>
                                                        <div className="pop-var-chips">
                                                            {cs.varieties_breakdown && cs.varieties_breakdown.length > 0 ? (
                                                                cs.varieties_breakdown.map(vb => (
                                                                    <span 
                                                                        key={vb.variety} 
                                                                        className="pop-var-chip active-neighbour"
                                                                        onClick={() => openVarietyModal(cs.crop)}
                                                                        title={`Click to explore ${vb.variety} agronomy details`}
                                                                    >
                                                                        <strong>{vb.variety}</strong>: {vb.farmers_count} {t('farmers', lang)} ({vb.avg_yield} {cs.yield_unit}/acre • {vb.market_price_display || vb.growing_season})
                                                                    </span>
                                                                ))
                                                            ) : cs.available_varieties && cs.available_varieties.length > 0 ? (
                                                                cs.available_varieties.slice(0, 4).map(v => (
                                                                    <span 
                                                                        key={v} 
                                                                        className="pop-var-chip"
                                                                        onClick={() => openVarietyModal(cs.crop)}
                                                                    >
                                                                        {v}
                                                                    </span>
                                                                ))
                                                            ) : (
                                                                <span className="pop-var-chip">Regional Cultivars</span>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                {/* Comprehensive Comparison Table */}
                                <div className="neighbour-comparison-table">
                                    <div className="section-title-row">
                                        <h4>📋 Crop Yield, Market Price & Cultivar Comparison</h4>
                                    </div>
                                    <div className="comparison-table-wrapper">
                                        <table className="comparison-table">
                                            <thead>
                                                <tr>
                                                    <th>Crop & Verified Varieties</th>
                                                    <th>Nearby Farmers</th>
                                                    <th>Growing Season</th>
                                                    <th>Soil & pH</th>
                                                    <th>Market Price</th>
                                                    <th>Avg Yield/Acre</th>
                                                    <th className="profit-col">Avg Profit/Acre</th>
                                                    <th>Recommendation</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {neighbourData.crop_summary.map((cs, idx) => {
                                                    const isRec = recommendations?.recommended_crops?.some(
                                                        (rc: any) => (typeof rc === 'string' ? rc : rc.crop).toLowerCase() === cs.crop.toLowerCase()
                                                    );
                                                    const varNames = cs.available_varieties?.slice(0, 3) || [];

                                                    return (
                                                        <tr key={cs.crop} className="comparison-row" style={{ animationDelay: `${idx * 0.08}s` }}>
                                                            <td className="comp-crop-cell">
                                                                <div className="comp-crop-content">
                                                                    <div className="comp-crop-title">
                                                                        <span className="comp-crop-emoji">{cropEmojis[cs.crop] || '🌿'}</span>
                                                                        <strong>{getCropName(cs.crop, lang)}</strong>
                                                                    </div>
                                                                    {varNames.length > 0 && (
                                                                        <div className="comp-variety-subtext">
                                                                            {varNames.map(v => (
                                                                                <span 
                                                                                    key={v} 
                                                                                    className="table-var-pill"
                                                                                    onClick={() => openVarietyModal(cs.crop)}
                                                                                    title="Click to view variety specs"
                                                                                >
                                                                                    {v}
                                                                                </span>
                                                                            ))}
                                                                            {cs.varieties_count && cs.varieties_count > 3 && (
                                                                                <small className="more-var-text" onClick={() => openVarietyModal(cs.crop)}>
                                                                                    +{cs.varieties_count - 3} more
                                                                                </small>
                                                                            )}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </td>
                                                            <td className="comp-count-cell">
                                                                <strong>{cs.farmer_count}</strong>
                                                                <small style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.74rem' }}>{cs.total_land_acres} ac</small>
                                                            </td>
                                                            <td className="comp-season-cell">
                                                                <span className="season-pill">{cs.primary_season || 'Kharif'}</span>
                                                            </td>
                                                            <td className="comp-soil-cell">
                                                                <span className="soil-text">{cs.soil_requirements || 'Loamy Soil'}</span>
                                                                {cs.soil_ph_range && (
                                                                    <small className="ph-text" style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.74rem' }}>
                                                                        pH {cs.soil_ph_range[0]} - {cs.soil_ph_range[1]}
                                                                    </small>
                                                                )}
                                                            </td>
                                                            <td className="comp-price-cell">
                                                                <span className="price-tag">{cs.price_range?.display || cs.top_varieties?.[0]?.price_display || 'Market Rate'}</span>
                                                            </td>
                                                            <td className="comp-yield-cell">
                                                                <strong>{cs.avg_yield_per_acre}</strong> {cs.yield_unit}/acre
                                                            </td>
                                                            <td className="comp-profit-cell">
                                                                ₹{cs.avg_profit_per_acre.toLocaleString('en-IN')}
                                                            </td>
                                                            <td className="comp-rec-cell">
                                                                {isRec ? (
                                                                    <span className="table-rec-badge match">✓ {t('recommendedForYou', lang)}</span>
                                                                ) : (
                                                                    <span className="table-rec-badge alt">Alternative</span>
                                                                )}
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                {/* Neighbour Farmer Cards */}
                                <div className="neighbour-cards-section">
                                    <div className="section-title-row">
                                        <h4>👥 {t('individualNeighbours', lang)}</h4>
                                        <span className="section-note">
                                            {selectedCropFilter ? `Showing ${selectedCropFilter} growers` : `All ${neighbourData.neighbours.length} nearby farmers`}
                                        </span>
                                    </div>
                                    <p className="chart-subtitle">{t('neighbourDetailsSub', lang)}</p>
                                    
                                    <div className="neighbour-cards-grid">
                                        {neighbourData.neighbours
                                            .filter(n => !selectedCropFilter || n.primary_crop === selectedCropFilter)
                                            .map((n, idx) => {
                                                const isRecCrop = recommendations?.recommended_crops?.some(
                                                    (rc: any) => (typeof rc === 'string' ? rc : rc.crop).toLowerCase() === n.primary_crop.toLowerCase()
                                                );

                                                return (
                                                    <div key={n.farmer_id} className="neighbour-card" style={{ animationDelay: `${idx * 0.06}s` }}>
                                                        <div className="nc-header">
                                                            <div className="nc-avatar">{n.name.charAt(0)}</div>
                                                            <div className="nc-name-info">
                                                                <div className="nc-name-row">
                                                                    <span className="nc-name">{n.name}</span>
                                                                    {n.is_real_data ? (
                                                                        <span className="nc-source-pill real" title="Verified farmer record from Taluk survey">Verified</span>
                                                                    ) : (
                                                                        <span className="nc-source-pill demo" title="Simulated farmer based on agro-climatic baseline">Demo</span>
                                                                    )}
                                                                </div>
                                                                <span className="nc-hobli">📍 {n.hobli}</span>
                                                            </div>
                                                            {isRecCrop && (
                                                                <span className="nc-rec-pill" title="Matches your farm recommendation">⭐ Recommended</span>
                                                            )}
                                                        </div>

                                                        <div className="nc-details">
                                                            <div className="nc-detail-row">
                                                                <span className="nc-detail-label">{t('primaryCrop', lang)}</span>
                                                                <span className="nc-detail-value">{cropEmojis[n.primary_crop] || '🌿'} {getCropName(n.primary_crop, lang)}</span>
                                                            </div>
                                                            
                                                            {/* Specific Variety Grown */}
                                                            <div className="nc-detail-row highlight-row">
                                                                <span className="nc-detail-label">Cultivar / Variety</span>
                                                                <span className="nc-detail-value var-highlight">
                                                                    <strong>{n.variety || 'Local Standard'}</strong>
                                                                    {n.variety_scientific && <small className="nc-sci-sub"> ({n.variety_scientific})</small>}
                                                                </span>
                                                            </div>

                                                            {/* Growing Season */}
                                                            <div className="nc-detail-row">
                                                                <span className="nc-detail-label">{t('growingSeason', lang)}</span>
                                                                <span className="nc-detail-value">{n.growing_season || 'Kharif'}</span>
                                                            </div>

                                                            {/* Market Price */}
                                                            <div className="nc-detail-row">
                                                                <span className="nc-detail-label">{t('marketPrice', lang)}</span>
                                                                <span className="nc-detail-value price-text">
                                                                    {n.market_price_display || (n.market_price ? `₹${n.market_price}/${n.yield_unit}` : 'Market Rate')}
                                                                </span>
                                                            </div>

                                                            {/* Soil Condition & pH */}
                                                            <div className="nc-detail-row">
                                                                <span className="nc-detail-label">{t('soilConditions', lang)}</span>
                                                                <span className="nc-detail-value">
                                                                    {n.soil_type} {n.soil_ph ? `(pH ${n.soil_ph})` : ''}
                                                                </span>
                                                            </div>

                                                            {/* Land Area */}
                                                            <div className="nc-detail-row">
                                                                <span className="nc-detail-label">Land Area</span>
                                                                <span className="nc-detail-value">{n.land_acres} acres {n.land_guntas ? `${n.land_guntas} gts` : ''}</span>
                                                            </div>

                                                            {/* Yield & Yield/Acre */}
                                                            <div className="nc-detail-row">
                                                                <span className="nc-detail-label">Yield ({n.latest_year})</span>
                                                                <span className="nc-detail-value">{n.latest_yield.toLocaleString('en-IN')} {n.yield_unit}</span>
                                                            </div>
                                                            <div className="nc-detail-row">
                                                                <span className="nc-detail-label">Yield/Acre</span>
                                                                <span className="nc-detail-value yield-text">{n.yield_per_acre.toLocaleString('en-IN')} {n.yield_unit}</span>
                                                            </div>
                                                        </div>

                                                        <div className="nc-footer">
                                                            <div className="nc-profit">
                                                                <span className="nc-profit-label">Profit/Acre</span>
                                                                <span className="nc-profit-value">₹{n.profit_per_acre.toLocaleString('en-IN')}</span>
                                                            </div>
                                                            <button 
                                                                type="button" 
                                                                className="nc-explore-var-btn"
                                                                onClick={() => openVarietyModal(n.primary_crop)}
                                                                title="Explore all cultivars of this crop"
                                                            >
                                                                {t('exploreVarieties', lang)} →
                                                            </button>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                    </div>
                                </div>
                                </div>
                            </div>
                        )}

                        {!loadingNeighbours && neighbourData && neighbourData.total_farmers === 0 && (
                            <div className="no-data-card">
                                <span className="no-data-icon">🏘️</span>
                                <h4>No Neighbour Data Available</h4>
                                <p>No farmer data was found for <strong>{neighbourData.scope}</strong>. Try switching to taluk-level view for broader results.</p>
                            </div>
                        )}
                    </div>
                )}

                {/* ===== MY FARM ANALYSIS ===== */}
                {activeTab === 'history' && (
                    farmerHistory ? (
                    <div className="section-card history-section">
                        <div className="history-header">
                            <h3>📊 My Farm Performance History</h3>
                            <div className="farmer-id-badge">Farmer ID: {farmerHistory.info.id}</div>
                        </div>
                        <p className="section-description">Analyzing your performance data from 2021 to 2025. This summary is based on your registered land and crop records.</p>

                        <div className="farm-stat-cards">
                            <div className="stat-card">
                                <span className="stat-icon">🗺️</span>
                                <div className="stat-info">
                                    <span className="stat-value">{registeredUser?.land_area_acres ?? farmerHistory.info.acres} Acres</span>
                                    {(registeredUser?.land_area_guntas ?? farmerHistory.info.guntas) !== undefined && (
                                        <span className="stat-sub">{registeredUser?.land_area_guntas ?? farmerHistory.info.guntas} Guntas</span>
                                    )}
                                </div>
                            </div>
                            <div className="stat-card">
                                <span className="stat-icon">🌱</span>
                                <div className="stat-info">
                                    <span className="stat-label">Primary Crop</span>
                                    <span className="stat-value">{farmerHistory.info.primary_crop}</span>
                                </div>
                            </div>
                            <div className="stat-card">
                                <span className="stat-icon">🏔️</span>
                                <div className="stat-info">
                                    <span className="stat-label">Soil Type</span>
                                    <span className="stat-value">{farmerHistory.info.soil_type}</span>
                                </div>
                            </div>
                            <div className="stat-card">
                                <span className="stat-icon">🧪</span>
                                <div className="stat-info">
                                    <span className="stat-label">pH Level</span>
                                    <span className="stat-value">{farmerHistory.info.ph}</span>
                                </div>
                            </div>
                        </div>

                        <div className="history-charts-grid">
                            <div className="chart-container">
                                <h4>📈 Annual Yield Trend ({farmerHistory.history[0]?.unit})</h4>
                                <div className="history-bars personal-bars">
                                    {farmerHistory.history.map((entry, idx) => {
                                        const maxVal = Math.max(...farmerHistory.history.map(e => e.yield));
                                        const heightPct = entry.yield > 0 ? (entry.yield / maxVal) * 100 : 0;
                                        return (
                                            <div key={entry.year} className="history-bar-group" style={{ animationDelay: `${idx * 0.1}s` }}>
                                                <div className="history-bar-wrapper">
                                                    <div className="history-bar yield-bar" style={{ height: `${heightPct}%` }}></div>
                                                </div>
                                                <span className="history-price">{entry.yield.toFixed(1)}</span>
                                                <span className="history-year">{entry.year}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            <div className="chart-container">
                                <h4>💰 Annual Net Profit Trend (INR)</h4>
                                <div className="history-bars personal-bars">
                                    {farmerHistory.history.map((entry, idx) => {
                                        const maxVal = Math.max(...farmerHistory.history.map(e => e.profit));
                                        const heightPct = entry.profit > 0 ? (entry.profit / maxVal) * 100 : 0;
                                        return (
                                            <div key={entry.year} className="history-bar-group" style={{ animationDelay: `${idx * 0.1}s` }}>
                                                <div className="history-bar-wrapper">
                                                    <div className="history-bar profit-bar" style={{ height: `${heightPct}%` }}></div>
                                                </div>
                                                <span className="history-price">₹{(entry.profit / 1000).toFixed(0)}k</span>
                                                <span className="history-year">{entry.year}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>

                        <div className="performance-summary">
                            <p>🌟 <strong>Performance Note:</strong> Your {farmerHistory.info.primary_crop} yield was highest in <strong>{
                                farmerHistory.history.reduce((prev, current) => (prev.yield > current.yield) ? prev : current).year
                            }</strong> with a total profit of <strong>₹{
                                farmerHistory.history.reduce((prev, current) => (prev.profit > current.profit) ? prev : current).profit.toLocaleString('en-IN')
                            }</strong>.</p>
                        </div>
                    </div>
                    ) : (
                    <div className="section-card history-section" style={{ textAlign: 'center', padding: '3.5rem 1.5rem' }}>
                        <div className="weather-loading"><span className="spinner"></span> Loading your farm performance analytics...</div>
                    </div>
                    )
                )}

                {/* ===== APMC WHATSAPP & SMS ALERTS ===== */}
                {activeTab === 'alerts' && (
                    <div className="section-card alerts-section">
                        {/* Hero Header */}
                        <div className="alerts-hero-banner">
                            <div className="alerts-hero-text">
                                <div className="alerts-badge-row">
                                    <span className="live-channel-badge whatsapp">🟢 WhatsApp Official Verified</span>
                                    <span className="live-channel-badge sms">⚡ TRAI DLT SMS Gateway</span>
                                    <span className="live-channel-badge pulse">🔔 Live Mandi Dispatch</span>
                                </div>
                                <h2>📲 {t('alertsHeroTitle', lang)}</h2>
                                <p>{t('alertsHeroDesc', lang)}</p>
                                <div className="alerts-farmer-tags">
                                    <span className="farmer-tag-pill">📱 {alertPreview?.phone_display || registeredUser?.phone_number || '+91 98451 12233'}</span>
                                    <span className="farmer-tag-pill">🌱 {getCropName(registeredUser?.current_crop || registeredUser?.primary_crop || 'Arecanut', lang)}</span>
                                    <span className="farmer-tag-pill">📍 {registeredUser?.taluk || 'Sirsi'} APMC Yard</span>
                                </div>
                            </div>
                            <div className="alerts-hero-stat">
                                <div className="live-price-pulse-card">
                                    <span className="pulse-title">Today's Modal Rate</span>
                                    <span className="pulse-rate">₹{alertPreview?.modal_price?.toLocaleString('en-IN') || '48,500'}</span>
                                    <span className="pulse-unit">per {alertPreview?.unit || 'Quintal'}</span>
                                    <span className="pulse-trend-badge up">▲ {alertPreview?.trend || '+2.8%'} Bullish Demand</span>
                                </div>
                            </div>
                        </div>

                        {/* Alert Type & Channel Selectors */}
                        <div className="alerts-config-grid">
                            <div className="config-card">
                                <h4>🎯 Select Alert Type</h4>
                                <div className="alert-type-buttons">
                                    <button
                                        type="button"
                                        className={`alert-type-btn ${alertType === 'daily_mandi' ? 'active' : ''}`}
                                        onClick={() => {
                                            setAlertType('daily_mandi');
                                            fetchAlertPreview('daily_mandi');
                                        }}
                                    >
                                        <span className="type-icon">🌾</span>
                                        <div>
                                            <strong>{t('alertTypeDaily', lang)}</strong>
                                            <small>Sent daily at 7:00 AM before auction</small>
                                        </div>
                                    </button>
                                    <button
                                        type="button"
                                        className={`alert-type-btn ${alertType === 'price_surge' ? 'active' : ''}`}
                                        onClick={() => {
                                            setAlertType('price_surge');
                                            fetchAlertPreview('price_surge');
                                        }}
                                    >
                                        <span className="type-icon">🚨</span>
                                        <div>
                                            <strong>{t('alertTypeSurge', lang)}</strong>
                                            <small>Instant trigger when rate spikes +3%</small>
                                        </div>
                                    </button>
                                    <button
                                        type="button"
                                        className={`alert-type-btn ${alertType === 'selling_advice' ? 'active' : ''}`}
                                        onClick={() => {
                                            setAlertType('selling_advice');
                                            fetchAlertPreview('selling_advice');
                                        }}
                                    >
                                        <span className="type-icon">⚖️</span>
                                        <div>
                                            <strong>{t('alertTypeSelling', lang)}</strong>
                                            <small>Harvest & grading premium advice</small>
                                        </div>
                                    </button>
                                </div>
                            </div>

                            <div className="config-card">
                                <h4>⚙️ Notification Channels & Schedule</h4>
                                <div className="channel-checkboxes">
                                    <label className="channel-toggle-row">
                                        <input
                                            type="checkbox"
                                            checked={channelWhatsApp}
                                            onChange={(e) => setChannelWhatsApp(e.target.checked)}
                                        />
                                        <span className="toggle-label">
                                            <strong>🟢 WhatsApp Notifications</strong>
                                            <small>Formatted chat bulletin with emojis & market trends</small>
                                        </span>
                                    </label>
                                    <label className="channel-toggle-row">
                                        <input
                                            type="checkbox"
                                            checked={channelSMS}
                                            onChange={(e) => setChannelSMS(e.target.checked)}
                                        />
                                        <span className="toggle-label">
                                            <strong>📱 SMS Priority Alerts</strong>
                                            <small>DLT Sender: KA-APMC (Works even without internet)</small>
                                        </span>
                                    </label>
                                </div>

                                <div className="frequency-selector">
                                    <label>Alert Frequency:</label>
                                    <select value={alertFrequency} onChange={(e) => setAlertFrequency(e.target.value)}>
                                        <option value="daily_7am">🌅 Daily 7:00 AM (Market Opening)</option>
                                        <option value="surge_only">⚡ Price Surge Spikes (+3%) Only</option>
                                        <option value="weekly">📅 Weekly Comprehensive Digest</option>
                                    </select>
                                </div>

                                <div className="dispatch-action-box">
                                    <button
                                        type="button"
                                        className="send-simulation-btn"
                                        onClick={handleSendSimulation}
                                        disabled={sendingAlert}
                                    >
                                        {sendingAlert ? (
                                            <><span className="spinner"></span> {t('sendingAlert', lang)}</>
                                        ) : (
                                            `🚀 ${t('sendTestAlert', lang)}`
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Dispatch Confirmation Toast */}
                        {alertDispatchResult && (
                            <div className="dispatch-toast animate-slide-in">
                                <div className="dispatch-toast-header">
                                    <span className="toast-icon">✅</span>
                                    <div>
                                        <strong>{t('deliverySimulatedSuccess', lang)}</strong>
                                        <p>{alertDispatchResult.message}</p>
                                    </div>
                                </div>
                                <div className="dispatch-meta-grid">
                                    <div className="meta-item">
                                        <span>Carrier Hub:</span>
                                        <strong>{alertDispatchResult.carrier}</strong>
                                    </div>
                                    {alertDispatchResult.sms_id && (
                                        <div className="meta-item">
                                            <span>SMS DLT ID:</span>
                                            <code>{alertDispatchResult.sms_id}</code>
                                        </div>
                                    )}
                                    {alertDispatchResult.wa_id && (
                                        <div className="meta-item">
                                            <span>WhatsApp Message ID:</span>
                                            <code>{alertDispatchResult.wa_id}</code>
                                        </div>
                                    )}
                                    <div className="meta-item">
                                        <span>Timestamp:</span>
                                        <strong>{alertDispatchResult.time}</strong>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Live Phone Mockup Dual Screen Preview */}
                        <div className="phone-previews-container">
                            <h3 className="previews-title">📱 Live Screen Preview on Farmer's Phone</h3>
                            <div className="phone-previews-grid">
                                {/* WhatsApp Simulator */}
                                <div className="smartphone-frame whatsapp-frame">
                                    <div className="phone-notch"></div>
                                    <div className="phone-top-bar">
                                        <span>9:41 AM</span>
                                        <span>📶 5G 🔋 98%</span>
                                    </div>
                                    <div className="wa-app-header">
                                        <div className="wa-avatar">🌾</div>
                                        <div className="wa-contact-info">
                                            <div className="wa-contact-name">
                                                Karnataka APMC <span className="wa-verified-tick">✓</span>
                                            </div>
                                            <div className="wa-contact-status">Official Govt Business Account</div>
                                        </div>
                                    </div>
                                    <div className="wa-chat-canvas">
                                        <div className="wa-date-pill">Today</div>
                                        <div className="wa-message-bubble">
                                            <pre className="wa-message-text">{alertPreview?.whatsapp_text || 'Loading Karnataka APMC Bulletin...'}</pre>
                                            <div className="wa-message-meta">
                                                <span>07:05 AM</span>
                                                <span className="wa-double-tick">✓✓</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="phone-actions-footer">
                                        {alertPreview?.whatsapp_share_url && (
                                            <a
                                                href={alertPreview.whatsapp_share_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="phone-btn wa-share-btn"
                                            >
                                                🟢 {t('shareToWhatsapp', lang)}
                                            </a>
                                        )}
                                        <button
                                            type="button"
                                            className="phone-btn copy-btn"
                                            onClick={() => handleCopyAlert(alertPreview?.whatsapp_text || '')}
                                        >
                                            {alertCopied ? `✓ ${t('copied', lang)}` : `📋 ${t('copyAlertText', lang)}`}
                                        </button>
                                    </div>
                                </div>

                                {/* SMS Simulator */}
                                <div className="smartphone-frame sms-frame">
                                    <div className="phone-notch"></div>
                                    <div className="phone-top-bar">
                                        <span>9:41 AM</span>
                                        <span>📶 5G 🔋 98%</span>
                                    </div>
                                    <div className="sms-app-header">
                                        <div className="sms-sender-avatar">🏛️</div>
                                        <div className="sms-sender-title">KA-APMC</div>
                                        <div className="sms-sender-sub">Govt of Karnataka • DLT Header</div>
                                    </div>
                                    <div className="sms-chat-canvas">
                                        <div className="sms-banner-card">
                                            <div className="sms-banner-top">
                                                <span>MESSAGES • now</span>
                                            </div>
                                            <div className="sms-banner-content">
                                                <strong>KA-APMC</strong>
                                                <p>{alertPreview?.sms_text || 'Loading SMS Alert...'}</p>
                                            </div>
                                        </div>
                                        <div className="sms-bubble">
                                            <p className="sms-body-text">{alertPreview?.sms_text || 'Loading SMS Alert...'}</p>
                                            <span className="sms-time">07:05 AM • via Carrier SMS</span>
                                        </div>
                                    </div>
                                    <div className="phone-actions-footer">
                                        <button
                                            type="button"
                                            className="phone-btn copy-btn full-width"
                                            onClick={() => handleCopyAlert(alertPreview?.sms_text || '')}
                                        >
                                            {alertCopied ? `✓ ${t('copied', lang)}` : `📋 Copy SMS Text`}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* =====================================================
                    VARIETY SHOWCASE & AGRONOMIC DETAIL MODAL
                    ===================================================== */}
                {varietyModalCrop && (
                    <div className="variety-modal-backdrop" onClick={() => setVarietyModalCrop(null)}>
                        <div className="variety-modal-content" onClick={(e) => e.stopPropagation()}>
                            <div className="variety-modal-header">
                                <div className="modal-header-info">
                                    <div>
                                        <h3>{getCropName(varietyModalCrop, lang)} — {t('modalTitle', lang)}</h3>
                                        <p className="modal-crop-subtitle">
                                            {varietyModalData?.botanical_genus && (
                                                <span><strong>Botanical Name:</strong> <em>{varietyModalData.botanical_genus}</em> • </span>
                                            )}
                                            <span><strong>{varietyModalData?.varieties_count || 0}</strong> {t('varietiesAvailable', lang)}</span>
                                            {varietyModalData?.price_range && (
                                                <span> • {t('priceRangeLabel', lang)}: <strong>{varietyModalData.price_range.display}</strong></span>
                                            )}
                                        </p>
                                    </div>
                                </div>
                                <button className="modal-close-btn" onClick={() => setVarietyModalCrop(null)} title={t('closeModal', lang)}>✕</button>
                            </div>

                            {/* Modal Controls Toolbar */}
                            <div className="variety-modal-toolbar">
                                <div className="modal-search-box">
                                    <input
                                        type="text"
                                        placeholder="Search by variety name, traits, or soil..."
                                        value={varietySearchQuery}
                                        onChange={(e) => setVarietySearchQuery(e.target.value)}
                                    />
                                    {varietySearchQuery && (
                                        <button className="clear-search-btn" onClick={() => setVarietySearchQuery('')}>✕</button>
                                    )}
                                </div>

                                <div className="modal-filter-pills">
                                    <button
                                        className={`filter-pill ${varietyFilterSeason === 'all' ? 'active' : ''}`}
                                        onClick={() => setVarietyFilterSeason('all')}
                                    >
                                        {t('filterAllSeason', lang)}
                                    </button>
                                    <button
                                        className={`filter-pill ${varietyFilterSeason === 'Kharif' ? 'active' : ''}`}
                                        onClick={() => setVarietyFilterSeason('Kharif')}
                                    >
                                        {t('filterKharif', lang)}
                                    </button>
                                    <button
                                        className={`filter-pill ${varietyFilterSeason === 'Rabi' ? 'active' : ''}`}
                                        onClick={() => setVarietyFilterSeason('Rabi')}
                                    >
                                        {t('filterRabi', lang)}
                                    </button>
                                    <button
                                        className={`filter-pill ${varietyFilterSeason === 'Summer' ? 'active' : ''}`}
                                        onClick={() => setVarietyFilterSeason('Summer')}
                                    >
                                        {t('filterSummer', lang)}
                                    </button>
                                </div>

                                <div className="modal-sort-box">
                                    <label>Sort:</label>
                                    <select value={varietySortBy} onChange={(e) => setVarietySortBy(e.target.value)}>
                                        <option value="match">{t('sortByMatch', lang)}</option>
                                        <option value="yield">{t('sortByYield', lang)}</option>
                                        <option value="price">{t('sortByPrice', lang)}</option>
                                        <option value="duration">{t('sortByDuration', lang)}</option>
                                    </select>
                                </div>
                            </div>

                            {/* Modal Body with Varieties Grid */}
                            <div className="variety-modal-body">
                                {loadingVarietyModal ? (
                                    <div className="variety-modal-loading">
                                        <span className="spinner"></span>
                                        <p>Loading cultivars and agronomic data...</p>
                                    </div>
                                ) : (
                                    (() => {
                                        let vars = (varietyModalData?.varieties || []).slice();

                                        // Helper: determine if a variety's season matches a given filter
                                        const matchesSeason = (varSeason: string, filter: string): boolean => {
                                            const s = (varSeason || '').toLowerCase();
                                            const f = filter.toLowerCase();

                                            // Perennial / Year-round crops grow in all seasons
                                            if (s.includes('perennial') || s.includes('year-round') || s.includes('annual')) {
                                                return true;
                                            }

                                            // Direct match (handles "Kharif", "Rabi", "Kharif/Rabi", "Rabi/Summer")
                                            if (s.includes(f)) return true;

                                            // Map month-based seasons to Kharif / Rabi / Summer
                                            // Kharif: Jun-Nov (monsoon crops)
                                            // Rabi: Oct-Mar (winter crops)
                                            // Summer: Feb-Jun (summer crops)
                                            const monthMap: Record<string, string[]> = {
                                                'jan': ['rabi'],
                                                'feb': ['rabi', 'summer'],
                                                'mar': ['rabi', 'summer'],
                                                'apr': ['summer'],
                                                'may': ['summer', 'kharif'],
                                                'jun': ['kharif', 'summer'],
                                                'jul': ['kharif'],
                                                'aug': ['kharif'],
                                                'sep': ['kharif'],
                                                'oct': ['kharif', 'rabi'],
                                                'nov': ['kharif', 'rabi'],
                                                'dec': ['rabi']
                                            };

                                            // Parse month-based format like "Jun-Aug", "Apr-Jul", "Feb-May"
                                            const monthPattern = s.match(/^([a-z]{3})\s*[-–]\s*([a-z]{3})$/);
                                            if (monthPattern) {
                                                const startMonth = monthPattern[1];
                                                const endMonth = monthPattern[2];
                                                const startSeasons = monthMap[startMonth] || [];
                                                const endSeasons = monthMap[endMonth] || [];
                                                const allSeasons = [...new Set([...startSeasons, ...endSeasons])];
                                                return allSeasons.includes(f);
                                            }

                                            return false;
                                        };

                                        // Search filter
                                        if (varietySearchQuery.trim()) {
                                            const q = varietySearchQuery.toLowerCase();
                                            vars = vars.filter(v => 
                                                v.name.toLowerCase().includes(q) ||
                                                (v.characteristics && v.characteristics.toLowerCase().includes(q)) ||
                                                (v.soil_type && v.soil_type.toLowerCase().includes(q)) ||
                                                (v.scientific_species && v.scientific_species.toLowerCase().includes(q)) ||
                                                (v.season && v.season.toLowerCase().includes(q)) ||
                                                (v.climate && v.climate.toLowerCase().includes(q)) ||
                                                (v.growing_months && v.growing_months.toLowerCase().includes(q)) ||
                                                (v.best_regions && v.best_regions.some(r => r.toLowerCase().includes(q)))
                                            );
                                        }

                                        // Season filter
                                        if (varietyFilterSeason !== 'all') {
                                            vars = vars.filter(v => matchesSeason(v.season, varietyFilterSeason));
                                        }

                                        // Sorting
                                        if (varietySortBy === 'yield') {
                                            vars.sort((a, b) => (b.yield_per_acre || 0) - (a.yield_per_acre || 0));
                                        } else if (varietySortBy === 'price') {
                                            vars.sort((a, b) => (b.price || 0) - (a.price || 0));
                                        } else if (varietySortBy === 'duration') {
                                            vars.sort((a, b) => (a.duration_days || 999) - (b.duration_days || 999));
                                        } else {
                                            // Best Match: sort by real suitability score
                                            vars.sort((a, b) => (b.suitability_score || 0) - (a.suitability_score || 0));
                                        }

                                        if (vars.length === 0) {
                                            return (
                                                <div className="no-varieties-found">
                                                    <p>No varieties match the selected filters. Select "All Seasons" or clear your search.</p>
                                                </div>
                                            );
                                        }

                                        return (
                                            <div className="modal-varieties-grid">
                                                {vars.map((v, idx) => {
                                                    const isSelectedVar = selectedVariety === v.name;
                                                    const matchScore = v.suitability_score || 0;

                                                    return (
                                                        <div key={v.name} className={`modal-variety-card ${isSelectedVar ? 'selected-card' : ''}`}>
                                                            {/* Top Banner Image with Overlay */}
                                                            <div className="modal-var-image-wrap">
                                                                <img
                                                                    src={resolveCropImage(varietyModalCrop || undefined, v.image_url, varietyModalData?.crop_image)}
                                                                    alt={v.name}
                                                                    className="modal-var-img"
                                                                    onError={(e: any) => {
                                                                        e.target.onerror = null;
                                                                        e.target.src = resolveCropImage(varietyModalCrop || undefined, v.image_url, varietyModalData?.crop_image);
                                                                    }}
                                                                />
                                                                <div className="modal-var-img-overlay">
                                                                    <span className="var-rank-badge">#{idx + 1}</span>
                                                                    <span className="var-suitability-tag">
                                                                        {matchScore}% match
                                                                    </span>
                                                                </div>
                                                            </div>

                                                            {/* Variety Info Content */}
                                                            <div className="modal-var-content">
                                                                <div className="modal-var-header-row">
                                                                    <div>
                                                                        <h4 className="modal-var-title">{v.name}</h4>
                                                                    </div>
                                                                    <span className="modal-var-price-badge">
                                                                        {v.price_display || `₹${v.price}/${varietyModalData?.unit || 'quintal'}`}
                                                                    </span>
                                                                </div>

                                                                {/* Top Match Highlight (1 clean, high-signal chip) */}
                                                                {v.match_highlights && v.match_highlights.length > 0 && (
                                                                    <div className="modal-var-match-single">
                                                                        <span className="match-reason-single-chip">
                                                                            ✓ {v.match_highlights.find((h: string) => h.toLowerCase().includes('soil') || h.toLowerCase().includes('match')) || v.match_highlights[0]}
                                                                        </span>
                                                                    </div>
                                                                )}

                                                                {/* Essential Agronomic Specifications (Clean 4-Item Grid) */}
                                                                <div className="modal-var-spec-grid">
                                                                    <div className="var-spec-item">
                                                                        <span className="spec-label">{t('expectedYieldLabel', lang)}</span>
                                                                        <span className="spec-value highlight-yield">{v.expected_yield || `${v.yield_per_acre} ${varietyModalData?.unit || 'q'}/acre`}</span>
                                                                    </div>
                                                                    <div className="var-spec-item">
                                                                        <span className="spec-label">{t('maturityPeriod', lang)}</span>
                                                                        <span className="spec-value">{v.maturity_period || `${v.duration_days} days`}</span>
                                                                    </div>
                                                                    <div className="var-spec-item">
                                                                        <span className="spec-label">{t('growingSeason', lang)}</span>
                                                                        <span className="spec-value">{v.growing_months || v.season}</span>
                                                                    </div>
                                                                    <div className="var-spec-item">
                                                                        <span className="spec-label">{t('soilRequirements', lang)}</span>
                                                                        <span className="spec-value">{(v.soil_type || 'Loamy').split(';')[0].split(',').slice(0, 2).join(', ').trim()}{v.soil_ph_range ? ` (pH ${v.soil_ph_range[0]}-${v.soil_ph_range[1]})` : ''}</span>
                                                                    </div>
                                                                </div>

                                                                {/* Key Agronomic Trait */}
                                                                {v.characteristics && (
                                                                    <p className="modal-var-desc">
                                                                        💡 {v.characteristics}
                                                                    </p>
                                                                )}

                                                                {/* Action Button */}
                                                                <button
                                                                    type="button"
                                                                    className={`modal-select-btn ${isSelectedVar ? 'selected' : ''}`}
                                                                    onClick={() => {
                                                                        setSelectedCrop(varietyModalCrop);
                                                                        setSelectedVariety(isSelectedVar ? '' : v.name);
                                                                        setVarietyModalCrop(null);
                                                                        setActiveTab('prices');
                                                                        setShowMarketResult(true);
                                                                        setSelectedMarketResult({
                                                                            crop: varietyModalCrop,
                                                                            price: v.price_display || `₹${v.price}`,
                                                                            trend: 'stable'
                                                                        });
                                                                        fetchCropSpecies(varietyModalCrop);
                                                                        setTimeout(() => {
                                                                            const el = document.getElementById('profit-estimator-box');
                                                                            if (el) el.scrollIntoView({ behavior: 'smooth' });
                                                                        }, 200);
                                                                    }}
                                                                >
                                                                    {isSelectedVar ? 'Selected for Estimator' : t('selectVarietyForProfit', lang)}
                                                                </button>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        );
                                    })()
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

export default App;
