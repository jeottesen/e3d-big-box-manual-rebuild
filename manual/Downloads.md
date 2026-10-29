# Downloads

**Contents**

- [Simplify3D profiles](#simplify3d-profiles)
- [Firmware](#firmware)
- [SD card files](#sd-card-files)
- [Still missing](#still-missing)

Files the wiki linked to that are no longer on the wiki, and where to find them now. They are linked, not copied: most of these repositories have no licence. Checked against the repositories on 2026-10-29.

## Simplify3D profiles

The Software page offered Simplify3D profiles, but the files were hosted on the wiki and are gone. The BigBox repository has profiles, and a community repository has a second set whose settings follow the material, quality and extruder you choose.

- [BigBox Pro.fff](https://github.com/BigBox3D/Simplify3D/blob/master/BigBox%20Pro.fff) – BigBox3D/Simplify3D
- [BigBox Dual.fff](https://github.com/BigBox3D/Simplify3D/blob/master/BigBox%20Dual.fff) – BigBox3D/Simplify3D
- [BigBox Hybrid-Pro.fff](https://github.com/BigBox3D/Simplify3D/blob/master/BigBox%20Hybrid-Pro.fff) – BigBox3D/Simplify3D
- [BigBox Hybrid-Dual.fff](https://github.com/BigBox3D/Simplify3D/blob/master/BigBox%20Hybrid-Dual.fff) – BigBox3D/Simplify3D
- [BigBox Print Farm.fff](https://github.com/BigBox3D/Simplify3D/blob/master/BigBox%20Print%20Farm.fff) – BigBox3D/Simplify3D
- [BigBox-Settings: README](https://github.com/Alex9779/BigBox-Settings/blob/master/README.md) – Alex9779/BigBox-Settings; explains the profiles
- [BigBox Pro.fff](https://github.com/Alex9779/BigBox-Settings/blob/master/Pro/Simplify3D/BigBox%20Pro.fff) – Alex9779/BigBox-Settings
- [BigBox Dual.fff](https://github.com/Alex9779/BigBox-Settings/blob/master/Dual/Simplify3D/BigBox%20Dual.fff) – Alex9779/BigBox-Settings
- [BigBox Hybrid-Pro.fff](https://github.com/Alex9779/BigBox-Settings/blob/master/Hybrid-Pro/Simplify3D/BigBox%20Hybrid-Pro.fff) – Alex9779/BigBox-Settings
- [BigBox Hybrid-Dual.fff](https://github.com/Alex9779/BigBox-Settings/blob/master/Hybrid-Dual/Simplify3D/BigBox%20Hybrid-Dual.fff) – Alex9779/BigBox-Settings
- [BigBox Hybrid-Dual Mirrored.fff](https://github.com/Alex9779/BigBox-Settings/blob/master/Hybrid-Dual/Simplify3D/BigBox%20Hybrid-Dual%20Mirrored.fff) – Alex9779/BigBox-Settings
- [BigBox Dual Titan.fff](https://github.com/Alex9779/BigBox-Settings/blob/master/Dual%20Titan/Simplify3D/BigBox%20Dual%20Titan.fff) – Alex9779/BigBox-Settings
- [BigBoxBedAssembly.stl](https://github.com/Alex9779/BigBox-Settings/blob/master/BigBoxBedAssembly.stl) – a model of the BigBox bed for Simplify3D; Alex9779/BigBox-Settings

## Firmware

Precompiled Marlin builds for each BigBox version, from the BigBox firmware repository. The mesh bed levelling builds need the IR sensor moved to the heated bed.

- [marlin_direct_dual.hex](https://github.com/BigBox3D/Firmware/blob/master/marlin_direct_dual.hex) – BigBox v1.0 Dual (Direct Dual), Kickstarter
- [marlin_direct_pro.hex](https://github.com/BigBox3D/Firmware/blob/master/marlin_direct_pro.hex) – BigBox v1.0 Pro (Direct Pro), Kickstarter
- [marlin_hybrid_dual.hex](https://github.com/BigBox3D/Firmware/blob/master/marlin_hybrid_dual.hex) – BigBox v1.1 Dual Hybrid (Titan and non-Titan), auto bed levelling
- [marlin_hybrid_pro.hex](https://github.com/BigBox3D/Firmware/blob/master/marlin_hybrid_pro.hex) – BigBox v1.1 Pro Hybrid (Titan and non-Titan), auto bed levelling
- [marlin_hybrid_dual_mesh.hex](https://github.com/BigBox3D/Firmware/blob/master/marlin_hybrid_dual_mesh.hex) – BigBox v1.1 Dual Hybrid, mesh bed levelling
- [marlin_hybrid_pro_mesh.hex](https://github.com/BigBox3D/Firmware/blob/master/marlin_hybrid_pro_mesh.hex) – BigBox v1.1 Pro Hybrid, mesh bed levelling
- [Firmware README](https://github.com/BigBox3D/Firmware/blob/master/README.md) – which file is for which version, and how to flash it
- [BigBox Marlin source](https://github.com/BigBox3D/Marlin) – one branch per BigBox version (GPL v3)

## SD card files

The files that came on the SD card in the kit.

- [3DBenchy.stl](https://github.com/BigBox3D/SD-Card/blob/master/3DBenchy.stl) – BigBox3D/SD-Card
- [Pro/3DBenchy.gcode](https://github.com/BigBox3D/SD-Card/blob/master/Pro/3DBenchy.gcode) – sliced for the Pro
- [Dual/3DBenchy.gcode](https://github.com/BigBox3D/SD-Card/blob/master/Dual/3DBenchy.gcode) – sliced for the Dual
- [Pro/calibration/extruder_0.gcode](https://github.com/BigBox3D/SD-Card/blob/master/Pro/calibration/extruder_0.gcode)
- [Dual/calibration/extruder_0.gcode](https://github.com/BigBox3D/SD-Card/blob/master/Dual/calibration/extruder_0.gcode)
- [Dual/calibration/extruder_1.gcode](https://github.com/BigBox3D/SD-Card/blob/master/Dual/calibration/extruder_1.gcode)

## Still missing

Not in the repositories above, and not kept by the Wayback Machine.

- BigBox_Fixings.pdf – the fixings list linked from the Bill of Materials (it was on Dropbox)
- BRACKET_PRINTED.pdf – the Titan mounting bracket engineering drawing linked from Titan Assembly (it was on files.e3d-online.com)
- BigBox_Slic3r_config_bundle.ini and BigBoxSingle-alpha-settings.fff – the early alpha Slic3r and Simplify3D profiles (they were on Dropbox); no Slic3r profile was found in the repositories
- Dual Experimental.fff – the experimental dual-extruder profile described in the appendix
