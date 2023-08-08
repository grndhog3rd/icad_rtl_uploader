# iCAD RTL Airband Uploader

### Requirements

#### Python 3.10
* colorama
* pytz
* requests
* mutagen

### Notes
Must use my **modified** version of RTL Airband. This will not work with the version from the official repo.
https://github.com/TheGreatCodeholio/RTLSDR-Airband


### Usage

For use with RTL_Airband modifed to run scripts after a file has been recorded. It will upload the transmission to RDIO or OpenMHZ.

### Installation

```
git clone https://github.com/TheGreatCodeholio/icad_rtl_uploader.git
cd icad_rtl_uploader
pip3 install -r requirements.txt
chmod +x rtl_upload.sh
```

### Configuration

##### RTL Airband Configuration Example

In the frequency block for each frequency. 
`split_on_transmission = True;` must be enabled. Splits transmission after `silence_release` time.
`include_freq = True;` must be enabled. Adds frequency to filename. Needed to parse `example_channels.csv` for talkgroup info.

* `silence_release` - How long to wait for next transmission before ending current recording.
* `minimum_length` - How long the file must be in seconds to be kept. 
* `external_script` - Path to BASH script to run. Followed by a space and the system name. System name is used in uploader config to differentiate settings for each system. 

##### Example Output Config

```
{
   type = "file";
   directory = "/home/adminlocal/bc_recordings";
   filename_template = "example-system";
   split_on_transmission = True;
   silence_release = 2.0;
   minimum_length = 1.0;
   external_script = "/home/adminlocal/icad_rtl_uploader/upload.sh example-system"
   squelch_threshold = -30;
   include_freq = true;
}
```

#### Uploader Configuration File
Here is a run down of the options in the uploader configuration file `etc/config.json`. Using bullets to give an example of the hierarchy of the JSON file. 
* `log_level` - 1 Debug, 2 Info, 3 Warning, 4, Critical, 5 Error
* `systems` - Holds systems in JSON format.
* * `example-system` - system name and holds system config data.
* * * `archive_days` - -1 delete files after finished, 0 do nothing, 1 or more how many days to keep an archive of files.
* * * `archive_path` - Path for archiving files. Archives in year/month/day/file structure
* * * `talkgroup_csv_path` - Absolute path to channels.csv in the same format as Trunk Recorder Channels File.
* * * `rdio_systems` - list of RDIO system configs in JSON format. One for each RDIO instance that you want the transmission to go to.
* * * * `enabled` - 0 Disabled 1 Enabled, Enables RDIO System
* * * * `system_id` - RDIO System ID (Established in RDIO Admin)
* * * * `rdio_url` - RDIO URL to post transmission to.
* * * * `rdio_api_key` - API Key from RDIO
* * * `openmhz` - Configuration for uploading to OpenMHZ
* * * * `enabled` - 0 Disabled, 1 Enabled. Enable/Disable Uploading to OpenMHZ
* * * * `short_name` - Short Name for your system. (Established on OpenMHZ)
* * * * `api_key` - API Key for OpenMHZ

#### Example Config
```json
{
  "log_level": 1,
  "systems": {
    "example-system": {
      "archive_days": 0,
      "archive_path": "/home/example/rtl_archive",
      "talkgroup_csv_path": "/home/example/icad_rtl_uploader/etc/example_channels.csv",
      "rdio_systems": [
        {
          "enabled": 0,
          "system_id": 1111,
          "rdio_url": "http://example.com:3000/api/trunk-recorder-call-upload",
          "rdio_api_key": "example-api-key"
        }
      ],
      "openmhz": {
        "enabled": 0,
        "short_name": "example",
        "api_key": "example-api-key"
      }
    }
  }
}
```

### Bash Script
`rtl_upload.sh` Used to jumpstart Python from BASH. RTL Airband modification only supports running BASH scripts.
**Modify the rtl_upload.sh** to fit your needs and that should be the target of `external_script` in the RTL Airband Configuration.



