#!/usr/bin/env python3
"""Tests for the data cleansing pipeline."""

from __future__ import annotations

import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_DIR, "scripts"))

from clean_fuelcheck import is_ev_only, normalize_brand_group, parse_fc_address, pivot_prices
from clean_google import parse_address, title_case_name
from merge_matched import confidence_label, haversine_meters


def test_google_name_all_caps():
    assert title_case_name("SPEEDWAY WEST RYDE") == "Speedway West Ryde"


def test_google_name_all_lower_bp():
    assert title_case_name("bp") == "BP"


def test_google_name_mixed_caps():
    assert title_case_name("BP PUTNEY") == "BP Putney"


def test_google_name_preserves_existing_acronyms():
    assert title_case_name("EG Ampol West Ryde") == "EG Ampol West Ryde"


def test_google_address_standard():
    street, suburb, state = parse_address("924 Victoria Rd, West Ryde NSW")
    assert street == "924 Victoria Rd"
    assert suburb == "West Ryde"
    assert state == "NSW"


def test_google_address_empty():
    assert parse_address("") == ("", "", "")


def test_google_address_none():
    assert parse_address(None) == ("", "", "")


def test_google_address_without_state():
    street, suburb, state = parse_address("123 Main St, Sydney")
    assert street == "123 Main St"
    assert suburb == "Sydney"
    assert state == ""


def test_fuelcheck_address_standard():
    street, suburb, state, postcode = parse_fc_address("924 Victoria Rd, WEST RYDE NSW 2114")
    assert street == "924 Victoria Rd"
    assert suburb == "West Ryde"
    assert state == "NSW"
    assert postcode == "2114"


def test_fuelcheck_address_two_word_suburb():
    street, suburb, state, postcode = parse_fc_address("172 Hector St, CHESTER HILL NSW 2162")
    assert street == "172 Hector St"
    assert suburb == "Chester Hill"
    assert state == "NSW"
    assert postcode == "2162"


def test_fuelcheck_address_with_extra_comma_in_street():
    street, suburb, state, postcode = parse_fc_address(
        "286-288 Pennant Hills Road, Cnr Adderton Road, Carlingford NSW 2118"
    )
    assert street == "286-288 Pennant Hills Road, Cnr Adderton Road"
    assert suburb == "Carlingford"
    assert state == "NSW"
    assert postcode == "2118"


def test_fuelcheck_address_corner_without_comma():
    street, suburb, state, postcode = parse_fc_address("Raymond St & Church St, Parramatta NSW 2150")
    assert street == "Raymond St & Church St"
    assert suburb == "Parramatta"
    assert state == "NSW"
    assert postcode == "2150"


def test_ev_only_true():
    assert is_ev_only({"prices": [{"fuel_type": "EV", "price": 0}]}) is True


def test_ev_only_false_for_mixed_station():
    assert is_ev_only(
        {"prices": [{"fuel_type": "EV", "price": 0}, {"fuel_type": "U91", "price": 250}]}
    ) is False


def test_ev_only_true_for_no_prices():
    assert is_ev_only({"prices": []}) is True


def test_price_pivot_standard():
    result, outlier = pivot_prices(
        [{"fuel_type": "E10", "price": 252.9}, {"fuel_type": "P98", "price": 278.9}]
    )
    assert result["fc_price_E10_cents"] == 252.9
    assert result["fc_price_P98_cents"] == 278.9
    assert result["fc_price_U91_cents"] == ""
    assert outlier is False


def test_price_pivot_outlier():
    result, outlier = pivot_prices([{"fuel_type": "E85", "price": 475.0}])
    assert result["fc_price_E85_cents"] == 475.0
    assert outlier is True


def test_price_pivot_ignores_ev():
    result, outlier = pivot_prices([{"fuel_type": "EV", "price": 0}])
    assert "fc_price_EV_cents" not in result
    assert outlier is False


def test_brand_group_normalization():
    assert normalize_brand_group("Ampol Foodary") == "Ampol"
    assert normalize_brand_group("Reddy Express") == "Shell"
    assert normalize_brand_group("BP") == "BP"


def test_haversine_same_point():
    assert haversine_meters(-33.8, 151.1, -33.8, 151.1) == 0


def test_haversine_known_short_distance():
    distance = haversine_meters(-33.8025054, 151.1003341, -33.802513, 151.100336)
    assert distance < 5


def test_haversine_beyond_threshold():
    distance = haversine_meters(-33.81, 151.10, -33.70, 151.10)
    assert distance > 10000


def test_confidence_label_bands():
    assert confidence_label(30) == "high"
    assert confidence_label(65) == "medium"
    assert confidence_label(95) == "low"
