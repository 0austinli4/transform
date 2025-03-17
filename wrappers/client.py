import ctypes
import os
import sys

# Path to the shared library (.dylib for macOS)
lib_path = os.path.join(os.path.dirname(__file__), "libexample.dylib")

# Load the library
library = ctypes.CDLL(lib_path)

# Set up function signatures
async_cpp_request = library.AsyncCppRequest
async_cpp_request.argtypes = [
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.POINTER(ctypes.c_size_t)
]
async_cpp_request.restype = ctypes.c_void_p  

# Free string function
free_string = library.FreeString
free_string.argtypes = [ctypes.c_void_p]  
free_string.restype = None

def call_cpp_function(op_types_json, keys_json, value=None, old_value=None):
    # Convert Python strings to C strings
    op_types_bytes = op_types_json.encode("utf-8") if op_types_json else None
    keys_bytes = keys_json.encode("utf-8") if keys_json else None
    value_bytes = value.encode("utf-8") if value else None
    old_value_bytes = old_value.encode("utf-8") if old_value else None

    # Prepare length output
    length = ctypes.c_size_t(0)
    length_ptr = ctypes.pointer(length)

    # Call the C++ function
    result_ptr = async_cpp_request(
        op_types_bytes, keys_bytes, value_bytes, old_value_bytes, length_ptr
    )
    
    result = None
    
    result = ctypes.string_at(result_ptr, length.value).decode("utf-8")
    free_string(result_ptr)
    
    return result
  
# Example usage
if __name__ == "__main__":
    try:
        result = call_cpp_function(
            '{"type": "read"}', '{"key": "example"}', "new_value", "old_value"
        )
        print(f"Result from C++: {result}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()