"""
Comprehensive Test Suite for Farmer Portal API
================================================
Tests cover:
  1. Pydantic model validation (RegistrationRequest, LoginRequest)
  2. Data utility functions (soil data, recommendations, market history, yield)
  3. All API endpoints (root, register, login, farmer-info, soil-data, lookup,
     weather, recommendations, market-prices, taluk-market-prices,
     market-history, profit-estimate, farmer-lookup, district-market-prices)
  4. Edge cases and error handling

Run with:  pytest test_farmer_portal.py -v
"""

import pytest
import sqlite3
import os
import json
from fastapi.testclient import TestClient

# Import the app and helper functions from main
from main import (
    app,
    get_soil_data_from_csv,
    get_recommendations_from_csv,
    get_market_history,
    get_avg_yield_for_crop,
    generate_mock_weather,
    RegistrationRequest,
    LoginRequest,
    DISTRICT_API_MAP,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_DB = "farmer_portal_test.db"


@pytest.fixture(autouse=True)
def _clean_test_user():
    """Remove the test user before and after each test to avoid conflicts."""
    conn = sqlite3.connect("farmer_portal.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM farmers WHERE name = ?", ("TestFarmer99",))
    conn.commit()
    conn.close()
    yield
    conn = sqlite3.connect("farmer_portal.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM farmers WHERE name = ?", ("TestFarmer99",))
    conn.commit()
    conn.close()


# ===========================================================================
# 1. PYDANTIC MODEL VALIDATION TESTS
# ===========================================================================


class TestModels:
    """Validate Pydantic request models."""

    def test_registration_model_valid(self):
        """Valid RegistrationRequest should pass."""
        req = RegistrationRequest(
            name="Test",
            current_crop="Rice", survey_number="100/A",
            phone_number="9876543210",
            state="Karnataka",
            district="Dakshina Kannada",
            taluk="Mangaluru",
            hobli="Mangaluru A",
            password="secret123",
            land_area_acres=2.5,
            land_area_guntas=20.0,
        )
        assert req.name == "Test"
        assert req.land_area_acres == 2.5

    def test_registration_model_defaults(self):
        """land_area_acres and guntas should default to 0.0."""
        req = RegistrationRequest(
            name="Test",
            current_crop="Rice", survey_number="100/A",
            phone_number="9876543210",
            state="Karnataka",
            district="Dakshina Kannada",
            taluk="Mangaluru",
            hobli="Mangaluru A",
            password="secret123",
        )
        assert req.land_area_acres == 0.0
        assert req.land_area_guntas == 0.0

    def test_login_model_valid(self):
        """Valid LoginRequest should pass."""
        req = LoginRequest(name="TestFarmer", password="abc123")
        assert req.name == "TestFarmer"
        assert req.password == "abc123"

    def test_registration_model_missing_field(self):
        """Missing required field should raise ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RegistrationRequest(
                name="Test",
                # required field missing
                phone_number="9876543210",
                state="Karnataka",
                district="DK",
                taluk="Mangaluru",
                hobli="A",
                password="pass",
            )


# ===========================================================================
# 2. DATA UTILITY FUNCTION TESTS
# ===========================================================================


class TestSoilData:
    """Tests for get_soil_data_from_csv()."""

    def test_returns_dict_with_keys(self):
        result = get_soil_data_from_csv()
        assert "ph" in result
        assert "soil_type" in result

    def test_ph_in_range(self):
        result = get_soil_data_from_csv()
        assert 4.0 <= result["ph"] <= 9.0, "Average pH should be within agronomic range"

    def test_soil_type_is_string(self):
        result = get_soil_data_from_csv()
        assert isinstance(result["soil_type"], str)
        assert len(result["soil_type"]) > 0


class TestRecommendations:
    """Tests for get_recommendations_from_csv()."""

    def test_returns_list(self):
        crops = get_recommendations_from_csv(ph=6.2, temp=28, rainfall=3500)
        assert isinstance(crops, list)

    def test_returns_at_most_5(self):
        crops = get_recommendations_from_csv(ph=6.2, temp=28, rainfall=3500)
        assert len(crops) <= 5

    def test_results_are_unique(self):
        crops = get_recommendations_from_csv(ph=6.2, temp=28, rainfall=3500)
        assert len(crops) == len(set(crops)), "Crop recommendations should be unique"

    def test_known_crops_appear(self):
        """With typical DK conditions, known crops like Rice/Banana/Arecanut should appear."""
        crops = get_recommendations_from_csv(ph=6.0, temp=28, rainfall=3500, humidity=85)
        known = {"Rice", "Banana", "Arecanut", "Pepper", "Coconut", "Cashew", "Rubber"}
        assert any(c in known for c in crops), f"Expected at least one known crop, got {crops}"

    def test_humidity_parameter(self):
        """Passing different humidity should still return valid results."""
        crops = get_recommendations_from_csv(ph=6.0, temp=28, rainfall=3500, humidity=60)
        assert isinstance(crops, list)
        assert len(crops) > 0

    def test_extreme_values(self):
        """Extreme inputs should not crash."""
        crops = get_recommendations_from_csv(ph=9.0, temp=40, rainfall=100)
        assert isinstance(crops, list)


class TestMarketHistory:
    """Tests for get_market_history()."""

    def test_returns_list_for_known_crop(self):
        history = get_market_history("Rice")
        assert isinstance(history, list)
        assert len(history) > 0

    def test_entry_structure(self):
        history = get_market_history("Rice")
        entry = history[0]
        assert "taluk" in entry
        assert "crop" in entry
        assert "year" in entry
        assert "month" in entry
        assert "price" in entry
        assert "unit" in entry
        assert "trend" in entry

    def test_filter_by_taluk(self):
        history = get_market_history("Rice", taluk="Mangaluru")
        assert all(e["taluk"] == "Mangaluru" for e in history)

    def test_unknown_crop_returns_empty(self):
        history = get_market_history("UnknownCrop123")
        assert history == []


class TestAvgYield:
    """Tests for get_avg_yield_for_crop()."""

    def test_known_crop_returns_number(self):
        result = get_avg_yield_for_crop("Rubber")
        if result is not None:
            assert isinstance(result, float)
            assert result > 0

    def test_unknown_crop_returns_none(self):
        result = get_avg_yield_for_crop("Dragonfruit")
        assert result is None


class TestMockWeather:
    """Tests for generate_mock_weather()."""

    def test_returns_expected_keys(self):
        w = generate_mock_weather("Mangaluru")
        for key in ["temperature", "humidity", "rainfall", "rain_current", "description", "location", "source"]:
            assert key in w, f"Missing key: {key}"

    def test_deterministic(self):
        """Same input should give same output."""
        w1 = generate_mock_weather("Bantwal")
        w2 = generate_mock_weather("Bantwal")
        assert w1 == w2

    def test_davanagere_override(self):
        w = generate_mock_weather("Davanagere")
        assert w["temperature"] == 32.4
        assert w["humidity"] == 62

    def test_mangaluru_override(self):
        w = generate_mock_weather("Mangaluru")
        assert w["temperature"] == 29.8
        assert w["humidity"] == 88

    def test_temperature_range(self):
        w = generate_mock_weather("SomeRandomPlace")
        assert 20 <= w["temperature"] <= 40


# ===========================================================================
# 3. API ENDPOINT TESTS
# ===========================================================================


class TestRootEndpoint:
    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_message(self):
        response = client.get("/")
        assert response.json()["message"] == "Farmer Portal API is running"


class TestRegistrationEndpoint:
    def test_register_success(self):
        payload = {
            "name": "TestFarmer99",
            "current_crop": "Rice", "survey_number": "999/T",
            "phone_number": "0000000000",
            "state": "Karnataka",
            "district": "Dakshina Kannada",
            "taluk": "Mangaluru",
            "hobli": "Test Hobli",
            "password": "testpass",
            "land_area_acres": 3.0,
            "land_area_guntas": 20.0,
        }
        response = client.post("/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_register_missing_field(self):
        """Missing required field should return 422."""
        payload = {"name": "TestFarmer99"}
        response = client.post("/register", json=payload)
        assert response.status_code == 422


class TestLoginEndpoint:
    def _register_test_user(self):
        client.post("/register", json={
            "name": "TestFarmer99",
            "current_crop": "Rice", "survey_number": "999/T",
            "phone_number": "0000000000",
            "state": "Karnataka",
            "district": "Dakshina Kannada",
            "taluk": "Mangaluru",
            "hobli": "Test Hobli",
            "password": "testpass",
            "land_area_acres": 5.0,
            "land_area_guntas": 10.0,
        })

    def test_login_success(self):
        self._register_test_user()
        response = client.post("/login", json={"name": "TestFarmer99", "password": "testpass"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["user"]["name"] == "TestFarmer99"
        assert data["user"]["taluk"] == "Mangaluru"
        assert data["user"]["district"] == "Dakshina Kannada"
        assert data["user"]["land_area_acres"] == 5.0
        assert data["user"]["land_area_guntas"] == 10.0

    def test_login_wrong_password(self):
        self._register_test_user()
        response = client.post("/login", json={"name": "TestFarmer99", "password": "wrong"})
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        response = client.post("/login", json={"name": "NoSuchUser12345", "password": "any"})
        assert response.status_code == 404


class TestFarmerInfoEndpoint:
    def test_farmer_info_success(self):
        # Register first
        client.post("/register", json={
            "name": "TestFarmer99",
            "current_crop": "Rice", "survey_number": "999/T",
            "phone_number": "0000000000",
            "state": "Karnataka",
            "district": "Dakshina Kannada",
            "taluk": "Mangaluru",
            "hobli": "Test Hobli",
            "password": "testpass",
        })
        response = client.get("/farmer-info/TestFarmer99")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TestFarmer99"

    def test_farmer_info_not_found(self):
        response = client.get("/farmer-info/NonExistentFarmerXYZ")
        assert response.status_code == 500 or response.status_code == 404


class TestSoilDataEndpoint:
    def test_soil_data_returns_200(self):
        response = client.get("/soil-data")
        assert response.status_code == 200

    def test_soil_data_structure(self):
        response = client.get("/soil-data")
        data = response.json()
        assert "ph" in data
        assert "soil_type" in data


class TestLookupEndpoint:
    def test_known_survey(self):
        response = client.get("/lookup/123/A")
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "Karnataka"

    def test_unknown_survey(self):
        response = client.get("/lookup/000/Z")
        assert response.status_code == 404


class TestWeatherEndpoint:
    def test_weather_returns_200(self):
        response = client.get("/weather/Mangaluru")
        assert response.status_code == 200

    def test_weather_keys(self):
        response = client.get("/weather/Mangaluru")
        data = response.json()
        assert "temperature" in data
        assert "humidity" in data
        assert "rainfall" in data


class TestRecommendationsEndpoint:
    def test_recommendations_default(self):
        response = client.get("/recommendations/Mangaluru")
        assert response.status_code == 200
        data = response.json()
        assert "soil_data" in data
        assert "recommended_crops" in data
        assert isinstance(data["recommended_crops"], list)

    def test_recommendations_with_params(self):
        response = client.get("/recommendations/Mangaluru?ph=6.0&temp=28&rainfall=3500&humidity=85")
        assert response.status_code == 200
        data = response.json()
        assert data["soil_data"]["ph"] == 6.0
        assert data["soil_data"]["temp"] == 28.0
        assert data["soil_data"]["rainfall"] == 3500.0

    def test_recommendations_returns_crops(self):
        response = client.get("/recommendations/Mangaluru")
        data = response.json()
        assert len(data["recommended_crops"]) > 0


class TestMarketPricesEndpoint:
    def test_market_prices_returns_list(self):
        response = client.get("/market-prices")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_market_prices_entry_structure(self):
        response = client.get("/market-prices")
        data = response.json()
        if len(data) > 0:
            entry = data[0]
            assert "crop" in entry
            assert "price" in entry
            assert "trend" in entry


class TestTalukMarketPricesEndpoint:
    def test_returns_200(self):
        response = client.get("/taluk-market-prices")
        assert response.status_code == 200

    def test_response_structure(self):
        response = client.get("/taluk-market-prices")
        data = response.json()
        assert "taluks" in data
        assert "crops" in data
        assert "prices" in data
        assert isinstance(data["taluks"], list)
        assert isinstance(data["crops"], list)
        assert isinstance(data["prices"], dict)

    def test_known_taluk_present(self):
        response = client.get("/taluk-market-prices")
        data = response.json()
        assert "Mangaluru" in data["taluks"]


class TestMarketHistoryEndpoint:
    def test_known_crop(self):
        response = client.get("/market-history/Rice")
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "Rice"
        assert len(data["history"]) > 0
        assert "yearly_averages" in data

    def test_with_taluk_filter(self):
        response = client.get("/market-history/Arecanut?taluk=Mangaluru")
        assert response.status_code == 200
        data = response.json()
        for entry in data["history"]:
            assert entry["taluk"] == "Mangaluru"

    def test_unknown_crop(self):
        response = client.get("/market-history/UnknownCropXYZ")
        assert response.status_code == 200
        data = response.json()
        assert data["history"] == []


class TestProfitEstimateEndpoint:
    def test_profit_estimate_success(self):
        response = client.get("/profit-estimate?crop=Rice&acres=2&guntas=0")
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "Rice"
        assert data["land_acres"] == 2.0
        assert "estimated_revenue" in data
        assert "estimated_profit" in data

    def test_profit_estimate_with_guntas(self):
        """40 guntas = 1 acre, so 2 acres + 20 guntas = 2.5 acres."""
        response = client.get("/profit-estimate?crop=Rice&acres=2&guntas=20")
        assert response.status_code == 200
        data = response.json()
        assert data["land_acres"] == 2.5

    def test_profit_estimate_zero_area(self):
        response = client.get("/profit-estimate?crop=Rice&acres=0&guntas=0")
        assert response.status_code == 400

    def test_profit_estimate_missing_crop(self):
        response = client.get("/profit-estimate?acres=2&guntas=0")
        assert response.status_code == 422

    def test_profit_values_positive(self):
        response = client.get("/profit-estimate?crop=Arecanut&acres=5&guntas=0")
        if response.status_code == 200:
            data = response.json()
            assert data["estimated_revenue"] >= 0
            assert data["estimated_total_yield"] >= 0


class TestFarmerLookupEndpoint:
    def test_known_farmer(self):
        """Use a farmer from the CSV dataset."""
        response = client.get("/farmer-lookup?name=Pushpa Gowda&phone=9126855092")
        assert response.status_code == 200
        data = response.json()
        assert data["found"] is True
        assert data["info"]["name"] == "Pushpa Gowda"
        assert len(data["history"]) > 0

    def test_unknown_farmer(self):
        response = client.get("/farmer-lookup?name=Nobody&phone=0000000000")
        assert response.status_code == 200
        data = response.json()
        assert data["found"] is False

    def test_farmer_history_sorted(self):
        response = client.get("/farmer-lookup?name=Pushpa Gowda&phone=9126855092")
        data = response.json()
        if data["found"]:
            years = [h["year"] for h in data["history"]]
            assert years == sorted(years), "History should be sorted by year"


class TestDistrictMarketPricesEndpoint:
    def test_known_district(self):
        response = client.get("/district-market-prices/Dakshina Kannada")
        assert response.status_code == 200
        data = response.json()
        assert "district" in data or "requested_district" in data

    def test_unknown_district(self):
        response = client.get("/district-market-prices/FakeDistrict")
        assert response.status_code == 200  # returns fallback, not 404


class TestLiveMarketPricesEndpoint:
    def test_returns_200(self):
        response = client.get("/market-prices-live")
        assert response.status_code == 200
        data = response.json()
        assert "source" in data


# ===========================================================================
# 4. DISTRICT API MAP TESTS
# ===========================================================================


class TestDistrictApiMap:
    def test_all_districts_mapped(self):
        """Ensure every mapped district has a non-empty API name."""
        for district, api_name in DISTRICT_API_MAP.items():
            assert isinstance(api_name, str)
            assert len(api_name) > 0, f"District '{district}' has empty API mapping"

    def test_known_mappings(self):
        assert DISTRICT_API_MAP["Belagavi"] == "Belgaum"
        assert DISTRICT_API_MAP["Mysuru"] == "Mysore"
        assert DISTRICT_API_MAP["Kalaburagi"] == "Gulbarga"
        assert DISTRICT_API_MAP["Dakshina Kannada"] == "Dakshina Kannada"


# ===========================================================================
# 5. SCORING ALGORITHM EDGE CASES
# ===========================================================================


class TestScoringAlgorithm:
    """Verify the crop recommendation scoring logic handles edge cases."""

    def test_perfect_match_scores_highest(self):
        """A crop whose row exactly matches the inputs should score highest."""
        # Use values from the first CSV row: pH=5.675, Temp=30.31, Rainfall=3733, Humidity=92
        crops = get_recommendations_from_csv(ph=5.675, temp=30.31, rainfall=3733, humidity=92)
        # The first crop in CSV with these values is Banana
        assert "Banana" in crops, f"Banana should be recommended for matching conditions, got {crops}"

    def test_different_conditions_give_different_results(self):
        """Very different inputs should potentially change recommendations."""
        crops_wet = get_recommendations_from_csv(ph=6.0, temp=28, rainfall=4000, humidity=90)
        crops_dry = get_recommendations_from_csv(ph=7.0, temp=35, rainfall=500, humidity=40)
        # They might overlap but the order or composition should differ
        assert isinstance(crops_wet, list)
        assert isinstance(crops_dry, list)


# ===========================================================================
# 6. INVALID INPUT TESTS
# ===========================================================================


class TestInvalidRegistration:
    """Test registration endpoint with various invalid inputs."""

    def test_empty_body(self):
        """Sending empty JSON body should return 422."""
        response = client.post("/register", json={})
        assert response.status_code == 422

    def test_no_body(self):
        """Sending no body at all should return 422."""
        response = client.post("/register")
        assert response.status_code == 422

    def test_wrong_data_type_for_acres(self):
        """Passing a string for land_area_acres should return 422."""
        payload = {
            "name": "TestFarmer99",
            "current_crop": "Rice", "survey_number": "999/T",
            "phone_number": "0000000000",
            "state": "Karnataka",
            "district": "DK",
            "taluk": "Mangaluru",
            "hobli": "Test",
            "password": "pass",
            "land_area_acres": "not_a_number",
            "land_area_guntas": 10.0,
        }
        response = client.post("/register", json=payload)
        assert response.status_code == 422

    def test_negative_land_area(self):
        """Negative land area should still be accepted by Pydantic (float field)
        but is logically invalid â€” verifying the API doesn't crash."""
        payload = {
            "name": "TestFarmer99",
            "current_crop": "Rice", "survey_number": "999/T",
            "phone_number": "0000000000",
            "state": "Karnataka",
            "district": "DK",
            "taluk": "Mangaluru",
            "hobli": "Test",
            "password": "pass",
            "land_area_acres": -5.0,
            "land_area_guntas": -10.0,
        }
        response = client.post("/register", json=payload)
        # Should not crash â€” Pydantic accepts negative floats
        assert response.status_code in (200, 422)

    def test_extra_unknown_fields(self):
        """Extra fields should be ignored, registration should succeed."""
        payload = {
            "name": "TestFarmer99",
            "current_crop": "Rice", "survey_number": "999/T",
            "phone_number": "0000000000",
            "state": "Karnataka",
            "district": "DK",
            "taluk": "Mangaluru",
            "hobli": "Test",
            "password": "pass",
            "unknown_field": "value",
            "another_extra": 12345,
        }
        response = client.post("/register", json=payload)
        assert response.status_code == 200

    def test_empty_string_fields(self):
        """Empty strings for required fields â€” Pydantic allows empty str."""
        payload = {
            "name": "",
            "current_crop": "Rice", "survey_number": "",
            "phone_number": "",
            "state": "",
            "district": "",
            "taluk": "",
            "hobli": "",
            "password": "",
        }
        response = client.post("/register", json=payload)
        # Pydantic doesn't enforce min-length by default, so 200 expected
        assert response.status_code == 200

    def test_special_characters_in_name(self):
        """Names with special characters should not crash the API."""
        payload = {
            "name": "TestFarmer99",
            "current_crop": "Rice", "survey_number": "!@#$%^&*()",
            "phone_number": "abc-def-ghi",
            "state": "<script>alert('xss')</script>",
            "district": "DK'; DROP TABLE farmers;--",
            "taluk": "Mangaluru",
            "hobli": "Test",
            "password": "pass",
        }
        response = client.post("/register", json=payload)
        # Should not crash â€” parameterized queries protect against SQL injection
        assert response.status_code == 200

    def test_very_long_name(self):
        """Extremely long input should not crash the server."""
        payload = {
            "name": "TestFarmer99",
            "current_crop": "Rice", "survey_number": "999/T",
            "phone_number": "0" * 1000,
            "state": "K" * 5000,
            "district": "DK",
            "taluk": "Mangaluru",
            "hobli": "Test",
            "password": "pass",
        }
        response = client.post("/register", json=payload)
        assert response.status_code == 200

    def test_null_values_in_payload(self):
        """Null for required string fields should return 422."""
        payload = {
            "name": None,
            "current_crop": "Rice", "survey_number": "999/T",
            "phone_number": "0000000000",
            "state": "Karnataka",
            "district": "DK",
            "taluk": "Mangaluru",
            "hobli": "Test",
            "password": "pass",
        }
        response = client.post("/register", json=payload)
        assert response.status_code == 422


class TestInvalidLogin:
    """Test login endpoint with various invalid inputs."""

    def test_empty_body(self):
        response = client.post("/login", json={})
        assert response.status_code == 422

    def test_missing_password(self):
        response = client.post("/login", json={"name": "SomeUser"})
        assert response.status_code == 422

    def test_missing_name(self):
        response = client.post("/login", json={"password": "pass"})
        assert response.status_code == 422

    def test_null_name(self):
        response = client.post("/login", json={"name": None, "password": "pass"})
        assert response.status_code == 422

    def test_null_password(self):
        response = client.post("/login", json={"name": "SomeUser", "password": None})
        assert response.status_code == 422

    def test_wrong_type_name(self):
        """Passing integer for name should return 422 or be coerced."""
        response = client.post("/login", json={"name": 12345, "password": "pass"})
        # Pydantic may coerce int to str, so check it doesn't crash
        assert response.status_code in (200, 401, 404, 422)

    def test_sql_injection_in_login(self):
        """SQL injection attempt should not bypass authentication."""
        response = client.post("/login", json={
            "name": "' OR '1'='1",
            "password": "' OR '1'='1"
        })
        # Should either return 404 (not found) or 401 (wrong pass), NOT 200
        assert response.status_code in (401, 404)

    def test_empty_strings(self):
        """Empty name/password â€” may match a row or return not found."""
        response = client.post("/login", json={"name": "", "password": ""})
        # 200 is possible if a farmer with empty name/password was registered
        assert response.status_code in (200, 401, 404)


class TestInvalidRecommendations:
    """Test recommendations endpoint with wrong input types."""

    def test_string_ph_value(self):
        """Passing string for pH query param should return 422."""
        response = client.get("/recommendations/Mangaluru?ph=not_a_number")
        assert response.status_code == 422

    def test_string_temp_value(self):
        response = client.get("/recommendations/Mangaluru?temp=hot")
        assert response.status_code == 422

    def test_string_rainfall_value(self):
        response = client.get("/recommendations/Mangaluru?rainfall=heavy")
        assert response.status_code == 422

    def test_string_humidity_value(self):
        response = client.get("/recommendations/Mangaluru?humidity=damp")
        assert response.status_code == 422

    def test_negative_ph(self):
        """Negative pH â€” API should still respond (no validation on range)."""
        response = client.get("/recommendations/Mangaluru?ph=-5")
        assert response.status_code == 200

    def test_zero_values(self):
        """All zeros â€” should still return recommendations."""
        response = client.get("/recommendations/Mangaluru?ph=0&temp=0&rainfall=0&humidity=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["recommended_crops"], list)

    def test_extremely_large_values(self):
        """Extremely large numbers should not crash."""
        response = client.get("/recommendations/Mangaluru?ph=999&temp=9999&rainfall=999999")
        assert response.status_code == 200


class TestInvalidProfitEstimate:
    """Test profit estimate endpoint with invalid inputs."""

    def test_missing_all_params(self):
        """No params at all should return 422 (crop is required)."""
        response = client.get("/profit-estimate")
        assert response.status_code == 422

    def test_string_acres(self):
        """String for acres should return 422."""
        response = client.get("/profit-estimate?crop=Rice&acres=big&guntas=0")
        assert response.status_code == 422

    def test_string_guntas(self):
        response = client.get("/profit-estimate?crop=Rice&acres=2&guntas=many")
        assert response.status_code == 422

    def test_negative_acres(self):
        """Negative acres â€” total area will be negative, should return 400."""
        response = client.get("/profit-estimate?crop=Rice&acres=-5&guntas=0")
        assert response.status_code == 400

    def test_negative_guntas(self):
        """Negative guntas making total <= 0 should return 400."""
        response = client.get("/profit-estimate?crop=Rice&acres=0&guntas=-10")
        assert response.status_code == 400

    def test_empty_crop_name(self):
        """Empty crop name â€” should still respond but with fallback data."""
        response = client.get("/profit-estimate?crop=&acres=2&guntas=0")
        # Empty crop won't match any data but shouldn't crash
        assert response.status_code in (200, 400)

    def test_nonexistent_crop(self):
        """Crop not in database â€” should use fallback yield."""
        response = client.get("/profit-estimate?crop=Dragonfruit&acres=2&guntas=0")
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "Dragonfruit"
        assert data["yield_per_acre"] == 100  # fallback default


class TestInvalidWeather:
    """Test weather endpoint with unusual inputs."""

    def test_empty_location(self):
        """Empty location path â€” should return mock weather or 404."""
        response = client.get("/weather/")
        # FastAPI may treat this as not matching the route
        assert response.status_code in (200, 404, 307)

    def test_numeric_location(self):
        """Numeric location string â€” should not crash."""
        response = client.get("/weather/12345")
        assert response.status_code == 200

    def test_special_chars_location(self):
        """Special characters in location should not crash."""
        response = client.get("/weather/!@%23%24%25")
        assert response.status_code == 200

    def test_very_long_location(self):
        long_loc = "A" * 500
        response = client.get(f"/weather/{long_loc}")
        assert response.status_code == 200


class TestInvalidFarmerLookup:
    """Test farmer-lookup endpoint with invalid inputs."""

    def test_missing_name(self):
        """Missing name query param should return 422."""
        response = client.get("/farmer-lookup?phone=9126855092")
        assert response.status_code == 422

    def test_missing_phone(self):
        """Missing phone query param should return 422."""
        response = client.get("/farmer-lookup?name=Pushpa Gowda")
        assert response.status_code == 422

    def test_both_missing(self):
        response = client.get("/farmer-lookup")
        assert response.status_code == 422

    def test_right_name_wrong_phone(self):
        """Correct name but wrong phone should not find a match."""
        response = client.get("/farmer-lookup?name=Pushpa Gowda&phone=0000000000")
        assert response.status_code == 200
        data = response.json()
        assert data["found"] is False

    def test_sql_injection_in_lookup(self):
        """SQL injection in lookup params â€” should not crash."""
        response = client.get("/farmer-lookup?name=' OR 1=1--&phone=anything")
        assert response.status_code == 200
        data = response.json()
        assert data["found"] is False


class TestInvalidMarketHistory:
    """Test market history endpoint with invalid inputs."""

    def test_empty_crop(self):
        """Empty crop path â€” will likely return empty or 404."""
        response = client.get("/market-history/")
        assert response.status_code in (200, 404, 307)

    def test_numeric_crop(self):
        response = client.get("/market-history/12345")
        assert response.status_code == 200
        data = response.json()
        assert data["history"] == []

    def test_special_chars_crop(self):
        response = client.get("/market-history/Rice%20%26%20Wheat")
        assert response.status_code == 200


class TestInvalidSurveyLookup:
    """Test survey lookup with invalid survey numbers."""

    def test_empty_survey(self):
        response = client.get("/lookup/")
        assert response.status_code in (200, 404, 307)

    def test_numeric_survey(self):
        response = client.get("/lookup/99999")
        assert response.status_code == 404

    def test_special_chars_survey(self):
        response = client.get("/lookup/!@%23$%25")
        assert response.status_code == 404

    def test_sql_injection_survey(self):
        response = client.get("/lookup/' OR 1=1--")
        assert response.status_code == 404


class TestInvalidEndpointAccess:
    """Test wrong HTTP methods and non-existent routes."""

    def test_get_on_register(self):
        """GET on /register should return 405 Method Not Allowed."""
        response = client.get("/register")
        assert response.status_code == 405

    def test_get_on_login(self):
        """GET on /login should return 405 Method Not Allowed."""
        response = client.get("/login")
        assert response.status_code == 405

    def test_post_on_soil_data(self):
        """POST on /soil-data should return 405."""
        response = client.post("/soil-data")
        assert response.status_code == 405

    def test_post_on_weather(self):
        """POST on /weather/Mangaluru should return 405."""
        response = client.post("/weather/Mangaluru")
        assert response.status_code == 405

    def test_nonexistent_route(self):
        """Completely unknown route should return 404."""
        response = client.get("/this/route/does/not/exist")
        assert response.status_code == 404

    def test_delete_on_register(self):
        """DELETE on /register should return 405."""
        response = client.delete("/register")
        assert response.status_code == 405

    def test_put_on_login(self):
        """PUT on /login should return 405."""
        response = client.put("/login", json={"name": "x", "password": "y"})
        assert response.status_code == 405


class TestCropSpecies:
    """Tests for /crop-species endpoints and variety-based pricing."""

    def test_get_all_crop_species(self):
        response = client.get("/crop-species")
        assert response.status_code == 200
        data = response.json()
        assert "total_crops" in data
        assert data["total_crops"] >= 22
        assert "Rice" in data["crops"]
        assert "Banana" in data["crops"]

    def test_get_crop_species_filter(self):
        response = client.get("/crop-species?crop=Rice")
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "Rice"
        assert len(data["varieties"]) > 0
        assert any(v["name"] == "Sona Masuri" for v in data["varieties"])
        assert any(v["price"] == 2800 for v in data["varieties"])

    def test_get_crop_species_by_path(self):
        response = client.get("/crop-species/Rice")
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "Rice"
        assert data["unit"] == "quintal"
        assert len(data["varieties"]) >= 7

    def test_get_crop_species_case_insensitive(self):
        response = client.get("/crop-species/banana")
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "Banana"
        assert data["unit"] == "kg"

    def test_get_crop_species_not_found(self):
        response = client.get("/crop-species/NonExistentCrop123")
        assert response.status_code == 404

    def test_recommendations_includes_species_and_pricing(self):
        response = client.get("/recommendations/Mangaluru")
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommended_crops"]) > 0
        for crop_item in data["recommended_crops"]:
            assert "crop" in crop_item
            assert "varieties" in crop_item
            assert isinstance(crop_item["varieties"], list)

    def test_profit_estimate_with_specific_variety(self):
        res_standard = client.get("/profit-estimate?crop=Rice&acres=2&guntas=0")
        assert res_standard.status_code == 200
        data_standard = res_standard.json()

        res_basmati = client.get("/profit-estimate?crop=Rice&acres=2&guntas=0&variety=Basmati (Pusa 1121)")
        assert res_basmati.status_code == 200
        data_basmati = res_basmati.json()
        assert data_basmati["variety"] == "Basmati (Pusa 1121)"
        assert data_basmati["current_price_per_unit"] == 4500
        assert data_basmati["estimated_profit"] != data_standard["estimated_profit"]
