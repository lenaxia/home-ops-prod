package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHandleStore(t *testing.T) {
	// Setup Redis and other dependencies if needed
	// ...

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
}
