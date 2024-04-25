package main

import "reflect"
import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHandleStore(t *testing.T) {
	// Setup Redis and other dependencies if needed
	preloadTestData(t) // Preload data into Redis and the local AI service for testing
	// ...

	// Preload data into Redis and the local AI service for testing
	preloadTestData(t)

	// Test storing data with Redis enabled
	t.Run("Store with Redis enabled", func(t *testing.T) {
		// Mock Redis being enabled
		mockRedis(true)

		// Perform the store request
		handler.ServeHTTP(rr, req)

		// Check the status code is what we expect
		if status := rr.Code; status != http.StatusOK {
			t.Errorf("handler returned wrong status code with Redis enabled: got %v want %v", status, http.StatusOK)
		}

		// Check the response body is what we expect
		expected := `{"status":"ok"}`
		if rr.Body.String() != expected {
			t.Errorf("handler returned unexpected body with Redis enabled: got %v want %v", rr.Body.String(), expected)
		}
	})

	// Test storing data with Redis disabled
	t.Run("Store with Redis disabled", func(t *testing.T) {
		// Mock Redis being disabled
		mockRedis(false)

		// Perform the store request
		handler.ServeHTTP(rr, req)

		// Check the status code is what we expect
		if status := rr.Code; status != http.StatusOK {
			t.Errorf("handler returned wrong status code with Redis disabled: got %v want %v", status, http.StatusOK)
		}

		// Check the response body is what we expect
		expected := `{"status":"ok"}`
		if rr.Body.String() != expected {
			t.Errorf("handler returned unexpected body with Redis disabled: got %v want %v", rr.Body.String(), expected)
		}
	})

	// Test storing data when the local AI service fails
	t.Run("Store with local AI service failure", func(t *testing.T) {
		// Mock local AI service failure
		mockLocalAIServiceFailure()

		// Perform the store request
		handler.ServeHTTP(rr, req)

		// Check the status code is what we expect
		if status := rr.Code; status != http.StatusInternalServerError {
			t.Errorf("handler returned wrong status code with local AI service failure: got %v want %v", status, http.StatusInternalServerError)
		}
	})
	preloadTestData(t)

	// Create a request to pass to our handler
	storeReq := StoreRequest{
		Store: "test_store",
		Items: []DataItem{
			{Content: "test content 1"},
			{Content: "test content 2"},
		},
	}
	jsonReq, err := json.Marshal(storeReq)
	if err != nil {
		t.Fatal(err)
	}
	req, err := http.NewRequest("POST", "/store", bytes.NewBuffer(jsonReq))
	if err != nil {
		t.Fatal(err)
	}

	// Create a ResponseRecorder to record the response
	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(handleStore)

	// Perform the request
	handler.ServeHTTP(rr, req)

	// Check the status code is what we expect
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	// Check the response body is what we expect
	expected := `{"status":"ok"}`
	if rr.Body.String() != expected {
		t.Errorf("handler returned unexpected body: got %v want %v", rr.Body.String(), expected)
	}

	// Test scenario when Redis is enabled but fails to store
	// ...

	// Test scenario when the embedding service is not available
	// ...

	// Test scenario when the store request to the local AI service fails
	// ...

	// Test scenario when Redis is enabled but fails to store
	// ...

	// Test scenario when the embedding service is not available
	// ...

	// Test scenario when the store request to the local AI service fails
	// ...
}
	// Test scenario when Redis is enabled but fails to store
	t.Run("Redis enabled but fails to store", func(t *testing.T) {
		// Mock Redis being enabled and simulate a failure to store data
		mockRedisFailure()

		// Perform the request
		handler.ServeHTTP(rr, req)

		// Check the status code is what we expect
		if status := rr.Code; status != http.StatusInternalServerError {
			t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusInternalServerError)
		}

		// Check the response body for an error message
		expected := "Failed to store data in Redis"
		if !strings.Contains(rr.Body.String(), expected) {
			t.Errorf("handler returned unexpected body: got %v want to include %v", rr.Body.String(), expected)
		}
	})

	// ... Additional test scenarios for embedding service not available and store request failure ...
