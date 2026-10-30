# BigBox OctoPrint Upgrade

Archived 20230529010658 · source: wiki.e3d-online.com/wiki/BigBox_OctoPrint_Upgrade · [archive link](https://web.archive.org/web/20230529010658/https://wiki.e3d-online.com/BigBox_OctoPrint_Upgrade)

**Contents**

- [Prepping the SD Card](#prepping-the-sd-card)
- [Terminal Configuration](#terminal-configuration)
- [Login Options & Update](#login-options--update)
- [Settings](#settings)
- [Plugins](#plugins)
- [Printing](#printing)
- [Where Next?](#where-next)

## Prepping the SD Card

*\[image not archived: "Oictoprint_website.jpg" Caption: "OctoPrint Website."\]*

Visit **[octoprint.org](http://octoprint.org/)**

Click the **Download** link.

*\[image not archived: "Oictoprint_download.jpg" Caption: "Download."\]*

OctoPrint is packaged into a downloadable .img distribution which has been designed specifically for the Raspberry Pi. This packaged is known as **OctoPi**.

You will need to download the latest version of the distribution and write it to your SD Card.

To begin click **Download OctoPi.**

(Marlin is mentioned later on... this is the firmware written to the memory (EPROM) on the Rumba)

[http://reprap.org/wiki/Marlin](http://reprap.org/wiki/Marlin)

*\[image not archived: "Octoprint_write.jpg" Caption: "Write to SD."\]*

You'll need to unpack the .img file into a folder, we recommend **[7zip](http://www.7-zip.org/)** to unpack the archive. Be warned it expands to over 3gb.

Once you have extracted the file following the instructions on the Raspberry Pi website for writting .img files to SD Cards \| **[installing images](https://www.raspberrypi.org/documentation/installation/installing-images/README.md)**.

*\[image not archived: "Octoprint_writing.jpg" Caption: "Writting."\]*

Writing the image to the SD Card.

*\[image not archived: "Putty_download.jpg" Caption: "PuTTY."\]*

While you wait for the card to finish you can download an [SSH](https://en.wikipedia.org/wiki/Secure_Shell) terminal program.

We use **PuTTY** \| [Download](http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html).

*\[image not archived: "Insert_sd.jpg" Caption: "Insert."\]*

Insert the card into the slot with the contacts facing up.

*\[image not archived: "Push_sd.jpg" Caption: "Push."\]*

Look through the slot to see where the card fits, and so you don't insert it above or below the contacts.

Push the SD Card into the slot.

The slot is spring loaded so you should feel the card click into place.

*\[image not archived: "Insert_network.jpg" Caption: "Network."\]*

Make sure you have a network cable plugged in at the back, also check the other end of the cable is plugged into a router or similar.

Turn on the power.

## Terminal Configuration

*\[image not archived: "Putty_open.jpg" Caption: "PuTTY."\]*

Load up PuTTY.

You'll need to discover the IP of your BigBox. The easiest way is to check via your router.

Enter the IP into the *Host Name* box and click **Open**.

*\[image not archived: "Putty_alert.jpg" Caption: "Alert!"\]*

Read the alert and click **Yes** when you are ready continue.

*\[image not archived: "Putty_login.jpg" Caption: "Login."\]*

Login to your BigBox.

Username \| **pi**

Password \| **raspberry**

**Note**: Nothing will appear on the screen when you type in the password. This is normal for [Linux](http://www.linuxfoundation.org/) based systems.

*\[image not archived: "Putty_config.jpg" Caption: "raspi-config."\]*

At the command prompt type **sudo raspi-config**.

*\[image not archived: "Putty_raspi_config.jpg" Caption: "Configuration."\]*

You will now be presented with the *Raspberry Pi Software Configuration Tool*.

Make sure **Expand Filesystem** is highlighted, then hit enter.

*\[image not archived: "Putty_expand.jpg" Caption: "Expanded."\]*

The SD will be expanded.

Hit Enter to return.

*\[image not archived: "Putty_advanced.jpg" Caption: "Options."\]*

This is all you need to do.

However if you would like to make other changes, such as altering the hostname, which can be done via the **Advanced Options** menu selection, please feel free to do so.

After you have made the changes highlight **Finish** and press enter.

The next screen will ask you if you would like to reboot, Do not reboot.

*\[image not archived: "Putty_reboot.jpg" Caption: "Do Not Reboot."\]*

Do not press enter to reboot.

## Login Options & Update

*\[image not archived: "Browser.jpg" Caption: "PuTTY."\]*

Point your favourite browser towards your BigBox Printer by entering the IP into the address bar.

Upon a successful connection you will be invited to **Configure Access Control**.

The choice is entirely yours as to whether you use the login function.

*\[image not archived: "Reboot.jpg" Caption: "PuTTY."\]*

Swap back to PuTTY and hit enter to reboot.

*\[image not archived: "Bigbox_reboot.jpg" Caption: "reboot."\]*

The server will go offline.

You can close PuTTY as it is no longer required.

(If you want to setup the camera you will have to login again after completing the steps below)

*\[image not archived: "Bigbox_update.jpg" Caption: "Update."\]*

After a few minutes OctoPrint will come back to life. If not, push the refresh button or **F5**.

If you are presented with an *Update Available* pop-up, click **Update Now**.

You may only get the update AFTER you login (if you setup access control)

**Note**: The system will restart during the update process. If this does not happen a window will pop up asking you to manually restart. This can be done via the **System** drop-down menu.

*\[image not archived: "Bigbox_reload.jpg" Caption: "Reload."\]*

After the update has completed you will be prompted to *Please Reload*, click **Reload Now** to do so.

You may get a system restart FAILED if so wait and you will shortly get the Reload Now button

## Settings

*\[image not archived: "Logged_in.jpg" Caption: "Logged In."\]*

If you have made an account login to your BigBox.

*\[image not archived: "Serial_connection.jpg" Caption: "Logged In."\]*

Click **Settings**.

In *Serial Connection* using the drop-down menu change,

Serial Port **/dev/ttyACM0**

Baudrate **230400**

Tick \| **Auto-connect to printer on server start**

*\[image not archived: "Printer_profile.jpg" Caption: "Printer Profiles."\]*

Click *Printer Profile* and click the **edit profile** icon for the default profile.

Change the following fields;

Name: **BigBox**

Model: **Pro** *Dual for Dual*

Colour: **Your Choice**

Volume

X: **300** *260 for Dual*

Z: **280**

Tick: **Heated Bed**

Axis

X: **3000**

Y: **3000**

Number of Extruders: **1** *2 for Dual*

*\[image not archived: "Printer_profile.jpg" Caption: "Printer Temperatures."\]*

Click *Temperatures*.

You can add filaments and change settings as you wish.

*\[image not archived: "Printer_scripts.jpg" Caption: "Printer GCODE Scripts."\]*

Click *GCODE Scripts*.

Leave *Before print job starts* and *After print job completes* blank as this is done in the slicer profiles, available from the [BigBox Software](BigBox_Software.md "BigBox Software") section.

To *After print job is cancelled* add;

(note that these commands below in bold go right at the start)

**;dock**

**T0**

**G1 X70 Y200 F3000**

**G1 X70 Y240 F3000**

To *After print job is paused* add

**M117 Printing Paused.**

To *Before print job is resumed* add

**M117 Printing Resumed.**

To *After connection to printer is established* add

**M117 OctoPrint Connected.**

*\[image not archived: "Printer_appearance.jpg" Caption: "Printer Appearance."\]*

Click *Appearance*.

Title: **BigBox Pro** or **BigBox Dual**

Colour: **As you wish**

Click the big blue **Save** button.

*\[image not archived: "Printer_connect.jpg" Caption: "Connect."\]*

Into the Connect window and from the dropdown menu set the Serial Port to **/dev/ttyACM0**, set the Baudrate to **23400** and tick **Save connection settings**. Then click the **Connect** button.

*\[image not archived: "Printer_online.jpg" Caption: "Online."\]*

It will take a few seconds to connect. Once it does you'll get temperature information and the contents of the SD Card will display on the screen.

*\[image not archived: "Printer_control.jpg" Caption: "Control."\]*

Click the **Control** tab and you'll be able to see the video stream.

## Plugins

*\[image not archived: "Plugins.jpg" Caption: "Plugins."\]*

Click **Settings**, **Plugin Manager** then the big grey **Get More** button.

*\[image not archived: "Plugins_by_date.jpg" Caption: "Plugins By Date."\]*

A new browser window will open listing the latest plugins. Scroll to the bottom and click **More...**

*\[image not archived: "Plugins_eeprom.jpg" Caption: "EEPROM."\]*

Click the link for the **EEPROM Marlin Editor**

Highlight the text in the Installation window.

*\[image not archived: "Plugins_paste.jpg" Caption: "Paste."\]*

Paste the link into the **... from URL** box and click the big blue **Install** button.

*\[image not archived: "Plugins_installing.jpg" Caption: "Installed."\]*

Click **Close** after the intallation has completed.

*\[image not archived: "Plugins_done.jpg" Caption: "Finished installing."\]*

There are quite a few available plugins.

We like to install a few in addition to the EEPROM Editor;

**[Autoselect](http://plugins.octoprint.org/plugins/autoselect/)**

**[DisplayZ](http://plugins.octoprint.org/plugins/displayz/)**

**[Printer Statistics](http://plugins.octoprint.org/plugins/stats/)** *This plugin is configured in OctoPrint's Settings*

## Printing

*\[image not archived: "Printing_timelapse.jpg" Caption: "Timelapse."\]*

You can skip this step if you'd like to leave out recording the print.

Open the **Timelapse** tab on OctoPrint.

Set the *Timelapse Mode* to **On Z Change**. *FPS* to **60** and the *Timelapse post roll* to **1**.

*\[image not archived: "Printing_terminal.jpg" Caption: "Terminal."\]*

Open the **Terminal** tab on OctoPrint.

Into the command box type **G28 *to home the printer and then type*** *G29'* to level the bed.

*\[image not archived: "Printing_temperature.jpg" Caption: "Temperature."\]*

Open the **Temperature** tab on OctoPrint.

Set the nozzle temperature to **210°C** and the bed temperature to **50°C**.

*\[image not archived: "Printing_print.jpg" Caption: "Print."\]*

Load the **3dbenc~1.gco** file into OctoPrint by clicking on the folder icon in the files list. Then click the big blue **Print** button.

Swap to the **Control** tab to see the printer do it's magic.

## Where Next?

Back to [Your First Print](Your_First_Print.md "Your First Print")

Continue to the \[\[\]\]

Home to the [BigBox Build Manual Main Index](BigBox_Build_Manual.md "BigBox Build Manual")
