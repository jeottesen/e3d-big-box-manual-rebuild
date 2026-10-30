# Mesh Levelling the Non-Hybrid Dual

Rebuilt page · source: wiki.e3d-online.com/wiki/Mesh_Levelling_the_Non-Hybrid_Dual · [archive link (parent page)](https://web.archive.org/web/20160811132429/http://wiki.e3d-online.com:80/wiki/Printer_Commissioning)

Recovered from an older version of Printer Commissioning (20160811132429), section "(9.2) Mesh Levelling the Dual" — the separate wiki page is not in the archive.

\[image not archived: "Bedlevelling_paper.jpg" Caption: "Mesh levelling."\]

The Mesh levelling sequence performs a more accurate and consistent function that the standard Auto levelling used by the Pro & Lite versions.

The process is a little more involved but the results are worth the extra work.

If you are interested in the mechanics of the process there is a short paper written by the engineer who implemented the system into Marlin \| [Mesh Bed Levelling](https://github.com/MarlinFirmware/Marlin/wiki/Manual-bed-leveling---mesh-bed-leveling).

To begin cut a short strip of paper.

\[image not archived: "Bedlevelling_start.jpg" Caption: "Level Bed."\]

Check the printer is clear of potential hazards.

Via the **Prepare** menu, select **Level Bed**.

The BigBox will home X, Y & Z and then move to a position approximately X10, Y10.

\[image not archived: "Bedlevelling_paper_next.jpg" Caption: "Papered."\]

Place the strip of paper under the left nozzle.

\[image not archived: "Bedlevelling_lcd_adj.jpg" Caption: "LCD."\]

The LCD will display a value of 4.0.

Rotating the knob will adjust the position of the bed.

Move the bed up so that the paper is just able to slide around under the nozzle.

Push the knob to continue.

\[image not archived: "Bedlevelling_next.jpg" Caption: "Next."\]

The Printhead will then move to the next position.

\[image not archived: "Bedlevelling_next_adj.jpg" Caption: "Adjust."\]

Place the paper under the nozzle again and adjust the bed's height as before.

\[image not archived: "Bedlevelling_last.jpg" Caption: "Last one."\]

There are a total of 9 points measured over the bed with the last being in the back right.

\[image not archived: "Bedlevelling_home.jpg" Caption: "Home."\]

When the process has complete the Printhead will return to the home position, this time however **it will move to X5, Y5, Z4.** This can be seen on the LCD.

\[image not archived: "Bedlevelling_store.jpg" Caption: "Store."\]

From the **Control** menu select **Store memory**.

**Note**: The LCD will beep but nothing will change on the screen when the knob is pressed.

The Mesh information will be permanently stored to the Rumba's EEPROM. You will not need to level the bed again unless you make any mechanical changes to the printer.

At this stage you may wish to **adjust the height of the "print cooling" fans** (those at the left and right of the nozzles) These fans have a duct to prevent the air from them cooling the nozzles (look closely) as if the nozzle temperature drops too low the print will fail. **Adjust these fans so that they are a few mm higher than the tip of the nozzles.** i.e. just high enough to avoid the print itself and also high enough not to hit the wiper on the bucket.
