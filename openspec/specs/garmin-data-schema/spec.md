## ADDED Requirements

### Requirement: Monitoring data schema documented

The system SHALL document the SQLite schema for daily monitoring data in `garmin.db`.

#### Scenario: Daily monitoring tables accessible
- **WHEN** user queries `garmin.db`
- **THEN** `monitoring_hr` table SHALL contain heart rate samples with timestamps
- **AND** `monitoring_intensity` table SHALL contain intensity minutes data
- **AND** `monitoring_climb` table SHALL contain floors climbed/descended
- **AND** `steps_activities` table SHALL contain step counts and distances

#### Scenario: Daily summary data accessible
- **WHEN** user queries for daily summaries
- **THEN** `days_summary` view SHALL provide aggregated daily statistics
- **AND** view SHALL include total steps, distance, calories, active minutes

### Requirement: Activity data schema documented

The system SHALL document the SQLite schema for activity data in `garmin_activities.db`.

#### Scenario: Activity summary accessible
- **WHEN** user queries `garmin_activities.db`
- **THEN** `activities` table SHALL contain one row per activity
- **AND** each activity SHALL have: sport type, start time, duration, distance, calories
- **AND** activities SHALL have unique identifiers for joining to detail tables

#### Scenario: Activity detail data accessible
- **WHEN** user queries activity details
- **THEN** `activity_laps` table SHALL contain lap splits for activities
- **AND** `activity_records` table SHALL contain per-second/per-point records
- **AND** records SHALL include heart rate, pace, cadence, power where available

### Requirement: Sleep data schema documented

The system SHALL document the SQLite schema for sleep data.

#### Scenario: Sleep records accessible
- **WHEN** user queries sleep data
- **THEN** `sleep` table SHALL contain one row per sleep session
- **AND** each record SHALL include: start time, end time, total sleep duration
- **AND** sleep stages (deep, light, REM, awake) SHALL be available where tracked

### Requirement: Health metrics schema documented

The system SHALL document the SQLite schema for weight and resting heart rate.

#### Scenario: Weight data accessible
- **WHEN** user queries weight data
- **THEN** `weight` table SHALL contain weight measurements with timestamps
- **AND** body composition data (body fat %, muscle mass) SHALL be included where available

#### Scenario: Resting heart rate accessible
- **WHEN** user queries RHR data
- **THEN** `resting_hr` table SHALL contain daily RHR values
- **AND** each record SHALL include date and RHR value in BPM

### Requirement: Summary data schema documented

The system SHALL document the SQLite schema for aggregated summaries in `garmin_summary.db`.

#### Scenario: Time-period summaries accessible
- **WHEN** user queries `garmin_summary.db`
- **THEN** `days_summary` table SHALL contain daily aggregates
- **AND** `weeks_summary` table SHALL contain weekly aggregates
- **AND** `months_summary` table SHALL contain monthly aggregates
- **AND** `years_summary` table SHALL contain yearly aggregates

#### Scenario: Summary metrics comprehensive
- **WHEN** user queries any summary table
- **THEN** records SHALL include: steps, distance, calories, active minutes
- **AND** records SHALL include: resting HR, stress level, sleep duration averages
- **AND** records SHALL include: activity counts and totals
