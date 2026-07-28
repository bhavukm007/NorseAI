param(
    [string]$SourcePath = (Join-Path $PSScriptRoot "..\frontend\public\logo.png"),
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "..\frontend\public")
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

function New-TransparentMaster {
    param([string]$Path)

    $source = [System.Drawing.Bitmap]::FromFile($SourcePath)
    $cropLeft = 14
    $cropTop = 4
    $cropWidth = 42
    $cropHeight = 50
    $isolated = [System.Drawing.Bitmap]::new(
        $cropWidth,
        $cropHeight,
        [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
    )

    for ($y = 0; $y -lt $cropHeight; $y++) {
        for ($x = 0; $x -lt $cropWidth; $x++) {
            $pixel = $source.GetPixel($x + $cropLeft, $y + $cropTop)
            $blueDominance = $pixel.B - (($pixel.R + $pixel.G) / 2)
            $alpha = if ($blueDominance -lt 8) {
                0
            } else {
                [Math]::Min(255, [int](($blueDominance - 8) * 2.7))
            }
            $isolated.SetPixel(
                $x,
                $y,
                [System.Drawing.Color]::FromArgb($alpha, 1, 111, 208)
            )
        }
    }

    $scale = 8
    $master = [System.Drawing.Bitmap]::new(
        $isolated.Width * $scale,
        $isolated.Height * $scale,
        [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
    )
    $graphics = [System.Drawing.Graphics]::FromImage($master)
    $graphics.Clear([System.Drawing.Color]::Transparent)
    $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
    $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $graphics.DrawImage($isolated, 0, 0, $master.Width, $master.Height)
    $master.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)

    $graphics.Dispose()
    $master.Dispose()
    $isolated.Dispose()
    $source.Dispose()
}

function New-NorseIcon {
    param([int]$Size, [string]$Path)

    $source = [System.Drawing.Image]::FromFile(
        (Join-Path $OutputDirectory "logo-transparent.png")
    )
    $bitmap = [System.Drawing.Bitmap]::new(
        $Size,
        $Size,
        [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
    )
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.Clear([System.Drawing.Color]::Transparent)
    $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
    $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality

    $targetWidth = [int]($Size * 0.9)
    $targetHeight = [int]($targetWidth * $source.Height / $source.Width)
    $left = [int](($Size - $targetWidth) / 2)
    $top = [int](($Size - $targetHeight) / 2)
    $graphics.DrawImage($source, $left, $top, $targetWidth, $targetHeight)
    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)

    $graphics.Dispose()
    $bitmap.Dispose()
    $source.Dispose()
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
New-TransparentMaster (Join-Path $OutputDirectory "logo-transparent.png")
New-NorseIcon 180 (Join-Path $OutputDirectory "apple-touch-icon.png")
New-NorseIcon 192 (Join-Path $OutputDirectory "android-chrome-192x192.png")
New-NorseIcon 512 (Join-Path $OutputDirectory "android-chrome-512x512.png")
New-NorseIcon 64 (Join-Path $OutputDirectory "favicon-64.png")

$source = [System.Drawing.Bitmap]::FromFile((Join-Path $OutputDirectory "favicon-64.png"))
$icon = [System.Drawing.Icon]::FromHandle($source.GetHicon())
$stream = [System.IO.File]::Create((Join-Path $OutputDirectory "favicon.ico"))
$icon.Save($stream)
$stream.Dispose()
$icon.Dispose()
$source.Dispose()
