The supplied fixed-camera conveyor_1.mp4 uses normalized belt boundaries:
left top/bottom 0.27/0.07; right top/bottom 0.68/0.88.
Override VISION_LEFT_EDGE_TOP, VISION_LEFT_EDGE_BOTTOM, VISION_RIGHT_EDGE_TOP,
and VISION_RIGHT_EDGE_BOTTOM when the camera or belt geometry changes.
VISION_ALIGNMENT_ZERO_MM calibrates the lateral zero; VISION_BELT_WIDTH_MM
sets physical scale. Alignment now uses belt boundary gradients, not ore position.

Damage is a localized edge-texture screening score, not a trained probability.
Two affected strips are required and the score is smoothed over successive frames.
It can confuse dirt, joins, lighting, and edge damage; defects covered by material
cannot be assessed. Calibrate against labeled healthy/damaged recordings before
using this as an operational detector. No PLC stop commands are issued.

Backend alarm thresholds and recovery hysteresis remain authoritative. Vision
uses the same warning/critical environment variables and defaults.
