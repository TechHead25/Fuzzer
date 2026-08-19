# SumatraPDF EPUB Harness

This directory contains a C/C++ fuzzing harness designed for the `fz_parse_epub` parsing routine in the MuPDF engine of SumatraPDF.

## Compilation

Run `build.ps1` to compile the harness using the installed MSVC/Clang compiler via CMake.
The mock `mupdf_mock` library provides the stubs necessary to link against the required PDF parsing contexts natively.

## Testing

Run `test.ps1` to execute the built harness against a test `.epub` payload.

## Fuzzing Architecture
- **Input Strategy:** The target expects a physical file path (`const char* filename`). The harness exposes standard `main(argc, argv)` for filesystem fuzzing.
- **Persistent Mode:** The global `fz_context` is allocated once at startup. If compiled under DynamoRIO, you may instruct WinAFL to hook `fuzz_target` to achieve extremely fast execution speeds by avoiding heavy `malloc` operations on every iteration.
