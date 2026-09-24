Add-Type -AssemblyName System.Drawing

# 脚本位于 frontend/scripts/，输出到 frontend/public/
$root = (Resolve-Path "$PSScriptRoot\..\public").Path

function New-Favicon {
    param(
        [int]$size,
        [string]$outPath
    )

    $bmp = New-Object System.Drawing.Bitmap $size, $size
    $g = [System.Drawing.Graphics]::FromImage($bmp)

    # 抗锯齿配置
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality

    # 圆角矩形背景（与 SVG 同色 #254373）
    $bgColor = [System.Drawing.Color]::FromArgb(255, 37, 67, 115)
    $bgBrush = New-Object System.Drawing.SolidBrush $bgColor
    $cornerRadius = [int][math]::Floor($size * 14 / 64)
    $r = $cornerRadius

    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $path.AddArc(0, 0, $r * 2, $r * 2, 180, 90)
    $path.AddArc($size - $r * 2, 0, $r * 2, $r * 2, 270, 90)
    $path.AddArc($size - $r * 2, $size - $r * 2, $r * 2, $r * 2, 0, 90)
    $path.AddArc(0, $size - $r * 2, $r * 2, $r * 2, 90, 90)
    $path.CloseFigure()
    $g.FillPath($bgBrush, $path)
    $path.Dispose()
    $bgBrush.Dispose()

    # M 字母（粗体白色，居中）
    # 用直接 float 变量传给 .NET，避免 PowerShell 类型转换问题
    $fontSizePx = [float]($size * 0.65)
    $font = New-Object System.Drawing.Font('Arial Black', $fontSizePx)
    $textBrush = [System.Drawing.Brushes]::White

    $ts = $g.MeasureString('M', $font)
    $tx = [float](($size - $ts.Width) / 2)
    $ty = [float](($size - $ts.Height) / 2)
    $g.DrawString('M', $font, $textBrush, $tx, $ty)

    $font.Dispose()

    # 输出 PNG
    $bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()

    Write-Host ("Generated: {0} ({1}x{1})" -f $outPath, $size)
}

New-Favicon 32  (Join-Path $root 'favicon-32x32.png')
New-Favicon 180 (Join-Path $root 'apple-touch-icon.png')