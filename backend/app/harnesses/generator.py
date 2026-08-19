"""
Harness Generation Engine

Generates C/C++ stubs for a fuzzing target based on its input requirements.
"""

from typing import Dict, Any

def generate_harness(target_name: str, module_name: str, input_type: str, metadata: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate the files for a fuzzing harness.
    Returns a dict mapping filename to content.
    """
    
    # Extract metadata configurations
    init_code = metadata.get("init_code", "")
    cleanup_code = metadata.get("cleanup_code", "")
    headers = metadata.get("headers", [])
    
    header_includes = "\n".join([f'#include <{h}>' if not h.endswith(".h") else f'#include "{h}"' for h in headers])
    if not header_includes:
        header_includes = '#include <windows.h>\n#include <stdio.h>\n#include <stdint.h>\n#include <stdlib.h>'
        
    cpp_content = f"""// Auto-generated Harness for {target_name} in {module_name}
// Input Type: {input_type}

{header_includes}

// Forward declare the target function if needed, or include its header above.
extern "C" {{
    // Add target signature here
    // e.g. int {target_name}(uint8_t* data, size_t size);
}}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {{
    // Initialization Hook
    {init_code}

"""

    if input_type == "file":
        cpp_content += f"""    // Write Data to a temporary file
    char temp_filename[MAX_PATH];
    GetTempFileNameA(".", "fuzz", 0, temp_filename);
    
    FILE *fp = fopen(temp_filename, "wb");
    if (fp) {{
        fwrite(Data, 1, Size, fp);
        fclose(fp);
        
        // Invoke Target
        // {target_name}(temp_filename);
        
        DeleteFileA(temp_filename);
    }}
"""
    elif input_type == "buffer_and_length":
        cpp_content += f"""    // Invoke Target with buffer and length
    // {target_name}((uint8_t*)Data, Size);
"""
    elif input_type == "memory_buffer":
        cpp_content += f"""    // Invoke Target with null-terminated memory buffer
    uint8_t* null_terminated = (uint8_t*)malloc(Size + 1);
    if (null_terminated) {{
        memcpy(null_terminated, Data, Size);
        null_terminated[Size] = 0;
        
        // {target_name}(null_terminated);
        
        free(null_terminated);
    }}
"""
    else:
        cpp_content += f"""    // Unknown input type: {input_type}
    // Implement custom invocation here
"""

    cpp_content += f"""
    // Cleanup Hook
    {cleanup_code}
    
    return 0; // Non-zero return values are reserved for future use.
}}
"""

    # CMakeLists.txt
    cmake_content = f"""cmake_minimum_required(VERSION 3.10)
project(Fuzz{target_name})

set(CMAKE_CXX_STANDARD 17)

# Fuzzing requires coverage and instrumentation flags
# e.g., for LibFuzzer/Clang: -fsanitize=fuzzer
# for MSVC/WinAFL, typically compiled as a DLL or standalone executable with DynamoRIO.

add_executable(harness_{target_name} harness.cpp)
# target_link_libraries(harness_{target_name} {module_name}.lib)
"""

    # build.bat
    build_bat = f"""@echo off
echo Building harness for {target_name}...
:: Ensure MSVC environment is set up (e.g. via vcvars64.bat)
:: cl.exe /O2 /Zi /EHsc harness.cpp /link /OUT:harness.exe

:: For MVP validation, we just simulate a build success or run clang++
echo Build command goes here.
exit /b 0
"""

    # test.bat
    test_bat = f"""@echo off
echo Running validation test for {target_name}...
:: echo dummy > test.bin
:: harness.exe test.bin
echo Validation command goes here.
exit /b 0
"""

    # README.md
    readme_content = f"""# Harness for {target_name}

## Target Info
- **Module**: `{module_name}`
- **Function**: `{target_name}`
- **Input Type**: `{input_type}`

## Instructions
1. Edit `harness.cpp` to correctly define the target function signature.
2. Edit `CMakeLists.txt` or `build.bat` to link against the correct libraries.
3. Validate the harness before running a campaign.
"""

    return {
        "harness.cpp": cpp_content,
        "CMakeLists.txt": cmake_content,
        "build.bat": build_bat,
        "test.bat": test_bat,
        "README.md": readme_content,
    }
