# GEMINI.md

## Project Overview

This project is a desktop application for managing and preserving TIFF files. It is built with Python and the PyQt5 GUI framework. The application provides functionality for generating reports on TIFF metadata, creating and validating checksums, and transferring files with integrity checks.

The project follows a Model-View-Controller (MVC) like architecture:

*   **Models:** (`models/`) Defines the data structures for the application, such as configuration settings and TIFF metadata.
*   **Views:** (`views/`) Contains the UI components of the application, built with PyQt5. This includes the main window and the different tabs for reports, checksums, and file transfers.
*   **Controllers:** (`controllers/`) Implements the business logic of the application. This includes scanning for files, generating reports, calculating checksums, and managing file transfers.

## Building and Running

### Dependencies

The project's dependencies are listed in `requirements.txt`. They can be installed using pip:

```bash
pip install -r requirements.txt
```

### Running the Application

The application can be run directly from the source code:

```bash
python main.py
```

### Building the Application

The project can be built into a standalone executable using the `build.py` script. This script uses PyInstaller to package the application.

```bash
python build.py
```

The build script will create a `dist` directory containing the executable.

## Development Conventions

*   **Coding Style:** The code follows standard Python conventions (PEP 8).
*   **Project Structure:** The project is organized into `models`, `views`, and `controllers` directories, separating data, UI, and business logic.
*   **Error Handling:** The application uses `try...except` blocks to handle potential errors, such as file not found or permission errors.
*   **UI Design:** The UI is built with PyQt5 and styled using a custom QSS stylesheet located in `resources/styles.qss`.
*   **Concurrency:** The application uses `QThread` to perform long-running tasks (such as scanning files, generating reports, and transferring files) in the background, preventing the UI from freezing.
