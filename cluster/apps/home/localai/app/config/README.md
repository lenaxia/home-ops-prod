# AI Completion Service

This Go program provides a RESTful API for handling various operations related to text completion and retrieval-augmented generation (RAG) using an external AI service and a data store.

## Features

- **Store Data**: Store text data along with their embeddings in an external data store.
- **Find Similar Data**: Retrieve similar text data from the external data store based on a given input text.
- **Completions with Constrained Grammar**: Generate text completions with a constrained grammar using the external AI service.
- **Retrieval-Augmented Generation (RAG)**: Generate text completions using retrieved data from the external data store (not yet implemented).
- **Redis Cache**: Optional support for Redis cache to improve response times for frequently accessed data.
- **Metrics**: Expose metrics for monitoring request counts and Redis cache hits/misses.

## Testing

The application includes a test suite for the API endpoints (`/store`, `/find`, `/completions`, and `/metrics`). The tests are located in the `test` directory and are designed to verify the functionality of each endpoint, including interactions with Redis and the local AI service.

### Current Test Coverage

- **Store Endpoint**: Tests verify that data is stored correctly in Redis when enabled, and in the local AI service when Redis is disabled. Error handling is also tested for failures in Redis and the local AI service.
- **Find Endpoint**: Tests check data retrieval with various Redis states (enabled with key present, enabled with key missing, and disabled) and handle local AI service retrieval failures.
- **Completions Endpoint**: Tests ensure that text completions are generated correctly with Redis enabled (with and without relevant data in cache) and disabled, and handle local AI service generation failures.
- **Metrics Endpoint**: Tests validate that metrics data is accurately returned.

### Additional Work Needed

To fully implement the test suite, the following tasks need to be completed:

- Implement mock functions to simulate Redis and local AI service behavior.
- Add assertions to verify the response body contains the expected results for both success and error scenarios.
- Create utility functions for common test setup tasks, such as preloading data and creating mock responses.
- Expand test scenarios to cover edge cases and additional error conditions.
- Integrate the test suite with a continuous integration (CI) system to run tests automatically on code changes.

### Running Tests

To run the tests, navigate to the `test` directory and use the Go test command:

```sh
go test -v ./...
```

This will execute all tests and provide verbose output. Ensure that any required environment variables are set before running the tests.

## Configuration

The program can be configured using environment variables:

- `EMBEDDING_MODEL` (default: `bert-cpp-minilm-v6`): The embedding model to be used for generating text embeddings.
- `LOCAL_AI_ENDPOINT` (default: `http://localhost:8080`): The URL of the local AI service.
- `TOPK` (default: `100`): The number of top similar items to retrieve.
- `LIMIT` (default: `10`): The maximum number of items to return.
- `REDIS_ADDR` (default: `localhost:6379`): The address of the Redis server.
- `REDIS_ENABLED` (default: `false`): Whether to enable Redis caching or not.
- `PORT` (default: `8080`): The port on which the server should listen.

## API Endpoints

### `/store`

**Method**: POST

**Description**: Store text data along with their embeddings in the external data store and Redis cache (if enabled).

**Request Body**:

```json
{
  "store": "store_name",
  "items": [
    {
      "content": "text_data_1"
    },
    {
      "content": "text_data_2"
    }
  ]
}
```

### `/find`

**Method**: POST

**Description**: Retrieve similar text data from the external data store based on a given input text. The results are also cached in Redis (if enabled).

**Request Body**:

```json
{
  "store": "store_name",
  "key": {
    "content": "input_text"
  },
  "topk": 100,
  "limit": 10,
  "page": 0
}
```

### `/completions`

**Method**: POST

**Description**: Generate text completions using the external AI service. If the `grammar` field is provided, the completion will be constrained by the provided grammar. Otherwise, retrieval-augmented generation (RAG) is expected (not yet implemented).

**Request Body**:

```json
{
  "prompt": "input_text",
  "max_tokens": 100,
  "temperature": 0.7,
  "top_p": 1.0,
  "grammar": "optional_grammar_definition",
  "store": "store_name_for_rag"
}
```

### `/metrics`

**Method**: GET

**Description**: Retrieve metrics for monitoring request counts and Redis cache hits/misses.

**Response Body**:

```json
{
  "store_requests": 10,
  "find_requests": 20,
  "completion_requests": 15,
  "redis_hits": 100,
  "redis_misses": 50
}
```

## Running the Server

## Testing

The application includes a test suite for the API endpoints (`/store`, `/find`, `/completions`, and `/metrics`). The tests are located in the `test` directory and are designed to verify the functionality of each endpoint, including interactions with Redis and the local AI service.

### Current Test Coverage

- **Store Endpoint**: Tests verify that data is stored correctly in Redis when enabled, and in the local AI service when Redis is disabled. Error handling is also tested for failures in Redis and the local AI service.
- **Find Endpoint**: Tests check data retrieval with various Redis states (enabled with key present, enabled with key missing, and disabled) and handle local AI service retrieval failures.
- **Completions Endpoint**: Tests ensure that text completions are generated correctly with Redis enabled (with and without relevant data in cache) and disabled, and handle local AI service generation failures.
- **Metrics Endpoint**: Tests validate that metrics data is accurately returned.

### Additional Work Needed

To fully implement the test suite, the following tasks need to be completed:

- Implement mock functions to simulate Redis and local AI service behavior.
- Add assertions to verify the response body contains the expected results for both success and error scenarios.
- Create utility functions for common test setup tasks, such as preloading data and creating mock responses.
- Expand test scenarios to cover edge cases and additional error conditions.
- Integrate the test suite with a continuous integration (CI) system to run tests automatically on code changes.

### Running Tests

To run the tests, navigate to the `test` directory and use the Go test command:

```sh
go test -v ./...
```

This will execute all tests and provide verbose output. Ensure that any required environment variables are set before running the tests.

1. Clone the repository or download the source code.
2. Build the program using `go build`.
3. Set the desired environment variables (e.g., `export LOCAL_AI_ENDPOINT=http://localhost:8080`).
4. Run the compiled binary.

The server should now be running and listening on the configured port (default: `8080`).

## Future Improvements

- Implement retrieval-augmented generation (RAG) using the retrieved data from the external data store.
- Add support for more configuration options and fine-tuning parameters for the completion and RAG processes.
- Improve error handling and logging.
- Add more comprehensive unit tests and integration tests.
- Implement caching mechanisms for embeddings to improve performance.
