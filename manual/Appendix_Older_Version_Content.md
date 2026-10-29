# Appendix Older Version Content

**Contents**

- [Slicer profiles (older Software page)](#slicer-profiles-older-software-page)
  - [Simplify3D](#simplify3d)
  - [Slic3r](#slic3r)
- [Simplify3D alpha profile (older First Print page)](#simplify3d-alpha-profile-older-first-print-page)
- [Slic3r alpha profile (older First Print page)](#slic3r-alpha-profile-older-first-print-page)

Content that appeared in older versions of this manual and was later removed, kept here for completeness. It is not part of the current build instructions. Current copies of the profiles and firmware are listed on the [Downloads](Downloads.md) page.

## Slicer profiles (older Software page)

From the BigBox Software page, version 20160601234712. Describes the Simplify3D and Slic3r profiles that were once offered, including the experimental dual-extruder profile. File and download links in this section pointed to files that the archive did not keep.

### [Simplify3D](https://www.simplify3d.com/)

The provided profiles are centered around printing E3D's Everyday PLA *(dead link; [archived copy](https://web.archive.org/web/20161105152053/http://e3d-online.com/All-Filament&filter=5,24,11))*, you will need to adjust the profile settings to suite your chosen filament.

Pro.fff *(dead link; [archived copy](https://web.archive.org/web/20160831005447/http://files.e3d-online.com/BigBox/Slicer%20Configs/Simplify3D/bigbox_pro.fff))*

This is the standard profile for Pro & Lite BigBox Printers.

Dual.fff *(dead link; [archived copy](https://web.archive.org/web/20160531182702/http://files.e3d-online.com/BigBox/Slicer%20Configs/Simplify3D/bigbox_dual.fff))*

This is the standard profile for Dual BigBox Printers.

Dual Experimental.fff *(dead link; [archived copy](https://web.archive.org/web/20160831005324/http://files.e3d-online.com/BigBox/Slicer%20Configs/Simplify3D/bigbox_dual_experimental.fff))*

This profile features an experimental *Layer-Change* script which removed the need to use a *Prime-Pillar* or an *Ooze-Sheild*. Use with caution. **Note**: This profile should only be used when printing with both extruders and using two filaments. Choosing this profile when only one extruder is in use will cause errors with your prints. You will need to change the *steps-per-mm* in the *Tool Change Script* to match your filaments.

### [Slic3r](http://slic3r.org/)

We have an alpha release of the BigBox Slic3r profile. It will work with all versions (Lite / Pro / Dual) but do note it is only for a single extruder.

BigBox_Slic3r_config_bundle.ini *(dead link)*

## Simplify3D alpha profile (older First Print page)

From the Your First Print page, version 20151230221140. Early single-extruder profile. File and download links in this section pointed to files that the archive did not keep.

We have an alpha release of the BigBox S3D profile. It will work with all versions (Lite / Pro / Dual) but do note it is only for a single extruder.

`https://dl.dropboxusercontent.com/u/54348751/BigBoxSingle-alpha-settings.fff` *(dead link)*

## Slic3r alpha profile (older First Print page)

From the Your First Print page, version 20151230221140. Early single-extruder profile. File and download links in this section pointed to files that the archive did not keep.

We have an alpha release of the BigBox Slic3r profile. It will work with all versions (Lite / Pro / Dual) but do note it is only for a single extruder.

`https://dl.dropboxusercontent.com/u/54348751/BigBox_Slic3r_config_bundle.ini` *(dead link)*
