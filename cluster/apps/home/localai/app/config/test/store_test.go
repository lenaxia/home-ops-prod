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

	// Define the store request payload
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

	// Define the store request payload
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

	// Define the store request payload
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

		// Verify that data is stored in Redis
		for _, item := range storeReq.Items {
			redisKey := fmt.Sprintf("%s:%s", storeReq.Store, item.Content)
			storedValue, err := redisClient.Get(redisKey).Result()
			if err != nil {
				t.Errorf("expected data to be stored in Redis for key %s, but got an error: %v", redisKey, err)
			}
			if storedValue == "" {
				t.Errorf("expected data to be stored in Redis for key %s, but it was empty", redisKey)
			}
		}

		// Verify that data is stored in Redis
		// ... (mock verification logic for Redis storage) ...

		// Verify that data is stored in Redis
		// ... (mock verification logic for Redis storage) ...
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

		// Verify that data is stored in the local AI service
		// ... (mock verification logic for local AI service storage) ...
		// This would involve calling a mock local AI service endpoint to check if the data was stored
		// Since we don't have the actual local AI service code, we'll assume the function exists
		if !mockLocalAIStoreVerification(storeReq) {
			t.Errorf("expected data to be stored in the local AI service, but it was not")
		}

		// Verify that data is stored in the local AI service
		// ... (mock verification logic for local AI service storage) ...

		// Verify that data is stored in the local AI service
		// ... (mock verification logic for local AI service storage) ...
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
	// Test storing data with Redis disabled and verifying storage
	t.Run("Store with Redis disabled and verify storage", func(t *testing.T) {
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

		// Verify that data is stored in the local AI service
		// ... (mock verification logic for local AI service storage) ...
		// This would involve calling a mock local AI service endpoint to check if the data was stored
		// Since we don't have the actual local AI service code, we'll assume the function exists
		if !mockLocalAIStoreVerification(storeReq) {
			t.Errorf("expected data to be stored in the local AI service, but it was not")
		}

		// Verify that data is stored in the local AI service
		// ... (mock verification logic for local AI service storage) ...

		// Verify that data is stored in the local AI service
		// ... (mock verification logic for local AI service storage) ...
	})

	// Additional test scenarios can be added here
	// ...

	// Test storing data when the local AI service fails to store
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
