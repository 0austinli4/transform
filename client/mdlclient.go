package main

// #include <stdlib.h>
import "C"
import (
	"encoding/json"
	"fmt"
	"sync"
	"unsafe"
)

type Response struct {
	Success bool        `json:"success"`
	Result  interface{} `json:"result"`
}

type AsynchClient struct {
	proposeReplyChan chan interface{}
	opCount          int32
	fast             bool
	noLeader         bool
	seqnos           map[int]int64
	SSA              bool
	latestReceived   int32
	mu               *sync.Mutex
	mapMu            *sync.Mutex
	repliesMap       map[int32]interface{}
}

// NewAsynchClient creates a new instance of AsynchClient
func NewAsynchClient() *AsynchClient {
	return &AsynchClient{
		proposeReplyChan: make(chan interface{}),
		seqnos:           make(map[int]int64),
		mu:               &sync.Mutex{},
		mapMu:            &sync.Mutex{},
		repliesMap:       make(map[int32]interface{}),
	}
}

//export AsyncAppRequest
func AsyncAppRequest(opTypesJSON *C.char, keysJSON *C.char) *C.char {
    fmt.Println("Go: Starting AppRequest")
    defer fmt.Println("Go: Finishing AppRequest")

    var opTypeStr string
    var key int64

    // Convert C strings to Go strings
    opTypesStr := C.GoString(opTypesJSON)
    keysStr := C.GoString(keysJSON)
    
    fmt.Printf("Go: Received strings - opTypes: %s, keys: %s\n", opTypesStr, keysStr)

    // Unmarshal JSON
    if err := json.Unmarshal([]byte(opTypesStr), &opTypeStr); err != nil {
        fmt.Printf("Go: Error unmarshaling opTypes: %v\n", err)
        response := Response{
            Success: false,
            Result:  err.Error(),
        }
        jsonResponse, _ := json.Marshal(response)
        return C.CString(string(jsonResponse))
    }

    if err := json.Unmarshal([]byte(keysStr), &key); err != nil {
        fmt.Printf("Go: Error unmarshaling key: %v\n", err)
        response := Response{
            Success: false,
            Result:  err.Error(),
        }
        jsonResponse, _ := json.Marshal(response)
        return C.CString(string(jsonResponse))
    }

    // Convert string to Operation
    var op Operation
    switch opTypeStr {
    case "GET":
        op = GET
    case "PUT":
        op = PUT
    case "CAS":
        op = CAS
    default:
        response := Response{
            Success: false,
            Result:  fmt.Sprintf("Unknown operation type: %s", opTypeStr),
        }
        jsonResponse, _ := json.Marshal(response)
        return C.CString(string(jsonResponse))
    }

    var stateOps []Operation
    stateOps = append(stateOps, op)

    var keys []int64
    keys = append(keys, key)

    // Create client instance and call AppRequestMock
    client := NewAsynchClient()
    success, result := client.AppRequestMock(stateOps, keys)
    response := Response{
        Success: success,
        Result:  result,
    }

    // Marshal response to JSON
    jsonResponse, err := json.Marshal(response)
    if err != nil {
        fmt.Printf("Go: Error marshaling response: %v\n", err)
        errResponse := Response{
            Success: false,
            Result:  err.Error(),
        }
        jsonResponse, _ = json.Marshal(errResponse)
    }

    return C.CString(string(jsonResponse))
}

func (c *AsynchClient) AppRequestMock(opTypes []Operation, keys []int64) (bool, int64) {
	if len(opTypes) > 0 && len(keys) > 0 {
		fmt.Printf("Mock AppRequest called with operation: %v and key: %v\n", opTypes[0], keys[0])
	} else {
		fmt.Println("Mock AppRequest called with empty operation or keys")
	}

	// check operation type
	if opTypes[0] == GET {
		fmt.Println("GET")
	} else if opTypes[0] == PUT {
		fmt.Println("PUT")
	} else {
		fmt.Println("COMPARE AND SWAP")
	}
	return true, 1234
}

//export FreeString
func FreeString(str *C.char) {
	C.free(unsafe.Pointer(str))
}

//export AsyncAppResponse
func AsyncAppResponse(keysJSON *C.char) *C.char {
    fmt.Println("Go: Starting AppResponse")
    defer fmt.Println("Go: Finishing AppResponse")

    var key int32
    // Convert C string to Go string
    keysStr := C.GoString(keysJSON)
    fmt.Printf("Go: Received string - keys: %s\n", keysStr)

    // Unmarshal JSON
    if err := json.Unmarshal([]byte(keysStr), &key); err != nil {
        fmt.Printf("Go: Error unmarshaling key: %v\n", err)
        response := Response{
            Success: false,
            Result:  err.Error(),
        }
        jsonResponse, _ := json.Marshal(response)
        return C.CString(string(jsonResponse))
    }

    // Create client instance and call AppResponseMock
    client := NewAsynchClient()
    result, success := client.AppResponseMock(key)
    response := Response{
        Success: success,
        Result:  result,  
    }

    // Marshal response to JSON
    jsonResponse, err := json.Marshal(response)
    if err != nil {
        fmt.Printf("Go: Error marshaling response: %v\n", err)
        errResponse := Response{
            Success: false,
            Result:  err.Error(),
        }
        jsonResponse, _ = json.Marshal(errResponse)
    }

    return C.CString(string(jsonResponse))
}

func (c *AsynchClient) AppResponseMock(commandId int32) ([]string, bool) {
    // Mock response with array of strings
    return []string{"a", "b", "c"}, true
}

func main() {}