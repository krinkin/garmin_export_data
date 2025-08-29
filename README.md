# Garmin Connect Data Exporter

> A Python tool that exports all available Garmin Connect fitness and health data into a single structured JSON file optimized for analysis by Large Language Models.

## Features

* **Comprehensive Data Export**: Exports user profile, activities, health metrics, fitness data, and specialized health information
* **LLM-Optimized Format**: Structured JSON output with analysis context and instructions for AI models
* **Smart Sampling**: Intelligent data sampling to balance detail with file size optimization
* **Error Handling**: Robust API error handling with graceful fallbacks for missing data

## Tech Stack

* **Backend:** Python 3.12, garminconnect library, pandas
* **Data Processing:** JSON export, smart sampling algorithms
* **Authentication:** Garmin Connect API with token storage
* **Dependencies:** garminconnect, pandas

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Make sure you have the following installed on your system:
* Python 3.12 or higher
* pip (Python package manager)
* Garmin Connect account with fitness data

### Installation

1. Clone the repository:
   ```bash
   git clone https://your-repository-url.git
   cd garmin
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install garminconnect pandas
   ```

### Environment Variables

No environment variables are required. The tool will prompt for your Garmin Connect credentials during first run and store authentication tokens locally.

### Running the Application

To start the data export process, run the following command:
```bash
python garmin_export.py
```

The tool will:
1. Prompt for your Garmin Connect email and password (first time only)
2. Ask how many days of data to export (default: 21 days)
3. Export all available data into a timestamped JSON file
4. Provide analysis context for LLM processing

## Available Scripts

* `python garmin_export.py`: Main export script with interactive prompts
* The script automatically handles all data collection and export processes

## Project Structure

* `garmin_export.py` - Main Python script containing the GarminLLMExporter class
* `venv/` - Python virtual environment with dependencies
* `garmin_export_*/` - Export output directories (generated during execution)
* `*.json` - Exported data files ready for LLM analysis

## Data Export Sections

The tool exports the following data categories:

1. **User Profile**: Personal information, unit system, device list
2. **Activities**: Recent activities with detailed samples for analysis
3. **Daily Health Metrics**: Heart rate, sleep, stress, steps, body battery (sampled every 2nd day)
4. **Fitness Metrics**: Training readiness, training status, resting heart rate, body composition
5. **Specialized Health**: Respiration, pulse oximetry, hydration, women's health data
6. **LLM Analysis Context**: Analysis instructions, data overview, and suggested approaches

## Usage with LLMs

After export, the generated JSON file is optimized for analysis by Large Language Models:

1. Upload the exported JSON file to ChatGPT, Claude, or other LLM platforms
2. Start analysis with the `llm_analysis_context` section
3. Ask for patterns, insights, and actionable health recommendations
4. The data structure includes analysis instructions and context for optimal results

## Error Handling

The tool includes comprehensive error handling for:
* API rate limits and authentication issues
* Missing or unavailable data endpoints
* Network connectivity problems
* Invalid data formats

## Contributing

This is a focused tool for Garmin Connect data export. Contributions are welcome for:
* Additional data endpoints
* Improved sampling algorithms
* Enhanced LLM analysis context
* Better error handling and logging

## License

[Add your license information here]

## Support

For issues or questions related to:
* Garmin Connect API: Check the [garminconnect library documentation](https://github.com/cyberjunky/python-garminconnect)
* Data export problems: Review the error messages and check your Garmin Connect credentials
* LLM analysis: Ensure you're using the `llm_analysis_context` section as a starting point
