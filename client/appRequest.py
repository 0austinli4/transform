import ctypes
import json
import os

print("Python: Starting script")

# Get the absolute path to the library
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(script_dir, 'libmdlclient.so')

# Load the library
try:
    print("Loading shared library")
    library = ctypes.cdll.LoadLibrary(lib_path)
except OSError as e:
    raise OSError(f"Failed to load library at {lib_path}. Error: {e}")

# REQUEST
app_request = library.AsyncAppRequest
app_request.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
app_request.restype = ctypes.c_char_p

# RESPONSE
app_response = library.AsyncAppResponse
app_response.argtypes = [ctypes.c_char_p]
app_response.restype = ctypes.c_char_p

def AppRequest(op_type, key, value=None):
    try:
        print(f"Python: Starting appRequest with op_type={op_type}, key={key}, value={value}")
        # Convert operation type and key to JSON arrays
        op_types_json = json.dumps(op_type).encode('utf-8')
        keys_json = json.dumps(int(key)).encode('utf-8')  # Ensure key is an integer
        
        print(f"Python: Encoded JSON - op_types={op_types_json}, keys={keys_json}")
        
        # Call Go function
        result_ptr = app_request(op_types_json, keys_json)
        print(f"Python: Received result pointer: {result_ptr}")
        
        if not result_ptr:
            raise Exception("Null pointer returned from Go function")

        # Convert result to Python string and parse JSON
        result_str = ctypes.string_at(result_ptr).decode('utf-8')
        print(f"Python: Decoded result string: {result_str}")
        
        result = json.loads(result_str)
        print(f"Python: Parsed JSON result: {result}")

        if not result['success']:
            raise Exception("Golang code did not succeed execution")
        
        return result['result']
    except Exception as e:
        print(f"Python: Error in appRequest: {str(e)}")
        raise


def AppResponse(keys):
    try:
        print(f"Python: Starting appResponse with keys={keys}")
        
        # Convert keys to JSON
        key_json = json.dumps(keys).encode('utf-8')
        print(f"Python: Encoded JSON - keys={key_json}")
        
        # Call Go function
        result_ptr = app_response(key_json)
        print(f"Python: Received result pointer: {result_ptr}")
            
        if not result_ptr:
            raise Exception("Null pointer returned from Go function")
            
        # Convert result to Python string and parse JSON
        result_str = ctypes.string_at(result_ptr).decode('utf-8')
        print(f"Python: Decoded result string: {result_str}")
        
        result = json.loads(result_str)
        print(f"Python: Parsed JSON result: {result}")

        if not result['success']:
            raise Exception(f"Golang code failed: {result['result']}")

        # The result field could be different types depending on the operation
        # For example, it might be an int64 for some operations
        # or a string for error messages
        return result['result']  # This could be any JSON-serializable type
    except Exception as e:
        print(f"Python: Error in appResponse: {str(e)}")
        raise


# Example usage
if __name__ == "__main__":
    key = 123
    value = 456
    # Example GET request
    result = appRequest("GET", key)
    final_answer = appResponse(result)
    print(f"Python: GET result, Result: {result}")
    print(f"Python: Final answer, Result: {final_answer}")
    