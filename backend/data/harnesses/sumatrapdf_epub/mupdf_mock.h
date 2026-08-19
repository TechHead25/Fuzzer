#ifndef MUPDF_MOCK_H
#define MUPDF_MOCK_H

#ifdef __cplusplus
extern "C" {
#endif

// Mock types
typedef struct fz_context_s fz_context;
typedef struct fz_document_s fz_document;

// Mock context initialization
fz_context* fz_new_context(void *alloc, void *locks, unsigned int max_store);
void fz_drop_context(fz_context *ctx);
void fz_register_document_handlers(fz_context *ctx);

// The target function
fz_document* fz_parse_epub(fz_context *ctx, const char *filename);
void fz_drop_document(fz_context *ctx, fz_document *doc);

#ifdef __cplusplus
}
#endif

#endif // MUPDF_MOCK_H
