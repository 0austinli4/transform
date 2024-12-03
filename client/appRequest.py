import ctypes
import json
import os

print("Python: Starting script")

# Get the absolute path to the library
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(script_dir, 'library.so')

# Load the library
try:
    print("Loading shared library")
    library = ctypes.cdll.LoadLibrary(lib_path)
except OSError as e:
    raise OSError(f"Failed to load library at {lib_path}. Error: {e}")

# REQUEST
app_request = library.AppRequest
app_request.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
app_request.restype = ctypes.c_char_p

# RESPONSE
app_response = library.AppResponse
app_response.argtypes = [ctypes.c_char_p]
app_response.restype = ctypes.c_char_p

def appRequest(op_types, keys):
    try:
        print(f"Python: Starting appRequest with op_types={op_types}, keys={keys}")
        
        # Convert inputs to JSON strings and encode to UTF-8
        op_types_json = json.dumps(op_types).encode('utf-8')
        keys_json = json.dumps(keys).encode('utf-8')
        
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

        return result['success'], result['result']
    except Exception as e:
        print(f"Python: Error in appRequest: {str(e)}")
        raise


def appResponse(keys):
    try:
        print(f"Python: Starting appRequest with op_types={op_types}, keys={keys}")
        
        # Convert inputs to JSON strings and encode to UTF-8
        keys_json = json.dumps(keys).encode('utf-8')
        
        print(f"Python: Encoded JSON - op_types={op_types_json}, keys={keys_json}")
        
        # Call Go function
        result_ptr = app_response(keys_json)
        print(f"Python: Received result pointer: {result_ptr}")
        
        if not result_ptr:
            raise Exception("Null pointer returned from Go function")
            
        # Convert result to Python string and parse JSON
        result_str = ctypes.string_at(result_ptr).decode('utf-8')
        print(f"Python: Decoded result string: {result_str}")
        
        result = json.loads(result_str)
        print(f"Python: Parsed JSON result: {result}")

        return result['success'], result['result']
    except Exception as e:
        print(f"Python: Error in appRequest: {str(e)}")
        raise


# Example usage
if __name__ == "__main__":
    timeline_id = 123
    success, result = appRequest([{"type": "PUT"}], timeline_id)
    print(f"Python: Final result - Success: {success}")
    print(f"Python: Final result - Result: {result}")