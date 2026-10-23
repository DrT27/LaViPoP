"""
# ==============================================
#
# LaViPoP - Language-aware Video Post-Processing
#
# ==============================================
#
# DrT 2026
# TopLab - Toplak Laboratory
#
#
# Video post processing:
# - portrait / landscape conversion
# - blurred or static background for portrait -> landscape
# - animated watermark
# - language icon
# - batch generation of both output formats
#
# Watermark positioning:
#
# x1_wm / y1_wm:
#     distance from upper-left corner
#
# x2_wm / y2_wm:
#     end position measured from upper-left origin
#
# Both start and end positions use the same coordinate system:
#     (0, 0) = upper-left corner
#
# The watermark moves from position 1 to position 2.
"""
# LaViPoP - Language-aware Video Post-Processing
#
# Copyright 2026 TopLab - Toplak Laboratory e.U.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ============================================================
# FLAVORS
# ============================================================

FLAVOR_TOPLAB = {
    "background": "background_image.png"

}


# ============================================================
# Output dimensions
# ============================================================

LANDSCAPE_WIDTH = 1920
LANDSCAPE_HEIGHT = 1080

PORTRAIT_WIDTH = 1080
PORTRAIT_HEIGHT = 1920


# ============================================================
# Static background image
# ============================================================
#
# Used only if:
#
#     use_static_background = True
#
# AND a portrait source is converted to landscape.
#

# STATIC_BACKGROUND_PATH = Path(
#     "backgrounds/toplab_solarpunk_HD_260730.png"
# )
STATIC_BACKGROUND_PATH = Path(
    "backgrounds/lavipop_bg1.png"
)


# ============================================================
# Configuration classes
# ============================================================

@dataclass
class WatermarkConfig:
    enabled: bool = True

    # ==========================------------
    # Start position
    #
    # Distance from upper-left corner.
    # ==========================------------

    x1_wm: int = 100
    y1_wm: int = 120

    # ==========================------------
    # End position
    #
    # Same coordinate system as start position:
    # distance from upper-left corner.
    #
    # (0, 0) = upper-left corner.
    # ==========================------------

    x2_wm: int = 100
    y2_wm: int = 120

    # ==========================------------
    # Watermark size
    # ==========================------------

    width: int = 413
    height: int = 195

    # ==========================------------
    # Timing
    # ==========================------------

    start_time: float = 2.0

    seconds_before_end: float = 2.0

    fade_duration: float = 2.0


@dataclass
class LanguageIconConfig:
    enabled: bool = True

    # Position from upper-left corner.
    x: int = 800
    y: int = 1200

    width: int = 32
    height: int = 32

    # Optional timing.
    #
    # If both values are None, the icon is visible
    # for the complete video.
    start_time: Optional[float] = None
    end_time: Optional[float] = None


# ============================================================
# VidPoP processor
# ============================================================

class VidPoPProcessor:
    """
    Reusable VidPoP FFmpeg processor.

    Supports
    --------

    Output formats:

        landscape
            1920 x 1080

        portrait
            1080 x 1920


    Conversion logic
    ----------------

    Landscape source -> landscape:
        scale / crop to 1920 x 1080

    Landscape source -> portrait:
        center crop to 1080 x 1920

    Portrait source -> portrait:
        scale / crop to 1080 x 1920

    Portrait source -> landscape:
        complete portrait video remains visible in foreground

        Background is either:

            use_static_background = False
                enlarged + blurred copy of video

            use_static_background = True
                static background image


    Additional processing
    ---------------------

    - animated watermark
    - optional language icon
    - original audio
    - portrait + landscape batch generation
    """

    def __init__(
        self,
        ffmpeg_path: str | Path,
        ffprobe_path: str | Path,
        use_static_background: bool = False,
    ):
        self.ffmpeg_path = Path(
            ffmpeg_path
        )

        self.ffprobe_path = Path(
            ffprobe_path
        )

        self.use_static_background = (
            use_static_background
        )

        if not self.ffmpeg_path.exists():
            raise FileNotFoundError(
                f"FFmpeg not found: "
                f"{self.ffmpeg_path}"
            )

        if not self.ffprobe_path.exists():
            raise FileNotFoundError(
                f"FFprobe not found: "
                f"{self.ffprobe_path}"
            )

    # ========================================================
    # Utility
    # ========================================================

    def get_video_duration(
        self,
        filename: str | Path,
    ) -> float:
        """
        Return video duration in seconds.
        """

        filename = Path(
            filename
        )

        command = [
            str(self.ffprobe_path),
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            str(filename),
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        data = json.loads(
            result.stdout
        )

        return float(
            data["format"]["duration"]
        )

    # ==========================------------

    def get_video_dimensions(
        self,
        filename: str | Path,
    ) -> tuple[int, int]:
        """
        Return:

            width, height
        """

        filename = Path(
            filename
        )

        command = [
            str(self.ffprobe_path),
            "-v",
            "quiet",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(filename),
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        data = json.loads(
            result.stdout
        )

        streams = data.get(
            "streams",
            []
        )

        if not streams:
            raise ValueError(
                f"No video stream found: "
                f"{filename}"
            )

        width = int(
            streams[0]["width"]
        )

        height = int(
            streams[0]["height"]
        )

        return width, height

    # ========================================================
    # Video format / aspect-ratio filter
    # ========================================================

    def _build_format_filter(
        self,
        source_width: int,
        source_height: int,
        target_format: str,
        static_background_input_index: Optional[int] = None,
    ) -> str:
        """
        Build the first stage of the FFmpeg filter graph.

        The resulting output label is always:

            [video_format]
        """

        source_is_portrait = (
            source_height > source_width
        )

        # ====================================================
        # PORTRAIT OUTPUT
        # ====================================================

        if target_format == "portrait":

            # ==========================----
            # Landscape -> portrait
            #
            # or
            #
            # Portrait -> portrait
            #
            # Fill complete portrait canvas.
            #
            # For landscape input this creates a center crop.
            # ==========================----

            return (
                f"[0:v]"
                f"scale="
                f"{PORTRAIT_WIDTH}:"
                f"{PORTRAIT_HEIGHT}:"
                f"force_original_aspect_ratio=increase,"
                f"crop="
                f"{PORTRAIT_WIDTH}:"
                f"{PORTRAIT_HEIGHT},"
                f"setsar=1"
                f"[video_format]"
            )

        # ====================================================
        # LANDSCAPE OUTPUT
        # ====================================================
        if target_format == "landscape":

            # =================================================
            # Landscape output: 1920 x 1080
            #
            # Preserve the complete source image (4:3, 16:9,
            # 9:16, etc.) without cropping.
            # =================================================

            # No background needed for native 16:9 sources.
            if abs(source_width / source_height - LANDSCAPE_WIDTH / LANDSCAPE_HEIGHT) < 0.001:
                return (
                    f"[0:v]"
                    f"scale={LANDSCAPE_WIDTH}:{LANDSCAPE_HEIGHT},"
                    f"setsar=1"
                    f"[video_format]"
                )

            # =================================================
            # Variant 1: static background image
            # =================================================

            if self.use_static_background:

                if static_background_input_index is None:
                    raise ValueError(
                        "Static background enabled but "
                        "no background input index supplied."
                    )

                return (
                    # Background fills entire landscape frame
                    f"[{static_background_input_index}:v]"
                    f"scale={LANDSCAPE_WIDTH}:{LANDSCAPE_HEIGHT}:"
                    f"force_original_aspect_ratio=increase,"
                    f"crop={LANDSCAPE_WIDTH}:{LANDSCAPE_HEIGHT},"
                    f"setsar=1"
                    f"[background];"

                    # Foreground: complete source frame
                    f"[0:v]"
                    f"scale={LANDSCAPE_WIDTH}:{LANDSCAPE_HEIGHT}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"setsar=1"
                    f"[foreground];"

                    # Center foreground over background
                    f"[background][foreground]"
                    f"overlay=x=(W-w)/2:y=(H-h)/2:"
                    f"shortest=1"
                    f"[video_format]"
                )

            # =================================================
            # Variant 2: blurred source video background
            # =================================================

            return (
                # Split original video
                f"[0:v]"
                f"split=2"
                f"[background_source][foreground_source];"

                # Background: fill, crop, blur
                f"[background_source]"
                f"scale={LANDSCAPE_WIDTH}:{LANDSCAPE_HEIGHT}:"
                f"force_original_aspect_ratio=increase,"
                f"crop={LANDSCAPE_WIDTH}:{LANDSCAPE_HEIGHT},"
                f"gblur=sigma=30,"
                f"eq=brightness=-0.08:saturation=0.90,"
                f"setsar=1"
                f"[background];"

                # Foreground: preserve complete source
                f"[foreground_source]"
                f"scale={LANDSCAPE_WIDTH}:{LANDSCAPE_HEIGHT}:"
                f"force_original_aspect_ratio=decrease,"
                f"setsar=1"
                f"[foreground];"

                # Center foreground over background
                f"[background][foreground]"
                f"overlay=x=(W-w)/2:y=(H-h)/2:"
                f"shortest=1"
                f"[video_format]"
            )
        # if target_format == "landscape":
        #
        #     # ==========================----
        #     # Source is already landscape
        #     # ==========================----
        #
        #     if not source_is_portrait:
        #         return (
        #             f"[0:v]"
        #             f"scale="
        #             f"{LANDSCAPE_WIDTH}:"
        #             f"{LANDSCAPE_HEIGHT}:"
        #             f"force_original_aspect_ratio=increase"
        #             f"crop="
        #             f"{LANDSCAPE_WIDTH}:"
        #             f"{LANDSCAPE_HEIGHT},"
        #             f"setsar=1"
        #             f"[video_format]"
        #         )
        #         # return (
        #         #     f"[0:v]"
        #         #     f"scale="
        #         #     f"{LANDSCAPE_WIDTH}:"
        #         #     f"{LANDSCAPE_HEIGHT}:"
        #         #     f"force_original_aspect_ratio=decrease" # increase,"
        #         #     f"crop="
        #         #     f"{LANDSCAPE_WIDTH}:"
        #         #     f"{LANDSCAPE_HEIGHT},"
        #         #     f"setsar=1"
        #         #     f"[video_format]"
        #         # )
        #
        #     # ==========================----
        #     # Portrait -> landscape
        #     #
        #     # The complete portrait video is retained.
        #     # ==========================----
        #
        #     # =================================================
        #     # Variant 1:
        #     # static background image
        #     # =================================================
        #
        #     if self.use_static_background:
        #
        #         if static_background_input_index is None:
        #             raise ValueError(
        #                 "Static background enabled but "
        #                 "no background input index supplied."
        #             )
        #
        #         return (
        #             # ----------------------------------------
        #             # Background
        #             # ----------------------------------------
        #
        #             f"[{static_background_input_index}:v]"
        #             f"scale="
        #             f"{LANDSCAPE_WIDTH}:"
        #             f"{LANDSCAPE_HEIGHT}:"
        #             f"force_original_aspect_ratio=increase,"
        #             f"crop="
        #             f"{LANDSCAPE_WIDTH}:"
        #             f"{LANDSCAPE_HEIGHT},"
        #             f"setsar=1"
        #             f"[background];"
        #
        #             # ----------------------------------------
        #             # Portrait foreground
        #             #
        #             # Scale to complete output height while
        #             # maintaining original aspect ratio.
        #             # ----------------------------------------
        #
        #             f"[0:v]"
        #             f"scale="
        #             f"-2:"
        #             f"{LANDSCAPE_HEIGHT},"
        #             f"setsar=1"
        #             f"[foreground];"
        #
        #             # ----------------------------------------
        #             # Center foreground over background
        #             # ----------------------------------------
        #
        #             f"[background]"
        #             f"[foreground]"
        #             f"overlay="
        #             f"x=(W-w)/2:"
        #             f"y=(H-h)/2"
        #             f"[video_format]"
        #         )
        #
        #     # =================================================
        #     # Variant 2:
        #     # blurred video stream
        #     # =================================================
        #
        #     return (
        #         # ==========================
        #         # Split original video
        #         # ==========================
        #
        #         f"[0:v]"
        #         f"split=2"
        #         f"[background_source]"
        #         f"[foreground_source];"
        #
        #         # ==========================
        #         # Background
        #         #
        #         # Scale until complete 16:9 frame is covered.
        #         # Then center-crop.
        #         # ==========================
        #
        #         f"[background_source]"
        #         f"scale="
        #         f"{LANDSCAPE_WIDTH}:"
        #         f"{LANDSCAPE_HEIGHT}:"
        #         f"force_original_aspect_ratio=increase,"
        #         f"crop="
        #         f"{LANDSCAPE_WIDTH}:"
        #         f"{LANDSCAPE_HEIGHT},"
        #
        #         # Blur
        #         f"gblur=sigma=30,"
        #
        #         # Slightly darken and desaturate
        #         f"eq="
        #         f"brightness=-0.08:"
        #         f"saturation=0.90,"
        #
        #         f"setsar=1"
        #         f"[background];"
        #
        #         # ==========================
        #         # Foreground
        #         #
        #         # Keep complete portrait image.
        #         # ==========================
        #
        #         f"[foreground_source]"
        #         f"scale="
        #         f"-2:"
        #         f"{LANDSCAPE_HEIGHT},"
        #         f"setsar=1"
        #         f"[foreground];"
        #
        #         # ==========================
        #         # Place foreground in center
        #         # ==========================
        #
        #         f"[background]"
        #         f"[foreground]"
        #         f"overlay="
        #         f"x=(W-w)/2:"
        #         f"y=(H-h)/2"
        #         f"[video_format]"
        #     )
        #
        # raise ValueError(
        #     f"Unknown target format: "
        #     f"{target_format}"
        # )

    # ========================================================
    # Watermark filter
    # ========================================================

    def _build_watermark_filter(
        self,
        duration: float,
        config: WatermarkConfig,
        input_index: int,
        source_label: str,
        output_label: str,
    ) -> str:
        """
        Build animated watermark filter.

        Position 1:
            x1_wm / y1_wm
            distance from upper-left corner

        Position 2:
            x2_wm / y2_wm
            distance from upper-left corner
        """

        fade_in_start = (
            config.start_time
        )

        fade_in_end = (
            config.start_time
            + config.fade_duration
        )

        fade_out_end = (
            duration
            - config.seconds_before_end
        )

        fade_out_start = (
            fade_out_end
            - config.fade_duration
        )

        if fade_out_start <= fade_in_end:
            raise ValueError(
                "Video too short or watermark timing overlaps: "
                "start_time, seconds_before_end and fade_duration "
                "must leave enough visible time."
            )

        movement_duration = (
            fade_out_start
            - config.start_time
        )

        # ==========================--------
        # X movement
        #
        # Both x1_wm and x2_wm are measured from the LEFT.
        #
        # Example:
        #     x1_wm = 108 px   (10% of 1080)
        #     x2_wm = 810 px   (75% of 1080)
        #
        # The watermark therefore moves to the right.
        # ==========================--------

        x_expression = (
            f"{config.x1_wm}"
            f"+("
            f"{config.x2_wm}"
            f"-{config.x1_wm}"
            f")"
            f"*clip("
            f"(t-{config.start_time})"
            f"/{movement_duration},"
            f"0,"
            f"1"
            f")"
        )

        # ==========================--------
        # Y movement
        #
        # Both positions are measured from the top.
        # ==========================--------

        y_expression = (
            f"{config.y1_wm}"
            f"+("
            f"{config.y2_wm}"
            f"-{config.y1_wm}"
            f")"
            f"*clip("
            f"(t-{config.start_time})"
            f"/{movement_duration},"
            f"0,"
            f"1"
            f")"
        )

        watermark_label = (
            f"wm_{input_index}"
        )

        return (
            # ==========================--
            # Prepare watermark
            # ==========================--

            f"[{input_index}:v]"
            f"scale="
            f"{config.width}:"
            f"{config.height},"
            f"format=rgba,"

            # Fade in
            f"fade="
            f"t=in:"
            f"st={fade_in_start}:"
            f"d={config.fade_duration}:"
            f"alpha=1,"

            # Fade out
            f"fade="
            f"t=out:"
            f"st={fade_out_start}:"
            f"d={config.fade_duration}:"
            f"alpha=1"

            f"[{watermark_label}];"

            # ==========================--
            # Overlay watermark
            # ==========================--

            f"[{source_label}]"
            f"[{watermark_label}]"
            f"overlay="
            f"x='{x_expression}':"
            f"y='{y_expression}':"
            f"enable='between("
            f"t,"
            f"{config.start_time},"
            f"{fade_out_end}"
            f")'"

            f"[{output_label}]"
        )

    # ========================================================
    # Language icon filter
    # ========================================================

    def _build_language_icon_filter(
        self,
        config: LanguageIconConfig,
        input_index: int,
        source_label: str,
        output_label: str,
    ) -> str:

        icon_label = (
            f"lang_{input_index}"
        )

        # ==========================--------
        # Visibility / timing
        # ==========================--------

        if (
            config.start_time is not None
            and config.end_time is not None
        ):

            enable_expr = (
                f":enable='between("
                f"t,"
                f"{config.start_time},"
                f"{config.end_time}"
                f")'"
            )

        elif config.start_time is not None:

            enable_expr = (
                f":enable='gte("
                f"t,"
                f"{config.start_time}"
                f")'"
            )

        elif config.end_time is not None:

            enable_expr = (
                f":enable='lte("
                f"t,"
                f"{config.end_time}"
                f")'"
            )

        else:

            enable_expr = ""

        # ==========================--------
        # Filter
        # ==========================--------

        return (
            f"[{input_index}:v]"
            f"scale="
            f"{config.width}:"
            f"{config.height},"
            f"format=rgba"
            f"[{icon_label}];"

            f"[{source_label}]"
            f"[{icon_label}]"
            f"overlay="
            f"x={config.x}:"
            f"y={config.y}"
            f"{enable_expr}"
            f"[{output_label}]"
        )

    # ========================================================
    # Main processing method
    # ========================================================

    def process_video(
        self,
        input_path: str | Path,
        output_path: str | Path,
        target_format: str,
        watermark_path: Optional[str | Path] = None,
        watermark_config: Optional[WatermarkConfig] = None,
        language_icon_path: Optional[str | Path] = None,
        language_icon_config: Optional[LanguageIconConfig] = None,
    ) -> Path:
        """
        Process one video.

        target_format:

            "portrait"
            "landscape"
        """

        input_path = Path(
            input_path
        )

        target_format = (
            target_format
            .lower()
            .strip()
        )

        output_path = Path(
            output_path
        )



        if target_format not in (
            "portrait",
            "landscape",
        ):
            raise ValueError(
                "target_format must be "
                "'portrait' or 'landscape'"
            )

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input video not found: "
                f"{input_path}"
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ====================================================
        # Analyze source
        # ====================================================

        duration = (
            self.get_video_duration(
                input_path
            )
        )

        (
            source_width,
            source_height,
        ) = self.get_video_dimensions(
            input_path
        )

        source_is_portrait = (
            source_height
            > source_width
        )

        print()
        print(
            "======================================"
        )
        print(
            "VidPoP processing"
        )
        print(
            "======================================"
        )

        print(
            f"Video duration : "
            f"{duration:.2f} s"
        )

        print(
            f"Source format  : "
            f"{source_width} x "
            f"{source_height}"
        )

        print(
            f"Orientation    : "
            f"{'portrait' if source_is_portrait else 'landscape'}"
        )

        print(
            f"Target format  : "
            f"{target_format}"
        )

        # ====================================================
        # Basic FFmpeg command
        # ====================================================

        command = [
            str(self.ffmpeg_path),
            "-y",

            "-i",
            str(input_path),
        ]

        filters: list[str] = []

        # Input 0:
        #
        #     original video
        #
        # Additional images start at index 1.

        next_input_index = 1

        # ====================================================
        # Static background
        # ====================================================

        static_background_input_index = (
            None
        )

        need_static_background = (
            target_format == "landscape"
            and source_is_portrait
            and self.use_static_background
        )

        if need_static_background:

            if not STATIC_BACKGROUND_PATH.exists():
                raise FileNotFoundError(
                    "Static background image not found: "
                    f"{STATIC_BACKGROUND_PATH}"
                )

            static_background_input_index = (
                next_input_index
            )

            command += [
                "-loop",
                "1",

                "-i",
                str(STATIC_BACKGROUND_PATH),
            ]

            next_input_index += 1

        # ====================================================
        # Step 1:
        # output format / canvas
        # ====================================================

        filters.append(
            self._build_format_filter(
                source_width=source_width,
                source_height=source_height,
                target_format=target_format,
                static_background_input_index=(
                    static_background_input_index
                ),
            )
        )

        current_label = (
            "video_format"
        )

        # ====================================================
        # Step 2:
        # Watermark
        # ====================================================

        if (
            watermark_config is not None
            and watermark_config.enabled
        ):

            if watermark_path is None:
                raise ValueError(
                    "Watermark enabled but "
                    "no watermark_path given."
                )

            watermark_path = Path(
                watermark_path
            )

            if not watermark_path.exists():
                raise FileNotFoundError(
                    f"Watermark not found: "
                    f"{watermark_path}"
                )

            watermark_input_index = (
                next_input_index
            )

            command += [
                "-loop",
                "1",

                "-i",
                str(watermark_path),
            ]

            next_input_index += 1

            output_label = (
                "video_wm"
            )

            filters.append(
                self._build_watermark_filter(
                    duration=duration,
                    config=watermark_config,
                    input_index=(
                        watermark_input_index
                    ),
                    source_label=(
                        current_label
                    ),
                    output_label=(
                        output_label
                    ),
                )
            )

            current_label = (
                output_label
            )

        # ====================================================
        # Step 3:
        # Language icon
        # ====================================================

        if (
            language_icon_config is not None
            and language_icon_config.enabled
        ):

            if language_icon_path is None:
                raise ValueError(
                    "Language icon enabled but "
                    "no language_icon_path given."
                )

            language_icon_path = Path(
                language_icon_path
            )

            if not language_icon_path.exists():
                raise FileNotFoundError(
                    f"Language icon not found: "
                    f"{language_icon_path}"
                )

            icon_input_index = (
                next_input_index
            )
            # print("language_icon_path: " + str(language_icon_path))
            command += [
                "-loop",
                "1",

                "-i",
                str(language_icon_path),
            ]

            next_input_index += 1

            output_label = (
                "video_lang"
            )

            filters.append(
                self._build_language_icon_filter(
                    config=(
                        language_icon_config
                    ),
                    input_index=(
                        icon_input_index
                    ),
                    source_label=(
                        current_label
                    ),
                    output_label=(
                        output_label
                    ),
                )
            )

            current_label = (
                output_label
            )

        # ====================================================
        # Final FFmpeg filter graph
        # ====================================================

        filter_complex = (
            ";".join(
                filters
            )
        )

        command += [
            "-filter_complex",
            filter_complex,

            # Final video stream
            "-map",
            f"[{current_label}]",

            # Original audio, if present
            "-map",
            "0:a?",

            # Video codec
            "-c:v",
            "libx264",

            # Quality
            "-crf",
            "18",

            # Encoding speed / compression trade-off
            "-preset",
            "medium",

            # Compatibility
            "-pix_fmt",
            "yuv420p",

            # Audio without re-encoding
            "-c:a",
            "copy",

            # Better web / streaming start
            "-movflags",
            "+faststart",

            # Stop looping image inputs at video duration
            "-t",
            str(duration),

            str(output_path).split(".")[0] + ".mp4",

        ]

        # ====================================================
        # Console information
        # ====================================================

        print()

        print(
            f"Input       : "
            f"{input_path}"
        )

        print(
            f"Target      : "
            f"{target_format}"
        )

        if (
            target_format == "portrait"
        ):
            print(
                f"Resolution  : "
                f"{PORTRAIT_WIDTH} x "
                f"{PORTRAIT_HEIGHT}"
            )

        else:
            print(
                f"Resolution  : "
                f"{LANDSCAPE_WIDTH} x "
                f"{LANDSCAPE_HEIGHT}"
            )

        if need_static_background:

            print(
                f"Background  : "
                f"{STATIC_BACKGROUND_PATH}"
            )

        elif (
            target_format == "landscape"
            and source_is_portrait
        ):

            print(
                "Background  : "
                "blurred video stream"
            )

        if (
            watermark_config is not None
            and watermark_config.enabled
        ):

            print(
                f"Watermark   : "
                f"{watermark_path}"
            )

        if (
            language_icon_config is not None
            and language_icon_config.enabled
        ):

            print(
                f"Language    : "
                f"{language_icon_path}"
            )

        print(
            f"Output      : "
            f"{output_path}"
        )

        print()
        print(
            "Starting FFmpeg..."
        )

        # ====================================================
        # Execute FFmpeg
        # ====================================================

        subprocess.run(
            command,
            check=True,
        )

        print(
            f"Finished     : "
            f"{output_path}"
        )

        return output_path

    # ========================================================
    # Batch processing
    # ========================================================

    def process_batch(
        self,
        input_path: str | Path,
        output_folder: str | Path,
        watermark_path: Optional[str | Path] = None,
        watermark_config: Optional[WatermarkConfig] = None,
        language_icon_path: Optional[str | Path] = None,
        language_icon_config: Optional[LanguageIconConfig] = None,
    ) -> tuple[Path, Path]:
        """
        Generate BOTH output versions.

        Example:

            input:
                maintenance.mp4

            output:
                maintenance_portrait.mp4
                maintenance_landscape.mp4

        Returns:

            (
                portrait_output,
                landscape_output,
            )
        """

        input_path = Path(
            input_path
        )

        output_folder = Path(
            output_folder
        )

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input video not found: "
                f"{input_path}"
            )

        output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        base_name = (
            input_path.stem
        )

        # ====================================================
        # Output filenames
        # ====================================================

        portrait_output = (
            output_folder
            / f"{base_name}_portrait.mp4"
        )

        landscape_output = (
            output_folder
            / f"{base_name}_landscape.mp4"
        )

        print()
        print()
        print(
            "######################################"
        )
        print(
            "# VidPoP batch"
        )
        print(
            "######################################"
        )

        print(
            f"Input: {input_path}"
        )

        print()

        # ====================================================
        # Portrait version
        # ====================================================

        self.process_video(
            input_path=input_path,

            output_path=portrait_output,

            target_format="portrait",

            watermark_path=(
                watermark_path
            ),

            watermark_config=(
                watermark_config
            ),

            language_icon_path=(
                language_icon_path
            ),

            language_icon_config=(
                language_icon_config
            ),
        )

        # ====================================================
        # Landscape version
        # ====================================================

        self.process_video(
            input_path=input_path,

            output_path=landscape_output,

            target_format="landscape",

            watermark_path=(
                watermark_path
            ),

            watermark_config=(
                watermark_config
            ),

            language_icon_path=(
                language_icon_path
            ),

            language_icon_config=(
                language_icon_config
            ),
        )

        # ====================================================
        # Finished
        # ====================================================

        print()
        print(
            "======================================"
        )
        print(
            "VidPoP batch finished"
        )
        print(
            "======================================"
        )

        print(
            f"Portrait  : "
            f"{portrait_output}"
        )

        print(
            f"Landscape : "
            f"{landscape_output}"
        )

        return (
            portrait_output,
            landscape_output,
        )
