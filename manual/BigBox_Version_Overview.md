# BigBox Version Overview

Archived 20210128113613 · source: wiki.e3d-online.com/wiki/BigBox_Version_Overview · [archive link](https://web.archive.org/web/20210128113613/https://wiki.e3d-online.com/BigBox_Version_Overview)

**Contents**

- [E3D supported versions](#e3d-supported-versions)
  - [BigBox Pro](#bigbox-pro)
  - [BigBox Dual](#bigbox-dual)
  - [BigBox Pro Hybrid Titan](#bigbox-pro-hybrid-titan)
  - [BigBox Dual Hybrid Titan](#bigbox-dual-hybrid-titan)
- [Derived versions](#derived-versions)
  - [BigBox Pro Hybrid](#bigbox-pro-hybrid)
  - [BigBox Dual Hybrid](#bigbox-dual-hybrid)
- [Special (community built) versions](#special-community-built-versions)
  - [BigBox Dual Hybrid Titan Mirrored](#bigbox-dual-hybrid-titan-mirrored)
  - [BigBox Dual Titan](#bigbox-dual-titan)
- [Remarks](#remarks)
  - [Kickstarter upgrade to Hybrid/V1.1](#kickstarter-upgrade-to-hybridv11)
- [Where next?](#where-next)

Due to the open design of the BigBox there are already several versions in the wild. Also the design was refined after the Kickstarter campaign and the release of the Titan introduced additional options.

## E3D supported versions

### BigBox Pro

aka Kickstarter Pro or V1.0 Pro

- Build volume: 300 x 200 x 300
- Extruder 0: direct (default E steps: 304)
- Auto bed leveling
- [Firmware source repository](https://github.com/BigBox3D/Marlin/tree/Pro)
- [Download firmware](https://github.com/BigBox3D/Marlin/releases/download/1.1.0-RC6/Marlin.Pro.hex)

### BigBox Dual

aka Kickstarter Dual or V1.0 Dual

- Build volume
  - single nozzle print either left or right: 260 x 200 x 300
  - dual nozzle print: 220 x 200 x 300
- Extruder 0 (left): direct (default E steps: 304)
- Extruder 1 (right): direct (default E steps: 304)
- Mesh bed levelling
- [Firmware source repository](https://github.com/BigBox3D/Marlin/tree/Dual)
- [Download firmware](https://github.com/BigBox3D/Marlin/releases/download/1.1.0-RC6/Marlin.Dual.hex)

### BigBox Pro Hybrid Titan

aka Pro V1.1 with Titan extruder

- Build volume
  - Factory V1.1: 300 x 200 x 300
  - Kickstarter upgrade: 290 x 200 x 300
- Extruder 0 (right): Titan direct (default E steps: 417.5)
- Auto bed leveling
- [Firmware source repository](https://github.com/BigBox3D/Marlin/tree/Hybrid-Pro)
- [Download firmware](https://github.com/BigBox3D/Marlin/releases/download/1.1.0-RC6/Marlin.Hybrid-Pro.hex)

### BigBox Dual Hybrid Titan

aka Dual V1.1 with Titan extruders

- Build volume
  - Factory V1.1: 300 x 200 x 300 (for single nozzle and dual nozzle prints)
  - Kickstarter upgrade: 290 x 200 x 300 (for single nozzle and dual nozzle prints, see \#Kickstarter upgrade to Hybrid)
- Extruder 0 (left): Titan bowden (default E steps: 417.5)
- Extruder 1 (right): Titan direct (default E steps: 417.5)
- Auto bed levelling
- [Firmware source repository](https://github.com/BigBox3D/Marlin/tree/Hybrid-Dual)
- [Download firmware](https://github.com/BigBox3D/Marlin/releases/download/1.1.0-RC6/Marlin.Hybrid-Dual.hex)

## Derived versions

The derived versions are actually supported versions but some changes are needed which can be done using the LCD menus.

### BigBox Pro Hybrid

aka Pro V1.1 derived from [\#BigBox Pro Hybrid Titan](#bigbox-pro-hybrid-titan)

- Build volume
  - Factory V1.1: 300 x 200 x 300
  - Kickstarter upgrade: 290 x 200 x 300
- Extruder 0 (right): direct (default E steps: 304)

### BigBox Dual Hybrid

aka Dual V1.1 derived from [\#BigBox Dual Hybrid Titan](#bigbox-dual-hybrid-titan)

- Build volume
  - Factory V1.1: 300 x 200 x 300 (for single nozzle and dual nozzle prints)
  - Kickstarter upgrade: 290 x 200 x 300 (for single nozzle and dual nozzle prints, [\#Kickstarter upgrade to Hybrid/V1.1](#kickstarter-upgrade-to-hybridv11))
- Extruder 0 (left): direct (default E steps: 304)
- Extruder 1 (right): direct (default E steps: 304)

## Special (community built) versions

### BigBox Dual Hybrid Titan Mirrored

aka Dual V1.1 with Titan extruders derived from [\#BigBox Dual Hybrid Titan](#bigbox-dual-hybrid-titan)

- Build volume
  - Factory V1.1: 300 x 200 x 300 (for single nozzle and dual nozzle prints)
  - Kickstarter upgrade: 290 x 200 x 300 (for single nozzle and dual nozzle prints)
- Extruder 0 (**right**): Titan direct (default E steps: 417.5)
- Extruder 1 (**left**): Titan bowden (default E steps: 417.5)

### BigBox Dual Titan

- Build volume: 300 x 200 x 300 (for single nozzle and dual nozzle prints)
- Extruder 0 (**left**): Titan direct (default E steps: 417.5)
- Extruder 1 (**right**): Titan direct (default E steps: 417.5)

## Remarks

### Kickstarter upgrade to Hybrid/V1.1

Due to the mounting situation of the hybrid head the case of the V1.1 BigBox had to be changed to allow the full build volume on the X axis of 300mm.

Unfortunately the Kickstarter BigBox does not have that change so the build volume of and upgrade Kickstarter BigBox is slightly smaller.

Currently there are two options to get to or near the full build volume:

1. Cut the top frame part
2. Use a slightly modified hybrid head

Solution 1 allows you to use all the factory parts for the BigBox V1.1 by cutting about 10mm of the inner right side of the top frame part. The DXF for the new is available on Thingiverse ([http://www.thingiverse.com/thing:1521722](http://www.thingiverse.com/thing:1521722)) in the ZIP file "DXF.zip" named "top.dxf".

Solution 2 consists of a changed top part for the hybrid carriage called "lifted". You can get that part also from Thingiverse ([http://www.thingiverse.com/thing:1515488](http://www.thingiverse.com/thing:1515488)). Using this part will bring your build volume up to 297 x 200 x 300. To get the last 3mm a solution is planned to reduce the offset of the nozzles to 35mm.

## Where next?

Home to the [BigBox Build Manual Main Index](BigBox_Build_Manual.md "BigBox Build Manual")
