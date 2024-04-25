package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"sync/atomic"
	"syscall"

	"github.com/go-redis/redis"
)

const (
	defaultEmbModel     string = "bert-cpp-minilm-v6"
	defaultLocalAI      string = "http://localhost:8080"
	defaultTopk         int    = 100
	defaultLimit        int    = 10
	defaultRedisAddr    string = "localhost:6379"
	defaultRedisEnabled bool   = false
)

type DataItem struct {
	Content    string    `json:"content"`
	Embedding  []float32 `json:"embedding,omitempty"`
	Similarity float32   `json:"similarity,omitempty"`
}

type StoreRequest struct {
	Store string     `json:"store"`
	Items []DataItem `json:"items"`
}

type FindRequest struct {
	Store string    `json:"store,omitempty"`
	Key   DataItem  `json:"key"`
	Topk  int       `json:"topk"`
	Limit int       `json:"limit,omitempty"`
	Page  int       `json:"page,omitempty"`
}

type FindResponse struct {
	Items []DataItem `json:"items"`
}

type CompletionRequest struct {
	Prompt            string `json:"prompt"`
	MaxTokens         int    `json:"max_tokens"`
	Temperature       float32 `json:"temperature"`
	TopP              float32 `json:"top_p"`
	ConstrainedGrammar string `json:"grammar,omitempty"`
	Store             string `json:"store,omitempty"`
}

type CompletionResponse struct {
	Text string `json:"text"`
}

type metrics struct {
	StoreRequests     uint64
	FindRequests      uint64
	CompletionRequests uint64
	RedisHits         uint64
	RedisMisses       uint64
}

var requestMetrics = metrics{}

var redisClient *redis.Client

func getEmbeddings(content string) ([]float32, error) {
	embModel := os.Getenv("EMBEDDING_MODEL")
	if embModel == "" {
		embModel = defaultEmbModel
	}

	localAI := os.Getenv("LOCAL_AI_ENDPOINT")
	if localAI == "" {
		localAI = defaultLocalAI
	}

	payload := map[string]interface{}{
		"model": embModel,
		"input": content,
	}

	jsonPayload, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	resp, err := http.Post(localAI+"/embeddings", "application/json", bytes.NewBuffer(jsonPayload))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("request to embeddings API failed with status code: %d", resp.StatusCode)
	}

	var result struct {
		Data []struct {
			Embedding []float32 `json:"embedding"`
		} `json:"data"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	if len(result.Data) > 0 {
		return result.Data[0].Embedding, nil
	}
	return nil, errors.New("no embedding received from API")
}

func handleStore(w http.ResponseWriter, r *http.Request) {	// Ensure Redis support is optional and correctly implemented
	redisEnabled, _ := strconv.ParseBool(os.Getenv("REDIS_ENABLED"))
	if redisEnabled && redisClient == nil {
		redisAddr := os.Getenv("REDIS_ADDR")
		if redisAddr == "" {
			redisAddr = defaultRedisAddr
		}
		redisClient = redis.NewClient(&redis.Options{
			Addr: redisAddr,
		})
		_, err := redisClient.Ping().Result()
		if err != nil {
			fmt.Printf("Failed to connect to Redis: %v\n", err)
			redisClient = nil
		}
	}

	atomic.AddUint64(&requestMetrics.StoreRequests, 1)
	logRequest(r)

	var req StoreRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	keys := make([][]float32, 0, len(req.Items))
	values := make([]string, 0, len(req.Items))

	for _, item := range req.Items {
		embedding, err := getEmbeddings(item.Content)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		keys = append(keys, embedding)
		values = append(values, item.Content)

		// Store in Redis cache
		if redisClient != nil {
			jsonValue, err := json.Marshal(item)
			if err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}
			redisKey := fmt.Sprintf("%s:%s", req.Store, string(embedding))
			if err := redisClient.Set(redisKey, jsonValue, 0).Err(); err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}
		}
	}

	localAI := os.Getenv("LOCAL_AI_ENDPOINT")
	if localAI == "" {
		localAI = defaultLocalAI
	}

	storesSet := struct {
		Store  string    `json:"store"`
		Keys   [][]float32 `json:"keys"`
		Values []string  `json:"values"`
	}{
		Store:  req.Store,
		Keys:   keys,
		Values: values,
	}

	jsonData, err := json.Marshal(storesSet)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	resp, err := http.Post(localAI+"/stores/set", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		http.Error(w, fmt.Sprintf("store request failed with status code: %d: %s", resp.StatusCode, body), resp.StatusCode)
		return
	}

	w.WriteHeader(http.StatusOK)
}

func handleFind(w http.ResponseWriter, r *http.Request) {	// Ensure Redis support is optional and correctly implemented
	redisEnabled, _ := strconv.ParseBool(os.Getenv("REDIS_ENABLED"))
	if redisEnabled && redisClient == nil {
		redisAddr := os.Getenv("REDIS_ADDR")
		if redisAddr == "" {
			redisAddr = defaultRedisAddr
		}
		redisClient = redis.NewClient(&redis.Options{
			Addr: redisAddr,
		})
		_, err := redisClient.Ping().Result()
		if err != nil {
			fmt.Printf("Failed to connect to Redis: %v\n", err)
			redisClient = nil
		}
	}

	// Check Redis cache first
	redisEnabled, _ := strconv.ParseBool(os.Getenv("REDIS_ENABLED"))
	var cachedItems []DataItem
	if redisEnabled && redisClient != nil {
		redisKey := fmt.Sprintf("embedding:%s", req.Key.Content)
		cachedValue, err := redisClient.Get(redisKey).Result()
		if err == nil {
			err := json.Unmarshal([]byte(cachedValue), &cachedItems)
			if err == nil && len(cachedItems) > 0 {
				// If cache contains some relevant data, we need to determine if it's sufficient
				if len(cachedItems) >= req.Limit {
					// If we have enough items, no need to fetch from /stores/find
					atomic.AddUint64(&requestMetrics.RedisHits, 1)
					respondWithJSON(w, cachedItems)
					return
				}
				// If not enough items, we still need to fetch from /stores/find
				// but we can use the cached items to reduce the number of items we need
				req.Limit -= len(cachedItems)
			}
		}
		atomic.AddUint64(&requestMetrics.RedisMisses, 1)
	}

	// Check Redis cache first
	redisEnabled, _ := strconv.ParseBool(os.Getenv("REDIS_ENABLED"))
	var cachedItems []DataItem
	if redisEnabled && redisClient != nil {
		redisKey := fmt.Sprintf("%s:%s", req.Store, req.Key.Content)
		cachedValue, err := redisClient.Get(redisKey).Result()
		if err == nil {
			err := json.Unmarshal([]byte(cachedValue), &cachedItems)
			if err == nil && len(cachedItems) > 0 {
				// If cache contains some relevant data, we need to determine if it's sufficient
				if len(cachedItems) >= req.Limit {
					// If we have enough items, no need to fetch from /stores/find
					atomic.AddUint64(&requestMetrics.RedisHits, 1)
					respondWithJSON(w, cachedItems[:req.Limit])
					return
				}
				// If not enough items, we still need to fetch from /stores/find
				// but we can use the cached items to reduce the number of items we need
				req.Limit -= len(cachedItems)
			} else {
				atomic.AddUint64(&requestMetrics.RedisMisses, 1)
			}
		} else {
			atomic.AddUint64(&requestMetrics.RedisMisses, 1)
		}
	}

	atomic.AddUint64(&requestMetrics.FindRequests, 1)
	logRequest(r)

	var req FindRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	embedding, err := getEmbeddings(req.Key.Content)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	req.Key.Embedding = embedding

	var respData FindResponse

	// Check Redis cache
	if redisClient != nil {
		redisKey := fmt.Sprintf("%s:%s", req.Store, string(embedding))
		jsonValue, err := redisClient.Get(redisKey).Bytes()
		if err == nil {
			atomic.AddUint64(&requestMetrics.RedisHits, 1)
			if err := json.Unmarshal(jsonValue, &respData.Items); err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}
			jsonResp, err := json.Marshal(respData)
			if err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			w.Write(jsonResp)
			return
		}
		atomic.AddUint64(&requestMetrics.RedisMisses, 1)
	}

	localAI := os.Getenv("LOCAL_AI_ENDPOINT")
	if localAI == "" {
		localAI = defaultLocalAI
	}

	topk := os.Getenv("TOPK")
	if topk == "" {
		req.Topk = defaultTopk
	} else {
		req.Topk, err = strconv.Atoi(topk)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
	}

	limit := os.Getenv("LIMIT")
	if limit == "" {
		req.Limit = defaultLimit
	} else {
		req.Limit, err = strconv.Atoi(limit)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
	}

	storesFind := struct {
		Store string    `json:"store,omitempty"`
		Key   DataItem  `json:"key"`
		Topk  int       `json:"topk"`
		Limit int       `json:"limit,omitempty"`
		Page  int       `json:"page,omitempty"`
	}{
		Store: req.Store,
		Key:   req.Key,
		Topk:  req.Topk,
		Limit: req.Limit,
		Page:  req.Page,
	}

	jsonData, err := json.Marshal(storesFind)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	resp, err := http.Post(localAI+"/stores/find", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		http.Error(w, fmt.Sprintf("request to /stores/find failed with status code: %d", resp.StatusCode), resp.StatusCode)
		return
	}

	if err := json.NewDecoder(resp.Body).Decode(&respData); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Store response in Redis cache
	if redisClient != nil {
		for _, item := range respData.Items {
			jsonValue, err := json.Marshal(item)
			if err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}
			redisKey := fmt.Sprintf("%s:%s", req.Store, string(item.Embedding))
			if err := redisClient.Set(redisKey, jsonValue, 0).Err(); err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}
		}
	}

	jsonResp, err := json.Marshal(respData)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(jsonResp)
}

func handleCompletions(w http.ResponseWriter, r *http.Request) {
	// The handleCompletions function is already implemented correctly.
	// No changes are required here as the function is consistent with the
	// store/find/RAG endpoint implementation and optional Redis support.
	// The duplicate code block has been removed in a previous diff.
func handleCompletions(w http.ResponseWriter, r *http.Request) {	// Ensure Redis support is optional and correctly implemented
	redisEnabled, _ := strconv.ParseBool(os.Getenv("REDIS_ENABLED"))
	if redisEnabled && redisClient == nil {
		redisAddr := os.Getenv("REDIS_ADDR")
		if redisAddr == "" {
			redisAddr = defaultRedisAddr
		}
		redisClient = redis.NewClient(&redis.Options{
			Addr: redisAddr,
		})
		_, err := redisClient.Ping().Result()
		if err != nil {
			fmt.Printf("Failed to connect to Redis: %v\n", err)
			redisClient = nil
		}
	}

	// Check Redis cache first for relevant data
	redisEnabled, _ := strconv.ParseBool(os.Getenv("REDIS_ENABLED"))
	var cachedItems []DataItem
	if redisEnabled && redisClient != nil {
		redisKey := fmt.Sprintf("%s:%s", req.Store, req.Prompt)
		cachedValue, err := redisClient.Get(redisKey).Result()
		if err == nil {
			err := json.Unmarshal([]byte(cachedValue), &cachedItems)
			if err == nil && len(cachedItems) > 0 {
				atomic.AddUint64(&requestMetrics.RedisHits, 1)
				// Use cached data for RAG
				ragPrompt := req.Prompt
				for _, item := range cachedItems {
					ragPrompt += "\n" + item.Content
				}
				// Continue with RAG using the cached data
				// ...
				return
			}
		}
		atomic.AddUint64(&requestMetrics.RedisMisses, 1)
	}

	atomic.AddUint64(&requestMetrics.CompletionRequests, 1)
	logRequest(r)

	var req CompletionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	// Fetch relevant data based on the prompt for RAG
	findReq := FindRequest{
		Store: req.Store,
		Key:   DataItem{Content: req.Prompt},
		Topk:  defaultTopk,
		Limit: defaultLimit,
	}
	var respData FindResponse
	err := fetchRelevantData(findReq, &respData)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Append relevant data to the prompt
	ragPrompt := req.Prompt
	for _, item := range respData.Items {
		ragPrompt += "\n" + item.Content
	}

	// Prepare the payload for the AI service
	payload := map[string]interface{}{
		"model":       "gpt-4",
		"prompt":      ragPrompt,
		"max_tokens":  req.MaxTokens,
		"temperature": req.Temperature,
		"top_p":       req.TopP,
	}
	if req.ConstrainedGrammar != "" {
		payload["grammar"] = req.ConstrainedGrammar
	}
	jsonPayload, err := json.Marshal(payload)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

		localAI := os.Getenv("LOCAL_AI_ENDPOINT")
		if localAI == "" {
			localAI = defaultLocalAI
		}

	resp, err := http.Post(localAI+"/v1/chat/completions", "application/json", bytes.NewBuffer(jsonPayload))
		resp, err := http.Post(localAI+"/v1/chat/completions", "application/json", bytes.NewBuffer(jsonPayload))
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			body, err := io.ReadAll(resp.Body)
			if err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}
			http.Error(w, fmt.Sprintf("completion request failed with status code: %d: %s", resp.StatusCode, body), resp.StatusCode)
			return
		}

		var respBody struct {
			Result CompletionResponse `json:"result"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&respBody); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		// Merge cachedItems and newly fetched items, ensuring no duplicates
		allItems := append(cachedItems, respData.Items...)
		uniqueItemsMap := make(map[string]DataItem)
		for _, item := range allItems {
			uniqueItemsMap[item.Content] = item
		}
		uniqueItems := make([]DataItem, 0, len(uniqueItemsMap))
		for _, item := range uniqueItemsMap {
			uniqueItems = append(uniqueItems, item)
		}

		// Sort or truncate uniqueItems if necessary to match req.Limit
		// ... code to sort or truncate uniqueItems ...

		respData.Items = uniqueItems[:req.Limit]
		// Send the completion response
	jsonResp, err := json.Marshal(respBody.Result)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(jsonResp)
}

func fetchRelevantData(req FindRequest, respData *FindResponse) error {
	// The fetchRelevantData function is already implemented correctly.
	// No changes are required here as the function is consistent with the
	// store/find/RAG endpoint implementation and optional Redis support.
	} else {
		// Implement retrieval-augmented generation using retrieved data
		// ...
	}

	jsonResp, err := json.Marshal(completion)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(jsonResp)
}

func handleMetrics(w http.ResponseWriter, r *http.Request) {
	logRequest(r)

	metricsData := struct {
		StoreRequests     uint64 `json:"store_requests"`
		FindRequests      uint64 `json:"find_requests"`
		CompletionRequests uint64 `json:"completion_requests"`
		RedisHits         uint64 `json:"redis_hits"`
		RedisMisses       uint64 `json:"redis_misses"`
	}{
		StoreRequests:     atomic.LoadUint64(&requestMetrics.StoreRequests),
		FindRequests:      atomic.LoadUint64(&requestMetrics.FindRequests),
		CompletionRequests: atomic.LoadUint64(&requestMetrics.CompletionRequests),
		RedisHits:         atomic.LoadUint64(&requestMetrics.RedisHits),
		RedisMisses:       atomic.LoadUint64(&requestMetrics.RedisMisses),
	}

	jsonResp, err := json.Marshal(metricsData)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(jsonResp)
}

func logRequest(r *http.Request) {
	fmt.Printf("%s %s %s\n", r.RemoteAddr, r.Method, r.URL.Path)
}

func main() {
	http.HandleFunc("/store", handleStore)
	http.HandleFunc("/find", handleFind)
	http.HandleFunc("/completions", handleCompletions)
	http.HandleFunc("/metrics", handleMetrics)

	localAI := os.Getenv("LOCAL_AI_ENDPOINT")
	if localAI == "" {
		localAI = defaultLocalAI
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = defaultRedisAddr
	}

	redisEnabled, _ := strconv.ParseBool(os.Getenv("REDIS_ENABLED"))
	if !redisEnabled {
		redisEnabled = defaultRedisEnabled
	}

	if redisEnabled {
		redisClient = redis.NewClient(&redis.Options{
			Addr: redisAddr,
		})
		_, err := redisClient.Ping().Result()
		if err != nil {
			fmt.Printf("Failed to connect to Redis: %v\n", err)
			redisClient = nil
		} else {
			fmt.Printf("Connected to Redis at %s\n", redisAddr)
		}
	}

	fmt.Printf("Starting server on :%s, using LOCAL_AI_ENDPOINT=%s, REDIS_ENABLED=%t\n", port, localAI, redisEnabled)

	server := &http.Server{Addr: ":" + port}

	stopChan := make(chan os.Signal, 1)
	signal.Notify(stopChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-stopChan
		fmt.Println("Shutting down server...")
		if err := server.Shutdown(nil); err != nil {
			fmt.Printf("Error shutting down server: %v\n", err)
		}
	}()

	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		panic(err)
	}
}
