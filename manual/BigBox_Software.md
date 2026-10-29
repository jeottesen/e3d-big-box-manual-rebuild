# BigBox Software

Archived 20201204024242 · source: wiki.e3d-online.com/wiki/BigBox_Software

**Contents**

- [Marlin](#marlin)
- [BigBox Slicer Profiles](#bigbox-slicer-profiles)
  - [Simplify3D](#simplify3d)
  - [Slic3r](#slic3r)
- [OctoPrint](#octoprint)
- [Where next?](#where-next)

## Marlin

Marlin is a firmware for RepRap 3D printers, the software that resides on the controller board and controls the input/output, voltage states, and movement of the 3D printer.

The firmware is available for download and is pre-configured for your BigBox including things like PID settings. We will periodically update this software as the need arises so consider subscribing to the repositories.

**[github.com/BigBox3D](https://github.com/BigBox3D)**

The source is configured for the current production state of the BigBox, you may have to alter it if you have a different setup. Have look at the branches for the four support setups.

For instructions on flashing the firmware read the [BigBox Firmware Flashing Guide](BigBox_Firmware_Flashing_Guide.md "BigBox Firmware Flashing Guide").

We have precompiled version-specific firmware builds and uploaded them to GitHub [BigBox Marlin Firmware Releases](https://github.com/BigBox3D/Marlin/releases).

## BigBox Slicer Profiles

### [Simplify3D](https://www.simplify3d.com/)

Simplify3D profiles are available in our [Settings repository for Simplify3D](https://github.com/BigBox3D/Simplify3D) on GitHub.

### [Slic3r](http://slic3r.org/)

We have an alpha release of the BigBox Slic3r profile. It will work with all versions (Lite / Pro / Dual) but do note it is only for a single extruder.

BigBox_Slic3r_config_bundle.ini *(dead link)*

## OctoPrint

[OctoPrint](http://octoprint.org/) is a so called host software for 3D printers that controls your 3D printer and sends it the actual commands to do its job.

OctoPrint differs from existing host solutions in that its major focus is to provide a web interface that allows controlling the printer remotely from anywhere on the network or even the internet while offering the same responsiveness and feedback options available on native host applications like the ones listed above. In order to achieve this, OctoPrint makes heavy use of current web technologies and frameworks, such as AJAX and HTML5 web sockets.

OctoPrint was developed to be run on small embedded devices such as the popular [Raspberry Pi](https://www.raspberrypi.org/). It allows you to turn your existing 3D printer into a WiFi enabled one and untether it from your laptop or work station.

Please refer to the [BigBox OctoPrint Upgrade](BigBox_OctoPrint_Upgrade.md "BigBox OctoPrint Upgrade") for instructions.

## Where next?

Home to the [BigBox Build Manual Main Index](BigBox_Build_Manual.md "BigBox Build Manual")
