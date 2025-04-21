CREATE DATABASE spotifydb;
DROP DATABASE spotifydb;
USE spotifydb;

CREATE TABLE streaming_stats (
    window_start DATETIME,
    window_end DATETIME,
    track_name VARCHAR(255),
    avg_ms_played DOUBLE
);

SELECT * FROM streaming_stats;

CREATE TABLE top_artist (
	window_start DATETIME,
    window_end DATETIME,
    artist_name VARCHAR(255),
    play_count INT
);

SELECT * FROM top_artist;

CREATE TABLE top_track (
	window_start DATETIME,
    window_end DATETIME,
    track_name VARCHAR(255),
    play_count INT
);

SELECT * FROM top_track;

CREATE TABLE songs_per_window (
	window_start DATETIME,
    window_end DATETIME,
    total_songs INT
);

SELECT * FROM songs_per_window;

CREATE TABLE monthly_listening_time (
	month_year VARCHAR(20),
    total_ms_played INT
);

SELECT * FROM monthly_listening_time;


TRUNCATE TABLE streaming_stats;
TRUNCATE TABLE top_artist;
TRUNCATE TABLE top_track;
TRUNCATE TABLE songs_per_window;
TRUNCATE TABLE monthly_listening_time;

SELECT * FROM weekly_top_songs;
SELECT * FROM weekly_top_artists;
SELECT * FROM monthly_listen_analysis;
SELECT * FROM yearly_listen_analysis;
SELECT * FROM hour_distribution_trends;
SELECT * FROM day_distribution_trends;
SELECT * FROM song_length_trends;
-- SELECT * FROM listening_intensity_trends;
SELECT * FROM seasonal_top_tracks;
SELECT * FROM seasonal_listening_stats;





