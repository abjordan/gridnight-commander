# GridNight Commander - Implementation Plan

## Current State Summary (Updated: 2025-10-30)

### What's Working ✅

**Core Functionality (All Stages 1-4 Complete)**:
- ✅ **MongoDB Connection** - Modal dialog with async connection using Motor
- ✅ **Dynamic File Tree** - Browse GridFS buckets and files with expandable tree navigation
- ✅ **File Preview** - View text files and rendered Markdown with metadata display
- ✅ **File Upload** - Add new files to any GridFS bucket with MIME type detection
- ✅ **File Delete** - Remove files from buckets with confirmation dialog
- ✅ **Keyboard Navigation** - Full keyboard-driven interface (c=connect, u=upload, d=delete, q=quit)
- ✅ **Tree Refresh** - Automatic tree updates after upload/delete operations
- ✅ **Error Handling** - Notifications for success/error states
- ✅ **Test Infrastructure** - Data generation script and automated tests

**Technical Implementation**:
- GridFsManager with full CRUD operations (create, read, delete)
- Message passing pattern for modal communication
- Reactive properties with explicit refresh methods
- Worker-based async operations with @work decorator
- Proper package imports (gridnight_commander.*)

### What Works Well ✅
- Connection flow is reliable using message passing pattern
- Tree population correctly displays all buckets and files
- File preview handles both text and Markdown rendering
- Upload workflow validates files and refreshes tree
- Delete confirmation prevents accidental deletions
- All operations provide user feedback via notifications

### Known Issues & Limitations 🚧

**Minor Issues**:
- Scroll jumpiness when navigating long files in preview pane
- No visual highlight for currently selected file (beyond tree cursor)
- Preview content can be bottom-aligned on initial load
- No download functionality (files can only be viewed, not saved locally)

**Missing Features** (Stage 5):
- File download to local filesystem
- Bucket statistics (total files, total size)
- Connection status indicator
- Search/filter functionality
- Connection profiles for quick switching

**Technical Debt**:
- Some widget ID management could be cleaner
- Could benefit from more comprehensive error scenarios testing
- No automated UI tests (only programmatic tests)

### What's Left to Do 📋

**Stage 5: Polish & UX Improvements** (Optional enhancements):
1. Add file download functionality
2. Improve visual feedback (selection highlighting, status indicators)
3. Add bucket statistics display
4. Enhanced keyboard navigation features
5. Search/filter capabilities

See Stage 5 section below for detailed breakdown.

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

**Status**: Complete ✅

**Implementation Notes**:
- Added `upload_file()` method to GridFsManager with MIME type detection
- Created UploadDialog modal with file path input, bucket selector, and optional filename
- Added `u` keyboard shortcut to trigger upload dialog
- Upload dialog validates file exists before uploading
- Tree automatically refreshes after successful upload via `refresh_tree()` method
- Success/error notifications provide user feedback

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

**Status**: Complete ✅

**Implementation Notes**:
- Added `delete_file()` method to GridFsManager that deletes files by ID from GridFS
- Created DeleteConfirmationDialog modal with file details and warning message
- Added 'd' keyboard shortcut to trigger deletion when file is selected
- Implemented `selected_file_info` tracking in GridFsBrowser to store currently selected file
- Added message handler that clears selection, clears preview, and refreshes tree after deletion
- Success/error notifications provide user feedback
- Tested programmatically - deletion works correctly at GridFsManager level

---

### Stage 5: Polish & UX Improvements
**Goal**: Enhance user experience with better visuals and conveniences

**Status**: Partially Complete (Documentation Done, Features Optional)

**Completed Items** ✅:
- ✅ Documentation updates
  - Comprehensive README with screenshot
  - All keyboard shortcuts documented
  - Installation and usage instructions
  - Architecture documentation
  - Troubleshooting via development section
- ✅ Basic keyboard navigation (arrow keys, Enter already working via Textual)
- ✅ Basic error handling with notifications

**Remaining Optional Enhancements** 🚧:

#### 1. File Download Functionality (High Priority)
**Why**: Users can preview files but cannot save them locally

**Tasks**:
- Add `download_file(bucket_name, file_id, dest_path)` to GridFsManager
- Create SaveDialog/DownloadDialog modal for choosing destination
- Bind to keyboard shortcut (e.g., `s` for save/download)
- Show progress indicator for large files
- Refresh local file browser or provide confirmation

**Success Criteria**:
- User can press `s` on selected file to download
- Dialog allows choosing save location and filename
- File downloads successfully to local filesystem
- Success notification confirms download location

#### 2. Visual Selection Highlighting (Medium Priority)
**Why**: Current tree cursor is subtle, could be more prominent

**Tasks**:
- Add CSS styling for selected file (background color, bold text)
- Highlight currently selected file even when focus moves to dialog
- Consider adding icon or marker next to selected file

**Success Criteria**:
- Selected file is visually distinct from others
- Selection persists visually when dialogs open
- Clear distinction between cursor position and selected file

#### 3. Bucket Statistics Display (Medium Priority)
**Why**: Would be helpful to see file counts and sizes at a glance

**Tasks**:
- Calculate total file count per bucket
- Calculate total size per bucket
- Display in tree node labels (e.g., "Dune/ (3 files, 2.4 KB)")
- Add connection status indicator to header or footer
- Show current database name in status area

**Success Criteria**:
- Bucket nodes show file count and total size
- Header/footer shows connection status (Connected/Disconnected)
- Current database name is visible

#### 4. Search/Filter Functionality (Low Priority/Stretch)
**Why**: Nice to have for databases with many files

**Tasks**:
- Add `/` keyboard shortcut to open search dialog
- Filter tree to show only matching files
- Support regex or simple substring matching
- Highlight matched text in results
- Clear filter easily (ESC key)

**Success Criteria**:
- User can press `/` to search
- Tree filters to show only matching results
- Easy to clear and return to full view
- Search works across bucket and filename

#### 5. Enhanced Error Handling (Low Priority)
**Why**: Current error handling is basic but functional

**Tasks**:
- Add connection lost detection (periodic heartbeat)
- Offer reconnect dialog when connection drops
- Add timeouts for long operations (large file preview)
- Better error messages for common MongoDB errors
- Graceful degradation when operations fail

**Success Criteria**:
- App detects when MongoDB connection is lost
- User can reconnect without restarting app
- Long operations timeout gracefully
- Error messages are specific and actionable

#### 6. Additional Nice-to-Haves (Very Low Priority)
- Connection profiles (save/load connection strings)
- File rename functionality
- Batch operations (multi-select delete)
- Copy/move files between buckets
- Export bucket contents as zip
- Custom CSS themes

**Tests for Remaining Items**:
- Download file and verify contents match original
- Verify visual feedback for selection
- Test statistics calculations with various bucket sizes
- Search/filter with different patterns
- Test error scenarios (disconnect during operation)

**Priority Recommendation**:
1. **File Download** - Most valuable missing feature
2. **Visual Selection** - Quick UX win
3. **Bucket Statistics** - Nice informational enhancement
4. **Search/Filter** - Only needed for large collections
5. **Enhanced Errors** - Current handling is adequate

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

## Project Status & Next Steps

### Current Status: **CORE FEATURES COMPLETE** ✅

All primary functionality (Stages 1-4) has been successfully implemented and tested:
- ✅ Stage 1: Dynamic File Tree
- ✅ Stage 2: File Preview
- ✅ Stage 3: File Upload
- ✅ Stage 4: File Delete
- ✅ Documentation & README

**The application is fully functional and ready to use!**

### If You Want to Continue Development

**Immediate Next Steps** (Optional):
1. **Try it out!** - Run `uv run gnc` and test all features
2. **Implement File Download** (Stage 5.1) - Most valuable missing feature
3. **Add Visual Selection Highlighting** (Stage 5.2) - Quick UX improvement
4. **Add Bucket Statistics** (Stage 5.3) - Nice informational enhancement

**Getting Started with Development**:
```bash
# Ensure MongoDB is running
docker compose up -d

# Generate test data
uv run python tests/generate_data.py

# Run the application
uv run gnc

# Connect to test database
# Connection: mongodb://devroot:devroot@localhost:27017/
# Database: gnc-test
```

**Priority Order for Stage 5**:
1. File Download (adds most user value)
2. Visual Selection (quick UX win)
3. Bucket Statistics (informational)
4. Search/Filter (only if needed for large collections)
5. Enhanced Errors (current handling is adequate)

### Maintenance & Future Ideas

The codebase is clean, documented, and follows established patterns. Future enhancements can build on the existing architecture:
- Message passing for modals
- @work decorator for async operations
- Reactive properties with refresh methods
- GridFsManager for all MongoDB operations

See Stage 5 section above for detailed optional enhancement ideas.
