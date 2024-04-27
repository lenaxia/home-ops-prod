package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHandleFind(t *testing.T) {
	// Setup Redis and other dependencies if needed
	preloadTestData(t) // Preload data into Redis and the local AI service for testing
	// ...

	// Create a request to pass to our handler
	findReq := FindRequest{
		Store: "test_store",
		Key:   DataItem{Content: "input text"},
		Topk:  100,
		Limit: 10,
	}
	jsonReq, err := json.Marshal(findReq)
	if err != nil {
		t.Fatal(err)
	}
	req, err := http.NewRequest("POST", "/find", bytes.NewBuffer(jsonReq))
	if err != nil {
		t.Fatal(err)
	}

	// Create a ResponseRecorder to record the response
	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(handleFind)

	// Preload data into Redis and the local AI service for testing
	preloadTestData(t)

	// Create a request to pass to our handler
	findReq := FindRequest{
		Store: "test_store",
		Key:   DataItem{Content: "input text"},
		Topk:  100,
		Limit: 10,
	}
	jsonReq, err := json.Marshal(findReq)
	if err != nil {
		t.Fatal(err)
	}
	req, err := http.NewRequest("POST", "/find", bytes.NewBuffer(jsonReq))
	if err != nil {
		t.Fatal(err)
	}

	// Create a ResponseRecorder to record the response
	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(handleFind)

	// Perform the request
	handler.ServeHTTP(rr, req)

	// Check the status code is what we expect
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	expectedItems := []DataItem{
		{Content: "related content 1", Similarity: 0.9},
		{Content: "related content 2", Similarity: 0.8},
		// ... more expected items ...
	}
	var resp FindResponse
	if err := json.Unmarshal(rr.Body.Bytes(), &resp); err != nil {
		t.Errorf("handler returned unexpected body: got %v want valid JSON FindResponse", rr.Body.String())
	}
	if !reflect.DeepEqual(resp.Items, expectedItems) {
		t.Errorf("handler returned unexpected body: got %v want %v", resp.Items, expectedItems)
	}

	// Test scenario when Redis is enabled but the key is not present
	// ...

	// Test scenario when Redis is enabled and the key is present
	// ...

	// Test scenario when Redis is disabled
	// ...

	// Test scenario when the local AI service is not available
	// ...

	// Test scenario when the find request to the local AI service fails
	// ...

	// Add more test scenarios here
	// ...
}
