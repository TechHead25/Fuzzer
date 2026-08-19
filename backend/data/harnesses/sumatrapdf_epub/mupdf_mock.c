#include "mupdf_mock.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct fz_context_s {
    int dummy;
};

struct fz_document_s {
    int dummy;
};

fz_context* fz_new_context(void *alloc, void *locks, unsigned int max_store) {
    // printf("[Mock] fz_new_context initialized.\n");
    fz_context* ctx = (fz_context*)malloc(sizeof(fz_context));
    return ctx;
}

void fz_drop_context(fz_context *ctx) {
    if (ctx) {
        free(ctx);
        // printf("[Mock] fz_drop_context executed safely.\n");
    }
}

void fz_register_document_handlers(fz_context *ctx) {
    // printf("[Mock] Document handlers registered.\n");
}

fz_document* fz_parse_epub(fz_context *ctx, const char *filename) {
    printf("[Mock] fz_parse_epub hit! Parsing file: %s\n", filename);
    
    // Simulate reading the file to ensure the harness actually passed a valid file path
    FILE* f = fopen(filename, "rb");
    if (!f) {
        printf("[Mock] fz_parse_epub ERROR: Could not open file.\n");
        return NULL;
    }
    
    // Read a few bytes to simulate parsing
    char buf[16];
    size_t bytes_read = fread(buf, 1, sizeof(buf), f);
    fclose(f);
    
    if (bytes_read == 0) {
        printf("[Mock] fz_parse_epub ERROR: File is empty.\n");
        return NULL;
    }
    
    fz_document* doc = (fz_document*)malloc(sizeof(fz_document));
    return doc;
}

void fz_drop_document(fz_context *ctx, fz_document *doc) {
    if (doc) {
        free(doc);
    }
}
