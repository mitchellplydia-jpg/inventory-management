"""
Tests for restocking API endpoints (recommendations and submitted orders).
"""
import pytest


class TestRestockingRecommendations:
    """Test suite for the restocking recommendation endpoint."""

    def test_get_recommendations_structure(self, client):
        """Test getting recommendations returns properly structured items."""
        response = client.get("/api/restocking/recommendations?budget=500")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        for item in data:
            assert "item_sku" in item
            assert "item_name" in item
            assert "quantity" in item
            assert "unit_cost" in item
            assert "line_total" in item
            assert "lead_time_days" in item
            assert "trend" in item
            assert isinstance(item["quantity"], int)
            assert item["quantity"] > 0

    def test_recommendations_respect_budget(self, client):
        """Test that total recommended cost never exceeds the given budget."""
        response = client.get("/api/restocking/recommendations?budget=500")
        assert response.status_code == 200

        data = response.json()
        total_cost = sum(item["line_total"] for item in data)
        assert total_cost <= 500

    def test_recommendations_zero_budget(self, client):
        """Test that a zero budget produces no recommendations."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data == []

    def test_recommendations_no_budget_param_defaults_to_zero(self, client):
        """Test that omitting budget defaults to no recommendations."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 200

        data = response.json()
        assert data == []

    def test_recommendations_prioritize_increasing_trend(self, client):
        """Test that with ample budget, increasing-trend items are included."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        skus = [item["item_sku"] for item in data]
        # Increasing-trend items with a positive demand gap should be recommended
        assert "WDG-001" in skus
        assert "GSK-203" in skus
        assert "FLT-405" in skus

        # Increasing-trend items should be ranked ahead of non-increasing items
        first_non_increasing_index = next(
            (i for i, item in enumerate(data) if item["trend"] != "increasing"), len(data)
        )
        increasing_indexes = [i for i, item in enumerate(data) if item["trend"] == "increasing"]
        assert all(i <= first_non_increasing_index for i in increasing_indexes)

    def test_recommendations_exclude_non_positive_gap_items(self, client):
        """Test that items with no forecasted growth (e.g. decreasing) are excluded."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()

        skus = [item["item_sku"] for item in data]
        # MTR-304 has decreasing demand (forecasted < current), should never be recommended
        assert "MTR-304" not in skus

    def test_recommendation_line_totals_are_correct(self, client):
        """Test that line_total equals quantity * unit_cost for each item."""
        response = client.get("/api/restocking/recommendations?budget=2000")
        data = response.json()

        for item in data:
            expected = round(item["quantity"] * item["unit_cost"], 2)
            assert abs(item["line_total"] - expected) < 0.01


class TestRestockingOrders:
    """Test suite for submitting and retrieving restocking orders."""

    def test_create_restocking_order(self, client):
        """Test submitting a restocking order with recommended items."""
        rec_response = client.get("/api/restocking/recommendations?budget=1000")
        items = rec_response.json()
        assert len(items) > 0

        response = client.post("/api/restocking-orders", json={
            "budget": 1000,
            "items": items
        })
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["status"] == "Processing"
        assert "created_date" in data

        expected_total = round(sum(item["line_total"] for item in items), 2)
        assert abs(data["total_cost"] - expected_total) < 0.01

        expected_max_lead_time = max(item["lead_time_days"] for item in items)
        assert data["max_lead_time_days"] == expected_max_lead_time

    def test_create_restocking_order_empty_items(self, client):
        """Test that submitting an order with no items is rejected."""
        response = client.post("/api/restocking-orders", json={
            "budget": 500,
            "items": []
        })
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_get_restocking_orders_includes_submitted(self, client):
        """Test that a submitted order appears in the list of restocking orders."""
        rec_response = client.get("/api/restocking/recommendations?budget=800")
        items = rec_response.json()
        assert len(items) > 0

        create_response = client.post("/api/restocking-orders", json={
            "budget": 800,
            "items": items
        })
        new_order_id = create_response.json()["id"]

        list_response = client.get("/api/restocking-orders")
        assert list_response.status_code == 200

        data = list_response.json()
        assert isinstance(data, list)
        assert any(order["id"] == new_order_id for order in data)
