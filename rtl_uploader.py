import csv
import json
import argparse
import os
from pathlib import Path

from lib.audio_file_handler import create_json, convert_mp3_m4a, archive_files, clean_files
from lib.logging_handler import CustomLogger
from lib.openmhz_handler import upload_to_openmhz
from lib.rdio_handler import upload_to_rdio


def parse_arguments():
    parser = argparse.ArgumentParser(description='Process Arguments.')
    parser.add_argument("call_path", help="Path to install dir.")
    parser.add_argument("app_config_path", help="Application config.json with path.")
    parser.add_argument("sys_name", help="System Name.")
    parser.add_argument("audio_mp3", help="Path to MP3.")
    args = parser.parse_args()

    return args


def get_paths(args):
    root_path = os.getcwd()
    config_file = 'config.json'
    config_path = args.app_config_path
    mp3_path = args.audio_mp3
    m4a_path = mp3_path.replace(".mp3", ".m4a")
    log_path = mp3_path.replace(".mp3", ".log")
    json_path = mp3_path.replace(".mp3", ".json")
    system_name = args.sys_name
    return config_path, mp3_path, m4a_path, log_path, json_path, system_name


def load_config(config_path, app_name, system_name, log_path):
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        logger = CustomLogger(config_data["log_level"], app_name, log_path).logger
        system_config = config_data["systems"][system_name]
        logger.info(f'Successfully loaded configuration.')
        return config_data, logger, system_config
    except FileNotFoundError:
        print(f'Configuration file {config_path} not found.')
        exit(0)
    except json.JSONDecodeError:
        print(f'Configuration file {config_path} is not in valid JSON format.')
        exit(0)


def load_csv_channels(system_config, csv_headers, logger):
    try:
        if system_config.get("talkgroup_csv_path", "") == "":
            logger.error("The path for the CSV file is missing or empty.")
            exit(1)
        with open(system_config["talkgroup_csv_path"], 'r') as csv_file:
            lines = csv_file.read().splitlines()
            reader = csv.DictReader(lines, fieldnames=csv_headers)
            first_row = next(reader, None)
            if first_row is not None and first_row[csv_headers[0]] != csv_headers[0] and first_row[csv_headers[1]] != \
                    csv_headers[1]:
                # The first two fields of the first row don't match the headers, so it's a data row.
                # Include it in the final data by creating a new list with it as the first element.
                talkgroup_data = [first_row] + [row for row in reader]
            else:
                # The first two fields of the first row match the headers, so it's a header row. Skip it.
                talkgroup_data = [row for row in reader]
        logger.debug(talkgroup_data)
        return talkgroup_data
    except KeyError:
        logger.error("Error: The 'talkgroup_csv_path' key is not present in system_config.")
        exit(1)
    except FileNotFoundError:
        logger.error(f"Error: File not found at {system_config['talkgroup_csv_path']}.")
        exit(1)
    except csv.Error:
        logger.error("Error: There was an issue with the CSV file/format.")
        exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        exit(1)


def main():
    app_name = "icad_rtl_uploader"
    args = parse_arguments()
    config_path, mp3_path, m4a_path, log_path, json_path, system_name = get_paths(args)
    config_data, logger, system_config = load_config(config_path, app_name, system_name, log_path)

    # check if mp3 exists
    mp3_exists = os.path.isfile(mp3_path)
    if not mp3_exists:
        logger.error("No MP3 File Exiting")
        exit(1)

    csv_headers = ["talkgroup_decimal", "channel_frequency", "pl_tone", "talkgroup_alpha_tag", "talkgroup_name",
                   "talkgroup_service_type", "talkgroup_group", "channel_enable"]

    talkgroup_data = load_csv_channels(system_config, csv_headers, logger)

    try:
        call_data = create_json(os.path.basename(mp3_path), os.path.dirname(mp3_path), json_path, talkgroup_data)
        if not call_data:
            logger.error("Could Not Create Call Data JSON")
            exit(1)
    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error("Could Not Create Call Data JSON")
        exit(1)

    logger.debug(call_data)

    # TODO Some Sort of Check For Duplicate Transmissions based on timestamp and length

    # Upload to RDIO
    for rdio in system_config["rdio_systems"]:
        if rdio["enabled"] == 1:
            try:
                upload_to_rdio(rdio, mp3_path, json_path)
                logger.info(f"Successfully uploaded to RDIO server: {rdio['rdio_url']}")
            except Exception as e:
                logger.error(f"Failed to upload to RDIO server: {rdio['rdio_url']}. Error: {str(e)}", exc_info=True)
                continue
        else:
            logger.info(f"RDIO system is disabled: {rdio['rdio_url']}")
            continue

    # Upload to OpenMHZ
    if system_config["openmhz"]["enabled"] == 1:
        # Convert MP3 to M4A
        convert_result = convert_mp3_m4a(mp3_path)
        if not convert_result:
            exit(1)
        openmhz_result = upload_to_openmhz(system_config["openmhz"], m4a_path, call_data)
        logger.debug(openmhz_result)

    if system_config["archive_days"] > 0:
        files = [log_path, json_path, mp3_path, m4a_path]
        archive_files(files, system_config["archive_path"])
        clean_files(system_config["archive_path"], system_config["archive_days"])
    elif system_config["archive_days"] == 0:
        pass
    elif system_config["archive_days"] == -1:
        files = [log_path, json_path, mp3_path, m4a_path]
        for file in files:
            file_path = Path(file)
            if file_path.is_file():
                try:
                    os.remove(file_path)
                    logger.debug(f"File {file} removed successfully.")
                except Exception as e:
                    logger.error(f"Unable to remove file {file}. Error: {str(e)}")
            else:
                logger.error(f"File {file} does not exist.")


if __name__ == "__main__":
    main()
