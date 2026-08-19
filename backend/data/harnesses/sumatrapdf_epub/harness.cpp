#include <iostream>
#include <fstream>
#include "mupdf_mock.h"

// DynamoRIO / WinAFL typically require a standard main() or a target function hook.
// For standard fuzzing, we define main() to take a filepath.
// WinAFL will hook main() or the specific fuzz_target() if compiled with DynamoRIO.

// Global context to avoid reallocation overhead during fuzzing if we use persistent mode.
fz_context *ctx = nullptr;

extern "C" __declspec(dllexport) int fuzz_target(const char* filepath) {
    if (!ctx) {
        ctx = fz_new_context(nullptr, nullptr, 64 * 1024 * 1024);
        fz_register_document_handlers(ctx);
    }
    
    // Call the target function (verified EPUB parser entry point)
    fz_document *doc = fz_parse_epub(ctx, filepath);
    
    if (doc) {
        // Safe cleanup
        fz_drop_document(ctx, doc);
    }
    
    return 0;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <input_file.epub>\n";
        return 1;
    }

    const char* filepath = argv[1];
    
    // Initialize context
    ctx = fz_new_context(nullptr, nullptr, 64 * 1024 * 1024);
    if (!ctx) {
        std::cerr << "Failed to allocate MuPDF context.\n";
        return 1;
    }
    
    fz_register_document_handlers(ctx);
    
    // Invoke the fuzzing routine
    fuzz_target(filepath);
    
    // Global Cleanup
    fz_drop_context(ctx);
    
    return 0;
}
