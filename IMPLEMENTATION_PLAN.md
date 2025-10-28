# GridNight Commander - Implementation Plan

## Current State Summary

### What's Working ✅
- Connection modal with async MongoDB connection
- GridFsManager with bucket discovery (`list_gridfs_buckets()`)
- Basic UI layout (header, tree panel, preview panel, footer)
- Reactive data binding infrastructure
- Test data generation script

### What's Incomplete 🚧
- MongoView displays hardcoded "Dune" data instead of real GridFS buckets
- Preview pane shows static "TEST" placeholder
- No file operations (upload, delete, download)
- No file selection handling or metadata display

---

## Implementation Stages

### Stage 1: Dynamic File Tree Population
**Goal**: Replace hardcoded tree data with real GridFS buckets and files

**Tasks**:
1. Add `list_files_in_bucket(bucket_name)` method to GridFsManager
   - Returns list of files with basic metadata (name, size, upload date)
   - Use `AsyncIOMotorGridFSBucket.find()` to list files

2. Implement `watch_client()` in MongoView to populate tree on connection
   - Clear existing tree
   - Call `list_gridfs_buckets()` to get bucket names
   - For each bucket, create tree node and populate with files
   - Handle empty buckets gracefully

3. Update tree structure to match README design
   - Collections as expandable parent nodes (e.g., "Dune/")
   - Files as leaf nodes under their collection
   - Show file count in parent node labels

**Success Criteria**:
- After connecting, tree shows all GridFS buckets from connected database
- Each bucket expands to show files stored in it
- Clicking on different buckets works correctly
- Empty buckets display "(empty)" indicator

**Tests**:
- Connect to test database created by `tests/generate_data.py`
- Verify "Dune", "Programming", and "Life Skills" buckets appear
- Verify files within each bucket are listed correctly
- Test with empty database (no buckets)

**Status**: Complete ✅

**Implementation Notes**:
- Added `list_files_in_bucket()` method to GridFsManager that returns file metadata
- Implemented `watch_client()` watcher that triggers on reactive client change
- Used `@work` decorator for async tree population
- Tree shows buckets with file counts, files with sizes
- File info stored in node.data for later use in Stage 2

---

### Stage 2: File Preview Implementation
**Goal**: Display file contents and metadata when a file is selected

**Tasks**:
1. Add `get_file_content(bucket_name, file_id)` method to GridFsManager
   - Download file contents as bytes
   - Return metadata (MIME type, size, upload date)

2. Create FilePreview widget/component
   - Replace static "TEST" placeholder
   - Display text content for text files
   - Display "Binary file" message for non-text files
   - Show file metadata at bottom (size, type, date)

3. Handle tree selection events
   - Detect when user clicks on a file in MongoView
   - Load file content asynchronously
   - Update preview pane with content
   - Show loading indicator during fetch

4. Add Markdown rendering support (stretch goal)
   - Use `rich.markdown.Markdown` for .md files
   - Fallback to plain text if rendering fails

**Success Criteria**:
- Clicking a file in the tree loads its content in preview pane
- Text files display their contents correctly
- Binary files show appropriate message
- Metadata displays: filename, size, MIME type, upload date
- No UI freeze during file loading (async handling)

**Tests**:
- Select various test files from different buckets
- Verify text files render correctly
- Verify binary files show message instead of garbage
- Test large files (loading indicator appears)
- Test rapid clicking between files (cancellation/queuing)

**Status**: Complete ✅

**Implementation Notes**:
- Added `get_file_content()` method to GridFsManager that downloads files from GridFS
- Created FilePreview widget using Vertical container with VerticalScroll for content
- Handles tree selection events with `on_tree_node_selected()`
- Dynamically switches between Static (text) and Markdown (rendered) widgets
- Displays file metadata (filename, size, upload date, content type)
- Text files display as plain text, .md files render with Markdown formatting
- Binary files show appropriate message

---

### Stage 3: File Upload Functionality
**Goal**: Allow users to upload files to GridFS buckets

**Tasks**:
1. Add `upload_file(bucket_name, local_path, filename)` method to GridFsManager
   - Read file from local filesystem
   - Detect MIME type
   - Upload to specified bucket with metadata
   - Return success/failure status

2. Create UploadDialog modal screen
   - File path input field
   - Bucket selector (dropdown or list)
   - Optional filename override
   - Upload/Cancel buttons

3. Add keyboard shortcut for upload
   - Bind `u` key to open upload dialog
   - Add to footer/help display

4. Implement upload progress feedback
   - Show loading indicator during upload
   - Display success/error notification
   - Refresh tree after successful upload

**Success Criteria**:
- User can press `u` to open upload dialog
- Can select target bucket from list
- Can browse and select local file
- File uploads successfully to chosen bucket
- Tree refreshes to show new file
- Error messages display for failures (file not found, connection issues)

**Tests**:
- Upload text file to "Dune" bucket
- Upload binary file (image, PDF) to "Programming" bucket
- Test invalid file path (error handling)
- Test upload while disconnected (error handling)
- Verify uploaded file appears in tree
- Verify uploaded file can be previewed

**Status**: Not Started

---

### Stage 4: File Delete Functionality
**Goal**: Allow users to delete files from GridFS buckets

**Tasks**:
1. Add `delete_file(bucket_name, file_id)` method to GridFsManager
   - Delete file by ID from specified bucket
   - Return success/failure status

2. Create DeleteConfirmationDialog modal
   - Show filename and bucket being deleted
   - Confirm/Cancel buttons
   - Warning message about irreversibility

3. Add keyboard shortcut for delete
   - Bind `d` key to trigger delete (when file selected)
   - Show confirmation dialog before deletion
   - Add to footer/help display

4. Implement deletion feedback and tree refresh
   - Show success/error notification
   - Remove deleted file from tree
   - Clear preview pane if deleted file was selected

**Success Criteria**:
- User can select a file and press `d` to delete
- Confirmation dialog appears with file details
- Confirming deletes the file from GridFS
- Tree updates to remove deleted file
- Preview pane clears if showing deleted file
- Error messages for failures (permission issues, connection lost)

**Tests**:
- Delete a file and verify it's removed from MongoDB
- Cancel deletion and verify file remains
- Try to delete while disconnected (error handling)
- Delete the currently previewed file (preview clears)
- Verify deleted file no longer appears after tree refresh

**Status**: Not Started

---

### Stage 5: Polish & UX Improvements
**Goal**: Enhance user experience with better visuals and conveniences

**Tasks**:
1. Add file selection highlighting
   - Visual indicator for currently selected file
   - Update CSS with highlight color/style

2. Improve status bar/metadata display
   - Show total file count per bucket
   - Show total size of files in bucket
   - Display connection status indicator

3. Add keyboard shortcuts for navigation
   - Arrow keys for file navigation (if not already working)
   - Enter to toggle bucket expand/collapse
   - `/` for search/filter (stretch goal)

4. Improve error handling and user feedback
   - Better error messages for common issues
   - Connection lost detection and reconnect option
   - Timeouts for long operations

5. Add download functionality (stretch goal)
   - Add `download_file(bucket_name, file_id, dest_path)` to GridFsManager
   - Create SaveDialog for choosing destination
   - Bind to keyboard shortcut (e.g., `s` for save)

6. Documentation updates
   - Update README with screenshots/demo
   - Document all keyboard shortcuts
   - Add troubleshooting section

**Success Criteria**:
- Selected file clearly highlighted in tree
- Status bar shows useful information
- All keyboard shortcuts documented and working
- Error messages are helpful and actionable
- Optional: Files can be downloaded to local filesystem

**Tests**:
- Navigate through tree with keyboard
- Verify visual feedback for all actions
- Test error scenarios (disconnect during operation)
- Verify all shortcuts work as expected
- Optional: Download file and verify contents match

**Status**: Not Started

---

## Development Guidelines

### Before Each Stage:
1. Review existing code patterns (async/await, reactive binding)
2. Run test data generator: `python tests/generate_data.py`
3. Ensure MongoDB is running: `docker compose up -d`

### During Implementation:
- Make small, incremental commits that compile and run
- Test each method in isolation before integrating
- Use Textual's logging: `self.log.info()` for debugging
- Follow existing patterns (e.g., Worker for async operations)

### After Each Stage:
- Run manual tests with test database
- Update this plan with completion status
- Commit working code with clear message
- Consider edge cases and error handling

### When Stuck:
- Check Textual documentation: https://textual.textualize.io
- Review Motor/PyMongo async docs
- Look at existing async patterns in ConnectionScreen
- Test GridFsManager methods in isolation

---

## Dependencies Check

Current dependencies (from pyproject.toml):
- `motor>=3.7.1` - Async MongoDB driver ✅
- `pymongo>=4.11.3` - MongoDB driver (for sync operations) ✅
- `python-dotenv>=1.0.1` - Environment variables ✅
- `textual>=2.1.2` - TUI framework ✅
- `textual-dev` - Dev tools (optional) ✅

No additional dependencies needed for core functionality.

For Markdown rendering (Stage 2 stretch goal):
- Textual includes `Rich` which has Markdown support built-in

---

## Priority Recommendations

**High Priority** (Core functionality):
1. Stage 1 - Dynamic File Tree (enables all other features)
2. Stage 2 - File Preview (main user value)
3. Stage 3 - Upload (makes tool useful for adding files)
4. Stage 4 - Delete (makes tool useful for managing files)

**Medium Priority** (Polish):
5. Stage 5 - UX Improvements (makes tool pleasant to use)

**Suggested Order**: 1 → 2 → 3 → 4 → 5

Each stage builds on the previous, and stages 3-4 can be done in parallel if desired.

---

## Next Steps

1. **Review this plan** - Ensure it matches your vision
2. **Set up test environment** - Run `docker compose up -d` and `python tests/generate_data.py`
3. **Start with Stage 1** - Get dynamic tree working first (foundation for everything else)
4. **Iterate quickly** - Small commits, frequent testing

When ready, say "Let's start with Stage 1" and I'll begin implementation!
