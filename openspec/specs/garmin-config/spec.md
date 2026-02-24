## ADDED Requirements

### Requirement: Configuration file exists with credentials

The system SHALL have a configuration file at `~/.GarminDb/GarminConnectConfig.json` containing Garmin Connect credentials and sync settings.

#### Scenario: Valid configuration file
- **WHEN** user has created `~/.GarminDb/GarminConnectConfig.json`
- **THEN** the file SHALL contain `credentials.user` with Garmin Connect email
- **AND** the file SHALL contain `credentials.password` with Garmin Connect password

#### Scenario: Configuration file with secure permissions
- **WHEN** configuration file is created
- **THEN** file permissions SHALL be set to owner-only readable (chmod 600)

### Requirement: Historical date ranges configured for full history

The system SHALL have date ranges configured to capture all historical data from the user's first Garmin device.

#### Scenario: Monitoring data start date
- **WHEN** `data.monitoring_start_date` is configured
- **THEN** it SHALL be set to a date on or before user's first Garmin device activation

#### Scenario: Sleep data start date
- **WHEN** `data.sleep_start_date` is configured  
- **THEN** it SHALL be set to a date on or before user's first sleep tracking activation

#### Scenario: Weight data start date
- **WHEN** `data.weight_start_date` is configured
- **THEN** it SHALL be set to a date on or before user's first weight entry

#### Scenario: RHR data start date
- **WHEN** `data.rhr_start_date` is configured
- **THEN** it SHALL be set to a date on or before user's first resting heart rate measurement

### Requirement: Download settings enable all data types

The system SHALL have download settings configured to fetch all available data dimensions.

#### Scenario: All download flags enabled
- **WHEN** configuration is loaded by GarminDB
- **THEN** `download.activities` SHALL be enabled
- **AND** `download.monitoring` SHALL be enabled
- **AND** `download.sleep` SHALL be enabled
- **AND** `download.weight` SHALL be enabled
- **AND** `download.rhr` SHALL be enabled
