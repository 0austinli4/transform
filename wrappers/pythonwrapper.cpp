// pythonwrapper.cpp
#include <string>
#include <cstring>
#include <iostream>

extern "C" {
    const char* AsyncCppRequest(const char* opTypesJSON, const char* keysJSON, const char* value, const char* oldValue, size_t* out_length) {
        try {
            // Process the inputs
            std::string op_types = opTypesJSON ? opTypesJSON : "";
            std::string keys = keysJSON ? keysJSON : "";
            std::string val = value ? value : "";
            std::string old_val = oldValue ? oldValue : "";
            
            // make app request
            std::string result = "Processed: " + op_types + ", " + keys;
            
            // Allocate memory for the result string using malloc
            // This is important for cross-language compatibility
            char* result_cstr = static_cast<char*>(malloc(result.length() + 1));
            if (!result_cstr) {
                std::cerr << "Memory allocation failed" << std::endl;
                return nullptr;
            }
            
            std::memcpy(result_cstr, result.c_str(), result.length());
            result_cstr[result.length()] = '\0';  // Null-terminate
            
            // Set the output length
            if (out_length) {
                *out_length = result.length();
            }
            
            return result_cstr;
        } catch (const std::exception& e) {
            std::cerr << "Error in AsyncCppRequest: " << e.what() << std::endl;
            return nullptr;
        }
    }
    
    // Function to free memory allocated by AsyncCppRequest
    void FreeString(const char* ptr) {
        if (ptr) {
            free(const_cast<char*>(ptr));  // Use free instead of delete[]
        }
    }
}