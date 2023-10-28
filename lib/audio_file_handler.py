import json
import logging
import os
import re
import shutil
import subprocess
import traceback
import datetime
from datetime import datetime, timezone
from pathlib import Path
import time
from mutagen.mp3 import MP3

module_logger = logging.getLogger('icad_rtl_uploader.mp3')


def convert_mp3_m4a(mp3_file_path):
    if not os.path.isfile(mp3_file_path):
        module_logger.error(f"MP3 file does not exist: {mp3_file_path}")
        return f"MP3 file does not exist: {mp3_file_path}"

    module_logger.info(f'Converting MP3 to Mono M4A at 8k')

    command = f"ffmpeg -y -i {mp3_file_path} -af aresample=resampler=soxr -ar 8000 -c:a aac -ac 1 -b:a 8k {mp3_file_path.replace('.mp3', '.m4a')}"

    try:
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
        module_logger.debug(output)
        module_logger.info(f"Successfully converted MP3 to M4A for file: {mp3_file_path}")
    except subprocess.CalledProcessError as e:
        error_message = f"Failed to convert MP3 to M4A: {e.output}"
        module_logger.critical(error_message)
        return None
    except Exception as e:
        error_message = f"An unexpected error occurred during conversion: {str(e)}"
        module_logger.critical(error_message, exc_info=True)
        return None

    return True


def create_json(mp3_filename, mp3_directory, json_path, channel_data):
    call_data = {
        "freq": 0,
        "start_time": 0,
        "stop_time": 0,
        "emergency": 0,
        "encrypted": 0,
        "call_length": 0,
        "talkgroup": 0,
        "talkgroup_tag": "",
        "talkgroup_description": "",
        "talkgroup_group_tag": "",
        "talkgroup_group": "",
        "audio_type": "analog",
        "short_name": "",
        "freqList": [],
        "srcList": []
    }
    # Split file name to extract data.
    parts = mp3_filename.split('_')

    # Extract the first, second, and third parts
    short_name = parts[0]
    timestamp_part = parts[1]
    frequency_part = int(parts[2].replace(".mp3", ""))
    module_logger.debug(f"Timestamp {timestamp_part} of parts.")
    # Extracting date and time from the filename and converting to datetime object

    # Making the datetime object timezone-aware and set to UTC


    # Converting the timezone-aware datetime object to a UTC timestamp
    epoch_timestamp = timestamp_part

    # Load the MP3 file
    audio = MP3(os.path.join(mp3_directory, mp3_filename))

    # Get the duration in seconds
    duration_sec = audio.info.length

    talkgroup_data = None

    for tg in channel_data:
        if int(tg["channel_frequency"]) == frequency_part:
            talkgroup_data = tg
            break

    if not talkgroup_data:
        return False

    call_split = "."
    call_time2 = epoch_timestamp.split(call_split, 1)[0]
    call_time3 = datetime.fromtimestamp(call_time2)
    call_time = call_time3.isoformat()
    module_logger.debug(f"Timestamp split {call_time} of parts.")
    call_data["talkgroup"] = int(talkgroup_data["talkgroup_decimal"])
    call_data["start_time"] = call_time
    call_data["call_length"] = duration_sec
    call_data["talkgroup_tag"] = talkgroup_data["talkgroup_alpha_tag"]
    call_data["talkgroup_description"] = talkgroup_data["talkgroup_name"]
    call_data["talkgroup_group"] = talkgroup_data["talkgroup_group"]
    call_data["talkgroup_group_tag"] = talkgroup_data["talkgroup_service_type"]
    call_data["short_name"] = short_name
    call_data["freqList"].append(
        {"freq": int(frequency_part), "time": call_time, "pos": 0.00, "len": duration_sec, "error_count": "0",
         "spike_count": "0"}),
    call_data["srcList"].append(
        {"src": -1, "time": call_time, "pos": 0.00, "emergency": 0, "signal_system": "", "tag": ""})

    with open(json_path, "w+") as f:
        json.dump(call_data, f, indent=4)
    f.close()

    return call_data


def archive_files(files, archive_path):
    # Get the current date
    current_date = datetime.now()

    # Extract year, month, and day from the current date
    year = current_date.year
    month = current_date.month
    day = current_date.day

    # Create folder structure
    folder_path = os.path.join(archive_path, str(year), str(month), str(day))
    os.makedirs(folder_path, exist_ok=True)

    for file in files:
        file_path = Path(file)
        if file_path.is_file():
            try:
                shutil.move(file_path, folder_path)
                module_logger.debug(f"File {file} archived successfully.")
            except Exception as e:
                module_logger.error(f"Unable to archive file {file}. Error: {str(e)}")
        else:
            module_logger.error(f"File {file} does not exist.")


def clean_files(archive_path, archive_days):
    current_time = time.time()
    count = 0
    archive_dir = os.path.abspath(archive_path)

    for root, dirs, files in os.walk(archive_dir, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            creation_time = os.path.getctime(file_path)
            days_difference = (current_time - creation_time) // (24 * 3600)

            if days_difference >= archive_days:
                try:
                    os.remove(file_path)
                    count += 1
                    module_logger.debug(f"Successfully cleaned file: {file_path}")
                except Exception as e:
                    module_logger.error(f"Failed to clean file: {file_path}, Error: {str(e)}")
                    traceback.print_exc()

        # Clean up empty directories

        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                os.rmdir(dir_path)
            except Exception as e:
                module_logger.error(f"Failed to remove directory: {dir_path}, Error: {str(e)}")
                traceback.print_exc()

    module_logger.info(f"Cleaned {count} files.")
